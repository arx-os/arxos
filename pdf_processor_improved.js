/**
 * Improved PDF Processing Module for Arxos BIM Converter
 * Better filtering for architectural walls vs other lines
 */

class PDFProcessorImproved {
    constructor() {
        this.pdfjsLib = null;
        this.walls = [];
        this.confidence = 0;
    }

    async initialize() {
        if (!window.pdfjsLib) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            document.head.appendChild(script);
            
            await new Promise(resolve => {
                script.onload = resolve;
            });
            
            pdfjsLib.GlobalWorkerOptions.workerSrc = 
                'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }
        
        this.pdfjsLib = window.pdfjsLib;
    }

    async processPDF(file, options = {}) {
        console.log('Processing PDF:', file.name);
        
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        try {
            const arrayBuffer = await this.readFileAsArrayBuffer(file);
            const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
            console.log('PDF loaded, pages:', pdf.numPages);
            
            // Process first page (usually the floor plan)
            const page = await pdf.getPage(1);
            
            // Try to extract vector paths first (more accurate)
            const vectorWalls = await this.extractVectorPaths(page);
            
            if (vectorWalls.length > 0) {
                console.log('Found vector paths:', vectorWalls.length);
                return this.processVectorWalls(vectorWalls);
            }
            
            // Fallback to raster processing
            console.log('No vector paths, using raster processing');
            return await this.processRasterPage(page, options);
            
        } catch (error) {
            console.error('PDF processing error:', error);
            throw error;
        }
    }

    async extractVectorPaths(page) {
        const walls = [];
        
        try {
            // Get page operators (drawing commands)
            const ops = await page.getOperatorList();
            
            let currentPath = null;
            let currentPoint = null;
            
            // Process drawing operations
            for (let i = 0; i < ops.fnArray.length; i++) {
                const fn = ops.fnArray[i];
                const args = ops.argsArray[i];
                
                switch (fn) {
                    case this.pdfjsLib.OPS.moveTo:
                        currentPoint = { x: args[0], y: args[1] };
                        if (currentPath) {
                            currentPath = null;
                        }
                        break;
                        
                    case this.pdfjsLib.OPS.lineTo:
                        if (currentPoint) {
                            const wall = {
                                startX: currentPoint.x,
                                startY: currentPoint.y,
                                endX: args[0],
                                endY: args[1],
                                confidence: 0.95
                            };
                            
                            // Filter for wall-like segments
                            if (this.isWallLike(wall)) {
                                walls.push(wall);
                            }
                            
                            currentPoint = { x: args[0], y: args[1] };
                        }
                        break;
                        
                    case this.pdfjsLib.OPS.rectangle:
                        // Extract rectangle edges as walls
                        const [x, y, width, height] = args;
                        
                        const rectWalls = [
                            { startX: x, startY: y, endX: x + width, endY: y },
                            { startX: x + width, startY: y, endX: x + width, endY: y + height },
                            { startX: x + width, startY: y + height, endX: x, endY: y + height },
                            { startX: x, startY: y + height, endX: x, endY: y }
                        ];
                        
                        rectWalls.forEach(wall => {
                            wall.confidence = 0.9;
                            if (this.isWallLike(wall)) {
                                walls.push(wall);
                            }
                        });
                        break;
                }
            }
        } catch (error) {
            console.log('Could not extract vector paths:', error);
        }
        
        return walls;
    }

    isWallLike(segment) {
        const length = Math.sqrt(
            Math.pow(segment.endX - segment.startX, 2) + 
            Math.pow(segment.endY - segment.startY, 2)
        );
        
        // Filter out very short segments (likely not walls)
        if (length < 20) return false;
        
        // Check if horizontal or vertical (most walls are)
        const angle = Math.atan2(
            segment.endY - segment.startY,
            segment.endX - segment.startX
        ) * 180 / Math.PI;
        
        const normalizedAngle = Math.abs(angle % 90);
        const isOrthogonal = normalizedAngle < 5 || normalizedAngle > 85;
        
        // Increase confidence for orthogonal lines
        if (isOrthogonal) {
            segment.confidence = Math.min(segment.confidence * 1.1, 1.0);
        }
        
        return true;
    }

    processVectorWalls(walls) {
        // Apply DBSCAN clustering
        const clustered = this.clusterEndpoints(walls, 2);
        
        // Merge collinear segments
        const merged = this.mergeCollinearWalls(clustered);
        
        // Filter out duplicates and very short segments
        const filtered = this.filterWalls(merged);
        
        // Detect rooms from walls
        const rooms = this.detectRoomsSimplified(filtered);
        
        // Calculate overall confidence
        const avgConfidence = filtered.reduce((sum, w) => sum + w.confidence, 0) / filtered.length;
        
        return {
            walls: filtered,
            rooms: rooms,
            confidence: avgConfidence || 0.5
        };
    }

    async processRasterPage(page, options) {
        const viewport = page.getViewport({ scale: 1.5 });
        
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        await page.render({
            canvasContext: context,
            viewport: viewport
        }).promise;
        
        console.log('Page rendered to canvas');
        
        // Extract walls using simplified edge detection
        const walls = this.extractWallsSimplified(canvas);
        
        return {
            walls: walls,
            rooms: [],
            confidence: 0.6
        };
    }

    extractWallsSimplified(canvas) {
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const walls = [];
        
        // Find dark horizontal and vertical lines
        const threshold = 128;
        const minLength = 50;
        
        // Scan for horizontal lines
        for (let y = 0; y < canvas.height; y += 5) {
            let lineStart = null;
            
            for (let x = 0; x < canvas.width; x++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx+1] + imageData.data[idx+2]) / 3;
                
                if (gray < threshold) {
                    if (!lineStart) {
                        lineStart = x;
                    }
                } else {
                    if (lineStart && (x - lineStart) > minLength) {
                        walls.push({
                            startX: lineStart,
                            startY: y,
                            endX: x,
                            endY: y,
                            confidence: 0.7
                        });
                    }
                    lineStart = null;
                }
            }
        }
        
        // Scan for vertical lines
        for (let x = 0; x < canvas.width; x += 5) {
            let lineStart = null;
            
            for (let y = 0; y < canvas.height; y++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx+1] + imageData.data[idx+2]) / 3;
                
                if (gray < threshold) {
                    if (!lineStart) {
                        lineStart = y;
                    }
                } else {
                    if (lineStart && (y - lineStart) > minLength) {
                        walls.push({
                            startX: x,
                            startY: lineStart,
                            endX: x,
                            endY: y,
                            confidence: 0.7
                        });
                    }
                    lineStart = null;
                }
            }
        }
        
        return walls;
    }

    clusterEndpoints(walls, epsilon) {
        const points = [];
        walls.forEach((wall, idx) => {
            points.push({ x: wall.startX, y: wall.startY, wallIdx: idx, isStart: true });
            points.push({ x: wall.endX, y: wall.endY, wallIdx: idx, isStart: false });
        });
        
        const clusters = [];
        const visited = new Set();
        
        points.forEach((point, idx) => {
            if (visited.has(idx)) return;
            
            const neighbors = [];
            points.forEach((p, i) => {
                if (i === idx) return;
                const dist = Math.sqrt(Math.pow(p.x - point.x, 2) + Math.pow(p.y - point.y, 2));
                if (dist <= epsilon) neighbors.push(i);
            });
            
            if (neighbors.length >= 1) {
                const cluster = [idx, ...neighbors];
                cluster.forEach(i => visited.add(i));
                clusters.push(cluster);
            }
        });
        
        const mergedWalls = [...walls];
        clusters.forEach(cluster => {
            let cx = 0, cy = 0;
            cluster.forEach(idx => {
                cx += points[idx].x;
                cy += points[idx].y;
            });
            cx /= cluster.length;
            cy /= cluster.length;
            
            cluster.forEach(idx => {
                const point = points[idx];
                if (point.isStart) {
                    mergedWalls[point.wallIdx].startX = cx;
                    mergedWalls[point.wallIdx].startY = cy;
                } else {
                    mergedWalls[point.wallIdx].endX = cx;
                    mergedWalls[point.wallIdx].endY = cy;
                }
            });
        });
        
        return mergedWalls;
    }

    mergeCollinearWalls(walls) {
        const merged = [];
        const used = new Set();
        
        walls.forEach((wall, i) => {
            if (used.has(i)) return;
            
            let extended = { ...wall };
            used.add(i);
            
            // Look for collinear walls to merge
            walls.forEach((other, j) => {
                if (i === j || used.has(j)) return;
                
                if (this.areCollinear(extended, other)) {
                    // Extend the wall
                    const points = [
                        { x: extended.startX, y: extended.startY },
                        { x: extended.endX, y: extended.endY },
                        { x: other.startX, y: other.startY },
                        { x: other.endX, y: other.endY }
                    ];
                    
                    // Find extremes
                    points.sort((a, b) => a.x - b.x || a.y - b.y);
                    
                    extended.startX = points[0].x;
                    extended.startY = points[0].y;
                    extended.endX = points[points.length - 1].x;
                    extended.endY = points[points.length - 1].y;
                    
                    used.add(j);
                }
            });
            
            merged.push(extended);
        });
        
        return merged;
    }

    areCollinear(wall1, wall2) {
        // Check if two walls are on the same line
        const threshold = 5; // pixels
        
        // Calculate angle for each wall
        const angle1 = Math.atan2(wall1.endY - wall1.startY, wall1.endX - wall1.startX);
        const angle2 = Math.atan2(wall2.endY - wall2.startY, wall2.endX - wall2.startX);
        
        // Check if angles are similar
        const angleDiff = Math.abs(angle1 - angle2) % Math.PI;
        if (angleDiff > 0.1 && angleDiff < (Math.PI - 0.1)) return false;
        
        // Check if one wall's endpoint is near the other wall's line
        const dist = this.pointToLineDistance(
            wall2.startX, wall2.startY,
            wall1.startX, wall1.startY,
            wall1.endX, wall1.endY
        );
        
        return dist < threshold;
    }

    pointToLineDistance(px, py, x1, y1, x2, y2) {
        const A = px - x1;
        const B = py - y1;
        const C = x2 - x1;
        const D = y2 - y1;
        
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        
        if (lenSq !== 0) param = dot / lenSq;
        
        let xx, yy;
        
        if (param < 0) {
            xx = x1;
            yy = y1;
        } else if (param > 1) {
            xx = x2;
            yy = y2;
        } else {
            xx = x1 + param * C;
            yy = y1 + param * D;
        }
        
        const dx = px - xx;
        const dy = py - yy;
        
        return Math.sqrt(dx * dx + dy * dy);
    }

    filterWalls(walls) {
        const filtered = [];
        const minLength = 30;
        
        walls.forEach(wall => {
            const length = Math.sqrt(
                Math.pow(wall.endX - wall.startX, 2) + 
                Math.pow(wall.endY - wall.startY, 2)
            );
            
            if (length >= minLength) {
                filtered.push(wall);
            }
        });
        
        return filtered;
    }

    detectRoomsSimplified(walls) {
        // Simplified room detection - find rectangular regions
        const rooms = [];
        
        // This is a placeholder - in production would use planar graph
        // For now, just create a few sample rooms based on wall density
        
        return rooms;
    }

    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PDFProcessorImproved;
}