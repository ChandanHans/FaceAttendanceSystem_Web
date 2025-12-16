/**
 * Attendance Sheet Report - Shows dates as columns
 */

async function loadAttendanceSheet() {
    const role = document.getElementById('roleFilter').value;
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const personId = document.getElementById('personIdFilter').value;
    
    let url = `/reports/attendance-sheet?role=${role}`;
    if (dateFrom) url += `&from=${dateFrom}`;
    if (dateTo) url += `&to=${dateTo}`;
    if (personId) url += `&id=${personId}`;
    
    try {
        const response = await apiCall(url);
        if (response.ok) {
            const data = await response.json();
            displayAttendanceSheet(data);
        } else {
            Dialog.error('Failed to load attendance sheet');
        }
    } catch (error) {
        Dialog.error('Network error. Please try again.');
    }
}

function displayAttendanceSheet(data) {
    const container = document.getElementById('sheetTableContainer');
    if (!container) return;
    
    // Store data globally for export
    window.currentSheetData = data;
    
    const { persons, dates, attendance, role } = data;
    
    if (persons.length === 0) {
        container.innerHTML = '<p class="text-center">No records found.</p>';
        return;
    }
    
    // Build table
    let html = '<div class="table-scroll"><table class="data-table attendance-sheet">';
    
    // Header row with dates
    html += '<thead><tr>';
    html += '<th>ID</th>';
    html += '<th>Name</th>';
    html += role === 'student' ? '<th>Course</th>' : '<th>Department</th>';
    
    dates.forEach(date => {
        const dateObj = new Date(date);
        const dayMonth = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' });
        html += `<th class="date-column" title="${date}"><div>${dayMonth}</div><div class="day-name">${dayName}</div></th>`;
    });
    
    html += '<th class="total-column">Total</th>';
    html += '</tr></thead><tbody>';
    
    // Body rows for each person
    persons.forEach(person => {
        html += '<tr>';
        html += `<td>${person.id}</td>`;
        html += `<td>${person.name}</td>`;
        html += `<td>${person.course || person.dep}</td>`;
        
        let totalPresent = 0;
        
        dates.forEach(date => {
            const key = `${person.id}_${date}`;
            const record = attendance[key];
            
            if (record) {
                totalPresent++;
                const time = record.check_in.substring(0, 5); // HH:MM
                html += `<td class="present" title="Check-in: ${record.check_in}">✓<br><span class="time">${time}</span></td>`;
            } else {
                html += '<td class="absent">✗</td>';
            }
        });
        
        html += `<td class="total-column"><strong>${totalPresent}/${dates.length}</strong></td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    container.innerHTML = html;
}

// Add button to switch view mode
function setupViewToggle() {
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'btn btn-secondary btn-sm';
    toggleBtn.id = 'toggleViewBtn';
    toggleBtn.textContent = 'Sheet View';
    toggleBtn.onclick = toggleReportView;
    
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn && exportBtn.parentElement) {
        exportBtn.parentElement.insertBefore(toggleBtn, exportBtn);
    }
}

let isSheetView = false;

function toggleReportView() {
    isSheetView = !isSheetView;
    window.isSheetView = isSheetView; // Make globally accessible for export
    
    const toggleBtn = document.getElementById('toggleViewBtn');
    const tableContainer = document.querySelector('#reports-tab .table-scroll');
    const sheetContainer = document.getElementById('sheetTableContainer') || createSheetContainer();
    
    if (isSheetView) {
        toggleBtn.textContent = 'List View';
        tableContainer.style.display = 'none';
        sheetContainer.style.display = 'block';
        loadAttendanceSheet();
    } else {
        toggleBtn.textContent = 'Sheet View';
        tableContainer.style.display = 'block';
        sheetContainer.style.display = 'none';
        loadReport();
    }
}

function createSheetContainer() {
    const container = document.createElement('div');
    container.id = 'sheetTableContainer';
    container.style.display = 'none';
    
    const reportsContainer = document.querySelector('#reports-tab .reports-container');
    if (reportsContainer) {
        reportsContainer.appendChild(container);
    }
    
    return container;
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupViewToggle);
} else {
    setupViewToggle();
}
