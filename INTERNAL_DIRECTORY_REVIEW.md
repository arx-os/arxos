# /internal Directory - Deep Review
**Systematic Analysis Against ArxOS Vision**

**Date**: October 9, 2025
**Scope**: Complete /internal directory tree
**Method**: File-by-file analysis with code inspection

---

## Overview

The `/internal` directory contains the core ArxOS application following Clean Architecture principles. This review examines each subdirectory in detail.

**Subdirectories**:
- `/app` - Dependency injection container
- `/build` - Build metrics and performance
- `/cli` - Command-line interface
- `/config` - Configuration management
- `/domain` - Domain models and business rules
- `/infrastructure` - External concerns (database, cache, IFC, etc.)
- `/interfaces` - API layers (HTTP, GraphQL, WebSocket, TUI)
- `/migrations` - Database schema evolution
- `/tui` - Terminal user interface
- `/usecase` - Business logic layer

---

# Part 1: `/internal/app` - Dependency Injection Container

## Directory Structure

```
/internal/app/
├── container.go       (502 lines) - Main DI container
├── container_test.go  - Container unit tests
└── l2/                - L2 cache subdirectory
```

## Detailed Analysis

### `container.go` (502 lines) - COMPREHENSIVE REVIEW

**Purpose**: Dependency injection container following Go Blueprint and Clean Architecture

**What It Does**:

#### 1. Infrastructure Layer Initialization
```go
Lines 136-174: initInfrastructure()
- ✅ Logger (first, needed by others)
- ✅ Database connection
- ✅ PostGIS connection with config
- ✅ Unified cache (L1/L2/L3)
```

**Status**: ✅ **COMPLETE** - All infrastructure properly initialized

#### 2. Repository Layer Initialization
```go
Lines 176-206: initRepositories()
- ✅ UserRepository (PostGIS)
- ✅ BuildingRepository (PostGIS)
- ✅ EquipmentRepository (PostGIS)
- ✅ OrganizationRepository (PostGIS)
- ✅ RepositoryRepository (version control)
- ✅ VersionRepository (version control)
- ✅ IFCRepository (IFC files)
- ✅ ComponentRepository (components)
- ✅ SpatialRepository (AR, point clouds)
```

**Status**: ✅ **COMPLETE** - All repositories registered

**Gap**: ❌ Missing repositories:
- FloorRepository (not in container)
- **RoomRepository** (not in container) ← CRITICAL
- NetworkDeviceRepository (Meraki - future)
- ARNavigationSessionRepository (Meraki - future)

#### 3. Infrastructure Services Initialization
```go
Lines 209-244: initInfrastructureServices()
- ✅ DataManager (filesystem paths)
- ✅ RepositoryFilesystemService
- ✅ JWTManager (authentication)
- ✅ IFC services (OpenShell client, native parser, enhanced service)
```

**Status**: ✅ **EXCELLENT** - All services properly initialized

**IFC Service Configuration** (Lines 246-271):
```go
✅ IfcOpenShellClient with retry logic
✅ NativeParser fallback
✅ EnhancedIFCService with circuit breaker
✅ Uses config.IFC.Service.Enabled flag
✅ Uses config.IFC.Fallback.Enabled flag
```

**Finding**: IFC service **IS** configurable! Can be disabled via config.

#### 4. Use Case Layer Initialization
```go
Lines 273-299: initUseCases()
- ✅ UserUseCase
- ✅ BuildingUseCase
- ✅ EquipmentUseCase
- ✅ OrganizationUseCase
- ✅ RepositoryUseCase (version control)
- ✅ IFCUseCase
- ✅ VersionUseCase
- ✅ ComponentUseCase
- ✅ DesignUseCase
```

**Status**: ✅ **GOOD** - Core use cases registered

**Gap**: ❌ Missing use cases:
- **RoomUseCase** ← CRITICAL
- AnalyticsUseCase (exists in /usecase but not in container)
- AuthUseCase (exists in /usecase but not in container)
- BuildingOpsUseCase (exists in /usecase but not in container)

#### 5. Interface Layer Initialization
```go
Lines 301-327: initInterfaces()
- ✅ BaseHandler (authentication & logging)
- ✅ APIHandler
- ✅ BuildingHandler
- ✅ AuthHandler
```

**Status**: ⚠️ **PARTIAL** - Only core handlers initialized

**Gap**: ❌ Missing handlers in container:
- EquipmentHandler (exists in /handlers but not registered)
- SpatialHandler (exists in /handlers but not registered)
- MobileHandler (exists in /handlers but not registered)
- OrganizationHandler (exists in /handlers but not registered)
- UserHandler (exists in /handlers but not registered)
- **RoomHandler** (doesn't exist yet)
- IFCHandler (exists but not registered)
- ComponentHandler (exists but not registered)

#### 6. Getter Methods (Lines 329-465)

**Available Getters**:
- ✅ GetConfig, GetDatabase, GetPostGIS, GetCache, GetLogger
- ✅ GetAPIHandler, GetBuildingHandler, GetAuthHandler
- ✅ GetUserUseCase, GetBuildingUseCase, GetEquipmentUseCase
- ✅ GetOrganizationUseCase, GetSpatialRepository
- ✅ GetRepositoryUseCase, GetIFCUseCase, GetVersionUseCase
- ✅ GetIfcOpenShellClient, GetNativeParser, GetIFCService
- ✅ GetComponentUseCase, GetDesignUseCase
- ✅ GetFilesystemService, GetDataManager

**Finding**: Container has 25+ getter methods - very comprehensive!

### Vision Alignment

| Requirement | Implemented | In Container | Status |
|-------------|-------------|--------------|--------|
| PostGIS connection | ✅ | ✅ | **COMPLETE** |
| Multi-tier cache | ✅ | ✅ | **COMPLETE** |
| IFC service | ✅ | ✅ | **COMPLETE** |
| IFC optional config | ✅ | ✅ | **COMPLETE** |
| Room repository | ✅ (exists in /postgis) | ❌ | **NOT REGISTERED** |
| Room use case | ❌ | ❌ | **MISSING** |
| Floor repository | ✅ (exists in /postgis) | ❌ | **NOT REGISTERED** |
| All HTTP handlers | ✅ (exist) | ⚠️ (partial) | **INCOMPLETE** |

### Critical Findings

#### 🟢 **EXCELLENT**:
1. Clean architecture properly implemented
2. IFC service **IS** optional via config
3. Circuit breaker pattern for IFC service
4. Proper initialization order (infra → repos → use cases → interfaces)
5. Thread-safe with mutex locks
6. Graceful shutdown

#### 🟡 **GOOD BUT INCOMPLETE**:
1. FloorRepository and RoomRepository exist but not registered in container
2. Most HTTP handlers exist but only 2 registered (Building, Auth)
3. Some use cases exist but not in container (Analytics, Auth, BuildingOps)

#### 🔴 **CRITICAL GAPS**:
1. **RoomRepository not registered** - Exists in `/postgis/room_repo.go` but not in container!
2. **FloorRepository not registered** - Exists in `/postgis/floor_repo.go` but not in container!
3. **RoomUseCase doesn't exist** - Need to create
4. **Most handlers not registered** - They exist but not wired up

### Development Tasks for `/internal/app`

#### Task APP-1: Register Missing Repositories (Priority: CRITICAL)
**Effort**: 1 hour
**File**: `internal/app/container.go`

**Add to struct** (after line 43):
```go
floorRepo    domain.FloorRepository
roomRepo     domain.RoomRepository
```

**Add to initRepositories()** (after line 191):
```go
// Floor repository - PostGIS implementation
c.floorRepo = postgis.NewFloorRepository(db)

// Room repository - PostGIS implementation
c.roomRepo = postgis.NewRoomRepository(db)
```

**Add getters** (after line 408):
```go
func (c *Container) GetFloorRepository() domain.FloorRepository {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.floorRepo
}

func (c *Container) GetRoomRepository() domain.RoomRepository {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.roomRepo
}
```

**Impact**: This alone will enable floor and room commands to work!

#### Task APP-2: Register Missing Use Cases (Priority: HIGH)
**Effort**: 2 hours
**File**: `internal/app/container.go`

**Add to struct** (after line 66):
```go
analyticsUC    *usecase.AnalyticsUseCase
authUC         *usecase.AuthUseCase
buildingOpsUC  *usecase.BuildingOpsUseCase
roomUC         *usecase.RoomUseCase  // After creating it
```

**Add to initUseCases()** (after line 297):
```go
// Analytics use case
c.analyticsUC = usecase.NewAnalyticsUseCase(c.buildingRepo, c.equipmentRepo, c.logger)

// Auth use case
c.authUC = usecase.NewAuthUseCase(c.userRepo, c.jwtManager, c.logger)

// Building ops use case
c.buildingOpsUC = usecase.NewBuildingOpsUseCase(c.buildingRepo, c.equipmentRepo, c.logger)

// Room use case (after creating it)
c.roomUC = usecase.NewRoomUseCase(c.roomRepo, c.floorRepo, c.logger)
```

**Add getters**: Similar pattern as above

#### Task APP-3: Register All HTTP Handlers (Priority: HIGH)
**Effort**: 3 hours
**File**: `internal/app/container.go`

**Add to struct** (after line 84):
```go
equipmentHandler    *handlers.EquipmentHandler
floorHandler        *handlers.FloorHandler
roomHandler         *handlers.RoomHandler
spatialHandler      *handlers.SpatialHandler
mobileHandler       *handlers.MobileHandler
organizationHandler *handlers.OrganizationHandler
userHandler         *handlers.UserHandler
ifcHandler          *handlers.IFCHandler
componentHandler    *handlers.ComponentHandler
healthHandler       *handlers.HealthHandler
jobHandler          *handlers.JobHandler
bulkHandler         *handlers.BulkHandler
```

**Add to initInterfaces()**: Initialize each handler with dependencies

**Benefits**: Full API will be available once handlers are registered

#### Task APP-4: Add Meraki Integration Support (Priority: MEDIUM - Future)
**Effort**: 1 day
**File**: `internal/app/container.go`

**When Meraki is implemented, add**:
```go
// Meraki integration
merakiClient       *meraki.Client
merakiIntegration  *meraki.Integration
networkDeviceRepo  domain.NetworkDeviceRepository
arNavSessionRepo   domain.ARNavigationSessionRepository

// Meraki use cases
findDeviceUC       *usecase.FindDeviceUseCase
pushARNavUC        *usecase.PushARNavigationUseCase
syncMerakiUC       *usecase.SyncMerakiUseCase
```

### Summary for `/internal/app`

**Overall Status**: 🟡 **85% Complete**

**Strengths**:
- ✅ Excellent clean architecture implementation
- ✅ Proper dependency injection
- ✅ Thread-safe with mutexes
- ✅ IFC service properly configured with optional flag
- ✅ All core infrastructure initialized

**Critical Issues**:
- 🔴 FloorRepository and RoomRepository not registered (they exist!)
- 🔴 Only 2 HTTP handlers registered (12+ exist but not wired up)
- 🔴 Several use cases exist but not in container

**Impact**: This is a **quick win** - just registering existing code will unlock features!

**Estimated Fix Time**: 1 day to register all existing repos/use cases/handlers

---

# Part 2: `/internal/domain` - Domain Models


## Directory Structure

```
/internal/domain/
├── entities.go (276 lines) - Core domain entities
├── interfaces.go (179 lines) - Repository & service interfaces
├── errors.go (505 lines) - Domain errors
├── spatial.go (192 lines) - Spatial domain types
├── spatial_types.go (233 lines) - AR & spatial structures
├── spatial_validation.go (466 lines) - Spatial validation logic
├── types/
│   └── id.go (146 lines) - ID type system
├── validation/
│   └── id_validator.go (146 lines) - ID validation
├── building/
│   ├── repository.go (183 lines) - Building repository model
│   ├── version.go - Version control
│   ├── diff.go (437 lines) - Change tracking
│   ├── object.go (195 lines) - Object model
│   ├── ifc.go (170 lines) - IFC structures
│   ├── validator.go - Validation rules
│   └── service.go - Service interfaces
├── component/
│   ├── component.go (212 lines) - Universal component model
│   └── interfaces.go (114 lines) - Component interfaces
└── design/
    └── interface.go (207 lines) - Design abstraction
```

**Total**: 18 files, ~4,000 lines of domain logic

## Detailed Analysis

### `entities.go` (276 lines) - Core Entities

**What's Defined**:

1. ✅ **User** (19 lines)
   - ID, Email, Name, Role, Active
   - CreatedAt, UpdatedAt
   - **Status**: Complete

2. ✅ **Organization** (10 lines)
   - ID, Name, Description, Plan, Active
   - **Status**: Complete

3. ✅ **Building** (12 lines)
   - ID, Name, Address, Coordinates
   - Floors []*Floor, Equipment []*Equipment
   - **Status**: Complete

4. ✅ **Floor** (9 lines)
   - ID, BuildingID, Name, Level
   - Rooms []*Room, Equipment []*Equipment
   - **Status**: Complete

5. ⚠️ **Room** (9 lines) - NEEDS ENHANCEMENT
   ```go
   type Room struct {
       ID        types.ID     `json:"id"`
       FloorID   types.ID     `json:"floor_id"`
       Name      string       `json:"name"`
       Number    string       `json:"number"`
       Equipment []*Equipment `json:"equipment,omitempty"`
       CreatedAt time.Time    `json:"created_at"`
       UpdatedAt time.Time    `json:"updated_at"`
   }
   ```

   **Missing for Three-Tier Vision**:
   - ❌ Width, Length, Height (for text-based Tier 2)
   - ❌ FidelitySource string (text/ifc/lidar)
   - ❌ ConfidenceLevel int (0-3)
   - ❌ ScanDataID reference

   **Status**: ⚠️ Needs enhancement

6. ✅ **Equipment** (13 lines)
   - ID, BuildingID, FloorID, RoomID
   - Name, Type, Model
   - **Location *Location** ← HAS spatial coordinates!
   - Status
   - **Status**: Complete and excellent

7. ✅ **Location** (4 lines)
   - X, Y, Z float64
   - **Status**: Perfect for equipment positioning

**Finding**: Equipment model is MORE complete than Room model for spatial data!

### `interfaces.go` (179 lines) - Repository Contracts

**Repository Interfaces Defined**:

1. ✅ **UserRepository** (7 methods)
   - Create, GetByID, GetByEmail, List, Update, Delete
   - GetOrganizations
   - **Status**: Complete interface

2. ✅ **BuildingRepository** (8 methods)
   - Create, GetByID, GetByAddress, List, Update, Delete
   - GetEquipment, GetFloors
   - **Status**: Complete interface

3. ✅ **EquipmentRepository** (7 methods)
   - Create, GetByID, GetByBuilding, GetByType, List, Update, Delete
   - GetByLocation(buildingID, floor, room)
   - **Status**: Complete interface

4. ✅ **OrganizationRepository** (8 methods)
   - Full CRUD + user management
   - **Status**: Complete interface

5. ✅ **FloorRepository** (8 methods) - FOUND!
   ```go
   Create(ctx, floor)
   GetByID, GetByBuilding, Update, Delete, List
   GetRooms(ctx, floorID)  // ← Returns rooms!
   GetEquipment(ctx, floorID)
   ```
   - **Status**: ✅ Complete interface defined
   - **Issue**: ⚠️ Not registered in container!

6. ✅ **RoomRepository** (8 methods) - FOUND!
   ```go
   Create(ctx, room)
   GetByID, GetByFloor, GetByNumber
   Update, Delete, List
   GetEquipment(ctx, roomID)  // ← Returns equipment in room!
   ```
   - **Status**: ✅ Complete interface defined
   - **Issue**: ⚠️ Not registered in container!

**Key Finding**: Room and Floor repository **interfaces are fully defined** and already have implementations in `/infrastructure/postgis/`. They just need to be registered in the container!

### `spatial_types.go` (233 lines) - AR & Spatial

**What's Defined**:

1. ✅ **SpatialPosition** - X, Y, Z
2. ✅ **SpatialRotation** - Quaternion (X, Y, Z, W)
3. ✅ **SpatialScale** - X, Y, Z scale factors
4. ✅ **MobileSpatialAnchor** - AR reference points with confidence
5. ✅ **PointCloudUploadRequest** - LiDAR data upload
6. ✅ **PointCloudData** - Individual points with color
7. ✅ **NearbyEquipmentRequest/Result** - Spatial queries
8. ✅ **BuildingSpatialSummary** - Coverage metrics
9. ✅ **SpatialRepository** interface - Full AR/spatial operations
10. ✅ **IFCImportResult** - IFC processing results

**Status**: ✅ **EXCELLENT** - Comprehensive AR and spatial support

**For Meraki Vision**:
- ✅ Spatial positioning foundation exists
- ✅ Confidence scoring exists
- ⚠️ Need NetworkDevice-specific types

### `component/component.go` (212 lines) - Universal Component System

**Component Model**:
- ✅ Path-based addressing (`/B1/3/CONF-301/HVAC/UNIT-01`)
- ✅ Location with X, Y, Z, Floor, Room, Building
- ✅ Properties (key-value flexible storage)
- ✅ Relations (upstream/downstream connections)
- ✅ Status tracking
- ✅ Version tracking
- ✅ Audit trail (CreatedBy, UpdatedBy)

**Component Types**: 20+ predefined types
- ✅ HVAC (4 types), Electrical (4 types), Plumbing (4 types)
- ✅ Fire Safety (3 types), Access Control (3 types)
- ✅ Generic types

**Methods**:
- ✅ AddProperty, GetProperty (typed getters for string/float/bool)
- ✅ AddRelation
- ✅ UpdateStatus

**Status**: ✅ **COMPLETE** - Sophisticated component system

**Finding**: Component system can handle network devices! Could model Meraki devices as components with type="network_device"

### `building/` Subdirectory - Version Control Domain

**Files**:
- ✅ `repository.go` (183 lines) - Repository model with IFCFiles, Plans, Equipment
- ✅ `version.go` - Version entities
- ✅ `diff.go` (437 lines) - Comprehensive diff system
- ✅ `object.go` (195 lines) - Object versioning
- ✅ `ifc.go` (170 lines) - IFC domain structures

**Diff System Capabilities** (`diff.go`):
- ✅ BuildingDiff, FloorDiff, RoomDiff, EquipmentDiff
- ✅ Spatial changes (bounds, positions)
- ✅ File changes
- ✅ Property changes

**Finding**: Version control system is **comprehensive** and supports rooms already!

### Vision Alignment Summary

| Vision Requirement | Exists | Complete | Notes |
|-------------------|--------|----------|-------|
| Core entities (User, Org, Building) | ✅ | ✅ | Perfect |
| Equipment with X,Y,Z | ✅ | ✅ | Excellent |
| Floor entity | ✅ | ✅ | Complete |
| Room entity | ✅ | ⚠️ | Needs dimensions & fidelity |
| FloorRepository interface | ✅ | ✅ | Defined! |
| RoomRepository interface | ✅ | ✅ | Defined! |
| Spatial types (AR, LiDAR) | ✅ | ✅ | Comprehensive |
| Component system | ✅ | ✅ | Excellent |
| Version control | ✅ | ✅ | Sophisticated |
| Network device types | ❌ | ❌ | Need for Meraki |
| AR navigation session | ⚠️ | ⚠️ | Has AR types, need CLI→Mobile |

### Critical Findings

#### 🟢 **EXCELLENT**:
1. Repository interfaces for Room and Floor **already defined**
2. Equipment spatial positioning complete
3. Component system is sophisticated and flexible
4. Version control supports all entity types including rooms
5. AR/LiDAR infrastructure comprehensive

#### 🟡 **NEEDS MINOR ENHANCEMENT**:
1. Room model needs dimensions (width, length, height)
2. Room needs fidelity tracking fields
3. Some methods in spatial repo marked TODO

#### 🔴 **MISSING FOR VISION**:
1. NetworkDevice domain entity
2. ARNavigationSession for CLI→Mobile workflow
3. WAP (Wireless Access Point) entity

### Development Tasks for `/internal/domain`

#### Task DOMAIN-1: Enhance Room Entity (Priority: CRITICAL)
**Effort**: 2 hours
**File**: `internal/domain/entities.go`

**Current** (lines 57-66):
```go
type Room struct {
    ID        types.ID
    FloorID   types.ID
    Name      string
    Number    string
    Equipment []*Equipment
    CreatedAt time.Time
    UpdatedAt time.Time
}
```

**Enhanced**:
```go
type Room struct {
    // Core identity
    ID        types.ID     `json:"id"`
    FloorID   types.ID     `json:"floor_id"`
    Name      string       `json:"name"`
    Number    string       `json:"number"`

    // Dimensions (optional - for text-based Tier 2)
    Width     *float64     `json:"width,omitempty"`      // meters
    Length    *float64     `json:"length,omitempty"`     // meters
    Height    *float64     `json:"height,omitempty"`     // meters
    Area      *float64     `json:"area,omitempty"`       // calculated or provided

    // Fidelity tracking (for progressive enhancement)
    FidelitySource  string   `json:"fidelity_source"`      // "text", "ifc", "lidar"
    ConfidenceLevel int      `json:"confidence_level"`     // 0-3
    ScanDataID      *types.ID `json:"scan_data_id,omitempty"` // Reference to point cloud

    // Relationships
    Equipment []*Equipment `json:"equipment,omitempty"`

    // Audit
    CreatedAt time.Time    `json:"created_at"`
    UpdatedAt time.Time    `json:"updated_at"`
}
```

**Also add DTOs** (after Equipment DTOs):
```go
type CreateRoomRequest struct {
    FloorID         types.ID  `json:"floor_id" validate:"required"`
    Name            string    `json:"name" validate:"required"`
    Number          string    `json:"number"`
    Width           *float64  `json:"width,omitempty"`
    Length          *float64  `json:"length,omitempty"`
    Height          *float64  `json:"height,omitempty"`
    FidelitySource  string    `json:"fidelity_source"`
}

type UpdateRoomRequest struct {
    ID              types.ID  `json:"id" validate:"required"`
    Name            *string   `json:"name,omitempty"`
    Number          *string   `json:"number,omitempty"`
    Width           *float64  `json:"width,omitempty"`
    Length          *float64  `json:"length,omitempty"`
    Height          *float64  `json:"height,omitempty"`
    FidelitySource  *string   `json:"fidelity_source,omitempty"`
    ConfidenceLevel *int      `json:"confidence_level,omitempty"`
}

type RoomFilter struct {
    FloorID         *types.ID `json:"floor_id,omitempty"`
    FidelitySource  *string   `json:"fidelity_source,omitempty"`
    MinConfidence   *int      `json:"min_confidence,omitempty"`
    Limit           int       `json:"limit,omitempty"`
    Offset          int       `json:"offset,omitempty"`
}
```

**Checklist**:
- [ ] Update Room struct in entities.go
- [ ] Add CreateRoomRequest, UpdateRoomRequest, RoomFilter
- [ ] Update all references to Room (should be minimal)
- [ ] Add unit tests for new fields
- [ ] Update JSON serialization tests

#### Task DOMAIN-2: Add Meraki Domain Entities (Priority: MEDIUM)
**Effort**: 1 day
**Files**:
- `internal/domain/network_device.go` (new)
- `internal/domain/ar_navigation_session.go` (new)

**See full specifications in**: `docs/integration/MERAKI_AR_NAVIGATION.md`

**Entities to create**:
- [ ] NetworkDevice
- [ ] DeviceType enum
- [ ] ConnectionStatus enum
- [ ] DeviceLocation
- [ ] ARNavigationSession
- [ ] NavigationStatus enum
- [ ] Priority enum
- [ ] Related DTOs and filters

#### Task DOMAIN-3: Add Room Service Interface (Priority: HIGH)
**Effort**: 1 hour
**File**: `internal/domain/interfaces.go`

**Add after BuildingService** (around line 106):
```go
// RoomService defines the contract for room business operations
type RoomService interface {
    CreateRoom(ctx context.Context, req *CreateRoomRequest) (*Room, error)
    CreateRoomFromText(ctx context.Context, req *CreateRoomRequest) (*Room, error)
    CreateRoomFromBoundary(ctx context.Context, floorID types.ID, name string, points []Location) (*Room, error)
    GetRoom(ctx context.Context, id types.ID) (*Room, error)
    UpdateRoom(ctx context.Context, req *UpdateRoomRequest) (*Room, error)
    DeleteRoom(ctx context.Context, id types.ID) error
    ListRooms(ctx context.Context, floorID types.ID) ([]*Room, error)
    GetRoomEquipment(ctx context.Context, roomID types.ID) ([]*Equipment, error)
    UpgradeRoomWithScan(ctx context.Context, roomID types.ID, scanSessionID types.ID) error
    ValidateRoomDimensions(ctx context.Context, width, length, height float64) error
}
```

**Checklist**:
- [ ] Add RoomService interface
- [ ] Add RoomUpgradeService interface (for scan upgrades)
- [ ] Add NetworkDeviceRepository interface (Meraki)
- [ ] Add ARNavigationSessionRepository interface (Meraki)

### Summary for `/internal/domain`

**Overall Status**: 🟢 **90% Complete**

**Strengths**:
- ✅ All core entities defined and complete
- ✅ Repository interfaces comprehensive
- ✅ Equipment positioning excellent
- ✅ Component system sophisticated
- ✅ Version control comprehensive
- ✅ AR/spatial types extensive
- ✅ Clean architecture principles followed

**Quick Wins**:
- 🎯 Room entity just needs 4 new fields (1 hour)
- 🎯 RoomService interface just needs definition (30 min)
- 🎯 DTOs are straightforward (1 hour)

**Medium Effort**:
- Meraki entities (1 day)
- Full testing of changes (2 days)

**Estimated Fix Time**: 3-4 days for all domain enhancements

---

# Part 3: `/internal/usecase` - Business Logic Layer

## Directory Structure

**Files**: 15 use case files (~154KB total)

```
/internal/usecase/
├── analytics_usecase.go (4.5K) - Building analytics
├── auth_usecase.go (8.9K) - Authentication
├── building_usecase.go (8.7K) - Building CRUD & import
├── buildingops_usecase.go (6.3K) - Building operations
├── component_usecase.go (10K) - Component management
├── design_usecase.go (12K) - Design abstractions
├── diff_service.go (23K) - Version diff calculations
├── equipment_usecase.go (9.0K) - Equipment CRUD
├── ifc_usecase.go (6.5K) - IFC import/export
├── organization_usecase.go (10K) - Multi-tenancy
├── repository_usecase.go (7.9K) - Repository management
├── rollback_service.go (19K) - Version rollback
├── snapshot_service.go (11K) - State snapshots
├── user_usecase.go (11K) - User management
└── version_usecase.go (7.5K) - Version control
```

## Use Case Inventory

### ✅ IMPLEMENTED (12 use cases)

1. **BuildingUseCase** (8.7K)
   - ✅ CreateBuilding, GetBuilding, UpdateBuilding, DeleteBuilding
   - ✅ ListBuildings with filtering
   - ✅ ImportBuilding (IFC - line 189)
   - ✅ ExportBuilding (stub - returns "not implemented")
   - **Container**: ✅ Registered

2. **EquipmentUseCase** (9.0K)
   - Full CRUD for equipment
   - Spatial positioning support
   - **Container**: ✅ Registered

3. **ComponentUseCase** (10K)
   - ✅ CreateComponent (path-based)
   - ✅ Get (by ID or path), Update, Delete
   - ✅ List with filtering
   - ✅ AddProperty, RemoveProperty
   - ✅ AddRelation, RemoveRelation
   - ✅ UpdateStatus
   - **Container**: ✅ Registered

4. **UserUseCase** (11K)
   - Full user management
   - **Container**: ✅ Registered

5. **OrganizationUseCase** (10K)
   - Multi-tenancy support
   - **Container**: ✅ Registered

6. **AuthUseCase** (8.9K)
   - Authentication logic
   - **Container**: ❌ NOT registered!

7. **AnalyticsUseCase** (4.5K)
   - Building analytics
   - **Container**: ❌ NOT registered!

8. **BuildingOpsUseCase** (6.3K)
   - Building operations
   - **Container**: ❌ NOT registered!

9. **RepositoryUseCase** (7.9K)
   - Repository management
   - **Container**: ✅ Registered

10. **IFCUseCase** (6.5K)
    - IFC import/export
    - **Container**: ✅ Registered

11. **VersionUseCase** (7.5K)
    - Version control
    - **Container**: ✅ Registered

12. **DesignUseCase** (12K)
    - Design abstractions
    - **Container**: ✅ Registered

### ✅ VERSION CONTROL SERVICES (3 services)

13. **SnapshotService** (11K)
    - State capture
    - **Container**: ❌ Not registered

14. **DiffService** (23K)
    - Change calculations
    - **Container**: ❌ Not registered

15. **RollbackService** (19K)
    - Version restoration
    - **Container**: ❌ Not registered

### ❌ MISSING for Vision

16. **RoomUseCase** - CRITICAL
    - CreateRoom, UpdateRoom, DeleteRoom
    - CreateRoomFromText (Tier 2)
    - CreateRoomFromBoundary
    - UpgradeRoomWithScan (Tier 3)
    - **Status**: Doesn't exist

17. **FloorUseCase** - HIGH
    - Full CRUD for floors
    - **Status**: Doesn't exist (floors managed via BuildingUseCase?)

18. **FindDeviceUseCase** - MEDIUM (Meraki)
    - Device search and location
    - **Status**: Design complete, not implemented

19. **PushARNavigationUseCase** - MEDIUM (Meraki)
    - CLI → Mobile AR push
    - **Status**: Design complete, not implemented

20. **SyncMerakiDevicesUseCase** - MEDIUM (Meraki)
    - Sync from Meraki Dashboard
    - **Status**: Design complete, not implemented

## Critical Finding: Use Cases Exist But Not Registered!

**Issue**: 6 use cases are fully implemented but **not in the container**:
- AnalyticsUseCase
- AuthUseCase
- BuildingOpsUseCase
- SnapshotService
- DiffService
- RollbackService

**Impact**: Features exist but **can't be used** because they're not wired up!

**Quick Fix**: Register these in container.go (< 1 hour work)

## Vision Alignment

| Vision Requirement | Use Case Needed | Exists | In Container | Status |
|-------------------|-----------------|--------|--------------|--------|
| Building CRUD | BuildingUseCase | ✅ | ✅ | Complete |
| Equipment positioning | EquipmentUseCase | ✅ | ✅ | Complete |
| Component system | ComponentUseCase | ✅ | ✅ | Complete |
| Version control | VersionUseCase | ✅ | ✅ | Complete |
| Snapshots | SnapshotService | ✅ | ❌ | **Not wired** |
| Diffs | DiffService | ✅ | ❌ | **Not wired** |
| Rollback | RollbackService | ✅ | ❌ | **Not wired** |
| **Room management** | **RoomUseCase** | ❌ | ❌ | **MISSING** |
| **Room from text** | **RoomUseCase** | ❌ | ❌ | **MISSING** |
| **Room upgrade** | **RoomUpgradeUseCase** | ❌ | ❌ | **MISSING** |
| Meraki find | FindDeviceUseCase | ❌ | ❌ | **MISSING** |
| Meraki push AR | PushARNavigationUseCase | ❌ | ❌ | **MISSING** |

## Development Tasks for `/internal/usecase`

### Task UC-1: Create RoomUseCase (Priority: CRITICAL)
**Effort**: 3-4 days
**File**: `internal/usecase/room_usecase.go` (new, estimate: ~300 lines)

**Structure**:
```go
package usecase

type RoomUseCase struct {
    roomRepo    domain.RoomRepository
    floorRepo   domain.FloorRepository
    equipment Repo domain.EquipmentRepository
    logger      domain.Logger
}

func NewRoomUseCase(...) *RoomUseCase

// Core CRUD
func (uc *RoomUseCase) CreateRoom(ctx, req) (*domain.Room, error)
func (uc *RoomUseCase) GetRoom(ctx, id) (*domain.Room, error)
func (uc *RoomUseCase) UpdateRoom(ctx, req) (*domain.Room, error)
func (uc *RoomUseCase) DeleteRoom(ctx, id) error
func (uc *RoomUseCase) ListRooms(ctx, floorID) ([]*domain.Room, error)

// Text-based creation (Tier 2)
func (uc *RoomUseCase) CreateRoomFromText(ctx, req) (*domain.Room, error) {
    // Validate dimensions (width, length, height > 0)
    // Calculate area = width * length
    // Set fidelity_source = "text"
    // Set confidence_level = 1 (medium)
    // Create room entity
    // Save to repository
    // Return room
}

func (uc *RoomUseCase) CreateRoomFromBoundary(ctx, floorID, name, points) (*domain.Room, error) {
    // Validate polygon (closed, non-intersecting)
    // Calculate area from polygon
    // Calculate bounding box (width, length)
    // Set fidelity_source = "text"
    // Set confidence_level = 2 (high - user provided precise bounds)
    // Create room entity
    // Save to repository
    // Return room
}

// Validation
func (uc *RoomUseCase) ValidateDimensions(width, length, height) error
func (uc *RoomUseCase) CheckRoomOverlaps(ctx, floorID, boundary) (bool, error)
func (uc *RoomUseCase) CalculateArea(width, length) float64

// Equipment management
func (uc *RoomUseCase) GetRoomEquipment(ctx, roomID) ([]*domain.Equipment, error)
func (uc *RoomUseCase) ValidateEquipmentPosition(ctx, roomID, position) error

// Private helpers
func (uc *RoomUseCase) validateCreateRoom(req) error
func (uc *RoomUseCase) validateUpdateRoom(req) error
```

**Test Coverage**:
- [ ] TestCreateRoom - basic creation
- [ ] TestCreateRoomFromText - with dimensions
- [ ] TestCreateRoomFromBoundary - with polygon
- [ ] TestValidateDimensions - edge cases
- [ ] TestCalculateArea - accuracy
- [ ] TestCheckOverlaps - spatial validation
- [ ] Integration tests with PostGIS

### Task UC-2: Create RoomUpgradeUseCase (Priority: HIGH)
**Effort**: 2-3 days
**File**: `internal/usecase/room_upgrade_usecase.go` (new, estimate: ~200 lines)

**Purpose**: Handle upgrading room fidelity (text → IFC → LiDAR)

```go
package usecase

type RoomUpgradeUseCase struct {
    roomRepo     domain.RoomRepository
    pointCloudRepo domain.PointCloudRepository // Need to create
    spatialRepo  domain.SpatialRepository
    versionUC    *VersionUseCase // For versioning upgrades
    logger       domain.Logger
}

func (uc *RoomUpgradeUseCase) UpgradeRoomWithScan(ctx, roomID, scanSessionID) error {
    // 1. Get current room
    // 2. Validate scan session exists and is complete
    // 3. Get point cloud data from scan
    // 4. Calculate room geometry from point cloud
    // 5. Preserve equipment positions (transform if needed)
    // 6. Update room:
    //    - fidelity_source = "lidar"
    //    - confidence_level = 3 (highest)
    //    - scan_data_id = scanSessionID
    //    - Update dimensions from scan
    // 7. Create version snapshot (for rollback)
    // 8. Save updated room
    // 9. Notify mobile app of completion
}

func (uc *RoomUpgradeUseCase) UpgradeRoomWithIFC(ctx, roomID, ifcSpaceData) error
func (uc *RoomUpgradeUseCase) ValidateUpgrade(ctx, roomID, newGeometry) error
func (uc *RoomUpgradeUseCase) PreserveEquipmentPositions(ctx, roomID, transform) error
func (uc *RoomUpgradeUseCase) RollbackUpgrade(ctx, roomID, snapshotID) error
```

### Task UC-3: Register Existing Use Cases in Container (Priority: CRITICAL)
**Effort**: 2 hours
**File**: `internal/app/container.go`

**Already exist, just need registration**:
- [ ] AnalyticsUseCase
- [ ] AuthUseCase
- [ ] BuildingOpsUseCase
- [ ] SnapshotService
- [ ] DiffService
- [ ] RollbackService

**Impact**: Unlocks existing functionality immediately!

### Task UC-4: Meraki Use Cases (Priority: MEDIUM)
**Effort**: 2 weeks total
**Files**: 4 new use cases

1. **FindDeviceUseCase** (est. 300 lines)
   - Device search by name/IP/MAC
   - Location queries
   - History tracking

2. **TrackDeviceUseCase** (est. 200 lines)
   - Real-time tracking
   - Movement history
   - Alerts

3. **PushARNavigationUseCase** (est. 400 lines)
   - Create navigation session
   - Calculate path
   - Send push notification
   - Track completion

4. **SyncMerakiDevicesUseCase** (est. 300 lines)
   - Poll Meraki API
   - Sync devices
   - Calculate positions
   - Update database

## Summary for `/internal/usecase`

**Overall Status**: 🟢 **85% Complete**

**Strengths**:
- ✅ 12 use cases fully implemented
- ✅ Clean separation of concerns
- ✅ Comprehensive version control (snapshot, diff, rollback)
- ✅ Component system complete
- ✅ Building and equipment complete

**Critical Issues**:
- 🔴 RoomUseCase doesn't exist (BLOCKING for Tier 2)
- 🔴 6 use cases exist but not registered in container
- 🟡 Meraki use cases needed (4 new)

**Quick Wins**:
- 🎯 Register 6 existing use cases (2 hours)

**Medium Effort**:
- Create RoomUseCase (3-4 days)
- Create RoomUpgradeUseCase (2-3 days)

**Estimated Fix Time**: 1-2 weeks for full three-tier fidelity

---

