/**
 * Drag Module
 * Handles drag and drop functionality for SVG objects
 */

export class Drag {
    constructor(viewportManager, selection, options = {}) {
        this.viewportManager = viewportManager;
        this.selection = selection;
        
        // Drag state
        this.isDragging = false;
        this.currentDragTarget = null;
        this.dragStartPosition = null;
        this.dragOffset = { x: 0, y: 0 };
        
        // Performance optimizations
        this.dragThrottleTimer = null;
        this.dragThrottleDelay = options.dragThrottleDelay || 16; // ~60fps
        
        // Drag constraints
        this.dragEnabled = options.dragEnabled !== false;
        this.dragBoundaries = options.dragBoundaries || {
            enabled: true,
            padding: 50
        };
        
        // Object pool for performance
        this.objectPool = new Map();
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.setupInteractJS();
    }

    setupEventListeners() {
        if (!this.viewportManager || !this.viewportManager.svg) return;
        
        const svg = this.viewportManager.svg;
        
        // Mouse events for drag
        svg.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        svg.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        svg.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Keyboard events for drag
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    setupInteractJS() {
        // Use InteractJS for enhanced drag functionality if available
        if (typeof interact !== 'undefined') {
            this.setupInteractJSDrag();
        }
    }

    setupInteractJSDrag() {
        interact('.draggable, .bim-object, .svg-object')
            .draggable({
                inertia: true,
                modifiers: [
                    interact.modifiers.restrictRect({
                        restriction: 'parent',
                        endOnly: true
                    })
                ],
                autoScroll: true,
                listeners: {
                    start: (event) => this.handleInteractDragStart(event),
                    move: (event) => this.handleInteractDragMove(event),
                    end: (event) => this.handleInteractDragEnd(event)
                }
            });
    }

    handleMouseDown(event) {
        if (!this.dragEnabled) return;
        
        const target = this.findDraggableObject(event.target);
        if (!target) return;
        
        // Check if target is selected
        if (!this.selection.isObjectSelected(target)) {
            this.selection.selectObject(target);
        }
        
        this.startDrag(event, target);
    }

    handleMouseMove(event) {
        if (!this.isDragging) return;
        
        event.preventDefault();
        this.updateDrag(event);
    }

    handleMouseUp(event) {
        if (!this.isDragging) return;
        
        this.endDrag(event);
    }

    handleKeyDown(event) {
        if (!this.isDragging) return;
        
        switch (event.key) {
            case 'Escape':
                this.cancelDrag();
                break;
            case 'Shift':
                // Enable constrained dragging
                this.enableConstrainedDrag();
                break;
        }
    }

    // InteractJS event handlers
    handleInteractDragStart(event) {
        const target = event.target;
        this.startDrag(event, target);
    }

    handleInteractDragMove(event) {
        if (!this.isDragging) return;
        
        const deltaX = event.delta.x;
        const deltaY = event.delta.y;
        
        this.moveSelectedObjects(deltaX, deltaY);
    }

    handleInteractDragEnd(event) {
        this.endDrag(event);
    }

    // Drag control methods
    startDrag(event, target) {
        this.isDragging = true;
        this.currentDragTarget = target;
        
        const mousePos = this.getMousePosition(event);
        const targetPos = this.getObjectPosition(target);
        
        this.dragStartPosition = mousePos;
        this.dragOffset = {
            x: mousePos.x - targetPos.x,
            y: mousePos.y - targetPos.y
        };
        
        // Save state before drag
        this.saveStateBeforeDrag();
        
        // Add drag visual feedback
        this.addDragVisualFeedback();
        
        this.triggerEvent('dragStarted', { target, position: mousePos });
    }

    updateDrag(event) {
        if (!this.isDragging || !this.currentDragTarget) return;
        
        // Throttle drag updates for performance
        if (this.dragThrottleTimer) return;
        
        this.dragThrottleTimer = setTimeout(() => {
            this.dragThrottleTimer = null;
        }, this.dragThrottleDelay);
        
        const mousePos = this.getMousePosition(event);
        const deltaX = mousePos.x - this.dragStartPosition.x;
        const deltaY = mousePos.y - this.dragStartPosition.y;
        
        this.moveSelectedObjects(deltaX, deltaY);
        
        this.triggerEvent('dragUpdated', { 
            target: this.currentDragTarget, 
            position: mousePos,
            delta: { x: deltaX, y: deltaY }
        });
    }

    endDrag(event) {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        
        // Save state after drag
        this.saveStateAfterDrag();
        
        // Remove drag visual feedback
        this.removeDragVisualFeedback();
        
        // Update object positions in backend
        this.saveObjectPositions();
        
        this.triggerEvent('dragEnded', { 
            target: this.currentDragTarget,
            finalPosition: this.getObjectPosition(this.currentDragTarget)
        });
        
        this.currentDragTarget = null;
        this.dragStartPosition = null;
    }

    cancelDrag() {
        if (!this.isDragging) return;
        
        // Restore original positions
        this.restoreObjectPositions();
        
        this.isDragging = false;
        this.removeDragVisualFeedback();
        
        this.triggerEvent('dragCancelled');
        
        this.currentDragTarget = null;
        this.dragStartPosition = null;
    }

    // Object movement methods
    moveSelectedObjects(deltaX, deltaY) {
        const selectedObjects = this.selection.getSelectedObjects();
        
        selectedObjects.forEach(obj => {
            this.moveObject(obj, deltaX, deltaY);
        });
    }

    moveObject(obj, deltaX, deltaY) {
        if (!obj) return;
        
        const currentPos = this.getObjectPosition(obj);
        const newPos = {
            x: currentPos.x + deltaX,
            y: currentPos.y + deltaY
        };
        
        // Apply constraints
        const constrainedPos = this.applyDragConstraints(newPos, obj);
        
        // Update object position
        this.setObjectPosition(obj, constrainedPos);
        
        // Update drag start position for next frame
        this.dragStartPosition = {
            x: this.dragStartPosition.x + deltaX,
            y: this.dragStartPosition.y + deltaY
        };
    }

    // Utility methods
    findDraggableObject(target) {
        if (!target) return null;
        
        // Walk up the DOM tree to find the closest draggable object
        let element = target;
        while (element && element !== this.viewportManager.svg) {
            if (this.isDraggableObject(element)) {
                return element;
            }
            element = element.parentElement;
        }
        
        return null;
    }

    isDraggableObject(element) {
        return element && (
            element.classList.contains('draggable') ||
            element.classList.contains('bim-object') ||
            element.classList.contains('svg-object') ||
            element.hasAttribute('data-draggable')
        );
    }

    getMousePosition(event) {
        const rect = this.viewportManager.svg.getBoundingClientRect();
        return {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
        };
    }

    getObjectPosition(obj) {
        const transform = obj.getAttribute('transform');
        if (transform) {
            // Parse transform matrix
            const matrix = transform.match(/translate\(([^,]+),([^)]+)\)/);
            if (matrix) {
                return {
                    x: parseFloat(matrix[1]),
                    y: parseFloat(matrix[2])
                };
            }
        }
        
        return {
            x: parseFloat(obj.getAttribute('x') || '0'),
            y: parseFloat(obj.getAttribute('y') || '0')
        };
    }

    setObjectPosition(obj, position) {
        // Update transform attribute
        const transform = `translate(${position.x}, ${position.y})`;
        obj.setAttribute('transform', transform);
        
        // Update data attributes for persistence
        obj.setAttribute('data-x', position.x.toString());
        obj.setAttribute('data-y', position.y.toString());
    }

    applyDragConstraints(position, obj) {
        if (!this.dragBoundaries.enabled) {
            return position;
        }
        
        const svgBounds = this.viewportManager.svg.getBoundingClientRect();
        const objBounds = obj.getBoundingClientRect();
        const padding = this.dragBoundaries.padding;
        
        const constrainedX = Math.max(
            -objBounds.width + padding,
            Math.min(svgBounds.width - padding, position.x)
        );
        
        const constrainedY = Math.max(
            -objBounds.height + padding,
            Math.min(svgBounds.height - padding, position.y)
        );
        
        return {
            x: constrainedX,
            y: constrainedY
        };
    }

    // State management
    saveStateBeforeDrag() {
        const selectedObjects = this.selection.getSelectedObjects();
        this.dragStartStates = new Map();
        
        selectedObjects.forEach(obj => {
            this.dragStartStates.set(obj, this.getObjectPosition(obj));
        });
    }

    saveStateAfterDrag() {
        // State is automatically saved by the drag operation
        this.dragStartStates = null;
    }

    restoreObjectPositions() {
        if (!this.dragStartStates) return;
        
        this.dragStartStates.forEach((position, obj) => {
            this.setObjectPosition(obj, position);
        });
    }

    // Visual feedback
    addDragVisualFeedback() {
        const selectedObjects = this.selection.getSelectedObjects();
        
        selectedObjects.forEach(obj => {
            obj.classList.add('dragging');
            obj.style.cursor = 'grabbing';
        });
    }

    removeDragVisualFeedback() {
        const selectedObjects = this.selection.getSelectedObjects();
        
        selectedObjects.forEach(obj => {
            obj.classList.remove('dragging');
            obj.style.cursor = 'grab';
        });
    }

    // Object pool for performance
    getObjectFromPool(type) {
        if (!this.objectPool.has(type)) {
            this.objectPool.set(type, []);
        }
        
        const pool = this.objectPool.get(type);
        return pool.length > 0 ? pool.pop() : null;
    }

    returnObjectToPool(object, type) {
        if (!this.objectPool.has(type)) {
            this.objectPool.set(type, []);
        }
        
        this.objectPool.get(type).push(object);
    }

    // Backend integration
    async saveObjectPositions() {
        const selectedObjects = this.selection.getSelectedObjects();
        
        if (selectedObjects.length === 0) return;
        
        const positions = selectedObjects.map(obj => ({
            id: obj.id,
            position: this.getObjectPosition(obj),
            type: obj.getAttribute('data-type')
        }));
        
        try {
            // Send to backend
            const response = await fetch('/api/objects/positions', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ positions })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save object positions');
            }
            
            this.triggerEvent('positionsSaved', { positions });
        } catch (error) {
            console.error('Error saving object positions:', error);
            this.triggerEvent('positionSaveError', { error });
        }
    }

    // Drag controls
    enableDrag() {
        this.dragEnabled = true;
    }

    disableDrag() {
        this.dragEnabled = false;
        if (this.isDragging) {
            this.cancelDrag();
        }
    }

    toggleDrag() {
        this.dragEnabled = !this.dragEnabled;
    }

    isDragEnabled() {
        return this.dragEnabled;
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, drag: this });
                } catch (error) {
                    console.error(`Error in drag event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        if (this.isDragging) {
            this.cancelDrag();
        }
        
        this.objectPool.clear();
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 