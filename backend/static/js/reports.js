// Reports functionality
let currentReportData = [];

document.addEventListener('DOMContentLoaded', () => {
    setupFilters();
    setDefaultDates();
});

function setupFilters() {
    document.getElementById('loadReportBtn').addEventListener('click', loadReport);
    document.getElementById('exportBtn').addEventListener('click', exportToCSV);
}

function setDefaultDates() {
    const today = new Date().toISOString().split('T')[0];
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    document.getElementById('dateFrom').value = weekAgo;
    document.getElementById('dateTo').value = today;
}

async function loadReport() {
    const role = document.getElementById('roleFilter').value;
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const personId = document.getElementById('personIdFilter').value;
    
    let url = `/reports/attendance?role=${role}`;
    if (dateFrom) url += `&from=${dateFrom}`;
    if (dateTo) url += `&to=${dateTo}`;
    if (personId) url += `&id=${personId}`;
    
    try {
        const response = await apiCall(url);
        if (response.ok) {
            const data = await response.json();
            currentReportData = data.data;
            displayReport(data);
        } else {
            Dialog.error('Failed to load report');
        }
    } catch (error) {
        Dialog.error('Network error. Please try again.');
    }
}

function displayReport(data) {
    const tbody = document.getElementById('reportTableBody');
    const recordCount = document.getElementById('recordCount');
    
    if (!tbody || !recordCount) return;
    
    tbody.innerHTML = '';
    recordCount.textContent = data.count;
    
    if (data.count === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No records found. Start monitoring to mark attendance.</td></tr>';
        return;
    }
    
    data.data.forEach(record => {
        const row = tbody.insertRow();
        
        if (data.role === 'student') {
            row.innerHTML = `
                <td>${record.id}</td>
                <td>${record.name}</td>
                <td>${record.course} - Sem ${record.sem}</td>
                <td>${record.date}</td>
                <td>${record.check_in}</td>
                <td>-</td>
            `;
        } else {
            row.innerHTML = `
                <td>${record.id}</td>
                <td>${record.name}</td>
                <td>${record.dep}</td>
                <td>${record.date}</td>
                <td>${record.check_in || '-'}</td>
                <td>${record.check_out || '-'}</td>
            `;
        }
    });
}

function exportToCSV() {
    // Check if we're in sheet view or list view
    if (window.isSheetView && window.currentSheetData) {
        exportSheetToCSV();
        return;
    }
    
    // Export list view
    if (currentReportData.length === 0) {
        Dialog.warning('No data to export. Please load a report first.');
        return;
    }
    
    const role = document.getElementById('roleFilter').value;
    let csv = '';
    
    if (role === 'student') {
        csv = 'ID,Name,Course,Semester,Date,Check In\n';
        currentReportData.forEach(record => {
            csv += `${record.id},${record.name},${record.course},${record.sem},${record.date},${record.check_in}\n`;
        });
    } else {
        csv = 'ID,Name,Department,Date,Check In,Check Out\n';
        currentReportData.forEach(record => {
            csv += `${record.id},${record.name},${record.dep},${record.date},${record.check_in || ''},${record.check_out || ''}\n`;
        });
    }
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_list_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function exportSheetToCSV() {
    const data = window.currentSheetData;
    if (!data || !data.persons || data.persons.length === 0) {
        Dialog.warning('No data to export. Please load attendance sheet first.');
        return;
    }
    
    const { persons, dates, attendance, role } = data;
    
    // Build CSV header
    let csv = 'ID,Name,' + (role === 'student' ? 'Course' : 'Department');
    dates.forEach(date => {
        csv += ',' + date;
    });
    csv += ',Total Present\n';
    
    // Build CSV rows
    persons.forEach(person => {
        let row = `${person.id},${person.name},${person.course || person.dep}`;
        let totalPresent = 0;
        
        dates.forEach(date => {
            const key = `${person.id}_${date}`;
            const record = attendance[key];
            if (record && record.check_in) {
                row += ',' + record.check_in;
                totalPresent++;
            } else {
                row += ',Absent';
            }
        });
        
        row += ',' + totalPresent;
        csv += row + '\n';
    });
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_sheet_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Make fetchAttendanceData globally accessible for main.js
window.fetchAttendanceData = loadReport;
