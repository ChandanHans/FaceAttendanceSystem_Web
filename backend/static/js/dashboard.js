// Dashboard functionality
document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardData();
    
    // Refresh data every 30 seconds
    setInterval(loadDashboardData, 30000);
});

// Cache for dashboard data to reduce API calls
let dashboardCache = {
    data: null,
    timestamp: 0,
    ttl: 30000 // Cache for 30 seconds
};

async function loadDashboardData() {
    try {
        // Check cache first
        const now = Date.now();
        if (dashboardCache.data && (now - dashboardCache.timestamp) < dashboardCache.ttl) {
            updateDashboardUI(dashboardCache.data);
            return;
        }
        
        // Load from new optimized endpoint
        const summaryResponse = await apiCall('/attendance/today-summary');
        if (summaryResponse.ok) {
            const summary = await summaryResponse.json();
            
            // Cache the data
            dashboardCache.data = summary;
            dashboardCache.timestamp = now;
            
            updateDashboardUI(summary);
        }
        
        // Load system status (lightweight, no caching needed)
        const statusResponse = await apiCall('/attendance/status');
        if (statusResponse.ok) {
            const status = await statusResponse.json();
            const statusText = status.is_running ? 'Running' : 'Stopped';
            const statusBadge = document.getElementById('systemStatusBadge');
            const statusElement = document.getElementById('systemStatus');
            
            if (statusElement) {
                statusElement.textContent = statusText;
            }
            if (statusBadge) {
                statusBadge.style.color = status.is_running ? '#10b981' : '#ef4444';
            }
        }
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function updateDashboardUI(summary) {
    const elements = {
        studentsPresent: document.getElementById('studentsPresent'),
        studentsTotal: document.getElementById('studentsTotal'),
        staffPresent: document.getElementById('staffPresent'),
        staffTotal: document.getElementById('staffTotal'),
        enrolledFaces: document.getElementById('enrolledFaces')
    };
    
    if (elements.studentsPresent) elements.studentsPresent.textContent = summary.students_present;
    if (elements.studentsTotal) elements.studentsTotal.textContent = summary.students_total;
    if (elements.staffPresent) elements.staffPresent.textContent = summary.staff_present;
    if (elements.staffTotal) elements.staffTotal.textContent = summary.staff_total;
    if (elements.enrolledFaces) elements.enrolledFaces.textContent = summary.total_enrolled;
}

// Invalidate cache when attendance is marked
function invalidateDashboardCache() {
    dashboardCache.timestamp = 0;
    loadDashboardData(); // Reload immediately
}
