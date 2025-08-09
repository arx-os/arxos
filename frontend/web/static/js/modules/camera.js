/**
 * Camera Module
 * Handles camera controls, animations, and smooth transitions
 */

export class Camera {
    constructor(viewport, options = {}) {
        this.viewport = viewport;

        // Animation settings
        this.animationDuration = options.animationDuration || 300;
        this.easingFunction = options.easingFunction || this.easeInOutCubic;

        // Animation state
        this.isAnimating = false;
        this.targetZoom = null;
        this.targetPanX = null;
        this.targetPanY = null;
        this.animationStartTime = null;
        this.animationStartZoom = null;
        this.animationStartPanX = null;
        this.animationStartPanY = null;

        // Camera constraints
        this.panBoundaries = options.panBoundaries || {
            enabled: true,
            padding: 100,
            maxDistance: 2000
        };

        this.initialize();
    }

    initialize() {
        // Listen for viewport changes
        this.viewport.addEventListener('viewportChanged', () => {
            this.updateCameraState();
        });
    }

    // Smooth zoom to a specific point
    zoomAtPoint(zoomFactor, centerX = null, centerY = null, smooth = true) {
        const currentZoom = this.viewport.getZoom();
        const newZoom = Math.max(
            this.viewport.getMinZoom(),
            Math.min(this.viewport.getMaxZoom(), currentZoom * zoomFactor)
        );

        if (smooth) {
            this.smoothZoomTo(newZoom, centerX, centerY);
        } else {
            this.applyZoomAtPoint(newZoom, centerX, centerY);
        }
    }

    // Smooth zoom to target values
    smoothZoomTo(targetZoom, targetPanX = null, targetPanY = null) {
        if (this.isAnimating) {
            this.stopAnimation();
        }

        this.targetZoom = targetZoom;
        this.targetPanX = targetPanX !== null ? targetPanX : this.viewport.getPan().x;
        this.targetPanY = targetPanY !== null ? targetPanY : this.viewport.getPan().y;

        this.startAnimation();
    }

    // Apply zoom at a specific point
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

        // Apply constraints
        const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);

        this.viewport.setZoom(zoom);
        this.viewport.setPan(constrainedPan.x, constrainedPan.y);
    }

    // Start smooth animation
    startAnimation() {
        if (this.isAnimating) return;

        this.isAnimating = true;
        this.animationStartTime = performance.now();
        this.animationStartZoom = this.viewport.getZoom();
        this.animationStartPanX = this.viewport.getPan().x;
        this.animationStartPanY = this.viewport.getPan().y;

        this.animate();
    }

    // Animation loop
    animate() {
        if (!this.isAnimating) return;

        const currentTime = performance.now();
        const elapsed = currentTime - this.animationStartTime;
        const progress = Math.min(elapsed / this.animationDuration, 1);
        const easedProgress = this.easingFunction(progress);

        // Interpolate values
        const currentZoom = this.animationStartZoom + (this.targetZoom - this.animationStartZoom) * easedProgress;
        const currentPanX = this.animationStartPanX + (this.targetPanX - this.animationStartPanX) * easedProgress;
        const currentPanY = this.animationStartPanY + (this.targetPanY - this.animationStartPanY) * easedProgress;

        // Apply constraints
        const constrainedPan = this.applyPanBoundaries(currentPanX, currentPanY);

        // Update viewport
        this.viewport.setZoom(currentZoom);
        this.viewport.setPan(constrainedPan.x, constrainedPan.y);

        if (progress < 1) {
            requestAnimationFrame(() => this.animate());
        } else {
            this.stopAnimation();
        }
    }

    // Stop animation
    stopAnimation() {
        this.isAnimating = false;
        this.targetZoom = null;
        this.targetPanX = null;
        this.targetPanY = null;
    }

    // Easing function
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
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

    // Camera controls
    resetView() {
        this.smoothZoomTo(1.0, 0, 0);
    }

    fitToView() {
        // Calculate the bounding box of all visible objects
        const svg = this.viewport.svg;
        const bbox = svg.getBBox();

        if (bbox.width === 0 || bbox.height === 0) {
            return;
        }

        const containerRect = this.viewport.container.getBoundingClientRect();
        const scaleX = containerRect.width / bbox.width;
        const scaleY = containerRect.height / bbox.height;
        const scale = Math.min(scaleX, scaleY) * 0.9; // 10% margin

        const centerX = bbox.x + bbox.width / 2;
        const centerY = bbox.y + bbox.height / 2;

        this.smoothZoomTo(scale, -centerX, -centerY);
    }

    zoomToFullExtent() {
        this.fitToView();
    }

    zoomToSelection(bbox) {
        if (!bbox || bbox.width === 0 || bbox.height === 0) {
            return;
        }

        const containerRect = this.viewport.container.getBoundingClientRect();
        const scaleX = containerRect.width / bbox.width;
        const scaleY = containerRect.height / bbox.height;
        const scale = Math.min(scaleX, scaleY) * 0.9; // 10% margin

        const centerX = bbox.x + bbox.width / 2;
        const centerY = bbox.y + bbox.height / 2;

        this.smoothZoomTo(scale, -centerX, -centerY);
    }

    // Camera state management
    updateCameraState() {
        // Update any camera-specific state when viewport changes
        this.triggerEvent('cameraStateChanged');
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
                    handler({ ...data, camera: this });
                } catch (error) {
                    console.error(`Error in camera event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.stopAnimation();
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
