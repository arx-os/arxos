/**
 * Fixed PDF Decoder - Properly scales vector coordinates to match raster
 */

class PDFDecoderFixed {
    constructor() {
        this.pdfjsLib = null;
        this.OPS_MAP = {
            1: 'dependency',
            2: 'setBlendMode',
            5: 'save',
            6: 'restore',
            7: 'transform',
            12: 'moveTo',
            13: 'lineTo',
            14: 'quadraticCurveTo',
            15: 'bezierCurveTo',
            16: 'arcTo',
            17: 'closePath',
            18: 'rectangle',
            19: 'arc',
            20: 'fill',
            21: 'stroke',
            22: 'clip',
            23: 'beginPath',
            25: 'setLineWidth',
            31: 'setStrokeColor',
            32: 'setFillColor',
            69: 'constructPath',
            91: 'constructPath'
        };
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
        console.log('🔍 Starting fixed PDF decoding...');
        
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        const arrayBuffer = await this.readFileAsArrayBuffer(file);
        const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
        const page = await pdf.getPage(1);
        
        // Get viewport at scale 2 for better resolution
        const viewport = page.getViewport({ scale: 2.0 });
        
        console.log(`📐 Page size: ${viewport.width}x${viewport.height}`);
        console.log(`📐 Viewport transform:`, viewport.transform);
        
        // Extract vector graphics
        const ops = await page.getOperatorList();
        const vectorWalls = await this.extractVectorWalls(ops, viewport);
        
        // Extract raster graphics
        const rasterWalls = await this.extractRasterWalls(page, viewport);
        
        // Combine and deduplicate
        const allWalls = this.combineWalls(vectorWalls, rasterWalls);
        
        // Detect rooms
        const rooms = this.detectRooms(allWalls);
        
        // Calculate confidence
        const confidence = this.calculateConfidence(allWalls);
        
        console.log(`✅ Extracted ${allWalls.length} walls with ${Math.round(confidence * 100)}% confidence`);
        
        return {
            walls: allWalls,
            rooms: rooms,
            confidence: confidence
        };
    }

    async extractVectorWalls(ops, viewport) {
        const walls = [];
        let currentPoint = null;
        let currentTransform = [1, 0, 0, 1, 0, 0];
        const transformStack = [];
        
        // Calculate scale factor from viewport
        // PDF coordinates are typically in points (1/72 inch)
        // We need to scale to match the viewport pixel size
        const scale = viewport.scale * 72 / 96; // Assuming 96 DPI screen
        
        for (let i = 0; i < ops.fnArray.length; i++) {
            const opCode = ops.fnArray[i];
            const args = ops.argsArray[i] || [];
            
            // Handle transforms
            if (opCode === 7) { // transform
                currentTransform = this.multiplyTransforms(currentTransform, args);
            } else if (opCode === 5) { // save
                transformStack.push([...currentTransform]);
            } else if (opCode === 6) { // restore
                if (transformStack.length > 0) {
                    currentTransform = transformStack.pop();
                }
            }
            
            // Handle constructPath operations
            if (opCode === 91 || opCode === 69) {
                const pathOps = args[0] || [];
                const pathCoords = args[1] || [];
                let coordIndex = 0;
                
                for (let j = 0; j < pathOps.length; j++) {
                    const pathOp = pathOps[j];
                    
                    // Use numeric codes directly
                    if (pathOp === 2) { // moveTo
                        const x = pathCoords[coordIndex] * scale;
                        const y = pathCoords[coordIndex + 1] * scale;
                        currentPoint = this.transformPoint(x, y, viewport.transform);
                        coordIndex += 2;
                    } else if (pathOp === 3) { // lineTo
                        if (currentPoint) {
                            const x = pathCoords[coordIndex] * scale;
                            const y = pathCoords[coordIndex + 1] * scale;
                            const newPoint = this.transformPoint(x, y, viewport.transform);
                            
                            const length = Math.sqrt(
                                Math.pow(newPoint.x - currentPoint.x, 2) + 
                                Math.pow(newPoint.y - currentPoint.y, 2)
                            );
                            
                            if (length > 1) { // Filter out tiny segments
                                walls.push({
                                    startX: currentPoint.x,
                                    startY: currentPoint.y,
                                    endX: newPoint.x,
                                    endY: newPoint.y,
                                    confidence: 0.95,
                                    source: 'vector'
                                });
                            }
                            
                            currentPoint = newPoint;
                        }
                        coordIndex += 2;
                    } else if (pathOp === 4 || pathOp === 5) { // curveTo
                        // Skip curve control points for now
                        coordIndex += 6;
                    } else if (pathOp === 6) { // rectangle
                        const x = pathCoords[coordIndex] * scale;
                        const y = pathCoords[coordIndex + 1] * scale;
                        const w = pathCoords[coordIndex + 2] * scale;
                        const h = pathCoords[coordIndex + 3] * scale;
                        
                        const tl = this.transformPoint(x, y, viewport.transform);
                        const tr = this.transformPoint(x + w, y, viewport.transform);
                        const br = this.transformPoint(x + w, y + h, viewport.transform);
                        const bl = this.transformPoint(x, y + h, viewport.transform);
                        
                        walls.push(
                            { startX: tl.x, startY: tl.y, endX: tr.x, endY: tr.y, confidence: 0.95, source: 'vector' },
                            { startX: tr.x, startY: tr.y, endX: br.x, endY: br.y, confidence: 0.95, source: 'vector' },
                            { startX: br.x, startY: br.y, endX: bl.x, endY: bl.y, confidence: 0.95, source: 'vector' },
                            { startX: bl.x, startY: bl.y, endX: tl.x, endY: tl.y, confidence: 0.95, source: 'vector' }
                        );
                        
                        coordIndex += 4;
                    }
                }
            }
        }
        
        console.log(`📊 Extracted ${walls.length} vector walls`);
        return walls;
    }

    async extractRasterWalls(page, viewport) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        await page.render({
            canvasContext: ctx,
            viewport: viewport
        }).promise;
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const walls = [];
        
        // Detect horizontal lines
        for (let y = 0; y < canvas.height; y += 3) {
            let lineStart = null;
            
            for (let x = 0; x < canvas.width; x++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx+1] + imageData.data[idx+2]) / 3;
                
                if (gray < 100) { // Dark pixel
                    if (!lineStart) lineStart = x;
                } else {
                    if (lineStart && (x - lineStart) > 20) {
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
        }
        
        // Detect vertical lines
        for (let x = 0; x < canvas.width; x += 3) {
            let lineStart = null;
            
            for (let y = 0; y < canvas.height; y++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx+1] + imageData.data[idx+2]) / 3;
                
                if (gray < 100) { // Dark pixel
                    if (!lineStart) lineStart = y;
                } else {
                    if (lineStart && (y - lineStart) > 20) {
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
        }
        
        console.log(`🖼️ Extracted ${walls.length} raster walls`);
        return walls;
    }

    transformPoint(x, y, transform) {
        return {
            x: transform[0] * x + transform[2] * y + transform[4],
            y: transform[1] * x + transform[3] * y + transform[5]
        };
    }

    multiplyTransforms(t1, t2) {
        return [
            t1[0] * t2[0] + t1[2] * t2[1],
            t1[1] * t2[0] + t1[3] * t2[1],
            t1[0] * t2[2] + t1[2] * t2[3],
            t1[1] * t2[2] + t1[3] * t2[3],
            t1[0] * t2[4] + t1[2] * t2[5] + t1[4],
            t1[1] * t2[4] + t1[3] * t2[5] + t1[5]
        ];
    }

    combineWalls(vectorWalls, rasterWalls) {
        const allWalls = [...vectorWalls, ...rasterWalls];
        
        // Apply DBSCAN clustering to merge nearby endpoints
        const clustered = this.clusterEndpoints(allWalls, 5);
        
        // Remove duplicates
        const unique = this.removeDuplicates(clustered);
        
        return unique;
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
                if (i !== idx) {
                    const dist = Math.sqrt(Math.pow(p.x - point.x, 2) + Math.pow(p.y - point.y, 2));
                    if (dist <= epsilon) neighbors.push(i);
                }
            });
            
            if (neighbors.length > 0) {
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

    removeDuplicates(walls) {
        const unique = [];
        const tolerance = 3;
        
        walls.forEach(wall => {
            let isDuplicate = false;
            
            for (const existing of unique) {
                const d1 = Math.sqrt(Math.pow(wall.startX - existing.startX, 2) + Math.pow(wall.startY - existing.startY, 2));
                const d2 = Math.sqrt(Math.pow(wall.endX - existing.endX, 2) + Math.pow(wall.endY - existing.endY, 2));
                const d3 = Math.sqrt(Math.pow(wall.startX - existing.endX, 2) + Math.pow(wall.startY - existing.endY, 2));
                const d4 = Math.sqrt(Math.pow(wall.endX - existing.startX, 2) + Math.pow(wall.endY - existing.startY, 2));
                
                if ((d1 < tolerance && d2 < tolerance) || (d3 < tolerance && d4 < tolerance)) {
                    isDuplicate = true;
                    break;
                }
            }
            
            if (!isDuplicate) {
                unique.push(wall);
            }
        });
        
        return unique;
    }

    detectRooms(walls) {
        // Simplified room detection
        // In production, use planar graph algorithm
        return [];
    }

    calculateConfidence(walls) {
        if (walls.length === 0) return 0;
        const sum = walls.reduce((acc, w) => acc + (w.confidence || 0.5), 0);
        return sum / walls.length;
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
    module.exports = PDFDecoderFixed;
}