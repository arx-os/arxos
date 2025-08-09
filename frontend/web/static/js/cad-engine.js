/**
 * Arxos CAD Engine - Core Drawing Engine
 * Handles Canvas 2D rendering, precision drawing, and Web Workers integration for high-performance CAD operations
 *
 * @author Arxos Team
 * @version 1.2.0 - Enhanced CAD Features and Parametric Modeling
 * @license MIT
 */

class CadEngine {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.isInitialized = false;

        // Drawing state
        this.currentTool = 'select';
        this.isDrawing = false;
        this.startPoint = null;
        this.currentPoint = null;

        // Enhanced precision settings
        this.precision = 0.001; // Sub-millimeter precision (0.001 inches)
        this.units = 'inches';
        this.scale = 1.0;
        this.gridSize = 0.1; // Grid size in current units

        // CAD-level precision system
        this.precisionLevels = {
            'UI': 0.01,      // UI precision (0.01 inches)
            'EDIT': 0.001,   // Edit precision (0.001 inches)
            'COMPUTE': 0.0001 // Compute precision (0.0001 inches)
        };
        this.currentPrecisionLevel = 'EDIT';

        // Geometric constraint system
        this.constraints = new Map();
        this.constraintSolver = new ConstraintSolver();

        // Parametric modeling system
        this.parameters = new Map();
        this.parametricObjects = new Map();
        this.parameterId = 0;

        // Performance tracking
        this.fps = 60;
        this.lastFrameTime = 0;
        this.frameCount = 0;

        // ArxObjects storage
        this.arxObjects = new Map();
        this.selectedObjects = new Set();

        // Web Workers
        this.workers = new Map();
        this.workerId = 0;

        // Event handlers
        this.eventHandlers = new Map();
        this.eventListeners = new Map();

        // Initialize Web Workers
        this.initializeWorkers();
    }

    /**
     * Initialize the CAD engine
     */
    async initialize(canvasId = 'cad-canvas') {
        try {
            console.log('Initializing Arxos CAD Engine...');

            // Get canvas and context
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) {
                throw new Error(`Canvas element with id '${canvasId}' not found`);
            }

            this.ctx = this.canvas.getContext('2d');
            if (!this.ctx) {
                throw new Error('Could not get 2D context');
            }

            // Set canvas size
            this.resizeCanvas();

            // Initialize drawing tools (only if we're in the main CAD interface)
            if (canvasId === 'cad-canvas') {
                this.initializeDrawingTools();
                this.initializeEventListeners();
            }

            // Start render loop
            this.startRenderLoop();

            this.isInitialized = true;
            console.log('Arxos CAD Engine initialized successfully');

        } catch (error) {
            console.error('Failed to initialize CAD Engine:', error);
            throw error;
        }
    }

    /**
     * Initialize Web Workers for background processing
     */
    initializeWorkers() {
        try {
            // SVGX Processing Worker
            const svgxWorker = new Worker('./static/js/cad-workers.js');
            svgxWorker.onmessage = (event) => {
                this.handleWorkerMessage('svgx', event.data);
            };
            this.workers.set('svgx', svgxWorker);

            // Geometry Processing Worker
            const geometryWorker = new Worker('./static/js/cad-workers.js');
            geometryWorker.onmessage = (event) => {
                this.handleWorkerMessage('geometry', event.data);
            };
            this.workers.set('geometry', geometryWorker);

            // Constraint Solver Worker
            const constraintWorker = new Worker('./static/js/cad-workers.js');
            constraintWorker.onmessage = (event) => {
                this.handleWorkerMessage('constraints', event.data);
            };
            this.workers.set('constraints', constraintWorker);

            console.log('Web Workers initialized:', this.workers.size, 'workers');
        } catch (error) {
            console.warn('Web Workers not available:', error);
            // Continue without Web Workers for now
        }
    }

    /**
     * Handle messages from Web Workers
     */
    handleWorkerMessage(workerType, data) {
        switch (workerType) {
            case 'svgx':
                this.handleSvgxWorkerMessage(data);
                break;
            case 'geometry':
                this.handleGeometryWorkerMessage(data);
                break;
            case 'constraints':
                this.handleConstraintWorkerMessage(data);
                break;
            default:
                console.warn('Unknown worker type:', workerType);
        }
    }

    /**
     * Handle SVGX worker messages
     */
    handleSvgxWorkerMessage(data) {
        switch (data.type) {
            case 'svgx_processed':
                this.updateArxObject(data.objectId, data.result);
                break;
            case 'svgx_error':
                console.error('SVGX processing error:', data.error);
                break;
            default:
                console.warn('Unknown SVGX message type:', data.type);
        }
    }

    /**
     * Handle geometry worker messages
     */
    handleGeometryWorkerMessage(data) {
        switch (data.type) {
            case 'geometry_calculated':
                this.updateGeometry(data.objectId, data.geometry);
                break;
            case 'geometry_error':
                console.error('Geometry calculation error:', data.error);
                break;
            default:
                console.warn('Unknown geometry message type:', data.type);
        }
    }

    /**
     * Handle constraint worker messages
     */
    handleConstraintWorkerMessage(data) {
        switch (data.type) {
            case 'constraints_solved':
                this.updateConstraints(data.objectId, data.constraints);
                break;
            case 'constraints_error':
                console.error('Constraint solving error:', data.error);
                break;
            default:
                console.warn('Unknown constraint message type:', data.type);
        }
    }

    /**
     * Resize canvas to fit container
     */
    resizeCanvas() {
        const container = this.canvas.parentElement;
        const rect = container.getBoundingClientRect();

        this.canvas.width = rect.width;
        this.canvas.height = rect.height;

        // Update canvas style
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';

        console.log('Canvas resized to:', rect.width, 'x', rect.height);
    }

    /**
     * Initialize drawing tools
     */
    initializeDrawingTools() {
        // Tool selection
        const toolButtons = document.querySelectorAll('.cad-tool-btn');
        toolButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.setCurrentTool(button.dataset.tool);

                // Update active state
                toolButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            });
        });

        // Precision selection
        const precisionSelect = document.getElementById('precision-select');
        if (precisionSelect) {
            precisionSelect.addEventListener('change', (e) => {
                this.setPrecisionLevel(e.target.value);
            });
        }
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Mouse events
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));

        // Keyboard events
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        document.addEventListener('keyup', (e) => this.handleKeyUp(e));

        // Window resize
        window.addEventListener('resize', () => this.resizeCanvas());

        // Touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e));
    }

    /**
     * Handle mouse down event
     */
    handleMouseDown(event) {
        const point = this.getCanvasPoint(event);
        if (!point) return; // Exit if point is invalid

        this.startPoint = this.snapToGrid(point);

        switch (this.currentTool) {
            case 'select':
                this.selectObjectAtPoint(this.startPoint);
                break;
            case 'line':
            case 'rectangle':
            case 'circle':
                this.isDrawing = true;
                this.currentPoint = this.startPoint;
                break;
        }

        this.updateMouseCoordinates(this.startPoint);
    }

    /**
     * Handle mouse move event
     */
    handleMouseMove(event) {
        const point = this.getCanvasPoint(event);
        if (!point) return; // Exit if point is invalid

        this.currentPoint = this.snapToGrid(point);

        if (this.isDrawing) {
            this.previewDrawing();
        }

        this.updateMouseCoordinates(this.currentPoint);
    }

    /**
     * Handle mouse up event
     */
    handleMouseUp(event) {
        if (this.isDrawing) {
            this.finishDrawing();
            this.isDrawing = false;
        }
    }

    /**
     * Handle key down event
     */
    handleKeyDown(event) {
        switch (event.key) {
            case 'Delete':
            case 'Backspace':
                this.deleteSelectedObjects();
                break;
            case 'Escape':
                this.cancelDrawing();
                break;
            case 'Ctrl+z':
            case 'Meta+z':
                event.preventDefault();
                this.undo();
                break;
            case 'Ctrl+y':
            case 'Meta+y':
                event.preventDefault();
                this.redo();
                break;
        }
    }

    /**
     * Handle key up event
     */
    handleKeyUp(event) {
        // Handle key up events if needed
    }

    /**
     * Handle touch events for mobile
     */
    handleTouchStart(event) {
        event.preventDefault();
        const touch = event.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.handleMouseDown(mouseEvent);
    }

    handleTouchMove(event) {
        event.preventDefault();
        const touch = event.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        this.handleMouseMove(mouseEvent);
    }

    handleTouchEnd(event) {
        event.preventDefault();
        const mouseEvent = new MouseEvent('mouseup', {});
        this.handleMouseUp(mouseEvent);
    }

    /**
     * Enhanced precision coordinate calculation with sub-millimeter accuracy
     * @param {number} x - Raw x coordinate
     * @param {number} y - Raw y coordinate
     * @returns {Object} Precision-adjusted point
     */
    calculatePrecisionPoint(x, y) {
        // Convert to current units and apply precision
        const precision = this.precisionLevels[this.currentPrecisionLevel];

        // Apply sub-millimeter precision (0.001 inches = 0.0254 mm)
        const precisionX = Math.round(x / precision) * precision;
        const precisionY = Math.round(y / precision) * precision;

        // Validate precision bounds
        const maxCoordinate = 1000000; // 1 million units
        if (Math.abs(precisionX) > maxCoordinate || Math.abs(precisionY) > maxCoordinate) {
            console.warn('Coordinate out of bounds:', { x: precisionX, y: precisionY });
            return null;
        }

        return {
            x: precisionX,
            y: precisionY,
            precision: precision,
            units: this.units,
            timestamp: Date.now()
        };
    }

    /**
     * Get canvas point with enhanced precision and validation
     * @param {Event} event - Mouse or touch event
     * @returns {Object} Precision-adjusted canvas point
     */
    getCanvasPoint(event) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;

        let clientX, clientY;

        if (event.touches && event.touches.length > 0) {
            clientX = event.touches[0].clientX;
            clientY = event.touches[0].clientY;
        } else {
            clientX = event.clientX;
            clientY = event.clientY;
        }

        const canvasX = (clientX - rect.left) * scaleX;
        const canvasY = (clientY - rect.top) * scaleY;

        // Apply precision and grid snapping
        const precisionPoint = this.calculatePrecisionPoint(canvasX, canvasY);
        if (!precisionPoint) return null;

        // Apply grid snapping if enabled
        if (document.getElementById('grid-snap')?.checked) {
            return this.snapToGrid(precisionPoint);
        }

        return precisionPoint;
    }

    /**
     * Enhanced grid snapping with precision levels
     * @param {Object} point - Point to snap
     * @returns {Object} Snapped point
     */
    snapToGrid(point) {
        const gridSize = parseFloat(document.getElementById('grid-size')?.value || this.gridSize);
        const precision = this.precisionLevels[this.currentPrecisionLevel];

        // Use the smaller of grid size or precision for snapping
        const snapSize = Math.min(gridSize, precision);

        const snappedX = Math.round(point.x / snapSize) * snapSize;
        const snappedY = Math.round(point.y / snapSize) * snapSize;

        return {
            ...point,
            x: snappedX,
            y: snappedY,
            snapped: true,
            snapSize: snapSize
        };
    }

    /**
     * Set precision level with validation and UI updates
     * @param {string} level - Precision level (UI, EDIT, COMPUTE)
     */
    setPrecisionLevel(level) {
        if (!this.precisionLevels[level]) {
            console.error('Invalid precision level:', level);
            return;
        }

        this.currentPrecisionLevel = level;
        this.precision = this.precisionLevels[level];

        // Update UI
        const precisionSelect = document.getElementById('precision-level');
        if (precisionSelect) {
            precisionSelect.value = level;
        }

        // Update status bar
        this.updateMouseCoordinates({ x: 0, y: 0 });

        console.log(`Precision level set to: ${level} (${this.precision} ${this.units})`);

        // Dispatch precision change event
        this.dispatchEvent('precisionChanged', {
            level: level,
            precision: this.precision,
            units: this.units
        });
    }

    /**
     * Update mouse coordinates display with enhanced precision
     * @param {Object} point - Current mouse point
     */
    updateMouseCoordinates(point) {
        const coordsElement = document.getElementById('mouse-coordinates');
        if (coordsElement) {
            const precision = this.precisionLevels[this.currentPrecisionLevel];
            const decimalPlaces = Math.abs(Math.log10(precision));
            const x = point.x.toFixed(decimalPlaces);
            const y = point.y.toFixed(decimalPlaces);
            coordsElement.textContent = `X: ${x}" Y: ${y}" (${this.currentPrecisionLevel})`;
        }
    }

    /**
     * Set current drawing tool
     */
    setCurrentTool(tool) {
        this.currentTool = tool;
        console.log('Current tool set to:', tool);
    }

    /**
     * Preview drawing in real-time
     */
    previewDrawing() {
        if (!this.startPoint || !this.currentPoint) return;

        // Clear canvas and redraw all objects
        this.clearCanvas();
        this.drawAllObjects();

        // Draw preview based on current tool
        this.ctx.save();
        this.ctx.strokeStyle = '#3B82F6';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);

        switch (this.currentTool) {
            case 'line':
                this.drawLine(this.startPoint, this.currentPoint);
                break;
            case 'rectangle':
                this.drawRectangle(this.startPoint, this.currentPoint);
                break;
            case 'circle':
                this.drawCircle(this.startPoint, this.currentPoint);
                break;
        }

        this.ctx.restore();
    }

    /**
     * Finish drawing and create ArxObject
     */
    finishDrawing() {
        if (!this.startPoint || !this.currentPoint) return;

        const arxObject = this.createArxObject(this.startPoint, this.currentPoint);
        if (arxObject) {
            this.addArxObject(arxObject);
            this.render();
        }
    }

    /**
     * Create ArxObject based on current tool
     */
    createArxObject(startPoint, endPoint) {
        const id = this.generateObjectId();

        switch (this.currentTool) {
            case 'line':
                return {
                    id: id,
                    type: 'line',
                    startPoint: startPoint,
                    endPoint: endPoint,
                    properties: {
                        length: this.calculateDistance(startPoint, endPoint),
                        angle: this.calculateAngle(startPoint, endPoint)
                    },
                    constraints: [],
                    measurements: []
                };

            case 'rectangle':
                return {
                    id: id,
                    type: 'rectangle',
                    startPoint: startPoint,
                    endPoint: endPoint,
                    properties: {
                        width: Math.abs(endPoint.x - startPoint.x),
                        height: Math.abs(endPoint.y - startPoint.y),
                        area: Math.abs(endPoint.x - startPoint.x) * Math.abs(endPoint.y - startPoint.y)
                    },
                    constraints: [],
                    measurements: []
                };

            case 'circle':
                const radius = this.calculateDistance(startPoint, endPoint);
                return {
                    id: id,
                    type: 'circle',
                    center: startPoint,
                    radius: radius,
                    properties: {
                        diameter: radius * 2,
                        circumference: 2 * Math.PI * radius,
                        area: Math.PI * radius * radius
                    },
                    constraints: [],
                    measurements: []
                };

            default:
                return null;
        }
    }

    /**
     * Add ArxObject to the drawing
     */
    addArxObject(arxObject) {
        this.arxObjects.set(arxObject.id, arxObject);

        // Send to Web Workers for processing
        this.processArxObject(arxObject);

        console.log('Added ArxObject:', arxObject);
    }

    /**
     * Process ArxObject with Web Workers
     */
    processArxObject(arxObject) {
        // Send to SVGX worker for processing
        const svgxWorker = this.workers.get('svgx');
        if (svgxWorker) {
            svgxWorker.postMessage({
                type: 'process_svgx',
                objectId: arxObject.id,
                object: arxObject
            });
        }

        // Send to geometry worker for calculations
        const geometryWorker = this.workers.get('geometry');
        if (geometryWorker) {
            geometryWorker.postMessage({
                type: 'calculate_geometry',
                objectId: arxObject.id,
                object: arxObject
            });
        }
    }

    /**
     * Start render loop
     */
    startRenderLoop() {
        const render = () => {
            this.render();
            this.updatePerformance();
            requestAnimationFrame(render);
        };
        render();
    }

    /**
     * Main render function
     */
    render() {
        this.clearCanvas();
        this.drawGrid();
        this.drawAllObjects();
        this.drawSelection();
    }

    /**
     * Clear canvas
     */
    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    /**
     * Draw grid
     */
    drawGrid() {
        const gridSize = 10 * this.scale;
        const gridColor = '#374151';

        this.ctx.save();
        this.ctx.strokeStyle = gridColor;
        this.ctx.lineWidth = 1;

        // Draw vertical lines
        for (let x = 0; x <= this.canvas.width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }

        // Draw horizontal lines
        for (let y = 0; y <= this.canvas.height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }

        this.ctx.restore();
    }

    /**
     * Draw all ArxObjects
     */
    drawAllObjects() {
        for (const [id, arxObject] of this.arxObjects) {
            this.drawArxObject(arxObject);
        }
    }

    /**
     * Draw single ArxObject
     */
    drawArxObject(arxObject) {
        this.ctx.save();

        // Set color based on selection
        if (this.selectedObjects.has(arxObject.id)) {
            this.ctx.strokeStyle = '#3B82F6';
            this.ctx.lineWidth = 3;
        } else {
            this.ctx.strokeStyle = '#1F2937';
            this.ctx.lineWidth = 2;
        }

        switch (arxObject.type) {
            case 'line':
                this.drawLine(arxObject.startPoint, arxObject.endPoint);
                break;
            case 'rectangle':
                this.drawRectangle(arxObject.startPoint, arxObject.endPoint);
                break;
            case 'circle':
                this.drawCircle(arxObject.center, { x: arxObject.center.x + arxObject.radius, y: arxObject.center.y });
                break;
        }

        this.ctx.restore();
    }

    /**
     * Draw line
     */
    drawLine(startPoint, endPoint) {
        this.ctx.beginPath();
        this.ctx.moveTo(startPoint.x * this.scale, startPoint.y * this.scale);
        this.ctx.lineTo(endPoint.x * this.scale, endPoint.y * this.scale);
        this.ctx.stroke();
    }

    /**
     * Draw rectangle
     */
    drawRectangle(startPoint, endPoint) {
        const x = Math.min(startPoint.x, endPoint.x) * this.scale;
        const y = Math.min(startPoint.y, endPoint.y) * this.scale;
        const width = Math.abs(endPoint.x - startPoint.x) * this.scale;
        const height = Math.abs(endPoint.y - startPoint.y) * this.scale;

        this.ctx.strokeRect(x, y, width, height);
    }

    /**
     * Draw circle
     */
    drawCircle(center, endPoint) {
        const radius = this.calculateDistance(center, endPoint) * this.scale;

        this.ctx.beginPath();
        this.ctx.arc(center.x * this.scale, center.y * this.scale, radius, 0, 2 * Math.PI);
        this.ctx.stroke();
    }

    /**
     * Draw selection indicators
     */
    drawSelection() {
        for (const objectId of this.selectedObjects) {
            const arxObject = this.arxObjects.get(objectId);
            if (arxObject) {
                this.drawSelectionBox(arxObject);
            }
        }
    }

    /**
     * Draw selection box around object
     */
    drawSelectionBox(arxObject) {
        // Implementation for selection box drawing
        // This would draw handles around selected objects
    }

    /**
     * Update performance metrics
     */
    updatePerformance() {
        const now = performance.now();
        const deltaTime = now - this.lastFrameTime;

        if (deltaTime > 0) {
            this.fps = 1000 / deltaTime;
        }

        this.lastFrameTime = now;
        this.frameCount++;

        // Update performance display
        const performanceElement = document.getElementById('performance-info');
        if (performanceElement) {
            performanceElement.textContent = `FPS: ${Math.round(this.fps)} | Objects: ${this.arxObjects.size}`;
        }
    }

    /**
     * Utility functions
     */
    calculateDistance(point1, point2) {
        const dx = point2.x - point1.x;
        const dy = point2.y - point1.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Round to current precision level
        const precision = this.precisionLevels[this.currentPrecisionLevel];
        return Math.round(distance / precision) * precision;
    }

    calculateAngle(point1, point2) {
        const angle = Math.atan2(point2.y - point1.y, point2.x - point1.x) * 180 / Math.PI;

        // Round to 0.1 degrees for CAD precision
        return Math.round(angle * 10) / 10;
    }

    generateObjectId() {
        return 'arx_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Selection methods
     */
    selectObjectAtPoint(point) {
        // Find object at point and select it
        for (const [id, arxObject] of this.arxObjects) {
            if (this.isPointInObject(point, arxObject)) {
                this.selectedObjects.add(id);
                this.updatePropertiesPanel(arxObject);
                return;
            }
        }

        // Clear selection if no object found
        this.selectedObjects.clear();
        this.updatePropertiesPanel(null);
    }

    isPointInObject(point, arxObject) {
        // Implementation for point-in-object detection
        // This would check if a point is within an object's bounds
        return false; // Placeholder
    }

    /**
     * Update properties panel
     */
    updatePropertiesPanel(arxObject) {
        const propertiesContent = document.getElementById('properties-content');
        if (!propertiesContent) return;

        if (arxObject) {
            propertiesContent.innerHTML = this.generatePropertiesHTML(arxObject);
        } else {
            propertiesContent.innerHTML = '<div class="text-gray-400 text-sm">Select an object to view properties</div>';
        }
    }

    generatePropertiesHTML(arxObject) {
        // Generate HTML for object properties
        return `<div class="space-y-2">
            <div><strong>Type:</strong> ${arxObject.type}</div>
            <div><strong>ID:</strong> ${arxObject.id}</div>
            ${Object.entries(arxObject.properties).map(([key, value]) =>
                `<div><strong>${key}:</strong> ${value}</div>`
            ).join('')}
        </div>`;
    }

    /**
     * Delete selected objects
     */
    deleteSelectedObjects() {
        for (const objectId of this.selectedObjects) {
            this.arxObjects.delete(objectId);
        }
        this.selectedObjects.clear();
        this.updatePropertiesPanel(null);
    }

    /**
     * Cancel current drawing
     */
    cancelDrawing() {
        this.isDrawing = false;
        this.startPoint = null;
        this.currentPoint = null;
    }

    /**
     * Undo/Redo (placeholder)
     */
    undo() {
        console.log('Undo not implemented yet');
    }

    redo() {
        console.log('Redo not implemented yet');
    }

    /**
     * Event system methods
     */
    addEventListener(eventType, callback) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(callback);
    }

    removeEventListener(eventType, callback) {
        if (this.eventListeners.has(eventType)) {
            const listeners = this.eventListeners.get(eventType);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    dispatchEvent(eventType, data) {
        if (this.eventListeners.has(eventType)) {
            const listeners = this.eventListeners.get(eventType);
            listeners.forEach(callback => {
                try {
                    callback({ type: eventType, ...data });
                } catch (error) {
                    console.error('Event listener error:', error);
                }
            });
        }
    }

    /**
     * Export to SVG
     */
    exportToSVG() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', this.canvas.width);
        svg.setAttribute('height', this.canvas.height);
        svg.setAttribute('viewBox', `0 0 ${this.canvas.width} ${this.canvas.height}`);

        // Add grid
        const gridGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        gridGroup.setAttribute('id', 'grid');

        const gridSize = 10 * this.scale;
        for (let x = 0; x <= this.canvas.width; x += gridSize) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x);
            line.setAttribute('y1', 0);
            line.setAttribute('x2', x);
            line.setAttribute('y2', this.canvas.height);
            line.setAttribute('stroke', '#374151');
            line.setAttribute('stroke-width', '1');
            gridGroup.appendChild(line);
        }

        for (let y = 0; y <= this.canvas.height; y += gridSize) {
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', 0);
            line.setAttribute('y1', y);
            line.setAttribute('x2', this.canvas.width);
            line.setAttribute('y2', y);
            line.setAttribute('stroke', '#374151');
            line.setAttribute('stroke-width', '1');
            gridGroup.appendChild(line);
        }

        svg.appendChild(gridGroup);

        // Add objects
        for (const [id, arxObject] of this.arxObjects) {
            const objectGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            objectGroup.setAttribute('id', arxObject.id);

            switch (arxObject.type) {
                case 'line':
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', arxObject.startPoint.x * this.scale);
                    line.setAttribute('y1', arxObject.startPoint.y * this.scale);
                    line.setAttribute('x2', arxObject.endPoint.x * this.scale);
                    line.setAttribute('y2', arxObject.endPoint.y * this.scale);
                    line.setAttribute('stroke', '#1F2937');
                    line.setAttribute('stroke-width', '2');
                    objectGroup.appendChild(line);
                    break;

                case 'rectangle':
                    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                    const x = Math.min(arxObject.startPoint.x, arxObject.endPoint.x) * this.scale;
                    const y = Math.min(arxObject.startPoint.y, arxObject.endPoint.y) * this.scale;
                    const width = Math.abs(arxObject.endPoint.x - arxObject.startPoint.x) * this.scale;
                    const height = Math.abs(arxObject.endPoint.y - arxObject.startPoint.y) * this.scale;

                    rect.setAttribute('x', x);
                    rect.setAttribute('y', y);
                    rect.setAttribute('width', width);
                    rect.setAttribute('height', height);
                    rect.setAttribute('stroke', '#1F2937');
                    rect.setAttribute('stroke-width', '2');
                    rect.setAttribute('fill', 'none');
                    objectGroup.appendChild(rect);
                    break;

                case 'circle':
                    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                    const radius = arxObject.radius * this.scale;

                    circle.setAttribute('cx', arxObject.center.x * this.scale);
                    circle.setAttribute('cy', arxObject.center.y * this.scale);
                    circle.setAttribute('r', radius);
                    circle.setAttribute('stroke', '#1F2937');
                    circle.setAttribute('stroke-width', '2');
                    circle.setAttribute('fill', 'none');
                    objectGroup.appendChild(circle);
                    break;
            }

            svg.appendChild(objectGroup);
        }

        return new XMLSerializer().serializeToString(svg);
    }

    /**
     * Update ArxObject
     */
    updateArxObject(objectId, updates) {
        const arxObject = this.arxObjects.get(objectId);
        if (!arxObject) {
            throw new Error('Object not found');
        }

        // Update properties
        if (updates.properties) {
            arxObject.properties = { ...arxObject.properties, ...updates.properties };
        }

        // Update geometry
        if (updates.geometry) {
            arxObject.geometry = { ...arxObject.geometry, ...updates.geometry };
        }

        // Dispatch event
        this.dispatchEvent('objectUpdated', { objectId, arxObject });

        return arxObject;
    }

    /**
     * Parametric Modeling Methods
     */

    /**
     * Define a parameter for parametric modeling
     * @param {string} name - Parameter name
     * @param {number} value - Parameter value
     * @param {Object} constraints - Parameter constraints
     * @returns {string} Parameter ID
     */
    defineParameter(name, value, constraints = {}) {
        const parameterId = `param_${++this.parameterId}`;

        const parameter = {
            id: parameterId,
            name: name,
            value: value,
            constraints: constraints,
            createdAt: Date.now()
        };

        this.parameters.set(parameterId, parameter);
        console.log(`Defined parameter: ${name} = ${value}`, parameter);

        // Dispatch event
        this.dispatchEvent('parameterDefined', { parameterId, parameter });

        return parameterId;
    }

    /**
     * Update a parameter value
     * @param {string} parameterId - Parameter ID
     * @param {number} newValue - New parameter value
     */
    updateParameter(parameterId, newValue) {
        const parameter = this.parameters.get(parameterId);
        if (!parameter) {
            throw new Error(`Parameter not found: ${parameterId}`);
        }

        // Validate constraints
        if (parameter.constraints.min !== undefined && newValue < parameter.constraints.min) {
            throw new Error(`Value ${newValue} is below minimum ${parameter.constraints.min}`);
        }
        if (parameter.constraints.max !== undefined && newValue > parameter.constraints.max) {
            throw new Error(`Value ${newValue} is above maximum ${parameter.constraints.max}`);
        }

        parameter.value = newValue;
        parameter.updatedAt = Date.now();

        // Update all parametric objects that depend on this parameter
        this.updateParametricObjects(parameterId);

        // Dispatch event
        this.dispatchEvent('parameterUpdated', { parameterId, parameter });

        console.log(`Updated parameter: ${parameter.name} = ${newValue}`);
    }

    /**
     * Create a parametric object
     * @param {string} type - Object type
     * @param {Object} parameters - Parameter dependencies
     * @param {Object} geometry - Base geometry
     * @returns {string} Object ID
     */
    createParametricObject(type, parameters, geometry) {
        const objectId = this.generateObjectId();

        const parametricObject = {
            id: objectId,
            type: type,
            parameters: parameters,
            baseGeometry: geometry,
            createdAt: Date.now()
        };

        this.parametricObjects.set(objectId, parametricObject);

        // Generate initial geometry
        this.generateParametricGeometry(objectId);

        console.log(`Created parametric object: ${type}`, parametricObject);

        // Dispatch event
        this.dispatchEvent('parametricObjectCreated', { objectId, parametricObject });

        return objectId;
    }

    /**
     * Generate geometry for a parametric object
     * @param {string} objectId - Parametric object ID
     */
    generateParametricGeometry(objectId) {
        const parametricObject = this.parametricObjects.get(objectId);
        if (!parametricObject) {
            throw new Error(`Parametric object not found: ${objectId}`);
        }

        // Calculate parameter values
        const parameterValues = {};
        for (const [paramName, paramId] of Object.entries(parametricObject.parameters)) {
            const parameter = this.parameters.get(paramId);
            if (parameter) {
                parameterValues[paramName] = parameter.value;
            }
        }

        // Generate geometry based on type and parameters
        let geometry;
        switch (parametricObject.type) {
            case 'rectangle':
                geometry = this.generateParametricRectangle(parametricObject.baseGeometry, parameterValues);
                break;
            case 'circle':
                geometry = this.generateParametricCircle(parametricObject.baseGeometry, parameterValues);
                break;
            case 'line':
                geometry = this.generateParametricLine(parametricObject.baseGeometry, parameterValues);
                break;
            default:
                throw new Error(`Unknown parametric object type: ${parametricObject.type}`);
        }

        // Create or update ArxObject
        const arxObject = {
            id: objectId,
            type: parametricObject.type,
            geometry: geometry,
            isParametric: true,
            parameterDependencies: parametricObject.parameters
        };

        this.arxObjects.set(objectId, arxObject);

        // Dispatch event
        this.dispatchEvent('parametricGeometryGenerated', { objectId, geometry });
    }

    /**
     * Generate parametric rectangle geometry
     * @param {Object} baseGeometry - Base geometry
     * @param {Object} parameters - Parameter values
     * @returns {Object} Generated geometry
     */
    generateParametricRectangle(baseGeometry, parameters) {
        const width = parameters.width || baseGeometry.width || 1;
        const height = parameters.height || baseGeometry.height || 1;
        const x = parameters.x || baseGeometry.x || 0;
        const y = parameters.y || baseGeometry.y || 0;

        return {
            type: 'rectangle',
            startPoint: { x: x, y: y },
            endPoint: { x: x + width, y: y + height },
            width: width,
            height: height
        };
    }

    /**
     * Generate parametric circle geometry
     * @param {Object} baseGeometry - Base geometry
     * @param {Object} parameters - Parameter values
     * @returns {Object} Generated geometry
     */
    generateParametricCircle(baseGeometry, parameters) {
        const radius = parameters.radius || baseGeometry.radius || 1;
        const centerX = parameters.centerX || baseGeometry.centerX || 0;
        const centerY = parameters.centerY || baseGeometry.centerY || 0;

        return {
            type: 'circle',
            center: { x: centerX, y: centerY },
            radius: radius
        };
    }

    /**
     * Generate parametric line geometry
     * @param {Object} baseGeometry - Base geometry
     * @param {Object} parameters - Parameter values
     * @returns {Object} Generated geometry
     */
    generateParametricLine(baseGeometry, parameters) {
        const startX = parameters.startX || baseGeometry.startX || 0;
        const startY = parameters.startY || baseGeometry.startY || 0;
        const endX = parameters.endX || baseGeometry.endX || 1;
        const endY = parameters.endY || baseGeometry.endY || 1;

        return {
            type: 'line',
            startPoint: { x: startX, y: startY },
            endPoint: { x: endX, y: endY }
        };
    }

    /**
     * Update all parametric objects that depend on a parameter
     * @param {string} parameterId - Parameter ID
     */
    updateParametricObjects(parameterId) {
        for (const [objectId, parametricObject] of this.parametricObjects) {
            // Check if this object depends on the updated parameter
            const dependsOnParameter = Object.values(parametricObject.parameters).includes(parameterId);

            if (dependsOnParameter) {
                this.generateParametricGeometry(objectId);
            }
        }
    }

    /**
     * Get all parameters
     * @returns {Array} Array of parameters
     */
    getParameters() {
        return Array.from(this.parameters.values());
    }

    /**
     * Get all parametric objects
     * @returns {Array} Array of parametric objects
     */
    getParametricObjects() {
        return Array.from(this.parametricObjects.values());
    }

    /**
     * Remove a parameter and update dependent objects
     * @param {string} parameterId - Parameter ID to remove
     */
    removeParameter(parameterId) {
        if (this.parameters.has(parameterId)) {
            this.parameters.delete(parameterId);

            // Remove parametric objects that depend on this parameter
            for (const [objectId, parametricObject] of this.parametricObjects) {
                const dependsOnParameter = Object.values(parametricObject.parameters).includes(parameterId);

                if (dependsOnParameter) {
                    this.parametricObjects.delete(objectId);
                    this.arxObjects.delete(objectId);
                }
            }

            console.log(`Removed parameter: ${parameterId}`);

            // Dispatch event
            this.dispatchEvent('parameterRemoved', { parameterId });
        }
    }

    /**
     * Enhanced Constraint Integration Methods
     */

    /**
     * Add a constraint with enhanced precision
     * @param {string} type - Constraint type
     * @param {Object} params - Constraint parameters
     * @returns {string} Constraint ID
     */
    addConstraint(type, params) {
        if (!this.constraintSolver) {
            throw new Error('Constraint solver not initialized');
        }

        const constraintId = this.constraintSolver.addConstraint(type, params);

        // Apply constraint to affected objects
        const affectedObjects = this.getAffectedObjects(params);
        if (affectedObjects.length > 0) {
            const updatedObjects = this.constraintSolver.solveConstraints(affectedObjects);
            this.updateObjectsFromConstraints(updatedObjects);
        }

        // Dispatch event
        this.dispatchEvent('constraintAdded', { constraintId, type, params });

        return constraintId;
    }

    /**
     * Get objects affected by a constraint
     * @param {Object} params - Constraint parameters
     * @returns {Array} Affected objects
     */
    getAffectedObjects(params) {
        const affectedObjects = [];

        if (params.objectIds) {
            for (const objectId of params.objectIds) {
                const arxObject = this.arxObjects.get(objectId);
                if (arxObject) {
                    affectedObjects.push(arxObject);
                }
            }
        }

        return affectedObjects;
    }

    /**
     * Update objects from constraint solving
     * @param {Array} updatedObjects - Updated objects from constraint solver
     */
    updateObjectsFromConstraints(updatedObjects) {
        for (const updatedObject of updatedObjects) {
            const existingObject = this.arxObjects.get(updatedObject.id);
            if (existingObject) {
                // Update geometry
                if (updatedObject.geometry) {
                    existingObject.geometry = updatedObject.geometry;
                }

                // Update properties
                if (updatedObject.properties) {
                    existingObject.properties = { ...existingObject.properties, ...updatedObject.properties };
                }

                // Dispatch event
                this.dispatchEvent('objectUpdated', { objectId: updatedObject.id, arxObject: existingObject });
            }
        }
    }

    /**
     * Get constraint statistics
     * @returns {Object} Constraint statistics
     */
    getConstraintStatistics() {
        if (!this.constraintSolver) {
            return { totalConstraints: 0, activeConstraints: 0 };
        }

        return this.constraintSolver.getStatistics();
    }

    /**
     * Enhanced Precision Methods
     */

    /**
     * Set precision level with validation
     * @param {string} level - Precision level (UI, EDIT, COMPUTE)
     */
    setPrecisionLevel(level) {
        if (!this.precisionLevels[level]) {
            throw new Error(`Invalid precision level: ${level}`);
        }

        this.currentPrecisionLevel = level;
        this.precision = this.precisionLevels[level];

        // Update constraint solver precision
        if (this.constraintSolver) {
            this.constraintSolver.precision = this.precision;
        }

        console.log(`Precision level set to: ${level} (${this.precision} inches)`);

        // Dispatch event
        this.dispatchEvent('precisionChanged', { level, precision: this.precision });
    }

    /**
     * Validate precision for a value
     * @param {number} value - Value to validate
     * @param {string} level - Precision level to validate against
     * @returns {boolean} True if value meets precision requirements
     */
    validatePrecision(value, level = this.currentPrecisionLevel) {
        const requiredPrecision = this.precisionLevels[level];
        const roundedValue = Math.round(value / requiredPrecision) * requiredPrecision;
        return Math.abs(value - roundedValue) < requiredPrecision / 2;
    }

    /**
     * Round value to current precision level
     * @param {number} value - Value to round
     * @returns {number} Rounded value
     */
    roundToPrecision(value) {
        const precision = this.precisionLevels[this.currentPrecisionLevel];
        return Math.round(value / precision) * precision;
    }
}

// Export for global use
window.CadEngine = CadEngine;
