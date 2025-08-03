/**
 * WebSocket Manager for Arxos Platform
 * Handles real-time communication, collaboration, and live updates
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.subscribers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectTimeout = null;
        this.currentCanvasId = null;
        this.currentSessionId = null;
    }

    connect(canvasId, sessionId) {
        if (this.isConnected || this.isConnecting) return;

        this.currentCanvasId = canvasId;
        this.currentSessionId = sessionId;
        this.isConnecting = true;

        const token = localStorage.getItem('access_token');
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/runtime/events?canvas_id=${canvasId}&session_id=${sessionId}&token=${token}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.isConnecting = false;
            this.reconnectAttempts = 0;

            // Send handshake
            this.sendMessage({
                event_type: 'handshake',
                canvas_id: canvasId,
                session_id: sessionId,
                user_id: window.authManager?.user?.user_id
            });

            window.toastManager.show('Connected to collaboration server', 'success');
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.ws.onclose = () => {
            this.isConnected = false;
            this.handleDisconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnected = false;
        };
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.isConnecting = false;
        this.currentCanvasId = null;
        this.currentSessionId = null;
        
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
    }

    sendMessage(message) {
        if (this.ws && this.isConnected) {
            this.ws.send(JSON.stringify(message));
        }
    }

    subscribe(eventType, callback) {
        if (!this.subscribers.has(eventType)) {
            this.subscribers.set(eventType, new Set());
        }
        this.subscribers.get(eventType).add(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.subscribers.get(eventType);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }

    handleMessage(message) {
        const callbacks = this.subscribers.get(message.type);
        if (callbacks) {
            callbacks.forEach(callback => callback(message.data));
        }

        // Handle specific message types
        switch (message.type) {
            case 'handshake_ack':
                console.log('Handshake acknowledged');
                break;
            
            case 'lock_acquired':
                this.handleLockAcquired(message.data);
                break;
            
            case 'lock_released':
                this.handleLockReleased(message.data);
                break;
            
            case 'object_updated':
                this.handleObjectUpdate(message.data);
                break;
            
            case 'user_activity':
                this.handleUserActivity(message.data);
                break;
            
            case 'collaboration_error':
                window.toastManager.show(message.data.message, 'error');
                break;
        }
    }

    handleLockAcquired(data) {
        const { object_id, user_id } = data;
        const element = document.querySelector(`[data-svgx-id="${object_id}"]`);
        if (element) {
            element.setAttribute('data-locked-by', user_id);
            element.classList.add('locked');
        }
    }

    handleLockReleased(data) {
        const { object_id } = data;
        const element = document.querySelector(`[data-svgx-id="${object_id}"]`);
        if (element) {
            element.removeAttribute('data-locked-by');
            element.classList.remove('locked');
        }
    }

    handleObjectUpdate(data) {
        const { object_id, updates } = data;
        const element = document.querySelector(`[data-svgx-id="${object_id}"]`);
        if (element) {
            Object.entries(updates).forEach(([attr, value]) => {
                element.setAttribute(attr, value);
            });
        }
    }

    handleUserActivity(data) {
        // Update user presence indicators
        const presenceContainer = document.getElementById('active-users');
        if (presenceContainer) {
            this.updateUserPresence(presenceContainer, data.users);
        }
    }

    updateUserPresence(container, users) {
        container.innerHTML = users.map(user => `
            <div class="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                <span class="text-sm">${user.username}</span>
                ${user.activity ? `<span class="text-xs text-gray-500">${user.activity}</span>` : ''}
            </div>
        `).join('');
    }

    handleDisconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.reconnectTimeout = setTimeout(() => {
                if (this.currentCanvasId && this.currentSessionId) {
                    this.connect(this.currentCanvasId, this.currentSessionId);
                }
            }, 1000 * Math.pow(2, this.reconnectAttempts));
        } else {
            window.toastManager.show('Connection lost. Please refresh the page.', 'error');
        }
    }

    // Canvas-specific methods
    sendObjectUpdate(objectId, updates) {
        this.sendMessage({
            event_type: 'object_update',
            canvas_id: this.currentCanvasId,
            object_id: objectId,
            data: updates
        });
    }

    requestLock(objectId) {
        this.sendMessage({
            event_type: 'lock_request',
            canvas_id: this.currentCanvasId,
            object_id: objectId,
            user_id: window.authManager?.user?.user_id
        });
    }

    releaseLock(objectId) {
        this.sendMessage({
            event_type: 'lock_release',
            canvas_id: this.currentCanvasId,
            object_id: objectId,
            user_id: window.authManager?.user?.user_id
        });
    }

    sendUserActivity(activity) {
        this.sendMessage({
            event_type: 'user_activity',
            canvas_id: this.currentCanvasId,
            user_id: window.authManager?.user?.user_id,
            activity: activity
        });
    }

    // SVGX Engine specific methods
    sendSVGXUpdate(svgxData) {
        this.sendMessage({
            event_type: 'svgx_update',
            canvas_id: this.currentCanvasId,
            data: svgxData
        });
    }

    sendPhysicsUpdate(physicsData) {
        this.sendMessage({
            event_type: 'physics_update',
            canvas_id: this.currentCanvasId,
            data: physicsData
        });
    }

    // Connection status methods
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            reconnectAttempts: this.reconnectAttempts,
            currentCanvasId: this.currentCanvasId
        };
    }

    // Utility methods
    isReady() {
        return this.isConnected && !this.isConnecting;
    }

    getConnectionInfo() {
        return {
            canvasId: this.currentCanvasId,
            sessionId: this.currentSessionId,
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

// Export for global use
window.WebSocketManager = WebSocketManager; 