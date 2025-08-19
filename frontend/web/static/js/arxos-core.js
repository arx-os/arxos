/**
 * Arxos Core - Lightweight Performance-First Architecture
 * The magic is in ArxObject, not framework complexity
 * Now with nanometer precision for campus-to-circuit zooming
 */

// Load coordinate system if not already loaded
if (typeof CoordinateSystem === 'undefined') {
    const script = document.createElement('script');
    script.src = '/static/js/arxos-coordinates.js';
    document.head.appendChild(script);
}

// ============================================================================
// 1. DataManager - Handles ArxObject data and API communication
// ============================================================================
class DataManager {
    constructor() {
        this.arxObjects = new Map();
        this.scaleCache = new Map();
        this.apiBase = '/api/v1';
        // Initialize coordinate system
        this.coordinateSystem = typeof CoordinateSystem !== 'undefined' ? 
            new CoordinateSystem() : null;
        // Initialize confidence manager if available
        this.confidenceManager = typeof ConfidenceManager !== 'undefined' ?
            new ConfidenceManager() : null;
        // WebSocket for real-time updates
        this.ws = null;
        this.initWebSocket();
    }

    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/validation`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected for real-time updates');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected, attempting reconnect in 5s...');
                setTimeout(() => this.initWebSocket(), 5000);
            };
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'confidence_update':
                this.updateObjectConfidence(data.objectId, data.confidence);
                break;
            case 'validation_complete':
                this.handleValidationComplete(data);
                break;
            case 'pattern_learned':
                this.handlePatternLearned(data);
                break;
        }
    }

    updateObjectConfidence(objectId, confidence) {
        const obj = this.arxObjects.get(objectId);
        if (obj) {
            obj.confidence = confidence;
            // Notify confidence manager if available
            if (this.confidenceManager) {
                this.confidenceManager.updateConfidence(objectId, confidence);
            }
            // Trigger re-render
            document.dispatchEvent(new CustomEvent('arxObjectUpdated', { 
                detail: { objectId, confidence }
            }));
        }
    }

    handleValidationComplete(data) {
        console.log('Validation complete:', data);
        // Update multiple objects if cascade occurred
        if (data.affectedObjects) {
            data.affectedObjects.forEach(obj => {
                this.updateObjectConfidence(obj.id, obj.confidence);
            });
        }
    }

    handlePatternLearned(data) {
        console.log('Pattern learned:', data);
        // Could show notification to user about improved confidence
        if (window.showNotification) {
            window.showNotification(`Pattern learned! ${data.objectsImproved} objects improved.`);
        }
    }

    async fetchArxObjectsAtScale(scale, viewport) {
        // Convert viewport to nanometers for backend
        const viewportNano = {
            x: viewport.x,  // Already in nanometers from coordinateSystem
            y: viewport.y,
            width: viewport.width,
            height: viewport.height,
            scale_level: this.coordinateSystem ? 
                this.coordinateSystem.getCurrentScaleLevel() : 2
        };
        
        const cacheKey = `${scale}:${viewportNano.x}:${viewportNano.y}:${viewportNano.width}:${viewportNano.height}`;
        
        if (this.scaleCache.has(cacheKey)) {
            return this.scaleCache.get(cacheKey);
        }

        try {
            // Add authentication header if available
            const headers = { 'Content-Type': 'application/json' };
            const token = localStorage.getItem('arxos_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${this.apiBase}/arxobjects`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ scale, viewport: viewportNano })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            const objects = data.objects || data; // Handle different response formats
            
            // Cache with TTL
            this.scaleCache.set(cacheKey, objects);
            setTimeout(() => this.scaleCache.delete(cacheKey), 300000); // 5 minute TTL
            
            // Store individual objects with nanometer coordinates
            objects.forEach(obj => {
                // Ensure confidence scores are present
                if (!obj.confidence) {
                    obj.confidence = {
                        overall: 1.0,
                        classification: 1.0,
                        position: 1.0,
                        properties: 1.0,
                        relationships: 1.0
                    };
                }
                
                // Convert to ArxObjectNano if coordinate system is available
                if (typeof ArxObjectNano !== 'undefined') {
                    const nanoObj = new ArxObjectNano(obj);
                    this.arxObjects.set(obj.id, nanoObj);
                } else {
                    this.arxObjects.set(obj.id, obj);
                }
            });
            
            return objects;
        } catch (error) {
            console.error('Failed to fetch ArxObjects:', error);
            
            // Return mock data for development
            if (window.location.hostname === 'localhost') {
                return this.generateMockObjects(viewportNano);
            }
            
            return [];
        }
    }

    // Generate mock objects for development/testing
    generateMockObjects(viewport) {
        const mockObjects = [];
        const types = ['wall', 'door', 'window', 'electrical_outlet', 'hvac_unit'];
        const systems = ['electrical', 'hvac', 'plumbing', 'structural'];
        
        for (let i = 0; i < 20; i++) {
            const type = types[Math.floor(Math.random() * types.length)];
            const system = systems[Math.floor(Math.random() * systems.length)];
            const confidence = 0.3 + Math.random() * 0.7; // Random confidence 0.3-1.0
            
            const obj = {
                id: `mock_${i}`,
                type: type,
                system: system,
                x: viewport.x + Math.random() * viewport.width,
                y: viewport.y + Math.random() * viewport.height,
                width: 10 + Math.random() * 40,
                height: 10 + Math.random() * 40,
                confidence: {
                    overall: confidence,
                    classification: confidence + (Math.random() - 0.5) * 0.2,
                    position: confidence + (Math.random() - 0.5) * 0.2,
                    properties: confidence + (Math.random() - 0.5) * 0.2,
                    relationships: confidence + (Math.random() - 0.5) * 0.2
                },
                properties: {
                    material: type === 'wall' ? 'drywall' : 'unknown',
                    color: '#' + Math.floor(Math.random()*16777215).toString(16)
                }
            };
            
            mockObjects.push(obj);
            this.arxObjects.set(obj.id, obj);
        }
        
        return mockObjects;
    }

    getArxObject(id) {
        return this.arxObjects.get(id);
    }

    // Get objects needing validation
    getObjectsNeedingValidation(threshold = 0.7) {
        const objects = [];
        this.arxObjects.forEach(obj => {
            const confidence = obj.confidence?.overall || 1.0;
            if (confidence < threshold) {
                objects.push(obj);
            }
        });
        return objects.sort((a, b) => 
            (a.confidence?.overall || 0) - (b.confidence?.overall || 0)
        );
    }

    // Flag object for validation
    async flagForValidation(objectId, reason) {
        try {
            const headers = { 'Content-Type': 'application/json' };
            const token = localStorage.getItem('arxos_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${this.apiBase}/validations/flag`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ object_id: objectId, reason })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Object flagged for validation:', data);
            
            // Show user feedback
            if (window.showNotification) {
                window.showNotification('Object flagged for validation', 'success');
            }
            
            return data;
        } catch (error) {
            console.error('Failed to flag object:', error);
            if (window.showNotification) {
                window.showNotification('Failed to flag object for validation', 'error');
            }
            throw error;
        }
    }

    // Get validation tasks for current user
    async getValidationTasks(filters = {}) {
        try {
            const headers = { 'Content-Type': 'application/json' };
            const token = localStorage.getItem('arxos_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const queryParams = new URLSearchParams(filters);
            const response = await fetch(`${this.apiBase}/validations/tasks?${queryParams}`, {
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch validation tasks:', error);
            return { tasks: [], total: 0 };
        }
    }

    // Submit validation result
    async submitValidation(validationData) {
        try {
            const headers = { 'Content-Type': 'application/json' };
            const token = localStorage.getItem('arxos_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${this.apiBase}/validations/submit`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(validationData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Update affected objects in cache
            if (result.affected_objects) {
                result.affected_objects.forEach(obj => {
                    this.updateObjectConfidence(obj.id, obj.confidence);
                });
            }
            
            return result;
        } catch (error) {
            console.error('Failed to submit validation:', error);
            throw error;
        }
    }
}

// ============================================================================
// 2. StateManager - Manages application state with fractal navigation
// ============================================================================
class StateManager {
    constructor() {
        this.state = {
            // Fractal scale levels (matching documentation)
            scaleLevel: 1.0,
            scaleLevels: {
                GLOBAL:    { min: 1000000, max: 10000000 },
                REGIONAL:  { min: 100000,  max: 1000000 },
                MUNICIPAL: { min: 10000,   max: 100000 },
                CAMPUS:    { min: 1000,    max: 10000 },
                BUILDING:  { min: 100,     max: 1000 },
                FLOOR:     { min: 10,      max: 100 },
                ROOM:      { min: 1,       max: 10 },
                COMPONENT: { min: 0.1,     max: 1 },
                CIRCUIT:   { min: 0.001,   max: 0.1 },
                TRACE:     { min: 0.0001,  max: 0.001 }
            },
            
            // Viewport
            viewport: { x: 0, y: 0, width: 1000, height: 1000 },
            
            // Selection
            selectedObject: null,
            highlightedObjects: [],
            
            // System visibility
            visibleSystems: ['electrical', 'hvac', 'plumbing', 'structural']
        };
        
        this.observers = [];
    }

    updateState(updates) {
        Object.assign(this.state, updates);
        this.notifyObservers(updates);
    }

    subscribe(callback) {
        this.observers.push(callback);
    }

    notifyObservers(updates) {
        this.observers.forEach(callback => callback(updates));
    }

    getCurrentScaleLevel() {
        const scale = this.state.scaleLevel;
        for (const [name, range] of Object.entries(this.state.scaleLevels)) {
            if (scale >= range.min && scale <= range.max) {
                return name;
            }
        }
        return 'ROOM';
    }
}

// ============================================================================
// 3. SvgRenderer - Pure SVG rendering with scale-aware optimization
// ============================================================================
class SvgRenderer {
    constructor(container, dataManager, stateManager) {
        this.container = container;
        this.dataManager = dataManager;
        this.stateManager = stateManager;
        
        this.svg = null;
        this.scaleGroups = new Map();
        this.renderedObjects = new Map();
        
        this.init();
    }

    init() {
        // Create main SVG element
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('width', '100%');
        this.svg.setAttribute('height', '100%');
        this.svg.setAttribute('viewBox', '0 0 1000 1000');
        this.container.appendChild(this.svg);
        
        // Subscribe to state changes
        this.stateManager.subscribe(this.handleStateChange.bind(this));
    }

    handleStateChange(updates) {
        if ('scaleLevel' in updates || 'viewport' in updates) {
            this.renderAtScale(this.stateManager.state.scaleLevel);
        }
        if ('selectedObject' in updates) {
            this.updateSelection();
        }
        if ('visibleSystems' in updates) {
            this.updateSystemVisibility();
        }
    }

    updateSystemVisibility() {
        const visibleSystems = this.stateManager.state.visibleSystems;
        
        // Update all rendered objects
        this.renderedObjects.forEach((element, id) => {
            const system = element.getAttribute('data-system');
            if (visibleSystems.includes(system)) {
                element.style.display = '';
                element.style.opacity = '1';
            } else {
                element.style.display = 'none';
            }
        });
        
        // Update system toggle buttons
        document.querySelectorAll('.system-toggle').forEach(button => {
            const system = button.getAttribute('data-system');
            if (visibleSystems.includes(system)) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }

    async renderAtScale(scale) {
        const viewport = this.stateManager.state.viewport;
        const objects = await this.dataManager.fetchArxObjectsAtScale(scale, viewport);
        
        // Clear previous scale groups that are too far from current scale
        this.scaleGroups.forEach((group, groupScale) => {
            const shouldShow = Math.abs(Math.log10(scale) - Math.log10(groupScale)) < 2;
            group.style.display = shouldShow ? 'block' : 'none';
        });
        
        // Render new objects
        objects.forEach(obj => this.renderArxObject(obj));
    }

    renderArxObject(arxObject) {
        if (this.renderedObjects.has(arxObject.id)) {
            // Update existing object if confidence changed
            const existingElement = this.renderedObjects.get(arxObject.id);
            this.updateArxObjectElement(existingElement, arxObject);
            return;
        }

        const element = this.createSVGElement(arxObject);
        
        // Get or create scale group
        const scaleGroup = this.getOrCreateScaleGroup(arxObject.scaleMin || 1.0);
        scaleGroup.appendChild(element);
        
        // Add to rendered objects map
        this.renderedObjects.set(arxObject.id, element);
        
        // Apply system visibility filters
        this.applySystemVisibility(element, arxObject.system);
    }

    updateArxObjectElement(element, arxObject) {
        // Update confidence attributes
        const confidence = arxObject.confidence?.overall || 1.0;
        element.setAttribute('data-confidence', confidence);
        
        // Update confidence styling
        const shape = element.querySelector('rect, circle, path, polygon');
        if (shape) {
            this.applyConfidenceStyle(shape, confidence);
        }
        
        // Update confidence indicator
        const existingIndicator = element.querySelector('.confidence-indicator');
        if (confidence < 0.7) {
            if (!existingIndicator) {
                const indicator = this.createConfidenceIndicator(confidence);
                element.appendChild(indicator);
            } else {
                this.updateConfidenceIndicator(existingIndicator, confidence);
            }
        } else if (existingIndicator) {
            existingIndicator.remove();
        }
    }

    updateConfidenceIndicator(indicator, confidence) {
        // Update color based on confidence level
        let color;
        if (confidence < 0.3) color = '#ff4444';
        else if (confidence < 0.5) color = '#ff8800';
        else if (confidence < 0.7) color = '#ffaa00';
        else color = '#88aa00';
        
        indicator.setAttribute('fill', color);
    }

    applySystemVisibility(element, system) {
        const visibleSystems = this.stateManager.state.visibleSystems;
        if (visibleSystems.includes(system)) {
            element.style.display = '';
        } else {
            element.style.display = 'none';
        }
    }

    createSVGElement(arxObject) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('data-arx-id', arxObject.id);
        g.setAttribute('data-system', arxObject.system || 'unknown');
        g.setAttribute('transform', `translate(${arxObject.x}, ${arxObject.y})`);
        
        // Add confidence data attribute
        const confidence = arxObject.confidence?.overall || 1.0;
        g.setAttribute('data-confidence', confidence);
        
        // Create the actual shape based on type
        const shape = this.createShape(arxObject);
        g.appendChild(shape);
        
        // Apply system-based styling
        this.applySystemStyle(shape, arxObject.system);
        
        // Apply confidence-based styling
        this.applyConfidenceStyle(shape, confidence);
        
        // Add confidence indicator if low
        if (confidence < 0.7) {
            const indicator = this.createConfidenceIndicator(confidence);
            g.appendChild(indicator);
        }
        
        return g;
    }

    createConfidenceIndicator(confidence) {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', '0');
        circle.setAttribute('cy', '0');
        circle.setAttribute('r', '3');
        circle.setAttribute('class', 'confidence-indicator');
        
        // Color based on confidence level
        let color;
        if (confidence < 0.3) color = '#ff4444';
        else if (confidence < 0.5) color = '#ff8800';
        else if (confidence < 0.7) color = '#ffaa00';
        else color = '#88aa00';
        
        circle.setAttribute('fill', color);
        circle.setAttribute('fill-opacity', '0.8');
        circle.setAttribute('stroke', '#ffffff');
        circle.setAttribute('stroke-width', '0.5');
        
        // Add pulsing animation for very low confidence
        if (confidence < 0.3) {
            const animate = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            animate.setAttribute('attributeName', 'r');
            animate.setAttribute('values', '3;5;3');
            animate.setAttribute('dur', '2s');
            animate.setAttribute('repeatCount', 'indefinite');
            circle.appendChild(animate);
        }
        
        return circle;
    }

    applyConfidenceStyle(element, confidence) {
        // Apply opacity based on confidence
        const opacity = 0.3 + (confidence * 0.7); // Range from 0.3 to 1.0
        element.setAttribute('fill-opacity', opacity);
        
        // Add dashed stroke for low confidence
        if (confidence < 0.5) {
            element.setAttribute('stroke-dasharray', '2,2');
        }
    }

    createShape(arxObject) {
        const type = arxObject.type?.toLowerCase();
        const width = arxObject.width || 10;
        const height = arxObject.height || 10;
        
        let shape;
        
        switch (type) {
            case 'door':
                // Create door shape with arc for swing
                shape = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                
                // Door frame
                const doorFrame = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                doorFrame.setAttribute('width', width);
                doorFrame.setAttribute('height', height);
                doorFrame.setAttribute('fill', 'none');
                doorFrame.setAttribute('stroke', '#8B4513');
                doorFrame.setAttribute('stroke-width', '2');
                shape.appendChild(doorFrame);
                
                // Door swing arc
                const arc = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const radius = Math.min(width, height) * 0.8;
                arc.setAttribute('d', `M 0 0 A ${radius} ${radius} 0 0 1 ${radius} ${radius}`);
                arc.setAttribute('fill', 'none');
                arc.setAttribute('stroke', '#8B4513');
                arc.setAttribute('stroke-width', '1');
                arc.setAttribute('stroke-dasharray', '2,2');
                shape.appendChild(arc);
                break;
                
            case 'window':
                // Create window shape
                shape = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                
                // Window frame
                const windowFrame = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                windowFrame.setAttribute('width', width);
                windowFrame.setAttribute('height', height);
                windowFrame.setAttribute('fill', '#87CEEB');
                windowFrame.setAttribute('stroke', '#4682B4');
                windowFrame.setAttribute('stroke-width', '1');
                windowFrame.setAttribute('fill-opacity', '0.6');
                shape.appendChild(windowFrame);
                
                // Window cross
                const crossH = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                crossH.setAttribute('x1', '0');
                crossH.setAttribute('y1', height/2);
                crossH.setAttribute('x2', width);
                crossH.setAttribute('y2', height/2);
                crossH.setAttribute('stroke', '#4682B4');
                crossH.setAttribute('stroke-width', '1');
                shape.appendChild(crossH);
                
                const crossV = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                crossV.setAttribute('x1', width/2);
                crossV.setAttribute('y1', '0');
                crossV.setAttribute('x2', width/2);
                crossV.setAttribute('y2', height);
                crossV.setAttribute('stroke', '#4682B4');
                crossV.setAttribute('stroke-width', '1');
                shape.appendChild(crossV);
                break;
                
            case 'electrical_outlet':
                // Create outlet shape
                shape = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                
                // Outlet body
                const outlet = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                outlet.setAttribute('width', width);
                outlet.setAttribute('height', height);
                outlet.setAttribute('fill', '#F5F5F5');
                outlet.setAttribute('stroke', '#333');
                outlet.setAttribute('stroke-width', '1');
                outlet.setAttribute('rx', '2');
                shape.appendChild(outlet);
                
                // Outlet holes
                const hole1 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                hole1.setAttribute('cx', width * 0.3);
                hole1.setAttribute('cy', height * 0.5);
                hole1.setAttribute('r', '1');
                hole1.setAttribute('fill', '#333');
                shape.appendChild(hole1);
                
                const hole2 = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                hole2.setAttribute('cx', width * 0.7);
                hole2.setAttribute('cy', height * 0.5);
                hole2.setAttribute('r', '1');
                hole2.setAttribute('fill', '#333');
                shape.appendChild(hole2);
                break;
                
            case 'hvac_unit':
                // Create HVAC vent shape
                shape = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                
                // Vent body
                const vent = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                vent.setAttribute('width', width);
                vent.setAttribute('height', height);
                vent.setAttribute('fill', '#C0C0C0');
                vent.setAttribute('stroke', '#808080');
                vent.setAttribute('stroke-width', '1');
                shape.appendChild(vent);
                
                // Vent lines
                for (let i = 1; i < 4; i++) {
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', '0');
                    line.setAttribute('y1', (height * i) / 4);
                    line.setAttribute('x2', width);
                    line.setAttribute('y2', (height * i) / 4);
                    line.setAttribute('stroke', '#808080');
                    line.setAttribute('stroke-width', '0.5');
                    shape.appendChild(line);
                }
                break;
                
            case 'wall':
                // Create wall shape - thicker rectangle
                shape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                shape.setAttribute('width', width);
                shape.setAttribute('height', height);
                shape.setAttribute('fill', '#444');
                shape.setAttribute('stroke', '#222');
                shape.setAttribute('stroke-width', '0.5');
                break;
                
            case 'room':
                // Create room outline
                shape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                shape.setAttribute('width', width);
                shape.setAttribute('height', height);
                shape.setAttribute('fill', 'none');
                shape.setAttribute('stroke', '#666');
                shape.setAttribute('stroke-width', '2');
                shape.setAttribute('stroke-dasharray', '5,5');
                break;
                
            default:
                // Default rectangular shape
                shape = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                shape.setAttribute('width', width);
                shape.setAttribute('height', height);
                shape.setAttribute('class', 'arx-object');
                break;
        }
        
        // Add common class if not already set
        if (shape.tagName !== 'g') {
            shape.setAttribute('class', 'arx-object');
        }
        
        return shape;
    }

    applySystemStyle(element, system) {
        const systemColors = {
            electrical: '#FFD700',
            hvac: '#FF6B35',
            plumbing: '#4A90E2',
            structural: '#795548'
        };
        
        element.setAttribute('fill', systemColors[system] || '#999999');
        element.setAttribute('stroke', '#000000');
        element.setAttribute('stroke-width', '0.5');
    }

    getOrCreateScaleGroup(scale) {
        if (!this.scaleGroups.has(scale)) {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', `scale-group-${scale}`);
            this.svg.appendChild(group);
            this.scaleGroups.set(scale, group);
        }
        return this.scaleGroups.get(scale);
    }

    updateSelection() {
        // Clear previous selection
        this.svg.querySelectorAll('.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Highlight selected object
        const selected = this.stateManager.state.selectedObject;
        if (selected) {
            const element = this.renderedObjects.get(selected.id);
            if (element) {
                element.classList.add('selected');
            }
        }
    }
}

// ============================================================================
// 4. InteractionManager - Handles user input and fractal navigation
// ============================================================================
class InteractionManager {
    constructor(container, dataManager, stateManager, renderer) {
        this.container = container;
        this.dataManager = dataManager;
        this.stateManager = stateManager;
        this.renderer = renderer;
        
        this.isPanning = false;
        this.panStart = { x: 0, y: 0 };
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Mouse events
        this.container.addEventListener('wheel', this.handleZoom.bind(this));
        this.container.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.container.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.container.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.container.addEventListener('click', this.handleClick.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboard.bind(this));
        
        // System toggle buttons
        document.querySelectorAll('.system-toggle').forEach(button => {
            button.addEventListener('click', this.handleSystemToggle.bind(this));
        });
        
        // Confidence panel start validation button
        const startValidationBtn = document.getElementById('start-validation');
        if (startValidationBtn) {
            startValidationBtn.addEventListener('click', this.startValidationSession.bind(this));
        }
    }

    handleSystemToggle(event) {
        const button = event.currentTarget;
        const system = button.getAttribute('data-system');
        
        if (system) {
            this.toggleSystem(system);
        }
    }

    toggleSystem(system) {
        const visible = this.stateManager.state.visibleSystems;
        const index = visible.indexOf(system);
        
        if (index !== -1) {
            // Remove system
            visible.splice(index, 1);
        } else {
            // Add system
            visible.push(system);
        }
        
        this.stateManager.updateState({ visibleSystems: [...visible] });
    }

    handleZoom(event) {
        event.preventDefault();
        
        const delta = event.deltaY > 0 ? 0.8 : 1.25;
        const currentScale = this.stateManager.state.scaleLevel;
        const newScale = currentScale * delta;
        
        // Clamp to valid range
        const minScale = 0.0001;
        const maxScale = 10000000;
        const clampedScale = Math.max(minScale, Math.min(maxScale, newScale));
        
        this.stateManager.updateState({ scaleLevel: clampedScale });
    }

    handleMouseDown(event) {
        if (event.button === 0) { // Left click
            this.isPanning = true;
            this.panStart = { x: event.clientX, y: event.clientY };
        }
    }

    handleMouseMove(event) {
        if (this.isPanning) {
            const dx = event.clientX - this.panStart.x;
            const dy = event.clientY - this.panStart.y;
            
            const viewport = this.stateManager.state.viewport;
            this.stateManager.updateState({
                viewport: {
                    ...viewport,
                    x: viewport.x - dx,
                    y: viewport.y - dy
                }
            });
            
            this.panStart = { x: event.clientX, y: event.clientY };
        }
    }

    handleMouseUp(event) {
        this.isPanning = false;
    }

    handleClick(event) {
        // Check if clicking on an ArxObject
        const target = event.target.closest('[data-arx-id]');
        if (target) {
            const arxId = target.getAttribute('data-arx-id');
            const arxObject = this.dataManager.getArxObject(arxId);
            
            if (arxObject) {
                this.stateManager.updateState({ selectedObject: arxObject });
                this.showObjectDetails(arxObject);
            }
        }
    }

    handleKeyboard(event) {
        switch(event.key) {
            case 'Escape':
                this.stateManager.updateState({ selectedObject: null });
                this.hideInfoPanel();
                break;
            case '1': case '2': case '3': case '4':
                this.toggleSystemByIndex(parseInt(event.key) - 1);
                break;
            case 'f':
                this.fitToView();
                break;
            case 'v':
                if (this.stateManager.state.selectedObject) {
                    this.startValidation(this.stateManager.state.selectedObject);
                }
                break;
            case 'c':
                this.toggleConfidencePanel();
                break;
        }
    }

    toggleSystemByIndex(index) {
        const systems = ['electrical', 'hvac', 'plumbing', 'structural'];
        if (index < systems.length) {
            this.toggleSystem(systems[index]);
        }
    }

    toggleConfidencePanel() {
        const panel = document.getElementById('confidence-panel');
        if (panel) {
            const isVisible = panel.style.display !== 'none';
            panel.style.display = isVisible ? 'none' : 'block';
        }
    }

    hideInfoPanel() {
        const panel = document.getElementById('info-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    startValidationSession() {
        // Get objects needing validation
        const needsValidation = this.dataManager.getObjectsNeedingValidation();
        
        if (needsValidation.length === 0) {
            if (window.showNotification) {
                window.showNotification('No objects need validation!', 'success');
            }
            return;
        }
        
        // Start validation UI if available
        if (window.arxosValidation) {
            window.arxosValidation.showValidationTasks();
        } else {
            alert(`Found ${needsValidation.length} objects that need validation. Validation UI not available.`);
        }
    }

    showObjectDetails(arxObject) {
        // Enhanced detail display with confidence info
        console.log('ArxObject:', arxObject);
        
        const panel = document.getElementById('info-panel');
        const content = document.getElementById('info-content');
        
        if (panel && content) {
            // Clear previous content
            content.innerHTML = '';
            
            // Add basic info
            this.addDetailRow(content, 'ID', arxObject.id);
            this.addDetailRow(content, 'Type', arxObject.type || 'Unknown');
            this.addDetailRow(content, 'System', arxObject.system || 'Unknown');
            
            // Add confidence info
            if (arxObject.confidence) {
                const overall = (arxObject.confidence.overall * 100).toFixed(1);
                this.addDetailRow(content, 'Confidence', `${overall}%`, 
                    this.getConfidenceColor(arxObject.confidence.overall));
                
                // Add validation button if low confidence
                if (arxObject.confidence.overall < 0.7) {
                    const validateBtn = document.createElement('button');
                    validateBtn.className = 'btn-validate';
                    validateBtn.textContent = 'Validate This Object';
                    validateBtn.onclick = () => this.startValidation(arxObject);
                    content.appendChild(validateBtn);
                }
            }
            
            // Show panel
            panel.style.display = 'block';
        }
    }

    addDetailRow(container, label, value, color) {
        const dt = document.createElement('dt');
        dt.textContent = label;
        container.appendChild(dt);
        
        const dd = document.createElement('dd');
        dd.textContent = value;
        if (color) dd.style.color = color;
        container.appendChild(dd);
    }

    getConfidenceColor(confidence) {
        if (confidence < 0.3) return '#ff4444';
        if (confidence < 0.5) return '#ff8800';
        if (confidence < 0.7) return '#ffaa00';
        if (confidence < 0.9) return '#88aa00';
        return '#44aa44';
    }

    startValidation(arxObject) {
        // Trigger validation modal if available
        if (window.ValidationUI) {
            const validationUI = new ValidationUI();
            validationUI.showValidationModal(arxObject);
        } else {
            // Fallback: flag for validation
            this.dataManager.flagForValidation(arxObject.id, 'User requested validation');
            alert('Object flagged for validation');
        }
    }

    fitToView() {
        // Reset viewport to default
        this.stateManager.updateState({
            viewport: { x: 0, y: 0, width: 1000, height: 1000 },
            scaleLevel: 1.0
        });
    }
}

// ============================================================================
// Application Initialization
// ============================================================================
class ArxosApp {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            throw new Error(`Container with id "${containerId}" not found`);
        }
        
        // Initialize the four core components
        this.dataManager = new DataManager();
        this.stateManager = new StateManager();
        this.renderer = new SvgRenderer(this.container, this.dataManager, this.stateManager);
        this.interaction = new InteractionManager(
            this.container, 
            this.dataManager, 
            this.stateManager, 
            this.renderer
        );
        
        // Initialize confidence visualization if available
        if (typeof initConfidenceVisualization === 'function') {
            initConfidenceVisualization();
        }
        
        // Listen for confidence updates
        document.addEventListener('arxObjectUpdated', (event) => {
            const { objectId, confidence } = event.detail;
            // Update visual representation
            const element = this.renderer.renderedObjects.get(objectId);
            if (element) {
                element.setAttribute('data-confidence', confidence.overall);
                // Re-apply confidence styling
                const shape = element.querySelector('rect, circle, path');
                if (shape) {
                    this.renderer.applyConfidenceStyle(shape, confidence.overall);
                }
            }
            // Update confidence overview
            this.updateConfidenceOverview();
        });
        
        // Listen for state changes to update scale indicator
        this.stateManager.subscribe((updates) => {
            if ('scaleLevel' in updates) {
                this.updateScaleIndicator();
            }
        });
        
        // Add validation keyboard shortcut
        document.addEventListener('keydown', (event) => {
            if (event.key === 'v' && this.stateManager.state.selectedObject) {
                this.interaction.startValidation(this.stateManager.state.selectedObject);
            }
        });
        
        // Initial render
        this.renderer.renderAtScale(1.0);
        
        // Initialize UI elements
        this.initializeUI();
    }

    initializeUI() {
        // Show confidence panel if available
        const confidencePanel = document.getElementById('confidence-panel');
        if (confidencePanel) {
            confidencePanel.style.display = 'block';
            this.updateConfidenceOverview();
        }
        
        // Update initial scale indicator
        this.updateScaleIndicator();
        
        // Add notification system
        if (!window.showNotification) {
            window.showNotification = this.showNotification.bind(this);
        }
    }

    updateScaleIndicator() {
        const scaleLevelElement = document.getElementById('scale-level');
        const scaleValueElement = document.getElementById('scale-value');
        
        if (scaleLevelElement && scaleValueElement) {
            const currentLevel = this.stateManager.getCurrentScaleLevel();
            const scale = this.stateManager.state.scaleLevel;
            
            scaleLevelElement.textContent = currentLevel;
            scaleValueElement.textContent = `1:${Math.round(scale)}`;
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            font-size: 14px;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        // Set colors based on type
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#10b981';
                break;
            case 'error':
                notification.style.backgroundColor = '#ef4444';
                break;
            case 'warning':
                notification.style.backgroundColor = '#f59e0b';
                break;
            default:
                notification.style.backgroundColor = '#3b82f6';
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Animate out and remove
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    updateConfidenceOverview() {
        const overview = document.getElementById('confidence-overview');
        if (!overview) return;
        
        const objects = this.dataManager.getObjectsNeedingValidation();
        const total = this.dataManager.arxObjects.size;
        const needValidation = objects.length;
        const avgConfidence = this.calculateAverageConfidence();
        
        overview.innerHTML = `
            <div class="confidence-stat">
                <span class="stat-label">Total Objects:</span>
                <span class="stat-value">${total}</span>
            </div>
            <div class="confidence-stat">
                <span class="stat-label">Need Validation:</span>
                <span class="stat-value" style="color: ${needValidation > 0 ? '#ff8800' : '#44aa44'}">
                    ${needValidation}
                </span>
            </div>
            <div class="confidence-stat">
                <span class="stat-label">Avg Confidence:</span>
                <span class="stat-value" style="color: ${this.interaction.getConfidenceColor(avgConfidence)}">
                    ${(avgConfidence * 100).toFixed(1)}%
                </span>
            </div>
        `;
    }

    calculateAverageConfidence() {
        let sum = 0;
        let count = 0;
        this.dataManager.arxObjects.forEach(obj => {
            sum += obj.confidence?.overall || 1.0;
            count++;
        });
        return count > 0 ? sum / count : 1.0;
    }
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.arxosApp = new ArxosApp('arxos-viewport');
});