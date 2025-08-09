// BIM Editing Integration for Floor Version Control
class BIMEditingIntegration {
    constructor(options = {}) {
        this.options = {
            autoSnapshotEnabled: true,
            autoSnapshotInterval: 300000, // 5 minutes
            manualSnapshotPrompts: true,
            editTrackingEnabled: true,
            majorEditThreshold: 10, // Number of edits before considering "major"
            versionControlSystem: null,
            viewportManager: null,
            objectInteraction: null,
            ...options
        };

        this.editCount = 0;
        this.lastSnapshotTime = Date.now();
        this.pendingChanges = new Set();
        this.editHistory = [];
        this.isProcessing = false;
        this.autoSnapshotTimer = null;

        this.initializeIntegration();
    }

    // Initialize integration with existing systems
    initializeIntegration() {
        this.connectToViewportManager();
        this.connectToObjectInteraction();
        this.connectToVersionControl();
        this.setupEventListeners();
        this.startAutoSnapshotTimer();
    }

    // Connect to viewport manager
    connectToViewportManager() {
        const checkViewportManager = () => {
            if (window.viewportManager) {
                this.options.viewportManager = window.viewportManager;
                window.arxLogger.info('BIMEditingIntegration connected to ViewportManager', { file: 'bim_editing_integration.js' });

                // Listen for viewport changes that might indicate editing
                this.options.viewportManager.addEventListener('objectMoved', (data) => {
                    this.trackEdit('object_move', data);
                });

                this.options.viewportManager.addEventListener('objectSelected', (data) => {
                    this.trackEdit('object_select', data);
                });

                this.options.viewportManager.addEventListener('zoomChanged', (data) => {
                    this.trackEdit('viewport_zoom', data);
                });
            } else {
                setTimeout(checkViewportManager, 100);
            }
        };
        checkViewportManager();
    }

    // Connect to object interaction system
    connectToObjectInteraction() {
        const checkObjectInteraction = () => {
            if (window.svgObjectInteraction) {
                this.options.objectInteraction = window.svgObjectInteraction;
                window.arxLogger.info('BIMEditingIntegration connected to SVGObjectInteraction', { file: 'bim_editing_integration.js' });

                // Override object interaction methods to track edits
                this.overrideObjectInteractionMethods();
            } else {
                setTimeout(checkObjectInteraction, 100);
            }
        };
        checkObjectInteraction();
    }

    // Connect to version control system
    connectToVersionControl() {
        const checkVersionControl = () => {
            if (window.floorVersionControl) {
                this.options.versionControlSystem = window.floorVersionControl;
                window.arxLogger.info('BIMEditingIntegration connected to FloorVersionControl', { file: 'bim_editing_integration.js' });
            } else {
                setTimeout(checkVersionControl, 100);
            }
        };
        checkVersionControl();
    }

    // Override object interaction methods to track edits
    overrideObjectInteractionMethods() {
        const original = this.options.objectInteraction;

        // Override moveSelectedObjectsWithArrowKeys
        const originalMove = original.moveSelectedObjectsWithArrowKeys.bind(original);
        original.moveSelectedObjectsWithArrowKeys = (key) => {
            this.trackEdit('keyboard_move', { key, objects: original.selectedObjects });
            return originalMove(key);
        };

        // Override rotateSelectedObjects
        if (original.rotateSelectedObjects) {
            const originalRotate = original.rotateSelectedObjects.bind(original);
            original.rotateSelectedObjects = (angle) => {
                this.trackEdit('object_rotate', { angle, objects: original.selectedObjects });
                return originalRotate(angle);
            };
        }

        // Override scaleSelectedObjects
        if (original.scaleSelectedObjects) {
            const originalScale = original.scaleSelectedObjects.bind(original);
            original.scaleSelectedObjects = (scale) => {
                this.trackEdit('object_scale', { scale, objects: original.selectedObjects });
                return originalScale(scale);
            };
        }

        // Override deleteSelectedObjects
        if (original.deleteSelectedObjects) {
            const originalDelete = original.deleteSelectedObjects.bind(original);
            original.deleteSelectedObjects = () => {
                this.trackEdit('object_delete', { objects: original.selectedObjects });
                return originalDelete();
            };
        }
    }

    // Setup event listeners for edit tracking
    setupEventListeners() {
        // Listen for symbol placement
        document.addEventListener('symbolPlaced', (event) => {
            this.trackEdit('symbol_place', event.detail);
        });

        // Listen for object property changes
        document.addEventListener('objectPropertyChanged', (event) => {
            this.trackEdit('property_change', event.detail);
        });

        // Listen for object deletion
        document.addEventListener('objectDeleted', (event) => {
            this.trackEdit('object_delete', event.detail);
        });

        // Listen for object duplication
        document.addEventListener('objectDuplicated', (event) => {
            this.trackEdit('object_duplicate', event.detail);
        });

        // Listen for layer changes
        document.addEventListener('layerChanged', (event) => {
            this.trackEdit('layer_change', event.detail);
        });

        // Listen for viewport operations
        document.addEventListener('viewportOperation', (event) => {
            this.trackEdit('viewport_operation', event.detail);
        });

        // Listen for undo/redo operations
        document.addEventListener('undoOperation', (event) => {
            this.trackEdit('undo', event.detail);
        });

        document.addEventListener('redoOperation', (event) => {
            this.trackEdit('redo', event.detail);
        });

        // Listen for save operations
        document.addEventListener('saveOperation', (event) => {
            this.trackEdit('save', event.detail);
        });

        // Listen for export operations
        document.addEventListener('exportOperation', (event) => {
            this.trackEdit('export', event.detail);
        });
    }

    // Track an edit operation
    trackEdit(type, data) {
        if (!this.options.editTrackingEnabled) return;

        const edit = {
            id: this.generateEditId(),
            type: type,
            data: data,
            timestamp: Date.now(),
            user: this.getCurrentUser(),
            session: this.getCurrentSession()
        };

        this.editHistory.push(edit);
        this.editCount++;
        this.pendingChanges.add(edit.id);

        // Check if this is a major edit
        if (this.isMajorEdit(edit)) {
            window.arxLogger.info('Major edit detected:', edit, { file: 'bim_editing_integration.js' });
            this.handleMajorEdit(edit);
        }

        // Update UI indicators
        this.updateEditIndicators();

        // Trigger auto-snapshot if needed
        this.checkAutoSnapshot();

        // Emit edit tracked event
        this.emitEvent('editTracked', edit);
    }

    // Check if an edit is considered "major"
    isMajorEdit(edit) {
        const majorEditTypes = [
            'object_delete',
            'symbol_place',
            'property_change',
            'object_duplicate',
            'layer_change'
        ];

        return majorEditTypes.includes(edit.type);
    }

    // Handle major edit
    handleMajorEdit(edit) {
        console.log('Major edit detected:', edit);

        // Show visual feedback
        this.showMajorEditIndicator(edit);

        // Prompt for manual snapshot if enabled
        if (this.options.manualSnapshotPrompts) {
            this.promptForManualSnapshot(edit);
        }

        // Emit major edit event
        this.emitEvent('majorEditDetected', edit);
    }

    // Show major edit indicator
    showMajorEditIndicator(edit) {
        // Create or update major edit indicator
        let indicator = document.getElementById('major-edit-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'major-edit-indicator';
            indicator.className = 'fixed top-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
            indicator.innerHTML = `
                <div class="flex items-center space-x-2">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Major edit detected</span>
                    <button onclick="bimEditingIntegration.createManualSnapshot()" class="bg-white text-yellow-500 px-2 py-1 rounded text-sm">
                        Snapshot
                    </button>
                </div>
            `;
            document.body.appendChild(indicator);
        }

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (indicator && indicator.parentElement) {
                indicator.remove();
            }
        }, 5000);
    }

    // Prompt for manual snapshot
    promptForManualSnapshot(edit) {
        // Check if we should show the prompt (avoid spam)
        const lastPromptTime = this.lastPromptTime || 0;
        const timeSinceLastPrompt = Date.now() - lastPromptTime;

        if (timeSinceLastPrompt < 30000) { // Don't prompt more than once every 30 seconds
            return;
        }

        this.lastPromptTime = Date.now();

        // Create snapshot prompt
        const prompt = document.createElement('div');
        prompt.className = 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white border border-gray-300 rounded-lg shadow-xl p-6 z-50 max-w-md';
        prompt.innerHTML = `
            <div class="text-center">
                <i class="fas fa-camera text-3xl text-blue-500 mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Create Snapshot?</h3>
                <p class="text-gray-600 mb-4">
                    A major edit was detected. Would you like to create a snapshot to save your progress?
                </p>
                <div class="flex space-x-3">
                    <button onclick="bimEditingIntegration.createManualSnapshot()" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                        Create Snapshot
                    </button>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400">
                        Later
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(prompt);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (prompt && prompt.parentElement) {
                prompt.remove();
            }
        }, 10000);
    }

    // Start auto-snapshot timer
    startAutoSnapshotTimer() {
        if (!this.options.autoSnapshotEnabled) return;

        this.autoSnapshotTimer = setInterval(() => {
            this.checkAutoSnapshot();
        }, this.options.autoSnapshotInterval);
    }

    // Check if auto-snapshot should be triggered
    checkAutoSnapshot() {
        if (!this.options.autoSnapshotEnabled) return;

        const timeSinceLastSnapshot = Date.now() - this.lastSnapshotTime;
        const hasPendingChanges = this.pendingChanges.size > 0;

        if (timeSinceLastSnapshot >= this.options.autoSnapshotInterval && hasPendingChanges) {
            this.createAutoSnapshot();
        }
    }

    // Create auto-snapshot
    async createAutoSnapshot() {
        if (this.isProcessing) return;

        try {
            this.isProcessing = true;

            const description = `Auto-save snapshot (${this.editCount} edits)`;
            const tags = ['auto-save'];

            await this.createSnapshot(description, tags, 'auto-save');

            // Clear pending changes
            this.pendingChanges.clear();
            this.lastSnapshotTime = Date.now();

            window.arxLogger.info('Auto-snapshot created successfully', { file: 'bim_editing_integration.js' });

        } catch (error) {
            console.error('Failed to create auto-snapshot:', error);
        } finally {
            this.isProcessing = false;
        }
    }

    // Create manual snapshot
    async createManualSnapshot() {
        if (this.isProcessing) return;

        try {
            this.isProcessing = true;

            // Get user input for description
            const description = await this.promptForSnapshotDescription();
            if (!description) return; // User cancelled

            const tags = ['manual'];

            await this.createSnapshot(description, tags, 'manual');

            // Clear pending changes
            this.pendingChanges.clear();
            this.lastSnapshotTime = Date.now();

            window.arxLogger.info('Manual snapshot created successfully', { file: 'bim_editing_integration.js' });

        } catch (error) {
            console.error('Failed to create manual snapshot:', error);
        } finally {
            this.isProcessing = false;
        }
    }

    // Prompt for snapshot description
    promptForSnapshotDescription() {
        return new Promise((resolve) => {
            const prompt = document.createElement('div');
            prompt.className = 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white border border-gray-300 rounded-lg shadow-xl p-6 z-50 max-w-md';
            prompt.innerHTML = `
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Create Snapshot</h3>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                        <textarea id="snapshot-description" class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" rows="3" placeholder="Describe what changes this snapshot captures..."></textarea>
                    </div>
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Tags</label>
                        <input type="text" id="snapshot-tags" class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" placeholder="Enter tags separated by commas...">
                    </div>
                    <div class="flex space-x-3">
                        <button onclick="bimEditingIntegration.confirmSnapshot()" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                            Create
                        </button>
                        <button onclick="bimEditingIntegration.cancelSnapshot()" class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400">
                            Cancel
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(prompt);

            // Store prompt reference for confirmation
            this.currentSnapshotPrompt = prompt;
            this.currentSnapshotResolve = resolve;

            // Focus on description field
            setTimeout(() => {
                const descriptionField = prompt.querySelector('#snapshot-description');
                if (descriptionField) {
                    descriptionField.focus();
                }
            }, 100);
        });
    }

    // Confirm snapshot creation
    confirmSnapshot() {
        if (!this.currentSnapshotPrompt || !this.currentSnapshotResolve) return;

        const description = this.currentSnapshotPrompt.querySelector('#snapshot-description').value;
        const tags = this.currentSnapshotPrompt.querySelector('#snapshot-tags').value;

        this.currentSnapshotPrompt.remove();
        this.currentSnapshotPrompt = null;

        this.currentSnapshotResolve({
            description: description || 'Manual snapshot',
            tags: tags ? tags.split(',').map(tag => tag.trim()).filter(tag => tag) : []
        });

        this.currentSnapshotResolve = null;
    }

    // Cancel snapshot creation
    cancelSnapshot() {
        if (!this.currentSnapshotPrompt || !this.currentSnapshotResolve) return;

        this.currentSnapshotPrompt.remove();
        this.currentSnapshotPrompt = null;
        this.currentSnapshotResolve(null);
        this.currentSnapshotResolve = null;
    }

    // Create snapshot using version control system
    async createSnapshot(description, tags, type) {
        if (!this.options.versionControlSystem) {
            throw new Error('Version control system not available');
        }

        // Get current floor ID
        const floorId = this.getCurrentFloorId();
        if (!floorId) {
            throw new Error('No floor selected');
        }

        // Create snapshot using version control system
        await this.options.versionControlSystem.createSnapshot(description, tags, type);

        // Emit snapshot created event
        this.emitEvent('snapshotCreated', {
            description,
            tags,
            type,
            floorId,
            editCount: this.editCount
        });
    }

    // Update edit indicators in UI
    updateEditIndicators() {
        // Update edit counter if it exists
        const editCounter = document.getElementById('edit-counter');
        if (editCounter) {
            editCounter.textContent = this.editCount;
            editCounter.className = this.editCount > 0 ? 'text-orange-600' : 'text-gray-500';
        }

        // Update pending changes indicator
        const pendingIndicator = document.getElementById('pending-changes-indicator');
        if (pendingIndicator) {
            if (this.pendingChanges.size > 0) {
                pendingIndicator.style.display = 'block';
                pendingIndicator.textContent = `${this.pendingChanges.size} pending`;
            } else {
                pendingIndicator.style.display = 'none';
            }
        }

        // Update auto-save indicator
        const autoSaveIndicator = document.getElementById('auto-save-indicator');
        if (autoSaveIndicator) {
            const timeSinceLastSnapshot = Date.now() - this.lastSnapshotTime;
            const timeUntilNextSnapshot = Math.max(0, this.options.autoSnapshotInterval - timeSinceLastSnapshot);
            const minutes = Math.ceil(timeUntilNextSnapshot / 60000);

            autoSaveIndicator.textContent = `Auto-save in ${minutes}m`;
            autoSaveIndicator.className = timeUntilNextSnapshot < 60000 ? 'text-red-600' : 'text-gray-500';
        }
    }

    // Get current user
    getCurrentUser() {
        // This would typically come from your authentication system
        return {
            id: localStorage.getItem('user_id') || 'unknown',
            name: localStorage.getItem('user_name') || 'Unknown User'
        };
    }

    // Get current session
    getCurrentSession() {
        return {
            id: sessionStorage.getItem('session_id') || this.generateSessionId(),
            timestamp: Date.now()
        };
    }

    // Get current floor ID
    getCurrentFloorId() {
        // This would typically come from your floor selection system
        return localStorage.getItem('current_floor_id') ||
               document.querySelector('[data-floor-id]')?.dataset.floorId;
    }

    // Generate edit ID
    generateEditId() {
        return 'edit_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Generate session ID
    generateSessionId() {
        const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        sessionStorage.setItem('session_id', sessionId);
        return sessionId;
    }

    // Emit custom event
    emitEvent(eventName, data) {
        const event = new CustomEvent(eventName, {
            detail: data,
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    // Get edit statistics
    getEditStatistics() {
        return {
            totalEdits: this.editCount,
            pendingChanges: this.pendingChanges.size,
            editHistory: this.editHistory,
            lastSnapshotTime: this.lastSnapshotTime,
            timeSinceLastSnapshot: Date.now() - this.lastSnapshotTime
        };
    }

    // Reset edit tracking
    resetEditTracking() {
        this.editCount = 0;
        this.pendingChanges.clear();
        this.editHistory = [];
        this.lastSnapshotTime = Date.now();
        this.updateEditIndicators();
    }

    // Enable/disable auto-snapshot
    setAutoSnapshotEnabled(enabled) {
        this.options.autoSnapshotEnabled = enabled;

        if (enabled) {
            this.startAutoSnapshotTimer();
        } else {
            if (this.autoSnapshotTimer) {
                clearInterval(this.autoSnapshotTimer);
                this.autoSnapshotTimer = null;
            }
        }
    }

    // Set auto-snapshot interval
    setAutoSnapshotInterval(interval) {
        this.options.autoSnapshotInterval = interval;

        // Restart timer with new interval
        if (this.options.autoSnapshotEnabled) {
            if (this.autoSnapshotTimer) {
                clearInterval(this.autoSnapshotTimer);
            }
            this.startAutoSnapshotTimer();
        }
    }

    // Destroy the integration
    destroy() {
        if (this.autoSnapshotTimer) {
            clearInterval(this.autoSnapshotTimer);
            this.autoSnapshotTimer = null;
        }

        // Remove any UI indicators
        const indicators = [
            'major-edit-indicator',
            'edit-counter',
            'pending-changes-indicator',
            'auto-save-indicator'
        ];

        indicators.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
            }
        });

        // Clear current snapshot prompt
        if (this.currentSnapshotPrompt) {
            this.currentSnapshotPrompt.remove();
            this.currentSnapshotPrompt = null;
        }
    }
}

// Initialize global BIM editing integration
const bimEditingIntegration = new BIMEditingIntegration();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BIMEditingIntegration;
}
