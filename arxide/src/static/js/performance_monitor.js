/**
 * Performance Monitor for SVG-BIM System
 * Tracks viewport culling statistics, rendering performance, and provides optimization insights
 */

class PerformanceMonitor {
    constructor(options = {}) {
        this.enabled = options.enabled !== false; // Default to true
        this.updateInterval = options.updateInterval || 1000; // Update every second
        this.maxHistorySize = options.maxHistorySize || 100; // Keep last 100 measurements

        // Performance metrics
        this.metrics = {
            culling: {
                totalObjects: 0,
                visibleObjects: 0,
                culledObjects: 0,
                cullingTime: 0,
                cullingEfficiency: 0,
                lastUpdate: 0
            },
            rendering: {
                frameTime: 0,
                fps: 0,
                renderTime: 0,
                lastFrameTime: 0
            },
            memory: {
                boundsCacheSize: 0,
                visibleObjectsSize: 0,
                totalMemoryUsage: 0
            },
            interaction: {
                zoomOperations: 0,
                panOperations: 0,
                objectSelections: 0,
                lastInteraction: 0
            }
        };

        // Performance history for trend analysis
        this.history = [];
        this.lastUpdate = 0;
        this.updateTimer = null;

        // Performance thresholds for warnings
        this.thresholds = {
            cullingTime: options.cullingTimeThreshold || 16, // 16ms = 60fps
            frameTime: options.frameTimeThreshold || 16,
            memoryUsage: options.memoryThreshold || 50 * 1024 * 1024, // 50MB
            objectCount: options.objectCountThreshold || 1000
        };

        // Event handlers
        this.eventHandlers = new Map();

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the performance monitor
     */
    initialize() {
        if (!this.enabled) {
            return;
        }

        // Start monitoring
        this.startMonitoring();

        if (window.arxLogger) {
          window.arxLogger.info('PerformanceMonitor initialized', {
            component: 'performance_monitor',
            update_interval: this.updateInterval,
            max_history_size: this.maxHistorySize
          });
        }
    }

    /**
     * Start performance monitoring
     */
    startMonitoring() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }

        this.updateTimer = setInterval(() => {
            this.updateMetrics();
        }, this.updateInterval);
    }

    /**
     * Stop performance monitoring
     */
    stopMonitoring() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }

    /**
     * Update performance metrics
     */
    updateMetrics() {
        const now = Date.now();

        // Update frame time and FPS
        if (this.metrics.rendering.lastFrameTime > 0) {
            const frameTime = now - this.metrics.rendering.lastFrameTime;
            this.metrics.rendering.frameTime = frameTime;
            this.metrics.rendering.fps = Math.round(1000 / frameTime);
        }
        this.metrics.rendering.lastFrameTime = now;

        // Calculate culling efficiency
        if (this.metrics.culling.totalObjects > 0) {
            this.metrics.culling.cullingEfficiency =
                (this.metrics.culling.culledObjects / this.metrics.culling.totalObjects) * 100;
        }

        // Add to history
        this.addToHistory();

        // Check for performance issues
        this.checkPerformanceIssues();

        // Trigger update event
        this.triggerEvent('metricsUpdated', this.metrics);
    }

    /**
     * Update culling metrics
     */
    updateCullingMetrics(stats) {
        this.metrics.culling = {
            ...this.metrics.culling,
            ...stats,
            lastUpdate: Date.now()
        };
    }

    /**
     * Update rendering metrics
     */
    updateRenderingMetrics(renderTime) {
        this.metrics.rendering.renderTime = renderTime;
    }

    /**
     * Update memory metrics
     */
    updateMemoryMetrics(boundsCacheSize, visibleObjectsSize) {
        this.metrics.memory.boundsCacheSize = boundsCacheSize;
        this.metrics.memory.visibleObjectsSize = visibleObjectsSize;

        // Estimate total memory usage
        this.metrics.memory.totalMemoryUsage =
            boundsCacheSize + visibleObjectsSize + (this.history.length * 1024); // Rough estimate
    }

    /**
     * Track interaction
     */
    trackInteraction(type) {
        this.metrics.interaction.lastInteraction = Date.now();

        switch (type) {
            case 'zoom':
                this.metrics.interaction.zoomOperations++;
                break;
            case 'pan':
                this.metrics.interaction.panOperations++;
                break;
            case 'selection':
                this.metrics.interaction.objectSelections++;
                break;
        }
    }

    /**
     * Add current metrics to history
     */
    addToHistory() {
        const snapshot = {
            timestamp: Date.now(),
            metrics: JSON.parse(JSON.stringify(this.metrics)) // Deep copy
        };

        this.history.push(snapshot);

        // Limit history size
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        }
    }

    /**
     * Check for performance issues and trigger warnings
     */
    checkPerformanceIssues() {
        const issues = [];

        // Check culling performance
        if (this.metrics.culling.cullingTime > this.thresholds.cullingTime) {
            issues.push({
                type: 'culling',
                severity: 'warning',
                message: `Culling time (${this.metrics.culling.cullingTime.toFixed(2)}ms) exceeds threshold (${this.thresholds.cullingTime}ms)`
            });
        }

        // Check frame time
        if (this.metrics.rendering.frameTime > this.thresholds.frameTime) {
            issues.push({
                type: 'rendering',
                severity: 'warning',
                message: `Frame time (${this.metrics.rendering.frameTime.toFixed(2)}ms) exceeds threshold (${this.thresholds.frameTime}ms)`
            });
        }

        // Check memory usage
        if (this.metrics.memory.totalMemoryUsage > this.thresholds.memoryUsage) {
            issues.push({
                type: 'memory',
                severity: 'warning',
                message: `Memory usage (${(this.metrics.memory.totalMemoryUsage / 1024 / 1024).toFixed(2)}MB) exceeds threshold (${(this.thresholds.memoryUsage / 1024 / 1024).toFixed(2)}MB)`
            });
        }

        // Check object count
        if (this.metrics.culling.totalObjects > this.thresholds.objectCount) {
            issues.push({
                type: 'objects',
                severity: 'info',
                message: `Large number of objects (${this.metrics.culling.totalObjects}) - consider enabling culling`
            });
        }

        // Trigger issues event if any found
        if (issues.length > 0) {
            this.triggerEvent('performanceIssues', issues);
        }
    }

    /**
     * Get current metrics
     */
    getMetrics() {
        return JSON.parse(JSON.stringify(this.metrics));
    }

    /**
     * Get performance history
     */
    getHistory() {
        return JSON.parse(JSON.stringify(this.history));
    }

    /**
     * Get performance trends
     */
    getTrends() {
        if (this.history.length < 2) {
            return null;
        }

        const recent = this.history.slice(-10); // Last 10 measurements
        const older = this.history.slice(-20, -10); // Previous 10 measurements

        if (older.length === 0) {
            return null;
        }

        const trends = {};

        // Calculate trends for key metrics
        const recentAvgCullingTime = recent.reduce((sum, h) => sum + h.metrics.culling.cullingTime, 0) / recent.length;
        const olderAvgCullingTime = older.reduce((sum, h) => sum + h.metrics.culling.cullingTime, 0) / older.length;

        trends.cullingTime = {
            change: recentAvgCullingTime - olderAvgCullingTime,
            percentage: ((recentAvgCullingTime - olderAvgCullingTime) / olderAvgCullingTime) * 100
        };

        const recentAvgFPS = recent.reduce((sum, h) => sum + h.metrics.rendering.fps, 0) / recent.length;
        const olderAvgFPS = older.reduce((sum, h) => sum + h.metrics.rendering.fps, 0) / older.length;

        trends.fps = {
            change: recentAvgFPS - olderAvgFPS,
            percentage: ((recentAvgFPS - olderAvgFPS) / olderAvgFPS) * 100
        };

        return trends;
    }

    /**
     * Generate performance report
     */
    generateReport() {
        const trends = this.getTrends();
        const report = {
            timestamp: Date.now(),
            currentMetrics: this.getMetrics(),
            trends: trends,
            recommendations: this.generateRecommendations()
        };

        return report;
    }

    /**
     * Generate performance recommendations
     */
    generateRecommendations() {
        const recommendations = [];

        // Culling recommendations
        if (this.metrics.culling.cullingEfficiency < 50) {
            recommendations.push({
                type: 'culling',
                priority: 'high',
                message: 'Low culling efficiency - consider adjusting culling margin or object placement'
            });
        }

        if (this.metrics.culling.cullingTime > this.thresholds.cullingTime) {
            recommendations.push({
                type: 'culling',
                priority: 'medium',
                message: 'High culling time - consider increasing culling throttle or optimizing bounds calculation'
            });
        }

        // Rendering recommendations
        if (this.metrics.rendering.fps < 30) {
            recommendations.push({
                type: 'rendering',
                priority: 'high',
                message: 'Low FPS - consider reducing object complexity or enabling more aggressive culling'
            });
        }

        // Memory recommendations
        if (this.metrics.memory.totalMemoryUsage > this.thresholds.memoryUsage) {
            recommendations.push({
                type: 'memory',
                priority: 'medium',
                message: 'High memory usage - consider clearing bounds cache or reducing history size'
            });
        }

        return recommendations;
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
                    console.error(`Error in performance monitor event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Enable performance monitoring
     */
    enable() {
        this.enabled = true;
        this.startMonitoring();
        if (window.arxLogger) {
          window.arxLogger.info('PerformanceMonitor: Enabled', {
            component: 'performance_monitor',
            status: 'enabled'
          });
        }
    }

    /**
     * Disable performance monitoring
     */
    disable() {
        this.enabled = false;
        this.stopMonitoring();
        if (window.arxLogger) {
          window.arxLogger.info('PerformanceMonitor: Disabled', {
            component: 'performance_monitor',
            status: 'disabled'
          });
        }
    }

    /**
     * Reset all metrics
     */
    reset() {
        this.metrics = {
            culling: {
                totalObjects: 0,
                visibleObjects: 0,
                culledObjects: 0,
                cullingTime: 0,
                cullingEfficiency: 0,
                lastUpdate: 0
            },
            rendering: {
                frameTime: 0,
                fps: 0,
                renderTime: 0,
                lastFrameTime: 0
            },
            memory: {
                boundsCacheSize: 0,
                visibleObjectsSize: 0,
                totalMemoryUsage: 0
            },
            interaction: {
                zoomOperations: 0,
                panOperations: 0,
                objectSelections: 0,
                lastInteraction: 0
            }
        };

        this.history = [];
        if (window.arxLogger) {
          window.arxLogger.info('PerformanceMonitor: Metrics reset', {
            component: 'performance_monitor',
            action: 'reset'
          });
        }
    }

    /**
     * Destroy the performance monitor
     */
    destroy() {
        this.stopMonitoring();
        this.eventHandlers.clear();
        this.history = [];
        if (window.arxLogger) {
          window.arxLogger.info('PerformanceMonitor: Destroyed', {
            component: 'performance_monitor',
            status: 'destroyed'
          });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceMonitor;
} else if (typeof window !== 'undefined') {
    window.PerformanceMonitor = PerformanceMonitor;
}
