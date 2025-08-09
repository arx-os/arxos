/**
 * Collaboration Manager
 * Orchestrates realtime, presence, and conflicts modules for collaborative features
 */

import { Realtime } from './realtime.js';
import { Presence } from './presence.js';
import { Conflicts } from './conflicts.js';

export class CollaborationManager {
    constructor(options = {}) {
        this.options = {
            floorLockTimeout: options.floorLockTimeout || 300000, // 5 minutes
            enableFloorLocking: options.enableFloorLocking !== false,
            enableCollaborativeIndicators: options.enableCollaborativeIndicators !== false,
            ...options
        };

        // Initialize modules
        this.realtime = new Realtime(options);
        this.presence = new Presence(options);
        this.conflicts = new Conflicts(options);

        // Connect modules
        this.connectModules();

        // Floor locking state
        this.currentFloor = null;
        this.floorLock = null;
        this.lockTimer = null;

        // UI elements
        this.collaborationUI = null;
        this.settingsModal = null;

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createUI();
    }

    connectModules() {
        // Connect realtime events
        this.realtime.addEventListener('connected', (data) => {
            this.triggerEvent('connected', data);
        });

        this.realtime.addEventListener('disconnected', (data) => {
            this.triggerEvent('disconnected', data);
        });

        this.realtime.addEventListener('floorLockAcquired', (data) => {
            this.handleFloorLockAcquired(data);
        });

        this.realtime.addEventListener('floorLockReleased', (data) => {
            this.handleFloorLockReleased(data);
        });

        this.realtime.addEventListener('liveUpdate', (data) => {
            this.handleLiveUpdate(data);
        });

        // Connect presence events
        this.presence.addEventListener('userJoined', (data) => {
            this.triggerEvent('userJoined', data);
        });

        this.presence.addEventListener('userLeft', (data) => {
            this.triggerEvent('userLeft', data);
        });

        this.presence.addEventListener('userStatusChanged', (data) => {
            this.triggerEvent('userStatusChanged', data);
        });

        // Connect conflicts events
        this.conflicts.addEventListener('conflictsDetected', (data) => {
            this.triggerEvent('conflictsDetected', data);
        });

        this.conflicts.addEventListener('conflictsResolved', (data) => {
            this.triggerEvent('conflictsResolved', data);
        });
    }

    setupEventListeners() {
        // Listen for floor selection changes
        document.addEventListener('floorSelected', (event) => {
            this.handleFloorSelection(event.detail);
        });

        // Listen for beforeunload
        window.addEventListener('beforeunload', () => {
            this.releaseFloorLock();
        });
    }

    // Floor selection handling
    async handleFloorSelection(floorData) {
        // Release lock on current floor
        if (this.currentFloor) {
            await this.releaseFloorLock();
        }

        this.currentFloor = floorData;

        // Request lock on new floor
        if (this.options.enableFloorLocking) {
            await this.requestFloorLock();
        }

        this.triggerEvent('floorChanged', { floor: floorData });
    }

    // Floor locking methods
    async requestFloorLock() {
        if (!this.currentFloor || !this.options.enableFloorLocking) return;

        try {
            const response = await fetch('/api/floors/lock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    floor_id: this.currentFloor.id,
                    user_id: this.getCurrentUser()?.id,
                    timeout: this.options.floorLockTimeout
                })
            });

            if (!response.ok) {
                const error = await response.json();
                this.handleFloorLockError(error);
                return;
            }

            const lockInfo = await response.json();
            this.handleFloorLockAcquired(lockInfo);

        } catch (error) {
            console.error('Error requesting floor lock:', error);
            this.handleFloorLockError(error);
        }
    }

    async refreshFloorLock() {
        if (!this.floorLock || !this.options.enableFloorLocking) return;

        try {
            const response = await fetch('/api/floors/lock/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    floor_id: this.currentFloor.id,
                    user_id: this.getCurrentUser()?.id,
                    lock_id: this.floorLock.id
                })
            });

            if (!response.ok) {
                throw new Error('Failed to refresh floor lock');
            }

            const lockInfo = await response.json();
            this.floorLock = lockInfo;

            this.triggerEvent('floorLockRefreshed', { lockInfo });

        } catch (error) {
            console.error('Error refreshing floor lock:', error);
            this.handleFloorLockError(error);
        }
    }

    async releaseFloorLock() {
        if (!this.floorLock) return;

        try {
            const response = await fetch('/api/floors/lock/release', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    floor_id: this.currentFloor.id,
                    user_id: this.getCurrentUser()?.id,
                    lock_id: this.floorLock.id
                })
            });

            if (!response.ok) {
                console.warn('Failed to release floor lock');
            }

            this.floorLock = null;
            this.clearLockTimer();

            this.triggerEvent('floorLockReleased', { floorId: this.currentFloor?.id });

        } catch (error) {
            console.error('Error releasing floor lock:', error);
        }
    }

    // Floor lock event handlers
    handleFloorLockAcquired(lockInfo) {
        this.floorLock = lockInfo;
        this.startLockTimer();
        this.updateFloorLockStatus(true, lockInfo.user_id);

        this.triggerEvent('floorLockAcquired', { lockInfo });
    }

    handleFloorLockReleased(data) {
        this.floorLock = null;
        this.clearLockTimer();
        this.updateFloorLockStatus(false);

        this.triggerEvent('floorLockReleased', data);
    }

    handleFloorLockError(error) {
        if (error.code === 'FLOOR_LOCKED_BY_OTHER') {
            this.handleFloorLockedByOther(error.lockInfo);
        } else if (error.code === 'FLOOR_LOCK_EXPIRED') {
            this.handleFloorLockExpired();
        } else {
            console.error('Floor lock error:', error);
            this.triggerEvent('floorLockError', { error });
        }
    }

    handleFloorLockedByOther(lockInfo) {
        this.updateFloorLockStatus(true, lockInfo.user_id);
        this.triggerEvent('floorLockedByOther', { lockInfo });

        // Show notification
        this.showNotification(`Floor is locked by ${lockInfo.user_name}`, 'warning');
    }

    handleFloorLockExpired() {
        this.floorLock = null;
        this.clearLockTimer();
        this.updateFloorLockStatus(false);

        this.triggerEvent('floorLockExpired');
        this.showNotification('Floor lock has expired', 'warning');
    }

    // Live update handling
    handleLiveUpdate(data) {
        const { userId, updateType, data: updateData } = data;

        // Apply live update to the UI
        this.applyLiveUpdate(updateType, updateData);

        this.triggerEvent('liveUpdateApplied', { userId, updateType, data: updateData });
    }

    applyLiveUpdate(updateType, data) {
        switch (updateType) {
            case 'object_added':
                this.applyObjectAdded(data);
                break;
            case 'object_modified':
                this.applyObjectModified(data);
                break;
            case 'object_deleted':
                this.applyObjectDeleted(data);
                break;
            case 'object_moved':
                this.applyObjectMoved(data);
                break;
            default:
                console.warn('Unknown live update type:', updateType);
        }
    }

    applyObjectAdded(data) {
        // Apply object addition to the canvas
        if (window.svgObjectInteraction) {
            window.svgObjectInteraction.addObject(data.object);
        }
    }

    applyObjectModified(data) {
        // Apply object modification to the canvas
        if (window.svgObjectInteraction) {
            window.svgObjectInteraction.modifyObject(data.objectId, data.changes);
        }
    }

    applyObjectDeleted(data) {
        // Apply object deletion to the canvas
        if (window.svgObjectInteraction) {
            window.svgObjectInteraction.deleteObject(data.objectId);
        }
    }

    applyObjectMoved(data) {
        // Apply object movement to the canvas
        if (window.svgObjectInteraction) {
            window.svgObjectInteraction.moveObject(data.objectId, data.position);
        }
    }

    // Timer management
    startLockTimer() {
        this.clearLockTimer();

        this.lockTimer = setTimeout(() => {
            this.refreshFloorLock();
        }, this.options.floorLockTimeout * 0.8); // Refresh at 80% of timeout
    }

    clearLockTimer() {
        if (this.lockTimer) {
            clearTimeout(this.lockTimer);
            this.lockTimer = null;
        }
    }

    // UI methods
    createUI() {
        this.createCollaborationUI();
        this.createSettingsModal();
    }

    createCollaborationUI() {
        this.collaborationUI = document.createElement('div');
        this.collaborationUI.id = 'collaboration-ui';
        this.collaborationUI.className = 'fixed top-4 left-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 z-40 max-w-sm';
        this.collaborationUI.style.display = 'none';

        this.collaborationUI.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold text-gray-900">Collaboration</h3>
                <button id="close-collaboration-ui" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="space-y-3">
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-700">Connection:</span>
                    <span id="connection-status" class="text-sm font-medium text-green-600">Connected</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-700">Floor Lock:</span>
                    <span id="floor-lock-status" class="text-sm font-medium text-gray-600">Unlocked</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-700">Active Users:</span>
                    <span id="active-users-count" class="text-sm font-medium text-blue-600">0</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-700">Conflicts:</span>
                    <span id="conflicts-count" class="text-sm font-medium text-red-600">0</span>
                </div>
            </div>
            <div class="mt-4 space-y-2">
                <button id="request-floor-lock" class="w-full bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 text-sm">
                    Request Floor Lock
                </button>
                <button id="release-floor-lock" class="w-full bg-red-600 text-white px-3 py-2 rounded-md hover:bg-red-700 text-sm">
                    Release Floor Lock
                </button>
                <button id="show-collaboration-settings" class="w-full bg-gray-600 text-white px-3 py-2 rounded-md hover:bg-gray-700 text-sm">
                    Settings
                </button>
            </div>
        `;

        document.body.appendChild(this.collaborationUI);
        this.setupCollaborationUIEvents();
    }

    createSettingsModal() {
        this.settingsModal = document.createElement('div');
        this.settingsModal.id = 'collaboration-settings-modal';
        this.settingsModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        this.settingsModal.style.display = 'none';

        this.settingsModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-semibold text-gray-900">Collaboration Settings</h3>
                    <button id="close-settings-modal" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-4">
                    <div>
                        <label class="flex items-center">
                            <input type="checkbox" id="enable-floor-locking" class="mr-2" ${this.options.enableFloorLocking ? 'checked' : ''}>
                            <span class="text-sm text-gray-700">Enable Floor Locking</span>
                        </label>
                    </div>
                    <div>
                        <label class="flex items-center">
                            <input type="checkbox" id="show-user-presence" class="mr-2" ${this.options.enableCollaborativeIndicators ? 'checked' : ''}>
                            <span class="text-sm text-gray-700">Show User Presence</span>
                        </label>
                    </div>
                    <div>
                        <label class="flex items-center">
                            <input type="checkbox" id="auto-resolve-conflicts" class="mr-2" ${this.options.autoResolveConflicts ? 'checked' : ''}>
                            <span class="text-sm text-gray-700">Auto-resolve Conflicts</span>
                        </label>
                    </div>
                </div>
                <div class="mt-6 flex space-x-2">
                    <button id="save-settings" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
                        Save Settings
                    </button>
                    <button id="cancel-settings" class="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 text-sm">
                        Cancel
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.settingsModal);
        this.setupSettingsModalEvents();
    }

    setupCollaborationUIEvents() {
        const closeButton = this.collaborationUI.querySelector('#close-collaboration-ui');
        const requestLockButton = this.collaborationUI.querySelector('#request-floor-lock');
        const releaseLockButton = this.collaborationUI.querySelector('#release-floor-lock');
        const settingsButton = this.collaborationUI.querySelector('#show-collaboration-settings');

        closeButton.addEventListener('click', () => {
            this.hideCollaborationUI();
        });

        requestLockButton.addEventListener('click', () => {
            this.requestFloorLock();
        });

        releaseLockButton.addEventListener('click', () => {
            this.releaseFloorLock();
        });

        settingsButton.addEventListener('click', () => {
            this.showSettingsModal();
        });
    }

    setupSettingsModalEvents() {
        const closeButton = this.settingsModal.querySelector('#close-settings-modal');
        const saveButton = this.settingsModal.querySelector('#save-settings');
        const cancelButton = this.settingsModal.querySelector('#cancel-settings');

        closeButton.addEventListener('click', () => {
            this.hideSettingsModal();
        });

        saveButton.addEventListener('click', () => {
            this.saveSettings();
        });

        cancelButton.addEventListener('click', () => {
            this.hideSettingsModal();
        });
    }

    // UI control methods
    showCollaborationUI() {
        if (this.collaborationUI) {
            this.collaborationUI.style.display = 'block';
            this.updateCollaborationStatus();
        }
    }

    hideCollaborationUI() {
        if (this.collaborationUI) {
            this.collaborationUI.style.display = 'none';
        }
    }

    showSettingsModal() {
        if (this.settingsModal) {
            this.settingsModal.style.display = 'flex';
        }
    }

    hideSettingsModal() {
        if (this.settingsModal) {
            this.settingsModal.style.display = 'none';
        }
    }

    updateCollaborationStatus() {
        if (!this.collaborationUI) return;

        // Update connection status
        const connectionStatus = this.collaborationUI.querySelector('#connection-status');
        if (connectionStatus) {
            const isConnected = this.realtime.isConnected();
            connectionStatus.textContent = isConnected ? 'Connected' : 'Disconnected';
            connectionStatus.className = `text-sm font-medium ${isConnected ? 'text-green-600' : 'text-red-600'}`;
        }

        // Update floor lock status
        const floorLockStatus = this.collaborationUI.querySelector('#floor-lock-status');
        if (floorLockStatus) {
            if (this.floorLock) {
                floorLockStatus.textContent = 'Locked';
                floorLockStatus.className = 'text-sm font-medium text-green-600';
            } else {
                floorLockStatus.textContent = 'Unlocked';
                floorLockStatus.className = 'text-sm font-medium text-gray-600';
            }
        }

        // Update active users count
        const activeUsersCount = this.collaborationUI.querySelector('#active-users-count');
        if (activeUsersCount) {
            const count = this.presence.getActiveUsersCount();
            activeUsersCount.textContent = count.toString();
        }

        // Update conflicts count
        const conflictsCount = this.collaborationUI.querySelector('#conflicts-count');
        if (conflictsCount) {
            const count = this.conflicts.getConflictCount();
            conflictsCount.textContent = count.toString();
        }
    }

    updateFloorLockStatus(locked, lockedBy = null) {
        if (locked) {
            this.showNotification(`Floor locked by ${lockedBy || 'you'}`, 'info');
        } else {
            this.showNotification('Floor lock released', 'info');
        }

        this.updateCollaborationStatus();
    }

    // Settings methods
    saveSettings() {
        const enableFloorLocking = this.settingsModal.querySelector('#enable-floor-locking').checked;
        const showUserPresence = this.settingsModal.querySelector('#show-user-presence').checked;
        const autoResolveConflicts = this.settingsModal.querySelector('#auto-resolve-conflicts').checked;

        // Update options
        this.options.enableFloorLocking = enableFloorLocking;
        this.options.enableCollaborativeIndicators = showUserPresence;
        this.options.autoResolveConflicts = autoResolveConflicts;

        // Save to localStorage
        localStorage.setItem('collaboration_settings', JSON.stringify(this.options));

        this.hideSettingsModal();
        this.showNotification('Settings saved successfully', 'success');

        this.triggerEvent('settingsSaved', { settings: this.options });
    }

    // Utility methods
    getCurrentUser() {
        return this.presence.getCurrentUser();
    }

    getCurrentFloor() {
        return this.currentFloor;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 bg-${type === 'success' ? 'green' : type === 'warning' ? 'yellow' : 'blue'}-600 text-white px-4 py-2 rounded-lg shadow-lg z-50`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Module access methods
    getRealtime() {
        return this.realtime;
    }

    getPresence() {
        return this.presence;
    }

    getConflicts() {
        return this.conflicts;
    }

    // Public API methods
    async sendLiveUpdate(updateType, data) {
        if (this.realtime.isConnected()) {
            this.realtime.sendLiveUpdate(updateType, data);
        }
    }

    async requestFloorLock() {
        await this.requestFloorLock();
    }

    async releaseFloorLock() {
        await this.releaseFloorLock();
    }

    getCollaborationStatistics() {
        return {
            connectionStatus: this.realtime.getConnectionStatus(),
            activeUsers: this.presence.getActiveUsersCount(),
            conflicts: this.conflicts.getConflictCount(),
            floorLock: this.floorLock ? 'locked' : 'unlocked',
            currentFloor: this.currentFloor?.id
        };
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
                    handler({ ...data, manager: this });
                } catch (error) {
                    console.error(`Error in collaboration manager event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        // Destroy modules
        if (this.realtime) {
            this.realtime.destroy();
        }
        if (this.presence) {
            this.presence.destroy();
        }
        if (this.conflicts) {
            this.conflicts.destroy();
        }

        // Clear timers
        this.clearLockTimer();

        // Remove UI elements
        if (this.collaborationUI) {
            this.collaborationUI.remove();
        }
        if (this.settingsModal) {
            this.settingsModal.remove();
        }

        // Clear event handlers
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
