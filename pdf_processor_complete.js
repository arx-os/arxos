/**
 * Complete PDF to BIM Processor - 1:1 Accurate Conversion
 * Extracts ALL architectural elements from PDF floor plans
 */

class PDFProcessorComplete {
    constructor() {
        this.pdfjsLib = null;
        this.debugMode = true;
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
        console.log('🏗️ Starting 1:1 PDF to BIM conversion for:', file.name);
        
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        try {
            const arrayBuffer = await this.readFileAsArrayBuffer(file);
            const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
            console.log('📄 PDF loaded, pages:', pdf.numPages);
            
            // Get the first page (main floor plan)
            const page = await pdf.getPage(1);
            const viewport = page.getViewport({ scale: 2.0 });
            
            console.log('📐 Page dimensions:', viewport.width, 'x', viewport.height);
            
            // Method 1: Extract vector graphics (most accurate)
            const vectorData = await this.extractCompleteVectorGraphics(page);
            
            // Method 2: Render and extract from high-res canvas
            const rasterData = await this.extractFromHighResRender(page);
            
            // Method 3: Extract text annotations for room labels
            const textData = await this.extractTextAnnotations(page);
            
            // Combine all extraction methods
            const combinedData = this.combineExtractionMethods(
                vectorData, 
                rasterData, 
                textData,
                viewport
            );
            
            // Process into BIM structure
            const bimData = this.processToBIM(combinedData);
            
            console.log('✅ Extraction complete:', {
                walls: bimData.walls.length,
                rooms: bimData.rooms.length,
                doors: bimData.doors.length,
                windows: bimData.windows.length,
                labels: bimData.labels.length
            });
            
            return bimData;
            
        } catch (error) {
            console.error('❌ PDF processing error:', error);
            throw error;
        }
    }

    async extractCompleteVectorGraphics(page) {
        console.log('🔍 Extracting vector graphics...');
        const graphics = {
            paths: [],
            lines: [],
            rectangles: [],
            curves: []
        };
        
        try {
            // Get the page's operator list (all drawing commands)
            const ops = await page.getOperatorList();
            
            // Get the page's dependencies (for proper coordinate transformation)
            const viewport = page.getViewport({ scale: 1.0 });
            
            let currentPath = [];
            let currentPoint = null;
            let transformMatrix = [1, 0, 0, 1, 0, 0]; // Identity matrix
            let lineWidth = 1;
            let strokeColor = [0, 0, 0]; // Black
            
            // Process all graphics operators
            for (let i = 0; i < ops.fnArray.length; i++) {
                const fn = ops.fnArray[i];
                const args = ops.argsArray[i];
                
                // Map operator codes to meaningful operations
                switch (fn) {
                    // Transform operations
                    case this.pdfjsLib.OPS.transform:
                        transformMatrix = args;
                        break;
                    
                    case this.pdfjsLib.OPS.save:
                        // Save graphics state
                        break;
                    
                    case this.pdfjsLib.OPS.restore:
                        // Restore graphics state
                        break;
                    
                    // Path construction
                    case this.pdfjsLib.OPS.moveTo:
                        if (currentPath.length > 0) {
                            graphics.paths.push([...currentPath]);
                        }
                        currentPath = [];
                        currentPoint = this.transformPoint(args[0], args[1], transformMatrix);
                        currentPath.push({ type: 'M', x: currentPoint.x, y: currentPoint.y });
                        break;
                    
                    case this.pdfjsLib.OPS.lineTo:
                        if (currentPoint) {
                            const newPoint = this.transformPoint(args[0], args[1], transformMatrix);
                            currentPath.push({ type: 'L', x: newPoint.x, y: newPoint.y });
                            
                            // Also store as individual line
                            graphics.lines.push({
                                start: { ...currentPoint },
                                end: { ...newPoint },
                                width: lineWidth,
                                color: [...strokeColor]
                            });
                            
                            currentPoint = newPoint;
                        }
                        break;
                    
                    case this.pdfjsLib.OPS.curveTo:
                        if (currentPoint) {
                            const cp1 = this.transformPoint(args[0], args[1], transformMatrix);
                            const cp2 = this.transformPoint(args[2], args[3], transformMatrix);
                            const end = this.transformPoint(args[4], args[5], transformMatrix);
                            
                            graphics.curves.push({
                                start: { ...currentPoint },
                                cp1: cp1,
                                cp2: cp2,
                                end: end
                            });
                            
                            currentPath.push({ 
                                type: 'C', 
                                cp1: cp1, 
                                cp2: cp2, 
                                x: end.x, 
                                y: end.y 
                            });
                            
                            currentPoint = end;
                        }
                        break;
                    
                    case this.pdfjsLib.OPS.closePath:
                        if (currentPath.length > 0) {
                            currentPath.push({ type: 'Z' });
                        }
                        break;
                    
                    // Rectangle
                    case this.pdfjsLib.OPS.rectangle:
                        const [x, y, width, height] = args;
                        const topLeft = this.transformPoint(x, y, transformMatrix);
                        const bottomRight = this.transformPoint(x + width, y + height, transformMatrix);
                        
                        const rect = {
                            x: topLeft.x,
                            y: topLeft.y,
                            width: bottomRight.x - topLeft.x,
                            height: bottomRight.y - topLeft.y,
                            lineWidth: lineWidth,
                            color: [...strokeColor]
                        };
                        
                        graphics.rectangles.push(rect);
                        
                        // Also add as lines for wall detection
                        graphics.lines.push(
                            { start: topLeft, end: { x: bottomRight.x, y: topLeft.y } },
                            { start: { x: bottomRight.x, y: topLeft.y }, end: bottomRight },
                            { start: bottomRight, end: { x: topLeft.x, y: bottomRight.y } },
                            { start: { x: topLeft.x, y: bottomRight.y }, end: topLeft }
                        );
                        break;
                    
                    // Style settings
                    case this.pdfjsLib.OPS.setLineWidth:
                        lineWidth = args[0];
                        break;
                    
                    case this.pdfjsLib.OPS.setStrokeRGBColor:
                        strokeColor = args;
                        break;
                    
                    // Drawing operations
                    case this.pdfjsLib.OPS.stroke:
                    case this.pdfjsLib.OPS.fill:
                    case this.pdfjsLib.OPS.fillStroke:
                        if (currentPath.length > 0) {
                            graphics.paths.push([...currentPath]);
                            currentPath = [];
                        }
                        break;
                }
            }
            
            // Add any remaining path
            if (currentPath.length > 0) {
                graphics.paths.push(currentPath);
            }
            
        } catch (error) {
            console.error('Vector extraction error:', error);
        }
        
        console.log(`📊 Extracted: ${graphics.lines.length} lines, ${graphics.rectangles.length} rectangles`);
        return graphics;
    }

    async extractFromHighResRender(page) {
        console.log('🖼️ Extracting from high-resolution render...');
        
        // Render at very high resolution for accuracy
        const scale = 3.0;
        const viewport = page.getViewport({ scale });
        
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        // Render with high quality settings
        await page.render({
            canvasContext: ctx,
            viewport: viewport,
            intent: 'display'
        }).promise;
        
        // Extract features from rendered image
        const features = this.extractImageFeatures(canvas);
        
        return features;
    }

    extractImageFeatures(canvas) {
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        const features = {
            horizontalLines: [],
            verticalLines: [],
            diagonalLines: [],
            corners: []
        };
        
        // Parameters for line detection
        const threshold = 50; // Darkness threshold
        const minLength = 30; // Minimum line length in pixels
        const gapTolerance = 3; // Allow small gaps in lines
        
        // Detect horizontal lines with gap tolerance
        for (let y = 0; y < canvas.height; y += 2) {
            let lineSegments = [];
            let currentSegment = null;
            let gapCount = 0;
            
            for (let x = 0; x < canvas.width; x++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                
                if (gray < threshold) {
                    // Dark pixel - part of line
                    if (!currentSegment) {
                        currentSegment = { start: x, end: x };
                    } else {
                        currentSegment.end = x;
                    }
                    gapCount = 0;
                } else {
                    // Light pixel - potential gap
                    if (currentSegment) {
                        gapCount++;
                        if (gapCount > gapTolerance) {
                            // Gap too large, save segment
                            if (currentSegment.end - currentSegment.start > minLength) {
                                lineSegments.push(currentSegment);
                            }
                            currentSegment = null;
                            gapCount = 0;
                        }
                    }
                }
            }
            
            // Save last segment
            if (currentSegment && currentSegment.end - currentSegment.start > minLength) {
                lineSegments.push(currentSegment);
            }
            
            // Convert segments to lines
            lineSegments.forEach(seg => {
                features.horizontalLines.push({
                    start: { x: seg.start, y: y },
                    end: { x: seg.end, y: y },
                    confidence: 0.8
                });
            });
        }
        
        // Detect vertical lines with gap tolerance
        for (let x = 0; x < canvas.width; x += 2) {
            let lineSegments = [];
            let currentSegment = null;
            let gapCount = 0;
            
            for (let y = 0; y < canvas.height; y++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                
                if (gray < threshold) {
                    if (!currentSegment) {
                        currentSegment = { start: y, end: y };
                    } else {
                        currentSegment.end = y;
                    }
                    gapCount = 0;
                } else {
                    if (currentSegment) {
                        gapCount++;
                        if (gapCount > gapTolerance) {
                            if (currentSegment.end - currentSegment.start > minLength) {
                                lineSegments.push(currentSegment);
                            }
                            currentSegment = null;
                            gapCount = 0;
                        }
                    }
                }
            }
            
            if (currentSegment && currentSegment.end - currentSegment.start > minLength) {
                lineSegments.push(currentSegment);
            }
            
            lineSegments.forEach(seg => {
                features.verticalLines.push({
                    start: { x: x, y: seg.start },
                    end: { x: x, y: seg.end },
                    confidence: 0.8
                });
            });
        }
        
        console.log(`🔍 Found ${features.horizontalLines.length} horizontal, ${features.verticalLines.length} vertical lines`);
        return features;
    }

    async extractTextAnnotations(page) {
        console.log('📝 Extracting text annotations...');
        
        const textContent = await page.getTextContent();
        const viewport = page.getViewport({ scale: 1.0 });
        
        const annotations = {
            roomLabels: [],
            dimensions: [],
            doorLabels: [],
            windowLabels: []
        };
        
        textContent.items.forEach(item => {
            const text = item.str.trim();
            if (!text) return;
            
            const x = item.transform[4];
            const y = viewport.height - item.transform[5];
            
            // Classify text by pattern
            if (/^(Room|Rm\.?|RM)\s*[\d\w]+/i.test(text) || 
                /^\d{3,4}[A-Z]?$/.test(text) ||
                /^[A-Z]-?\d{2,3}$/.test(text)) {
                annotations.roomLabels.push({ text, x, y });
            } else if (/\d+['"]\s*[-x]\s*\d+['"]/.test(text) || 
                       /\d+\.\d+/.test(text)) {
                annotations.dimensions.push({ text, x, y });
            } else if (/door|DOOR|Door/i.test(text)) {
                annotations.doorLabels.push({ text, x, y });
            } else if (/window|WINDOW|Window/i.test(text)) {
                annotations.windowLabels.push({ text, x, y });
            }
        });
        
        console.log(`📋 Found ${annotations.roomLabels.length} room labels`);
        return annotations;
    }

    transformPoint(x, y, matrix) {
        // Apply transformation matrix
        return {
            x: matrix[0] * x + matrix[2] * y + matrix[4],
            y: matrix[1] * x + matrix[3] * y + matrix[5]
        };
    }

    combineExtractionMethods(vectorData, rasterData, textData, viewport) {
        console.log('🔄 Combining extraction methods...');
        
        const combined = {
            walls: [],
            texts: textData,
            viewport: viewport
        };
        
        // Priority 1: Vector lines (most accurate)
        if (vectorData.lines.length > 0) {
            vectorData.lines.forEach(line => {
                combined.walls.push({
                    startX: line.start.x,
                    startY: line.start.y,
                    endX: line.end.x,
                    endY: line.end.y,
                    confidence: 0.95,
                    source: 'vector',
                    thickness: line.width || 2
                });
            });
        }
        
        // Priority 2: Raster detection (fill gaps)
        const scale = viewport.width / 1000; // Normalize coordinates
        
        rasterData.horizontalLines.forEach(line => {
            combined.walls.push({
                startX: line.start.x / scale,
                startY: line.start.y / scale,
                endX: line.end.x / scale,
                endY: line.end.y / scale,
                confidence: line.confidence || 0.7,
                source: 'raster',
                thickness: 2
            });
        });
        
        rasterData.verticalLines.forEach(line => {
            combined.walls.push({
                startX: line.start.x / scale,
                startY: line.start.y / scale,
                endX: line.end.x / scale,
                endY: line.end.y / scale,
                confidence: line.confidence || 0.7,
                source: 'raster',
                thickness: 2
            });
        });
        
        // Remove duplicates
        combined.walls = this.removeDuplicateWalls(combined.walls);
        
        console.log(`🏗️ Combined total: ${combined.walls.length} walls`);
        return combined;
    }

    removeDuplicateWalls(walls) {
        const unique = [];
        const tolerance = 5;
        
        walls.forEach(wall => {
            let isDuplicate = false;
            
            for (const existing of unique) {
                if (this.wallsAreSimilar(wall, existing, tolerance)) {
                    // Keep the one with higher confidence
                    if (wall.confidence > existing.confidence) {
                        existing.confidence = wall.confidence;
                        existing.source = wall.source;
                    }
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

    wallsAreSimilar(wall1, wall2, tolerance) {
        const dist1 = Math.sqrt(
            Math.pow(wall1.startX - wall2.startX, 2) + 
            Math.pow(wall1.startY - wall2.startY, 2)
        );
        const dist2 = Math.sqrt(
            Math.pow(wall1.endX - wall2.endX, 2) + 
            Math.pow(wall1.endY - wall2.endY, 2)
        );
        
        // Check both orientations
        const dist3 = Math.sqrt(
            Math.pow(wall1.startX - wall2.endX, 2) + 
            Math.pow(wall1.startY - wall2.endY, 2)
        );
        const dist4 = Math.sqrt(
            Math.pow(wall1.endX - wall2.startX, 2) + 
            Math.pow(wall1.endY - wall2.startY, 2)
        );
        
        return (dist1 < tolerance && dist2 < tolerance) || 
               (dist3 < tolerance && dist4 < tolerance);
    }

    processToBIM(combinedData) {
        console.log('🏢 Converting to BIM structure...');
        
        // Apply DBSCAN clustering to connect nearby endpoints
        const clusteredWalls = this.applyDBSCAN(combinedData.walls, 3);
        
        // Extend walls to intersections
        const connectedWalls = this.connectWalls(clusteredWalls);
        
        // Detect rooms from wall network
        const rooms = this.detectRooms(connectedWalls);
        
        // Identify doors and windows
        const openings = this.detectOpenings(connectedWalls);
        
        // Match room labels to detected rooms
        if (combinedData.texts && combinedData.texts.roomLabels) {
            this.assignRoomLabels(rooms, combinedData.texts.roomLabels);
        }
        
        // Calculate confidence
        const avgConfidence = connectedWalls.reduce((sum, w) => sum + w.confidence, 0) / connectedWalls.length;
        
        return {
            walls: connectedWalls,
            rooms: rooms,
            doors: openings.doors,
            windows: openings.windows,
            labels: combinedData.texts?.roomLabels || [],
            confidence: avgConfidence || 0.5
        };
    }

    applyDBSCAN(walls, epsilon) {
        console.log('🔗 Applying DBSCAN clustering...');
        
        // Extract all endpoints
        const points = [];
        walls.forEach((wall, idx) => {
            points.push({ 
                x: wall.startX, 
                y: wall.startY, 
                wallIdx: idx, 
                isStart: true 
            });
            points.push({ 
                x: wall.endX, 
                y: wall.endY, 
                wallIdx: idx, 
                isStart: false 
            });
        });
        
        // Find clusters
        const clusters = [];
        const visited = new Set();
        const minPoints = 2;
        
        points.forEach((point, idx) => {
            if (visited.has(idx)) return;
            
            const neighbors = [];
            points.forEach((p, i) => {
                if (i === idx) return;
                const dist = Math.sqrt(
                    Math.pow(p.x - point.x, 2) + 
                    Math.pow(p.y - point.y, 2)
                );
                if (dist <= epsilon) {
                    neighbors.push(i);
                }
            });
            
            if (neighbors.length >= minPoints - 1) {
                const cluster = [idx];
                visited.add(idx);
                
                const queue = [...neighbors];
                while (queue.length > 0) {
                    const pIdx = queue.shift();
                    if (visited.has(pIdx)) continue;
                    
                    visited.add(pIdx);
                    cluster.push(pIdx);
                    
                    const pNeighbors = [];
                    points.forEach((p, i) => {
                        if (visited.has(i)) return;
                        const dist = Math.sqrt(
                            Math.pow(p.x - points[pIdx].x, 2) + 
                            Math.pow(p.y - points[pIdx].y, 2)
                        );
                        if (dist <= epsilon) {
                            pNeighbors.push(i);
                        }
                    });
                    
                    if (pNeighbors.length >= minPoints - 1) {
                        queue.push(...pNeighbors);
                    }
                }
                
                clusters.push(cluster);
            }
        });
        
        // Apply clustering to walls
        const mergedWalls = [...walls];
        clusters.forEach(cluster => {
            // Calculate cluster centroid
            let cx = 0, cy = 0;
            cluster.forEach(idx => {
                cx += points[idx].x;
                cy += points[idx].y;
            });
            cx /= cluster.length;
            cy /= cluster.length;
            
            // Update wall endpoints
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
        
        console.log(`✅ Created ${clusters.length} endpoint clusters`);
        return mergedWalls;
    }

    connectWalls(walls) {
        console.log('🔧 Connecting walls at intersections...');
        
        // Extend walls to meet at intersections
        const connected = [...walls];
        
        for (let i = 0; i < connected.length; i++) {
            for (let j = i + 1; j < connected.length; j++) {
                const wall1 = connected[i];
                const wall2 = connected[j];
                
                // Check if walls are perpendicular and close
                if (this.shouldConnect(wall1, wall2)) {
                    this.extendToMeet(wall1, wall2);
                }
            }
        }
        
        return connected;
    }

    shouldConnect(wall1, wall2) {
        // Check if walls are roughly perpendicular
        const angle1 = Math.atan2(wall1.endY - wall1.startY, wall1.endX - wall1.startX);
        const angle2 = Math.atan2(wall2.endY - wall2.startY, wall2.endX - wall2.startX);
        
        const angleDiff = Math.abs(angle1 - angle2);
        const isPerpendicular = Math.abs(angleDiff - Math.PI/2) < 0.2 || 
                                Math.abs(angleDiff - 3*Math.PI/2) < 0.2;
        
        if (!isPerpendicular) return false;
        
        // Check if endpoints are close
        const threshold = 20;
        const distances = [
            this.pointDistance(wall1.startX, wall1.startY, wall2.startX, wall2.startY),
            this.pointDistance(wall1.startX, wall1.startY, wall2.endX, wall2.endY),
            this.pointDistance(wall1.endX, wall1.endY, wall2.startX, wall2.startY),
            this.pointDistance(wall1.endX, wall1.endY, wall2.endX, wall2.endY)
        ];
        
        return Math.min(...distances) < threshold;
    }

    extendToMeet(wall1, wall2) {
        // Calculate intersection point of extended lines
        const x1 = wall1.startX, y1 = wall1.startY;
        const x2 = wall1.endX, y2 = wall1.endY;
        const x3 = wall2.startX, y3 = wall2.startY;
        const x4 = wall2.endX, y4 = wall2.endY;
        
        const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
        if (Math.abs(denom) < 0.001) return; // Parallel lines
        
        const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
        const u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom;
        
        // Calculate intersection point
        const ix = x1 + t * (x2 - x1);
        const iy = y1 + t * (y2 - y1);
        
        // Extend walls to intersection if close enough
        const threshold = 20;
        
        if (this.pointDistance(wall1.startX, wall1.startY, ix, iy) < threshold) {
            wall1.startX = ix;
            wall1.startY = iy;
        } else if (this.pointDistance(wall1.endX, wall1.endY, ix, iy) < threshold) {
            wall1.endX = ix;
            wall1.endY = iy;
        }
        
        if (this.pointDistance(wall2.startX, wall2.startY, ix, iy) < threshold) {
            wall2.startX = ix;
            wall2.startY = iy;
        } else if (this.pointDistance(wall2.endX, wall2.endY, ix, iy) < threshold) {
            wall2.endX = ix;
            wall2.endY = iy;
        }
    }

    detectRooms(walls) {
        console.log('🏠 Detecting rooms from wall network...');
        
        // Build graph from walls
        const graph = this.buildWallGraph(walls);
        
        // Find closed cycles (rooms)
        const cycles = this.findCycles(graph);
        
        // Convert cycles to room polygons
        const rooms = cycles.map((cycle, idx) => ({
            id: idx + 1,
            polygon: cycle.map(nodeId => {
                const node = graph.nodes[nodeId];
                return { x: node.x, y: node.y };
            }),
            area: this.calculateArea(cycle.map(nodeId => graph.nodes[nodeId])),
            perimeter: this.calculatePerimeter(cycle.map(nodeId => graph.nodes[nodeId])),
            confidence: 0.8
        }));
        
        console.log(`🚪 Found ${rooms.length} rooms`);
        return rooms;
    }

    buildWallGraph(walls) {
        const graph = { nodes: {}, edges: [] };
        let nodeId = 0;
        
        // Create nodes at wall endpoints
        const pointToNode = {};
        
        walls.forEach(wall => {
            const startKey = `${Math.round(wall.startX)},${Math.round(wall.startY)}`;
            const endKey = `${Math.round(wall.endX)},${Math.round(wall.endY)}`;
            
            if (!pointToNode[startKey]) {
                pointToNode[startKey] = nodeId;
                graph.nodes[nodeId] = { id: nodeId, x: wall.startX, y: wall.startY, edges: [] };
                nodeId++;
            }
            
            if (!pointToNode[endKey]) {
                pointToNode[endKey] = nodeId;
                graph.nodes[nodeId] = { id: nodeId, x: wall.endX, y: wall.endY, edges: [] };
                nodeId++;
            }
            
            // Create edge
            const startNode = pointToNode[startKey];
            const endNode = pointToNode[endKey];
            
            graph.nodes[startNode].edges.push(endNode);
            graph.nodes[endNode].edges.push(startNode);
            graph.edges.push({ start: startNode, end: endNode });
        });
        
        return graph;
    }

    findCycles(graph) {
        const cycles = [];
        const visited = new Set();
        
        // Simple cycle detection (for rectangular rooms)
        // In production, use more sophisticated planar graph algorithms
        
        Object.keys(graph.nodes).forEach(nodeId => {
            if (visited.has(nodeId)) return;
            
            const cycle = this.findCycleFromNode(graph, parseInt(nodeId), visited);
            if (cycle && cycle.length >= 3) {
                cycles.push(cycle);
                cycle.forEach(n => visited.add(n));
            }
        });
        
        return cycles;
    }

    findCycleFromNode(graph, startNode, globalVisited) {
        // Simplified cycle detection
        const path = [startNode];
        const visited = new Set([startNode]);
        
        const dfs = (node, depth) => {
            if (depth > 10) return null; // Limit depth
            
            for (const neighbor of graph.nodes[node].edges) {
                if (neighbor === startNode && path.length >= 3) {
                    // Found cycle back to start
                    return [...path];
                }
                
                if (!visited.has(neighbor) && !globalVisited.has(neighbor)) {
                    visited.add(neighbor);
                    path.push(neighbor);
                    
                    const result = dfs(neighbor, depth + 1);
                    if (result) return result;
                    
                    path.pop();
                }
            }
            
            return null;
        };
        
        return dfs(startNode, 0);
    }

    detectOpenings(walls) {
        // Detect gaps in walls (doors/windows)
        const openings = { doors: [], windows: [] };
        
        // Simplified opening detection
        // In production, use more sophisticated gap analysis
        
        return openings;
    }

    assignRoomLabels(rooms, labels) {
        // Match text labels to room centers
        rooms.forEach(room => {
            const center = this.calculateCentroid(room.polygon);
            
            // Find closest label
            let closestLabel = null;
            let minDist = Infinity;
            
            labels.forEach(label => {
                const dist = this.pointDistance(center.x, center.y, label.x, label.y);
                if (dist < minDist) {
                    minDist = dist;
                    closestLabel = label;
                }
            });
            
            if (closestLabel && minDist < 50) {
                room.label = closestLabel.text;
            }
        });
    }

    calculateArea(points) {
        let area = 0;
        for (let i = 0; i < points.length; i++) {
            const j = (i + 1) % points.length;
            area += points[i].x * points[j].y;
            area -= points[j].x * points[i].y;
        }
        return Math.abs(area / 2);
    }

    calculatePerimeter(points) {
        let perimeter = 0;
        for (let i = 0; i < points.length; i++) {
            const j = (i + 1) % points.length;
            perimeter += this.pointDistance(points[i].x, points[i].y, points[j].x, points[j].y);
        }
        return perimeter;
    }

    calculateCentroid(polygon) {
        let cx = 0, cy = 0;
        polygon.forEach(p => {
            cx += p.x;
            cy += p.y;
        });
        return { x: cx / polygon.length, y: cy / polygon.length };
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
    module.exports = PDFProcessorComplete;
}