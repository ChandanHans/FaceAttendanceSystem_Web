// Main.js - Coordinates single-page application functionality
class DashboardManager {
    constructor() {
        this.currentTab = 'monitoring';
        this.monitoringActive = false;
        this.stats = {
            today: 0,
            students: 0,
            staff: 0
        };
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupMonitoring();
        this.loadStats();
        this.setupLogout();
        
        // Load initial data
        if (window.loadEnrolledPersons) {
            window.loadEnrolledPersons();
        }
    }

    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                
                // Update button states
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update content visibility
                tabContents.forEach(content => {
                    if (content.id === `${targetTab}-tab`) {
                        content.classList.add('active');
                    } else {
                        content.classList.remove('active');
                    }
                });
                
                this.currentTab = targetTab;
                
                // Refresh data when switching tabs
                if (targetTab === 'enrollment' && window.loadEnrolledPersons) {
                    window.loadEnrolledPersons();
                } else if (targetTab === 'reports' && window.fetchAttendanceData) {
                    window.fetchAttendanceData();
                }
            });
        });
    }

    setupMonitoring() {
        const toggleBtn = document.getElementById('toggleMonitoring');
        if (!toggleBtn) return;

        toggleBtn.addEventListener('click', async () => {
            if (!this.monitoringActive) {
                await this.startMonitoring();
            } else {
                await this.stopMonitoring();
            }
        });
    }

    async startMonitoring() {
        try {
            const response = await fetch('/api/attendance/start', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });

            if (response.ok) {
                this.monitoringActive = true;
                this.updateMonitoringUI(true);
                this.startVideoStream();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to start monitoring');
            }
        } catch (error) {
            console.error('Error starting monitoring:', error);
            Dialog.error('Failed to start attendance monitoring: ' + error.message);
        }
    }

    async stopMonitoring() {
        try {
            const response = await fetch('/api/attendance/stop', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });

            if (response.ok) {
                this.monitoringActive = false;
                this.updateMonitoringUI(false);
                this.stopVideoStream();
            }
        } catch (error) {
            console.error('Error stopping monitoring:', error);
            Dialog.error('Failed to stop monitoring: ' + error.message);
        }
    }

    updateMonitoringUI(active) {
        const toggleBtn = document.getElementById('toggleMonitoring');
        const statusIndicator = document.getElementById('statusIndicator');
        const systemStatus = document.getElementById('systemStatus');
        const systemStatusBadge = document.getElementById('systemStatusBadge');
        const videoOverlay = document.querySelector('.video-overlay');

        if (active) {
            if (toggleBtn) {
                toggleBtn.textContent = '⏸ Stop Monitoring';
                toggleBtn.classList.remove('btn-success');
                toggleBtn.classList.add('btn-danger');
            }
            if (statusIndicator) statusIndicator.textContent = '● Active';
            if (systemStatus) systemStatus.textContent = 'Active';
            if (systemStatusBadge) systemStatusBadge.textContent = '●';
            if (systemStatusBadge) systemStatusBadge.style.color = '#10b981';
            if (videoOverlay) videoOverlay.classList.add('hidden');
        } else {
            if (toggleBtn) {
                toggleBtn.textContent = '▶ Start Monitoring';
                toggleBtn.classList.remove('btn-danger');
                toggleBtn.classList.add('btn-success');
            }
            if (statusIndicator) statusIndicator.textContent = '● Inactive';
            if (systemStatus) systemStatus.textContent = 'Stopped';
            if (systemStatusBadge) systemStatusBadge.textContent = '●';
            if (systemStatusBadge) systemStatusBadge.style.color = '#ef4444';
            if (videoOverlay) videoOverlay.classList.remove('hidden');
        }
    }

    startVideoStream() {
        const videoElement = document.getElementById('videoStream');
        if (!videoElement) return;

        const token = localStorage.getItem('access_token');
        videoElement.src = `/api/attendance/stream?token=${token}&t=${Date.now()}`;
        videoElement.style.display = 'block';
    }

    stopVideoStream() {
        const videoElement = document.getElementById('videoStream');
        if (!videoElement) return;

        videoElement.src = '';
        videoElement.style.display = 'none';
    }

    async loadStats() {
        try {
            const response = await fetch('/api/attendance/today-summary', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateStats(data);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateStats(data) {
        this.stats = {
            today: data.total_today || 0,
            students: data.students_today || 0,
            staff: data.staff_today || 0
        };

        // Update UI
        const todayCount = document.getElementById('todayCount');
        const studentCount = document.getElementById('studentCount');
        const staffCount = document.getElementById('staffCount');

        if (todayCount) todayCount.textContent = this.stats.today;
        if (studentCount) studentCount.textContent = this.stats.students;
        if (staffCount) staffCount.textContent = this.stats.staff;
    }

    setupLogout() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            });
        }
    }

    // Refresh stats periodically
    startStatsRefresh() {
        setInterval(() => {
            if (this.monitoringActive) {
                this.loadStats();
            }
        }, 30000); // Every 30 seconds
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new DashboardManager();
    dashboard.startStatsRefresh();
    
    // Make dashboard accessible globally for other modules
    window.dashboard = dashboard;
});

// Utility function to format time
function formatTime(timeString) {
    if (!timeString) return '-';
    const date = new Date(timeString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

// Utility function to format date
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// Export utilities
window.formatTime = formatTime;
window.formatDate = formatDate;
