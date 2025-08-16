/**
 * PDF Processing Module for Arxos BIM Converter
 * Handles PDF parsing, wall extraction, and topology building
 */

class PDFProcessor {
    constructor() {
        this.pdfjsLib = null;
        this.walls = [];
        this.segments = [];
        this.confidence = 0;
        this.processingStages = [
            'Extracting PDF pages',
            'Detecting wall segments',
            'Clustering endpoints (DBSCAN)',
            'Building topology graph',
            'Detecting rooms',
            'Analyzing semantics'
        ];
    }

    /**
     * Initialize PDF.js library
     */
    async initialize() {
        // Load PDF.js if not already loaded
        if (!window.pdfjsLib) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            document.head.appendChild(script);
            
            await new Promise(resolve => {
                script.onload = resolve;
            });
            
            // Set worker
            pdfjsLib.GlobalWorkerOptions.workerSrc = 
                'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }
        
        this.pdfjsLib = window.pdfjsLib;
    }

    /**
     * Process uploaded PDF file
     */
    async processPDF(file, options = {}) {
        console.log('Processing PDF:', file.name);
        
        // Initialize if needed
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        try {
            // Read file as ArrayBuffer
            const arrayBuffer = await this.readFileAsArrayBuffer(file);
            
            // Load PDF document
            const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
            console.log('PDF loaded, pages:', pdf.numPages);
            
            // Process each page
            const results = [];
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                const pageResult = await this.processPage(pdf, pageNum, options);
                results.push(pageResult);
            }
            
            // Combine results from all pages
            return this.combineResults(results);
            
        } catch (error) {
            console.error('PDF processing error:', error);
            throw error;
        }
    }

    /**
     * Process a single PDF page
     */
    async processPage(pdf, pageNumber, options) {
        const page = await pdf.getPage(pageNumber);
        
        // Get viewport
        const viewport = page.getViewport({ scale: 2.0 });
        
        // Create canvas
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        // Render PDF page to canvas
        await page.render({
            canvasContext: context,
            viewport: viewport
        }).promise;
        
        console.log(`Page ${pageNumber} rendered to canvas`);
        
        // Extract walls from canvas
        const walls = await this.extractWalls(canvas, options);
        
        // Extract text (for room labels)
        const textContent = await page.getTextContent();
        const labels = this.extractRoomLabels(textContent, viewport);
        
        return {
            pageNumber,
            walls,
            labels,
            dimensions: {
                width: viewport.width,
                height: viewport.height
            }
        };
    }

    /**
     * Extract walls from rendered canvas
     */
    async extractWalls(canvas, options) {
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // Convert to grayscale
        const grayData = this.toGrayscale(imageData);
        
        // Edge detection
        const edges = this.cannyEdgeDetection(grayData, canvas.width, canvas.height);
        
        // Hough transform for line detection
        const lines = this.houghTransform(edges, canvas.width, canvas.height);
        
        // Filter and merge lines into walls
        const walls = this.processLines(lines);
        
        // Apply DBSCAN clustering to merge nearby endpoints
        const clusteredWalls = this.clusterEndpoints(walls, options.epsilon || 5);
        
        return clusteredWalls;
    }

    /**
     * Convert image to grayscale
     */
    toGrayscale(imageData) {
        const data = imageData.data;
        const grayData = new Uint8Array(imageData.width * imageData.height);
        
        for (let i = 0, j = 0; i < data.length; i += 4, j++) {
            // Use luminance formula
            grayData[j] = Math.round(0.299 * data[i] + 0.587 * data[i+1] + 0.114 * data[i+2]);
        }
        
        return grayData;
    }

    /**
     * Canny edge detection
     */
    cannyEdgeDetection(grayData, width, height) {
        // Simplified Canny edge detection
        const edges = new Uint8Array(width * height);
        
        // Apply Gaussian blur
        const blurred = this.gaussianBlur(grayData, width, height);
        
        // Calculate gradients
        const gradients = this.sobelOperator(blurred, width, height);
        
        // Non-maximum suppression
        const suppressed = this.nonMaximumSuppression(gradients, width, height);
        
        // Double threshold
        const threshold = this.doubleThreshold(suppressed, 50, 150);
        
        // Edge tracking by hysteresis
        return this.edgeTracking(threshold, width, height);
    }

    /**
     * Gaussian blur
     */
    gaussianBlur(data, width, height) {
        const kernel = [
            [1, 2, 1],
            [2, 4, 2],
            [1, 2, 1]
        ];
        const kernelSum = 16;
        
        const blurred = new Uint8Array(width * height);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                let sum = 0;
                
                for (let ky = -1; ky <= 1; ky++) {
                    for (let kx = -1; kx <= 1; kx++) {
                        const idx = (y + ky) * width + (x + kx);
                        sum += data[idx] * kernel[ky + 1][kx + 1];
                    }
                }
                
                blurred[y * width + x] = Math.round(sum / kernelSum);
            }
        }
        
        return blurred;
    }

    /**
     * Sobel operator for gradient calculation
     */
    sobelOperator(data, width, height) {
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
        
        const gradients = {
            magnitude: new Float32Array(width * height),
            direction: new Float32Array(width * height)
        };
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                let gx = 0, gy = 0;
                
                for (let ky = -1; ky <= 1; ky++) {
                    for (let kx = -1; kx <= 1; kx++) {
                        const idx = (y + ky) * width + (x + kx);
                        gx += data[idx] * sobelX[ky + 1][kx + 1];
                        gy += data[idx] * sobelY[ky + 1][kx + 1];
                    }
                }
                
                const idx = y * width + x;
                gradients.magnitude[idx] = Math.sqrt(gx * gx + gy * gy);
                gradients.direction[idx] = Math.atan2(gy, gx);
            }
        }
        
        return gradients;
    }

    /**
     * Non-maximum suppression
     */
    nonMaximumSuppression(gradients, width, height) {
        const suppressed = new Float32Array(width * height);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = y * width + x;
                const mag = gradients.magnitude[idx];
                const dir = gradients.direction[idx];
                
                // Quantize direction to 0, 45, 90, or 135 degrees
                const angle = ((dir + Math.PI) * 180 / Math.PI) % 180;
                
                let n1, n2;
                if (angle < 22.5 || angle >= 157.5) {
                    // Horizontal edge
                    n1 = gradients.magnitude[idx - 1];
                    n2 = gradients.magnitude[idx + 1];
                } else if (angle < 67.5) {
                    // Diagonal /
                    n1 = gradients.magnitude[idx - width - 1];
                    n2 = gradients.magnitude[idx + width + 1];
                } else if (angle < 112.5) {
                    // Vertical edge
                    n1 = gradients.magnitude[idx - width];
                    n2 = gradients.magnitude[idx + width];
                } else {
                    // Diagonal \
                    n1 = gradients.magnitude[idx - width + 1];
                    n2 = gradients.magnitude[idx + width - 1];
                }
                
                if (mag >= n1 && mag >= n2) {
                    suppressed[idx] = mag;
                }
            }
        }
        
        return suppressed;
    }

    /**
     * Double threshold
     */
    doubleThreshold(data, low, high) {
        const result = new Uint8Array(data.length);
        
        for (let i = 0; i < data.length; i++) {
            if (data[i] >= high) {
                result[i] = 255; // Strong edge
            } else if (data[i] >= low) {
                result[i] = 128; // Weak edge
            }
        }
        
        return result;
    }

    /**
     * Edge tracking by hysteresis
     */
    edgeTracking(data, width, height) {
        const result = new Uint8Array(data.length);
        
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = y * width + x;
                
                if (data[idx] === 255) {
                    result[idx] = 255;
                    
                    // Check neighbors for weak edges
                    for (let dy = -1; dy <= 1; dy++) {
                        for (let dx = -1; dx <= 1; dx++) {
                            const nIdx = (y + dy) * width + (x + dx);
                            if (data[nIdx] === 128) {
                                result[nIdx] = 255;
                            }
                        }
                    }
                }
            }
        }
        
        return result;
    }

    /**
     * Hough transform for line detection
     */
    houghTransform(edges, width, height) {
        const lines = [];
        const threshold = 100; // Minimum votes
        
        // Simplified Hough transform
        const maxRho = Math.sqrt(width * width + height * height);
        const rhoStep = 1;
        const thetaStep = Math.PI / 180;
        
        const accumulator = {};
        
        // Vote for lines
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                if (edges[y * width + x] > 0) {
                    for (let theta = 0; theta < Math.PI; theta += thetaStep) {
                        const rho = x * Math.cos(theta) + y * Math.sin(theta);
                        const key = `${Math.round(rho)},${Math.round(theta * 180 / Math.PI)}`;
                        accumulator[key] = (accumulator[key] || 0) + 1;
                    }
                }
            }
        }
        
        // Find peaks in accumulator
        for (const key in accumulator) {
            if (accumulator[key] >= threshold) {
                const [rho, theta] = key.split(',').map(Number);
                lines.push({
                    rho,
                    theta: theta * Math.PI / 180,
                    votes: accumulator[key]
                });
            }
        }
        
        return lines;
    }

    /**
     * Process Hough lines into wall segments
     */
    processLines(lines) {
        const walls = [];
        
        lines.forEach(line => {
            // Convert polar to cartesian coordinates
            const cos = Math.cos(line.theta);
            const sin = Math.sin(line.theta);
            
            // Find line endpoints (simplified)
            let x1, y1, x2, y2;
            
            if (Math.abs(cos) > 0.5) {
                // More horizontal
                x1 = 0;
                y1 = line.rho / sin;
                x2 = 1000; // Canvas width
                y2 = (line.rho - x2 * cos) / sin;
            } else {
                // More vertical
                y1 = 0;
                x1 = line.rho / cos;
                y2 = 1000; // Canvas height
                x2 = (line.rho - y2 * sin) / cos;
            }
            
            walls.push({
                startX: x1,
                startY: y1,
                endX: x2,
                endY: y2,
                confidence: Math.min(line.votes / 200, 1.0)
            });
        });
        
        return walls;
    }

    /**
     * DBSCAN clustering for endpoint merging
     */
    clusterEndpoints(walls, epsilon) {
        // Extract all endpoints
        const points = [];
        walls.forEach((wall, idx) => {
            points.push({ x: wall.startX, y: wall.startY, wallIdx: idx, isStart: true });
            points.push({ x: wall.endX, y: wall.endY, wallIdx: idx, isStart: false });
        });
        
        // Simple DBSCAN implementation
        const clusters = [];
        const visited = new Set();
        
        points.forEach((point, idx) => {
            if (visited.has(idx)) return;
            
            const neighbors = this.getNeighbors(points, idx, epsilon);
            if (neighbors.length >= 2) {
                const cluster = [idx];
                visited.add(idx);
                
                const queue = [...neighbors];
                while (queue.length > 0) {
                    const pIdx = queue.shift();
                    if (visited.has(pIdx)) continue;
                    
                    visited.add(pIdx);
                    cluster.push(pIdx);
                    
                    const pNeighbors = this.getNeighbors(points, pIdx, epsilon);
                    if (pNeighbors.length >= 2) {
                        queue.push(...pNeighbors);
                    }
                }
                
                clusters.push(cluster);
            }
        });
        
        // Merge clustered endpoints
        const mergedWalls = [...walls];
        clusters.forEach(cluster => {
            // Calculate centroid
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
        
        return mergedWalls;
    }

    /**
     * Get neighbors within epsilon distance
     */
    getNeighbors(points, idx, epsilon) {
        const neighbors = [];
        const point = points[idx];
        
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
        
        return neighbors;
    }

    /**
     * Extract room labels from text content
     */
    extractRoomLabels(textContent, viewport) {
        const labels = [];
        
        textContent.items.forEach(item => {
            const text = item.str.trim();
            
            // Look for room numbers or names
            if (/^(Room|Rm\.?)\s*\d+/i.test(text) || 
                /^\d{3,4}$/.test(text) ||
                /^[A-Z]\d{2,3}$/.test(text)) {
                
                const transform = item.transform;
                labels.push({
                    text,
                    x: transform[4],
                    y: viewport.height - transform[5], // Flip Y coordinate
                });
            }
        });
        
        return labels;
    }

    /**
     * Combine results from multiple pages
     */
    combineResults(results) {
        const combined = {
            walls: [],
            rooms: [],
            labels: [],
            confidence: 0
        };
        
        let totalConfidence = 0;
        let wallCount = 0;
        
        results.forEach(result => {
            result.walls.forEach(wall => {
                combined.walls.push(wall);
                totalConfidence += wall.confidence;
                wallCount++;
            });
            
            combined.labels.push(...result.labels);
        });
        
        // Calculate average confidence
        combined.confidence = wallCount > 0 ? totalConfidence / wallCount : 0;
        
        // Detect rooms from walls
        combined.rooms = this.detectRooms(combined.walls);
        
        return combined;
    }

    /**
     * Detect rooms from wall segments
     */
    detectRooms(walls) {
        // Simplified room detection
        // In production, this would use the planar graph algorithm
        const rooms = [];
        
        // For now, create sample rooms based on wall patterns
        // This is a placeholder - real implementation would use
        // the planar graph face detection algorithm
        
        return rooms;
    }

    /**
     * Read file as ArrayBuffer
     */
    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }
}

// Export for use in HTML
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PDFProcessor;
}