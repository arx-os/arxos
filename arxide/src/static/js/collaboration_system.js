// Collaboration System for Floor Version Control
class CollaborationSystem {
    constructor(options = {}) {
        this.options = {
            floorLockTimeout: 300000, // 5 minutes
            conflictCheckInterval: 10000, // 10 seconds
            userActivityTimeout: 60000, // 1 minute
            showUserPresence: true,
            enableFloorLocking: true,
            enableConflictResolution: true,
            enableCollaborativeIndicators: true,
            ...options
        };
        
        this.currentUser = null;
        this.currentFloor = null;
        this.floorLock = null;
        this.activeUsers = new Map();
        this.userActivity = new Map();
        this.conflictQueue = [];
        this.isProcessing = false;
        
        this.lockTimer = null;
        this.activityTimer = null;
        this.conflictTimer = null;
        this.presenceTimer = null;
        
        this.initializeSystem();
    }

    // Initialize the collaboration system
    initializeSystem() {
        this.initializeCurrentUser();
        this.setupEventListeners();
        this.startTimers();
        this.initializeUI();
    }

    // Initialize current user
    initializeCurrentUser() {
        this.currentUser = {
            id: localStorage.getItem('user_id') || this.generateUserId(),
            name: localStorage.getItem('user_name') || 'Unknown User',
            email: localStorage.getItem('user_email') || '',
            avatar: localStorage.getItem('user_avatar') || null,
            sessionId: this.generateSessionId()
        };
        
        // Store user info if not already stored
        if (!localStorage.getItem('user_id')) {
            localStorage.setItem('user_id', this.currentUser.id);
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Listen for floor selection changes
        document.addEventListener('floorSelected', (event) => {
            this.handleFloorSelection(event.detail);
        });
        
        // Listen for user activity
        document.addEventListener('mousedown', () => this.updateUserActivity());
        document.addEventListener('keydown', () => this.updateUserActivity());
        document.addEventListener('touchstart', () => this.updateUserActivity());
        
        // Listen for page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });
        
        // Listen for beforeunload
        window.addEventListener('beforeunload', () => {
            this.releaseFloorLock();
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

    // Start all timers
    startTimers() {
        this.startLockTimer();
        this.startActivityTimer();
        this.startConflictTimer();
        this.startPresenceTimer();
    }

    // Start lock timer
    startLockTimer() {
        this.lockTimer = setInterval(() => {
            this.refreshFloorLock();
        }, this.options.floorLockTimeout / 2); // Refresh halfway through timeout
    }

    // Start activity timer
    startActivityTimer() {
        this.activityTimer = setInterval(() => {
            this.checkUserActivity();
        }, this.options.userActivityTimeout);
    }

    // Start conflict timer
    startConflictTimer() {
        this.conflictTimer = setInterval(() => {
            this.checkForConflicts();
        }, this.options.conflictCheckInterval);
    }

    // Start presence timer
    startPresenceTimer() {
        this.presenceTimer = setInterval(() => {
            this.updateUserPresence();
        }, 30000); // Update presence every 30 seconds
    }

    // Initialize UI elements
    initializeUI() {
        this.createCollaborationUI();
        this.updateCollaborationStatus();
    }

    // Create collaboration UI
    createCollaborationUI() {
        // Create collaboration status bar
        const statusBar = document.createElement('div');
        statusBar.id = 'collaboration-status-bar';
        statusBar.className = 'fixed bottom-0 left-0 right-0 bg-gray-800 text-white p-2 text-sm z-50';
        statusBar.innerHTML = `
            <div class="flex items-center justify-between max-w-7xl mx-auto">
                <div class="flex items-center space-x-4">
                    <div id="floor-lock-status" class="flex items-center space-x-2">
                        <i class="fas fa-lock text-green-400"></i>
                        <span>Floor unlocked</span>
                    </div>
                    <div id="active-users" class="flex items-center space-x-2">
                        <i class="fas fa-users text-blue-400"></i>
                        <span>0 active users</span>
                    </div>
                    <div id="conflict-status" class="flex items-center space-x-2" style="display: none;">
                        <i class="fas fa-exclamation-triangle text-red-400"></i>
                        <span>Conflicts detected</span>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <div id="user-activity" class="flex items-center space-x-2">
                        <i class="fas fa-circle text-green-400"></i>
                        <span>Active</span>
                    </div>
                    <button id="collaboration-settings" class="text-gray-300 hover:text-white">
                        <i class="fas fa-cog"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(statusBar);
        
        // Create user presence panel
        const presencePanel = document.createElement('div');
        presencePanel.id = 'user-presence-panel';
        presencePanel.className = 'fixed top-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 z-50 max-w-xs';
        presencePanel.style.display = 'none';
        presencePanel.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold text-gray-900">Active Users</h3>
                <button id="close-presence-panel" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="user-list" class="space-y-2">
                <!-- User list will be populated here -->
            </div>
        `;
        
        document.body.appendChild(presencePanel);
        
        // Create conflict resolution modal
        const conflictModal = document.createElement('div');
        conflictModal.id = 'conflict-resolution-modal';
        conflictModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        conflictModal.style.display = 'none';
        conflictModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Conflict Resolution</h3>
                    <button id="close-conflict-modal" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div id="conflict-list" class="space-y-4 mb-4">
                    <!-- Conflicts will be listed here -->
                </div>
                <div class="flex justify-end space-x-3">
                    <button id="resolve-conflicts" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                        Resolve Conflicts
                    </button>
                    <button id="ignore-conflicts" class="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400">
                        Ignore
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(conflictModal);
        
        // Add event listeners
        this.setupUIEventListeners();
    }

    // Setup UI event listeners
    setupUIEventListeners() {
        // Collaboration settings button
        document.getElementById('collaboration-settings')?.addEventListener('click', () => {
            this.showCollaborationSettings();
        });
        
        // Active users click to show presence panel
        document.getElementById('active-users')?.addEventListener('click', () => {
            this.togglePresencePanel();
        });
        
        // Close presence panel
        document.getElementById('close-presence-panel')?.addEventListener('click', () => {
            this.hidePresencePanel();
        });
        
        // Close conflict modal
        document.getElementById('close-conflict-modal')?.addEventListener('click', () => {
            this.hideConflictModal();
        });
        
        // Resolve conflicts
        document.getElementById('resolve-conflicts')?.addEventListener('click', () => {
            this.resolveConflicts();
        });
        
        // Ignore conflicts
        document.getElementById('ignore-conflicts')?.addEventListener('click', () => {
            this.ignoreConflicts();
        });
    }

    // Handle floor selection
    async handleFloorSelection(floorData) {
        const previousFloor = this.currentFloor;
        this.currentFloor = floorData;
        
        // Release lock on previous floor
        if (previousFloor && previousFloor.id !== floorData.id) {
            await this.releaseFloorLock();
        }
        
        // Request lock on new floor
        if (this.options.enableFloorLocking) {
            await this.requestFloorLock();
        }
        
        // Update collaboration status
        this.updateCollaborationStatus();
        
        // Update user presence
        this.updateUserPresence();
    }

    // Request floor lock
    async requestFloorLock() {
        if (!this.currentFloor || !this.options.enableFloorLocking) return;
        
        try {
            const response = await fetch(`/api/floors/${this.currentFloor.id}/lock`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    session_id: this.currentUser.sessionId,
                    lock_type: 'version_control',
                    expires_at: new Date(Date.now() + this.options.floorLockTimeout).toISOString()
                })
            });
            
            if (response.ok) {
                const lockData = await response.json();
                this.floorLock = lockData;
                this.updateFloorLockStatus(true);
                console.log('Floor lock acquired successfully');
            } else if (response.status === 409) {
                // Floor is locked by another user
                const lockInfo = await response.json();
                this.handleFloorLockedByOther(lockInfo);
            } else {
                throw new Error('Failed to acquire floor lock');
            }
        } catch (error) {
            console.error('Error requesting floor lock:', error);
            this.handleFloorLockError(error);
        }
    }

    // Refresh floor lock
    async refreshFloorLock() {
        if (!this.floorLock || !this.currentFloor) return;
        
        try {
            const response = await fetch(`/api/floors/${this.currentFloor.id}/lock/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    session_id: this.currentUser.sessionId,
                    expires_at: new Date(Date.now() + this.options.floorLockTimeout).toISOString()
                })
            });
            
            if (response.ok) {
                const lockData = await response.json();
                this.floorLock = lockData;
                console.log('Floor lock refreshed successfully');
            } else {
                // Lock expired or was taken by another user
                this.handleFloorLockExpired();
            }
        } catch (error) {
            console.error('Error refreshing floor lock:', error);
            this.handleFloorLockError(error);
        }
    }

    // Release floor lock
    async releaseFloorLock() {
        if (!this.floorLock || !this.currentFloor) return;
        
        try {
            await fetch(`/api/floors/${this.currentFloor.id}/lock/release`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    session_id: this.currentUser.sessionId
                })
            });
            
            this.floorLock = null;
            this.updateFloorLockStatus(false);
            console.log('Floor lock released successfully');
        } catch (error) {
            console.error('Error releasing floor lock:', error);
        }
    }

    // Handle floor locked by other user
    handleFloorLockedByOther(lockInfo) {
        this.updateFloorLockStatus(false, lockInfo.locked_by);
        
        // Show notification
        this.showNotification(
            `Floor is locked by ${lockInfo.locked_by_name || 'another user'}`,
            'warning'
        );
        
        // Emit event
        this.emitEvent('floorLockedByOther', lockInfo);
    }

    // Handle floor lock expired
    handleFloorLockExpired() {
        this.floorLock = null;
        this.updateFloorLockStatus(false);
        
        // Show notification
        this.showNotification('Floor lock expired', 'warning');
        
        // Try to reacquire lock
        setTimeout(() => {
            this.requestFloorLock();
        }, 1000);
        
        // Emit event
        this.emitEvent('floorLockExpired');
    }

    // Handle floor lock error
    handleFloorLockError(error) {
        this.floorLock = null;
        this.updateFloorLockStatus(false);
        
        // Show notification
        this.showNotification('Failed to acquire floor lock', 'error');
        
        // Emit event
        this.emitEvent('floorLockError', error);
    }

    // Update floor lock status in UI
    updateFloorLockStatus(locked, lockedBy = null) {
        const statusElement = document.getElementById('floor-lock-status');
        if (!statusElement) return;
        
        if (locked) {
            statusElement.innerHTML = `
                <i class="fas fa-lock text-green-400"></i>
                <span>Floor locked</span>
            `;
        } else if (lockedBy) {
            statusElement.innerHTML = `
                <i class="fas fa-lock text-red-400"></i>
                <span>Locked by ${lockedBy}</span>
            `;
        } else {
            statusElement.innerHTML = `
                <i class="fas fa-unlock text-gray-400"></i>
                <span>Floor unlocked</span>
            `;
        }
    }

    // Update user activity
    updateUserActivity() {
        this.userActivity.set(this.currentUser.id, Date.now());
        
        // Update activity indicator
        const activityElement = document.getElementById('user-activity');
        if (activityElement) {
            activityElement.innerHTML = `
                <i class="fas fa-circle text-green-400"></i>
                <span>Active</span>
            `;
        }
    }

    // Check user activity
    checkUserActivity() {
        const now = Date.now();
        const inactiveThreshold = this.options.userActivityTimeout;
        
        // Check current user activity
        const lastActivity = this.userActivity.get(this.currentUser.id);
        if (lastActivity && (now - lastActivity) > inactiveThreshold) {
            this.handleUserInactive();
        }
        
        // Check other users' activity
        for (const [userId, lastActivity] of this.userActivity.entries()) {
            if (userId !== this.currentUser.id && (now - lastActivity) > inactiveThreshold) {
                this.handleUserBecameInactive(userId);
            }
        }
    }

    // Handle user becoming inactive
    handleUserInactive() {
        const activityElement = document.getElementById('user-activity');
        if (activityElement) {
            activityElement.innerHTML = `
                <i class="fas fa-circle text-gray-400"></i>
                <span>Inactive</span>
            `;
        }
        
        // Emit event
        this.emitEvent('userInactive', { userId: this.currentUser.id });
    }

    // Handle other user becoming inactive
    handleUserBecameInactive(userId) {
        this.activeUsers.delete(userId);
        this.userActivity.delete(userId);
        
        // Update presence panel
        this.updatePresencePanel();
        
        // Emit event
        this.emitEvent('userBecameInactive', { userId });
    }

    // Update user presence
    async updateUserPresence() {
        if (!this.currentFloor) return;
        
        try {
            const response = await fetch(`/api/floors/${this.currentFloor.id}/presence`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    session_id: this.currentUser.sessionId,
                    user_name: this.currentUser.name,
                    user_email: this.currentUser.email,
                    user_avatar: this.currentUser.avatar,
                    last_activity: Date.now()
                })
            });
            
            if (response.ok) {
                const presenceData = await response.json();
                this.updateActiveUsers(presenceData.active_users);
            }
        } catch (error) {
            console.error('Error updating user presence:', error);
        }
    }

    // Update active users
    updateActiveUsers(users) {
        this.activeUsers.clear();
        
        users.forEach(user => {
            if (user.user_id !== this.currentUser.id) {
                this.activeUsers.set(user.user_id, user);
                this.userActivity.set(user.user_id, user.last_activity);
            }
        });
        
        // Update UI
        this.updateActiveUsersCount();
        this.updatePresencePanel();
    }

    // Update active users count
    updateActiveUsersCount() {
        const countElement = document.getElementById('active-users');
        if (countElement) {
            const count = this.activeUsers.size;
            countElement.innerHTML = `
                <i class="fas fa-users text-blue-400"></i>
                <span>${count} active user${count !== 1 ? 's' : ''}</span>
            `;
        }
    }

    // Update presence panel
    updatePresencePanel() {
        const userList = document.getElementById('user-list');
        if (!userList) return;
        
        userList.innerHTML = '';
        
        this.activeUsers.forEach(user => {
            const userElement = document.createElement('div');
            userElement.className = 'flex items-center space-x-3 p-2 bg-gray-50 rounded';
            userElement.innerHTML = `
                <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    ${user.user_name ? user.user_name.charAt(0).toUpperCase() : 'U'}
                </div>
                <div class="flex-1">
                    <div class="font-medium text-gray-900">${user.user_name || 'Unknown User'}</div>
                    <div class="text-sm text-gray-500">${user.user_email || ''}</div>
                </div>
                <div class="flex items-center space-x-1">
                    <div class="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span class="text-xs text-gray-500">Active</span>
                </div>
            `;
            userList.appendChild(userElement);
        });
    }

    // Toggle presence panel
    togglePresencePanel() {
        const panel = document.getElementById('user-presence-panel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    }

    // Hide presence panel
    hidePresencePanel() {
        const panel = document.getElementById('user-presence-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    // Check for conflicts
    async checkForConflicts() {
        if (!this.currentFloor || this.isProcessing) return;
        
        try {
            const response = await fetch(`/api/floors/${this.currentFloor.id}/conflicts`);
            if (response.ok) {
                const conflicts = await response.json();
                if (conflicts.length > 0) {
                    this.handleConflictsDetected(conflicts);
                }
            }
        } catch (error) {
            console.error('Error checking for conflicts:', error);
        }
    }

    // Handle conflicts detected
    handleConflictsDetected(conflicts) {
        this.conflictQueue = conflicts;
        
        // Update conflict status
        const conflictElement = document.getElementById('conflict-status');
        if (conflictElement) {
            conflictElement.style.display = 'flex';
            conflictElement.innerHTML = `
                <i class="fas fa-exclamation-triangle text-red-400"></i>
                <span>${conflicts.length} conflict${conflicts.length !== 1 ? 's' : ''} detected</span>
            `;
        }
        
        // Show notification
        this.showNotification(`${conflicts.length} conflict(s) detected`, 'warning');
        
        // Emit event
        this.emitEvent('conflictsDetected', conflicts);
    }

    // Show conflict resolution modal
    showConflictModal() {
        const modal = document.getElementById('conflict-resolution-modal');
        const conflictList = document.getElementById('conflict-list');
        
        if (!modal || !conflictList) return;
        
        conflictList.innerHTML = '';
        
        this.conflictQueue.forEach(conflict => {
            const conflictElement = document.createElement('div');
            conflictElement.className = 'border border-red-200 bg-red-50 p-3 rounded';
            conflictElement.innerHTML = `
                <div class="flex items-center justify-between mb-2">
                    <h4 class="font-medium text-red-900">${conflict.type}</h4>
                    <span class="text-sm text-red-600">${conflict.severity}</span>
                </div>
                <p class="text-sm text-red-700 mb-2">${conflict.description}</p>
                <div class="text-xs text-red-600">
                    <strong>Affected:</strong> ${conflict.affected_objects.join(', ')}
                </div>
            `;
            conflictList.appendChild(conflictElement);
        });
        
        modal.style.display = 'flex';
    }

    // Hide conflict modal
    hideConflictModal() {
        const modal = document.getElementById('conflict-resolution-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Resolve conflicts
    async resolveConflicts() {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        
        try {
            const response = await fetch(`/api/floors/${this.currentFloor.id}/conflicts/resolve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.currentUser.id,
                    conflicts: this.conflictQueue
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.handleConflictsResolved(result);
            } else {
                throw new Error('Failed to resolve conflicts');
            }
        } catch (error) {
            console.error('Error resolving conflicts:', error);
            this.showNotification('Failed to resolve conflicts', 'error');
        } finally {
            this.isProcessing = false;
        }
    }

    // Handle conflicts resolved
    handleConflictsResolved(result) {
        this.conflictQueue = [];
        
        // Hide conflict status
        const conflictElement = document.getElementById('conflict-status');
        if (conflictElement) {
            conflictElement.style.display = 'none';
        }
        
        // Hide modal
        this.hideConflictModal();
        
        // Show success notification
        this.showNotification('Conflicts resolved successfully', 'success');
        
        // Emit event
        this.emitEvent('conflictsResolved', result);
    }

    // Ignore conflicts
    ignoreConflicts() {
        this.conflictQueue = [];
        
        // Hide conflict status
        const conflictElement = document.getElementById('conflict-status');
        if (conflictElement) {
            conflictElement.style.display = 'none';
        }
        
        // Hide modal
        this.hideConflictModal();
        
        // Show notification
        this.showNotification('Conflicts ignored', 'info');
        
        // Emit event
        this.emitEvent('conflictsIgnored');
    }

    // Handle version restore started
    handleVersionRestoreStarted() {
        if (this.options.enableFloorLocking) {
            this.requestFloorLock();
        }
    }

    // Handle version restore completed
    handleVersionRestoreCompleted() {
        // Release lock after restore
        setTimeout(() => {
            this.releaseFloorLock();
        }, 5000); // Keep lock for 5 seconds after restore
    }

    // Handle version restore failed
    handleVersionRestoreFailed() {
        // Release lock immediately on failure
        this.releaseFloorLock();
    }

    // Handle page hidden
    handlePageHidden() {
        // Mark user as inactive
        this.handleUserInactive();
    }

    // Handle page visible
    handlePageVisible() {
        // Mark user as active
        this.updateUserActivity();
    }

    // Show collaboration settings
    showCollaborationSettings() {
        // Create settings modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Collaboration Settings</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <label class="text-sm font-medium text-gray-700">Floor Locking</label>
                        <input type="checkbox" id="enable-floor-locking" ${this.options.enableFloorLocking ? 'checked' : ''} class="rounded">
                    </div>
                    <div class="flex items-center justify-between">
                        <label class="text-sm font-medium text-gray-700">Conflict Resolution</label>
                        <input type="checkbox" id="enable-conflict-resolution" ${this.options.enableConflictResolution ? 'checked' : ''} class="rounded">
                    </div>
                    <div class="flex items-center justify-between">
                        <label class="text-sm font-medium text-gray-700">User Presence</label>
                        <input type="checkbox" id="show-user-presence" ${this.options.showUserPresence ? 'checked' : ''} class="rounded">
                    </div>
                </div>
                <div class="flex justify-end mt-6">
                    <button onclick="collaborationSystem.saveSettings()" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                        Save Settings
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        modal.querySelector('#enable-floor-locking').addEventListener('change', (e) => {
            this.options.enableFloorLocking = e.target.checked;
        });
        
        modal.querySelector('#enable-conflict-resolution').addEventListener('change', (e) => {
            this.options.enableConflictResolution = e.target.checked;
        });
        
        modal.querySelector('#show-user-presence').addEventListener('change', (e) => {
            this.options.showUserPresence = e.target.checked;
            this.updateCollaborationStatus();
        });
    }

    // Save settings
    saveSettings() {
        // Save to localStorage
        localStorage.setItem('collaboration_settings', JSON.stringify({
            enableFloorLocking: this.options.enableFloorLocking,
            enableConflictResolution: this.options.enableConflictResolution,
            showUserPresence: this.options.showUserPresence
        }));
        
        // Close modal
        document.querySelector('.fixed.inset-0').remove();
        
        // Show notification
        this.showNotification('Settings saved successfully', 'success');
    }

    // Update collaboration status
    updateCollaborationStatus() {
        // Update UI based on current status
        this.updateFloorLockStatus(!!this.floorLock);
        this.updateActiveUsersCount();
        this.updateUserActivity();
    }

    // Show notification
    showNotification(message, type = 'info') {
        // Use notification system if available
        if (window.notificationSystem) {
            window.notificationSystem.show(message, type);
        } else {
            // Fallback to console
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    // Generate user ID
    generateUserId() {
        return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Generate session ID
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Emit custom event
    emitEvent(eventName, data) {
        const event = new CustomEvent(eventName, {
            detail: data,
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    // Get collaboration statistics
    getCollaborationStatistics() {
        return {
            currentUser: this.currentUser,
            currentFloor: this.currentFloor,
            floorLock: this.floorLock,
            activeUsers: Array.from(this.activeUsers.values()),
            activeUsersCount: this.activeUsers.size,
            conflictQueue: this.conflictQueue,
            userActivity: Object.fromEntries(this.userActivity)
        };
    }

    // Destroy the collaboration system
    destroy() {
        // Clear all timers
        if (this.lockTimer) clearInterval(this.lockTimer);
        if (this.activityTimer) clearInterval(this.activityTimer);
        if (this.conflictTimer) clearInterval(this.conflictTimer);
        if (this.presenceTimer) clearInterval(this.presenceTimer);
        
        // Release floor lock
        this.releaseFloorLock();
        
        // Remove UI elements
        const elements = [
            'collaboration-status-bar',
            'user-presence-panel',
            'conflict-resolution-modal'
        ];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
            }
        });
        
        // Clear data
        this.activeUsers.clear();
        this.userActivity.clear();
        this.conflictQueue = [];
    }
}

// Initialize global collaboration system
const collaborationSystem = new CollaborationSystem();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CollaborationSystem;
} 