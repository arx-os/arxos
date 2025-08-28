# Arxos CLI Development Guide

This guide covers developing the Arxos command-line interface, emphasizing the **"Building as Filesystem"** and **"Infrastructure as Code"** principles that make Arxos revolutionary.

## 🎯 **Overview**

The Arxos CLI is the **terminal-first interface** for the revolutionary Arxos platform. It transforms buildings into navigable filesystems with infinite fractal zoom capabilities, from campus level down to submicron precision. Every building component becomes an ArxObject with a path, properties, and real-time intelligence.

---

## 🏗️ **Core Design Philosophy**

### **Revolutionary Principles**
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

### **Terminal-First Design**
- **Primary Interface** - CLI is the main way to interact with buildings
- **Filesystem Navigation** - Navigate buildings like file systems with familiar commands
- **Git-like Operations** - Version control for buildings with commits, branches, merges
- **Real-time Monitoring** - Live updates and status monitoring
- **Infinite Zoom Commands** - Zoom from campus to submicron levels

---

## 🔧 **Command Structure**

### **Root Command Structure**

```go
// Root command with building context
var RootCmd = &cobra.Command{
    Use:   "arx",
    Short: "Arxos - Revolutionary Building Infrastructure as Code",
    Long: `Arxos transforms buildings into navigable filesystems with infinite fractal zoom.
    
    Think of buildings as code - every wall, room, and system is an ArxObject
    that can be navigated, modified, and version controlled through the terminal.
    
    The CLI provides access to all 6 visualization layers:
    - 3D SVG-based BIM (CAD-like precision)
    - AR ArxObject overlay (on-site visualization)
    - 2D SVG building plans
    - ASCII art 3D rendering
    - ASCII art 2D plans
    - Raw data and AQL queries`,
    PersistentPreRun: func(cmd *cobra.Command, args []string) {
        // Initialize building context and ArxObject runtime
        initBuildingContext(cmd)
    },
}
```

### **Command Categories**

```go
// Command organization by functionality
func init() {
    // Building filesystem commands
    RootCmd.AddCommand(initCmd, cdCmd, lsCmd, pwdCmd, treeCmd)
    
    // Infinite zoom commands
    RootCmd.AddCommand(zoomCmd, viewCmd, levelCmd)
    
    // ArxObject operations
    RootCmd.AddCommand(inspectCmd, propertiesCmd, modifyCmd)
    
    // Search and query commands
    RootCmd.AddCommand(findCmd, grepCmd, locateCmd, aqlCmd)
    
    // Version control commands
    RootCmd.AddCommand(commitCmd, branchCmd, mergeCmd, statusCmd, diffCmd)
    
    // Real-time monitoring
    RootCmd.AddCommand(monitorCmd, watchCmd, liveCmd)
    
    // Export and visualization
    RootCmd.AddCommand(exportCmd, asciiCmd, svgCmd, threeCmd)
    
    // AR and field operations
    RootCmd.AddCommand(arCmd, scanCmd, validateCmd)
}
```

---

## 🚀 **Initialization Patterns**

### **The `arx init` Command**

The `arx init` command is the **entry point** for working with Arxos - it creates the building filesystem foundation that all other commands depend on.

#### **Command Implementation**

```go
var initCmd = &cobra.Command{
    Use:   "init [building-id]",
    Short: "Initialize a new building filesystem with ArxObject hierarchy",
    Long: `Initialize creates a new building filesystem and ArxObject hierarchy.
    
    This command sets up the foundational structure that enables all other
    Arxos operations. Think of it as 'git init' for buildings.
    
    The building will support:
    - Infinite zoom from campus to submicron levels
    - SVG-based BIM with 1:1 accuracy
    - ASCII art rendering for universal access
    - Real-time ArxObject intelligence
    - Git-like version control`,
    Args: cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        buildingID := args[0]
        return initializeBuilding(buildingID, cmd)
    },
}

func init() {
    initCmd.Flags().String("type", "office", "Building type (office, residential, industrial, retail)")
    initCmd.Flags().Int("floors", 1, "Number of floors")
    initCmd.Flags().String("area", "", "Total building area")
    initCmd.Flags().String("location", "", "Building location/address")
    initCmd.Flags().String("from-pdf", "", "Initialize from PDF floor plan")
    initCmd.Flags().String("from-ifc", "", "Initialize from IFC file")
    initCmd.Flags().String("from-svg", "", "Initialize from SVG BIM file")
    initCmd.Flags().String("config", "", "Use custom configuration file")
    initCmd.Flags().String("template", "", "Use predefined building template")
    initCmd.Flags().Bool("force", false, "Overwrite existing building if it exists")
    initCmd.Flags().Bool("ascii-render", true, "Enable ASCII art rendering")
    initCmd.Flags().Bool("svg-bim", true, "Enable SVG-based BIM")
    initCmd.Flags().Bool("ar-overlay", true, "Enable AR ArxObject overlay")
}
```

#### **Initialization Process**

```go
func initializeBuilding(buildingID string, cmd *cobra.Command) error {
    // 1. Validate building ID format
    if err := validateBuildingID(buildingID); err != nil {
        return fmt.Errorf("invalid building ID: %w", err)
    }
    
    // 2. Check if building already exists
    if buildingExists(buildingID) && !getBoolFlag(cmd, "force") {
        return fmt.Errorf("building %s already exists. Use --force to overwrite", buildingID)
    }
    
    // 3. Create building filesystem structure
    if err := createBuildingFilesystem(buildingID); err != nil {
        return fmt.Errorf("failed to create filesystem: %w", err)
    }
    
    // 4. Initialize ArxObject hierarchy with C core
    if err := initializeArxObjectHierarchy(buildingID, cmd); err != nil {
        return fmt.Errorf("failed to initialize ArxObjects: %w", err)
    }
    
    // 5. Set up ASCII-BIM engine
    if err := initializeASCIIBIMEngine(buildingID, cmd); err != nil {
        return fmt.Errorf("failed to initialize ASCII-BIM engine: %w", err)
    }
    
    // 6. Set up version control
    if err := initializeVersionControl(buildingID); err != nil {
        return fmt.Errorf("failed to initialize version control: %w", err)
    }
    
    // 7. Create initial configuration
    if err := createInitialConfiguration(buildingID, cmd); err != nil {
        return fmt.Errorf("failed to create configuration: %w", err)
    }
    
    // 8. Process input files if provided
    if err := processInputFiles(buildingID, cmd); err != nil {
        return fmt.Errorf("failed to process input files: %w", err)
    }
    
    fmt.Printf("✅ Building %s initialized successfully!\n", buildingID)
    fmt.Printf("🏗️  ArxObject hierarchy created with C core engine\n")
    fmt.Printf("📊 ASCII-BIM engine ready for infinite zoom\n")
    fmt.Printf("📁 Navigate to building: arx cd %s\n", buildingID)
    fmt.Printf("🔍 View structure: arx ls --tree\n")
    fmt.Printf("🔬 Test zoom: arx zoom campus\n")
    
    return nil
}
```

#### **Building Filesystem Structure**

```go
func createBuildingFilesystem(buildingID string) error {
    basePath := getBuildingPath(buildingID)
    
    // Create main building directory
    if err := os.MkdirAll(basePath, 0755); err != nil {
        return err
    }
    
    // Create metadata directory structure
    metadataDirs := []string{
        ".arxos/config",           // Building configuration
        ".arxos/objects",          // ArxObject database
        ".arxos/ascii-bim",        # ASCII-BIM engine data
        ".arxos/svg-bim",          # SVG-based BIM data
        ".arxos/ar-overlay",       # AR ArxObject overlay data
        ".arxos/vcs/snapshots",    # Version control snapshots
        ".arxos/vcs/branches",     # Version branches
        ".arxos/cache",            # Performance cache
        ".arxos/coordinate-systems", # Coordinate transformations
        "systems/electrical",      # Electrical system
        "systems/hvac",            # HVAC system
        "systems/automation",      # Building automation
        "systems/structural",      # Structural system
        "systems/plumbing",        # Plumbing system
        "schemas",                 # Building schemas
        "ascii-renders",           # ASCII art renders
        "svg-models",              # SVG BIM models
    }
    
    for _, dir := range metadataDirs {
        fullPath := filepath.Join(basePath, dir)
        if err := os.MkdirAll(fullPath, 0755); err != nil {
            return fmt.Errorf("failed to create %s: %w", dir, err)
        }
    }
    
    return nil
}
```

#### **ArxObject Hierarchy Initialization**

```go
func initializeArxObjectHierarchy(buildingID string, cmd *cobra.Command) error {
    // Use C core ArxObject runtime for maximum performance
    cRuntime := C.arxobject_runtime_create()
    if cRuntime == nil {
        return fmt.Errorf("failed to create ArxObject runtime")
    }
    defer C.arxobject_runtime_destroy(cRuntime)
    
    // Create root building ArxObject
    buildingObj := C.arxobject_create(
        C.CString(buildingID),
        C.CString("building"),
        C.ARX_STRUCTURAL,
    )
    if buildingObj == nil {
        return fmt.Errorf("failed to create building ArxObject")
    }
    
    // Set building properties
    C.arxobject_set_property(buildingObj, C.CString("type"), C.CString(getStringFlag(cmd, "type")))
    C.arxobject_set_property(buildingObj, C.CString("floors"), C.CString(fmt.Sprintf("%d", getIntFlag(cmd, "floors"))))
    C.arxobject_set_property(buildingObj, C.CString("area"), C.CString(getStringFlag(cmd, "area")))
    C.arxobject_set_property(buildingObj, C.CString("location"), C.CString(getStringFlag(cmd, "location")))
    
    // Create floor ArxObjects
    floors := getIntFlag(cmd, "floors")
    for i := 1; i <= floors; i++ {
        floorObj := C.arxobject_create(
            C.CString(fmt.Sprintf("floor:%d", i)),
            C.CString(fmt.Sprintf("Floor %d", i)),
            C.ARX_SPACE,
        )
        
        // Set floor properties
        C.arxobject_set_property(floorObj, C.CString("floor_number"), C.CString(fmt.Sprintf("%d", i)))
        C.arxobject_set_property(floorObj, C.CString("height"), C.CString("3000")) // 3m floor height
        
        // Add to building
        C.arxobject_add_child(buildingObj, floorObj)
    }
    
    // Create system ArxObjects
    systems := []string{"electrical", "hvac", "automation", "structural", "plumbing"}
    for _, system := range systems {
        systemObj := C.arxobject_create(
            C.CString(fmt.Sprintf("systems:%s", system)),
            C.CString(fmt.Sprintf("%s System", strings.Title(system))),
            C.ARX_SYSTEM,
        )
        
        // Set system properties
        C.arxobject_set_property(systemObj, C.CString("system_type"), C.CString(system))
        C.arxobject_set_property(systemObj, C.CString("status"), C.CString("inactive"))
        
        // Add to building
        C.arxobject_add_child(buildingObj, systemObj)
    }
    
    // Save to ArxObject database
    return saveArxObjectHierarchy(buildingID, buildingObj)
}
```

#### **ASCII-BIM Engine Initialization**

```go
func initializeASCIIBIMEngine(buildingID string, cmd *cobra.Command) error {
    if !getBoolFlag(cmd, "ascii-render") {
        return nil // Skip if ASCII rendering disabled
    }
    
    // Initialize C core ASCII-BIM engine
    asciiEngine := C.ascii_bim_engine_create()
    if asciiEngine == nil {
        return fmt.Errorf("failed to create ASCII-BIM engine")
    }
    defer C.ascii_bim_engine_destroy(asciiEngine)
    
    // Configure infinite zoom levels
    zoomLevels := []C.ZoomLevel{
        C.ZOOM_CAMPUS,      // 1 char = 100m
        C.ZOOM_SITE,        // 1 char = 10m
        C.ZOOM_BUILDING,    // 1 char = 1m
        C.ZOOM_FLOOR,       // 1 char = 0.1m
        C.ZOOM_ROOM,        // 1 char = 0.01m
        C.ZOOM_FURNITURE,   // 1 char = 0.001m
        C.ZOOM_EQUIPMENT,   // 1 char = 0.0001m
        C.ZOOM_COMPONENT,   // 1 char = 0.00001m
        C.ZOOM_DETAIL,      // 1 char = 0.000001m
        C.ZOOM_SUBMICRON,   // 1 char = 0.0000001m
        C.ZOOM_NANOSCOPIC,  // 1 char = 0.00000001m
    }
    
    for _, level := range zoomLevels {
        C.ascii_bim_engine_add_zoom_level(asciiEngine, level)
    }
    
    // Configure Pixatool-inspired rendering
    C.ascii_bim_engine_set_renderer(asciiEngine, C.ASCII_RENDERER_PIXATOOL)
    
    // Save engine configuration
    return saveASCIIBIMEngine(buildingID, asciiEngine)
}
```

---

## 🔍 **Infinite Zoom System**

### **Zoom Command Implementation**

```go
var zoomCmd = &cobra.Command{
    Use:   "zoom [level]",
    Short: "Zoom to specific level (campus to nanoscopic)",
    Long: `Zoom to a specific level in the infinite zoom system.
    
    Available levels:
    - campus: Campus overview (1 char = 100m)
    - site: Site plan (1 char = 10m)
    - building: Building outline (1 char = 1m)
    - floor: Floor plan (1 char = 0.1m)
    - room: Room detail (1 char = 0.01m)
    - furniture: Furniture layout (1 char = 0.001m)
    - equipment: Equipment detail (1 char = 0.0001m)
    - component: Component detail (1 char = 0.00001m)
    - detail: Micro detail (1 char = 0.000001m)
    - submicron: Submicron detail (1 char = 0.0000001m)
    - nanoscopic: Nanoscopic detail (1 char = 0.00000001m)`,
    Args: cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        level := args[0]
        smooth := getBoolFlag(cmd, "smooth")
        return zoomToLevel(level, smooth)
    },
}

func init() {
    zoomCmd.Flags().BoolP("smooth", "s", true, "Smooth transition")
    zoomCmd.Flags().Bool("ascii", false, "Show ASCII art render")
    zoomCmd.Flags().Bool("svg", false, "Show SVG BIM view")
    zoomCmd.Flags().Bool("3d", false, "Show 3D view")
}
```

### **Zoom Implementation**

```go
func zoomToLevel(level string, smooth bool) error {
    // Get current building context
    buildingID, err := getCurrentBuilding()
    if err != nil {
        return fmt.Errorf("no building context: %w", err)
    }
    
    // Validate zoom level
    validLevels := map[string]bool{
        "campus": true, "site": true, "building": true, "floor": true,
        "room": true, "furniture": true, "equipment": true, "component": true,
        "detail": true, "submicron": true, "nanoscopic": true,
    }
    
    if !validLevels[level] {
        return fmt.Errorf("invalid zoom level: %s", level)
    }
    
    // Use C core ASCII-BIM engine for zoom
    asciiEngine := getASCIIBIMEngine(buildingID)
    if asciiEngine == nil {
        return fmt.Errorf("ASCII-BIM engine not available")
    }
    
    // Convert level to C enum
    var cLevel C.ZoomLevel
    switch level {
    case "campus":
        cLevel = C.ZOOM_CAMPUS
    case "site":
        cLevel = C.ZOOM_SITE
    case "building":
        cLevel = C.ZOOM_BUILDING
    case "floor":
        cLevel = C.ZOOM_FLOOR
    case "room":
        cLevel = C.ZOOM_ROOM
    case "furniture":
        cLevel = C.ZOOM_FURNITURE
    case "equipment":
        cLevel = C.ZOOM_EQUIPMENT
    case "component":
        cLevel = C.ZOOM_COMPONENT
    case "detail":
        cLevel = C.ZOOM_DETAIL
    case "submicron":
        cLevel = C.ZOOM_SUBMICRON
    case "nanoscopic":
        cLevel = C.ZOOM_NANOSCOPIC
    }
    
    // Execute zoom
    if smooth {
        C.ascii_bim_engine_zoom_smooth(asciiEngine, cLevel)
    } else {
        C.ascii_bim_engine_zoom_instant(asciiEngine, cLevel)
    }
    
    // Get zoom information
    info := C.ascii_bim_engine_get_zoom_info(asciiEngine)
    defer C.free(unsafe.Pointer(info))
    
    fmt.Printf("🔬 Zoomed to %s level\n", level)
    fmt.Printf("📏 Scale: 1 char = %s %s\n", C.GoString(info.scale), C.GoString(info.units))
    fmt.Printf("🎯 Precision: %s\n", C.GoString(info.precision))
    fmt.Printf("📝 Description: %s\n", C.GoString(info.description))
    
    return nil
}
```

---

## 🗂️ **Filesystem Navigation**

### **Navigation Commands**

```go
// Change directory command
var cdCmd = &cobra.Command{
    Use:   "cd [path]",
    Short: "Change directory in building filesystem",
    Long: `Navigate the building filesystem like a Unix filesystem.
    
    Examples:
      arx cd /electrical/main-panel
      arx cd floor:1/room:101
      arx cd systems/hvac/unit:1
      arx cd ..                    # Go up one level
      arx cd /                     # Go to building root
      arx cd ~                     # Go to home building`,
    Args: cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        path := args[0]
        return changeDirectory(path)
    },
}

// List directory command
var lsCmd = &cobra.Command{
    Use:   "ls [path]",
    Short: "List directory contents",
    Long: `List contents of a directory in the building filesystem.
    
    Examples:
      arx ls                       # List current directory
      arx ls /electrical          # List electrical systems
      arx ls --tree               # Show tree structure
      arx ls --ascii              # Show ASCII art render
      arx ls --svg                # Show SVG BIM view
      arx ls --properties         # Show object properties`,
    Args: cobra.MaximumNArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        path := "."
        if len(args) > 0 {
            path = args[0]
        }
        
        tree := getBoolFlag(cmd, "tree")
        ascii := getBoolFlag(cmd, "ascii")
        svg := getBoolFlag(cmd, "svg")
        properties := getBoolFlag(cmd, "properties")
        
        return listDirectory(path, tree, ascii, svg, properties)
    },
}

func init() {
    lsCmd.Flags().BoolP("tree", "t", false, "Show tree structure")
    lsCmd.Flags().Bool("ascii", false, "Show ASCII art render")
    lsCmd.Flags().Bool("svg", false, "Show SVG BIM view")
    lsCmd.Flags().BoolP("properties", "p", false, "Show object properties")
    lsCmd.Flags().BoolP("long", "l", false, "Use long listing format")
}
```

### **Navigation Implementation**

```go
func changeDirectory(path string) error {
    // Get current building context
    buildingID, err := getCurrentBuilding()
    if err != nil {
        return fmt.Errorf("no building context: %w", err)
    }
    
    // Resolve path using ArxObject system
    targetObj, err := resolvePath(buildingID, path)
    if err != nil {
        return fmt.Errorf("failed to resolve path %s: %w", path, err)
    }
    
    // Check if object is navigable
    if !targetObj.IsNavigable() {
        return fmt.Errorf("cannot navigate to %s: not a navigable object", path)
    }
    
    // Update working directory
    if err := updateWorkingDirectory(buildingID, targetObj.GetPath()); err != nil {
        return fmt.Errorf("failed to update working directory: %w", err)
    }
    
    fmt.Printf("📁 Changed directory to: %s\n", targetObj.GetPath())
    
    // Show current location info
    if err := showLocationInfo(targetObj); err != nil {
        return fmt.Errorf("failed to show location info: %w", err)
    }
    
    return nil
}

func listDirectory(path string, tree, ascii, svg, properties bool) error {
    // Get current building context
    buildingID, err := getCurrentBuilding()
    if err != nil {
        return fmt.Errorf("no building context: %w", err)
    }
    
    // Resolve path
    targetObj, err := resolvePath(buildingID, path)
    if err != nil {
        return fmt.Errorf("failed to resolve path %s: %w", path, err)
    }
    
    // List children
    children := targetObj.GetChildren()
    
    if tree {
        // Show tree structure
        showTreeStructure(targetObj, "", true)
    } else {
        // Show simple list
        for _, child := range children {
            fmt.Printf("%s/  %s\n", child.GetType(), child.GetName())
        }
    }
    
    // Show ASCII render if requested
    if ascii {
        if err := showASCIIRender(buildingID, targetObj); err != nil {
            return fmt.Errorf("failed to show ASCII render: %w", err)
        }
    }
    
    // Show SVG BIM if requested
    if svg {
        if err := showSVGBIM(buildingID, targetObj); err != nil {
            return fmt.Errorf("failed to show SVG BIM: %w", err)
        }
    }
    
    // Show properties if requested
    if properties {
        showObjectProperties(targetObj)
    }
    
    return nil
}
```

---

## 🔍 **Search and Query**

### **Find Command**

```go
var findCmd = &cobra.Command{
    Use:   "find [query]",
    Short: "Find ArxObjects by properties, type, or location",
    Long: `Find ArxObjects in the building using various criteria.
    
    Examples:
      arx find "electrical outlet"           # Find by name/type
      arx find --type "hvac"                 # Find by object type
      arx find --property "status=active"    # Find by property
      arx find --location "floor:1"          # Find in specific location
      arx find --system "electrical"         # Find in specific system
      arx find --confidence 0.8              # Minimum confidence threshold`,
    Args: cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        query := args[0]
        objectType := getStringFlag(cmd, "type")
        property := getStringFlag(cmd, "property")
        location := getStringFlag(cmd, "location")
        system := getStringFlag(cmd, "system")
        confidence := getFloatFlag(cmd, "confidence")
        
        return findArxObjects(query, objectType, property, location, system, confidence)
    },
}

func init() {
    findCmd.Flags().String("type", "", "Filter by object type")
    findCmd.Flags().String("property", "", "Filter by property (key=value)")
    findCmd.Flags().String("location", "", "Filter by location")
    findCmd.Flags().String("system", "", "Filter by system")
    findCmd.Flags().Float64("confidence", 0.0, "Minimum confidence threshold")
    findCmd.Flags().BoolP("verbose", "v", false, "Verbose output")
}
```

### **AQL Command**

```go
var aqlCmd = &cobra.Command{
    Use:   "aql [query]",
    Short: "Execute Arxos Query Language (AQL) queries",
    Long: `Execute complex queries using the Arxos Query Language.
    
    AQL provides SQL-like syntax for querying building data:
    
    Examples:
      arx aql "SELECT * FROM /electrical WHERE type='outlet'"
      arx aql "SELECT name, status FROM /hvac WHERE status='active'"
      arx aql "SELECT * FROM /floor:1 WHERE confidence > 0.8"
      arx aql "SELECT * FROM /systems WHERE system_type IN ('electrical', 'hvac')"
      arx aql "SELECT * FROM / WHERE position.x BETWEEN 0 AND 100"`,
    Args: cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        query := args[0]
        format := getStringFlag(cmd, "format")
        return executeAQLQuery(query, format)
    },
}

func init() {
    aqlCmd.Flags().String("format", "table", "Output format (table, json, csv)")
    aqlCmd.Flags().Bool("explain", false, "Show query execution plan")
}
```

---

## 📊 **Real-time Monitoring**

### **Monitor Command**

```go
var monitorCmd = &cobra.Command{
    Use:   "monitor [path]",
    Short: "Monitor ArxObjects in real-time",
    Long: `Monitor ArxObjects for real-time updates and changes.
    
    Examples:
      arx monitor /electrical/main-panel     # Monitor specific object
      arx monitor /systems                   # Monitor all systems
      arx monitor --watch                    # Watch for changes
      arx monitor --interval 1s              # Update interval
      arx monitor --format table             # Output format`,
    Args: cobra.MaximumNArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        path := "."
        if len(args) > 0 {
            path = args[0]
        }
        
        watch := getBoolFlag(cmd, "watch")
        interval := getStringFlag(cmd, "interval")
        format := getStringFlag(cmd, "format")
        
        return monitorArxObjects(path, watch, interval, format)
    },
}

func init() {
    monitorCmd.Flags().BoolP("watch", "w", false, "Watch for changes")
    monitorCmd.Flags().String("interval", "1s", "Update interval")
    monitorCmd.Flags().String("format", "table", "Output format")
    monitorCmd.Flags().Bool("ascii", false, "Show ASCII art updates")
    monitorCmd.Flags().Bool("svg", false, "Show SVG BIM updates")
}
```

---

## 🧪 **Testing**

### **Command Testing**

```go
func TestZoomCommand(t *testing.T) {
    // Create temporary test directory
    testDir, err := os.MkdirTemp("", "arxos-test-*")
    if err != nil {
        t.Fatal(err)
    }
    defer os.RemoveAll(testDir)
    
    // Change to test directory
    originalDir, err := os.Getwd()
    if err != nil {
        t.Fatal(err)
    }
    defer os.Chdir(originalDir)
    
    if err := os.Chdir(testDir); err != nil {
        t.Fatal(err)
    }
    
    // Test building initialization
    cmd := exec.Command("arx", "init", "building:test", "--type", "office", "--floors", "2")
    if err := cmd.Run(); err != nil {
        t.Fatalf("init command failed: %v", err)
    }
    
    // Test zoom to campus level
    cmd = exec.Command("arx", "zoom", "campus")
    output, err := cmd.CombinedOutput()
    if err != nil {
        t.Fatalf("zoom command failed: %v\nOutput: %s", err, output)
    }
    
    // Verify zoom output contains expected information
    if !strings.Contains(string(output), "Zoomed to campus level") {
        t.Error("zoom output missing expected text")
    }
    
    if !strings.Contains(string(output), "1 char = 100m") {
        t.Error("zoom output missing scale information")
    }
    
    // Test zoom to submicron level
    cmd = exec.Command("arx", "zoom", "submicron")
    output, err = cmd.CombinedOutput()
    if err != nil {
        t.Fatalf("zoom to submicron failed: %v\nOutput: %s", err, output)
    }
    
    if !strings.Contains(string(output), "Zoomed to submicron level") {
        t.Error("submicron zoom output missing expected text")
    }
    
    if !strings.Contains(string(output), "1 char = 0.0000001m") {
        t.Error("submicron zoom output missing correct scale")
    }
}
```

---

## 🚀 **Performance Considerations**

### **C Core Integration**

```go
// Use C core for maximum performance
type ArxObjectRuntime struct {
    cRuntime *C.struct_ArxObjectRuntime
    mutex    sync.RWMutex
}

func (rt *ArxObjectRuntime) GetArxObject(path string) (*ArxObject, error) {
    rt.mutex.RLock()
    defer rt.mutex.RUnlock()
    
    cPath := C.CString(path)
    defer C.free(unsafe.Pointer(cPath))
    
    cObj := C.arxobject_get_by_path(rt.cRuntime, cPath)
    if cObj == nil {
        return nil, fmt.Errorf("ArxObject not found: %s", path)
    }
    
    return &ArxObject{cPtr: cObj}, nil
}

// Zero-allocation spatial queries
func (rt *ArxObjectRuntime) SpatialQuery(bbox [6]float64) ([]*ArxObject, error) {
    rt.mutex.RLock()
    defer rt.mutex.RUnlock()
    
    var cBbox [6]C.float
    for i, v := range bbox {
        cBbox[i] = C.float(v)
    }
    
    var results []*ArxObject
    C.arxobject_spatial_query(rt.cRuntime, &cBbox[0], func(obj *C.struct_ArxObject) {
        results = append(results, &ArxObject{cPtr: obj})
    })
    
    return results, nil
}
```

---

## 🔗 **Related Documentation**

- **Vision**: [Platform Vision](../../vision.md)
- **Architecture**: [Current Architecture](current-architecture.md)
- **ASCII-BIM**: [ASCII-BIM Engine](../architecture/ascii-bim.md)
- **ArxObjects**: [ArxObject System](../architecture/arxobjects.md)
- **CLI Architecture**: [CLI Architecture](../architecture/cli-architecture.md)
- **Workflows**: [PDF to 3D Pipeline](../workflows/pdf-to-3d.md)

---

## 🆘 **Getting Help**

- **Architecture Questions**: Review [Current Architecture](current-architecture.md)
- **C Development**: Check [Core C Engine](../core/c/README.md)
- **Go Development**: Review [Go Services](../core/README.md)
- **CLI Issues**: Test with [Enhanced Zoom Demo](../frontend/demo-enhanced-zoom.html)

**Happy building! 🏗️✨**
