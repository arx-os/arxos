/**
 * Worker Pool for managing parallel extraction tasks
 * @module extraction/WorkerPool
 */

export class WorkerPool {
    constructor(options = {}) {
        this.options = {
            workerCount: options.workerCount || navigator.hardwareConcurrency || 4,
            workerScript: options.workerScript || './extraction.worker.js',
            timeout: options.timeout || 30000,
            debug: options.debug || false
        };
        
        this.workers = [];
        this.taskQueue = [];
        this.activeTasks = new Map();
        this.initialized = false;
    }
    
    /**
     * Initialize worker pool
     */
    async initialize() {
        if (this.initialized) return;
        
        if (this.options.debug) {
            console.log(`Initializing worker pool with ${this.options.workerCount} workers`);
        }
        
        for (let i = 0; i < this.options.workerCount; i++) {
            const worker = new Worker(this.options.workerScript);
            
            worker.id = i;
            worker.busy = false;
            
            worker.onmessage = (e) => this.handleWorkerMessage(worker, e);
            worker.onerror = (e) => this.handleWorkerError(worker, e);
            
            this.workers.push(worker);
        }
        
        this.initialized = true;
    }
    
    /**
     * Process image in parallel tiles
     * @param {HTMLCanvasElement} canvas - Input canvas
     * @param {Object} options - Extraction options
     * @returns {Promise<Array>} Combined results
     */
    async processImage(canvas, options = {}) {
        await this.initialize();
        
        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;
        
        // Calculate optimal tile size
        const tileSize = this.calculateTileSize(width, height);
        const tiles = this.generateTiles(width, height, tileSize);
        
        if (this.options.debug) {
            console.log(`Processing ${width}x${height} image with ${tiles.length} tiles`);
        }
        
        // Process each tile
        const promises = tiles.map(tile => 
            this.processTile(ctx, tile, options)
        );
        
        // Wait for all tiles to complete
        const results = await Promise.all(promises);
        
        // Combine results
        return this.combineResults(results);
    }
    
    /**
     * Calculate optimal tile size
     * @private
     */
    calculateTileSize(width, height) {
        // Balance between parallelism and overhead
        const targetTiles = this.options.workerCount * 2;
        const area = width * height;
        const tileArea = area / targetTiles;
        const tileSize = Math.sqrt(tileArea);
        
        // Round to nearest power of 2 for efficiency
        const size = Math.pow(2, Math.round(Math.log2(tileSize)));
        
        // Clamp to reasonable range
        return Math.max(128, Math.min(512, size));
    }
    
    /**
     * Generate tile coordinates
     * @private
     */
    generateTiles(width, height, tileSize) {
        const tiles = [];
        const overlap = Math.floor(tileSize * 0.1); // 10% overlap
        
        for (let y = 0; y < height; y += tileSize - overlap) {
            for (let x = 0; x < width; x += tileSize - overlap) {
                tiles.push({
                    x: x,
                    y: y,
                    width: Math.min(tileSize, width - x),
                    height: Math.min(tileSize, height - y)
                });
            }
        }
        
        return tiles;
    }
    
    /**
     * Process a single tile
     * @private
     */
    processTile(ctx, tile, options) {
        return new Promise((resolve, reject) => {
            // Get tile image data
            const imageData = ctx.getImageData(
                tile.x, tile.y, tile.width, tile.height
            );
            
            const task = {
                id: Math.random().toString(36).substr(2, 9),
                type: 'extract',
                data: {
                    imageData: imageData,
                    tileX: tile.x,
                    tileY: tile.y,
                    tileWidth: tile.width,
                    tileHeight: tile.height,
                    options: options
                },
                resolve: resolve,
                reject: reject,
                startTime: performance.now()
            };
            
            // Add to queue
            this.taskQueue.push(task);
            this.processTasks();
        });
    }
    
    /**
     * Process queued tasks
     * @private
     */
    processTasks() {
        while (this.taskQueue.length > 0) {
            const worker = this.getAvailableWorker();
            if (!worker) break;
            
            const task = this.taskQueue.shift();
            this.runTask(worker, task);
        }
    }
    
    /**
     * Get available worker
     * @private
     */
    getAvailableWorker() {
        return this.workers.find(w => !w.busy);
    }
    
    /**
     * Run task on worker
     * @private
     */
    runTask(worker, task) {
        worker.busy = true;
        this.activeTasks.set(worker.id, task);
        
        // Set timeout
        const timeoutId = setTimeout(() => {
            task.reject(new Error(`Task timeout after ${this.options.timeout}ms`));
            worker.busy = false;
            this.activeTasks.delete(worker.id);
            this.processTasks();
        }, this.options.timeout);
        
        task.timeoutId = timeoutId;
        
        // Send task to worker
        worker.postMessage({
            type: task.type,
            data: task.data
        });
    }
    
    /**
     * Handle worker message
     * @private
     */
    handleWorkerMessage(worker, event) {
        const task = this.activeTasks.get(worker.id);
        if (!task) return;
        
        const { type, result, error } = event.data;
        
        if (type === 'error') {
            task.reject(new Error(error));
        } else if (type === 'extract-complete') {
            task.resolve(result);
        }
        
        // Cleanup
        clearTimeout(task.timeoutId);
        worker.busy = false;
        this.activeTasks.delete(worker.id);
        
        // Process next task
        this.processTasks();
        
        if (this.options.debug) {
            const duration = performance.now() - task.startTime;
            console.log(`Worker ${worker.id} completed task in ${duration.toFixed(2)}ms`);
        }
    }
    
    /**
     * Handle worker error
     * @private
     */
    handleWorkerError(worker, error) {
        console.error(`Worker ${worker.id} error:`, error);
        
        const task = this.activeTasks.get(worker.id);
        if (task) {
            task.reject(error);
            clearTimeout(task.timeoutId);
            this.activeTasks.delete(worker.id);
        }
        
        worker.busy = false;
        this.processTasks();
    }
    
    /**
     * Combine results from all tiles
     * @private
     */
    combineResults(results) {
        const allLines = [];
        
        for (const result of results) {
            if (result && result.lines) {
                allLines.push(...result.lines);
            }
        }
        
        // Remove duplicates at tile boundaries
        return this.removeDuplicates(allLines);
    }
    
    /**
     * Remove duplicate lines at tile boundaries
     * @private
     */
    removeDuplicates(lines) {
        const unique = [];
        const threshold = 10; // Distance threshold
        
        for (const line of lines) {
            let isDuplicate = false;
            
            for (const existing of unique) {
                // Check if lines are very similar
                const d1 = Math.hypot(line.x1 - existing.x1, line.y1 - existing.y1);
                const d2 = Math.hypot(line.x2 - existing.x2, line.y2 - existing.y2);
                
                if (d1 < threshold && d2 < threshold) {
                    isDuplicate = true;
                    // Update confidence if higher
                    if (line.confidence > existing.confidence) {
                        existing.confidence = line.confidence;
                    }
                    break;
                }
            }
            
            if (!isDuplicate) {
                unique.push(line);
            }
        }
        
        return unique;
    }
    
    /**
     * Terminate all workers
     */
    terminate() {
        for (const worker of this.workers) {
            worker.terminate();
        }
        
        this.workers = [];
        this.taskQueue = [];
        this.activeTasks.clear();
        this.initialized = false;
    }
}

/**
 * Singleton instance for convenience
 */
let defaultPool = null;

export function getDefaultPool() {
    if (!defaultPool) {
        defaultPool = new WorkerPool();
    }
    return defaultPool;
}

export default WorkerPool;