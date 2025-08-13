/**
 * LOD Testing Utility for SVG-BIM System
 * Tests Level of Detail system with various symbol complexities and zoom levels
 */

class LODTester {
    constructor() {
        this.testSymbols = [];
        this.testResults = [];
        this.isRunning = false;
        this.currentTest = null;

        // Test configurations
        this.testConfigs = {
            simple: {
                name: 'Simple Symbols',
                symbolCount: 50,
                complexity: 'low',
                description: 'Basic geometric shapes'
            },
            medium: {
                name: 'Medium Complexity',
                symbolCount: 30,
                complexity: 'medium',
                description: 'Symbols with moderate detail'
            },
            complex: {
                name: 'Complex Symbols',
                symbolCount: 20,
                complexity: 'high',
                description: 'Highly detailed symbols'
            },
            mixed: {
                name: 'Mixed Complexity',
                symbolCount: 100,
                complexity: 'mixed',
                description: 'Mix of simple and complex symbols'
            }
        };

        // Performance metrics
        this.metrics = {
            renderTime: 0,
            memoryUsage: 0,
            lodSwitches: 0,
            averageSwitchTime: 0
        };

        this.initialize();
    }

    /**
     * Initialize the LOD tester
     */
    initialize() {
        this.generateTestSymbols();
        window.arxLogger.info('LODTester initialized', { file: 'lod_tester.js' });
    }

    /**
     * Generate test symbols with different complexities
     */
    generateTestSymbols() {
        this.testSymbols = [
            // Simple symbols (low complexity)
            {
                id: 'test-simple-1',
                name: 'Simple Circle',
                category: 'test',
                svg: '<circle cx="10" cy="10" r="8" fill="blue" stroke="black" stroke-width="1"/>',
                complexity: 'low'
            },
            {
                id: 'test-simple-2',
                name: 'Simple Square',
                category: 'test',
                svg: '<rect x="2" y="2" width="16" height="16" fill="red" stroke="black" stroke-width="1"/>',
                complexity: 'low'
            },
            {
                id: 'test-simple-3',
                name: 'Simple Triangle',
                category: 'test',
                svg: '<polygon points="10,2 18,18 2,18" fill="green" stroke="black" stroke-width="1"/>',
                complexity: 'low'
            },

            // Medium complexity symbols
            {
                id: 'test-medium-1',
                name: 'Medium Device',
                category: 'test',
                svg: `
                    <rect x="3" y="3" width="14" height="14" fill="lightblue" stroke="black" stroke-width="1"/>
                    <circle cx="10" cy="10" r="3" fill="white" stroke="black" stroke-width="1"/>
                    <line x1="7" y1="10" x2="13" y2="10" stroke="black" stroke-width="2"/>
                    <line x1="10" y1="7" x2="10" y2="13" stroke="black" stroke-width="2"/>
                `,
                complexity: 'medium'
            },
            {
                id: 'test-medium-2',
                name: 'Medium Sensor',
                category: 'test',
                svg: `
                    <circle cx="10" cy="10" r="8" fill="yellow" stroke="black" stroke-width="1"/>
                    <circle cx="10" cy="10" r="5" fill="orange" stroke="black" stroke-width="1"/>
                    <circle cx="10" cy="10" r="2" fill="red"/>
                    <text x="10" y="22" text-anchor="middle" font-size="3" fill="black">S</text>
                `,
                complexity: 'medium'
            },

            // Complex symbols (high complexity)
            {
                id: 'test-complex-1',
                name: 'Complex Controller',
                category: 'test',
                svg: `
                    <rect x="2" y="2" width="16" height="16" fill="lightgray" stroke="black" stroke-width="1"/>
                    <rect x="4" y="4" width="12" height="4" fill="white" stroke="black" stroke-width="0.5"/>
                    <rect x="4" y="10" width="12" height="4" fill="white" stroke="black" stroke-width="0.5"/>
                    <circle cx="6" cy="6" r="1" fill="green"/>
                    <circle cx="10" cy="6" r="1" fill="yellow"/>
                    <circle cx="14" cy="6" r="1" fill="red"/>
                    <circle cx="6" cy="12" r="1" fill="blue"/>
                    <circle cx="10" cy="12" r="1" fill="purple"/>
                    <circle cx="14" cy="12" r="1" fill="orange"/>
                    <text x="10" y="18" text-anchor="middle" font-size="2" fill="black">CTRL</text>
                `,
                complexity: 'high'
            },
            {
                id: 'test-complex-2',
                name: 'Complex Panel',
                category: 'test',
                svg: `
                    <rect x="1" y="1" width="18" height="18" fill="darkgray" stroke="black" stroke-width="1"/>
                    <rect x="3" y="3" width="14" height="6" fill="black"/>
                    <rect x="3" y="11" width="14" height="6" fill="black"/>
                    <rect x="5" y="5" width="2" height="2" fill="red"/>
                    <rect x="8" y="5" width="2" height="2" fill="green"/>
                    <rect x="11" y="5" width="2" height="2" fill="blue"/>
                    <rect x="14" y="5" width="2" height="2" fill="yellow"/>
                    <rect x="5" y="13" width="2" height="2" fill="cyan"/>
                    <rect x="8" y="13" width="2" height="2" fill="magenta"/>
                    <rect x="11" y="13" width="2" height="2" fill="orange"/>
                    <rect x="14" y="13" width="2" height="2" fill="pink"/>
                    <text x="10" y="22" text-anchor="middle" font-size="2" fill="black">PANEL</text>
                `,
                complexity: 'high'
            }
        ];
    }

    /**
     * Run a specific LOD test
     */
    async runTest(testType) {
        if (this.isRunning) {
            console.warn('LODTester: Test already running');
            return;
        }

        const config = this.testConfigs[testType];
        if (!config) {
            console.error(`LODTester: Unknown test type: ${testType}`);
            return;
        }

        this.isRunning = true;
        this.currentTest = testType;

        window.arxLogger.info(`LODTester: Starting ${config.name} test`, { file: 'lod_tester.js' });

        try {
            // Clear existing test objects
            this.clearTestObjects();

            // Generate test objects
            const testObjects = this.generateTestObjects(config);

            // Place test objects
            await this.placeTestObjects(testObjects);

            // Run zoom test
            await this.runZoomTest();

            // Collect results
            const results = this.collectTestResults(config);

            // Store results
            this.testResults.push(results);

            window.arxLogger.info(`LODTester: ${config.name} test completed`, { results, file: 'lod_tester.js' });

            return results;

        } catch (error) {
            console.error('LODTester: Test failed', error);
            throw error;
        } finally {
            this.isRunning = false;
            this.currentTest = null;
        }
    }

    /**
     * Generate test objects based on configuration
     */
    generateTestObjects(config) {
        const objects = [];
        const symbols = this.getSymbolsByComplexity(config.complexity);

        for (let i = 0; i < config.symbolCount; i++) {
            const symbol = symbols[i % symbols.length];
            const x = Math.random() * 800 + 100;
            const y = Math.random() * 600 + 100;

            objects.push({
                symbol: symbol,
                x: x,
                y: y,
                id: `test-${config.complexity}-${i}`
            });
        }

        return objects;
    }

    /**
     * Get symbols by complexity level
     */
    getSymbolsByComplexity(complexity) {
        if (complexity === 'mixed') {
            return this.testSymbols;
        }

        return this.testSymbols.filter(symbol => symbol.complexity === complexity);
    }

    /**
     * Place test objects in the SVG
     */
    async placeTestObjects(objects) {
        const svg = document.querySelector('#svg-container svg');
        if (!svg) {
            throw new Error('SVG container not found');
        }

        const startTime = performance.now();

        for (const obj of objects) {
            await this.placeTestObject(svg, obj);
            // Small delay to prevent blocking
            await new Promise(resolve => setTimeout(resolve, 10));
        }

        this.metrics.renderTime = performance.now() - startTime;
    }

    /**
     * Place a single test object
     */
    async placeTestObject(svg, obj) {
        // Create symbol element
        const symbolElement = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        symbolElement.setAttribute('id', obj.id);
        symbolElement.setAttribute('class', 'placed-symbol test-object');
        symbolElement.setAttribute('data-symbol-id', obj.symbol.id);
        symbolElement.setAttribute('data-symbol-name', obj.symbol.name);
        symbolElement.setAttribute('data-category', obj.symbol.category);
        symbolElement.setAttribute('data-complexity', obj.symbol.complexity);
        symbolElement.setAttribute('data-x', obj.x.toString());
        symbolElement.setAttribute('data-y', obj.y.toString());
        symbolElement.setAttribute('data-base-scale', '1.0');
        symbolElement.setAttribute('data-lod-level', 'medium');
        symbolElement.setAttribute('data-lod-complexity', '0.7');
        symbolElement.setAttribute('data-lod-enabled', 'true');

        // Create SVG content
        const symbolSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        symbolSvg.setAttribute('width', '40');
        symbolSvg.setAttribute('height', '40');
        symbolSvg.setAttribute('viewBox', '0 0 20 20');
        symbolSvg.innerHTML = obj.symbol.svg;

        symbolElement.appendChild(symbolSvg);
        symbolElement.setAttribute('transform', `translate(${obj.x}, ${obj.y})`);

        svg.appendChild(symbolElement);
    }

    /**
     * Run zoom test to trigger LOD switches
     */
    async runZoomTest() {
        if (!window.viewportManager) {
            console.warn('LODTester: ViewportManager not available for zoom test');
            return;
        }

        const viewportManager = window.viewportManager;
        const lodManager = window.lodManager;

        if (!lodManager) {
            console.warn('LODTester: LODManager not available for zoom test');
            return;
        }

        // Store initial state
        const initialZoom = viewportManager.currentZoom;
        const initialLOD = lodManager.getCurrentLODLevel();

        // Test different zoom levels
        const zoomLevels = [0.1, 0.5, 1.0, 2.0, 5.0];
        const lodSwitches = [];

        for (const zoom of zoomLevels) {
            const startTime = performance.now();

            // Set zoom level
            viewportManager.setZoom(zoom);

            // Wait for LOD switch
            await new Promise(resolve => setTimeout(resolve, 500));

            const switchTime = performance.now() - startTime;
            const currentLOD = lodManager.getCurrentLODLevel();

            lodSwitches.push({
                zoom: zoom,
                lodLevel: currentLOD,
                switchTime: switchTime
            });
        }

        // Restore initial state
        viewportManager.setZoom(initialZoom);

        // Update metrics
        this.metrics.lodSwitches = lodSwitches.length;
        this.metrics.averageSwitchTime = lodSwitches.reduce((sum, s) => sum + s.switchTime, 0) / lodSwitches.length;

        return lodSwitches;
    }

    /**
     * Collect test results
     */
    collectTestResults(config) {
        const testObjects = document.querySelectorAll('.test-object');
        const lodManager = window.lodManager;

        const results = {
            testType: config.name,
            timestamp: new Date().toISOString(),
            objectCount: testObjects.length,
            renderTime: this.metrics.renderTime,
            lodSwitches: this.metrics.lodSwitches,
            averageSwitchTime: this.metrics.averageSwitchTime,
            currentLODLevel: lodManager ? lodManager.getCurrentLODLevel() : 'unknown',
            memoryUsage: this.getMemoryUsage(),
            performance: {
                fps: this.calculateFPS(),
                objectVisibility: this.calculateObjectVisibility()
            }
        };

        return results;
    }

    /**
     * Get memory usage (approximate)
     */
    getMemoryUsage() {
        if (performance.memory) {
            return {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit
            };
        }
        return null;
    }

    /**
     * Calculate approximate FPS
     */
    calculateFPS() {
        // Simple FPS calculation based on render time
        const renderTime = this.metrics.renderTime;
        const objectCount = document.querySelectorAll('.test-object').length;

        if (renderTime > 0 && objectCount > 0) {
            const timePerObject = renderTime / objectCount;
            return Math.round(1000 / timePerObject);
        }

        return 60; // Default assumption
    }

    /**
     * Calculate object visibility percentage
     */
    calculateObjectVisibility() {
        const testObjects = document.querySelectorAll('.test-object');
        const viewportManager = window.viewportManager;

        if (!viewportManager) return 100;

        let visibleCount = 0;
        testObjects.forEach(obj => {
            const x = parseFloat(obj.getAttribute('data-x'));
            const y = parseFloat(obj.getAttribute('data-y'));

            if (viewportManager.isObjectVisible(x, y)) {
                visibleCount++;
            }
        });

        return Math.round((visibleCount / testObjects.length) * 100);
    }

    /**
     * Clear test objects
     */
    clearTestObjects() {
        const testObjects = document.querySelectorAll('.test-object');
        testObjects.forEach(obj => obj.remove());
    }

    /**
     * Get test results summary
     */
    getTestResultsSummary() {
        if (this.testResults.length === 0) {
            return { message: 'No test results available' };
        }

        const summary = {
            totalTests: this.testResults.length,
            averageRenderTime: 0,
            averageLODSwitches: 0,
            averageSwitchTime: 0,
            bestPerformance: null,
            worstPerformance: null
        };

        // Calculate averages
        summary.averageRenderTime = this.testResults.reduce((sum, r) => sum + r.renderTime, 0) / this.testResults.length;
        summary.averageLODSwitches = this.testResults.reduce((sum, r) => sum + r.lodSwitches, 0) / this.testResults.length;
        summary.averageSwitchTime = this.testResults.reduce((sum, r) => sum + r.averageSwitchTime, 0) / this.testResults.length;

        // Find best and worst performance
        const sortedByRenderTime = [...this.testResults].sort((a, b) => a.renderTime - b.renderTime);
        summary.bestPerformance = sortedByRenderTime[0];
        summary.worstPerformance = sortedByRenderTime[sortedByRenderTime.length - 1];

        return summary;
    }

    /**
     * Export test results
     */
    exportTestResults() {
        const data = {
            summary: this.getTestResultsSummary(),
            detailedResults: this.testResults,
            timestamp: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `lod-test-results-${new Date().toISOString().split('T')[0]}.json`;
        a.click();

        URL.revokeObjectURL(url);
    }

    /**
     * Reset test results
     */
    resetTestResults() {
        this.testResults = [];
        this.metrics = {
            renderTime: 0,
            memoryUsage: 0,
            lodSwitches: 0,
            averageSwitchTime: 0
        };
        window.arxLogger.info('LODTester: Test results reset', { file: 'lod_tester.js' });
    }

    /**
     * Get available test types
     */
    getAvailableTests() {
        return Object.keys(this.testConfigs);
    }

    /**
     * Get test configuration
     */
    getTestConfig(testType) {
        return this.testConfigs[testType];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LODTester;
} else if (typeof window !== 'undefined') {
    window.LODTester = LODTester;
}
