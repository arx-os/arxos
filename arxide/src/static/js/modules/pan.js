/**
 * Pan Module
 * Handles panning controls, mouse events, and pan constraints
 */

export class Pan {
    constructor(viewport, options = {}) {
        this.viewport = viewport;
        
        // Pan settings
        this.panEnabled = options.panEnabled !== false; // Default to true
        this.panInertia = options.panInertia !== false; // Default to true
        this.panInertiaDecay = options.panInertiaDecay || 0.95; // Decay factor for inertia
        this.panInertiaDuration = options.panInertiaDuration || 300; // Inertia duration in ms
        this.panBoundaries = options.panBoundaries || {
            enabled: true,
            padding: 100, // Padding from edges
            maxDistance: 2000 // Maximum pan distance from center
        };
        
        // Pan state
        this.isPanning = false;
        this.panStartX = 0;
        this.panStartY = 0;
        this.panStartViewX = 0;
        this.panStartViewY = 0;
        this.panVelocityX = 0;
        this.panVelocityY = 0;
        this.panInertiaAnimation = null;
        this.hasShownPanIndicator = false;
        this.lastPanTime = null;
        
        // Pan feedback
        this.panFeedbackElement = null;
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createPanFeedback();
    }

    setupEventListeners() {
        // Mouse pan events
        this.viewport.svg.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.viewport.svg.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.viewport.svg.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Keyboard pan events
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    handleMouseDown(event) {
        if (!this.panEnabled || event.button !== 0) return; // Left mouse button only
        
        event.preventDefault();
        this.startPan(event);
    }

    handleMouseMove(event) {
        if (!this.isPanning) return;
        
        event.preventDefault();
        
        const currentTime = performance.now();
        const deltaTime = this.lastPanTime ? currentTime - this.lastPanTime : 0;
        this.lastPanTime = currentTime;
        
        // Calculate pan delta
        const deltaX = event.clientX - this.panStartX;
        const deltaY = event.clientY - this.panStartY;
        
        // Convert to viewport coordinates
        const currentZoom = this.viewport.getZoom();
        const viewDeltaX = deltaX / currentZoom;
        const viewDeltaY = deltaY / currentZoom;
        
        // Calculate new pan position
        const newPanX = this.panStartViewX - viewDeltaX;
        const newPanY = this.panStartViewY - viewDeltaY;
        
        // Apply boundaries
        const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);
        
        // Update viewport
        this.viewport.setPan(constrainedPan.x, constrainedPan.y);
        
        // Calculate velocity for inertia
        if (deltaTime > 0) {
            this.panVelocityX = viewDeltaX / deltaTime;
            this.panVelocityY = viewDeltaY / deltaTime;
        }
        
        // Show pan feedback
        this.showPanFeedback();
    }

    handleMouseUp(event) {
        if (!this.isPanning) return;
        
        event.preventDefault();
        this.endPan();
    }

    handleKeyDown(event) {
        if (!this.panEnabled) return;
        
        const panStep = 50;
        const currentPan = this.viewport.getPan();
        let newPanX = currentPan.x;
        let newPanY = currentPan.y;
        
        switch (event.key) {
            case 'ArrowLeft':
                event.preventDefault();
                newPanX -= panStep;
                break;
            case 'ArrowRight':
                event.preventDefault();
                newPanX += panStep;
                break;
            case 'ArrowUp':
                event.preventDefault();
                newPanY -= panStep;
                break;
            case 'ArrowDown':
                event.preventDefault();
                newPanY += panStep;
                break;
            case 'Home':
                event.preventDefault();
                this.resetPan();
                return;
        }
        
        // Apply boundaries
        const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);
        this.viewport.setPan(constrainedPan.x, constrainedPan.y);
    }

    startPan(event) {
        this.isPanning = true;
        this.panStartX = event.clientX;
        this.panStartY = event.clientY;
        this.panStartViewX = this.viewport.getPan().x;
        this.panStartViewY = this.viewport.getPan().y;
        this.panVelocityX = 0;
        this.panVelocityY = 0;
        this.lastPanTime = performance.now();
        
        // Change cursor
        this.viewport.svg.style.cursor = 'grabbing';
        
        // Show pan indicator
        this.showPanIndicator();
    }

    endPan() {
        this.isPanning = false;
        this.viewport.svg.style.cursor = 'grab';
        
        // Start inertia if enabled
        if (this.panInertia && (Math.abs(this.panVelocityX) > 0.1 || Math.abs(this.panVelocityY) > 0.1)) {
            this.startPanInertia();
        }
        
        // Hide pan feedback
        this.hidePanFeedback();
    }

    startPanInertia() {
        if (this.panInertiaAnimation) {
            cancelAnimationFrame(this.panInertiaAnimation);
        }
        
        const startTime = performance.now();
        const startVelocityX = this.panVelocityX;
        const startVelocityY = this.panVelocityY;
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / this.panInertiaDuration, 1);
            
            // Apply decay
            const decay = Math.pow(this.panInertiaDecay, progress);
            const currentVelocityX = startVelocityX * decay;
            const currentVelocityY = startVelocityY * decay;
            
            // Update pan position
            const currentPan = this.viewport.getPan();
            const newPanX = currentPan.x - currentVelocityX * 16; // 60fps
            const newPanY = currentPan.y - currentVelocityY * 16;
            
            // Apply boundaries
            const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);
            this.viewport.setPan(constrainedPan.x, constrainedPan.y);
            
            // Continue animation if velocity is significant
            if (progress < 1 && (Math.abs(currentVelocityX) > 0.01 || Math.abs(currentVelocityY) > 0.01)) {
                this.panInertiaAnimation = requestAnimationFrame(animate);
            } else {
                this.stopPanInertia();
            }
        };
        
        this.panInertiaAnimation = requestAnimationFrame(animate);
    }

    stopPanInertia() {
        if (this.panInertiaAnimation) {
            cancelAnimationFrame(this.panInertiaAnimation);
            this.panInertiaAnimation = null;
        }
    }

    // Pan boundaries
    applyPanBoundaries(panX, panY) {
        if (!this.panBoundaries.enabled) {
            return { x: panX, y: panY };
        }

        const bounds = this.viewport.getViewportBounds();
        const maxDistance = this.panBoundaries.maxDistance;
        const padding = this.panBoundaries.padding;

        // Calculate boundaries
        const minX = -bounds.width + padding;
        const maxX = bounds.width - padding;
        const minY = -bounds.height + padding;
        const maxY = bounds.height - padding;

        // Apply distance constraint
        const distance = Math.sqrt(panX * panX + panY * panY);
        if (distance > maxDistance) {
            const scale = maxDistance / distance;
            panX *= scale;
            panY *= scale;
        }

        return {
            x: Math.max(minX, Math.min(maxX, panX)),
            y: Math.max(minY, Math.min(maxY, panY))
        };
    }

    // Pan controls
    resetPan() {
        this.viewport.setPan(0, 0);
    }

    enablePan() {
        this.panEnabled = true;
        this.viewport.svg.style.cursor = 'grab';
    }

    disablePan() {
        this.panEnabled = false;
        this.viewport.svg.style.cursor = 'default';
        if (this.isPanning) {
            this.endPan();
        }
    }

    togglePan() {
        if (this.panEnabled) {
            this.disablePan();
        } else {
            this.enablePan();
        }
    }

    isPanEnabled() {
        return this.panEnabled;
    }

    setPanBoundaries(boundaries) {
        this.panBoundaries = { ...this.panBoundaries, ...boundaries };
    }

    getPanBoundaries() {
        return { ...this.panBoundaries };
    }

    // Pan feedback
    showPanFeedback() {
        if (!this.panFeedbackElement) return;
        
        this.panFeedbackElement.style.display = 'block';
        this.panFeedbackElement.textContent = 'Panning';
    }

    hidePanFeedback() {
        if (!this.panFeedbackElement) return;
        
        this.panFeedbackElement.style.display = 'none';
    }

    showPanIndicator() {
        if (this.hasShownPanIndicator) return;
        
        this.hasShownPanIndicator = true;
        // Could show a tooltip or notification here
    }

    createPanFeedback() {
        this.panFeedbackElement = document.createElement('div');
        this.panFeedbackElement.className = 'pan-feedback';
        this.panFeedbackElement.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            display: none;
            top: 10px;
            left: 10px;
        `;
        
        this.viewport.container.appendChild(this.panFeedbackElement);
    }

    // Utility methods
    isAtPanBoundary() {
        const pan = this.viewport.getPan();
        const bounds = this.viewport.getViewportBounds();
        const padding = this.panBoundaries.padding;
        
        return (
            pan.x <= -bounds.width + padding ||
            pan.x >= bounds.width - padding ||
            pan.y <= -bounds.height + padding ||
            pan.y >= bounds.height - padding
        );
    }

    // Cleanup
    destroy() {
        this.stopPanInertia();
        if (this.panFeedbackElement) {
            this.panFeedbackElement.remove();
        }
    }
} 