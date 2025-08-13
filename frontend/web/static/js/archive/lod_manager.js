/**
 * Level of Detail (LOD) Manager for SVG-BIM System
 * Optimizes rendering performance by showing simplified symbol versions at different zoom levels
 */

class LODManager {
    constructor(options = {}) {
        // LOD configuration
        this.lodLevels = options.lodLevels || {
            high: { minZoom: 2.0, complexity: 1.0, name: 'High Detail' },
            medium: { minZoom: 0.5, complexity: 0.7, name: 'Medium Detail' },
            low: { minZoom: 0.1, complexity: 0.4, name: 'Low Detail' },
            minimal: { minZoom: 0.0, complexity: 0.2, name: 'Minimal Detail' }
        };

        // Performance settings
        this.switchThreshold = options.switchThreshold || 0.1; // Zoom level difference for switching
        this.transitionDuration = options.transitionDuration || 200; // ms for LOD transitions
        this.enableTransitions = options.enableTransitions !== false; // Default to true

        // State management
        this.currentLODLevel = 'medium';
        this.lastZoomLevel = 1.0;
        this.switchingLOD = false;
        this.lodCache = new Map();
        this.symbolLODData = new Map();

        // Performance tracking
        this.lodStats = {
            totalSwitches: 0,
            lastSwitchTime: 0,
            averageSwitchTime: 0,
            switchTimes: []
        };

        // Event handlers
        this.eventHandlers = new Map();

        // References to other components
        this.viewportManager = null;
        this.symbolScaler = null;

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the LOD manager
     */
    initialize() {
        this.connectToViewportManager();
        this.connectToSymbolScaler();
        console.log('LODManager initialized');
    }

    /**
     * Connect to viewport manager for zoom awareness
     */
    connectToViewportManager() {
        const checkViewportManager = () => {
            if (window.viewportManager) {
                this.viewportManager = window.viewportManager;
                console.log('LODManager connected to ViewportManager');

                // Listen for zoom changes
                this.viewportManager.addEventListener('zoomChanged', (data) => {
                    this.handleZoomChange(data.zoom);
                });

                this.viewportManager.addEventListener('viewReset', () => {
                    this.handleZoomChange(this.viewportManager.currentZoom);
                });
            } else {
                setTimeout(checkViewportManager, 100);
            }
        };
        checkViewportManager();
    }

    /**
     * Connect to symbol scaler for coordinated scaling
     */
    connectToSymbolScaler() {
        const checkSymbolScaler = () => {
            if (window.symbolScaler) {
                this.symbolScaler = window.symbolScaler;
                console.log('LODManager connected to SymbolScaler');
            } else {
                setTimeout(checkSymbolScaler, 100);
            }
        };
        checkSymbolScaler();
    }

    /**
     * Handle zoom level changes
     */
    handleZoomChange(zoomLevel) {
        if (this.switchingLOD) return;

        const targetLOD = this.getLODLevelForZoom(zoomLevel);

        if (targetLOD !== this.currentLODLevel) {
            this.switchLODLevel(targetLOD, zoomLevel);
        }

        this.lastZoomLevel = zoomLevel;
    }

    /**
     * Get appropriate LOD level for zoom level
     */
    getLODLevelForZoom(zoomLevel) {
        const levels = Object.keys(this.lodLevels).reverse(); // Start with highest detail

        for (const level of levels) {
            if (zoomLevel >= this.lodLevels[level].minZoom) {
                return level;
            }
        }

        return 'minimal'; // Fallback
    }

    /**
     * Switch to a new LOD level
     */
    switchLODLevel(newLevel, zoomLevel) {
        if (this.switchingLOD || newLevel === this.currentLODLevel) {
            return;
        }

        this.switchingLOD = true;
        const startTime = performance.now();

        console.log(`LODManager: Switching from ${this.currentLODLevel} to ${newLevel} at zoom ${zoomLevel}`);

        // Update all symbols to new LOD level
        this.updateAllSymbolsLOD(newLevel);

        // Update current level
        this.currentLODLevel = newLevel;

        // Track performance
        const switchTime = performance.now() - startTime;
        this.updateLODStats(switchTime);

        // Trigger event
        this.triggerEvent('lodChanged', {
            fromLevel: this.currentLODLevel,
            toLevel: newLevel,
            zoomLevel: zoomLevel,
            switchTime: switchTime
        });

        this.switchingLOD = false;
    }

    /**
     * Update all symbols to a specific LOD level
     */
    updateAllSymbolsLOD(lodLevel) {
        const symbols = document.querySelectorAll('.placed-symbol');
        const lodConfig = this.lodLevels[lodLevel];

        symbols.forEach(symbol => {
            this.updateSymbolLOD(symbol, lodLevel, lodConfig);
        });
    }

    /**
     * Update a single symbol's LOD level
     */
    updateSymbolLOD(symbolElement, lodLevel, lodConfig) {
        if (!symbolElement) return;

        const symbolId = symbolElement.getAttribute('data-symbol-id');
        if (!symbolId) return;

        // Get LOD data for this symbol
        const lodData = this.getSymbolLODData(symbolId);
        if (!lodData) return;

        // Get the appropriate SVG for this LOD level
        const svgContent = this.getLODSVG(lodData, lodLevel);
        if (!svgContent) return;

        // Update the symbol's SVG content
        this.updateSymbolSVG(symbolElement, svgContent, lodLevel, lodConfig);
    }

    /**
     * Get LOD data for a symbol
     */
    getSymbolLODData(symbolId) {
        // Check cache first
        if (this.symbolLODData.has(symbolId)) {
            return this.symbolLODData.get(symbolId);
        }

        // Try to get from symbol library
        if (window.symbolLibrary) {
            const symbol = window.symbolLibrary.symbols.find(s => s.id === symbolId);
            if (symbol && symbol.lodData) {
                this.symbolLODData.set(symbolId, symbol.lodData);
                return symbol.lodData;
            }
        }

        // Generate default LOD data
        const defaultLODData = this.generateDefaultLODData(symbolId);
        this.symbolLODData.set(symbolId, defaultLODData);
        return defaultLODData;
    }

    /**
     * Generate default LOD data for a symbol
     */
    generateDefaultLODData(symbolId) {
        const symbol = this.getSymbolById(symbolId);
        if (!symbol) return null;

        const originalSVG = symbol.svg || '';

        return {
            symbolId: symbolId,
            levels: {
                high: {
                    svg: originalSVG,
                    complexity: 1.0,
                    elementCount: this.countSVGElements(originalSVG)
                },
                medium: {
                    svg: this.simplifySVG(originalSVG, 0.7),
                    complexity: 0.7,
                    elementCount: this.countSVGElements(this.simplifySVG(originalSVG, 0.7))
                },
                low: {
                    svg: this.simplifySVG(originalSVG, 0.4),
                    complexity: 0.4,
                    elementCount: this.countSVGElements(this.simplifySVG(originalSVG, 0.4))
                },
                minimal: {
                    svg: this.simplifySVG(originalSVG, 0.2),
                    complexity: 0.2,
                    elementCount: this.countSVGElements(this.simplifySVG(originalSVG, 0.2))
                }
            }
        };
    }

    /**
     * Get symbol by ID
     */
    getSymbolById(symbolId) {
        if (window.symbolLibrary) {
            return window.symbolLibrary.symbols.find(s => s.id === symbolId);
        }
        return null;
    }

    /**
     * Count SVG elements for complexity measurement
     */
    countSVGElements(svgContent) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = svgContent;
        const svgElement = tempDiv.querySelector('svg');

        if (!svgElement) return 0;

        // Count various SVG elements
        const elements = svgElement.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon, text');
        return elements.length;
    }

    /**
     * Simplify SVG based on complexity factor
     */
    simplifySVG(svgContent, complexityFactor) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = svgContent;
        const svgElement = tempDiv.querySelector('svg');

        if (!svgElement) return svgContent;

        const simplifiedSVG = svgElement.cloneNode(true);

        // Apply simplification based on complexity factor
        if (complexityFactor < 0.5) {
            // Remove detailed elements
            const detailedElements = simplifiedSVG.querySelectorAll('text, path[d*="c"], path[d*="s"]');
            detailedElements.forEach(el => el.remove());
        }

        if (complexityFactor < 0.3) {
            // Remove more elements, keep only basic shapes
            const complexElements = simplifiedSVG.querySelectorAll('path:not([d*="M"]):not([d*="L"]), text, circle[r*="."]');
            complexElements.forEach(el => el.remove());
        }

        if (complexityFactor < 0.2) {
            // Keep only the most basic representation
            const basicElements = simplifiedSVG.querySelectorAll('rect, circle, line');
            const allElements = simplifiedSVG.querySelectorAll('*');

            allElements.forEach(el => {
                if (!basicElements.includes(el) && el !== simplifiedSVG) {
                    el.remove();
                }
            });
        }

        return simplifiedSVG.outerHTML;
    }

    /**
     * Get SVG content for a specific LOD level
     */
    getLODSVG(lodData, lodLevel) {
        if (!lodData || !lodData.levels || !lodData.levels[lodLevel]) {
            return null;
        }

        return lodData.levels[lodLevel].svg;
    }

    /**
     * Update symbol's SVG content with transition
     */
    updateSymbolSVG(symbolElement, svgContent, lodLevel, lodConfig) {
        if (!symbolElement || !svgContent) return;

        // Find the SVG element within the symbol
        const svgElement = symbolElement.querySelector('svg');
        if (!svgElement) return;

        // Store current transform
        const currentTransform = svgElement.getAttribute('transform') || '';
        const currentScale = symbolElement.getAttribute('data-scale') || '1';

        // Create temporary element to parse new SVG
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = svgContent;
        const newSVG = tempDiv.querySelector('svg');

        if (!newSVG) return;

        // Apply transition if enabled
        if (this.enableTransitions) {
            svgElement.style.transition = `opacity ${this.transitionDuration}ms ease`;
            svgElement.style.opacity = '0';

            setTimeout(() => {
                // Update SVG content
                svgElement.innerHTML = newSVG.innerHTML;
                svgElement.setAttribute('viewBox', newSVG.getAttribute('viewBox') || '0 0 20 20');
                svgElement.setAttribute('transform', currentTransform);

                // Restore opacity
                svgElement.style.opacity = '1';

                setTimeout(() => {
                    svgElement.style.transition = '';
                }, this.transitionDuration);
            }, this.transitionDuration / 2);
        } else {
            // Update immediately without transition
            svgElement.innerHTML = newSVG.innerHTML;
            svgElement.setAttribute('viewBox', newSVG.getAttribute('viewBox') || '0 0 20 20');
            svgElement.setAttribute('transform', currentTransform);
        }

        // Update LOD attributes
        symbolElement.setAttribute('data-lod-level', lodLevel);
        symbolElement.setAttribute('data-lod-complexity', lodConfig.complexity);

        // Trigger LOD change event
        this.triggerEvent('symbolLODChanged', {
            symbolElement: symbolElement,
            lodLevel: lodLevel,
            complexity: lodConfig.complexity
        });
    }

    /**
     * Update LOD statistics
     */
    updateLODStats(switchTime) {
        this.lodStats.totalSwitches++;
        this.lodStats.lastSwitchTime = Date.now();
        this.lodStats.switchTimes.push(switchTime);

        // Keep only last 100 switch times
        if (this.lodStats.switchTimes.length > 100) {
            this.lodStats.switchTimes.shift();
        }

        // Calculate average
        this.lodStats.averageSwitchTime = this.lodStats.switchTimes.reduce((a, b) => a + b, 0) / this.lodStats.switchTimes.length;
    }

    /**
     * Get current LOD level
     */
    getCurrentLODLevel() {
        return this.currentLODLevel;
    }

    /**
     * Get LOD configuration
     */
    getLODConfig() {
        return { ...this.lodLevels };
    }

    /**
     * Set LOD configuration
     */
    setLODConfig(config) {
        this.lodLevels = { ...config };
        console.log('LODManager: Configuration updated');
    }

    /**
     * Force LOD level for testing
     */
    forceLODLevel(level) {
        if (!this.lodLevels[level]) {
            console.warn(`LODManager: Invalid LOD level: ${level}`);
            return;
        }

        this.switchLODLevel(level, this.lastZoomLevel);
    }

    /**
     * Get LOD statistics
     */
    getLODStats() {
        return { ...this.lodStats };
    }

    /**
     * Clear LOD cache
     */
    clearLODCache() {
        this.lodCache.clear();
        this.symbolLODData.clear();
        console.log('LODManager: Cache cleared');
    }

    /**
     * Add event listener
     */
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event listener
     */
    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Trigger custom event
     */
    triggerEvent(event, data = {}) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in LOD manager event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Enable/disable LOD transitions
     */
    setTransitionsEnabled(enabled) {
        this.enableTransitions = enabled;
        console.log(`LODManager: Transitions ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Set transition duration
     */
    setTransitionDuration(duration) {
        this.transitionDuration = duration;
        console.log(`LODManager: Transition duration set to ${duration}ms`);
    }

    /**
     * Get performance report
     */
    getPerformanceReport() {
        const report = {
            currentLODLevel: this.currentLODLevel,
            totalSwitches: this.lodStats.totalSwitches,
            averageSwitchTime: this.lodStats.averageSwitchTime,
            lastSwitchTime: this.lodStats.lastSwitchTime,
            cacheSize: this.lodCache.size,
            symbolLODDataSize: this.symbolLODData.size,
            configuration: this.getLODConfig()
        };

        return report;
    }

    /**
     * Destroy the LOD manager
     */
    destroy() {
        this.eventHandlers.clear();
        this.lodCache.clear();
        this.symbolLODData.clear();
        console.log('LODManager: Destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LODManager;
} else if (typeof window !== 'undefined') {
    window.LODManager = LODManager;
}
