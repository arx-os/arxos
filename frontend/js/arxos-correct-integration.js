/**
 * Arxos Correct Integration Module
 * Properly integrates SVG + ArxObject + Three.js for 1:1 accurate BIM rendering
 * 
 * This module implements the correct Arxos architecture:
 * - SVG provides precise coordinate system
 * - ArxObjects provide building intelligence and real-time data
 * - Three.js renders 3D visualization from SVG + ArxObject data
 * - Result: CAD-like presentation with pinpoint accuracy
 */

class ArxosCorrectIntegration {
    constructor(options = {}) {
        this.options = {
            containerId: options.containerId || 'arxos-3d-container',
            buildingId: options.buildingId || null,
            enableRealtime: options.enableRealtime !== false,
            enablePrecisionMode: options.enablePrecisionMode !== false, // Submicron accuracy
            defaultUnits: options.defaultUnits || 'mm', // millimeters for precision
            ...options
        };
        
        // Core components
        this.svgArxObjectIntegration = null;
        this.threeRenderer = null;
        this.realtime = null;
        
        // Building data
        this.buildingData = null;
        this.currentView = '3d'; // '3d', 'ascii', 'ar'
        
        // Event handlers
        this.eventHandlers = new Map();
        
        // Initialize components
        this.init();
    }
    
    /**
     * Initialize the integration system
     */
    async init() {
        try {
            console.log('Initializing Arxos Correct Integration...');
            
            // Initialize SVG + ArxObject integration
            await this._initSVGArxObjectIntegration();
            
            // Initialize Three.js renderer
            await this._initThreeRenderer();
            
            // Initialize real-time updates
            if (this.options.enableRealtime) {
                await this._initRealtime();
            }
            
            // Set up event handlers
            this._setupEventHandlers();
            
            // Load building data if specified
            if (this.options.buildingId) {
                await this.loadBuilding(this.options.buildingId);
            }
            
            console.log('Arxos Correct Integration initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize Arxos Correct Integration:', error);
            throw error;
        }
    }
    
    /**
     * Initialize SVG + ArxObject integration
     */
    async _initSVGArxObjectIntegration() {
        try {
            // Check if the integration module is available
            if (typeof ArxosSVGArxObjectIntegration === 'undefined') {
                throw new Error('ArxosSVGArxObjectIntegration not loaded. Please include svg-arxobject-integration.js before initializing Arxos.');
            }
            
            // Create SVG + ArxObject integration
            this.svgArxObjectIntegration = new ArxosSVGArxObjectIntegration({
                enablePrecisionMode: this.options.enablePrecisionMode,
                defaultUnits: this.options.defaultUnits
            });
            
            // Set up event listeners
            this.svgArxObjectIntegration.on('svgLoaded', (data) => {
                this._handleSVGLoaded(data);
            });
            
            this.svgArxObjectIntegration.on('arxObjectsLoaded', (data) => {
                this._handleArxObjectsLoaded(data);
            });
            
            this.svgArxObjectIntegration.on('arxObjectUpdated', (data) => {
                this._handleArxObjectUpdated(data);
            });
            
            console.log('SVG + ArxObject integration initialized');
            
        } catch (error) {
            console.error('Failed to initialize SVG + ArxObject integration:', error);
            throw error;
        }
    }
    
    /**
     * Initialize Three.js renderer
     */
    async _initThreeRenderer() {
        try {
            // Check if Three.js is available
            if (typeof THREE === 'undefined') {
                throw new Error('Three.js not loaded. Please include three.min.js before initializing Arxos.');
            }
            
            // Check if the correct renderer is available
            if (typeof ArxosThreeRenderer === 'undefined') {
                throw new Error('ArxosThreeRenderer not loaded. Please include arxos-three-renderer.js before initializing Arxos.');
            }
            
            // Create Three.js renderer
            this.threeRenderer = new ArxosThreeRenderer(this.options.containerId, {
                width: window.innerWidth,
                height: window.innerHeight,
                enableShadows: true,
                enableGrid: true,
                enableAxes: true,
                precisionMode: this.options.enablePrecisionMode
            });
            
            // Connect SVG + ArxObject integration to Three.js renderer
            this.threeRenderer.setSVGArxObjectIntegration(this.svgArxObjectIntegration);
            
            // Wait for renderer to be ready
            await this._waitForRenderer();
            
            console.log('Three.js renderer initialized');
            
        } catch (error) {
            console.error('Failed to initialize Three.js renderer:', error);
            throw error;
        }
    }
    
    /**
     * Wait for renderer to be ready
     */
    async _waitForRenderer() {
        return new Promise((resolve) => {
            const checkReady = () => {
                if (this.threeRenderer && this.threeRenderer.scene) {
                    resolve();
                } else {
                    setTimeout(checkReady, 100);
                }
            };
            checkReady();
        });
    }
    
    /**
     * Initialize real-time updates
     */
    async _initRealtime() {
        try {
            // Check if real-time module is available
            if (typeof ArxosRealtimeUpdates === 'undefined') {
                console.warn('ArxosRealtimeUpdates not loaded - real-time features disabled');
                return;
            }
            
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
    
    /**
     * Set up event handlers
     */
    _setupEventHandlers() {
        // Three.js renderer events
        if (this.threeRenderer) {
            this.threeRenderer.container.addEventListener('arxos:objectSelected', (event) => {
                this._handleObjectSelection(event.detail);
            });
            
            this.threeRenderer.container.addEventListener('arxos:zoomLevelChanged', (event) => {
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
    
    /**
     * Get WebSocket URL for real-time updates
     */
    _getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = '8081'; // WebSocket port
        return `${protocol}//${host}:${port}`;
    }
    
    // Public API methods
    
    /**
     * Load SVG-based BIM model
     * @param {string|Document} svgSource - SVG source
     * @param {Array} arxObjects - ArxObject data
     */
    async loadSVGBIMModel(svgSource, arxObjects = []) {
        try {
            console.log('Loading SVG BIM model...');
            
            // Load SVG document and ArxObjects
            await this.svgArxObjectIntegration.loadSVGBIM(svgSource);
            
            if (arxObjects.length > 0) {
                await this.svgArxObjectIntegration.loadArxObjects(arxObjects);
            }
            
            // Load into Three.js renderer
            await this.threeRenderer.loadSVGBIMModel(svgSource, arxObjects);
            
            // Subscribe to real-time updates if available
            if (this.realtime && this.realtime.isConnected) {
                this._subscribeToRealtimeUpdates();
            }
            
            // Emit model loaded event
            this._emitEvent('svgBIMModelLoaded', { svgSource, arxObjects });
            
            console.log('SVG BIM model loaded successfully');
            
        } catch (error) {
            console.error('Failed to load SVG BIM model:', error);
            throw error;
        }
    }
    
    /**
     * Load building from ArxObject filesystem
     * @param {string} buildingId - Building ID
     */
    async loadBuilding(buildingId) {
        try {
            console.log(`Loading building: ${buildingId}`);
            
            // Fetch building data from ArxObject filesystem
            const response = await fetch(`/api/buildings/${buildingId}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch building: ${response.statusText}`);
            }
            
            this.buildingData = await response.json();
            this.options.buildingId = buildingId;
            
            // Extract SVG and ArxObject data from building
            const { svgData, arxObjects } = this._extractBuildingData(this.buildingData);
            
            // Load SVG BIM model
            await this.loadSVGBIMModel(svgData, arxObjects);
            
            // Emit building loaded event
            this._emitEvent('buildingLoaded', { buildingId, buildingData: this.buildingData });
            
            console.log('Building loaded successfully');
            
        } catch (error) {
            console.error('Failed to load building:', error);
            throw error;
        }
    }
    
    /**
     * Load building from SVG file
     * @param {File} svgFile - SVG file
     */
    async loadSVGFile(svgFile) {
        try {
            console.log('Loading SVG file...');
            
            const svgText = await this._readFileAsText(svgFile);
            
            // Load SVG BIM model
            await this.loadSVGBIMModel(svgText);
            
            console.log('SVG file loaded successfully');
            
        } catch (error) {
            console.error('Failed to load SVG file:', error);
            throw error;
        }
    }
    
    /**
     * Update ArxObject properties
     * @param {string} id - ArxObject ID
     * @param {Object} updates - Property updates
     */
    async updateArxObject(id, updates) {
        try {
            // Update in SVG + ArxObject integration
            this.svgArxObjectIntegration.updateArxObject(id, updates);
            
            // Update in Three.js renderer
            this.threeRenderer.updateArxObjectMesh(id, updates);
            
            // Emit update event
            this._emitEvent('arxObjectUpdated', { id, updates });
            
            console.log(`ArxObject updated: ${id}`);
            
        } catch (error) {
            console.error(`Failed to update ArxObject ${id}:`, error);
            throw error;
        }
    }
    
    /**
     * Set zoom level
     * @param {string} level - Zoom level
     * @param {boolean} smooth - Enable smooth transition
     */
    setZoomLevel(level, smooth = true) {
        if (this.threeRenderer) {
            this.threeRenderer.setZoomLevel(level, smooth);
        }
    }
    
    /**
     * Switch camera type
     * @param {string} cameraType - 'perspective' or 'orthographic'
     */
    switchCamera(cameraType) {
        if (this.threeRenderer) {
            this.threeRenderer.switchCamera(cameraType);
        }
    }
    
    /**
     * Switch view type
     * @param {string} viewType - '3d', 'ascii', 'ar'
     */
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
    
    // Private methods
    
    /**
     * Extract building data from ArxObject filesystem
     */
    _extractBuildingData(buildingData) {
        // This method would extract SVG and ArxObject data from the building filesystem
        // In a real implementation, this would read from .arxos/objects/ directory
        
        const svgData = buildingData.svg || this._generateDefaultSVG(buildingData);
        const arxObjects = buildingData.arxObjects || this._generateDefaultArxObjects(buildingData);
        
        return { svgData, arxObjects };
    }
    
    /**
     * Generate default SVG from building data
     */
    _generateDefaultSVG(buildingData) {
        // Generate basic SVG structure from building data
        // This is a placeholder - in production, this would be more sophisticated
        
        const width = buildingData.width || 100;
        const height = buildingData.height || 100;
        
        return `
            <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" 
                 data-units="mm" data-scale="1:1" data-coordinate-system="cartesian">
                <rect x="0" y="0" width="${width}" height="${height}" 
                      data-arxos-id="building-outline" data-building-element="building" 
                      fill="none" stroke="black" stroke-width="1"/>
            </svg>
        `;
    }
    
    /**
     * Generate default ArxObjects from building data
     */
    _generateDefaultArxObjects(buildingData) {
        // Generate basic ArxObjects from building data
        // This is a placeholder - in production, this would read from filesystem
        
        return [
            {
                id: 'building-outline',
                type: 'building',
                properties: {
                    width: buildingData.width || 100,
                    height: buildingData.height || 100,
                    material: 'concrete'
                }
            }
        ];
    }
    
    /**
     * Read file as text
     */
    _readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
    }
    
    /**
     * Subscribe to real-time updates
     */
    _subscribeToRealtimeUpdates() {
        if (this.realtime && this.options.buildingId) {
            this.realtime.subscribeToBuilding(this.options.buildingId, [], (data) => {
                this._handleRealtimeUpdate(data);
            });
        }
    }
    
    // Event handling methods
    
    _handleSVGLoaded(data) {
        this._emitEvent('svgLoaded', data);
        console.log(`SVG loaded: ${data.objectCount} ArxObjects`);
    }
    
    _handleArxObjectsLoaded(data) {
        this._emitEvent('arxObjectsLoaded', data);
        console.log(`${data.count} ArxObjects loaded`);
    }
    
    _handleArxObjectUpdated(data) {
        this._emitEvent('arxObjectUpdated', data);
    }
    
    _handleObjectSelection(data) {
        this._emitEvent('objectSelected', data);
        this._showObjectDetails(data.object);
    }
    
    _handleZoomLevelChange(data) {
        this._emitEvent('zoomLevelChanged', data);
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
        // Update ArxObject
        this.updateArxObject(data.objectId, data.properties);
        
        this._emitEvent('objectUpdated', data);
    }
    
    _handleRealtimeUpdate(data) {
        this._emitEvent('realtimeUpdate', data);
    }
    
    _handleWindowResize() {
        if (this.threeRenderer) {
            this.threeRenderer._onWindowResize();
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
                if (this.threeRenderer) {
                    this.threeRenderer.resetCamera();
                }
                break;
            case 'h':
                if (this.threeRenderer) {
                    this.threeRenderer.toggleGrid();
                }
                break;
            case 'c':
                if (this.threeRenderer) {
                    this.threeRenderer.switchCamera(
                        this.threeRenderer.options.defaultCamera === 'perspective' ? 'orthographic' : 'perspective'
                    );
                }
                break;
        }
    }
    
    // View management methods
    
    _show3DView() {
        // Show 3D renderer container
        if (this.threeRenderer && this.threeRenderer.container) {
            this.threeRenderer.container.style.display = 'block';
        }
        
        // Hide other view containers
        this._hideOtherViews('3d');
    }
    
    _showASCIIView() {
        // Hide 3D renderer
        if (this.threeRenderer && this.threeRenderer.container) {
            this.threeRenderer.container.style.display = 'none';
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
        if (this.threeRenderer && this.threeRenderer.container) {
            this.threeRenderer.container.style.display = 'none';
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
        
        // Generate ASCII representation from ArxObjects
        this._generateASCIIView(asciiContainer);
    }
    
    _generateASCIIView(container) {
        if (!this.svgArxObjectIntegration) {
            container.innerHTML = '<pre>No ArxObject data available</pre>';
            return;
        }
        
        // Generate ASCII representation from ArxObjects
        const arxObjects = this.svgArxObjectIntegration.getAllArxObjects();
        
        if (arxObjects.length === 0) {
            container.innerHTML = '<pre>No ArxObjects loaded</pre>';
            return;
        }
        
        // Create ASCII grid
        const gridSize = 80;
        const grid = Array(gridSize).fill().map(() => Array(gridSize).fill(' '));
        
        // Draw ArxObjects as ASCII
        arxObjects.forEach(arxObject => {
            const coords = arxObject.svgCoordinates;
            if (coords) {
                this._drawArxObjectAsASCII(grid, arxObject, gridSize);
            }
        });
        
        // Convert grid to ASCII string
        const ascii = grid.map(row => row.join('')).join('\n');
        container.innerHTML = `<pre>${ascii}</pre>`;
    }
    
    _drawArxObjectAsASCII(grid, arxObject, gridSize) {
        const coords = arxObject.svgCoordinates;
        const type = arxObject.type;
        
        // Map ArxObject types to ASCII characters
        const charMap = {
            'wall': '█',
            'door': '▢',
            'window': '□',
            'column': '◊',
            'beam': '═',
            'electrical_panel': '▣',
            'hvac_unit': '◎',
            'pipe': '│',
            'valve': '●'
        };
        
        const char = charMap[type] || '?';
        
        // Convert coordinates to grid positions
        if (coords.type === 'rectangle') {
            const x = Math.floor((coords.x / 100) * gridSize);
            const y = Math.floor((coords.y / 100) * gridSize);
            const width = Math.floor((coords.width / 100) * gridSize);
            const height = Math.floor((coords.height / 100) * gridSize);
            
            // Draw rectangle
            for (let i = Math.max(0, y); i < Math.min(gridSize, y + height); i++) {
                for (let j = Math.max(0, x); j < Math.min(gridSize, x + width); j++) {
                    if (i >= 0 && i < gridSize && j >= 0 && j < gridSize) {
                        grid[i][j] = char;
                    }
                }
            }
        } else if (coords.type === 'line') {
            const x1 = Math.floor((coords.x1 / 100) * gridSize);
            const y1 = Math.floor((coords.y1 / 100) * gridSize);
            const x2 = Math.floor((coords.x2 / 100) * gridSize);
            const y2 = Math.floor((coords.y2 / 100) * gridSize);
            
            // Draw line
            this._drawLine(grid, x1, y1, x2, y2, char);
        }
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
            <h4>ArxObject Details</h4>
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
        
        // Update SVG BIM model
        const { svgData, arxObjects } = this._extractBuildingData(this.buildingData);
        this.loadSVGBIMModel(svgData, arxObjects);
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
    
    getThreeRenderer() {
        return this.threeRenderer;
    }
    
    getSVGArxObjectIntegration() {
        return this.svgArxObjectIntegration;
    }
    
    getRealtime() {
        return this.realtime;
    }
    
    // Cleanup
    
    destroy() {
        try {
            // Stop real-time updates
            if (this.realtime) {
                this.realtime.disconnect();
            }
            
            // Destroy Three.js renderer
            if (this.threeRenderer) {
                this.threeRenderer.destroy();
            }
            
            // Destroy SVG + ArxObject integration
            if (this.svgArxObjectIntegration) {
                this.svgArxObjectIntegration.destroy();
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
            
            console.log('Arxos Correct Integration destroyed');
            
        } catch (error) {
            console.error('Error during cleanup:', error);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxosCorrectIntegration;
}
