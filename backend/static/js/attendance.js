// Attendance Monitoring - Clean State Management
let isMonitoring = false;
let isProcessing = false;
let isBusy = false;

document.addEventListener('DOMContentLoaded', () => {
    initializeAttendanceTab();
});

async function initializeAttendanceTab() {
    // Check server status on load
    await updateMonitoringState();
    
    // Setup button click handler
    const toggleBtn = document.getElementById('toggleMonitoring');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', handleToggleClick);
    }
    
    // Periodic status check every 10 seconds
    setInterval(updateMonitoringState, 10000);
}

async function handleToggleClick() {
    if (isProcessing || isBusy) {
        console.log('⏳ Operation already in progress...');
        return;
    }
    
    isProcessing = true;
    setButtonLoading(true);
    
    try {
        if (isMonitoring) {
            console.log('🛑 Stopping monitoring...');
            await stopMonitoring();
            // Wait a bit for cleanup
            await new Promise(resolve => setTimeout(resolve, 500));
        } else {
            console.log('▶ Starting monitoring...');
            await startMonitoring();
            // Wait for video stream to actually start
            await waitForVideoStream();
        }
    } catch (error) {
        console.error('❌ Operation failed:', error);
        Dialog.error(error.message || 'Operation failed. Please try again.');
    } finally {
        isProcessing = false;
        setButtonLoading(false);
        await updateMonitoringState(); // Refresh state after action
    }
}

// Update monitoring state from server
async function updateMonitoringState() {
    try {
        const response = await apiCall('/attendance/status');
        if (response.ok) {
            const status = await response.json();
            isMonitoring = status.is_running;
            isBusy = !!status.is_busy;
            
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

// Wait for video stream to initialize
async function waitForVideoStream(maxWait = 3000) {
    const videoStream = document.getElementById('videoStream');
    if (!videoStream) return;
    
    return new Promise((resolve) => {
        const startTime = Date.now();
        const checkInterval = setInterval(() => {
            // Check if video has loaded or timeout
            if (videoStream.complete || videoStream.naturalWidth > 0 || Date.now() - startTime > maxWait) {
                clearInterval(checkInterval);
                resolve();
            }
        }, 100);
    });
}

// Start monitoring
async function startMonitoring() {
    console.log('🎥 Auto-detecting camera source...');
    let cameraSource = await detectBestCamera();
    console.log('📹 Using camera source:', cameraSource);
    
    const response = await apiCall('/attendance/start', {
        method: 'POST',
        body: JSON.stringify({ camera_source: cameraSource })
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
    if (isProcessing || isBusy) {
        toggleBtn.disabled = true;
        toggleBtn.style.opacity = '0.6';
        toggleBtn.textContent = 'Please wait...';
        return;
    }
    
    if (isMonitoring) {
        toggleBtn.textContent = 'Stop Monitoring';
        toggleBtn.classList.remove('btn-success');
        toggleBtn.classList.add('btn-danger');
        toggleBtn.disabled = false;
        toggleBtn.style.opacity = '1';
    } else {
        toggleBtn.textContent = 'Start Monitoring';
        toggleBtn.classList.remove('btn-danger');
        toggleBtn.classList.add('btn-success');
        toggleBtn.disabled = false;
        toggleBtn.style.opacity = '1';
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
    const monitoringSince = document.getElementById('monitoringSince');
    
    if (systemStatus) {
        systemStatus.textContent = isBusy ? 'Initializing…' : (isMonitoring ? 'Running' : 'Stopped');
        systemStatus.style.color = isBusy ? 'var(--warning-color)' : (isMonitoring ? 'var(--success-color)' : 'var(--danger-color)');
    }
    
    if (cameraSource) {
        cameraSource.disabled = isMonitoring || isBusy;
    }
    
    if (monitoringSince && !isMonitoring) {
        monitoringSince.textContent = '-';
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
        videoOverlay.style.display = isBusy ? 'flex' : 'none';
        const overlayText = videoOverlay.querySelector('p');
        if (overlayText) {
            overlayText.textContent = isBusy ? 'Initializing camera…' : '';
        }
    }
    
    if (videoStream) {
        videoStream.src = `${window.location.origin}/api/attendance/stream?t=${Date.now()}`;
        videoStream.style.display = 'block';
        
        videoStream.onerror = () => {
            console.error('❌ Failed to load video stream');
            if (videoOverlay) {
                videoOverlay.style.display = 'flex';
                const overlayText = videoOverlay.querySelector('p');
                if (overlayText) {
                    overlayText.textContent = 'Failed to load video stream';
                }
            }
        };
    }
    
    if (streamStatus) {
        streamStatus.textContent = isBusy ? 'Initializing' : 'Live';
        streamStatus.style.backgroundColor = isBusy ? 'var(--warning-color)' : 'var(--success-color)';
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
