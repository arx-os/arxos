/**
 * Performance Tester for SVG-BIM System
 * Generates large numbers of objects for testing viewport culling and rendering performance
 */

class PerformanceTester {
    constructor(svgElement, options = {}) {
        this.svg = svgElement;
        this.container = svgElement.parentElement;

        // Test configuration
        this.testConfig = {
            objectTypes: options.objectTypes || ['sensor', 'valve', 'pump', 'fan', 'controller'],
            gridSpacing: options.gridSpacing || 50,
            objectSize: options.objectSize || { width: 30, height: 30 },
            colorVariation: options.colorVariation !== false,
            randomRotation: options.randomRotation !== false,
            randomScale: options.randomScale !== false
        };

        // Test state
        this.isGenerating = false;
        this.generatedObjects = [];
        this.currentTest = null;

        // Performance tracking
        this.generationTimes = [];
        this.renderTimes = [];

        // Event handlers
        this.eventHandlers = new Map();

        window.arxLogger.info('PerformanceTester initialized', { file: 'performance_tester.js' });
    }

    /**
     * Generate a grid of objects for performance testing
     */
    generateObjectGrid(count, options = {}) {
        if (this.isGenerating) {
            console.warn('PerformanceTester: Already generating objects');
            return;
        }

        this.isGenerating = true;
        const startTime = performance.now();

        // Calculate grid dimensions
        const cols = Math.ceil(Math.sqrt(count));
        const rows = Math.ceil(count / cols);

        // Grid bounds
        const gridWidth = cols * this.testConfig.gridSpacing;
        const gridHeight = rows * this.testConfig.gridSpacing;

        // Center the grid
        const containerRect = this.container.getBoundingClientRect();
        const startX = (containerRect.width - gridWidth) / 2;
        const startY = (containerRect.height - gridHeight) / 2;

        window.arxLogger.debug(`PerformanceTester: Generating ${count} objects in ${cols}x${rows} grid`, { file: 'performance_tester.js' });

        // Generate objects
        const objects = [];
        let objectIndex = 0;

        for (let row = 0; row < rows && objectIndex < count; row++) {
            for (let col = 0; col < cols && objectIndex < count; col++) {
                const x = startX + (col * this.testConfig.gridSpacing);
                const y = startY + (row * this.testConfig.gridSpacing);

                const object = this.createTestObject(x, y, objectIndex, options);
                objects.push(object);
                objectIndex++;
            }
        }

        // Add objects to SVG
        this.addObjectsToSVG(objects);

        const generationTime = performance.now() - startTime;
        this.generationTimes.push(generationTime);

        this.generatedObjects = objects;
        this.isGenerating = false;

        // Trigger event
        this.triggerEvent('objectsGenerated', {
            count: objects.length,
            generationTime: generationTime,
            objects: objects
        });

        window.arxLogger.performance('generate_grid', generationTime, { count, cols, rows, file: 'performance_tester.js' });

        return objects;
    }

    /**
     * Generate objects in a random pattern
     */
    generateRandomObjects(count, options = {}) {
        if (this.isGenerating) {
            console.warn('PerformanceTester: Already generating objects');
            return;
        }

        this.isGenerating = true;
        const startTime = performance.now();

        const containerRect = this.container.getBoundingClientRect();
        const margin = 100;
        const maxX = containerRect.width - margin;
        const maxY = containerRect.height - margin;

        window.arxLogger.debug(`PerformanceTester: Generating ${count} random objects`, { file: 'performance_tester.js' });

        const objects = [];

        for (let i = 0; i < count; i++) {
            const x = margin + Math.random() * (maxX - margin);
            const y = margin + Math.random() * (maxY - margin);

            const object = this.createTestObject(x, y, i, options);
            objects.push(object);
        }

        // Add objects to SVG
        this.addObjectsToSVG(objects);

        const generationTime = performance.now() - startTime;
        this.generationTimes.push(generationTime);

        this.generatedObjects = objects;
        this.isGenerating = false;

        // Trigger event
        this.triggerEvent('objectsGenerated', {
            count: objects.length,
            generationTime: generationTime,
            objects: objects
        });

        window.arxLogger.performance('generate_random', generationTime, { count, file: 'performance_tester.js' });

        return objects;
    }

    /**
     * Generate objects in a spiral pattern
     */
    generateSpiralObjects(count, options = {}) {
        if (this.isGenerating) {
            console.warn('PerformanceTester: Already generating objects');
            return;
        }

        this.isGenerating = true;
        const startTime = performance.now();

        const containerRect = this.container.getBoundingClientRect();
        const centerX = containerRect.width / 2;
        const centerY = containerRect.height / 2;

        window.arxLogger.debug(`PerformanceTester: Generating ${count} spiral objects`, { file: 'performance_tester.js' });

        const objects = [];
        const spacing = this.testConfig.gridSpacing;

        for (let i = 0; i < count; i++) {
            const angle = i * 0.5; // Spiral angle
            const radius = i * spacing * 0.1; // Increasing radius

            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            const object = this.createTestObject(x, y, i, options);
            objects.push(object);
        }

        // Add objects to SVG
        this.addObjectsToSVG(objects);

        const generationTime = performance.now() - startTime;
        this.generationTimes.push(generationTime);

        this.generatedObjects = objects;
        this.isGenerating = false;

        // Trigger event
        this.triggerEvent('objectsGenerated', {
            count: objects.length,
            generationTime: generationTime,
            objects: objects
        });

        window.arxLogger.performance('generate_spiral', generationTime, { count, file: 'performance_tester.js' });

        return objects;
    }

    /**
     * Create a test object
     */
    createTestObject(x, y, index, options = {}) {
        const objectType = this.testConfig.objectTypes[index % this.testConfig.objectTypes.length];
        const size = this.testConfig.objectSize;

        // Create SVG element
        const object = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        object.setAttribute('class', 'placed-symbol test-object');
        object.setAttribute('data-placed-symbol', 'true');
        object.setAttribute('data-type', objectType);
        object.setAttribute('data-test-object', 'true');
        object.setAttribute('data-object-id', `test-${index}`);

        // Apply transforms
        let transform = `translate(${x}, ${y})`;

        if (this.testConfig.randomRotation) {
            const rotation = Math.random() * 360;
            transform += ` rotate(${rotation})`;
        }

        if (this.testConfig.randomScale) {
            const scale = 0.5 + Math.random() * 1.5;
            transform += ` scale(${scale})`;
        }

        object.setAttribute('transform', transform);

        // Create visual representation
        const visual = this.createObjectVisual(objectType, size, index);
        object.appendChild(visual);

        // Add metadata
        object.setAttribute('data-x', x);
        object.setAttribute('data-y', y);
        object.setAttribute('data-index', index);

        return object;
    }

    /**
     * Create visual representation for object type
     */
    createObjectVisual(type, size, index) {
        const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        // Generate color based on type and index
        const color = this.getObjectColor(type, index);

        switch (type) {
            case 'sensor':
                return this.createSensorVisual(size, color);
            case 'valve':
                return this.createValveVisual(size, color);
            case 'pump':
                return this.createPumpVisual(size, color);
            case 'fan':
                return this.createFanVisual(size, color);
            case 'controller':
                return this.createControllerVisual(size, color);
            default:
                return this.createDefaultVisual(size, color);
        }
    }

    /**
     * Create sensor visual
     */
    createSensorVisual(size, color) {
        const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', size.width / 2);
        circle.setAttribute('cy', size.height / 2);
        circle.setAttribute('r', Math.min(size.width, size.height) / 3);
        circle.setAttribute('fill', color);
        circle.setAttribute('stroke', '#333');
        circle.setAttribute('stroke-width', '2');

        visual.appendChild(circle);
        return visual;
    }

    /**
     * Create valve visual
     */
    createValveVisual(size, color) {
        const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', size.width * 0.1);
        rect.setAttribute('y', size.height * 0.1);
        rect.setAttribute('width', size.width * 0.8);
        rect.setAttribute('height', size.height * 0.8);
        rect.setAttribute('fill', color);
        rect.setAttribute('stroke', '#333');
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('rx', '3');

        visual.appendChild(rect);
        return visual;
    }

    /**
     * Create pump visual
     */
    createPumpVisual(size, color) {
        const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        const centerX = size.width / 2;
        const centerY = size.height / 2;
        const radius = Math.min(size.width, size.height) / 3;

        const points = [];
        for (let i = 0; i < 6; i++) {
            const angle = (i * Math.PI) / 3;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;
            points.push(`${x},${y}`);
        }

        polygon.setAttribute('points', points.join(' '));
        polygon.setAttribute('fill', color);
        polygon.setAttribute('stroke', '#333');
        polygon.setAttribute('stroke-width', '2');

        visual.appendChild(polygon);
        return visual;
    }

    /**
     * Create fan visual
     */
    createFanVisual(size, color) {
        const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        const centerX = size.width / 2;
        const centerY = size.height / 2;
        const radius = Math.min(size.width, size.height) / 3;

        // Create fan blades
        for (let i = 0; i < 4; i++) {
            const angle = (i * Math.PI) / 2;
            const x1 = centerX + Math.cos(angle) * radius * 0.3;
            const y1 = centerY + Math.sin(angle) * radius * 0.3;
            const x2 = centerX + Math.cos(angle) * radius;
            const y2 = centerY + Math.sin(angle) * radius;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1);
            line.setAttribute('y1', y1);
            line.setAttribute('x2', x2);
            line.setAttribute('y2', y2);
            line.setAttribute('stroke', color);
            line.setAttribute('stroke-width', '3');

            visual.appendChild(line);
        }

        // Center circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', centerX);
        circle.setAttribute('cy', centerY);
        circle.setAttribute('r', radius * 0.2);
        circle.setAttribute('fill', color);
        circle.setAttribute('stroke', '#333');
        circle.setAttribute('stroke-width', '2');

        visual.appendChild(circle);
        return visual;
    }

    /**
     * Create controller visual
     */
    createControllerVisual(size, color) {
        const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', size.width * 0.1);
        rect.setAttribute('y', size.height * 0.1);
        rect.setAttribute('width', size.width * 0.8);
        rect.setAttribute('height', size.height * 0.8);
        rect.setAttribute('fill', color);
        rect.setAttribute('stroke', '#333');
        rect.setAttribute('stroke-width', '2');

        // Add some internal details
        const innerRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        innerRect.setAttribute('x', size.width * 0.25);
        innerRect.setAttribute('y', size.height * 0.25);
        innerRect.setAttribute('width', size.width * 0.5);
        innerRect.setAttribute('height', size.height * 0.5);
        innerRect.setAttribute('fill', 'none');
        innerRect.setAttribute('stroke', '#333');
        innerRect.setAttribute('stroke-width', '1');

        visual.appendChild(rect);
        visual.appendChild(innerRect);
        return visual;
    }

    /**
     * Create default visual
     */
    createDefaultVisual(size, color) {
        const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g');

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', size.width * 0.1);
        rect.setAttribute('y', size.height * 0.1);
        rect.setAttribute('width', size.width * 0.8);
        rect.setAttribute('height', size.height * 0.8);
        rect.setAttribute('fill', color);
        rect.setAttribute('stroke', '#333');
        rect.setAttribute('stroke-width', '2');

        visual.appendChild(rect);
        return visual;
    }

    /**
     * Get object color based on type and index
     */
    getObjectColor(type, index) {
        if (!this.testConfig.colorVariation) {
            return '#4CAF50';
        }

        const colors = [
            '#4CAF50', '#2196F3', '#FF9800', '#F44336', '#9C27B0',
            '#00BCD4', '#FF5722', '#795548', '#607D8B', '#E91E63'
        ];

        const colorIndex = (index + type.length) % colors.length;
        return colors[colorIndex];
    }

    /**
     * Add objects to SVG
     */
    addObjectsToSVG(objects) {
        const renderStart = performance.now();

        // Create a container for test objects if it doesn't exist
        let testContainer = this.svg.querySelector('#test-objects-container');
        if (!testContainer) {
            testContainer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            testContainer.setAttribute('id', 'test-objects-container');
            this.svg.appendChild(testContainer);
        }

        // Add objects to container
        objects.forEach(object => {
            testContainer.appendChild(object);
        });

        const renderTime = performance.now() - renderStart;
        this.renderTimes.push(renderTime);

        window.arxLogger.performance('render_objects', renderTime, { count: objects.length, file: 'performance_tester.js' });

        console.log(`PerformanceTester: Rendered ${objects.length} objects in ${renderTime.toFixed(2)}ms`);
    }

    /**
     * Clear all test objects
     */
    clearTestObjects() {
        const testContainer = this.svg.querySelector('#test-objects-container');
        if (testContainer) {
            testContainer.remove();
        }

        this.generatedObjects = [];

        // Trigger event
        this.triggerEvent('objectsCleared', {
            clearedCount: this.generatedObjects.length
        });

        window.arxLogger.info('PerformanceTester: Cleared all test objects', { file: 'performance_tester.js' });
    }

    /**
     * Run performance test suite
     */
    async runPerformanceTest(testConfig = {}) {
        const tests = testConfig.tests || [
            { name: 'Grid 100', count: 100, pattern: 'grid' },
            { name: 'Grid 500', count: 500, pattern: 'grid' },
            { name: 'Grid 1000', count: 1000, pattern: 'grid' },
            { name: 'Random 100', count: 100, pattern: 'random' },
            { name: 'Random 500', count: 500, pattern: 'random' },
            { name: 'Spiral 100', count: 100, pattern: 'spiral' },
            { name: 'Spiral 500', count: 500, pattern: 'spiral' }
        ];

        const results = [];

        for (const test of tests) {
            window.arxLogger.info(`PerformanceTester: Running test: ${test.name}`, { file: 'performance_tester.js' });

            // Clear previous objects
            this.clearTestObjects();

            // Wait a bit for cleanup
            await new Promise(resolve => setTimeout(resolve, 100));

            // Generate objects
            const startTime = performance.now();
            let objects;

            switch (test.pattern) {
                case 'grid':
                    objects = this.generateObjectGrid(test.count, test.options);
                    break;
                case 'random':
                    objects = this.generateRandomObjects(test.count, test.options);
                    break;
                case 'spiral':
                    objects = this.generateSpiralObjects(test.count, test.options);
                    break;
                default:
                    objects = this.generateObjectGrid(test.count, test.options);
            }

            const totalTime = performance.now() - startTime;

            // Wait for rendering to complete
            await new Promise(resolve => setTimeout(resolve, 200));

            // Measure performance metrics
            const metrics = this.measurePerformance();

            results.push({
                name: test.name,
                count: test.count,
                pattern: test.pattern,
                generationTime: this.generationTimes[this.generationTimes.length - 1] || 0,
                renderTime: this.renderTimes[this.renderTimes.length - 1] || 0,
                totalTime: totalTime,
                metrics: metrics
            });
        }

        // Trigger test completion event
        this.triggerEvent('performanceTestCompleted', {
            results: results,
            summary: this.generateTestSummary(results)
        });

        window.arxLogger.info('PerformanceTester: Performance test completed', { results, file: 'performance_tester.js' });
        return results;
    }

    /**
     * Measure current performance metrics
     */
    measurePerformance() {
        const objects = this.svg.querySelectorAll('.test-object');
        const visibleObjects = this.svg.querySelectorAll('.test-object:not(.culled)');

        return {
            totalObjects: objects.length,
            visibleObjects: visibleObjects.length,
            culledObjects: objects.length - visibleObjects.length,
            cullingEfficiency: objects.length > 0 ? ((objects.length - visibleObjects.length) / objects.length) * 100 : 0
        };
    }

    /**
     * Generate test summary
     */
    generateTestSummary(results) {
        const summary = {
            totalTests: results.length,
            totalObjects: results.reduce((sum, r) => sum + r.count, 0),
            averageGenerationTime: results.reduce((sum, r) => sum + r.generationTime, 0) / results.length,
            averageRenderTime: results.reduce((sum, r) => sum + r.renderTime, 0) / results.length,
            averageTotalTime: results.reduce((sum, r) => sum + r.totalTime, 0) / results.length
        };

        return summary;
    }

    /**
     * Get test statistics
     */
    getTestStats() {
        return {
            generatedObjects: this.generatedObjects.length,
            generationTimes: [...this.generationTimes],
            renderTimes: [...this.renderTimes],
            averageGenerationTime: this.generationTimes.length > 0 ?
                this.generationTimes.reduce((sum, time) => sum + time, 0) / this.generationTimes.length : 0,
            averageRenderTime: this.renderTimes.length > 0 ?
                this.renderTimes.reduce((sum, time) => sum + time, 0) / this.renderTimes.length : 0
        };
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
                    console.error(`Error in performance tester event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Destroy the performance tester
     */
    destroy() {
        this.clearTestObjects();
        this.eventHandlers.clear();
        this.generationTimes = [];
        this.renderTimes = [];
        window.arxLogger.info('PerformanceTester: Destroyed', { file: 'performance_tester.js' });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceTester;
} else if (typeof window !== 'undefined') {
    window.PerformanceTester = PerformanceTester;
}
