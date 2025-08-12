# Arxos Fractal Demo

Interactive demonstration of the fractal ArxObject system with Google Maps-style lazy loading and infinite zoom capabilities.

## Features

### 🔍 Infinite Zoom Architecture
- **7 Scale Levels**: Campus (1km) → Building → Floor → Room → Fixture → Component → Schematic (1mm)
- **Smooth Transitions**: Fluid zoom and pan with momentum-based gestures
- **Scale-Aware Rendering**: Objects appear/disappear based on zoom level relevance

### 🚀 Performance Optimization
- **Adaptive Performance Budget**: Automatically adjusts quality based on device capabilities
- **Multi-Level Caching**: Memory → Redis → Database → Generate pipeline
- **Predictive Preloading**: ML-powered movement prediction with TensorFlow.js
- **Frame Budget Management**: Maintains 60 FPS through progressive loading

### 🎮 Interactive Controls
- **Mouse/Trackpad**: Scroll to zoom, drag to pan, double-click to zoom in
- **Touch Gestures**: Pinch-to-zoom, pan, multi-touch support
- **Keyboard Shortcuts**: `+/-` zoom, `0` reset, `Ctrl+D` debug mode

### 📊 Real-Time Monitoring
- **FPS Counter**: Live performance monitoring with color-coded indicators
- **Memory Usage**: Real-time memory tracking with automatic optimization
- **Cache Statistics**: Hit rates and efficiency metrics
- **Debug Mode**: Tile grid visualization and detailed performance stats

## Architecture Integration

### Scale Engine API
Connects to the NestJS Scale Engine service at `localhost:3001`:
- `/lazy-loading/tiles/load` - Batch tile loading with priority
- `/lazy-loading/details/progressive` - Progressive detail enhancement
- `/viewport/zoom` - Synchronized zoom operations
- `/lazy-loading/preload/area` - Predictive area preloading

### Data Pipeline
```
Frontend Request → Scale Engine → PostgreSQL/PostGIS → MinIO → Redis → Response
                                     ↓
                              Vector Tiles ← TensorFlow.js Predictions
```

### WebGL Rendering
- **Three.js/React Three Fiber**: Hardware-accelerated 3D rendering
- **Orthographic Projection**: 2D-style fractal viewing with 3D objects
- **LOD System**: Level-of-detail management based on distance and scale
- **Frustum Culling**: Only render objects in viewport

## Scale Level Details

| Level | Name | Scale Range | Objects | Purpose |
|-------|------|-------------|---------|---------|
| 1 | Campus | 0.01-0.1x | Buildings | Site overview |
| 2 | Building | 0.1-1.0x | Floors | Building layout |
| 3 | Floor | 1.0-10x | Rooms | Floor plans |
| 4 | Room | 10-100x | Fixtures | Room details |
| 5 | Fixture | 100-1000x | Components | Equipment |
| 6 | Component | 1000-10000x | Parts | Component details |
| 7 | Schematic | 10000-100000x | Wiring | Technical drawings |

## Getting Started

### Prerequisites
- Node.js 18+
- Running Scale Engine service at `localhost:3001`
- PostgreSQL with PostGIS and TimescaleDB extensions

### Installation
```bash
cd frontend/fractal-demo
npm install
```

### Development
```bash
npm run dev
```

Visit http://localhost:3000 to see the demo.

### Production Build
```bash
npm run build
npm run start
```

## Environment Variables

```env
SCALE_ENGINE_URL=http://localhost:3001
WEBSOCKET_URL=ws://localhost:3001
NEXT_PUBLIC_PERFORMANCE_MONITORING=true
NEXT_PUBLIC_DEBUG_TILES=false
NEXT_PUBLIC_MAX_TILE_CACHE_SIZE=1000
NEXT_PUBLIC_PREDICTION_ENABLED=true
```

## Controls & Usage

### Navigation
- **Zoom**: Mouse wheel or `+`/`-` keys
- **Pan**: Click and drag or arrow keys
- **Reset**: Press `0` or click reset button
- **Debug**: Press `Ctrl+D` to toggle debug mode

### UI Elements
- **Zoom Controls**: Right panel with scale indicator and level display
- **Performance Monitor**: Bottom right with FPS, memory, and cache stats
- **Scale Level Indicator**: Top left showing current scale and context
- **Loading Indicators**: Animated when fetching new data

### Interaction
- **Click Objects**: Zoom in and center on clicked object
- **Hover Effects**: Highlight and show object details
- **BILT Rewards**: Display token rewards for contributions
- **Contributors**: Show collaboration indicators

## Performance Features

### Adaptive Quality
- Automatically reduces quality on lower-end devices
- Dynamic LOD adjustment based on performance
- Memory pressure detection and cleanup

### Caching Strategy
- **L1 Cache**: Browser memory for immediate access
- **L2 Cache**: Redis for cross-session persistence
- **L3 Cache**: Database with spatial indexing
- **Predictive**: Pre-loads based on user behavior patterns

### Optimization Techniques
- **Viewport Culling**: Only load visible objects
- **Tile-Based Loading**: Chunked data requests
- **Progressive Enhancement**: Load basic details first
- **Debounced Requests**: Batch operations to reduce API calls

## Development Notes

### Adding New Object Types
1. Update `FractalArxObject` type definition
2. Add rendering logic in `FractalObject.tsx`
3. Configure color scheme and geometry
4. Test across all scale levels

### Performance Tuning
- Monitor FPS in development mode
- Use React DevTools Profiler
- Check memory usage patterns
- Optimize tile cache size based on device capabilities

### Testing
```bash
npm run test        # Unit tests
npm run test:e2e    # End-to-end tests
npm run type-check  # TypeScript validation
npm run lint        # Code quality
```

This demo showcases the core fractal ArxObject architecture and demonstrates how infinite zoom with lazy loading can provide seamless navigation from campus-level overview down to millimeter-precision schematics.