/**
 * Zoom Module
 * Handles zoom controls, wheel events, and zoom constraints
 */

export class Zoom {
    constructor(viewport, options = {}) {
        this.viewport = viewport;
        
        // Zoom settings
        this.minZoom = options.minZoom || 0.1;
        this.maxZoom = options.maxZoom || 5.0;
        this.zoomStep = options.zoomStep || 0.1;
        
        // Mouse wheel zoom settings
        this.wheelZoomSpeed = options.wheelZoomSpeed || 0.001;
        this.wheelZoomSmooth = options.wheelZoomSmooth !== false; // Default to true
        this.wheelZoomDuration = options.wheelZoomDuration || 150;
        
        // Zoom history for undo/redo
        this.zoomHistory = [];
        this.maxHistorySize = options.maxHistorySize || 50;
        this.historyIndex = -1;
        
        // Zoom feedback
        this.zoomFeedbackElement = null;
        this.zoomFeedbackTimeout = null;
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createZoomFeedback();
    }

    setupEventListeners() {
        // Mouse wheel zoom
        this.viewport.svg.addEventListener('wheel', (e) => this.handleWheel(e));
        
        // Keyboard zoom
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    handleWheel(event) {
        event.preventDefault();
        
        const delta = event.deltaY;
        const zoomFactor = delta > 0 ? 0.9 : 1.1;
        
        // Get mouse position relative to SVG
        const rect = this.viewport.svg.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;
        
        // Convert to SVG coordinates
        const svgCoords = this.viewport.screenToSVG(mouseX, mouseY);
        
        // Apply zoom at mouse position
        this.zoomAtPoint(zoomFactor, svgCoords.x, svgCoords.y, this.wheelZoomSmooth);
        
        // Show zoom feedback
        this.showZoomFeedback(event);
    }

    handleKeyDown(event) {
        // Zoom in/out with keyboard
        if (event.key === '+' || event.key === '=') {
            event.preventDefault();
            this.zoomIn();
        } else if (event.key === '-') {
            event.preventDefault();
            this.zoomOut();
        } else if (event.key === '0') {
            event.preventDefault();
            this.resetZoom();
        }
    }

    // Zoom controls
    zoomIn() {
        const currentZoom = this.viewport.getZoom();
        const newZoom = Math.min(this.maxZoom, currentZoom + this.zoomStep);
        this.setZoom(newZoom);
    }

    zoomOut() {
        const currentZoom = this.viewport.getZoom();
        const newZoom = Math.max(this.minZoom, currentZoom - this.zoomStep);
        this.setZoom(newZoom);
    }

    zoomAtPoint(zoomFactor, centerX = null, centerY = null, smooth = false) {
        const currentZoom = this.viewport.getZoom();
        const newZoom = Math.max(
            this.minZoom,
            Math.min(this.maxZoom, currentZoom * zoomFactor)
        );

        if (smooth) {
            // Use camera for smooth zoom
            if (this.viewport.camera) {
                this.viewport.camera.zoomAtPoint(zoomFactor, centerX, centerY, true);
            } else {
                this.applyZoomAtPoint(newZoom, centerX, centerY);
            }
        } else {
            this.applyZoomAtPoint(newZoom, centerX, centerY);
        }
    }

    applyZoomAtPoint(zoom, centerX, centerY) {
        const currentPan = this.viewport.getPan();
        const currentZoom = this.viewport.getZoom();

        if (centerX === null || centerY === null) {
            // Zoom at viewport center
            const bounds = this.viewport.getViewportBounds();
            centerX = (bounds.left + bounds.right) / 2;
            centerY = (bounds.top + bounds.bottom) / 2;
        }

        // Calculate new pan to keep the center point fixed
        const zoomRatio = zoom / currentZoom;
        const newPanX = centerX - (centerX - currentPan.x) * zoomRatio;
        const newPanY = centerY - (centerY - currentPan.y) * zoomRatio;

        this.setZoom(zoom);
        this.viewport.setPan(newPanX, newPanY);
    }

    setZoom(zoom) {
        const constrainedZoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
        
        // Save to history before changing
        this.saveZoomState();
        
        this.viewport.setZoom(constrainedZoom);
        
        // Update zoom button states
        this.updateZoomButtonStates();
    }

    resetZoom() {
        this.setZoom(1.0);
    }

    // Zoom history
    saveZoomState() {
        const currentState = {
            zoom: this.viewport.getZoom(),
            panX: this.viewport.getPan().x,
            panY: this.viewport.getPan().y,
            timestamp: Date.now()
        };

        // Remove any states after current index
        this.zoomHistory = this.zoomHistory.slice(0, this.historyIndex + 1);
        
        // Add new state
        this.zoomHistory.push(currentState);
        
        // Limit history size
        if (this.zoomHistory.length > this.maxHistorySize) {
            this.zoomHistory.shift();
        }
        
        this.historyIndex = this.zoomHistory.length - 1;
    }

    undoZoom() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.restoreZoomState(this.zoomHistory[this.historyIndex]);
        }
    }

    redoZoom() {
        if (this.historyIndex < this.zoomHistory.length - 1) {
            this.historyIndex++;
            this.restoreZoomState(this.zoomHistory[this.historyIndex]);
        }
    }

    restoreZoomState(state) {
        if (!state) return;
        
        this.viewport.setZoom(state.zoom);
        this.viewport.setPan(state.panX, state.panY);
        this.updateZoomButtonStates();
    }

    // Zoom feedback
    showZoomFeedback(event) {
        if (!this.zoomFeedbackElement) return;

        const zoomPercent = this.viewport.getZoomPercent();
        this.zoomFeedbackElement.textContent = `${zoomPercent}%`;
        this.zoomFeedbackElement.style.display = 'block';

        // Position feedback near mouse
        const rect = this.viewport.svg.getBoundingClientRect();
        this.zoomFeedbackElement.style.left = `${event.clientX - rect.left + 10}px`;
        this.zoomFeedbackElement.style.top = `${event.clientY - rect.top - 30}px`;

        // Clear previous timeout
        if (this.zoomFeedbackTimeout) {
            clearTimeout(this.zoomFeedbackTimeout);
        }

        // Hide after delay
        this.zoomFeedbackTimeout = setTimeout(() => {
            if (this.zoomFeedbackElement) {
                this.zoomFeedbackElement.style.display = 'none';
            }
        }, 1000);
    }

    createZoomFeedback() {
        this.zoomFeedbackElement = document.createElement('div');
        this.zoomFeedbackElement.className = 'zoom-feedback';
        this.zoomFeedbackElement.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            display: none;
        `;
        
        this.viewport.container.appendChild(this.zoomFeedbackElement);
    }

    // Zoom constraints
    isAtZoomConstraint() {
        const zoom = this.viewport.getZoom();
        return zoom <= this.minZoom || zoom >= this.maxZoom;
    }

    getZoomConstraintMessage() {
        const zoom = this.viewport.getZoom();
        if (zoom <= this.minZoom) {
            return 'Minimum zoom reached';
        } else if (zoom >= this.maxZoom) {
            return 'Maximum zoom reached';
        }
        return null;
    }

    // UI updates
    updateZoomButtonStates() {
        const zoom = this.viewport.getZoom();
        const zoomInButton = document.getElementById('zoom-in-btn');
        const zoomOutButton = document.getElementById('zoom-out-btn');
        const resetZoomButton = document.getElementById('reset-zoom-btn');

        if (zoomInButton) {
            zoomInButton.disabled = zoom >= this.maxZoom;
        }
        if (zoomOutButton) {
            zoomOutButton.disabled = zoom <= this.minZoom;
        }
        if (resetZoomButton) {
            resetZoomButton.disabled = zoom === 1.0;
        }
    }

    // Utility methods
    getZoomPercent() {
        return this.viewport.getZoomPercent();
    }

    setZoomPercent(percent) {
        this.setZoom(percent / 100);
    }

    getMinZoom() {
        return this.minZoom;
    }

    getMaxZoom() {
        return this.maxZoom;
    }

    // Cleanup
    destroy() {
        if (this.zoomFeedbackTimeout) {
            clearTimeout(this.zoomFeedbackTimeout);
        }
        if (this.zoomFeedbackElement) {
            this.zoomFeedbackElement.remove();
        }
    }
} 