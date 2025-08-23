# Wall Composition System Architecture

## 🎯 **Overview**

This document outlines the architecture, design decisions, and implementation plan for the ArxObject Wall Composition System. The system transforms individual wall ArxObjects extracted from PDF floor plans into composed wall structures that can be rendered as BIM elements.

## 🏗️ **System Architecture**

### **High-Level Architecture**
```
PDF Floor Plan → AI Extraction → Wall ArxObjects → Wall Composition Engine → Wall Structures → SVG Rendering → BIM Visualization
```

### **Core Components**
1. **WallCompositionEngine** - Main orchestration and composition logic
2. **WallStructure** - Composed wall representation
3. **WallSegment** - Individual wall pieces within a structure
4. **SpatialIndex** - Optimized spatial queries for wall connection detection
5. **CoordinateSystem** - Unit-aware coordinate handling
6. **ConfidenceRenderer** - Confidence-based visual styling

## 🧬 **Design Philosophy**

### **Core Principles**
1. **ArxObject-First**: Walls are composed from ArxObjects, not created independently
2. **Confidence-Aware**: All composition decisions consider confidence scores
3. **Performance-Optimized**: Spatial indexing and parallel processing for large datasets
4. **Unit-Agnostic**: Internal calculations use nanometer precision, external interfaces use appropriate units
5. **Validation-Ready**: Designed for user validation and confidence improvement

### **Key Design Decisions**
1. **Wall Connection Logic**: Alignment + gap detection for accurate composition
2. **Coordinate System**: Template-based unit conversion for efficiency
3. **SVG Integration**: Direct coordinate mapping for real-world scale representation
4. **Performance**: Spatial indexing + parallel processing for scalability

## 📐 **Data Models**

### **WallStructure**
```go
type WallStructure struct {
    ID           uint64
    Segments     []WallSegment
    StartPoint   SmartPoint3D
    EndPoint     SmartPoint3D
    Length       float64          // Calculated from start/end points
    Height       float64
    Thickness    float64          // Stubbed for future implementation
    Material     string           // Stubbed for future implementation
    FireRating   string           // Stubbed for future implementation
    Confidence   float32          // Overall wall confidence
    Validation   ValidationState
    ArxObjects   []uint64         // IDs of composing ArxObjects
    Metadata     WallMetadata
}
```

### **WallSegment**
```go
type WallSegment struct {
    ID           uint64
    StartPoint   SmartPoint3D
    EndPoint     SmartPoint3D
    Length       float64
    Height       float64
    Thickness    float64          // Stubbed
    Material     string           // Stubbed
    FireRating   string           // Stubbed
    ArxObjects   []uint64         // IDs of composing ArxObjects
    Confidence   float32          // Individual segment confidence
    Orientation  float64          // Wall angle in degrees
}
```

### **SmartPoint3D**
```go
type SmartPoint3D struct {
    X, Y, Z int64  // Stored in nanometers for precision
    unit    Unit   // What unit this represents
}

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
```

## 🔗 **Wall Connection Logic**

### **Connection Detection Algorithm**
```
1. Spatial Proximity Check
   - Use spatial index to find nearby walls (O(log n))
   - Filter by maximum gap tolerance (configurable, default: 50mm)

2. Alignment Validation
   - Calculate wall orientation angles
   - Check if walls are parallel (tolerance: ±5 degrees)
   - Verify walls are collinear (lie on same line)

3. Connection Classification
   - End-to-end: Walls connect at endpoints
   - Overlapping: Walls share common area
   - Intersecting: Walls cross at angles
   - Adjacent: Walls are parallel and close
```

### **Connection Types**
```go
type ConnectionType int

const (
    EndToEnd ConnectionType = iota
    Overlapping
    Intersecting
    Adjacent
    None
)

type WallConnection struct {
    Wall1ID        uint64
    Wall2ID        uint64
    Type           ConnectionType
    ConnectionPoint SmartPoint3D
    Confidence     float32
}
```

## 📏 **Coordinate System Design**

### **Unit Conversion Strategy**
```go
// Template-based unit conversion for compile-time optimization
type UnitConverter[T ~int64] struct {
    value T
    unit  Unit
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

func (uc UnitConverter[T]) To(target Unit) float64 {
    factor := conversionFactors[uc.unit] / conversionFactors[target]
    return float64(uc.value) * factor
}
```

### **Coordinate Operations**
```go
// All internal calculations use nanometers
// External interfaces convert to appropriate units
func (p *SmartPoint3D) ToMillimeters() (x, y, z float64) {
    return float64(p.X) / 1e6, float64(p.Y) / 1e6, float64(p.Z) / 1e6
}

func (p *SmartPoint3D) ToMeters() (x, y, z float64) {
    return float64(p.X) / 1e9, float64(p.Y) / 1e9, float64(p.Z) / 1e9
}

func (p *SmartPoint3D) DistanceTo(other SmartPoint3D) float64 {
    dx := float64(p.X - other.X)
    dy := float64(p.Y - other.Y)
    dz := float64(p.Z - other.Z)
    return math.Sqrt(dx*dx + dy*dy + dz*dz) / 1e6 // Return in mm
}
```

## 🎨 **SVG Integration Architecture**

### **Coordinate System Mapping**
```go
type SVGCoordinateSystem struct {
    ViewBox     BoundingBox      // SVG viewBox in world coordinates
    Scale       float64          // Pixels per millimeter
    Origin      SmartPoint3D     // Origin point in world coordinates
    Units       Unit             // Display units (typically mm)
}

// Convert world coordinates to SVG coordinates
func (scs *SVGCoordinateSystem) ToSVGCoordinates(worldPoint SmartPoint3D) (x, y float64) {
    // Convert to display units
    displayX := UnitConverter[int64]{worldPoint.X, Nanometer}.To(scs.Units)
    displayY := UnitConverter[int64]{worldPoint.Y, Nanometer}.To(scs.Units)
    
    // Apply scale and offset
    x = (displayX - float64(scs.Origin.X)/1e6) * scs.Scale
    y = (displayY - float64(scs.Origin.Y)/1e6) * scs.Scale
    
    return x, y
}
```

### **SVG Rendering Pipeline**
```go
// Wall structure to SVG
func (w *WallStructure) RenderToSVG(coordinateSystem *SVGCoordinateSystem) string {
    style := GetWallRenderStyle(w.Confidence)
    
    svg := fmt.Sprintf(`<g class="wall-structure" data-id="%d" data-confidence="%.2f">`, 
        w.ID, w.Confidence)
    
    // Render each segment
    for _, segment := range w.Segments {
        svg += segment.RenderToSVG(coordinateSystem)
    }
    
    // Add metadata
    svg += w.renderMetadata(coordinateSystem)
    
    svg += "</g>"
    return svg
}

// Confidence-based styling
func GetWallRenderStyle(confidence float32) RenderStyle {
    switch {
    case confidence <= 0.60:
        return RenderStyle{
            StrokeColor: "#FF4444",    // Red
            StrokeWidth: 3,
            StrokeDash:  "5,5",        // Dashed line
            Opacity:     0.8,
            FillColor:   "#FFEEEE",    // Light red fill
        }
    case confidence <= 0.80:
        return RenderStyle{
            StrokeColor: "#FFAA00",    // Yellow/Orange
            StrokeWidth: 2,
            Opacity:     0.9,
            FillColor:   "#FFF8E1",    // Light yellow fill
        }
    default:
        return RenderStyle{
            StrokeColor: "#44AA44",    // Green
            StrokeWidth: 2,
            Opacity:     1.0,
            FillColor:   "#E8F5E8",    // Light green fill
        }
    }
}
```

## ⚡ **Performance Architecture**

### **Spatial Indexing Strategy**
```go
// Quadtree-based spatial index for O(log n) queries
type SpatialIndex struct {
    root *QuadNode
    maxDepth int
    maxObjects int
}

type QuadNode struct {
    bounds    BoundingBox
    objects   []uint64
    children  [4]*QuadNode
    isLeaf    bool
    depth     int
}

// Spatial query optimization
func (si *SpatialIndex) FindNearbyObjects(point SmartPoint3D, radius float64) []uint64 {
    var results []uint64
    searchBounds := BoundingBox{
        MinX: point.X - int64(radius*1e6), // Convert mm to nm
        MinY: point.Y - int64(radius*1e6),
        MaxX: point.X + int64(radius*1e6),
        MaxY: point.Y + int64(radius*1e6),
    }
    
    si.root.query(searchBounds, &results)
    return results
}
```

### **Parallel Processing Strategy**
```go
// Parallel wall composition for large datasets
func (e *WallCompositionEngine) ComposeWallsParallel(arxObjects []ArxObject) []WallStructure {
    // Determine optimal chunk size based on dataset size
    optimalChunkSize := e.calculateOptimalChunkSize(len(arxObjects))
    
    // Split work across CPU cores
    numWorkers := runtime.NumCPU()
    chunks := e.createChunks(arxObjects, optimalChunkSize, numWorkers)
    
    // Process chunks in parallel
    results := e.processChunksParallel(chunks)
    
    // Merge results and resolve cross-chunk connections
    return e.mergeResults(results)
}

// Dynamic chunk sizing based on dataset characteristics
func (e *WallCompositionEngine) calculateOptimalChunkSize(totalObjects int) int {
    // Smaller chunks for complex layouts, larger for simple layouts
    if totalObjects < 1000 {
        return totalObjects // No parallelization needed
    } else if totalObjects < 10000 {
        return 1000
    } else {
        return 2000
    }
}
```

### **Caching Strategy**
```go
// Multi-level caching for wall composition results
type WallCompositionCache struct {
    // L1: In-memory cache for active sessions
    memoryCache map[string]CachedResult
    
    // L2: Persistent cache for repeated operations
    persistentCache *PersistentCache
    
    // L3: Distributed cache for multi-user scenarios
    distributedCache *DistributedCache
    
    mu    sync.RWMutex
    ttl   time.Duration
}

type CachedResult struct {
    Walls      []WallStructure
    Timestamp  time.Time
    Metadata   CacheMetadata
}

// Cache key generation based on input characteristics
func (wcc *WallCompositionCache) generateKey(arxObjects []ArxObject) string {
    // Create deterministic key from object characteristics
    hash := fnv.New64a()
    
    // Sort objects by ID for consistent hashing
    sorted := make([]ArxObject, len(arxObjects))
    copy(sorted, arxObjects)
    sort.Slice(sorted, func(i, j int) bool {
        return sorted[i].ID < sorted[j].ID
    })
    
    // Hash object characteristics
    for _, obj := range sorted {
        binary.Write(hash, binary.LittleEndian, obj.ID)
        binary.Write(hash, binary.LittleEndian, obj.X)
        binary.Write(hash, binary.LittleEndian, obj.Y)
        binary.Write(hash, binary.LittleEndian, obj.Type)
    }
    
    return fmt.Sprintf("walls_%x", hash.Sum64())
}
```

## 🔧 **Implementation Plan**

### **Phase 1: Core Infrastructure (Week 1-2)**
1. **Coordinate System Implementation**
   - Implement SmartPoint3D with unit conversion
   - Create UnitConverter template system
   - Add coordinate operation methods

2. **Basic Data Models**
   - Implement WallStructure and WallSegment
   - Create WallMetadata and related types
   - Add validation and serialization methods

3. **Spatial Index Foundation**
   - Implement basic quadtree structure
   - Add spatial query methods
   - Create bounding box calculations

### **Phase 2: Wall Composition Engine (Week 3-4)**
1. **Connection Detection**
   - Implement alignment validation
   - Add gap detection logic
   - Create connection classification system

2. **Wall Grouping**
   - Build wall grouping algorithm
   - Implement connected wall detection
   - Add confidence calculation for groups

3. **Structure Composition**
   - Create wall structure composition logic
   - Implement segment generation
   - Add overall wall property calculation

### **Phase 3: Rendering and Integration (Week 5-6)**
1. **SVG Coordinate System**
   - Implement SVGCoordinateSystem
   - Create coordinate mapping functions
   - Add viewBox and scale handling

2. **SVG Rendering**
   - Implement wall structure SVG output
   - Add confidence-based styling
   - Create metadata and labeling

3. **Integration Testing**
   - Test with existing ArxObject data
   - Validate coordinate system accuracy
   - Performance testing with large datasets

### **Phase 4: Performance Optimization (Week 7-8)**
1. **Parallel Processing**
   - Implement parallel wall composition
   - Add dynamic chunk sizing
   - Create result merging logic

2. **Advanced Caching**
   - Implement multi-level caching
   - Add cache invalidation
   - Create distributed cache support

3. **Performance Monitoring**
   - Add performance metrics
   - Implement profiling tools
   - Create optimization benchmarks

## 🧪 **Testing Strategy**

### **Unit Testing**
- Coordinate system conversions
- Wall connection detection
- Spatial indexing operations
- Confidence calculations

### **Integration Testing**
- End-to-end wall composition
- SVG rendering pipeline
- Performance under load
- Memory usage optimization

### **Validation Testing**
- Real PDF floor plan data
- Coordinate accuracy verification
- Rendering quality assessment
- User validation workflow

## 📊 **Performance Targets**

### **Wall Composition Performance**
- **Small buildings** (< 100 walls): < 100ms
- **Medium buildings** (100-1000 walls): < 500ms
- **Large buildings** (1000+ walls): < 2s

### **Memory Usage**
- **Base memory**: < 50MB for 10,000 walls
- **Scaling factor**: +5MB per 1000 additional walls
- **Peak memory**: < 2x base memory during processing

### **Rendering Performance**
- **SVG generation**: < 50ms for 1000 walls
- **Coordinate conversion**: < 10ms for 1000 points
- **Style application**: < 20ms for 1000 elements

## 🔮 **Future Enhancements**

### **Advanced Wall Features**
- Curved wall support
- Wall thickness and material properties
- Fire rating and safety features
- Acoustic and thermal properties

### **Enhanced Rendering**
- 3D wall extrusion
- Material texture mapping
- Dynamic lighting and shadows
- Interactive wall editing

### **Performance Improvements**
- GPU acceleration for large datasets
- Real-time collaboration support
- Incremental composition updates
- Advanced spatial indexing algorithms

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Next Review**: [Date + 2 weeks]  
**Architecture Owner**: [Your Name]
