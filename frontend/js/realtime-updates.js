/**
 * Arxos Real-time Updates System
 * Provides WebSocket-based live synchronization of building data
 */

class ArxosRealtimeUpdates {
    constructor(options = {}) {
        this.options = {
            serverUrl: options.serverUrl || 'ws://localhost:8081',
            reconnectInterval: options.reconnectInterval || 5000,
            maxReconnectAttempts: options.maxReconnectAttempts || 10,
            heartbeatInterval: options.heartbeatInterval || 30000,
            ...options
        };
        
        // Connection state
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.heartbeatTimer = null;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        // Message queue for offline scenarios
        this.messageQueue = [];
        this.maxQueueSize = 1000;
        
        // Subscriptions for different data types
        this.subscriptions = new Map();
        
        // Performance monitoring
        this.metrics = {
            messagesSent: 0,
            messagesReceived: 0,
            bytesSent: 0,
            bytesReceived: 0,
            reconnections: 0,
            lastMessageTime: null,
            connectionUptime: 0
        };
        
        // Initialize connection
        this.connect();
    }
    
    connect() {
        try {
            console.log(`Connecting to Arxos WebSocket server: ${this.options.serverUrl}`);
            
            this.websocket = new WebSocket(this.options.serverUrl);
            this._setupWebSocketHandlers();
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this._scheduleReconnect();
        }
    }
    
    _setupWebSocketHandlers() {
        this.websocket.onopen = (event) => {
            this._onConnectionOpen(event);
        };
        
        this.websocket.onmessage = (event) => {
            this._onMessage(event);
        };
        
        this.websocket.onclose = (event) => {
            this._onConnectionClose(event);
        };
        
        this.websocket.onerror = (event) => {
            this._onConnectionError(event);
        };
    }
    
    _onConnectionOpen(event) {
        console.log('WebSocket connection established');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.connectionStartTime = Date.now();
        
        // Start heartbeat
        this._startHeartbeat();
        
        // Process queued messages
        this._processMessageQueue();
        
        // Restore subscriptions
        this._restoreSubscriptions();
        
        // Emit connection event
        this._emitEvent('connected', { timestamp: Date.now() });
        
        // Update metrics
        this.metrics.reconnections++;
    }
    
    _onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this._handleMessage(message);
            
            // Update metrics
            this.metrics.messagesReceived++;
            this.metrics.bytesReceived += event.data.length;
            this.metrics.lastMessageTime = Date.now();
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }
    
    _onConnectionClose(event) {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnected = false;
        
        // Stop heartbeat
        this._stopHeartbeat();
        
        // Calculate uptime
        if (this.connectionStartTime) {
            this.metrics.connectionUptime += Date.now() - this.connectionStartTime;
        }
        
        // Emit disconnection event
        this._emitEvent('disconnected', { 
            code: event.code, 
            reason: event.reason,
            timestamp: Date.now()
        });
        
        // Attempt reconnection if not a clean close
        if (event.code !== 1000) {
            this._scheduleReconnect();
        }
    }
    
    _onConnectionError(event) {
        console.error('WebSocket connection error:', event);
        this._emitEvent('error', { error: event, timestamp: Date.now() });
    }
    
    _handleMessage(message) {
        const { type, data, timestamp, buildingId, objectId } = message;
        
        console.log(`Received message: ${type}`, { buildingId, objectId, timestamp });
        
        // Handle different message types
        switch (type) {
            case 'building_update':
                this._handleBuildingUpdate(data);
                break;
                
            case 'object_update':
                this._handleObjectUpdate(data);
                break;
                
            case 'object_deleted':
                this._handleObjectDeleted(data);
                break;
                
            case 'validation_update':
                this._handleValidationUpdate(data);
                break;
                
            case 'alert':
                this._handleAlert(data);
                break;
                
            case 'heartbeat':
                this._handleHeartbeat(data);
                break;
                
            case 'subscription_confirmed':
                this._handleSubscriptionConfirmed(data);
                break;
                
            default:
                console.warn(`Unknown message type: ${type}`);
        }
        
        // Emit generic message event
        this._emitEvent('message', { type, data, timestamp });
    }
    
    _handleBuildingUpdate(data) {
        const { buildingId, changes, timestamp } = data;
        
        // Emit building update event
        this._emitEvent('buildingUpdate', {
            buildingId,
            changes,
            timestamp
        });
        
        // Update local building data if available
        if (window.arxosBuildingData && window.arxosBuildingData.buildingId === buildingId) {
            this._applyBuildingChanges(window.arxosBuildingData, changes);
        }
    }
    
    _handleObjectUpdate(data) {
        const { objectId, buildingId, properties, timestamp } = data;
        
        // Emit object update event
        this._emitEvent('objectUpdate', {
            objectId,
            buildingId,
            properties,
            timestamp
        });
        
        // Update 3D renderer if available
        if (window.arxosRenderer) {
            this._updateRendererObject(objectId, properties);
        }
    }
    
    _handleObjectDeleted(data) {
        const { objectId, buildingId, timestamp } = data;
        
        // Emit object deleted event
        this._emitEvent('objectDeleted', {
            objectId,
            buildingId,
            timestamp
        });
        
        // Remove from 3D renderer if available
        if (window.arxosRenderer) {
            window.arxosRenderer.removeObject(objectId);
        }
    }
    
    _handleValidationUpdate(data) {
        const { objectId, buildingId, validation, confidence, timestamp } = data;
        
        // Emit validation update event
        this._emitEvent('validationUpdate', {
            objectId,
            buildingId,
            validation,
            confidence,
            timestamp
        });
        
        // Update confidence indicators in UI
        this._updateConfidenceIndicator(objectId, confidence);
    }
    
    _handleAlert(data) {
        const { alertId, type, message, severity, timestamp } = data;
        
        // Emit alert event
        this._emitEvent('alert', {
            alertId,
            type,
            message,
            severity,
            timestamp
        });
        
        // Show alert in UI
        this._showAlert(type, message, severity);
    }
    
    _handleHeartbeat(data) {
        // Respond to heartbeat
        this.sendMessage({
            type: 'heartbeat_response',
            timestamp: Date.now()
        });
    }
    
    _handleSubscriptionConfirmed(data) {
        const { subscriptionId, status, message } = data;
        console.log(`Subscription confirmed: ${subscriptionId} - ${status}`);
    }
    
    _applyBuildingChanges(buildingData, changes) {
        // Apply changes to local building data
        changes.forEach(change => {
            const { path, value, operation } = change;
            
            switch (operation) {
                case 'set':
                    this._setNestedProperty(buildingData, path, value);
                    break;
                    
                case 'delete':
                    this._deleteNestedProperty(buildingData, path);
                    break;
                    
                case 'add':
                    this._addToArray(buildingData, path, value);
                    break;
                    
                case 'remove':
                    this._removeFromArray(buildingData, path, value);
                    break;
            }
        });
        
        // Trigger UI update
        this._emitEvent('buildingDataChanged', { buildingData, changes });
    }
    
    _setNestedProperty(obj, path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            if (!(key in current)) {
                current[key] = {};
            }
            return current[key];
        }, obj);
        
        target[lastKey] = value;
    }
    
    _deleteNestedProperty(obj, path) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            return current && current[key];
        }, obj);
        
        if (target && lastKey in target) {
            delete target[lastKey];
        }
    }
    
    _addToArray(obj, path, value) {
        const target = this._getNestedProperty(obj, path);
        if (Array.isArray(target)) {
            target.push(value);
        }
    }
    
    _removeFromArray(obj, path, value) {
        const target = this._getNestedProperty(obj, path);
        if (Array.isArray(target)) {
            const index = target.indexOf(value);
            if (index > -1) {
                target.splice(index, 1);
            }
        }
    }
    
    _getNestedProperty(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key];
        }, obj);
    }
    
    _updateRendererObject(objectId, properties) {
        try {
            const object = window.arxosRenderer.getObjectById(objectId);
            if (object) {
                // Update object properties
                Object.entries(properties).forEach(([key, value]) => {
                    if (key === 'position' && Array.isArray(value)) {
                        object.position.set(value[0], value[1], value[2]);
                    } else if (key === 'rotation' && Array.isArray(value)) {
                        object.rotation.set(value[0], value[1], value[2]);
                    } else if (key === 'scale' && Array.isArray(value)) {
                        object.scale.set(value[0], value[1], value[2]);
                    } else if (key === 'material' && object.material) {
                        if (typeof value === 'string') {
                            object.material.color.setHex(parseInt(value.replace('#', '0x')));
                        }
                    } else {
                        // Store in userData for custom properties
                        object.userData[key] = value;
                    }
                });
                
                // Trigger render update
                window.arxosRenderer.render();
            }
        } catch (error) {
            console.error('Failed to update renderer object:', error);
        }
    }
    
    _updateConfidenceIndicator(objectId, confidence) {
        // Find confidence indicator in UI
        const indicator = document.querySelector(`[data-object-id="${objectId}"] .confidence-indicator`);
        if (indicator) {
            // Update confidence display
            indicator.textContent = `${Math.round(confidence * 100)}%`;
            indicator.className = `confidence-indicator confidence-${this._getConfidenceClass(confidence)}`;
        }
    }
    
    _getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'high';
        if (confidence >= 0.6) return 'medium';
        if (confidence >= 0.4) return 'low';
        return 'very-low';
    }
    
    _showAlert(type, message, severity) {
        // Create alert element
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${severity} alert-${type}`;
        alertElement.innerHTML = `
            <div class="alert-content">
                <span class="alert-message">${message}</span>
                <button class="alert-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add to alert container
        const alertContainer = document.getElementById('alert-container') || document.body;
        alertContainer.appendChild(alertElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertElement.parentElement) {
                alertElement.remove();
            }
        }, 5000);
    }
    
    _startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected) {
                this.sendMessage({
                    type: 'heartbeat',
                    timestamp: Date.now()
                });
            }
        }, this.options.heartbeatInterval);
    }
    
    _stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
    
    _scheduleReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this._emitEvent('maxReconnectAttemptsReached', { 
                attempts: this.reconnectAttempts 
            });
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.options.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
        
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    _processMessageQueue() {
        if (this.messageQueue.length === 0) return;
        
        console.log(`Processing ${this.messageQueue.length} queued messages`);
        
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.sendMessage(message);
        }
    }
    
    _restoreSubscriptions() {
        // Restore all active subscriptions
        this.subscriptions.forEach((subscription, id) => {
            this.sendMessage({
                type: 'subscribe',
                subscriptionId: id,
                ...subscription
            });
        });
    }
    
    // Public API methods
    
    sendMessage(message) {
        if (!this.isConnected) {
            // Queue message for later
            if (this.messageQueue.length < this.maxQueueSize) {
                this.messageQueue.push(message);
                console.log('Message queued (offline):', message.type);
            } else {
                console.warn('Message queue full, dropping message:', message.type);
            }
            return false;
        }
        
        try {
            const messageStr = JSON.stringify(message);
            this.websocket.send(messageStr);
            
            // Update metrics
            this.metrics.messagesSent++;
            this.metrics.bytesSent += messageStr.length;
            
            return true;
        } catch (error) {
            console.error('Failed to send message:', error);
            return false;
        }
    }
    
    subscribe(buildingId, objectTypes = [], callback = null) {
        const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        const subscription = {
            buildingId,
            objectTypes,
            callback
        };
        
        this.subscriptions.set(subscriptionId, subscription);
        
        // Send subscription request
        this.sendMessage({
            type: 'subscribe',
            subscriptionId,
            buildingId,
            objectTypes
        });
        
        // Set up event handler if callback provided
        if (callback) {
            this.on('objectUpdate', (data) => {
                if (data.buildingId === buildingId && 
                    (objectTypes.length === 0 || objectTypes.includes(data.objectType))) {
                    callback(data);
                }
            });
        }
        
        return subscriptionId;
    }
    
    unsubscribe(subscriptionId) {
        if (this.subscriptions.has(subscriptionId)) {
            // Send unsubscribe request
            this.sendMessage({
                type: 'unsubscribe',
                subscriptionId
            });
            
            // Remove subscription
            this.subscriptions.delete(subscriptionId);
            
            return true;
        }
        return false;
    }
    
    // Event handling
    
    on(eventName, handler) {
        if (!this.eventHandlers.has(eventName)) {
            this.eventHandlers.set(eventName, []);
        }
        this.eventHandlers.get(eventName).push(handler);
    }
    
    off(eventName, handler) {
        if (this.eventHandlers.has(eventName)) {
            const handlers = this.eventHandlers.get(eventName);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    _emitEvent(eventName, data) {
        if (this.eventHandlers.has(eventName)) {
            this.eventHandlers.get(eventName).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventName}:`, error);
                }
            });
        }
        
        // Also emit as DOM event
        const event = new CustomEvent(`arxos:${eventName}`, { detail: data });
        document.dispatchEvent(event);
    }
    
    // Utility methods
    
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            uptime: this.metrics.connectionUptime,
            lastMessageTime: this.metrics.lastMessageTime
        };
    }
    
    getMetrics() {
        return { ...this.metrics };
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close(1000, 'Client disconnect');
        }
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
    
    // Building-specific methods
    
    subscribeToBuilding(buildingId, callback = null) {
        return this.subscribe(buildingId, [], callback);
    }
    
    subscribeToObjectType(buildingId, objectType, callback = null) {
        return this.subscribe(buildingId, [objectType], callback);
    }
    
    subscribeToObject(buildingId, objectId, callback = null) {
        // Subscribe to specific object updates
        const subscriptionId = `obj_${objectId}_${Date.now()}`;
        
        this.on('objectUpdate', (data) => {
            if (data.buildingId === buildingId && data.objectId === objectId) {
                callback(data);
            }
        });
        
        return subscriptionId;
    }
    
    // Real-time building operations
    
    updateObject(buildingId, objectId, properties) {
        return this.sendMessage({
            type: 'update_object',
            buildingId,
            objectId,
            properties,
            timestamp: Date.now()
        });
    }
    
    deleteObject(buildingId, objectId) {
        return this.sendMessage({
            type: 'delete_object',
            buildingId,
            objectId,
            timestamp: Date.now()
        });
    }
    
    validateObject(buildingId, objectId, validation, confidence) {
        return this.sendMessage({
            type: 'validate_object',
            buildingId,
            objectId,
            validation,
            confidence,
            timestamp: Date.now()
        });
    }
    
    // Performance monitoring
    
    startPerformanceMonitoring() {
        this.performanceInterval = setInterval(() => {
            const metrics = this.getMetrics();
            const status = this.getConnectionStatus();
            
            console.log('Arxos Realtime Performance:', {
                connection: status,
                metrics: metrics,
                queueSize: this.messageQueue.length,
                subscriptions: this.subscriptions.size
            });
            
            // Emit performance event
            this._emitEvent('performance', { metrics, status });
            
        }, 60000); // Every minute
    }
    
    stopPerformanceMonitoring() {
        if (this.performanceInterval) {
            clearInterval(this.performanceInterval);
            this.performanceInterval = null;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxosRealtimeUpdates;
}
