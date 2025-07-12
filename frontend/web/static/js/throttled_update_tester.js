/**
 * Throttled Update Tester for SVG-BIM System
 * Tests smoothness and performance of throttled updates on different devices
 */

class ThrottledUpdateTester {
    constructor(options = {}) {
        // Test configuration
        this.testDuration = options.testDuration || 5000; // 5 seconds
        this.updateInterval = options.updateInterval || 16; // ~60fps
        this.batchSizes = options.batchSizes || [1, 10, 50, 100];
        this.deviceTypes = ['low', 'medium', 'high'];
        
        // Test state
        this.isRunning = false;
        this.currentTest = null;
        this.testResults = [];
        this.performanceMetrics = [];
        
        // Performance tracking
        this.frameCount = 0;
        this.lastFPSUpdate = 0;
        this.currentFPS = 0;
        this.frameTimes = [];
        this.maxFrameTimeHistory = 120; // Keep last 120 frame times
        
        // Event handlers
        this.eventHandlers = new Map();
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the tester
     */
    initialize() {
        window.arxLogger.info('ThrottledUpdateTester initialized', { file: 'throttled_update_tester.js' });
        
        // Start performance monitoring
        this.startPerformanceMonitoring();
    }
    
    /**
     * Start performance monitoring
     */
    startPerformanceMonitoring() {
        let lastTime = performance.now();
        
        const monitorFrame = (currentTime) => {
            // Calculate frame time
            const frameTime = currentTime - lastTime;
            lastTime = currentTime;
            
            // Track frame times
            this.frameTimes.push(frameTime);
            if (this.frameTimes.length > this.maxFrameTimeHistory) {
                this.frameTimes.shift();
            }
            
            // Update FPS counter
            this.frameCount++;
            if (currentTime - this.lastFPSUpdate >= 1000) {
                this.currentFPS = this.frameCount;
                this.frameCount = 0;
                this.lastFPSUpdate = currentTime;
            }
            
            // Continue monitoring
            requestAnimationFrame(monitorFrame);
        };
        
        requestAnimationFrame(monitorFrame);
    }
    
    /**
     * Run a comprehensive throttled update test
     */
    async runTest(testType = 'comprehensive') {
        if (this.isRunning) {
            console.warn('Test already running');
            return;
        }
        
        window.arxLogger.info(`=== Running Throttled Update Test: ${testType} ===`, { file: 'throttled_update_tester.js' });
        
        this.isRunning = true;
        this.currentTest = testType;
        
        try {
            let results;
            
            switch (testType) {
                case 'zoom':
                    results = await this.runZoomTest();
                    break;
                case 'pan':
                    results = await this.runPanTest();
                    break;
                case 'batch':
                    results = await this.runBatchTest();
                    break;
                case 'device':
                    results = await this.runDeviceTest();
                    break;
                case 'comprehensive':
                default:
                    results = await this.runComprehensiveTest();
                    break;
            }
            
            // Store results
            this.testResults.push({
                type: testType,
                timestamp: new Date().toISOString(),
                results: results
            });
            
            window.arxLogger.info('Test completed:', { results, file: 'throttled_update_tester.js' });
            return results;
            
        } catch (error) {
            console.error('Test failed:', error);
            throw error;
        } finally {
            this.isRunning = false;
            this.currentTest = null;
        }
    }
    
    /**
     * Run zoom performance test
     */
    async runZoomTest() {
        const results = {
            testType: 'zoom',
            duration: this.testDuration,
            zoomLevels: [],
            frameRates: [],
            smoothness: 0
        };
        
        const startTime = performance.now();
        const endTime = startTime + this.testDuration;
        
        // Simulate zoom events
        while (performance.now() < endTime) {
            const zoomLevel = 0.5 + Math.random() * 2; // 0.5x to 2.5x zoom
            const centerX = Math.random() * window.innerWidth;
            const centerY = Math.random() * window.innerHeight;
            
            // Trigger zoom event
            this.triggerZoomEvent(zoomLevel, centerX, centerY);
            
            // Record metrics
            results.zoomLevels.push(zoomLevel);
            results.frameRates.push(this.currentFPS);
            
            // Wait for next update
            await this.sleep(this.updateInterval);
        }
        
        // Calculate smoothness score
        results.smoothness = this.calculateSmoothnessScore(results.frameRates);
        
        return results;
    }
    
    /**
     * Run pan performance test
     */
    async runPanTest() {
        const results = {
            testType: 'pan',
            duration: this.testDuration,
            panDistances: [],
            frameRates: [],
            smoothness: 0
        };
        
        const startTime = performance.now();
        const endTime = startTime + this.testDuration;
        
        // Simulate pan events
        while (performance.now() < endTime) {
            const deltaX = (Math.random() - 0.5) * 100; // -50 to 50 pixels
            const deltaY = (Math.random() - 0.5) * 100;
            
            // Trigger pan event
            this.triggerPanEvent(deltaX, deltaY);
            
            // Record metrics
            results.panDistances.push(Math.sqrt(deltaX * deltaX + deltaY * deltaY));
            results.frameRates.push(this.currentFPS);
            
            // Wait for next update
            await this.sleep(this.updateInterval);
        }
        
        // Calculate smoothness score
        results.smoothness = this.calculateSmoothnessScore(results.frameRates);
        
        return results;
    }
    
    /**
     * Run batch update test
     */
    async runBatchTest() {
        const results = {
            testType: 'batch',
            batchSizes: this.batchSizes,
            batchResults: []
        };
        
        for (const batchSize of this.batchSizes) {
            const batchResult = await this.testBatchSize(batchSize);
            results.batchResults.push(batchResult);
        }
        
        return results;
    }
    
    /**
     * Test specific batch size
     */
    async testBatchSize(batchSize) {
        const results = {
            batchSize: batchSize,
            frameRates: [],
            processingTimes: [],
            smoothness: 0
        };
        
        const testDuration = Math.min(this.testDuration, 2000); // Shorter test for batches
        const startTime = performance.now();
        const endTime = startTime + testDuration;
        
        while (performance.now() < endTime) {
            const processingStart = performance.now();
            
            // Simulate batch update
            this.triggerBatchUpdate(batchSize);
            
            const processingTime = performance.now() - processingStart;
            
            // Record metrics
            results.frameRates.push(this.currentFPS);
            results.processingTimes.push(processingTime);
            
            // Wait for next update
            await this.sleep(this.updateInterval);
        }
        
        // Calculate smoothness score
        results.smoothness = this.calculateSmoothnessScore(results.frameRates);
        results.averageProcessingTime = results.processingTimes.reduce((a, b) => a + b, 0) / results.processingTimes.length;
        
        return results;
    }
    
    /**
     * Run device performance test
     */
    async runDeviceTest() {
        const results = {
            testType: 'device',
            deviceTypes: this.deviceTypes,
            deviceResults: []
        };
        
        for (const deviceType of this.deviceTypes) {
            const deviceResult = await this.testDevicePerformance(deviceType);
            results.deviceResults.push(deviceResult);
        }
        
        return results;
    }
    
    /**
     * Test device performance
     */
    async testDevicePerformance(deviceType) {
        const results = {
            deviceType: deviceType,
            frameRates: [],
            smoothness: 0,
            recommendations: []
        };
        
        // Simulate device performance characteristics
        const performanceSettings = this.getDevicePerformanceSettings(deviceType);
        
        const testDuration = Math.min(this.testDuration, 3000); // Shorter test for devices
        const startTime = performance.now();
        const endTime = startTime + testDuration;
        
        while (performance.now() < endTime) {
            // Simulate mixed workload
            this.triggerZoomEvent(1.1, window.innerWidth / 2, window.innerHeight / 2);
            this.triggerPanEvent(10, 10);
            this.triggerBatchUpdate(10);
            
            // Record metrics
            results.frameRates.push(this.currentFPS);
            
            // Wait for next update
            await this.sleep(performanceSettings.updateInterval);
        }
        
        // Calculate smoothness score
        results.smoothness = this.calculateSmoothnessScore(results.frameRates);
        
        // Generate recommendations
        results.recommendations = this.generateDeviceRecommendations(deviceType, results);
        
        return results;
    }
    
    /**
     * Run comprehensive test
     */
    async runComprehensiveTest() {
        const results = {
            testType: 'comprehensive',
            zoomTest: null,
            panTest: null,
            batchTest: null,
            deviceTest: null,
            overallScore: 0
        };
        
        // Run all tests
        results.zoomTest = await this.runZoomTest();
        results.panTest = await this.runPanTest();
        results.batchTest = await this.runBatchTest();
        results.deviceTest = await this.runDeviceTest();
        
        // Calculate overall score
        results.overallScore = this.calculateOverallScore(results);
        
        return results;
    }
    
    /**
     * Trigger zoom event
     */
    triggerZoomEvent(zoomFactor, centerX, centerY) {
        if (window.viewportManager) {
            window.viewportManager.zoomAtPoint(zoomFactor, centerX, centerY, false);
        }
        
        // Trigger custom event
        this.triggerEvent('zoomTest', {
            zoomFactor: zoomFactor,
            centerX: centerX,
            centerY: centerY,
            timestamp: performance.now()
        });
    }
    
    /**
     * Trigger pan event
     */
    triggerPanEvent(deltaX, deltaY) {
        if (window.viewportManager) {
            // Simulate pan by updating viewport
            const currentPan = window.viewportManager.getPan();
            const newPanX = currentPan.x + deltaX;
            const newPanY = currentPan.y + deltaY;
            window.viewportManager.setPan(newPanX, newPanY);
        }
        
        // Trigger custom event
        this.triggerEvent('panTest', {
            deltaX: deltaX,
            deltaY: deltaY,
            timestamp: performance.now()
        });
    }
    
    /**
     * Trigger batch update
     */
    triggerBatchUpdate(batchSize) {
        if (window.throttledUpdateManager) {
            // Queue multiple updates
            for (let i = 0; i < batchSize; i++) {
                window.throttledUpdateManager.queueUpdate('symbols', {
                    id: i,
                    x: Math.random() * 1000,
                    y: Math.random() * 1000
                }, { batch: true });
            }
        }
        
        // Trigger custom event
        this.triggerEvent('batchTest', {
            batchSize: batchSize,
            timestamp: performance.now()
        });
    }
    
    /**
     * Calculate smoothness score
     */
    calculateSmoothnessScore(frameRates) {
        if (frameRates.length === 0) return 0;
        
        const avgFPS = frameRates.reduce((a, b) => a + b, 0) / frameRates.length;
        const variance = frameRates.reduce((sum, fps) => sum + Math.pow(fps - avgFPS, 2), 0) / frameRates.length;
        const stdDev = Math.sqrt(variance);
        
        // Higher FPS and lower variance = better smoothness
        const fpsScore = Math.min(avgFPS / 60, 1); // Normalize to 60fps
        const consistencyScore = Math.max(0, 1 - (stdDev / 30)); // Lower std dev = better
        
        return (fpsScore * 0.7 + consistencyScore * 0.3) * 100;
    }
    
    /**
     * Calculate overall score
     */
    calculateOverallScore(results) {
        const scores = [
            results.zoomTest.smoothness,
            results.panTest.smoothness,
            results.batchTest.batchResults.reduce((sum, r) => sum + r.smoothness, 0) / results.batchTest.batchResults.length,
            results.deviceTest.deviceResults.reduce((sum, r) => sum + r.smoothness, 0) / results.deviceTest.deviceResults.length
        ];
        
        return scores.reduce((a, b) => a + b, 0) / scores.length;
    }
    
    /**
     * Get device performance settings
     */
    getDevicePerformanceSettings(deviceType) {
        switch (deviceType) {
            case 'high':
                return { updateInterval: 8, targetFPS: 120 };
            case 'medium':
                return { updateInterval: 16, targetFPS: 60 };
            case 'low':
                return { updateInterval: 32, targetFPS: 30 };
            default:
                return { updateInterval: 16, targetFPS: 60 };
        }
    }
    
    /**
     * Generate device recommendations
     */
    generateDeviceRecommendations(deviceType, results) {
        const recommendations = [];
        
        if (results.smoothness < 50) {
            recommendations.push('Consider reducing update frequency');
            recommendations.push('Enable viewport culling for better performance');
        }
        
        if (results.smoothness < 30) {
            recommendations.push('Switch to low-performance mode');
            recommendations.push('Reduce batch sizes for smoother updates');
        }
        
        if (results.smoothness >= 80) {
            recommendations.push('System can handle high refresh rates');
            recommendations.push('Consider enabling advanced features');
        }
        
        return recommendations;
    }
    
    /**
     * Get test results summary
     */
    getTestResultsSummary() {
        if (this.testResults.length === 0) {
            return { message: 'No tests have been run yet' };
        }
        
        const latestTest = this.testResults[this.testResults.length - 1];
        const results = latestTest.results;
        
        return {
            lastTest: latestTest.type,
            timestamp: latestTest.timestamp,
            overallScore: results.overallScore || 0,
            zoomSmoothness: results.zoomTest?.smoothness || 0,
            panSmoothness: results.panTest?.smoothness || 0,
            averageFPS: this.currentFPS,
            totalTests: this.testResults.length
        };
    }
    
    /**
     * Get performance metrics
     */
    getPerformanceMetrics() {
        const avgFrameTime = this.frameTimes.length > 0 
            ? this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length 
            : 0;
        
        return {
            currentFPS: this.currentFPS,
            averageFrameTime: avgFrameTime,
            frameTimeHistory: [...this.frameTimes],
            isRunning: this.isRunning,
            currentTest: this.currentTest
        };
    }
    
    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
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
                    console.error(`Error in throttled update tester event handler for ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Clear test results
     */
    clearTestResults() {
        this.testResults = [];
        window.arxLogger.info('Test results cleared', { file: 'throttled_update_tester.js' });
    }
    
    /**
     * Destroy the tester
     */
    destroy() {
        this.isRunning = false;
        this.eventHandlers.clear();
        window.arxLogger.info('ThrottledUpdateTester: Destroyed', { file: 'throttled_update_tester.js' });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThrottledUpdateTester;
} else if (typeof window !== 'undefined') {
    window.ThrottledUpdateTester = ThrottledUpdateTester;
} 