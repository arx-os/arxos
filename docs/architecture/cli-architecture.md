# 🖥️ CLI Architecture - Terminal-First Design

## 🎯 **CLI Architecture Overview**

The **Arxos CLI** is built on the revolutionary principle of **terminal-first design**, where buildings become navigable filesystems accessible through powerful command-line tools. This architecture enables engineers, technicians, and developers to interact with building infrastructure using the same tools and workflows they use for software development.

**Core Innovation**: Buildings become navigable filesystems with Git-like version control, infinite zoom capabilities, and terminal-native operations that work everywhere from SSH terminals to embedded systems.

## 🚀 **Terminal-First Design Philosophy**

### **Why Terminal-First?**

The terminal-first approach provides several revolutionary advantages:

- **Universal Accessibility** - Works everywhere from SSH terminals to embedded systems
- **Power User Efficiency** - Engineers can navigate buildings faster than with GUI tools
- **Automation Friendly** - Scripts and CI/CD pipelines can manage building infrastructure
- **Resource Efficient** - Minimal resource requirements, works on any device
- **Version Control** - Git-like operations for building changes and rollbacks
- **Real-time Updates** - Live building data in terminal format

### **Design Principles**

```bash
# 1. Filesystem Navigation - Navigate buildings like file systems
arx @building-47 cd /electrical/main-panel
arx @building-47 ls -la
arx @building-47 pwd

# 2. Git-like Operations - Version control for buildings
arx @building-47 status
arx @building-47 diff
arx @building-47 commit -m "Updated circuit breaker settings"
arx @building-47 log --oneline

# 3. Infinite Zoom - From campus to chip level
arx @building-47 zoom campus
arx @building-47 zoom building
arx @building-47 zoom floor --level 2
arx @building-47 zoom room --id mechanical-room

# 4. Real-time Monitoring - Live building data
arx @building-47 watch --type electrical
arx @building-47 monitor --dashboard
arx @building-47 alerts --live
```

## 🏗️ **Core Architecture Components**

### **Command Structure**

```go
// Main command structure
type ArxosCommand struct {
    Use     string
    Short   string
    Long    string
    Example string
    RunE    func(cmd *cobra.Command, args []string) error
}

// Building context management
type BuildingContext struct {
    CurrentBuilding *Building
    CurrentPath     string
    ZoomLevel       ZoomLevel
    ViewMode        ViewMode
    OutputFormat    OutputFormat
}

// Command categories
var commandCategories = map[string][]*cobra.Command{
    "navigation": {
        cdCmd, lsCmd, pwdCmd, treeCmd, findCmd,
    },
    "building": {
        initCmd, statusCmd, diffCmd, commitCmd, logCmd,
    },
    "visualization": {
        renderCmd, zoomCmd, viewCmd, asciiCmd,
    },
    "monitoring": {
        watchCmd, monitorCmd, alertsCmd, metricsCmd,
    },
    "operations": {
        setCmd, getCmd, queryCmd, validateCmd,
    },
}
```

### **Building Context Management**

```go
// Building context management
type BuildingContext struct {
    CurrentBuilding *Building
    CurrentPath     string
    ZoomLevel       ZoomLevel
    ViewMode        ViewMode
    OutputFormat    OutputFormat
}

// Context switching
func (ctx *BuildingContext) SwitchBuilding(buildingID string) error {
    building, err := loadBuilding(buildingID)
    if err != nil {
        return fmt.Errorf("failed to load building: %w", err)
    }
    
    ctx.CurrentBuilding = building
    ctx.CurrentPath = "/"
    ctx.ZoomLevel = ZoomLevelBuilding
    
    return nil
}

// Path navigation
func (ctx *BuildingContext) NavigateTo(path string) error {
    if !ctx.CurrentBuilding.PathExists(path) {
        return fmt.Errorf("path does not exist: %s", path)
    }
    
    ctx.CurrentPath = path
    return nil
}
```

## 🗂️ **Filesystem Navigation Commands**

### **Core Navigation Commands**

```bash
# Building selection and context
arx @building-47                    # Switch to building-47
arx @campus-east                    # Switch to campus context
arx @site-main                      # Switch to site context

# Path navigation
arx cd /electrical/main-panel       # Navigate to electrical panel
arx cd ..                           # Go up one level
arx cd /                            # Go to root
arx cd -                            # Go to previous location

# Directory listing
arx ls                              # List current directory
arx ls -la                          # List with details
arx ls --type outlet               # List only outlets
arx ls --filter "load > 15A"       # List with filter

# Path information
arx pwd                             # Show current path
arx tree                            # Show directory tree
arx tree --depth 3                 # Limit tree depth
arx tree --type electrical         # Show only electrical systems
```

### **Advanced Navigation Features**

```bash
# Pattern-based navigation
arx cd /electrical/panel-*         # Navigate to any panel
arx cd /hvac/ahu-[1-3]            # Navigate to AHUs 1-3
arx cd /structural/column-[a1-d8] # Navigate to columns

# Search and find
arx find --type outlet             # Find all outlets
arx find --query "load > 15A"     # Find with query
arx find --path "/electrical/*"    # Find in path pattern
arx find --confidence > 0.8       # Find high-confidence objects

# Quick navigation
arx cd @electrical                 # Quick jump to electrical
arx cd @hvac                      # Quick jump to HVAC
arx cd @structural                # Quick jump to structural
arx cd @network                   # Quick jump to network
```

## 🔄 **Git-like Version Control**

### **Building State Management**

```bash
# Status and changes
arx status                         # Show building status
arx status --short                 # Compact status
arx status --type electrical       # Status for electrical systems

# Diff and changes
arx diff                           # Show all changes
arx diff /electrical/main-panel    # Show changes in specific area
arx diff --type outlet            # Show changes by type
arx diff --since "2 hours ago"    # Show recent changes

# Commit and history
arx commit -m "Updated circuit settings"
arx commit --all -m "Bulk update of electrical systems"
arx log                            # Show commit history
arx log --oneline                  # Compact history
arx log --since "1 day ago"       # Recent history

# Branching and merging
arx branch maintenance-mode        # Create maintenance branch
arx checkout maintenance-mode      # Switch to maintenance mode
arx merge main                     # Merge changes back to main
```

### **Version Control Implementation**

```go
// Building version control
type BuildingVersionControl struct {
    CurrentBranch string
    Branches      map[string]*Branch
    Commits       []*Commit
    StagedChanges map[string]*Change
}

// Commit structure
type Commit struct {
    ID          string
    Message     string
    Timestamp   time.Time
    Author      string
    Changes     []*Change
    Parent      *Commit
    Branch      string
}

// Change tracking
type Change struct {
    Path        string
    Type        ChangeType
    OldValue    interface{}
    NewValue    interface{}
    Timestamp   time.Time
    Author      string
}

// Commit changes
func (bvc *BuildingVersionControl) Commit(message string, author string) error {
    if len(bvc.StagedChanges) == 0 {
        return fmt.Errorf("no changes to commit")
    }
    
    commit := &Commit{
        ID:        generateCommitID(),
        Message:   message,
        Timestamp: time.Now(),
        Author:    author,
        Changes:   make([]*Change, 0),
        Parent:    bvc.getCurrentCommit(),
        Branch:    bvc.CurrentBranch,
    }
    
    // Convert staged changes to commit
    for _, change := range bvc.StagedChanges {
        commit.Changes = append(commit.Changes, change)
    }
    
    // Add to commit history
    bvc.Commits = append(bvc.Commits, commit)
    
    // Clear staged changes
    bvc.StagedChanges = make(map[string]*Change)
    
    return nil
}
```

## 🎯 **Infinite Zoom System**

### **Zoom Level Management**

```bash
# Zoom level commands
arx zoom campus                     # Campus overview (100m per char)
arx zoom site                       # Site plan (10m per char)
arx zoom building                   # Building outline (1m per char)
arx zoom floor --level 2            # Floor plan (10cm per char)
arx zoom room --id mechanical-room  # Room detail (1cm per char)
arx zoom equipment --id plc-cabinet # Equipment (1mm per char)
arx zoom component --id cpu-module  # Component (0.1mm per char)
arx zoom chip                       # Chip level (0.01mm per char)

# Zoom with specific coordinates
arx zoom --x 100 --y 200 --scale 0.1
arx zoom --center "electrical/main-panel"
arx zoom --fit "hvac/ahu-1"

# Zoom history
arx zoom --back                     # Go back to previous zoom
arx zoom --forward                  # Go forward in zoom history
arx zoom --reset                    # Reset to default zoom
```

### **Zoom Implementation**

```go
// Zoom level management
type ZoomLevel struct {
    Scale       float64
    Description string
    Units       string
    Precision   string
}

var zoomLevels = map[string]ZoomLevel{
    "campus": {
        Scale:       0.0001,
        Description: "Campus overview",
        Units:       "km",
        Precision:   "kilometer",
    },
    "site": {
        Scale:       0.001,
        Description: "Site plan",
        Units:       "hm",
        Precision:   "hectometer",
    },
    "building": {
        Scale:       0.01,
        Description: "Building outline",
        Units:       "dam",
        Precision:   "decameter",
    },
    "floor": {
        Scale:       0.1,
        Description: "Floor plan",
        Units:       "m",
        Precision:   "meter",
    },
    "room": {
        Scale:       1.0,
        Description: "Room detail",
        Units:       "dm",
        Precision:   "decimeter",
    },
    "equipment": {
        Scale:       10.0,
        Description: "Equipment detail",
        Units:       "cm",
        Precision:   "centimeter",
    },
    "component": {
        Scale:       100.0,
        Description: "Component detail",
        Units:       "mm",
        Precision:   "millimeter",
    },
    "chip": {
        Scale:       1000.0,
        Description: "Chip level",
        Units:       "μm",
        Precision:   "micrometer",
    },
}

// Zoom to specific level
func (ctx *BuildingContext) ZoomToLevel(level string) error {
    zoomLevel, exists := zoomLevels[level]
    if !exists {
        return fmt.Errorf("invalid zoom level: %s", level)
    }
    
    ctx.ZoomLevel = zoomLevel
    return ctx.updateView()
}
```

## 📊 **Real-time Monitoring Commands**

### **Live Building Data**

```bash
# Real-time monitoring
arx watch                          # Watch all changes
arx watch --type electrical        # Watch electrical systems
arx watch --path /hvac/ahu-1      # Watch specific equipment
arx watch --filter "temp > 80"    # Watch with filter

# Dashboard views
arx monitor --dashboard            # Show monitoring dashboard
arx monitor --type energy          # Energy monitoring dashboard
arx monitor --type security        # Security monitoring dashboard
arx monitor --type hvac            # HVAC monitoring dashboard

# Alerts and notifications
arx alerts                         # Show active alerts
arx alerts --live                  # Live alert stream
arx alerts --type critical         # Critical alerts only
arx alerts --since "1 hour ago"    # Recent alerts

# Performance metrics
arx metrics                        # Show performance metrics
arx metrics --type electrical      # Electrical metrics
arx metrics --type hvac            # HVAC metrics
arx metrics --history "24h"        # 24-hour history
```

### **Monitoring Implementation**

```go
// Real-time monitoring
type MonitoringSystem struct {
    Watchers    map[string]*Watcher
    Alerts      []*Alert
    Metrics     map[string]*Metric
    Dashboard   *Dashboard
}

// Watcher for real-time updates
type Watcher struct {
    ID       string
    Type     string
    Path     string
    Filter   string
    Callback func(*Change)
    Active   bool
}

// Start watching
func (ms *MonitoringSystem) StartWatching(watcher *Watcher) error {
    if watcher.Active {
        return fmt.Errorf("watcher already active")
    }
    
    watcher.Active = true
    ms.Watchers[watcher.ID] = watcher
    
    // Start background monitoring
    go ms.monitorWatcher(watcher)
    
    return nil
}

// Monitor watcher in background
func (ms *MonitoringSystem) monitorWatcher(watcher *Watcher) {
    ticker := time.NewTicker(100 * time.Millisecond)
    defer ticker.Stop()
    
    for watcher.Active {
        select {
        case <-ticker.C:
            // Check for changes
            changes := ms.checkForChanges(watcher)
            for _, change := range changes {
                watcher.Callback(change)
            }
        }
    }
}
```

## 🔧 **Property and Query Operations**

### **Object Property Management**

```bash
# Property operations
arx get /electrical/main-panel/circuit-1 --property load_current
arx get /hvac/ahu-1 --property supply_air_temp
arx get /structural/column-a1 --property load_capacity

# Set properties
arx set /electrical/main-panel/circuit-1 --property load_current=15.5
arx set /hvac/ahu-1 --property supply_air_temp=72
arx set /structural/column-a1 --property load_capacity=5000

# Query operations
arx query "SELECT path FROM /electrical WHERE type='outlet' AND load > 15A"
arx query "SELECT * FROM /hvac WHERE temp > 80 ORDER BY temp DESC"
arx query "SELECT COUNT(*) FROM /structural WHERE type='column'"

# Bulk operations
arx set --bulk /electrical/panel-* --property voltage=480
arx set --bulk /hvac/ahu-* --property mode="auto"
arx set --bulk /structural/column-* --property inspection_due="2024-06-01"
```

### **Query Language Implementation**

```go
// Query language parser
type QueryParser struct {
    Tokens []Token
    Pos    int
}

// Query execution
type QueryExecutor struct {
    Building *Building
    Context  *BuildingContext
}

// Execute query
func (qe *QueryExecutor) ExecuteQuery(query string) ([]*ArxObject, error) {
    parser := NewQueryParser(query)
    ast, err := parser.Parse()
    if err != nil {
        return nil, fmt.Errorf("parse error: %w", err)
    }
    
    return qe.executeAST(ast)
}

// Query AST execution
func (qe *QueryExecutor) executeAST(ast *QueryAST) ([]*ArxObject, error) {
    switch ast.Type {
    case ASTSelect:
        return qe.executeSelect(ast)
    case ASTUpdate:
        return qe.executeUpdate(ast)
    case ASTDelete:
        return qe.executeDelete(ast)
    default:
        return nil, fmt.Errorf("unsupported query type")
    }
}

// Execute SELECT query
func (qe *QueryExecutor) executeSelect(ast *SelectAST) ([]*ArxObject, error) {
    // Parse FROM clause
    objects, err := qe.resolvePath(ast.From)
    if err != nil {
        return nil, err
    }
    
    // Apply WHERE clause
    if ast.Where != nil {
        objects = qe.applyWhereClause(objects, ast.Where)
    }
    
    // Apply ORDER BY
    if ast.OrderBy != nil {
        objects = qe.applyOrderBy(objects, ast.OrderBy)
    }
    
    // Apply LIMIT
    if ast.Limit > 0 {
        objects = qe.applyLimit(objects, ast.Limit)
    }
    
    return objects, nil
}
```

## 🎨 **Visualization Commands**

### **ASCII Rendering**

```bash
# ASCII rendering
arx render                         # Render current view
arx render --type 2d              # 2D floor plan
arx render --type 3d              # 3D building view
arx render --type electrical      # Electrical system view
arx render --type hvac            # HVAC system view

# View modes
arx view --mode structural        # Structural view
arx view --mode electrical        # Electrical view
arx view --mode hvac              # HVAC view
arx view --mode network           # Network view
arx view --mode plumbing          # Plumbing view

# Output formats
arx render --format ascii         # ASCII output
arx render --format json          # JSON output
arx render --format yaml          # YAML output
arx render --format csv           # CSV output
arx render --format table         # Table output
```

### **Rendering Implementation**

```go
// Rendering system
type RenderingSystem struct {
    Renderers map[string]Renderer
    Context   *BuildingContext
}

// Renderer interface
type Renderer interface {
    Render(building *Building, context *BuildingContext) (string, error)
    SupportsFormat(format string) bool
    GetSupportedFormats() []string
}

// ASCII renderer
type ASCIIRenderer struct {
    CharacterSet map[string]string
    ZoomLevel    ZoomLevel
    ViewMode     ViewMode
}

// Render building in ASCII
func (ar *ASCIIRenderer) Render(building *Building, context *BuildingContext) (string, error) {
    // Get objects in current view
    objects := building.GetObjectsInPath(context.CurrentPath)
    
    // Apply zoom level
    objects = ar.applyZoomLevel(objects, context.ZoomLevel)
    
    // Apply view mode
    objects = ar.applyViewMode(objects, context.ViewMode)
    
    // Generate ASCII representation
    return ar.generateASCII(objects, context)
}

// Generate ASCII output
func (ar *ASCIIRenderer) generateASCII(objects []*ArxObject, context *BuildingContext) (string, error) {
    var output strings.Builder
    
    // Calculate canvas dimensions
    width, height := ar.calculateCanvasSize(objects, context.ZoomLevel)
    
    // Create canvas
    canvas := ar.createCanvas(width, height)
    
    // Render objects
    for _, obj := range objects {
        ar.renderObject(canvas, obj, context)
    }
    
    // Convert canvas to string
    return ar.canvasToString(canvas), nil
}
```

## 🔌 **Integration and Automation**

### **Scripting and Automation**

```bash
# Script execution
arx exec --file update_electrical.sh
arx exec --script "cd /electrical && ls -la"
arx exec --inline "set /hvac/ahu-1 --property mode=auto"

# Batch operations
arx batch --file operations.yaml
arx batch --script "update_all_panels.sh"
arx batch --inline "set --bulk /electrical/* --property voltage=480"

# Scheduled operations
arx schedule --cron "0 6 * * *" --command "set /hvac/ahu-1 --property mode=auto"
arx schedule --daily "06:00" --command "set /hvac/ahu-1 --property mode=auto"
arx schedule --weekly "monday 06:00" --command "maintenance_check.sh"
```

### **API Integration**

```bash
# REST API integration
arx api --endpoint "https://api.arxos.com" --token "your-token"
arx api --method GET --path "/buildings/building-47/electrical"
arx api --method POST --path "/buildings/building-47/electrical" --data '{"voltage": 480}'

# WebSocket integration
arx ws --connect "wss://ws.arxos.com" --subscribe "building-47"
arx ws --send '{"type": "command", "action": "set_property", "path": "/hvac/ahu-1", "property": "mode", "value": "auto"}'
```

## 🏆 **Key Benefits**

### **Universal Accessibility**

- **Works Everywhere** - From SSH terminals to embedded systems
- **No Dependencies** - Pure terminal, no graphics libraries needed
- **Cross-Platform** - Same experience on any operating system
- **Resource Efficient** - Minimal memory and CPU requirements

### **Power User Efficiency**

- **Fast Navigation** - Navigate buildings faster than with GUI tools
- **Keyboard Driven** - No mouse required, pure keyboard operation
- **Scriptable** - Automate building operations with scripts
- **Batch Operations** - Perform operations on multiple objects

### **Developer Experience**

- **Familiar Interface** - Git-like operations for building management
- **Version Control** - Track changes and rollback when needed
- **Query Language** - SQL-like queries for building data
- **API Integration** - REST and WebSocket APIs for external tools

---

**The Arxos CLI represents a fundamental shift in building management - making complex building infrastructure accessible through the universal language of the terminal.** 🖥️✨
