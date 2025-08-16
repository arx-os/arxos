/**
 * Hybrid PDF Decoder - Combines multiple extraction methods
 * Uses inverted room detection as primary, with fallbacks
 */

class PDFDecoderHybrid {
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
        console.log('🚀 Starting hybrid PDF extraction...');
        
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        const arrayBuffer = await this.readFileAsArrayBuffer(file);
        const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
        const page = await pdf.getPage(1);
        
        const viewport = page.getViewport({ scale: 2.0 });
        console.log(`📐 Page: ${viewport.width}x${viewport.height}px`);
        
        // Render to canvas for analysis
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        await page.render({
            canvasContext: ctx,
            viewport: viewport
        }).promise;
        
        // Method 1: Inverted room detection (primary)
        const roomData = await this.detectRoomsInverted(canvas, ctx);
        
        // Method 2: Direct wall detection (fallback/supplement)
        const wallData = await this.detectWallsDirect(canvas, ctx);
        
        // Combine results
        const combined = this.combineResults(roomData, wallData);
        
        console.log(`✅ Extraction complete: ${combined.rooms.length} rooms, ${combined.walls.length} walls`);
        
        return combined;
    }

    async detectRoomsInverted(canvas, ctx) {
        console.log('🔄 Detecting rooms using inverted method...');
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        const width = canvas.width;
        const height = canvas.height;
        
        // Create binary image
        const binary = new Uint8Array(width * height);
        const threshold = 200;
        
        for (let i = 0; i < data.length; i += 4) {
            const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;
            binary[i / 4] = gray > threshold ? 1 : 0;
        }
        
        // Find connected components (rooms)
        const rooms = [];
        const visited = new Uint8Array(width * height);
        const minRoomSize = 100;
        
        for (let y = 10; y < height - 10; y += 5) {
            for (let x = 10; x < width - 10; x += 5) {
                const idx = y * width + x;
                
                if (binary[idx] === 1 && visited[idx] === 0) {
                    const room = this.floodFill(binary, visited, x, y, width, height);
                    
                    if (room.pixels > minRoomSize) {
                        rooms.push({
                            id: `room_${rooms.length + 1}`,
                            bounds: room.bounds,
                            center: room.center,
                            area: room.pixels,
                            confidence: 0.9
                        });
                    }
                }
            }
        }
        
        // Extract walls from room boundaries
        const walls = this.extractWallsFromRooms(rooms);
        
        return { rooms, walls };
    }

    floodFill(binary, visited, startX, startY, width, height) {
        let pixels = 0;
        let minX = width, maxX = 0, minY = height, maxY = 0;
        let sumX = 0, sumY = 0;
        
        const stack = [{ x: startX, y: startY }];
        
        while (stack.length > 0) {
            const { x, y } = stack.pop();
            const idx = y * width + x;
            
            if (x < 0 || x >= width || y < 0 || y >= height) continue;
            if (visited[idx] === 1 || binary[idx] === 0) continue;
            
            visited[idx] = 1;
            pixels++;
            
            minX = Math.min(minX, x);
            maxX = Math.max(maxX, x);
            minY = Math.min(minY, y);
            maxY = Math.max(maxY, y);
            sumX += x;
            sumY += y;
            
            // Add neighbors
            stack.push(
                { x: x - 1, y },
                { x: x + 1, y },
                { x, y: y - 1 },
                { x, y: y + 1 }
            );
        }
        
        return {
            pixels,
            bounds: { minX, minY, maxX, maxY },
            center: { x: sumX / pixels, y: sumY / pixels }
        };
    }

    extractWallsFromRooms(rooms) {
        const walls = [];
        const wallMap = new Map();
        
        rooms.forEach(room => {
            const b = room.bounds;
            
            // Top wall
            this.addWall(wallMap, b.minX, b.minY, b.maxX, b.minY, room.id);
            // Right wall
            this.addWall(wallMap, b.maxX, b.minY, b.maxX, b.maxY, room.id);
            // Bottom wall
            this.addWall(wallMap, b.maxX, b.maxY, b.minX, b.maxY, room.id);
            // Left wall
            this.addWall(wallMap, b.minX, b.maxY, b.minX, b.minY, room.id);
        });
        
        wallMap.forEach(wall => walls.push(wall));
        return walls;
    }

    addWall(wallMap, x1, y1, x2, y2, roomId) {
        // Normalize direction
        if (x1 > x2 || (x1 === x2 && y1 > y2)) {
            [x1, x2, y1, y2] = [x2, x1, y2, y1];
        }
        
        const key = `${Math.round(x1)},${Math.round(y1)}-${Math.round(x2)},${Math.round(y2)}`;
        
        if (!wallMap.has(key)) {
            wallMap.set(key, {
                startX: x1,
                startY: y1,
                endX: x2,
                endY: y2,
                confidence: 0.85,
                source: 'room_boundary',
                rooms: [roomId]
            });
        } else {
            const wall = wallMap.get(key);
            if (!wall.rooms.includes(roomId)) {
                wall.rooms.push(roomId);
                wall.confidence = 0.95; // Higher confidence for shared walls
            }
        }
    }

    async detectWallsDirect(canvas, ctx) {
        console.log('📏 Detecting walls directly...');
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const walls = [];
        
        // Simplified line detection
        const threshold = 100;
        const minLength = 30;
        
        // Horizontal lines
        for (let y = 0; y < canvas.height; y += 3) {
            let lineStart = null;
            
            for (let x = 0; x < canvas.width; x++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx + 1] + imageData.data[idx + 2]) / 3;
                
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
                            source: 'direct'
                        });
                    }
                    lineStart = null;
                }
            }
        }
        
        // Vertical lines
        for (let x = 0; x < canvas.width; x += 3) {
            let lineStart = null;
            
            for (let y = 0; y < canvas.height; y++) {
                const idx = (y * canvas.width + x) * 4;
                const gray = (imageData.data[idx] + imageData.data[idx + 1] + imageData.data[idx + 2]) / 3;
                
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
                            source: 'direct'
                        });
                    }
                    lineStart = null;
                }
            }
        }
        
        return walls;
    }

    combineResults(roomData, directWalls) {
        // Start with room-based walls (higher confidence)
        const allWalls = [...roomData.walls];
        const wallKeys = new Set();
        
        // Add keys of existing walls
        roomData.walls.forEach(wall => {
            const key = this.getWallKey(wall);
            wallKeys.add(key);
        });
        
        // Add direct walls that don't overlap
        let addedCount = 0;
        directWalls.forEach(wall => {
            const key = this.getWallKey(wall);
            if (!wallKeys.has(key)) {
                allWalls.push(wall);
                wallKeys.add(key);
                addedCount++;
            }
        });
        
        console.log(`  Added ${addedCount} supplemental walls from direct detection`);
        
        // Calculate overall confidence
        const avgConfidence = allWalls.length > 0
            ? allWalls.reduce((sum, w) => sum + w.confidence, 0) / allWalls.length
            : 0;
        
        return {
            rooms: roomData.rooms,
            walls: allWalls,
            confidence: avgConfidence,
            stats: {
                roomBasedWalls: roomData.walls.length,
                directWalls: directWalls.length,
                combinedWalls: allWalls.length
            }
        };
    }

    getWallKey(wall) {
        const x1 = Math.round(wall.startX / 10) * 10;
        const y1 = Math.round(wall.startY / 10) * 10;
        const x2 = Math.round(wall.endX / 10) * 10;
        const y2 = Math.round(wall.endY / 10) * 10;
        
        if (x1 < x2 || (x1 === x2 && y1 < y2)) {
            return `${x1},${y1}-${x2},${y2}`;
        } else {
            return `${x2},${y2}-${x1},${y1}`;
        }
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
    module.exports = PDFDecoderHybrid;
}