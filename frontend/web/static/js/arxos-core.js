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
            const response = await fetch(`${this.apiBase}/arxobjects`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scale, viewport: viewportNano })
            });
            
            const objects = await response.json();
            this.scaleCache.set(cacheKey, objects);
            
            // Store individual objects with nanometer coordinates
            objects.forEach(obj => {
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
            return [];
        }
    }

    getArxObject(id) {
        return this.arxObjects.get(id);
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
            return; // Already rendered
        }

        const element = this.createSVGElement(arxObject);
        
        // Get or create scale group
        const scaleGroup = this.getOrCreateScaleGroup(arxObject.scaleMin);
        scaleGroup.appendChild(element);
        
        this.renderedObjects.set(arxObject.id, element);
    }

    createSVGElement(arxObject) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('data-arx-id', arxObject.id);
        g.setAttribute('data-system', arxObject.system || 'unknown');
        g.setAttribute('transform', `translate(${arxObject.x}, ${arxObject.y})`);
        
        // Create the actual shape based on type
        const shape = this.createShape(arxObject);
        g.appendChild(shape);
        
        // Apply system-based styling
        this.applySystemStyle(shape, arxObject.system);
        
        return g;
    }

    createShape(arxObject) {
        // Simple shapes for now - can be extended
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('width', arxObject.width || 10);
        rect.setAttribute('height', arxObject.height || 10);
        rect.setAttribute('class', 'arx-object');
        return rect;
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
                break;
            case '1': case '2': case '3': case '4':
                this.toggleSystem(parseInt(event.key) - 1);
                break;
            case 'f':
                this.fitToView();
                break;
        }
    }

    toggleSystem(index) {
        const systems = ['electrical', 'hvac', 'plumbing', 'structural'];
        if (index < systems.length) {
            const system = systems[index];
            const visible = this.stateManager.state.visibleSystems;
            
            if (visible.includes(system)) {
                visible.splice(visible.indexOf(system), 1);
            } else {
                visible.push(system);
            }
            
            this.stateManager.updateState({ visibleSystems: [...visible] });
        }
    }

    showObjectDetails(arxObject) {
        // Simple detail display - can be enhanced
        console.log('ArxObject:', arxObject);
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
        
        // Initial render
        this.renderer.renderAtScale(1.0);
    }
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.arxosApp = new ArxosApp('arxos-viewport');
});