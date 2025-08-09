/**
 * Core Viewport Module
 * Handles basic viewport state and coordinate conversion
 */

export class Viewport {
    constructor(svgElement, options = {}) {
        this.svg = svgElement;
        this.container = svgElement.parentElement;

        // Viewport state
        this.currentZoom = options.initialZoom || 1.0;
        this.panX = options.initialPanX || 0;
        this.panY = options.initialPanY || 0;

        // Zoom constraints
        this.minZoom = options.minZoom || 0.1;
        this.maxZoom = options.maxZoom || 5.0;
        this.zoomStep = options.zoomStep || 0.1;

        // Scale factors for real-world coordinate conversion
        this.scaleFactors = {
            x: 1.0,
            y: 1.0
        };
        this.currentUnit = 'pixels';

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.updateViewport();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Basic event listeners for viewport changes
        window.addEventListener('resize', () => this.handleResize());
    }

    handleResize() {
        this.updateViewport();
        this.triggerEvent('resize');
    }

    // Coordinate conversion methods
    screenToSVG(screenX, screenY) {
        const rect = this.svg.getBoundingClientRect();
        const x = (screenX - rect.left) / this.currentZoom - this.panX;
        const y = (screenY - rect.top) / this.currentZoom - this.panY;
        return { x, y };
    }

    svgToScreen(svgX, svgY) {
        const rect = this.svg.getBoundingClientRect();
        const x = (svgX + this.panX) * this.currentZoom + rect.left;
        const y = (svgY + this.panY) * this.currentZoom + rect.top;
        return { x, y };
    }

    // Real-world coordinate conversion
    screenToRealWorld(screenX, screenY) {
        const svgCoords = this.screenToSVG(screenX, screenY);
        return this.svgToRealWorld(svgCoords.x, svgCoords.y);
    }

    realWorldToScreen(realWorldX, realWorldY) {
        const svgCoords = this.realWorldToSVG(realWorldX, realWorldY);
        return this.svgToScreen(svgCoords.x, svgCoords.y);
    }

    svgToRealWorld(svgX, svgY) {
        return {
            x: svgX * this.scaleFactors.x,
            y: svgY * this.scaleFactors.y
        };
    }

    realWorldToSVG(realWorldX, realWorldY) {
        return {
            x: realWorldX / this.scaleFactors.x,
            y: realWorldY / this.scaleFactors.y
        };
    }

    // Viewport state methods
    getViewportTransform() {
        return {
            zoom: this.currentZoom,
            panX: this.panX,
            panY: this.panY
        };
    }

    updateViewport() {
        if (!this.svg) return;

        const transform = `translate(${this.panX}, ${this.panY}) scale(${this.currentZoom})`;
        this.svg.style.transform = transform;

        this.triggerEvent('viewportChanged');
    }

    // Zoom methods
    getZoom() {
        return this.currentZoom;
    }

    setZoom(zoom) {
        this.currentZoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
        this.updateViewport();
        this.triggerEvent('zoomChanged');
    }

    zoomIn() {
        this.setZoom(this.currentZoom + this.zoomStep);
    }

    zoomOut() {
        this.setZoom(this.currentZoom - this.zoomStep);
    }

    // Pan methods
    getPan() {
        return { x: this.panX, y: this.panY };
    }

    setPan(x, y) {
        this.panX = x;
        this.panY = y;
        this.updateViewport();
        this.triggerEvent('panChanged');
    }

    // Scale factor methods
    setScaleFactors(scaleX, scaleY, unit = 'pixels') {
        this.scaleFactors.x = scaleX;
        this.scaleFactors.y = scaleY;
        this.currentUnit = unit;
        this.triggerEvent('scaleFactorsChanged');
    }

    getScaleFactors() {
        return {
            x: this.scaleFactors.x,
            y: this.scaleFactors.y,
            unit: this.currentUnit
        };
    }

    // Utility methods
    getViewportBounds() {
        const rect = this.svg.getBoundingClientRect();
        const topLeft = this.screenToSVG(rect.left, rect.top);
        const bottomRight = this.screenToSVG(rect.right, rect.bottom);

        return {
            left: topLeft.x,
            top: topLeft.y,
            right: bottomRight.x,
            bottom: bottomRight.y,
            width: bottomRight.x - topLeft.x,
            height: bottomRight.y - topLeft.y
        };
    }

    getZoomPercent() {
        return Math.round(this.currentZoom * 100);
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
                    handler({ ...data, viewport: this });
                } catch (error) {
                    console.error(`Error in viewport event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.eventHandlers.clear();
    }
}
