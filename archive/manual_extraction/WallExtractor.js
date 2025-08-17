/**
 * Main wall extraction class that combines all algorithms
 * @module extraction/WallExtractor
 */

import { findOptimalThreshold, adaptiveThreshold } from './threshold.js';
import { houghTransform, probabilisticHough } from './hough.js';
import { cannyEdgeDetection, sobelEdgeDetection } from './edge.js';
import { mergeWalls, filterArchitectural, snapToGrid } from './postprocess.js';

/**
 * WallExtractor - Main class for extracting walls from PDFs
 */
export class WallExtractor {
    constructor(options = {}) {
        this.options = {
            method: 'hybrid',              // 'hough', 'probabilistic', 'hybrid'
            preprocess: true,              // Apply preprocessing
            postprocess: true,             // Apply postprocessing
            multiscale: false,             // Use multi-scale analysis
            scales: [0.5, 1.0, 2.0],      // Scales for multi-scale
            gridSize: 10,                  // Grid size for snapping
            minWallLength: 50,             // Minimum wall length in pixels
            maxWallThickness: 20,          // Maximum wall thickness
            confidenceThreshold: 0.5,      // Minimum confidence score
            debug: false,                  // Enable debug output
            ...options
        };
        
        this.stats = {};
    }
    
    /**
     * Extract walls from canvas
     * @param {HTMLCanvasElement} canvas - Input canvas
     * @returns {Promise<Object>} Extraction results
     */
    async extract(canvas) {
        const startTime = performance.now();
        
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        let walls = [];
        
        if (this.options.multiscale) {
            walls = await this.multiscaleExtraction(canvas);
        } else {
            walls = await this.singleScaleExtraction(imageData);
        }
        
        // Postprocessing
        if (this.options.postprocess) {
            walls = this.postprocessWalls(walls, imageData.width, imageData.height);
        }
        
        const endTime = performance.now();
        
        // Gather statistics
        this.stats = {
            processingTime: endTime - startTime,
            wallCount: walls.length,
            imageSize: { width: imageData.width, height: imageData.height },
            method: this.options.method,
            confidence: this.calculateOverallConfidence(walls)
        };
        
        return {
            walls,
            stats: this.stats,
            debug: this.options.debug ? this.debugInfo : null
        };
    }
    
    /**
     * Single scale extraction
     * @private
     */
    async singleScaleExtraction(imageData) {
        const { width, height } = imageData;
        
        // Step 1: Find optimal threshold
        const thresholdResult = findOptimalThreshold(imageData);
        
        if (this.options.debug) {
            console.log('Threshold:', thresholdResult);
        }
        
        // Step 2: Create binary image
        let binaryImage;
        if (thresholdResult.confidence > 0.7) {
            // Use simple threshold if confident
            binaryImage = this.applyThreshold(imageData, thresholdResult.threshold);
        } else {
            // Use adaptive threshold for complex images
            binaryImage = adaptiveThreshold(imageData);
        }
        
        // Step 3: Edge detection (optional preprocessing)
        if (this.options.preprocess) {
            const edges = cannyEdgeDetection(imageData, {
                lowThreshold: 50,
                highThreshold: 150
            });
            
            // Combine with binary image
            for (let i = 0; i < binaryImage.length; i++) {
                binaryImage[i] = binaryImage[i] || edges[i];
            }
        }
        
        // Step 4: Line detection
        let walls = [];
        
        switch (this.options.method) {
            case 'hough':
                walls = houghTransform(binaryImage, width, height, {
                    threshold: 50,
                    minLineLength: this.options.minWallLength,
                    maxLineGap: 10
                });
                break;
                
            case 'probabilistic':
                walls = probabilisticHough(binaryImage, width, height, {
                    threshold: 10,
                    minLineLength: this.options.minWallLength,
                    maxLineGap: 10
                });
                break;
                
            case 'hybrid':
            default:
                // Use both methods and combine results
                const houghWalls = houghTransform(binaryImage, width, height, {
                    threshold: 50,
                    minLineLength: this.options.minWallLength
                });
                
                const probWalls = probabilisticHough(binaryImage, width, height, {
                    threshold: 10,
                    minLineLength: this.options.minWallLength
                });
                
                walls = this.combineResults(houghWalls, probWalls);
                break;
        }
        
        return walls;
    }
    
    /**
     * Multi-scale extraction for better accuracy
     * @private
     */
    async multiscaleExtraction(canvas) {
        const results = [];
        
        for (const scale of this.options.scales) {
            // Create scaled canvas
            const scaledCanvas = document.createElement('canvas');
            const scaledCtx = scaledCanvas.getContext('2d');
            
            scaledCanvas.width = Math.floor(canvas.width * scale);
            scaledCanvas.height = Math.floor(canvas.height * scale);
            
            // Draw scaled image
            scaledCtx.drawImage(
                canvas,
                0, 0, canvas.width, canvas.height,
                0, 0, scaledCanvas.width, scaledCanvas.height
            );
            
            // Extract at this scale
            const imageData = scaledCtx.getImageData(
                0, 0, scaledCanvas.width, scaledCanvas.height
            );
            
            const walls = await this.singleScaleExtraction(imageData);
            
            // Scale walls back to original size
            const scaledWalls = walls.map(wall => ({
                ...wall,
                x1: wall.x1 / scale,
                y1: wall.y1 / scale,
                x2: wall.x2 / scale,
                y2: wall.y2 / scale,
                scale: scale,
                confidence: wall.confidence * (scale === 1.0 ? 1.0 : 0.8)
            }));
            
            results.push(...scaledWalls);
        }
        
        // Merge walls from different scales
        return this.mergeMultiscaleResults(results);
    }
    
    /**
     * Apply simple threshold to image
     * @private
     */
    applyThreshold(imageData, threshold) {
        const { data, width, height } = imageData;
        const binary = new Uint8Array(width * height);
        
        for (let i = 0; i < data.length; i += 4) {
            const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
            binary[i / 4] = brightness < threshold ? 255 : 0;
        }
        
        return binary;
    }
    
    /**
     * Combine results from different methods
     * @private
     */
    combineResults(walls1, walls2) {
        const combined = [...walls1];
        const threshold = 20; // Distance threshold for duplicate detection
        
        for (const wall2 of walls2) {
            let isDuplicate = false;
            
            for (const wall1 of walls1) {
                const dist = this.wallDistance(wall1, wall2);
                if (dist < threshold) {
                    isDuplicate = true;
                    // Update confidence if not duplicate
                    wall1.confidence = Math.max(wall1.confidence || 0.5, wall2.confidence || 0.5);
                    break;
                }
            }
            
            if (!isDuplicate) {
                combined.push(wall2);
            }
        }
        
        return combined;
    }
    
    /**
     * Calculate distance between two walls
     * @private
     */
    wallDistance(wall1, wall2) {
        // Calculate minimum distance between line segments
        const d1 = Math.hypot(wall1.x1 - wall2.x1, wall1.y1 - wall2.y1);
        const d2 = Math.hypot(wall1.x2 - wall2.x2, wall1.y2 - wall2.y2);
        const d3 = Math.hypot(wall1.x1 - wall2.x2, wall1.y1 - wall2.y2);
        const d4 = Math.hypot(wall1.x2 - wall2.x1, wall1.y2 - wall2.y1);
        
        return Math.min(d1, d2, d3, d4);
    }
    
    /**
     * Merge results from multiple scales
     * @private
     */
    mergeMultiscaleResults(walls) {
        // Group similar walls and keep the best one
        const groups = [];
        const used = new Set();
        
        for (let i = 0; i < walls.length; i++) {
            if (used.has(i)) continue;
            
            const group = [walls[i]];
            used.add(i);
            
            for (let j = i + 1; j < walls.length; j++) {
                if (used.has(j)) continue;
                
                const dist = this.wallDistance(walls[i], walls[j]);
                if (dist < 30) {
                    group.push(walls[j]);
                    used.add(j);
                }
            }
            
            groups.push(group);
        }
        
        // Select best wall from each group
        return groups.map(group => {
            // Sort by confidence and scale (prefer scale 1.0)
            group.sort((a, b) => {
                const scoreA = a.confidence * (a.scale === 1.0 ? 1.2 : 1.0);
                const scoreB = b.confidence * (b.scale === 1.0 ? 1.2 : 1.0);
                return scoreB - scoreA;
            });
            
            return group[0];
        });
    }
    
    /**
     * Post-process walls
     * @private
     */
    postprocessWalls(walls, width, height) {
        let processed = [...walls];
        
        // Step 1: Merge nearby parallel walls
        processed = mergeWalls(processed, {
            parallelThreshold: 5,
            distanceThreshold: 15
        });
        
        // Step 2: Filter out non-architectural elements
        processed = filterArchitectural(processed, {
            minLength: this.options.minWallLength,
            maxThickness: this.options.maxWallThickness,
            imageWidth: width,
            imageHeight: height
        });
        
        // Step 3: Snap to grid
        if (this.options.gridSize > 0) {
            processed = snapToGrid(processed, this.options.gridSize);
        }
        
        // Step 4: Ensure connectivity
        processed = this.ensureConnectivity(processed);
        
        return processed;
    }
    
    /**
     * Ensure walls are properly connected
     * @private
     */
    ensureConnectivity(walls) {
        const threshold = 10; // Connection threshold in pixels
        const connected = [...walls];
        
        // Extend walls to meet at intersections
        for (let i = 0; i < connected.length; i++) {
            for (let j = i + 1; j < connected.length; j++) {
                const wall1 = connected[i];
                const wall2 = connected[j];
                
                // Check endpoints proximity
                const connections = [
                    { p1: { x: wall1.x1, y: wall1.y1 }, p2: { x: wall2.x1, y: wall2.y1 }, w1End: 'start', w2End: 'start' },
                    { p1: { x: wall1.x1, y: wall1.y1 }, p2: { x: wall2.x2, y: wall2.y2 }, w1End: 'start', w2End: 'end' },
                    { p1: { x: wall1.x2, y: wall1.y2 }, p2: { x: wall2.x1, y: wall2.y1 }, w1End: 'end', w2End: 'start' },
                    { p1: { x: wall1.x2, y: wall1.y2 }, p2: { x: wall2.x2, y: wall2.y2 }, w1End: 'end', w2End: 'end' }
                ];
                
                for (const conn of connections) {
                    const dist = Math.hypot(conn.p1.x - conn.p2.x, conn.p1.y - conn.p2.y);
                    
                    if (dist < threshold && dist > 0) {
                        // Snap endpoints together
                        const midX = (conn.p1.x + conn.p2.x) / 2;
                        const midY = (conn.p1.y + conn.p2.y) / 2;
                        
                        if (conn.w1End === 'start') {
                            wall1.x1 = midX;
                            wall1.y1 = midY;
                        } else {
                            wall1.x2 = midX;
                            wall1.y2 = midY;
                        }
                        
                        if (conn.w2End === 'start') {
                            wall2.x1 = midX;
                            wall2.y1 = midY;
                        } else {
                            wall2.x2 = midX;
                            wall2.y2 = midY;
                        }
                    }
                }
            }
        }
        
        return connected;
    }
    
    /**
     * Calculate overall confidence score
     * @private
     */
    calculateOverallConfidence(walls) {
        if (walls.length === 0) return 0;
        
        const avgConfidence = walls.reduce((sum, wall) => 
            sum + (wall.confidence || 0.5), 0) / walls.length;
        
        // Factor in wall count (too few or too many is suspicious)
        let countFactor = 1.0;
        if (walls.length < 4) countFactor = 0.5;
        else if (walls.length > 200) countFactor = 0.7;
        
        return avgConfidence * countFactor;
    }
}

export default WallExtractor;