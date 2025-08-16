/**
 * AI Vision-based PDF Extractor
 * Uses GPT-4V or Claude Vision to extract floor plans with high accuracy
 * Cost-optimized with user approval for large batches
 */

class PDFAIExtractor {
    constructor(apiKey, provider = 'openai') {
        this.apiKey = apiKey;
        this.provider = provider;
        this.costPerImage = provider === 'openai' ? 0.01 : 0.003; // Approximate costs
    }

    async extractFromPDF(file, options = {}) {
        const {
            requireApproval = true,
            maxCost = 1.00,
            pages = 'all'
        } = options;

        console.log('🤖 Starting AI vision extraction...');
        
        // Convert PDF to images
        const images = await this.pdfToImages(file, pages);
        const estimatedCost = images.length * this.costPerImage;
        
        // Check cost and get approval if needed
        if (requireApproval && estimatedCost > maxCost) {
            const approved = await this.requestApproval(estimatedCost, images.length);
            if (!approved) {
                throw new Error('Extraction cancelled - cost not approved');
            }
        }

        // Process each page
        const results = [];
        for (let i = 0; i < images.length; i++) {
            console.log(`Processing page ${i + 1}/${images.length}...`);
            const pageResult = await this.extractFromImage(images[i], i + 1);
            results.push(pageResult);
        }

        // Combine results
        return this.combineResults(results);
    }

    async pdfToImages(file, pages = 'all') {
        // Initialize PDF.js
        if (!window.pdfjsLib) {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            document.head.appendChild(script);
            await new Promise(resolve => script.onload = resolve);
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }

        const arrayBuffer = await this.readFileAsArrayBuffer(file);
        const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
        
        const images = [];
        const pagesToProcess = pages === 'all' 
            ? Array.from({length: pdf.numPages}, (_, i) => i + 1)
            : Array.isArray(pages) ? pages : [pages];

        for (const pageNum of pagesToProcess) {
            const page = await pdf.getPage(pageNum);
            const viewport = page.getViewport({ scale: 2.0 });
            
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            
            await page.render({
                canvasContext: ctx,
                viewport: viewport
            }).promise;
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/png');
            images.push(imageData);
        }

        return images;
    }

    async extractFromImage(imageData, pageNumber) {
        const prompt = `Analyze this floor plan image and extract the following in JSON format:

1. Rooms: List each room with:
   - ID (unique identifier)
   - Type (classroom, hallway, office, bathroom, storage, etc.)
   - Approximate boundaries (as percentage of image width/height)
   - Any visible room numbers or labels

2. Walls: List major walls with:
   - Start point (x%, y%)
   - End point (x%, y%)
   - Type (exterior, interior, partition)

3. Doors: List visible doors with:
   - Location (x%, y%)
   - Connects (which rooms)

4. Key features:
   - Windows
   - Stairs
   - Elevators
   - Emergency exits

Return ONLY valid JSON with this structure:
{
  "rooms": [...],
  "walls": [...],
  "doors": [...],
  "features": {...},
  "confidence": 0.0-1.0
}`;

        if (this.provider === 'openai') {
            return await this.callOpenAI(imageData, prompt);
        } else if (this.provider === 'anthropic') {
            return await this.callAnthropic(imageData, prompt);
        } else {
            throw new Error(`Unsupported provider: ${this.provider}`);
        }
    }

    async callOpenAI(imageData, prompt) {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                model: 'gpt-4-vision-preview',
                messages: [
                    {
                        role: 'user',
                        content: [
                            { type: 'text', text: prompt },
                            { type: 'image_url', image_url: { url: imageData } }
                        ]
                    }
                ],
                max_tokens: 4096
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(`OpenAI API error: ${data.error?.message || 'Unknown error'}`);
        }

        try {
            const content = data.choices[0].message.content;
            // Extract JSON from the response
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
            throw new Error('No valid JSON in response');
        } catch (e) {
            console.error('Failed to parse AI response:', e);
            throw new Error('Invalid response format from AI');
        }
    }

    async callAnthropic(imageData, prompt) {
        // Convert base64 to just the data part
        const base64Data = imageData.split(',')[1];
        
        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': this.apiKey,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: 'claude-3-opus-20240229',
                max_tokens: 4096,
                messages: [
                    {
                        role: 'user',
                        content: [
                            { type: 'text', text: prompt },
                            { 
                                type: 'image', 
                                source: {
                                    type: 'base64',
                                    media_type: 'image/png',
                                    data: base64Data
                                }
                            }
                        ]
                    }
                ]
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(`Anthropic API error: ${data.error?.message || 'Unknown error'}`);
        }

        try {
            const content = data.content[0].text;
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
            throw new Error('No valid JSON in response');
        } catch (e) {
            console.error('Failed to parse AI response:', e);
            throw new Error('Invalid response format from AI');
        }
    }

    async requestApproval(cost, pageCount) {
        return new Promise((resolve) => {
            const message = `AI extraction will process ${pageCount} page(s) for approximately $${cost.toFixed(2)}. Proceed?`;
            
            // In production, use a proper modal/dialog
            if (typeof window !== 'undefined' && window.confirm) {
                resolve(window.confirm(message));
            } else {
                console.log(message);
                resolve(true); // Auto-approve in non-browser environment
            }
        });
    }

    combineResults(results) {
        const combined = {
            rooms: [],
            walls: [],
            doors: [],
            features: {},
            pages: results.length,
            confidence: 0
        };

        let totalConfidence = 0;

        results.forEach((result, pageIndex) => {
            // Add page prefix to IDs to avoid conflicts
            const pagePrefix = `p${pageIndex + 1}_`;
            
            if (result.rooms) {
                result.rooms.forEach(room => {
                    combined.rooms.push({
                        ...room,
                        id: pagePrefix + room.id,
                        page: pageIndex + 1
                    });
                });
            }

            if (result.walls) {
                result.walls.forEach(wall => {
                    combined.walls.push({
                        ...wall,
                        page: pageIndex + 1
                    });
                });
            }

            if (result.doors) {
                result.doors.forEach(door => {
                    combined.doors.push({
                        ...door,
                        page: pageIndex + 1
                    });
                });
            }

            if (result.features) {
                combined.features[`page_${pageIndex + 1}`] = result.features;
            }

            totalConfidence += result.confidence || 0;
        });

        combined.confidence = totalConfidence / results.length;

        return combined;
    }

    convertToPixels(percentageData, imageWidth, imageHeight) {
        // Convert percentage-based coordinates to pixels
        const converted = {
            rooms: [],
            walls: [],
            doors: []
        };

        if (percentageData.rooms) {
            percentageData.rooms.forEach(room => {
                // Convert room boundaries from percentages to pixels
                const pixelRoom = {
                    ...room,
                    bounds: {
                        minX: (room.boundaries?.left || 0) * imageWidth / 100,
                        minY: (room.boundaries?.top || 0) * imageHeight / 100,
                        maxX: (room.boundaries?.right || 100) * imageWidth / 100,
                        maxY: (room.boundaries?.bottom || 100) * imageHeight / 100
                    }
                };
                converted.rooms.push(pixelRoom);
            });
        }

        if (percentageData.walls) {
            percentageData.walls.forEach(wall => {
                converted.walls.push({
                    ...wall,
                    startX: (wall.start?.x || wall.startX || 0) * imageWidth / 100,
                    startY: (wall.start?.y || wall.startY || 0) * imageHeight / 100,
                    endX: (wall.end?.x || wall.endX || 0) * imageWidth / 100,
                    endY: (wall.end?.y || wall.endY || 0) * imageHeight / 100
                });
            });
        }

        if (percentageData.doors) {
            percentageData.doors.forEach(door => {
                converted.doors.push({
                    ...door,
                    x: (door.location?.x || door.x || 0) * imageWidth / 100,
                    y: (door.location?.y || door.y || 0) * imageHeight / 100
                });
            });
        }

        return converted;
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
    module.exports = PDFAIExtractor;
}