/**
 * Threshold algorithms for image binarization
 * @module extraction/threshold
 */

/**
 * Apply adaptive threshold to image data
 * Uses local mean to determine threshold for each pixel
 * @param {ImageData} imageData - Input image data
 * @param {Object} options - Configuration options
 * @param {number} options.windowSize - Size of local window (default: 15)
 * @param {number} options.c - Constant subtracted from mean (default: 2)
 * @returns {Uint8Array} Binary image (0 or 255)
 */
export function adaptiveThreshold(imageData, options = {}) {
    const { windowSize = 15, c = 2 } = options;
    const { data, width, height } = imageData;
    const output = new Uint8Array(width * height);
    const halfWindow = Math.floor(windowSize / 2);
    
    // Pre-calculate integral image for fast mean calculation
    const integral = calculateIntegralImage(data, width, height);
    
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            
            // Calculate local mean using integral image
            const x1 = Math.max(0, x - halfWindow);
            const y1 = Math.max(0, y - halfWindow);
            const x2 = Math.min(width - 1, x + halfWindow);
            const y2 = Math.min(height - 1, y + halfWindow);
            
            const area = (x2 - x1 + 1) * (y2 - y1 + 1);
            const sum = getIntegralSum(integral, x1, y1, x2, y2, width);
            const mean = sum / area;
            
            // Get pixel brightness
            const pixelIdx = idx * 4;
            const brightness = (data[pixelIdx] + data[pixelIdx + 1] + data[pixelIdx + 2]) / 3;
            
            // Apply threshold
            output[idx] = brightness < (mean - c) ? 255 : 0;
        }
    }
    
    return output;
}

/**
 * Calculate integral image for fast area sum computation
 * @private
 */
function calculateIntegralImage(data, width, height) {
    const integral = new Float32Array(width * height);
    
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            const pixelIdx = idx * 4;
            const brightness = (data[pixelIdx] + data[pixelIdx + 1] + data[pixelIdx + 2]) / 3;
            
            integral[idx] = brightness;
            
            if (x > 0) integral[idx] += integral[idx - 1];
            if (y > 0) integral[idx] += integral[idx - width];
            if (x > 0 && y > 0) integral[idx] -= integral[idx - width - 1];
        }
    }
    
    return integral;
}

/**
 * Get sum of rectangular area using integral image
 * @private
 */
function getIntegralSum(integral, x1, y1, x2, y2, width) {
    let sum = integral[y2 * width + x2];
    
    if (x1 > 0) sum -= integral[y2 * width + (x1 - 1)];
    if (y1 > 0) sum -= integral[(y1 - 1) * width + x2];
    if (x1 > 0 && y1 > 0) sum += integral[(y1 - 1) * width + (x1 - 1)];
    
    return sum;
}

/**
 * Otsu's method for automatic threshold selection
 * Finds threshold that minimizes intra-class variance
 * @param {ImageData} imageData - Input image data
 * @returns {number} Optimal threshold value
 */
export function otsuThreshold(imageData) {
    const histogram = new Array(256).fill(0);
    const { data } = imageData;
    
    // Build histogram
    for (let i = 0; i < data.length; i += 4) {
        const brightness = Math.floor((data[i] + data[i + 1] + data[i + 2]) / 3);
        histogram[brightness]++;
    }
    
    const total = data.length / 4;
    let sum = 0;
    
    for (let i = 0; i < 256; i++) {
        sum += i * histogram[i];
    }
    
    let sumB = 0;
    let wB = 0;
    let wF = 0;
    let maxVariance = 0;
    let threshold = 0;
    
    for (let t = 0; t < 256; t++) {
        wB += histogram[t];
        if (wB === 0) continue;
        
        wF = total - wB;
        if (wF === 0) break;
        
        sumB += t * histogram[t];
        
        const mB = sumB / wB;
        const mF = (sum - sumB) / wF;
        
        const variance = wB * wF * (mB - mF) * (mB - mF);
        
        if (variance > maxVariance) {
            maxVariance = variance;
            threshold = t;
        }
    }
    
    return threshold;
}

/**
 * Multi-level thresholding for complex images
 * @param {ImageData} imageData - Input image data
 * @param {number[]} thresholds - Array of threshold values to try
 * @returns {Object} Results for each threshold
 */
export function multiThreshold(imageData, thresholds) {
    const results = {};
    const { data, width, height } = imageData;
    
    for (const threshold of thresholds) {
        const binary = new Uint8Array(width * height);
        let darkPixels = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const idx = i / 4;
            const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
            
            if (brightness < threshold) {
                binary[idx] = 255;
                darkPixels++;
            } else {
                binary[idx] = 0;
            }
        }
        
        results[threshold] = {
            binary,
            darkPixels,
            percentage: (darkPixels / (width * height)) * 100
        };
    }
    
    return results;
}

/**
 * Find optimal threshold for architectural drawings
 * Looks for threshold that gives 0.5-10% dark pixels
 * @param {ImageData} imageData - Input image data
 * @returns {Object} Optimal threshold and stats
 */
export function findOptimalThreshold(imageData) {
    const candidates = [250, 245, 240, 235, 230, 225, 220, 215, 210, 200, 190, 180, 170, 160, 150, 140, 130, 120];
    const { data, width, height } = imageData;
    const totalPixels = width * height;
    
    for (const threshold of candidates) {
        let darkCount = 0;
        
        for (let i = 0; i < data.length; i += 4) {
            const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
            if (brightness < threshold) darkCount++;
        }
        
        const percentage = (darkCount / totalPixels) * 100;
        
        // Good range for architectural drawings
        if (percentage >= 0.5 && percentage <= 10) {
            return {
                threshold,
                darkPixels: darkCount,
                percentage,
                confidence: calculateConfidence(percentage)
            };
        }
    }
    
    // Fallback to Otsu if no good threshold found
    const otsu = otsuThreshold(imageData);
    return {
        threshold: otsu,
        darkPixels: 0,
        percentage: 0,
        confidence: 0.5,
        method: 'otsu'
    };
}

/**
 * Calculate confidence score based on dark pixel percentage
 * @private
 */
function calculateConfidence(percentage) {
    // Ideal range is 1-5% for architectural drawings
    if (percentage >= 1 && percentage <= 5) return 1.0;
    if (percentage >= 0.5 && percentage <= 10) return 0.8;
    return 0.5;
}

export default {
    adaptiveThreshold,
    otsuThreshold,
    multiThreshold,
    findOptimalThreshold
};