// Enrollment functionality
let currentRole = 'student';
let sessionId = null;
let video = null;
let canvas = null;
let capturing = false;
let captureInterval = null;
let isStartingEnrollment = false;
let isCaptureBusy = false;

document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure all elements are rendered
    setTimeout(() => {
        setupToggleButtons();
        setupForm();
        loadEnrolledList();
    }, 100);
});

function setupToggleButtons() {
    const studentBtn = document.getElementById('studentBtn');
    const staffBtn = document.getElementById('staffBtn');
    const studentFields = document.getElementById('studentFields');
    const staffFields = document.getElementById('staffFields');
    
    // Get all form fields
    const courseField = document.getElementById('course');
    const semesterField = document.getElementById('semester');
    const departmentField = document.getElementById('department');
    
    studentBtn.classList.add('active');
    
    studentBtn.addEventListener('click', () => {
        currentRole = 'student';
        studentBtn.classList.add('active');
        staffBtn.classList.remove('active');
        studentFields.style.display = 'block';
        staffFields.style.display = 'none';
        
        // Enable student fields, disable staff fields
        courseField.required = true;
        semesterField.required = true;
        departmentField.required = false;
    });
    
    staffBtn.addEventListener('click', () => {
        currentRole = 'staff';
        staffBtn.classList.add('active');
        studentBtn.classList.remove('active');
        studentFields.style.display = 'none';
        staffFields.style.display = 'block';
        
        // Disable student fields, enable staff fields
        courseField.required = false;
        semesterField.required = false;
        departmentField.required = true;
    });
}

function setupForm() {
    const form = document.getElementById('enrollmentForm');
    const completeBtn = document.getElementById('completeBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await startEnrollment();
    });
    
    completeBtn.addEventListener('click', completeEnrollment);
    cancelBtn.addEventListener('click', cancelEnrollment);
}

async function startEnrollment() {
    if (isStartingEnrollment) {
        console.log('⏳ Enrollment start in progress...');
        return;
    }
    isStartingEnrollment = true;
    const submitBtn = document.querySelector('#enrollmentForm button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    console.log('=== START ENROLLMENT CALLED ===');
    console.log('apiCall function available:', typeof apiCall !== 'undefined');
    console.log('localStorage token:', localStorage.getItem('access_token') ? 'Present' : 'Missing');
    
    if (typeof apiCall === 'undefined') {
        console.error('apiCall is not defined. Check if auth.js is loaded.');
        Dialog.error('Error: API function not available. Please refresh the page.');
        isStartingEnrollment = false;
        if (submitBtn) submitBtn.disabled = false;
        return;
    }
    
    const personId = document.getElementById('personId');
    const personName = document.getElementById('personName');
    
    console.log('Form elements found:', {
        personId: !!personId,
        personName: !!personName
    });
    
    if (!personId || !personName) {
        console.error('Form elements not found!');
        Dialog.error('Error: Form elements not found. Please refresh the page.');
        isStartingEnrollment = false;
        if (submitBtn) submitBtn.disabled = false;
        return;
    }
    
    if (!personId.value || !personName.value) {
        Dialog.warning('Please fill in ID and Name fields');
        return;
    }
    
    const data = {
        id: personId.value,
        name: personName.value,
        role: currentRole
    };
    
    if (currentRole === 'student') {
        data.course = document.getElementById('course').value;
        data.sem = document.getElementById('semester').value;
        console.log('Student fields:', { course: data.course, sem: data.sem });
        if (!data.course || !data.sem) {
            Dialog.warning('Please select Course and Semester');
            return;
        }
    } else {
        data.dep = document.getElementById('department').value;
        console.log('Staff field:', { dep: data.dep });
        if (!data.dep) {
            Dialog.warning('Please select Department');
            return;
        }
    }
    
    console.log('=== ENROLLMENT DATA ===', data);
    
    try {
        const response = await apiCall('/enrollment/start', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Enrollment started:', result);
            sessionId = result.session_id;
            await startCamera();
            isStartingEnrollment = false;
            if (submitBtn) submitBtn.disabled = true; // keep disabled while camera active
        } else {
            const error = await response.json();
            console.error('Enrollment error:', error);
            Dialog.error(error.error || 'Failed to start enrollment');
            isStartingEnrollment = false;
            if (submitBtn) submitBtn.disabled = false;
        }
    } catch (error) {
        console.error('Network error:', error);
        Dialog.error('Network error: ' + error.message);
        isStartingEnrollment = false;
        if (submitBtn) submitBtn.disabled = false;
    }
}

async function startCamera() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    const startCaptureBtn = document.getElementById('startCaptureBtn');
    if (startCaptureBtn) startCaptureBtn.disabled = true;
    
    // Get selected camera source
    const cameraSource = document.getElementById('cameraSource')?.value || 'browser';
    console.log('Selected camera source:', cameraSource);
    
    // If HTTP stream or server-side camera is selected, use server-side processing
    if (cameraSource !== 'browser') {
        await startServerSideCapture(cameraSource);
        return;
    }
    
    // Check browser compatibility for browser camera
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Browser camera not supported, trying alternatives...');
        await tryAlternativeCameraSources();
        return;
    }
    
    try {
        // Get available cameras
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        
        console.log('Available cameras:', videoDevices.length);
        
        // If no cameras found, try alternatives
        if (videoDevices.length === 0) {
            console.warn('No browser cameras found, trying alternatives...');
            await tryAlternativeCameraSources();
            return;
        }
        
        // Let user choose if multiple cameras available
        let selectedDeviceId = null;
        if (videoDevices.length > 1) {
            selectedDeviceId = await showCameraSelector(videoDevices);
            if (!selectedDeviceId) {
                Dialog.warning('No camera selected. Using default camera.');
            }
        }
        
        // Request camera with optimal settings
        const constraints = {
            video: selectedDeviceId ? {
                deviceId: { exact: selectedDeviceId },
                width: { ideal: 640 },
                height: { ideal: 480 }
            } : {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user' // Front camera on mobile, default on desktop
            }
        };
        
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        
        // Wait for video to be ready
        await new Promise(resolve => {
            video.onloadedmetadata = () => {
                video.play();
                resolve();
            };
        });
        
        console.log('Camera started successfully');
        
        // Show capture panel and hide form
        document.getElementById('capturePanel').style.display = 'block';
        document.getElementById('enrollmentForm').style.display = 'none';
        document.getElementById('cancelBtn').style.display = 'inline-block';
        if (startCaptureBtn) startCaptureBtn.disabled = true; // ensure disabled while auto-capturing
        
        capturing = true;
        captureInterval = setInterval(captureFrame, 500);
        console.log('Started capturing frames');
        
    } catch (error) {
        console.error('Browser camera error:', error);
        console.warn('Browser camera failed, trying alternatives...');
        await tryAlternativeCameraSources();
    }
}

async function tryAlternativeCameraSources() {
    console.log('Attempting to use alternative camera sources...');
    
    // Try server-side camera as fallback
    const confirmed = await Dialog.confirm(
        'Browser camera not available. Would you like to use server-side camera capture instead?'
    );
    
    if (confirmed) {
        await startServerSideCapture('server');
    } else {
        Dialog.error('Camera access required for enrollment. Please connect a camera or use server-side capture.');
        const submitBtn = document.querySelector('#enrollmentForm button[type="submit"]');
        if (submitBtn) submitBtn.disabled = false;
        const startCaptureBtn = document.getElementById('startCaptureBtn');
        if (startCaptureBtn) startCaptureBtn.disabled = false;
    }
}

async function startServerSideCapture(source) {
    console.log('Starting server-side capture with source:', source);
    
    try {
        // Show capture panel and hide form
        document.getElementById('capturePanel').style.display = 'block';
        document.getElementById('enrollmentForm').style.display = 'none';
        document.getElementById('cancelBtn').style.display = 'inline-block';
        
        // Show info message
        Dialog.info('Using server-side camera. Please position yourself in front of the camera.');
        
        // Start capturing using server
        capturing = true;
        captureInterval = setInterval(captureFrameFromServer, 1000); // Slower interval for server-side
        console.log('Started server-side frame capture');
        
        // Display message in video area
        video = document.getElementById('video');
        const videoContainer = video.parentElement;
        const statusDiv = document.getElementById('captureStatus');
        statusDiv.textContent = 'Using server-side camera capture';
        statusDiv.style.display = 'block';
        
    } catch (error) {
        console.error('Server-side capture error:', error);
        Dialog.error('Failed to start server-side capture: ' + error.message);
        const submitBtn = document.querySelector('#enrollmentForm button[type="submit"]');
        if (submitBtn) submitBtn.disabled = false;
        const startCaptureBtn = document.getElementById('startCaptureBtn');
        if (startCaptureBtn) startCaptureBtn.disabled = false;
    }
}

async function captureFrameFromServer() {
    if (!capturing || !sessionId) return;
    if (isCaptureBusy) return;
    
    isCaptureBusy = true;
    
    try {
        // Request server to capture from its camera
        const response = await apiCall('/enrollment/capture_server', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Server capture result:', result);
            
            if (result.captured) {
                updateProgress(result.captured_count, result.total_required);
                
                if (result.captured_count >= result.total_required) {
                    stopCapturing();
                    document.getElementById('completeBtn').style.display = 'inline-block';
                    Dialog.success('All images captured! You can now complete enrollment.');
                }
            }
        } else {
            const error = await response.json();
            console.error('Server capture error:', error);
        }
    } catch (error) {
        console.error('Server capture request error:', error);
    } finally {
        isCaptureBusy = false;
    }
}

async function captureFrame() {
    if (!capturing || !video || !canvas) return;
    if (isCaptureBusy) return; // avoid overlapping requests while server is busy
    
    try {
        // Check user preference and model availability
        const processingToggle = document.getElementById('processingToggle');
        const userWantsClient = processingToggle ? processingToggle.checked : false;
        const modelsAvailable = window.FaceProcessor && FaceProcessor.modelsLoaded;
        const useClientProcessing = userWantsClient && modelsAvailable;
        
        if (!modelsAvailable && userWantsClient) {
            console.warn('⚠️ Client processing selected but models not loaded. Using server-side.');
        }
        
        if (useClientProcessing) {
            // CLIENT-SIDE PROCESSING (face-api.js - lightweight on Pi)
            console.log('💻 Using CLIENT-SIDE processing (face-api.js)');
            const faceData = await FaceProcessor.detectFace(video);
            
            if (!faceData) {
                // Clear canvas and show message
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0);
                
                updateProgress({
                    count: 0,
                    target: 5,
                    message: '⚠️ No face detected. Please face the camera.',
                    complete: false
                });
                return;
            }
            
            // Draw video frame and face axis on canvas
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            // Draw face axis visualization
            FaceProcessor.drawFaceAxis(ctx, faceData.landmarks, faceData.angle, faceData.box);
            
            // Log face data with detailed angles
            console.log('📐 ANGLES - Yaw:', faceData.angle.yaw.toFixed(1) + '°', 'Pitch:', faceData.angle.pitch.toFixed(1) + '°', 'Roll:', faceData.angle.roll.toFixed(1) + '°');
            console.log('🎯 Detection Score:', faceData.score.toFixed(3));
            
            // Send descriptor (512 bytes instead of 50KB!)
            isCaptureBusy = true;
            const response = await apiCall('/enrollment/capture', {
                method: 'POST',
                body: JSON.stringify({
                    session_id: sessionId,
                    descriptor: faceData.descriptor,
                    angle: faceData.angle,
                    use_client_processing: true
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                updateProgress(result);
                
                if (result.captured) {
                    console.log(`✅ Captured ${result.count}/${result.target}`);
                }
                
                if (result.complete) {
                    clearInterval(captureInterval);
                    capturing = false;
                    document.getElementById('completeBtn').style.display = 'inline-block';
                }
                isCaptureBusy = false;
            }
        } else {
            // FALLBACK: SERVER-SIDE PROCESSING (dlib on Pi)
            console.log('🖥️ Using SERVER-SIDE processing (dlib)');
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            // Add text overlay for server-side mode
            ctx.font = 'bold 18px Arial';
            ctx.fillStyle = '#FFFF00';
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 3;
            ctx.strokeText('Server Processing', 10, 30);
            ctx.fillText('Server Processing', 10, 30);
            
            const frameData = canvas.toDataURL('image/jpeg', 0.8);
            
            isCaptureBusy = true;
            const response = await apiCall('/enrollment/capture', {
                method: 'POST',
                body: JSON.stringify({
                    session_id: sessionId,
                    frame: frameData,
                    use_client_processing: false
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Log angle if provided by server
                if (result.angle !== undefined) {
                    console.log(`📐 Server detected angle: ${result.angle.toFixed(1)}°`);
                }
                
                updateProgress(result);
                
                if (result.captured) {
                    console.log(`📸 Captured ${result.count}/${result.target}`);
                }
                
                if (result.complete) {
                    clearInterval(captureInterval);
                    capturing = false;
                    document.getElementById('completeBtn').style.display = 'inline-block';
                }
                isCaptureBusy = false;
            }
        }
    } catch (error) {
        console.error('Capture error:', error);
        isCaptureBusy = false;
    }
}

function updateProgress(result) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const captureStatus = document.getElementById('captureStatus');
    
    const percentage = (result.count / result.target) * 100;
    progressFill.style.width = percentage + '%';
    progressText.textContent = `${result.count} / ${result.target} captured`;
    captureStatus.textContent = result.message;
}

async function completeEnrollment() {
    const completeBtn = document.getElementById('completeBtn');
    if (completeBtn) completeBtn.disabled = true;
    try {
        const response = await apiCall('/enrollment/complete', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
        
        if (response.ok) {
            Dialog.success('Enrollment completed successfully!');
            resetEnrollment();
            loadEnrolledList();
        } else {
            const error = await response.json();
            Dialog.error(error.error || 'Failed to complete enrollment');
        }
    } catch (error) {
        Dialog.error('Network error. Please try again.');
    }
    if (completeBtn) completeBtn.disabled = false;
}

function cancelEnrollment() {
    if (sessionId) {
        apiCall('/enrollment/cancel', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
    }
    resetEnrollment();
}

function resetEnrollment() {
    console.log('=== RESET ENROLLMENT CALLED ===');
    console.log('Stack trace:', new Error().stack);
    
    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
    
    capturing = false;
    if (captureInterval) {
        clearInterval(captureInterval);
    }
    
    console.log('Clearing sessionId:', sessionId);
    sessionId = null;
    
    // Reset and show form, hide capture panel
    document.getElementById('enrollmentForm').reset();
    document.getElementById('enrollmentForm').style.display = 'flex';
    document.getElementById('capturePanel').style.display = 'none';
    
    // Reset progress
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = '0 / 5 captured';
    document.getElementById('captureStatus').textContent = '';
    document.getElementById('completeBtn').style.display = 'none';
    document.getElementById('cancelBtn').style.display = 'none';
    document.getElementById('startCaptureBtn').disabled = false;
    const submitBtn = document.querySelector('#enrollmentForm button[type="submit"]');
    if (submitBtn) submitBtn.disabled = false;
    isStartingEnrollment = false;
    
    console.log('Enrollment reset complete');
}

async function loadEnrolledList(filter = 'all') {
    try {
        const response = await apiCall('/enrollment/list');
        if (response.ok) {
            const data = await response.json();
            displayEnrolledList(data, filter);
        }
    } catch (error) {
        console.error('Error loading enrolled list:', error);
    }
}

function displayEnrolledList(data, filter) {
    const tbody = document.getElementById('enrolledTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    let items = [];
    if (filter === 'all' || filter === 'student') {
        items = items.concat(data.students);
    }
    if (filter === 'all' || filter === 'staff') {
        items = items.concat(data.staff);
    }
    
    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">No enrolled persons found. Start enrollment to add faces.</td></tr>';
        return;
    }
    
    items.forEach(person => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${person.id}</td>
            <td>${person.name}</td>
            <td>${person.course || person.dep}${person.sem ? ' - Sem ' + person.sem : ''}</td>
            <td style="text-align: center;">
                <button class="btn btn-danger btn-sm" onclick="deletePerson('${person.id}', '${person.role}')">
                    🗑️ Delete
                </button>
            </td>
        `;
    });
}

async function deletePerson(personId, role) {
    if (!await Dialog.confirm(`Are you sure you want to delete ${personId}?`)) {
        return;
    }
    
    try {
        const response = await apiCall(`/enrollment/delete/${personId}?role=${role}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            Dialog.success('Deleted successfully');
            loadEnrolledList();
        } else {
            const error = await response.json();
            Dialog.error(error.error || 'Failed to delete');
        }
    } catch (error) {
        Dialog.error('Network error. Please try again.');
    }
}

// Filter buttons with active state
function setupFilterButtons() {
    const filterBtns = document.querySelectorAll('.filter-btns .btn-xs');
    const showAllBtn = document.getElementById('showAll');
    const showStudentsBtn = document.getElementById('showStudents');
    const showStaffBtn = document.getElementById('showStaff');
    
    if (showAllBtn) {
        showAllBtn.addEventListener('click', () => {
            filterBtns.forEach(btn => btn.classList.remove('active'));
            showAllBtn.classList.add('active');
            loadEnrolledList('all');
        });
    }
    
    if (showStudentsBtn) {
        showStudentsBtn.addEventListener('click', () => {
            filterBtns.forEach(btn => btn.classList.remove('active'));
            showStudentsBtn.classList.add('active');
            loadEnrolledList('student');
        });
    }
    
    if (showStaffBtn) {
        showStaffBtn.addEventListener('click', () => {
            filterBtns.forEach(btn => btn.classList.remove('active'));
            showStaffBtn.classList.add('active');
            loadEnrolledList('staff');
        });
    }
}

// Initialize filter buttons when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setupFilterButtons();
});

// Camera selection dialog
async function showCameraSelector(cameras) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay show';
        overlay.style.zIndex = '10001';
        
        const dialog = document.createElement('div');
        dialog.className = 'dialog-box';
        dialog.innerHTML = `
            <div class="dialog-icon">📹</div>
            <h3 class="dialog-title">Select Camera</h3>
            <p class="dialog-message">Choose which camera to use for enrollment:</p>
            <select id="cameraSelect" class="select-sm" style="width: 100%; margin: 1rem 0; padding: 0.5rem;">
                ${cameras.map((cam, idx) => `
                    <option value="${cam.deviceId}">
                        ${cam.label || `Camera ${idx + 1}`}
                    </option>
                `).join('')}
            </select>
            <div class="dialog-actions">
                <button class="btn btn-primary" id="confirmCamera">Use This Camera</button>
                <button class="btn btn-secondary" id="cancelCamera">Use Default</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        document.getElementById('confirmCamera').onclick = () => {
            const select = document.getElementById('cameraSelect');
            const deviceId = select.value;
            document.body.removeChild(overlay);
            resolve(deviceId);
        };
        
        document.getElementById('cancelCamera').onclick = () => {
            document.body.removeChild(overlay);
            resolve(null);
        };
    });
}

// Make loadEnrolledList globally accessible
window.loadEnrolledPersons = () => loadEnrolledList('all');
