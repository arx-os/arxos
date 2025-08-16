/**
 * Debug version of PDF Decoder to understand coordinate issues
 */

class PDFDecoderDebug {
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

    async debugPDF(file) {
        console.log('🔍 DEBUG: Starting PDF analysis...');
        
        if (!this.pdfjsLib) {
            await this.initialize();
        }

        const arrayBuffer = await this.readFileAsArrayBuffer(file);
        const pdf = await this.pdfjsLib.getDocument(arrayBuffer).promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 1.0 });
        
        console.log('📐 Viewport:', viewport.width, 'x', viewport.height);
        console.log('📐 ViewBox:', viewport.viewBox);
        
        const ops = await page.getOperatorList();
        
        // Analyze operations
        const analysis = {
            totalOps: ops.fnArray.length,
            transforms: [],
            constructPaths: [],
            standardPaths: [],
            currentTransform: [1, 0, 0, 1, 0, 0],
            transformStack: []
        };
        
        // Count operation types
        const opCounts = {};
        
        for (let i = 0; i < ops.fnArray.length; i++) {
            const opCode = ops.fnArray[i];
            const args = ops.argsArray[i] || [];
            
            // Count operations
            opCounts[opCode] = (opCounts[opCode] || 0) + 1;
            
            // Track transforms
            if (opCode === 7) { // transform
                analysis.transforms.push({
                    index: i,
                    matrix: args,
                    current: [...analysis.currentTransform]
                });
                // Update current transform
                this.multiplyTransform(analysis.currentTransform, args);
                console.log(`Transform at ${i}:`, args, '-> Current:', analysis.currentTransform);
            }
            
            // Track save/restore
            if (opCode === 5) { // save
                analysis.transformStack.push([...analysis.currentTransform]);
                console.log(`Save at ${i}, stack depth: ${analysis.transformStack.length}`);
            }
            if (opCode === 6) { // restore
                if (analysis.transformStack.length > 0) {
                    analysis.currentTransform = analysis.transformStack.pop();
                    console.log(`Restore at ${i}, stack depth: ${analysis.transformStack.length}`);
                }
            }
            
            // Analyze constructPath operations
            if (opCode === 91 || opCode === 69) {
                const pathOps = args[0] || [];
                const pathCoords = args[1] || [];
                
                console.log(`ConstructPath at ${i}:`, {
                    ops: pathOps.length,
                    coords: pathCoords.length,
                    transform: [...analysis.currentTransform],
                    firstCoords: pathCoords.slice(0, 6)
                });
                
                analysis.constructPaths.push({
                    index: i,
                    opCount: pathOps.length,
                    coordCount: pathCoords.length,
                    transform: [...analysis.currentTransform],
                    sampleCoords: pathCoords.slice(0, 10)
                });
            }
            
            // Standard path operations
            if (opCode === 12 || opCode === 13) { // moveTo, lineTo
                analysis.standardPaths.push({
                    index: i,
                    type: opCode === 12 ? 'moveTo' : 'lineTo',
                    coords: args,
                    transform: [...analysis.currentTransform]
                });
            }
        }
        
        console.log('📊 Operation counts:', opCounts);
        console.log('📊 Analysis:', analysis);
        
        // Now extract with proper transformations
        const extraction = await this.extractWithTransforms(ops, viewport);
        
        return {
            analysis,
            extraction,
            opCounts
        };
    }
    
    multiplyTransform(current, newTransform) {
        const [a1, b1, c1, d1, e1, f1] = current;
        const [a2, b2, c2, d2, e2, f2] = newTransform;
        
        current[0] = a1 * a2 + b1 * c2;
        current[1] = a1 * b2 + b1 * d2;
        current[2] = c1 * a2 + d1 * c2;
        current[3] = c1 * b2 + d1 * d2;
        current[4] = e1 * a2 + f1 * c2 + e2;
        current[5] = e1 * b2 + f1 * d2 + f2;
    }
    
    async extractWithTransforms(ops, viewport) {
        const lines = [];
        let currentTransform = [1, 0, 0, 1, 0, 0];
        const transformStack = [];
        
        const applyTransform = (x, y) => {
            return {
                x: currentTransform[0] * x + currentTransform[2] * y + currentTransform[4],
                y: currentTransform[1] * x + currentTransform[3] * y + currentTransform[5]
            };
        };
        
        let currentPoint = null;
        
        for (let i = 0; i < ops.fnArray.length; i++) {
            const opCode = ops.fnArray[i];
            const args = ops.argsArray[i] || [];
            
            // Handle transforms
            if (opCode === 7) {
                this.multiplyTransform(currentTransform, args);
            } else if (opCode === 5) {
                transformStack.push([...currentTransform]);
            } else if (opCode === 6) {
                if (transformStack.length > 0) {
                    currentTransform = transformStack.pop();
                }
            }
            
            // Handle constructPath
            if (opCode === 91 || opCode === 69) {
                const pathOps = args[0] || [];
                const pathCoords = args[1] || [];
                let coordIndex = 0;
                
                for (let j = 0; j < pathOps.length; j++) {
                    const pathOp = pathOps[j];
                    
                    if (pathOp === 2 || pathOp === this.pdfjsLib?.OPS?.moveTo) { // moveTo
                        const raw = {
                            x: pathCoords[coordIndex],
                            y: pathCoords[coordIndex + 1]
                        };
                        currentPoint = applyTransform(raw.x, raw.y);
                        console.log(`MoveTo: raw(${raw.x.toFixed(2)}, ${raw.y.toFixed(2)}) -> transformed(${currentPoint.x.toFixed(2)}, ${currentPoint.y.toFixed(2)})`);
                        coordIndex += 2;
                    } else if (pathOp === 3 || pathOp === this.pdfjsLib?.OPS?.lineTo) { // lineTo
                        if (currentPoint) {
                            const raw = {
                                x: pathCoords[coordIndex],
                                y: pathCoords[coordIndex + 1]
                            };
                            const newPoint = applyTransform(raw.x, raw.y);
                            
                            const length = Math.sqrt(
                                Math.pow(newPoint.x - currentPoint.x, 2) + 
                                Math.pow(newPoint.y - currentPoint.y, 2)
                            );
                            
                            if (length > 0.5) {
                                lines.push({
                                    start: { ...currentPoint },
                                    end: { ...newPoint },
                                    raw: { start: raw, end: raw },
                                    transform: [...currentTransform]
                                });
                                console.log(`LineTo: raw(${raw.x.toFixed(2)}, ${raw.y.toFixed(2)}) -> transformed(${newPoint.x.toFixed(2)}, ${newPoint.y.toFixed(2)}), length: ${length.toFixed(2)}`);
                            }
                            
                            currentPoint = newPoint;
                        }
                        coordIndex += 2;
                    } else if (pathOp === 6) { // rectangle
                        const x = pathCoords[coordIndex];
                        const y = pathCoords[coordIndex + 1];
                        const w = pathCoords[coordIndex + 2];
                        const h = pathCoords[coordIndex + 3];
                        
                        const tl = applyTransform(x, y);
                        const tr = applyTransform(x + w, y);
                        const br = applyTransform(x + w, y + h);
                        const bl = applyTransform(x, y + h);
                        
                        lines.push(
                            { start: tl, end: tr },
                            { start: tr, end: br },
                            { start: br, end: bl },
                            { start: bl, end: tl }
                        );
                        
                        coordIndex += 4;
                    } else {
                        // Skip other operations but advance coord index appropriately
                        if (pathOp === 4 || pathOp === 5) { // curveTo operations
                            coordIndex += 6;
                        }
                    }
                }
            }
        }
        
        console.log(`Extracted ${lines.length} lines`);
        return lines;
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
    module.exports = PDFDecoderDebug;
}