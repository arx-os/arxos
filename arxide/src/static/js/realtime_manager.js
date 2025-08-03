/**
 * Real-time Manager for Arxos Platform
 * Handles WebSocket connections, user presence, collaborative editing, and cache management
 */

class RealTimeManager {
    constructor() {
        this.websocket = null;
        this.userId = null;
        this.username = null;
        this.currentRoom = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.presenceUpdateInterval = null;
        
        // Event listeners
        this.eventListeners = {
            'connection': [],
            'disconnection': [],
            'user_joined': [],
            'user_left': [],
            'presence_update': [],
            'lock_acquired': [],
            'lock_released': [],
            'conflict_detected': [],
            'conflict_resolved': [],
            'broadcast': [],
            'error': []
        };
        
        // Collaborative editing state
        this.activeLocks = new Map();
        this.conflicts = new Map();
        this.roomUsers = new Map();
        
        // Cache management
        this.cacheStats = null;
        this.preloadQueue = [];
        
        // Initialize
        this.init();
    }
    
    init() {
        // Get user info from session/localStorage
        this.userId = localStorage.getItem('user_id') || this.generateUserId();
        this.username = localStorage.getItem('username') || `User_${this.userId}`;
        
        // Save user info
        localStorage.setItem('user_id', this.userId);
        localStorage.setItem('username', this.username);
        
        // Setup event listeners
        this.setupEventListeners();
        
        window.arxLogger.info('RealTimeManager initialized for user:', this.username, { file: 'realtime_manager.js' });
    }
    
    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupEventListeners() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.updatePresence({ current_action: 'away' });
            } else {
                this.updatePresence({ current_action: 'active' });
            }
        });
        
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
        
        // Handle mouse movement for cursor position
        let cursorTimeout;
        document.addEventListener('mousemove', (e) => {
            clearTimeout(cursorTimeout);
            cursorTimeout = setTimeout(() => {
                this.updatePresence({
                    cursor_position: [e.clientX, e.clientY]
                });
            }, 100);
        });
    }
    
    async connect() {
        if (this.isConnected) {
            window.arxLogger.info('Already connected', { file: 'realtime_manager.js' });
            return;
        }
        
        try {
            const wsUrl = `ws://${window.location.host}/v1/realtime/ws/${this.userId}`;
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                window.arxLogger.info('WebSocket connected', { file: 'realtime_manager.js' });
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                this.startPresenceUpdates();
                this.emit('connection');
            };
            
            this.websocket.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                window.arxLogger.warning('WebSocket disconnected', { file: 'realtime_manager.js' });
                this.isConnected = false;
                this.stopHeartbeat();
                this.stopPresenceUpdates();
                this.emit('disconnection');
                this.handleReconnection();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error('Failed to connect:', error);
            this.emit('error', error);
        }
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
        this.stopHeartbeat();
        this.stopPresenceUpdates();
    }
    
    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            window.arxLogger.warning(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`, { file: 'realtime_manager.js' });
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.emit('error', new Error('Max reconnection attempts reached'));
        }
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.sendMessage({
                    type: 'heartbeat',
                    timestamp: new Date().toISOString()
                });
            }
        }, 30000); // 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    startPresenceUpdates() {
        this.presenceUpdateInterval = setInterval(() => {
            if (this.isConnected) {
                this.updatePresence();
            }
        }, 10000); // 10 seconds
    }
    
    stopPresenceUpdates() {
        if (this.presenceUpdateInterval) {
            clearInterval(this.presenceUpdateInterval);
            this.presenceUpdateInterval = null;
        }
    }
    
    sendMessage(message) {
        if (this.websocket && this.isConnected) {
            this.websocket.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, message not sent:', message);
        }
    }
    
    handleMessage(message) {
        window.arxLogger.debug('Received message:', message, { file: 'realtime_manager.js' });
        
        switch (message.type) {
            case 'connection_established':
                this.handleConnectionEstablished(message);
                break;
                
            case 'user_joined_room':
                this.handleUserJoinedRoom(message);
                break;
                
            case 'user_left_room':
                this.handleUserLeftRoom(message);
                break;
                
            case 'presence_updated':
                this.handlePresenceUpdated(message);
                break;
                
            case 'lock_acquired':
                this.handleLockAcquired(message);
                break;
                
            case 'lock_released':
                this.handleLockReleased(message);
                break;
                
            case 'conflict_detected':
                this.handleConflictDetected(message);
                break;
                
            case 'conflict_resolved':
                this.handleConflictResolved(message);
                break;
                
            case 'broadcast':
                this.handleBroadcast(message);
                break;
                
            case 'room_state':
                this.handleRoomState(message);
                break;
                
            case 'error':
                this.handleError(message);
                break;
                
            default:
                console.warn('Unknown message type:', message.type);
        }
    }
    
    handleConnectionEstablished(message) {
        window.arxLogger.info('Connection established:', message, { file: 'realtime_manager.js' });
        this.emit('connection', message);
    }
    
    handleUserJoinedRoom(message) {
        window.arxLogger.info('User joined room:', message, { file: 'realtime_manager.js' });
        this.emit('user_joined', message);
        this.updateRoomUsers(message.room_id);
    }
    
    handleUserLeftRoom(message) {
        window.arxLogger.info('User left room:', message, { file: 'realtime_manager.js' });
        this.emit('user_left', message);
        this.updateRoomUsers(message.room_id);
    }
    
    handlePresenceUpdated(message) {
        window.arxLogger.debug('Presence updated:', message, { file: 'realtime_manager.js' });
        this.emit('presence_update', message);
    }
    
    handleLockAcquired(message) {
        window.arxLogger.info('Lock acquired:', message, { file: 'realtime_manager.js' });
        this.activeLocks.set(message.lock_id, message);
        this.emit('lock_acquired', message);
    }
    
    handleLockReleased(message) {
        window.arxLogger.info('Lock released:', message, { file: 'realtime_manager.js' });
        this.activeLocks.delete(message.lock_id);
        this.emit('lock_released', message);
    }
    
    handleConflictDetected(message) {
        window.arxLogger.warning('Conflict detected:', message, { file: 'realtime_manager.js' });
        this.conflicts.set(message.conflict_id, message);
        this.emit('conflict_detected', message);
        this.showConflictNotification(message);
    }
    
    handleConflictResolved(message) {
        window.arxLogger.info('Conflict resolved:', message, { file: 'realtime_manager.js' });
        this.conflicts.delete(message.conflict_id);
        this.emit('conflict_resolved', message);
        this.showConflictResolutionNotification(message);
    }
    
    handleBroadcast(message) {
        window.arxLogger.debug('Broadcast received:', message, { file: 'realtime_manager.js' });
        this.emit('broadcast', message);
    }
    
    handleRoomState(message) {
        window.arxLogger.debug('Room state received:', message, { file: 'realtime_manager.js' });
        this.roomUsers.set(message.room_id, message.users);
        this.activeLocks.clear();
        message.locks.forEach(lock => {
            this.activeLocks.set(lock.lock_id, lock);
        });
    }
    
    handleError(message) {
        console.error('Error received:', message);
        this.emit('error', message);
        this.showErrorNotification(message);
    }
    
    async joinRoom(roomId) {
        if (!this.isConnected) {
            await this.connect();
        }
        
        this.sendMessage({
            type: 'join_room',
            room_id: roomId
        });
        
        this.currentRoom = roomId;
        window.arxLogger.info('Joined room:', roomId, { file: 'realtime_manager.js' });
    }
    
    leaveRoom(roomId) {
        this.sendMessage({
            type: 'leave_room',
            room_id: roomId
        });
        
        if (this.currentRoom === roomId) {
            this.currentRoom = null;
        }
        
        window.arxLogger.info('Left room:', roomId, { file: 'realtime_manager.js' });
    }
    
    updatePresence(data = {}) {
        const presenceData = {
            type: 'update_presence',
            floor_id: this.currentRoom,
            current_action: data.current_action || 'active',
            cursor_position: data.cursor_position,
            metadata: data.metadata || {}
        };
        
        this.sendMessage(presenceData);
    }
    
    async acquireLock(lockType, resourceId, metadata = {}) {
        const message = {
            type: 'acquire_lock',
            lock_type: lockType,
            resource_id: resourceId,
            metadata: metadata
        };
        
        this.sendMessage(message);
        
        // Return a promise that resolves when lock is acquired
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Lock acquisition timeout'));
            }, 10000);
            
            const handleLockResponse = (event) => {
                if (event.detail.type === 'lock_response') {
                    clearTimeout(timeout);
                    this.removeEventListener('lock_acquired', handleLockResponse);
                    
                    if (event.detail.success) {
                        resolve(event.detail.lock_id);
                    } else {
                        reject(new Error(event.detail.result));
                    }
                }
            };
            
            this.addEventListener('lock_acquired', handleLockResponse);
        });
    }
    
    releaseLock(lockId) {
        this.sendMessage({
            type: 'release_lock',
            lock_id: lockId
        });
    }
    
    async resolveConflict(conflictId, resolution) {
        const message = {
            type: 'resolve_conflict',
            conflict_id: conflictId,
            resolution: resolution
        };
        
        this.sendMessage(message);
    }
    
    broadcast(message, roomId = null) {
        this.sendMessage({
            type: 'broadcast',
            room_id: roomId || this.currentRoom,
            message: message
        });
    }
    
    async getRoomUsers(roomId) {
        try {
            const response = await fetch(`/v1/realtime/room-users/${roomId}`);
            const data = await response.json();
            return data.users;
        } catch (error) {
            console.error('Failed to get room users:', error);
            return [];
        }
    }
    
    async getActiveLocks(resourceId) {
        try {
            const response = await fetch(`/v1/realtime/active-locks/${resourceId}`);
            const data = await response.json();
            return data.locks;
        } catch (error) {
            console.error('Failed to get active locks:', error);
            return [];
        }
    }
    
    async getCacheStats() {
        try {
            const response = await fetch('/v1/realtime/cache-stats');
            const data = await response.json();
            this.cacheStats = data.cache_stats;
            return this.cacheStats;
        } catch (error) {
            console.error('Failed to get cache stats:', error);
            return null;
        }
    }
    
    async preloadFloorData(floorId) {
        try {
            const response = await fetch('/v1/realtime/preload-floor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ floor_id: floorId })
            });
            
            const data = await response.json();
            window.arxLogger.info('Floor data preloaded:', data, { file: 'realtime_manager.js' });
            return data.success;
        } catch (error) {
            console.error('Failed to preload floor data:', error);
            return false;
        }
    }
    
    async invalidateFloorCache(floorId) {
        try {
            const response = await fetch('/v1/realtime/invalidate-floor-cache', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ floor_id: floorId })
            });
            
            const data = await response.json();
            window.arxLogger.info('Floor cache invalidated:', data, { file: 'realtime_manager.js' });
            return data.count;
        } catch (error) {
            console.error('Failed to invalidate floor cache:', error);
            return 0;
        }
    }
    
    updateRoomUsers(roomId) {
        this.getRoomUsers(roomId).then(users => {
            this.roomUsers.set(roomId, users);
        });
    }
    
    showConflictNotification(conflict) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'conflict-notification';
        notification.innerHTML = `
            <div class="conflict-header">
                <h4>Conflict Detected</h4>
                <button class="close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="conflict-content">
                <p><strong>Type:</strong> ${conflict.conflict_type}</p>
                <p><strong>Severity:</strong> ${conflict.severity}</p>
                <p><strong>Description:</strong> ${conflict.description}</p>
                <p><strong>Users:</strong> ${conflict.user_id_1}, ${conflict.user_id_2}</p>
            </div>
            <div class="conflict-actions">
                <button onclick="resolveConflict('${conflict.conflict_id}', 'accept_mine')">Accept Mine</button>
                <button onclick="resolveConflict('${conflict.conflict_id}', 'accept_theirs')">Accept Theirs</button>
                <button onclick="resolveConflict('${conflict.conflict_id}', 'merge')">Merge</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 30000);
    }
    
    showConflictResolutionNotification(resolution) {
        const notification = document.createElement('div');
        notification.className = 'conflict-resolution-notification';
        notification.innerHTML = `
            <div class="conflict-header">
                <h4>Conflict Resolved</h4>
                <button class="close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="conflict-content">
                <p><strong>Resolution:</strong> ${resolution.resolution}</p>
                <p><strong>Resolved by:</strong> ${resolution.resolved_by}</p>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    showErrorNotification(error) {
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.innerHTML = `
            <div class="error-header">
                <h4>Error</h4>
                <button class="close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
            <div class="error-content">
                <p>${error.message || 'An error occurred'}</p>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Event system
    addEventListener(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }
    
    removeEventListener(event, callback) {
        if (this.eventListeners[event]) {
            const index = this.eventListeners[event].indexOf(callback);
            if (index > -1) {
                this.eventListeners[event].splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in event listener:', error);
                }
            });
        }
        
        // Also dispatch custom event
        const customEvent = new CustomEvent(event, { detail: data });
        document.dispatchEvent(customEvent);
    }
    
    // Utility methods
    isLocked(resourceId, lockType) {
        for (const [lockId, lock] of this.activeLocks) {
            if (lock.resource_id === resourceId && lock.lock_type === lockType) {
                return lock;
            }
        }
        return null;
    }
    
    hasConflict(resourceId) {
        for (const [conflictId, conflict] of this.conflicts) {
            if (conflict.resource_id === resourceId && !conflict.resolved) {
                return conflict;
            }
        }
        return null;
    }
    
    getRoomUserCount(roomId) {
        const users = this.roomUsers.get(roomId);
        return users ? users.length : 0;
    }
    
    getCurrentUser() {
        return {
            id: this.userId,
            username: this.username
        };
    }
}

// Global instance
window.realtimeManager = new RealTimeManager();

// Helper functions for conflict resolution
window.resolveConflict = function(conflictId, resolution) {
    window.realtimeManager.resolveConflict(conflictId, resolution);
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealTimeManager;
} 