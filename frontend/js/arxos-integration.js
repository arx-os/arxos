/**
 * Arxos Main Integration Module
 * Connects Three.js renderer, real-time updates, and AI services
 */

class ArxosIntegration {
    constructor(options = {}) {
        this.options = {
            containerId: options.containerId || 'arxos-3d-container',
            buildingId: options.buildingId || null,
            enableRealtime: options.enableRealtime !== false,
            enableAI: options.enableAI !== false,
            ...options
        };
        
        // Core components
        this.renderer = null;
        this.realtime = null;
        this.aiService = null;
        
        // Building data
        this.buildingData = null;
        this.currentView = '3d'; // '3d', 'ascii', 'ar'
        
        // Event handlers
        this.eventHandlers = new Map();
        
        // Initialize components
        this.init();
    }
    
    async init() {
        try {
            console.log('Initializing Arxos Integration...');
            
            // Initialize 3D renderer
            await this._initRenderer();
            
            // Initialize real-time updates
            if (this.options.enableRealtime) {
                await this._initRealtime();
            }
            
            // Initialize AI service
            if (this.options.enableAI) {
                await this._initAIService();
            }
            
            // Set up event handlers
            this._setupEventHandlers();
            
            // Load building data if specified
            if (this.options.buildingId) {
                await this.loadBuilding(this.options.buildingId);
            }
            
            console.log('Arxos Integration initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize Arxos Integration:', error);
            throw error;
        }
    }
    
    async _initRenderer() {
        try {
            // Check if Three.js is available
            if (typeof THREE === 'undefined') {
                throw new Error('Three.js not loaded. Please include three.min.js before initializing Arxos.');
            }
            
            // Check if OrbitControls is available
            if (typeof THREE.OrbitControls === 'undefined') {
                throw new Error('Three.js OrbitControls not loaded. Please include OrbitControls.js before initializing Arxos.');
            }
            
            // Create 3D renderer
            this.renderer = new ArxosThreeRenderer(this.options.containerId, {
                width: window.innerWidth,
                height: window.innerHeight,
                enableShadows: true,
                enableGrid: true,
                enableAxes: true
            });
            
            // Wait for renderer to be ready
            await this._waitForRenderer();
            
            console.log('3D renderer initialized');
            
        } catch (error) {
            console.error('Failed to initialize 3D renderer:', error);
            throw error;
        }
    }
    
    async _waitForRenderer() {
        return new Promise((resolve) => {
            const checkReady = () => {
                if (this.renderer && this.renderer.scene) {
                    resolve();
                } else {
                    setTimeout(checkReady, 100);
                }
            };
            checkReady();
        });
    }
    
    async _initRealtime() {
        try {
            this.realtime = new ArxosRealtimeUpdates({
                serverUrl: this._getWebSocketUrl(),
                reconnectInterval: 5000,
                maxReconnectAttempts: 10,
                heartbeatInterval: 30000
            });
            
            // Set up real-time event handlers
            this.realtime.on('connected', () => {
                console.log('Real-time connection established');
                this._emitEvent('realtimeConnected');
            });
            
            this.realtime.on('buildingUpdate', (data) => {
                this._handleRealtimeBuildingUpdate(data);
            });
            
            this.realtime.on('objectUpdate', (data) => {
                this._handleRealtimeObjectUpdate(data);
            });
            
            console.log('Real-time updates initialized');
            
        } catch (error) {
            console.error('Failed to initialize real-time updates:', error);
            // Don't throw - real-time is optional
        }
    }
    
    async _initAIService() {
        try {
            // Initialize AI service connection
            this.aiService = {
                async processPDF(pdfFile, options = {}) {
                    const formData = new FormData();
                    formData.append('pdf', pdfFile);
                    formData.append('options', JSON.stringify(options));
                    
                    const response = await fetch('/api/ai/process-pdf', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`AI service error: ${response.statusText}`);
                    }
                    
                    return await response.json();
                },
                
                async extractGeometry(imageData, options = {}) {
                    const response = await fetch('/api/ai/extract-geometry', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            imageData,
                            options
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`AI service error: ${response.statusText}`);
                    }
                    
                    return await response.json();
                }
            };
            
            console.log('AI service initialized');
            
        } catch (error) {
            console.error('Failed to initialize AI service:', error);
            // Don't throw - AI service is optional
        }
    }
    
    _setupEventHandlers() {
        // Renderer events
        if (this.renderer) {
            this.renderer.container.addEventListener('arxos:objectSelected', (event) => {
                this._handleObjectSelection(event.detail);
            });
            
            this.renderer.container.addEventListener('arxos:zoomLevelChanged', (event) => {
                this._handleZoomLevelChange(event.detail);
            });
        }
        
        // Window events
        window.addEventListener('resize', () => {
            this._handleWindowResize();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this._handleKeyboardShortcuts(event);
        });
    }
    
    _getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = '8081'; // WebSocket port
        return `${protocol}//${host}:${port}`;
    }
    
    // Public API methods
    
    async loadBuilding(buildingId) {
        try {
            console.log(`Loading building: ${buildingId}`);
            
            // Fetch building data
            const response = await fetch(`/api/buildings/${buildingId}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch building: ${response.statusText}`);
            }
            
            this.buildingData = await response.json();
            this.options.buildingId = buildingId;
            
            // Load into 3D renderer
            if (this.renderer) {
                this.renderer.loadBuildingModel(this.buildingData);
            }
            
            // Subscribe to real-time updates
            if (this.realtime && this.realtime.isConnected) {
                this.realtime.subscribeToBuilding(buildingId, [], (data) => {
                    this._handleRealtimeUpdate(data);
                });
            }
            
            // Emit building loaded event
            this._emitEvent('buildingLoaded', { buildingId, buildingData: this.buildingData });
            
            console.log('Building loaded successfully');
            
        } catch (error) {
            console.error('Failed to load building:', error);
            throw error;
        }
    }
    
    async processPDFFloorPlan(pdfFile, options = {}) {
        try {
            if (!this.aiService) {
                throw new Error('AI service not available');
            }
            
            console.log('Processing PDF floor plan...');
            
            // Process PDF through AI service
            const result = await this.aiService.processPDF(pdfFile, options);
            
            // Convert AI result to building data
            const buildingData = this._convertAIResultToBuilding(result);
            
            // Load building data
            this.buildingData = buildingData;
            
            // Update 3D renderer
            if (this.renderer) {
                this.renderer.loadBuildingModel(buildingData);
            }
            
            // Emit PDF processed event
            this._emitEvent('pdfProcessed', { result, buildingData });
            
            console.log('PDF floor plan processed successfully');
            return buildingData;
            
        } catch (error) {
            console.error('Failed to process PDF floor plan:', error);
            throw error;
        }
    }
    
    _convertAIResultToBuilding(aiResult) {
        // Convert AI extraction result to Arxos building format
        const buildingData = {
            id: `building_${Date.now()}`,
            name: 'Extracted Building',
            type: 'office',
            foundation: {
                id: 'foundation_1',
                width: 100,
                height: 10,
                depth: 100,
                x: 0,
                z: 0
            },
            floors: [],
            structural: {
                columns: [],
                beams: []
            },
            mep: {
                electrical: { panels: [] },
                hvac: { units: [] }
            }
        };
        
        // Process extracted walls
        if (aiResult.walls) {
            const floor = {
                id: 'floor_1',
                width: 100,
                height: 10,
                depth: 100,
                slabThickness: 2,
                x: 0,
                z: 0,
                walls: [],
                rooms: []
            };
            
            aiResult.walls.forEach((wall, index) => {
                floor.walls.push({
                    id: `wall_${index + 1}`,
                    start_point: wall.start_point,
                    end_point: wall.end_point,
                    height: wall.height || 10,
                    thickness: wall.thickness || 0.2,
                    properties: wall.properties || {}
                });
            });
            
            buildingData.floors.push(floor);
        }
        
        // Process extracted doors
        if (aiResult.doors) {
            aiResult.doors.forEach((door, index) => {
                // Add doors to appropriate floor
                if (buildingData.floors.length > 0) {
                    buildingData.floors[0].doors = buildingData.floors[0].doors || [];
                    buildingData.floors[0].doors.push({
                        id: `door_${index + 1}`,
                        center_point: door.center_point,
                        width: door.width,
                        height: door.height,
                        properties: door.properties || {}
                    });
                }
            });
        }
        
        // Process extracted windows
        if (aiResult.windows) {
            aiResult.windows.forEach((window, index) => {
                // Add windows to appropriate floor
                if (buildingData.floors.length > 0) {
                    buildingData.floors[0].windows = buildingData.floors[0].windows || [];
                    buildingData.floors[0].windows.push({
                        id: `window_${index + 1}`,
                        center_point: window.center_point,
                        width: window.width,
                        height: window.height,
                        properties: window.properties || {}
                    });
                }
            });
        }
        
        // Process extracted rooms
        if (aiResult.rooms) {
            aiResult.rooms.forEach((room, index) => {
                if (buildingData.floors.length > 0) {
                    buildingData.floors[0].rooms.push({
                        id: `room_${index + 1}`,
                        corners: room.corners,
                        area: room.area,
                        properties: room.properties || {}
                    });
                }
            });
        }
        
        return buildingData;
    }
    
    // View management
    
    switchView(viewType) {
        if (this.currentView === viewType) return;
        
        try {
            switch (viewType) {
                case '3d':
                    this._show3DView();
                    break;
                    
                case 'ascii':
                    this._showASCIIView();
                    break;
                    
                case 'ar':
                    this._showARView();
                    break;
                    
                default:
                    throw new Error(`Unknown view type: ${viewType}`);
            }
            
            this.currentView = viewType;
            this._emitEvent('viewChanged', { viewType });
            
        } catch (error) {
            console.error(`Failed to switch to ${viewType} view:`, error);
        }
    }
    
    _show3DView() {
        // Show 3D renderer container
        if (this.renderer && this.renderer.container) {
            this.renderer.container.style.display = 'block';
        }
        
        // Hide other view containers
        this._hideOtherViews('3d');
    }
    
    _showASCIIView() {
        // Hide 3D renderer
        if (this.renderer && this.renderer.container) {
            this.renderer.container.style.display = 'none';
        }
        
        // Show ASCII view (implement ASCII rendering)
        this._showASCIIContainer();
        
        // Hide other view containers
        this._hideOtherViews('ascii');
    }
    
    _showARView() {
        // Check if AR is supported
        if (!this._isARSupported()) {
            console.warn('AR not supported on this device');
            return;
        }
        
        // Hide 3D renderer
        if (this.renderer && this.renderer.container) {
            this.renderer.container.style.display = 'none';
        }
        
        // Show AR view
        this._showARContainer();
        
        // Hide other view containers
        this._hideOtherViews('ar');
    }
    
    _hideOtherViews(currentView) {
        // Hide ASCII container
        const asciiContainer = document.getElementById('arxos-ascii-container');
        if (asciiContainer) {
            asciiContainer.style.display = currentView === 'ascii' ? 'block' : 'none';
        }
        
        // Hide AR container
        const arContainer = document.getElementById('arxos-ar-container');
        if (arContainer) {
            arContainer.style.display = currentView === 'ar' ? 'block' : 'none';
        }
    }
    
    _showASCIIContainer() {
        let asciiContainer = document.getElementById('arxos-ascii-container');
        if (!asciiContainer) {
            asciiContainer = document.createElement('div');
            asciiContainer.id = 'arxos-ascii-container';
            asciiContainer.className = 'arxos-ascii-view';
            asciiContainer.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: #000;
                color: #0f0;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                line-height: 1;
                overflow: auto;
                display: none;
            `;
            
            // Add to main container
            const mainContainer = document.getElementById(this.options.containerId);
            if (mainContainer) {
                mainContainer.appendChild(asciiContainer);
            }
        }
        
        asciiContainer.style.display = 'block';
        
        // Generate ASCII representation
        this._generateASCIIView(asciiContainer);
    }
    
    _generateASCIIView(container) {
        if (!this.buildingData) {
            container.innerHTML = '<pre>No building data available</pre>';
            return;
        }
        
        // Generate ASCII floor plan
        let ascii = '';
        
        if (this.buildingData.floors && this.buildingData.floors.length > 0) {
            const floor = this.buildingData.floors[0];
            
            // Create ASCII grid
            const gridSize = 80;
            const grid = Array(gridSize).fill().map(() => Array(gridSize).fill(' '));
            
            // Draw walls
            if (floor.walls) {
                floor.walls.forEach(wall => {
                    const start = wall.start_point;
                    const end = wall.end_point;
                    
                    // Convert coordinates to grid positions
                    const startX = Math.floor((start[0] / 100) * gridSize);
                    const startY = Math.floor((start[1] / 100) * gridSize);
                    const endX = Math.floor((end[0] / 100) * gridSize);
                    const endY = Math.floor((end[1] / 100) * gridSize);
                    
                    // Draw wall line
                    this._drawLine(grid, startX, startY, endX, endY, '█');
                });
            }
            
            // Draw doors
            if (floor.doors) {
                floor.doors.forEach(door => {
                    const center = door.center_point;
                    const x = Math.floor((center[0] / 100) * gridSize);
                    const y = Math.floor((center[1] / 100) * gridSize);
                    
                    if (x >= 0 && x < gridSize && y >= 0 && y < gridSize) {
                        grid[y][x] = '▢';
                    }
                });
            }
            
            // Draw windows
            if (floor.windows) {
                floor.windows.forEach(window => {
                    const center = window.center_point;
                    const x = Math.floor((center[0] / 100) * gridSize);
                    const y = Math.floor((center[1] / 100) * gridSize);
                    
                    if (x >= 0 && x < gridSize && y >= 0 && y < gridSize) {
                        grid[y][x] = '□';
                    }
                });
            }
            
            // Convert grid to ASCII string
            ascii = grid.map(row => row.join('')).join('\n');
        }
        
        container.innerHTML = `<pre>${ascii}</pre>`;
    }
    
    _drawLine(grid, x1, y1, x2, y2, char) {
        const dx = Math.abs(x2 - x1);
        const dy = Math.abs(y2 - y1);
        const sx = x1 < x2 ? 1 : -1;
        const sy = y1 < y2 ? 1 : -1;
        let err = dx - dy;
        
        while (true) {
            if (x1 >= 0 && x1 < grid[0].length && y1 >= 0 && y1 < grid.length) {
                grid[y1][x1] = char;
            }
            
            if (x1 === x2 && y1 === y2) break;
            
            const e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x1 += sx;
            }
            if (e2 < dx) {
                err += dx;
                y1 += sy;
            }
        }
    }
    
    _showARContainer() {
        let arContainer = document.getElementById('arxos-ar-container');
        if (!arContainer) {
            arContainer = document.createElement('div');
            arContainer.id = 'arxos-ar-container';
            arContainer.className = 'arxos-ar-view';
            arContainer.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: #000;
                color: #fff;
                display: none;
            `;
            
            arContainer.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <h3>AR View</h3>
                    <p>AR functionality requires device with AR capabilities</p>
                    <button onclick="this.parentElement.parentElement.style.display='none'">Close</button>
                </div>
            `;
            
            // Add to main container
            const mainContainer = document.getElementById(this.options.containerId);
            if (mainContainer) {
                mainContainer.appendChild(arContainer);
            }
        }
        
        arContainer.style.display = 'block';
    }
    
    _isARSupported() {
        // Check for WebXR support
        return 'xr' in navigator && navigator.xr.isSessionSupported('immersive-ar');
    }
    
    // Event handling
    
    _handleObjectSelection(data) {
        this._emitEvent('objectSelected', data);
        
        // Update UI to show object details
        this._showObjectDetails(data.object);
    }
    
    _handleZoomLevelChange(data) {
        this._emitEvent('zoomLevelChanged', data);
        
        // Update UI to show zoom level
        this._updateZoomLevelIndicator(data.level);
    }
    
    _handleRealtimeBuildingUpdate(data) {
        // Update local building data
        if (this.buildingData && this.buildingData.id === data.buildingId) {
            this._applyBuildingChanges(data.changes);
        }
        
        this._emitEvent('buildingUpdated', data);
    }
    
    _handleRealtimeObjectUpdate(data) {
        // Update 3D renderer
        if (this.renderer) {
            this.renderer.updateObject(data.objectId, data.properties);
        }
        
        this._emitEvent('objectUpdated', data);
    }
    
    _handleRealtimeUpdate(data) {
        // Generic real-time update handler
        this._emitEvent('realtimeUpdate', data);
    }
    
    _handleWindowResize() {
        if (this.renderer) {
            this.renderer._onWindowResize();
        }
    }
    
    _handleKeyboardShortcuts(event) {
        // Only handle shortcuts when not typing in input fields
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        switch (event.key.toLowerCase()) {
            case '1':
                this.switchView('3d');
                break;
            case '2':
                this.switchView('ascii');
                break;
            case '3':
                this.switchView('ar');
                break;
            case 'r':
                if (this.renderer) {
                    this.renderer.resetCamera();
                }
                break;
            case 'h':
                if (this.renderer) {
                    this.renderer.toggleGrid();
                }
                break;
        }
    }
    
    _showObjectDetails(object) {
        // Create or update object details panel
        let detailsPanel = document.getElementById('arxos-object-details');
        if (!detailsPanel) {
            detailsPanel = document.createElement('div');
            detailsPanel.id = 'arxos-object-details';
            detailsPanel.className = 'arxos-object-details';
            detailsPanel.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                width: 300px;
                background: #fff;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
            `;
            
            document.body.appendChild(detailsPanel);
        }
        
        // Populate details
        detailsPanel.innerHTML = `
            <h4>Object Details</h4>
            <p><strong>Type:</strong> ${object.userData.type || 'Unknown'}</p>
            <p><strong>ID:</strong> ${object.userData.arxObjectId || 'Unknown'}</p>
            <p><strong>Position:</strong> ${object.position.x.toFixed(2)}, ${object.position.y.toFixed(2)}, ${object.position.z.toFixed(2)}</p>
            ${object.userData.properties ? `
                <h5>Properties:</h5>
                <ul>
                    ${Object.entries(object.userData.properties).map(([key, value]) => 
                        `<li><strong>${key}:</strong> ${value}</li>`
                    ).join('')}
                </ul>
            ` : ''}
            <button onclick="this.parentElement.remove()">Close</button>
        `;
    }
    
    _updateZoomLevelIndicator(level) {
        // Update zoom level indicator in UI
        let indicator = document.getElementById('arxos-zoom-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'arxos-zoom-indicator';
            indicator.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: rgba(0,0,0,0.7);
                color: #fff;
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                z-index: 1000;
            `;
            document.body.appendChild(indicator);
        }
        
        indicator.textContent = `Zoom: ${level}`;
    }
    
    _applyBuildingChanges(changes) {
        // Apply changes to local building data
        changes.forEach(change => {
            const { path, value, operation } = change;
            
            switch (operation) {
                case 'set':
                    this._setNestedProperty(this.buildingData, path, value);
                    break;
                case 'delete':
                    this._deleteNestedProperty(this.buildingData, path);
                    break;
                case 'add':
                    this._addToArray(this.buildingData, path, value);
                    break;
                case 'remove':
                    this._removeFromArray(this.buildingData, path, value);
                    break;
            }
        });
        
        // Update 3D renderer
        if (this.renderer) {
            this.renderer.loadBuildingModel(this.buildingData);
        }
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
    
    // Event system
    
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
    
    getCurrentView() {
        return this.currentView;
    }
    
    getBuildingData() {
        return this.buildingData;
    }
    
    getRenderer() {
        return this.renderer;
    }
    
    getRealtime() {
        return this.realtime;
    }
    
    getAIService() {
        return this.aiService;
    }
    
    // Cleanup
    
    destroy() {
        try {
            // Stop real-time updates
            if (this.realtime) {
                this.realtime.disconnect();
            }
            
            // Stop performance monitoring
            if (this.realtime) {
                this.realtime.stopPerformanceMonitoring();
            }
            
            // Remove event listeners
            this.eventHandlers.clear();
            
            // Remove UI elements
            const elements = [
                'arxos-object-details',
                'arxos-zoom-indicator',
                'arxos-ascii-container',
                'arxos-ar-container'
            ];
            
            elements.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.remove();
                }
            });
            
            console.log('Arxos Integration destroyed');
            
        } catch (error) {
            console.error('Error during cleanup:', error);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxosIntegration;
}
