/**
 * Toast Notification Manager for Arxos Platform
 * Provides user feedback for actions and events
 */

class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        this.toasts = new Map();
        this.nextId = 1;
    }

    show(message, type = 'info', duration = 4000) {
        const toastId = this.nextId++;
        const toast = this.createToast(toastId, message, type);
        
        this.container.appendChild(toast);
        this.toasts.set(toastId, toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        });

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toastId);
            }, duration);
        }

        return toastId;
    }

    createToast(id, message, type) {
        const colors = {
            success: {
                bg: 'bg-green-500',
                icon: '✓',
                iconColor: 'text-green-100'
            },
            error: {
                bg: 'bg-red-500',
                icon: '✕',
                iconColor: 'text-red-100'
            },
            warning: {
                bg: 'bg-yellow-500',
                icon: '⚠',
                iconColor: 'text-yellow-100'
            },
            info: {
                bg: 'bg-blue-500',
                icon: 'ℹ',
                iconColor: 'text-blue-100'
            }
        };

        const config = colors[type] || colors.info;

        const toast = document.createElement('div');
        toast.id = `toast-${id}`;
        toast.className = `${config.bg} text-white px-6 py-4 rounded-lg shadow-lg mb-2 transform transition-all duration-300 translate-x-full opacity-0 max-w-sm`;
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <span class="${config.iconColor} text-lg">${config.icon}</span>
                    <span class="text-sm">${this.escapeHtml(message)}</span>
                </div>
                <button onclick="window.toastManager.remove(${id})" 
                        class="ml-4 text-white hover:text-gray-200 transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;

        return toast;
    }

    remove(toastId) {
        const toast = this.toasts.get(toastId);
        if (toast) {
            toast.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
                this.toasts.delete(toastId);
            }, 300);
        }
    }

    removeAll() {
        this.toasts.forEach((toast, id) => {
            this.remove(id);
        });
    }

    // Utility methods
    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 4000) {
        return this.show(message, 'info', duration);
    }

    // Progress toast for long-running operations
    showProgress(message, progressCallback) {
        const toastId = this.show(message, 'info', 0); // No auto-remove
        
        const updateProgress = (progress) => {
            const toast = this.toasts.get(toastId);
            if (toast) {
                const progressBar = toast.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = `${progress}%`;
                }
            }
        };

        // Add progress bar to toast
        const toast = this.toasts.get(toastId);
        if (toast) {
            const progressContainer = document.createElement('div');
            progressContainer.className = 'mt-2 bg-white bg-opacity-20 rounded-full h-2';
            progressContainer.innerHTML = '<div class="progress-bar bg-white h-2 rounded-full transition-all duration-300" style="width: 0%"></div>';
            toast.querySelector('.flex').appendChild(progressContainer);
        }

        return {
            update: updateProgress,
            complete: (finalMessage) => {
                this.remove(toastId);
                if (finalMessage) {
                    this.success(finalMessage);
                }
            },
            error: (errorMessage) => {
                this.remove(toastId);
                this.error(errorMessage);
            }
        };
    }

    // Confirmation toast
    confirm(message, onConfirm, onCancel) {
        const toastId = this.show(message, 'info', 0);
        const toast = this.toasts.get(toastId);
        
        if (toast) {
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'mt-3 flex space-x-2';
            buttonContainer.innerHTML = `
                <button onclick="window.toastManager.handleConfirm(${toastId}, true)" 
                        class="px-3 py-1 bg-white text-blue-600 rounded text-xs hover:bg-gray-100 transition-colors">
                    Confirm
                </button>
                <button onclick="window.toastManager.handleConfirm(${toastId}, false)" 
                        class="px-3 py-1 bg-gray-200 text-gray-700 rounded text-xs hover:bg-gray-300 transition-colors">
                    Cancel
                </button>
            `;
            toast.querySelector('.flex').appendChild(buttonContainer);
        }

        // Store callbacks
        this.confirmCallbacks = this.confirmCallbacks || new Map();
        this.confirmCallbacks.set(toastId, { onConfirm, onCancel });

        return toastId;
    }

    handleConfirm(toastId, confirmed) {
        const callbacks = this.confirmCallbacks?.get(toastId);
        if (callbacks) {
            if (confirmed && callbacks.onConfirm) {
                callbacks.onConfirm();
            } else if (!confirmed && callbacks.onCancel) {
                callbacks.onCancel();
            }
            this.confirmCallbacks.delete(toastId);
        }
        this.remove(toastId);
    }

    // Escape HTML to prevent XSS
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Toast positioning
    setPosition(position = 'top-right') {
        const positions = {
            'top-right': 'fixed top-4 right-4',
            'top-left': 'fixed top-4 left-4',
            'bottom-right': 'fixed bottom-4 right-4',
            'bottom-left': 'fixed bottom-4 left-4',
            'top-center': 'fixed top-4 left-1/2 transform -translate-x-1/2',
            'bottom-center': 'fixed bottom-4 left-1/2 transform -translate-x-1/2'
        };

        this.container.className = `${positions[position]} z-50 space-y-2`;
    }

    // Toast stacking
    setMaxToasts(max = 5) {
        this.maxToasts = max;
    }

    // Auto-remove oldest toast when limit reached
    enforceMaxToasts() {
        if (this.maxToasts && this.toasts.size > this.maxToasts) {
            const oldestId = this.toasts.keys().next().value;
            this.remove(oldestId);
        }
    }
}

// Export for global use
window.ToastManager = ToastManager; 