/**
 * Modular Viewport Manager
 * Orchestrates viewport, camera, zoom, and pan modules
 */

import { Viewport } from './viewport.js';
import { Camera } from './camera.js';
import { Zoom } from './zoom.js';
import { Pan } from './pan.js';

export class ViewportManager {
    constructor(svgElement, options = {}) {
        this.svgElement = svgElement;
        this.options = options;
        
        // Initialize modules
        this.viewport = new Viewport(svgElement, options);
        this.camera = new Camera(this.viewport, options);
        this.zoom = new Zoom(this.viewport, options);
        this.pan = new Pan(this.viewport, options);
        
        // Connect modules
        this.connectModules();
        
        // Performance optimization
        this.isUpdating = false;
        this.updateQueue = [];
        this.lastUpdateTime = 0;
        this.updateThrottle = options.updateThrottle || 16; // ~60fps
        
        // Throttled update manager integration
        this.throttledUpdateManager = null;
        this.enableThrottledUpdates = options.enableThrottledUpdates !== false;
        
        this.initialize();
    }

    initialize() {
        this.connectToThrottledUpdateManager();
        this.setupEventListeners();
    }

    connectModules() {
        // Connect camera to viewport
        this.viewport.camera = this.camera;
        
        // Listen for viewport changes
        this.viewport.addEventListener('viewportChanged', () => {
            this.handleViewportChange();
        });
        
        this.viewport.addEventListener('zoomChanged', () => {
            this.handleZoomChange();
        });
        
        this.viewport.addEventListener('panChanged', () => {
            this.handlePanChange();
        });
    }

    connectToThrottledUpdateManager() {
        if (!this.enableThrottledUpdates) return;
        
        const checkThrottledUpdateManager = () => {
            if (window.throttledUpdateManager) {
                this.throttledUpdateManager = window.throttledUpdateManager;
                this.throttledUpdateManager.addEventListener('update', (data) => {
                    this.handleThrottledUpdate(data);
                });
                
                this.throttledUpdateManager.addEventListener('batchedUpdate', (data) => {
                    this.handleBatchedUpdate(data);
                });
                
                this.throttledUpdateManager.addEventListener('updateProcessed', (data) => {
                    this.handleUpdateProcessed(data);
                });
                
                console.log('ViewportManager connected to ThrottledUpdateManager');
            } else {
                setTimeout(checkThrottledUpdateManager, 100);
            }
        };
        checkThrottledUpdateManager();
    }

    setupEventListeners() {
        // Global event listeners
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });
    }

    // Event handlers
    handleViewportChange() {
        this.triggerEvent('viewportChanged');
        this.queueUpdate();
    }

    handleZoomChange() {
        this.triggerEvent('zoomChanged');
        this.updateZoomDisplay();
    }

    handlePanChange() {
        this.triggerEvent('panChanged');
    }

    handleResize() {
        this.viewport.handleResize();
        this.triggerEvent('resize');
    }

    handleKeyDown(event) {
        // Global keyboard shortcuts
        switch (event.key) {
            case 'Escape':
                this.cancelOperations();
                break;
            case 'F':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.camera.fitToView();
                }
                break;
            case 'R':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.camera.resetView();
                }
                break;
            case '0':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.zoom.resetZoom();
                }
                break;
        }
    }

    // Performance optimization
    queueUpdate() {
        if (this.isUpdating) return;
        
        const currentTime = performance.now();
        if (currentTime - this.lastUpdateTime < this.updateThrottle) {
            return;
        }
        
        this.isUpdating = true;
        this.lastUpdateTime = currentTime;
        
        requestAnimationFrame(() => {
            this.performUpdate();
            this.isUpdating = false;
        });
    }

    performUpdate() {
        // Perform any necessary updates
        this.updateUIElements();
        this.triggerEvent('update');
    }

    // Throttled update handling
    handleThrottledUpdate(data) {
        // Handle throttled updates from the update manager
        this.triggerEvent('throttledUpdate', data);
    }

    handleBatchedUpdate(data) {
        // Handle batched updates
        this.triggerEvent('batchedUpdate', data);
    }

    handleUpdateProcessed(data) {
        // Handle processed updates
        this.triggerEvent('updateProcessed', data);
    }

    // UI updates
    updateZoomDisplay() {
        const zoomDisplay = document.getElementById('zoom-display');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${this.viewport.getZoomPercent()}%`;
        }
    }

    updateUIElements() {
        // Update any UI elements that depend on viewport state
        this.updateZoomDisplay();
        this.zoom.updateZoomButtonStates();
    }

    // Operations
    cancelOperations() {
        // Cancel any ongoing operations
        this.camera.stopAnimation();
        this.pan.stopPanInertia();
        this.triggerEvent('operationsCancelled');
    }

    // Public API - delegate to appropriate modules
    getZoom() {
        return this.viewport.getZoom();
    }

    setZoom(zoom) {
        this.zoom.setZoom(zoom);
    }

    zoomIn() {
        this.zoom.zoomIn();
    }

    zoomOut() {
        this.zoom.zoomOut();
    }

    getPan() {
        return this.viewport.getPan();
    }

    setPan(x, y) {
        this.viewport.setPan(x, y);
    }

    resetView() {
        this.camera.resetView();
    }

    fitToView() {
        this.camera.fitToView();
    }

    zoomToSelection(bbox) {
        this.camera.zoomToSelection(bbox);
    }

    // Coordinate conversion
    screenToSVG(screenX, screenY) {
        return this.viewport.screenToSVG(screenX, screenY);
    }

    svgToScreen(svgX, svgY) {
        return this.viewport.svgToScreen(svgX, svgY);
    }

    screenToRealWorld(screenX, screenY) {
        return this.viewport.screenToRealWorld(screenX, screenY);
    }

    realWorldToScreen(realWorldX, realWorldY) {
        return this.viewport.realWorldToScreen(realWorldX, realWorldY);
    }

    // Viewport bounds
    getViewportBounds() {
        return this.viewport.getViewportBounds();
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers) {
            this.eventHandlers = new Map();
        }
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers && this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers && this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, viewportManager: this });
                } catch (error) {
                    console.error(`Error in viewport manager event handler for ${event}:`, error);
                }
            });
        }
    }

    // Module access
    getViewport() {
        return this.viewport;
    }

    getCamera() {
        return this.camera;
    }

    getZoom() {
        return this.zoom;
    }

    getPan() {
        return this.pan;
    }

    // Cleanup
    destroy() {
        this.cancelOperations();
        
        if (this.viewport) {
            this.viewport.destroy();
        }
        if (this.camera) {
            this.camera.destroy();
        }
        if (this.zoom) {
            this.zoom.destroy();
        }
        if (this.pan) {
            this.pan.destroy();
        }
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 