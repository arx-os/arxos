/**
 * Conflicts Module
 * Handles conflict detection, resolution, and conflict management
 */

export class Conflicts {
    constructor(options = {}) {
        this.options = {
            conflictCheckInterval: options.conflictCheckInterval || 10000, // 10 seconds
            enableConflictResolution: options.enableConflictResolution !== false,
            autoResolveConflicts: options.autoResolveConflicts || false,
            conflictTimeout: options.conflictTimeout || 300000, // 5 minutes
            ...options
        };

        // Conflict state
        this.conflictQueue = [];
        this.activeConflicts = new Map();
        this.resolvedConflicts = new Map();
        this.isProcessing = false;

        // Timers
        this.conflictTimer = null;
        this.conflictTimeoutTimer = null;

        // UI elements
        this.conflictModal = null;
        this.conflictPanel = null;

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.startTimers();
        this.createUI();
    }

    setupEventListeners() {
        // Listen for conflict detection from realtime module
        document.addEventListener('conflictDetected', (event) => {
            this.handleConflictsDetected(event.detail);
        });

        // Listen for version control operations
        document.addEventListener('versionRestoreStarted', () => {
            this.handleVersionRestoreStarted();
        });

        document.addEventListener('versionRestoreCompleted', () => {
            this.handleVersionRestoreCompleted();
        });

        document.addEventListener('versionRestoreFailed', () => {
            this.handleVersionRestoreFailed();
        });
    }

    startTimers() {
        this.startConflictTimer();
    }

    startConflictTimer() {
        this.conflictTimer = setInterval(() => {
            this.checkForConflicts();
        }, this.options.conflictCheckInterval);
    }

    // Conflict detection methods
    async checkForConflicts() {
        if (this.isProcessing) return;

        try {
            this.isProcessing = true;

            // Get current floor and version
            const currentFloor = this.getCurrentFloor();
            if (!currentFloor) return;

            // Check for conflicts with server
            const response = await fetch(`/api/conflicts/check?floor_id=${currentFloor.id}`);

            if (!response.ok) {
                throw new Error('Failed to check for conflicts');
            }

            const conflicts = await response.json();

            if (conflicts.length > 0) {
                this.handleConflictsDetected(conflicts);
            }

        } catch (error) {
            console.error('Error checking for conflicts:', error);
            this.triggerEvent('conflictCheckFailed', { error });
        } finally {
            this.isProcessing = false;
        }
    }

    handleConflictsDetected(conflicts) {
        // Add conflicts to queue
        conflicts.forEach(conflict => {
            this.conflictQueue.push(conflict);
            this.activeConflicts.set(conflict.id, conflict);
        });

        // Start conflict timeout
        this.startConflictTimeout();

        // Show conflict modal if auto-resolve is disabled
        if (!this.options.autoResolveConflicts) {
            this.showConflictModal();
        } else {
            this.autoResolveConflicts();
        }

        this.triggerEvent('conflictsDetected', { conflicts });
    }

    // Conflict resolution methods
    async resolveConflicts() {
        if (this.conflictQueue.length === 0) return;

        try {
            this.isProcessing = true;

            const conflicts = [...this.conflictQueue];
            const resolutionStrategy = this.determineResolutionStrategy(conflicts);

            // Send resolution request to server
            const response = await fetch('/api/conflicts/resolve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    conflicts: conflicts,
                    strategy: resolutionStrategy
                })
            });

            if (!response.ok) {
                throw new Error('Failed to resolve conflicts');
            }

            const result = await response.json();

            // Mark conflicts as resolved
            conflicts.forEach(conflict => {
                this.resolvedConflicts.set(conflict.id, {
                    ...conflict,
                    resolvedAt: Date.now(),
                    strategy: resolutionStrategy
                });
                this.activeConflicts.delete(conflict.id);
            });

            // Clear queue
            this.conflictQueue = [];

            this.hideConflictModal();
            this.handleConflictsResolved(result);

        } catch (error) {
            console.error('Error resolving conflicts:', error);
            this.triggerEvent('conflictResolutionFailed', { error });
        } finally {
            this.isProcessing = false;
        }
    }

    autoResolveConflicts() {
        if (this.options.autoResolveConflicts) {
            this.resolveConflicts();
        }
    }

    ignoreConflicts() {
        // Mark conflicts as ignored
        this.conflictQueue.forEach(conflict => {
            this.resolvedConflicts.set(conflict.id, {
                ...conflict,
                resolvedAt: Date.now(),
                strategy: 'ignored'
            });
            this.activeConflicts.delete(conflict.id);
        });

        // Clear queue
        this.conflictQueue = [];

        this.hideConflictModal();
        this.triggerEvent('conflictsIgnored', { count: this.conflictQueue.length });
    }

    determineResolutionStrategy(conflicts) {
        // Analyze conflicts to determine best resolution strategy
        const strategies = {
            'latest_wins': 0,
            'merge': 0,
            'manual': 0
        };

        conflicts.forEach(conflict => {
            switch (conflict.type) {
                case 'object_modified':
                    strategies['latest_wins']++;
                    break;
                case 'object_deleted':
                    strategies['manual']++;
                    break;
                case 'object_added':
                    strategies['merge']++;
                    break;
                default:
                    strategies['manual']++;
            }
        });

        // Return the most common strategy
        return Object.entries(strategies).reduce((a, b) => a[1] > b[1] ? a : b)[0];
    }

    // Version control event handlers
    handleVersionRestoreStarted() {
        // Pause conflict checking during version restore
        this.pauseConflictChecking();
    }

    handleVersionRestoreCompleted() {
        // Resume conflict checking after version restore
        this.resumeConflictChecking();

        // Clear any existing conflicts
        this.clearConflicts();
    }

    handleVersionRestoreFailed() {
        // Resume conflict checking after failed version restore
        this.resumeConflictChecking();
    }

    // Conflict timeout handling
    startConflictTimeout() {
        if (this.conflictTimeoutTimer) {
            clearTimeout(this.conflictTimeoutTimer);
        }

        this.conflictTimeoutTimer = setTimeout(() => {
            this.handleConflictTimeout();
        }, this.options.conflictTimeout);
    }

    handleConflictTimeout() {
        console.warn('Conflict resolution timeout reached');
        this.triggerEvent('conflictTimeout', { conflicts: this.conflictQueue });

        // Auto-resolve or ignore based on settings
        if (this.options.autoResolveConflicts) {
            this.resolveConflicts();
        } else {
            this.ignoreConflicts();
        }
    }

    // Conflict checking control
    pauseConflictChecking() {
        if (this.conflictTimer) {
            clearInterval(this.conflictTimer);
            this.conflictTimer = null;
        }
    }

    resumeConflictChecking() {
        if (!this.conflictTimer) {
            this.startConflictTimer();
        }
    }

    // UI methods
    createUI() {
        this.createConflictModal();
        this.createConflictPanel();
    }

    createConflictModal() {
        this.conflictModal = document.createElement('div');
        this.conflictModal.id = 'conflict-modal';
        this.conflictModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        this.conflictModal.style.display = 'none';

        this.conflictModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-semibold text-gray-900">Conflicts Detected</h3>
                    <button id="close-conflict-modal" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="mb-4">
                    <p class="text-sm text-gray-600 mb-4">
                        Conflicts have been detected with the current version. How would you like to proceed?
                    </p>
                    <div id="conflict-details" class="text-xs text-gray-500 mb-4">
                        <!-- Conflict details will be populated here -->
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button id="resolve-conflicts" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
                        Resolve Conflicts
                    </button>
                    <button id="ignore-conflicts" class="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 text-sm">
                        Ignore
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.conflictModal);
        this.setupConflictModalEvents();
    }

    createConflictPanel() {
        this.conflictPanel = document.createElement('div');
        this.conflictPanel.id = 'conflict-panel';
        this.conflictPanel.className = 'fixed top-4 right-4 bg-red-100 border border-red-300 rounded-lg shadow-lg p-3 z-40';
        this.conflictPanel.style.display = 'none';

        this.conflictPanel.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                <span class="text-sm text-red-700">Conflicts detected</span>
                <button id="show-conflicts" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-exclamation-triangle"></i>
                </button>
            </div>
        `;

        document.body.appendChild(this.conflictPanel);
        this.setupConflictPanelEvents();
    }

    setupConflictModalEvents() {
        const closeButton = this.conflictModal.querySelector('#close-conflict-modal');
        const resolveButton = this.conflictModal.querySelector('#resolve-conflicts');
        const ignoreButton = this.conflictModal.querySelector('#ignore-conflicts');

        closeButton.addEventListener('click', () => {
            this.hideConflictModal();
        });

        resolveButton.addEventListener('click', () => {
            this.resolveConflicts();
        });

        ignoreButton.addEventListener('click', () => {
            this.ignoreConflicts();
        });
    }

    setupConflictPanelEvents() {
        const showButton = this.conflictPanel.querySelector('#show-conflicts');
        showButton.addEventListener('click', () => {
            this.showConflictModal();
        });
    }

    showConflictModal() {
        if (this.conflictModal) {
            this.updateConflictDetails();
            this.conflictModal.style.display = 'flex';
        }
    }

    hideConflictModal() {
        if (this.conflictModal) {
            this.conflictModal.style.display = 'none';
        }
    }

    updateConflictDetails() {
        const detailsElement = this.conflictModal.querySelector('#conflict-details');

        if (detailsElement && this.conflictQueue.length > 0) {
            const details = this.conflictQueue.map(conflict =>
                `${conflict.type}: ${conflict.description}`
            ).join('\n');

            detailsElement.textContent = details;
        }
    }

    updateConflictPanel() {
        if (this.conflictPanel) {
            const hasConflicts = this.conflictQueue.length > 0;
            this.conflictPanel.style.display = hasConflicts ? 'block' : 'none';

            if (hasConflicts) {
                const countElement = this.conflictPanel.querySelector('span');
                if (countElement) {
                    countElement.textContent = `${this.conflictQueue.length} conflict(s) detected`;
                }
            }
        }
    }

    // Conflict resolution result handling
    handleConflictsResolved(result) {
        this.triggerEvent('conflictsResolved', {
            result,
            resolvedCount: this.resolvedConflicts.size
        });

        // Update UI
        this.updateConflictPanel();

        // Show success notification
        this.showNotification('Conflicts resolved successfully', 'success');
    }

    // Utility methods
    getCurrentFloor() {
        // Get current floor from global state
        return window.currentFloor || null;
    }

    getActiveConflicts() {
        return Array.from(this.activeConflicts.values());
    }

    getResolvedConflicts() {
        return Array.from(this.resolvedConflicts.values());
    }

    getConflictCount() {
        return this.conflictQueue.length;
    }

    clearConflicts() {
        this.conflictQueue = [];
        this.activeConflicts.clear();
        this.resolvedConflicts.clear();
        this.updateConflictPanel();
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 bg-${type === 'success' ? 'green' : 'blue'}-600 text-white px-4 py-2 rounded-lg shadow-lg z-50`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Timer cleanup
    clearTimers() {
        if (this.conflictTimer) {
            clearInterval(this.conflictTimer);
            this.conflictTimer = null;
        }

        if (this.conflictTimeoutTimer) {
            clearTimeout(this.conflictTimeoutTimer);
            this.conflictTimeoutTimer = null;
        }
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, conflicts: this });
                } catch (error) {
                    console.error(`Error in conflicts event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.clearTimers();
        this.conflictQueue = [];
        this.activeConflicts.clear();
        this.resolvedConflicts.clear();

        if (this.conflictModal) {
            this.conflictModal.remove();
        }

        if (this.conflictPanel) {
            this.conflictPanel.remove();
        }

        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
