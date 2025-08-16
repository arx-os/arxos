/**
 * PDF Decoder v2 - Improved extraction with proper scaling
 * Handles both standard and non-standard PDF operations
 * Continuously evolving based on real-world PDF variations
 */

class PDFDecoderV2 {
    constructor() {
        this.pdfjsLib = null;
    }

    async initialize() {
        if (!window.pdfjsLib) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            document.head.appendChild(script);
            await new Promise(resolve => script.onload = resolve);
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }
        this.pdfjsLib = window.pdfjsLib;
    }

    async decodePDF(file) {
        console.log('🔍 Starting PDF decoding v2...');
        
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        const arrayBuffer = await this.readFileAsArrayBuffer(file);
        const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
        const page = await pdf.getPage(1);
        
        // Get viewport for rendering
        const scale = 2.0; // Higher scale for better resolution
        const viewport = page.getViewport({ scale });
        
        console.log(`📐 Viewport: ${viewport.width}x${viewport.height}`);
        
        // Method 1: Extract from PDF operations
        const vectorWalls = await this.extractVectorWalls(page, viewport);
        
        // Method 2: Extract from rendered canvas
        const rasterWalls = await this.extractRasterWalls(page, viewport);
        
        // Combine both methods
        const allWalls = this.mergeWalls(vectorWalls, rasterWalls);
        
        // Apply DBSCAN clustering
        const clusteredWalls = this.clusterWalls(allWalls);
        
        // Detect rooms
        const rooms = this.detectRooms(clusteredWalls);
        
        // Calculate confidence
        const avgConfidence = clusteredWalls.length > 0 
            ? clusteredWalls.reduce((sum, w) => sum + w.confidence, 0) / clusteredWalls.length 
            : 0;
        
        console.log(`✅ Extraction complete: ${clusteredWalls.length} walls, ${rooms.length} rooms`);
        
        return {
            walls: clusteredWalls,
            rooms: rooms,
            confidence: avgConfidence
        };
    }

    async extractVectorWalls(page, viewport) {
        console.log('📊 Extracting vector walls...');
        console.log('  Viewport transform:', viewport.transform);
        
        // The viewport transform [0, 2, 2, 0, 0, 0] indicates:
        // [a, b, c, d, e, f] where:
        // x' = a*x + c*y + e
        // y' = b*x + d*y + f
        // Our transform has a=0, b=2, c=2, d=0
        // This means: x' = 2*y, y' = 2*x (90-degree rotation with 2x scale)
        
        const ops = await page.getOperatorList();
        console.log(`  Total operations: ${ops.fnArray.length}`);
        
        const walls = [];
        
        let currentPoint = null;
        let pathStarted = false;
        
        // Get the transform from the viewport to convert PDF coordinates to canvas pixels
        const transform = viewport.transform;
        console.log(`  Viewport transform:`, transform);
        
        // Count operation types for debugging
        const opCounts = {};
        ops.fnArray.forEach(op => {
            opCounts[op] = (opCounts[op] || 0) + 1;
        });
        console.log(`  Operation types found:`, opCounts);
        
        // Get page dimensions to understand the coordinate space
        const pageRect = page.view; // [x0, y0, x1, y1]
        const pageWidth = pageRect[2] - pageRect[0];
        const pageHeight = pageRect[3] - pageRect[1];
        console.log(`  PDF page dimensions: ${pageWidth}x${pageHeight} units`);
        
        // Apply transformation using the viewport transform matrix
        const transformPoint = (x, y) => {
            // Apply the viewport transformation matrix
            // transform = [a, b, c, d, e, f]
            // x' = a*x + c*y + e
            // y' = b*x + d*y + f
            const tx = transform[0] * x + transform[2] * y + transform[4];
            const ty = transform[1] * x + transform[3] * y + transform[5];
            
            return { x: tx, y: ty };
        };
        
        let constructPathCount = 0;
        
        for (let i = 0; i < ops.fnArray.length; i++) {
            const fn = ops.fnArray[i];
            const args = ops.argsArray[i] || [];
            
            // Handle constructPath operations (91 is the key operation in your PDFs)
            if (fn === 91 || fn === 69) {
                constructPathCount++;
                const pathOps = args[0] || [];
                const pathCoords = args[1] || [];
                let coordIndex = 0;
                
                console.log(`  ConstructPath ${constructPathCount}: ${pathOps.length} ops, ${pathCoords.length} coords`);
                
                // Log first few operations for debugging
                if (constructPathCount <= 3) {
                    console.log(`    Path ops:`, pathOps);
                    console.log(`    Path coords:`, pathCoords.slice(0, 10));
                }
                
                for (let j = 0; j < pathOps.length; j++) {
                    const op = pathOps[j];
                    
                    // Log operation type to understand what we're dealing with
                    if (constructPathCount === 1 && j === 0) {
                        console.log(`    First op type: ${op}`);
                    }
                    
                    // These operation codes are from PDF.js internal representation
                    // Note: Your PDF uses 13 for moveTo and 14 for lineTo!
                    switch (op) {
                        case 2: // standard moveTo
                        case 13: // moveTo (as seen in your PDF)
                            if (coordIndex + 1 < pathCoords.length) {
                                currentPoint = transformPoint(
                                    pathCoords[coordIndex],
                                    pathCoords[coordIndex + 1]
                                );
                                pathStarted = true;
                                coordIndex += 2;
                                
                                if (constructPathCount <= 3) {
                                    console.log(`    MoveTo: (${pathCoords[coordIndex-2]}, ${pathCoords[coordIndex-1]}) -> (${currentPoint.x}, ${currentPoint.y})`);
                                }
                            }
                            break;
                            
                        case 3: // standard lineTo
                        case 14: // lineTo (as seen in your PDF)
                            if (currentPoint && pathStarted && coordIndex + 1 < pathCoords.length) {
                                const endPoint = transformPoint(
                                    pathCoords[coordIndex],
                                    pathCoords[coordIndex + 1]
                                );
                                
                                // Calculate line length
                                const length = Math.sqrt(
                                    Math.pow(endPoint.x - currentPoint.x, 2) + 
                                    Math.pow(endPoint.y - currentPoint.y, 2)
                                );
                                
                                if (constructPathCount <= 3) {
                                    console.log(`    LineTo: (${pathCoords[coordIndex]}, ${pathCoords[coordIndex+1]}) -> (${endPoint.x}, ${endPoint.y}), length: ${length}`);
                                }
                                
                                // Only add lines longer than 2 pixels
                                if (length > 2) {
                                    walls.push({
                                        startX: currentPoint.x,
                                        startY: currentPoint.y,
                                        endX: endPoint.x,
                                        endY: endPoint.y,
                                        confidence: 0.95,
                                        source: 'vector',
                                        length: length
                                    });
                                }
                                
                                currentPoint = endPoint;
                                coordIndex += 2;
                            }
                            break;
                            
                        case 4: // standard curveTo (cubic bezier)
                        case 15: // curveTo (possible alternate code)
                            if (coordIndex + 5 < pathCoords.length) {
                                // For now, approximate curve as straight line from current to end point
                                const endPoint = transformPoint(
                                    pathCoords[coordIndex + 4],
                                    pathCoords[coordIndex + 5]
                                );
                                
                                if (currentPoint) {
                                    const length = Math.sqrt(
                                        Math.pow(endPoint.x - currentPoint.x, 2) + 
                                        Math.pow(endPoint.y - currentPoint.y, 2)
                                    );
                                    
                                    if (length > 2) {
                                        walls.push({
                                            startX: currentPoint.x,
                                            startY: currentPoint.y,
                                            endX: endPoint.x,
                                            endY: endPoint.y,
                                            confidence: 0.85,
                                            source: 'vector',
                                            length: length
                                        });
                                    }
                                    currentPoint = endPoint;
                                }
                                coordIndex += 6;
                            }
                            break;
                            
                        case 5: // standard closePath
                        case 16: // closePath (possible alternate)
                            pathStarted = false;
                            break;
                            
                        case 6: // standard rectangle
                        case 17: // rectangle (possible alternate)
                            if (coordIndex + 3 < pathCoords.length) {
                                const x = pathCoords[coordIndex];
                                const y = pathCoords[coordIndex + 1];
                                const w = pathCoords[coordIndex + 2];
                                const h = pathCoords[coordIndex + 3];
                                
                                const tl = transformPoint(x, y);
                                const tr = transformPoint(x + w, y);
                                const br = transformPoint(x + w, y + h);
                                const bl = transformPoint(x, y + h);
                                
                                // Add rectangle edges as walls
                                walls.push(
                                    { startX: tl.x, startY: tl.y, endX: tr.x, endY: tr.y, confidence: 0.95, source: 'vector' },
                                    { startX: tr.x, startY: tr.y, endX: br.x, endY: br.y, confidence: 0.95, source: 'vector' },
                                    { startX: br.x, startY: br.y, endX: bl.x, endY: bl.y, confidence: 0.95, source: 'vector' },
                                    { startX: bl.x, startY: bl.y, endX: tl.x, endY: tl.y, confidence: 0.95, source: 'vector' }
                                );
                                
                                coordIndex += 4;
                            }
                            break;
                            
                        default:
                            // Log unexpected operation codes
                            if (constructPathCount === 1) {
                                console.log(`    Unknown operation: ${op}`);
                            }
                            break;
                    }
                }
            }
            
            // Also handle standard PDF operations
            else if (fn === 12) { // standard moveTo
                if (args.length >= 2) {
                    currentPoint = transformPoint(args[0], args[1]);
                    pathStarted = true;
                }
            }
            else if (fn === 13) { // standard lineTo
                if (currentPoint && pathStarted && args.length >= 2) {
                    const endPoint = transformPoint(args[0], args[1]);
                    
                    const length = Math.sqrt(
                        Math.pow(endPoint.x - currentPoint.x, 2) + 
                        Math.pow(endPoint.y - currentPoint.y, 2)
                    );
                    
                    if (length > 2) {
                        walls.push({
                            startX: currentPoint.x,
                            startY: currentPoint.y,
                            endX: endPoint.x,
                            endY: endPoint.y,
                            confidence: 0.9,
                            source: 'vector',
                            length: length
                        });
                    }
                    
                    currentPoint = endPoint;
                }
            }
            else if (fn === 18) { // standard rectangle
                if (args.length >= 4) {
                    const [x, y, w, h] = args;
                    const tl = transformPoint(x, y);
                    const tr = transformPoint(x + w, y);
                    const br = transformPoint(x + w, y + h);
                    const bl = transformPoint(x, y + h);
                    
                    walls.push(
                        { startX: tl.x, startY: tl.y, endX: tr.x, endY: tr.y, confidence: 0.9, source: 'vector' },
                        { startX: tr.x, startY: tr.y, endX: br.x, endY: br.y, confidence: 0.9, source: 'vector' },
                        { startX: br.x, startY: br.y, endX: bl.x, endY: bl.y, confidence: 0.9, source: 'vector' },
                        { startX: bl.x, startY: bl.y, endX: tl.x, endY: tl.y, confidence: 0.9, source: 'vector' }
                    );
                }
            }
        }
        
        console.log(`  Found ${walls.length} vector walls from ${constructPathCount} constructPath operations`);
        
        // If no walls found but we had operations, log more details
        if (walls.length === 0 && ops.fnArray.length > 0) {
            console.warn('  ⚠️ No vector walls extracted despite having operations');
            console.log('  Trying alternative approach...');
            
            // Let's try a different approach - look at the raw operations
            for (let i = 0; i < ops.fnArray.length && i < 20; i++) {
                console.log(`  Op ${i}: ${ops.fnArray[i]}, args:`, ops.argsArray[i]);
            }
        }
        
        return walls;
    }

    async extractRasterWalls(page, viewport) {
        console.log('🖼️ Extracting raster walls...');
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        // Render PDF to canvas
        await page.render({
            canvasContext: ctx,
            viewport: viewport
        }).promise;
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const walls = [];
        
        // Parameters for line detection
        const threshold = 100; // Darkness threshold
        const minLength = 20; // Minimum line length in pixels
        const scanStep = 3; // Scan every 3rd pixel for speed
        
        // Detect horizontal lines
        for (let y = 0; y < canvas.height; y += scanStep) {
            let lineStart = null;
            
            for (let x = 0; x < canvas.width; x++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx+1] + imageData.data[idx+2]) / 3;
                
                if (gray < threshold) {
                    if (!lineStart) lineStart = x;
                } else {
                    if (lineStart && (x - lineStart) > minLength) {
                        walls.push({
                            startX: lineStart,
                            startY: y,
                            endX: x,
                            endY: y,
                            confidence: 0.7,
                            source: 'raster'
                        });
                    }
                    lineStart = null;
                }
            }
            
            // Check end of line
            if (lineStart && (canvas.width - lineStart) > minLength) {
                walls.push({
                    startX: lineStart,
                    startY: y,
                    endX: canvas.width,
                    endY: y,
                    confidence: 0.7,
                    source: 'raster'
                });
            }
        }
        
        // Detect vertical lines
        for (let x = 0; x < canvas.width; x += scanStep) {
            let lineStart = null;
            
            for (let y = 0; y < canvas.height; y++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx+1] + imageData.data[idx+2]) / 3;
                
                if (gray < threshold) {
                    if (!lineStart) lineStart = y;
                } else {
                    if (lineStart && (y - lineStart) > minLength) {
                        walls.push({
                            startX: x,
                            startY: lineStart,
                            endX: x,
                            endY: y,
                            confidence: 0.7,
                            source: 'raster'
                        });
                    }
                    lineStart = null;
                }
            }
            
            // Check end of line
            if (lineStart && (canvas.height - lineStart) > minLength) {
                walls.push({
                    startX: x,
                    startY: lineStart,
                    endX: x,
                    endY: canvas.height,
                    confidence: 0.7,
                    source: 'raster'
                });
            }
        }
        
        console.log(`  Found ${walls.length} raster walls`);
        return walls;
    }

    mergeWalls(vectorWalls, rasterWalls) {
        const allWalls = [];
        
        // Add all vector walls (higher priority)
        allWalls.push(...vectorWalls);
        
        // Add raster walls that don't overlap with vector walls
        const tolerance = 5;
        rasterWalls.forEach(rasterWall => {
            let isOverlapping = false;
            
            for (const vectorWall of vectorWalls) {
                if (this.wallsOverlap(rasterWall, vectorWall, tolerance)) {
                    isOverlapping = true;
                    break;
                }
            }
            
            if (!isOverlapping) {
                allWalls.push(rasterWall);
            }
        });
        
        console.log(`🔄 Merged to ${allWalls.length} total walls`);
        return allWalls;
    }

    wallsOverlap(wall1, wall2, tolerance) {
        // Check if two walls are essentially the same
        const dist1 = this.pointDistance(wall1.startX, wall1.startY, wall2.startX, wall2.startY);
        const dist2 = this.pointDistance(wall1.endX, wall1.endY, wall2.endX, wall2.endY);
        const dist3 = this.pointDistance(wall1.startX, wall1.startY, wall2.endX, wall2.endY);
        const dist4 = this.pointDistance(wall1.endX, wall1.endY, wall2.startX, wall2.startY);
        
        return (dist1 < tolerance && dist2 < tolerance) || 
               (dist3 < tolerance && dist4 < tolerance);
    }

    mergeCollinearSegments(walls) {
        console.log(`🔗 Merging collinear segments from ${walls.length} walls...`);
        const merged = [];
        const used = new Set();
        
        // Helper function to check if two segments are collinear
        const areCollinear = (w1, w2, tolerance = 10) => {
            // Calculate direction vectors
            const v1x = w1.endX - w1.startX;
            const v1y = w1.endY - w1.startY;
            const v2x = w2.endX - w2.startX;
            const v2y = w2.endY - w2.startY;
            
            // Normalize vectors
            const len1 = Math.sqrt(v1x * v1x + v1y * v1y);
            const len2 = Math.sqrt(v2x * v2x + v2y * v2y);
            
            if (len1 < 0.001 || len2 < 0.001) return false;
            
            const n1x = v1x / len1;
            const n1y = v1y / len1;
            const n2x = v2x / len2;
            const n2y = v2y / len2;
            
            // Check if parallel (dot product close to 1 or -1)
            const dot = Math.abs(n1x * n2x + n1y * n2y);
            if (dot < 0.98) return false;
            
            // Check if on same line (perpendicular distance)
            const dx = w2.startX - w1.startX;
            const dy = w2.startY - w1.startY;
            const cross = Math.abs(dx * n1y - dy * n1x);
            
            return cross < tolerance;
        };
        
        // Helper function to get distance between point and segment
        const pointToSegmentDistance = (px, py, x1, y1, x2, y2) => {
            const dx = x2 - x1;
            const dy = y2 - y1;
            const len2 = dx * dx + dy * dy;
            
            if (len2 < 0.001) {
                return Math.sqrt((px - x1) * (px - x1) + (py - y1) * (py - y1));
            }
            
            let t = ((px - x1) * dx + (py - y1) * dy) / len2;
            t = Math.max(0, Math.min(1, t));
            
            const projX = x1 + t * dx;
            const projY = y1 + t * dy;
            
            return Math.sqrt((px - projX) * (px - projX) + (py - projY) * (py - projY));
        };
        
        // Group walls by orientation (horizontal vs vertical)
        const horizontal = [];
        const vertical = [];
        const diagonal = [];
        
        walls.forEach((wall, idx) => {
            const dx = Math.abs(wall.endX - wall.startX);
            const dy = Math.abs(wall.endY - wall.startY);
            
            if (dy < 5) { // Horizontal (within 5 pixels)
                horizontal.push({ wall, idx });
            } else if (dx < 5) { // Vertical (within 5 pixels)
                vertical.push({ wall, idx });
            } else {
                diagonal.push({ wall, idx });
            }
        });
        
        // Create line groups for merging
        const lineGroups = [];
        
        // Process all walls to find connected groups
        for (let i = 0; i < walls.length; i++) {
            if (used.has(i)) continue;
            
            const group = [i];
            used.add(i);
            
            // Find all walls that should be merged with this one
            for (let j = i + 1; j < walls.length; j++) {
                if (used.has(j)) continue;
                
                // Check if walls are collinear
                if (areCollinear(walls[i], walls[j], 12)) {
                    // Check gap distance between segments
                    const gap1 = Math.sqrt(
                        Math.pow(walls[j].startX - walls[i].endX, 2) + 
                        Math.pow(walls[j].startY - walls[i].endY, 2)
                    );
                    const gap2 = Math.sqrt(
                        Math.pow(walls[i].startX - walls[j].endX, 2) + 
                        Math.pow(walls[i].startY - walls[j].endY, 2)
                    );
                    const gap3 = Math.sqrt(
                        Math.pow(walls[j].endX - walls[i].endX, 2) + 
                        Math.pow(walls[j].endY - walls[i].endY, 2)
                    );
                    const gap4 = Math.sqrt(
                        Math.pow(walls[j].startX - walls[i].startX, 2) + 
                        Math.pow(walls[j].startY - walls[i].startY, 2)
                    );
                    
                    const minGap = Math.min(gap1, gap2, gap3, gap4);
                    
                    // Merge if gap is small enough
                    if (minGap < 40) {
                        group.push(j);
                        used.add(j);
                    }
                }
            }
            
            lineGroups.push(group);
        }
        
        // Merge each group into a single line
        lineGroups.forEach(group => {
            if (group.length === 1) {
                // Single wall, add as-is
                merged.push(walls[group[0]]);
            } else {
                // Multiple walls to merge
                let allPoints = [];
                let maxConfidence = 0;
                let source = walls[group[0]].source;
                
                group.forEach(idx => {
                    const wall = walls[idx];
                    allPoints.push({ x: wall.startX, y: wall.startY });
                    allPoints.push({ x: wall.endX, y: wall.endY });
                    maxConfidence = Math.max(maxConfidence, wall.confidence);
                });
                
                // Find the extreme points for the merged line
                let minX = Infinity, maxX = -Infinity;
                let minY = Infinity, maxY = -Infinity;
                
                allPoints.forEach(p => {
                    minX = Math.min(minX, p.x);
                    maxX = Math.max(maxX, p.x);
                    minY = Math.min(minY, p.y);
                    maxY = Math.max(maxY, p.y);
                });
                
                // Determine if horizontal or vertical
                const isHorizontal = (maxY - minY) < (maxX - minX);
                
                if (isHorizontal) {
                    // Create horizontal line
                    const avgY = allPoints.reduce((sum, p) => sum + p.y, 0) / allPoints.length;
                    merged.push({
                        startX: minX,
                        startY: avgY,
                        endX: maxX,
                        endY: avgY,
                        confidence: maxConfidence,
                        source: source,
                        merged: true
                    });
                } else {
                    // Create vertical line
                    const avgX = allPoints.reduce((sum, p) => sum + p.x, 0) / allPoints.length;
                    merged.push({
                        startX: avgX,
                        startY: minY,
                        endX: avgX,
                        endY: maxY,
                        confidence: maxConfidence,
                        source: source,
                        merged: true
                    });
                }
            }
        });
        
        console.log(`  Merged ${walls.length} segments into ${merged.length} walls`);
        return merged;
    }

    clusterWalls(walls) {
        // First, merge collinear segments that are close together
        const merged = this.mergeCollinearSegments(walls);
        
        // Then apply DBSCAN clustering to merge nearby endpoints
        const epsilon = 10;  // Increased from 5 for better merging
        const points = [];
        
        merged.forEach((wall, idx) => {
            points.push({ x: wall.startX, y: wall.startY, wallIdx: idx, isStart: true });
            points.push({ x: wall.endX, y: wall.endY, wallIdx: idx, isStart: false });
        });
        
        const clusters = [];
        const visited = new Set();
        
        points.forEach((point, idx) => {
            if (visited.has(idx)) return;
            
            const neighbors = [];
            points.forEach((p, i) => {
                if (i !== idx) {
                    const dist = this.pointDistance(point.x, point.y, p.x, p.y);
                    if (dist <= epsilon) neighbors.push(i);
                }
            });
            
            if (neighbors.length > 0) {
                const cluster = [idx, ...neighbors];
                cluster.forEach(i => visited.add(i));
                clusters.push(cluster);
            }
        });
        
        // Apply clustering
        const finalWalls = [...merged];
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
                    finalWalls[point.wallIdx].startX = cx;
                    finalWalls[point.wallIdx].startY = cy;
                } else {
                    finalWalls[point.wallIdx].endX = cx;
                    finalWalls[point.wallIdx].endY = cy;
                }
            });
        });
        
        return finalWalls;
    }

    detectRooms(walls) {
        // Simplified room detection
        // In production, implement full planar graph algorithm
        return [];
    }

    pointDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
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
    module.exports = PDFDecoderV2;
}