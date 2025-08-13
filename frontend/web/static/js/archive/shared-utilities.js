/**
 * Shared Utilities for Arxos Web Frontend
 * Consolidates common functionality used across multiple modules
 */

class SharedUtilities {
    constructor(options = {}) {
        this.options = {
            enableNotifications: true,
            notificationDuration: 5000,
            maxFileSize: 50 * 1024 * 1024, // 50MB
            supportedFormats: ['json', 'svg', 'zip', 'pdf'],
            ...options
        };

        this.notificationQueue = [];
        this.isProcessingNotifications = false;

        this.initializeNotificationSystem();
    }

    // ===== FILE OPERATIONS =====

    /**
     * Read file as text
     */
    async readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    /**
     * Read file as ArrayBuffer
     */
    async readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Get file extension from filename
     */
    getFileExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    }

    /**
     * Validate file type
     */
    validateFileType(file, allowedTypes = this.options.supportedFormats) {
        const extension = this.getFileExtension(file.name);
        return allowedTypes.includes(extension);
    }

    /**
     * Validate file size
     */
    validateFileSize(file, maxSize = this.options.maxFileSize) {
        return file.size <= maxSize;
    }

    // ===== DOWNLOAD/EXPORT UTILITIES =====

    /**
     * Download file with data
     */
    async downloadFile(data, filename, mimeType = 'application/octet-stream') {
        const blob = new Blob([data], { type: mimeType });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
    }

    /**
     * Download JSON data
     */
    async downloadJSON(data, filename) {
        const jsonString = JSON.stringify(data, null, 2);
        await this.downloadFile(jsonString, filename, 'application/json');
    }

    /**
     * Download SVG data
     */
    async downloadSVG(svgContent, filename) {
        await this.downloadFile(svgContent, filename, 'image/svg+xml');
    }

    /**
     * Download ZIP data
     */
    async downloadZIP(zipData, filename) {
        await this.downloadFile(zipData, filename, 'application/zip');
    }

    // ===== NOTIFICATION SYSTEM =====

    /**
     * Initialize notification system
     */
    initializeNotificationSystem() {
        if (!this.options.enableNotifications) return;

        // Create notification container if it doesn't exist
        let container = document.getElementById('shared-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'shared-notifications';
            container.className = 'shared-notifications-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }

        this.notificationContainer = container;
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = this.options.notificationDuration) {
        if (!this.options.enableNotifications) {
            console.log(`[${type.toUpperCase()}] ${message}`);
            return;
        }

        const notification = this.createNotificationElement(message, type);
        this.notificationContainer.appendChild(notification);

        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);

        return notification;
    }

    /**
     * Create notification element
     */
    createNotificationElement(message, type) {
        const notification = document.createElement('div');
        notification.className = `shared-notification shared-notification-${type}`;
        notification.style.cssText = `
            background: ${this.getNotificationColor(type)};
            color: white;
            padding: 12px 16px;
            margin-bottom: 8px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            font-size: 14px;
            line-height: 1.4;
            max-width: 100%;
            word-wrap: break-word;
            animation: slideInRight 0.3s ease-out;
        `;

        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <span>${this.escapeHtml(message)}</span>
                <button onclick="this.parentElement.parentElement.remove()"
                        style="background: none; border: none; color: white; cursor: pointer; margin-left: 8px; font-size: 16px;">
                    ×
                </button>
            </div>
        `;

        return notification;
    }

    /**
     * Get notification color based on type
     */
    getNotificationColor(type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        return colors[type] || colors.info;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== VALIDATION UTILITIES =====

    /**
     * Validate email format
     */
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Validate required fields
     */
    validateRequiredFields(data, requiredFields) {
        const missing = [];
        for (const field of requiredFields) {
            if (!data[field] || data[field].toString().trim() === '') {
                missing.push(field);
            }
        }
        return missing;
    }

    // ===== STRING UTILITIES =====

    /**
     * Generate random string
     */
    generateRandomString(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Format date
     */
    formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }

    // ===== ERROR HANDLING =====

    /**
     * Handle errors consistently
     */
    handleError(error, context = '') {
        const errorMessage = error.message || error.toString();
        console.error(`[${context}] Error:`, error);
        this.showNotification(`Error: ${errorMessage}`, 'error');
        return { success: false, error: errorMessage };
    }

    /**
     * Retry operation with exponential backoff
     */
    async retryOperation(operation, maxRetries = 3, baseDelay = 1000) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                if (attempt === maxRetries) {
                    throw error;
                }

                const delay = baseDelay * Math.pow(2, attempt - 1);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    // ===== PERFORMANCE UTILITIES =====

    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function calls
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Create global instance
window.sharedUtilities = new SharedUtilities();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SharedUtilities;
}
