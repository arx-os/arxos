/**
 * Selection Module
 * Handles object selection, multi-selection, and selection state management
 */

export class Selection {
    constructor(viewportManager, options = {}) {
        this.viewportManager = viewportManager;
        
        // Selection state
        this.selectedObjects = new Set();
        this.selectionCache = new Map();
        this.maxUndoSteps = options.maxUndoSteps || 50;
        
        // Marquee selection
        this.isMarqueeSelecting = false;
        this.marqueeStart = null;
        this.marqueeElement = null;
        
        // Performance optimizations
        this.selectionUpdateThrottle = options.selectionUpdateThrottle || 16; // ~60fps
        this.lastSelectionUpdate = 0;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createMarqueeElement();
    }

    setupEventListeners() {
        if (!this.viewportManager || !this.viewportManager.svg) return;
        
        const svg = this.viewportManager.svg;
        
        // Click to select
        svg.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        
        // Marquee selection
        svg.addEventListener('mousedown', (e) => this.handleMarqueeStart(e));
        svg.addEventListener('mousemove', (e) => this.handleMarqueeMove(e));
        svg.addEventListener('mouseup', (e) => this.handleMarqueeEnd(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    handleMouseDown(event) {
        const target = this.findClosestObject(event.target);
        if (!target) {
            this.clearSelection();
            return;
        }
        
        if (event.shiftKey) {
            this.toggleObjectSelection(target);
        } else {
            this.selectObject(target);
        }
        
        this.triggerEvent('selectionChanged', { target });
    }

    handleMarqueeStart(event) {
        if (event.target !== this.viewportManager.svg && 
            !event.target.classList.contains('svg-background')) {
            return;
        }
        
        this.startMarqueeSelection(event);
    }

    handleMarqueeMove(event) {
        if (!this.isMarqueeSelecting) return;
        
        this.updateMarqueeSelection(event);
    }

    handleMarqueeEnd(event) {
        if (!this.isMarqueeSelecting) return;
        
        this.endMarqueeSelection(event);
    }

    handleKeyDown(event) {
        switch (event.key) {
            case 'a':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.selectAllObjects();
                }
                break;
            case 'Escape':
                this.clearSelection();
                break;
        }
    }

    // Object selection methods
    selectObject(obj) {
        if (!obj) return;
        
        this.clearSelection();
        this.selectedObjects.add(obj);
        this.highlightObject(obj);
        this.updateSelectionCache();
        this.triggerEvent('objectSelected', { object: obj });
    }

    toggleObjectSelection(obj) {
        if (!obj) return;
        
        if (this.selectedObjects.has(obj)) {
            this.deselectObject(obj);
        } else {
            this.selectedObjects.add(obj);
            this.highlightObject(obj);
        }
        
        this.updateSelectionCache();
        this.triggerEvent('selectionToggled', { object: obj });
    }

    deselectObject(obj) {
        if (!obj) return;
        
        this.selectedObjects.delete(obj);
        this.unhighlightObject(obj);
        this.triggerEvent('objectDeselected', { object: obj });
    }

    clearSelection() {
        this.selectedObjects.forEach(obj => {
            this.unhighlightObject(obj);
        });
        this.selectedObjects.clear();
        this.updateSelectionCache();
        this.triggerEvent('selectionCleared');
    }

    selectAllObjects() {
        const allObjects = this.getAllSelectableObjects();
        allObjects.forEach(obj => {
            this.selectedObjects.add(obj);
            this.highlightObject(obj);
        });
        this.updateSelectionCache();
        this.triggerEvent('allObjectsSelected', { count: allObjects.length });
    }

    // Marquee selection methods
    startMarqueeSelection(event) {
        this.isMarqueeSelecting = true;
        this.marqueeStart = this.getMousePosition(event);
        
        if (this.marqueeElement) {
            this.marqueeElement.style.display = 'block';
            this.marqueeElement.style.left = `${this.marqueeStart.x}px`;
            this.marqueeElement.style.top = `${this.marqueeStart.y}px`;
            this.marqueeElement.style.width = '0px';
            this.marqueeElement.style.height = '0px';
        }
    }

    updateMarqueeSelection(event) {
        if (!this.isMarqueeSelecting || !this.marqueeStart) return;
        
        const currentPos = this.getMousePosition(event);
        const rect = this.calculateMarqueeRect(this.marqueeStart, currentPos);
        
        if (this.marqueeElement) {
            this.marqueeElement.style.left = `${rect.left}px`;
            this.marqueeElement.style.top = `${rect.top}px`;
            this.marqueeElement.style.width = `${rect.width}px`;
            this.marqueeElement.style.height = `${rect.height}px`;
        }
        
        // Update selection based on marquee
        this.updateSelectionFromMarquee(rect);
    }

    endMarqueeSelection(event) {
        this.isMarqueeSelecting = false;
        
        if (this.marqueeElement) {
            this.marqueeElement.style.display = 'none';
        }
        
        this.triggerEvent('marqueeSelectionEnded');
    }

    updateSelectionFromMarquee(rect) {
        const objectsInRect = this.getObjectsInRect(rect);
        
        if (event.shiftKey) {
            // Add to existing selection
            objectsInRect.forEach(obj => {
                this.selectedObjects.add(obj);
                this.highlightObject(obj);
            });
        } else {
            // Replace selection
            this.clearSelection();
            objectsInRect.forEach(obj => {
                this.selectedObjects.add(obj);
                this.highlightObject(obj);
            });
        }
        
        this.updateSelectionCache();
    }

    // Utility methods
    findClosestObject(target) {
        if (!target) return null;
        
        // Walk up the DOM tree to find the closest selectable object
        let element = target;
        while (element && element !== this.viewportManager.svg) {
            if (this.isSelectableObject(element)) {
                return element;
            }
            element = element.parentElement;
        }
        
        return null;
    }

    isSelectableObject(element) {
        return element && (
            element.classList.contains('selectable') ||
            element.classList.contains('bim-object') ||
            element.classList.contains('svg-object')
        );
    }

    getAllSelectableObjects() {
        const selectableElements = this.viewportManager.svg.querySelectorAll('.selectable, .bim-object, .svg-object');
        return Array.from(selectableElements);
    }

    getMousePosition(event) {
        const rect = this.viewportManager.svg.getBoundingClientRect();
        return {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
        };
    }

    getObjectsInRect(rect) {
        const objects = [];
        const selectableElements = this.getAllSelectableObjects();
        
        selectableElements.forEach(obj => {
            const objRect = obj.getBoundingClientRect();
            const svgRect = this.viewportManager.svg.getBoundingClientRect();
            
            const objScreenRect = {
                left: objRect.left - svgRect.left,
                top: objRect.top - svgRect.top,
                right: objRect.right - svgRect.left,
                bottom: objRect.bottom - svgRect.top
            };
            
            if (this.rectsIntersect(rect, objScreenRect)) {
                objects.push(obj);
            }
        });
        
        return objects;
    }

    calculateMarqueeRect(start, end) {
        return {
            left: Math.min(start.x, end.x),
            top: Math.min(start.y, end.y),
            width: Math.abs(end.x - start.x),
            height: Math.abs(end.y - start.y)
        };
    }

    rectsIntersect(rect1, rect2) {
        return !(rect1.left > rect2.right || 
                rect1.right < rect2.left || 
                rect1.top > rect2.bottom || 
                rect1.bottom < rect2.top);
    }

    // Visual feedback methods
    highlightObject(obj) {
        if (!obj) return;
        
        obj.classList.add('selected');
        obj.setAttribute('data-selected', 'true');
    }

    unhighlightObject(obj) {
        if (!obj) return;
        
        obj.classList.remove('selected');
        obj.removeAttribute('data-selected');
    }

    createMarqueeElement() {
        this.marqueeElement = document.createElement('div');
        this.marqueeElement.className = 'marquee-selection';
        this.marqueeElement.style.cssText = `
            position: absolute;
            border: 2px dashed #007bff;
            background: rgba(0, 123, 255, 0.1);
            pointer-events: none;
            z-index: 1000;
            display: none;
        `;
        
        this.viewportManager.container.appendChild(this.marqueeElement);
    }

    // Selection state management
    updateSelectionCache() {
        const currentTime = performance.now();
        if (currentTime - this.lastSelectionUpdate < this.selectionUpdateThrottle) {
            return;
        }
        
        this.lastSelectionUpdate = currentTime;
        
        this.selectionCache.clear();
        this.selectedObjects.forEach(obj => {
            this.selectionCache.set(obj, this.extractObjectData(obj));
        });
        
        this.triggerEvent('selectionCacheUpdated');
    }

    extractObjectData(obj) {
        return {
            id: obj.id,
            type: obj.getAttribute('data-type'),
            position: {
                x: parseFloat(obj.getAttribute('x') || '0'),
                y: parseFloat(obj.getAttribute('y') || '0')
            },
            transform: obj.getAttribute('transform') || '',
            selected: true
        };
    }

    // Selection query methods
    getSelectedObjects() {
        return Array.from(this.selectedObjects);
    }

    getSelectedObjectCount() {
        return this.selectedObjects.size;
    }

    isObjectSelected(obj) {
        return this.selectedObjects.has(obj);
    }

    getSelectionBounds() {
        if (this.selectedObjects.size === 0) return null;
        
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        this.selectedObjects.forEach(obj => {
            const rect = obj.getBoundingClientRect();
            const svgRect = this.viewportManager.svg.getBoundingClientRect();
            
            const x = rect.left - svgRect.left;
            const y = rect.top - svgRect.top;
            const width = rect.width;
            const height = rect.height;
            
            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x + width);
            maxY = Math.max(maxY, y + height);
        });
        
        return {
            left: minX,
            top: minY,
            right: maxX,
            bottom: maxY,
            width: maxX - minX,
            height: maxY - minY
        };
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
                    handler({ ...data, selection: this });
                } catch (error) {
                    console.error(`Error in selection event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.clearSelection();
        this.selectedObjects.clear();
        this.selectionCache.clear();
        
        if (this.marqueeElement) {
            this.marqueeElement.remove();
        }
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 