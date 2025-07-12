/**
 * Throttled Update Manager for SVG-BIM System
 * Handles smooth updates with requestAnimationFrame and batching for optimal performance
 */

class ThrottledUpdateManager {
    constructor(options = {}) {
        // Performance settings
        this.targetFPS = options.targetFPS || 60;
        this.frameInterval = 1000 / this.targetFPS; // ms between frames
        this.maxBatchSize = options.maxBatchSize || 100; // Maximum updates per batch
        this.batchTimeout = options.batchTimeout || 16; // ms to wait for batching
        
        // Update state
        this.isRunning = false;
        this.lastFrameTime = 0;
        this.pendingUpdates = new Map(); // Map of update types to their data
        this.updateQueue = []; // Queue of batched updates
        this.animationFrameId = null;
        
        // Performance tracking
        this.frameCount = 0;
        this.lastFPSUpdate = 0;
        this.currentFPS = 0;
        this.frameTimes = [];
        this.maxFrameTimeHistory = 60; // Keep last 60 frame times
        
        // Device performance detection
        this.devicePerformance = this.detectDevicePerformance();
        this.adaptiveThrottling = options.adaptiveThrottling !== false; // Default to true
        
        // Event handlers
        this.eventHandlers = new Map();
        
        // Update types and their priorities
        this.updateTypes = {
            'viewport': { priority: 1, throttle: 16 }, // High priority, 60fps
            'zoom': { priority: 1, throttle: 16 }, // High priority, 60fps
            'pan': { priority: 1, throttle: 16 }, // High priority, 60fps
            'culling': { priority: 2, throttle: 50 }, // Medium priority, 20fps
            'symbols': { priority: 3, throttle: 100 }, // Lower priority, 10fps
            'ui': { priority: 4, throttle: 200 }, // Lowest priority, 5fps
            'batch': { priority: 0, throttle: 0 } // Immediate, no throttling
        };
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the throttled update manager
     */
    initialize() {
        if (window.arxLogger) {
          window.arxLogger.info('ThrottledUpdateManager initialized', {
            component: 'throttled_update_manager',
            device_performance: this.devicePerformance,
            target_fps: this.targetFPS
          });
        }
        
        // Adjust settings based on device performance
        this.adaptToDevicePerformance();
        
        // Start the update loop
        this.start();
    }
    
    /**
     * Detect device performance capabilities
     */
    detectDevicePerformance() {
        const performance = window.performance;
        const memory = performance.memory;
        const hardwareConcurrency = navigator.hardwareConcurrency || 1;
        
        // Check for high refresh rate displays
        const refreshRate = this.detectRefreshRate();
        
        // Check for hardware acceleration
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        const hasHardwareAcceleration = gl && gl.getExtension('WEBGL_debug_renderer_info');
        
        // Calculate performance score
        let score = 0;
        
        // CPU cores
        if (hardwareConcurrency >= 8) score += 3;
        else if (hardwareConcurrency >= 4) score += 2;
        else if (hardwareConcurrency >= 2) score += 1;
        
        // Memory
        if (memory) {
            const totalMemory = memory.totalJSHeapSizeLimit;
            if (totalMemory >= 2147483648) score += 3; // 2GB+
            else if (totalMemory >= 1073741824) score += 2; // 1GB+
            else if (totalMemory >= 536870912) score += 1; // 512MB+
        }
        
        // Refresh rate
        if (refreshRate >= 120) score += 2;
        else if (refreshRate >= 60) score += 1;
        
        // Hardware acceleration
        if (hasHardwareAcceleration) score += 1;
        
        // Determine performance level
        if (score >= 8) return 'high';
        else if (score >= 5) return 'medium';
        else return 'low';
    }
    
    /**
     * Detect display refresh rate
     */
    detectRefreshRate() {
        // Try to detect refresh rate using requestAnimationFrame
        let lastTime = performance.now();
        let frameCount = 0;
        let refreshRate = 60; // Default
        
        const detectFrame = (currentTime) => {
            frameCount++;
            
            if (frameCount >= 60) {
                const elapsed = currentTime - lastTime;
                refreshRate = Math.round((frameCount / elapsed) * 1000);
                return;
            }
            
            requestAnimationFrame(detectFrame);
        };
        
        requestAnimationFrame(detectFrame);
        
        // Return detected refresh rate (with fallback)
        return refreshRate || 60;
    }
    
    /**
     * Adapt settings based on device performance
     */
    adaptToDevicePerformance() {
        if (!this.adaptiveThrottling) return;
        
        switch (this.devicePerformance) {
            case 'high':
                this.targetFPS = 120;
                this.frameInterval = 1000 / this.targetFPS;
                this.maxBatchSize = 200;
                this.batchTimeout = 8;
                break;
            case 'medium':
                this.targetFPS = 60;
                this.frameInterval = 1000 / this.targetFPS;
                this.maxBatchSize = 100;
                this.batchTimeout = 16;
                break;
            case 'low':
                this.targetFPS = 30;
                this.frameInterval = 1000 / this.targetFPS;
                this.maxBatchSize = 50;
                this.batchTimeout = 32;
                break;
        }
        
        if (window.arxLogger) {
          window.arxLogger.info('Adapted settings for device performance', {
            component: 'throttled_update_manager',
            device_performance: this.devicePerformance,
            target_fps: this.targetFPS,
            max_batch_size: this.maxBatchSize,
            batch_timeout_ms: this.batchTimeout
          });
        }
    }
    
    /**
     * Start the update loop
     */
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.lastFrameTime = performance.now();
        this.animationFrameId = requestAnimationFrame(this.updateLoop.bind(this));
        
        if (window.arxLogger) {
          window.arxLogger.info('ThrottledUpdateManager: Update loop started', {
            component: 'throttled_update_manager',
            status: 'started'
          });
        }
    }
    
    /**
     * Stop the update loop
     */
    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        
        if (window.arxLogger) {
          window.arxLogger.info('ThrottledUpdateManager: Update loop stopped', {
            component: 'throttled_update_manager',
            status: 'stopped'
          });
        }
    }
    
    /**
     * Main update loop using requestAnimationFrame
     */
    updateLoop(currentTime) {
        if (!this.isRunning) return;
        
        // Calculate frame time
        const frameTime = currentTime - this.lastFrameTime;
        this.lastFrameTime = currentTime;
        
        // Track frame times for FPS calculation
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
        
        // Check if we should process updates
        if (frameTime >= this.frameInterval) {
            this.processUpdates(currentTime);
        }
        
        // Continue the loop
        this.animationFrameId = requestAnimationFrame(this.updateLoop.bind(this));
    }
    
    /**
     * Process pending updates
     */
    processUpdates(currentTime) {
        // Process high priority updates first
        const sortedUpdates = Array.from(this.pendingUpdates.entries())
            .sort((a, b) => {
                const typeA = a[0];
                const typeB = b[0];
                const priorityA = this.updateTypes[typeA]?.priority || 5;
                const priorityB = this.updateTypes[typeB]?.priority || 5;
                return priorityA - priorityB;
            });
        
        let processedCount = 0;
        const processedTypes = new Set();
        
        for (const [updateType, updateData] of sortedUpdates) {
            if (processedCount >= this.maxBatchSize) break;
            
            const updateConfig = this.updateTypes[updateType];
            if (!updateConfig) continue;
            
            // Check if enough time has passed since last update of this type
            const lastUpdate = updateData.lastUpdate || 0;
            if (currentTime - lastUpdate < updateConfig.throttle) continue;
            
            // Process the update
            this.executeUpdate(updateType, updateData);
            
            // Mark as processed
            processedTypes.add(updateType);
            processedCount++;
            
            // Update timestamp
            updateData.lastUpdate = currentTime;
        }
        
        // Remove processed updates
        for (const updateType of processedTypes) {
            this.pendingUpdates.delete(updateType);
        }
        
        // Process batched updates
        this.processBatchedUpdates();
        
        // Trigger performance event
        this.triggerEvent('updateProcessed', {
            processedCount,
            currentFPS: this.currentFPS,
            frameTime: this.frameTimes[this.frameTimes.length - 1] || 0,
            pendingUpdates: this.pendingUpdates.size
        });
    }
    
    /**
     * Queue an update for processing
     */
    queueUpdate(updateType, updateData = {}, options = {}) {
        if (!this.updateTypes[updateType]) {
            console.warn(`ThrottledUpdateManager: Unknown update type: ${updateType}`);
            return;
        }
        
        const {
            priority = this.updateTypes[updateType].priority,
            immediate = false,
            batch = false
        } = options;
        
        // Handle immediate updates
        if (immediate) {
            this.executeUpdate(updateType, updateData);
            return;
        }
        
        // Handle batched updates
        if (batch) {
            this.queueBatchedUpdate(updateType, updateData);
            return;
        }
        
        // Queue regular update
        this.pendingUpdates.set(updateType, {
            ...updateData,
            priority,
            timestamp: performance.now()
        });
    }
    
    /**
     * Queue a batched update
     */
    queueBatchedUpdate(updateType, updateData) {
        this.updateQueue.push({
            type: updateType,
            data: updateData,
            timestamp: performance.now()
        });
        
        // Process batch after timeout
        setTimeout(() => {
            this.processBatchedUpdates();
        }, this.batchTimeout);
    }
    
    /**
     * Process batched updates
     */
    processBatchedUpdates() {
        if (this.updateQueue.length === 0) return;
        
        // Group updates by type
        const groupedUpdates = new Map();
        
        for (const update of this.updateQueue) {
            if (!groupedUpdates.has(update.type)) {
                groupedUpdates.set(update.type, []);
            }
            groupedUpdates.get(update.type).push(update);
        }
        
        // Process each group
        for (const [updateType, updates] of groupedUpdates) {
            if (updates.length === 1) {
                // Single update, process normally
                this.executeUpdate(updateType, updates[0].data);
            } else {
                // Multiple updates, batch them
                this.executeBatchedUpdate(updateType, updates);
            }
        }
        
        // Clear the queue
        this.updateQueue = [];
    }
    
    /**
     * Execute a single update
     */
    executeUpdate(updateType, updateData) {
        try {
            // Trigger update event
            this.triggerEvent('update', {
                type: updateType,
                data: updateData,
                timestamp: performance.now()
            });
            
            // Trigger type-specific event
            this.triggerEvent(`${updateType}Update`, updateData);
            
        } catch (error) {
            console.error(`ThrottledUpdateManager: Error executing ${updateType} update:`, error);
        }
    }
    
    /**
     * Execute a batched update
     */
    executeBatchedUpdate(updateType, updates) {
        try {
            // Combine update data
            const batchedData = {
                updates: updates.map(u => u.data),
                count: updates.length,
                timestamp: performance.now()
            };
            
            // Trigger batched update event
            this.triggerEvent('batchedUpdate', {
                type: updateType,
                data: batchedData
            });
            
            // Trigger type-specific batched event
            this.triggerEvent(`${updateType}BatchedUpdate`, batchedData);
            
        } catch (error) {
            console.error(`ThrottledUpdateManager: Error executing batched ${updateType} update:`, error);
        }
    }
    
    /**
     * Throttle a function call
     */
    throttle(func, delay) {
        let lastCall = 0;
        return function (...args) {
            const now = performance.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return func.apply(this, args);
            }
        };
    }
    
    /**
     * Debounce a function call
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    }
    
    /**
     * Get current performance metrics
     */
    getPerformanceMetrics() {
        const avgFrameTime = this.frameTimes.length > 0 
            ? this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length 
            : 0;
        
        return {
            currentFPS: this.currentFPS,
            targetFPS: this.targetFPS,
            averageFrameTime: avgFrameTime,
            devicePerformance: this.devicePerformance,
            pendingUpdates: this.pendingUpdates.size,
            queuedUpdates: this.updateQueue.length,
            frameTimeHistory: [...this.frameTimes]
        };
    }
    
    /**
     * Set update type configuration
     */
    setUpdateTypeConfig(updateType, config) {
        this.updateTypes[updateType] = {
            ...this.updateTypes[updateType],
            ...config
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
                    console.error(`Error in throttled update event handler for ${event}:`, error);
                }
            });
        }
    }
    
    /**
     * Clear all pending updates
     */
    clearPendingUpdates() {
        this.pendingUpdates.clear();
        this.updateQueue = [];
    }
    
    /**
     * Force immediate processing of all pending updates
     */
    forceProcessUpdates() {
        const currentTime = performance.now();
        this.processUpdates(currentTime);
    }
    
    /**
     * Destroy the throttled update manager
     */
    destroy() {
        this.stop();
        this.clearPendingUpdates();
        this.eventHandlers.clear();
        if (window.arxLogger) {
          window.arxLogger.info('ThrottledUpdateManager: Destroyed', {
            component: 'throttled_update_manager',
            status: 'destroyed'
          });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThrottledUpdateManager;
} else if (typeof window !== 'undefined') {
    window.ThrottledUpdateManager = ThrottledUpdateManager;
} 