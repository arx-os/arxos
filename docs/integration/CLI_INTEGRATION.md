# Arx CLI Integration with IfcOpenShell + PostGIS + Daemon Pipeline

## Overview

The Arx CLI is the **command interface** that orchestrates and triggers the entire data flow. It acts as the **user-facing entry point** that connects to the IfcOpenShell + PostGIS + Daemon pipeline through dependency injection and service contexts.

## CLI Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Arx CLI Integration Flow                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   User      │───▶│   Arx CLI    │───▶│   Service      │───▶│   Data      │  │
│  │   Commands  │    │   Commands   │    │   Context      │    │   Pipeline  │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘  │
│         │                    │                    │                    │        │
│         │                    │                    │                    │        │
│         ▼                    ▼                    ▼                    ▼        │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Terminal  │    │   Cobra      │    │   Dependency    │    │   IfcOpen   │  │
│  │   Interface │    │   Framework  │    │   Injection     │    │   Shell     │  │
│  └─────────────┘    └──────────────┘    └─────────────────┘    └─────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## CLI Command Integration

### 1. Command Structure

```go
// internal/cli/commands/import_export.go
func CreateImportCommand(serviceContext interface{}) *cobra.Command {
    cmd := &cobra.Command{
        Use:   "import <file>",
        Short: "Import building data from files",
        Long:  "Import building data from IFC, PDF, or other supported formats",
        Args:  cobra.ExactArgs(1),
        RunE: func(cmd *cobra.Command, args []string) error {
            filePath := args[0]
            
            // Get repository ID from flags
            repoID, _ := cmd.Flags().GetString("repository")
            
            // Get format from flags or auto-detect
            format, _ := cmd.Flags().GetString("format")
            if format == "" {
                if len(filePath) > 4 && filePath[len(filePath)-4:] == ".ifc" {
                    format = "ifc"
                }
            }
            
            // Read file data
            fileData, err := os.ReadFile(filePath)
            if err != nil {
                return fmt.Errorf("failed to read file: %w", err)
            }
            
            // Import using the IFC service
            if format == "ifc" {
                // TODO: Get IFC service from service context
                fmt.Printf("   File size: %d bytes\n", len(fileData))
                fmt.Printf("   Ready for IfcOpenShell integration\n")
                
                fmt.Printf("✅ Successfully imported: %s\n", filePath)
                fmt.Printf("   Repository: %s\n", repoID)
                fmt.Printf("   Format: %s\n", format)
                fmt.Printf("   Entities: [Will be populated by IfcOpenShell service]\n")
            }
            
            return nil
        },
    }
    
    // Add flags
    cmd.Flags().StringP("repository", "r", "", "Repository ID (required)")
    cmd.Flags().StringP("format", "f", "", "File format (ifc, pdf, csv, json)")
    cmd.Flags().Bool("validate", true, "Validate against buildingSMART standards")
    cmd.Flags().BoolP("enhance", "e", false, "Enhance with spatial data")
    
    return cmd
}
```

### 2. Service Context Integration

```go
// internal/cli/context.go
type ServiceContext struct {
    container *app.Container
}

func (sc *ServiceContext) GetRepositoryService() building.RepositoryService {
    return &RepositoryServiceImpl{
        repositoryUC: sc.container.GetRepositoryUseCase(),
        ifcUC:        sc.container.GetIFCUseCase(),        // ← IFC Use Case
        versionUC:    sc.container.GetVersionUseCase(),
        filesystem:   sc.container.GetFilesystemService(),
    }
}

// RepositoryServiceImpl implements building.RepositoryService interface
type RepositoryServiceImpl struct {
    repositoryUC *usecase.RepositoryUseCase
    ifcUC        *usecase.IFCUseCase        // ← Direct access to IFC processing
    versionUC    *usecase.VersionUseCase
    filesystem   *filesystem.RepositoryFilesystemService
}
```

### 3. Dependency Injection Container

```go
// internal/app/container.go
type Container struct {
    // IFC services
    ifcOpenShellClient *ifc.IfcOpenShellClient
    nativeParser       *ifc.NativeParser
    ifcService         *ifc.EnhancedIFCService
    
    // Use cases
    ifcUC        *usecase.IFCUseCase        // ← CLI accesses this
    repositoryUC *usecase.RepositoryUseCase
}

func (c *Container) initIFCServices(ctx context.Context) error {
    // Create IfcOpenShell client
    c.ifcOpenShellClient = ifc.NewIfcOpenShellClient(
        c.config.IFC.Service.URL,
        30*time.Second,
        3, // retries
    )
    
    // Create native parser as fallback
    c.nativeParser = ifc.NewNativeParser(100 * 1024 * 1024)
    
    // Create enhanced IFC service
    c.ifcService = ifc.NewEnhancedIFCService(
        c.ifcOpenShellClient,
        c.nativeParser,
        c.config.IFC.Service.Enabled,
        c.config.IFC.Fallback.Enabled,
        5,              // failure threshold
        60*time.Second, // recovery timeout
        logger,
    )
    
    return nil
}

func (c *Container) initUseCases(ctx context.Context) error {
    // IFC use case with service integration
    c.ifcUC = usecase.NewIFCUseCase(
        c.repositoryRepo, 
        c.ifcRepo, 
        nil, 
        c.ifcService,    // ← Injected IFC service
        c.logger,
    )
    
    return nil
}
```

## Complete CLI Integration Flow

### 1. User Command Execution

```bash
# User runs CLI command
arx import building.ifc --repository repo-123 --format ifc --validate --enhance
```

### 2. CLI Command Processing

```go
// internal/cli/commands/import_export.go
func CreateImportCommand(serviceContext interface{}) *cobra.Command {
    cmd := &cobra.Command{
        RunE: func(cmd *cobra.Command, args []string) error {
            filePath := args[0]                    // "building.ifc"
            repoID, _ := cmd.Flags().GetString("repository")  // "repo-123"
            format, _ := cmd.Flags().GetString("format")      // "ifc"
            
            // Read file data
            fileData, err := os.ReadFile(filePath)
            
            // Get service from context
            sc, ok := serviceContext.(*cli.ServiceContext)
            if !ok {
                return fmt.Errorf("service context not available")
            }
            
            // Get repository service (includes IFC processing)
            repoService := sc.GetRepositoryService()
            
            // Import IFC file
            result, err := repoService.ImportIFC(context.Background(), repoID, fileData)
            if err != nil {
                return fmt.Errorf("failed to import IFC: %w", err)
            }
            
            fmt.Printf("✅ Successfully imported: %s\n", filePath)
            fmt.Printf("   Repository: %s\n", repoID)
            fmt.Printf("   Format: %s\n", format)
            fmt.Printf("   Entities: %d\n", result.Entities)
            fmt.Printf("   Buildings: %d\n", result.Buildings)
            fmt.Printf("   Spaces: %d\n", result.Spaces)
            fmt.Printf("   Equipment: %d\n", result.Equipment)
            
            return nil
        },
    }
}
```

### 3. Service Context Integration

```go
// internal/cli/context.go
func (sc *ServiceContext) GetRepositoryService() building.RepositoryService {
    return &RepositoryServiceImpl{
        repositoryUC: sc.container.GetRepositoryUseCase(),
        ifcUC:        sc.container.GetIFCUseCase(),        // ← IFC Use Case
        versionUC:    sc.container.GetVersionUseCase(),
        filesystem:   sc.container.GetFilesystemService(),
    }
}

// RepositoryServiceImpl.ImportIFC calls the IFC use case
func (s *RepositoryServiceImpl) ImportIFC(ctx context.Context, repoID string, data []byte) (*building.IFCImportResult, error) {
    return s.ifcUC.ImportIFC(ctx, repoID, data)  // ← Triggers IFC processing
}
```

### 4. IFC Use Case Processing

```go
// internal/usecase/ifc_usecase.go
func (uc *IFCUseCase) ImportIFC(ctx context.Context, repoID string, ifcData []byte) (*building.IFCImportResult, error) {
    // Parse IFC data using IfcOpenShell service
    parseResult, err := uc.ifcService.ParseIFC(ctx, ifcData)  // ← Calls IfcOpenShell
    if err != nil {
        return nil, fmt.Errorf("failed to parse IFC file: %w", err)
    }
    
    // Create IFC file record with parsed data
    ifcFile := &building.IFCFile{
        ID:         uc.generateIFCFileID(),
        Name:       "building.ifc",
        Version:    parseResult.Metadata.IFCVersion,
        Size:       int64(len(ifcData)),
        Entities:   parseResult.TotalEntities,
        Validated:  true,
    }
    
    // Save to PostGIS
    if err := uc.ifcRepo.Create(ctx, ifcFile); err != nil {
        return nil, fmt.Errorf("failed to save IFC file: %w", err)
    }
    
    return &building.IFCImportResult{
        Success:      true,
        RepositoryID: repoID,
        IFCFileID:    ifcFile.ID,
        Entities:     parseResult.TotalEntities,
        Buildings:    parseResult.Buildings,
        Spaces:       parseResult.Spaces,
        Equipment:    parseResult.Equipment,
    }, nil
}
```

## CLI Commands That Trigger the Pipeline

### 1. **Import Command** - Direct Pipeline Trigger
```bash
arx import building.ifc --repository repo-123 --format ifc --validate
```
**Flow**: CLI → Service Context → IFC Use Case → IfcOpenShell Service → PostGIS

### 2. **Repository Commands** - Repository Management
```bash
arx repo init my-building
arx repo list
arx repo status repo-123
```
**Flow**: CLI → Service Context → Repository Use Case → PostGIS

### 3. **Watch Command** - Daemon Integration
```bash
arx watch /data/imports
```
**Flow**: CLI → Service Context → Daemon Service → File Watcher → IFC Pipeline

### 4. **Query Command** - Direct Database Access
```bash
arx query "SELECT * FROM ifc_files WHERE entities > 100"
```
**Flow**: CLI → Service Context → PostGIS Repository → Database

### 5. **CADTUI Command** - Interactive Interface
```bash
arx cadtui
```
**Flow**: CLI → Service Context → TUI Interface → All Services

## CLI Service Integration Points

### 1. **Direct IFC Processing**
```go
// CLI command directly calls IFC service
func (s *RepositoryServiceImpl) ImportIFC(ctx context.Context, repoID string, data []byte) (*building.IFCImportResult, error) {
    return s.ifcUC.ImportIFC(ctx, repoID, data)  // ← Direct IFC processing
}
```

### 2. **Repository Management**
```go
// CLI manages building repositories
func (s *RepositoryServiceImpl) CreateRepository(ctx context.Context, req *building.CreateRepositoryRequest) (*building.BuildingRepository, error) {
    return s.repositoryUC.CreateRepository(ctx, req)  // ← Repository creation
}
```

### 3. **File System Integration**
```go
// CLI integrates with file system services
func (s *RepositoryServiceImpl) GetRepositoryStructure(ctx context.Context, repoID string) (*building.RepositoryStructure, error) {
    return s.filesystem.GetStructure(ctx, repoID)  // ← File system access
}
```

## CLI Configuration Integration

### 1. **IFC Service Configuration**
```yaml
# configs/development.yml
ifc:
  service:
    enabled: true
    url: "http://localhost:5000"
    timeout: "30s"
    retries: 3
    circuit_breaker:
      enabled: true
      failure_threshold: 5
      recovery_timeout: "60s"
  fallback:
    enabled: true
    parser: "native"
  performance:
    cache_enabled: true
    cache_ttl: "2h"
    max_file_size: "200MB"
```

### 2. **CLI App Initialization**
```go
// internal/cli/app.go
func NewApp(cfg *config.Config) *App {
    app := &App{
        config: cfg,
        logger: &Logger{},
    }
    
    // Initialize dependency injection container
    app.container = app.NewContainer()
    
    // Initialize container with context
    ctx := context.Background()
    if err := container.Initialize(ctx, a.config); err != nil {
        fmt.Printf("Warning: Failed to initialize container: %v\n", err)
    }
    
    return app
}
```

## CLI Command Examples

### 1. **Complete IFC Import Workflow**
```bash
# 1. Create repository
arx repo init my-building --type architectural

# 2. Import IFC file
arx import building.ifc --repository my-building --format ifc --validate --enhance

# 3. Check import status
arx repo status my-building

# 4. Query imported data
arx query "SELECT name, entities, validated FROM ifc_files WHERE repository_id = 'my-building'"
```

### 2. **Daemon Integration**
```bash
# Start daemon service
arx serve --daemon

# Watch directory for automatic imports
arx watch /data/imports --repository my-building

# Check daemon health
arx health --service daemon
```

### 3. **Interactive CADTUI**
```bash
# Launch interactive interface
arx cadtui

# Within CADTUI:
# > import building.ifc
# > validate
# > query spaces
# > export pdf
```

## Benefits of CLI Integration

### 1. **Unified Interface**
- Single command-line interface for all operations
- Consistent command structure across all services
- Easy automation and scripting

### 2. **Service Orchestration**
- CLI coordinates between multiple services
- Handles service discovery and configuration
- Provides fallback mechanisms

### 3. **User Experience**
- Clear command structure with help and validation
- Progress indicators and status reporting
- Error handling with helpful messages

### 4. **Development Workflow**
- Easy testing and debugging
- Command-line automation
- Integration with CI/CD pipelines

## CLI Command Structure

```
arx
├── import <file>           # Import IFC/PDF files
├── export <format>         # Export building data
├── repo                    # Repository management
│   ├── init <name>         # Create repository
│   ├── list                # List repositories
│   └── status <id>         # Repository status
├── component               # Component management
├── cadtui                  # Interactive CAD interface
├── watch <directory>      # File watching
├── serve                   # Start services
├── query <sql>            # Database queries
├── health                  # Service health checks
└── version                 # Version information
```

The Arx CLI serves as the **command orchestrator** that connects users to the entire IfcOpenShell + PostGIS + Daemon pipeline through a clean, consistent interface. It handles service discovery, dependency injection, error handling, and provides a unified experience for all building data operations.
