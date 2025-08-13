/**
 * Application Manager for Arxos Platform
 * Coordinates all components and handles global application state
 */

class AppManager {
    constructor() {
        this.currentPage = null;
        this.currentCanvas = null;
        this.isInitialized = false;
        this.init();
    }

    async init() {
        try {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                await new Promise(resolve => {
                    document.addEventListener('DOMContentLoaded', resolve);
                });
            }

            // Initialize managers
            this.initializeManagers();

            // Setup global event listeners
            this.setupGlobalEventListeners();

            // Setup HTMX interceptors
            this.setupHTMXInterceptors();

            // Setup keyboard shortcuts
            this.setupKeyboardShortcuts();

            this.isInitialized = true;
            console.log('✅ Arxos Application initialized successfully');

        } catch (error) {
            console.error('❌ Failed to initialize Arxos Application:', error);
            window.toastManager.error('Failed to initialize application');
        }
    }

    initializeManagers() {
        // Initialize auth manager
        if (!window.authManager) {
            window.authManager = new AuthManager();
        }

        // Initialize WebSocket manager
        if (!window.wsManager) {
            window.wsManager = new WebSocketManager();
        }

        // Initialize toast manager
        if (!window.toastManager) {
            window.toastManager = new ToastManager();
        }

        // Setup auth interceptor
        window.authManager.setupHTMXInterceptor();
    }

    setupGlobalEventListeners() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });

        // Handle beforeunload
        window.addEventListener('beforeunload', (event) => {
            this.handlePageUnload(event);
        });

        // Handle online/offline status
        window.addEventListener('online', () => {
            window.toastManager.success('Connection restored');
        });

        window.addEventListener('offline', () => {
            window.toastManager.warning('Connection lost. Some features may be unavailable.');
        });

        // Handle resize events
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    setupHTMXInterceptors() {
        // Add loading indicators
        document.body.addEventListener('htmx:beforeRequest', (event) => {
            this.showLoadingIndicator();
        });

        document.body.addEventListener('htmx:afterRequest', (event) => {
            this.hideLoadingIndicator();
        });

        // Handle HTMX errors
        document.body.addEventListener('htmx:responseError', (event) => {
            this.handleHTMXError(event);
        });

        // Handle successful swaps
        document.body.addEventListener('htmx:afterSwap', (event) => {
            this.handleHTMXSwap(event);
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Only handle shortcuts when not in input fields
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                return;
            }

            // Ctrl/Cmd + S for save
            if ((event.ctrlKey || event.metaKey) && event.key === 's') {
                event.preventDefault();
                this.handleSave();
            }

            // Ctrl/Cmd + Z for undo
            if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
                event.preventDefault();
                this.handleUndo();
            }

            // Ctrl/Cmd + Y for redo
            if ((event.ctrlKey || event.metaKey) && event.key === 'y') {
                event.preventDefault();
                this.handleRedo();
            }

            // Escape to close modals/panels
            if (event.key === 'Escape') {
                this.handleEscape();
            }

            // F1 for help
            if (event.key === 'F1') {
                event.preventDefault();
                this.showHelp();
            }
        });
    }

    // Page lifecycle handlers
    handlePageHidden() {
        // Pause real-time updates when page is hidden
        if (window.wsManager && window.wsManager.isConnected) {
            window.wsManager.sendUserActivity('page_hidden');
        }
    }

    handlePageVisible() {
        // Resume real-time updates when page becomes visible
        if (window.wsManager && window.wsManager.isConnected) {
            window.wsManager.sendUserActivity('page_visible');
        }
    }

    handlePageUnload(event) {
        // Warn user if there are unsaved changes
        if (this.hasUnsavedChanges()) {
            event.preventDefault();
            event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return event.returnValue;
        }

        // Clean up WebSocket connection
        if (window.wsManager) {
            window.wsManager.disconnect();
        }
    }

    handleResize() {
        // Notify canvas manager of resize
        if (window.canvasManager) {
            window.canvasManager.handleResize();
        }
    }

    // HTMX event handlers
    showLoadingIndicator() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    hideLoadingIndicator() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    handleHTMXError(event) {
        const status = event.detail.xhr.status;
        const response = event.detail.xhr.responseText;

        switch (status) {
            case 401:
                window.authManager.logout();
                break;
            case 403:
                window.toastManager.error('Access denied');
                break;
            case 404:
                window.toastManager.error('Resource not found');
                break;
            case 500:
                window.toastManager.error('Server error occurred');
                break;
            default:
                window.toastManager.error('Request failed');
        }

        console.error('HTMX Error:', status, response);
    }

    handleHTMXSwap(event) {
        // Update current page tracking
        const newPath = event.detail.pathInfo.requestPath;
        this.currentPage = newPath;

        // Initialize page-specific functionality
        this.initializePageFeatures();

        // Update browser history
        if (newPath !== window.location.pathname) {
            window.history.pushState({}, '', newPath);
        }
    }

    // Keyboard shortcut handlers
    handleSave() {
        if (window.canvasManager) {
            window.canvasManager.save();
        } else {
            window.toastManager.info('No active canvas to save');
        }
    }

    handleUndo() {
        if (window.canvasManager) {
            window.canvasManager.undo();
        }
    }

    handleRedo() {
        if (window.canvasManager) {
            window.canvasManager.redo();
        }
    }

    handleEscape() {
        // Close any open modals or panels
        const modals = document.querySelectorAll('.modal, .panel');
        modals.forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
            }
        });

        // Clear selections
        if (window.canvasManager) {
            window.canvasManager.clearSelection();
        }
    }

    showHelp() {
        window.toastManager.info('Press F1 again to close help');
        // TODO: Implement help system
    }

    // Canvas management
    setCurrentCanvas(canvasId) {
        this.currentCanvas = canvasId;

        // Connect WebSocket for canvas
        if (window.wsManager && canvasId) {
            const sessionId = `session_${Date.now()}_${window.authManager?.user?.user_id}`;
            window.wsManager.connect(canvasId, sessionId);
        }
    }

    getCurrentCanvas() {
        return this.currentCanvas;
    }

    // Page feature initialization
    initializePageFeatures() {
        const path = window.location.pathname;

        if (path.includes('/canvas/')) {
            this.initializeCanvasPage();
        } else if (path.includes('/dashboard')) {
            this.initializeDashboardPage();
        } else if (path.includes('/settings')) {
            this.initializeSettingsPage();
        }
    }

    initializeCanvasPage() {
        // Initialize canvas-specific features
        if (!window.canvasManager) {
            const canvasId = this.extractCanvasId();
            if (canvasId) {
                this.setCurrentCanvas(canvasId);
                // Canvas manager will be initialized by the canvas page
            }
        }
    }

    initializeDashboardPage() {
        // Initialize dashboard-specific features
        this.loadDashboardData();
    }

    initializeSettingsPage() {
        // Initialize settings-specific features
        this.loadUserSettings();
    }

    // Utility methods
    extractCanvasId() {
        const match = window.location.pathname.match(/\/canvas\/([^\/]+)/);
        return match ? match[1] : null;
    }

    hasUnsavedChanges() {
        // Check if there are unsaved changes
        if (window.canvasManager) {
            return window.canvasManager.hasUnsavedChanges();
        }
        return false;
    }

    loadDashboardData() {
        // Load dashboard data via HTMX
        htmx.ajax('GET', '/api/dashboard/data', {
            target: '#dashboard-content',
            swap: 'innerHTML'
        });
    }

    loadUserSettings() {
        // Load user settings via HTMX
        htmx.ajax('GET', '/api/user/settings', {
            target: '#settings-content',
            swap: 'innerHTML'
        });
    }

    // Navigation helpers
    navigateTo(path) {
        htmx.ajax('GET', path, {
            target: '#main-content',
            swap: 'innerHTML'
        });
    }

    // Error handling
    handleError(error, context = '') {
        console.error(`Error in ${context}:`, error);
        window.toastManager.error(`An error occurred: ${error.message}`);
    }

    // Performance monitoring
    startPerformanceMonitoring() {
        // Monitor page load times
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
        });

        // Monitor HTMX request times
        document.body.addEventListener('htmx:beforeRequest', (event) => {
            event.detail.startTime = performance.now();
        });

        document.body.addEventListener('htmx:afterRequest', (event) => {
            const duration = performance.now() - event.detail.startTime;
            console.log(`HTMX request completed in ${duration.toFixed(2)}ms`);
        });
    }

    // Debug helpers
    getDebugInfo() {
        return {
            currentPage: this.currentPage,
            currentCanvas: this.currentCanvas,
            isInitialized: this.isInitialized,
            authStatus: window.authManager?.isAuthenticated,
            wsStatus: window.wsManager?.getConnectionStatus(),
            userAgent: navigator.userAgent,
            screenSize: `${window.innerWidth}x${window.innerHeight}`
        };
    }
}

// Export for global use
window.AppManager = AppManager;
