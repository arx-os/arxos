/**
 * AI Ingestion Service
 * Handles AI-powered conversion of floor plans to ArxObjects
 */

class AIIngestionService {
    constructor(config = ARXOS_CONFIG) {
        this.config = config;
        this.logger = new Logger('AIIngestionService');
    }

    /**
     * Process any supported file type with AI
     * @param {File} file - The file to process
     * @param {Object} options - Processing options
     * @returns {Promise<Array>} Array of ArxObjects
     */
    async processFile(file, options = {}) {
        this.logger.info(`Processing file: ${file.name}`);
        
        try {
            // Validate file
            this.validateFile(file);
            
            // Check cache first
            if (this.config.get('cache.cacheProcessedFiles')) {
                const cached = await this.checkCache(file);
                if (cached) {
                    this.logger.info('Returning cached result');
                    return cached;
                }
            }
            
            // Determine file type and process accordingly
            const fileType = this.detectFileType(file);
            let result;
            
            switch (fileType) {
                case 'ifc':
                    result = await this.processIFC(file, options);
                    break;
                    
                case 'pdf':
                    result = await this.processPDF(file, options);
                    break;
                    
                case 'image':
                    result = await this.processImage(file, options);
                    break;
                    
                case 'lidar':
                    result = await this.processLiDAR(file, options);
                    break;
                    
                default:
                    throw new Error(`Unsupported file type: ${fileType}`);
            }
            
            // Cache result
            if (this.config.get('cache.cacheProcessedFiles')) {
                await this.cacheResult(file, result);
            }
            
            return result;
            
        } catch (error) {
            this.logger.error('Processing failed', error);
            
            // Try fallback if configured
            if (this.config.get('ingestion.fallbackToManual')) {
                return this.fallbackToManual(file);
            }
            
            throw error;
        }
    }

    /**
     * Process image file with AI vision
     */
    async processImage(file, options = {}) {
        const startTime = performance.now();
        
        // Convert file to base64
        const base64 = await this.fileToBase64(file);
        
        // Prepare request
        const request = {
            image: base64,
            filename: file.name,
            prompt: this.getFloorPlanPrompt(options),
            provider: this.config.get('ingestion.aiProvider'),
            model: this.config.get('ingestion.aiModel')
        };
        
        // Call backend API
        const response = await this.callAPI('/ai/ingest', request);
        
        // Parse and validate response
        const arxObjects = this.parseAIResponse(response);
        
        const processingTime = performance.now() - startTime;
        this.logger.info(`Processed in ${processingTime}ms, found ${arxObjects.length} objects`);
        
        return arxObjects;
    }

    /**
     * Process PDF file
     */
    async processPDF(file, options = {}) {
        // First try to extract vector graphics
        const vectorGraphics = await this.extractVectorGraphics(file);
        
        if (vectorGraphics && vectorGraphics.length > 0) {
            this.logger.info('Using vector graphics from PDF');
            return this.vectorToArxObjects(vectorGraphics);
        }
        
        // Fall back to rasterization and AI vision
        this.logger.info('Converting PDF to image for AI processing');
        const imageFile = await this.pdfToImage(file);
        return this.processImage(imageFile, options);
    }

    /**
     * Process IFC file (stub - to be implemented)
     */
    async processIFC(file, options = {}) {
        throw new Error('IFC processing not yet implemented');
    }

    /**
     * Process LiDAR file (stub - to be implemented)
     */
    async processLiDAR(file, options = {}) {
        throw new Error('LiDAR processing not yet implemented');
    }

    /**
     * Generate prompt for floor plan analysis
     */
    getFloorPlanPrompt(options = {}) {
        const basePrompt = `Analyze this floor plan image and extract the following information:

1. WALLS: Identify all walls as line segments. For each wall provide:
   - Start point (x1, y1) in pixels from top-left origin
   - End point (x2, y2) in pixels from top-left origin
   - Wall type (exterior, interior, partition)
   - Estimated thickness (thin, standard, thick)

2. ROOMS: Identify all enclosed spaces. For each room provide:
   - Room boundary as polygon points
   - Room label/number if visible
   - Room type (classroom, office, bathroom, corridor, etc.)
   - Approximate area

3. OPENINGS: Identify doors and windows. For each provide:
   - Position (x, y)
   - Type (door, window, opening)
   - Width estimate
   - Direction (if door)

4. LABELS: Extract all text labels including:
   - Room numbers
   - Room names
   - Dimensions
   - Any other annotations

5. METADATA:
   - Estimated scale (pixels per meter)
   - Building orientation if indicated
   - Floor number if visible

Return the data as structured JSON following this schema:
{
  "walls": [
    {
      "id": "string",
      "x1": number,
      "y1": number,
      "x2": number,
      "y2": number,
      "type": "exterior|interior|partition",
      "thickness": "thin|standard|thick"
    }
  ],
  "rooms": [
    {
      "id": "string",
      "boundary": [[x,y], [x,y], ...],
      "label": "string",
      "type": "string",
      "area": number
    }
  ],
  "openings": [
    {
      "id": "string",
      "x": number,
      "y": number,
      "type": "door|window|opening",
      "width": number,
      "direction": "up|down|left|right|null"
    }
  ],
  "labels": [
    {
      "text": "string",
      "x": number,
      "y": number,
      "type": "room_number|room_name|dimension|annotation"
    }
  ],
  "metadata": {
    "scale": number,
    "orientation": "north|south|east|west|unknown",
    "floor": "string|null"
  }
}

Be precise with coordinates. Detect all walls including partial walls. Group connected walls properly.`;

        // Add any custom instructions from options
        if (options.customInstructions) {
            return basePrompt + '\n\nAdditional instructions: ' + options.customInstructions;
        }
        
        return basePrompt;
    }

    /**
     * Parse AI response and convert to ArxObjects
     */
    parseAIResponse(response) {
        const arxObjects = [];
        
        if (!response || !response.data) {
            throw new Error('Invalid AI response');
        }
        
        const data = typeof response.data === 'string' ? 
            JSON.parse(response.data) : response.data;
        
        // Convert walls to ArxObjects
        if (data.walls && Array.isArray(data.walls)) {
            data.walls.forEach((wall, index) => {
                arxObjects.push(this.wallToArxObject(wall, index));
            });
        }
        
        // Convert rooms to ArxObjects (as spaces)
        if (data.rooms && Array.isArray(data.rooms)) {
            data.rooms.forEach((room, index) => {
                arxObjects.push(this.roomToArxObject(room, index));
            });
        }
        
        // Convert openings to ArxObjects
        if (data.openings && Array.isArray(data.openings)) {
            data.openings.forEach((opening, index) => {
                arxObjects.push(this.openingToArxObject(opening, index));
            });
        }
        
        return arxObjects;
    }

    /**
     * Convert wall data to ArxObject
     */
    wallToArxObject(wall, index) {
        // Assume pixel to meter conversion (will be refined with scale)
        const scale = 0.01; // 1 pixel = 1cm default
        
        const x1 = wall.x1 * scale;
        const y1 = wall.y1 * scale;
        const x2 = wall.x2 * scale;
        const y2 = wall.y2 * scale;
        
        const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        const angle = Math.atan2(y2 - y1, x2 - x1);
        
        // Determine wall thickness based on type
        const thickness = {
            'thin': 0.1,
            'standard': 0.2,
            'thick': 0.3
        }[wall.thickness] || 0.2;
        
        return {
            id: wall.id || `wall_${Date.now()}_${index}`,
            type: 'StructuralWall',
            subtype: wall.type || 'interior',
            x1: x1,
            y1: y1,
            z1: 0,
            x2: x2,
            y2: y2,
            z2: 0,
            centerX: (x1 + x2) / 2,
            centerY: (y1 + y2) / 2,
            centerZ: 1.5, // Mid-height
            length: length,
            width: thickness,
            height: 3.0, // Standard ceiling height
            rotation: angle,
            confidence: 0.9, // High confidence from AI
            source: 'ai_vision',
            metadata: {
                aiProvider: this.config.get('ingestion.aiProvider'),
                processedAt: new Date().toISOString(),
                originalCoords: {
                    x1: wall.x1,
                    y1: wall.y1,
                    x2: wall.x2,
                    y2: wall.y2
                }
            }
        };
    }

    /**
     * Convert room data to ArxObject
     */
    roomToArxObject(room, index) {
        const scale = 0.01; // 1 pixel = 1cm default
        
        // Calculate room center and bounds
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        room.boundary.forEach(point => {
            minX = Math.min(minX, point[0]);
            minY = Math.min(minY, point[1]);
            maxX = Math.max(maxX, point[0]);
            maxY = Math.max(maxY, point[1]);
        });
        
        const centerX = (minX + maxX) / 2 * scale;
        const centerY = (minY + maxY) / 2 * scale;
        const width = (maxX - minX) * scale;
        const depth = (maxY - minY) * scale;
        
        return {
            id: room.id || `room_${Date.now()}_${index}`,
            type: 'Space',
            subtype: room.type || 'room',
            label: room.label || '',
            centerX: centerX,
            centerY: centerY,
            centerZ: 1.5,
            width: width,
            depth: depth,
            height: 3.0,
            area: room.area || (width * depth),
            boundary: room.boundary.map(p => ({
                x: p[0] * scale,
                y: p[1] * scale
            })),
            confidence: 0.85,
            source: 'ai_vision',
            metadata: {
                aiProvider: this.config.get('ingestion.aiProvider'),
                processedAt: new Date().toISOString()
            }
        };
    }

    /**
     * Convert opening data to ArxObject
     */
    openingToArxObject(opening, index) {
        const scale = 0.01; // 1 pixel = 1cm default
        
        const width = (opening.width || 100) * scale; // Default 1m width
        const height = opening.type === 'window' ? 1.5 : 2.1; // Window vs door height
        
        return {
            id: opening.id || `${opening.type}_${Date.now()}_${index}`,
            type: opening.type === 'door' ? 'Door' : 'Window',
            x: opening.x * scale,
            y: opening.y * scale,
            z: opening.type === 'window' ? 1.0 : 0, // Window sill height
            width: width,
            height: height,
            direction: opening.direction || null,
            confidence: 0.8,
            source: 'ai_vision',
            metadata: {
                aiProvider: this.config.get('ingestion.aiProvider'),
                processedAt: new Date().toISOString()
            }
        };
    }

    /**
     * Call backend API
     */
    async callAPI(endpoint, data) {
        const url = this.config.get('api.baseUrl') + endpoint;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: this.config.get('api.headers'),
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }
        
        return response.json();
    }

    /**
     * Validate file before processing
     */
    validateFile(file) {
        // Check file size
        const fileType = this.detectFileType(file);
        const maxSize = this.config.get(`ingestion.maxFileSize.${fileType}`);
        
        if (file.size > maxSize) {
            throw new Error(`File too large. Maximum size is ${maxSize / 1024 / 1024}MB`);
        }
        
        // Check file format
        const supportedFormats = this.config.get(`ingestion.supportedFormats.${fileType}`);
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!supportedFormats.includes(extension)) {
            throw new Error(`Unsupported file format: ${extension}`);
        }
        
        return true;
    }

    /**
     * Detect file type from extension
     */
    detectFileType(file) {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        
        const formats = this.config.get('ingestion.supportedFormats');
        
        for (const [type, extensions] of Object.entries(formats)) {
            if (extensions.includes(extension)) {
                return type;
            }
        }
        
        return 'unknown';
    }

    /**
     * Convert file to base64
     */
    async fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    /**
     * Check cache for processed file
     */
    async checkCache(file) {
        // Generate cache key based on file content
        const key = await this.generateCacheKey(file);
        
        // Check cache storage
        const cached = localStorage.getItem(`arxos_cache_${key}`);
        
        if (cached) {
            const data = JSON.parse(cached);
            
            // Check if cache is still valid
            const age = Date.now() - data.timestamp;
            const ttl = this.config.get('cache.ttl');
            
            if (age < ttl) {
                return data.result;
            }
        }
        
        return null;
    }

    /**
     * Cache processing result
     */
    async cacheResult(file, result) {
        const key = await this.generateCacheKey(file);
        
        const data = {
            timestamp: Date.now(),
            filename: file.name,
            result: result
        };
        
        try {
            localStorage.setItem(`arxos_cache_${key}`, JSON.stringify(data));
        } catch (error) {
            this.logger.warn('Failed to cache result', error);
        }
    }

    /**
     * Generate cache key from file
     */
    async generateCacheKey(file) {
        const text = file.name + file.size + file.lastModified;
        const encoder = new TextEncoder();
        const data = encoder.encode(text);
        const hash = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hash));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    /**
     * Fallback to manual extraction (stub)
     */
    async fallbackToManual(file) {
        this.logger.warn('Falling back to manual extraction');
        
        // This would load the archived manual extraction engine if needed
        throw new Error('Manual extraction fallback not implemented');
    }

    /**
     * Extract vector graphics from PDF (stub)
     */
    async extractVectorGraphics(file) {
        // This would use pdf.js or similar to extract vector paths
        return null;
    }

    /**
     * Convert PDF to image (stub)
     */
    async pdfToImage(file) {
        // This would use pdf.js to render PDF to canvas
        throw new Error('PDF to image conversion not implemented');
    }

    /**
     * Convert vector graphics to ArxObjects (stub)
     */
    vectorToArxObjects(vectorGraphics) {
        // This would convert SVG/vector paths to ArxObjects
        return [];
    }
}

// Simple logger class
class Logger {
    constructor(name) {
        this.name = name;
        this.enabled = true;
    }

    info(message, ...args) {
        if (this.enabled) {
            console.log(`[${this.name}] ${message}`, ...args);
        }
    }

    warn(message, ...args) {
        if (this.enabled) {
            console.warn(`[${this.name}] ${message}`, ...args);
        }
    }

    error(message, ...args) {
        if (this.enabled) {
            console.error(`[${this.name}] ${message}`, ...args);
        }
    }
}

// Make available globally in browser
if (typeof window !== 'undefined') {
    window.AIIngestionService = AIIngestionService;
}