/**
 * Web Worker for parallel wall extraction
 * Processes image tiles independently for better performance
 */

// Import extraction functions (available in worker context)
importScripts('./threshold.js', './hough.js', './edge.js');

/**
 * Message handler
 */
self.onmessage = function(e) {
    const { type, data } = e.data;
    
    switch (type) {
        case 'extract':
            extractTile(data);
            break;
            
        case 'threshold':
            processThreshold(data);
            break;
            
        case 'edge':
            processEdge(data);
            break;
            
        case 'hough':
            processHough(data);
            break;
            
        default:
            self.postMessage({
                type: 'error',
                error: `Unknown message type: ${type}`
            });
    }
};

/**
 * Extract walls from a tile
 */
function extractTile(data) {
    const { 
        imageData, 
        tileX, 
        tileY, 
        tileWidth, 
        tileHeight,
        options 
    } = data;
    
    try {
        const startTime = performance.now();
        
        // Find optimal threshold
        const threshold = findOptimalThreshold(imageData);
        
        // Create binary image
        const binary = applyThreshold(imageData, threshold.threshold);
        
        // Apply edge detection if requested
        let edges = binary;
        if (options.useEdgeDetection) {
            edges = sobelEdgeDetection(imageData, options.edgeThreshold || 100);
            
            // Combine with binary
            for (let i = 0; i < binary.length; i++) {
                binary[i] = binary[i] || edges[i];
            }
        }
        
        // Detect lines using Hough transform
        const lines = houghTransform(
            binary,
            tileWidth,
            tileHeight,
            {
                threshold: options.houghThreshold || 50,
                minLineLength: options.minLineLength || 40,
                maxLineGap: options.maxLineGap || 10
            }
        );
        
        // Adjust coordinates to global space
        const globalLines = lines.map(line => ({
            ...line,
            x1: line.x1 + tileX,
            y1: line.y1 + tileY,
            x2: line.x2 + tileX,
            y2: line.y2 + tileY,
            tile: { x: tileX, y: tileY, width: tileWidth, height: tileHeight }
        }));
        
        const endTime = performance.now();
        
        self.postMessage({
            type: 'extract-complete',
            result: {
                lines: globalLines,
                tile: { x: tileX, y: tileY },
                processingTime: endTime - startTime,
                threshold: threshold.threshold
            }
        });
        
    } catch (error) {
        self.postMessage({
            type: 'error',
            error: error.message,
            tile: { x: tileX, y: tileY }
        });
    }
}

/**
 * Process threshold detection
 */
function processThreshold(data) {
    const { imageData, method } = data;
    
    try {
        let result;
        
        switch (method) {
            case 'otsu':
                result = otsuThreshold(imageData);
                break;
                
            case 'adaptive':
                result = adaptiveThreshold(imageData);
                break;
                
            case 'optimal':
            default:
                result = findOptimalThreshold(imageData);
                break;
        }
        
        self.postMessage({
            type: 'threshold-complete',
            result
        });
        
    } catch (error) {
        self.postMessage({
            type: 'error',
            error: error.message
        });
    }
}

/**
 * Process edge detection
 */
function processEdge(data) {
    const { imageData, method, options } = data;
    
    try {
        let edges;
        
        switch (method) {
            case 'canny':
                edges = cannyEdgeDetection(imageData, options);
                break;
                
            case 'sobel':
            default:
                edges = sobelEdgeDetection(imageData, options.threshold || 100);
                break;
        }
        
        self.postMessage({
            type: 'edge-complete',
            result: edges
        });
        
    } catch (error) {
        self.postMessage({
            type: 'error',
            error: error.message
        });
    }
}

/**
 * Process Hough transform
 */
function processHough(data) {
    const { binaryImage, width, height, method, options } = data;
    
    try {
        let lines;
        
        switch (method) {
            case 'probabilistic':
                lines = probabilisticHough(binaryImage, width, height, options);
                break;
                
            case 'standard':
            default:
                lines = houghTransform(binaryImage, width, height, options);
                break;
        }
        
        self.postMessage({
            type: 'hough-complete',
            result: lines
        });
        
    } catch (error) {
        self.postMessage({
            type: 'error',
            error: error.message
        });
    }
}

/**
 * Apply simple threshold
 */
function applyThreshold(imageData, threshold) {
    const { data, width, height } = imageData;
    const binary = new Uint8Array(width * height);
    
    for (let i = 0; i < data.length; i += 4) {
        const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
        binary[i / 4] = brightness < threshold ? 255 : 0;
    }
    
    return binary;
}

// Simplified versions of functions for worker context
// (Full implementations would be imported from modules)

function findOptimalThreshold(imageData) {
    const candidates = [250, 245, 240, 235, 230, 225, 220, 210, 200, 180, 160, 140, 120];
    const { data, width, height } = imageData;
    const totalPixels = width * height;
    
    for (const threshold of candidates) {
        let darkCount = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
            if (brightness < threshold) darkCount++;
        }
        
        const percentage = (darkCount / totalPixels) * 100;
        
        if (percentage >= 0.5 && percentage <= 10) {
            return {
                threshold,
                darkPixels: darkCount,
                percentage
            };
        }
    }
    
    return { threshold: 200, darkPixels: 0, percentage: 0 };
}

function sobelEdgeDetection(imageData, threshold) {
    const { data, width, height } = imageData;
    const edges = new Uint8Array(width * height);
    
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = y * width + x;
            
            // Get 3x3 neighborhood brightness values
            const tl = getBrightness(data, ((y-1) * width + (x-1)) * 4);
            const tm = getBrightness(data, ((y-1) * width + x) * 4);
            const tr = getBrightness(data, ((y-1) * width + (x+1)) * 4);
            const ml = getBrightness(data, (y * width + (x-1)) * 4);
            const mr = getBrightness(data, (y * width + (x+1)) * 4);
            const bl = getBrightness(data, ((y+1) * width + (x-1)) * 4);
            const bm = getBrightness(data, ((y+1) * width + x) * 4);
            const br = getBrightness(data, ((y+1) * width + (x+1)) * 4);
            
            // Sobel operators
            const gx = -tl - 2*ml - bl + tr + 2*mr + br;
            const gy = -tl - 2*tm - tr + bl + 2*bm + br;
            
            const magnitude = Math.sqrt(gx * gx + gy * gy);
            edges[idx] = magnitude > threshold ? 255 : 0;
        }
    }
    
    return edges;
}

function getBrightness(data, idx) {
    return (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
}

function houghTransform(binaryImage, width, height, options) {
    // Simplified Hough transform for worker
    const lines = [];
    const threshold = options.threshold || 50;
    
    // This would be the full implementation
    // For now, return placeholder
    return lines;
}