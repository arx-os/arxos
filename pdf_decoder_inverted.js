/**
 * PDF Decoder using Inverted Space Detection
 * Instead of finding walls, find the empty spaces (rooms) and derive walls from boundaries
 */

class PDFDecoderInverted {
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
        console.log('🔍 Starting inverted space detection...');
        
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        const arrayBuffer = await this.readFileAsArrayBuffer(file);
        const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
        const page = await pdf.getPage(1);
        
        const viewport = page.getViewport({ scale: 2.0 });
        console.log(`📐 Viewport: ${viewport.width}x${viewport.height}`);
        
        // Render to canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        await page.render({
            canvasContext: ctx,
            viewport: viewport
        }).promise;
        
        // Find rooms using flood fill
        const rooms = this.findRooms(canvas, ctx);
        
        // Extract walls from room boundaries
        const walls = this.extractWallsFromRooms(rooms);
        
        // Calculate confidence
        const confidence = rooms.length > 0 ? 0.85 : 0;
        
        console.log(`✅ Found ${rooms.length} rooms and ${walls.length} walls`);
        
        return {
            walls: walls,
            rooms: rooms,
            confidence: confidence,
            canvas: canvas
        };
    }

    findRooms(canvas, ctx) {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        const width = canvas.width;
        const height = canvas.height;
        
        // Create binary image (1 = empty/white, 0 = wall/black)
        const binary = new Uint8Array(width * height);
        const threshold = 200; // Threshold for white/empty space
        
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = (y * width + x) * 4;
                const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                binary[y * width + x] = gray > threshold ? 1 : 0;
            }
        }
        
        // Find connected components (rooms) using flood fill
        const visited = new Uint8Array(width * height);
        const rooms = [];
        const minRoomSize = 100; // Minimum pixels for a valid room
        
        for (let y = 10; y < height - 10; y += 5) { // Skip edges
            for (let x = 10; x < width - 10; x += 5) {
                const idx = y * width + x;
                
                if (binary[idx] === 1 && visited[idx] === 0) {
                    // Found unvisited empty space - flood fill to find room
                    const room = this.floodFill(binary, visited, x, y, width, height);
                    
                    if (room.pixels.length > minRoomSize) {
                        // Calculate room bounds and center
                        let minX = width, maxX = 0;
                        let minY = height, maxY = 0;
                        let centerX = 0, centerY = 0;
                        
                        room.pixels.forEach(pixel => {
                            minX = Math.min(minX, pixel.x);
                            maxX = Math.max(maxX, pixel.x);
                            minY = Math.min(minY, pixel.y);
                            maxY = Math.max(maxY, pixel.y);
                            centerX += pixel.x;
                            centerY += pixel.y;
                        });
                        
                        centerX /= room.pixels.length;
                        centerY /= room.pixels.length;
                        
                        rooms.push({
                            id: `room_${rooms.length + 1}`,
                            bounds: { minX, minY, maxX, maxY },
                            center: { x: centerX, y: centerY },
                            area: room.pixels.length,
                            perimeter: room.perimeter
                        });
                    }
                }
            }
        }
        
        console.log(`🏠 Found ${rooms.length} rooms`);
        return rooms;
    }

    floodFill(binary, visited, startX, startY, width, height) {
        const pixels = [];
        const perimeter = [];
        const stack = [{ x: startX, y: startY }];
        
        while (stack.length > 0) {
            const { x, y } = stack.pop();
            const idx = y * width + x;
            
            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            if (visited[idx] === 1 || binary[idx] === 0) continue;
            
            visited[idx] = 1;
            pixels.push({ x, y });
            
            // Check if this pixel is on the perimeter (adjacent to a wall)
            let isPerimeter = false;
            
            // Check 8 neighbors
            const neighbors = [
                { dx: -1, dy: 0 }, { dx: 1, dy: 0 },
                { dx: 0, dy: -1 }, { dx: 0, dy: 1 },
                { dx: -1, dy: -1 }, { dx: 1, dy: -1 },
                { dx: -1, dy: 1 }, { dx: 1, dy: 1 }
            ];
            
            for (const { dx, dy } of neighbors) {
                const nx = x + dx;
                const ny = y + dy;
                
                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    const nidx = ny * width + nx;
                    
                    if (binary[nidx] === 0) {
                        isPerimeter = true;
                    } else if (visited[nidx] === 0) {
                        // Add unvisited empty neighbors to stack
                        stack.push({ x: nx, y: ny });
                    }
                }
            }
            
            if (isPerimeter) {
                perimeter.push({ x, y });
            }
        }
        
        return { pixels, perimeter };
    }

    extractWallsFromRooms(rooms) {
        console.log('🧱 Extracting walls from room perimeters...');
        const walls = [];
        const wallMap = new Map(); // Track unique walls
        
        // For simplicity and performance, use bounding boxes
        // In production, would use more sophisticated perimeter tracing
        rooms.forEach(room => {
            const bounds = room.bounds;
            
            // Only add walls for reasonably sized rooms
            if (room.area > 50) {
                // Add four walls for each room's bounding box
                this.addWallSegment(wallMap, bounds.minX, bounds.minY, bounds.maxX, bounds.minY, room.id);
                this.addWallSegment(wallMap, bounds.maxX, bounds.minY, bounds.maxX, bounds.maxY, room.id);
                this.addWallSegment(wallMap, bounds.maxX, bounds.maxY, bounds.minX, bounds.maxY, room.id);
                this.addWallSegment(wallMap, bounds.minX, bounds.maxY, bounds.minX, bounds.minY, room.id);
            }
        });
        
        // Convert wall map to array
        wallMap.forEach((wall, key) => {
            walls.push(wall);
        });
        
        console.log(`  Extracted ${walls.length} unique wall segments`);
        
        // Merge collinear segments into continuous walls
        return this.mergeCollinearWalls(walls);
    }
    
    tracePerimeter(perimeter) {
        // Convert perimeter pixels into line segments
        const segments = [];
        if (perimeter.length < 2) return segments;
        
        // Sort perimeter points to trace boundary
        const sorted = [...perimeter].sort((a, b) => {
            const angleA = Math.atan2(a.y - perimeter[0].y, a.x - perimeter[0].x);
            const angleB = Math.atan2(b.y - perimeter[0].y, b.x - perimeter[0].x);
            return angleA - angleB;
        });
        
        // Detect straight line segments using Douglas-Peucker algorithm (simplified)
        let current = sorted[0];
        let direction = null;
        let segmentStart = current;
        
        for (let i = 1; i < sorted.length; i++) {
            const next = sorted[i];
            const dx = next.x - current.x;
            const dy = next.y - current.y;
            
            // Check if direction changed (new segment)
            const newDirection = Math.atan2(dy, dx);
            
            if (direction === null) {
                direction = newDirection;
            } else if (Math.abs(newDirection - direction) > 0.2) {
                // Direction changed significantly - end current segment
                segments.push({
                    startX: segmentStart.x,
                    startY: segmentStart.y,
                    endX: current.x,
                    endY: current.y
                });
                segmentStart = current;
                direction = newDirection;
            }
            
            current = next;
        }
        
        // Add final segment
        if (segmentStart !== current) {
            segments.push({
                startX: segmentStart.x,
                startY: segmentStart.y,
                endX: current.x,
                endY: current.y
            });
        }
        
        return segments;
    }
    
    addWallSegment(wallMap, x1, y1, x2, y2, roomId) {
        // Normalize wall direction (always go from left to right, or top to bottom)
        let startX = x1, startY = y1, endX = x2, endY = y2;
        
        if (x1 > x2 || (x1 === x2 && y1 > y2)) {
            startX = x2; startY = y2;
            endX = x1; endY = y1;
        }
        
        // Create unique key for this wall segment
        const key = `${Math.round(startX)},${Math.round(startY)}-${Math.round(endX)},${Math.round(endY)}`;
        
        if (!wallMap.has(key)) {
            wallMap.set(key, {
                startX: startX,
                startY: startY,
                endX: endX,
                endY: endY,
                confidence: 0.9,
                source: 'room_perimeter',
                rooms: [roomId]
            });
        } else {
            // Wall is shared between rooms
            const wall = wallMap.get(key);
            if (!wall.rooms.includes(roomId)) {
                wall.rooms.push(roomId);
                wall.confidence = 0.95; // Higher confidence for shared walls
            }
        }
    }
    
    mergeCollinearWalls(walls) {
        // Group and merge collinear wall segments
        const merged = [];
        const used = new Set();
        
        for (let i = 0; i < walls.length; i++) {
            if (used.has(i)) continue;
            
            const wall1 = walls[i];
            const group = [wall1];
            used.add(i);
            
            // Find all collinear walls
            for (let j = i + 1; j < walls.length; j++) {
                if (used.has(j)) continue;
                
                const wall2 = walls[j];
                
                // Check if walls are collinear
                if (this.areCollinear(wall1, wall2, 5)) {
                    group.push(wall2);
                    used.add(j);
                }
            }
            
            // Merge the group into a single wall
            if (group.length === 1) {
                merged.push(wall1);
            } else {
                merged.push(this.mergeWallGroup(group));
            }
        }
        
        return merged;
    }
    
    areCollinear(w1, w2, tolerance) {
        // Check if two walls are on the same line
        const v1x = w1.endX - w1.startX;
        const v1y = w1.endY - w1.startY;
        const v2x = w2.endX - w2.startX;
        const v2y = w2.endY - w2.startY;
        
        // Check if parallel
        const cross = Math.abs(v1x * v2y - v1y * v2x);
        const len1 = Math.sqrt(v1x * v1x + v1y * v1y);
        const len2 = Math.sqrt(v2x * v2x + v2y * v2y);
        
        if (len1 < 0.001 || len2 < 0.001) return false;
        
        // Normalized cross product should be near zero for parallel lines
        if (cross / (len1 * len2) > 0.1) return false;
        
        // Check if on same line (point-to-line distance)
        const dx = w2.startX - w1.startX;
        const dy = w2.startY - w1.startY;
        const dist = Math.abs(dx * v1y - dy * v1x) / len1;
        
        return dist < tolerance;
    }
    
    mergeWallGroup(group) {
        // Find extent of all walls in group
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;
        let maxConfidence = 0;
        const allRooms = new Set();
        
        group.forEach(wall => {
            minX = Math.min(minX, wall.startX, wall.endX);
            maxX = Math.max(maxX, wall.startX, wall.endX);
            minY = Math.min(minY, wall.startY, wall.endY);
            maxY = Math.max(maxY, wall.startY, wall.endY);
            maxConfidence = Math.max(maxConfidence, wall.confidence);
            
            if (wall.rooms) {
                wall.rooms.forEach(room => allRooms.add(room));
            }
        });
        
        // Create merged wall
        const isHorizontal = (maxX - minX) > (maxY - minY);
        
        return {
            startX: isHorizontal ? minX : (minX + maxX) / 2,
            startY: isHorizontal ? (minY + maxY) / 2 : minY,
            endX: isHorizontal ? maxX : (minX + maxX) / 2,
            endY: isHorizontal ? (minY + maxY) / 2 : maxY,
            confidence: maxConfidence,
            source: 'room_perimeter',
            rooms: Array.from(allRooms),
            merged: true
        };
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
    module.exports = PDFDecoderInverted;
}