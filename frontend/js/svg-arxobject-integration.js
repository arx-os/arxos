/**
 * Arxos SVG + ArxObject Integration Module
 * Core architecture for 1:1 accurate BIM rendering using SVG coordinates and ArxObject intelligence
 * 
 * This module implements the correct Arxos architecture:
 * - SVG provides precise coordinate system
 * - ArxObjects provide building intelligence and real-time data
 * - Three.js renders 3D visualization from SVG + ArxObject data
 * - Result: CAD-like presentation with pinpoint accuracy
 */

class ArxosSVGArxObjectIntegration {
    constructor(options = {}) {
        this.options = {
            enablePrecisionMode: options.enablePrecisionMode !== false, // Submicron accuracy
            coordinateSystem: options.coordinateSystem || 'svg', // 'svg', 'world', 'hybrid'
            defaultUnits: options.defaultUnits || 'mm', // millimeters for precision
            ...options
        };
        
        // Core data structures
        this.svgDocument = null;
        this.arxObjects = new Map(); // ID -> ArxObject
        this.svgElements = new Map(); // ID -> SVGElement
        this.coordinateMappings = new Map(); // ArxObject ID -> SVG coordinates
        
        // Precision and scaling
        this.scaleFactors = {
            svgToWorld: 1.0, // SVG units to world units
            worldToThree: 1.0, // World units to Three.js units
            currentZoom: 1.0 // Current zoom level
        };
        
        // Coordinate transformation matrices
        this.transformMatrix = new DOMMatrix();
        this.inverseMatrix = new DOMMatrix();
        
        // Event system
        this.eventHandlers = new Map();
        
        // Performance monitoring
        this.performanceMetrics = {
            renderTime: 0,
            objectCount: 0,
            coordinateTransformations: 0
        };
        
        console.log('Arxos SVG + ArxObject Integration initialized');
    }
    
    /**
     * Load SVG-based BIM document
     * @param {string|Document} svgSource - SVG string, URL, or Document
     * @param {Object} options - Loading options
     */
    async loadSVGBIM(svgSource, options = {}) {
        try {
            console.log('Loading SVG-based BIM document...');
            
            let svgDoc;
            if (typeof svgSource === 'string') {
                if (svgSource.startsWith('http') || svgSource.startsWith('data:')) {
                    // Load from URL or data URI
                    svgDoc = await this._loadSVGFromSource(svgSource);
                } else {
                    // Parse SVG string
                    svgDoc = this._parseSVGString(svgSource);
                }
            } else if (svgSource instanceof Document) {
                svgDoc = svgSource;
            } else {
                throw new Error('Invalid SVG source type');
            }
            
            // Validate SVG structure
            this._validateSVGStructure(svgDoc);
            
            // Parse SVG elements and create ArxObject mappings
            await this._parseSVGElements(svgDoc);
            
            // Extract coordinate system information
            this._extractCoordinateSystem(svgDoc);
            
            // Set up coordinate transformations
            this._setupCoordinateTransformations();
            
            // Emit loaded event
            this._emitEvent('svgLoaded', {
                document: svgDoc,
                objectCount: this.arxObjects.size,
                coordinateSystem: this.options.coordinateSystem
            });
            
            console.log(`SVG BIM loaded successfully: ${this.arxObjects.size} ArxObjects`);
            return true;
            
        } catch (error) {
            console.error('Failed to load SVG BIM:', error);
            this._emitEvent('svgLoadError', { error: error.message });
            throw error;
        }
    }
    
    /**
     * Load ArxObjects from filesystem or API
     * @param {Array|Object} arxObjectData - ArxObject data
     */
    async loadArxObjects(arxObjectData) {
        try {
            console.log('Loading ArxObjects...');
            
            const objects = Array.isArray(arxObjectData) ? arxObjectData : [arxObjectData];
            
            for (const obj of objects) {
                await this._createArxObject(obj);
            }
            
            // Link ArxObjects to SVG elements
            await this._linkArxObjectsToSVG();
            
            // Emit loaded event
            this._emitEvent('arxObjectsLoaded', {
                count: this.arxObjects.size,
                objects: Array.from(this.arxObjects.values())
            });
            
            console.log(`${this.arxObjects.size} ArxObjects loaded and linked`);
            return true;
            
        } catch (error) {
            console.error('Failed to load ArxObjects:', error);
            this._emitEvent('arxObjectsLoadError', { error: error.message });
            throw error;
        }
    }
    
    /**
     * Get ArxObject by ID with SVG coordinate mapping
     * @param {string} id - ArxObject ID
     * @returns {Object} ArxObject with SVG coordinates
     */
    getArxObject(id) {
        const arxObject = this.arxObjects.get(id);
        if (!arxObject) return null;
        
        // Get SVG coordinate mapping
        const svgCoords = this.coordinateMappings.get(id);
        
        return {
            ...arxObject,
            svgCoordinates: svgCoords,
            worldCoordinates: this._svgToWorld(svgCoords),
            threeCoordinates: this._worldToThree(this._svgToWorld(svgCoords))
        };
    }
    
    /**
     * Get all ArxObjects with coordinate mappings
     * @returns {Array} Array of ArxObjects with coordinates
     */
    getAllArxObjects() {
        return Array.from(this.arxObjects.values()).map(obj => 
            this.getArxObject(obj.id)
        );
    }
    
    /**
     * Update ArxObject properties (real-time updates)
     * @param {string} id - ArxObject ID
     * @param {Object} updates - Property updates
     */
    updateArxObject(id, updates) {
        const arxObject = this.arxObjects.get(id);
        if (!arxObject) {
            throw new Error(`ArxObject not found: ${id}`);
        }
        
        // Update properties
        Object.assign(arxObject, updates);
        arxObject.lastUpdated = new Date();
        
        // Update SVG element if linked
        const svgElement = this.svgElements.get(id);
        if (svgElement) {
            this._updateSVGElement(svgElement, updates);
        }
        
        // Emit update event
        this._emitEvent('arxObjectUpdated', {
            id,
            updates,
            arxObject: this.getArxObject(id)
        });
        
        console.log(`ArxObject updated: ${id}`);
    }
    
    /**
     * Get coordinate transformation for specific zoom level
     * @param {number} zoomLevel - Zoom level (campus to submicron)
     * @returns {Object} Transformation matrix and scale factors
     */
    getCoordinateTransformation(zoomLevel) {
        const zoomConfig = this._getZoomConfig(zoomLevel);
        
        return {
            matrix: this.transformMatrix.scale(zoomConfig.scale, zoomConfig.scale, zoomConfig.scale),
            inverseMatrix: this.inverseMatrix.scale(1/zoomConfig.scale, 1/zoomConfig.scale, 1/zoomConfig.scale),
            scale: zoomConfig.scale,
            precision: zoomConfig.precision,
            units: zoomConfig.units
        };
    }
    
    /**
     * Transform coordinates between coordinate systems
     * @param {Array} coordinates - [x, y, z] coordinates
     * @param {string} fromSystem - Source coordinate system
     * @param {string} toSystem - Target coordinate system
     * @returns {Array} Transformed coordinates
     */
    transformCoordinates(coordinates, fromSystem, toSystem) {
        const [x, y, z] = coordinates;
        
        switch (`${fromSystem}_to_${toSystem}`) {
            case 'svg_to_world':
                return this._svgToWorld([x, y, z]);
            case 'world_to_svg':
                return this._worldToSVG([x, y, z]);
            case 'svg_to_three':
                return this._svgToThree([x, y, z]);
            case 'three_to_svg':
                return this._threeToSVG([x, y, z]);
            case 'world_to_three':
                return this._worldToThree([x, y, z]);
            case 'three_to_world':
                return this._threeToWorld([x, y, z]);
            default:
                throw new Error(`Unsupported coordinate transformation: ${fromSystem} to ${toSystem}`);
        }
    }
    
    // Private methods
    
    async _loadSVGFromSource(source) {
        const response = await fetch(source);
        const svgText = await response.text();
        return this._parseSVGString(svgText);
    }
    
    _parseSVGString(svgString) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgString, 'image/svg+xml');
        
        if (doc.documentElement.tagName !== 'svg') {
            throw new Error('Invalid SVG document');
        }
        
        return doc;
    }
    
    _validateSVGStructure(svgDoc) {
        const svgElement = svgDoc.documentElement;
        
        // Check for required attributes
        if (!svgElement.hasAttribute('viewBox') && !svgElement.hasAttribute('width') && !svgElement.hasAttribute('height')) {
            throw new Error('SVG must have viewBox, width, or height attributes');
        }
        
        // Check for building-related elements
        const buildingElements = svgDoc.querySelectorAll('[data-arxos-type], [data-building-element]');
        if (buildingElements.length === 0) {
            console.warn('No building elements found in SVG - this may be a basic SVG');
        }
    }
    
    async _parseSVGElements(svgDoc) {
        const svgElement = svgDoc.documentElement;
        
        // Get viewBox for coordinate system
        const viewBox = svgElement.getAttribute('viewBox');
        if (viewBox) {
            const [x, y, width, height] = viewBox.split(' ').map(Number);
            this.svgBounds = { x, y, width, height };
        }
        
        // Parse all elements with ArxObject data
        const elements = svgDoc.querySelectorAll('[data-arxos-id], [data-building-element]');
        
        for (const element of elements) {
            await this._parseSVGElement(element);
        }
    }
    
    async _parseSVGElement(element) {
        const arxosId = element.getAttribute('data-arxos-id');
        const buildingType = element.getAttribute('data-building-element');
        
        if (!arxosId && !buildingType) return;
        
        const id = arxosId || `element_${Date.now()}_${Math.random()}`;
        
        // Extract SVG coordinates
        const coordinates = this._extractElementCoordinates(element);
        
        // Create ArxObject mapping
        const arxObject = {
            id,
            type: buildingType || 'unknown',
            svgElement: element,
            coordinates,
            properties: this._extractElementProperties(element),
            metadata: this._extractElementMetadata(element)
        };
        
        // Store mappings
        this.svgElements.set(id, element);
        this.arxObjects.set(id, arxObject);
        this.coordinateMappings.set(id, coordinates);
        
        console.log(`Parsed SVG element: ${id} (${buildingType})`);
    }
    
    _extractElementCoordinates(element) {
        // Extract coordinates based on element type
        const tagName = element.tagName.toLowerCase();
        
        switch (tagName) {
            case 'rect':
                const x = parseFloat(element.getAttribute('x') || 0);
                const y = parseFloat(element.getAttribute('y') || 0);
                const width = parseFloat(element.getAttribute('width') || 0);
                const height = parseFloat(element.getAttribute('height') || 0);
                return { x, y, width, height, type: 'rectangle' };
                
            case 'circle':
                const cx = parseFloat(element.getAttribute('cx') || 0);
                const cy = parseFloat(element.getAttribute('cy') || 0);
                const r = parseFloat(element.getAttribute('r') || 0);
                return { x: cx, y: cy, radius: r, type: 'circle' };
                
            case 'line':
                const x1 = parseFloat(element.getAttribute('x1') || 0);
                const y1 = parseFloat(element.getAttribute('y1') || 0);
                const x2 = parseFloat(element.getAttribute('x2') || 0);
                const y2 = parseFloat(element.getAttribute('y2') || 0);
                return { x1, y1, x2, y2, type: 'line' };
                
            case 'path':
                const d = element.getAttribute('d') || '';
                return { pathData: d, type: 'path' };
                
            default:
                // Try to extract transform-based coordinates
                const transform = element.getAttribute('transform');
                if (transform) {
                    return this._parseTransformCoordinates(transform);
                }
                return { x: 0, y: 0, type: 'unknown' };
        }
    }
    
    _extractElementProperties(element) {
        const properties = {};
        
        // Extract data attributes
        for (const attr of element.attributes) {
            if (attr.name.startsWith('data-')) {
                const key = attr.name.replace('data-', '');
                properties[key] = attr.value;
            }
        }
        
        // Extract common building properties
        const commonProps = ['material', 'thickness', 'height', 'width', 'depth', 'load', 'voltage', 'flow'];
        for (const prop of commonProps) {
            const value = element.getAttribute(prop);
            if (value) {
                properties[prop] = value;
            }
        }
        
        return properties;
    }
    
    _extractElementMetadata(element) {
        return {
            tagName: element.tagName,
            className: element.className.baseVal || '',
            id: element.id || '',
            namespace: element.namespaceURI || ''
        };
    }
    
    _parseTransformCoordinates(transform) {
        // Parse SVG transform attribute
        const transforms = transform.match(/(\w+)\s*\(([^)]+)\)/g);
        const coordinates = { x: 0, y: 0, type: 'transformed' };
        
        if (transforms) {
            for (const t of transforms) {
                const [type, values] = t.match(/(\w+)\s*\(([^)]+)\)/).slice(1);
                const nums = values.split(/[,\s]+/).map(Number).filter(n => !isNaN(n));
                
                switch (type) {
                    case 'translate':
                        coordinates.x += nums[0] || 0;
                        coordinates.y += nums[1] || 0;
                        break;
                    case 'scale':
                        coordinates.scaleX = nums[0] || 1;
                        coordinates.scaleY = nums[1] || nums[0] || 1;
                        break;
                    case 'rotate':
                        coordinates.rotation = nums[0] || 0;
                        break;
                }
            }
        }
        
        return coordinates;
    }
    
    _extractCoordinateSystem(svgDoc) {
        const svgElement = svgDoc.documentElement;
        
        // Extract units
        const units = svgElement.getAttribute('data-units') || 'mm';
        this.options.defaultUnits = units;
        
        // Extract scale information
        const scale = svgElement.getAttribute('data-scale') || '1:1';
        this._parseScale(scale);
        
        // Extract coordinate system type
        const coordSystem = svgElement.getAttribute('data-coordinate-system') || 'cartesian';
        this.options.coordinateSystem = coordSystem;
        
        console.log(`Coordinate system: ${coordSystem}, Units: ${units}, Scale: ${scale}`);
    }
    
    _parseScale(scaleString) {
        const match = scaleString.match(/(\d+):(\d+)/);
        if (match) {
            const [, numerator, denominator] = match;
            this.scaleFactors.svgToWorld = parseFloat(numerator) / parseFloat(denominator);
        } else {
            this.scaleFactors.svgToWorld = 1.0;
        }
    }
    
    _setupCoordinateTransformations() {
        // Set up transformation matrices for coordinate conversions
        this.transformMatrix = new DOMMatrix();
        this.inverseMatrix = this.transformMatrix.inverse();
        
        // Apply scale factors
        this.transformMatrix = this.transformMatrix.scale(
            this.scaleFactors.svgToWorld,
            this.scaleFactors.svgToWorld,
            1
        );
        
        this.inverseMatrix = this.transformMatrix.inverse();
    }
    
    async _linkArxObjectsToSVG() {
        // Link ArxObjects to their corresponding SVG elements
        for (const [id, arxObject] of this.arxObjects) {
            const svgElement = this.svgElements.get(id);
            if (svgElement) {
                arxObject.svgElement = svgElement;
                arxObject.svgId = id;
                
                // Set up event listeners for SVG element changes
                this._setupSVGElementListeners(svgElement, arxObject);
            }
        }
    }
    
    _setupSVGElementListeners(svgElement, arxObject) {
        // Monitor SVG element changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes') {
                    this._handleSVGElementChange(arxObject, mutation);
                }
            });
        });
        
        observer.observe(svgElement, {
            attributes: true,
            attributeFilter: ['transform', 'd', 'x', 'y', 'width', 'height']
        });
        
        // Store observer for cleanup
        arxObject.svgObserver = observer;
    }
    
    _handleSVGElementChange(arxObject, mutation) {
        // Update ArxObject when SVG element changes
        const newCoordinates = this._extractElementCoordinates(arxObject.svgElement);
        arxObject.coordinates = newCoordinates;
        this.coordinateMappings.set(arxObject.id, newCoordinates);
        
        // Emit change event
        this._emitEvent('svgElementChanged', {
            arxObjectId: arxObject.id,
            attribute: mutation.attributeName,
            newValue: mutation.target.getAttribute(mutation.attributeName),
            coordinates: newCoordinates
        });
    }
    
    _updateSVGElement(svgElement, updates) {
        // Update SVG element based on ArxObject changes
        if (updates.coordinates) {
            const coords = updates.coordinates;
            
            switch (coords.type) {
                case 'rectangle':
                    if (coords.x !== undefined) svgElement.setAttribute('x', coords.x);
                    if (coords.y !== undefined) svgElement.setAttribute('y', coords.y);
                    if (coords.width !== undefined) svgElement.setAttribute('width', coords.width);
                    if (coords.height !== undefined) svgElement.setAttribute('height', coords.height);
                    break;
                    
                case 'circle':
                    if (coords.x !== undefined) svgElement.setAttribute('cx', coords.x);
                    if (coords.y !== undefined) svgElement.setAttribute('cy', coords.y);
                    if (coords.radius !== undefined) svgElement.setAttribute('r', coords.radius);
                    break;
                    
                case 'line':
                    if (coords.x1 !== undefined) svgElement.setAttribute('x1', coords.x1);
                    if (coords.y1 !== undefined) svgElement.setAttribute('y1', coords.y1);
                    if (coords.x2 !== undefined) svgElement.setAttribute('x2', coords.x2);
                    if (coords.y2 !== undefined) svgElement.setAttribute('y2', coords.y2);
                    break;
            }
        }
        
        // Update other properties
        if (updates.properties) {
            for (const [key, value] of Object.entries(updates.properties)) {
                svgElement.setAttribute(`data-${key}`, value);
            }
        }
    }
    
    _getZoomConfig(zoomLevel) {
        // Define zoom configurations from campus to submicron
        const zoomConfigs = {
            'campus': { scale: 0.001, precision: 'meter', units: 'm' },
            'building': { scale: 0.01, precision: 'decimeter', units: 'dm' },
            'floor': { scale: 0.1, precision: 'centimeter', units: 'cm' },
            'room': { scale: 1.0, precision: 'millimeter', units: 'mm' },
            'equipment': { scale: 10.0, precision: 'submillimeter', units: '0.1mm' },
            'component': { scale: 100.0, precision: 'micrometer', units: 'μm' },
            'submicron': { scale: 1000.0, precision: 'nanometer', units: 'nm' }
        };
        
        return zoomConfigs[zoomLevel] || zoomConfigs.room;
    }
    
    // Coordinate transformation methods
    
    _svgToWorld(svgCoords) {
        if (!svgCoords) return [0, 0, 0];
        
        const x = (svgCoords.x || svgCoords.x1 || 0) * this.scaleFactors.svgToWorld;
        const y = (svgCoords.y || svgCoords.y1 || 0) * this.scaleFactors.svgToWorld;
        const z = svgCoords.z || 0;
        
        return [x, y, z];
    }
    
    _worldToSVG(worldCoords) {
        if (!worldCoords) return [0, 0, 0];
        
        const x = (worldCoords[0] || 0) / this.scaleFactors.svgToWorld;
        const y = (worldCoords[1] || 0) / this.scaleFactors.svgToWorld;
        const z = worldCoords[2] || 0;
        
        return [x, y, z];
    }
    
    _svgToThree(svgCoords) {
        const worldCoords = this._svgToWorld(svgCoords);
        return this._worldToThree(worldCoords);
    }
    
    _threeToSVG(threeCoords) {
        const worldCoords = this._threeToWorld(threeCoords);
        return this._worldToSVG(worldCoords);
    }
    
    _worldToThree(worldCoords) {
        if (!worldCoords) return [0, 0, 0];
        
        const x = (worldCoords[0] || 0) * this.scaleFactors.worldToThree;
        const y = (worldCoords[1] || 0) * this.scaleFactors.worldToThree;
        const z = (worldCoords[2] || 0) * this.scaleFactors.worldToThree;
        
        return [x, y, z];
    }
    
    _threeToWorld(threeCoords) {
        if (!threeCoords) return [0, 0, 0];
        
        const x = (threeCoords[0] || 0) / this.scaleFactors.worldToThree;
        const y = (threeCoords[1] || 0) / this.scaleFactors.worldToThree;
        const z = (threeCoords[2] || 0) / this.scaleFactors.worldToThree;
        
        return [x, y, z];
    }
    
    // Event system
    
    on(eventName, handler) {
        if (!this.eventHandlers.has(eventName)) {
            this.eventHandlers.set(eventName, []);
        }
        this.eventHandlers.get(eventName).push(handler);
    }
    
    off(eventName, handler) {
        if (this.eventHandlers.has(eventName)) {
            const handlers = this.eventHandlers.get(eventName);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    _emitEvent(eventName, data) {
        if (this.eventHandlers.has(eventName)) {
            this.eventHandlers.get(eventName).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${eventName}:`, error);
                }
            });
        }
    }
    
    // Utility methods
    
    getPerformanceMetrics() {
        return { ...this.performanceMetrics };
    }
    
    getCoordinateSystemInfo() {
        return {
            system: this.options.coordinateSystem,
            units: this.options.defaultUnits,
            scaleFactors: { ...this.scaleFactors },
            bounds: this.svgBounds
        };
    }
    
    // Cleanup
    
    destroy() {
        // Clean up SVG element observers
        for (const arxObject of this.arxObjects.values()) {
            if (arxObject.svgObserver) {
                arxObject.svgObserver.disconnect();
            }
        }
        
        // Clear data structures
        this.svgDocument = null;
        this.arxObjects.clear();
        this.svgElements.clear();
        this.coordinateMappings.clear();
        this.eventHandlers.clear();
        
        console.log('Arxos SVG + ArxObject Integration destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxosSVGArxObjectIntegration;
}
