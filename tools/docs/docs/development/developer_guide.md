# Developer Guide - Viewport Manager

## Overview

This document provides comprehensive technical documentation for developers integrating and extending the Arxos SVG-BIM viewport manager. It covers API reference, integration patterns, customization options, and best practices.

## Table of Contents

1. [API Reference](#api-reference)
2. [Integration Guide](#integration-guide)
3. [Customization](#customization)
4. [Event System](#event-system)
5. [Performance Optimization](#performance-optimization)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## API Reference

### ViewportManager Class

#### Constructor
```javascript
new ViewportManager(svgElement, options)
```

**Parameters:**
- `svgElement` (HTMLElement): The SVG element to manage
- `options` (Object): Configuration options

**Options:**
```javascript
{
    minZoom: 0.1,              // Minimum zoom level
    maxZoom: 5.0,              // Maximum zoom level
    zoomStep: 0.1,             // Zoom increment
    maxHistorySize: 50,        // Maximum history entries
    enableTouchGestures: true, // Enable touch support
    coordinateSystem: 'meters', // Coordinate system units
    performanceMode: 'auto',   // Performance optimization
    panBoundaries: {           // Pan boundary settings
        enabled: true,
        maxDistance: 2000
    }
}
```

#### Core Methods

##### Zoom Operations
```javascript
// Set zoom level
viewport.setZoom(zoomLevel)

// Get current zoom level
const zoom = viewport.getZoom()

// Zoom in by one step
viewport.zoomIn()

// Zoom out by one step
viewport.zoomOut()

// Zoom to fit all content
viewport.zoomToFit()

// Reset zoom to 100%
viewport.resetZoom()
```

##### Pan Operations
```javascript
// Set pan position
viewport.setPan(x, y)

// Get current pan position
const [x, y] = viewport.getPan()

// Pan by offset
viewport.panBy(deltaX, deltaY)

// Center view on coordinates
viewport.centerOn(x, y)
```

##### Coordinate Conversion
```javascript
// Convert screen coordinates to SVG coordinates
const [svgX, svgY] = viewport.screenToSVG(screenX, screenY)

// Convert SVG coordinates to screen coordinates
const [screenX, screenY] = viewport.svgToScreen(svgX, svgY)

// Get current viewport bounds
const bounds = viewport.getViewportBounds()
```

##### History Management
```javascript
// Undo last zoom operation
const success = viewport.undoZoom()

// Redo last zoom operation
const success = viewport.redoZoom()

// Clear zoom history
viewport.clearZoomHistory()

// Get history information
const history = viewport.getZoomHistory()
```

##### Event Management
```javascript
// Add event listener
viewport.addEventListener(eventType, handler)

// Remove event listener
viewport.removeEventListener(eventType, handler)

// Trigger custom event
viewport.triggerEvent(eventType, data)
```

#### Properties

```javascript
// Current zoom level
viewport.zoom

// Current pan position
viewport.panX
viewport.panY

// Zoom history
viewport.zoomHistory

// History index
viewport.historyIndex

// Configuration
viewport.config

// Touch state
viewport.touchState

// Performance metrics
viewport.performanceMetrics
```

## Integration Guide

### Basic Integration

#### 1. Include the Library
```html
<script src="viewport-manager.js"></script>
```

#### 2. Create SVG Element
```html
<svg id="building-model" width="800" height="600">
    <!-- Your building model content -->
</svg>
```

#### 3. Initialize Viewport Manager
```javascript
const svgElement = document.getElementById('building-model');
const viewport = new ViewportManager(svgElement, {
    minZoom: 0.1,
    maxZoom: 5.0,
    enableTouchGestures: true
});
```

#### 4. Add Event Listeners
```javascript
viewport.addEventListener('zoomChanged', (data) => {
    console.log('Zoom changed:', data.zoom);
    updateZoomDisplay(data.zoom);
});

viewport.addEventListener('panChanged', (data) => {
    console.log('Pan changed:', data.x, data.y);
    updatePanDisplay(data.x, data.y);
});
```

### Advanced Integration

#### Custom Controls
```javascript
// Custom zoom controls
document.getElementById('zoom-in').addEventListener('click', () => {
    viewport.zoomIn();
});

document.getElementById('zoom-out').addEventListener('click', () => {
    viewport.zoomOut();
});

document.getElementById('zoom-fit').addEventListener('click', () => {
    viewport.zoomToFit();
});

// Custom pan controls
document.getElementById('pan-left').addEventListener('click', () => {
    viewport.panBy(-100, 0);
});

document.getElementById('pan-right').addEventListener('click', () => {
    viewport.panBy(100, 0);
});
```

#### Coordinate Display
```javascript
// Update coordinate display
function updateCoordinateDisplay(event) {
    const [svgX, svgY] = viewport.screenToSVG(event.clientX, event.clientY);
    document.getElementById('coordinates').textContent =
        `X: ${svgX.toFixed(3)} Y: ${svgY.toFixed(3)}`;
}

svgElement.addEventListener('mousemove', updateCoordinateDisplay);
```

#### Performance Monitoring
```javascript
// Monitor performance
setInterval(() => {
    const metrics = viewport.performanceMetrics;
    console.log('FPS:', metrics.fps);
    console.log('Memory Usage:', metrics.memoryUsage);
    console.log('Render Time:', metrics.renderTime);
}, 1000);
```

## Customization

### Custom Zoom Behavior
```javascript
class CustomViewportManager extends ViewportManager {
    constructor(svgElement, options) {
        super(svgElement, options);
        this.customZoomBehavior = true;
    }

    setZoom(zoom) {
        // Custom zoom logic
        const adjustedZoom = this.adjustZoomForCustomBehavior(zoom);
        super.setZoom(adjustedZoom);
    }

    adjustZoomForCustomBehavior(zoom) {
        // Implement custom zoom adjustment
        return zoom * 1.1; // Example: 10% boost
    }
}
```

### Custom Coordinate System
```javascript
class CustomCoordinateSystem {
    constructor(originX, originY, scale) {
        this.originX = originX;
        this.originY = originY;
        this.scale = scale;
    }

    convertToRealWorld(screenX, screenY) {
        return {
            x: (screenX - this.originX) * this.scale,
            y: (screenY - this.originY) * this.scale
        };
    }

    convertToScreen(realX, realY) {
        return {
            x: realX / this.scale + this.originX,
            y: realY / this.scale + this.originY
        };
    }
}
```

### Custom Event Handlers
```javascript
// Custom zoom handler with analytics
function customZoomHandler(data) {
    // Track zoom usage
    analytics.track('viewport_zoom', {
        zoomLevel: data.zoom,
        timestamp: Date.now()
    });

    // Update UI
    updateZoomIndicator(data.zoom);

    // Trigger custom logic
    if (data.zoom > 3.0) {
        showHighZoomWarning();
    }
}

viewport.addEventListener('zoomChanged', customZoomHandler);
```

## Event System

### Available Events

#### Navigation Events
```javascript
// Zoom events
viewport.addEventListener('zoomChanged', (data) => {
    // data.zoom: new zoom level
    // data.previousZoom: previous zoom level
    // data.source: 'mouse', 'keyboard', 'touch', 'programmatic'
});

// Pan events
viewport.addEventListener('panChanged', (data) => {
    // data.x: new x position
    // data.y: new y position
    // data.previousX: previous x position
    // data.previousY: previous y position
});

// Viewport events
viewport.addEventListener('viewportChanged', (data) => {
    // data.zoom: current zoom
    // data.x: current x position
    // data.y: current y position
    // data.bounds: viewport bounds
});
```

#### History Events
```javascript
// History events
viewport.addEventListener('historyChanged', (data) => {
    // data.canUndo: boolean
    // data.canRedo: boolean
    // data.historySize: number
});

// Undo/redo events
viewport.addEventListener('undoPerformed', (data) => {
    // data.zoom: restored zoom level
    // data.x: restored x position
    // data.y: restored y position
});

viewport.addEventListener('redoPerformed', (data) => {
    // data.zoom: restored zoom level
    // data.x: restored x position
    // data.y: restored y position
});
```

#### Performance Events
```javascript
// Performance events
viewport.addEventListener('performanceWarning', (data) => {
    // data.type: 'memory', 'cpu', 'fps'
    // data.value: current value
    // data.threshold: threshold value
});

viewport.addEventListener('constraintViolation', (data) => {
    // data.type: 'zoom', 'pan'
    // data.value: attempted value
    // data.limit: constraint limit
});
```

### Custom Events
```javascript
// Trigger custom events
viewport.triggerEvent('customAction', {
    action: 'symbolSelected',
    symbolId: 'door-001',
    coordinates: { x: 100, y: 200 }
});

// Listen for custom events
viewport.addEventListener('customAction', (data) => {
    console.log('Custom action:', data);
});
```

## Performance Optimization

### Configuration Optimization
```javascript
// Performance-focused configuration
const performanceConfig = {
    minZoom: 0.2,              // Higher minimum zoom
    maxZoom: 3.0,              // Lower maximum zoom
    maxHistorySize: 25,        // Smaller history
    performanceMode: 'high',   // High performance mode
    enableTouchGestures: false, // Disable if not needed
    throttleUpdates: true      // Enable throttling
};
```

### Memory Management
```javascript
// Monitor memory usage
function monitorMemory() {
    const metrics = viewport.performanceMetrics;
    if (metrics.memoryUsage > 100) { // 100MB threshold
        console.warn('High memory usage detected');
        viewport.clearZoomHistory();
    }
}

setInterval(monitorMemory, 5000);
```

### Rendering Optimization
```javascript
// Optimize rendering for large models
function optimizeRendering() {
    const zoom = viewport.getZoom();
    const symbolCount = getSymbolCount();

    if (symbolCount > 1000 && zoom < 0.5) {
        // Enable level of detail
        enableLOD();
    } else {
        disableLOD();
    }
}

viewport.addEventListener('zoomChanged', optimizeRendering);
```

## Testing

### Unit Testing
```javascript
// Example test using Jest
describe('ViewportManager', () => {
    let viewport;
    let svgElement;

    beforeEach(() => {
        svgElement = document.createElement('svg');
        viewport = new ViewportManager(svgElement);
    });

    test('should set zoom level correctly', () => {
        viewport.setZoom(2.0);
        expect(viewport.getZoom()).toBe(2.0);
    });

    test('should respect zoom constraints', () => {
        viewport.setZoom(10.0); // Beyond max
        expect(viewport.getZoom()).toBe(5.0); // Max zoom
    });

    test('should convert coordinates correctly', () => {
        viewport.setZoom(2.0);
        viewport.setPan(100, 200);

        const [svgX, svgY] = viewport.screenToSVG(200, 400);
        expect(svgX).toBe(50); // (200 - 100) / 2
        expect(svgY).toBe(100); // (400 - 200) / 2
    });
});
```

### Integration Testing
```javascript
// Example integration test
describe('Viewport Integration', () => {
    test('should integrate with symbol library', () => {
        const symbolLibrary = new SymbolLibrary();
        const viewport = new ViewportManager(svgElement);

        // Add symbol to viewport
        const symbol = symbolLibrary.createSymbol('door');
        viewport.addSymbol(symbol);

        // Test symbol interaction
        const symbols = viewport.getSymbolsAt(100, 200);
        expect(symbols).toContain(symbol);
    });
});
```

### Performance Testing
```javascript
// Performance test
describe('Viewport Performance', () => {
    test('should handle high-frequency zoom operations', () => {
        const startTime = performance.now();

        for (let i = 0; i < 1000; i++) {
            viewport.setZoom(Math.random() * 5);
        }

        const endTime = performance.now();
        const duration = endTime - startTime;

        expect(duration).toBeLessThan(1000); // Should complete in <1 second
    });
});
```

## Troubleshooting

### Common Issues

#### Performance Problems
```javascript
// Check performance metrics
const metrics = viewport.performanceMetrics;
console.log('Performance metrics:', metrics);

// Common solutions
if (metrics.fps < 30) {
    // Reduce zoom level
    viewport.setZoom(Math.min(viewport.getZoom(), 2.0));

    // Clear history
    viewport.clearZoomHistory();

    // Enable performance mode
    viewport.setPerformanceMode('high');
}
```

#### Memory Leaks
```javascript
// Check for memory leaks
function checkMemoryLeaks() {
    const initialMemory = performance.memory.usedJSHeapSize;

    // Perform operations
    for (let i = 0; i < 100; i++) {
        viewport.setZoom(Math.random() * 5);
    }

    const finalMemory = performance.memory.usedJSHeapSize;
    const memoryIncrease = finalMemory - initialMemory;

    if (memoryIncrease > 10 * 1024 * 1024) { // 10MB threshold
        console.warn('Potential memory leak detected');
    }
}
```

#### Event Listener Issues
```javascript
// Debug event listeners
function debugEventListeners() {
    const events = viewport.getEventListeners();
    console.log('Active event listeners:', events);

    // Check for duplicate listeners
    const duplicates = findDuplicateListeners(events);
    if (duplicates.length > 0) {
        console.warn('Duplicate listeners found:', duplicates);
    }
}
```

### Debug Mode
```javascript
// Enable debug mode
const viewport = new ViewportManager(svgElement, {
    debug: true,
    logLevel: 'verbose'
});

// Debug information will be logged to console
```

## Best Practices

### Code Organization
```javascript
// Separate concerns
class ViewportController {
    constructor(svgElement) {
        this.viewport = new ViewportManager(svgElement);
        this.setupEventHandlers();
        this.setupUI();
    }

    setupEventHandlers() {
        this.viewport.addEventListener('zoomChanged', this.handleZoom.bind(this));
        this.viewport.addEventListener('panChanged', this.handlePan.bind(this));
    }

    setupUI() {
        // Setup UI controls
    }

    handleZoom(data) {
        // Handle zoom changes
    }

    handlePan(data) {
        // Handle pan changes
    }
}
```

### Error Handling
```javascript
// Robust error handling
class SafeViewportManager {
    constructor(svgElement, options) {
        try {
            this.viewport = new ViewportManager(svgElement, options);
            this.setupErrorHandling();
        } catch (error) {
            console.error('Failed to initialize viewport:', error);
            this.fallbackToBasicViewport();
        }
    }

    setupErrorHandling() {
        this.viewport.addEventListener('error', (error) => {
            console.error('Viewport error:', error);
            this.handleError(error);
        });
    }

    handleError(error) {
        // Implement error recovery
        switch (error.type) {
            case 'constraint_violation':
                this.handleConstraintViolation(error);
                break;
            case 'performance_warning':
                this.handlePerformanceWarning(error);
                break;
            default:
                this.handleGenericError(error);
        }
    }
}
```

### Performance Optimization
```javascript
// Performance optimization patterns
class OptimizedViewportManager {
    constructor(svgElement, options) {
        this.viewport = new ViewportManager(svgElement, {
            ...options,
            throttleUpdates: true,
            performanceMode: 'high'
        });

        this.setupPerformanceMonitoring();
    }

    setupPerformanceMonitoring() {
        // Monitor and optimize performance
        setInterval(() => {
            this.optimizePerformance();
        }, 1000);
    }

    optimizePerformance() {
        const metrics = this.viewport.performanceMetrics;

        if (metrics.fps < 30) {
            this.enablePerformanceMode();
        }

        if (metrics.memoryUsage > 100) {
            this.cleanupMemory();
        }
    }
}
```

### Testing Strategy
```javascript
// Comprehensive testing strategy
describe('ViewportManager Testing', () => {
    // Unit tests for individual methods
    describe('Unit Tests', () => {
        test('zoom operations');
        test('pan operations');
        test('coordinate conversion');
    });

    // Integration tests for component interaction
    describe('Integration Tests', () => {
        test('symbol library integration');
        test('event system integration');
        test('performance monitoring');
    });

    // Performance tests for optimization
    describe('Performance Tests', () => {
        test('high-frequency operations');
        test('memory usage');
        test('rendering performance');
    });

    // Browser compatibility tests
    describe('Browser Tests', () => {
        test('Chrome compatibility');
        test('Firefox compatibility');
        test('Safari compatibility');
        test('Edge compatibility');
    });
});
```

---

**Documentation Version**: 1.0.0
**Last Updated**: [Current Date]
**Target Audience**: Developers and Technical Users
**Compatibility**: Viewport Manager v1.0.0+
