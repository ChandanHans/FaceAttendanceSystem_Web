// Enrollment functionality - SERVER-SIDE ONLY
let currentRole = 'student';
let sessionId = null;
let capturing = false;
let captureInterval = null;
let isStartingEnrollment = false;
let isCaptureBusy = false;

document.addEventListener('DOMContentLoaded', () => {
    setupToggleButtons();
    setupForm();
    loadEnrolledList();
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
    
    const personId = document.getElementById('personId');
    const personName = document.getElementById('personName');
    
    if (!personId || !personName) {
        Dialog.error('Form elements not found');
        isStartingEnrollment = false;
        if (submitBtn) submitBtn.disabled = false;
        return;
    }
    
    if (!personId.value || !personName.value) {
        Dialog.warning('Please fill in ID and Name fields');
        isStartingEnrollment = false;
        if (submitBtn) submitBtn.disabled = false;
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
        if (!data.dep) {
            Dialog.warning('Please select Department');
            isStartingEnrollment = false;
            if (submitBtn) submitBtn.disabled = false;
            return;
        }
    }
    
    try {
        const response = await apiCall('/enrollment/start', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const result = await response.json();
            sessionId = result.session_id;
            startServerSideCapture();
            isStartingEnrollment = false;
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

function startServerSideCapture() {
    console.log('🎥 Starting server-side camera capture...');
    
    // Show capture panel and hide form
    document.getElementById('capturePanel').style.display = 'block';
    document.getElementById('enrollmentForm').style.display = 'none';
    document.getElementById('cancelBtn').style.display = 'inline-block';
    document.getElementById('completeBtn').style.display = 'none';
    
    // Update progress display
    updateProgress({
        count: 0,
        target: 5,
        message: 'Capturing from server camera...'
    });
    
    // Update info text
    const captureInfo = document.getElementById('captureInfo');
    if (captureInfo) {
        captureInfo.textContent = 'Using server camera. Please look at the camera and turn your head slowly.';
    }
    
    // Start capturing
    capturing = true;
    captureInterval = setInterval(captureFrameFromServer, 1500);
    console.log('Started server-side capture');
}

async function captureFrameFromServer() {
    if (!capturing || !sessionId) {
        console.log('Server capture skipped - capturing:', capturing, 'sessionId:', sessionId);
        return;
    }
    if (isCaptureBusy) {
        console.log('Server capture skipped - busy');
        return;
    }
    
    isCaptureBusy = true;
    console.log('📸 Requesting server capture...');
    
    try {
        // Request server to capture from its camera
        const response = await apiCall('/enrollment/capture_server', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
        
        console.log('Server response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Server capture result:', result);
            console.log('  - captured:', result.captured);
            console.log('  - captured_count:', result.captured_count);
            console.log('  - total_required:', result.total_required);
            console.log('  - message:', result.message);
            
            // Validate response data
            const count = typeof result.captured_count === 'number' ? result.captured_count : 0;
            const target = typeof result.total_required === 'number' ? result.total_required : 5;
            const message = result.message || 'Processing...';
            
            console.log('Updating progress with count:', count, 'target:', target);
            
            // Update progress with proper format
            updateProgress({
                count: count,
                target: target,
                message: message
            });
            
            if (result.captured) {
                console.log('✅ Frame captured successfully!');
                if (count >= target) {
                    console.log('🎉 All frames captured!');
                    stopCapturing();
                    document.getElementById('completeBtn').style.display = 'inline-block';
                    Dialog.success('All images captured! You can now complete enrollment.');
                }
            } else {
                console.log('⏭️ Frame not captured:', message);
            }
        } else {
            const error = await response.json();
            console.error('Server capture error response:', error);
            updateProgress({
                count: 0,
                target: 5,
                message: error.error || 'Server capture failed'
            });
        }
    } catch (error) {
        console.error('Server capture request error:', error);
        updateProgress({
            count: 0,
            target: 5,
            message: 'Connection error: ' + error.message
        });
    } finally {
        isCaptureBusy = false;
    }
}

function stopCapturing() {
    capturing = false;
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
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
    // Stop capturing
    capturing = false;
    if (captureInterval) {
        clearInterval(captureInterval);
    }
    
    sessionId = null;
    
    // Reset and show form, hide capture panel
    document.getElementById('enrollmentForm').reset();
    document.getElementById('enrollmentForm').style.display = 'flex';
    document.getElementById('capturePanel').style.display = 'none';
    
    // Reset info text
    const captureInfo = document.getElementById('captureInfo');
    if (captureInfo) {
        captureInfo.textContent = 'System will capture 5 images from different angles using server camera.';
    }
    
    // Reset progress
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('progressText').textContent = '0 / 5 captured';
    document.getElementById('captureStatus').textContent = '';
    document.getElementById('completeBtn').style.display = 'none';
    document.getElementById('cancelBtn').style.display = 'none';
    
    const submitBtn = document.querySelector('#enrollmentForm button[type="submit"]');
    if (submitBtn) submitBtn.disabled = false;
    isStartingEnrollment = false;
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

// Make loadEnrolledList globally accessible
window.loadEnrolledPersons = () => loadEnrolledList('all');
