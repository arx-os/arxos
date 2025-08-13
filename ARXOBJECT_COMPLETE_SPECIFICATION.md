# ArxObject Complete Specification
## The DNA of Building Infrastructure - Single Source of Truth

### Overview
An ArxObject is a self-contained data capsule that represents ANY piece of building infrastructure - from an entire campus down to a single screw. Each ArxObject knows:
- What it is (identity)
- Where it exists (position in space)
- When it's visible (zoom level)
- How it connects to other objects
- Its complete history
- How it overlaps with other objects in 2D space

### Core Concept: Everything is an ArxObject

```
Campus (ArxObject)
  └── Building (ArxObject)
      └── Floor (ArxObject)
          └── Room (ArxObject)
              └── Outlet (ArxObject)
                  └── Terminal (ArxObject)
                      └── Screw (ArxObject)
```

## The ArxObject Data Structure

```go
type ArxObject struct {
    // === IDENTITY ===
    ID       string  // Unique identifier: "arx:plant-high:floor-1:room-201:outlet-1"
    Type     string  // What this is: "outlet", "room", "building"
    Name     string  // Human readable: "Outlet 1", "Room 201"
    System   string  // Which system: "electrical", "hvac", "structural"
    
    // === FRACTAL HIERARCHY ===
    ParentID string     // Who contains me: "arx:plant-high:floor-1:room-201"
    ChildIDs []string   // What I contain: ["arx:...:terminal-1", "arx:...:terminal-2"]
    
    // === SPATIAL LOCATION ===
    Position struct {
        X float64  // Millimeter precision: 1234.567
        Y float64  // Millimeter precision: 5678.901
        Z float64  // Height/elevation: 2500.000 (2.5 meters)
    }
    
    // === SYSTEM PLANE (FOR OVERLAP HANDLING) ===
    SystemPlane struct {
        Layer    string   // "electrical", "hvac", "plumbing"
        ZOrder   int      // Rendering order: 0=bottom, 100=top
        Elevation string  // "floor", "wall", "ceiling", "above_ceiling"
    }
    
    // === OVERLAP MANAGEMENT ===
    Overlap struct {
        SharesSpaceWith []string  // IDs of objects at same X,Y
        Relationship    string    // "mounted_on", "inside", "adjacent", "controls"
        VisualOffset    Vector3D  // Micro-offset for visualization if needed
    }
    
    // === ZOOM VISIBILITY ===
    ScaleRange struct {
        MinZoom float64  // Visible starting at zoom: 10.0 (building level)
        MaxZoom float64  // Visible up to zoom: 0.001 (component level)
        OptimalZoom float64  // Best viewed at: 1.0 (floor level)
    }
    
    // === VISUAL REPRESENTATION ===
    Geometry struct {
        SVGPath string   // How to draw me: "M0,0 L100,0 L100,50 L0,50 Z"
        Style   string   // How I look: "fill:#fff;stroke:#000"
        Icon    string   // Symbol at low zoom: "⚡" for electrical
        SymbolID string  // Reference to symbol library: "symbol:electrical:outlet:duplex"
    }
    
    // === PROPERTIES (The DNA) ===
    Properties map[string]interface{} {
        // Electrical outlet example:
        "voltage": 120,
        "amperage": 20,
        "num_receptacles": 2,
        "gfci_protected": true,
        "circuit": "A-5",
        "install_date": "2020-03-15",
        "manufacturer": "Leviton",
        "model": "5362-W",
        "last_tested": "2024-01-15"
    }
    
    // === CONNECTIONS ===
    Connections []Connection {
        // What this connects to:
        {
            ToID: "arx:plant-high:floor-1:panel-a:breaker-5",
            Type: "electrical_feed",
            Properties: {"wire_gauge": "12 AWG", "wire_type": "THHN"}
        }
    }
    
    // === HISTORY ===
    History []Change {
        // Every modification tracked:
        {
            Timestamp: "2024-01-15T10:30:00Z",
            Contributor: "user:john-doe",
            Action: "tested",
            Details: "GFCI test passed",
            BILTReward: 0.5
        }
    }
    
    // === CONTRIBUTIONS ===
    Contributors []Contributor {
        // Who has worked on this:
        {
            UserID: "user:john-doe",
            TotalBILT: 5.5,
            Contributions: 3
        }
    }
}
```

## System Layer Definitions (For Overlap Resolution)

### Standard Z-Order Layers
```go
const (
    LAYER_UNDERGROUND  = -10  // Underground utilities
    LAYER_FOUNDATION   = 0    // Slab, foundation
    LAYER_FLOOR        = 10   // Floor level items
    LAYER_WALL_LOW     = 20   // Lower wall (outlets - 18" AFF)
    LAYER_WALL_MID     = 30   // Mid wall (switches - 48" AFF)
    LAYER_WALL_HIGH    = 40   // Upper wall (thermostats - 60" AFF)
    LAYER_CEILING      = 50   // Ceiling mounted
    LAYER_ABOVE_CEIL   = 60   // Above ceiling (ducts, cable trays)
    LAYER_ROOF         = 70   // Roof level
)
```

### System-Specific Default Layers
```go
var SystemLayers = map[string]LayerConfig{
    "structural": {
        DefaultZOrder: 0,
        SubLayers: map[string]int{
            "foundation": 0,
            "columns": 5,
            "beams": 55,
            "walls": 10,
        },
    },
    "electrical": {
        DefaultZOrder: 25,
        SubLayers: map[string]int{
            "underground": -5,
            "floor_boxes": 15,
            "outlets": 25,
            "switches": 35,
            "lighting": 50,
            "panel": 30,
        },
    },
    "hvac": {
        DefaultZOrder: 60,
        SubLayers: map[string]int{
            "floor_vents": 15,
            "thermostats": 35,
            "ceiling_diffusers": 50,
            "ductwork": 65,
            "equipment": 70,
        },
    },
    "plumbing": {
        DefaultZOrder: 20,
        SubLayers: map[string]int{
            "underground": -8,
            "in_slab": 5,
            "in_wall": 20,
            "fixtures": 30,
            "roof_drains": 72,
        },
    },
    "fire_protection": {
        DefaultZOrder: 55,
        SubLayers: map[string]int{
            "pull_stations": 35,
            "sprinklers": 55,
            "smoke_detectors": 52,
            "fire_extinguishers": 38,
        },
    },
}
```

## The Symbol Library System

### Symbol Structure
```go
type SystemSymbol struct {
    // Identity
    ID          string   // "symbol:electrical:outlet:duplex"
    System      string   // "electrical", "hvac", "plumbing", "fire", "structural"
    Category    string   // "outlet", "switch", "breaker", "fixture"
    SubType     string   // "duplex", "gfci", "dedicated", "weatherproof"
    
    // Visual Patterns (what to look for in PDFs)
    Patterns    []Pattern {
        {
            Type: "circle_with_lines",  // Common outlet representation
            SVGPattern: "M0,0 A5,5 0 1,1 0,0.1 M-3,0 L3,0 M0,-3 L0,3",
            Confidence: 0.95,
        },
    }
    
    // Text Clues (labels to look for nearby)
    TextClues   []string {"DUPLEX", "120V", "20A", "GFCI", "WP"}
    
    // Default Properties to Auto-Assign
    DefaultProperties map[string]interface{} {
        "voltage": 120,
        "receptacles": 2,
        "mounting": "wall",
        "height_aff": 18,  // 18 inches above finished floor
    }
    
    // Typical Size (for scale detection)
    TypicalSize struct {
        Width  float64  // 4.5 inches
        Height float64  // 2.75 inches
    }
    
    // Default Layer Assignment
    DefaultLayer struct {
        System: "electrical",
        ZOrder: 25,
        Elevation: "wall",
    }
}
```

### Core Symbol Libraries

#### Electrical Symbols
```go
var ElectricalSymbols = []SystemSymbol{
    {
        ID: "symbol:electrical:outlet:duplex",
        System: "electrical",
        Category: "outlet",
        SubType: "duplex",
        Patterns: []Pattern{{SVGPattern: "circle_with_two_lines"}},
        DefaultProperties: map[string]interface{}{
            "voltage": 120, "amperage": 20, "receptacles": 2,
        },
        DefaultLayer: {System: "electrical", ZOrder: 25, Elevation: "wall"},
    },
    {
        ID: "symbol:electrical:panel:distribution",
        System: "electrical",
        Category: "panel",
        SubType: "distribution",
        Patterns: []Pattern{{SVGPattern: "rectangle_with_grid"}},
        TextClues: []string{"PANEL", "PP", "LP"},
        DefaultLayer: {System: "electrical", ZOrder: 30, Elevation: "wall"},
    },
    // ... more electrical symbols
}
```

#### HVAC Symbols
```go
var HVACSymbols = []SystemSymbol{
    {
        ID: "symbol:hvac:diffuser:supply",
        System: "hvac",
        Category: "diffuser",
        SubType: "supply",
        Patterns: []Pattern{{SVGPattern: "square_with_four_arrows_out"}},
        TextClues: []string{"SA", "SUPPLY", "CFM"},
        DefaultLayer: {System: "hvac", ZOrder: 50, Elevation: "ceiling"},
    },
    // ... more HVAC symbols
}
```

## The SVGX File Format

SVGX is our extended SVG format that embeds ArxObjects into a visual representation:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svgx xmlns="http://arxos.io/svgx" version="1.0">
    <!-- Metadata about this file -->
    <metadata>
        <building>Plant High School</building>
        <created>2024-01-15</created>
        <scale-levels>7</scale-levels>
        <bounds>
            <min-x>0</min-x>
            <min-y>0</min-y>
            <max-x>100000</max-x>  <!-- 100 meters -->
            <max-y>150000</max-y>  <!-- 150 meters -->
        </bounds>
    </metadata>
    
    <!-- ArxObject definitions -->
    <arxobjects>
        <!-- Building level object (visible at zoom 10-100) -->
        <arxobject id="arx:plant-high" zoom-min="10" zoom-max="100">
            <type>building</type>
            <name>Plant High School</name>
            <geometry>
                <rect x="0" y="0" width="100000" height="150000"/>
            </geometry>
            <properties>
                <property name="address">2415 S Himes Ave, Tampa, FL</property>
                <property name="year_built">1927</property>
                <property name="square_feet">250000</property>
            </properties>
        </arxobject>
        
        <!-- Room with overlapping systems -->
        <arxobject id="arx:plant-high:floor-1:room-201" zoom-min="0.1" zoom-max="5">
            <type>room</type>
            <name>Room 201</name>
            <geometry>
                <rect x="10000" y="20000" width="8000" height="10000"/>
            </geometry>
            <overlaps>
                <!-- Multiple objects at same location -->
                <overlap-group x="11000" y="21000">
                    <object ref="arx:...:outlet-1" layer="electrical" z-order="25"/>
                    <object ref="arx:...:thermostat-1" layer="hvac" z-order="35"/>
                    <object ref="arx:...:wall-segment-1" layer="structural" z-order="5"/>
                </overlap-group>
            </overlaps>
        </arxobject>
    </arxobjects>
</svgx>
```

## Three Methods of Ingestion

### Method 1: PDF/IFC File Ingestion (Digital Files)
```go
func IngestPDF(pdfFile []byte) ([]ArxObject, error) {
    // 1. Load Symbol Library
    symbols := LoadSymbolLibraries()
    
    // 2. Extract visual elements from PDF
    elements := ExtractPDFElements(pdfFile)
    
    // 3. Identify objects using Symbol Library
    arxObjects := []ArxObject{}
    for _, element := range elements {
        matches := symbols.FindMatches(element)
        
        if bestMatch := matches.GetBest(); bestMatch != nil {
            // Create ArxObject from matched symbol
            arxObj := CreateArxObjectFromSymbol(bestMatch, element)
            
            // 4. Handle overlaps with existing objects
            overlaps := DetectOverlaps(arxObj, arxObjects)
            if len(overlaps) > 0 {
                arxObj = ResolveOverlaps(arxObj, overlaps)
            }
            
            arxObjects = append(arxObjects, arxObj)
        }
    }
    
    // 5. Build spatial relationships
    BuildSpatialRelationships(arxObjects)
    
    // 6. Index by system
    SystemIndex := IndexBySystem(arxObjects)
    
    return arxObjects, nil
}
```

### Method 2: Photo Capture of Physical Building Maps (Paper Maps at Front Desk)
```go
// This is the HCPS reality - paper maps at every school front desk
func IngestPhotoOfPaperMap(photo []byte) ([]ArxObject, error) {
    // 1. Perspective Correction
    corrected := PerspectiveCorrection(photo)
    
    // 2. Image Enhancement
    enhanced := EnhanceImage(corrected)
    
    // 3. OCR for Text Extraction
    textElements := ExtractTextFromImage(enhanced)
    roomNumbers := ExtractRoomNumbers(textElements)
    buildingName := ExtractBuildingName(textElements)
    
    // 4. Edge Detection for Walls
    edges := DetectEdges(enhanced)
    walls := ExtractWalls(edges)
    
    // 5. Symbol Recognition (same library)
    symbols := LoadSymbolLibraries()
    detectedSymbols := DetectSymbolsInPhoto(enhanced, symbols)
    
    // 6. Scale Calibration
    scale := CalibrateScale(walls, textElements)
    
    // 7. Create ArxObjects
    arxObjects := []ArxObject{}
    
    // Create room objects
    for _, room := range DetectRooms(walls) {
        arxObj := ArxObject{
            ID: GenerateID(buildingName, room.Number),
            Type: "room",
            Name: room.Number,
            System: "structural",
            Position: room.Centroid,
            Geometry: room.Boundary,
            Properties: map[string]interface{}{
                "room_number": room.Number,
                "source": "paper_map_photo",
                "confidence": room.DetectionConfidence,
            },
        }
        arxObjects = append(arxObjects, arxObj)
    }
    
    // Add detected symbols as ArxObjects
    for _, symbol := range detectedSymbols {
        arxObjects = append(arxObjects, symbol.ToArxObject())
    }
    
    return arxObjects, nil
}

// Mobile App UI for Photo Capture
type PhotoCaptureWorkflow struct {
    Steps []Step{
        {
            Name: "Capture",
            Instructions: "Take photo of building map",
            Actions: []Action{
                ShowCameraOverlay(),  // Shows guides for alignment
                AutoDetectPaper(),    // Highlights paper edges
                CaptureHighRes(),     // Takes high-res photo
            },
        },
        {
            Name: "Align",
            Instructions: "Confirm corners of map",
            Actions: []Action{
                ShowCornerHandles(),  // User adjusts corners
                PreviewCorrection(),  // Shows corrected view
                ConfirmAlignment(),   // User confirms
            },
        },
        {
            Name: "Identify",
            Instructions: "Verify building and floor",
            Actions: []Action{
                ShowDetectedText(),   // "Is this Plant High School?"
                SelectFloor(),        // "Floor 1, 2, or 3?"
                ConfirmIdentity(),    // User verifies
            },
        },
        {
            Name: "Enhance",
            Instructions: "Mark any missed rooms",
            Actions: []Action{
                ShowDetectedRooms(),  // Overlay on photo
                AllowManualAddition(), // User can add missed rooms
                MarkDoors(),          // User marks door locations
            },
        },
    }
}

// Real-world Example
func HCPSContractorWorkflow() {
    // 1. Contractor arrives at school
    // 2. Gets work order: "Fix outlet in Room 201"
    // 3. Goes to front desk, sees paper map on wall
    // 4. Opens Arxos mobile app
    // 5. Takes photo of map
    // 6. App processes and creates basic floor plan
    // 7. Contractor navigates to Room 201
    // 8. Adds photo of actual broken outlet
    // 9. Earns BILT for contributing real-world data
}
```

### Method 3: LiDAR Field Capture (Building from Scratch)
```go
// When NOTHING exists - field user creates the building model on-site
func IngestFromLiDAR(lidarSession LiDARCapture) ([]ArxObject, error) {
    arxObjects := []ArxObject{}
    
    // Real-time capture as user walks through building
    for _, scan := range lidarSession.Scans {
        // 1. Process point cloud
        pointCloud := ProcessLiDARPoints(scan)
        
        // 2. Detect planes (walls, floors, ceilings)
        planes := DetectPlanes(pointCloud)
        
        // 3. Extract walls
        walls := ExtractWallsFromPlanes(planes)
        
        // 4. Detect room boundaries
        rooms := InferRoomsFromWalls(walls)
        
        // 5. Create ArxObjects
        for _, wall := range walls {
            arxObj := ArxObject{
                ID: GenerateID(),
                Type: "wall",
                System: "structural",
                Position: wall.Center,
                Geometry: wall.ToSVGPath(),
                Properties: map[string]interface{}{
                    "height": wall.Height,
                    "thickness": wall.EstimatedThickness,
                    "material": wall.InferredMaterial,
                    "captured_by": "lidar",
                    "confidence": wall.Confidence,
                },
            }
            arxObjects = append(arxObjects, arxObj)
        }
    }
    
    return arxObjects, nil
}

// Mobile LiDAR Capture Interface
type LiDARCaptureApp struct {
    Mode string  // "walls", "electrical", "plumbing", etc.
    
    // Real-time feedback
    Display struct {
        PointCloud   bool  // Show raw points
        DetectedWalls bool  // Show wall overlays
        MeasureMode  bool  // Show dimensions
        SystemMode   string // Current system being mapped
    }
}

// The Field Worker LiDAR Workflow
func FieldWorkerLiDARWorkflow() Workflow {
    return Workflow{
        Steps: []WorkflowStep{
            {
                Name: "Trace Walls",
                Instructions: "Walk around room perimeter",
                UI: LiDARUI{
                    Mode: "wall_capture",
                    Overlay: "wall_guidelines",
                    Feedback: "Hold phone vertically, walk slowly",
                },
                Process: func(scan) {
                    DetectWalls(scan)
                    ShowWallsInAR()  // Real-time AR overlay
                    AutoSnapToGrid()  // Snap to 90-degree angles
                },
            },
            {
                Name: "Mark Outlets",
                Instructions: "Point at each outlet",
                UI: LiDARUI{
                    Mode: "point_capture",
                    Symbol: "electrical_outlet",
                    Feedback: "Tap to mark outlet location",
                },
                Process: func(point) {
                    CreateArxObject("outlet", point)
                    SnapToWall()  // Auto-attach to nearest wall
                    ShowHeightAFF()  // Show height above floor
                },
            },
            {
                Name: "Trace Conduit",
                Instructions: "Follow conduit path",
                UI: LiDARUI{
                    Mode: "path_capture",
                    Symbol: "electrical_conduit",
                    Feedback: "Trace the conduit route",
                },
                Process: func(path) {
                    CreateConduitPath(path)
                    AutoConnectToDevices()  // Connect to outlets/panels
                },
            },
        },
    }
}

// Advanced LiDAR Features
type AdvancedLiDARFeatures struct {
    // Automatic Detection
    AutoDetect struct {
        Outlets     bool  // AI detects outlets in point cloud
        Switches    bool  // AI detects switches
        LightFixtures bool  // AI detects ceiling fixtures
        HVAC_Vents  bool  // AI detects diffusers
    }
    
    // Measurement Tools
    Measure struct {
        PointToPoint  bool  // Measure distances
        FloorArea     bool  // Calculate room area
        CeilingHeight bool  // Auto-detect height
        DoorWidth     bool  // Measure openings
    }
    
    // AR Overlay (iPhone/iPad Pro)
    ARMode struct {
        ShowExisting   bool  // Overlay existing ArxObjects
        CompareToPlans bool  // Show planned vs actual
        SystemColors   bool  // Color by system type
        ClashDetection bool  // Highlight conflicts
    }
}

// Combined Ingestion Pipeline
func UniversalIngestionPipeline(input IngestionInput) ([]ArxObject, error) {
    switch input.Type {
    case "pdf":
        return IngestPDF(input.Data)
        
    case "ifc":
        return IngestIFC(input.Data)
        
    case "photo":
        // Photo of paper map
        return IngestPhotoOfPaperMap(input.Data)
        
    case "lidar":
        // Real-time LiDAR capture
        return IngestFromLiDAR(input.LiDARSession)
        
    case "hybrid":
        // Combine multiple sources
        arxObjects := []ArxObject{}
        
        // Start with PDF if available
        if input.PDF != nil {
            arxObjects = append(arxObjects, IngestPDF(input.PDF)...)
        }
        
        // Enhance with photo
        if input.Photo != nil {
            photoObjects := IngestPhotoOfPaperMap(input.Photo)
            arxObjects = MergeAndDeduplicate(arxObjects, photoObjects)
        }
        
        // Add field-captured data
        if input.LiDAR != nil {
            fieldObjects := IngestFromLiDAR(input.LiDAR)
            arxObjects = MergeAndEnhance(arxObjects, fieldObjects)
        }
        
        return arxObjects, nil
    }
}
```

### Overlap Detection and Resolution
```go
func DetectOverlaps(newObject ArxObject, existingObjects []ArxObject) []Overlap {
    overlaps := []Overlap{}
    threshold := 50.0  // 50mm overlap threshold
    
    for _, existing := range existingObjects {
        distance := CalculateDistance2D(newObject.Position, existing.Position)
        
        if distance < threshold {
            // Determine relationship type
            relationship := DetermineRelationship(newObject, existing)
            
            // Add to overlap list
            newObject.Overlap.SharesSpaceWith = append(
                newObject.Overlap.SharesSpaceWith, 
                existing.ID,
            )
            newObject.Overlap.Relationship = relationship
            
            overlaps = append(overlaps, Overlap{
                ObjectA: newObject.ID,
                ObjectB: existing.ID,
                Relationship: relationship,
            })
        }
    }
    
    return overlaps
}

func ResolveOverlaps(obj ArxObject, overlaps []Overlap) ArxObject {
    // Assign appropriate Z-order based on system
    obj.SystemPlane.ZOrder = SystemLayers[obj.System].DefaultZOrder
    
    // Apply micro-offset if needed for visualization
    if len(overlaps) > 2 {
        angle := (2 * math.Pi) / float64(len(overlaps))
        obj.Overlap.VisualOffset = Vector3D{
            X: 100 * math.Cos(angle),  // 100mm offset
            Y: 100 * math.Sin(angle),
            Z: 0,
        }
    }
    
    return obj
}
```

## The Fractal Zoom System with Google Maps-Style Lazy Loading

### Zoom Levels
```
Zoom 100:   Campus view (buildings as rectangles)
Zoom 10:    Building outline (floors visible)
Zoom 1:     Floor plan (rooms visible)
Zoom 0.1:   Room details (outlets, switches visible)
Zoom 0.01:  Fixture details (individual terminals)
Zoom 0.001: Component level (screws, wire connections)
```

### Tile-Based Lazy Loading System

#### Tile Structure
```go
type Tile struct {
    // Tile identity
    Z        int      // Zoom level (0-20)
    X        int      // Tile X coordinate
    Y        int      // Tile Y coordinate
    
    // Tile bounds in world coordinates
    Bounds   BoundingBox {
        MinX float64
        MinY float64
        MaxX float64
        MaxY float64
    }
    
    // Tile data
    Objects  []ArxObject  // Objects in this tile
    Loaded   bool         // Is tile loaded?
    Loading  bool         // Is tile currently loading?
    CacheKey string       // Redis cache key
    
    // Performance
    LastAccessed time.Time
    Size         int64     // Bytes
}

type TileCache struct {
    // In-memory cache (like Google Maps)
    ActiveTiles   map[string]*Tile  // Currently visible tiles
    PrefetchTiles map[string]*Tile  // Adjacent tiles for smooth panning
    MaxMemory     int64             // Maximum memory usage
    
    // Redis backing for persistence
    RedisClient   *redis.Client
    
    // Cleanup
    LastCleanup   time.Time
    CleanupInterval time.Duration
}
```

#### Tile Loading Algorithm
```go
func (tc *TileCache) LoadVisibleTiles(viewport Viewport, zoom int) []*Tile {
    // 1. Calculate which tiles are needed
    neededTiles := CalculateTilesForViewport(viewport, zoom)
    
    // 2. Check what's already loaded
    loadedTiles := []*Tile{}
    tilesToLoad := []TileCoordinate{}
    
    for _, coord := range neededTiles {
        tileKey := fmt.Sprintf("%d/%d/%d", coord.Z, coord.X, coord.Y)
        
        if tile, exists := tc.ActiveTiles[tileKey]; exists {
            // Already in memory
            loadedTiles = append(loadedTiles, tile)
            tile.LastAccessed = time.Now()
        } else {
            // Need to load
            tilesToLoad = append(tilesToLoad, coord)
        }
    }
    
    // 3. Load missing tiles in parallel (like Google Maps)
    if len(tilesToLoad) > 0 {
        newTiles := tc.LoadTilesParallel(tilesToLoad)
        loadedTiles = append(loadedTiles, newTiles...)
    }
    
    // 4. Prefetch adjacent tiles for smooth panning
    go tc.PrefetchAdjacentTiles(viewport, zoom)
    
    // 5. Clean up old tiles if memory pressure
    if tc.GetMemoryUsage() > tc.MaxMemory {
        tc.CleanupOldTiles()
    }
    
    return loadedTiles
}
```

#### Parallel Tile Loading (Google Maps Style)
```go
func (tc *TileCache) LoadTilesParallel(coords []TileCoordinate) []*Tile {
    tiles := make([]*Tile, len(coords))
    var wg sync.WaitGroup
    
    for i, coord := range coords {
        wg.Add(1)
        go func(index int, c TileCoordinate) {
            defer wg.Done()
            
            // Try Redis cache first
            tile := tc.LoadFromRedis(c)
            if tile == nil {
                // Load from database
                tile = tc.LoadFromDatabase(c)
                // Cache in Redis for next time
                tc.SaveToRedis(tile)
            }
            
            tiles[index] = tile
            tc.ActiveTiles[tile.CacheKey] = tile
        }(i, coord)
    }
    
    wg.Wait()
    return tiles
}
```

#### Database Query for Tile
```go
func (tc *TileCache) LoadFromDatabase(coord TileCoordinate) *Tile {
    // Calculate tile bounds
    bounds := CalculateTileBounds(coord)
    
    // Query only objects in this tile and zoom level
    query := `
        SELECT * FROM arxobjects 
        WHERE 
            ST_Intersects(position, ST_MakeEnvelope($1, $2, $3, $4))
            AND zoom_min <= $5 
            AND zoom_max >= $5
            AND (
                -- Performance optimization: skip tiny objects at high zoom
                CASE 
                    WHEN $5 > 10 THEN optimal_zoom >= 5
                    WHEN $5 > 5 THEN optimal_zoom >= 1
                    ELSE true
                END
            )
        ORDER BY 
            importance_level DESC,  -- Most important first
            system_plane_zorder ASC -- Proper layering
        LIMIT 1000  -- Prevent tile overload
    `
    
    objects := db.Query(query, 
        bounds.MinX, bounds.MinY, bounds.MaxX, bounds.MaxY, 
        coord.Z)
    
    return &Tile{
        Z: coord.Z,
        X: coord.X,
        Y: coord.Y,
        Bounds: bounds,
        Objects: objects,
        Loaded: true,
        CacheKey: fmt.Sprintf("%d/%d/%d", coord.Z, coord.X, coord.Y),
    }
}
```

#### Predictive Prefetching
```go
func (tc *TileCache) PrefetchAdjacentTiles(viewport Viewport, zoom int) {
    // Calculate movement vector from last viewport
    movement := CalculateMovementVector(tc.LastViewport, viewport)
    
    // Predict which tiles user will need next
    predictedTiles := []TileCoordinate{}
    
    if movement.IsMoving() {
        // User is panning - prefetch in direction of movement
        predictedTiles = GetTilesInDirection(viewport, movement.Direction, zoom)
    } else {
        // User is stationary - prefetch all adjacent tiles
        predictedTiles = GetAdjacentTiles(viewport, zoom)
    }
    
    // Load predicted tiles with lower priority
    for _, coord := range predictedTiles {
        tileKey := fmt.Sprintf("%d/%d/%d", coord.Z, coord.X, coord.Y)
        
        if _, exists := tc.PrefetchTiles[tileKey]; !exists {
            go func(c TileCoordinate) {
                tile := tc.LoadFromDatabase(c)
                tc.PrefetchTiles[tile.CacheKey] = tile
            }(coord)
        }
    }
}
```

#### Progressive Detail Loading
```go
func (tc *TileCache) LoadTileProgressive(coord TileCoordinate) *Tile {
    tile := &Tile{
        Z: coord.Z,
        X: coord.X,
        Y: coord.Y,
    }
    
    // Step 1: Load basic geometry immediately (fast)
    tile.Objects = tc.LoadBasicGeometry(coord)
    
    // Step 2: Load properties asynchronously (slower)
    go func() {
        properties := tc.LoadDetailedProperties(coord)
        for i, obj := range tile.Objects {
            if props, exists := properties[obj.ID]; exists {
                tile.Objects[i].Properties = props
            }
        }
        tile.FullyLoaded = true
    }()
    
    return tile
}
```

#### Memory Management
```go
func (tc *TileCache) CleanupOldTiles() {
    // Sort tiles by last access time
    tiles := tc.GetAllTiles()
    sort.Slice(tiles, func(i, j int) bool {
        return tiles[i].LastAccessed.Before(tiles[j].LastAccessed)
    })
    
    // Remove oldest tiles until under memory limit
    currentMemory := tc.GetMemoryUsage()
    for _, tile := range tiles {
        if currentMemory < tc.MaxMemory * 0.8 {  // Keep 20% buffer
            break
        }
        
        // Don't remove currently visible tiles
        if time.Since(tile.LastAccessed) > 30*time.Second {
            delete(tc.ActiveTiles, tile.CacheKey)
            currentMemory -= tile.Size
        }
    }
}
```

#### Client-Side Tile Rendering
```javascript
class TileRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.tiles = new Map();
        this.loading = new Set();
        this.viewport = null;
        this.zoom = 1;
    }
    
    async updateViewport(viewport, zoom) {
        this.viewport = viewport;
        this.zoom = zoom;
        
        // Calculate needed tiles
        const neededTiles = this.calculateNeededTiles(viewport, zoom);
        
        // Load tiles in parallel
        const loadPromises = neededTiles
            .filter(key => !this.tiles.has(key) && !this.loading.has(key))
            .map(key => this.loadTile(key));
        
        await Promise.all(loadPromises);
        
        // Render all visible tiles
        this.render();
        
        // Prefetch adjacent tiles
        this.prefetchAdjacent(viewport, zoom);
    }
    
    async loadTile(tileKey) {
        this.loading.add(tileKey);
        
        try {
            const response = await fetch(`/api/tiles/${tileKey}`);
            const tileData = await response.json();
            
            this.tiles.set(tileKey, {
                data: tileData,
                loaded: Date.now(),
                rendered: false
            });
            
            // Render this tile immediately
            this.renderTile(tileKey);
        } finally {
            this.loading.delete(tileKey);
        }
    }
    
    renderTile(tileKey) {
        const tile = this.tiles.get(tileKey);
        if (!tile) return;
        
        // Transform tile coordinates to canvas coordinates
        const [z, x, y] = tileKey.split('/').map(Number);
        const tileSize = 256; // pixels per tile
        const scale = Math.pow(2, this.zoom - z);
        
        const canvasX = (x * tileSize - this.viewport.x) * scale;
        const canvasY = (y * tileSize - this.viewport.y) * scale;
        
        // Render ArxObjects in this tile
        tile.data.objects.forEach(obj => {
            this.renderArxObject(obj, canvasX, canvasY, scale);
        });
        
        tile.rendered = true;
    }
    
    // Clean up old tiles (like Google Maps)
    cleanupTiles() {
        const now = Date.now();
        const maxAge = 60000; // 60 seconds
        
        for (const [key, tile] of this.tiles) {
            if (now - tile.loaded > maxAge && !this.isTileVisible(key)) {
                this.tiles.delete(key);
            }
        }
    }
}
```

### Dynamic Loading with Overlap Handling
```go
func GetVisibleObjects(viewport Viewport, zoomLevel float64, viewMode string) []ArxObject {
    // Use tile cache for efficient loading
    tileCache := GetTileCache()
    tiles := tileCache.LoadVisibleTiles(viewport, int(zoomLevel))
    
    // Aggregate objects from all loaded tiles
    objects := []ArxObject{}
    for _, tile := range tiles {
        objects = append(objects, tile.Objects...)
    }
    
    // Apply view mode filters
    switch viewMode {
    case "all_systems":
        return objects
    case "electrical_only":
        return FilterBySystem(objects, "electrical")
    case "no_above_ceiling":
        return FilterByElevation(objects, "floor", "wall", "ceiling")
    }
    
    return objects
}
```

## User Interaction with Overlapping Objects

### Click Handling
```go
func HandleClick(x, y float64) ClickResult {
    // Find ALL objects at this position (considering overlaps)
    objectsAtPosition := GetObjectsAtPoint(x, y)
    
    if len(objectsAtPosition) == 0 {
        return ClickResult{Type: "empty"}
    }
    
    if len(objectsAtPosition) == 1 {
        return ClickResult{Type: "single", Object: objectsAtPosition[0]}
    }
    
    // Multiple overlapping objects - show selection menu
    return ClickResult{
        Type: "multiple",
        Objects: SortByZOrder(objectsAtPosition),
        ShowUI: "overlap_selector",
    }
}
```

### Visualization Modes for Overlaps
```go
type ViewMode struct {
    Name string
    Config ViewConfig
}

var ViewModes = []ViewMode{
    {
        Name: "All Systems",
        Config: ViewConfig{
            ShowAll: true,
            Opacity: 0.8,  // Slight transparency to see overlaps
        },
    },
    {
        Name: "System Isolation",
        Config: ViewConfig{
            IsolateSystem: "electrical",
            GhostOthers: true,
            GhostOpacity: 0.2,
        },
    },
    {
        Name: "Exploded View",
        Config: ViewConfig{
            ExplodeOverlaps: true,
            ExplosionDistance: 500,  // 500mm separation
        },
    },
    {
        Name: "By Elevation",
        Config: ViewConfig{
            ShowElevations: []string{"floor", "wall", "ceiling"},
            HideElevations: []string{"above_ceiling", "underground"},
        },
    },
}
```

## BILT Reward Calculation

```go
func CalculateBILTReward(contribution Contribution) float64 {
    baseReward := 1.0
    
    // Detail level multiplier
    detailMultiplier := map[string]float64{
        "building":  1.0,   // Adding building outline
        "floor":     1.5,   // Adding floor plan
        "room":      2.0,   // Adding room details
        "fixture":   2.5,   // Adding fixtures/outlets
        "component": 3.0,   // Adding component specs
        "wiring":    4.0,   // Adding wiring diagrams
        "overlap":   1.5,   // Resolving overlap relationships
    }
    
    // Quality multiplier
    qualityMultiplier := 1.0
    if contribution.HasPhoto {
        qualityMultiplier += 0.5
    }
    if contribution.HasSpecs {
        qualityMultiplier += 0.5
    }
    if contribution.ResolvedOverlap {
        qualityMultiplier += 0.3  // Bonus for clarifying overlaps
    }
    
    return baseReward * detailMultiplier[contribution.Level] * qualityMultiplier
}
```

## Implementation Phases

### Phase 1: Core ArxObject Engine (Weeks 1-2)
1. Implement complete ArxObject struct with overlap handling
2. Create PostgreSQL schema with spatial indexes
3. Build CRUD operations
4. Implement Z-order layer system

### Phase 2: Symbol Library (Weeks 3-4)
1. Create symbol database for all systems
2. Build pattern matching engine
3. Test with real PDFs
4. Implement symbol contribution system

### Phase 3: Ingestion Pipeline (Weeks 5-6)
1. PDF parser with symbol recognition
2. Overlap detection algorithm
3. Automatic layer assignment
4. Relationship inference

### Phase 4: Fractal Visualization (Weeks 7-8)
1. Multi-layer rendering engine
2. Overlap selection UI
3. System isolation views
4. Exploded view mode

### Phase 5: Contribution System (Weeks 9-10)
1. Contribution tracking
2. BILT reward calculation
3. Overlap resolution rewards
4. Quality validation

## Critical Success Factors

1. **Overlap Resolution** - Must handle complex mechanical rooms with 20+ overlapping systems
2. **Performance** - Must render 10,000+ objects smoothly
3. **Accuracy** - Symbol recognition must be 95%+ accurate
4. **User Experience** - Clicking overlaps must feel intuitive
5. **Data Integrity** - Never lose information due to overlaps

## The Complete System Flow

1. **Upload** - Engineer uploads PDF floor plan
2. **Recognition** - System uses Symbol Library to identify all objects
3. **Creation** - Each symbol becomes an ArxObject with proper layer
4. **Overlap Detection** - System finds all overlapping objects
5. **Resolution** - Assigns Z-orders and relationships
6. **Indexing** - Objects indexed by system (electrical, HVAC, etc.)
7. **Visualization** - Rendered with proper layering
8. **Interaction** - Click shows all objects at location
9. **Contribution** - Field workers enhance with photos/specs
10. **Rewards** - BILT tokens for contributions

This is the complete ArxObject specification - your single source of truth for building the system.