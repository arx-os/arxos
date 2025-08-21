/**
 * Interactive BIM Viewer for Arxos
 * Provides pan, zoom, select, and edit capabilities for building components
 */

class InteractiveBIMViewer {
    constructor(canvasId, options = {}) {
        this.svg = document.getElementById(canvasId);
        this.viewport = document.getElementById('bim-viewport');
        
        // View state
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.rotation = 0;
        
        // Interaction state
        this.mode = 'pan'; // 'pan', 'select', 'edit', 'measure'
        this.selectedObjects = new Set();
        this.hoveredObject = null;
        this.isDragging = false;
        this.isPanning = false;
        
        // Data
        this.objects = [];
        this.objectMap = new Map();
        this.relationships = new Map();
        
        // Options
        this.options = {
            gridVisible: true,
            snapToGrid: true,
            gridSize: 100, // mm
            selectionColor: '#4CAF50',
            hoverColor: '#2196F3',
            editHandleSize: 8,
            minZoom: 0.1,
            maxZoom: 10,
            ...options
        };
        
        // Edit state
        this.editHandles = [];
        this.dragStart = null;
        this.originalPositions = new Map();
        
        // Measurement state
        this.measurePoints = [];
        this.measurements = [];
        
        // Initialize
        this.setupViewport();
        this.setupInteractions();
        this.setupKeyboardShortcuts();
        this.createLayers();
        this.createUI();
    }
    
    setupViewport() {
        const rect = this.viewport.getBoundingClientRect();
        this.svg.setAttribute('width', rect.width);
        this.svg.setAttribute('height', rect.height);
        this.viewportWidth = rect.width;
        this.viewportHeight = rect.height;
        
        // Set initial viewBox
        this.svg.setAttribute('viewBox', `0 0 ${rect.width} ${rect.height}`);
        
        // Enable pointer events
        this.svg.style.cursor = 'grab';
    }
    
    createLayers() {
        // Clear existing content
        while (this.svg.firstChild) {
            this.svg.removeChild(this.svg.firstChild);
        }
        
        // Create layer structure
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        this.svg.appendChild(defs);
        
        // Add patterns and filters
        this.createPatterns(defs);
        this.createFilters(defs);
        
        // Create layer groups
        this.gridLayer = this.createGroup('grid-layer');
        this.objectLayer = this.createGroup('object-layer');
        this.selectionLayer = this.createGroup('selection-layer');
        this.annotationLayer = this.createGroup('annotation-layer');
        this.handleLayer = this.createGroup('handle-layer');
        
        // Create main transform group
        this.mainGroup = this.createGroup('main-group');
        this.mainGroup.appendChild(this.gridLayer);
        this.mainGroup.appendChild(this.objectLayer);
        this.mainGroup.appendChild(this.selectionLayer);
        this.mainGroup.appendChild(this.annotationLayer);
        this.mainGroup.appendChild(this.handleLayer);
        
        this.svg.appendChild(this.mainGroup);
        
        // Draw grid
        this.drawGrid();
    }
    
    createPatterns(defs) {
        // Grid pattern
        const pattern = document.createElementNS('http://www.w3.org/2000/svg', 'pattern');
        pattern.setAttribute('id', 'grid-pattern');
        pattern.setAttribute('width', this.options.gridSize);
        pattern.setAttribute('height', this.options.gridSize);
        pattern.setAttribute('patternUnits', 'userSpaceOnUse');
        
        const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line1.setAttribute('x1', '0');
        line1.setAttribute('y1', '0');
        line1.setAttribute('x2', this.options.gridSize);
        line1.setAttribute('y2', '0');
        line1.setAttribute('stroke', '#e0e0e0');
        line1.setAttribute('stroke-width', '0.5');
        
        const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line2.setAttribute('x1', '0');
        line2.setAttribute('y1', '0');
        line2.setAttribute('x2', '0');
        line2.setAttribute('y2', this.options.gridSize);
        line2.setAttribute('stroke', '#e0e0e0');
        line2.setAttribute('stroke-width', '0.5');
        
        pattern.appendChild(line1);
        pattern.appendChild(line2);
        defs.appendChild(pattern);
    }
    
    createFilters(defs) {
        // Drop shadow filter
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'drop-shadow');
        filter.setAttribute('x', '-50%');
        filter.setAttribute('y', '-50%');
        filter.setAttribute('width', '200%');
        filter.setAttribute('height', '200%');
        
        const feGaussianBlur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
        feGaussianBlur.setAttribute('in', 'SourceAlpha');
        feGaussianBlur.setAttribute('stdDeviation', '3');
        
        const feOffset = document.createElementNS('http://www.w3.org/2000/svg', 'feOffset');
        feOffset.setAttribute('dx', '2');
        feOffset.setAttribute('dy', '2');
        feOffset.setAttribute('result', 'offsetblur');
        
        const feComponentTransfer = document.createElementNS('http://www.w3.org/2000/svg', 'feComponentTransfer');
        const feFuncA = document.createElementNS('http://www.w3.org/2000/svg', 'feFuncA');
        feFuncA.setAttribute('type', 'linear');
        feFuncA.setAttribute('slope', '0.3');
        feComponentTransfer.appendChild(feFuncA);
        
        const feMerge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
        const feMergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        const feMergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
        feMergeNode2.setAttribute('in', 'SourceGraphic');
        feMerge.appendChild(feMergeNode1);
        feMerge.appendChild(feMergeNode2);
        
        filter.appendChild(feGaussianBlur);
        filter.appendChild(feOffset);
        filter.appendChild(feComponentTransfer);
        filter.appendChild(feMerge);
        defs.appendChild(filter);
    }
    
    drawGrid() {
        if (!this.options.gridVisible) return;
        
        // Create grid rectangle
        const gridRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        gridRect.setAttribute('x', '-10000');
        gridRect.setAttribute('y', '-10000');
        gridRect.setAttribute('width', '20000');
        gridRect.setAttribute('height', '20000');
        gridRect.setAttribute('fill', 'url(#grid-pattern)');
        gridRect.setAttribute('opacity', '0.5');
        
        this.gridLayer.appendChild(gridRect);
    }
    
    setupInteractions() {
        // Mouse events
        this.svg.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.svg.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.svg.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.svg.addEventListener('wheel', this.handleWheel.bind(this));
        this.svg.addEventListener('dblclick', this.handleDoubleClick.bind(this));
        
        // Touch events for mobile
        this.svg.addEventListener('touchstart', this.handleTouchStart.bind(this));
        this.svg.addEventListener('touchmove', this.handleTouchMove.bind(this));
        this.svg.addEventListener('touchend', this.handleTouchEnd.bind(this));
        
        // Context menu
        this.svg.addEventListener('contextmenu', this.handleContextMenu.bind(this));
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Mode switching
            if (e.key === 'v') this.setMode('pan');
            else if (e.key === 's') this.setMode('select');
            else if (e.key === 'e') this.setMode('edit');
            else if (e.key === 'm') this.setMode('measure');
            
            // Selection
            else if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                this.selectAll();
            }
            else if (e.key === 'Escape') {
                this.clearSelection();
                this.clearMeasurement();
            }
            
            // Delete
            else if (e.key === 'Delete' || e.key === 'Backspace') {
                this.deleteSelected();
            }
            
            // Copy/Paste
            else if (e.key === 'c' && (e.ctrlKey || e.metaKey)) {
                this.copySelected();
            }
            else if (e.key === 'v' && (e.ctrlKey || e.metaKey)) {
                this.pasteObjects();
            }
            
            // Undo/Redo
            else if (e.key === 'z' && (e.ctrlKey || e.metaKey)) {
                if (e.shiftKey) this.redo();
                else this.undo();
            }
            
            // Grid
            else if (e.key === 'g') {
                this.toggleGrid();
            }
            
            // Zoom
            else if (e.key === '=' || e.key === '+') {
                this.zoomIn();
            }
            else if (e.key === '-' || e.key === '_') {
                this.zoomOut();
            }
            else if (e.key === '0') {
                this.resetView();
            }
        });
    }
    
    handleMouseDown(e) {
        const point = this.getMousePosition(e);
        
        if (this.mode === 'pan') {
            this.startPan(point);
        } else if (this.mode === 'select') {
            this.startSelection(point, e);
        } else if (this.mode === 'edit') {
            this.startEdit(point, e);
        } else if (this.mode === 'measure') {
            this.addMeasurePoint(point);
        }
    }
    
    handleMouseMove(e) {
        const point = this.getMousePosition(e);
        
        if (this.isPanning) {
            this.pan(point);
        } else if (this.isDragging) {
            this.drag(point);
        } else {
            this.hover(point);
        }
    }
    
    handleMouseUp(e) {
        if (this.isPanning) {
            this.endPan();
        } else if (this.isDragging) {
            this.endDrag();
        }
    }
    
    handleWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        const point = this.getMousePosition(e);
        this.zoom(delta, point);
    }
    
    handleDoubleClick(e) {
        const point = this.getMousePosition(e);
        const object = this.getObjectAtPoint(point);
        
        if (object) {
            this.editObject(object);
        }
    }
    
    handleTouchStart(e) {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const point = this.getTouchPosition(touch);
            this.handleMouseDown({ clientX: touch.clientX, clientY: touch.clientY });
        } else if (e.touches.length === 2) {
            // Pinch zoom
            this.startPinchZoom(e.touches);
        }
    }
    
    handleTouchMove(e) {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            this.handleMouseMove({ clientX: touch.clientX, clientY: touch.clientY });
        } else if (e.touches.length === 2) {
            this.pinchZoom(e.touches);
        }
    }
    
    handleTouchEnd(e) {
        this.handleMouseUp({});
    }
    
    handleContextMenu(e) {
        e.preventDefault();
        const point = this.getMousePosition(e);
        this.showContextMenu(point, e);
    }
    
    // Coordinate transformations
    getMousePosition(e) {
        const rect = this.svg.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left - this.translateX) / this.scale,
            y: (e.clientY - rect.top - this.translateY) / this.scale
        };
    }
    
    getTouchPosition(touch) {
        const rect = this.svg.getBoundingClientRect();
        return {
            x: (touch.clientX - rect.left - this.translateX) / this.scale,
            y: (touch.clientY - rect.top - this.translateY) / this.scale
        };
    }
    
    // Mode management
    setMode(mode) {
        this.mode = mode;
        this.svg.className = `mode-${mode}`;
        
        // Update cursor
        if (mode === 'pan') {
            this.svg.style.cursor = 'grab';
        } else if (mode === 'select') {
            this.svg.style.cursor = 'crosshair';
        } else if (mode === 'edit') {
            this.svg.style.cursor = 'pointer';
        } else if (mode === 'measure') {
            this.svg.style.cursor = 'crosshair';
        }
        
        // Clear mode-specific state
        if (mode !== 'measure') {
            this.clearMeasurement();
        }
        
        // Dispatch mode change event
        this.dispatchEvent('modechange', { mode });
    }
    
    // Pan functionality
    startPan(point) {
        this.isPanning = true;
        this.panStart = {
            x: point.x * this.scale + this.translateX,
            y: point.y * this.scale + this.translateY
        };
        this.svg.style.cursor = 'grabbing';
    }
    
    pan(point) {
        if (!this.isPanning) return;
        
        this.translateX = this.panStart.x - point.x * this.scale;
        this.translateY = this.panStart.y - point.y * this.scale;
        this.updateTransform();
    }
    
    endPan() {
        this.isPanning = false;
        this.svg.style.cursor = this.mode === 'pan' ? 'grab' : 'crosshair';
    }
    
    // Zoom functionality
    zoom(delta, point) {
        const oldScale = this.scale;
        this.scale *= delta;
        this.scale = Math.max(this.options.minZoom, Math.min(this.options.maxZoom, this.scale));
        
        // Zoom to point
        if (point) {
            const scaleDiff = this.scale - oldScale;
            this.translateX -= point.x * scaleDiff;
            this.translateY -= point.y * scaleDiff;
        }
        
        this.updateTransform();
        this.dispatchEvent('zoom', { scale: this.scale });
    }
    
    zoomIn() {
        this.zoom(1.2, { x: this.viewportWidth / 2, y: this.viewportHeight / 2 });
    }
    
    zoomOut() {
        this.zoom(0.8, { x: this.viewportWidth / 2, y: this.viewportHeight / 2 });
    }
    
    resetView() {
        this.scale = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.rotation = 0;
        this.updateTransform();
    }
    
    fitView() {
        if (this.objects.length === 0) return;
        
        // Calculate bounding box
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        this.objects.forEach(obj => {
            if (obj.x !== undefined && obj.y !== undefined) {
                minX = Math.min(minX, obj.x);
                minY = Math.min(minY, obj.y);
                maxX = Math.max(maxX, obj.x + (obj.width || 0));
                maxY = Math.max(maxY, obj.y + (obj.height || 0));
            }
        });
        
        const width = maxX - minX;
        const height = maxY - minY;
        
        // Calculate scale to fit
        const scaleX = this.viewportWidth / width;
        const scaleY = this.viewportHeight / height;
        this.scale = Math.min(scaleX, scaleY) * 0.9; // 90% to add padding
        
        // Center the view
        this.translateX = (this.viewportWidth - width * this.scale) / 2 - minX * this.scale;
        this.translateY = (this.viewportHeight - height * this.scale) / 2 - minY * this.scale;
        
        this.updateTransform();
    }
    
    // Transform update
    updateTransform() {
        this.mainGroup.setAttribute('transform', 
            `translate(${this.translateX}, ${this.translateY}) scale(${this.scale}) rotate(${this.rotation})`);
    }
    
    // Selection functionality
    startSelection(point, event) {
        const object = this.getObjectAtPoint(point);
        
        if (object) {
            if (event.shiftKey) {
                // Add to selection
                this.toggleSelection(object);
            } else if (!this.selectedObjects.has(object.id)) {
                // New selection
                this.clearSelection();
                this.selectObject(object);
            }
            
            // Start dragging if object is selected
            if (this.selectedObjects.has(object.id)) {
                this.startDrag(point);
            }
        } else {
            // Start selection box
            if (!event.shiftKey) {
                this.clearSelection();
            }
            this.startSelectionBox(point);
        }
    }
    
    selectObject(object) {
        this.selectedObjects.add(object.id);
        this.highlightObject(object, this.options.selectionColor);
        this.showEditHandles(object);
        this.dispatchEvent('select', { objects: Array.from(this.selectedObjects) });
    }
    
    toggleSelection(object) {
        if (this.selectedObjects.has(object.id)) {
            this.deselectObject(object);
        } else {
            this.selectObject(object);
        }
    }
    
    deselectObject(object) {
        this.selectedObjects.delete(object.id);
        this.unhighlightObject(object);
        this.hideEditHandles(object);
    }
    
    clearSelection() {
        this.selectedObjects.forEach(id => {
            const object = this.objectMap.get(id);
            if (object) {
                this.unhighlightObject(object);
                this.hideEditHandles(object);
            }
        });
        this.selectedObjects.clear();
        this.dispatchEvent('select', { objects: [] });
    }
    
    selectAll() {
        this.objects.forEach(obj => this.selectObject(obj));
    }
    
    // Object manipulation
    startDrag(point) {
        this.isDragging = true;
        this.dragStart = point;
        
        // Store original positions
        this.originalPositions.clear();
        this.selectedObjects.forEach(id => {
            const object = this.objectMap.get(id);
            if (object) {
                this.originalPositions.set(id, {
                    x: object.x || 0,
                    y: object.y || 0
                });
            }
        });
    }
    
    drag(point) {
        if (!this.isDragging) return;
        
        const dx = point.x - this.dragStart.x;
        const dy = point.y - this.dragStart.y;
        
        // Snap to grid if enabled
        let snappedDx = dx;
        let snappedDy = dy;
        
        if (this.options.snapToGrid) {
            snappedDx = Math.round(dx / this.options.gridSize) * this.options.gridSize;
            snappedDy = Math.round(dy / this.options.gridSize) * this.options.gridSize;
        }
        
        // Update positions
        this.selectedObjects.forEach(id => {
            const object = this.objectMap.get(id);
            const original = this.originalPositions.get(id);
            
            if (object && original) {
                object.x = original.x + snappedDx;
                object.y = original.y + snappedDy;
                
                // Update visual representation
                const element = document.getElementById(`obj-${id}`);
                if (element) {
                    this.updateObjectElement(element, object);
                }
            }
        });
        
        this.dispatchEvent('drag', { objects: Array.from(this.selectedObjects), dx: snappedDx, dy: snappedDy });
    }
    
    endDrag() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        
        // Commit changes
        const changes = [];
        this.selectedObjects.forEach(id => {
            const object = this.objectMap.get(id);
            const original = this.originalPositions.get(id);
            
            if (object && original) {
                if (object.x !== original.x || object.y !== original.y) {
                    changes.push({
                        id: id,
                        oldPosition: original,
                        newPosition: { x: object.x, y: object.y }
                    });
                }
            }
        });
        
        if (changes.length > 0) {
            this.commitChanges('move', changes);
        }
    }
    
    // Render objects
    renderObjects(arxObjects) {
        this.clear();
        this.objects = arxObjects;
        
        // Build object map
        this.objectMap.clear();
        arxObjects.forEach(obj => {
            this.objectMap.set(obj.id, obj);
        });
        
        // Group by type for layered rendering
        const grouped = this.groupObjectsByType(arxObjects);
        
        // Render in order
        this.renderRooms(grouped.rooms);
        this.renderWalls(grouped.walls);
        this.renderDoors(grouped.doors);
        this.renderWindows(grouped.windows);
        this.renderOthers(grouped.others);
        
        // Build relationships
        this.buildRelationships(arxObjects);
        
        // Fit view
        this.fitView();
        
        this.dispatchEvent('render', { objects: arxObjects });
    }
    
    groupObjectsByType(objects) {
        return {
            rooms: objects.filter(o => o.type === 'room'),
            walls: objects.filter(o => o.type === 'wall'),
            doors: objects.filter(o => o.type === 'door'),
            windows: objects.filter(o => o.type === 'window'),
            others: objects.filter(o => !['room', 'wall', 'door', 'window'].includes(o.type))
        };
    }
    
    renderWalls(walls) {
        walls.forEach(wall => {
            const element = this.createWallElement(wall);
            this.objectLayer.appendChild(element);
        });
    }
    
    renderRooms(rooms) {
        rooms.forEach(room => {
            const element = this.createRoomElement(room);
            this.objectLayer.appendChild(element);
        });
    }
    
    renderDoors(doors) {
        doors.forEach(door => {
            const element = this.createDoorElement(door);
            this.objectLayer.appendChild(element);
        });
    }
    
    renderWindows(windows) {
        windows.forEach(window => {
            const element = this.createWindowElement(window);
            this.objectLayer.appendChild(element);
        });
    }
    
    renderOthers(others) {
        others.forEach(obj => {
            const element = this.createGenericElement(obj);
            this.objectLayer.appendChild(element);
        });
    }
    
    createWallElement(wall) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('id', `obj-${wall.id}`);
        rect.setAttribute('x', wall.x || 0);
        rect.setAttribute('y', wall.y || 0);
        rect.setAttribute('width', wall.width || 100);
        rect.setAttribute('height', wall.height || 10);
        rect.setAttribute('fill', '#333333');
        rect.setAttribute('stroke', '#000000');
        rect.setAttribute('stroke-width', '1');
        rect.setAttribute('data-type', 'wall');
        rect.setAttribute('data-id', wall.id);
        
        // Add interactivity
        this.makeInteractive(rect, wall);
        
        return rect;
    }
    
    createRoomElement(room) {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('id', `obj-${room.id}`);
        rect.setAttribute('x', room.x || 0);
        rect.setAttribute('y', room.y || 0);
        rect.setAttribute('width', room.width || 200);
        rect.setAttribute('height', room.height || 200);
        rect.setAttribute('fill', '#f0f0f0');
        rect.setAttribute('fill-opacity', '0.3');
        rect.setAttribute('stroke', '#999999');
        rect.setAttribute('stroke-width', '1');
        rect.setAttribute('stroke-dasharray', '5,5');
        rect.setAttribute('data-type', 'room');
        rect.setAttribute('data-id', room.id);
        
        // Add label if available
        if (room.label) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', room.x + room.width / 2);
            text.setAttribute('y', room.y + room.height / 2);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'middle');
            text.setAttribute('font-size', '14');
            text.setAttribute('fill', '#666666');
            text.textContent = room.label;
            
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.appendChild(rect);
            group.appendChild(text);
            
            this.makeInteractive(group, room);
            return group;
        }
        
        this.makeInteractive(rect, room);
        return rect;
    }
    
    createDoorElement(door) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('id', `obj-${door.id}`);
        group.setAttribute('data-type', 'door');
        group.setAttribute('data-id', door.id);
        
        // Door opening
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', door.x || 0);
        rect.setAttribute('y', door.y || 0);
        rect.setAttribute('width', door.width || 80);
        rect.setAttribute('height', door.height || 10);
        rect.setAttribute('fill', 'white');
        rect.setAttribute('stroke', '#8b6914');
        rect.setAttribute('stroke-width', '2');
        
        // Door swing arc
        const arc = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const cx = door.x;
        const cy = door.y;
        const r = door.width || 80;
        arc.setAttribute('d', `M ${cx} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy + r}`);
        arc.setAttribute('stroke', '#8b6914');
        arc.setAttribute('stroke-width', '1');
        arc.setAttribute('fill', 'none');
        arc.setAttribute('stroke-dasharray', '3,3');
        
        group.appendChild(rect);
        group.appendChild(arc);
        
        this.makeInteractive(group, door);
        return group;
    }
    
    createWindowElement(window) {
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('id', `obj-${window.id}`);
        group.setAttribute('data-type', 'window');
        group.setAttribute('data-id', window.id);
        
        // Window frame
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', window.x || 0);
        rect.setAttribute('y', window.y || 0);
        rect.setAttribute('width', window.width || 60);
        rect.setAttribute('height', window.height || 5);
        rect.setAttribute('fill', 'none');
        rect.setAttribute('stroke', '#6b9bd2');
        rect.setAttribute('stroke-width', '2');
        
        // Glass lines
        const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line1.setAttribute('x1', window.x + 2);
        line1.setAttribute('y1', window.y);
        line1.setAttribute('x2', window.x + 2);
        line1.setAttribute('y2', window.y + window.height);
        line1.setAttribute('stroke', '#6b9bd2');
        line1.setAttribute('stroke-width', '1');
        
        const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line2.setAttribute('x1', window.x + window.width - 2);
        line2.setAttribute('y1', window.y);
        line2.setAttribute('x2', window.x + window.width - 2);
        line2.setAttribute('y2', window.y + window.height);
        line2.setAttribute('stroke', '#6b9bd2');
        line2.setAttribute('stroke-width', '1');
        
        group.appendChild(rect);
        group.appendChild(line1);
        group.appendChild(line2);
        
        this.makeInteractive(group, window);
        return group;
    }
    
    createGenericElement(obj) {
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('id', `obj-${obj.id}`);
        circle.setAttribute('cx', obj.x || 0);
        circle.setAttribute('cy', obj.y || 0);
        circle.setAttribute('r', 5);
        circle.setAttribute('fill', '#666666');
        circle.setAttribute('data-type', obj.type);
        circle.setAttribute('data-id', obj.id);
        
        this.makeInteractive(circle, obj);
        return circle;
    }
    
    makeInteractive(element, object) {
        element.style.cursor = 'pointer';
        
        element.addEventListener('mouseenter', () => {
            if (!this.selectedObjects.has(object.id)) {
                this.highlightObject(object, this.options.hoverColor, 0.5);
            }
        });
        
        element.addEventListener('mouseleave', () => {
            if (!this.selectedObjects.has(object.id)) {
                this.unhighlightObject(object);
            }
        });
        
        element.addEventListener('click', (e) => {
            e.stopPropagation();
            if (this.mode === 'select' || this.mode === 'edit') {
                if (e.shiftKey) {
                    this.toggleSelection(object);
                } else {
                    this.clearSelection();
                    this.selectObject(object);
                }
            }
        });
    }
    
    highlightObject(object, color, opacity = 1) {
        const element = document.getElementById(`obj-${object.id}`);
        if (element) {
            element.style.filter = 'drop-shadow(0 0 5px ' + color + ')';
            element.style.opacity = opacity;
        }
    }
    
    unhighlightObject(object) {
        const element = document.getElementById(`obj-${object.id}`);
        if (element) {
            element.style.filter = '';
            element.style.opacity = 1;
        }
    }
    
    // Edit handles
    showEditHandles(object) {
        if (this.mode !== 'edit') return;
        
        const element = document.getElementById(`obj-${object.id}`);
        if (!element) return;
        
        // Create resize handles
        const handles = [
            { position: 'nw', cursor: 'nw-resize' },
            { position: 'n', cursor: 'n-resize' },
            { position: 'ne', cursor: 'ne-resize' },
            { position: 'e', cursor: 'e-resize' },
            { position: 'se', cursor: 'se-resize' },
            { position: 's', cursor: 's-resize' },
            { position: 'sw', cursor: 'sw-resize' },
            { position: 'w', cursor: 'w-resize' }
        ];
        
        handles.forEach(handle => {
            const handleElement = this.createHandle(object, handle);
            this.handleLayer.appendChild(handleElement);
            this.editHandles.push(handleElement);
        });
    }
    
    createHandle(object, handleInfo) {
        const handle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        const size = this.options.editHandleSize;
        
        // Calculate position based on object bounds and handle position
        let x = object.x || 0;
        let y = object.y || 0;
        const w = object.width || 100;
        const h = object.height || 100;
        
        switch(handleInfo.position) {
            case 'nw': break;
            case 'n': x += w/2; break;
            case 'ne': x += w; break;
            case 'e': x += w; y += h/2; break;
            case 'se': x += w; y += h; break;
            case 's': x += w/2; y += h; break;
            case 'sw': y += h; break;
            case 'w': y += h/2; break;
        }
        
        handle.setAttribute('x', x - size/2);
        handle.setAttribute('y', y - size/2);
        handle.setAttribute('width', size);
        handle.setAttribute('height', size);
        handle.setAttribute('fill', this.options.selectionColor);
        handle.setAttribute('stroke', 'white');
        handle.setAttribute('stroke-width', '1');
        handle.style.cursor = handleInfo.cursor;
        
        handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            this.startResize(object, handleInfo.position, this.getMousePosition(e));
        });
        
        return handle;
    }
    
    hideEditHandles(object) {
        this.editHandles.forEach(handle => handle.remove());
        this.editHandles = [];
    }
    
    // Helper methods
    createGroup(id) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('id', id);
        return g;
    }
    
    clear() {
        this.objectLayer.innerHTML = '';
        this.selectionLayer.innerHTML = '';
        this.annotationLayer.innerHTML = '';
        this.handleLayer.innerHTML = '';
        this.objects = [];
        this.objectMap.clear();
        this.selectedObjects.clear();
    }
    
    getObjectAtPoint(point) {
        // Find object at point (simplified - uses bounding box)
        for (const obj of this.objects) {
            if (obj.x <= point.x && point.x <= obj.x + obj.width &&
                obj.y <= point.y && point.y <= obj.y + obj.height) {
                return obj;
            }
        }
        return null;
    }
    
    // Event system
    dispatchEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        this.svg.dispatchEvent(event);
    }
    
    // Additional features
    toggleGrid() {
        this.options.gridVisible = !this.options.gridVisible;
        this.gridLayer.style.display = this.options.gridVisible ? 'block' : 'none';
    }
    
    createUI() {
        // Mode buttons could be added here
        // This would create floating UI controls
    }
    
    buildRelationships(objects) {
        // Build relationship map from objects
        this.relationships.clear();
        objects.forEach(obj => {
            if (obj.relationships) {
                this.relationships.set(obj.id, obj.relationships);
            }
        });
    }
    
    updateObjectElement(element, object) {
        // Update SVG element attributes based on object properties
        if (element.tagName === 'rect') {
            element.setAttribute('x', object.x);
            element.setAttribute('y', object.y);
            element.setAttribute('width', object.width);
            element.setAttribute('height', object.height);
        } else if (element.tagName === 'circle') {
            element.setAttribute('cx', object.x);
            element.setAttribute('cy', object.y);
        }
    }
    
    commitChanges(type, changes) {
        // Store changes for undo/redo
        this.dispatchEvent('change', { type, changes });
    }
    
    clearMeasurement() {
        this.measurePoints = [];
        // Clear measurement visualizations
    }
    
    addMeasurePoint(point) {
        this.measurePoints.push(point);
        // Add measurement visualization
    }
}