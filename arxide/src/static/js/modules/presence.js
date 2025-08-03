/**
 * Presence Module
 * Handles user presence tracking, activity monitoring, and presence UI
 */

export class Presence {
    constructor(options = {}) {
        this.options = {
            userActivityTimeout: options.userActivityTimeout || 60000, // 1 minute
            presenceUpdateInterval: options.presenceUpdateInterval || 30000, // 30 seconds
            showUserPresence: options.showUserPresence !== false,
            maxInactiveTime: options.maxInactiveTime || 300000, // 5 minutes
            ...options
        };
        
        // User state
        this.currentUser = null;
        this.activeUsers = new Map();
        this.userActivity = new Map();
        this.userStatus = new Map();
        
        // Timers
        this.activityTimer = null;
        this.presenceTimer = null;
        this.inactiveTimer = null;
        
        // UI elements
        this.presencePanel = null;
        this.presenceIndicator = null;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.initializeCurrentUser();
        this.setupEventListeners();
        this.startTimers();
        this.createUI();
    }

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
        
        // Initialize current user activity
        this.updateUserActivity();
    }

    setupEventListeners() {
        // Listen for user activity
        document.addEventListener('mousedown', () => this.updateUserActivity());
        document.addEventListener('keydown', () => this.updateUserActivity());
        document.addEventListener('touchstart', () => this.updateUserActivity());
        document.addEventListener('scroll', () => this.updateUserActivity());
        
        // Listen for page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });
        
        // Listen for presence updates from realtime module
        document.addEventListener('presenceUpdate', (event) => {
            this.handlePresenceUpdate(event.detail);
        });
        
        document.addEventListener('userJoined', (event) => {
            this.handleUserJoined(event.detail);
        });
        
        document.addEventListener('userLeft', (event) => {
            this.handleUserLeft(event.detail);
        });
    }

    startTimers() {
        this.startActivityTimer();
        this.startPresenceTimer();
        this.startInactiveTimer();
    }

    startActivityTimer() {
        this.activityTimer = setInterval(() => {
            this.checkUserActivity();
        }, this.options.userActivityTimeout);
    }

    startPresenceTimer() {
        this.presenceTimer = setInterval(() => {
            this.updateUserPresence();
        }, this.options.presenceUpdateInterval);
    }

    startInactiveTimer() {
        this.inactiveTimer = setTimeout(() => {
            this.handleUserInactive();
        }, this.options.maxInactiveTime);
    }

    // User activity methods
    updateUserActivity() {
        const now = Date.now();
        this.userActivity.set(this.currentUser.id, now);
        
        // Reset inactive timer
        if (this.inactiveTimer) {
            clearTimeout(this.inactiveTimer);
        }
        this.startInactiveTimer();
        
        // Update user status to active
        this.updateUserStatus('active');
        
        this.triggerEvent('userActivityUpdated', { 
            userId: this.currentUser.id, 
            timestamp: now 
        });
    }

    checkUserActivity() {
        const now = Date.now();
        const lastActivity = this.userActivity.get(this.currentUser.id);
        
        if (lastActivity && (now - lastActivity) > this.options.userActivityTimeout) {
            this.handleUserBecameInactive();
        }
    }

    handleUserInactive() {
        this.updateUserStatus('inactive');
        this.triggerEvent('userBecameInactive', { userId: this.currentUser.id });
    }

    handleUserBecameInactive(userId) {
        if (userId === this.currentUser.id) {
            this.updateUserStatus('inactive');
        }
        
        this.triggerEvent('userBecameInactive', { userId });
    }

    // User status methods
    updateUserStatus(status) {
        this.userStatus.set(this.currentUser.id, {
            status,
            timestamp: Date.now()
        });
        
        this.triggerEvent('userStatusChanged', { 
            userId: this.currentUser.id, 
            status 
        });
    }

    getUserStatus(userId) {
        return this.userStatus.get(userId) || { status: 'unknown', timestamp: 0 };
    }

    // Presence update methods
    async updateUserPresence() {
        try {
            const presenceData = {
                user_id: this.currentUser.id,
                name: this.currentUser.name,
                status: this.getUserStatus(this.currentUser.id).status,
                last_activity: this.userActivity.get(this.currentUser.id),
                timestamp: Date.now()
            };
            
            // Send presence update to server
            const response = await fetch('/api/presence/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(presenceData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to update presence');
            }
            
            this.triggerEvent('presenceUpdated', { data: presenceData });
        } catch (error) {
            console.error('Error updating presence:', error);
            this.triggerEvent('presenceUpdateFailed', { error });
        }
    }

    handlePresenceUpdate(data) {
        const { users } = data;
        
        // Update active users
        users.forEach(user => {
            this.activeUsers.set(user.id, user);
            this.userActivity.set(user.id, user.last_activity);
            this.userStatus.set(user.id, {
                status: user.status,
                timestamp: user.timestamp
            });
        });
        
        this.updatePresencePanel();
        this.triggerEvent('presenceDataUpdated', { users });
    }

    handleUserJoined(data) {
        const { user } = data;
        this.activeUsers.set(user.id, user);
        this.updatePresencePanel();
    }

    handleUserLeft(data) {
        const { userId } = data;
        this.activeUsers.delete(userId);
        this.userActivity.delete(userId);
        this.userStatus.delete(userId);
        this.updatePresencePanel();
    }

    // Page visibility handling
    handlePageHidden() {
        this.updateUserStatus('away');
        this.triggerEvent('userStatusChanged', { 
            userId: this.currentUser.id, 
            status: 'away' 
        });
    }

    handlePageVisible() {
        this.updateUserStatus('active');
        this.updateUserActivity();
        this.triggerEvent('userStatusChanged', { 
            userId: this.currentUser.id, 
            status: 'active' 
        });
    }

    // UI methods
    createUI() {
        this.createPresenceIndicator();
        this.createPresencePanel();
    }

    createPresenceIndicator() {
        this.presenceIndicator = document.createElement('div');
        this.presenceIndicator.id = 'presence-indicator';
        this.presenceIndicator.className = 'fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-2 z-40';
        this.presenceIndicator.style.display = 'none';
        
        this.presenceIndicator.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                <span class="text-sm text-gray-700">0 online</span>
                <button id="toggle-presence-panel" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-users"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(this.presenceIndicator);
        this.setupPresenceIndicatorEvents();
    }

    createPresencePanel() {
        this.presencePanel = document.createElement('div');
        this.presencePanel.id = 'presence-panel';
        this.presencePanel.className = 'fixed bottom-16 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 z-50 max-w-sm';
        this.presencePanel.style.display = 'none';
        
        this.presencePanel.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-semibold text-gray-900">Active Users</h3>
                <button id="close-presence-panel" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="presence-users-list" class="space-y-2">
                <!-- Users will be populated here -->
            </div>
        `;
        
        document.body.appendChild(this.presencePanel);
        this.setupPresencePanelEvents();
    }

    setupPresenceIndicatorEvents() {
        const toggleButton = this.presenceIndicator.querySelector('#toggle-presence-panel');
        toggleButton.addEventListener('click', () => {
            this.togglePresencePanel();
        });
    }

    setupPresencePanelEvents() {
        const closeButton = this.presencePanel.querySelector('#close-presence-panel');
        closeButton.addEventListener('click', () => {
            this.hidePresencePanel();
        });
    }

    updatePresencePanel() {
        if (!this.options.showUserPresence) return;
        
        const usersList = this.presencePanel.querySelector('#presence-users-list');
        const activeUsers = this.getActiveUsers();
        
        usersList.innerHTML = activeUsers.map(user => `
            <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-${this.getStatusColor(user.id)} rounded-full"></div>
                <span class="text-sm text-gray-700">${user.name}</span>
                <span class="text-xs text-gray-500">${this.getStatusText(user.id)}</span>
            </div>
        `).join('');
        
        this.updateActiveUsersCount();
    }

    updateActiveUsersCount() {
        const count = this.getActiveUsersCount();
        const countElement = this.presenceIndicator.querySelector('span');
        
        if (countElement) {
            countElement.textContent = `${count} online`;
        }
        
        // Show/hide indicator based on count
        if (count > 1) {
            this.presenceIndicator.style.display = 'block';
        } else {
            this.presenceIndicator.style.display = 'none';
        }
    }

    togglePresencePanel() {
        if (this.presencePanel.style.display === 'none') {
            this.showPresencePanel();
        } else {
            this.hidePresencePanel();
        }
    }

    showPresencePanel() {
        if (this.presencePanel) {
            this.presencePanel.style.display = 'block';
        }
    }

    hidePresencePanel() {
        if (this.presencePanel) {
            this.presencePanel.style.display = 'none';
        }
    }

    // Utility methods
    getActiveUsers() {
        return Array.from(this.activeUsers.values());
    }

    getActiveUsersCount() {
        return this.activeUsers.size;
    }

    getStatusColor(userId) {
        const status = this.getUserStatus(userId).status;
        switch (status) {
            case 'active':
                return 'green-500';
            case 'away':
                return 'yellow-500';
            case 'inactive':
                return 'red-500';
            default:
                return 'gray-500';
        }
    }

    getStatusText(userId) {
        const status = this.getUserStatus(userId).status;
        switch (status) {
            case 'active':
                return 'Active';
            case 'away':
                return 'Away';
            case 'inactive':
                return 'Inactive';
            default:
                return 'Unknown';
        }
    }

    generateUserId() {
        return 'user_' + Math.random().toString(36).substring(2, 15);
    }

    generateSessionId() {
        return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    }

    // User management
    setCurrentUser(user) {
        this.currentUser = user;
        this.updateUserActivity();
    }

    getCurrentUser() {
        return this.currentUser;
    }

    // Timer cleanup
    clearTimers() {
        if (this.activityTimer) {
            clearInterval(this.activityTimer);
            this.activityTimer = null;
        }
        
        if (this.presenceTimer) {
            clearInterval(this.presenceTimer);
            this.presenceTimer = null;
        }
        
        if (this.inactiveTimer) {
            clearTimeout(this.inactiveTimer);
            this.inactiveTimer = null;
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
                    handler({ ...data, presence: this });
                } catch (error) {
                    console.error(`Error in presence event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.clearTimers();
        this.activeUsers.clear();
        this.userActivity.clear();
        this.userStatus.clear();
        
        if (this.presenceIndicator) {
            this.presenceIndicator.remove();
        }
        
        if (this.presencePanel) {
            this.presencePanel.remove();
        }
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 