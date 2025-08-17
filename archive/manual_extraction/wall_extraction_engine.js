/**
 * Universal Wall Extraction Engine
 * Processes ANY building floor plan image (photo, scan, PDF render) 
 * and extracts walls as geometric primitives
 */

class WallExtractionEngine {
    constructor() {
        this.debugMode = false;
    }

    /**
     * Main entry point - processes any image and returns walls
     * @param {ImageData} imageData - Raw image data from canvas
     * @returns {Array} Array of wall objects with coordinates
     */
    async extractWalls(imageData) {
        // Step 1: Preprocessing
        const preprocessed = this.preprocess(imageData);
        
        // Step 2: Edge Detection
        const edges = this.detectEdges(preprocessed);
        
        // Step 3: Line Detection using Hough Transform
        const lines = this.houghTransform(edges);
        
        // Step 4: Merge and filter lines into walls
        const walls = this.linesToWalls(lines);
        
        // Step 5: Post-processing and cleanup
        const finalWalls = this.postProcess(walls);
        
        return finalWalls;
    }

    /**
     * Preprocessing pipeline to normalize any input image
     */
    preprocess(imageData) {
        // Convert to grayscale
        let gray = this.toGrayscale(imageData);
        
        // Adaptive thresholding for varying lighting conditions
        gray = this.adaptiveThreshold(gray);
        
        // Morphological operations to clean up noise
        gray = this.morphologicalClean(gray);
        
        return gray;
    }

    /**
     * Convert image to grayscale
     */
    toGrayscale(imageData) {
        const width = imageData.width;
        const height = imageData.height;
        const data = imageData.data;
        const gray = new Uint8Array(width * height);
        
        for (let i = 0, j = 0; i < data.length; i += 4, j++) {
            // Standard grayscale conversion
            gray[j] = Math.round(0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]);
        }
        
        return { data: gray, width, height };
    }

    /**
     * Adaptive threshold to handle varying lighting and paper quality
     */
    adaptiveThreshold(grayImage) {
        const { data, width, height } = grayImage;
        const output = new Uint8Array(data.length);
        const windowSize = 25; // Larger window for floor plans
        const threshold = 15; // Higher threshold to reduce noise
        
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = y * width + x;
                
                // Calculate local mean
                let sum = 0;
                let count = 0;
                
                for (let dy = -windowSize; dy <= windowSize; dy++) {
                    for (let dx = -windowSize; dx <= windowSize; dx++) {
                        const ny = y + dy;
                        const nx = x + dx;
                        
                        if (ny >= 0 && ny < height && nx >= 0 && nx < width) {
                            sum += data[ny * width + nx];
                            count++;
                        }
                    }
                }
                
                const localMean = sum / count;
                output[idx] = data[idx] < (localMean - threshold) ? 0 : 255;
            }
        }
        
        return { data: output, width, height };
    }

    /**
     * Morphological operations to clean up the image
     */
    morphologicalClean(binaryImage) {
        // Erosion followed by dilation (opening) to remove small noise
        let cleaned = this.erode(binaryImage);
        cleaned = this.dilate(cleaned);
        
        // Close small gaps in lines
        cleaned = this.dilate(cleaned);
        cleaned = this.erode(cleaned);
        
        return cleaned;
    }

    /**
     * Morphological erosion
     */
    erode(image) {
        const { data, width, height } = image;
        const output = new Uint8Array(data.length);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = y * width + x;
                
                // Check 3x3 neighborhood
                let min = 255;
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        const nidx = (y + dy) * width + (x + dx);
                        min = Math.min(min, data[nidx]);
                    }
                }
                
                output[idx] = min;
            }
        }
        
        return { data: output, width, height };
    }

    /**
     * Morphological dilation
     */
    dilate(image) {
        const { data, width, height } = image;
        const output = new Uint8Array(data.length);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = y * width + x;
                
                // Check 3x3 neighborhood
                let max = 0;
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        const nidx = (y + dy) * width + (x + dx);
                        max = Math.max(max, data[nidx]);
                    }
                }
                
                output[idx] = max;
            }
        }
        
        return { data: output, width, height };
    }

    /**
     * Edge detection using Canny edge detector
     */
    detectEdges(binaryImage) {
        const { data, width, height } = binaryImage;
        
        // Sobel operators for gradient calculation
        const sobelX = [
            [-1, 0, 1],
            [-2, 0, 2],
            [-1, 0, 1]
        ];
        
        const sobelY = [
            [-1, -2, -1],
            [0, 0, 0],
            [1, 2, 1]
        ];
        
        const gradientMag = new Float32Array(width * height);
        const gradientDir = new Float32Array(width * height);
        
        // Calculate gradients
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                let gx = 0, gy = 0;
                
                // Apply Sobel operators
                for (let dy = -1; dy <= 1; dy++) {
                    for (let dx = -1; dx <= 1; dx++) {
                        const pixel = data[(y + dy) * width + (x + dx)];
                        gx += pixel * sobelX[dy + 1][dx + 1];
                        gy += pixel * sobelY[dy + 1][dx + 1];
                    }
                }
                
                const idx = y * width + x;
                gradientMag[idx] = Math.sqrt(gx * gx + gy * gy);
                gradientDir[idx] = Math.atan2(gy, gx);
            }
        }
        
        // Non-maximum suppression
        const edges = this.nonMaxSuppression(gradientMag, gradientDir, width, height);
        
        // Double thresholding and edge tracking
        const finalEdges = this.doubleThreshold(edges, width, height);
        
        return finalEdges;
    }

    /**
     * Non-maximum suppression for edge thinning
     */
    nonMaxSuppression(gradientMag, gradientDir, width, height) {
        const output = new Uint8Array(width * height);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = y * width + x;
                const mag = gradientMag[idx];
                const angle = gradientDir[idx];
                
                // Quantize angle to 4 directions
                let q = Math.round(angle / (Math.PI / 4)) % 4;
                if (q < 0) q += 4;
                
                let n1, n2;
                
                // Get neighbors based on gradient direction
                switch (q) {
                    case 0: // Horizontal edge
                        n1 = gradientMag[idx - 1];
                        n2 = gradientMag[idx + 1];
                        break;
                    case 1: // Diagonal /
                        n1 = gradientMag[idx - width - 1];
                        n2 = gradientMag[idx + width + 1];
                        break;
                    case 2: // Vertical edge
                        n1 = gradientMag[idx - width];
                        n2 = gradientMag[idx + width];
                        break;
                    case 3: // Diagonal \
                        n1 = gradientMag[idx - width + 1];
                        n2 = gradientMag[idx + width - 1];
                        break;
                }
                
                // Keep only if local maximum
                if (mag >= n1 && mag >= n2 && mag > 50) {
                    output[idx] = Math.min(255, mag);
                }
            }
        }
        
        return output;
    }

    /**
     * Double thresholding for edge detection
     */
    doubleThreshold(edges, width, height) {
        const lowThreshold = 50;
        const highThreshold = 150;
        const output = new Uint8Array(edges.length);
        
        // Mark strong and weak edges
        for (let i = 0; i < edges.length; i++) {
            if (edges[i] >= highThreshold) {
                output[i] = 255; // Strong edge
            } else if (edges[i] >= lowThreshold) {
                output[i] = 128; // Weak edge
            }
        }
        
        // Connect weak edges to strong edges
        let changed = true;
        while (changed) {
            changed = false;
            
            for (let y = 1; y < height - 1; y++) {
                for (let x = 1; x < width - 1; x++) {
                    const idx = y * width + x;
                    
                    if (output[idx] === 128) {
                        // Check if connected to strong edge
                        let hasStrongNeighbor = false;
                        
                        for (let dy = -1; dy <= 1; dy++) {
                            for (let dx = -1; dx <= 1; dx++) {
                                if (output[(y + dy) * width + (x + dx)] === 255) {
                                    hasStrongNeighbor = true;
                                    break;
                                }
                            }
                        }
                        
                        if (hasStrongNeighbor) {
                            output[idx] = 255;
                            changed = true;
                        }
                    }
                }
            }
        }
        
        // Remove weak edges not connected to strong edges
        for (let i = 0; i < output.length; i++) {
            if (output[i] === 128) {
                output[i] = 0;
            }
        }
        
        return { data: output, width, height };
    }

    /**
     * Hough Transform for line detection
     */
    houghTransform(edgeImage) {
        const { data, width, height } = edgeImage;
        const lines = [];
        
        // Hough parameters - TUNED for floor plans
        const rhoResolution = 1;
        const thetaResolution = Math.PI / 180;
        const threshold = Math.min(width, height) / 10; // Balance between noise and detail
        
        // Calculate maximum rho
        const maxRho = Math.sqrt(width * width + height * height);
        const rhoSize = Math.ceil(maxRho * 2);
        
        // Create accumulator array
        const accumulator = new Int32Array(rhoSize * 180);
        
        // Vote in Hough space
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                if (data[y * width + x] === 0) continue;
                
                // For each edge point, vote for all possible lines through it
                for (let theta = 0; theta < 180; theta++) {
                    const thetaRad = theta * thetaResolution;
                    const rho = x * Math.cos(thetaRad) + y * Math.sin(thetaRad);
                    const rhoIdx = Math.round(rho + maxRho);
                    
                    accumulator[rhoIdx * 180 + theta]++;
                }
            }
        }
        
        // Find peaks in accumulator
        for (let rhoIdx = 0; rhoIdx < rhoSize; rhoIdx++) {
            for (let theta = 0; theta < 180; theta++) {
                const votes = accumulator[rhoIdx * 180 + theta];
                
                if (votes >= threshold) {
                    // Check if local maximum
                    let isMax = true;
                    
                    for (let dr = -5; dr <= 5; dr++) {
                        for (let dt = -5; dt <= 5; dt++) {
                            const nr = rhoIdx + dr;
                            const nt = (theta + dt + 180) % 180;
                            
                            if (nr >= 0 && nr < rhoSize) {
                                if (accumulator[nr * 180 + nt] > votes) {
                                    isMax = false;
                                    break;
                                }
                            }
                        }
                        if (!isMax) break;
                    }
                    
                    if (isMax) {
                        const rho = rhoIdx - maxRho;
                        const thetaRad = theta * thetaResolution;
                        
                        // Convert to line endpoints
                        const line = this.houghLineToSegment(rho, thetaRad, width, height);
                        if (line) {
                            lines.push({
                                ...line,
                                votes: votes,
                                rho: rho,
                                theta: thetaRad
                            });
                        }
                    }
                }
            }
        }
        
        return lines;
    }

    /**
     * Convert Hough parameters to line segment
     */
    houghLineToSegment(rho, theta, width, height) {
        const cos = Math.cos(theta);
        const sin = Math.sin(theta);
        
        // Find intersections with image boundaries
        const points = [];
        
        // Top boundary (y = 0)
        const x1 = rho / cos;
        if (x1 >= 0 && x1 <= width) {
            points.push({ x: x1, y: 0 });
        }
        
        // Bottom boundary (y = height)
        const x2 = (rho - height * sin) / cos;
        if (x2 >= 0 && x2 <= width) {
            points.push({ x: x2, y: height });
        }
        
        // Left boundary (x = 0)
        const y1 = rho / sin;
        if (y1 >= 0 && y1 <= height) {
            points.push({ x: 0, y: y1 });
        }
        
        // Right boundary (x = width)
        const y2 = (rho - width * cos) / sin;
        if (y2 >= 0 && y2 <= height) {
            points.push({ x: width, y: y2 });
        }
        
        if (points.length >= 2) {
            return {
                x1: Math.round(points[0].x),
                y1: Math.round(points[0].y),
                x2: Math.round(points[1].x),
                y2: Math.round(points[1].y)
            };
        }
        
        return null;
    }

    /**
     * Convert detected lines to wall segments
     */
    linesToWalls(lines) {
        const walls = [];
        
        // Group parallel lines that are close together
        const groups = this.groupParallelLines(lines);
        
        // Merge each group into wall segments
        for (const group of groups) {
            const mergedWalls = this.mergeLineGroup(group);
            walls.push(...mergedWalls);
        }
        
        return walls;
    }

    /**
     * Group lines that are parallel and close
     */
    groupParallelLines(lines) {
        const groups = [];
        const used = new Set();
        
        for (let i = 0; i < lines.length; i++) {
            if (used.has(i)) continue;
            
            const group = [lines[i]];
            used.add(i);
            
            for (let j = i + 1; j < lines.length; j++) {
                if (used.has(j)) continue;
                
                // Check if parallel (similar theta)
                const thetaDiff = Math.abs(lines[i].theta - lines[j].theta);
                if (thetaDiff < 0.1 || Math.abs(thetaDiff - Math.PI) < 0.1) {
                    // Check if close (similar rho)
                    const rhoDiff = Math.abs(lines[i].rho - lines[j].rho);
                    if (rhoDiff < 20) {
                        group.push(lines[j]);
                        used.add(j);
                    }
                }
            }
            
            groups.push(group);
        }
        
        return groups;
    }

    /**
     * Merge a group of parallel lines into wall segments
     */
    mergeLineGroup(group) {
        if (group.length === 0) return [];
        
        // Average the line parameters
        let avgRho = 0, avgTheta = 0;
        let totalVotes = 0;
        
        for (const line of group) {
            avgRho += line.rho * line.votes;
            avgTheta += line.theta * line.votes;
            totalVotes += line.votes;
        }
        
        avgRho /= totalVotes;
        avgTheta /= totalVotes;
        
        // Determine if horizontal or vertical
        const isVertical = Math.abs(Math.cos(avgTheta)) > Math.abs(Math.sin(avgTheta));
        
        // Create wall segment
        const wall = {
            x1: group[0].x1,
            y1: group[0].y1,
            x2: group[0].x2,
            y2: group[0].y2,
            type: isVertical ? 'vertical' : 'horizontal',
            confidence: Math.min(1.0, totalVotes / 100)
        };
        
        return [wall];
    }

    /**
     * Post-process walls to clean up and finalize
     */
    postProcess(walls) {
        // Remove duplicate walls
        let cleaned = this.removeDuplicates(walls);
        
        // Extend walls to intersections
        cleaned = this.extendToIntersections(cleaned);
        
        // Remove very short segments - TUNED for floor plans
        cleaned = cleaned.filter(wall => {
            const length = Math.sqrt(
                Math.pow(wall.x2 - wall.x1, 2) + 
                Math.pow(wall.y2 - wall.y1, 2)
            );
            return length > 30; // Balanced minimum wall length for room detection
        });
        
        // Filter to primarily horizontal and vertical walls (common in floor plans)
        cleaned = cleaned.filter(wall => {
            const angle = Math.atan2(wall.y2 - wall.y1, wall.x2 - wall.x1);
            const deg = Math.abs(angle * 180 / Math.PI);
            
            // Keep walls that are roughly horizontal (0°, 180°) or vertical (90°, 270°)
            const isHorizontal = deg < 10 || deg > 170;
            const isVertical = (deg > 80 && deg < 100);
            const isDiagonal = (deg > 35 && deg < 55) || (deg > 125 && deg < 145); // 45° angles with tolerance
            
            return isHorizontal || isVertical || isDiagonal;
        });
        
        return cleaned;
    }

    /**
     * Remove duplicate walls
     */
    removeDuplicates(walls) {
        const unique = [];
        
        for (const wall of walls) {
            let isDuplicate = false;
            
            for (const existing of unique) {
                const dist1 = this.pointDistance(wall.x1, wall.y1, existing.x1, existing.y1);
                const dist2 = this.pointDistance(wall.x2, wall.y2, existing.x2, existing.y2);
                const dist3 = this.pointDistance(wall.x1, wall.y1, existing.x2, existing.y2);
                const dist4 = this.pointDistance(wall.x2, wall.y2, existing.x1, existing.y1);
                
                if ((dist1 < 10 && dist2 < 10) || (dist3 < 10 && dist4 < 10)) {
                    isDuplicate = true;
                    break;
                }
            }
            
            if (!isDuplicate) {
                unique.push(wall);
            }
        }
        
        return unique;
    }

    /**
     * Extend walls to meet at intersections
     */
    extendToIntersections(walls) {
        const extended = [];
        
        for (const wall of walls) {
            let newWall = { ...wall };
            
            // Find potential intersections with other walls
            for (const other of walls) {
                if (wall === other) continue;
                
                // Check if walls are perpendicular
                if (wall.type === other.type) continue;
                
                // Find intersection point
                const intersection = this.lineIntersection(wall, other);
                
                if (intersection) {
                    // Extend wall to intersection if close
                    const dist1 = this.pointDistance(wall.x1, wall.y1, intersection.x, intersection.y);
                    const dist2 = this.pointDistance(wall.x2, wall.y2, intersection.x, intersection.y);
                    
                    if (dist1 < 30 && dist1 > 5) {
                        newWall.x1 = intersection.x;
                        newWall.y1 = intersection.y;
                    }
                    
                    if (dist2 < 30 && dist2 > 5) {
                        newWall.x2 = intersection.x;
                        newWall.y2 = intersection.y;
                    }
                }
            }
            
            extended.push(newWall);
        }
        
        return extended;
    }

    /**
     * Calculate intersection point of two lines
     */
    lineIntersection(line1, line2) {
        const x1 = line1.x1, y1 = line1.y1;
        const x2 = line1.x2, y2 = line1.y2;
        const x3 = line2.x1, y3 = line2.y1;
        const x4 = line2.x2, y4 = line2.y2;
        
        const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
        
        if (Math.abs(denom) < 0.001) {
            return null; // Lines are parallel
        }
        
        const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
        
        return {
            x: x1 + t * (x2 - x1),
            y: y1 + t * (y2 - y1)
        };
    }

    /**
     * Calculate distance between two points
     */
    pointDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }
}

// Export for use in browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WallExtractionEngine;
}