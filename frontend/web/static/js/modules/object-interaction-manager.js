/**
 * Object Interaction Manager
 * Orchestrates selection, drag, click, and hover modules
 */

import { Selection } from './selection.js';
import { Drag } from './drag.js';
import { Click } from './click.js';
import { Hover } from './hover.js';

export class ObjectInteractionManager {
    constructor(viewportManager, options = {}) {
        this.viewportManager = viewportManager;
        this.options = options;
        
        // Initialize modules
        this.selection = new Selection(viewportManager, options);
        this.drag = new Drag(viewportManager, this.selection, options);
        this.click = new Click(viewportManager, this.selection, options);
        this.hover = new Hover(viewportManager, options);
        
        // Connect modules
        this.connectModules();
        
        // Performance optimizations
        this.autoSaveTimer = null;
        this.autoSaveDelay = options.autoSaveDelay || 2000; // 2 seconds
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.setupAutoSave();
        this.createAutoSaveIndicator();
    }

    connectModules() {
        // Connect selection events to other modules
        this.selection.addEventListener('selectionChanged', () => {
            this.click.updateRotateHandlePosition();
            this.triggerEvent('selectionChanged');
        });
        
        this.selection.addEventListener('selectionCleared', () => {
            this.click.hideRotateHandle();
            this.triggerEvent('selectionCleared');
        });
        
        // Connect drag events
        this.drag.addEventListener('dragStarted', (data) => {
            this.triggerEvent('dragStarted', data);
        });
        
        this.drag.addEventListener('dragEnded', (data) => {
            this.triggerEvent('dragEnded', data);
            this.triggerAutoSave();
        });
        
        // Connect click events
        this.click.addEventListener('objectsDeleted', (data) => {
            this.triggerEvent('objectsDeleted', data);
            this.triggerAutoSave();
        });
        
        this.click.addEventListener('objectsRotated', (data) => {
            this.triggerEvent('objectsRotated', data);
            this.triggerAutoSave();
        });
        
        // Connect hover events
        this.hover.addEventListener('tooltipShown', (data) => {
            this.triggerEvent('tooltipShown', data);
        });
    }

    setupEventListeners() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Window events
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });
    }

    setupAutoSave() {
        // Auto-save functionality
        this.autoSaveEnabled = this.options.autoSaveEnabled !== false;
    }

    createAutoSaveIndicator() {
        this.autoSaveIndicator = document.createElement('div');
        this.autoSaveIndicator.className = 'auto-save-indicator';
        this.autoSaveIndicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 123, 255, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 10000;
            display: none;
            pointer-events: none;
        `;
        
        document.body.appendChild(this.autoSaveIndicator);
    }

    handleKeyDown(event) {
        // Global keyboard shortcuts
        switch (event.key) {
            case 'Escape':
                this.cancelAllOperations();
                break;
            case 's':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.saveState();
                }
                break;
            case 'z':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.undo();
                }
                break;
            case 'y':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.redo();
                }
                break;
        }
    }

    // Auto-save functionality
    triggerAutoSave() {
        if (!this.autoSaveEnabled) return;
        
        // Clear existing timer
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // Set new timer
        this.autoSaveTimer = setTimeout(() => {
            this.saveState();
        }, this.autoSaveDelay);
    }

    async saveState() {
        try {
            const selectedObjects = this.selection.getSelectedObjects();
            const state = {
                selectedObjects: selectedObjects.map(obj => ({
                    id: obj.id,
                    type: obj.getAttribute('data-type'),
                    position: this.getObjectPosition(obj),
                    rotation: this.getObjectRotation(obj)
                })),
                timestamp: Date.now()
            };
            
            // Save to localStorage for persistence
            localStorage.setItem('objectInteractionState', JSON.stringify(state));
            
            // Show auto-save indicator
            this.showAutoSaveIndicator('Auto-saved');
            
            this.triggerEvent('stateSaved', { state });
        } catch (error) {
            console.error('Error saving state:', error);
            this.triggerEvent('stateSaveError', { error });
        }
    }

    loadState() {
        try {
            const savedState = localStorage.getItem('objectInteractionState');
            if (savedState) {
                const state = JSON.parse(savedState);
                this.restoreState(state);
                this.triggerEvent('stateLoaded', { state });
            }
        } catch (error) {
            console.error('Error loading state:', error);
            this.triggerEvent('stateLoadError', { error });
        }
    }

    restoreState(state) {
        if (!state || !state.selectedObjects) return;
        
        // Restore selected objects
        state.selectedObjects.forEach(objData => {
            const obj = document.getElementById(objData.id);
            if (obj) {
                this.selection.selectedObjects.add(obj);
                this.selection.highlightObject(obj);
                
                // Restore position and rotation
                if (objData.position) {
                    this.setObjectPosition(obj, objData.position);
                }
                if (objData.rotation !== undefined) {
                    this.setObjectRotation(obj, objData.rotation);
                }
            }
        });
        
        this.selection.updateSelectionCache();
    }

    // Utility methods
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

    setObjectPosition(obj, position) {
        const transform = `translate(${position.x}, ${position.y})`;
        obj.setAttribute('transform', transform);
        obj.setAttribute('data-x', position.x.toString());
        obj.setAttribute('data-y', position.y.toString());
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
        const transformWithoutRotation = currentTransform.replace(/rotate\([^)]+\)/g, '');
        const newTransform = `${transformWithoutRotation} rotate(${angle})`;
        obj.setAttribute('transform', newTransform);
        obj.setAttribute('data-rotation', angle.toString());
    }

    // Operation control methods
    cancelAllOperations() {
        this.drag.cancelDrag();
        this.selection.clearSelection();
        this.click.hideContextMenu();
        this.hover.hideTooltip();
        
        this.triggerEvent('allOperationsCancelled');
    }

    // Undo/Redo functionality
    undo() {
        // Implement undo functionality
        this.triggerEvent('undo');
    }

    redo() {
        // Implement redo functionality
        this.triggerEvent('redo');
    }

    // Auto-save indicator
    showAutoSaveIndicator(message) {
        if (!this.autoSaveIndicator) return;
        
        this.autoSaveIndicator.textContent = message;
        this.autoSaveIndicator.style.display = 'block';
        
        setTimeout(() => {
            this.autoSaveIndicator.style.display = 'none';
        }, 2000);
    }

    // Module access methods
    getSelection() {
        return this.selection;
    }

    getDrag() {
        return this.drag;
    }

    getClick() {
        return this.click;
    }

    getHover() {
        return this.hover;
    }

    // Public API methods
    selectObject(obj) {
        return this.selection.selectObject(obj);
    }

    clearSelection() {
        return this.selection.clearSelection();
    }

    getSelectedObjects() {
        return this.selection.getSelectedObjects();
    }

    isObjectSelected(obj) {
        return this.selection.isObjectSelected(obj);
    }

    enableDrag() {
        return this.drag.enableDrag();
    }

    disableDrag() {
        return this.drag.disableDrag();
    }

    isDragEnabled() {
        return this.drag.isDragEnabled();
    }

    enableHoverEffects() {
        return this.hover.enableHoverEffects();
    }

    disableHoverEffects() {
        return this.hover.disableHoverEffects();
    }

    enableTooltip() {
        return this.hover.enableTooltip();
    }

    disableTooltip() {
        return this.hover.disableTooltip();
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
                    handler({ ...data, manager: this });
                } catch (error) {
                    console.error(`Error in object interaction manager event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        // Clear auto-save timer
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // Remove auto-save indicator
        if (this.autoSaveIndicator) {
            this.autoSaveIndicator.remove();
        }
        
        // Destroy modules
        if (this.selection) {
            this.selection.destroy();
        }
        if (this.drag) {
            this.drag.destroy();
        }
        if (this.click) {
            this.click.destroy();
        }
        if (this.hover) {
            this.hover.destroy();
        }
        
        // Clear event handlers
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 