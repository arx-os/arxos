// Object Interaction Module with Performance Optimizations

class SVGObjectInteraction {
    constructor() {
        this.selectedObjects = new Set();
        this.isDragging = false;
        this.currentDragTarget = null;
        this.rotateHandle = null;
        this.undoStack = [];
        this.redoStack = [];
        this.maxUndoSteps = 50;
        
        // Performance optimizations
        this.objectPool = new Map();
        this.dragThrottleTimer = null;
        this.dragThrottleDelay = 16; // ~60fps
        this.selectionCache = new Map();
        this.autoSaveTimer = null;
        this.autoSaveDelay = 2000; // 2 seconds
        
        // UX improvements
        this.loadingStates = new Set();
        this.notifications = [];
        this.helpOverlay = null;
        
        // Marquee selection
        this.isMarqueeSelecting = false;
        this.marqueeStart = null;
        this.marqueeElement = null;
        this.autoSaveIndicator = null;
        
        // Viewport manager integration
        this.viewportManager = null;
        
        this.init();
    }

    init() {
        this.svgContainer = document.getElementById('svg-container');
        this.svgElement = this.svgContainer ? this.svgContainer.querySelector('svg') : null;
        if (!this.svgContainer || !this.svgElement) return;
        
        this.connectToViewportManager();
        this.setupEventListeners();
        this.setupInteractJS();
        this.createHelpOverlay();
        this.setupAutoSave();
        this.createAutoSaveIndicator();
    }

    /**
     * Connect to the viewport manager for coordinate conversion
     */
    connectToViewportManager() {
        // Wait for viewport manager to be available
        const checkViewportManager = () => {
            if (window.viewportManager) {
                this.viewportManager = window.viewportManager;
                window.arxLogger.info('SVGObjectInteraction connected to ViewportManager', { file: 'object_interaction.js' });
                
                // Listen for viewport changes
                this.viewportManager.addEventListener('zoomChanged', () => {
                    this.updateRotateHandlePosition();
                });
                
                this.viewportManager.addEventListener('viewReset', () => {
                    this.updateRotateHandlePosition();
                });
            } else {
                // Retry after a short delay
                setTimeout(checkViewportManager, 100);
            }
        };
        checkViewportManager();
    }

    setupEventListeners() {
        // Click to select with optimized detection
        this.svgElement.addEventListener('mousedown', (e) => {
            const target = this.findClosestObject(e.target);
            if (!target) {
                this.clearSelection();
                this.removeRotateHandle();
                return;
            }
            if (e.shiftKey) {
                this.toggleObjectSelection(target);
            } else {
                this.selectObject(target);
            }
            this.showRotateHandle(target);
        });

        // Marquee selection
        this.svgElement.addEventListener('mousedown', (e) => {
            if (e.target === this.svgElement || e.target.classList.contains('svg-background')) {
                this.startMarqueeSelection(e);
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (this.isMarqueeSelecting) {
                this.updateMarqueeSelection(e);
            }
        });

        document.addEventListener('mouseup', (e) => {
            if (this.isMarqueeSelecting) {
                this.endMarqueeSelection(e);
            }
        });

        // Keyboard shortcuts with help overlay
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' || e.key === 'Backspace') {
                this.deleteSelectedObjects();
            } else if (e.key.toLowerCase() === 'r') {
                this.rotateSelectedObjects(15);
            } else if (e.key === 'Escape') {
                this.cancelOperations();
            } else if (e.ctrlKey || e.metaKey) {
                if (e.key.toLowerCase() === 'z') {
                    e.preventDefault();
                    this.undo();
                } else if (e.key.toLowerCase() === 'y') {
                    e.preventDefault();
                    this.redo();
                } else if (e.key === '?') {
                    e.preventDefault();
                    this.toggleHelpOverlay();
                } else if (e.key.toLowerCase() === 'a') {
                    e.preventDefault();
                    this.selectAllObjects();
                } else if (e.key.toLowerCase() === 'd') {
                    e.preventDefault();
                    this.clearSelection();
                }
            } else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
                this.moveSelectedObjectsWithArrowKeys(e.key);
            }
        });

        // Performance: Throttle scroll and resize events
        let scrollTimer, resizeTimer;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(() => this.updateSelectionCache(), 100);
        });
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => this.updateSelectionCache(), 100);
        });
    }

    // Marquee selection methods
    getMousePosition(e) {
        const rect = this.svgContainer.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    getObjectsInRect(rect) {
        const objects = [];
        const placedSymbols = this.svgElement.querySelectorAll('.placed-symbol');
        
        placedSymbols.forEach(symbol => {
            const symbolRect = symbol.getBoundingClientRect();
            if (this.rectsIntersect(rect, symbolRect)) {
                objects.push(symbol);
            }
        });
        
        return objects;
    }

    /**
     * Get objects in marquee selection with proper coordinate conversion
     */
    getObjectsInMarqueeSelection() {
        if (!this.marqueeElement) return [];
        
        const marqueeRect = this.marqueeElement.getBoundingClientRect();
        const objects = [];
        const placedSymbols = this.svgElement.querySelectorAll('.placed-symbol');
        
        placedSymbols.forEach(symbol => {
            const symbolRect = symbol.getBoundingClientRect();
            if (this.rectsIntersect(marqueeRect, symbolRect)) {
                objects.push(symbol);
            }
        });
        
        return objects;
    }

    /**
     * Enhanced marquee selection with zoom awareness
     */
    startMarqueeSelection(e) {
        this.isMarqueeSelecting = true;
        this.marqueeStart = this.getMousePosition(e);
        
        this.marqueeElement = document.createElement('div');
        this.marqueeElement.className = 'marquee-selection';
        this.marqueeElement.style.left = this.marqueeStart.x + 'px';
        this.marqueeElement.style.top = this.marqueeStart.y + 'px';
        this.marqueeElement.style.width = '0px';
        this.marqueeElement.style.height = '0px';
        
        this.svgContainer.appendChild(this.marqueeElement);
    }

    updateMarqueeSelection(e) {
        if (!this.isMarqueeSelecting || !this.marqueeElement) return;
        
        const currentPos = this.getMousePosition(e);
        const startX = Math.min(this.marqueeStart.x, currentPos.x);
        const startY = Math.min(this.marqueeStart.y, currentPos.y);
        const width = Math.abs(currentPos.x - this.marqueeStart.x);
        const height = Math.abs(currentPos.y - this.marqueeStart.y);
        
        this.marqueeElement.style.left = startX + 'px';
        this.marqueeElement.style.top = startY + 'px';
        this.marqueeElement.style.width = width + 'px';
        this.marqueeElement.style.height = height + 'px';
    }

    endMarqueeSelection(e) {
        if (!this.isMarqueeSelecting) return;
        
        this.isMarqueeSelecting = false;
        
        if (this.marqueeElement) {
            const selectedObjects = this.getObjectsInMarqueeSelection();
            
            if (e.shiftKey) {
                selectedObjects.forEach(obj => this.toggleObjectSelection(obj));
            } else {
                this.clearSelection();
                selectedObjects.forEach(obj => this.selectObject(obj));
            }
            
            this.marqueeElement.remove();
            this.marqueeElement = null;
        }
        
        this.marqueeStart = null;
    }

    rectsIntersect(rect1, rect2) {
        return !(rect2.left > rect1.right || 
                rect2.right < rect1.left || 
                rect2.top > rect1.bottom ||
                rect2.bottom < rect1.top);
    }

    selectAllObjects() {
        const allObjects = this.svgElement.querySelectorAll('.placed-symbol');
        allObjects.forEach(obj => {
            this.selectedObjects.add(obj);
            obj.classList.add('selected');
        });
        this.updateContextPanel();
        this.showNotification(`${allObjects.length} objects selected`, 'info');
    }

    setupInteractJS() {
        if (typeof interact === 'undefined') return;
        
        interact('.placed-symbol', { context: this.svgElement })
            .draggable({
                listeners: {
                    start: (event) => {
                        this.setLoadingState(event.target, true);
                        this.saveStateBeforeDrag();
                        this.currentDragTarget = event.target;
                    },
                    move: (event) => {
                        // Enhanced throttling with requestAnimationFrame
                        if (this.dragThrottleTimer) return;
                        
                        this.dragThrottleTimer = requestAnimationFrame(() => {
                            this.handleDragMove(event);
                            this.dragThrottleTimer = null;
                        });
                    },
                    end: () => {
                        this.setLoadingState(this.currentDragTarget, false);
                        this.saveStateAfterDrag();
                        this.triggerAutoSave();
                        this.currentDragTarget = null;
                    }
                }
            });
    }

    handleDragMove(event) {
        const target = event.target;
        
        // Get current position in SVG coordinates
        let currentX = parseFloat(target.getAttribute('data-x')) || 0;
        let currentY = parseFloat(target.getAttribute('data-y')) || 0;
        
        // Convert drag delta to SVG coordinates if viewport manager is available
        let deltaX = event.dx;
        let deltaY = event.dy;
        
        if (this.viewportManager && this.viewportManager.currentZoom) {
            // Convert screen delta to SVG delta based on current zoom
            deltaX = deltaX / this.viewportManager.currentZoom;
            deltaY = deltaY / this.viewportManager.currentZoom;
        }
        
        let newX = currentX + deltaX;
        let newY = currentY + deltaY;
        
        // Snap to grid (optional)
        const gridSize = 5;
        newX = Math.round(newX / gridSize) * gridSize;
        newY = Math.round(newY / gridSize) * gridSize;
        
        // Update object position
        target.setAttribute('data-x', newX);
        target.setAttribute('data-y', newY);
        const rotation = target.getAttribute('data-rotation') || 0;
        target.setAttribute('transform', `translate(${newX},${newY}) rotate(${rotation})`);
        
        // Move selected objects together
        if (this.selectedObjects.has(target)) {
            this.selectedObjects.forEach(obj => {
                if (obj !== target) {
                    let objX = parseFloat(obj.getAttribute('data-x')) || 0;
                    let objY = parseFloat(obj.getAttribute('data-y')) || 0;
                    
                    // Apply same delta to other selected objects
                    let objNewX = objX + deltaX;
                    let objNewY = objY + deltaY;
                    
                    // Snap to grid
                    objNewX = Math.round(objNewX / gridSize) * gridSize;
                    objNewY = Math.round(objNewY / gridSize) * gridSize;
                    
                    obj.setAttribute('data-x', objNewX);
                    obj.setAttribute('data-y', objNewY);
                    const objRotation = obj.getAttribute('data-rotation') || 0;
                    obj.setAttribute('transform', `translate(${objNewX},${objNewY}) rotate(${objRotation})`);
                }
            });
        }
        
        // Update rotate handle position if visible
        this.updateRotateHandlePosition();
        
        // Trigger viewport manager event
        if (this.viewportManager) {
            this.viewportManager.triggerEvent('objectMoved', {
                objectId: target.getAttribute('data-id'),
                x: newX,
                y: newY,
                element: target
            });
        }
    }

    // Optimized object detection using spatial indexing
    findClosestObject(target) {
        if (target.classList.contains('placed-symbol')) {
            return target;
        }
        
        // Use cached selection for better performance
        const cacheKey = `${target.offsetLeft},${target.offsetTop}`;
        if (this.selectionCache.has(cacheKey)) {
            return this.selectionCache.get(cacheKey);
        }
        
        const closest = target.closest('.placed-symbol');
        this.selectionCache.set(cacheKey, closest);
        
        // Limit cache size
        if (this.selectionCache.size > 1000) {
            const firstKey = this.selectionCache.keys().next().value;
            this.selectionCache.delete(firstKey);
        }
        
        return closest;
    }

    updateSelectionCache() {
        this.selectionCache.clear();
    }

    // Object pooling for better memory management
    getObjectFromPool(type) {
        if (this.objectPool.has(type)) {
            const pool = this.objectPool.get(type);
            return pool.length > 0 ? pool.pop() : null;
        }
        return null;
    }

    returnObjectToPool(object, type) {
        if (!this.objectPool.has(type)) {
            this.objectPool.set(type, []);
        }
        this.objectPool.get(type).push(object);
    }

    selectObject(obj) {
        this.clearSelection();
        this.selectedObjects.add(obj);
        obj.classList.add('selected');
        this.showRotateHandle(obj);
        this.updateContextPanel();
        this.showNotification('Object selected', 'info');
    }

    toggleObjectSelection(obj) {
        if (this.selectedObjects.has(obj)) {
            this.selectedObjects.delete(obj);
            obj.classList.remove('selected');
        } else {
            this.selectedObjects.add(obj);
            obj.classList.add('selected');
        }
        this.showRotateHandle(obj);
        this.updateContextPanel();
        this.showNotification(`${this.selectedObjects.size} objects selected`, 'info');
    }

    clearSelection() {
        this.selectedObjects.forEach(obj => obj.classList.remove('selected'));
        this.selectedObjects.clear();
        this.removeRotateHandle();
        this.updateContextPanel();
    }

    rotateSelectedObjects(angle) {
        this.saveStateBeforeOperation('rotate');
        this.setLoadingState(Array.from(this.selectedObjects), true);
        
        this.selectedObjects.forEach(obj => {
            let rotation = parseFloat(obj.getAttribute('data-rotation') || 0) + angle;
            obj.setAttribute('data-rotation', rotation);
            let x = obj.getAttribute('data-x') || 0;
            let y = obj.getAttribute('data-y') || 0;
            obj.setAttribute('transform', `translate(${x},${y}) rotate(${rotation})`);
        });
        
        this.setLoadingState(Array.from(this.selectedObjects), false);
        this.saveStateAfterOperation();
        this.triggerAutoSave();
        this.showNotification('Objects rotated', 'success');
    }

    moveSelectedObjectsWithArrowKeys(key) {
        // Adjust step size based on zoom level
        let step = 1;
        if (this.viewportManager && this.viewportManager.currentZoom) {
            // Smaller steps at higher zoom levels for finer control
            step = Math.max(0.5, 1 / this.viewportManager.currentZoom);
        }
        
        let deltaX = 0, deltaY = 0;
        
        switch (key) {
            case 'ArrowUp': deltaY = -step; break;
            case 'ArrowDown': deltaY = step; break;
            case 'ArrowLeft': deltaX = -step; break;
            case 'ArrowRight': deltaX = step; break;
        }
        
        if (deltaX !== 0 || deltaY !== 0) {
            this.saveStateBeforeOperation('move');
            this.selectedObjects.forEach(obj => {
                const currentX = parseFloat(obj.getAttribute('data-x') || 0);
                const currentY = parseFloat(obj.getAttribute('data-y') || 0);
                const newX = currentX + deltaX;
                const newY = currentY + deltaY;
                
                obj.setAttribute('data-x', newX);
                obj.setAttribute('data-y', newY);
                
                const rotation = obj.getAttribute('data-rotation') || 0;
                obj.setAttribute('transform', `translate(${newX},${newY}) rotate(${rotation})`);
                
                // Trigger viewport manager event
                if (this.viewportManager) {
                    this.viewportManager.triggerEvent('objectMoved', {
                        objectId: obj.getAttribute('data-id'),
                        x: newX,
                        y: newY,
                        element: obj
                    });
                }
            });
            
            // Update rotate handle position
            this.updateRotateHandlePosition();
            
            this.saveStateAfterOperation();
            this.triggerAutoSave();
        }
    }

    showRotateHandle(obj) {
        this.removeRotateHandle();
        if (!obj) return;
        
        const bbox = obj.getBBox();
        const handle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        
        // Calculate handle position in SVG coordinates
        const handleX = bbox.x + bbox.width + 10;
        const handleY = bbox.y + bbox.height / 2;
        
        handle.setAttribute('cx', handleX);
        handle.setAttribute('cy', handleY);
        handle.setAttribute('r', 8);
        handle.setAttribute('fill', '#3b82f6');
        handle.setAttribute('stroke', '#1e40af');
        handle.setAttribute('stroke-width', 2);
        handle.setAttribute('class', 'rotate-handle');
        handle.style.cursor = 'pointer';
        
        // Store object reference for position updates
        handle.setAttribute('data-target-object', obj.getAttribute('data-id'));
        
        let startAngle = 0, startRotation = 0;
        handle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            this.saveStateBeforeOperation('rotate');
            this.setLoadingState(obj, true);
            
            const svg = this.svgElement;
            const objCenter = {
                x: bbox.x + bbox.width / 2,
                y: bbox.y + bbox.height / 2
            };
            
            const mouseMove = (ev) => {
                // Convert mouse position to SVG coordinates
                let svgP;
                if (this.viewportManager && this.viewportManager.screenToSVG) {
                    svgP = this.viewportManager.screenToSVG(ev.clientX, ev.clientY);
                } else {
                    const pt = svg.createSVGPoint();
                    pt.x = ev.clientX; 
                    pt.y = ev.clientY;
                    svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
                }
                
                const dx = svgP.x - objCenter.x;
                const dy = svgP.y - objCenter.y;
                const angle = Math.atan2(dy, dx) * 180 / Math.PI;
                const rotation = angle;
                
                obj.setAttribute('data-rotation', rotation);
                let x = obj.getAttribute('data-x') || 0;
                let y = obj.getAttribute('data-y') || 0;
                obj.setAttribute('transform', `translate(${x},${y}) rotate(${rotation})`);
                
                // Update rotate handle position
                this.updateRotateHandlePosition();
            };
            
            const mouseUp = () => {
                document.removeEventListener('mousemove', mouseMove);
                document.removeEventListener('mouseup', mouseUp);
                this.setLoadingState(obj, false);
                this.saveStateAfterOperation();
                this.triggerAutoSave();
                this.showNotification('Object rotated', 'success');
            };
            
            document.addEventListener('mousemove', mouseMove);
            document.addEventListener('mouseup', mouseUp);
        });
        
        obj.parentNode.appendChild(handle);
        this.rotateHandle = handle;
    }

    /**
     * Update rotate handle position when viewport changes
     */
    updateRotateHandlePosition() {
        if (!this.rotateHandle) return;
        
        const targetId = this.rotateHandle.getAttribute('data-target-object');
        const target = document.querySelector(`[data-id="${targetId}"]`);
        
        if (!target) {
            this.removeRotateHandle();
            return;
        }
        
        const bbox = target.getBBox();
        const handleX = bbox.x + bbox.width + 10;
        const handleY = bbox.y + bbox.height / 2;
        
        this.rotateHandle.setAttribute('cx', handleX);
        this.rotateHandle.setAttribute('cy', handleY);
    }

    removeRotateHandle() {
        if (this.rotateHandle && this.rotateHandle.parentNode) {
            this.rotateHandle.parentNode.removeChild(this.rotateHandle);
        }
        this.rotateHandle = null;
    }

    deleteSelectedObjects() {
        if (this.selectedObjects.size === 0) return;
        if (!confirm(`Delete ${this.selectedObjects.size} selected object(s)?`)) return;
        
        this.saveStateBeforeOperation('delete');
        this.setLoadingState(Array.from(this.selectedObjects), true);
        
        const deletedObjects = Array.from(this.selectedObjects).map(obj => ({
            element: obj,
            data: this.extractObjectData(obj)
        }));
        
        this.selectedObjects.forEach(obj => {
            obj.remove();
            this.deleteObjectBackend(obj.getAttribute('data-id'));
        });
        
        this.selectedObjects.clear();
        this.removeRotateHandle();
        this.updateContextPanel();
        
        this.setLoadingState(Array.from(this.selectedObjects), false);
        this.currentOperation.deletedObjects = deletedObjects;
        this.saveStateAfterOperation();
        this.showNotification(`${deletedObjects.length} objects deleted`, 'success');
    }

    cancelOperations() {
        this.clearSelection();
        this.removeRotateHandle();
        this.isDragging = false;
        this.currentDragTarget = null;
        this.showNotification('Operation cancelled', 'info');
    }

    // Auto-save functionality
    setupAutoSave() {
        this.autoSaveTimer = null;
    }

    createAutoSaveIndicator() {
        this.autoSaveIndicator = document.createElement('div');
        this.autoSaveIndicator.className = 'auto-save-indicator';
        this.autoSaveIndicator.textContent = 'Auto-saving...';
        document.body.appendChild(this.autoSaveIndicator);
    }

    triggerAutoSave() {
        clearTimeout(this.autoSaveTimer);
        this.autoSaveTimer = setTimeout(() => {
            this.saveObjectPositions();
        }, this.autoSaveDelay);
    }

    // Loading states
    setLoadingState(objects, isLoading) {
        const objectArray = Array.isArray(objects) ? objects : [objects];
        objectArray.forEach(obj => {
            if (isLoading) {
                this.loadingStates.add(obj);
                obj.classList.add('loading');
            } else {
                this.loadingStates.delete(obj);
                obj.classList.remove('loading');
            }
        });
    }

    // Enhanced notifications
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add icon based on type
        const icon = document.createElement('span');
        icon.className = 'mr-2';
        icon.innerHTML = type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ';
        notification.insertBefore(icon, notification.firstChild);
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
        
        this.notifications.push(notification);
    }

    // Help overlay
    createHelpOverlay() {
        this.helpOverlay = document.createElement('div');
        this.helpOverlay.className = 'help-overlay hidden';
        this.helpOverlay.innerHTML = `
            <div class="help-content">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold">Keyboard Shortcuts</h2>
                    <button id="close-help" class="text-gray-400 hover:text-gray-600">✗</button>
                </div>
                <div class="help-grid">
                    <div class="help-section">
                        <h3>Selection</h3>
                        <div class="space-y-1">
                            <div><kbd>Click</kbd> Select object</div>
                            <div><kbd>Shift + Click</kbd> Multi-select</div>
                            <div><kbd>Ctrl + A</kbd> Select all</div>
                            <div><kbd>Ctrl + D</kbd> Deselect all</div>
                            <div><kbd>Escape</kbd> Cancel operation</div>
                        </div>
                    </div>
                    <div class="help-section">
                        <h3>Manipulation</h3>
                        <div class="space-y-1">
                            <div><kbd>Drag</kbd> Move object</div>
                            <div><kbd>R</kbd> Rotate 15°</div>
                            <div><kbd>Arrow Keys</kbd> Fine movement</div>
                            <div><kbd>Delete</kbd> Delete object</div>
                        </div>
                    </div>
                    <div class="help-section">
                        <h3>History</h3>
                        <div class="space-y-1">
                            <div><kbd>Ctrl + Z</kbd> Undo</div>
                            <div><kbd>Ctrl + Y</kbd> Redo</div>
                        </div>
                    </div>
                    <div class="help-section">
                        <h3>Help</h3>
                        <div class="space-y-1">
                            <div><kbd>Ctrl + ?</kbd> Show this help</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.helpOverlay);
        
        // Close button
        this.helpOverlay.querySelector('#close-help').addEventListener('click', () => {
            this.hideHelpOverlay();
        });
        
        // Click outside to close
        this.helpOverlay.addEventListener('click', (e) => {
            if (e.target === this.helpOverlay) {
                this.hideHelpOverlay();
            }
        });
    }

    toggleHelpOverlay() {
        if (this.helpOverlay.classList.contains('hidden')) {
            this.showHelpOverlay();
        } else {
            this.hideHelpOverlay();
        }
    }

    showHelpOverlay() {
        this.helpOverlay.classList.remove('hidden');
    }

    hideHelpOverlay() {
        this.helpOverlay.classList.add('hidden');
    }

    // Rest of the existing methods with performance improvements...
    saveStateBeforeOperation(operationType) {
        this.currentOperation = {
            type: operationType,
            timestamp: Date.now(),
            objects: Array.from(this.selectedObjects).map(obj => ({
                element: obj,
                data: this.extractObjectData(obj)
            }))
        };
    }

    saveStateBeforeDrag() {
        this.saveStateBeforeOperation('drag');
    }

    saveStateAfterOperation() {
        if (this.currentOperation) {
            this.undoStack.push(this.currentOperation);
            this.redoStack = [];
            
            if (this.undoStack.length > this.maxUndoSteps) {
                this.undoStack.shift();
            }
            
            this.currentOperation = null;
        }
    }

    saveStateAfterDrag() {
        this.saveStateAfterOperation();
    }

    undo() {
        if (this.undoStack.length === 0) return;
        
        const operation = this.undoStack.pop();
        this.redoStack.push(operation);
        
        switch (operation.type) {
            case 'move':
            case 'drag':
            case 'rotate':
                this.restoreObjectStates(operation.objects);
                break;
            case 'delete':
                this.restoreDeletedObjects(operation.deletedObjects);
                break;
        }
        
        this.updateContextPanel();
        this.showNotification('Undo completed', 'success');
    }

    redo() {
        if (this.redoStack.length === 0) return;
        
        const operation = this.redoStack.pop();
        this.undoStack.push(operation);
        
        switch (operation.type) {
            case 'move':
            case 'drag':
            case 'rotate':
                this.restoreObjectStates(operation.objects, true);
                break;
            case 'delete':
                this.deleteSelectedObjects();
                break;
        }
        
        this.updateContextPanel();
        this.showNotification('Redo completed', 'success');
    }

    restoreObjectStates(objects, isRedo = false) {
        objects.forEach(({ element, data }) => {
            if (element && element.parentNode) {
                element.setAttribute('data-x', data.x);
                element.setAttribute('data-y', data.y);
                element.setAttribute('data-rotation', data.rotation);
                element.setAttribute('transform', `translate(${data.x},${data.y}) rotate(${data.rotation})`);
            }
        });
    }

    restoreDeletedObjects(deletedObjects) {
        deletedObjects.forEach(({ element, data }) => {
            if (element) {
                this.svgElement.appendChild(element);
                this.selectedObjects.add(element);
                element.classList.add('selected');
            }
        });
    }

    extractObjectData(obj) {
        return {
            id: obj.getAttribute('data-id'),
            x: parseFloat(obj.getAttribute('data-x') || 0),
            y: parseFloat(obj.getAttribute('data-y') || 0),
            rotation: parseFloat(obj.getAttribute('data-rotation') || 0),
            name: obj.getAttribute('data-name'),
            type: obj.getAttribute('data-type'),
            system: obj.getAttribute('data-system'),
            status: obj.getAttribute('data-status')
        };
    }

    async saveObjectPositions() {
        const objects = Array.from(this.selectedObjects).map(obj => {
            const baseData = {
                id: obj.getAttribute('data-id'),
                x: parseFloat(obj.getAttribute('data-x') || 0),
                y: parseFloat(obj.getAttribute('data-y') || 0),
                rotation: parseFloat(obj.getAttribute('data-rotation') || 0)
            };

            // Add scale metadata if available
            if (window.scaleManager && window.scaleManager.scaleFactors.x !== 1.0) {
                baseData.scale_factors = {
                    x: window.scaleManager.scaleFactors.x,
                    y: window.scaleManager.scaleFactors.y
                };
                baseData.coordinates = {
                    coordinate_system: "real_world",
                    units: window.scaleManager.currentUnit,
                    svg_coordinates: {
                        x: baseData.x,
                        y: baseData.y
                    },
                    real_world_coords: {
                        x: baseData.x * window.scaleManager.scaleFactors.x,
                        y: baseData.y * window.scaleManager.scaleFactors.y
                    }
                };
            }

            // Add real-world coordinates if stored in element attributes
            const realWorldX = obj.getAttribute('data-real-world-x');
            const realWorldY = obj.getAttribute('data-real-world-y');
            const unit = obj.getAttribute('data-unit');
            
            if (realWorldX && realWorldY && unit) {
                if (!baseData.coordinates) {
                    baseData.coordinates = {};
                }
                baseData.coordinates.real_world_coords = {
                    x: parseFloat(realWorldX),
                    y: parseFloat(realWorldY)
                };
                baseData.coordinates.units = unit;
                baseData.coordinates.coordinate_system = "real_world";
            }

            return baseData;
        });

        if (objects.length === 0) return;

        try {
            // Show auto-save indicator
            this.autoSaveIndicator.classList.add('show');
            
            const response = await fetch('/api/bim/objects/bulk-update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    bim_object_ids: objects.map(obj => parseInt(obj.id)),
                    updates: {
                        x: objects[0].x,
                        y: objects[0].y,
                        rotation: objects[0].rotation
                    },
                    scale_factors: objects[0].scale_factors,
                    coordinates: objects[0].coordinates
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            this.showNotification('Changes saved successfully with scale metadata', 'success');
            
            // Update element attributes with saved data
            objects.forEach(objData => {
                const element = document.querySelector(`[data-id="${objData.id}"]`);
                if (element) {
                    if (objData.coordinates && objData.coordinates.real_world_coords) {
                        element.setAttribute('data-real-world-x', objData.coordinates.real_world_coords.x.toString());
                        element.setAttribute('data-real-world-y', objData.coordinates.real_world_coords.y.toString());
                        element.setAttribute('data-unit', objData.coordinates.units);
                    }
                }
            });
            
        } catch (error) {
            console.error('Error saving object positions:', error);
            this.showNotification('Failed to save changes. Use Ctrl+Z to undo.', 'error');
        } finally {
            // Hide auto-save indicator
            setTimeout(() => {
                this.autoSaveIndicator.classList.remove('show');
            }, 1000);
        }
    }

    async deleteObjectBackend(id) {
        try {
            const response = await fetch(`/api/bim/objects/${id}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            window.arxLogger.info('Object deleted successfully:', id, { file: 'object_interaction.js' });
        } catch (error) {
            console.error('Error deleting object:', error);
            this.showNotification('Failed to delete object from backend.', 'error');
        }
    }

    updateContextPanel() {
        if (window.contextPanel) {
            window.contextPanel.updateSelection(this.selectedObjects);
        }
    }

    /**
     * Convert screen coordinates to SVG coordinates
     */
    screenToSVGCoordinates(screenX, screenY) {
        if (this.viewportManager && this.viewportManager.screenToSVG) {
            return this.viewportManager.screenToSVG(screenX, screenY);
        }
        return { x: screenX, y: screenY };
    }

    /**
     * Convert SVG coordinates to screen coordinates
     */
    svgToScreenCoordinates(svgX, svgY) {
        if (this.viewportManager && this.viewportManager.svgToScreen) {
            return this.viewportManager.svgToScreen(svgX, svgY);
        }
        return { x: svgX, y: svgY };
    }

    /**
     * Test multi-object selection with zoom
     */
    testMultiObjectSelection() {
        if (!this.viewportManager) {
            console.warn('Viewport manager not available for testing');
            return;
        }

        window.arxLogger.debug('=== Testing Multi-Object Selection with Zoom ===', { file: 'object_interaction.js' });
        
        const placedSymbols = document.querySelectorAll('.placed-symbol');
        if (placedSymbols.length < 2) {
            console.warn('Need at least 2 objects for multi-selection testing');
            return;
        }

        // Test at different zoom levels
        const zoomLevels = [0.5, 1.0, 2.0, 3.0];
        
        zoomLevels.forEach((zoom, zoomIndex) => {
            window.arxLogger.debug(`\n--- Testing at Zoom Level ${zoom} ---`, { file: 'object_interaction.js' });
            
            // Set zoom level
            this.viewportManager.setZoom(zoom);
            
            // Clear selection
            this.clearSelection();
            
            // Select multiple objects
            const objectsToSelect = Array.from(placedSymbols).slice(0, 3);
            objectsToSelect.forEach((obj, index) => {
                this.selectObject(obj);
                window.arxLogger.debug(`Selected object ${index + 1}: ${obj.getAttribute('data-id')}`, { file: 'object_interaction.js' });
            });
            
            // Test selection state
            window.arxLogger.debug(`Total selected objects: ${this.selectedObjects.size}`, { file: 'object_interaction.js' });
            
            // Test object positions
            this.selectedObjects.forEach((obj, index) => {
                const x = parseFloat(obj.getAttribute('data-x')) || 0;
                const y = parseFloat(obj.getAttribute('data-y')) || 0;
                window.arxLogger.debug(`Object ${index + 1} position: (${x.toFixed(2)}, ${y.toFixed(2)})`, { file: 'object_interaction.js' });
            });
            
            // Test rotate handle
            if (this.selectedObjects.size > 0) {
                const firstObject = Array.from(this.selectedObjects)[0];
                this.showRotateHandle(firstObject);
                window.arxLogger.debug('Rotate handle displayed', { file: 'object_interaction.js' });
            }
            
            // Wait before next test
            setTimeout(() => {
                if (zoomIndex < zoomLevels.length - 1) {
                    window.arxLogger.debug('Moving to next zoom level...', { file: 'object_interaction.js' });
                } else {
                    window.arxLogger.debug('Multi-object selection testing complete!', { file: 'object_interaction.js' });
                    this.clearSelection();
                }
            }, 1000);
        });
        
        // Reset to original zoom
        setTimeout(() => {
            this.viewportManager.setZoom(1.0);
            window.arxLogger.debug('Reset to original zoom level', { file: 'object_interaction.js' });
        }, zoomLevels.length * 1000 + 2000);
    }

    /**
     * Get selection bounds in SVG coordinates
     */
    getSelectionBounds() {
        if (this.selectedObjects.size === 0) return null;
        
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        this.selectedObjects.forEach(obj => {
            const x = parseFloat(obj.getAttribute('data-x')) || 0;
            const y = parseFloat(obj.getAttribute('data-y')) || 0;
            
            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x);
            maxY = Math.max(maxY, y);
        });
        
        return {
            minX, minY, maxX, maxY,
            width: maxX - minX,
            height: maxY - minY,
            centerX: (minX + maxX) / 2,
            centerY: (minY + maxY) / 2
        };
    }

    /**
     * Move selection to center of viewport
     */
    centerSelection() {
        const bounds = this.getSelectionBounds();
        if (!bounds || !this.viewportManager) return;
        
        const containerRect = this.svgContainer.getBoundingClientRect();
        const centerX = containerRect.width / 2;
        const centerY = containerRect.height / 2;
        
        // Convert screen center to SVG coordinates
        const svgCenter = this.screenToSVGCoordinates(centerX, centerY);
        
        // Calculate offset to move selection to center
        const offsetX = svgCenter.x - bounds.centerX;
        const offsetY = svgCenter.y - bounds.centerY;
        
        // Move all selected objects
        this.selectedObjects.forEach(obj => {
            const currentX = parseFloat(obj.getAttribute('data-x')) || 0;
            const currentY = parseFloat(obj.getAttribute('data-y')) || 0;
            const newX = currentX + offsetX;
            const newY = currentY + offsetY;
            
            obj.setAttribute('data-x', newX);
            obj.setAttribute('data-y', newY);
            const rotation = obj.getAttribute('data-rotation') || 0;
            obj.setAttribute('transform', `translate(${newX},${newY}) rotate(${rotation})`);
        });
        
        // Update rotate handle
        this.updateRotateHandlePosition();
        
        window.arxLogger.info('Selection centered', { file: 'object_interaction.js' });
    }

    /**
     * Load objects with scale metadata and restore coordinate information
     */
    async loadObjectsWithScaleMetadata(floorId) {
        try {
            const response = await fetch(`/api/bim/floor/${floorId}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const bimModel = await response.json();
            
            // Process all BIM objects and restore scale metadata
            const allObjects = [
                ...bimModel.rooms || [],
                ...bimModel.devices || [],
                ...bimModel.labels || [],
                ...bimModel.panels || [],
                ...bimModel.connectors || [],
                ...bimModel.walls || [],
                ...bimModel.zones || []
            ];

            allObjects.forEach(obj => {
                this.restoreObjectScaleMetadata(obj);
            });

            window.arxLogger.info(`Loaded ${allObjects.length} objects with scale metadata`, { file: 'object_interaction.js' });
            this.showNotification(`Loaded ${allObjects.length} objects with scale metadata`, 'success');
            
        } catch (error) {
            console.error('Error loading objects with scale metadata:', error);
            this.showNotification('Failed to load objects with scale metadata', 'error');
        }
    }

    /**
     * Restore scale metadata for a single object
     */
    restoreObjectScaleMetadata(bimObject) {
        const element = document.querySelector(`[data-id="${bimObject.object_id}"]`);
        if (!element) {
            console.warn(`Element not found for BIM object: ${bimObject.object_id}`);
            return;
        }

        // Restore scale factors if available
        if (bimObject.scale_factors) {
            try {
                const scaleFactors = typeof bimObject.scale_factors === 'string' 
                    ? JSON.parse(bimObject.scale_factors) 
                    : bimObject.scale_factors;
                
                element.setAttribute('data-scale-x', scaleFactors.x.toString());
                element.setAttribute('data-scale-y', scaleFactors.y.toString());
            } catch (error) {
                console.warn(`Failed to parse scale factors for object ${bimObject.object_id}:`, error);
            }
        }

        // Restore coordinate system information
        if (bimObject.coordinate_system) {
            element.setAttribute('data-coordinate-system', bimObject.coordinate_system);
        }

        if (bimObject.units) {
            element.setAttribute('data-unit', bimObject.units);
        }

        // Restore SVG coordinates if available
        if (bimObject.svg_coordinates) {
            try {
                const svgCoords = typeof bimObject.svg_coordinates === 'string' 
                    ? JSON.parse(bimObject.svg_coordinates) 
                    : bimObject.svg_coordinates;
                
                element.setAttribute('data-svg-x', svgCoords.x.toString());
                element.setAttribute('data-svg-y', svgCoords.y.toString());
            } catch (error) {
                console.warn(`Failed to parse SVG coordinates for object ${bimObject.object_id}:`, error);
            }
        }

        // Restore real-world coordinates if available
        if (bimObject.real_world_coords) {
            try {
                const realWorldCoords = typeof bimObject.real_world_coords === 'string' 
                    ? JSON.parse(bimObject.real_world_coords) 
                    : bimObject.real_world_coords;
                
                element.setAttribute('data-real-world-x', realWorldCoords.x.toString());
                element.setAttribute('data-real-world-y', realWorldCoords.y.toString());
            } catch (error) {
                console.warn(`Failed to parse real-world coordinates for object ${bimObject.object_id}:`, error);
            }
        }

        // Update scale manager if this is the first object with scale metadata
        if (window.scaleManager && bimObject.scale_factors && !window.scaleManager.scaleFactors.x) {
            try {
                const scaleFactors = typeof bimObject.scale_factors === 'string' 
                    ? JSON.parse(bimObject.scale_factors) 
                    : bimObject.scale_factors;
                
                window.scaleManager.setScaleFactors(scaleFactors.x, scaleFactors.y, bimObject.units || 'pixels');
                window.arxLogger.info(`Restored scale factors from object ${bimObject.object_id}:`, scaleFactors, { file: 'object_interaction.js' });
            } catch (error) {
                console.warn(`Failed to restore scale factors from object ${bimObject.object_id}:`, error);
            }
        }
    }

    /**
     * Test coordinate persistence across sessions
     */
    testCoordinatePersistence() {
        window.arxLogger.debug('=== Testing Coordinate Persistence ===', { file: 'object_interaction.js' });
        
        // Test 1: Save objects with scale metadata
        window.arxLogger.debug('1. Testing save with scale metadata...', { file: 'object_interaction.js' });
        this.saveObjectPositions();
        
        setTimeout(() => {
            // Test 2: Simulate session reload
            window.arxLogger.debug('2. Simulating session reload...', { file: 'object_interaction.js' });
            this.simulateSessionReload();
        }, 2000);
    }

    /**
     * Simulate session reload by clearing and restoring objects
     */
    simulateSessionReload() {
        // Store current objects
        const currentObjects = Array.from(this.selectedObjects).map(obj => ({
            id: obj.getAttribute('data-id'),
            x: obj.getAttribute('data-x'),
            y: obj.getAttribute('data-y'),
            rotation: obj.getAttribute('data-rotation'),
            realWorldX: obj.getAttribute('data-real-world-x'),
            realWorldY: obj.getAttribute('data-real-world-y'),
            unit: obj.getAttribute('data-unit'),
            scaleX: obj.getAttribute('data-scale-x'),
            scaleY: obj.getAttribute('data-scale-y')
        }));

        window.arxLogger.debug('Stored objects for session reload:', currentObjects, { file: 'object_interaction.js' });

        // Clear selection
        this.clearSelection();

        // Simulate loading objects back
        setTimeout(() => {
            window.arxLogger.debug('3. Restoring objects from session...', { file: 'object_interaction.js' });
            currentObjects.forEach(objData => {
                const element = document.querySelector(`[data-id="${objData.id}"]`);
                if (element) {
                    // Restore attributes
                    if (objData.x) element.setAttribute('data-x', objData.x);
                    if (objData.y) element.setAttribute('data-y', objData.y);
                    if (objData.rotation) element.setAttribute('data-rotation', objData.rotation);
                    if (objData.realWorldX) element.setAttribute('data-real-world-x', objData.realWorldX);
                    if (objData.realWorldY) element.setAttribute('data-real-world-y', objData.realWorldY);
                    if (objData.unit) element.setAttribute('data-unit', objData.unit);
                    if (objData.scaleX) element.setAttribute('data-scale-x', objData.scaleX);
                    if (objData.scaleY) element.setAttribute('data-scale-y', objData.scaleY);

                    // Select the object
                    this.selectObject(element);
                }
            });

            window.arxLogger.debug('Session reload simulation complete!', { file: 'object_interaction.js' });
            this.showNotification('Coordinate persistence test completed', 'success');
        }, 1000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.svgObjectInteraction = new SVGObjectInteraction();
});
