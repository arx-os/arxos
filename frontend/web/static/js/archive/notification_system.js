// Notification System for Floor Version Control
class NotificationSystem {
    constructor(options = {}) {
        this.options = {
            position: 'top-right', // top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
            maxNotifications: 5,
            autoClose: true,
            autoCloseDelay: 5000,
            showProgress: true,
            showIcons: true,
            showCloseButton: true,
            animationDuration: 300,
            ...options
        };

        this.notifications = [];
        this.container = null;
        this.init();
    }

    // Initialize the notification system
    init() {
        this.createContainer();
        this.setupGlobalStyles();
    }

    // Create notification container
    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = `notification-container fixed z-50 ${this.getPositionClasses()}`;
        this.container.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 20px;
            pointer-events: none;
        `;

        document.body.appendChild(this.container);
    }

    // Get position classes
    getPositionClasses() {
        const positions = {
            'top-right': 'top-0 right-0',
            'top-left': 'top-0 left-0',
            'bottom-right': 'bottom-0 right-0',
            'bottom-left': 'bottom-0 left-0',
            'top-center': 'top-0 left-1/2 transform -translate-x-1/2',
            'bottom-center': 'bottom-0 left-1/2 transform -translate-x-1/2'
        };
        return positions[this.options.position] || positions['top-right'];
    }

    // Setup global styles
    setupGlobalStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .notification {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                padding: 16px;
                margin-bottom: 8px;
                min-width: 300px;
                max-width: 400px;
                pointer-events: auto;
                position: relative;
                overflow: hidden;
                animation: slideIn 0.3s ease-out;
            }

            .notification.success {
                border-left: 4px solid #10b981;
            }

            .notification.error {
                border-left: 4px solid #ef4444;
            }

            .notification.warning {
                border-left: 4px solid #f59e0b;
            }

            .notification.info {
                border-left: 4px solid #3b82f6;
            }

            .notification.processing {
                border-left: 4px solid #8b5cf6;
            }

            .notification-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }

            .notification-title {
                font-weight: 600;
                font-size: 14px;
                color: #1f2937;
                display: flex;
                align-items: center;
            }

            .notification-icon {
                margin-right: 8px;
                font-size: 16px;
            }

            .notification-close {
                background: none;
                border: none;
                color: #6b7280;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                transition: all 0.2s;
            }

            .notification-close:hover {
                background: #f3f4f6;
                color: #374151;
            }

            .notification-message {
                font-size: 13px;
                color: #6b7280;
                line-height: 1.4;
                margin-bottom: 8px;
            }

            .notification-progress {
                height: 3px;
                background: #e5e7eb;
                border-radius: 2px;
                overflow: hidden;
                margin-top: 8px;
            }

            .notification-progress-bar {
                height: 100%;
                background: #3b82f6;
                transition: width 0.1s linear;
            }

            .notification-actions {
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }

            .notification-btn {
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
            }

            .notification-btn.primary {
                background: #3b82f6;
                color: white;
            }

            .notification-btn.primary:hover {
                background: #2563eb;
            }

            .notification-btn.secondary {
                background: #f3f4f6;
                color: #374151;
            }

            .notification-btn.secondary:hover {
                background: #e5e7eb;
            }

            .notification-btn.danger {
                background: #ef4444;
                color: white;
            }

            .notification-btn.danger:hover {
                background: #dc2626;
            }

            .notification.loading .notification-icon {
                animation: spin 1s linear infinite;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }

            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }

            .notification.removing {
                animation: slideOut 0.3s ease-in forwards;
            }
        `;

        document.head.appendChild(style);
    }

    // Show notification
    show(options) {
        const notification = {
            id: this.generateId(),
            type: options.type || 'info',
            title: options.title || '',
            message: options.message || '',
            duration: options.duration || this.options.autoCloseDelay,
            actions: options.actions || [],
            onClose: options.onClose || null,
            onAction: options.onAction || null,
            progress: 100,
            element: null
        };

        this.notifications.push(notification);
        this.renderNotification(notification);
        this.manageNotifications();

        if (this.options.autoClose && notification.duration > 0) {
            this.startAutoClose(notification);
        }

        return notification.id;
    }

    // Render notification
    renderNotification(notification) {
        const element = document.createElement('div');
        element.className = `notification ${notification.type}`;
        element.dataset.notificationId = notification.id;

        const icon = this.getIcon(notification.type);
        const actions = this.renderActions(notification);

        element.innerHTML = `
            <div class="notification-header">
                <div class="notification-title">
                    ${this.options.showIcons ? `<i class="fas ${icon} notification-icon"></i>` : ''}
                    ${notification.title}
                </div>
                ${this.options.showCloseButton ? `
                    <button class="notification-close" onclick="notificationSystem.close('${notification.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                ` : ''}
            </div>
            <div class="notification-message">${notification.message}</div>
            ${this.options.showProgress ? `
                <div class="notification-progress">
                    <div class="notification-progress-bar" style="width: ${notification.progress}%"></div>
                </div>
            ` : ''}
            ${actions}
        `;

        notification.element = element;
        this.container.appendChild(element);
    }

    // Render actions
    renderActions(notification) {
        if (!notification.actions || notification.actions.length === 0) {
            return '';
        }

        const actionsHtml = notification.actions.map(action => `
            <button class="notification-btn ${action.type || 'secondary'}"
                    onclick="notificationSystem.handleAction('${notification.id}', '${action.key}')">
                ${action.label}
            </button>
        `).join('');

        return `<div class="notification-actions">${actionsHtml}</div>`;
    }

    // Get icon for notification type
    getIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle',
            'processing': 'fa-spinner'
        };
        return icons[type] || icons['info'];
    }

    // Start auto close
    startAutoClose(notification) {
        const startTime = Date.now();
        const duration = notification.duration;

        const updateProgress = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.max(0, 100 - (elapsed / duration) * 100);

            notification.progress = progress;

            if (notification.element) {
                const progressBar = notification.element.querySelector('.notification-progress-bar');
                if (progressBar) {
                    progressBar.style.width = `${progress}%`;
                }
            }

            if (progress > 0) {
                requestAnimationFrame(updateProgress);
            } else {
                this.close(notification.id);
            }
        };

        requestAnimationFrame(updateProgress);
    }

    // Close notification
    close(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;

        if (notification.element) {
            notification.element.classList.add('removing');

            setTimeout(() => {
                if (notification.element && notification.element.parentElement) {
                    notification.element.parentElement.removeChild(notification.element);
                }
            }, this.options.animationDuration);
        }

        this.notifications = this.notifications.filter(n => n.id !== id);

        if (notification.onClose) {
            notification.onClose();
        }
    }

    // Handle action
    handleAction(notificationId, actionKey) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification || !notification.onAction) return;

        notification.onAction(actionKey);
    }

    // Manage notifications (limit number)
    manageNotifications() {
        if (this.notifications.length > this.options.maxNotifications) {
            const oldestNotification = this.notifications[0];
            this.close(oldestNotification.id);
        }
    }

    // Generate unique ID
    generateId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Success notification
    success(title, message, options = {}) {
        return this.show({
            type: 'success',
            title,
            message,
            ...options
        });
    }

    // Error notification
    error(title, message, options = {}) {
        return this.show({
            type: 'error',
            title,
            message,
            ...options
        });
    }

    // Warning notification
    warning(title, message, options = {}) {
        return this.show({
            type: 'warning',
            title,
            message,
            ...options
        });
    }

    // Info notification
    info(title, message, options = {}) {
        return this.show({
            type: 'info',
            title,
            message,
            ...options
        });
    }

    // Processing notification
    processing(title, message, options = {}) {
        return this.show({
            type: 'processing',
            title,
            message,
            duration: 0, // Don't auto-close processing notifications
            ...options
        });
    }

    // Update processing notification
    updateProcessing(id, title, message, progress = null) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification || !notification.element) return;

        if (title) {
            const titleElement = notification.element.querySelector('.notification-title');
            if (titleElement) {
                titleElement.innerHTML = `
                    ${this.options.showIcons ? `<i class="fas ${this.getIcon('processing')} notification-icon"></i>` : ''}
                    ${title}
                `;
            }
        }

        if (message) {
            const messageElement = notification.element.querySelector('.notification-message');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }

        if (progress !== null) {
            notification.progress = progress;
            const progressBar = notification.element.querySelector('.notification-progress-bar');
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
        }
    }

    // Complete processing notification
    completeProcessing(id, type = 'success', title = null, message = null) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;

        // Update the notification
        if (notification.element) {
            notification.element.className = `notification ${type}`;

            const icon = this.getIcon(type);
            const titleElement = notification.element.querySelector('.notification-title');
            if (titleElement && title) {
                titleElement.innerHTML = `
                    ${this.options.showIcons ? `<i class="fas ${icon} notification-icon"></i>` : ''}
                    ${title}
                `;
            }

            if (message) {
                const messageElement = notification.element.querySelector('.notification-message');
                if (messageElement) {
                    messageElement.textContent = message;
                }
            }
        }

        // Auto-close after a short delay
        setTimeout(() => {
            this.close(id);
        }, 2000);
    }

    // Clear all notifications
    clear() {
        this.notifications.forEach(notification => {
            this.close(notification.id);
        });
    }

    // Get notification count
    getCount() {
        return this.notifications.length;
    }

    // Destroy the notification system
    destroy() {
        this.clear();
        if (this.container && this.container.parentElement) {
            this.container.parentElement.removeChild(this.container);
        }
    }
}

// Initialize global notification system
const notificationSystem = new NotificationSystem();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}
