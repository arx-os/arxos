// Symbol Scaler Module for Dynamic Sizing and Zoom-Aware Rendering

class SymbolScaler {
    constructor() {
        this.baseSize = 20; // Base size for symbols in pixels
        this.minSize = 8;   // Minimum symbol size
        this.maxSize = 100; // Maximum symbol size
        this.scaleFactors = {
            tiny: 0.5,
            small: 0.75,
            normal: 1.0,
            large: 1.5,
            huge: 2.0
        };
        this.zoomThresholds = {
            min: 0.1,
            max: 10.0
        };
        this.viewportManager = null;
        this.scaleCache = new Map();
        this.init();
    }

    init() {
        this.connectToViewportManager();
        this.setupEventListeners();
    }

    /**
     * Connect to the viewport manager for zoom awareness
     */
    connectToViewportManager() {
        const checkViewportManager = () => {
            if (window.viewportManager) {
                this.viewportManager = window.viewportManager;
                window.arxLogger.info('SymbolScaler connected to ViewportManager', { file: 'symbol_scaler.js' });

                // Listen for zoom changes
                this.viewportManager.addEventListener('zoomChanged', () => {
                    this.updateAllSymbolScales();
                });

                this.viewportManager.addEventListener('viewReset', () => {
                    this.updateAllSymbolScales();
                });
            } else {
                setTimeout(checkViewportManager, 100);
            }
        };
        checkViewportManager();
    }

    /**
     * Setup event listeners for scaling controls
     */
    setupEventListeners() {
        // Listen for symbol scale changes
        document.addEventListener('symbolScaleChanged', (e) => {
            this.updateSymbolScale(e.detail.symbolId, e.detail.scale);
        });

        // Listen for global scale changes
        document.addEventListener('globalScaleChanged', (e) => {
            this.updateGlobalScale(e.detail.scale);
        });
    }

    /**
     * Calculate optimal symbol size based on zoom level
     */
    calculateOptimalSize(zoomLevel = 1.0, baseScale = 1.0) {
        // Clamp zoom level to reasonable bounds
        const clampedZoom = Math.max(this.zoomThresholds.min,
                                   Math.min(this.zoomThresholds.max, zoomLevel));

        // Calculate size that maintains visual consistency across zoom levels
        const optimalSize = this.baseSize * baseScale / clampedZoom;

        // Clamp to min/max bounds
        return Math.max(this.minSize, Math.min(this.maxSize, optimalSize));
    }

    /**
     * Get scale factor for a specific zoom level
     */
    getScaleFactor(zoomLevel, baseScale = 1.0) {
        const cacheKey = `${zoomLevel}_${baseScale}`;

        if (this.scaleCache.has(cacheKey)) {
            return this.scaleCache.get(cacheKey);
        }

        const optimalSize = this.calculateOptimalSize(zoomLevel, baseScale);
        const scaleFactor = optimalSize / this.baseSize;

        // Cache the result
        this.scaleCache.set(cacheKey, scaleFactor);

        // Limit cache size
        if (this.scaleCache.size > 1000) {
            const firstKey = this.scaleCache.keys().next().value;
            this.scaleCache.delete(firstKey);
        }

        return scaleFactor;
    }

    /**
     * Scale a symbol element
     */
    scaleSymbol(symbolElement, scaleFactor, options = {}) {
        if (!symbolElement) return;

        const {
            maintainAspectRatio = true,
            centerTransform = true,
            animate = false
        } = options;

        // Get current transform
        const currentTransform = symbolElement.getAttribute('transform') || '';
        const x = parseFloat(symbolElement.getAttribute('data-x')) || 0;
        const y = parseFloat(symbolElement.getAttribute('data-y')) || 0;
        const rotation = parseFloat(symbolElement.getAttribute('data-rotation')) || 0;

        // Calculate new transform
        let newTransform = '';

        if (centerTransform) {
            // Apply scale from center
            newTransform = `translate(${x},${y}) scale(${scaleFactor}) rotate(${rotation})`;
        } else {
            // Apply scale from origin
            newTransform = `translate(${x},${y}) rotate(${rotation}) scale(${scaleFactor})`;
        }

        // Apply transform with optional animation
        if (animate) {
            symbolElement.style.transition = 'transform 0.3s ease';
            symbolElement.setAttribute('transform', newTransform);
            setTimeout(() => {
                symbolElement.style.transition = '';
            }, 300);
        } else {
            symbolElement.setAttribute('transform', newTransform);
        }

        // Store scale factor for future reference
        symbolElement.setAttribute('data-scale', scaleFactor);

        // Update symbol size attribute
        const newSize = this.baseSize * scaleFactor;
        symbolElement.setAttribute('data-size', newSize);

        // Trigger scale change event
        this.triggerScaleChangeEvent(symbolElement, scaleFactor);
    }

    /**
     * Update symbol scale based on current zoom level
     */
    updateSymbolScale(symbolElement, baseScale = 1.0) {
        if (!symbolElement || !this.viewportManager) return;

        const zoomLevel = this.viewportManager.currentZoom || 1.0;
        const scaleFactor = this.getScaleFactor(zoomLevel, baseScale);

        this.scaleSymbol(symbolElement, scaleFactor, {
            animate: true,
            centerTransform: true
        });
    }

    /**
     * Update all placed symbols with current zoom level
     */
    updateAllSymbolScales() {
        if (!this.viewportManager) return;

        const placedSymbols = document.querySelectorAll('.placed-symbol');
        const zoomLevel = this.viewportManager.currentZoom || 1.0;

        placedSymbols.forEach(symbol => {
            const baseScale = parseFloat(symbol.getAttribute('data-base-scale')) || 1.0;
            this.updateSymbolScale(symbol, baseScale);
        });
    }

    /**
     * Set base scale for a symbol (independent of zoom)
     */
    setBaseScale(symbolElement, baseScale) {
        if (!symbolElement) return;

        symbolElement.setAttribute('data-base-scale', baseScale);
        this.updateSymbolScale(symbolElement, baseScale);
    }

    /**
     * Get current scale of a symbol
     */
    getCurrentScale(symbolElement) {
        if (!symbolElement) return 1.0;

        return parseFloat(symbolElement.getAttribute('data-scale')) || 1.0;
    }

    /**
     * Get base scale of a symbol
     */
    getBaseScale(symbolElement) {
        if (!symbolElement) return 1.0;

        return parseFloat(symbolElement.getAttribute('data-base-scale')) || 1.0;
    }

    /**
     * Scale symbol preview in library
     */
    scaleSymbolPreview(previewElement, scaleFactor, options = {}) {
        if (!previewElement) return;

        const {
            maintainAspectRatio = true,
            animate = false
        } = options;

        const svg = previewElement.querySelector('svg');
        if (!svg) return;

        const currentWidth = parseFloat(svg.getAttribute('width')) || 32;
        const currentHeight = parseFloat(svg.getAttribute('height')) || 32;

        const newWidth = currentWidth * scaleFactor;
        const newHeight = maintainAspectRatio ? currentHeight * scaleFactor : currentHeight;

        if (animate) {
            svg.style.transition = 'width 0.3s ease, height 0.3s ease';
        }

        svg.setAttribute('width', newWidth);
        svg.setAttribute('height', newHeight);

        if (animate) {
            setTimeout(() => {
                svg.style.transition = '';
            }, 300);
        }

        // Store scale for reference
        previewElement.setAttribute('data-scale', scaleFactor);
    }

    /**
     * Update all symbol previews in library
     */
    updateSymbolPreviews() {
        if (!this.viewportManager) return;

        const previews = document.querySelectorAll('.symbol-preview');
        const zoomLevel = this.viewportManager.currentZoom || 1.0;

        previews.forEach(preview => {
            const baseScale = parseFloat(preview.getAttribute('data-base-scale')) || 1.0;
            const scaleFactor = this.getScaleFactor(zoomLevel, baseScale);
            this.scaleSymbolPreview(preview, scaleFactor, { animate: true });
        });
    }

    /**
     * Create scaled symbol element for placement
     */
    createScaledSymbol(symbol, x, y, baseScale = 1.0) {
        const zoomLevel = this.viewportManager ? this.viewportManager.currentZoom || 1.0 : 1.0;
        const scaleFactor = this.getScaleFactor(zoomLevel, baseScale);

        // Create symbol group
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.classList.add('placed-symbol');
        g.setAttribute('data-x', x);
        g.setAttribute('data-y', y);
        g.setAttribute('data-rotation', '0');
        g.setAttribute('data-base-scale', baseScale);
        g.setAttribute('data-scale', scaleFactor);
        g.setAttribute('data-size', this.baseSize * scaleFactor);

        // Create SVG element with proper scaling
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        const size = this.baseSize * scaleFactor;
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', '0 0 20 20');
        svg.innerHTML = symbol.svg || '';

        g.appendChild(svg);

        // Apply transform
        const transform = `translate(${x},${y}) scale(${scaleFactor})`;
        g.setAttribute('transform', transform);

        return g;
    }

    /**
     * Test symbol scaling consistency across zoom levels
     */
    testSymbolScaling() {
        if (!this.viewportManager) {
            console.warn('Viewport manager not available for scaling test');
            return;
        }

        console.log('=== Testing Symbol Scaling Consistency ===');

        const testZoomLevels = [0.25, 0.5, 1.0, 2.0, 4.0];
        const testBaseScales = [0.5, 1.0, 1.5, 2.0];

        testZoomLevels.forEach(zoomLevel => {
            console.log(`\n--- Testing at Zoom Level ${zoomLevel} ---`);

            testBaseScales.forEach(baseScale => {
                const scaleFactor = this.getScaleFactor(zoomLevel, baseScale);
                const actualSize = this.baseSize * scaleFactor;

                console.log(`  Base Scale ${baseScale}:`);
                console.log(`    Scale Factor: ${scaleFactor.toFixed(3)}`);
                console.log(`    Actual Size: ${actualSize.toFixed(1)}px`);
                console.log(`    Optimal Size: ${this.calculateOptimalSize(zoomLevel, baseScale).toFixed(1)}px`);
            });
        });

        console.log('\nScaling test complete!');
    }

    /**
     * Get scaling statistics for performance monitoring
     */
    getScalingStats() {
        const placedSymbols = document.querySelectorAll('.placed-symbol');
        const stats = {
            totalSymbols: placedSymbols.length,
            averageScale: 0,
            minScale: Infinity,
            maxScale: -Infinity,
            scaleDistribution: {}
        };

        let totalScale = 0;

        placedSymbols.forEach(symbol => {
            const scale = this.getCurrentScale(symbol);
            totalScale += scale;

            stats.minScale = Math.min(stats.minScale, scale);
            stats.maxScale = Math.max(stats.maxScale, scale);

            // Categorize scale ranges
            const scaleRange = scale < 0.5 ? 'tiny' :
                             scale < 0.75 ? 'small' :
                             scale < 1.25 ? 'normal' :
                             scale < 1.75 ? 'large' : 'huge';

            stats.scaleDistribution[scaleRange] = (stats.scaleDistribution[scaleRange] || 0) + 1;
        });

        if (placedSymbols.length > 0) {
            stats.averageScale = totalScale / placedSymbols.length;
        }

        return stats;
    }

    /**
     * Trigger scale change event
     */
    triggerScaleChangeEvent(symbolElement, scaleFactor) {
        const event = new CustomEvent('symbolScaleChanged', {
            detail: {
                symbolId: symbolElement.getAttribute('data-id'),
                scale: scaleFactor,
                element: symbolElement
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * Clear scale cache
     */
    clearScaleCache() {
        this.scaleCache.clear();
        console.log('Symbol scale cache cleared');
    }

    /**
     * Reset all symbols to default scaling
     */
    resetAllScales() {
        const placedSymbols = document.querySelectorAll('.placed-symbol');
        placedSymbols.forEach(symbol => {
            this.setBaseScale(symbol, 1.0);
        });

        console.log('All symbol scales reset to default');
    }
}

// Initialize symbol scaler when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.symbolScaler = new SymbolScaler();
});
