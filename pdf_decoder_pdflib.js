/**
 * PDF Decoder using pdf-lib - Alternative approach
 * pdf-lib provides lower-level access to PDF structure
 */

class PDFDecoderPdfLib {
    constructor() {
        this.PDFLib = null;
    }

    async initialize() {
        if (!this.PDFLib) {
            // Load pdf-lib from CDN
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js';
            document.head.appendChild(script);
            await new Promise(resolve => script.onload = resolve);
            this.PDFLib = window.PDFLib;
        }
    }

    async decodePDF(file) {
        console.log('🔍 Starting PDF decoding with pdf-lib...');
        
        await this.initialize();
        
        const arrayBuffer = await this.readFileAsArrayBuffer(file);
        const pdfDoc = await this.PDFLib.PDFDocument.load(arrayBuffer);
        
        const pages = pdfDoc.getPages();
        const firstPage = pages[0];
        
        const { width, height } = firstPage.getSize();
        console.log(`📐 Page size: ${width}x${height} points`);
        
        // Get the page's content stream
        const walls = await this.extractWallsFromPage(firstPage);
        
        return {
            walls: walls,
            rooms: [],
            confidence: walls.length > 0 ? 0.9 : 0
        };
    }

    async extractWallsFromPage(page) {
        const walls = [];
        
        try {
            // Get page node (low-level access)
            const pageNode = page.node;
            
            // Get content streams
            const contents = pageNode.Contents();
            if (!contents) {
                console.log('No content streams found');
                return walls;
            }

            // Parse content stream
            const contentStream = contents.asArray ? contents.asArray() : [contents];
            
            for (const stream of contentStream) {
                if (stream) {
                    const streamData = stream.getStreamData();
                    console.log('Stream data length:', streamData.length);
                    
                    // Parse the stream to find drawing commands
                    const commands = this.parseContentStream(streamData);
                    const streamWalls = this.extractWallsFromCommands(commands, page.getSize());
                    walls.push(...streamWalls);
                }
            }
        } catch (error) {
            console.error('Error extracting walls:', error);
            
            // Fallback: Try to get operations directly
            console.log('Trying fallback method...');
            walls.push(...this.fallbackExtraction(page));
        }
        
        console.log(`✅ Extracted ${walls.length} walls`);
        return walls;
    }

    parseContentStream(streamData) {
        // Convert stream data to string
        const decoder = new TextDecoder('utf-8');
        const streamText = decoder.decode(streamData);
        
        console.log('First 500 chars of stream:', streamText.substring(0, 500));
        
        // Parse PDF commands (simplified parser)
        const commands = [];
        const lines = streamText.split(/[\r\n]+/);
        
        let currentPath = [];
        let currentX = 0, currentY = 0;
        
        for (const line of lines) {
            const tokens = line.trim().split(/\s+/);
            if (tokens.length === 0) continue;
            
            const operator = tokens[tokens.length - 1];
            const operands = tokens.slice(0, -1).map(t => parseFloat(t));
            
            // Handle common PDF operators
            switch (operator) {
                case 'm': // moveto
                    if (operands.length >= 2) {
                        currentX = operands[0];
                        currentY = operands[1];
                        currentPath = [{ type: 'move', x: currentX, y: currentY }];
                    }
                    break;
                    
                case 'l': // lineto
                    if (operands.length >= 2 && currentPath.length > 0) {
                        const endX = operands[0];
                        const endY = operands[1];
                        commands.push({
                            type: 'line',
                            startX: currentX,
                            startY: currentY,
                            endX: endX,
                            endY: endY
                        });
                        currentX = endX;
                        currentY = endY;
                    }
                    break;
                    
                case 're': // rectangle
                    if (operands.length >= 4) {
                        const x = operands[0];
                        const y = operands[1];
                        const w = operands[2];
                        const h = operands[3];
                        
                        // Add rectangle as 4 lines
                        commands.push(
                            { type: 'line', startX: x, startY: y, endX: x + w, endY: y },
                            { type: 'line', startX: x + w, startY: y, endX: x + w, endY: y + h },
                            { type: 'line', startX: x + w, startY: y + h, endX: x, endY: y + h },
                            { type: 'line', startX: x, startY: y + h, endX: x, endY: y }
                        );
                    }
                    break;
                    
                case 'h': // closepath
                    currentPath = [];
                    break;
                    
                case 'S': // stroke
                case 's': // close and stroke
                case 'f': // fill
                case 'F': // fill (alternate)
                case 'f*': // fill even-odd
                case 'B': // fill and stroke
                case 'B*': // fill even-odd and stroke
                case 'b': // close, fill and stroke
                case 'b*': // close, fill even-odd and stroke
                    // These indicate the path should be drawn
                    break;
            }
        }
        
        console.log(`Parsed ${commands.length} drawing commands`);
        return commands;
    }

    extractWallsFromCommands(commands, pageSize) {
        const walls = [];
        const { width: pageWidth, height: pageHeight } = pageSize;
        
        // Canvas size (assuming 2x scale like before)
        const scale = 2;
        const canvasWidth = pageWidth * scale;
        const canvasHeight = pageHeight * scale;
        
        for (const cmd of commands) {
            if (cmd.type === 'line') {
                // Transform coordinates from PDF space to canvas space
                // PDF coordinates start at bottom-left, canvas at top-left
                const wall = {
                    startX: cmd.startX * scale,
                    startY: (pageHeight - cmd.startY) * scale, // Flip Y coordinate
                    endX: cmd.endX * scale,
                    endY: (pageHeight - cmd.endY) * scale, // Flip Y coordinate
                    confidence: 0.9,
                    source: 'pdflib'
                };
                
                // Only add lines that are long enough
                const length = Math.sqrt(
                    Math.pow(wall.endX - wall.startX, 2) + 
                    Math.pow(wall.endY - wall.startY, 2)
                );
                
                if (length > 5) {
                    walls.push(wall);
                }
            }
        }
        
        return walls;
    }

    fallbackExtraction(page) {
        // Simple fallback - create boundary walls
        const { width, height } = page.getSize();
        const scale = 2;
        
        return [
            { startX: 0, startY: 0, endX: width * scale, endY: 0, confidence: 0.5, source: 'boundary' },
            { startX: width * scale, startY: 0, endX: width * scale, endY: height * scale, confidence: 0.5, source: 'boundary' },
            { startX: width * scale, startY: height * scale, endX: 0, endY: height * scale, confidence: 0.5, source: 'boundary' },
            { startX: 0, startY: height * scale, endX: 0, endY: 0, confidence: 0.5, source: 'boundary' }
        ];
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
    module.exports = PDFDecoderPdfLib;
}