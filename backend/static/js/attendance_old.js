// Attendance monitoring functionality
let isMonitoring = false;

document.addEventListener('DOMContentLoaded', () => {
    setupAttendanceControls();
    
    // Small delay to ensure DOM is fully rendered
    setTimeout(() => {
        checkServerStatusOnLoad();
    }, 100);
});

function setupAttendanceControls() {
    const toggleBtn = document.getElementById('toggleMonitoring');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', async () => {
            // Store the intended action BEFORE syncing (based on button text)
            const buttonText = toggleBtn.textContent.trim();
            const shouldStart = buttonText.includes('Start');
            
            console.log(`� Button clicked. Text: "${buttonText}", shouldStart: ${shouldStart}`);
            
            // Disable button during operation
            toggleBtn.disabled = true;
            toggleBtn.style.opacity = '0.6';
            toggleBtn.textContent = 'Checking...';
            
            try {
                // First, verify current server state
                await syncServerState();
                
                // Take action based on INTENDED action (from button), not current state
                console.log(`🎯 Decision: shouldStart=${shouldStart}, isMonitoring=${isMonitoring}`);
                
                if (shouldStart && !isMonitoring) {
                    console.log('▶️ CONDITION 1: User wants START, server STOPPED → Starting...');
                    await startAttendance();
                } else if (!shouldStart && isMonitoring) {
                    console.log('⏹️ CONDITION 2: User wants STOP, server RUNNING → Stopping...');
                    await stopAttendance();
                } else if (shouldStart && isMonitoring) {
                    console.log('🔄 CONDITION 3: User wants START, server RUNNING → No action needed');
                    // Just update UI, no action needed
                } else if (!shouldStart && !isMonitoring) {
                    console.log('🔄 CONDITION 4: User wants STOP, server STOPPED → No action needed');
                    // Just update UI, no action needed
                } else {
                    console.log('❓ CONDITION 5: Unexpected state combination');
                }
            } finally {
                // Re-enable button
                toggleBtn.disabled = false;
                toggleBtn.style.opacity = '1';
            }
        });
    }
}

// Update monitoring state from server
async function updateMonitoringState() {
    try {
        const response = await apiCall('/attendance/status');
        if (response.ok) {
            const status = await response.json();
            isMonitoring = status.is_running;
            
            // Update all UI elements
            updateButton();
            updateStatusIndicators();
            updateVideoStream();
            updateFaceCounts(status.known_faces_count);
            
            console.log(`📊 State: ${isMonitoring ? 'RUNNING ✅' : 'STOPPED ⏹'}`);
        }
    } catch (error) {
        console.error('❌ Failed to fetch status:', error);
    }
}

// Start monitoring
async function startMonitoring() {
    const cameraSource = document.getElementById('cameraSource')?.value || 0;
    
    const response = await apiCall('/attendance/start', {
        method: 'POST',
        body: JSON.stringify({ camera_source: parseInt(cameraSource) })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to start monitoring');
    }
    
    isMonitoring = true;
    const monitoringSince = document.getElementById('monitoringSince');
    if (monitoringSince) {
        monitoringSince.textContent = new Date().toLocaleString();
    }
    console.log('✅ Monitoring started');
}

// Stop monitoring
async function stopMonitoring() {
    const response = await apiCall('/attendance/stop', {
        method: 'POST'
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to stop monitoring');
    }
    
    isMonitoring = false;
    
    // Invalidate dashboard cache
    if (typeof invalidateDashboardCache === 'function') {
        invalidateDashboardCache();
    }
    
    console.log('✅ Monitoring stopped');
}

// Update button appearance
function updateButton() {
    const toggleBtn = document.getElementById('toggleMonitoring');
    if (!toggleBtn) return;
    
    if (isMonitoring) {
        toggleBtn.textContent = 'Stop Monitoring';
        toggleBtn.classList.remove('btn-success');
        toggleBtn.classList.add('btn-danger');
    } else {
        toggleBtn.textContent = 'Start Monitoring';
        toggleBtn.classList.remove('btn-danger');
        toggleBtn.classList.add('btn-success');
    }
}

// Set button loading state
function setButtonLoading(loading) {
    const toggleBtn = document.getElementById('toggleMonitoring');
    if (!toggleBtn) return;
    
    toggleBtn.disabled = loading;
    toggleBtn.style.opacity = loading ? '0.6' : '1';
    if (loading) {
        toggleBtn.textContent = 'Please wait...';
    }
}

// Update status indicators
function updateStatusIndicators() {
    const systemStatus = document.getElementById('systemStatus');
    const cameraSource = document.getElementById('cameraSource');
    
    if (systemStatus) {
        systemStatus.textContent = isMonitoring ? 'Running' : 'Stopped';
        systemStatus.style.color = isMonitoring ? 'var(--success-color)' : 'var(--danger-color)';
    }
    
    if (cameraSource) {
        cameraSource.disabled = isMonitoring;
    }
}

// Update face counts
function updateFaceCounts(count) {
    const knownFacesElement = document.getElementById('knownFacesCount');
    if (knownFacesElement) {
        knownFacesElement.textContent = count;
    }
    
    const enrolledFacesElement = document.getElementById('enrolledFaces');
    if (enrolledFacesElement) {
        enrolledFacesElement.textContent = count;
    }
}

// Update video stream based on state
function updateVideoStream() {
    if (isMonitoring) {
        startVideoStream();
    } else {
        stopVideoStream();
    }
}

// Video stream management
function startVideoStream() {
    const videoStream = document.getElementById('videoStream');
    const streamStatus = document.getElementById('streamStatus');
    const videoOverlay = document.getElementById('videoOverlay');
    
    if (videoOverlay) {
        videoOverlay.style.display = 'none';
    }
    
    if (videoStream) {
        videoStream.src = `${window.location.origin}/api/attendance/stream?t=${Date.now()}`;
        videoStream.style.display = 'block';
        
        videoStream.onerror = () => {
            console.error('❌ Failed to load video stream');
            if (videoOverlay) {
                videoOverlay.style.display = 'flex';
                videoOverlay.querySelector('p').textContent = 'Failed to load video stream';
            }
        };
    }
    
    if (streamStatus) {
        streamStatus.textContent = 'Live';
        streamStatus.style.backgroundColor = 'var(--success-color)';
    }
}

function stopVideoStream() {
    const videoStream = document.getElementById('videoStream');
    const streamStatus = document.getElementById('streamStatus');
    const videoOverlay = document.getElementById('videoOverlay');
    
    if (videoStream) {
        videoStream.src = '';
        videoStream.style.display = 'none';
    }
    
    if (videoOverlay) {
        videoOverlay.style.display = 'flex';
        const overlayText = videoOverlay.querySelector('p');
        if (overlayText) {
            overlayText.textContent = 'Click "Start Monitoring" to begin';
        }
    }
    
    if (streamStatus) {
        streamStatus.textContent = 'Not Running';
        streamStatus.style.backgroundColor = 'var(--danger-color)';
    }
}
