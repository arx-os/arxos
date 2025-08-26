# CLI Architecture

## 🎯 **Overview**

The Arxos CLI is designed as a powerful, intuitive interface for managing buildings as programmable infrastructure. It provides familiar Unix-like commands while adding building-specific functionality, enabling users to navigate, inspect, and operate buildings through the command line.

## 🏗️ **Design Philosophy**

### **Building as Filesystem**
- **Familiar Commands**: `cd`, `ls`, `pwd`, `tree`, `find` work just like Unix filesystems
- **Hierarchical Navigation**: Navigate from campus to microchip level seamlessly
- **Path-Based Addressing**: Every building component has a unique path
- **Infinite Depth**: No limit to how deep you can navigate

### **Infrastructure as Code**
- **YAML Configuration**: Buildings defined through declarative YAML files
- **Git-Like Version Control**: Commit, branch, merge, and rollback building changes
- **Automated Operations**: Script building management tasks
- **CI/CD Integration**: Integrate building operations into deployment pipelines

### **Field-First Design**
- **Mobile Optimized**: Touch-friendly interface for field workers
- **AR Integration**: Seamless transition between CLI and AR views
- **Offline Capable**: Full functionality without internet connection
- **Real-Time Updates**: Live building state synchronization

## 🏛️ **Architecture Overview**

### **Component Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI INTERFACE LAYER                          │
│  Command Parser │  Interactive Shell │  Auto-completion        │
│  - Cobra CLI    │  - REPL interface  │  - Path completion      │
│  - Flag parsing │  - History support │  - Command suggestions   │
├─────────────────────────────────────────────────────────────────┤
│                COMMAND EXECUTION LAYER                          │
│  Navigation     │  Building Ops     │  Version Control         │
│  - cd, ls, pwd  │  - inspect, status│  - commit, branch, merge│
│  - tree, find   │  - validate, sim  │  - rollback, diff        │
├─────────────────────────────────────────────────────────────────┤
│                ARXOBJECT INTEGRATION LAYER                      │
│  CGO Bridge     │  ArxObject Engine │  ASCII-BIM Renderer      │
│  - Go ↔ C calls │  - Tree traversal │  - ASCII generation      │
│  - Type safety  │  - Property ops   │  - Multi-resolution      │
├─────────────────────────────────────────────────────────────────┤
│                BUILDING STATE LAYER                             │
│  Database       │  Cache Layer      │  Real-time Sync          │
│  - PostgreSQL   │  - In-memory      │  - WebSocket updates     │
│  - Spatial index│  - LRU eviction   │  - Change notifications  │
└─────────────────────────────────────────────────────────────────┘
```

### **Data Flow**

```
User Input → Command Parser → Command Executor → ArxObject Engine → ASCII Renderer → Output
     ↓              ↓              ↓              ↓              ↓
  Interactive   Flag/Arg      Business      C Runtime      ASCII String
     Shell      Parsing        Logic        Operations     Generation
```

## 🔧 **Command Structure**

### **Command Hierarchy**

```go
// Root command structure
type RootCmd struct {
    Use   string
    Short string
    Long  string
    
    // Subcommands
    Commands []*cobra.Command
    
    // Global flags
    Building string
    Format   string
    Verbose  bool
}

// Command categories
var commandCategories = map[string][]*cobra.Command{
    "Navigation": {
        cdCmd, lsCmd, pwdCmd, treeCmd,
    },
    "Inspection": {
        inspectCmd, statusCmd, propertiesCmd,
    },
    "Search": {
        findCmd, grepCmd, locateCmd,
    },
    "Management": {
        createCmd, updateCmd, deleteCmd,
    },
    "Version Control": {
        commitCmd, branchCmd, mergeCmd, rollbackCmd,
    },
    "Operations": {
        validateCmd, simulateCmd, controlCmd,
    },
    "Export": {
        exportCmd, backupCmd, syncCmd,
    },
}
```

### **Command Pattern**

```go
// Standard command structure
var cdCmd = &cobra.Command{
    Use:     "cd [path]",
    Short:   "Change directory in building filesystem",
    Long:    `Navigate through the building hierarchy using familiar cd commands.`,
    Example: `  arx @building-47 cd /electrical/
  arx @building-47 cd /hvac/ahu-1/
  arx @building-47 cd ../../`,
    
    Args: cobra.MaximumNArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        return executeCD(cmd, args)
    },
}

// Command execution function
func executeCD(cmd *cobra.Command, args []string) error {
    // Get building context
    building := getBuildingFromContext(cmd)
    
    // Parse path argument
    var path string
    if len(args) > 0 {
        path = args[0]
    } else {
        path = "~" // Default to home
    }
    
    // Execute navigation
    return building.NavigateTo(path)
}
```

## 🧭 **Navigation System**

### **Path Resolution**

```go
// Path resolution engine
type PathResolver struct {
    current *ArxObject
    root    *ArxObject
    cache   map[string]*ArxObject
}

// Resolve path from current location
func (pr *PathResolver) ResolvePath(path string) (*ArxObject, error) {
    // Handle special paths
    if path == "/" {
        return pr.root, nil
    }
    if path == "." {
        return pr.current, nil
    }
    if path == ".." {
        if pr.current.Parent != nil {
            return pr.current.Parent, nil
        }
        return nil, fmt.Errorf("no parent directory")
    }
    if path == "~" {
        return pr.getHomeDirectory()
    }
    
    // Handle absolute paths
    if strings.HasPrefix(path, "/") {
        return pr.resolveAbsolutePath(path)
    }
    
    // Handle relative paths
    return pr.resolveRelativePath(path)
}

// Resolve absolute path
func (pr *PathResolver) resolveAbsolutePath(path string) (*ArxObject, error) {
    components := strings.Split(strings.Trim(path, "/"), "/")
    current := pr.root
    
    for _, component := range components {
        if component == "" {
            continue
        }
        
        child := current.GetChild(component)
        if child == nil {
            return nil, fmt.Errorf("path not found: %s", path)
        }
        current = child
    }
    
    return current, nil
}
```

### **Working Directory Management**

```go
// Working directory state
type WorkingDirectory struct {
    building *Building
    current  *ArxObject
    history  []*ArxObject
    maxHistory int
}

// Change directory
func (wd *WorkingDirectory) ChangeDirectory(path string) error {
    // Resolve path
    target, err := wd.building.ResolvePath(path)
    if err != nil {
        return err
    }
    
    // Add to history
    wd.addToHistory(wd.current)
    
    // Update current directory
    wd.current = target
    
    return nil
}

// Get current path
func (wd *WorkingDirectory) GetCurrentPath() string {
    if wd.current == nil {
        return "/"
    }
    
    path := wd.current.Name
    parent := wd.current.Parent
    
    for parent != nil && parent != wd.building.Root {
        path = parent.Name + "/" + path
        parent = parent.Parent
    }
    
    return "/" + path
}
```

## 🔍 **Search and Query System**

### **Find Command Engine**

```go
// Find command engine
type FindEngine struct {
    building *Building
    index    *SpatialIndex
}

// Find objects by criteria
func (fe *FindEngine) Find(criteria *FindCriteria) ([]*ArxObject, error) {
    var results []*ArxObject
    
    // Start search from root or specified path
    startPath := criteria.StartPath
    if startPath == "" {
        startPath = "/"
    }
    
    startObject, err := fe.building.ResolvePath(startPath)
    if err != nil {
        return nil, err
    }
    
    // Execute search based on criteria
    if criteria.TypeFilter != "" {
        results = fe.findByType(startObject, criteria.TypeFilter, criteria.MaxDepth)
    } else if len(criteria.PropertyFilters) > 0 {
        results = fe.findByProperties(startObject, criteria.PropertyFilters, criteria.MaxDepth)
    } else if criteria.SpatialFilter != nil {
        results = fe.findBySpatialCriteria(startObject, criteria.SpatialFilter)
    } else {
        // Default: find all objects
        results = fe.findAllObjects(startObject, criteria.MaxDepth)
    }
    
    // Apply result limits
    if criteria.MaxResults > 0 && len(results) > criteria.MaxResults {
        results = results[:criteria.MaxResults]
    }
    
    return results, nil
}

// Find criteria structure
type FindCriteria struct {
    StartPath       string
    TypeFilter      string
    PropertyFilters []PropertyFilter
    SpatialFilter   *SpatialFilter
    MaxDepth        int
    MaxResults      int
    Format          string
}

type PropertyFilter struct {
    Key      string
    Operator string
    Value    interface{}
}
```

### **Query Language (AQL)**

```go
// Arxos Query Language parser
type AQLParser struct {
    scanner *Scanner
    parser  *Parser
}

// Parse AQL query
func (aql *AQLParser) ParseQuery(query string) (*Query, error) {
    // Tokenize query
    tokens, err := aql.scanner.Scan(query)
    if err != nil {
        return nil, err
    }
    
    // Parse tokens into AST
    ast, err := aql.parser.Parse(tokens)
    if err != nil {
        return nil, err
    }
    
    return ast, nil
}

// Example AQL queries
var exampleQueries = []string{
    "SELECT * FROM building:hq:floor:3 WHERE type = 'wall'",
    "SELECT * FROM building:* WHERE confidence < 0.7",
    "SELECT path, type, confidence FROM /electrical WHERE type = 'outlet'",
    "FIND /hvac WHERE temperature > 75F AND status = 'active'",
}
```

## 🛠️ **Building Operations**

### **Inspection Engine**

```go
// Inspection engine for examining objects
type InspectionEngine struct {
    building *Building
    formatter *OutputFormatter
}

// Inspect object
func (ie *InspectionEngine) Inspect(path string, options *InspectOptions) (*InspectionResult, error) {
    // Resolve object
    obj, err := ie.building.ResolvePath(path)
    if err != nil {
        return nil, err
    }
    
    // Build inspection result
    result := &InspectionResult{
        Object: obj,
        Properties: ie.getObjectProperties(obj, options),
        Relationships: ie.getObjectRelationships(obj, options),
        History: ie.getObjectHistory(obj, options),
        Validation: ie.getObjectValidation(obj, options),
    }
    
    return result, nil
}

// Inspection options
type InspectOptions struct {
    Format      string
    ShowProperties bool
    ShowRelationships bool
    ShowHistory bool
    ShowValidation bool
    MaxDepth    int
}

// Inspection result
type InspectionResult struct {
    Object        *ArxObject
    Properties   map[string]interface{}
    Relationships []Relationship
    History      []HistoryEntry
    Validation   ValidationInfo
}
```

### **Status Engine**

```go
// Status engine for building health
type StatusEngine struct {
    building *Building
    monitor  *BuildingMonitor
}

// Get building status
func (se *StatusEngine) GetStatus(path string, options *StatusOptions) (*StatusResult, error) {
    // Resolve target object
    target, err := se.building.ResolvePath(path)
    if err != nil {
        return nil, err
    }
    
    // Collect status information
    status := &StatusResult{
        Object: target,
        Health: se.getHealthStatus(target),
        Alerts: se.getActiveAlerts(target),
        Metrics: se.getPerformanceMetrics(target),
        LastUpdated: time.Now(),
    }
    
    return status, nil
}

// Status result
type StatusResult struct {
    Object       *ArxObject
    Health       HealthStatus
    Alerts       []Alert
    Metrics      map[string]float64
    LastUpdated  time.Time
}

type HealthStatus struct {
    Overall      string  // "healthy", "warning", "critical"
    Score        float64 // 0.0 - 1.0
    Issues       []Issue
    Recommendations []string
}
```

## 📚 **Version Control System**

### **Building Version Control**

```go
// Building version control system
type BuildingVCS struct {
    building *Building
    storage  *VersionStorage
    config   *VCSConfig
}

// Commit changes
func (vcs *BuildingVCS) Commit(message string, options *CommitOptions) (*Commit, error) {
    // Get current working state
    workingState, err := vcs.building.GetWorkingState()
    if err != nil {
        return nil, err
    }
    
    // Get last commit for comparison
    lastCommit, err := vcs.storage.GetLastCommit()
    if err != nil {
        return nil, err
    }
    
    // Calculate changes
    changes, err := vcs.calculateChanges(lastCommit.State, workingState)
    if err != nil {
        return nil, err
    }
    
    // Create commit
    commit := &Commit{
        ID:          generateCommitID(),
        Message:     message,
        Author:      options.Author,
        Timestamp:   time.Now(),
        Parent:      lastCommit.ID,
        Changes:     changes,
        State:       workingState,
        Tags:        options.Tags,
    }
    
    // Store commit
    err = vcs.storage.StoreCommit(commit)
    if err != nil {
        return nil, err
    }
    
    return commit, nil
}

// Commit structure
type Commit struct {
    ID        string
    Message   string
    Author    string
    Timestamp time.Time
    Parent    string
    Changes   []Change
    State     *BuildingState
    Tags      []string
}

type Change struct {
    Type      ChangeType // "create", "update", "delete"
    Path      string
    OldValue  interface{}
    NewValue  interface{}
    ObjectID  string
}
```

### **Branch Management**

```go
// Branch management
func (vcs *BuildingVCS) CreateBranch(name string, options *BranchOptions) (*Branch, error) {
    // Check if branch already exists
    if vcs.storage.BranchExists(name) {
        return nil, fmt.Errorf("branch %s already exists", name)
    }
    
    // Get current commit
    currentCommit, err := vcs.storage.GetCurrentCommit()
    if err != nil {
        return nil, err
    }
    
    // Create branch
    branch := &Branch{
        Name:       name,
        CommitID:   currentCommit.ID,
        Created:    time.Now(),
        Creator:    options.Creator,
        Description: options.Description,
    }
    
    // Store branch
    err = vcs.storage.StoreBranch(branch)
    if err != nil {
        return nil, err
    }
    
    return branch, nil
}

// Branch structure
type Branch struct {
    Name        string
    CommitID    string
    Created     time.Time
    Creator     string
    Description string
    IsActive    bool
}
```

## 🔄 **Real-Time Operations**

### **Live Building State**

```go
// Live building state manager
type LiveStateManager struct {
    building *Building
    cache    *StateCache
    notifier *ChangeNotifier
}

// Get real-time state
func (lsm *LiveStateManager) GetLiveState(path string) (*LiveState, error) {
    // Check cache first
    if cached := lsm.cache.Get(path); cached != nil {
        return cached, nil
    }
    
    // Get from building
    obj, err := lsm.building.ResolvePath(path)
    if err != nil {
        return nil, err
    }
    
    // Build live state
    liveState := &LiveState{
        Object:      obj,
        Properties:  lsm.getLiveProperties(obj),
        Performance: lsm.getPerformanceMetrics(obj),
        Alerts:      lsm.getActiveAlerts(obj),
        LastUpdate:  time.Now(),
    }
    
    // Cache result
    lsm.cache.Set(path, liveState)
    
    return liveState, nil
}

// Live state structure
type LiveState struct {
    Object      *ArxObject
    Properties  map[string]interface{}
    Performance map[string]float64
    Alerts      []Alert
    LastUpdate  time.Time
}
```

### **Change Notifications**

```go
// Change notification system
type ChangeNotifier struct {
    subscribers map[string][]Subscriber
    websocket   *WebSocketManager
}

// Subscribe to changes
func (cn *ChangeNotifier) Subscribe(path string, subscriber Subscriber) error {
    if cn.subscribers[path] == nil {
        cn.subscribers[path] = make([]Subscriber, 0)
    }
    
    cn.subscribers[path] = append(cn.subscribers[path], subscriber)
    return nil
}

// Notify subscribers of changes
func (cn *ChangeNotifier) NotifyChange(change *Change) error {
    // Notify local subscribers
    if subscribers, exists := cn.subscribers[change.Path]; exists {
        for _, subscriber := range subscribers {
            subscriber.OnChange(change)
        }
    }
    
    // Notify WebSocket clients
    if cn.websocket != nil {
        cn.websocket.BroadcastChange(change)
    }
    
    return nil
}
```

## 📱 **Mobile Integration**

### **Touch-Optimized Interface**

```go
// Touch-optimized CLI interface
type TouchCLI struct {
    cli        *CLI
    touchOpts  *TouchOptions
    gestureHandler *GestureHandler
}

// Handle touch gestures
func (tcli *TouchCLI) HandleGesture(gesture *TouchGesture) error {
    switch gesture.Type {
    case "tap":
        return tcli.handleTap(gesture)
    case "double_tap":
        return tcli.handleDoubleTap(gesture)
    case "long_press":
        return tcli.handleLongPress(gesture)
    case "swipe":
        return tcli.handleSwipe(gesture)
    case "pinch":
        return tcli.handlePinch(gesture)
    default:
        return fmt.Errorf("unknown gesture type: %s", gesture.Type)
    }
}

// Touch gesture structure
type TouchGesture struct {
    Type      string
    Position  Point2D
    Delta     Vector2D
    Scale     float64
    Duration  time.Duration
}
```

### **AR Mode Integration**

```go
// AR mode integration
type ARModeManager struct {
    cli        *CLI
    arEngine   *AREngine
    mode       ARMode
}

// Switch to AR mode
func (arm *ARModeManager) SwitchToARMode(mode ARMode) error {
    // Update mode
    arm.mode = mode
    
    // Notify AR engine
    err := arm.arEngine.SetMode(mode)
    if err != nil {
        return err
    }
    
    // Update CLI display
    arm.cli.SetDisplayMode("ar")
    
    return nil
}

// AR modes
type ARMode string

const (
    ARModeASCIIOverlay    ARMode = "ascii_overlay"
    ARModePDFGhost        ARMode = "pdf_ghost"
    ARModeLiDARMesh       ARMode = "lidar_mesh"
    ARModeHybrid          ARMode = "hybrid"
)
```

## 🔧 **Configuration Management**

### **CLI Configuration**

```yaml
# CLI configuration file
cli:
  # Default settings
  default_building: "building-47"
  default_format: "table"
  max_history: 1000
  
  # Display settings
  display:
    colors: true
    unicode: true
    max_width: 120
    show_progress: true
    
  # Navigation settings
  navigation:
    auto_complete: true
    fuzzy_search: true
    case_sensitive: false
    
  # Output settings
  output:
    default_format: "table"
    show_timestamps: true
    show_confidence: true
    
  # Performance settings
  performance:
    cache_size: 1000
    cache_ttl: "5m"
    max_concurrent: 10
```

### **Building Configuration**

```yaml
# Building configuration
building:
  id: "building-47"
  name: "HCPS Administration Building"
  campus: "east-region"
  coordinates: [27.9506, -82.2373]
  
  # System definitions
  systems:
    electrical:
      main_panel:
        capacity: 400A
        circuits:
          - id: "circuit-1"
            breaker: 20A
            loads:
              - outlets: [1-8]
              - lights: [1-4]
            constraints:
              - "load < 16A"  # 80% rule
              
    hvac:
      ahu_1:
        supply_temp: 55F
        schedules:
          occupied: "07:00-18:00"
          unoccupied_setback: 10F
        optimization:
          mode: "efficiency"
          constraints:
            - comfort_priority: 0.7
            - energy_priority: 0.3
```

## 📊 **Performance and Scalability**

### **Performance Targets**

| Operation | Target | Architecture |
|-----------|--------|--------------|
| Command Response | <100ms | Optimized execution |
| Path Resolution | <10ms | Spatial indexing |
| Object Inspection | <50ms | Cached results |
| Search Operations | <200ms | Indexed queries |
| Real-time Updates | <100ms | WebSocket streaming |

### **Caching Strategy**

```go
// Multi-level caching system
type CacheManager struct {
    l1Cache *LRUCache      // In-memory cache
    l2Cache *RedisCache    // Redis cache
    l3Cache *DatabaseCache // Database cache
}

// Get cached value
func (cm *CacheManager) Get(key string) (interface{}, error) {
    // Try L1 cache first
    if value := cm.l1Cache.Get(key); value != nil {
        return value, nil
    }
    
    // Try L2 cache
    if value := cm.l2Cache.Get(key); value != nil {
        // Populate L1 cache
        cm.l1Cache.Set(key, value)
        return value, nil
    }
    
    // Try L3 cache
    if value := cm.l3Cache.Get(key); value != nil {
        // Populate L1 and L2 caches
        cm.l1Cache.Set(key, value)
        cm.l2Cache.Set(key, value)
        return value, nil
    }
    
    return nil, fmt.Errorf("key not found: %s", key)
}
```

## 📚 **Best Practices**

### **Command Design**
1. **Follow Unix conventions** for familiar user experience
2. **Use consistent naming** across related commands
3. **Provide helpful examples** in command help
4. **Implement proper error handling** with user-friendly messages
5. **Support both interactive and scripted** usage

### **Performance Optimization**
1. **Use efficient data structures** for large buildings
2. **Implement intelligent caching** for frequently accessed data
3. **Optimize path resolution** with spatial indexing
4. **Batch operations** when possible
5. **Use async operations** for long-running tasks

### **User Experience**
1. **Provide clear feedback** for all operations
2. **Support auto-completion** for paths and commands
3. **Show progress indicators** for long operations
4. **Implement undo/redo** where appropriate
5. **Support multiple output formats** (table, JSON, YAML)

---

**The Arxos CLI transforms building management into a powerful, intuitive command-line experience.** 🏗️💻
