/**
 * Post-processing utilities for wall extraction
 * @module extraction/postprocess
 */

/**
 * Merge nearby parallel walls
 * @param {Array} walls - Input walls
 * @param {Object} options - Configuration
 * @returns {Array} Merged walls
 */
export function mergeWalls(walls, options = {}) {
    const {
        parallelThreshold = 5,    // Degrees
        distanceThreshold = 15,   // Pixels
        overlapThreshold = 0.5    // Minimum overlap ratio
    } = options;
    
    const merged = [];
    const used = new Set();
    
    for (let i = 0; i < walls.length; i++) {
        if (used.has(i)) continue;
        
        const wall1 = walls[i];
        const group = [wall1];
        used.add(i);
        
        // Find all parallel nearby walls
        for (let j = i + 1; j < walls.length; j++) {
            if (used.has(j)) continue;
            
            const wall2 = walls[j];
            
            if (areParallel(wall1, wall2, parallelThreshold) &&
                areNearby(wall1, wall2, distanceThreshold) &&
                doOverlap(wall1, wall2, overlapThreshold)) {
                
                group.push(wall2);
                used.add(j);
            }
        }
        
        // Merge the group into a single wall
        if (group.length > 1) {
            merged.push(mergeGroup(group));
        } else {
            merged.push(wall1);
        }
    }
    
    return merged;
}

/**
 * Check if two walls are parallel
 * @private
 */
function areParallel(wall1, wall2, threshold) {
    const angle1 = Math.atan2(wall1.y2 - wall1.y1, wall1.x2 - wall1.x1);
    const angle2 = Math.atan2(wall2.y2 - wall2.y1, wall2.x2 - wall2.x1);
    
    let diff = Math.abs(angle1 - angle2) * 180 / Math.PI;
    
    // Handle angle wrapping
    if (diff > 180) diff = 360 - diff;
    if (diff > 90) diff = 180 - diff;
    
    return diff < threshold;
}

/**
 * Check if two walls are nearby
 * @private
 */
function areNearby(wall1, wall2, threshold) {
    // Calculate perpendicular distance between lines
    const dist = perpendicularDistance(wall1, wall2);
    return dist < threshold;
}

/**
 * Calculate perpendicular distance between two lines
 * @private
 */
function perpendicularDistance(wall1, wall2) {
    // Point to line distance for each endpoint
    const d1 = pointToLineDistance(
        { x: wall1.x1, y: wall1.y1 },
        wall2
    );
    const d2 = pointToLineDistance(
        { x: wall1.x2, y: wall1.y2 },
        wall2
    );
    const d3 = pointToLineDistance(
        { x: wall2.x1, y: wall2.y1 },
        wall1
    );
    const d4 = pointToLineDistance(
        { x: wall2.x2, y: wall2.y2 },
        wall1
    );
    
    return Math.min(d1, d2, d3, d4);
}

/**
 * Calculate distance from point to line
 * @private
 */
function pointToLineDistance(point, line) {
    const A = point.x - line.x1;
    const B = point.y - line.y1;
    const C = line.x2 - line.x1;
    const D = line.y2 - line.y1;
    
    const dot = A * C + B * D;
    const lenSq = C * C + D * D;
    
    if (lenSq === 0) return Math.hypot(A, B);
    
    let t = dot / lenSq;
    t = Math.max(0, Math.min(1, t));
    
    const projX = line.x1 + t * C;
    const projY = line.y1 + t * D;
    
    return Math.hypot(point.x - projX, point.y - projY);
}

/**
 * Check if two parallel walls overlap
 * @private
 */
function doOverlap(wall1, wall2, threshold) {
    // Project walls onto their common direction
    const angle = Math.atan2(wall1.y2 - wall1.y1, wall1.x2 - wall1.x1);
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    
    // Project endpoints
    const p1 = wall1.x1 * cos + wall1.y1 * sin;
    const p2 = wall1.x2 * cos + wall1.y2 * sin;
    const p3 = wall2.x1 * cos + wall2.y1 * sin;
    const p4 = wall2.x2 * cos + wall2.y2 * sin;
    
    const min1 = Math.min(p1, p2);
    const max1 = Math.max(p1, p2);
    const min2 = Math.min(p3, p4);
    const max2 = Math.max(p3, p4);
    
    const overlap = Math.min(max1, max2) - Math.max(min1, min2);
    const length1 = max1 - min1;
    const length2 = max2 - min2;
    
    return overlap > threshold * Math.min(length1, length2);
}

/**
 * Merge a group of walls into one
 * @private
 */
function mergeGroup(group) {
    // Find the dominant direction
    let totalDx = 0, totalDy = 0;
    
    for (const wall of group) {
        totalDx += wall.x2 - wall.x1;
        totalDy += wall.y2 - wall.y1;
    }
    
    const angle = Math.atan2(totalDy, totalDx);
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);
    
    // Project all points and find extremes
    let minProj = Infinity, maxProj = -Infinity;
    let sumPerp = 0, countPerp = 0;
    
    for (const wall of group) {
        const proj1 = wall.x1 * cos + wall.y1 * sin;
        const proj2 = wall.x2 * cos + wall.y2 * sin;
        const perp1 = -wall.x1 * sin + wall.y1 * cos;
        const perp2 = -wall.x2 * sin + wall.y2 * cos;
        
        minProj = Math.min(minProj, proj1, proj2);
        maxProj = Math.max(maxProj, proj1, proj2);
        sumPerp += perp1 + perp2;
        countPerp += 2;
    }
    
    const avgPerp = sumPerp / countPerp;
    
    // Convert back to x,y coordinates
    const x1 = minProj * cos - avgPerp * sin;
    const y1 = minProj * sin + avgPerp * cos;
    const x2 = maxProj * cos - avgPerp * sin;
    const y2 = maxProj * sin + avgPerp * cos;
    
    // Calculate average confidence
    const avgConfidence = group.reduce((sum, wall) => 
        sum + (wall.confidence || 0.5), 0) / group.length;
    
    return {
        x1, y1, x2, y2,
        confidence: avgConfidence,
        merged: true,
        sourceCount: group.length
    };
}

/**
 * Filter out non-architectural elements
 * @param {Array} walls - Input walls
 * @param {Object} options - Configuration
 * @returns {Array} Filtered walls
 */
export function filterArchitectural(walls, options = {}) {
    const {
        minLength = 50,
        maxThickness = 20,
        imageWidth,
        imageHeight,
        borderMargin = 10
    } = options;
    
    return walls.filter(wall => {
        // Check minimum length
        const length = Math.hypot(wall.x2 - wall.x1, wall.y2 - wall.y1);
        if (length < minLength) return false;
        
        // Remove walls too close to image border (likely frame)
        if (imageWidth && imageHeight) {
            const nearBorder = 
                wall.x1 < borderMargin || wall.x1 > imageWidth - borderMargin ||
                wall.y1 < borderMargin || wall.y1 > imageHeight - borderMargin ||
                wall.x2 < borderMargin || wall.x2 > imageWidth - borderMargin ||
                wall.y2 < borderMargin || wall.y2 > imageHeight - borderMargin;
            
            if (nearBorder) {
                // Check if it's a border wall (full width/height)
                const isHorizontalBorder = 
                    Math.abs(wall.y1 - wall.y2) < 5 &&
                    Math.abs(wall.x2 - wall.x1) > imageWidth * 0.8;
                
                const isVerticalBorder = 
                    Math.abs(wall.x1 - wall.x2) < 5 &&
                    Math.abs(wall.y2 - wall.y1) > imageHeight * 0.8;
                
                if (isHorizontalBorder || isVerticalBorder) {
                    return false;
                }
            }
        }
        
        return true;
    });
}

/**
 * Snap walls to grid
 * @param {Array} walls - Input walls
 * @param {number} gridSize - Grid size in pixels
 * @returns {Array} Snapped walls
 */
export function snapToGrid(walls, gridSize) {
    return walls.map(wall => ({
        ...wall,
        x1: Math.round(wall.x1 / gridSize) * gridSize,
        y1: Math.round(wall.y1 / gridSize) * gridSize,
        x2: Math.round(wall.x2 / gridSize) * gridSize,
        y2: Math.round(wall.y2 / gridSize) * gridSize
    }));
}

/**
 * Extend walls to intersect
 * @param {Array} walls - Input walls
 * @param {Object} options - Configuration
 * @returns {Array} Extended walls
 */
export function extendWalls(walls, options = {}) {
    const {
        maxExtension = 20,
        angleThreshold = 10
    } = options;
    
    const extended = [...walls];
    
    for (let i = 0; i < extended.length; i++) {
        for (let j = i + 1; j < extended.length; j++) {
            const wall1 = extended[i];
            const wall2 = extended[j];
            
            // Check if walls are roughly perpendicular
            const angle1 = Math.atan2(wall1.y2 - wall1.y1, wall1.x2 - wall1.x1);
            const angle2 = Math.atan2(wall2.y2 - wall2.y1, wall2.x2 - wall2.x1);
            
            let angleDiff = Math.abs(angle1 - angle2) * 180 / Math.PI;
            if (angleDiff > 180) angleDiff = 360 - angleDiff;
            
            const isPerpendicular = Math.abs(angleDiff - 90) < angleThreshold;
            
            if (isPerpendicular) {
                // Try to extend walls to meet
                const intersection = lineIntersection(wall1, wall2);
                
                if (intersection) {
                    // Check if intersection is close to endpoints
                    const distances = [
                        Math.hypot(wall1.x1 - intersection.x, wall1.y1 - intersection.y),
                        Math.hypot(wall1.x2 - intersection.x, wall1.y2 - intersection.y),
                        Math.hypot(wall2.x1 - intersection.x, wall2.y1 - intersection.y),
                        Math.hypot(wall2.x2 - intersection.x, wall2.y2 - intersection.y)
                    ];
                    
                    const minDist = Math.min(...distances);
                    
                    if (minDist < maxExtension && minDist > 1) {
                        // Extend the closest endpoint to intersection
                        const minIdx = distances.indexOf(minDist);
                        
                        if (minIdx === 0) {
                            wall1.x1 = intersection.x;
                            wall1.y1 = intersection.y;
                        } else if (minIdx === 1) {
                            wall1.x2 = intersection.x;
                            wall1.y2 = intersection.y;
                        } else if (minIdx === 2) {
                            wall2.x1 = intersection.x;
                            wall2.y1 = intersection.y;
                        } else {
                            wall2.x2 = intersection.x;
                            wall2.y2 = intersection.y;
                        }
                    }
                }
            }
        }
    }
    
    return extended;
}

/**
 * Find intersection point of two lines
 * @private
 */
function lineIntersection(line1, line2) {
    const x1 = line1.x1, y1 = line1.y1;
    const x2 = line1.x2, y2 = line1.y2;
    const x3 = line2.x1, y3 = line2.y1;
    const x4 = line2.x2, y4 = line2.y2;
    
    const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
    
    if (Math.abs(denom) < 0.001) return null; // Parallel lines
    
    const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
    
    return {
        x: x1 + t * (x2 - x1),
        y: y1 + t * (y2 - y1)
    };
}

/**
 * Detect and mark wall junctions
 * @param {Array} walls - Input walls
 * @returns {Object} Walls with junction information
 */
export function detectJunctions(walls) {
    const junctions = [];
    const threshold = 10; // Distance threshold for junction
    
    for (let i = 0; i < walls.length; i++) {
        for (let j = i + 1; j < walls.length; j++) {
            const wall1 = walls[i];
            const wall2 = walls[j];
            
            // Check all endpoint combinations
            const points = [
                { x: wall1.x1, y: wall1.y1, wall1: i, end1: 'start' },
                { x: wall1.x2, y: wall1.y2, wall1: i, end1: 'end' },
                { x: wall2.x1, y: wall2.y1, wall2: j, end2: 'start' },
                { x: wall2.x2, y: wall2.y2, wall2: j, end2: 'end' }
            ];
            
            // Find clusters of nearby points
            for (let k = 0; k < points.length; k++) {
                for (let l = k + 1; l < points.length; l++) {
                    const dist = Math.hypot(
                        points[k].x - points[l].x,
                        points[k].y - points[l].y
                    );
                    
                    if (dist < threshold) {
                        junctions.push({
                            x: (points[k].x + points[l].x) / 2,
                            y: (points[k].y + points[l].y) / 2,
                            walls: [
                                points[k].wall1 || points[k].wall2,
                                points[l].wall1 || points[l].wall2
                            ],
                            type: detectJunctionType(wall1, wall2)
                        });
                    }
                }
            }
        }
    }
    
    return {
        walls: walls.map((wall, idx) => ({
            ...wall,
            junctions: junctions.filter(j => j.walls.includes(idx))
        })),
        junctions
    };
}

/**
 * Detect junction type (L, T, X)
 * @private
 */
function detectJunctionType(wall1, wall2) {
    const angle1 = Math.atan2(wall1.y2 - wall1.y1, wall1.x2 - wall1.x1);
    const angle2 = Math.atan2(wall2.y2 - wall2.y1, wall2.x2 - wall2.x1);
    
    let angleDiff = Math.abs(angle1 - angle2) * 180 / Math.PI;
    if (angleDiff > 180) angleDiff = 360 - angleDiff;
    
    if (Math.abs(angleDiff - 90) < 15) return 'L';
    if (Math.abs(angleDiff - 180) < 15) return 'T';
    
    return 'X';
}

export default {
    mergeWalls,
    filterArchitectural,
    snapToGrid,
    extendWalls,
    detectJunctions
};