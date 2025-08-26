# Arxos CLI Development Guide

This guide covers developing the Arxos command-line interface, emphasizing the "Building as Filesystem" and "Infrastructure as Code" principles.

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Command Structure](#command-structure)
3. [Initialization Patterns](#initialization-patterns)
4. [Navigation System](#navigation-system)
5. [Infinite Zoom](#infinite-zoom)
6. [Search and Query](#search-and-query)
7. [Building Operations](#building-operations)
8. [Version Control](#version-control)
9. [Real-time Operations](#real-time-operations)
10. [Mobile Integration](#mobile-integration)
11. [Testing](#testing)
12. [Performance Considerations](#performance-considerations)

## Design Philosophy

The Arxos CLI follows these core principles:

- **Building as Filesystem**: Every building is a navigable filesystem with familiar Unix-like commands
- **Infrastructure as Code**: Buildings are defined through declarative YAML configurations
- **Progressive Reality**: Start simple and build complexity through field validation
- **Terminal First**: CLI is the primary interface for power users and automation
- **AR Integration**: Seamless connection between terminal operations and field reality

## Command Structure

### Root Command Structure

```go
// Root command with building context
var RootCmd = &cobra.Command{
    Use:   "arx",
    Short: "Arxos - Building Infrastructure as Code",
    Long: `Arxos transforms buildings into navigable filesystems with Git-like version control.
    
    Think of buildings as code - every wall, room, and system is an ArxObject
    that can be navigated, modified, and version controlled through the terminal.`,
    PersistentPreRun: func(cmd *cobra.Command, args []string) {
        // Initialize building context
        initBuildingContext(cmd)
    },
}
```

### Command Categories

```go
// Command organization by functionality
func init() {
    // Initialization commands
    RootCmd.AddCommand(initCmd)
    
    // Navigation commands
    RootCmd.AddCommand(cdCmd, lsCmd, pwdCmd, treeCmd, zoomCmd)
    
    // Inspection commands
    RootCmd.AddCommand(inspectCmd, statusCmd, propertiesCmd)
    
    // Search commands
    RootCmd.AddCommand(findCmd, grepCmd, locateCmd)
    
    // Management commands
    RootCmd.AddCommand(createCmd, modifyCmd, deleteCmd)
    
    // Version control commands
    RootCmd.AddCommand(commitCmd, branchCmd, mergeCmd)
    
    // Operations commands
    RootCmd.AddCommand(startCmd, stopCmd, restartCmd)
    
    // Export commands
    RootCmd.AddCommand(exportCmd, backupCmd, reportCmd)
}
```

## Initialization Patterns

### The `arx init` Command

The `arx init` command is the **entry point** for working with Arxos - it creates the building filesystem foundation that all other commands depend on.

#### Command Implementation

```go
var initCmd = &cobra.Command{
    Use:   "init [building-id]",
    Short: "Initialize a new building filesystem",
    Long: `Initialize creates a new building filesystem and ArxObject hierarchy.
    
    This command sets up the foundational structure that enables all other
    Arxos operations. Think of it as 'git init' for buildings.`,
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
    initCmd.Flags().String("config", "", "Use custom configuration file")
    initCmd.Flags().String("template", "", "Use predefined building template")
    initCmd.Flags().Bool("force", false, "Overwrite existing building if it exists")
}
```

#### Initialization Process

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
    
    // 4. Initialize ArxObject hierarchy
    if err := initializeArxObjectHierarchy(buildingID, cmd); err != nil {
        return fmt.Errorf("failed to initialize ArxObjects: %w", err)
    }
    
    // 5. Set up version control
    if err := initializeVersionControl(buildingID); err != nil {
        return fmt.Errorf("failed to initialize version control: %w", err)
    }
    
    // 6. Create initial configuration
    if err := createInitialConfiguration(buildingID, cmd); err != nil {
        return fmt.Errorf("failed to create configuration: %w", err)
    }
    
    // 7. Process input files if provided
    if err := processInputFiles(buildingID, cmd); err != nil {
        return fmt.Errorf("failed to process input files: %w", err)
    }
    
    fmt.Printf("✅ Building %s initialized successfully!\n", buildingID)
    fmt.Printf("📁 Navigate to building: arx cd %s\n", buildingID)
    fmt.Printf("📋 View structure: arx ls --tree\n")
    
    return nil
}
```

#### Building Filesystem Structure

```go
func createBuildingFilesystem(buildingID string) error {
    basePath := getBuildingPath(buildingID)
    
    // Create main building directory
    if err := os.MkdirAll(basePath, 0755); err != nil {
        return err
    }
    
    // Create metadata directory structure
    metadataDirs := []string{
        ".arxos/config",
        ".arxos/objects", 
        ".arxos/vcs/snapshots",
        ".arxos/vcs/branches",
        ".arxos/cache",
        "systems/electrical",
        "systems/hvac",
        "systems/automation",
        "schemas",
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

#### ArxObject Hierarchy Initialization

```go
func initializeArxObjectHierarchy(buildingID string, cmd *cobra.Command) error {
    // Create root building ArxObject
    buildingObj := &ArxObject{
        ID:       buildingID,
        Type:     ArxObjectTypeBuilding,
        Name:     getStringFlag(cmd, "name"),
        Position: Point3D{X: 0, Y: 0, Z: 0},
        Properties: map[string]interface{}{
            "type":     getStringFlag(cmd, "type"),
            "floors":   getIntFlag(cmd, "floors"),
            "area":     getStringFlag(cmd, "area"),
            "location": getStringFlag(cmd, "location"),
        },
        Children: make([]*ArxObject, 0),
    }
    
    // Create floor ArxObjects
    floors := getIntFlag(cmd, "floors")
    for i := 1; i <= floors; i++ {
        floorObj := &ArxObject{
            ID:       fmt.Sprintf("floor:%d", i),
            Type:     ArxObjectTypeFloor,
            Name:     fmt.Sprintf("Floor %d", i),
            Position: Point3D{X: 0, Y: 0, Z: int64(i-1) * 3000}, // 3m floor height
            Properties: map[string]interface{}{
                "floor_number": i,
                "height":       3000, // mm
            },
            Children: make([]*ArxObject, 0),
        }
        buildingObj.Children = append(buildingObj.Children, floorObj)
    }
    
    // Create system ArxObjects
    systems := []string{"electrical", "hvac", "automation"}
    for _, system := range systems {
        systemObj := &ArxObject{
            ID:       fmt.Sprintf("systems:%s", system),
            Type:     ArxObjectTypeSystem,
            Name:     fmt.Sprintf("%s System", strings.Title(system)),
            Position: Point3D{X: 0, Y: 0, Z: 0},
            Properties: map[string]interface{}{
                "system_type": system,
                "status":      "inactive",
            },
            Children: make([]*ArxObject, 0),
        }
        buildingObj.Children = append(buildingObj.Children, systemObj)
    }
    
    // Save to ArxObject database
    return saveArxObjectHierarchy(buildingID, buildingObj)
}
```

#### Configuration File Creation

```go
func createInitialConfiguration(buildingID string, cmd *cobra.Command) error {
    basePath := getBuildingPath(buildingID)
    
    // Main building configuration
    mainConfig := BuildingConfig{
        BuildingID: buildingID,
        Type:       getStringFlag(cmd, "type"),
        Floors:     getIntFlag(cmd, "floors"),
        Area:       getStringFlag(cmd, "area"),
        Location:   getStringFlag(cmd, "location"),
        Created:    time.Now().UTC(),
        Version:    "1.0.0",
        Systems: map[string]SystemConfig{
            "electrical": {
                Type:    "electrical",
                Status:  "inactive",
                Voltage: "480V",
            },
            "hvac": {
                Type:   "hvac",
                Status: "inactive",
            },
            "automation": {
                Type:   "automation",
                Status: "inactive",
            },
        },
    }
    
    // Write main configuration
    mainConfigPath := filepath.Join(basePath, "arxos.yml")
    if err := writeYAML(mainConfigPath, mainConfig); err != nil {
        return err
    }
    
    // Write floor configurations
    floors := getIntFlag(cmd, "floors")
    for i := 1; i <= floors; i++ {
        floorConfig := FloorConfig{
            FloorNumber: i,
            Height:      3000, // mm
            Status:      "inactive",
        }
        
        floorConfigPath := filepath.Join(basePath, fmt.Sprintf("floor:%d", i), "arxos.yml")
        if err := writeYAML(floorConfigPath, floorConfig); err != nil {
            return err
        }
    }
    
    // Write system configurations
    for systemName, systemConfig := range mainConfig.Systems {
        systemConfigPath := filepath.Join(basePath, "systems", systemName, "arxos.yml")
        if err := writeYAML(systemConfigPath, systemConfig); err != nil {
            return err
        }
    }
    
    return nil
}
```

#### Input File Processing

```go
func processInputFiles(buildingID string, cmd *cobra.Command) error {
    // Process PDF floor plan if provided
    if pdfPath := getStringFlag(cmd, "from-pdf"); pdfPath != "" {
        if err := processPDFFloorPlan(buildingID, pdfPath); err != nil {
            return fmt.Errorf("PDF processing failed: %w", err)
        }
    }
    
    // Process IFC file if provided
    if ifcPath := getStringFlag(cmd, "from-ifc"); ifcPath != "" {
        if err := processIFCFile(buildingID, ifcPath); err != nil {
            return fmt.Errorf("IFC processing failed: %w", err)
        }
    }
    
    // Process custom configuration if provided
    if configPath := getStringFlag(cmd, "config"); configPath != "" {
        if err := processCustomConfig(buildingID, configPath); err != nil {
            return fmt.Errorf("custom config processing failed: %w", err)
        }
    }
    
    // Apply template if provided
    if template := getStringFlag(cmd, "template"); template != "" {
        if err := applyBuildingTemplate(buildingID, template); err != nil {
            return fmt.Errorf("template application failed: %w", err)
        }
    }
    
    return nil
}
```

#### Metadata Directory Structure

The `.arxos` directory contains all the metadata needed to operate the building filesystem:

```
.arxos/
├── config/                    # Building configuration files
│   ├── arxos.yml            # Main building configuration
│   ├── environments/         # Environment-specific configs
│   │   ├── development.yml
│   │   ├── staging.yml
│   │   └── production.yml
│   └── templates/            # Building templates
│       ├── office.yml
│       ├── residential.yml
│       └── industrial.yml
├── objects/                   # ArxObject database
│   ├── index.db             # Spatial and property indexes
│   ├── objects.db           # ArxObject storage
│   └── relationships.db      # Object relationship graph
├── vcs/                      # Version control data
│   ├── snapshots/            # Building state snapshots
│   │   ├── HEAD             # Current state
│   │   ├── main             # Main branch
│   │   └── commits/         # Individual commits
│   ├── branches/             # Version branches
│   │   ├── main             # Main branch
│   │   └── feature/         # Feature branches
│   └── metadata/             # VCS metadata
│       ├── config           # VCS configuration
│       └── hooks/           # Pre/post commit hooks
├── cache/                     # Temporary data and cache
│   ├── ascii/               # ASCII rendering cache
│   ├── spatial/             # Spatial query cache
│   └── validation/          # Validation result cache
└── logs/                      # Building operation logs
    ├── access.log            # Command access logs
    ├── error.log             # Error logs
    └── audit.log             # Change audit logs
```

#### Configuration Schema

```yaml
# arxos.schema.yml - Building configuration schema
BuildingConfig:
  type: object
  required: [building_id, type, floors]
  properties:
    building_id:
      type: string
      pattern: '^building:[a-zA-Z0-9_-]+$'
    type:
      type: string
      enum: [office, residential, industrial, retail, mixed_use]
    floors:
      type: integer
      minimum: 1
      maximum: 200
    area:
      type: string
      description: "Total building area (e.g., '25,000 sq ft')"
    location:
      type: string
      description: "Building address or coordinates"
    created:
      type: string
      format: date-time
    version:
      type: string
      pattern: '^\\d+\\.\\d+\\.\\d+$'
    systems:
      type: object
      additionalProperties:
        $ref: '#/definitions/SystemConfig'

SystemConfig:
  type: object
  required: [type, status]
  properties:
    type:
      type: string
      enum: [electrical, hvac, automation, structural, plumbing]
    status:
      type: string
      enum: [inactive, active, maintenance, error]
    voltage:
      type: string
      description: "System voltage (for electrical systems)"
    capacity:
      type: string
      description: "System capacity"
```

### Initialization Workflow

The complete initialization workflow follows this sequence:

1. **Validation**: Check building ID format and existence
2. **Filesystem Creation**: Create directory structure and metadata
3. **ArxObject Initialization**: Create core building hierarchy
4. **Configuration Setup**: Generate initial configuration files
5. **Version Control**: Initialize Git-like version control
6. **Input Processing**: Handle PDF/IFC files and templates
7. **Validation**: Verify the created structure
8. **Success Feedback**: Provide user guidance for next steps

This initialization pattern ensures that every building has a consistent, navigable structure that supports all subsequent CLI operations.

## Navigation System

### Path Resolution Engine

The path resolution engine is the core of the navigation system, translating human-readable paths into ArxObject references.

```go
type PathResolver struct {
    currentPath string
    buildingID  string
    cache       map[string]*ArxObject
}

func (pr *PathResolver) ResolvePath(path string) (*ArxObject, error) {
    // Handle special paths
    switch path {
    case "/", "":
        return pr.getBuildingRoot()
    case "~":
        return pr.getHomeBuilding()
    case ".", "":
        return pr.getCurrentObject()
    case "..":
        return pr.getParentObject()
    }
    
    // Resolve relative or absolute paths
    if strings.HasPrefix(path, "/") {
        return pr.resolveAbsolutePath(path)
    }
    return pr.resolveRelativePath(path)
}
```

### Working Directory Management

```go
type WorkingDirectory struct {
    currentPath string
    buildingID  string
    history     []string
    maxHistory  int
}

func (wd *WorkingDirectory) ChangeDirectory(path string) error {
    // Resolve the target path
    target, err := wd.resolvePath(path)
    if err != nil {
        return err
    }
    
    // Validate that it's navigable
    if !target.IsNavigable() {
        return fmt.Errorf("cannot navigate to %s: not a navigable object", path)
    }
    
    // Add to history
    wd.addToHistory(wd.currentPath)
    
    // Update current path
    wd.currentPath = target.GetPath()
    
    return nil
}

func (wd *WorkingDirectory) GetCurrentPath() string {
    return wd.currentPath
}

func (wd *WorkingDirectory) GetHistory() []string {
    return wd.history
}
```

### Infinite Zoom Navigation

```go
type ZoomLevel struct {
    Level     string  // campus, building, floor, room, component
    Scale     float64 // zoom factor
    Detail    string  // detail level
    Context   string  // context information
}

type ZoomNavigator struct {
    currentLevel ZoomLevel
    levels       []ZoomLevel
    cache        map[string]*ArxObject
}

func (zn *ZoomNavigator) ZoomIn() error {
    currentIndex := zn.getCurrentLevelIndex()
    if currentIndex >= len(zn.levels)-1 {
        return fmt.Errorf("already at maximum zoom level")
    }
    
    zn.currentLevel = zn.levels[currentIndex+1]
    return zn.updateView()
}

func (zn *ZoomNavigator) ZoomOut() error {
    currentIndex := zn.getCurrentLevelIndex()
    if currentIndex <= 0 {
        return fmt.Errorf("already at minimum zoom level")
    }
    
    zn.currentLevel = zn.levels[currentIndex-1]
    return zn.updateView()
}

func (zn *ZoomNavigator) ZoomTo(level string) error {
    for _, l := range zn.levels {
        if l.Level == level {
            zn.currentLevel = l
            return zn.updateView()
        }
    }
    return fmt.Errorf("invalid zoom level: %s", level)
}
```

## Search and Query

### Find Engine

```go
type FindEngine struct {
    indexer    *SpatialIndexer
    validator  *ValidationEngine
    cache      *QueryCache
}

type FindQuery struct {
    Type       string            `json:"type"`
    Properties map[string]string `json:"properties"`
    Location   *LocationQuery    `json:"location"`
    System     string            `json:"system"`
    Status     string            `json:"status"`
    Confidence float64           `json:"confidence"`
    Limit      int               `json:"limit"`
}

func (fe *FindEngine) Find(query *FindQuery) ([]*ArxObject, error) {
    // Build spatial query
    spatialQuery := fe.buildSpatialQuery(query)
    
    // Execute spatial search
    candidates, err := fe.indexer.Search(spatialQuery)
    if err != nil {
        return nil, err
    }
    
    // Apply property filters
    filtered := fe.applyPropertyFilters(candidates, query.Properties)
    
    // Apply system filters
    if query.System != "" {
        filtered = fe.applySystemFilters(filtered, query.System)
    }
    
    // Apply status filters
    if query.Status != "" {
        filtered = fe.applyStatusFilters(filtered, query.Status)
    }
    
    // Apply confidence threshold
    if query.Confidence > 0 {
        filtered = fe.applyConfidenceFilter(filtered, query.Confidence)
    }
    
    // Apply limit
    if query.Limit > 0 && len(filtered) > query.Limit {
        filtered = filtered[:query.Limit]
    }
    
    return filtered, nil
}
```

### AQL Parser

```go
type AQLParser struct {
    lexer  *SQLLexer
    parser *SQLParser
}

type AQLQuery struct {
    Select   []string          `json:"select"`
    From     string            `json:"from"`
    Where    []*WhereClause    `json:"where"`
    OrderBy  []string          `json:"order_by"`
    Limit    int               `json:"limit"`
    Offset   int               `json:"offset"`
}

func (ap *AQLParser) Parse(query string) (*AQLQuery, error) {
    tokens, err := ap.lexer.Tokenize(query)
    if err != nil {
        return nil, err
    }
    
    return ap.parser.Parse(tokens)
}

func (ap *AQLParser) Execute(query *AQLQuery) ([]*ArxObject, error) {
    // Parse the FROM clause to get building context
    buildingID, err := ap.parseBuildingContext(query.From)
    if err != nil {
        return nil, err
    }
    
    // Build spatial query from WHERE clauses
    spatialQuery := ap.buildSpatialQuery(query.Where)
    
    // Execute search
    results, err := ap.findEngine.Find(spatialQuery)
    if err != nil {
        return nil, err
    }
    
    // Apply property filters
    results = ap.applyPropertyFilters(results, query.Where)
    
    // Apply ordering
    if len(query.OrderBy) > 0 {
        results = ap.applyOrdering(results, query.OrderBy)
    }
    
    // Apply limit and offset
    if query.Limit > 0 {
        if query.Offset > 0 {
            if query.Offset < len(results) {
                results = results[query.Offset:]
            } else {
                results = []*ArxObject{}
            }
        }
        if len(results) > query.Limit {
            results = results[:query.Limit]
        }
    }
    
    return results, nil
}
```

## Building Operations

### State Management

```go
type BuildingState struct {
    BuildingID    string                 `json:"building_id"`
    CurrentPath   string                 `json:"current_path"`
    ArxObjects    map[string]*ArxObject  `json:"arx_objects"`
    Properties    map[string]interface{} `json:"properties"`
    Relationships map[string][]string     `json:"relationships"`
    Metadata      map[string]interface{} `json:"metadata"`
    LastModified  time.Time              `json:"last_modified"`
}

type StateManager struct {
    buildingID string
    state      *BuildingState
    mutex      sync.RWMutex
    watchers   []StateWatcher
}

func (sm *StateManager) GetState() *BuildingState {
    sm.mutex.RLock()
    defer sm.mutex.RUnlock()
    return sm.state
}

func (sm *StateManager) UpdateState(updates map[string]interface{}) error {
    sm.mutex.Lock()
    defer sm.mutex.Unlock()
    
    // Apply updates
    for key, value := range updates {
        if err := sm.applyUpdate(key, value); err != nil {
            return err
        }
    }
    
    // Update timestamp
    sm.state.LastModified = time.Now().UTC()
    
    // Notify watchers
    sm.notifyWatchers()
    
    return nil
}
```

### Version Control

```go
type BuildingVCS struct {
    buildingID string
    snapshots  *SnapshotManager
    branches   *BranchManager
    commits    *CommitManager
}

type Snapshot struct {
    ID          string                 `json:"id"`
    Message     string                 `json:"message"`
    Author      string                 `json:"author"`
    Timestamp   time.Time              `json:"timestamp"`
    State       *BuildingState         `json:"state"`
    Parent      string                 `json:"parent"`
    Children    []string               `json:"children"`
    Metadata    map[string]interface{} `json:"metadata"`
}

func (vcs *BuildingVCS) CreateSnapshot(message string, author string) (*Snapshot, error) {
    // Get current state
    currentState := vcs.getCurrentState()
    
    // Create snapshot
    snapshot := &Snapshot{
        ID:        generateSnapshotID(),
        Message:   message,
        Author:    author,
        Timestamp: time.Now().UTC(),
        State:     currentState,
        Parent:    vcs.getCurrentSnapshotID(),
        Children:  []string{},
        Metadata:  make(map[string]interface{}),
    }
    
    // Save snapshot
    if err := vcs.snapshots.Save(snapshot); err != nil {
        return nil, err
    }
    
    // Update current pointer
    vcs.setCurrentSnapshot(snapshot.ID)
    
    return snapshot, nil
}
```

## Real-time Operations

### Live State Manager

```go
type LiveStateManager struct {
    buildingID string
    state      *BuildingState
    watchers   map[string]StateWatcher
    mutex      sync.RWMutex
    ticker     *time.Ticker
    done       chan bool
}

type StateWatcher interface {
    OnStateChange(oldState, newState *BuildingState)
    OnPropertyChange(objectID, property string, oldValue, newValue interface{})
    OnObjectAdded(object *ArxObject)
    OnObjectRemoved(objectID string)
}

func (lsm *LiveStateManager) Start() {
    lsm.ticker = time.NewTicker(100 * time.Millisecond) // 10 FPS
    lsm.done = make(chan bool)
    
    go func() {
        for {
            select {
            case <-lsm.ticker.C:
                lsm.checkForUpdates()
            case <-lsm.done:
                return
            }
        }
    }()
}

func (lsm *LiveStateManager) Stop() {
    if lsm.ticker != nil {
        lsm.ticker.Stop()
    }
    if lsm.done != nil {
        close(lsm.done)
    }
}
```

## Mobile Integration

### Touch CLI

```go
type TouchCLI struct {
    buildingID string
    session    *ARSession
    commands   map[string]TouchCommand
}

type TouchCommand struct {
    Name        string                 `json:"name"`
    Description string                 `json:"description"`
    Gesture     string                 `json:"gesture"`
    Parameters  map[string]interface{} `json:"parameters"`
    Handler     func(*TouchContext)    `json:"-"`
}

type TouchContext struct {
    UserID      string                 `json:"user_id"`
    Location    Point3D                `json:"location"`
    Gesture     string                 `json:"gesture"`
    Parameters  map[string]interface{} `json:"parameters"`
    BuildingID  string                 `json:"building_id"`
    ObjectID    string                 `json:"object_id"`
}

func (tcli *TouchCLI) HandleTouchCommand(ctx *TouchContext) error {
    command, exists := tcli.commands[ctx.Gesture]
    if !exists {
        return fmt.Errorf("unknown touch command: %s", ctx.Gesture)
    }
    
    // Validate parameters
    if err := tcli.validateParameters(command, ctx.Parameters); err != nil {
        return err
    }
    
    // Execute command
    return command.Handler(ctx)
}

func (tcli *TouchCLI) RegisterCommand(cmd TouchCommand) {
    tcli.commands[cmd.Gesture] = cmd
}
```

### AR Field App Integration

```go
type ARFieldApp struct {
    buildingID string
    session    *ARSession
    cli        *TouchCLI
    scanner    *QRScanner
    validator  *FieldValidator
}

type ARSession struct {
    SessionID  string                 `json:"session_id"`
    UserID     string                 `json:"user_id"`
    BuildingID string                 `json:"building_id"`
    Location   Point3D                `json:"location"`
    Objects    []*ARObject            `json:"objects"`
    Status     string                 `json:"status"`
    StartTime  time.Time              `json:"start_time"`
}

type ARObject struct {
    ObjectID   string                 `json:"object_id"`
    Type       string                 `json:"type"`
    Position   Point3D                `json:"position"`
    Properties map[string]interface{} `json:"properties"`
    Status     string                 `json:"status"`
    Confidence float64                `json:"confidence"`
}

func (arfa *ARFieldApp) StartSession(userID string) (*ARSession, error) {
    session := &ARSession{
        SessionID:  generateSessionID(),
        UserID:     userID,
        BuildingID: arfa.buildingID,
        Location:   arfa.getCurrentLocation(),
        Objects:    []*ARObject{},
        Status:     "active",
        StartTime:  time.Now().UTC(),
    }
    
    arfa.session = session
    
    // Start AR tracking
    if err := arfa.startARTracking(); err != nil {
        return nil, err
    }
    
    return session, nil
}

func (arfa *ARFieldApp) ScanQRCode(qrData string) error {
    // Parse QR code data
    objectID, err := arfa.parseQRCode(qrData)
    if err != nil {
        return err
    }
    
    // Get object from building
    object, err := arfa.getObject(objectID)
    if err != nil {
        return err
    }
    
    // Add to AR session
    arfa.session.Objects = append(arfa.session.Objects, &ARObject{
        ObjectID:   object.ID,
        Type:       object.Type,
        Position:   object.Position,
        Properties: object.Properties,
        Status:     object.Status,
        Confidence: object.Confidence,
    })
    
    return nil
}
```

## Testing

### Command Testing

```go
func TestInitCommand(t *testing.T) {
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
    
    // Test basic initialization
    cmd := exec.Command("arx", "init", "building:test", "--type", "office", "--floors", "2")
    output, err := cmd.CombinedOutput()
    if err != nil {
        t.Fatalf("init command failed: %v\nOutput: %s", err, output)
    }
    
    // Verify filesystem structure
    if !fileExists("building:test/.arxos/config/arxos.yml") {
        t.Error("building configuration file not created")
    }
    
    if !fileExists("building:test/floor:1/arxos.yml") {
        t.Error("floor configuration file not created")
    }
    
    if !fileExists("building:test/systems/electrical/arxos.yml") {
        t.Error("electrical system configuration not created")
    }
    
    // Test navigation
    cmd = exec.Command("arx", "cd", "building:test")
    if err := cmd.Run(); err != nil {
        t.Errorf("cd command failed: %v", err)
    }
    
    // Test listing
    cmd = exec.Command("arx", "ls", "--tree")
    output, err = cmd.CombinedOutput()
    if err != nil {
        t.Errorf("ls command failed: %v", err)
    }
    
    // Verify output contains expected structure
    if !strings.Contains(string(output), "floor:1") {
        t.Error("tree output missing floor:1")
    }
    
    if !strings.Contains(string(output), "systems:electrical") {
        t.Error("tree output missing electrical system")
    }
}
```

### Integration Testing

```go
func TestCompleteWorkflow(t *testing.T) {
    // Setup test environment
    testDir := setupTestEnvironment(t)
    defer cleanupTestEnvironment(t, testDir)
    
    // 1. Initialize building
    t.Run("Initialize", func(t *testing.T) {
        testBuildingInitialization(t)
    })
    
    // 2. Navigate and create structure
    t.Run("Navigation", func(t *testing.T) {
        testNavigationAndCreation(t)
    })
    
    // 3. Version control operations
    t.Run("VersionControl", func(t *testing.T) {
        testVersionControl(t)
    })
    
    // 4. Search and query
    t.Run("Search", func(t *testing.T) {
        testSearchAndQuery(t)
    })
    
    // 5. Export and backup
    t.Run("Export", func(t *testing.T) {
        testExportAndBackup(t)
    })
}

func testBuildingInitialization(t *testing.T) {
    // Test various initialization scenarios
    testCases := []struct {
        name     string
        args     []string
        expected []string
    }{
        {
            name: "Basic Office",
            args: []string{"building:office", "--type", "office", "--floors", "3"},
            expected: []string{
                "building:office/.arxos/config/arxos.yml",
                "building:office/floor:1/arxos.yml",
                "building:office/floor:2/arxos.yml",
                "building:office/floor:3/arxos.yml",
                "building:office/systems/electrical/arxos.yml",
                "building:office/systems/hvac/arxos.yml",
                "building:office/systems/automation/arxos.yml",
            },
        },
        {
            name: "Industrial Warehouse",
            args: []string{"building:warehouse", "--type", "industrial", "--floors", "1", "--area", "50,000 sq ft"},
            expected: []string{
                "building:warehouse/.arxos/config/arxos.yml",
                "building:warehouse/floor:1/arxos.yml",
                "building:warehouse/systems/electrical/arxos.yml",
            },
        },
    }
    
    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            cmd := exec.Command("arx", append([]string{"init"}, tc.args...)...)
            if err := cmd.Run(); err != nil {
                t.Errorf("init command failed: %v", err)
                return
            }
            
            // Verify expected files exist
            for _, expectedFile := range tc.expected {
                if !fileExists(expectedFile) {
                    t.Errorf("expected file not created: %s", expectedFile)
                }
            }
        })
    }
}
```

## Performance Considerations

### Caching Strategy

```go
type CacheManager struct {
    objectCache    *ObjectCache
    spatialCache   *SpatialCache
    queryCache     *QueryCache
    renderCache    *RenderCache
}

type ObjectCache struct {
    cache map[string]*ArxObject
    mutex sync.RWMutex
    ttl   time.Duration
}

func (oc *ObjectCache) Get(key string) (*ArxObject, bool) {
    oc.mutex.RLock()
    defer oc.mutex.RUnlock()
    
    obj, exists := oc.cache[key]
    if !exists {
        return nil, false
    }
    
    // Check TTL
    if time.Since(obj.LastAccessed) > oc.ttl {
        delete(oc.cache, key)
        return nil, false
    }
    
    // Update access time
    obj.LastAccessed = time.Now().UTC()
    return obj, true
}

func (oc *ObjectCache) Set(key string, obj *ArxObject) {
    oc.mutex.Lock()
    defer oc.mutex.Unlock()
    
    obj.LastAccessed = time.Now().UTC()
    oc.cache[key] = obj
}
```

### Spatial Indexing

```go
type SpatialIndexer struct {
    rtree    *rtree.RTree
    mutex    sync.RWMutex
    objects  map[string]*ArxObject
}

func (si *SpatialIndexer) Insert(obj *ArxObject) error {
    si.mutex.Lock()
    defer si.mutex.Unlock()
    
    // Create spatial bounds
    bounds := obj.GetBoundingBox()
    
    // Insert into R-tree
    si.rtree.Insert(bounds, obj)
    
    // Store object reference
    si.objects[obj.ID] = obj
    
    return nil
}

func (si *SpatialIndexer) Search(query *SpatialQuery) ([]*ArxObject, error) {
    si.mutex.RLock()
    defer si.mutex.RUnlock()
    
    var results []*ArxObject
    
    // Execute spatial search
    si.rtree.Search(query.Bounds, func(item interface{}) bool {
        if obj, ok := item.(*ArxObject); ok {
            if si.matchesQuery(obj, query) {
                results = append(results, obj)
            }
        }
        return true
    })
    
    return results, nil
}
```

This development guide provides comprehensive coverage of building the Arxos CLI, from initialization patterns to advanced features like real-time operations and mobile integration. The focus on "Building as Filesystem" and "Infrastructure as Code" principles ensures that the CLI provides a familiar, powerful interface for managing buildings through the terminal.
