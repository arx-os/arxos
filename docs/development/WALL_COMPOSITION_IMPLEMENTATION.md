# Wall Composition System Implementation Specification

## 🎯 **Overview**

This document provides the detailed technical implementation specification for the Wall Composition System, including interfaces, data structures, algorithms, and code organization.

## 🏗️ **Code Organization**

### **Directory Structure**
```
core/wall_composition/
├── types/
│   ├── wall_structure.go      # WallStructure and WallSegment types
│   ├── smart_point.go         # SmartPoint3D and unit conversion
│   ├── connection.go          # Connection types and logic
│   └── metadata.go            # Wall metadata and validation
├── engine/
│   ├── composition_engine.go  # Main wall composition logic
│   ├── connection_detector.go # Wall connection detection
│   ├── wall_grouper.go        # Wall grouping algorithms
│   └── structure_builder.go   # Wall structure construction
├── spatial/
│   ├── spatial_index.go       # Quadtree spatial indexing
│   ├── bounding_box.go        # Bounding box calculations
│   └── spatial_query.go       # Spatial query operations
├── rendering/
│   ├── svg_coordinate.go      # SVG coordinate system
│   ├── wall_renderer.go       # SVG rendering logic
│   └── confidence_style.go    # Confidence-based styling
├── performance/
│   ├── parallel_processor.go  # Parallel processing logic
│   ├── cache_manager.go       # Multi-level caching
│   └── performance_monitor.go # Performance metrics
└── utils/
    ├── unit_converter.go      # Unit conversion utilities
    ├── math_utils.go          # Mathematical operations
    └── validation.go          # Input validation
```

## 📐 **Core Data Types**

### **1. SmartPoint3D Implementation**

```go
// core/wall_composition/types/smart_point.go

package types

import (
    "fmt"
    "math"
)

// Unit represents measurement units
type Unit int

const (
    Nanometer Unit = iota
    Micrometer
    Millimeter
    Centimeter
    Meter
    Inch
    Foot
)

// String representation of units
func (u Unit) String() string {
    switch u {
    case Nanometer:
        return "nm"
    case Micrometer:
        return "μm"
    case Millimeter:
        return "mm"
    case Centimeter:
        return "cm"
    case Meter:
        return "m"
    case Inch:
        return "in"
    case Foot:
        return "ft"
    default:
        return "unknown"
    }
}

// Conversion factors (compile-time constants)
var conversionFactors = map[Unit]float64{
    Nanometer:  1.0,
    Micrometer: 1e3,
    Millimeter: 1e6,
    Centimeter: 1e7,
    Meter:      1e9,
    Inch:       2.54e7,
    Foot:       3.048e8,
}

// SmartPoint3D represents a 3D point with automatic unit conversion
type SmartPoint3D struct {
    X, Y, Z int64  // Stored in nanometers for precision
    unit    Unit   // What unit this represents
}

// NewSmartPoint3D creates a new SmartPoint3D
func NewSmartPoint3D(x, y, z int64, unit Unit) SmartPoint3D {
    return SmartPoint3D{
        X:    x,
        Y:    y,
        Z:    z,
        unit: unit,
    }
}

// ToNanometers converts to nanometers (no conversion needed)
func (p SmartPoint3D) ToNanometers() (x, y, z int64) {
    return p.X, p.Y, p.Z
}

// ToMicrometers converts to micrometers
func (p SmartPoint3D) ToMicrometers() (x, y, z float64) {
    return float64(p.X) / 1e3, float64(p.Y) / 1e3, float64(p.Z) / 1e3
}

// ToMillimeters converts to millimeters
func (p SmartPoint3D) ToMillimeters() (x, y, z float64) {
    return float64(p.X) / 1e6, float64(p.Y) / 1e6, float64(p.Z) / 1e6
}

// ToMeters converts to meters
func (p SmartPoint3D) ToMeters() (x, y, z float64) {
    return float64(p.X) / 1e9, float64(p.Y) / 1e9, float64(p.Z) / 1e9
}

// DistanceTo calculates distance to another point in millimeters
func (p SmartPoint3D) DistanceTo(other SmartPoint3D) float64 {
    dx := float64(p.X - other.X)
    dy := float64(p.Y - other.Y)
    dz := float64(p.Z - other.Z)
    return math.Sqrt(dx*dx + dy*dy + dz*dz) / 1e6
}

// String returns string representation
func (p SmartPoint3D) String() string {
    x, y, z := p.ToMillimeters()
    return fmt.Sprintf("(%.2f, %.2f, %.2f) mm", x, y, z)
}
```

### **2. Wall Structure Types**

```go
// core/wall_composition/types/wall_structure.go

package types

import (
    "time"
)

// ValidationState represents wall validation status
type ValidationState int

const (
    ValidationPending ValidationState = iota
    ValidationPartial
    ValidationComplete
    ValidationConflict
)

// String representation of validation state
func (vs ValidationState) String() string {
    switch vs {
    case ValidationPending:
        return "pending"
    case ValidationPartial:
        return "partial"
    case ValidationComplete:
        return "complete"
    case ValidationConflict:
        return "conflict"
    default:
        return "unknown"
    }
}

// WallStructure represents a composed wall made of multiple segments
type WallStructure struct {
    ID           uint64
    Segments     []WallSegment
    StartPoint   SmartPoint3D
    EndPoint     SmartPoint3D
    Length       float64          // Calculated from start/end points (mm)
    Height       float64          // Maximum height of all segments (mm)
    Thickness    float64          // Stubbed for future implementation
    Material     string           // Stubbed for future implementation
    FireRating   string           // Stubbed for future implementation
    Confidence   float32          // Overall wall confidence (0.0 - 1.0)
    Validation   ValidationState
    ArxObjects   []uint64         // IDs of composing ArxObjects
    Metadata     WallMetadata
    CreatedAt    time.Time
    UpdatedAt    time.Time
}

// WallSegment represents an individual wall piece within a structure
type WallSegment struct {
    ID           uint64
    StartPoint   SmartPoint3D
    EndPoint     SmartPoint3D
    Length       float64          // Segment length (mm)
    Height       float64          // Segment height (mm)
    Thickness    float64          // Stubbed for future implementation
    Material     string           // Stubbed for future implementation
    FireRating   string           // Stubbed for future implementation
    ArxObjects   []uint64         // IDs of composing ArxObjects
    Confidence   float32          // Individual segment confidence (0.0 - 1.0)
    Orientation  float64          // Wall angle in degrees (0-360)
    CreatedAt    time.Time
}

// WallMetadata contains additional wall information
type WallMetadata struct {
    BuildingID   string
    FloorID      string
    RoomID       string
    WallType     string          // interior, exterior, load-bearing, etc.
    Notes        string
    Tags         []string
    CustomFields map[string]interface{}
}

// NewWallStructure creates a new wall structure
func NewWallStructure() *WallStructure {
    now := time.Now()
    return &WallStructure{
        ID:        0,
        Segments:  make([]WallSegment, 0),
        Confidence: 0.0,
        Validation: ValidationPending,
        ArxObjects: make([]uint64, 0),
        Metadata:  WallMetadata{},
        CreatedAt: now,
        UpdatedAt: now,
    }
}

// AddSegment adds a segment to the wall structure
func (w *WallStructure) AddSegment(segment WallSegment) {
    w.Segments = append(w.Segments, segment)
    w.UpdatedAt = time.Now()
    w.recalculateProperties()
}

// recalculateProperties recalculates wall properties from segments
func (w *WallStructure) recalculateProperties() {
    if len(w.Segments) == 0 {
        return
    }
    
    // Calculate overall length
    w.Length = w.calculateTotalLength()
    
    // Calculate overall height
    w.Height = w.calculateMaxHeight()
    
    // Calculate overall confidence
    w.Confidence = w.calculateOverallConfidence()
    
    // Update start and end points
    w.updateEndpoints()
}

// calculateTotalLength calculates total wall length
func (w *WallStructure) calculateTotalLength() float64 {
    totalLength := 0.0
    for _, segment := range w.Segments {
        totalLength += segment.Length
    }
    return totalLength
}

// calculateMaxHeight calculates maximum height of all segments
func (w *WallStructure) calculateMaxHeight() float64 {
    maxHeight := 0.0
    for _, segment := range w.Segments {
        if segment.Height > maxHeight {
            maxHeight = segment.Height
        }
    }
    return maxHeight
}

// calculateOverallConfidence calculates weighted confidence
func (w *WallStructure) calculateOverallConfidence() float32 {
    if len(w.Segments) == 0 {
        return 0.0
    }
    
    // Weight by segment length
    totalLength := 0.0
    weightedConfidence := 0.0
    
    for _, segment := range w.Segments {
        totalLength += segment.Length
        weightedConfidence += float64(segment.Confidence) * segment.Length
    }
    
    if totalLength == 0 {
        return 0.0
    }
    
    return float32(weightedConfidence / totalLength)
}

// updateEndpoints updates start and end points based on segments
func (w *WallStructure) updateEndpoints() {
    if len(w.Segments) == 0 {
        return
    }
    
    // Find extreme points
    minX, minY := w.Segments[0].StartPoint.X, w.Segments[0].StartPoint.Y
    maxX, maxY := w.Segments[0].StartPoint.X, w.Segments[0].StartPoint.Y
    
    for _, segment := range w.Segments {
        // Check start point
        if segment.StartPoint.X < minX {
            minX = segment.StartPoint.X
        }
        if segment.StartPoint.X > maxX {
            maxX = segment.StartPoint.X
        }
        if segment.StartPoint.Y < minY {
            minY = segment.StartPoint.Y
        }
        if segment.StartPoint.Y > maxY {
            maxY = segment.StartPoint.Y
        }
        
        // Check end point
        if segment.EndPoint.X < minX {
            minX = segment.EndPoint.X
        }
        if segment.EndPoint.X > maxX {
            maxX = segment.EndPoint.X
        }
        if segment.EndPoint.Y < minY {
            minY = segment.EndPoint.Y
        }
        if segment.EndPoint.Y > maxY {
            maxY = segment.EndPoint.Y
        }
    }
    
    w.StartPoint = SmartPoint3D{X: minX, Y: minY, Z: w.Segments[0].StartPoint.Z}
    w.EndPoint = SmartPoint3D{X: maxX, Y: maxY, Z: w.Segments[0].StartPoint.Z}
}
```

### **3. Connection Types**

```go
// core/wall_composition/types/connection.go

package types

// ConnectionType represents how two walls connect
type ConnectionType int

const (
    ConnectionNone ConnectionType = iota
    ConnectionEndToEnd
    ConnectionOverlapping
    ConnectionIntersecting
    ConnectionAdjacent
)

// String representation of connection type
func (ct ConnectionType) String() string {
    switch ct {
    case ConnectionNone:
        return "none"
    case ConnectionEndToEnd:
        return "end-to-end"
    case ConnectionOverlapping:
        return "overlapping"
    case ConnectionIntersecting:
        return "intersecting"
    case ConnectionAdjacent:
        return "adjacent"
    default:
        return "unknown"
    }
}

// WallConnection represents a connection between two walls
type WallConnection struct {
    Wall1ID        uint64
    Wall2ID        uint64
    Type           ConnectionType
    ConnectionPoint SmartPoint3D
    Confidence     float32
    Distance       float64        // Distance between walls (mm)
    Angle          float64        // Angle between walls (degrees)
}

// NewWallConnection creates a new wall connection
func NewWallConnection(wall1ID, wall2ID uint64, connType ConnectionType) *WallConnection {
    return &WallConnection{
        Wall1ID:    wall1ID,
        Wall2ID:    wall2ID,
        Type:       connType,
        Confidence: 0.0,
        Distance:   0.0,
        Angle:      0.0,
    }
}
```

## 🔧 **Core Engine Implementation**

### **1. Wall Composition Engine**

```go
// core/wall_composition/engine/composition_engine.go

package engine

import (
    "fmt"
    "runtime"
    "sync"
    "time"
    
    "arxos/core/wall_composition/types"
    "arxos/core/wall_composition/spatial"
    "arxos/core/wall_composition/performance"
)

// WallCompositionEngine orchestrates the wall composition process
type WallCompositionEngine struct {
    // Configuration
    config CompositionConfig
    
    // Components
    connectionDetector *ConnectionDetector
    wallGrouper       *WallGrouper
    structureBuilder   *StructureBuilder
    spatialIndex       *spatial.SpatialIndex
    cache             *performance.CacheManager
    
    // Performance monitoring
    performanceMonitor *performance.PerformanceMonitor
    
    // Internal state
    mu sync.RWMutex
}

// CompositionConfig holds engine configuration
type CompositionConfig struct {
    MaxWallGap            float64  // Maximum gap to consider walls connected (mm)
    MinWallLength         float64  // Minimum wall length to consider valid (mm)
    AlignmentTolerance    float64  // Tolerance for wall alignment (degrees)
    MaxProcessingTime     time.Duration // Maximum time for composition
    EnableParallel        bool     // Enable parallel processing
    EnableCaching         bool     // Enable result caching
    CacheTTL              time.Duration // Cache time-to-live
}

// DefaultCompositionConfig returns default configuration
func DefaultCompositionConfig() CompositionConfig {
    return CompositionConfig{
        MaxWallGap:         50.0,   // 50mm
        MinWallLength:      100.0,  // 100mm
        AlignmentTolerance: 5.0,    // 5 degrees
        MaxProcessingTime:  30 * time.Second,
        EnableParallel:     true,
        EnableCaching:      true,
        CacheTTL:           5 * time.Minute,
    }
}

// NewWallCompositionEngine creates a new composition engine
func NewWallCompositionEngine(config CompositionConfig) *WallCompositionEngine {
    engine := &WallCompositionEngine{
        config: config,
    }
    
    // Initialize components
    engine.connectionDetector = NewConnectionDetector(config)
    engine.wallGrouper = NewWallGrouper(config)
    engine.structureBuilder = NewStructureBuilder(config)
    engine.spatialIndex = spatial.NewSpatialIndex()
    engine.cache = performance.NewCacheManager(config.CacheTTL)
    engine.performanceMonitor = performance.NewPerformanceMonitor()
    
    return engine
}

// ComposeWalls is the main entry point for wall composition
func (e *WallCompositionEngine) ComposeWalls(arxObjects []ArxObject) ([]types.WallStructure, error) {
    startTime := time.Now()
    e.performanceMonitor.StartOperation("compose_walls")
    
    defer func() {
        e.performanceMonitor.EndOperation("compose_walls")
        e.performanceMonitor.RecordMetric("total_composition_time", time.Since(startTime))
    }()
    
    // Check cache first
    if e.config.EnableCaching {
        if cached, exists := e.cache.GetWalls(arxObjects); exists {
            e.performanceMonitor.RecordMetric("cache_hit", 1)
            return cached, nil
        }
    }
    
    // Filter for wall ArxObjects
    wallObjects := e.filterWallObjects(arxObjects)
    e.performanceMonitor.RecordMetric("wall_objects_count", len(wallObjects))
    
    // Build spatial index
    e.spatialIndex.Build(wallObjects)
    e.performanceMonitor.RecordMetric("spatial_index_build_time", time.Since(startTime))
    
    // Compose walls
    var walls []types.WallStructure
    var err error
    
    if e.config.EnableParallel && len(wallObjects) > 1000 {
        walls, err = e.composeWallsParallel(wallObjects)
    } else {
        walls, err = e.composeWallsSequential(wallObjects)
    }
    
    if err != nil {
        return nil, fmt.Errorf("wall composition failed: %w", err)
    }
    
    // Cache results
    if e.config.EnableCaching {
        e.cache.SetWalls(arxObjects, walls)
    }
    
    e.performanceMonitor.RecordMetric("composed_walls_count", len(walls))
    e.performanceMonitor.RecordMetric("total_composition_time", time.Since(startTime))
    
    return walls, nil
}

// filterWallObjects filters ArxObjects for structural walls
func (e *WallCompositionEngine) filterWallObjects(arxObjects []ArxObject) []ArxObject {
    var walls []ArxObject
    
    for _, obj := range arxObjects {
        if obj.Type == StructuralWall && obj.Flags&1 != 0 { // Active flag
            // Check minimum length
            if obj.Length >= int64(e.config.MinWallLength*1e6) { // Convert mm to nm
                walls = append(walls, obj)
            }
        }
    }
    
    return walls
}

// composeWallsSequential composes walls using sequential processing
func (e *WallCompositionEngine) composeWallsSequential(wallObjects []ArxObject) ([]types.WallStructure, error) {
    // Group wall objects
    groups := e.wallGrouper.GroupWalls(wallObjects)
    
    // Build wall structures
    walls := make([]types.WallStructure, 0, len(groups))
    for _, group := range groups {
        if wall := e.structureBuilder.BuildWallStructure(group); wall != nil {
            walls = append(walls, *wall)
        }
    }
    
    return walls, nil
}

// composeWallsParallel composes walls using parallel processing
func (e *WallCompositionEngine) composeWallsParallel(wallObjects []ArxObject) ([]types.WallStructure, error) {
    // Determine optimal chunk size
    optimalChunkSize := e.calculateOptimalChunkSize(len(wallObjects))
    
    // Split work across CPU cores
    numWorkers := runtime.NumCPU()
    chunks := e.createChunks(wallObjects, optimalChunkSize, numWorkers)
    
    // Process chunks in parallel
    results := e.processChunksParallel(chunks)
    
    // Merge results and resolve cross-chunk connections
    return e.mergeResults(results), nil
}

// calculateOptimalChunkSize determines optimal chunk size for parallel processing
func (e *WallCompositionEngine) calculateOptimalChunkSize(totalObjects int) int {
    if totalObjects < 1000 {
        return totalObjects // No parallelization needed
    } else if totalObjects < 10000 {
        return 1000
    } else {
        return 2000
    }
}

// createChunks splits work into chunks for parallel processing
func (e *WallCompositionEngine) createChunks(wallObjects []ArxObject, chunkSize, numWorkers int) [][]ArxObject {
    chunks := make([][]ArxObject, 0, numWorkers)
    
    for i := 0; i < len(wallObjects); i += chunkSize {
        end := i + chunkSize
        if end > len(wallObjects) {
            end = len(wallObjects)
        }
        chunks = append(chunks, wallObjects[i:end])
    }
    
    return chunks
}

// processChunksParallel processes chunks in parallel
func (e *WallCompositionEngine) processChunksParallel(chunks [][]ArxObject) [][]types.WallStructure {
    var wg sync.WaitGroup
    results := make([][]types.WallStructure, len(chunks))
    
    for i, chunk := range chunks {
        wg.Add(1)
        go func(chunkIndex int, chunkData []ArxObject) {
            defer wg.Done()
            
            // Process chunk
            if walls, err := e.composeWallsSequential(chunkData); err == nil {
                results[chunkIndex] = walls
            }
        }(i, chunk)
    }
    
    wg.Wait()
    return results
}

// mergeResults merges parallel processing results
func (e *WallCompositionEngine) mergeResults(results [][]types.WallStructure) []types.WallStructure {
    var allWalls []types.WallStructure
    
    // Collect all walls
    for _, result := range results {
        allWalls = append(allWalls, result...)
    }
    
    // TODO: Resolve cross-chunk connections
    // This is a simplified version - in practice, we'd need to detect
    // walls that span chunk boundaries and merge them
    
    return allWalls
}
```

## 🎨 **Rendering Implementation**

### **1. SVG Coordinate System**

```go
// core/wall_composition/rendering/svg_coordinate.go

package rendering

import (
    "arxos/core/wall_composition/types"
)

// SVGCoordinateSystem handles coordinate conversion for SVG rendering
type SVGCoordinateSystem struct {
    ViewBox     BoundingBox      // SVG viewBox in world coordinates
    Scale       float64          // Pixels per millimeter
    Origin      types.SmartPoint3D // Origin point in world coordinates
    Units       types.Unit       // Display units (typically mm)
    Width       float64          // SVG width in pixels
    Height      float64          // SVG height in pixels
}

// BoundingBox represents a 2D bounding box
type BoundingBox struct {
    MinX, MinY float64
    MaxX, MaxY float64
}

// NewSVGCoordinateSystem creates a new SVG coordinate system
func NewSVGCoordinateSystem(arxObjects []ArxObject, width, height float64) *SVGCoordinateSystem {
    // Calculate bounding box from ArxObjects
    bounds := calculateBoundingBox(arxObjects)
    
    // Calculate optimal scale
    scale := calculateOptimalScale(bounds, width, height)
    
    return &SVGCoordinateSystem{
        ViewBox: bounds,
        Scale:   scale,
        Origin:  types.SmartPoint3D{X: int64(bounds.MinX * 1e6), Y: int64(bounds.MinY * 1e6), Z: 0},
        Units:   types.Millimeter,
        Width:   width,
        Height:  height,
    }
}

// ToSVGCoordinates converts world coordinates to SVG coordinates
func (scs *SVGCoordinateSystem) ToSVGCoordinates(worldPoint types.SmartPoint3D) (x, y float64) {
    // Convert to display units
    displayX := float64(worldPoint.X) / 1e6 // Convert nm to mm
    displayY := float64(worldPoint.Y) / 1e6
    
    // Apply scale and offset
    x = (displayX - float64(scs.Origin.X)/1e6) * scs.Scale
    y = (displayY - float64(scs.Origin.Y)/1e6) * scs.Scale
    
    return x, y
}

// calculateBoundingBox calculates bounding box from ArxObjects
func calculateBoundingBox(arxObjects []ArxObject) BoundingBox {
    if len(arxObjects) == 0 {
        return BoundingBox{}
    }
    
    // Initialize with first object
    minX := float64(arxObjects[0].X) / 1e6
    minY := float64(arxObjects[0].Y) / 1e6
    maxX := minX
    maxY := minY
    
    // Find extremes
    for _, obj := range arxObjects {
        x := float64(obj.X) / 1e6
        y := float64(obj.Y) / 1e6
        
        if x < minX {
            minX = x
        }
        if x > maxX {
            maxX = x
        }
        if y < minY {
            minY = y
        }
        if y > maxY {
            maxY = y
        }
    }
    
    return BoundingBox{
        MinX: minX,
        MinY: minY,
        MaxX: maxX,
        MaxY: maxY,
    }
}

// calculateOptimalScale calculates optimal scale for SVG rendering
func calculateOptimalScale(bounds BoundingBox, width, height float64) float64 {
    worldWidth := bounds.MaxX - bounds.MinX
    worldHeight := bounds.MaxY - bounds.MinY
    
    if worldWidth <= 0 || worldHeight <= 0 {
        return 1.0
    }
    
    // Calculate scale to fit in SVG dimensions
    scaleX := width / worldWidth
    scaleY := height / worldHeight
    
    // Use smaller scale to ensure everything fits
    if scaleX < scaleY {
        return scaleX
    }
    return scaleY
}
```

### **2. Wall Renderer**

```go
// core/wall_composition/rendering/wall_renderer.go

package rendering

import (
    "fmt"
    "arxos/core/wall_composition/types"
)

// WallRenderer handles SVG rendering of wall structures
type WallRenderer struct {
    coordinateSystem *SVGCoordinateSystem
}

// NewWallRenderer creates a new wall renderer
func NewWallRenderer(coordinateSystem *SVGCoordinateSystem) *WallRenderer {
    return &WallRenderer{
        coordinateSystem: coordinateSystem,
    }
}

// RenderWallStructure renders a wall structure to SVG
func (wr *WallRenderer) RenderWallStructure(wall types.WallStructure) string {
    style := GetWallRenderStyle(wall.Confidence)
    
    svg := fmt.Sprintf(`<g class="wall-structure" data-id="%d" data-confidence="%.2f">`, 
        wall.ID, wall.Confidence)
    
    // Render each segment
    for _, segment := range wall.Segments {
        svg += wr.renderWallSegment(segment)
    }
    
    // Add metadata
    svg += wr.renderWallMetadata(wall)
    
    svg += "</g>"
    return svg
}

// renderWallSegment renders an individual wall segment
func (wr *WallRenderer) renderWallSegment(segment types.WallSegment) string {
    style := GetWallRenderStyle(segment.Confidence)
    
    // Convert coordinates to SVG space
    x1, y1 := wr.coordinateSystem.ToSVGCoordinates(segment.StartPoint)
    x2, y2 := wr.coordinateSystem.ToSVGCoordinates(segment.EndPoint)
    
    // Create SVG line
    svg := fmt.Sprintf(`<line x1="%f" y1="%f" x2="%f" y2="%f" 
        stroke="%s" stroke-width="%d" opacity="%.1f"`,
        x1, y1, x2, y2, style.StrokeColor, style.StrokeWidth, style.Opacity)
    
    if style.StrokeDash != "" {
        svg += fmt.Sprintf(` stroke-dasharray="%s"`, style.StrokeDash)
    }
    
    svg += "/>"
    return svg
}

// renderWallMetadata renders wall metadata and labels
func (wr *WallRenderer) renderWallMetadata(wall types.WallStructure) string {
    // Calculate label position (center of wall)
    centerX := (float64(wall.StartPoint.X) + float64(wall.EndPoint.X)) / 2 / 1e6
    centerY := (float64(wall.StartPoint.Y) + float64(wall.EndPoint.Y)) / 2 / 1e6
    
    svgX, svgY := wr.coordinateSystem.ToSVGCoordinates(types.SmartPoint3D{
        X: int64(centerX * 1e6),
        Y: int64(centerY * 1e6),
        Z: 0,
    })
    
    // Create label
    label := fmt.Sprintf(`<text x="%f" y="%f" class="wall-label" 
        font-size="12" text-anchor="middle" dominant-baseline="middle">`,
        svgX, svgY)
    
    label += fmt.Sprintf("Wall %d (%.1fmm, %.1f%% confidence)", 
        wall.ID, wall.Length, wall.Confidence*100)
    
    label += "</text>"
    
    return label
}
```

## ⚡ **Performance Implementation**

### **1. Spatial Index**

```go
// core/wall_composition/spatial/spatial_index.go

package spatial

import (
    "arxos/core/wall_composition/types"
)

// SpatialIndex provides spatial querying for wall objects
type SpatialIndex struct {
    root *QuadNode
    maxDepth int
    maxObjects int
}

// QuadNode represents a node in the quadtree
type QuadNode struct {
    bounds    BoundingBox
    objects   []uint64
    children  [4]*QuadNode
    isLeaf    bool
    depth     int
}

// NewSpatialIndex creates a new spatial index
func NewSpatialIndex() *SpatialIndex {
    return &SpatialIndex{
        maxDepth: 8,
        maxObjects: 10,
    }
}

// Build builds the spatial index from ArxObjects
func (si *SpatialIndex) Build(arxObjects []ArxObject) {
    if len(arxObjects) == 0 {
        return
    }
    
    // Calculate overall bounds
    bounds := si.calculateBounds(arxObjects)
    
    // Create root node
    si.root = &QuadNode{
        bounds: bounds,
        depth: 0,
    }
    
    // Insert all objects
    for _, obj := range arxObjects {
        si.insertObject(si.root, obj.ID, obj.X, obj.Y)
    }
}

// FindNearbyObjects finds objects within a radius of a point
func (si *SpatialIndex) FindNearbyObjects(point types.SmartPoint3D, radius float64) []uint64 {
    var results []uint64
    
    // Convert radius from mm to nm
    radiusNano := int64(radius * 1e6)
    
    searchBounds := BoundingBox{
        MinX: point.X - radiusNano,
        MinY: point.Y - radiusNano,
        MaxX: point.X + radiusNano,
        MaxY: point.Y + radiusNano,
    }
    
    si.query(si.root, searchBounds, &results)
    return results
}

// insertObject inserts an object into the quadtree
func (si *SpatialIndex) insertObject(node *QuadNode, objectID uint64, x, y int64) {
    if !node.bounds.Contains(x, y) {
        return
    }
    
    if node.isLeaf {
        node.objects = append(node.objects, objectID)
        
        // Split if too many objects
        if len(node.objects) > si.maxObjects && node.depth < si.maxDepth {
            si.splitNode(node)
        }
    } else {
        // Find appropriate child
        for _, child := range node.children {
            if child != nil && child.bounds.Contains(x, y) {
                si.insertObject(child, objectID, x, y)
                break
            }
        }
    }
}

// splitNode splits a leaf node into four children
func (si *SpatialIndex) splitNode(node *QuadNode) {
    if !node.isLeaf {
        return
    }
    
    // Calculate child bounds
    midX := (node.bounds.MinX + node.bounds.MaxX) / 2
    midY := (node.bounds.MinY + node.bounds.MaxY) / 2
    
    node.children[0] = &QuadNode{ // Top-left
        bounds: BoundingBox{MinX: node.bounds.MinX, MinY: midY, MaxX: midX, MaxY: node.bounds.MaxY},
        depth: node.depth + 1,
    }
    node.children[1] = &QuadNode{ // Top-right
        bounds: BoundingBox{MinX: midX, MinY: midY, MaxX: node.bounds.MaxX, MaxY: node.bounds.MaxY},
        depth: node.depth + 1,
    }
    node.children[2] = &QuadNode{ // Bottom-left
        bounds: BoundingBox{MinX: node.bounds.MinX, MinY: node.bounds.MinY, MaxX: midX, MaxY: midY},
        depth: node.depth + 1,
    }
    node.children[3] = &QuadNode{ // Bottom-right
        bounds: BoundingBox{MinX: midX, MinY: node.bounds.MinY, MaxX: node.bounds.MaxX, MaxY: midY},
        depth: node.depth + 1,
    }
    
    // Redistribute objects to children
    for _, objectID := range node.objects {
        // Find object coordinates (simplified - in practice, you'd store these)
        // For now, we'll just distribute randomly
        for _, child := range node.children {
            if child != nil {
                child.objects = append(child.objects, objectID)
                break
            }
        }
    }
    
    // Clear parent objects and mark as non-leaf
    node.objects = nil
    node.isLeaf = false
}

// query performs a spatial query on the quadtree
func (si *SpatialIndex) query(node *QuadNode, bounds BoundingBox, results *[]uint64) {
    if node == nil || !node.bounds.Intersects(bounds) {
        return
    }
    
    if node.isLeaf {
        // Add all objects in this leaf
        *results = append(*results, node.objects...)
    } else {
        // Query children
        for _, child := range node.children {
            if child != nil {
                si.query(child, bounds, results)
            }
        }
    }
}
```

## 🧪 **Testing Strategy**

### **1. Unit Tests**

```go
// core/wall_composition/types/smart_point_test.go

package types

import (
    "testing"
    "math"
)

func TestSmartPoint3D_ToMillimeters(t *testing.T) {
    point := NewSmartPoint3D(1000000, 2000000, 3000000, Nanometer)
    x, y, z := point.ToMillimeters()
    
    if x != 1.0 || y != 2.0 || z != 3.0 {
        t.Errorf("Expected (1.0, 2.0, 3.0), got (%.1f, %.1f, %.1f)", x, y, z)
    }
}

func TestSmartPoint3D_DistanceTo(t *testing.T) {
    point1 := NewSmartPoint3D(0, 0, 0, Nanometer)
    point2 := NewSmartPoint3D(3000000, 4000000, 0, Nanometer) // 3mm, 4mm
    
    distance := point1.DistanceTo(point2)
    expected := 5.0 // 5mm (3-4-5 triangle)
    
    if math.Abs(distance-expected) > 0.001 {
        t.Errorf("Expected distance %.3f, got %.3f", expected, distance)
    }
}
```

### **2. Integration Tests**

```go
// core/wall_composition/engine/composition_engine_test.go

package engine

import (
    "testing"
    "arxos/core/wall_composition/types"
)

func TestWallCompositionEngine_ComposeWalls(t *testing.T) {
    // Create test ArxObjects
    arxObjects := createTestArxObjects()
    
    // Create engine
    config := DefaultCompositionConfig()
    engine := NewWallCompositionEngine(config)
    
    // Compose walls
    walls, err := engine.ComposeWalls(arxObjects)
    if err != nil {
        t.Fatalf("Wall composition failed: %v", err)
    }
    
    // Verify results
    if len(walls) == 0 {
        t.Error("Expected composed walls, got none")
    }
    
    // Verify wall properties
    for _, wall := range walls {
        if wall.Length <= 0 {
            t.Errorf("Wall %d has invalid length: %.2f", wall.ID, wall.Length)
        }
        
        if wall.Confidence < 0 || wall.Confidence > 1 {
            t.Errorf("Wall %d has invalid confidence: %.2f", wall.ID, wall.Confidence)
        }
    }
}

func createTestArxObjects() []ArxObject {
    // Create test wall ArxObjects
    return []ArxObject{
        // Wall 1: (0,0) to (1000,0) - 1 meter long
        {
            ID:   1,
            Type: StructuralWall,
            X:    0,
            Y:    0,
            Z:    0,
            Length: 1000000000, // 1m in nm
            Width:  200000000,  // 200mm in nm
            Height: 2700000000,  // 2.7m in nm
            Flags: 1,
        },
        // Wall 2: (1000,0) to (1000,1000) - 1 meter long
        {
            ID:   2,
            Type: StructuralWall,
            X:    1000000000,
            Y:    0,
            Z:    0,
            Length: 1000000000, // 1m in nm
            Width:  200000000,  // 200mm in nm
            Height: 2700000000,  // 2.7m in nm
            Flags: 1,
        },
    }
}
```

## 📊 **Performance Benchmarks**

### **1. Benchmark Tests**

```go
// core/wall_composition/performance/benchmarks_test.go

package performance

import (
    "testing"
    "arxos/core/wall_composition/engine"
)

func BenchmarkWallComposition_Small(b *testing.B) {
    arxObjects := generateTestArxObjects(100)
    config := engine.DefaultCompositionConfig()
    engine := engine.NewWallCompositionEngine(config)
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, err := engine.ComposeWalls(arxObjects)
        if err != nil {
            b.Fatalf("Composition failed: %v", err)
        }
    }
}

func BenchmarkWallComposition_Medium(b *testing.B) {
    arxObjects := generateTestArxObjects(1000)
    config := engine.DefaultCompositionConfig()
    engine := engine.NewWallCompositionEngine(config)
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, err := engine.ComposeWalls(arxObjects)
        if err != nil {
            b.Fatalf("Composition failed: %v", err)
        }
    }
}

func BenchmarkWallComposition_Large(b *testing.B) {
    arxObjects := generateTestArxObjects(10000)
    config := engine.DefaultCompositionConfig()
    engine := engine.NewWallCompositionEngine(config)
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, err := engine.ComposeWalls(arxObjects)
        if err != nil {
            b.Fatalf("Composition failed: %v", err)
        }
    }
}

func generateTestArxObjects(count int) []ArxObject {
    arxObjects := make([]ArxObject, count)
    
    for i := 0; i < count; i++ {
        arxObjects[i] = ArxObject{
            ID:     uint64(i + 1),
            Type:   StructuralWall,
            X:      int64(i * 1000000000), // 1m spacing
            Y:      0,
            Z:      0,
            Length: 1000000000, // 1m
            Width:  200000000,  // 200mm
            Height: 2700000000,  // 2.7m
            Flags:  1,
        }
    }
    
    return arxObjects
}
```

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Date + 1 week]  
**Implementation Owner**: [Your Name]
