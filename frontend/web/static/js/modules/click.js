/**
 * Click Module
 * Handles click interactions, object manipulation, and context menus
 */

export class Click {
    constructor(viewportManager, selection, options = {}) {
        this.viewportManager = viewportManager;
        this.selection = selection;
        
        // Click state
        this.clickTimeout = null;
        this.clickDelay = options.clickDelay || 300; // ms for double click
        this.lastClickTime = 0;
        this.lastClickTarget = null;
        
        // Context menu
        this.contextMenu = null;
        this.contextMenuEnabled = options.contextMenuEnabled !== false;
        
        // Object manipulation
        this.rotateHandle = null;
        this.rotateEnabled = options.rotateEnabled !== false;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createContextMenu();
        this.createRotateHandle();
    }

    setupEventListeners() {
        if (!this.viewportManager || !this.viewportManager.svg) return;
        
        const svg = this.viewportManager.svg;
        
        // Click events
        svg.addEventListener('click', (e) => this.handleClick(e));
        svg.addEventListener('dblclick', (e) => this.handleDoubleClick(e));
        svg.addEventListener('contextmenu', (e) => this.handleContextMenu(e));
        
        // Keyboard events
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Global click to close context menu
        document.addEventListener('click', (e) => this.handleGlobalClick(e));
    }

    handleClick(event) {
        const target = this.findClickableObject(event.target);
        if (!target) {
            this.clearSelection();
            this.hideRotateHandle();
            return;
        }
        
        const currentTime = Date.now();
        const isDoubleClick = (currentTime - this.lastClickTime) < this.clickDelay && 
                             target === this.lastClickTarget;
        
        if (isDoubleClick) {
            // Handle double click
            this.handleDoubleClick(event);
        } else {
            // Handle single click
            this.handleSingleClick(event, target);
        }
        
        this.lastClickTime = currentTime;
        this.lastClickTarget = target;
    }

    handleSingleClick(event, target) {
        if (event.shiftKey) {
            this.selection.toggleObjectSelection(target);
        } else {
            this.selection.selectObject(target);
        }
        
        this.showRotateHandle(target);
        this.triggerEvent('objectClicked', { target, event });
    }

    handleDoubleClick(event) {
        const target = this.findClickableObject(event.target);
        if (!target) return;
        
        // Open object properties or edit mode
        this.openObjectProperties(target);
        this.triggerEvent('objectDoubleClicked', { target, event });
    }

    handleContextMenu(event) {
        if (!this.contextMenuEnabled) return;
        
        event.preventDefault();
        
        const target = this.findClickableObject(event.target);
        if (target) {
            // Select object if not already selected
            if (!this.selection.isObjectSelected(target)) {
                this.selection.selectObject(target);
            }
            
            this.showContextMenu(event, target);
        } else {
            this.showBackgroundContextMenu(event);
        }
    }

    handleKeyDown(event) {
        switch (event.key) {
            case 'Delete':
            case 'Backspace':
                this.deleteSelectedObjects();
                break;
            case 'r':
            case 'R':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.rotateSelectedObjects(90);
                }
                break;
            case 'Escape':
                this.clearSelection();
                this.hideContextMenu();
                break;
        }
    }

    handleGlobalClick(event) {
        // Close context menu if clicking outside
        if (this.contextMenu && !this.contextMenu.contains(event.target)) {
            this.hideContextMenu();
        }
    }

    // Object manipulation methods
    deleteSelectedObjects() {
        const selectedObjects = this.selection.getSelectedObjects();
        
        if (selectedObjects.length === 0) return;
        
        // Confirm deletion
        if (!confirm(`Delete ${selectedObjects.length} selected object(s)?`)) {
            return;
        }
        
        selectedObjects.forEach(obj => {
            this.deleteObject(obj);
        });
        
        this.selection.clearSelection();
        this.hideRotateHandle();
        
        this.triggerEvent('objectsDeleted', { count: selectedObjects.length });
    }

    async deleteObject(obj) {
        if (!obj || !obj.id) return;
        
        try {
            const response = await fetch(`/api/objects/${obj.id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete object');
            }
            
            // Remove from DOM
            obj.remove();
            
            this.triggerEvent('objectDeleted', { object: obj });
        } catch (error) {
            console.error('Error deleting object:', error);
            this.triggerEvent('objectDeleteError', { object: obj, error });
        }
    }

    rotateSelectedObjects(angle) {
        const selectedObjects = this.selection.getSelectedObjects();
        
        selectedObjects.forEach(obj => {
            this.rotateObject(obj, angle);
        });
        
        this.triggerEvent('objectsRotated', { angle, count: selectedObjects.length });
    }

    rotateObject(obj, angle) {
        if (!obj) return;
        
        const currentRotation = this.getObjectRotation(obj);
        const newRotation = currentRotation + angle;
        
        this.setObjectRotation(obj, newRotation);
    }

    getObjectRotation(obj) {
        const transform = obj.getAttribute('transform');
        if (transform) {
            const rotation = transform.match(/rotate\(([^)]+)\)/);
            if (rotation) {
                return parseFloat(rotation[1]);
            }
        }
        return 0;
    }

    setObjectRotation(obj, angle) {
        const currentTransform = obj.getAttribute('transform') || '';
        const position = this.getObjectPosition(obj);
        
        // Remove existing rotation
        const transformWithoutRotation = currentTransform.replace(/rotate\([^)]+\)/g, '');
        
        // Add new rotation
        const newTransform = `${transformWithoutRotation} rotate(${angle})`;
        obj.setAttribute('transform', newTransform);
        
        // Update data attribute
        obj.setAttribute('data-rotation', angle.toString());
    }

    getObjectPosition(obj) {
        const transform = obj.getAttribute('transform');
        if (transform) {
            const translate = transform.match(/translate\(([^,]+),([^)]+)\)/);
            if (translate) {
                return {
                    x: parseFloat(translate[1]),
                    y: parseFloat(translate[2])
                };
            }
        }
        
        return {
            x: parseFloat(obj.getAttribute('x') || '0'),
            y: parseFloat(obj.getAttribute('y') || '0')
        };
    }

    // Rotate handle methods
    showRotateHandle(obj) {
        if (!this.rotateEnabled || !obj) return;
        
        this.hideRotateHandle();
        
        const rect = obj.getBoundingClientRect();
        const svgRect = this.viewportManager.svg.getBoundingClientRect();
        
        this.rotateHandle.style.display = 'block';
        this.rotateHandle.style.left = `${rect.right - svgRect.left + 10}px`;
        this.rotateHandle.style.top = `${rect.top - svgRect.top}px`;
        
        this.setupRotateHandleEvents(obj);
    }

    hideRotateHandle() {
        if (this.rotateHandle) {
            this.rotateHandle.style.display = 'none';
        }
    }

    updateRotateHandlePosition() {
        const selectedObjects = this.selection.getSelectedObjects();
        if (selectedObjects.length === 1) {
            this.showRotateHandle(selectedObjects[0]);
        } else {
            this.hideRotateHandle();
        }
    }

    setupRotateHandleEvents(obj) {
        if (!this.rotateHandle) return;
        
        const handleMouseDown = (event) => {
            event.stopPropagation();
            this.startRotation(event, obj);
        };
        
        this.rotateHandle.onmousedown = handleMouseDown;
    }

    startRotation(event, obj) {
        const startAngle = this.calculateAngle(event, obj);
        let isRotating = true;
        
        const handleMouseMove = (moveEvent) => {
            if (!isRotating) return;
            
            const currentAngle = this.calculateAngle(moveEvent, obj);
            const deltaAngle = currentAngle - startAngle;
            
            this.rotateObject(obj, deltaAngle);
        };
        
        const handleMouseUp = () => {
            isRotating = false;
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }

    calculateAngle(event, obj) {
        const rect = obj.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        const deltaX = event.clientX - centerX;
        const deltaY = event.clientY - centerY;
        
        return Math.atan2(deltaY, deltaX) * 180 / Math.PI;
    }

    createRotateHandle() {
        this.rotateHandle = document.createElement('div');
        this.rotateHandle.className = 'rotate-handle';
        this.rotateHandle.innerHTML = '↻';
        this.rotateHandle.style.cssText = `
            position: absolute;
            width: 20px;
            height: 20px;
            background: #007bff;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 12px;
            z-index: 1000;
            display: none;
        `;
        
        this.viewportManager.container.appendChild(this.rotateHandle);
    }

    // Context menu methods
    showContextMenu(event, target) {
        if (!this.contextMenu) return;
        
        this.contextMenu.style.display = 'block';
        this.contextMenu.style.left = `${event.clientX}px`;
        this.contextMenu.style.top = `${event.clientY}px`;
        
        this.updateContextMenuItems(target);
    }

    showBackgroundContextMenu(event) {
        if (!this.contextMenu) return;
        
        this.contextMenu.style.display = 'block';
        this.contextMenu.style.left = `${event.clientX}px`;
        this.contextMenu.style.top = `${event.clientY}px`;
        
        this.updateBackgroundContextMenuItems();
    }

    hideContextMenu() {
        if (this.contextMenu) {
            this.contextMenu.style.display = 'none';
        }
    }

    updateContextMenuItems(target) {
        if (!this.contextMenu) return;
        
        this.contextMenu.innerHTML = `
            <div class="context-menu-item" data-action="properties">Properties</div>
            <div class="context-menu-item" data-action="edit">Edit</div>
            <div class="context-menu-item" data-action="duplicate">Duplicate</div>
            <div class="context-menu-item" data-action="delete">Delete</div>
            <div class="context-menu-separator"></div>
            <div class="context-menu-item" data-action="bring-to-front">Bring to Front</div>
            <div class="context-menu-item" data-action="send-to-back">Send to Back</div>
        `;
        
        this.setupContextMenuEvents(target);
    }

    updateBackgroundContextMenuItems() {
        if (!this.contextMenu) return;
        
        this.contextMenu.innerHTML = `
            <div class="context-menu-item" data-action="paste">Paste</div>
            <div class="context-menu-item" data-action="select-all">Select All</div>
            <div class="context-menu-separator"></div>
            <div class="context-menu-item" data-action="zoom-to-fit">Zoom to Fit</div>
        `;
        
        this.setupBackgroundContextMenuEvents();
    }

    setupContextMenuEvents(target) {
        if (!this.contextMenu) return;
        
        this.contextMenu.addEventListener('click', (event) => {
            const action = event.target.getAttribute('data-action');
            if (action) {
                this.handleContextMenuAction(action, target);
            }
        });
    }

    setupBackgroundContextMenuEvents() {
        if (!this.contextMenu) return;
        
        this.contextMenu.addEventListener('click', (event) => {
            const action = event.target.getAttribute('data-action');
            if (action) {
                this.handleBackgroundContextMenuAction(action);
            }
        });
    }

    handleContextMenuAction(action, target) {
        this.hideContextMenu();
        
        switch (action) {
            case 'properties':
                this.openObjectProperties(target);
                break;
            case 'edit':
                this.editObject(target);
                break;
            case 'duplicate':
                this.duplicateObject(target);
                break;
            case 'delete':
                this.deleteObject(target);
                break;
            case 'bring-to-front':
                this.bringToFront(target);
                break;
            case 'send-to-back':
                this.sendToBack(target);
                break;
        }
    }

    handleBackgroundContextMenuAction(action) {
        this.hideContextMenu();
        
        switch (action) {
            case 'paste':
                this.pasteObjects();
                break;
            case 'select-all':
                this.selection.selectAllObjects();
                break;
            case 'zoom-to-fit':
                this.viewportManager.fitToView();
                break;
        }
    }

    createContextMenu() {
        this.contextMenu = document.createElement('div');
        this.contextMenu.className = 'context-menu';
        this.contextMenu.style.cssText = `
            position: fixed;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 4px 0;
            z-index: 10000;
            display: none;
            min-width: 150px;
        `;
        
        document.body.appendChild(this.contextMenu);
    }

    // Utility methods
    findClickableObject(target) {
        if (!target) return null;
        
        // Walk up the DOM tree to find the closest clickable object
        let element = target;
        while (element && element !== this.viewportManager.svg) {
            if (this.isClickableObject(element)) {
                return element;
            }
            element = element.parentElement;
        }
        
        return null;
    }

    isClickableObject(element) {
        return element && (
            element.classList.contains('clickable') ||
            element.classList.contains('bim-object') ||
            element.classList.contains('svg-object') ||
            element.hasAttribute('data-clickable')
        );
    }

    clearSelection() {
        this.selection.clearSelection();
        this.hideRotateHandle();
    }

    // Object manipulation actions
    openObjectProperties(target) {
        // Open properties dialog
        this.triggerEvent('openProperties', { target });
    }

    editObject(target) {
        // Enter edit mode
        this.triggerEvent('editObject', { target });
    }

    duplicateObject(target) {
        // Duplicate object
        this.triggerEvent('duplicateObject', { target });
    }

    pasteObjects() {
        // Paste objects from clipboard
        this.triggerEvent('pasteObjects');
    }

    bringToFront(target) {
        // Bring object to front
        if (target.parentNode) {
            target.parentNode.appendChild(target);
        }
        this.triggerEvent('objectBroughtToFront', { target });
    }

    sendToBack(target) {
        // Send object to back
        if (target.parentNode && target.parentNode.firstChild) {
            target.parentNode.insertBefore(target, target.parentNode.firstChild);
        }
        this.triggerEvent('objectSentToBack', { target });
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
                    handler({ ...data, click: this });
                } catch (error) {
                    console.error(`Error in click event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.hideContextMenu();
        this.hideRotateHandle();
        
        if (this.contextMenu) {
            this.contextMenu.remove();
        }
        
        if (this.rotateHandle) {
            this.rotateHandle.remove();
        }
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 