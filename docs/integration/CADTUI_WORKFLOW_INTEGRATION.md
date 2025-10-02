# CADTUI Integration with Complete Data Workflow

## CADTUI as Visual Interface Layer

The CADTUI sits as a **visual interface layer** on top of the entire IfcOpenShell + PostGIS + Daemon + CLI workflow, providing real-time visual context and interactive control.

## Complete Data Flow with CADTUI

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ArxOS Complete Data Flow with CADTUI                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   User      │───▶│   CADTUI     │───▶│   CLI Commands  │───▶│   Service   │  │
│  │   Interface │    │   (Visual)   │    │   (Commands)    │    │   Context   │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘  │
│         │                    │                    │                    │        │
│         │                    │                    │                    │        │
│         ▼                    ▼                    ▼                    ▼        │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Visual    │    │   Real-time  │    │   IFC Service   │    │   PostGIS   │  │
│  │   Context   │    │   Rendering  │    │   (Processing)  │    │  Database   │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘  │
│         │                    │                    │                    │        │
│         │                    │                    │                    │        │
│         ▼                    ▼                    ▼                    ▼        │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Spatial   │    │   Component  │    │   IfcOpenShell  │    │   Spatial   │  │
│  │   Queries   │    │   Selection  │    │   Service       │    │   Storage   │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 1. CADTUI Data Consumption

### A. Real-Time Data Access
```go
// internal/tui/services/data_service.go
type DataService struct {
    db domain.Database  // ← Direct access to PostGIS
}

func (ds *DataService) GetBuildingData(ctx context.Context, buildingID string) (*BuildingData, error) {
    // Query PostGIS for spatial data
    spatialData, err := ds.getSpatialData(ctx, buildingID)
    if err != nil {
        return nil, fmt.Errorf("failed to get spatial data: %w", err)
    }
    
    // Query equipment data
    equipment, err := ds.getEquipmentData(ctx, buildingID)
    if err != nil {
        return nil, fmt.Errorf("failed to get equipment data: %w", err)
    }
    
    // Query IFC file data
    ifcFiles, err := ds.getIFCFileData(ctx, buildingID)
    if err != nil {
        return nil, fmt.Errorf("failed to get IFC file data: %w", err)
    }
    
    return &BuildingData{
        Building:  spatialData.Building,
        Floors:    spatialData.Floors,
        Equipment: equipment,
        Alerts:    ds.getAlerts(ctx, buildingID),
        Metrics:   ds.getMetrics(ctx, buildingID),
    }, nil
}
```

### B. Spatial Data Integration
```go
// internal/tui/services/postgis_client.go
func (pc *PostGISClient) GetBuildingSpatialData(ctx context.Context, buildingID string) (*BuildingSpatialData, error) {
    // Query building spatial reference
    spatialRef, err := pc.getBuildingSpatialRef(ctx, buildingID)
    
    // Query equipment positions
    equipmentPositions, err := pc.getEquipmentPositions(ctx, buildingID)
    
    // Query scanned regions for coverage
    scannedRegions, err := pc.getScannedRegions(ctx, buildingID)
    
    return &BuildingSpatialData{
        BuildingID:         buildingID,
        SpatialRef:         spatialRef,
        EquipmentPositions: equipmentPositions,
        ScannedRegions:     scannedRegions,
        LastUpdate:         time.Now(),
    }, nil
}
```

## 2. CADTUI Command Integration

### A. CADTUI Commands Trigger Full Pipeline
```bash
# CADTUI commands that trigger the complete workflow
CADTUI> import data/ifc/hospital.ifc --visual
# ↓ Triggers: CLI → Service Context → IFC Use Case → IfcOpenShell → PostGIS

CADTUI> select space-001
# ↓ Triggers: PostGIS spatial query → Visual rendering

CADTUI> name "OR-301" --confirm
# ↓ Triggers: Update PostGIS → Refresh visual display

CADTUI> connect space-001 equipment-001 supplies
# ↓ Triggers: PostGIS relationship update → Visual connection rendering
```

### B. Real-Time Visual Updates
```go
// internal/interfaces/tui/cadtui.go
func (tui *CADTUI) Render(ctx context.Context) error {
    // Get current scene from PostGIS
    scene, err := tui.designInterface.RenderScene(ctx, component.ComponentFilter{
        Limit: 100,
    })
    if err != nil {
        return fmt.Errorf("failed to render scene: %w", err)
    }
    tui.scene = scene
    
    // Render visual representation
    tui.renderViewport()
    
    return nil
}

func (tui *CADTUI) renderViewport() {
    // Create visual grid from PostGIS spatial data
    grid := make([][]string, tui.viewport.Height)
    
    // Place components from PostGIS data
    for _, comp := range tui.scene.Components {
        x := comp.Position.X
        y := comp.Position.Y
        
        if x >= 0 && x < tui.viewport.Width && y >= 0 && y < tui.viewport.Height {
            // Highlight selected component
            if tui.selectedComponent != nil && comp.ComponentID == *tui.selectedComponent {
                grid[y][x] = fmt.Sprintf("\033[1;33m%s\033[0m", comp.Symbol)
            } else {
                grid[y][x] = comp.Symbol
            }
        }
    }
    
    // Render the visual grid
    for _, row := range grid {
        fmt.Println(strings.Join(row, ""))
    }
}
```

## 3. Complete Workflow Integration

### A. Import Workflow with Visual Feedback
```bash
# 1. User imports IFC file through CADTUI
CADTUI> import data/ifc/hospital.ifc --visual

# 2. CADTUI triggers CLI command
# Internal: CADTUI → CLI Command → Service Context → IFC Use Case

# 3. IFC Use Case processes through IfcOpenShell
# Internal: IFC Use Case → IfcOpenShell Client → Python Service → IfcOpenShell Library

# 4. Results stored in PostGIS
# Internal: IFC Use Case → PostGIS Repository → Spatial Indexing

# 5. CADTUI queries PostGIS for visual rendering
# Internal: CADTUI → Data Service → PostGIS Client → Spatial Queries

# 6. Visual display updated
CADTUI> # Shows visual representation of imported building
```

### B. Real-Time Naming with Visual Context
```bash
# 1. User selects component visually
CADTUI> select space-001
# ↓ CADTUI queries PostGIS for component data
# ↓ Visual selection with context displayed

# 2. User names component with visual confirmation
CADTUI> name "OR-301" --confirm
# ↓ Updates PostGIS database
# ↓ Refreshes visual display
# ↓ Shows updated naming in context

# 3. User sees immediate visual feedback
CADTUI> # Component now shows "OR-301" in visual grid
```

## 4. Data Flow Architecture

### A. CADTUI Data Sources
```go
// CADTUI consumes data from multiple sources
type CADTUIDataSources struct {
    // PostGIS spatial data
    spatialData *PostGISClient
    
    // IFC processing results
    ifcData *IFCService
    
    // Real-time updates
    realTimeUpdates *DaemonService
    
    // User interactions
    userInput *CLICommands
}
```

### B. Real-Time Data Synchronization
```go
// CADTUI maintains real-time sync with PostGIS
func (tui *CADTUI) syncWithDatabase(ctx context.Context) error {
    // Query PostGIS for latest data
    latestData, err := tui.dataService.GetBuildingData(ctx, tui.buildingID)
    if err != nil {
        return fmt.Errorf("failed to sync with database: %w", err)
    }
    
    // Update visual representation
    tui.updateVisualRepresentation(latestData)
    
    // Refresh viewport
    return tui.Render(ctx)
}
```

## 5. CADTUI Command Mapping

### A. CADTUI Commands → Pipeline Actions
```bash
# Import commands
CADTUI> import <file> --visual
# → CLI import command → IFC processing → PostGIS storage → Visual rendering

# Selection commands  
CADTUI> select <component-id>
# → PostGIS spatial query → Visual highlighting

# Naming commands
CADTUI> name <new-name> --confirm
# → PostGIS update → Visual refresh

# Connection commands
CADTUI> connect <source> <target> <relation>
# → PostGIS relationship update → Visual connection rendering

# Query commands
CADTUI> query <spatial-query>
# → PostGIS spatial query → Visual results display
```

### B. Visual Feedback Loop
```go
// CADTUI provides continuous visual feedback
func (tui *CADTUI) handleUserAction(ctx context.Context, action UserAction) error {
    // Execute action through pipeline
    result, err := tui.executeAction(ctx, action)
    if err != nil {
        return err
    }
    
    // Update PostGIS if needed
    if action.UpdatesDatabase {
        err = tui.updateDatabase(ctx, result)
        if err != nil {
            return err
        }
    }
    
    // Refresh visual display
    return tui.Render(ctx)
}
```

## 6. Benefits of CADTUI Integration

### **🔄 Real-Time Synchronization**
- **Live Updates**: CADTUI reflects changes immediately
- **Data Consistency**: Single source of truth in PostGIS
- **Visual Confirmation**: Users see results instantly

### **🎯 Contextual Operations**
- **Visual Selection**: Users see what they're working with
- **Spatial Awareness**: Understanding of component relationships
- **Interactive Naming**: Visual context for naming decisions

### **⚡ Efficient Workflow**
- **Single Interface**: All operations through CADTUI
- **Pipeline Integration**: Seamless data flow
- **Real-Time Feedback**: Immediate visual confirmation

### **🛡️ Data Integrity**
- **PostGIS Backend**: Reliable spatial data storage
- **Transaction Safety**: Database consistency maintained
- **Audit Trail**: Complete operation history

## 7. CADTUI as Workflow Orchestrator

The CADTUI serves as the **visual orchestrator** of the entire workflow:

1. **User Interface**: Provides visual context for all operations
2. **Command Router**: Routes commands to appropriate services
3. **Data Consumer**: Consumes data from PostGIS for visualization
4. **Real-Time Sync**: Maintains synchronization with database
5. **Visual Feedback**: Provides immediate visual confirmation

The CADTUI transforms the entire IfcOpenShell + PostGIS + Daemon + CLI workflow into a **visual, interactive experience** where users can see, select, name, and manipulate building components with full spatial context and real-time feedback.
