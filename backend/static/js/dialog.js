/**
 * Custom Dialog System - Replaces browser alerts
 */

const Dialog = {
    overlay: null,
    okBtn: null,
    cancelBtn: null,
    resolvePromise: null,
    
    init() {
        this.overlay = document.getElementById('customDialog');
        this.okBtn = document.getElementById('dialogOkBtn');
        this.cancelBtn = document.getElementById('dialogCancelBtn');
        
        this.okBtn.addEventListener('click', () => this.handleOk());
        this.cancelBtn.addEventListener('click', () => this.handleCancel());
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) this.handleCancel();
        });
    },
    
    show(options) {
        const {
            title = 'Notification',
            message = '',
            type = 'info', // info, success, error, warning, confirm
            showCancel = false
        } = options;
        
        return new Promise((resolve) => {
            this.resolvePromise = resolve;
            
            document.getElementById('dialogTitle').textContent = title;
            document.getElementById('dialogMessage').textContent = message;
            
            // Set icon based on type
            const iconElement = document.getElementById('dialogIcon');
            const icons = {
                info: 'ℹ️',
                success: '✅',
                error: '❌',
                warning: '⚠️',
                confirm: '❓'
            };
            iconElement.textContent = icons[type] || icons.info;
            
            // Show/hide cancel button
            this.cancelBtn.style.display = showCancel ? 'inline-block' : 'none';
            
            // Show dialog
            this.overlay.classList.add('show');
        });
    },
    
    handleOk() {
        this.overlay.classList.remove('show');
        if (this.resolvePromise) this.resolvePromise(true);
    },
    
    handleCancel() {
        this.overlay.classList.remove('show');
        if (this.resolvePromise) this.resolvePromise(false);
    },
    
    // Convenience methods
    alert(message, title = 'Notification') {
        return this.show({ title, message, type: 'info' });
    },
    
    success(message, title = 'Success') {
        return this.show({ title, message, type: 'success' });
    },
    
    error(message, title = 'Error') {
        return this.show({ title, message, type: 'error' });
    },
    
    warning(message, title = 'Warning') {
        return this.show({ title, message, type: 'warning' });
    },
    
    confirm(message, title = 'Confirm') {
        return this.show({ title, message, type: 'confirm', showCancel: true });
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Dialog.init());
} else {
    Dialog.init();
}

// Make globally available
window.Dialog = Dialog;
