/**
 * Formats Module
 * Handles different file formats, format conversion, and format validation
 */

export class Formats {
    constructor(options = {}) {
        this.options = {
            supportedFormats: ['json', 'svg', 'zip', 'png', 'pdf'],
            compressionEnabled: true,
            formatValidation: true,
            ...options
        };
        
        // Format handlers
        this.formatHandlers = new Map();
        this.converters = new Map();
        
        this.initialize();
    }

    initialize() {
        this.registerFormatHandlers();
        this.registerConverters();
    }

    registerFormatHandlers() {
        // JSON format handler
        this.formatHandlers.set('json', {
            mimeType: 'application/json',
            extensions: ['.json'],
            validate: (data) => this.validateJSON(data),
            parse: (content) => this.parseJSON(content),
            stringify: (data) => this.stringifyJSON(data)
        });
        
        // SVG format handler
        this.formatHandlers.set('svg', {
            mimeType: 'image/svg+xml',
            extensions: ['.svg'],
            validate: (data) => this.validateSVG(data),
            parse: (content) => this.parseSVG(content),
            stringify: (data) => this.stringifySVG(data)
        });
        
        // ZIP format handler
        this.formatHandlers.set('zip', {
            mimeType: 'application/zip',
            extensions: ['.zip'],
            validate: (data) => this.validateZIP(data),
            parse: (content) => this.parseZIP(content),
            stringify: (data) => this.stringifyZIP(data)
        });
        
        // PNG format handler
        this.formatHandlers.set('png', {
            mimeType: 'image/png',
            extensions: ['.png'],
            validate: (data) => this.validatePNG(data),
            parse: (content) => this.parsePNG(content),
            stringify: (data) => this.stringifyPNG(data)
        });
        
        // PDF format handler
        this.formatHandlers.set('pdf', {
            mimeType: 'application/pdf',
            extensions: ['.pdf'],
            validate: (data) => this.validatePDF(data),
            parse: (content) => this.parsePDF(content),
            stringify: (data) => this.stringifyPDF(data)
        });
    }

    registerConverters() {
        // SVG to PNG converter
        this.converters.set('svg-to-png', {
            from: 'svg',
            to: 'png',
            convert: (svgData, options) => this.convertSVGToPNG(svgData, options)
        });
        
        // SVG to PDF converter
        this.converters.set('svg-to-pdf', {
            from: 'svg',
            to: 'pdf',
            convert: (svgData, options) => this.convertSVGToPDF(svgData, options)
        });
        
        // JSON to SVG converter
        this.converters.set('json-to-svg', {
            from: 'json',
            to: 'svg',
            convert: (jsonData, options) => this.convertJSONToSVG(jsonData, options)
        });
        
        // SVG to JSON converter
        this.converters.set('svg-to-json', {
            from: 'svg',
            to: 'json',
            convert: (svgData, options) => this.convertSVGToJSON(svgData, options)
        });
    }

    // Format detection
    detectFormat(file) {
        const fileName = file.name.toLowerCase();
        const extension = fileName.substring(fileName.lastIndexOf('.'));
        
        for (const [format, handler] of this.formatHandlers) {
            if (handler.extensions.includes(extension)) {
                return format;
            }
        }
        
        // Fallback to MIME type detection
        return this.detectFormatByMimeType(file.type);
    }

    detectFormatByMimeType(mimeType) {
        for (const [format, handler] of this.formatHandlers) {
            if (handler.mimeType === mimeType) {
                return format;
            }
        }
        
        return null;
    }

    // Format validation
    validateFormat(format, data) {
        const handler = this.formatHandlers.get(format);
        if (!handler) {
            throw new Error(`Unsupported format: ${format}`);
        }
        
        if (this.options.formatValidation) {
            return handler.validate(data);
        }
        
        return true;
    }

    // JSON format methods
    validateJSON(data) {
        try {
            if (typeof data === 'string') {
                JSON.parse(data);
            } else if (typeof data === 'object') {
                JSON.stringify(data);
            } else {
                throw new Error('Invalid JSON data type');
            }
            return true;
        } catch (error) {
            throw new Error(`JSON validation failed: ${error.message}`);
        }
    }

    parseJSON(content) {
        try {
            return JSON.parse(content);
        } catch (error) {
            throw new Error(`JSON parsing failed: ${error.message}`);
        }
    }

    stringifyJSON(data) {
        try {
            return JSON.stringify(data, null, 2);
        } catch (error) {
            throw new Error(`JSON stringification failed: ${error.message}`);
        }
    }

    // SVG format methods
    validateSVG(data) {
        try {
            if (typeof data === 'string') {
                // Basic SVG validation
                if (!data.includes('<svg') || !data.includes('</svg>')) {
                    throw new Error('Invalid SVG structure');
                }
                
                // Parse SVG to check for errors
                const parser = new DOMParser();
                const doc = parser.parseFromString(data, 'image/svg+xml');
                
                if (doc.querySelector('parsererror')) {
                    throw new Error('SVG parsing error');
                }
            } else {
                throw new Error('SVG data must be a string');
            }
            return true;
        } catch (error) {
            throw new Error(`SVG validation failed: ${error.message}`);
        }
    }

    parseSVG(content) {
        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(content, 'image/svg+xml');
            
            if (doc.querySelector('parsererror')) {
                throw new Error('SVG parsing error');
            }
            
            return doc;
        } catch (error) {
            throw new Error(`SVG parsing failed: ${error.message}`);
        }
    }

    stringifySVG(data) {
        try {
            if (data instanceof Document) {
                return new XMLSerializer().serializeToString(data);
            } else if (typeof data === 'string') {
                return data;
            } else {
                throw new Error('Invalid SVG data type');
            }
        } catch (error) {
            throw new Error(`SVG stringification failed: ${error.message}`);
        }
    }

    // ZIP format methods
    validateZIP(data) {
        try {
            // Basic ZIP validation (check for ZIP header)
            if (data instanceof ArrayBuffer) {
                const view = new Uint8Array(data);
                if (view.length < 4 || view[0] !== 0x50 || view[1] !== 0x4B) {
                    throw new Error('Invalid ZIP header');
                }
            } else {
                throw new Error('ZIP data must be an ArrayBuffer');
            }
            return true;
        } catch (error) {
            throw new Error(`ZIP validation failed: ${error.message}`);
        }
    }

    parseZIP(content) {
        // ZIP parsing would require a ZIP library
        // For now, return the raw content
        return content;
    }

    stringifyZIP(data) {
        // ZIP creation would require a ZIP library
        // For now, return the raw data
        return data;
    }

    // PNG format methods
    validatePNG(data) {
        try {
            if (data instanceof ArrayBuffer) {
                const view = new Uint8Array(data);
                if (view.length < 8 || 
                    view[0] !== 0x89 || view[1] !== 0x50 || 
                    view[2] !== 0x4E || view[3] !== 0x47) {
                    throw new Error('Invalid PNG header');
                }
            } else {
                throw new Error('PNG data must be an ArrayBuffer');
            }
            return true;
        } catch (error) {
            throw new Error(`PNG validation failed: ${error.message}`);
        }
    }

    parsePNG(content) {
        // PNG parsing would require canvas or image processing
        return content;
    }

    stringifyPNG(data) {
        // PNG creation would require canvas
        return data;
    }

    // PDF format methods
    validatePDF(data) {
        try {
            if (data instanceof ArrayBuffer) {
                const view = new Uint8Array(data);
                if (view.length < 4 || 
                    view[0] !== 0x25 || view[1] !== 0x50 || 
                    view[2] !== 0x44 || view[3] !== 0x46) {
                    throw new Error('Invalid PDF header');
                }
            } else {
                throw new Error('PDF data must be an ArrayBuffer');
            }
            return true;
        } catch (error) {
            throw new Error(`PDF validation failed: ${error.message}`);
        }
    }

    parsePDF(content) {
        // PDF parsing would require a PDF library
        return content;
    }

    stringifyPDF(data) {
        // PDF creation would require a PDF library
        return data;
    }

    // Format conversion methods
    async convertFormat(fromFormat, toFormat, data, options = {}) {
        const converterKey = `${fromFormat}-to-${toFormat}`;
        const converter = this.converters.get(converterKey);
        
        if (!converter) {
            throw new Error(`No converter available for ${fromFormat} to ${toFormat}`);
        }
        
        return await converter.convert(data, options);
    }

    // SVG to PNG conversion
    async convertSVGToPNG(svgData, options = {}) {
        const { width = 800, height = 600, backgroundColor = 'white' } = options;
        
        return new Promise((resolve, reject) => {
            try {
                // Create canvas
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                canvas.width = width;
                canvas.height = height;
                
                // Set background
                ctx.fillStyle = backgroundColor;
                ctx.fillRect(0, 0, width, height);
                
                // Create image from SVG
                const img = new Image();
                const svgBlob = new Blob([svgData], { type: 'image/svg+xml' });
                const url = URL.createObjectURL(svgBlob);
                
                img.onload = () => {
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    // Convert to PNG
                    canvas.toBlob((blob) => {
                        URL.revokeObjectURL(url);
                        resolve(blob);
                    }, 'image/png');
                };
                
                img.onerror = () => {
                    URL.revokeObjectURL(url);
                    reject(new Error('Failed to load SVG image'));
                };
                
                img.src = url;
            } catch (error) {
                reject(error);
            }
        });
    }

    // SVG to PDF conversion
    async convertSVGToPDF(svgData, options = {}) {
        const { width = 800, height = 600 } = options;
        
        // This would require a PDF library like jsPDF
        // For now, return a placeholder
        throw new Error('PDF conversion requires additional libraries');
    }

    // JSON to SVG conversion
    async convertJSONToSVG(jsonData, options = {}) {
        const { width = 800, height = 600, style = 'default' } = options;
        
        try {
            // Extract objects from JSON
            const objects = jsonData.objects || [];
            
            // Create SVG document
            let svgContent = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
            
            // Add style if specified
            if (style !== 'default') {
                svgContent += `<style>${this.getStyleForType(style)}</style>`;
            }
            
            // Convert objects to SVG elements
            objects.forEach(obj => {
                svgContent += this.convertObjectToSVG(obj);
            });
            
            svgContent += '</svg>';
            
            return svgContent;
        } catch (error) {
            throw new Error(`JSON to SVG conversion failed: ${error.message}`);
        }
    }

    // SVG to JSON conversion
    async convertSVGToJSON(svgData, options = {}) {
        try {
            // Parse SVG
            const svgDoc = this.parseSVG(svgData);
            const svgElement = svgDoc.querySelector('svg');
            
            if (!svgElement) {
                throw new Error('No SVG element found');
            }
            
            // Extract objects
            const objects = [];
            const elements = svgElement.querySelectorAll('rect, circle, ellipse, line, polyline, polygon, path, text');
            
            elements.forEach((element, index) => {
                objects.push({
                    id: element.id || `object-${index}`,
                    type: element.tagName.toLowerCase(),
                    attributes: this.extractElementAttributes(element),
                    content: element.outerHTML
                });
            });
            
            // Create JSON structure
            const jsonData = {
                version: '1.0',
                objects: objects,
                metadata: {
                    width: svgElement.getAttribute('width'),
                    height: svgElement.getAttribute('height'),
                    timestamp: new Date().toISOString()
                }
            };
            
            return jsonData;
        } catch (error) {
            throw new Error(`SVG to JSON conversion failed: ${error.message}`);
        }
    }

    // Helper methods
    extractElementAttributes(element) {
        const attributes = {};
        
        for (let attr of element.attributes) {
            attributes[attr.name] = attr.value;
        }
        
        return attributes;
    }

    convertObjectToSVG(obj) {
        const { type, attributes, content } = obj;
        
        if (content) {
            return content;
        }
        
        // Create SVG element based on type
        let element = `<${type}`;
        
        // Add attributes
        if (attributes) {
            for (const [key, value] of Object.entries(attributes)) {
                element += ` ${key}="${value}"`;
            }
        }
        
        element += '/>';
        
        return element;
    }

    getStyleForType(styleType) {
        const styles = {
            default: `
                rect { fill: #ccc; stroke: #333; stroke-width: 1; }
                circle { fill: #f0f0f0; stroke: #333; stroke-width: 1; }
                path { fill: none; stroke: #333; stroke-width: 2; }
                text { font-family: Arial, sans-serif; font-size: 12px; fill: #333; }
            `,
            modern: `
                rect { fill: #4a90e2; stroke: #2171c1; stroke-width: 2; }
                circle { fill: #f39c12; stroke: #e67e22; stroke-width: 2; }
                path { fill: none; stroke: #27ae60; stroke-width: 3; }
                text { font-family: 'Segoe UI', sans-serif; font-size: 14px; fill: #2c3e50; }
            `,
            minimal: `
                rect { fill: #fff; stroke: #000; stroke-width: 1; }
                circle { fill: #fff; stroke: #000; stroke-width: 1; }
                path { fill: none; stroke: #000; stroke-width: 1; }
                text { font-family: monospace; font-size: 10px; fill: #000; }
            `
        };
        
        return styles[styleType] || styles.default;
    }

    // Format utilities
    getSupportedFormats() {
        return Array.from(this.formatHandlers.keys());
    }

    isFormatSupported(format) {
        return this.formatHandlers.has(format);
    }

    getFormatHandler(format) {
        return this.formatHandlers.get(format);
    }

    getMimeType(format) {
        const handler = this.formatHandlers.get(format);
        return handler ? handler.mimeType : null;
    }

    getExtensions(format) {
        const handler = this.formatHandlers.get(format);
        return handler ? handler.extensions : [];
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers) {
            this.eventHandlers = new Map();
        }
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers && this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers && this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, formats: this });
                } catch (error) {
                    console.error(`Error in formats event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.formatHandlers.clear();
        this.converters.clear();
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 