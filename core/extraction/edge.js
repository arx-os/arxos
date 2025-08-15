/**
 * Edge detection algorithms for preprocessing
 * @module extraction/edge
 */

/**
 * Canny edge detection
 * @param {ImageData} imageData - Input image
 * @param {Object} options - Configuration options
 * @returns {Uint8Array} Binary edge map
 */
export function cannyEdgeDetection(imageData, options = {}) {
    const {
        lowThreshold = 50,
        highThreshold = 150,
        gaussianSize = 5,
        gaussianSigma = 1.4
    } = options;
    
    const { data, width, height } = imageData;
    
    // Step 1: Gaussian blur
    const blurred = gaussianBlur(data, width, height, gaussianSize, gaussianSigma);
    
    // Step 2: Gradient calculation (Sobel)
    const { magnitude, direction } = calculateGradients(blurred, width, height);
    
    // Step 3: Non-maximum suppression
    const suppressed = nonMaximumSuppression(magnitude, direction, width, height);
    
    // Step 4: Double thresholding
    const { strong, weak } = doubleThreshold(suppressed, width, height, lowThreshold, highThreshold);
    
    // Step 5: Edge tracking by hysteresis
    const edges = edgeTracking(strong, weak, width, height);
    
    return edges;
}

/**
 * Apply Gaussian blur to image
 * @private
 */
function gaussianBlur(data, width, height, size, sigma) {
    const kernel = createGaussianKernel(size, sigma);
    const output = new Uint8Array(data.length);
    const halfSize = Math.floor(size / 2);
    
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            let sumR = 0, sumG = 0, sumB = 0, sumW = 0;
            
            for (let ky = -halfSize; ky <= halfSize; ky++) {
                for (let kx = -halfSize; kx <= halfSize; kx++) {
                    const px = Math.min(Math.max(x + kx, 0), width - 1);
                    const py = Math.min(Math.max(y + ky, 0), height - 1);
                    const idx = (py * width + px) * 4;
                    const weight = kernel[(ky + halfSize) * size + (kx + halfSize)];
                    
                    sumR += data[idx] * weight;
                    sumG += data[idx + 1] * weight;
                    sumB += data[idx + 2] * weight;
                    sumW += weight;
                }
            }
            
            const outIdx = (y * width + x) * 4;
            output[outIdx] = sumR / sumW;
            output[outIdx + 1] = sumG / sumW;
            output[outIdx + 2] = sumB / sumW;
            output[outIdx + 3] = data[outIdx + 3];
        }
    }
    
    return output;
}

/**
 * Create Gaussian kernel
 * @private
 */
function createGaussianKernel(size, sigma) {
    const kernel = new Float32Array(size * size);
    const center = Math.floor(size / 2);
    let sum = 0;
    
    for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
            const dx = x - center;
            const dy = y - center;
            const value = Math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma));
            kernel[y * size + x] = value;
            sum += value;
        }
    }
    
    // Normalize
    for (let i = 0; i < kernel.length; i++) {
        kernel[i] /= sum;
    }
    
    return kernel;
}

/**
 * Calculate gradients using Sobel operator
 * @private
 */
function calculateGradients(data, width, height) {
    const magnitude = new Float32Array(width * height);
    const direction = new Float32Array(width * height);
    
    // Sobel kernels
    const sobelX = [-1, 0, 1, -2, 0, 2, -1, 0, 1];
    const sobelY = [-1, -2, -1, 0, 0, 0, 1, 2, 1];
    
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            let gx = 0, gy = 0;
            
            // Apply Sobel kernels
            for (let ky = -1; ky <= 1; ky++) {
                for (let kx = -1; kx <= 1; kx++) {
                    const idx = ((y + ky) * width + (x + kx)) * 4;
                    const brightness = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
                    const kernelIdx = (ky + 1) * 3 + (kx + 1);
                    
                    gx += brightness * sobelX[kernelIdx];
                    gy += brightness * sobelY[kernelIdx];
                }
            }
            
            const outIdx = y * width + x;
            magnitude[outIdx] = Math.sqrt(gx * gx + gy * gy);
            direction[outIdx] = Math.atan2(gy, gx);
        }
    }
    
    return { magnitude, direction };
}

/**
 * Non-maximum suppression
 * @private
 */
function nonMaximumSuppression(magnitude, direction, width, height) {
    const output = new Float32Array(width * height);
    
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = y * width + x;
            const mag = magnitude[idx];
            const dir = direction[idx];
            
            // Quantize direction to 0, 45, 90, or 135 degrees
            const angle = ((dir + Math.PI) * 180 / Math.PI) % 180;
            
            let n1, n2;
            
            if (angle < 22.5 || angle >= 157.5) {
                // Horizontal edge
                n1 = magnitude[idx - 1];
                n2 = magnitude[idx + 1];
            } else if (angle < 67.5) {
                // Diagonal edge /
                n1 = magnitude[idx - width - 1];
                n2 = magnitude[idx + width + 1];
            } else if (angle < 112.5) {
                // Vertical edge
                n1 = magnitude[idx - width];
                n2 = magnitude[idx + width];
            } else {
                // Diagonal edge \
                n1 = magnitude[idx - width + 1];
                n2 = magnitude[idx + width - 1];
            }
            
            // Keep only if local maximum
            if (mag >= n1 && mag >= n2) {
                output[idx] = mag;
            }
        }
    }
    
    return output;
}

/**
 * Double thresholding
 * @private
 */
function doubleThreshold(magnitude, width, height, low, high) {
    const strong = new Uint8Array(width * height);
    const weak = new Uint8Array(width * height);
    
    for (let i = 0; i < magnitude.length; i++) {
        if (magnitude[i] >= high) {
            strong[i] = 255;
        } else if (magnitude[i] >= low) {
            weak[i] = 128;
        }
    }
    
    return { strong, weak };
}

/**
 * Edge tracking by hysteresis
 * @private
 */
function edgeTracking(strong, weak, width, height) {
    const edges = new Uint8Array(width * height);
    const visited = new Uint8Array(width * height);
    
    // Copy strong edges
    for (let i = 0; i < strong.length; i++) {
        if (strong[i] > 0) {
            edges[i] = 255;
        }
    }
    
    // Track weak edges connected to strong edges
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = y * width + x;
            
            if (strong[idx] > 0 && !visited[idx]) {
                // DFS from strong edge
                const stack = [{ x, y }];
                
                while (stack.length > 0) {
                    const { x: cx, y: cy } = stack.pop();
                    const cidx = cy * width + cx;
                    
                    if (visited[cidx]) continue;
                    visited[cidx] = 1;
                    
                    // Check 8-connected neighbors
                    for (let dy = -1; dy <= 1; dy++) {
                        for (let dx = -1; dx <= 1; dx++) {
                            if (dx === 0 && dy === 0) continue;
                            
                            const nx = cx + dx;
                            const ny = cy + dy;
                            
                            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                                const nidx = ny * width + nx;
                                
                                if (weak[nidx] > 0 && !visited[nidx]) {
                                    edges[nidx] = 255;
                                    stack.push({ x: nx, y: ny });
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return edges;
}

/**
 * Sobel edge detection (simpler alternative to Canny)
 * @param {ImageData} imageData - Input image
 * @param {number} threshold - Edge threshold
 * @returns {Uint8Array} Binary edge map
 */
export function sobelEdgeDetection(imageData, threshold = 100) {
    const { data, width, height } = imageData;
    const edges = new Uint8Array(width * height);
    
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            // Get 3x3 neighborhood
            const tl = getBrightness(data, (y-1) * width + (x-1));
            const tm = getBrightness(data, (y-1) * width + x);
            const tr = getBrightness(data, (y-1) * width + (x+1));
            const ml = getBrightness(data, y * width + (x-1));
            const mm = getBrightness(data, y * width + x);
            const mr = getBrightness(data, y * width + (x+1));
            const bl = getBrightness(data, (y+1) * width + (x-1));
            const bm = getBrightness(data, (y+1) * width + x);
            const br = getBrightness(data, (y+1) * width + (x+1));
            
            // Sobel X
            const gx = -tl - 2*ml - bl + tr + 2*mr + br;
            
            // Sobel Y
            const gy = -tl - 2*tm - tr + bl + 2*bm + br;
            
            // Magnitude
            const magnitude = Math.sqrt(gx * gx + gy * gy);
            
            edges[y * width + x] = magnitude > threshold ? 255 : 0;
        }
    }
    
    return edges;
}

/**
 * Get brightness value from image data
 * @private
 */
function getBrightness(data, pixelIdx) {
    const idx = pixelIdx * 4;
    return (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
}

export default {
    cannyEdgeDetection,
    sobelEdgeDetection
};