/**
 * Arxos Comprehensive Test Suite
 * Tests all components of the corrected architecture systematically
 */

class ArxosTestSuite {
    constructor() {
        this.testResults = new Map();
        this.currentTest = null;
        this.testCount = 0;
        this.passCount = 0;
        this.failCount = 0;
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🧪 Starting Arxos Comprehensive Test Suite...');
        
        // Test SVG + ArxObject Integration
        await this.testSVGArxObjectIntegration();
        
        // Test Three.js Renderer
        await this.testThreeRenderer();
        
        // Test Main Integration
        await this.testMainIntegration();
        
        // Test Coordinate Transformations
        await this.testCoordinateTransformations();
        
        // Test Performance
        await this.testPerformance();
        
        this.generateReport();
    }

    /**
     * Test SVG + ArxObject Integration Module
     */
    async testSVGArxObjectIntegration() {
        this.startTestGroup('SVG + ArxObject Integration');
        
        try {
            // Test module loading
            this.assert(typeof ArxosSVGArxObjectIntegration === 'function', 'Module should be loaded');
            
            // Test instantiation
            const integration = new ArxosSVGArxObjectIntegration();
            this.assert(integration !== null, 'Should instantiate correctly');
            this.assert(typeof integration.loadSVGBIM === 'function', 'Should have loadSVGBIM method');
            
            // Test SVG parsing
            const testSVG = this.createTestSVG();
            const result = await integration.loadSVGBIM(testSVG);
            this.assert(result.success, 'Should parse test SVG successfully');
            this.assert(result.arxObjects.length > 0, 'Should extract ArxObjects');
            
            // Test ArxObject management
            const arxObject = integration.getArxObject('test-wall-1');
            this.assert(arxObject !== null, 'Should retrieve ArxObject by ID');
            this.assert(arxObject.type === 'wall', 'Should have correct type');
            
            // Test coordinate transformations
            const coords = { x: 100, y: 200 };
            const transformed = integration.transformCoordinates(coords, 'svg', 'world');
            this.assert(transformed.x !== coords.x || transformed.y !== coords.y, 'Should transform coordinates');
            
        } catch (error) {
            this.fail(`SVG + ArxObject Integration test failed: ${error.message}`);
        }
    }

    /**
     * Test Three.js Renderer Module
     */
    async testThreeRenderer() {
        this.startTestGroup('Three.js Renderer');
        
        try {
            // Test module loading
            this.assert(typeof ArxosThreeRenderer === 'function', 'Module should be loaded');
            
            // Test instantiation
            const renderer = new ArxosThreeRenderer('test-container');
            this.assert(renderer !== null, 'Should instantiate correctly');
            this.assert(typeof renderer.loadSVGBIMModel === 'function', 'Should have loadSVGBIMModel method');
            
            // Test scene setup
            this.assert(renderer.scene !== null, 'Should have scene');
            this.assert(renderer.camera !== null, 'Should have camera');
            this.assert(renderer.renderer !== null, 'Should have renderer');
            
            // Test zoom functionality
            this.assert(typeof renderer.setZoomLevel === 'function', 'Should have setZoomLevel method');
            this.assert(typeof renderer.smoothZoomToScale === 'function', 'Should have smoothZoomToScale method');
            this.assert(typeof renderer.zoomToCampus === 'function', 'Should have zoomToCampus method');
            this.assert(typeof renderer.zoomToSubmicron === 'function', 'Should have zoomToSubmicron method');
            this.assert(typeof renderer.getZoomInfo === 'function', 'Should have getZoomInfo method');
            this.assert(typeof renderer.getAvailableZoomLevels === 'function', 'Should have getAvailableZoomLevels method');
            
            // Test camera controls
            this.assert(typeof renderer.switchCamera === 'function', 'Should have switchCamera method');
            
        } catch (error) {
            this.fail(`Three.js Renderer test failed: ${error.message}`);
        }
    }

    /**
     * Test Main Integration Module
     */
    async testMainIntegration() {
        this.startTestGroup('Main Integration');
        
        try {
            // Test module loading
            this.assert(typeof ArxosCorrectIntegration === 'function', 'Module should be loaded');
            
            // Test instantiation
            const integration = new ArxosCorrectIntegration();
            this.assert(integration !== null, 'Should instantiate correctly');
            
            // Test initialization
            await integration.init();
            this.assert(integration.isInitialized, 'Should initialize correctly');
            
            // Test view switching
            this.assert(typeof integration.switchView === 'function', 'Should have switchView method');
            this.assert(typeof integration.setZoomLevel === 'function', 'Should have setZoomLevel method');
            
        } catch (error) {
            this.fail(`Main Integration test failed: ${error.message}`);
        }
    }

    /**
     * Test Coordinate Transformations
     */
    async testCoordinateTransformations() {
        this.startTestGroup('Coordinate Transformations');
        
        try {
            const integration = new ArxosSVGArxObjectIntegration();
            
            // Test SVG to World transformation
            const svgCoords = { x: 100, y: 200 };
            const worldCoords = integration.transformCoordinates(svgCoords, 'svg', 'world');
            this.assert(worldCoords.x !== svgCoords.x || worldCoords.y !== svgCoords.y, 'SVG to World transformation');
            
            // Test World to Three.js transformation
            const threeCoords = integration.transformCoordinates(worldCoords, 'world', 'three');
            this.assert(threeCoords.x !== worldCoords.x || threeCoords.y !== worldCoords.y, 'World to Three.js transformation');
            
            // Test inverse transformations
            const backToWorld = integration.transformCoordinates(threeCoords, 'three', 'world');
            const backToSVG = integration.transformCoordinates(backToWorld, 'world', 'svg');
            
            // Allow for floating point precision
            const tolerance = 0.001;
            this.assert(
                Math.abs(backToSVG.x - svgCoords.x) < tolerance && 
                Math.abs(backToSVG.y - svgCoords.y) < tolerance,
                'Inverse transformations should be accurate'
            );
            
        } catch (error) {
            this.fail(`Coordinate Transformations test failed: ${error.message}`);
        }
    }

    /**
     * Test Performance
     */
    async testPerformance() {
        this.startTestGroup('Performance');
        
        try {
            const integration = new ArxosSVGArxObjectIntegration();
            
            // Test large dataset handling
            const largeSVG = this.createLargeTestSVG(1000); // 1000 elements
            const startTime = performance.now();
            const result = await integration.loadSVGBIM(largeSVG);
            const endTime = performance.now();
            
            const processingTime = endTime - startTime;
            this.assert(result.success, 'Should handle large datasets');
            this.assert(processingTime < 1000, `Should process large datasets in under 1 second (${processingTime.toFixed(2)}ms)`);
            
            // Test memory usage
            const memoryBefore = performance.memory ? performance.memory.usedJSHeapSize : 0;
            const largeArxObjects = this.createLargeArxObjectSet(10000);
            integration.loadArxObjects(largeArxObjects);
            const memoryAfter = performance.memory ? performance.memory.usedJSHeapSize : 0;
            
            if (performance.memory) {
                const memoryIncrease = memoryAfter - memoryBefore;
                this.assert(memoryIncrease < 50 * 1024 * 1024, `Memory increase should be reasonable (${(memoryIncrease / 1024 / 1024).toFixed(2)}MB)`);
            }
            
        } catch (error) {
            this.fail(`Performance test failed: ${error.message}`);
        }
    }

    /**
     * Helper Methods
     */
    startTestGroup(name) {
        this.currentTest = name;
        console.log(`\n📋 Testing: ${name}`);
    }

    assert(condition, message) {
        this.testCount++;
        if (condition) {
            this.passCount++;
            console.log(`  ✅ ${message}`);
        } else {
            this.failCount++;
            console.log(`  ❌ ${message}`);
        }
    }

    fail(message) {
        this.testCount++;
        this.failCount++;
        console.log(`  ❌ ${message}`);
    }

    generateReport() {
        console.log('\n📊 Test Results Summary');
        console.log('========================');
        console.log(`Total Tests: ${this.testCount}`);
        console.log(`Passed: ${this.passCount}`);
        console.log(`Failed: ${this.failCount}`);
        console.log(`Success Rate: ${((this.passCount / this.testCount) * 100).toFixed(1)}%`);
        
        if (this.failCount === 0) {
            console.log('\n🎉 All tests passed! Arxos architecture is working correctly.');
        } else {
            console.log('\n⚠️  Some tests failed. Please review the implementation.');
        }
    }

    createTestSVG() {
        return `
            <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
                <rect id="test-wall-1" x="100" y="100" width="200" height="20" 
                      data-arxobject='{"id":"test-wall-1","type":"wall","properties":{"material":"concrete","thickness":0.2},"coordinates":{"x":100,"y":100,"width":200,"height":20}}' />
                <rect id="test-door-1" x="200" y="80" width="40" height="60" 
                      data-arxobject='{"id":"test-door-1","type":"door","properties":{"material":"wood","width":1.0},"coordinates":{"x":200,"y":80,"width":40,"height":60}}' />
                <circle id="test-window-1" cx="150" cy="120" r="15" 
                        data-arxobject='{"id":"test-window-1","type":"window","properties":{"material":"glass","diameter":0.3},"coordinates":{"x":150,"y":120,"radius":15}}' />
            </svg>
        `;
    }

    createLargeTestSVG(elementCount) {
        let svg = `<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">`;
        
        for (let i = 0; i < elementCount; i++) {
            const x = (i * 10) % 800;
            const y = Math.floor((i * 10) / 800) * 20;
            svg += `<rect id="test-element-${i}" x="${x}" y="${y}" width="8" height="15" 
                          data-arxobject='{"id":"test-element-${i}","type":"element","properties":{"index":${i}},"coordinates":{"x":${x},"y":${y},"width":8,"height":15}}' />`;
        }
        
        svg += '</svg>';
        return svg;
    }

    createLargeArxObjectSet(count) {
        const arxObjects = [];
        for (let i = 0; i < count; i++) {
            arxObjects.push({
                id: `test-arxobject-${i}`,
                type: 'test',
                properties: { index: i },
                coordinates: { x: i, y: i, z: 0 }
            });
        }
        return arxObjects;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxosTestSuite;
}
