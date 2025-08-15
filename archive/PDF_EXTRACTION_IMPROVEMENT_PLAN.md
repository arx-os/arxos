# PDF Wall Extraction - Accuracy & Performance Improvement Plan

## Current State Analysis
- **Working**: Detecting 33 walls from Alafia_ES_IDF_CallOut.pdf with threshold 240
- **Issues**: Not fully accurate, some walls missing/incorrect, performance could be optimized
- **Goal**: Achieve 95%+ accuracy for architectural floor plans with <1 second processing time

## Phase 1: Accuracy Improvements (Priority: HIGH)

### 1.1 Advanced Line Detection
```javascript
// Implement Hough Transform for robust line detection
class HoughTransform {
    detectLines(imageData) {
        // Convert to edge map using Canny edge detection
        // Apply Hough transform to find lines
        // Return line parameters (rho, theta)
    }
}
```
**Benefits**: More accurate line detection, handles broken lines, rotation-invariant
**Timeline**: 2 days

### 1.2 Multi-Scale Analysis
```javascript
// Process PDF at multiple resolutions
const scales = [0.5, 1.0, 2.0, 4.0];
for (let scale of scales) {
    // Render PDF at scale
    // Extract walls
    // Combine results with confidence scoring
}
```
**Benefits**: Catches thin lines at high res, thick walls at low res
**Timeline**: 1 day

### 1.3 Context-Aware Filtering
```javascript
// Use architectural knowledge to filter false positives
class ArchitecturalFilter {
    rules = {
        minWallLength: 50,      // mm in real scale
        maxWallThickness: 400,  // mm typical max
        parallelTolerance: 2,   // degrees
        perpendicularTolerance: 2
    }
    
    filterWalls(walls) {
        // Remove non-architectural elements
        // Snap to grid
        // Enforce right angles
    }
}
```
**Benefits**: Removes text, dimensions, symbols; keeps only structural walls
**Timeline**: 2 days

### 1.4 Machine Learning Enhancement (Optional)
```javascript
// Pre-trained model for architectural element detection
class WallDetectorML {
    async loadModel() {
        // Load TensorFlow.js model trained on floor plans
    }
    
    async detectWalls(canvas) {
        // Run inference
        // Return bounding boxes and confidence scores
    }
}
```
**Benefits**: Learns from real architectural drawings, handles complex cases
**Timeline**: 1 week (if pursuing)

## Phase 2: Performance Optimizations

### 2.1 Web Workers for Parallel Processing
```javascript
// Move heavy computation to background threads
class ExtractionWorker {
    constructor() {
        this.worker = new Worker('extraction-worker.js');
    }
    
    async extract(imageData, params) {
        // Divide image into tiles
        // Process tiles in parallel
        // Merge results
    }
}
```
**Benefits**: Non-blocking UI, 4x faster on quad-core
**Timeline**: 1 day

### 2.2 Incremental Processing
```javascript
// Process visible area first, background process rest
class IncrementalExtractor {
    extractVisible(viewport) {
        // Extract walls in current view
        // Queue rest for background
    }
    
    backgroundProcess() {
        // Process remaining areas
        // Update progressively
    }
}
```
**Benefits**: Instant feedback, perceived performance boost
**Timeline**: 1 day

### 2.3 Caching & Memoization
```javascript
// Cache extraction results
class ExtractionCache {
    cache = new Map();
    
    getKey(pdf, page, scale, threshold) {
        return `${pdf.fingerprint}_${page}_${scale}_${threshold}`;
    }
    
    get(params) {
        return this.cache.get(this.getKey(params));
    }
}
```
**Benefits**: Instant re-rendering, saves computation
**Timeline**: 0.5 days

### 2.4 WASM Acceleration (Advanced)
```rust
// Rust implementation compiled to WebAssembly
pub fn extract_walls(
    image_data: &[u8],
    width: u32,
    height: u32,
    threshold: u8
) -> Vec<Wall> {
    // High-performance line detection
}
```
**Benefits**: 10x faster than JavaScript for image processing
**Timeline**: 3 days

## Phase 3: Algorithm Improvements

### 3.1 Adaptive Thresholding
```javascript
// Local adaptive thresholding instead of global
function adaptiveThreshold(imageData, windowSize = 15) {
    // Calculate local mean for each pixel
    // Threshold based on local statistics
    // Handles varying lighting/contrast
}
```
**Benefits**: Works with scanned PDFs, varying quality
**Timeline**: 1 day

### 3.2 Connected Component Analysis
```javascript
// Group connected pixels into wall segments
class ConnectedComponents {
    findWalls(binaryImage) {
        // Label connected regions
        // Extract wall-like components
        // Filter by aspect ratio, size
    }
}
```
**Benefits**: Better wall segmentation, removes noise
**Timeline**: 1 day

### 3.3 Vectorization & Simplification
```javascript
// Convert raster walls to clean vectors
class WallVectorizer {
    vectorize(walls) {
        // Fit lines to pixel data
        // Merge collinear segments
        // Simplify with Douglas-Peucker
    }
}
```
**Benefits**: Clean geometric output, smaller data size
**Timeline**: 2 days

### 3.4 Corner & Junction Detection
```javascript
// Detect wall intersections and corners
class JunctionDetector {
    findJunctions(walls) {
        // Detect L, T, X junctions
        // Snap walls to junctions
        // Ensure connectivity
    }
}
```
**Benefits**: Accurate building topology, proper connections
**Timeline**: 2 days

## Phase 4: Quality Assurance

### 4.1 Confidence Scoring
```javascript
// Rate extraction quality
class QualityScorer {
    score(walls, originalImage) {
        return {
            coverage: this.calculateCoverage(walls, originalImage),
            consistency: this.checkConsistency(walls),
            topology: this.validateTopology(walls),
            overall: this.computeOverallScore()
        };
    }
}
```

### 4.2 Manual Correction Tools
```javascript
// UI for fixing extraction errors
class WallEditor {
    tools = {
        addWall: () => {},
        deleteWall: () => {},
        extendWall: () => {},
        splitWall: () => {},
        mergeWalls: () => {}
    }
}
```

### 4.3 Test Suite
```javascript
// Automated testing with ground truth
const testCases = [
    { pdf: 'simple_rectangle.pdf', expectedWalls: 4 },
    { pdf: 'complex_school.pdf', expectedWalls: 127 },
    { pdf: 'residential.pdf', expectedWalls: 43 }
];
```

## Implementation Priority

### Week 1 (Immediate Impact)
1. **Adaptive Thresholding** - Handles more PDF types
2. **Hough Transform** - Major accuracy boost
3. **Web Workers** - Better performance
4. **Connected Components** - Cleaner extraction

### Week 2 (Refinement)
1. **Multi-Scale Analysis** - Catches all wall types
2. **Architectural Filtering** - Removes false positives
3. **Vectorization** - Clean output
4. **Junction Detection** - Proper topology

### Week 3 (Advanced)
1. **WASM Acceleration** - Maximum performance
2. **ML Enhancement** - State-of-the-art accuracy
3. **Quality Scoring** - Confidence metrics
4. **Manual Correction** - User refinement

## Success Metrics

### Accuracy Targets
- **Simple PDFs** (rectangles): 100% accuracy
- **Medium PDFs** (10-50 walls): 95% accuracy
- **Complex PDFs** (50+ walls): 90% accuracy
- **Poor Quality** (scanned/faded): 80% accuracy

### Performance Targets
- **Small PDFs** (<1MB): <500ms
- **Medium PDFs** (1-5MB): <1 second
- **Large PDFs** (>5MB): <3 seconds
- **UI Responsiveness**: Never blocked

### Quality Indicators
- Wall connectivity: All walls properly connected
- Right angles: 90° angles preserved
- Parallel walls: Detected and aligned
- Noise removal: <5% false positives

## Technical Stack

### Core Technologies
- **PDF.js**: PDF rendering
- **Canvas API**: Image manipulation
- **Web Workers**: Parallel processing
- **WebAssembly**: Performance critical code

### Optional Enhancements
- **TensorFlow.js**: ML-based detection
- **OpenCV.js**: Computer vision algorithms
- **GPU.js**: GPU acceleration

## Testing Strategy

### Unit Tests
```javascript
describe('Wall Extraction', () => {
    test('detects horizontal lines', () => {});
    test('detects vertical lines', () => {});
    test('merges nearby segments', () => {});
    test('filters noise', () => {});
});
```

### Integration Tests
```javascript
describe('PDF Processing', () => {
    test('extracts walls from simple PDF', () => {});
    test('handles rotated PDFs', () => {});
    test('processes multi-page PDFs', () => {});
});
```

### Performance Benchmarks
```javascript
const benchmark = {
    measureExtraction(pdf) {
        const start = performance.now();
        const walls = extract(pdf);
        const time = performance.now() - start;
        return { walls, time };
    }
};
```

## Next Steps

1. **Implement Adaptive Thresholding** (Today)
   - Better handles varying line darkness
   - Reduces false negatives

2. **Add Hough Transform** (Tomorrow)
   - More robust line detection
   - Handles gaps and noise

3. **Setup Web Workers** (Day 3)
   - Non-blocking processing
   - Better UX

4. **Create Test Suite** (Day 4)
   - Measure improvements
   - Prevent regressions

## Code Organization

```
/arxos/extraction/
├── core/
│   ├── threshold.js      # Thresholding algorithms
│   ├── hough.js         # Hough transform
│   ├── connected.js     # Connected components
│   └── vectorize.js     # Vectorization
├── filters/
│   ├── architectural.js # Architecture-specific
│   ├── noise.js        # Noise removal
│   └── merge.js        # Wall merging
├── workers/
│   ├── extraction.worker.js
│   └── pool.js         # Worker pool manager
├── ml/ (optional)
│   ├── model.js        # TensorFlow model
│   └── training/       # Training scripts
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/       # Test PDFs
```

## Summary

This plan provides a roadmap to achieve:
- **95%+ accuracy** on typical architectural PDFs
- **<1 second** processing time for most documents
- **Robust handling** of various PDF qualities
- **Clean, editable** BIM output

The phased approach allows for incremental improvements while maintaining a working system throughout development.