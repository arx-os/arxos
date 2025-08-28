/**
 * WebSocket Client - Layer 4 ASCII WebSocket communication with ArxOS
 * Handles real-time updates and layer-aware messaging
 */

class ArxOSWebSocketClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.messageQueue = [];
        
        // Layer 4 ASCII context
        this.layerContext = {
            layer: 'LayerASCII',
            precision: 'medium',
            viewport: {
                minX: 0,
                minY: 0,
                maxX: 100,
                maxY: 100
            }
        };
        
        // Event handlers
        this.eventHandlers = {
            'connect': [],
            'disconnect': [],
            'object_update': [],
            'viewport_update': [],
            'building_list': [],
            'error': []
        };
        
        // Current building state
        this.currentBuilding = null;
        this.currentFloor = 'f1';
        
        this.connect();
    }
    
    connect() {
        try {
            // Try different connection URLs
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = window.location.hostname;
            const wsPort = window.location.port || '8080';
            
            const wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws`;
            
            console.log('Connecting to ArxOS WebSocket:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('Connected to ArxOS WebSocket');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                this.updateConnectionStatus(true);
                
                // Send layer context
                this.sendLayerContext();
                
                // Process queued messages
                while (this.messageQueue.length > 0) {
                    const message = this.messageQueue.shift();
                    this.send(message);
                }
                
                // Trigger connect event handlers
                this.triggerEvent('connect');
                
                // Request building list
                this.requestBuildingList();
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error, event.data);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket connection closed:', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.triggerEvent('disconnect', { code: event.code, reason: event.reason });
                
                // Attempt to reconnect if not intentionally closed
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.reconnectDelay *= 1.5; // Exponential backoff
                        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                        this.connect();
                    }, this.reconnectDelay);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.triggerEvent('error', error);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus(false);
            this.triggerEvent('error', error);
        }
    }
    
    disconnect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.close(1000, 'Client requested disconnect');
        }
        this.isConnected = false;
        this.updateConnectionStatus(false);
    }
    
    send(message) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            // Queue message for when connection is restored
            this.messageQueue.push(message);
        }
    }
    
    sendLayerContext() {
        this.send({
            type: 'layer_context',
            context: this.layerContext,
            timestamp: new Date().toISOString()
        });
    }
    
    handleMessage(message) {
        console.log('Received message:', message.type, message);
        
        switch (message.type) {
            case 'object_update':
                this.handleObjectUpdate(message);
                break;
            case 'viewport_update':
                this.handleViewportUpdate(message);
                break;
            case 'building_list':
                this.handleBuildingList(message);
                break;
            case 'building_data':
                this.handleBuildingData(message);
                break;
            case 'error':
                this.handleError(message);
                break;
            default:
                console.log('Unknown message type:', message.type);
                break;
        }
        
        // Trigger event handlers
        this.triggerEvent(message.type, message);
    }
    
    handleObjectUpdate(message) {
        if (message.payload && Array.isArray(message.payload)) {
            // Update UI with new objects
            this.updateObjectsList(message.payload);
            this.updateLayersList(message.payload);
        }
    }
    
    handleViewportUpdate(message) {
        if (message.payload) {
            console.log('Viewport updated:', message.payload);
        }
    }
    
    handleBuildingList(message) {
        if (message.payload && Array.isArray(message.payload)) {
            this.updateBuildingSelector(message.payload);
        }
    }
    
    handleBuildingData(message) {
        if (message.payload && message.payload.objects) {
            console.log('Received building data:', message.payload.objects.length, 'objects');
            
            // Transform ArxObjects to format expected by renderer
            const objects = this.transformArxObjects(message.payload.objects);
            
            // Trigger object update for renderer
            this.triggerEvent('object_update', objects);
        }
    }
    
    handleError(message) {
        console.error('Server error:', message.error);
        
        // Show error to user
        this.showNotification(`Error: ${message.error}`, 'error');
    }
    
    transformArxObjects(arxObjects) {
        return arxObjects.map(obj => {
            // Convert ArxObject format to renderer format
            const transformed = {
                id: obj.id || obj.ID,
                type: obj.type || obj.Type,
                name: obj.name || obj.Name,
                geometry: {
                    position: {
                        x: obj.geometry?.position?.x || obj.Geometry?.Position?.X || 0,
                        y: obj.geometry?.position?.y || obj.Geometry?.Position?.Y || 0,
                        z: obj.geometry?.position?.z || obj.Geometry?.Position?.Z || 0
                    },
                    bounding_box: null
                },
                properties: obj.properties || obj.Properties || {},
                confidence: obj.confidence || obj.Confidence || 1.0
            };
            
            // Create bounding box if we have geometry data
            if (obj.geometry?.bounding_box || obj.Geometry?.BoundingBox) {
                const bbox = obj.geometry?.bounding_box || obj.Geometry?.BoundingBox;
                transformed.geometry.bounding_box = {
                    min: {
                        x: bbox.min?.x || bbox.Min?.X || transformed.geometry.position.x - 0.5,
                        y: bbox.min?.y || bbox.Min?.Y || transformed.geometry.position.y - 0.5
                    },
                    max: {
                        x: bbox.max?.x || bbox.Max?.X || transformed.geometry.position.x + 0.5,
                        y: bbox.max?.y || bbox.Max?.Y || transformed.geometry.position.y + 0.5
                    }
                };
            } else {
                // Create default bounding box
                transformed.geometry.bounding_box = {
                    min: {
                        x: transformed.geometry.position.x - 0.5,
                        y: transformed.geometry.position.y - 0.5
                    },
                    max: {
                        x: transformed.geometry.position.x + 0.5,
                        y: transformed.geometry.position.y + 0.5
                    }
                };
            }
            
            return transformed;
        });
    }
    
    updateObjectsList(objects) {
        const objectsList = document.getElementById('objectsList');
        if (!objectsList) return;
        
        // Group objects by type
        const objectsByType = {};
        objects.forEach(obj => {
            const type = obj.type || 'unknown';
            if (!objectsByType[type]) {
                objectsByType[type] = [];
            }
            objectsByType[type].push(obj);
        });
        
        let html = '';
        for (const [type, typeObjects] of Object.entries(objectsByType)) {
            typeObjects.forEach(obj => {
                html += `
                    <div class="object-item" data-object-id="${obj.id}">
                        <div class="object-type">${type}</div>
                        <div class="object-name">${obj.name || 'Unnamed'}</div>
                        <div class="object-props">ID: ${obj.id}</div>
                    </div>
                `;
            });
        }
        
        objectsList.innerHTML = html;
        
        // Add click handlers
        objectsList.querySelectorAll('.object-item').forEach(item => {
            item.addEventListener('click', () => {
                const objectId = item.dataset.objectId;
                const obj = objects.find(o => o.id === objectId);
                if (obj) {
                    this.triggerEvent('object_selected', obj);
                }
            });
        });
    }
    
    updateLayersList(objects) {
        const layersContent = document.getElementById('layersContent');
        if (!layersContent) return;
        
        // Count objects by type for layers
        const layers = {};
        objects.forEach(obj => {
            const type = obj.type || 'unknown';
            layers[type] = (layers[type] || 0) + 1;
        });
        
        let html = '';
        for (const [layerName, count] of Object.entries(layers)) {
            html += `
                <div class="layer-item">
                    <input type="checkbox" class="layer-checkbox" id="layer-${layerName}" checked>
                    <label for="layer-${layerName}" class="layer-name">${layerName}</label>
                    <span class="layer-count">${count}</span>
                </div>
            `;
        }
        
        layersContent.innerHTML = html;
    }
    
    updateBuildingSelector(buildings) {
        const buildingSelect = document.getElementById('buildingSelect');
        if (!buildingSelect) return;
        
        buildingSelect.innerHTML = '<option value="">Select Building...</option>';
        
        buildings.forEach(building => {
            const option = document.createElement('option');
            option.value = building.id || building.ID;
            option.textContent = building.name || building.Name || building.id;
            buildingSelect.appendChild(option);
        });
    }
    
    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connectionStatus');
        const connectionText = document.getElementById('connectionText');
        
        if (statusIndicator) {
            statusIndicator.className = connected ? 'status-indicator connected' : 'status-indicator';
        }
        
        if (connectionText) {
            connectionText.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }
    
    showNotification(message, type = 'info') {
        // Simple notification system
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Could implement toast notifications here
        if (type === 'error') {
            alert(`Error: ${message}`);
        }
    }
    
    // Public API methods
    requestBuildingList() {
        this.send({
            type: 'get_building_list',
            timestamp: new Date().toISOString()
        });
    }
    
    selectBuilding(buildingId) {
        this.currentBuilding = buildingId;
        this.send({
            type: 'select_building',
            building_id: buildingId,
            floor: this.currentFloor,
            timestamp: new Date().toISOString()
        });
    }
    
    selectFloor(floorId) {
        this.currentFloor = floorId;
        if (this.currentBuilding) {
            this.send({
                type: 'select_building',
                building_id: this.currentBuilding,
                floor: floorId,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    updateViewport(viewport) {
        this.layerContext.viewport = viewport;
        this.send({
            type: 'viewport_change',
            viewport: viewport,
            context: this.layerContext,
            timestamp: new Date().toISOString()
        });
    }
    
    setPrecision(precision) {
        this.layerContext.precision = precision;
        this.sendLayerContext();
    }
    
    // Event system
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    off(event, handler) {
        if (this.eventHandlers[event]) {
            const index = this.eventHandlers[event].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[event].splice(index, 1);
            }
        }
    }
    
    triggerEvent(event, data = null) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    // Cleanup
    destroy() {
        this.disconnect();
        this.eventHandlers = {};
        this.messageQueue = [];
    }
}

// Export for use in other modules
window.ArxOSWebSocketClient = ArxOSWebSocketClient;