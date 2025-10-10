# ADR 007: Version Control System Architecture ("Git of Buildings")

## Status
✅ **Accepted** | 🚧 **Implementation in Progress**

## Context

ArxOS needs a Git-like version control system for building data, enabling facilities managers to track changes, compare versions, and roll back when needed. This is the "Git of Buildings" vision that differentiates ArxOS from traditional BIM tools.

### Business Requirements

1. **Track all building changes** over time
2. **Compare versions** to see what changed
3. **Rollback to previous versions** when mistakes occur
4. **Understand change history** with commit messages and diffs
5. **Handle large files efficiently** (IFC models, plans, equipment specs)
6. **Support concurrent updates** from multiple users/systems
7. **Integrate with operational data** (sensors, BMS, maintenance records)

### Technical Constraints

- Must work with PostgreSQL/PostGIS for spatial data
- Must handle binary files (IFC, PDF plans) efficiently
- Must scale to buildings with 10,000+ equipment items
- Must provide fast diffs without scanning entire database
- Must support atomic version creation (all-or-nothing)
- Must preserve referential integrity across versions

## Decision

We will implement a **hybrid content-addressable version control system** combining Git's object model with PostgreSQL's relational capabilities.

### Core Architecture: Three-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│                    Version Layer                         │
│  (Commits, branches, tags, version graph)               │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Snapshot Layer                         │
│  (Building state, equipment list, spatial data)         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    Object Layer                          │
│  (Content-addressed blobs, files, metadata)             │
└─────────────────────────────────────────────────────────┘
```

---

## 1. What Gets Versioned

### 1.1 Structured Data (PostgreSQL)

**Building Structure:**
- Building metadata (name, type, address, floors)
- Floor definitions (level, elevation, area)
- Room definitions (name, type, area, geometry)
- Spatial relationships (contains, adjacent, connected)

**Equipment Inventory:**
- Equipment records (ID, name, type, manufacturer, model)
- Equipment locations (floor, room, 3D coordinates)
- Equipment specifications (capacity, power, efficiency)
- Equipment relationships (serves, controls, monitors)

**Operational Data:**
- Maintenance schedules
- Energy benchmarks
- Occupancy schedules
- System set points

**Integration Metadata:**
- BMS connections
- Sensor mappings
- API configurations

### 1.2 File Data (Content-Addressable Storage)

**IFC Models:**
- Full IFC files (4.0, 4.3, etc.)
- IFC discipline files (architectural, MEP, structural)
- IFC validation reports

**Plans & Drawings:**
- Floor plans (IFC)
- Site plans
- Sections and elevations
- As-built drawings

**Equipment Specifications:**
- Manufacturer datasheets (PDF)
- O&M manuals
- Warranty documents
- Equipment photos

**Reports & Documents:**
- Commissioning reports
- Inspection reports
- Energy audits
- Compliance certifications

### 1.3 What's NOT Versioned

- **Time-series sensor data** - Too high frequency, use separate TSDB
- **User sessions** - Ephemeral state
- **Cache entries** - Temporary performance optimization
- **Log files** - Separate logging infrastructure
- **Binary large objects > 100MB** - Use external storage with references

---

## 2. Storage Format

### 2.1 Content-Addressable Object Store

**Inspired by Git's object model, adapted for building data:**

```go
type ObjectType string

const (
    ObjectTypeBlob     ObjectType = "blob"      // File contents
    ObjectTypeTree     ObjectType = "tree"      // Directory structure
    ObjectTypeSnapshot ObjectType = "snapshot"  // Building state snapshot
    ObjectTypeVersion  ObjectType = "version"   // Version metadata
)

type Object struct {
    Hash       string     // SHA-256 hash of contents
    Type       ObjectType // Object type
    Size       int64      // Size in bytes
    Contents   []byte     // Actual data (for small objects)
    StorePath  string     // File path (for large objects)
    CreatedAt  time.Time  // When object was created
    RefCount   int        // Reference count for GC
}
```

**Hash Calculation:**
```
hash = SHA256(type + size + contents)
```

**Storage Strategy:**
- **< 1KB**: Store in PostgreSQL `objects` table (JSON/JSONB)
- **1KB - 10MB**: Store in filesystem at `~/.arxos/objects/{hash[:2]}/{hash[2:]}`
- **> 10MB**: Store in filesystem with compression (gzip)

### 2.2 Snapshot Structure

A **snapshot** represents the complete state of a building at a point in time:

```go
type Snapshot struct {
    Hash           string             // Content hash of snapshot
    RepositoryID   string             // Which building repository
    BuildingTree   string             // Hash of building structure tree
    EquipmentTree  string             // Hash of equipment tree
    SpatialTree    string             // Hash of spatial data tree
    FilesTree      string             // Hash of files tree
    OperationsTree string             // Hash of operations tree
    Metadata       SnapshotMetadata   // Additional metadata
    CreatedAt      time.Time          // Snapshot creation time
}

type SnapshotMetadata struct {
    BuildingCount  int               // Number of buildings
    FloorCount     int               // Number of floors
    RoomCount      int               // Number of rooms
    EquipmentCount int               // Number of equipment items
    FileCount      int               // Number of files
    TotalSize      int64             // Total data size
    Checksums      map[string]string // Component checksums
}
```

**Tree Structure (Merkle Tree):**
```
snapshot:abc123
├── building-tree:def456
│   ├── building-metadata:gh789
│   ├── floors-list:ijk012
│   └── rooms-list:lmn345
├── equipment-tree:opq678
│   ├── hvac-equipment:rst901
│   ├── electrical-equipment:uvw234
│   └── plumbing-equipment:xyz567
├── spatial-tree:aaa111
│   ├── 3d-positions:bbb222
│   ├── floor-plans:ccc333
│   └── bounding-boxes:ddd444
└── files-tree:eee555
    ├── ifc-files:fff666
    ├── plans:ggg777
    └── specs:hhh888
```

**Benefits:**
- **Deduplication**: Unchanged subtrees share same hash
- **Fast comparison**: Compare tree hashes, drill down only where different
- **Efficient storage**: Only store changed trees
- **Parallel processing**: Can compute/compare trees concurrently

### 2.3 Version (Commit) Structure

A **version** is a commit-like object referencing a snapshot:

```go
type Version struct {
    ID           string            // UUID (for human reference)
    Hash         string            // SHA-256 hash of version contents
    RepositoryID string            // Which building repository
    Snapshot     string            // Hash of building snapshot
    Parent       string            // Parent version hash (empty for initial)
    Parents      []string          // Multiple parents for merges
    Tag          string            // Semantic version (v1.2.3)
    Message      string            // Commit message
    Author       Author            // Who made the change
    Timestamp    time.Time         // When version was created
    Metadata     VersionMetadata   // Additional metadata
}

type Author struct {
    Name  string // User name
    Email string // User email
    ID    string // User ID
}

type VersionMetadata struct {
    ChangeCount    int               // Number of changes
    ChangeSummary  Summary           // High-level summary
    Source         string            // How created (manual, import, sync)
    SystemVersion  string            // ArxOS version
    ValidatedAt    *time.Time        // When validated
    ValidationHash string            // Hash of validation result
}
```

**Version Graph:**
```
v1.0.0 (initial) ──→ v1.1.0 ──→ v1.2.0 ──→ v1.3.0 (current)
                         │                      ↑
                         └─→ v1.1.1-hotfix ────┘
```

### 2.4 Database Schema

**Core Tables:**

```sql
-- Object store (small objects only)
CREATE TABLE version_objects (
    hash         TEXT PRIMARY KEY,
    type         TEXT NOT NULL,
    size         BIGINT NOT NULL,
    contents     JSONB,          -- For small objects
    store_path   TEXT,           -- For large objects
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ref_count    INTEGER NOT NULL DEFAULT 0,
    compressed   BOOLEAN DEFAULT FALSE
);

-- Snapshots
CREATE TABLE version_snapshots (
    hash            TEXT PRIMARY KEY,
    repository_id   UUID NOT NULL REFERENCES building_repositories(id),
    building_tree   TEXT NOT NULL REFERENCES version_objects(hash),
    equipment_tree  TEXT NOT NULL REFERENCES version_objects(hash),
    spatial_tree    TEXT NOT NULL REFERENCES version_objects(hash),
    files_tree      TEXT NOT NULL REFERENCES version_objects(hash),
    operations_tree TEXT NOT NULL REFERENCES version_objects(hash),
    metadata        JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Versions (commits)
CREATE TABLE versions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hash          TEXT UNIQUE NOT NULL,
    repository_id UUID NOT NULL REFERENCES building_repositories(id),
    snapshot      TEXT NOT NULL REFERENCES version_snapshots(hash),
    parent        TEXT REFERENCES versions(hash),
    tag           TEXT,
    message       TEXT NOT NULL,
    author_name   TEXT NOT NULL,
    author_email  TEXT NOT NULL,
    author_id     UUID REFERENCES users(id),
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata      JSONB NOT NULL,

    UNIQUE(repository_id, tag)
);

-- Parent relationships (for merges)
CREATE TABLE version_parents (
    version_hash TEXT NOT NULL REFERENCES versions(hash),
    parent_hash  TEXT NOT NULL REFERENCES versions(hash),
    parent_order INT NOT NULL,
    PRIMARY KEY (version_hash, parent_hash)
);

-- Indexes
CREATE INDEX idx_versions_repository ON versions(repository_id, timestamp DESC);
CREATE INDEX idx_versions_tag ON versions(repository_id, tag);
CREATE INDEX idx_versions_parent ON versions(parent);
CREATE INDEX idx_snapshots_repository ON version_snapshots(repository_id);
CREATE INDEX idx_objects_type ON version_objects(type);
CREATE INDEX idx_objects_created ON version_objects(created_at);
```

**Spatial Extension:**
```sql
-- Spatial version metadata
CREATE TABLE version_spatial_metadata (
    snapshot_hash TEXT PRIMARY KEY REFERENCES version_snapshots(hash),
    bounds        GEOMETRY(POLYGON, 4326) NOT NULL,
    center        GEOMETRY(POINT, 4326) NOT NULL,
    floor_count   INTEGER NOT NULL,
    room_count    INTEGER NOT NULL,
    total_area    NUMERIC(10,2) NOT NULL
);

CREATE INDEX idx_version_spatial_bounds ON version_spatial_metadata USING GIST(bounds);
```

---

## 3. Diff Algorithm

### 3.1 Three-Phase Diff Strategy

**Phase 1: Tree-Level Diff (Fast)**
```go
func DiffSnapshots(from, to *Snapshot) *SnapshotDiff {
    diff := &SnapshotDiff{}

    // Compare tree hashes
    if from.BuildingTree != to.BuildingTree {
        diff.BuildingChanged = true
    }
    if from.EquipmentTree != to.EquipmentTree {
        diff.EquipmentChanged = true
    }
    if from.SpatialTree != to.SpatialTree {
        diff.SpatialChanged = true
    }
    if from.FilesTree != to.FilesTree {
        diff.FilesChanged = true
    }

    return diff
}
```

**Phase 2: Subtree-Level Diff (Medium)**
```go
func DiffTrees(fromTree, toTree *Tree) []Change {
    changes := []Change{}

    // Build maps for fast lookup
    fromEntries := buildEntryMap(fromTree)
    toEntries := buildEntryMap(toTree)

    // Find added and modified
    for path, toEntry := range toEntries {
        fromEntry, exists := fromEntries[path]
        if !exists {
            changes = append(changes, Change{
                Type: ChangeTypeAdded,
                Path: path,
                Hash: toEntry.Hash,
            })
        } else if fromEntry.Hash != toEntry.Hash {
            changes = append(changes, Change{
                Type: ChangeTypeModified,
                Path: path,
                OldHash: fromEntry.Hash,
                NewHash: toEntry.Hash,
            })
        }
    }

    // Find deleted
    for path, fromEntry := range fromEntries {
        if _, exists := toEntries[path]; !exists {
            changes = append(changes, Change{
                Type: ChangeTypeDeleted,
                Path: path,
                Hash: fromEntry.Hash,
            })
        }
    }

    return changes
}
```

**Phase 3: Object-Level Diff (Detailed)**
```go
func DiffObjects(fromHash, toHash string) (*ObjectDiff, error) {
    // Load both objects
    fromObj, err := loadObject(fromHash)
    if err != nil {
        return nil, err
    }
    toObj, err := loadObject(toHash)
    if err != nil {
        return nil, err
    }

    // Type-specific diff
    switch fromObj.Type {
    case ObjectTypeEquipment:
        return diffEquipment(fromObj, toObj)
    case ObjectTypeBuilding:
        return diffBuilding(fromObj, toObj)
    case ObjectTypeSpatial:
        return diffSpatial(fromObj, toObj)
    case ObjectTypeBlob:
        return diffBlob(fromObj, toObj)
    }

    return nil, fmt.Errorf("unsupported object type: %s", fromObj.Type)
}
```

### 3.2 Domain-Specific Diff Algorithms

**Building Structure Diff:**
```go
type BuildingDiff struct {
    MetadataChanges   []FieldChange  // Name, address, type changed
    FloorsAdded       []Floor        // New floors
    FloorsRemoved     []Floor        // Removed floors
    FloorsModified    []FloorDiff    // Modified floors
    RoomsAdded        []Room         // New rooms
    RoomsRemoved      []Room         // Removed rooms
    RoomsModified     []RoomDiff     // Modified rooms
}

type FieldChange struct {
    Field    string
    OldValue interface{}
    NewValue interface{}
}
```

**Equipment Diff:**
```go
type EquipmentDiff struct {
    Added        []Equipment           // New equipment
    Removed      []Equipment           // Removed equipment
    Modified     []EquipmentChange     // Changed equipment
    Moved        []EquipmentMove       // Position changes
    Reclassified []EquipmentReclass    // Type changes
}

type EquipmentMove struct {
    Equipment  Equipment
    FromFloor  string
    ToFloor    string
    FromRoom   string
    ToRoom     string
    FromPos    Point3D
    ToPos      Point3D
    Distance   float64  // 3D distance moved
}
```

**Spatial Data Diff:**
```go
type SpatialDiff struct {
    GeometryChanges  []GeometryChange   // Shape changes
    PositionChanges  []PositionChange   // Location changes
    BoundsChanged    bool               // Building bounds changed
    BoundsDiff       BoundingBox        // New vs old bounds
}

type GeometryChange struct {
    EntityType string        // "floor", "room", "equipment"
    EntityID   string
    OldGeom    Geometry
    NewGeom    Geometry
    AreaDiff   float64       // Area change (sq meters)
    Overlap    float64       // Percentage overlap
}
```

**File Diff:**
```go
type FileDiff struct {
    Added      []FileInfo      // New files
    Removed    []FileInfo      // Deleted files
    Modified   []FileChange    // Changed files
    Renamed    []FileRename    // Renamed files
    Moved      []FileMove      // Moved files
    TotalSize  int64           // Net size change
}

type FileChange struct {
    Path       string
    OldHash    string
    NewHash    string
    OldSize    int64
    NewSize    int64
    SizeDiff   int64
}
```

### 3.3 Diff Output Formats

**Unified Diff (Git-style):**
```
diff --arx a/building/floor-3 b/building/floor-3
--- a/building/floor-3
+++ b/building/floor-3
@@ -1,3 +1,3 @@
 name: Third Floor
-area: 5000.0
+area: 5250.0
 elevation: 9.5

diff --arx a/equipment/AHU-101 b/equipment/AHU-101
--- a/equipment/AHU-101
+++ b/equipment/AHU-101
@@ -1,4 +1,4 @@
 name: Air Handler Unit 101
 type: HVAC
-capacity: 10000
+capacity: 12000
 location: Mechanical Room
```

**JSON Diff (API-friendly):**
```json
{
  "from_version": "v1.0.0",
  "to_version": "v1.1.0",
  "summary": {
    "total_changes": 15,
    "buildings_modified": 1,
    "floors_added": 0,
    "rooms_modified": 3,
    "equipment_added": 5,
    "equipment_modified": 7,
    "files_added": 2
  },
  "changes": [
    {
      "type": "equipment_added",
      "path": "equipment/AHU-105",
      "entity": {
        "id": "eq-123",
        "name": "Air Handler Unit 105",
        "type": "HVAC"
      }
    }
  ]
}
```

**Semantic Diff (Human-readable):**
```
Building: ArxOS HQ (v1.0.0 → v1.1.0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Equipment Changes:
  + Added 5 HVAC units on Floor 3
  ↻ Upgraded AHU-101 capacity: 10000 CFM → 12000 CFM
  ✓ Moved VAV-205 from Room 301 → Room 305 (15.3m)
  - Removed obsolete Fan Coil Units (FCU-401, FCU-402)

Spatial Changes:
  ↻ Floor 3 area increased: 5000.0m² → 5250.0m²
  + Added Room 306 (Conference Room, 45.5m²)
```

---

## 4. Merge Strategy

### 4.1 Merge Scenarios

**Scenario 1: Linear History (Fast-Forward)**
```
main:      v1.0 ──→ v1.1 ──→ v1.2
branch:                          └──→ v1.3 (merge = fast-forward)
```
✅ **No conflicts possible** - Simple pointer update

**Scenario 2: Divergent History (Three-Way Merge)**
```
main:      v1.0 ──→ v1.1 ──→ v1.2 (base)
                             ├──→ v1.3 (ours)
                             └──→ v1.2.1 (theirs)
                                      │
                                      ↓
                                   v1.4 (merged)
```
⚠️ **Conflicts possible** - Need merge algorithm

### 4.2 Conflict Detection

**Non-Conflicting Changes (Auto-Merge):**
- Different entities modified (Equipment A vs Equipment B)
- Different properties modified (name vs capacity)
- Different files modified (plan1.ifc vs plan2.ifc)
- Different floors modified (Floor 1 vs Floor 2)

**Conflicting Changes (Manual Resolution):**
- Same entity, same property modified differently
- Same file modified differently
- Spatial overlap conflicts (equipment in same location)
- Referential integrity violations (equipment references deleted room)

```go
type MergeConflict struct {
    Type         ConflictType
    Path         string
    BaseValue    interface{}
    OursValue    interface{}
    TheirsValue  interface{}
    Description  string
    Resolution   ResolutionStrategy
}

type ConflictType string

const (
    ConflictTypePropertyChange  ConflictType = "property_change"
    ConflictTypeSpatialOverlap  ConflictType = "spatial_overlap"
    ConflictTypeReferenceViolation ConflictType = "reference_violation"
    ConflictTypeFileModified    ConflictType = "file_modified"
)

type ResolutionStrategy string

const (
    ResolutionKeepOurs      ResolutionStrategy = "keep_ours"
    ResolutionKeepTheirs    ResolutionStrategy = "keep_theirs"
    ResolutionKeepBoth      ResolutionStrategy = "keep_both"
    ResolutionManual        ResolutionStrategy = "manual"
)
```

### 4.3 Three-Way Merge Algorithm

**Step 1: Find Common Ancestor**
```go
func FindMergeBase(ours, theirs *Version) (*Version, error) {
    // Walk version graph to find common ancestor
    oursAncestors := collectAncestors(ours)
    theirsAncestors := collectAncestors(theirs)

    // Find most recent common ancestor
    for _, v := range oursAncestors {
        if contains(theirsAncestors, v) {
            return v, nil
        }
    }

    return nil, ErrNoCommonAncestor
}
```

**Step 2: Three-Way Diff**
```go
func ThreeWayMerge(base, ours, theirs *Snapshot) (*MergeResult, error) {
    result := &MergeResult{
        Conflicts: []MergeConflict{},
        Changes:   []Change{},
    }

    // Diff base → ours
    ourChanges := DiffSnapshots(base, ours)

    // Diff base → theirs
    theirChanges := DiffSnapshots(base, theirs)

    // Find conflicts
    for _, ourChange := range ourChanges {
        for _, theirChange := range theirChanges {
            if conflict := detectConflict(ourChange, theirChange); conflict != nil {
                result.Conflicts = append(result.Conflicts, *conflict)
            }
        }
    }

    // Apply non-conflicting changes
    for _, change := range ourChanges {
        if !hasConflict(change, result.Conflicts) {
            result.Changes = append(result.Changes, change)
        }
    }
    for _, change := range theirChanges {
        if !hasConflict(change, result.Conflicts) {
            result.Changes = append(result.Changes, change)
        }
    }

    return result, nil
}
```

**Step 3: Automatic Resolution (where possible)**
```go
func AutoResolveConflicts(conflicts []MergeConflict) ([]Change, []MergeConflict) {
    resolved := []Change{}
    remaining := []MergeConflict{}

    for _, conflict := range conflicts {
        switch conflict.Type {
        case ConflictTypePropertyChange:
            // Use "last write wins" for non-critical properties
            if isNonCriticalProperty(conflict.Path) {
                resolved = append(resolved, Change{
                    Type: ChangeTypeModified,
                    Path: conflict.Path,
                    NewValue: conflict.TheirsValue, // Newer timestamp
                })
            } else {
                remaining = append(remaining, conflict)
            }

        case ConflictTypeSpatialOverlap:
            // Cannot auto-resolve spatial conflicts
            remaining = append(remaining, conflict)

        case ConflictTypeReferenceViolation:
            // Cannot auto-resolve integrity violations
            remaining = append(remaining, conflict)

        case ConflictTypeFileModified:
            // Keep both versions with suffixes
            resolved = append(resolved, Change{
                Type: ChangeTypeAdded,
                Path: conflict.Path + ".ours",
                NewValue: conflict.OursValue,
            })
            resolved = append(resolved, Change{
                Type: ChangeTypeAdded,
                Path: conflict.Path + ".theirs",
                NewValue: conflict.TheirsValue,
            })
        }
    }

    return resolved, remaining
}
```

### 4.4 Merge Strategies

**Strategy 1: Ours (Prefer Current)**
```bash
arx repo merge --strategy=ours v1.2.1
# Keep all our changes in case of conflict
```

**Strategy 2: Theirs (Prefer Incoming)**
```bash
arx repo merge --strategy=theirs v1.2.1
# Keep all their changes in case of conflict
```

**Strategy 3: Three-Way (Default)**
```bash
arx repo merge v1.2.1
# Three-way merge with conflict detection
# Requires manual resolution of conflicts
```

**Strategy 4: Union (Keep Both)**
```bash
arx repo merge --strategy=union v1.2.1
# Add equipment from both versions
# Only for additive changes (equipment, files)
```

### 4.5 Merge Workflow

```
1. User initiates merge
   ↓
2. Find common ancestor (merge base)
   ↓
3. Three-way diff (base, ours, theirs)
   ↓
4. Detect conflicts
   ↓
5. Auto-resolve where possible
   ↓
6. Present remaining conflicts to user
   ↓
7. User resolves conflicts
   ↓
8. Create merge commit with two parents
   ↓
9. Update current version pointer
```

---

## 5. Version Creation Workflow

### 5.1 Commit Process

```go
func CreateVersion(ctx context.Context, repoID string, message string) (*Version, error) {
    // 1. Begin transaction
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
        return nil, err
    }
    defer tx.Rollback()

    // 2. Capture current building state
    snapshot, err := captureSnapshot(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }

    // 3. Store snapshot (content-addressable)
    snapshotHash, err := storeSnapshot(ctx, tx, snapshot)
    if err != nil {
        return nil, err
    }

    // 4. Get parent version
    parent, err := getCurrentVersion(ctx, tx, repoID)
    if err != nil && err != ErrNoVersion {
        return nil, err
    }

    // 5. Calculate changes (if parent exists)
    var changes []Change
    if parent != nil {
        parentSnapshot, err := loadSnapshot(ctx, tx, parent.Snapshot)
        if err != nil {
            return nil, err
        }
        changes = DiffSnapshots(parentSnapshot, snapshot)
    }

    // 6. Create version object
    version := &Version{
        ID:           uuid.New().String(),
        Hash:         calculateVersionHash(snapshotHash, parent, message),
        RepositoryID: repoID,
        Snapshot:     snapshotHash,
        Parent:       parentHash(parent),
        Tag:          generateTag(parent),
        Message:      message,
        Author:       getAuthorFromContext(ctx),
        Timestamp:    time.Now(),
        Metadata: VersionMetadata{
            ChangeCount:   len(changes),
            ChangeSummary: summarizeChanges(changes),
        },
    }

    // 7. Store version
    if err := storeVersion(ctx, tx, version); err != nil {
        return nil, err
    }

    // 8. Update repository current version
    if err := setCurrentVersion(ctx, tx, repoID, version.Hash); err != nil {
        return nil, err
    }

    // 9. Increment reference counts
    if err := incrementReferences(ctx, tx, snapshot); err != nil {
        return nil, err
    }

    // 10. Commit transaction
    if err := tx.Commit(); err != nil {
        return nil, err
    }

    return version, nil
}
```

### 5.2 Snapshot Capture

```go
func captureSnapshot(ctx context.Context, tx *sql.Tx, repoID string) (*Snapshot, error) {
    snapshot := &Snapshot{
        RepositoryID: repoID,
        CreatedAt:    time.Now(),
    }

    // Capture building structure
    buildingTree, err := captureBuildingTree(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }
    snapshot.BuildingTree = buildingTree.Hash

    // Capture equipment
    equipmentTree, err := captureEquipmentTree(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }
    snapshot.EquipmentTree = equipmentTree.Hash

    // Capture spatial data
    spatialTree, err := captureSpatialTree(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }
    snapshot.SpatialTree = spatialTree.Hash

    // Capture files
    filesTree, err := captureFilesTree(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }
    snapshot.FilesTree = filesTree.Hash

    // Capture operations data
    operationsTree, err := captureOperationsTree(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }
    snapshot.OperationsTree = operationsTree.Hash

    // Calculate snapshot hash
    snapshot.Hash = calculateSnapshotHash(snapshot)

    return snapshot, nil
}
```

### 5.3 Tree Construction

```go
func captureBuildingTree(ctx context.Context, tx *sql.Tx, repoID string) (*Tree, error) {
    tree := &Tree{
        Type:    ObjectTypeTree,
        Entries: []TreeEntry{},
    }

    // Fetch building metadata
    building, err := fetchBuilding(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }

    // Store building as object
    buildingObj := serializeBuilding(building)
    buildingHash, err := storeObject(ctx, tx, buildingObj)
    if err != nil {
        return nil, err
    }

    tree.Entries = append(tree.Entries, TreeEntry{
        Type: ObjectTypeBlob,
        Name: "building-metadata",
        Hash: buildingHash,
        Size: int64(len(buildingObj)),
    })

    // Fetch floors
    floors, err := fetchFloors(ctx, tx, repoID)
    if err != nil {
        return nil, err
    }

    // Store floors as subtree
    floorsTree, err := captureFloorsTree(ctx, tx, floors)
    if err != nil {
        return nil, err
    }
    floorsHash, err := storeObject(ctx, tx, floorsTree)
    if err != nil {
        return nil, err
    }

    tree.Entries = append(tree.Entries, TreeEntry{
        Type: ObjectTypeTree,
        Name: "floors",
        Hash: floorsHash,
        Size: int64(len(floorsTree.Entries)),
    })

    // Similar for rooms...

    // Calculate tree hash
    tree.Hash = calculateTreeHash(tree)

    return tree, nil
}
```

---

## 6. Performance Optimizations

### 6.1 Deduplication

**Content-addressable storage automatically deduplicates:**
- Unchanged files share same hash
- Unchanged subtrees share same hash
- Only store delta between versions

**Example:**
```
Version 1.0: Building (1 MB) + Equipment (500 KB) + Files (10 MB) = 11.5 MB
Version 1.1: Building (1 MB) + Equipment (520 KB) + Files (10 MB) = 11.52 MB
             ↑ same hash      ↑ new hash          ↑ same hash

Storage: 11.5 MB + 20 KB = 11.52 MB (not 23.02 MB)
```

### 6.2 Lazy Loading

**Load only what's needed:**
```go
// Load version (lightweight)
version := loadVersion(versionID)  // ~1 KB

// Load snapshot (medium)
snapshot := loadSnapshot(version.Snapshot)  // ~10 KB

// Load specific tree (on demand)
equipmentTree := loadTree(snapshot.EquipmentTree)  // ~100 KB

// Load specific object (on demand)
equipment := loadObject(equipmentTree.Entries[0].Hash)  // ~1 KB
```

### 6.3 Caching Strategy

```go
// L1: In-memory LRU cache
type VersionCache struct {
    versions  *lru.Cache  // 1000 versions (~10 MB)
    snapshots *lru.Cache  // 500 snapshots (~5 MB)
    trees     *lru.Cache  // 2000 trees (~20 MB)
    objects   *lru.Cache  // 10000 objects (~100 MB)
}

// L2: Redis cache
// - Hot versions (accessed in last hour)
// - Frequently compared snapshots
// - Tree hashes for quick diff

// L3: PostgreSQL + Filesystem
// - Full durability
// - All historical data
```

### 6.4 Diff Optimization

**Progressive Diff:**
```go
// Level 1: Snapshot hash comparison (instant)
if from.Hash == to.Hash {
    return NoDiff  // Identical versions
}

// Level 2: Tree hash comparison (fast, ~10ms)
treeChanges := compareTreeHashes(from, to)
if treeChanges.Empty() {
    return NoDiff  // Metadata changed only
}

// Level 3: Entry-level comparison (medium, ~100ms)
entryChanges := compareTreeEntries(from, to, treeChanges)

// Level 4: Object-level diff (detailed, ~1s)
if detailed {
    objectDiffs := compareObjects(entryChanges)
    return DetailedDiff{objectDiffs}
}

return SummaryDiff{entryChanges}
```

### 6.5 Garbage Collection

**Reference Counting:**
```sql
-- Increment references when version created
UPDATE version_objects
SET ref_count = ref_count + 1
WHERE hash IN (SELECT unnest(referenced_objects));

-- Decrement references when version deleted
UPDATE version_objects
SET ref_count = ref_count - 1
WHERE hash IN (SELECT unnest(referenced_objects));

-- Delete unreferenced objects (run periodically)
DELETE FROM version_objects
WHERE ref_count = 0
  AND created_at < NOW() - INTERVAL '30 days';
```

**Mark-and-Sweep (alternative):**
```go
// Mark phase: Mark all reachable objects
func MarkReachableObjects(ctx context.Context) error {
    // Get all current versions
    versions := getAllVersions(ctx)

    // Mark all objects reachable from versions
    for _, version := range versions {
        snapshot := loadSnapshot(ctx, version.Snapshot)
        markTree(ctx, snapshot.BuildingTree)
        markTree(ctx, snapshot.EquipmentTree)
        // ... mark all trees recursively
    }

    return nil
}

// Sweep phase: Delete unmarked objects
func SweepUnreachableObjects(ctx context.Context) (int, error) {
    count, err := db.Exec(`
        DELETE FROM version_objects
        WHERE marked = false
          AND created_at < NOW() - INTERVAL '30 days'
    `)
    return count, err
}
```

---

## 7. Consequences

### 7.1 Positive ✅

1. **Complete Change History**
   - Every building change is tracked forever
   - Full auditability for compliance
   - Forensic analysis of issues

2. **Efficient Storage**
   - Content-addressable deduplication
   - Incremental snapshots
   - ~10% storage overhead typical case

3. **Fast Comparisons**
   - Tree hashing enables O(log n) diffs
   - No need to scan entire database
   - Parallel tree comparison

4. **Flexible Workflows**
   - Support branching (future)
   - Support tagging (milestones)
   - Support rollback

5. **Git-Like UX**
   - Familiar commands (commit, log, diff, checkout)
   - Understandable by developers
   - Transferable skills

6. **Scalable**
   - Handles buildings with 10K+ equipment
   - Handles 100+ versions efficiently
   - Distributed storage possible (future)

### 7.2 Negative ❌

1. **Complexity**
   - More complex than simple versioning
   - Requires understanding of content-addressable storage
   - **Mitigation**: Hide complexity behind clean API, good docs

2. **Storage Overhead**
   - Need to store all versions
   - Minimum ~5-10% overhead
   - **Mitigation**: Compression, deduplication, garbage collection

3. **Transaction Overhead**
   - Version creation requires full transaction
   - Slight performance penalty (~100-200ms)
   - **Mitigation**: Async version creation, batch commits

4. **No Partial Commits**
   - Must version entire building snapshot
   - Cannot version just equipment (atomic snapshots)
   - **Mitigation**: Fast enough for practical use, clear UX

### 7.3 Neutral ~

1. **Merge Complexity**
   - Manual conflict resolution sometimes required
   - **Tradeoff**: Better than losing data or overwriting

2. **Learning Curve**
   - Users need to understand version control concepts
   - **Tradeoff**: One-time investment, long-term benefit

---

## 8. Alternatives Considered

### Alternative 1: Simple Audit Log

```sql
CREATE TABLE change_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT,
    record_id TEXT,
    operation TEXT,
    old_value JSONB,
    new_value JSONB,
    timestamp TIMESTAMPTZ
);
```

**Rejected because:**
- ❌ Cannot restore to specific version
- ❌ Cannot compare arbitrary versions
- ❌ No deduplication
- ❌ No snapshot concept
- ❌ Grows infinitely without cleanup
- ✅ Simple to implement

### Alternative 2: Temporal Tables (PostgreSQL)

```sql
CREATE TABLE buildings (
    id UUID PRIMARY KEY,
    name TEXT,
    -- ... columns
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ NOT NULL DEFAULT 'infinity'
);

CREATE INDEX ON buildings (id, valid_from, valid_to);
```

**Rejected because:**
- ❌ Row-level versioning only (no snapshot)
- ❌ No hash-based deduplication
- ❌ No tree structure for fast diff
- ❌ No Git-like semantics
- ✅ PostgreSQL native
- ✅ Time-travel queries

### Alternative 3: Event Sourcing

```go
type BuildingEvent struct {
    ID        string
    Type      EventType
    Aggregate string
    Data      json.RawMessage
    Timestamp time.Time
}

// Replay events to reconstruct state
func ReconstructBuilding(events []BuildingEvent) *Building {
    building := &Building{}
    for _, event := range events {
        building.Apply(event)
    }
    return building
}
```

**Rejected because:**
- ❌ Slow to reconstruct from many events
- ❌ No snapshot concept (or need separate snapshots)
- ❌ Complex event replay logic
- ❌ Event schema evolution difficult
- ✅ Perfect audit trail
- ✅ Support time-travel

### Alternative 4: Full Database Snapshots

```bash
pg_dump arxos_building_123 > snapshot-v1.0.0.sql
```

**Rejected because:**
- ❌ Massive storage overhead (no deduplication)
- ❌ Slow to create and restore
- ❌ Cannot diff efficiently
- ❌ No content-addressable storage
- ✅ Simple conceptually
- ✅ Full backup/restore capability

---

## 9. Implementation Plan

### Phase 6B.2: Object Storage (5-7 hours)
- Implement object store (PostgreSQL + filesystem)
- Content-addressable hashing (SHA-256)
- Object serialization/deserialization
- Reference counting
- Unit tests

### Phase 6B.3: Snapshot System (6-8 hours)
- Tree construction algorithms
- Snapshot capture logic
- Merkle tree implementation
- Snapshot storage/retrieval
- Unit + integration tests

### Phase 6B.4: Diff Engine (6-8 hours)
- Tree-level diff algorithm
- Object-level diff algorithms
- Domain-specific diff (building, equipment, spatial)
- Diff output formatting (unified, JSON, semantic)
- Comprehensive tests

### Phase 6B.5: Version Management (4-6 hours)
- Version creation workflow
- Version storage/retrieval
- Version graph traversal
- Parent/child relationships
- Integration tests

### Phase 6B.6: Rollback System (4-6 hours)
- Rollback algorithm
- State restoration
- Validation after rollback
- Transaction management
- Tests

### Phase 6B.7: CLI Implementation (5-7 hours)
- `arx repo commit -m "message"`
- `arx repo status`
- `arx repo log`
- `arx repo diff v1.0.0 v1.1.0`
- `arx repo checkout v1.0.0`
- E2E tests

### Phase 6B.8: Testing & Docs (3-5 hours)
- Integration tests
- E2E workflow tests
- Performance benchmarks
- Documentation
- ADR updates

**Total**: ~35-50 hours for complete implementation

---

## 10. Success Metrics

### Functional Requirements ✅

- [ ] Create versions with commit messages
- [ ] List version history
- [ ] Compare any two versions
- [ ] Show detailed diffs (building, equipment, spatial)
- [ ] Rollback to previous versions
- [ ] Maintain referential integrity
- [ ] Handle concurrent updates

### Performance Requirements ⚡

- [ ] Version creation: < 1 second (typical building)
- [ ] Version listing: < 100ms
- [ ] Diff calculation: < 500ms (two recent versions)
- [ ] Rollback: < 2 seconds
- [ ] Storage overhead: < 20% (with deduplication)

### Quality Requirements 🔍

- [ ] 80%+ test coverage for version control code
- [ ] All core workflows have integration tests
- [ ] E2E tests for CLI commands
- [ ] Performance benchmarks documented
- [ ] Architecture documented in ADR

---

## References

- **Git Internals** - Git object model and content-addressable storage
- **Merkle Trees** - Hash tree structure for efficient comparison
- **Three-Way Merge** - Standard merge algorithm
- **Content-Addressable Storage** - Storage by content hash
- **Event Sourcing** - Alternative pattern for change tracking
- **Temporal Tables** - PostgreSQL native versioning

---

**Author**: ArxOS Engineering Team
**Date**: October 8, 2025
**Status**: Accepted
**Supersedes**: N/A
**Related**: ADR-006 (TUI Data Integration)


