# ArxOS Terminal Data Visualization Architecture

## Executive Summary

This document outlines the comprehensive design and architecture for integrating PostGIS-powered spatial visualizations directly into the ArxOS terminal interface. Built on **Clean Architecture principles** with **go-blueprint patterns**, ArxOS leverages modern terminal capabilities (Unicode, 256 colors, box-drawing characters) and PostGIS spatial queries to provide rich spatial data visualization with bidirectional control without requiring a web browser or 3D interface.

## Core Philosophy

- **Clean Architecture**: Terminal visualizations follow Clean Architecture principles with clear separation of concerns
- **PostGIS-Powered**: All visualizations query PostGIS spatial database for real-time data
- **Bidirectional Control**: Terminal visualizations allow direct spatial data modification
- **Terminal-First**: All visualizations must work in a standard terminal emulator
- **Progressive Enhancement**: Use colors and Unicode when available, fallback to ASCII
- **Actionable Insights**: Every visualization should lead to executable PostGIS commands
- **Spatial Intelligence**: Leverage PostGIS spatial functions for advanced visualizations
- **Performance**: Visualizations should render in <100ms for responsive feel
- **Real-time Updates**: Visualizations reflect PostGIS changes immediately
- **Dependency Injection**: Terminal components use dependency injection for better testability

## Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│                CLI Spatial Commands                     │
│  (query, update, move, add, analyze, monitor)          │
│              ↕ (Bidirectional Control)                 │
└─────────────────────┬──────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────┐
│                PostGIS Database                         │
│            (Single Source of Truth)                     │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ST_Distance, ST_Contains, ST_Within, ST_Buffer  │  │
│  │ Spatial indexes, 3D coordinates, relationships │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────┬──────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────┐
│              Spatial Visualization Engine               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Renderer   │  │Spatial Mapper│  │ Layout Engine│ │
│  │   - ASCII    │  │- PostGIS Query│  │  - Grid      │ │
│  │   - Unicode  │  │- Coordinate   │  │  - Flow      │ │
│  │   - Colors   │  │  Transform   │  │  - Spatial   │ │
│  └─────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────┬──────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────┐
│           Interactive Terminal Output                   │
│    (Click to modify PostGIS, real-time updates)        │
└─────────────────────────────────────────────────────────┘
```

## Package Structure

```
internal/visualization/
├── core/
│   ├── renderer.go      # Base renderer interface
│   ├── canvas.go        # Terminal canvas abstraction
│   ├── colors.go        # Color schemes and theming
│   ├── symbols.go       # Unicode/ASCII symbol sets
│   └── postgis.go       # PostGIS query interface for visualizations
├── charts/
│   ├── bar.go           # Bar charts from PostGIS aggregations
│   ├── line.go          # Line charts and sparklines
│   ├── heatmap.go       # 2D spatial heatmaps from PostGIS
│   ├── tree.go          # Building hierarchy views
│   ├── gauge.go         # Gauges and progress indicators
│   ├── table.go         # Enhanced spatial data tables
│   ├── spatial.go       # NEW: Spatial relationship visualizations
│   └── floor_plan.go    # NEW: ASCII floor plans from PostGIS
├── spatial/
│   ├── queries.go       # PostGIS spatial query builders
│   ├── proximity.go     # Proximity and distance visualizations
│   ├── containment.go   # Spatial containment charts
│   └── clustering.go    # Equipment clustering visualizations
├── interactive/
│   ├── editor.go        # Interactive spatial editing in terminal
│   ├── commands.go      # Command generation from visual interactions
│   └── feedback.go      # Real-time PostGIS update feedback
├── layouts/
│   ├── dashboard.go     # Multi-chart dashboard layouts
│   ├── grid.go          # Grid-based positioning
│   ├── spatial_grid.go  # NEW: Spatial coordinate grid layouts
│   └── responsive.go    # Terminal size adaptation
└── examples/
    ├── demo.go          # Interactive demo of all charts
    └── spatial_demo.go  # NEW: Spatial visualization demos
```

## Core Components

### 1. PostGIS Visualization Interface

```go
package visualization

type PostGISVisualizer struct {
    db       *database.PostGISDB
    renderer Renderer
}

// Query PostGIS and visualize spatial relationships
func (pv *PostGISVisualizer) RenderSpatialQuery(query string, args []interface{}) (string, error) {
    // 1. Execute PostGIS spatial query
    results, err := pv.db.QuerySpatial(query, args...)
    if err != nil {
        return "", err
    }
    
    // 2. Convert spatial results to visualization data
    spatialData := pv.transformSpatialResults(results)
    
    // 3. Render using appropriate chart type
    return pv.renderer.RenderSpatial(spatialData)
}

// Interactive spatial editing in terminal
func (pv *PostGISVisualizer) InteractiveEdit(buildingID string) error {
    // 1. Display current spatial layout
    layout := pv.RenderFloorPlan(buildingID)
    fmt.Print(layout)
    
    // 2. Allow user to click/select equipment
    selected := pv.captureUserSelection()
    
    // 3. Generate PostGIS update command
    command := pv.generateSpatialCommand(selected)
    
    // 4. Execute and show real-time feedback
    return pv.executeWithFeedback(command)
}

// Real-time visualization updates from PostGIS changes
func (pv *PostGISVisualizer) StreamUpdates(buildingID string) {
    for change := range pv.db.ChangeStream(buildingID) {
        // Re-render affected visualizations
        pv.updateVisualization(change)
    }
}
```

### 2. Renderer Engine

```go
package visualization

type Renderer interface {
    // Core rendering method
    Render(data DataSet, options RenderOptions) (Canvas, error)

    // Get dimensions
    GetDimensions() (width, height int)

    // Capability detection
    SupportsUnicode() bool
    SupportsColors() bool
    Supports256Colors() bool
    SupportsTrueColor() bool
}

type RenderOptions struct {
    Width        int
    Height       int
    ColorScheme  ColorScheme
    SymbolSet    SymbolSet  // ASCII, Unicode, or Custom
    Title        string
    ShowLegend   bool
    ShowAxes     bool
    Interactive  bool        // For future: mouse support
}

type Canvas struct {
    cells    [][]Cell
    width    int
    height   int
}

type Cell struct {
    Char       rune
    Foreground Color
    Background Color
    Bold       bool
    Dim        bool
}
```

### 2. Chart Types

#### Bar Chart
```go
type BarChart struct {
    renderer Renderer
}

func (b *BarChart) Render(data []DataPoint) string {
    // Example output:
    // Equipment Status by Floor:
    // Floor 5  ████████████████░░░░ 80% (40/50)
    // Floor 4  ███████████████████░ 95% (38/40)
    // Floor 3  █████████░░░░░░░░░░░ 45% (27/60)
}
```

#### Sparkline
```go
type Sparkline struct {
    renderer Renderer
}

func (s *Sparkline) Render(values []float64) string {
    // Example output:
    // Power: ▁▂▃▅▇█▇▅▃▃▂▁▁▂▃▅▇█▇▅▃▂▁▁ (24hr)
}
```

#### Heatmap
```go
type Heatmap struct {
    renderer Renderer
}

func (h *Heatmap) Render(matrix [][]float64) string {
    // Example output:
    // Energy Usage (kWh/sqft):
    //      A    B    C    D    E
    // 5  [█▓▓][▒▒▒][░░░][▒▒▒][▓▓█]
    // 4  [▒▒▒][░░░][   ][░░░][▒▒▓]
    // 3  [░░░][   ][   ][░░░][▒▒▒]
}
```

#### Tree View
```go
type TreeView struct {
    renderer Renderer
}

func (t *TreeView) Render(root *TreeNode) string {
    // Example output:
    // ARXOS-001/
    // ├─ HVAC/ (92% efficient)
    // │  ├─ AHU-01 ✓ operational
    // │  └─ AHU-02 ⚠ maintenance
    // └─ Power/ (98% uptime)
    //    └─ PANEL-A ✓ 45A/100A
}
```

#### NEW: Spatial Floor Plan View
```go
type SpatialFloorPlan struct {
    postgis  *database.PostGISDB
    renderer Renderer
}

func (sfp *SpatialFloorPlan) RenderFloor(buildingID string, floor int) string {
    // Query PostGIS for equipment positions
    equipment := sfp.postgis.QueryFloorEquipment(buildingID, floor)
    
    // Example output with precise positioning:
    // Floor 3 Layout (1 unit = 0.5m):
    // ┌─────────────────────────────────────┐
    // │ CONF_A    │           │    OFFICE_B │
    // │     🔌₁   │           │  💻₃     🔌₄│ 
    // │           │  HALLWAY  │             │
    // │     📺₂   │    💡₅    │        📞₆ │
    // └─────────────────────────────────────┘
    // 
    // Equipment (PostGIS coordinates):
    // 🔌₁ OUTLET_01: (12.547, 8.291, 1.127) [Click to edit]
    // 📺₂ DISPLAY_01: (12.1, 7.8, 1.2) [Click to edit]
    // 💻₃ COMPUTER_01: (15.2, 8.5, 0.75) [Click to edit]
}

// Interactive editing capability
func (sfp *SpatialFloorPlan) HandleClick(x, y int) string {
    // Convert terminal coordinates to PostGIS query
    equipment := sfp.findEquipmentAt(x, y)
    if equipment != nil {
        return fmt.Sprintf("Selected: %s\nCommands:\n  arx update %s --location \"x,y,z\"\n  arx move %s --by \"dx,dy,dz\"", 
                          equipment.ID, equipment.Path, equipment.Path)
    }
    return "Click on equipment to edit position"
}
```

#### NEW: Spatial Proximity Visualization  
```go
type ProximityChart struct {
    postgis  *database.PostGISDB
    renderer Renderer
}

func (pc *ProximityChart) RenderNearby(centerEquipment string, radius float64) string {
    // PostGIS spatial query
    nearby := pc.postgis.FindWithinRadius(centerEquipment, radius)
    
    // Example output:
    // Equipment within 2.0m of OUTLET_02:
    // 
    //     SWITCH_01 ●────1.2m────● OUTLET_02 (center)
    //                              │
    //                            0.8m
    //                              │
    //                           PANEL_A ●
    // 
    // Spatial Commands:
    // arx query --near "12.547,8.291,1.127" --radius 2.0
    // arx update SWITCH_01 --move-to "12.0,8.0,1.1"
}
```

#### NEW: System Tracing Visualization
```go
type SystemTracer struct {
    postgis  *database.PostGISDB
    renderer Renderer
}

func (st *SystemTracer) RenderPowerTrace(startEquipment string) string {
    // PostGIS query for power connections using spatial relationships
    query := `
        WITH RECURSIVE power_trace AS (
            SELECT id, name, geom, 0 as level
            FROM equipment WHERE id = $1
            UNION
            SELECT e.id, e.name, e.geom, pt.level + 1
            FROM equipment e, power_trace pt
            WHERE ST_DWithin(e.geom, pt.geom, 50) -- 50m max connection distance
            AND e.equipment_type LIKE 'electrical%'
            AND pt.level < 10
        )
        SELECT * FROM power_trace ORDER BY level
    `
    
    // Example output:
    // Power Trace from OUTLET_02:
    // 
    // OUTLET_02 ●─────────┐
    //                     │ 15.2m
    //                     ▼
    // PANEL_A ●───────────┐
    //                     │ 45.8m  
    //                     ▼
    // MAIN_ELECTRICAL ●───┐
    //                     │ 12.1m
    //                     ▼
    // TRANSFORMER ●
    // 
    // Trace Commands:
    // arx trace OUTLET_02 --type power --visualize path
    // arx update PANEL_A --location "x,y,z" # Update connection point
}
```

#### NEW: 3D Cross-Section View
```go
type CrossSectionView struct {
    postgis  *database.PostGISDB
    renderer Renderer
}

func (csv *CrossSectionView) RenderVerticalSlice(buildingID string, slicePlane string) string {
    // PostGIS query for vertical cross-section
    query := `
        SELECT e.id, e.name, e.equipment_type, 
               ST_Z(e.geom) as height, ST_Distance(e.geom, $2) as distance
        FROM equipment e, buildings b
        WHERE e.building_id = b.id AND b.arxos_id = $1
        AND ST_DWithin(e.geom, ST_GeomFromText($2), 1.0) -- 1m slice width
        ORDER BY ST_Z(e.geom) DESC
    `
    
    // Example output:
    // Vertical Cross-Section (North-South @ X=12.5m):
    // 
    // 15m ┤
    //     │  🏢 ROOF_UNIT_01
    // 12m ┤
    //     │
    //  9m ┤  💡 LIGHT_03
    //     │
    //  6m ┤  💡 LIGHT_02
    //     │
    //  3m ┤  💡 LIGHT_01    🔌 OUTLET_02
    //     │
    //  0m └────────────────────────────────
    //     0m    5m    10m   15m   20m
    // 
    // Cross-section Commands:
    // arx view --cross-section "LINESTRING(0 12.5, 25 12.5)" --visualize vertical
    // arx update LIGHT_03 --height 8.5 # Adjust height
}
```

#### NEW: Equipment Status Overlay
```go
type StatusOverlay struct {
    postgis  *database.PostGISDB
    renderer Renderer
}

func (so *StatusOverlay) RenderFloorStatus(buildingID string, floor int) string {
    // PostGIS query for equipment with status
    query := `
        SELECT e.id, e.name, e.status, ST_X(e.geom), ST_Y(e.geom),
               CASE e.status 
                   WHEN 'OPERATIONAL' THEN '✓'
                   WHEN 'WARNING' THEN '⚠'
                   WHEN 'FAILED' THEN '✗'
                   WHEN 'MAINTENANCE' THEN '🔧'
                   ELSE '?'
               END as status_symbol
        FROM equipment e
        JOIN floors f ON ST_Intersects(e.geom, f.geom)
        WHERE f.building_id = $1 AND f.level = $2
    `
    
    // Example output:
    // Floor 3 Equipment Status:
    // ┌─────────────────────────────────────┐
    // │ CONF_A    │           │    OFFICE_B │
    // │     ✓₁    │           │  ⚠₃     ✓₄ │ 
    // │           │  HALLWAY  │             │
    // │     ✗₂    │    ✓₅     │        🔧₆ │
    // └─────────────────────────────────────┘
    // 
    // Status Summary: ✓ 3 operational, ⚠ 1 warning, ✗ 1 failed, 🔧 1 maintenance
    // 
    // Status Commands:
    // arx update OUTLET_02 --status operational
    // arx query --status failed --floor 3 --visualize status-overlay
}
```

#### NEW: Confidence Heatmap
```go
type ConfidenceHeatmap struct {
    postgis  *database.PostGISDB
    renderer Renderer
}

func (ch *ConfidenceHeatmap) RenderConfidence(buildingID string, floor int) string {
    // PostGIS query for confidence levels with spatial clustering
    query := `
        SELECT ST_X(e.geom), ST_Y(e.geom), 
               CASE e.position_confidence
                   WHEN 'HIGH' THEN 3
                   WHEN 'MEDIUM' THEN 2  
                   WHEN 'LOW' THEN 1
                   ELSE 0
               END as confidence_value
        FROM equipment e
        JOIN floors f ON ST_Intersects(e.geom, f.geom)  
        WHERE f.building_id = $1 AND f.level = $2
    `
    
    // Example output:
    // Floor 3 Data Confidence Heatmap:
    //      A    B    C    D    E
    // 5  [███][▓▓▓][░░░][▓▓▓][███]  ← High confidence (LiDAR verified)
    // 4  [▓▓▓][░░░][   ][░░░][▓▓▓]  ← Medium confidence (IFC + AR)
    // 3  [░░░][   ][   ][░░░][▓▓▓]  ← Low confidence (PDF estimated)
    // 
    // Legend: ███ High (LiDAR/AR), ▓▓▓ Medium (IFC), ░░░ Low (PDF), [   ] No data
    // 
    // Confidence Commands:
    // arx query --confidence high --floor 3
    // arx analyze coverage --building ARXOS-001 --visualize confidence
}
```

### 3. Enhanced Symbol Sets (Spatial & Building-Specific)

```go
type SymbolSet struct {
    // Bar chart symbols
    BarFull      rune
    BarEmpty     rune
    BarPartial   []rune  // For fractional bars

    // Box drawing
    BoxTopLeft   rune
    BoxTopRight  rune
    BoxHoriz     rune
    BoxVert      rune

    // Tree symbols
    TreeBranch   rune
    TreeMid      rune
    TreeEnd      rune

    // Status indicators
    CheckMark    rune
    Warning      rune
    Error        rune
    Info         rune
    
    // NEW: Equipment symbols
    Outlet       rune
    Switch       rune
    Panel        rune
    HVAC         rune
    Light        rune
    Computer     rune
    Camera       rune
    Sensor       rune
    
    // NEW: Spatial relationship symbols
    Connection   rune
    Distance     rune
    Boundary     rune
    Center       rune
    
    // NEW: Confidence indicators
    HighConf     rune
    MediumConf   rune
    LowConf      rune
    NoData       rune
    
    // NEW: System connection symbols
    PowerLine    rune
    NetworkLine  rune
    PlumbingLine rune
    HVACLine     rune
}

var ASCIISymbols = SymbolSet{
    BarFull:     '#',
    BarEmpty:    '-',
    BoxTopLeft:  '+',
    BoxHoriz:    '-',
    TreeBranch:  '|',
    TreeMid:     '+-',
    TreeEnd:     '+-',
    CheckMark:   '[OK]',
    Warning:     '[!]',
    Error:       '[X]',
    
    // Equipment (ASCII)
    Outlet:      'O',
    Switch:      'S',
    Panel:       'P',
    HVAC:        'H',
    Light:       'L',
    Computer:    'C',
    Camera:      'M',
    Sensor:      'T',
    
    // Spatial (ASCII)
    Connection:  '-',
    Distance:    '~',
    Boundary:    '#',
    Center:      '+',
    
    // Confidence (ASCII)
    HighConf:    'H',
    MediumConf:  'M',
    LowConf:     'L',
    NoData:      '.',
    
    // System connections (ASCII)
    PowerLine:   '=',
    NetworkLine: '-',
    PlumbingLine: '~',
    HVACLine:    '≈',
}

var UnicodeSymbols = SymbolSet{
    BarFull:     '█',
    BarEmpty:    '░',
    BarPartial:  []rune{'▏','▎','▍','▌','▋','▊','▉'},
    BoxTopLeft:  '┌',
    BoxHoriz:    '─',
    TreeBranch:  '│',
    TreeMid:     '├─',
    TreeEnd:     '└─',
    CheckMark:   '✓',
    Warning:     '⚠',
    Error:       '✗',
    
    // Equipment (Unicode)
    Outlet:      '🔌',
    Switch:      '🔘',
    Panel:       '⚡',
    HVAC:        '🌡️',
    Light:       '💡',
    Computer:    '💻',
    Camera:      '📷',
    Sensor:      '📡',
    
    // Spatial (Unicode)
    Connection:  '──',
    Distance:    '↔',
    Boundary:    '▓',
    Center:      '●',
    
    // Confidence (Unicode)
    HighConf:    '███',
    MediumConf:  '▓▓▓',
    LowConf:     '░░░',
    NoData:      '   ',
    
    // System connections (Unicode)
    PowerLine:   '═',
    NetworkLine: '─',
    PlumbingLine: '≋',
    HVACLine:    '≈',
}
```

### 4. Color Schemes

```go
type ColorScheme struct {
    Primary     Color
    Secondary   Color
    Success     Color
    Warning     Color
    Error       Color
    Info        Color

    // Gradient colors for heatmaps
    GradientLow  Color
    GradientMid  Color
    GradientHigh Color

    // Chart-specific
    BarColors    []Color
    LineColors   []Color
}

var DefaultScheme = ColorScheme{
    Primary:   Blue,
    Success:   Green,
    Warning:   Yellow,
    Error:     Red,
    Info:      Cyan,
}

var MonochromeScheme = ColorScheme{
    // All colors map to different patterns/intensities
}
```

## Integration Points

### 1. Query Command Enhancement (PostGIS-Powered)

```bash
# Spatial visualization flags with PostGIS queries
arx query --building ARXOS-001 --visualize spatial --floor 3
arx query --near "12.5,8.3,1.1" --radius 5.0 --visualize proximity
arx query --building ARXOS-001 --visualize heatmap --metric density
arx query --equipment HVAC --visualize connections --trace-power

# PostGIS spatial queries with visualization
arx query --spatial "ST_Distance(geom, point) < 2" --visualize scatter
arx query --contains "room_polygon" --visualize floor-plan
```

### 2. Spatial Control Commands (Aligned with CLI Structure)

```bash
# CRUD operations with spatial visualization feedback
arx update /3/A/301/E/OUTLET_02 --location "12.547,8.291,1.127" --show-impact
arx update /3/A/301/E/OUTLET_02 --move-by "0.05,0,0" --visualize changes
arx add /3/A/301/E/OUTLET_03 --location "12.6,8.3,1.1" --type outlet --preview

# Trace command with spatial visualization
arx trace /3/A/301/E/OUTLET_02 --type power --visualize path --depth 5
arx trace /3/A/301/N/HVAC_01 --type hvac --visualize connections

# Spatial validation with visualization
arx query --building ARXOS-001 --spatial --visualize conflicts
arx query --floor 3 --analyze spacing --visualize density
```

### 3. Enhanced Monitor Command (PostGIS Real-time)

```bash
# Real-time PostGIS monitoring with spatial visualizations
arx monitor --building ARXOS-001 --spatial --refresh 5s
arx monitor --equipment HVAC/* --visualize spatial-status
arx monitor --floor 3 --proximity --center "12.5,8.3,1.1" --radius 5.0
```

### 4. Enhanced Analyze Command (Spatial Analysis)

```bash
# PostGIS spatial analysis with visualizations
arx analyze spatial --building ARXOS-001 --clustering equipment
arx analyze efficiency --building ARXOS-001 --spatial-correlation
arx analyze patterns --system HVAC --spatial-proximity
arx analyze coverage --building ARXOS-001 --confidence-heatmap
```

### 4. Report Command

```bash
# Generate terminal-based reports with embedded visualizations
arx report daily --building ARXOS-001 --output terminal
arx report maintenance --upcoming 30d --visualize gantt
```

### 5. Dashboard Command

```bash
# Full terminal dashboard with multiple live visualizations
arx dashboard
arx dashboard --layout energy-focus
arx dashboard --building ARXOS-001 --floor 3
```

## Implementation Phases

### Phase 1: PostGIS Integration Foundation (Week 1-2)
- [ ] Set up `internal/visualization` package structure with PostGIS interface
- [ ] Implement PostGIS query interface for visualizations
- [ ] Create spatial data transformation pipeline
- [ ] Add terminal capability detection (colors, Unicode)
- [ ] Implement ASCII and Unicode symbol sets for spatial data

### Phase 2: Spatial Visualizations (Week 3-4)
- [ ] Implement Spatial Floor Plan renderer with PostGIS queries
- [ ] Implement Proximity Chart with ST_Distance operations
- [ ] Implement Spatial Heatmap with PostGIS density functions
- [ ] Add interactive spatial editing capabilities
- [ ] Create unit tests for PostGIS visualization integration

### Phase 3: Advanced Spatial Features (Week 5-6)
- [ ] Implement real-time PostGIS change monitoring
- [ ] Add spatial relationship visualizations (containment, proximity)
- [ ] Implement spatial clustering and density analysis
- [ ] Add coordinate precision indicators and confidence visualization
- [ ] Implement spatial validation and conflict detection visualizations

### Phase 4: CLI Integration (Week 7-8)
- [ ] Enhance `query` command with spatial visualization flags
- [ ] Implement `edit` command for interactive spatial modification
- [ ] Create `analyze` command for spatial pattern analysis
- [ ] Add `monitor` command for real-time spatial updates
- [ ] Implement bidirectional CLI ↔ PostGIS control

### Phase 5: Professional Polish (Week 9-10)
- [ ] Add professional BIM visualization features
- [ ] Optimize PostGIS query performance for large datasets
- [ ] Add spatial precision configuration options
- [ ] Create professional workflow documentation
- [ ] Implement comprehensive spatial testing suite

## Example Implementations

### 1. PostGIS Spatial Bar Chart

```go
func RenderSpatialBarChart(postgis *database.PostGISDB, buildingID string) string {
    // Query PostGIS for equipment density by floor
    query := `
        SELECT f.level, COUNT(e.id) as equipment_count
        FROM floors f
        LEFT JOIN equipment e ON ST_Intersects(e.geom, f.geom)
        WHERE f.building_id = $1
        GROUP BY f.level
        ORDER BY f.level
    `
    
    rows, _ := postgis.Query(query, buildingID)
    defer rows.Close()
    
    var output strings.Builder
    output.WriteString("Equipment Density by Floor (PostGIS):\n")
    
    for rows.Next() {
        var floor int
        var count int
        rows.Scan(&floor, &count)
        
        // Interactive bar with click commands
        bar := strings.Repeat("█", count/2) + strings.Repeat("░", 20-count/2)
        output.WriteString(fmt.Sprintf("Floor %d  %s %d items [arx query --floor %d]\n",
            floor, bar, count, floor))
    }
    
    return output.String()
}
```

### 2. Sparkline Example

```go
func RenderSparkline(values []float64) string {
    sparks := []rune{'▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'}
    min, max := findMinMax(values)

    var output strings.Builder
    for _, v := range values {
        index := int((v - min) / (max - min) * 7)
        if index > 7 { index = 7 }
        if index < 0 { index = 0 }
        output.WriteRune(sparks[index])
    }

    return output.String()
}
```

### 3. PostGIS Spatial Dashboard Example

```go
func RenderSpatialDashboard(postgis *database.PostGISDB, buildingID string) string {
    term := termenv.NewOutput(os.Stdout)
    width, height := getTerminalSize()

    // Create layout grid
    grid := NewGrid(width, height, 2, 2) // 2x2 grid

    // Render each quadrant with PostGIS data
    grid.SetCell(0, 0, RenderSpatialFloorPlan(postgis, buildingID, 3))
    grid.SetCell(0, 1, RenderProximityAnalysis(postgis, buildingID))
    grid.SetCell(1, 0, RenderSpatialAlerts(postgis, buildingID))
    grid.SetCell(1, 1, RenderEquipmentDensity(postgis, buildingID))

    // Add interactive commands at bottom
    grid.AddFooter("Commands: [arx update <id> --location \"x,y,z\"] [arx query --near \"x,y,z\"]")

    return grid.Render()
}

// Interactive spatial floor plan with click-to-edit
func RenderSpatialFloorPlan(postgis *database.PostGISDB, buildingID string, floor int) string {
    // Query PostGIS for precise equipment positions
    query := `
        SELECT id, name, type, ST_X(geom), ST_Y(geom), ST_Z(geom)
        FROM equipment e
        JOIN floors f ON ST_Intersects(e.geom, f.geom)
        WHERE f.building_id = $1 AND f.level = $2
    `
    
    equipment, _ := postgis.QueryEquipmentPositions(query, buildingID, floor)
    
    // Convert PostGIS coordinates to terminal grid
    grid := convertToTerminalGrid(equipment, 40, 20) // 40x20 character grid
    
    var output strings.Builder
    output.WriteString(fmt.Sprintf("Floor %d - Spatial Layout (PostGIS):\n", floor))
    
    for y := 0; y < 20; y++ {
        for x := 0; x < 40; x++ {
            if eq := grid[y][x]; eq != nil {
                output.WriteRune(getEquipmentSymbol(eq.Type))
            } else {
                output.WriteRune(' ')
            }
        }
        output.WriteRune('\n')
    }
    
    // Add equipment legend with precise coordinates
    output.WriteString("\nEquipment (click to edit):\n")
    for _, eq := range equipment {
        output.WriteString(fmt.Sprintf("%s %s: (%.3f, %.3f, %.3f)\n", 
            getEquipmentSymbol(eq.Type), eq.ID, eq.X, eq.Y, eq.Z))
    }
    
    return output.String()
}
```

## Terminal Capability Detection

```go
func DetectCapabilities() TerminalCaps {
    term := termenv.NewOutput(os.Stdout)

    return TerminalCaps{
        Colors:      term.Profile != termenv.Ascii,
        Colors256:   term.Profile >= termenv.ANSI256,
        TrueColor:   term.Profile >= termenv.TrueColor,
        Unicode:     canDisplayUnicode(),
        Width:       getWidth(),
        Height:      getHeight(),
        Interactive: isatty.IsTerminal(os.Stdout.Fd()),
    }
}
```

## Error Handling & Edge Cases

### PostGIS Connection Issues
```go
type VisualizationErrorHandler struct {
    fallbackRenderer Renderer
    postgisDB       *database.PostGISDB // Primary data source
}

func (veh *VisualizationErrorHandler) HandlePostGISFailure(query string) (string, error) {
    // 1. Attempt PostGIS query
    if veh.postgisDB != nil {
        fallbackData, err := veh.postgisDB.QueryBasic(query)
        if err == nil {
            return veh.fallbackRenderer.RenderWithWarning(fallbackData, "Using fallback data - PostGIS unavailable")
        }
    }
    
    // 2. Show helpful error message
    return fmt.Sprintf(`
PostGIS Connection Failed
┌─────────────────────────────────────┐
│ ⚠ Spatial database unavailable     │
│                                     │
│ Troubleshooting:                    │
│ • arx status --check-postgis        │
│ • arx install --setup-postgis       │
│ • Check PostGIS service status      │
└─────────────────────────────────────┘
`), nil
}
```

### Large Dataset Visualization Strategies
```go
func (pv *PostGISVisualizer) HandleLargeDataset(query string, maxResults int) (string, error) {
    // 1. Check result count first
    countQuery := fmt.Sprintf("SELECT COUNT(*) FROM (%s) as count_query", query)
    count, _ := pv.postgis.QueryCount(countQuery)
    
    if count > maxResults {
        // 2. Offer sampling or aggregation options
        return fmt.Sprintf(`
Large Dataset Detected (%d items)
┌─────────────────────────────────────┐
│ 📊 Too many results for visualization│
│                                     │
│ Options:                            │
│ • --limit %d (show first %d)        │
│ • --sample 1000 (random sample)     │
│ • --aggregate floor (group by floor)│
│ • --heatmap (density visualization) │
└─────────────────────────────────────┘
`, count, maxResults, maxResults), nil
    }
    
    return pv.renderNormal(query)
}
```

### Coordinate Precision Display Options
```go
type CoordinatePrecision int

const (
    PrecisionGrid CoordinatePrecision = iota  // Grid coordinates (45, 30)
    PrecisionMeter                            // Meter precision (12.5, 8.3, 1.1)
    PrecisionMillimeter                       // Full precision (12.547, 8.291, 1.127)
    PrecisionDMS                              // Degrees/Minutes/Seconds
)

func (pv *PostGISVisualizer) FormatCoordinates(point Point3D, precision CoordinatePrecision) string {
    switch precision {
    case PrecisionGrid:
        return fmt.Sprintf("(%d, %d)", int(point.X/0.5), int(point.Y/0.5))
    case PrecisionMeter:
        return fmt.Sprintf("(%.1f, %.1f, %.1f)", point.X, point.Y, point.Z)
    case PrecisionMillimeter:
        return fmt.Sprintf("(%.3f, %.3f, %.3f)", point.X, point.Y, point.Z)
    case PrecisionDMS:
        return formatDMS(point)
    }
}
```

### Interactive Editing Validation
```go
func (pv *PostGISVisualizer) ValidateInteractiveEdit(equipmentID string, newLocation Point3D) (string, error) {
    // 1. Check if location is valid (within building bounds)
    inBuilding, err := pv.postgis.CheckWithinBuilding(equipmentID, newLocation)
    if err != nil || !inBuilding {
        return `
❌ Invalid Location
┌─────────────────────────────────────┐
│ Location outside building bounds    │
│                                     │
│ Suggested:                          │
│ • arx query --building bounds       │
│ • arx validate --location "x,y,z"   │
└─────────────────────────────────────┘
`, err
    }
    
    // 2. Check for conflicts with existing equipment
    conflicts, _ := pv.postgis.FindConflicts(newLocation, 0.5) // 50cm buffer
    if len(conflicts) > 0 {
        return fmt.Sprintf(`
⚠ Spatial Conflict Detected
┌─────────────────────────────────────┐
│ %d equipment within 50cm:           │
│ %s                                  │
│                                     │
│ Options:                            │
│ • --force (ignore conflicts)        │
│ • --move-others (auto-adjust)       │
│ • Choose different location         │
└─────────────────────────────────────┘
`, len(conflicts), strings.Join(conflicts, ", ")), nil
    }
    
    return "✅ Location validated", nil
}
```

## Configuration

Users can customize spatial visualizations via `~/.arxos/config/visualization.yaml`:

```yaml
visualization:
  # PostGIS integration
  postgis:
    query_timeout: 30s
    max_results: 1000
    spatial_precision: millimeter
    coordinate_display: decimal  # decimal, dms, or grid

  # Symbol preferences
  symbols: unicode  # ascii, unicode, or nerd-fonts

  # Color preferences
  colors: auto      # auto, 16, 256, true, or none
  theme: default    # default, high-contrast, colorblind, monochrome

  # Spatial visualization defaults
  spatial:
    floor_plan:
      grid_size: 40x20
      show_coordinates: true
      interactive: true
    proximity:
      default_radius: 5.0
      show_distances: true
    heatmap:
      density_function: "ST_Buffer"
      resolution: 1.0  # meters per cell

  # Chart defaults
  defaults:
    bar_chart:
      show_values: true
      show_percentage: true
      data_source: postgis
    sparkline:
      width: 20
      show_trend: true
      real_time: true
    heatmap:
      gradient: blue-red
      spatial_enabled: true

  # Dashboard layouts with PostGIS
  dashboards:
    spatial:
      layout: "2x2"
      refresh: 5s
      data_source: postgis
      widgets:
        - type: spatial_floor_plan
          floor: 3
          interactive: true
        - type: proximity_chart
          center: "auto"
          radius: 5.0
        - type: spatial_heatmap
          metric: equipment_density
        - type: spatial_alerts
          limit: 5
          spatial_filter: true
```

## Professional BIM Visualization Integration

### Real-time IFC Updates in Terminal
```go
type ProfessionalVisualizer struct {
    postgis     *database.PostGISDB
    ifcMonitor  *daemon.IFCWatcher
    renderer    Renderer
}

func (pv *ProfessionalVisualizer) MonitorBIMChanges(buildingID string) {
    // Listen for IFC file changes from daemon
    for change := range pv.ifcMonitor.ChangeStream() {
        // 1. Show what changed in terminal
        diff := pv.renderBIMDiff(change)
        fmt.Print(diff)
        
        // 2. Update any active visualizations
        pv.refreshActiveVisualizations(buildingID)
        
        // 3. Show updated spatial relationships
        if change.HasSpatialChanges() {
            spatial := pv.renderSpatialImpact(change)
            fmt.Print(spatial)
        }
    }
}

func (pv *ProfessionalVisualizer) renderBIMDiff(change *daemon.IFCChange) string {
    return fmt.Sprintf(`
🏗️ BIM Update Detected
┌─────────────────────────────────────┐
│ Source: %s                          │
│ Changed: %d equipment items         │
│ Added: %d items                     │
│ Moved: %d items                     │
│                                     │
│ View Changes:                       │
│ • arx query --building %s --recent  │
│ • arx visualize --changes --floor 3 │
└─────────────────────────────────────┘
`, change.SourceFile, change.ModifiedCount, change.AddedCount, change.MovedCount, change.BuildingID)
}
```

### BIM Coordinate System Visualization
```go
func (pv *ProfessionalVisualizer) RenderCoordinateSystem(buildingID string) string {
    // Query PostGIS for building coordinate system info
    origin, rotation, scale := pv.postgis.GetBuildingTransform(buildingID)
    
    // Example output:
    // Building Coordinate System (ARXOS-001):
    // ┌─────────────────────────────────────┐
    // │ Origin: 40.7128°N, 74.0060°W        │
    // │ Rotation: 15.5° from North          │
    // │ Scale: 1 grid unit = 0.5 meters     │
    // │                                     │
    // │ Coordinate Formats:                 │
    // │ • PostGIS: (12.547, 8.291, 1.127)  │
    // │ • Grid: (25, 17) Floor 3            │
    // │ • IFC: Local(12.547, 8.291, 1.127) │
    // │                                     │
    // │ Transform Commands:                 │
    // │ • arx convert --grid-to-world "25,17" │
    // │ • arx convert --world-to-grid "12.5,8.3" │
    // └─────────────────────────────────────┘
}
```

### Professional User Interface Patterns
```go
type ProfessionalUI struct {
    postgis  *database.PostGISDB
    renderer Renderer
}

// Professional-focused visualization with BIM context
func (pui *ProfessionalUI) RenderProfessionalDashboard(buildingID string) string {
    // Query for professional-relevant metrics
    metrics := pui.postgis.QueryProfessionalMetrics(buildingID)
    
    // Example output:
    // Professional Dashboard - ARXOS-001
    // ┌─────────────────┬─────────────────┐
    // │ Model Status    │ Spatial Quality │
    // │ ✅ IFC Current  │ 🟢 95% Verified │
    // │ 📊 2,847 items  │ 🟡 3% Estimated │
    // │ 🔄 Last: 2m ago │ 🔴 2% Conflicts │
    // ├─────────────────┼─────────────────┤
    // │ Recent Changes  │ Team Activity   │
    // │ • 15 moved      │ 👤 3 active     │
    // │ • 3 added       │ 📱 2 mobile     │
    // │ • 1 removed     │ 💻 1 terminal   │
    // └─────────────────┴─────────────────┘
    // 
    // Professional Commands:
    // arx export --format ifc --precision full
    // arx query --changed --since "2h" --visualize impact
    // arx validate --building ARXOS-001 --professional
}
```

## Technical Implementation Details

### PostGIS Query Optimization for Visualizations
```go
type OptimizedSpatialQuery struct {
    postgis *database.PostGISDB
    cache   map[string]interface{}
}

func (osq *OptimizedSpatialQuery) OptimizeForVisualization(query string, visualizationType string) string {
    switch visualizationType {
    case "floor-plan":
        // Use spatial indexes and limit precision for display
        return osq.addSpatialOptimizations(query, "GIST", "meter")
    case "proximity":
        // Use distance optimization
        return osq.addDistanceOptimizations(query)
    case "heatmap":
        // Use clustering for performance
        return osq.addClusteringOptimizations(query)
    }
    return query
}

func (osq *OptimizedSpatialQuery) addSpatialOptimizations(query, indexType, precision string) string {
    // Add spatial index hints and precision rounding
    optimized := fmt.Sprintf(`
        SELECT id, name, type,
               ROUND(ST_X(geom), 1) as x,  -- Meter precision for display
               ROUND(ST_Y(geom), 1) as y,
               ROUND(ST_Z(geom), 1) as z
        FROM (%s) as base_query
        -- Use spatial index: %s
    `, query, indexType)
    return optimized
}
```

### Coordinate Transformation Algorithms
```go
type CoordinateTransformer struct {
    buildingOrigin Point3D
    gridScale      float64
    terminalBounds Bounds
}

func (ct *CoordinateTransformer) PostGISToTerminalGrid(postgisPoint Point3D, terminalWidth, terminalHeight int) (int, int) {
    // 1. Convert PostGIS coordinates to building-relative coordinates
    relativeX := postgisPoint.X - ct.buildingOrigin.X
    relativeY := postgisPoint.Y - ct.buildingOrigin.Y
    
    // 2. Scale to terminal grid
    gridX := int((relativeX / ct.gridScale) * float64(terminalWidth) / ct.terminalBounds.Width())
    gridY := int((relativeY / ct.gridScale) * float64(terminalHeight) / ct.terminalBounds.Height())
    
    // 3. Clamp to terminal bounds
    gridX = max(0, min(gridX, terminalWidth-1))
    gridY = max(0, min(gridY, terminalHeight-1))
    
    return gridX, gridY
}

func (ct *CoordinateTransformer) TerminalToPostGIS(terminalX, terminalY, terminalWidth, terminalHeight int) Point3D {
    // Reverse transformation for interactive editing
    relativeX := (float64(terminalX) / float64(terminalWidth)) * ct.terminalBounds.Width() * ct.gridScale
    relativeY := (float64(terminalY) / float64(terminalHeight)) * ct.terminalBounds.Height() * ct.gridScale
    
    return Point3D{
        X: ct.buildingOrigin.X + relativeX,
        Y: ct.buildingOrigin.Y + relativeY,
        Z: ct.buildingOrigin.Z, // Default to ground level
    }
}
```

### Interactive State Management
```go
type InteractiveState struct {
    selectedEquipment string
    editMode         EditMode
    pendingChanges   []PendingChange
    visualizationCache map[string]string
}

type EditMode int
const (
    ModeView EditMode = iota
    ModeSelect
    ModeMove
    ModeAdd
    ModeDelete
)

func (is *InteractiveState) HandleKeyPress(key rune) (*Command, error) {
    switch is.editMode {
    case ModeSelect:
        return is.handleSelectionKey(key)
    case ModeMove:
        return is.handleMovementKey(key)
    case ModeAdd:
        return is.handleAdditionKey(key)
    }
    return nil, nil
}

func (is *InteractiveState) generatePostGISCommand(action string) *Command {
    if is.selectedEquipment == "" {
        return nil
    }
    
    switch action {
    case "move":
        return &Command{
            Type: "update",
            Args: []string{is.selectedEquipment, "--move-by", is.getMovementDelta()},
        }
    case "delete":
        return &Command{
            Type: "remove",
            Args: []string{is.selectedEquipment, "--cascade"},
        }
    }
    return nil
}
```

### Real-time Update Architecture
```go
type RealTimeUpdater struct {
    postgis      *database.PostGISDB
    activeViews  map[string]*ActiveVisualization
    updateQueue  chan UpdateEvent
}

type UpdateEvent struct {
    Type        string    // "equipment_moved", "equipment_added", "status_changed"
    EquipmentID string
    OldValue    interface{}
    NewValue    interface{}
    Timestamp   time.Time
}

func (rtu *RealTimeUpdater) StartUpdateMonitor() {
    // Listen for PostGIS NOTIFY events
    listener := pq.NewListener(rtu.postgis.ConnectionString(), 10*time.Second, time.Minute, nil)
    listener.Listen("equipment_changes")
    
    for {
        select {
        case notification := <-listener.Notify:
            event := parseUpdateEvent(notification.Extra)
            rtu.updateQueue <- event
            
        case event := <-rtu.updateQueue:
            rtu.processUpdate(event)
        }
    }
}

func (rtu *RealTimeUpdater) processUpdate(event UpdateEvent) {
    // Update all active visualizations that might be affected
    for viewID, view := range rtu.activeViews {
        if view.isAffectedBy(event) {
            refreshed := view.refresh(event)
            view.redraw(refreshed)
        }
    }
}
```

## Testing Strategy

### Unit Tests
- Test PostGIS query integration for each chart type
- Test spatial coordinate transformation and display
- Test terminal capability detection
- Test color scheme application with spatial data
- Test interactive spatial editing commands
- **NEW**: Test error handling for PostGIS connection failures
- **NEW**: Test coordinate precision display options
- **NEW**: Test interactive editing validation

### PostGIS Integration Tests
- Test spatial query performance with large datasets
- Test real-time PostGIS change detection and visualization updates
- Test bidirectional CLI ↔ PostGIS command generation
- Test spatial precision maintenance across visualizations
- **NEW**: Test coordinate transformation accuracy
- **NEW**: Test interactive state management
- **NEW**: Test professional BIM integration workflows

### Visual Regression Tests
- Capture spatial visualization output snapshots
- Compare PostGIS query results against expected visualizations
- Test interactive command generation accuracy
- Flag any spatial precision or visualization changes
- **NEW**: Test symbol set rendering across different terminals
- **NEW**: Test error message formatting and clarity

### Professional Workflow Tests
- Test visualization integration with BIM professional workflows
- Test real-time updates from IFC imports
- Test spatial visualization accuracy against known BIM coordinates
- **NEW**: Test professional dashboard metrics and layout
- **NEW**: Test coordinate system visualization accuracy
- **NEW**: Test real-time IFC change detection and display

## Performance Targets

- **PostGIS Query + Render**: <100ms for spatial visualizations
- **Spatial Dashboard Render**: <200ms for full PostGIS-powered dashboard
- **Real-time Spatial Updates**: <50ms for PostGIS change visualization
- **Interactive Response**: <25ms for click-to-command generation
- **Memory Usage**: <15MB for spatial dashboard with PostGIS data
- **CPU Usage**: <5% during real-time spatial monitoring
- **PostGIS Connection**: <10ms query response for typical spatial operations

## Accessibility Considerations

1. **Screen Reader Support**
   - Provide text descriptions for all charts
   - Use semantic markers for navigation

2. **Monochrome Support**
   - Use patterns in addition to colors
   - Ensure sufficient contrast

3. **Keyboard Navigation**
   - All interactive elements accessible via keyboard
   - Clear focus indicators

## Future Enhancements

### 1. **Mouse Support** (using terminal mouse protocols)
   - Click on chart elements for details
   - Hover tooltips
   - Drag-and-drop spatial editing

### 2. **Chart Export**
   - Save as ASCII art
   - Export data as CSV
   - Generate HTML reports

### 3. **Custom Widgets**
   - Plugin system for custom visualizations
   - User-defined chart types

### 4. **Animation**
   - Smooth transitions for value changes
   - Loading indicators
   - Alert pulses

### 5. **Particle System for Building Systems** 🌟

#### **Concept**
Real-time particle animation in terminal to visualize building system flows and operations:

```bash
# Energy flow visualization
arx monitor --building ARXOS-001 --particles --system hvac
# Shows air particles flowing through ducts in real-time ASCII

arx trace OUTLET_02 --particles --type power
# Shows electrical flow as animated particles from source to outlet

arx monitor --system network --particles --live
# Shows data packets moving through network infrastructure
```

#### **Particle Types**
```go
type ParticleType int

const (
    ParticleAir      ParticleType = iota // HVAC airflow: ○ → ○ → ○
    ParticlePower                        // Electrical: ⚡ → ⚡ → ⚡  
    ParticleData                         // Network: ● → ● → ●
    ParticleWater                        // Plumbing: ~ → ~ → ~
    ParticleHeat                         // Thermal: ≈ → ≈ → ≈
)
```

#### **Example Visualizations**
```
HVAC System - Real-time Airflow:
┌─────────────────────────────────────┐
│ AHU_01 ≈≈≈○○○→→→ VENT_A             │
│          ≈≈○○→→   ↓                  │
│               ○→→ VENT_B             │
│                   ↓                  │
│ RETURN ←←←○○≈≈≈≈≈≈≈                 │
└─────────────────────────────────────┘

Network Activity - Live Data Flow:
┌─────────────────────────────────────┐
│ SWITCH_01 ●●●━━━┓                   │
│                ┣━━━● COMPUTER_A      │
│                ┣━━━● COMPUTER_B      │
│                ┗━━━● SERVER_01       │
└─────────────────────────────────────┘

Power Distribution - Live Electrical Flow:
┌─────────────────────────────────────┐
│ PANEL_A ⚡⚡⚡═══┓                   │
│                ╠═══⚡ OUTLET_01      │
│                ╠═══⚡ OUTLET_02      │
│                ╚═══⚡ HVAC_01        │
└─────────────────────────────────────┘
```

#### **Professional Applications**
- **System Commissioning**: Verify flows work as designed
- **Troubleshooting**: Visual diagnosis of flow interruptions
- **Training**: Show technicians how building systems interconnect
- **Monitoring**: Real-time system health and performance
- **Optimization**: Visualize system efficiency and bottlenecks

#### **Implementation Strategy**
```go
type ParticleSystem struct {
    postgis     *database.PostGISDB
    iotSensors  *iot.SensorNetwork
    particles   []Particle
    flowPaths   map[string]FlowPath
}

// Phase 1: Static flow patterns from PostGIS connections
func (ps *ParticleSystem) RenderStaticFlow(systemType string) string

// Phase 2: Real-time data integration from IoT sensors  
func (ps *ParticleSystem) RenderLiveFlow(systemType string) string

// Phase 3: Interactive particle editing
func (ps *ParticleSystem) InteractiveFlowEditor(buildingID string) string
```

#### **Technical Considerations**
- **Performance**: 60fps animation in terminal requires optimization
- **Data Integration**: Need real-time sensor data for accurate flow
- **ASCII Limitations**: Creative use of Unicode for smooth animation
- **Optional Feature**: `--particles` flag for users who want enhanced visualization

**Value Proposition**: Transform static building diagrams into **living, breathing system visualizations** that help professionals understand, diagnose, and optimize building operations in ways never before possible in a terminal interface.

## Dependencies

### Required
- `github.com/muesli/termenv` - Terminal capability detection
- `github.com/pterm/pterm` - Enhanced terminal output
- `golang.org/x/term` - Terminal size detection

### Optional
- `github.com/guptarohit/asciigraph` - ASCII line graphs
- `github.com/aybabtme/uniplot` - Unicode plots

## Success Metrics

1. **User Adoption**
   - 80% of users use at least one visualization daily
   - Positive feedback on visibility of system state

2. **Performance**
   - All charts render within target times
   - No noticeable lag during interaction

3. **Coverage**
   - All major data types have visualization options
   - Dashboards available for all common workflows

## Conclusion

This PostGIS-powered terminal visualization architecture positions ArxOS as a unique professional BIM integration platform that provides rich spatial insights with bidirectional control directly in the terminal. By combining PostGIS spatial intelligence with interactive terminal interfaces, ArxOS bridges the gap between professional BIM tools and operational building management.

### Key Differentiators

1. **Spatial Intelligence in Terminal**: PostGIS spatial functions (ST_Distance, ST_Contains) accessible via ASCII visualizations
2. **Bidirectional Control**: Terminal users can query and modify millimeter-precision spatial data
3. **Professional Integration**: Real-time visualization updates from any IFC-exporting BIM tool
4. **Interactive Spatial Editing**: Click-to-edit functionality with PostGIS validation
5. **Multi-precision Display**: Grid coordinates for humans, millimeter precision for professionals

### Professional Value

- **BIM Professionals**: See their model changes visualized immediately in terminal
- **Building Managers**: Get spatial insights without learning PostGIS
- **Field Teams**: Understand precise equipment relationships before AR work
- **System Engineers**: Trace spatial connections with visual feedback

This architecture transforms the terminal from a simple command interface into a **powerful spatial visualization and control platform** that maintains professional-grade precision while remaining accessible to all building stakeholders.