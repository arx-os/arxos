/**
 * Realtime Module
 * Handles real-time collaboration, WebSocket connections, and live updates
 */

export class Realtime {
    constructor(options = {}) {
        this.options = {
            websocketUrl: options.websocketUrl || '/ws/collaboration',
            reconnectInterval: options.reconnectInterval || 5000,
            heartbeatInterval: options.heartbeatInterval || 30000,
            maxReconnectAttempts: options.maxReconnectAttempts || 5,
            ...options
        };
        
        // WebSocket connection
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.heartbeatTimer = null;
        
        // Real-time state
        this.currentFloor = null;
        this.currentUser = null;
        this.activeUsers = new Map();
        this.liveUpdates = new Map();
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.connect();
    }

    setupEventListeners() {
        // Listen for floor selection changes
        document.addEventListener('floorSelected', (event) => {
            this.handleFloorSelection(event.detail);
        });
        
        // Listen for user activity
        document.addEventListener('mousedown', () => this.sendUserActivity());
        document.addEventListener('keydown', () => this.sendUserActivity());
        document.addEventListener('touchstart', () => this.sendUserActivity());
        
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
            this.disconnect();
        });
    }

    // WebSocket connection methods
    connect() {
        if (this.isConnected) return;
        
        try {
            const url = this.buildWebSocketUrl();
            this.websocket = new WebSocket(url);
            
            this.websocket.onopen = () => this.handleConnectionOpen();
            this.websocket.onmessage = (event) => this.handleMessage(event);
            this.websocket.onclose = (event) => this.handleConnectionClose(event);
            this.websocket.onerror = (error) => this.handleConnectionError(error);
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }

    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        this.isConnected = false;
        this.clearTimers();
        this.triggerEvent('disconnected');
    }

    buildWebSocketUrl() {
        const baseUrl = this.options.websocketUrl;
        const params = new URLSearchParams({
            user_id: this.currentUser?.id || 'anonymous',
            session_id: this.currentUser?.sessionId || this.generateSessionId(),
            floor_id: this.currentFloor?.id || ''
        });
        
        return `${baseUrl}?${params.toString()}`;
    }

    // WebSocket event handlers
    handleConnectionOpen() {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        this.startHeartbeat();
        this.sendJoinMessage();
        
        this.triggerEvent('connected');
    }

    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.processMessage(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    handleConnectionClose(event) {
        this.isConnected = false;
        this.clearTimers();
        
        if (event.code !== 1000) { // Not a normal closure
            this.scheduleReconnect();
        }
        
        this.triggerEvent('connectionClosed', { code: event.code, reason: event.reason });
    }

    handleConnectionError(error) {
        console.error('WebSocket error:', error);
        this.triggerEvent('connectionError', { error });
    }

    // Message processing
    processMessage(data) {
        const { type, payload } = data;
        
        switch (type) {
            case 'user_joined':
                this.handleUserJoined(payload);
                break;
            case 'user_left':
                this.handleUserLeft(payload);
                break;
            case 'user_activity':
                this.handleUserActivity(payload);
                break;
            case 'floor_lock_acquired':
                this.handleFloorLockAcquired(payload);
                break;
            case 'floor_lock_released':
                this.handleFloorLockReleased(payload);
                break;
            case 'live_update':
                this.handleLiveUpdate(payload);
                break;
            case 'conflict_detected':
                this.handleConflictDetected(payload);
                break;
            case 'presence_update':
                this.handlePresenceUpdate(payload);
                break;
            case 'heartbeat':
                this.handleHeartbeat(payload);
                break;
            default:
                console.warn('Unknown message type:', type);
        }
    }

    // Message handlers
    handleUserJoined(payload) {
        const { user } = payload;
        this.activeUsers.set(user.id, user);
        
        this.triggerEvent('userJoined', { user });
        this.updateActiveUsers();
    }

    handleUserLeft(payload) {
        const { user_id } = payload;
        this.activeUsers.delete(user_id);
        
        this.triggerEvent('userLeft', { userId: user_id });
        this.updateActiveUsers();
    }

    handleUserActivity(payload) {
        const { user_id, activity_type, timestamp } = payload;
        
        this.triggerEvent('userActivity', { 
            userId: user_id, 
            activityType: activity_type, 
            timestamp 
        });
    }

    handleFloorLockAcquired(payload) {
        const { user_id, floor_id, timestamp } = payload;
        
        this.triggerEvent('floorLockAcquired', { 
            userId: user_id, 
            floorId: floor_id, 
            timestamp 
        });
    }

    handleFloorLockReleased(payload) {
        const { floor_id, timestamp } = payload;
        
        this.triggerEvent('floorLockReleased', { 
            floorId: floor_id, 
            timestamp 
        });
    }

    handleLiveUpdate(payload) {
        const { user_id, update_type, data, timestamp } = payload;
        
        // Store live update
        this.liveUpdates.set(`${user_id}_${timestamp}`, {
            userId: user_id,
            updateType: update_type,
            data,
            timestamp
        });
        
        this.triggerEvent('liveUpdate', { 
            userId: user_id, 
            updateType: update_type, 
            data, 
            timestamp 
        });
    }

    handleConflictDetected(payload) {
        const { conflicts, timestamp } = payload;
        
        this.triggerEvent('conflictDetected', { 
            conflicts, 
            timestamp 
        });
    }

    handlePresenceUpdate(payload) {
        const { users } = payload;
        
        // Update active users
        users.forEach(user => {
            this.activeUsers.set(user.id, user);
        });
        
        this.triggerEvent('presenceUpdate', { users });
        this.updateActiveUsers();
    }

    handleHeartbeat(payload) {
        // Respond to heartbeat
        this.sendMessage({
            type: 'heartbeat_response',
            payload: { timestamp: Date.now() }
        });
    }

    // Message sending methods
    sendMessage(message) {
        if (!this.isConnected || !this.websocket) {
            console.warn('WebSocket not connected, cannot send message');
            return;
        }
        
        try {
            this.websocket.send(JSON.stringify(message));
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
        }
    }

    sendJoinMessage() {
        this.sendMessage({
            type: 'join_floor',
            payload: {
                user: this.currentUser,
                floor_id: this.currentFloor?.id
            }
        });
    }

    sendLeaveMessage() {
        this.sendMessage({
            type: 'leave_floor',
            payload: {
                user_id: this.currentUser?.id,
                floor_id: this.currentFloor?.id
            }
        });
    }

    sendUserActivity() {
        this.sendMessage({
            type: 'user_activity',
            payload: {
                user_id: this.currentUser?.id,
                activity_type: 'interaction',
                timestamp: Date.now()
            }
        });
    }

    sendFloorLockRequest() {
        this.sendMessage({
            type: 'request_floor_lock',
            payload: {
                user_id: this.currentUser?.id,
                floor_id: this.currentFloor?.id,
                timestamp: Date.now()
            }
        });
    }

    sendFloorLockRelease() {
        this.sendMessage({
            type: 'release_floor_lock',
            payload: {
                user_id: this.currentUser?.id,
                floor_id: this.currentFloor?.id,
                timestamp: Date.now()
            }
        });
    }

    sendLiveUpdate(updateType, data) {
        this.sendMessage({
            type: 'live_update',
            payload: {
                user_id: this.currentUser?.id,
                floor_id: this.currentFloor?.id,
                update_type: updateType,
                data,
                timestamp: Date.now()
            }
        });
    }

    // Floor selection handling
    async handleFloorSelection(floorData) {
        // Leave current floor if any
        if (this.currentFloor) {
            this.sendLeaveMessage();
        }
        
        this.currentFloor = floorData;
        
        // Join new floor
        if (this.isConnected) {
            this.sendJoinMessage();
        }
        
        this.triggerEvent('floorChanged', { floor: floorData });
    }

    // User activity handling
    sendUserActivity() {
        if (this.isConnected) {
            this.sendUserActivity();
        }
    }

    handlePageHidden() {
        // Send away status
        this.sendMessage({
            type: 'user_status',
            payload: {
                user_id: this.currentUser?.id,
                status: 'away',
                timestamp: Date.now()
            }
        });
    }

    handlePageVisible() {
        // Send back status
        this.sendMessage({
            type: 'user_status',
            payload: {
                user_id: this.currentUser?.id,
                status: 'active',
                timestamp: Date.now()
            }
        });
    }

    // Timer management
    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            this.sendMessage({
                type: 'heartbeat',
                payload: { timestamp: Date.now() }
            });
        }, this.options.heartbeatInterval);
    }

    clearTimers() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    // Reconnection handling
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.triggerEvent('reconnectFailed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.options.reconnectInterval * this.reconnectAttempts;
        
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
        
        this.triggerEvent('reconnecting', { attempt: this.reconnectAttempts });
    }

    // User management
    setCurrentUser(user) {
        this.currentUser = user;
    }

    getCurrentUser() {
        return this.currentUser;
    }

    getActiveUsers() {
        return Array.from(this.activeUsers.values());
    }

    getActiveUsersCount() {
        return this.activeUsers.size;
    }

    updateActiveUsers() {
        this.triggerEvent('activeUsersUpdated', { 
            users: this.getActiveUsers(),
            count: this.getActiveUsersCount()
        });
    }

    // Live updates management
    getLiveUpdates() {
        return Array.from(this.liveUpdates.values());
    }

    clearLiveUpdates() {
        this.liveUpdates.clear();
    }

    // Connection status
    isConnected() {
        return this.isConnected;
    }

    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            activeUsers: this.getActiveUsersCount()
        };
    }

    // Utility methods
    generateSessionId() {
        return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
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
                    handler({ ...data, realtime: this });
                } catch (error) {
                    console.error(`Error in realtime event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.disconnect();
        this.activeUsers.clear();
        this.liveUpdates.clear();
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 