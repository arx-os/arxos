/**
 * Hough Transform for robust line detection
 * @module extraction/hough
 */

/**
 * Detect lines using Hough Transform
 * @param {Uint8Array} binaryImage - Binary image (0 or 255)
 * @param {number} width - Image width
 * @param {number} height - Image height
 * @param {Object} options - Configuration options
 * @returns {Array<Object>} Detected lines in {rho, theta} or {x1,y1,x2,y2} format
 */
export function houghTransform(binaryImage, width, height, options = {}) {
    const {
        threshold = 50,        // Min votes to consider a line
        minLineLength = 40,    // Min length of line segment
        maxLineGap = 10,       // Max gap between line segments
        angleResolution = 1,   // Angle resolution in degrees
        rhoResolution = 1      // Distance resolution in pixels
    } = options;
    
    // Convert to radians
    const thetaStep = (angleResolution * Math.PI) / 180;
    const numAngles = Math.ceil(Math.PI / thetaStep);
    
    // Maximum possible rho value
    const maxRho = Math.sqrt(width * width + height * height);
    const numRhos = Math.ceil(maxRho * 2 / rhoResolution);
    
    // Create accumulator array
    const accumulator = new Int32Array(numRhos * numAngles);
    
    // Pre-calculate sin/cos values for performance
    const sinTable = new Float32Array(numAngles);
    const cosTable = new Float32Array(numAngles);
    
    for (let t = 0; t < numAngles; t++) {
        const theta = t * thetaStep;
        sinTable[t] = Math.sin(theta);
        cosTable[t] = Math.cos(theta);
    }
    
    // Voting phase - find edge pixels and vote
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            
            // Skip non-edge pixels
            if (binaryImage[idx] === 0) continue;
            
            // Vote for all possible lines through this point
            for (let t = 0; t < numAngles; t++) {
                const rho = x * cosTable[t] + y * sinTable[t];
                const rhoIdx = Math.round((rho + maxRho) / rhoResolution);
                
                if (rhoIdx >= 0 && rhoIdx < numRhos) {
                    accumulator[rhoIdx * numAngles + t]++;
                }
            }
        }
    }
    
    // Find peaks in accumulator
    const lines = findPeaks(accumulator, numRhos, numAngles, threshold);
    
    // Convert from Hough space to line segments
    return convertToLineSegments(lines, binaryImage, width, height, {
        maxRho,
        rhoResolution,
        thetaStep,
        sinTable,
        cosTable,
        minLineLength,
        maxLineGap
    });
}

/**
 * Find peaks in Hough accumulator
 * @private
 */
function findPeaks(accumulator, numRhos, numAngles, threshold) {
    const peaks = [];
    const suppression = 5; // Non-maxima suppression radius
    
    for (let r = suppression; r < numRhos - suppression; r++) {
        for (let t = suppression; t < numAngles - suppression; t++) {
            const idx = r * numAngles + t;
            const value = accumulator[idx];
            
            if (value < threshold) continue;
            
            // Check if local maximum
            let isMax = true;
            for (let dr = -suppression; dr <= suppression && isMax; dr++) {
                for (let dt = -suppression; dt <= suppression && isMax; dt++) {
                    if (dr === 0 && dt === 0) continue;
                    
                    const neighborIdx = (r + dr) * numAngles + (t + dt);
                    if (accumulator[neighborIdx] > value) {
                        isMax = false;
                    }
                }
            }
            
            if (isMax) {
                peaks.push({
                    rhoIdx: r,
                    thetaIdx: t,
                    votes: value
                });
            }
        }
    }
    
    // Sort by votes (strongest lines first)
    peaks.sort((a, b) => b.votes - a.votes);
    
    return peaks;
}

/**
 * Convert Hough lines to line segments
 * @private
 */
function convertToLineSegments(peaks, binaryImage, width, height, params) {
    const segments = [];
    const {
        maxRho,
        rhoResolution,
        thetaStep,
        sinTable,
        cosTable,
        minLineLength,
        maxLineGap
    } = params;
    
    for (const peak of peaks) {
        const rho = (peak.rhoIdx * rhoResolution) - maxRho;
        const theta = peak.thetaIdx * thetaStep;
        const sin = sinTable[peak.thetaIdx];
        const cos = cosTable[peak.thetaIdx];
        
        // Extract line segments along this infinite line
        const lineSegments = extractSegments(
            binaryImage, width, height,
            rho, theta, sin, cos,
            minLineLength, maxLineGap
        );
        
        segments.push(...lineSegments);
    }
    
    return segments;
}

/**
 * Extract line segments along an infinite line
 * @private
 */
function extractSegments(binaryImage, width, height, rho, theta, sin, cos, minLength, maxGap) {
    const segments = [];
    const points = [];
    
    // Determine if line is more horizontal or vertical
    const isVertical = Math.abs(cos) > Math.abs(sin);
    
    if (isVertical) {
        // Iterate over y values
        for (let y = 0; y < height; y++) {
            const x = Math.round((rho - y * sin) / cos);
            
            if (x >= 0 && x < width && binaryImage[y * width + x] > 0) {
                points.push({ x, y });
            }
        }
    } else {
        // Iterate over x values
        for (let x = 0; x < width; x++) {
            const y = Math.round((rho - x * cos) / sin);
            
            if (y >= 0 && y < height && binaryImage[y * width + x] > 0) {
                points.push({ x, y });
            }
        }
    }
    
    // Group points into segments
    if (points.length === 0) return segments;
    
    let segmentStart = points[0];
    let segmentEnd = points[0];
    
    for (let i = 1; i < points.length; i++) {
        const dist = Math.hypot(
            points[i].x - segmentEnd.x,
            points[i].y - segmentEnd.y
        );
        
        if (dist <= maxGap) {
            // Extend segment
            segmentEnd = points[i];
        } else {
            // Save current segment if long enough
            const length = Math.hypot(
                segmentEnd.x - segmentStart.x,
                segmentEnd.y - segmentStart.y
            );
            
            if (length >= minLength) {
                segments.push({
                    x1: segmentStart.x,
                    y1: segmentStart.y,
                    x2: segmentEnd.x,
                    y2: segmentEnd.y,
                    confidence: 1.0,
                    method: 'hough'
                });
            }
            
            // Start new segment
            segmentStart = points[i];
            segmentEnd = points[i];
        }
    }
    
    // Save last segment
    const length = Math.hypot(
        segmentEnd.x - segmentStart.x,
        segmentEnd.y - segmentStart.y
    );
    
    if (length >= minLength) {
        segments.push({
            x1: segmentStart.x,
            y1: segmentStart.y,
            x2: segmentEnd.x,
            y2: segmentEnd.y,
            confidence: 1.0,
            method: 'hough'
        });
    }
    
    return segments;
}

/**
 * Progressive Probabilistic Hough Transform (faster variant)
 * @param {Uint8Array} binaryImage - Binary image
 * @param {number} width - Image width
 * @param {number} height - Image height
 * @param {Object} options - Configuration options
 * @returns {Array<Object>} Line segments
 */
export function probabilisticHough(binaryImage, width, height, options = {}) {
    const {
        threshold = 10,
        minLineLength = 50,
        maxLineGap = 10,
        maxLines = 500
    } = options;
    
    const segments = [];
    const used = new Uint8Array(width * height);
    
    // Create list of edge points
    const edgePoints = [];
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            if (binaryImage[idx] > 0) {
                edgePoints.push({ x, y, idx });
            }
        }
    }
    
    // Randomly sample points
    while (edgePoints.length > 0 && segments.length < maxLines) {
        // Pick random point
        const randIdx = Math.floor(Math.random() * edgePoints.length);
        const point = edgePoints[randIdx];
        
        if (used[point.idx]) {
            edgePoints.splice(randIdx, 1);
            continue;
        }
        
        // Try to grow a line from this point
        const line = growLine(point, binaryImage, used, width, height, maxLineGap);
        
        if (line && line.length >= minLineLength) {
            segments.push(line);
        }
        
        edgePoints.splice(randIdx, 1);
    }
    
    return segments;
}

/**
 * Grow a line from a seed point
 * @private
 */
function growLine(seed, binaryImage, used, width, height, maxGap) {
    const directions = [
        { dx: 1, dy: 0 },   // Right
        { dx: 1, dy: 1 },   // Down-right
        { dx: 0, dy: 1 },   // Down
        { dx: -1, dy: 1 },  // Down-left
        { dx: -1, dy: 0 },  // Left
        { dx: -1, dy: -1 }, // Up-left
        { dx: 0, dy: -1 },  // Up
        { dx: 1, dy: -1 }   // Up-right
    ];
    
    let bestDir = null;
    let maxLength = 0;
    
    // Find best direction
    for (const dir of directions) {
        const length = measureLineLength(
            seed.x, seed.y, dir.dx, dir.dy,
            binaryImage, width, height, maxGap
        );
        
        if (length > maxLength) {
            maxLength = length;
            bestDir = dir;
        }
    }
    
    if (!bestDir || maxLength < 10) return null;
    
    // Trace line in both directions
    const { forward, backward } = traceLine(
        seed.x, seed.y, bestDir.dx, bestDir.dy,
        binaryImage, used, width, height, maxGap
    );
    
    return {
        x1: backward.x,
        y1: backward.y,
        x2: forward.x,
        y2: forward.y,
        length: Math.hypot(forward.x - backward.x, forward.y - backward.y),
        confidence: 0.9,
        method: 'probabilistic_hough'
    };
}

/**
 * Measure potential line length in a direction
 * @private
 */
function measureLineLength(x, y, dx, dy, binaryImage, width, height, maxGap) {
    let length = 0;
    let gap = 0;
    let cx = x;
    let cy = y;
    
    while (cx >= 0 && cx < width && cy >= 0 && cy < height) {
        const idx = cy * width + cx;
        
        if (binaryImage[idx] > 0) {
            length++;
            gap = 0;
        } else {
            gap++;
            if (gap > maxGap) break;
        }
        
        cx += dx;
        cy += dy;
    }
    
    return length;
}

/**
 * Trace line in both directions from seed
 * @private
 */
function traceLine(x, y, dx, dy, binaryImage, used, width, height, maxGap) {
    // Trace forward
    let fx = x;
    let fy = y;
    let gap = 0;
    
    while (fx >= 0 && fx < width && fy >= 0 && fy < height && gap <= maxGap) {
        const idx = fy * width + fx;
        
        if (binaryImage[idx] > 0) {
            used[idx] = 1;
            gap = 0;
        } else {
            gap++;
        }
        
        fx += dx;
        fy += dy;
    }
    
    // Trace backward
    let bx = x;
    let by = y;
    gap = 0;
    
    while (bx >= 0 && bx < width && by >= 0 && by < height && gap <= maxGap) {
        const idx = by * width + bx;
        
        if (binaryImage[idx] > 0) {
            used[idx] = 1;
            gap = 0;
        } else {
            gap++;
        }
        
        bx -= dx;
        by -= dy;
    }
    
    return {
        forward: { x: fx - dx * (gap + 1), y: fy - dy * (gap + 1) },
        backward: { x: bx + dx * (gap + 1), y: by + dy * (gap + 1) }
    };
}

export default {
    houghTransform,
    probabilisticHough
};