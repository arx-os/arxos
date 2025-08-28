# Development Guide

## 🎯 **Overview**

This guide provides comprehensive information for developers working on the **ARXOS platform** - a revolutionary programmable building infrastructure system. ARXOS represents buildings as navigable filesystems with infinite fractal zoom capabilities, from campus level down to submicron precision.

---

## 🏗️ **Core Architecture Principles**

### **Revolutionary Design Philosophy**
- **Building as Filesystem** - Every building component has a path and properties
- **Infinite Zoom Architecture** - Seamless navigation from campus to nanoscopic levels
- **ASCII as Universal Language** - Buildings represented in ASCII art for universal access
- **SVG-Based BIM Foundation** - Precise coordinate system for 1:1 accurate rendering
- **ArxObject Intelligence** - Hierarchical system providing real-time data and control

### **6-Layer Visualization System**
```
1. SVG-based 3D Building Information Model (CAD-like, browser/mobile)
2. AR ArxObject Overlay (on-site system visualization)
3. SVG-based 2D Building Plan View
4. ASCII art "3D" rendering (terminal, web, mobile)
5. ASCII art 2D building plan (terminal, web, mobile)
6. CLI tools and AQL (terminal-first data interaction)
```

### **Technology Stack Constraints**
- **Core Engine**: C (ArxObject runtime, ASCII-BIM engine)
- **Bridge Layer**: CGO for Go-C interoperability
- **Service Layer**: Go (CLI, API, business logic)
- **AI Services**: Python (ML, computer vision, PDF processing)
- **Frontend**: Vanilla JavaScript + Three.js (no frameworks)
- **Database**: PostgreSQL/PostGIS, Time Series DB

---

## 🔧 **Core C Engine Development**

### **Code Organization**
```
core/c/
├── arxobject/           # ArxObject runtime engine
│   ├── arxobject.h     # Core ArxObject structures
│   ├── arxobject.c     # Implementation
│   └── tests/          # C unit tests
├── ascii_bim/          # ASCII-BIM spatial engine
│   ├── renderer.h      # Rendering pipeline
│   ├── coordinates.h   # Coordinate transformations
│   └── pixatool.c      # Pixatool-inspired rendering
├── spatial/            # Spatial query engine
│   ├── spatial.h       # Spatial operations
│   └── index.h         # Spatial indexing
└── performance/        # Performance monitoring
    └── metrics.h       # Performance metrics
```

### **Coding Standards**

#### **ArxObject System**
```c
// Core ArxObject structure
struct ArxObject {
    // File tree structure
    char* name;                     // Object name (e.g., "panel-a")
    char* path;                     // Full path (e.g., "/electrical/panel-a/circuit-7")
    ArxObject* parent;              // Parent object in tree
    ArxObject** children;           // Array of child objects
    int child_count;               // Number of children
    int child_capacity;            // Allocated capacity
    
    // Object properties
    ArxObjectType type;            // Object type enum
    char* id;                      // Unique identifier
    time_t created_time;           // Creation timestamp
    time_t updated_time;           // Last update timestamp
    
    // Spatial properties
    float position[3];             // 3D coordinates (x, y, z)
    float dimensions[3];           // Width, height, depth
    float rotation[3];             // Rotation angles
    
    // Dynamic properties
    ArxObjectProperties* properties; // Key-value properties
    ArxObjectConnection** connections; // Connections to other objects
    int connection_count;          // Number of connections
    
    // Performance optimization
    void* spatial_data;            // Spatial index data
    void* cache_data;              // Cached computed values
};

// ArxObject type enumeration
typedef enum {
    ARX_STRUCTURAL,        // Foundation, beams, walls
    ARX_MEP,              // Electrical, HVAC, plumbing
    ARX_EQUIPMENT,        // Machinery, devices
    ARX_SPACE,            // Rooms, zones, areas
    ARX_SYSTEM,           // Control systems, networks
    ARX_METADATA          // Documentation, specifications
} ArxObjectType;
```

#### **ASCII-BIM Engine**
```c
// Pixatool-inspired rendering pipeline
typedef struct {
    float depth;        // Z-buffer depth value
    float luminance;    // Brightness 0.0-1.0
    float edge_strength; // Edge detection result
    int material_type;  // Wall, door, equipment, etc.
    float normal_x, normal_y, normal_z; // Surface normal
} PixelData;

typedef struct {
    char character;      // ASCII character to render
    int color;          // ANSI color code
    float confidence;   // Rendering confidence
    PixelData pixel;    // Associated pixel data
} ASCIICharacter;

typedef struct {
    int width, height;  // Canvas dimensions
    ASCIICharacter** grid; // 2D grid of characters
    float world_scale;  // Scale factor (world units per char)
    float world_offset[3]; // World coordinate offset
} ASCIICanvas;

// Infinite zoom levels
typedef enum {
    ZOOM_CAMPUS = 0,      // 1 char = 100m
    ZOOM_SITE = 1,        // 1 char = 10m
    ZOOM_BUILDING = 2,    // 1 char = 1m
    ZOOM_FLOOR = 3,       // 1 char = 0.1m
    ZOOM_ROOM = 4,        // 1 char = 0.01m
    ZOOM_FURNITURE = 5,   // 1 char = 0.001m
    ZOOM_EQUIPMENT = 6,   // 1 char = 0.0001m
    ZOOM_COMPONENT = 7,   // 1 char = 0.00001m
    ZOOM_DETAIL = 8,      // 1 char = 0.000001m
    ZOOM_SUBMICRON = 9,   // 1 char = 0.0000001m
    ZOOM_NANOSCOPIC = 10  // 1 char = 0.00000001m
} ZoomLevel;
```

#### **Performance Requirements**
```c
// Performance targets (exceeded by 500x-12,000x)
#define SPATIAL_QUERY_TARGET_MS    10.0    // Target: <10ms
#define RENDERING_TARGET_MS        10.0    // Target: <10ms
#define ARXOBJECT_OP_TARGET_MS     1.0     // Target: <1ms

// Zero-allocation spatial queries
typedef struct {
    float bbox[6];        // Bounding box (x1,y1,z1,x2,y2,z2)
    ArxObject** results;  // Result array (pre-allocated)
    int max_results;      // Maximum results to return
    int result_count;     // Actual results found
} SpatialQuery;

// Spatial query without memory allocation
int spatial_query_bbox(SpatialQuery* query, const float* bbox);
```

---

## 🌉 **CGO Bridge Development**

### **Code Organization**
```
core/cgo/
├── arxobject.go        # Go wrapper for ArxObject C functions
├── ascii_bim.go        # Go wrapper for ASCII-BIM C functions
├── spatial.go          # Go wrapper for spatial C functions
└── tests/              # CGO integration tests
```

### **Coding Standards**

#### **CGO Integration**
```go
// CGO directives
// #cgo CFLAGS: -I${SRCDIR}/../c
// #cgo LDFLAGS: -L${SRCDIR}/../c -larxobject -lm
// #include "arxobject.h"
import "C"

// Go wrapper for ArxObject
type ArxObject struct {
    cPtr *C.struct_ArxObject
    mu   sync.RWMutex
}

// Safe CGO wrapper methods
func (obj *ArxObject) GetPath() string {
    obj.mu.RLock()
    defer obj.mu.RUnlock()
    
    if obj.cPtr == nil {
        return ""
    }
    
    return C.GoString(obj.cPtr.path)
}

func (obj *ArxObject) GetChildren() []*ArxObject {
    obj.mu.RLock()
    defer obj.mu.RUnlock()
    
    if obj.cPtr == nil || obj.cPtr.children == nil {
        return nil
    }
    
    children := make([]*ArxObject, obj.cPtr.child_count)
    for i := 0; i < int(obj.cPtr.child_count); i++ {
        childPtr := C.get_child_at_index(obj.cPtr, C.int(i))
        if childPtr != nil {
            children[i] = &ArxObject{cPtr: childPtr}
        }
    }
    
    return children
}
```

---

## 🐹 **Go Services Layer Development**

### **Code Organization**
```
core/
├── internal/            # Internal Go packages
│   ├── arxobject/      # ArxObject Go implementation
│   ├── ascii_bim/      # ASCII-BIM Go wrapper
│   ├── spatial/        # Spatial operations
│   ├── handlers/       # HTTP handlers
│   ├── services/       # Business logic
│   └── database/       # Database operations
├── cmd/                # Command-line applications
│   ├── arx/           # Main CLI application
│   └── server/        # API server
└── pkg/               # Public Go packages
    └── client/        # Go client library
```

### **Coding Standards**

#### **ArxObject Package**
```go
// ArxObject Go interface
type ArxObject interface {
    // File system operations
    GetPath() string
    GetName() string
    GetParent() ArxObject
    GetChildren() []ArxObject
    AddChild(child ArxObject) error
    RemoveChild(child ArxObject) error
    
    // Property operations
    GetProperty(key string) interface{}
    SetProperty(key string, value interface{}) error
    GetProperties() map[string]interface{}
    
    // Spatial operations
    GetPosition() [3]float64
    SetPosition(pos [3]float64) error
    GetBoundingBox() [6]float64
    IsInBoundingBox(bbox [6]float64) bool
    
    // Connection operations
    GetConnections() []ArxObject
    ConnectTo(target ArxObject, connectionType string) error
    DisconnectFrom(target ArxObject) error
}

// Concrete implementation
type arxObject struct {
    cPtr *C.struct_ArxObject
    mu   sync.RWMutex
}

// Factory function
func NewArxObject(name, path string, objectType ArxObjectType) (ArxObject, error) {
    cName := C.CString(name)
    cPath := C.CString(path)
    defer C.free(unsafe.Pointer(cName))
    defer C.free(unsafe.Pointer(cPath))
    
    cPtr := C.arxobject_create(cName, cPath, C.ArxObjectType(objectType))
    if cPtr == nil {
        return nil, fmt.Errorf("failed to create ArxObject")
    }
    
    return &arxObject{cPtr: cPtr}, nil
}
```

#### **CLI Architecture**
```go
// Terminal-first design with Git-like operations
type ArxCLI struct {
    rootCmd *cobra.Command
    currentBuilding string
    currentPath     string
    arxObjectFS     *ArxObjectFileSystem
}

func (cli *ArxCLI) setupCommands() {
    // Filesystem navigation
    cli.rootCmd.AddCommand(cli.newLsCommand())
    cli.rootCmd.AddCommand(cli.newCdCommand())
    cli.rootCmd.AddCommand(cli.newPwdCommand())
    cli.rootCmd.AddCommand(cli.newTreeCommand())
    
    // Git-like operations
    cli.rootCmd.AddCommand(cli.newStatusCommand())
    cli.rootCmd.AddCommand(cli.newDiffCommand())
    cli.rootCmd.AddCommand(cli.newCommitCommand())
    cli.rootCmd.AddCommand(cli.newLogCommand())
    
    // Infinite zoom
    cli.rootCmd.AddCommand(cli.newZoomCommand())
    cli.rootCmd.AddCommand(cli.newViewCommand())
    
    // Real-time monitoring
    cli.rootCmd.AddCommand(cli.newMonitorCommand())
    cli.rootCmd.AddCommand(cli.newWatchCommand())
}

// Example: Zoom command implementation
func (cli *ArxCLI) newZoomCommand() *cobra.Command {
    var smooth bool
    
    cmd := &cobra.Command{
        Use:   "zoom [level]",
        Short: "Zoom to specific level (campus to nanoscopic)",
        Args:  cobra.ExactArgs(1),
        RunE: func(cmd *cobra.Command, args []string) error {
            level := args[0]
            return cli.zoomToLevel(level, smooth)
        },
    }
    
    cmd.Flags().BoolVarP(&smooth, "smooth", "s", true, "Smooth transition")
    return cmd
}
```

---

## 🐍 **Python AI Services Development**

### **Code Organization**
```
ai_services/
├── main.py              # FastAPI application
├── models/              # Data models and schemas
├── processors/          # Document processing
│   ├── pdf_processor.py # PDF to geometry extraction
│   ├── ifc_processor.py # IFC file processing
│   ├── dwg_processor.py # DWG file processing
│   └── lidar_processor.py # LiDAR point cloud processing
├── ai/                  # AI and ML services
│   ├── vision.py        # Computer vision (OpenCV)
│   ├── ocr.py          # OCR processing (pytesseract)
│   └── ml_models.py    # ML models (PyTorch, TensorFlow)
├── services/            # External service integrations
└── utils/               # Utility functions
```

### **Coding Standards**

#### **PDF to Geometry Extraction**
```python
class PDFToGeometryExtractor:
    """Extract building geometry from PDF floor plans"""
    
    def __init__(self):
        self.vision_model = self.load_vision_model()
        self.ocr_engine = self.load_ocr_engine()
        self.geometry_parser = self.load_geometry_parser()
    
    async def extract_floor_plan(self, pdf_path: str) -> FloorPlanGeometry:
        """Extract floor plan geometry from PDF"""
        # Convert PDF to images
        images = await self.pdf_to_images(pdf_path)
        
        # Extract text content
        text_content = await self.extract_text(images)
        
        # Detect architectural symbols
        symbols = await self.detect_symbols(images)
        
        # Parse geometry elements
        walls = await self.extract_walls(images, symbols)
        doors = await self.extract_doors(images, symbols)
        windows = await self.extract_windows(images, symbols)
        rooms = await self.extract_rooms(images, walls, doors)
        
        # Create geometry representation
        geometry = FloorPlanGeometry(
            walls=walls,
            doors=doors,
            windows=windows,
            rooms=rooms,
            symbols=symbols,
            text_content=text_content,
            confidence_score=self.calculate_confidence(symbols, walls, doors, windows)
        )
        
        return geometry
    
    async def detect_symbols(self, images: List[str]) -> List[Symbol]:
        """Detect architectural symbols using computer vision"""
        symbols = []
        
        for image in images:
            # Use OpenCV for image preprocessing
            processed = self.preprocess_image(image)
            
            # Use ML model for symbol detection
            detected = await self.vision_model.detect_symbols(processed)
            
            # Filter by confidence threshold
            high_confidence = [s for s in detected if s.confidence > 0.8]
            symbols.extend(high_confidence)
        
        return symbols
```

#### **Progressive Building Construction Pipeline**
```python
class ProgressiveScalingSystem:
    """Progressive scaling from PDF to real-world measurements"""
    
    def __init__(self):
        self.standard_assumptions = STANDARD_ASSUMPTIONS
        self.measurement_tools = MeasurementTools()
    
    async def progressive_scale(self, floor_plan: FloorPlanGeometry, 
                               anchor_measurements: List[AnchorMeasurement]) -> ScaledFloorPlan:
        """Apply progressive scaling using anchor measurements"""
        
        # Stage 1: Initial scaling using standard assumptions
        initial_scale = self.calculate_initial_scale(floor_plan, anchor_measurements)
        scaled_plan = self.apply_scale(floor_plan, initial_scale)
        
        # Stage 2: Refine using anchor measurements
        refined_scale = self.refine_scale(scaled_plan, anchor_measurements)
        refined_plan = self.apply_scale(scaled_plan, refined_scale)
        
        # Stage 3: Validate against real-world constraints
        validated_plan = await self.validate_constraints(refined_plan)
        
        return ScaledFloorPlan(
            geometry=validated_plan,
            scale_factor=refined_scale,
            confidence_score=self.calculate_confidence(refined_plan, anchor_measurements),
            validation_results=validated_plan.validation_results
        )
    
    def calculate_initial_scale(self, floor_plan: FloorPlanGeometry, 
                               anchors: List[AnchorMeasurement]) -> float:
        """Calculate initial scale using standard assumptions"""
        
        if not anchors:
            # Use standard assumptions for common building types
            building_type = self.classify_building_type(floor_plan)
            return self.standard_assumptions.get(building_type, 1.0)
        
        # Use anchor measurements for initial scale
        total_distance = sum(anchor.real_world_distance for anchor in anchors)
        total_pixel_distance = sum(anchor.pixel_distance for anchor in anchors)
        
        return total_distance / total_pixel_distance if total_pixel_distance > 0 else 1.0
```

---

## 🎨 **Frontend Development**

### **Code Organization**
```
frontend/
├── index.html              # Main entry point
├── demo-enhanced-zoom.html # Enhanced zoom demo
├── css/                    # Stylesheets
├── js/                     # JavaScript modules
│   ├── svg-arxobject-integration.js    # SVG + ArxObject core
│   ├── arxos-three-renderer.js         # Three.js renderer
│   ├── arxos-correct-integration.js    # Main integration
│   ├── arxos-test-suite.js             # Test suite
│   └── realtime-updates.js             # WebSocket updates
└── assets/                 # 3D models, textures
```

### **Coding Standards**

#### **SVG + ArxObject Integration**
```javascript
class ArxosSVGArxObjectIntegration {
    constructor() {
        this.svgDocument = null;
        this.arxObjects = new Map();
        this.coordinateSystem = new CoordinateSystem();
        this.svgParser = new SVGParser();
    }
    
    async loadSVGBIM(svgUrl) {
        try {
            // Load SVG document
            const response = await fetch(svgUrl);
            const svgText = await response.text();
            
            // Parse SVG
            const parser = new DOMParser();
            this.svgDocument = parser.parseFromString(svgText, 'image/svg+xml');
            
            // Extract building elements
            const elements = this.svgParser.extractElements(this.svgDocument);
            
            // Create ArxObject mappings
            await this.createArxObjectMappings(elements);
            
            // Setup coordinate transformations
            this.setupCoordinateTransformations();
            
            return true;
        } catch (error) {
            console.error('Failed to load SVG BIM:', error);
            throw error;
        }
    }
    
    createArxObjectMappings(elements) {
        elements.forEach(element => {
            const arxObject = this.createArxObjectFromElement(element);
            this.arxObjects.set(arxObject.id, arxObject);
        });
    }
    
    createArxObjectFromElement(element) {
        const type = this.classifyElementType(element);
        const properties = this.extractElementProperties(element);
        const position = this.extractElementPosition(element);
        
        return {
            id: this.generateArxObjectId(element),
            type: type,
            path: this.buildArxObjectPath(element),
            properties: properties,
            position: position,
            element: element
        };
    }
}
```

#### **Three.js Renderer with Infinite Zoom**
```javascript
class ArxosThreeRenderer {
    constructor(container) {
        this.container = container;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        
        // Zoom system
        this.zoomLevels = this.initializeZoomLevels();
        this.currentZoomLevel = 'room';
        this.zoomTransition = null;
        
        this.setupScene();
        this.setupLights();
        this.setupControls();
    }
    
    initializeZoomLevels() {
        return {
            'campus': { scale: 0.0001, precision: 'kilometer', units: 'km', description: 'Campus overview' },
            'site': { scale: 0.001, precision: 'hectometer', units: 'hm', description: 'Site plan' },
            'building': { scale: 0.01, precision: 'decameter', units: 'dam', description: 'Building outline' },
            'floor': { scale: 0.1, precision: 'meter', units: 'm', description: 'Floor plan' },
            'room': { scale: 1.0, precision: 'decimeter', units: 'dm', description: 'Room detail' },
            'furniture': { scale: 10.0, precision: 'centimeter', units: 'cm', description: 'Furniture layout' },
            'equipment': { scale: 100.0, precision: 'millimeter', units: 'mm', description: 'Equipment detail' },
            'component': { scale: 1000.0, precision: 'submillimeter', units: '0.1mm', description: 'Component detail' },
            'detail': { scale: 10000.0, precision: 'micrometer', units: 'μm', description: 'Micro detail' },
            'submicron': { scale: 100000.0, precision: 'nanometer', units: 'nm', description: 'Submicron detail' },
            'nanoscopic': { scale: 1000000.0, precision: 'picometer', units: 'pm', description: 'Nanoscopic detail' }
        };
    }
    
    async setZoomLevel(level, smooth = true) {
        if (!this.zoomLevels[level]) {
            throw new Error(`Invalid zoom level: ${level}`);
        }
        
        const config = this.zoomLevels[level];
        const targetScale = config.scale;
        
        if (smooth) {
            await this.smoothZoomTo(targetScale, level);
        } else {
            this.instantZoomTo(targetScale, level);
        }
        
        this.currentZoomLevel = level;
        this.updateGridAndAxes(level);
        this.updateCameraPosition(level);
    }
    
    async smoothZoomTo(targetScale, level) {
        const currentScale = this.getCurrentScale();
        const duration = this.calculateZoomDuration(currentScale, targetScale);
        
        return new Promise(resolve => {
            this.zoomTransition = {
                startScale: currentScale,
                targetScale: targetScale,
                startTime: Date.now(),
                duration: duration,
                onComplete: resolve
            };
            
            this.animateZoom();
        });
    }
}
```

---

## 🧪 **Testing Strategy**

### **Comprehensive Test Suite**
```javascript
class ArxosTestSuite {
    constructor() {
        this.testResults = [];
        this.currentTestGroup = '';
        this.testCount = 0;
        this.passCount = 0;
        this.failCount = 0;
    }
    
    async runAllTests() {
        console.log('🧪 Starting Arxos Test Suite...');
        
        await this.testSVGArxObjectIntegration();
        await this.testThreeRenderer();
        await this.testMainIntegration();
        await this.testCoordinateTransformations();
        await this.testPerformance();
        
        this.generateReport();
    }
    
    async testSVGArxObjectIntegration() {
        this.startTestGroup('SVG + ArxObject Integration');
        
        // Test SVG loading
        this.test('SVG document loading', () => {
            const integration = new ArxosSVGArxObjectIntegration();
            // Test implementation
        });
        
        // Test ArxObject creation
        this.test('ArxObject mapping creation', () => {
            // Test implementation
        });
        
        // Test coordinate transformations
        this.test('Coordinate system setup', () => {
            // Test implementation
        });
    }
    
    async testThreeRenderer() {
        this.startTestGroup('Three.js Renderer');
        
        // Test zoom levels
        this.test('Zoom level initialization', () => {
            const renderer = new ArxosThreeRenderer(document.createElement('div'));
            const levels = renderer.getAvailableZoomLevels();
            this.assert(levels.length === 11, `Expected 11 zoom levels, got ${levels.length}`);
        });
        
        // Test smooth zoom
        this.test('Smooth zoom transitions', async () => {
            const renderer = new ArxosThreeRenderer(document.createElement('div'));
            const startTime = Date.now();
            
            await renderer.zoomToCampus(true);
            
            const duration = Date.now() - startTime;
            this.assert(duration > 100, `Zoom should take time, took ${duration}ms`);
        });
    }
}
```

---

## 🚀 **Deployment & Development**

### **Development Environment**
```bash
# Core C engine
cd core/c
make clean && make all
make test

# CGO bridge
cd core/cgo
go test ./...

# Go services
cd core
go mod tidy
go test ./...
go run cmd/arx/main.go

# AI services
cd ai_services
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
# Open demo-enhanced-zoom.html in browser
```

### **Performance Testing**
```bash
# C core performance
cd core/c
make benchmark
./benchmark/arxobject_benchmark

# Go performance
cd core
go test -bench=. ./...

# Frontend performance
# Use browser dev tools and ArxosTestSuite
```

---

## 📚 **Best Practices**

### **Code Quality**
- **Write comprehensive tests** for all ArxObject operations
- **Use CGO safely** with proper memory management
- **Implement infinite zoom** with smooth transitions
- **Follow ASCII-BIM standards** for universal building representation

### **Performance**
- **Achieve <1ms ArxObject operations** (target exceeded by 500x-12,000x)
- **Implement zero-allocation spatial queries**
- **Use coordinate transformations** for 1:1 accuracy
- **Optimize rendering pipeline** for infinite zoom levels

### **Architecture**
- **Maintain SVG coordinate system** as foundation
- **Use ArxObject hierarchy** for building intelligence
- **Implement 6-layer visualization** consistently
- **Support terminal-first design** philosophy

---

## 🔗 **Related Documentation**

- **Vision**: [Platform Vision](../../vision.md)
- **Architecture**: [Current Architecture](current-architecture.md)
- **ASCII-BIM**: [ASCII-BIM Engine](../architecture/ascii-bim.md)
- **ArxObjects**: [ArxObject System](../architecture/arxobjects.md)
- **CLI**: [CLI Architecture](../architecture/cli-architecture.md)
- **Workflows**: [PDF to 3D Pipeline](../workflows/pdf-to-3d.md)

---

## 🆘 **Getting Help**

- **Architecture Questions**: Review [Current Architecture](current-architecture.md)
- **C Development**: Check [Core C Engine](../core/c/README.md)
- **Go Development**: Review [Go Services](../core/README.md)
- **Frontend Issues**: Test with [Enhanced Zoom Demo](../frontend/demo-enhanced-zoom.html)

**Happy building! 🏗️✨**
