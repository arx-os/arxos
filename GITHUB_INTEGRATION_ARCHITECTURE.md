# ArxOS + GitHub: Technical Architecture & Implementation Plan

**Architecture Design Document**
**Date:** October 22, 2025
**Status:** Technical Design - Ready for Implementation
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Architecture](#core-architecture)
3. [Data Storage Strategy](#data-storage-strategy)
4. [Universal Path System](#universal-path-system)
5. [YAML as Collaboration Layer](#yaml-as-collaboration-layer)
6. [Mobile App Integration](#mobile-app-integration)
7. [SMS/MMS Field Updates](#smsmms-field-updates)
8. [Terminal Rendering Strategy](#terminal-rendering-strategy)
9. [Platform Agnostic Design](#platform-agnostic-design)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Technical Specifications](#technical-specifications)

---

## Executive Summary

### The Solution

ArxOS integrates Git-based collaboration (GitHub/GitLab) with PostGIS spatial database, creating a hybrid architecture where:

- **PostGIS** = Operational database (IFC imports, spatial queries, live sensor data)
- **Git/YAML** = Collaboration layer (version control, pull requests, audit trail)
- **Universal Paths** = The bridge connecting both systems
- **Mobile App** = Field data capture with SMS/MMS for external contributors
- **Terminal** = Live rendering combining Git config + PostGIS data

### Key Decisions

✅ **PostGIS remains primary database** - IFC imports, spatial queries, time-series data
✅ **YAML in Git for collaboration** - PRs, version history, team workflow
✅ **Standard YAML format** - No custom parser needed
✅ **Platform agnostic** - Works with GitHub, GitLab, Bitbucket, local Git
✅ **Building phone numbers** - SMS/MMS for external field updates
✅ **Path-based sync** - Universal paths connect PostGIS ↔ Git ↔ BAS

### Timeline

**MVP: 5-6 weeks**
**Full Implementation: 10-12 weeks**
**Public Launch: 16 weeks**

---

## Core Architecture

### Three-Tier System

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Repository                            │
│              (Collaboration & Version Control)               │
│                                                              │
│  equipment/B1/3/301/HVAC/VAV-301.yml  ← YAML representation │
│  • Configuration snapshots                                   │
│  • Pull requests for changes                                 │
│  • Git history = audit trail                                 │
│  • Team collaboration via PRs                                │
│  • GitHub Actions automation                                 │
└─────────────────────────────────────────────────────────────┘
                              ↕
                    Bidirectional Sync
                  (Path-based reconciliation)
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    PostGIS Database                          │
│              (Operational & Spatial Database)                │
│                                                              │
│  • IFC imports (buildings, floors, rooms, equipment)        │
│  • Spatial queries (millimeter precision)                   │
│  • Path-based queries (/B1/3/301/HVAC/VAV-301)             │
│  • Time-series sensor data                                  │
│  • 3D coordinates and geometry                              │
│  • BAS point mapping                                        │
│  • Live operational state                                   │
│                                                              │
│  THIS REMAINS THE PRIMARY DATABASE ✅                       │
└─────────────────────────────────────────────────────────────┘
                              ↕
                    BACnet/Modbus/Metasys
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   Physical Building (BAS)                    │
│                                                              │
│  • Actual sensors and equipment                             │
│  • Real-time control systems                                │
│  • Building automation systems                              │
└─────────────────────────────────────────────────────────────┘
```

### Access Patterns

```
┌──────────────┐
│  CLI Users   │ → Query PostGIS directly (arx get /B1/3/*)
│ (IT/Facility)│ → Edit YAML in Git → Sync to PostGIS
└──────────────┘

┌──────────────┐
│  Mobile App  │ → Updates PostGIS (scans, photos, notes)
│ (Field Users)│ → SMS/MMS package → GitHub PR
└──────────────┘

┌──────────────┐
│  External    │ → Text to building number
│ Contributors │ → Creates GitHub issue/PR
└──────────────┘

┌──────────────┐
│GitHub Actions│ → Automated workflows
│  (Automation)│ → Hourly sync, alerts, reports
└──────────────┘
```

---

## Data Storage Strategy

### What Lives in PostGIS (Primary Database)

**All operational and spatial data:**

```sql
-- Buildings, floors, rooms (from IFC imports)
buildings (id, name, address, coordinates, ...)
floors (id, building_id, level, name, ...)
rooms (id, floor_id, number, geometry, ...)

-- Equipment with spatial data
equipment (
    id,
    path TEXT,              -- /B1/3/301/HVAC/VAV-301
    name,
    type,
    location_x, location_y, location_z,  -- 3D coordinates
    config JSONB,           -- Current configuration
    ...
)

-- BAS integration
bas_points (path, point_name, system, ...)
bas_systems (building_id, vendor, ...)

-- Sensor data (time-series)
sensor_readings (
    path TEXT,
    timestamp TIMESTAMPTZ,
    value FLOAT,
    ...
)

-- Spatial anchors (from LiDAR/AR scans)
spatial_anchors (
    id,
    path TEXT,
    position GEOMETRY(POINTZ),
    ar_anchor_id TEXT,
    confidence FLOAT,
    created_by TEXT,  -- User who created
    source TEXT,      -- 'lidar', 'ar', 'manual'
    ...
)

-- Version control (Git-like features)
versions, branches, commits, pull_requests, issues
```

**PostGIS Responsibilities:**
- ✅ Store IFC imports with full spatial fidelity
- ✅ Fast path-based queries (already working: 9-36ms!)
- ✅ Spatial queries (PostGIS geometry)
- ✅ Time-series sensor data
- ✅ Real-time operational state
- ✅ Analytics and reporting

### What Lives in Git/YAML (Collaboration Layer)

**Snapshots and configuration:**

```yaml
# equipment/B1/3/301/HVAC/VAV-301.yml

apiVersion: arxos.io/v1
kind: Equipment
metadata:
  name: VAV-301
  path: /B1/3/301/HVAC/VAV-301
  id: eq_vav_301_abc123          # PostGIS ID
  labels:
    system: hvac
    criticality: medium

spec:
  # Configuration (editable via PRs)
  manufacturer: Trane
  model: VAV-500
  serial_number: TRN-2020-12345

  setpoints:
    temperature: 72
    humidity: 50

  schedule: weekday-9to5

  # Spatial data (from PostGIS, read-only in YAML)
  location:
    x: 10.5
    y: 8.2
    z: 2.7
    ar_anchor: anchor_abc123
    confidence: 0.95
    source: lidar_scan

  # BAS integration
  bas:
    system: metasys
    point_name: "VAV301.ZN-T"

status:
  # Current state (synced from PostGIS, read-only)
  operational_state: running
  current_temp: 71.8
  damper_position: 45
  last_updated: 2024-10-21T10:30:00Z

_arxos:
  postgis_id: eq_abc123
  last_synced_from_postgis: 2024-10-21T10:30:00Z
  last_synced_to_postgis: 2024-10-21T09:00:00Z
```

**Git/YAML Responsibilities:**
- ✅ Version history of configurations
- ✅ Pull request workflow for changes
- ✅ Team collaboration
- ✅ Audit trail (who changed what when)
- ✅ GitHub Actions automation
- ✅ Rollback capability

### Data Sync Rules

**PostGIS → Git (Export)**
- **When:** Hourly snapshots via GitHub Action
- **What:** Current equipment configuration + spatial data
- **Why:** Version history, audit trail

**Git → PostGIS (Import)**
- **When:** PR merged to main
- **What:** Updated configuration (setpoints, schedules, etc.)
- **Why:** Apply approved changes to operational database

**Never Synced to Git:**
- ❌ Time-series sensor readings (too frequent)
- ❌ Individual sensor values (changes every 30s)
- ❌ Transient alarms

**Always Synced to Git:**
- ✅ Equipment configuration
- ✅ Spatial coordinates (from scans)
- ✅ Maintenance schedules
- ✅ BAS point mappings

---

## Universal Path System

### The Foundation (Already Built!)

**Path Format:**
```
/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT
```

**Examples:**
```
/B1/3/301/HVAC/VAV-301
/EMPIRE-STATE/ROOF/MER-NORTH/HVAC/AHU-01
/CAMPUS-WEST/1/101/LIGHTS/ZONE-A
```

**Path = Universal Address** (like IP address for equipment)

### Path-Based File Organization in Git

**Path determines Git file location:**

```
PostGIS Path:           /B1/3/301/HVAC/VAV-301
Git File Path:          equipment/B1/3/301/HVAC/VAV-301.yml

PostGIS Path:           /EMPIRE-STATE/ROOF/MER-NORTH/HVAC/AHU-01
Git File Path:          equipment/EMPIRE-STATE/ROOF/MER-NORTH/HVAC/AHU-01.yml
```

**Conversion function:**

```go
func PathToGitFile(universalPath string) string {
    // /B1/3/301/HVAC/VAV-301 → equipment/B1/3/301/HVAC/VAV-301.yml
    return "equipment" + universalPath + ".yml"
}

func GitFileToPath(gitFilePath string) string {
    // equipment/B1/3/301/HVAC/VAV-301.yml → /B1/3/301/HVAC/VAV-301
    path := strings.TrimPrefix(gitFilePath, "equipment")
    path = strings.TrimSuffix(path, ".yml")
    return path
}
```

### Path-Based Sync

**Sync is simple because paths match:**

```go
// PostGIS → Git
func ExportEquipment(eq *domain.Equipment) error {
    yamlData, _ := yaml.Marshal(eq)
    filePath := PathToGitFile(eq.Path)  // Use path!
    return git.WriteFile(filePath, yamlData)
}

// Git → PostGIS
func ImportEquipment(gitFilePath string) error {
    path := GitFileToPath(gitFilePath)  // Extract path!
    yamlData := git.ReadFile(gitFilePath)

    var eq domain.Equipment
    yaml.Unmarshal(yamlData, &eq)

    // Query PostGIS by path (already works!)
    return postgis.UpdateByPath(ctx, path, &eq)
}
```

---

## YAML as Collaboration Layer

### Purpose: Human-Editable Git Representation

**YAML is NOT replacing PostGIS!**

**YAML is:**
- A serialization format for Git storage
- Human-readable representation
- Version-controlled snapshots
- PR-able configuration

**YAML is NOT:**
- The primary database
- Real-time query target
- Spatial query engine

### YAML Structure (Standard Format)

```yaml
# Kubernetes-style manifest

apiVersion: arxos.io/v1
kind: Equipment

metadata:
  name: VAV-301
  path: /B1/3/301/HVAC/VAV-301
  id: eq_abc123                    # PostGIS UUID

  labels:                          # GitHub-friendly labels
    system: hvac
    type: vav
    criticality: medium
    building: B1
    floor: "3"
    room: "301"

spec:
  # Configuration (editable via PR)
  manufacturer: Trane
  model: VAV-500
  serial_number: TRN-2020-12345
  install_date: 2020-03-15

  capacity:
    cfm: 1000
    heating_btuh: 15000

  setpoints:
    temperature: 72
    humidity: 50

  schedule: weekday-9to5

  location:
    x: 10.5        # From LiDAR/IFC import
    y: 8.2
    z: 2.7
    ar_anchor: anchor_abc123
    confidence: 0.95
    source: lidar_scan

  bas:
    system: metasys
    network_address: "10.20.30.100"
    point_name: "VAV301.ZN-T"

status:
  # Current state (synced from PostGIS hourly)
  operational_state: running
  health: healthy
  current_values:
    temperature: 71.8
    humidity: 48
    damper_position: 45
  last_updated: 2024-10-21T10:30:00Z

maintenance:
  schedule: quarterly
  last_pm: 2024-09-15
  next_pm: 2024-12-15
  vendor: ACME HVAC

_arxos:
  # Sync metadata
  postgis_id: eq_abc123
  postgis_sync:
    last_export: 2024-10-21T10:30:00Z
    last_import: 2024-10-21T09:00:00Z
  git_commit: a3f2b1c
```

### Implementation (Minimal Effort)

**Already have:**
- ✅ `gopkg.in/yaml.v3` in go.mod
- ✅ Domain models (`domain.Equipment`)

**Need to add:**
```go
// Just add YAML tags to existing structs!

type Equipment struct {
    ID         types.ID  `json:"id" yaml:"id" db:"id"`
    Path       string    `json:"path" yaml:"path" db:"path"`
    Name       string    `json:"name" yaml:"name" db:"name"`
    Type       string    `json:"type" yaml:"type" db:"equipment_type"`
    // ... existing fields, just add yaml tags
}

// Marshal/unmarshal (trivial)
func EquipmentToYAML(eq *domain.Equipment) ([]byte, error) {
    return yaml.Marshal(eq)
}

func YAMLToEquipment(data []byte) (*domain.Equipment, error) {
    var eq domain.Equipment
    err := yaml.Unmarshal(data, &eq)
    return &eq, err
}
```

**Engineering effort: 1 week** to add YAML serialization.

---

## Mobile App Integration

### Mobile App Workflow

**Field user in app:**

```
1. Scan equipment QR code
   ↓
2. Options:
   a) LiDAR scan room/equipment
   b) Take photo
   c) Add notes/status update
   d) Record maintenance
   ↓
3. App processes on-device:
   - LiDAR scan → Extract spatial anchors
   - Photo → Compress/upload
   - Notes → Text data
   ↓
4. App creates update package
   ↓
5. Send options:
   a) Direct upload (WiFi/cellular) → PostGIS API
   b) SMS/MMS package → Building phone number
   c) Save locally, sync later
```

### LiDAR Scan Processing (On-Device)

**What mobile app extracts from LiDAR scan:**

```typescript
// Mobile app (React Native)
interface SpatialScanResult {
  room_path: string;              // /B1/3/301
  dimensions: {
    width: number;                // 10.5 meters
    height: number;               // 8.2 meters
    depth: number;                // 2.7 meters
  };
  equipment_detected: Array<{
    estimated_path: string;       // /B1/3/301/HVAC/VAV-301
    position: {x: number, y: number, z: number};
    ar_anchor_id: string;
    confidence: number;           // 0.0-1.0
  }>;
  scan_metadata: {
    timestamp: Date;
    device: string;
    user_id: string;
  };
}

// Compress to YAML
const package = {
  type: 'spatial_scan',
  path: '/B1/3/301',
  data: scanResult
};

// Serialize and compress
const yaml = YAML.stringify(package);      // ~500 bytes
const compressed = gzip(yaml);             // ~200 bytes
const encoded = base64(compressed);        // ~270 chars
const payload = `ARXOS:spatial:${encoded}`;
```

**Key points:**
- ❌ NOT sending full .ply file (too large: 50-500MB)
- ✅ Sending extracted spatial metadata (200-500 bytes)
- ✅ Equipment positions, room dimensions, AR anchors
- ✅ Fits in MMS (300KB limit, we only need <1KB)

### Package Size Analysis

**Single equipment update:**
```yaml
path: /B1/3/301/HVAC/VAV-301
position: {x: 10.5, y: 8.2, z: 2.7}
ar_anchor: anchor_abc123
notes: "Filter needs replacement"
```
- Raw: ~150 bytes
- Compressed: ~60 bytes
- Base64: ~80 chars
- ✅ **Fits in SMS** (160 char limit)

**Room scan (5 equipment):**
```yaml
room: /B1/3/301
dimensions: {width: 10.5, height: 8.2, depth: 2.7}
equipment:
  - {path: /B1/3/301/HVAC/VAV-301, pos: [10.5, 8.2, 2.7]}
  - {path: /B1/3/301/LIGHTS/ZONE-A, pos: [5.2, 4.1, 2.8]}
  # ... 3 more
```
- Raw: ~800 bytes
- Compressed: ~300 bytes
- Base64: ~400 chars
- ✅ **Fits in MMS** (300KB limit)

**Floor scan (20 rooms, 100 equipment):**
```yaml
floor: /B1/3
rooms: [20 rooms with dimensions]
equipment: [100 equipment with positions]
```
- Raw: ~15KB
- Compressed: ~5KB
- Base64: ~7KB
- ✅ **Fits in MMS** (300KB limit)

**Whole building scan:**
- Raw: ~500KB - 2MB
- Compressed: ~200KB - 800KB
- ❌ **Too large for MMS**
- **Solution:** App uploads directly via API when on WiFi/cellular data

### Upload Strategy

**Decision tree:**

```
Scan size < 1KB:
└─→ SMS (base64 encoded)

Scan size < 100KB:
└─→ MMS (compressed YAML)

Scan size > 100KB:
└─→ Direct API upload (cellular data/WiFi)
    └─→ OR save locally, prompt user "Upload when on WiFi?"
```

---

## SMS/MMS Field Updates

### Building Phone Number System

**Each building gets unique phone number:**

```
Building Naming Convention:
ARXOS-NA-US-NY-NYC-0001  →  Phone: +1-212-ARXOS-01
ARXOS-NA-US-CA-SFO-0042  →  Phone: +1-415-ARXOS-42

Or simpler:
Empire State Building    →  Phone: +1-844-278-6701
                               (844-ARXOS-01)
```

**Phone number registry:**

```sql
-- PostGIS table
CREATE TABLE building_phone_numbers (
    building_id UUID PRIMARY KEY,
    phone_number TEXT UNIQUE,
    building_name TEXT,
    github_repo TEXT,
    created_at TIMESTAMPTZ
);

-- Example:
+1-844-278-6701 → github.com/acme/empire-state-building
```

### External Contributor Workflow

**Use Case: Contractor notices issue, no ArxOS access**

```
1. Contractor texts building number:
   To: +1-844-278-6701
   Message: "AHU-01 making loud noise, vibration in north wing"

2. Twilio webhook → ArxOS SMS Gateway

3. Gateway processes:
   - Parse building number → Lookup repo
   - Parse message for equipment name/path
   - Extract details

4. Creates GitHub issue:
   Title: "Field Report: AHU-01 vibration"
   Body: "External report via SMS
          From: +1-555-123-4567
          Message: AHU-01 making loud noise, vibration in north wing
          Time: 2024-10-21 10:30 AM"
   Labels: external-report, hvac, needs-triage

5. Facilities team notified
   - Reviews issue
   - Assigns to technician
   - Creates work order
```

**Benefits:**
- ✅ Anyone can report (no account needed)
- ✅ Works in basement (SMS works anywhere with cellular)
- ✅ No app required (basic text message)
- ✅ Auto-routes to correct building repo
- ✅ Creates audit trail in GitHub

### Mobile App Field Update Workflow

**Use Case: ArxOS mobile user scans equipment**

```
1. User scans equipment in mobile app:
   - LiDAR scans room
   - App extracts spatial data
   - User adds notes

2. App creates package:
   {
     type: 'spatial_update',
     path: '/B1/3/301/HVAC/VAV-301',
     spatial: {x: 10.5, y: 8.2, z: 2.7},
     ar_anchor: 'anchor_abc123',
     notes: 'Filter replacement needed',
     photo_ref: 'upload_xyz789'
   }
   → Compress to ~200-500 bytes

3. Send options:

   Option A (Has WiFi/Data):
   └─→ Direct API call to ArxOS backend
       └─→ Updates PostGIS immediately
       └─→ GitHub Action syncs to Git hourly

   Option B (Offline/Cellular only):
   └─→ Text package to building number
       └─→ SMS gateway → GitHub PR
       └─→ Approval → Updates PostGIS

   Option C (No connectivity):
   └─→ Save to local SQLite
       └─→ Sync when connectivity restored
```

### SMS Package Format

**Compact YAML for text transmission:**

```yaml
# Uncompressed (human-readable)
v: 1
t: spatial
p: /B1/3/301/HVAC/VAV-301
s: {x: 10.5, y: 8.2, z: 2.7}
a: anchor_abc123
n: Filter replacement needed

# Compressed + base64
ARXOS:v1:eJyDVshNzMlPTFXITSwuLcpMUbBVSM7PLShKLS5O
```

**Size: ~80-150 characters** (fits in SMS)

### Gateway Implementation

```go
// SMS webhook handler
func HandleSMSWebhook(w http.ResponseWriter, r *http.Request) {
    // Parse Twilio webhook
    from := r.FormValue("From")
    to := r.FormValue("To")
    body := r.FormValue("Body")

    // Lookup building by phone number
    building := lookupBuildingByPhone(to)

    // Parse package
    if strings.HasPrefix(body, "ARXOS:") {
        // Decode compressed package
        pkg := decodePackage(body)

        // Create GitHub PR
        pr := createPRFromPackage(building.GitHubRepo, pkg)

        // Send confirmation SMS
        sendSMS(from, fmt.Sprintf("✅ Update received for %s. PR #%d created.",
            building.Name, pr.Number))
    } else {
        // Plain text message → Create issue
        createIssue(building.GitHubRepo, from, body)
    }
}
```

---

## Terminal Rendering Strategy

### Rendering Decision Tree

```go
func RenderBuilding(ctx context.Context, buildingID string) error {
    // Always query PostGIS for data
    equipment := postgis.FindByPath(ctx, fmt.Sprintf("/%s/*", buildingID))

    // Check what data is available
    hasSpatial := checkSpatialData(equipment)

    if hasSpatial {
        // Fancy: ASCII floor plan with positioned equipment
        return renderFloorPlan(equipment)
    } else {
        // Simple: Tree view based on paths
        return renderPathTree(equipment)
    }
}

func checkSpatialData(equipment []*domain.Equipment) bool {
    // If any equipment has x,y,z coordinates
    for _, eq := range equipment {
        if eq.Location != nil &&
           eq.Location.X != 0 &&
           eq.Location.Y != 0 {
            return true
        }
    }
    return false
}
```

### Simple Rendering (No Spatial Data)

**Path-based tree view:**

```bash
$ arx status B1

Building B1
├── Floor 1
│   ├── Room 101
│   │   ├── /B1/1/101/HVAC/VAV-101     ✅ 72.1°F
│   │   └── /B1/1/101/LIGHTS/ZONE-A    ✅ ON (75%)
│   └── Room 102
│       └── /B1/1/102/HVAC/VAV-102     ✅ 71.8°F
├── Floor 3
│   └── Room 301
│       └── /B1/3/301/HVAC/VAV-301     ⚠️  67.5°F (high)
└── ROOF
    └── MER-NORTH
        ├── /B1/ROOF/MER-NORTH/HVAC/AHU-01  ✅ 55.2°F
        └── /B1/ROOF/MER-NORTH/HVAC/AHU-02  ⚠️  67.5°F

Total: 6 equipment | ✅ 5 healthy | ⚠️  1 warning
```

**Data source:** PostGIS queries using existing path system.

### Spatial Rendering (With IFC/LiDAR Data)

**ASCII floor plan (when coordinates available):**

```bash
$ arx render --floor 3

Floor 3: Third Floor (10,500 sqft)
┌──────────────────────────────────────────────────────┐
│                                                       │
│  ┌─────────────┐              ┌──────────────┐      │
│  │  Room 301   │              │  Room 302    │      │
│  │  Conference │              │  Office      │      │
│  │             │              │              │      │
│  │  🌡️  VAV-301 │              │  🌡️  VAV-302  │      │
│  │  71.8°F ✅  │              │  70.5°F ✅   │      │
│  │  [10.5,8.2] │              │  [25.3,8.1]  │      │
│  └─────────────┘              └──────────────┘      │
│                                                       │
│  ┌──────────────────────────────┐                   │
│  │  Room 303 - Open Office      │                   │
│  │                               │                   │
│  │  🌡️  VAV-303   🌡️  VAV-304   │                   │
│  │  72.1°F ✅    71.5°F ✅      │                   │
│  └──────────────────────────────┘                   │
└──────────────────────────────────────────────────────┘

Data: PostGIS (coordinates from IFC import + LiDAR scans)
Last Update: 2 seconds ago
```

**Data source:** PostGIS spatial queries with x,y,z coordinates.

### Implementation (Uses Existing TUI)

```go
// internal/tui/ - Already exists!
// Just enhance to query PostGIS and render based on available data

type BuildingRenderer struct {
    postgis *PostGIS
}

func (r *BuildingRenderer) Render(ctx context.Context, buildingID string) {
    // Query PostGIS
    equipment := r.postgis.GetEquipmentByBuilding(buildingID)

    // Detect rendering mode
    if hasCoordinates(equipment) {
        r.renderSpatial(equipment)    // ASCII floor plan
    } else {
        r.renderTree(equipment)        // Simple tree
    }
}
```

**Engineering effort: 1 week** to enhance existing TUI.

---

## Platform Agnostic Design

### Git Provider Abstraction

**Interface (works with any Git platform):**

```go
// internal/infrastructure/git/provider.go

type GitProvider interface {
    // Repository operations
    Clone(url string, dest string) error
    Pull() error
    Push() error

    // File operations
    GetFile(path string) ([]byte, error)
    WriteFile(path string, data []byte) error
    ListFiles(prefix string) ([]string, error)

    // Commit operations
    Commit(message string) error

    // Branch operations
    CreateBranch(name string) error
    CheckoutBranch(name string) error
    MergeBranch(source, target string) error

    // Platform-specific (optional)
    CreatePR(title, body string) error          // GitHub/GitLab
    CreateIssue(title, body string) error       // GitHub/GitLab
    TriggerWorkflow(name string) error          // GitHub Actions
}
```

### Implementations

```go
// GitHub
type GitHubProvider struct {
    client *github.Client
    repo   *git.Repository
}

// GitLab
type GitLabProvider struct {
    client *gitlab.Client
    repo   *git.Repository
}

// Gitea (self-hosted)
type GiteaProvider struct {
    client *gitea.Client
    repo   *git.Repository
}

// Local Git (no platform)
type LocalGitProvider struct {
    repo *git.Repository
}
```

### Configuration

```yaml
# .arxos/config.yml

git:
  provider: github  # or gitlab, gitea, local

  github:
    org: acme-properties
    repo: empire-state-building
    token: ${GITHUB_TOKEN}

  # Alternative: GitLab
  gitlab:
    group: acme-properties
    project: empire-state-building
    token: ${GITLAB_TOKEN}
    instance: https://gitlab.com
```

**Platform detection:**

```go
func DetectProvider(repoURL string) GitProvider {
    switch {
    case strings.Contains(repoURL, "github.com"):
        return NewGitHubProvider()
    case strings.Contains(repoURL, "gitlab.com"):
        return NewGitLabProvider()
    default:
        return NewLocalGitProvider()
    }
}
```

---

## Implementation Roadmap

### Phase 1: Core Git Integration (5-6 weeks)

**Week 1: YAML Serialization**
- Add YAML tags to domain models
- Marshal/unmarshal functions
- Path ↔ FilePath conversion
- Testing

**Week 2-3: Git Provider**
- Git provider interface
- GitHub implementation (use `google/go-github`)
- GitLab implementation (use `xanzy/go-gitlab`)
- Local Git implementation (use `go-git/go-git`)
- Tests

**Week 4-5: Sync Commands**
```bash
arx export --to-git              # PostGIS → Git
arx import --from-git            # Git → PostGIS
arx sync --bidirectional         # Both directions
```

**Week 6: Testing & Polish**
- Integration tests
- Documentation
- Examples

**Deliverable:** Working Git sync with PostGIS

### Phase 2: Mobile Field Updates (3-4 weeks)

**Week 7: Mobile App Updates**
- LiDAR scan processing
- Spatial data extraction
- Package compression
- YAML generation

**Week 8: SMS Gateway**
- Twilio integration
- Building phone number registry
- Package decode/encode
- GitHub PR/issue creation

**Week 9-10: Integration**
- Mobile → SMS → GitHub workflow
- Direct API upload option
- Offline queue
- Testing

**Deliverable:** Field updates via mobile + SMS

### Phase 3: GitHub Actions (2-3 weeks)

**Week 11: Core Actions**
```yaml
arxos/sync-action@v1         # Hourly PostGIS → Git sync
arxos/alert-action@v1        # Equipment monitoring
arxos/validate-action@v1     # PR validation
```

**Week 12-13: Documentation & Publishing**
- Action documentation
- GitHub Marketplace publishing
- Example workflows
- Video tutorials

**Deliverable:** Published GitHub Actions

### Phase 4: Enhanced Features (2-3 weeks)

**Week 14: Enhanced Terminal**
- Spatial rendering (if coordinates available)
- Live data refresh
- Interactive navigation

**Week 15-16: Polish**
- Documentation
- Examples
- Case studies
- Launch preparation

**Total: 16 weeks (4 months) for complete implementation**

---

## Technical Specifications

### YAML Schema

```yaml
# Minimal equipment YAML
path: /B1/3/301/HVAC/VAV-301      # Required
name: VAV-301                      # Required
type: hvac                         # Required

# Optional fields
manufacturer: Trane
model: VAV-500
config: {...}
location: {x, y, z}
bas: {...}
status: {...}
```

### SMS Package Protocol

**Format:** `ARXOS:{version}:{type}:{payload}`

**Examples:**
```
ARXOS:v1:spatial:eJyD8f9...        # Spatial scan
ARXOS:v1:status:eJyD8f9...         # Status update
ARXOS:v1:maintenance:eJyD8f9...    # Maintenance note
```

**Payload encoding:**
```
YAML → gzip → base64
```

**Maximum sizes:**
- SMS: 160 chars (~120 bytes data)
- MMS: 300KB (~220KB data)

### API Endpoints

**New endpoints needed:**

```
POST /api/v1/git/sync/export       # PostGIS → Git
POST /api/v1/git/sync/import       # Git → PostGIS
POST /api/v1/sms/webhook           # Twilio webhook
POST /api/v1/mobile/field-update   # Direct mobile upload
GET  /api/v1/buildings/{id}/phone  # Get building phone number
```

### GitHub Actions Spec

**Sync action (`arxos/sync-action@v1`):**

```yaml
# .github/workflows/sync.yml
- uses: arxos/sync-action@v1
  with:
    postgis_url: ${{ secrets.POSTGIS_URL }}
    direction: export  # or import, bidirectional
    interval: hourly
```

---

## Architecture Patterns

### Kubernetes-Style Reconciliation

```go
type Reconciler struct {
    git     GitProvider
    postgis *PostGIS
    bas     *BASClient
}

// Continuous reconciliation loop
func (r *Reconciler) ReconcileLoop(ctx context.Context) {
    ticker := time.NewTicker(5 * time.Minute)

    for {
        select {
        case <-ticker.C:
            r.reconcileAll(ctx)
        case <-ctx.Done():
            return
        }
    }
}

func (r *Reconciler) reconcileAll(ctx context.Context) {
    // 1. Get desired state from Git
    desiredState := r.git.LoadAll()

    // 2. Get actual state from PostGIS
    actualState := r.postgis.GetAll()

    // 3. Reconcile differences
    for path, desired := range desiredState {
        actual := actualState[path]

        if !reflect.DeepEqual(desired.Config, actual.Config) {
            // Apply changes
            r.postgis.Update(path, desired)
            r.bas.ApplyConfig(path, desired.Config)
        }
    }
}
```

### Event-Driven Updates

```go
// Watch for Git commits (webhook)
github.OnCommit(func(commit) {
    // Get changed files
    for _, file := range commit.ChangedFiles {
        if strings.HasPrefix(file, "equipment/") {
            path := GitFileToPath(file)

            // Load YAML
            yamlData := git.ReadFile(file)
            eq := parseYAML(yamlData)

            // Update PostGIS
            postgis.UpdateByPath(ctx, path, eq)

            // Apply to BAS if config changed
            if configChanged(eq) {
                bas.ApplyConfig(eq)
            }
        }
    }
})
```

---

## Complete System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      GitHub Repository                        │
│  equipment/B1/3/301/HVAC/VAV-301.yml (YAML files)           │
│  • Version control via Git                                   │
│  • PRs for configuration changes                             │
│  • GitHub Actions for automation                             │
│  • Issues for work orders                                    │
│  • Projects for planning                                     │
└──────────────────────────────────────────────────────────────┘
        ↕ Hourly sync                    ↕ PR merges
        ↕ GitHub Actions                 ↕ Webhook triggers
┌──────────────────────────────────────────────────────────────┐
│                      PostGIS Database                         │
│  • IFC imports (spatial data preserved)                      │
│  • Path-based queries (fast, indexed)                        │
│  • Time-series sensor data                                   │
│  • Spatial coordinates (x,y,z)                               │
│  • Current operational state                                 │
│  • Equipment cache for fast queries                          │
└──────────────────────────────────────────────────────────────┘
        ↕ BACnet/Modbus              ↕ API updates
        ↕ Live sensors               ↕ Mobile app writes
┌──────────────────────────────────────────────────────────────┐
│                    Physical Building (BAS)                    │
│  • Actual sensors and equipment                              │
│  • Real-time control systems                                 │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       User Interfaces                         │
├──────────────────────────────────────────────────────────────┤
│  CLI (IT/Facility)                                           │
│  • Query PostGIS: arx get /B1/3/*                           │
│  • Edit Git YAML: vim equipment/...                          │
│  • Apply changes: arx apply                                  │
│  • View status: arx status (PostGIS data)                   │
├──────────────────────────────────────────────────────────────┤
│  Mobile App (Field Users)                                    │
│  • Scan equipment (QR/AR)                                    │
│  • LiDAR spatial capture                                     │
│  • Updates → PostGIS API                                     │
│  • Package → SMS/MMS → GitHub PR                            │
├──────────────────────────────────────────────────────────────┤
│  SMS/MMS (External Contributors)                             │
│  • Text to building phone number                             │
│  • Compressed package or plain text                          │
│  • Creates GitHub issue/PR                                   │
│  • No account required                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow Examples

### Example 1: IFC Import → Git Export

```bash
# 1. Import IFC to PostGIS (already works!)
arx import building.ifc --repository repo-123

# PostGIS now has:
# - 1 building
# - 58 equipment items
# - Spatial coordinates
# - Path: /B1/3/301/HVAC/VAV-301

# 2. Export to Git
arx export --to-git github.com/acme/building

# Creates Git repo with:
# - equipment/B1/3/301/HVAC/VAV-301.yml
# - ... (57 more YAML files)
# - Each YAML has spatial data from IFC
```

### Example 2: Configuration Change (Git → PostGIS → BAS)

```bash
# 1. Engineer clones repo
git clone github.com/acme/building
cd building

# 2. Edit configuration
vim equipment/B1/3/301/HVAC/VAV-301.yml
# Change: setpoints.temperature: 70 → 72

# 3. Create PR
git checkout -b update-vav-301
git commit -m "Increase VAV-301 setpoint"
git push
gh pr create --title "Comfort: Increase VAV-301 temp"

# 4. PR approved and merged

# 5. GitHub Action or webhook triggers:
arx sync --from-git

# 6. ArxOS:
# - Reads changed YAML
# - Updates PostGIS equipment table
# - Applies to BAS (sends BACnet command)
# - BAS updates physical damper

# 7. Verify
arx get /B1/3/301/HVAC/VAV-301
# Returns: setpoint=72, actual_temp=71.8 (from PostGIS)
```

### Example 3: Mobile LiDAR Scan → PostGIS → Git

```bash
# 1. Field user scans room with mobile app
# - LiDAR captures room + equipment positions
# - App extracts spatial metadata:
{
  room_path: "/B1/3/301",
  dimensions: {width: 10.5, height: 8.2, depth: 2.7},
  equipment: [
    {path: "/B1/3/301/HVAC/VAV-301", position: {x: 10.5, y: 8.2, z: 2.7}},
    {path: "/B1/3/301/LIGHTS/ZONE-A", position: {x: 5.2, y: 4.1, z: 2.8}}
  ]
}

# 2. App sends package (two options):

# Option A: Direct API (has WiFi/data)
POST /api/v1/mobile/spatial-update
→ Updates PostGIS immediately
→ GitHub Action syncs to Git hourly

# Option B: SMS/MMS (no WiFi)
Compress to ~500 bytes
→ Text to +1-844-BUILDING-01
→ Gateway creates PR
→ Approval → Updates PostGIS

# 3. PostGIS now has spatial coordinates

# 4. Terminal rendering now works:
arx render --floor 3
# Shows ASCII floor plan with equipment positions
```

### Example 4: External Contractor Report

```bash
# 1. Contractor (no ArxOS account) notices issue
# Texts to building phone number:

To: +1-844-278-6701 (Empire State Building)
Message: "AHU-01 vibrating loudly, possible bearing failure"

# 2. SMS Gateway:
# - Looks up building by phone number
# - Finds repo: github.com/acme/empire-state
# - Searches PostGIS for "AHU-01"
# - Finds path: /B1/ROOF/MER-NORTH/HVAC/AHU-01

# 3. Creates GitHub Issue:
Title: "Field Report: AHU-01 vibration"
Body: "External report via SMS
       From: +1-555-123-4567 (Contractor)
       Equipment: /B1/ROOF/MER-NORTH/HVAC/AHU-01
       Message: AHU-01 vibrating loudly, possible bearing failure
       Time: 2024-10-21 10:30 AM"
Labels: external-report, hvac, needs-triage, urgent
Assignees: @facilities-team

# 4. Facilities manager gets notified
# - Reviews issue
# - Creates work order
# - Assigns technician
# - All tracked in GitHub
```

---

## System Integration Points

### PostGIS ↔ Git Sync

**Export (PostGIS → Git):**

```go
func ExportToGit(ctx context.Context) error {
    // 1. Query all equipment from PostGIS (using existing queries!)
    equipment := postgis.FindByPath(ctx, "/*/*/*/*/*/*")

    // 2. For each equipment
    for _, eq := range equipment {
        // Generate YAML
        yamlData, _ := yaml.Marshal(eq)

        // Path determines file location
        filePath := PathToGitFile(eq.Path)
        // /B1/3/301/HVAC/VAV-301 → equipment/B1/3/301/HVAC/VAV-301.yml

        // Write to Git
        git.WriteFile(filePath, yamlData)
    }

    // 3. Commit all changes
    git.Commit(fmt.Sprintf("Sync from PostGIS: %s", time.Now()))

    // 4. Push to remote
    return git.Push()
}
```

**Import (Git → PostGIS):**

```go
func ImportFromGit(ctx context.Context, changedFiles []string) error {
    for _, filePath := range changedFiles {
        // 1. Extract path from filename
        path := GitFileToPath(filePath)
        // equipment/B1/3/301/HVAC/VAV-301.yml → /B1/3/301/HVAC/VAV-301

        // 2. Read YAML from Git
        yamlData, _ := git.ReadFile(filePath)

        // 3. Parse to Equipment
        var eq domain.Equipment
        yaml.Unmarshal(yamlData, &eq)

        // 4. Update PostGIS (using existing repository!)
        postgis.UpdateByPath(ctx, path, &eq)
    }
}
```

### Mobile App ↔ PostGIS

**Direct API update:**

```typescript
// Mobile app (React Native)

async function sendSpatialUpdate(scanData: SpatialScan) {
  const package = {
    room_path: scanData.roomPath,
    dimensions: scanData.dimensions,
    equipment: scanData.equipment.map(eq => ({
      path: eq.path,
      position: eq.position,
      ar_anchor: eq.arAnchor,
      confidence: eq.confidence
    }))
  };

  // Send to ArxOS API
  const response = await fetch(`${API_URL}/mobile/spatial-update`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(package)
  });

  // PostGIS updates happen in backend
  // Git sync happens hourly via GitHub Action
}
```

**Go backend handler:**

```go
func HandleMobileSpatialUpdate(w http.ResponseWriter, r *http.Request) {
    var pkg SpatialUpdatePackage
    json.NewDecoder(r.Body).Decode(&pkg)

    // Update PostGIS with spatial data
    for _, eq := range pkg.Equipment {
        postgis.UpdateLocation(ctx, eq.Path, eq.Position)
        postgis.UpdateARanchor(ctx, eq.Path, eq.ARanchor, eq.Confidence)
    }

    // Update room dimensions
    postgis.UpdateRoomDimensions(ctx, pkg.RoomPath, pkg.Dimensions)

    // Log the update
    postgis.CreateAuditLog(ctx, "mobile_scan", pkg)

    json.NewEncoder(w).Encode(map[string]string{
        "status": "success",
        "message": "Spatial data updated"
    })
}
```

### SMS Gateway ↔ GitHub

```go
// Twilio webhook handler
func HandleSMSWebhook(w http.ResponseWriter, r *http.Request) {
    from := r.FormValue("From")
    to := r.FormValue("To")
    body := r.FormValue("Body")

    // Lookup building by phone number
    building := postgis.GetBuildingByPhone(to)

    if strings.HasPrefix(body, "ARXOS:") {
        // Compressed package from mobile app
        pkg := decodeARXOSPackage(body)

        // Create PR with spatial data
        pr := github.CreatePR(building.GitHubRepo, PullRequest{
            Title: fmt.Sprintf("Mobile Field Update: %s", pkg.Path),
            Body: formatPackageAsPR(pkg),
            Labels: []string{"mobile-update", "spatial-data"},
        })

        // On PR merge → Update PostGIS

    } else {
        // Plain text message → Create issue
        issue := github.CreateIssue(building.GitHubRepo, Issue{
            Title: fmt.Sprintf("Field Report from %s", from),
            Body: body,
            Labels: []string{"external-report", "needs-triage"},
        })
    }

    // Send confirmation
    sendSMS(from, "✅ Update received")
}
```

---

## Key Technical Decisions

### 1. PostGIS is Primary, Git is Secondary

**PostGIS:**
- All IFC imports
- Spatial queries
- Time-series data
- Real-time state
- Fast queries (milliseconds)

**Git:**
- Configuration snapshots
- Version history
- Team collaboration
- Audit trail

### 2. Standard YAML (Not Custom Format)

**Why:**
- Industry standard
- Already have yaml.v3 library
- Everyone knows YAML
- Excellent tooling
- Zero parser development

**Engineering: 1 week** vs 7-10 weeks for custom format

### 3. Platform Agnostic (Abstract Git)

**Support:**
- GitHub
- GitLab
- Bitbucket
- Gitea (self-hosted)
- Local Git

**Interface:**
```go
type GitProvider interface {
    Clone, Pull, Push, Commit
    CreatePR, CreateIssue
}
```

### 4. Path-Based Everything

**Paths connect all systems:**
- PostGIS queries: `WHERE path = '/B1/3/301/HVAC/VAV-301'`
- Git files: `equipment/B1/3/301/HVAC/VAV-301.yml`
- Mobile updates: `{path: '/B1/3/301/HVAC/VAV-301', ...}`
- SMS packages: Include path for routing
- Terminal display: Organized by path hierarchy

**Paths are the universal key!**

### 5. Building Phone Numbers

**Each building gets unique phone number:**

```sql
CREATE TABLE building_phone_numbers (
    building_id UUID PRIMARY KEY,
    phone_number TEXT UNIQUE,         -- +1-844-278-6701
    building_name TEXT,                -- Empire State Building
    github_repo TEXT,                  -- acme/empire-state
    created_at TIMESTAMPTZ
);
```

**Purpose:**
- External contributor access
- Field user updates without WiFi
- Universal building contact point

### 6. Mobile Package Format

**Compressed YAML for SMS/MMS:**

```yaml
# Uncompressed
v: 1
t: spatial
p: /B1/3/301/HVAC/VAV-301
s: {x: 10.5, y: 8.2, z: 2.7}
a: anchor_abc123
c: 0.95

# Compressed
ARXOS:v1:spatial:eJyD8f9A2...
```

**Size limits:**
- Single equipment: ~80 chars (SMS)
- Room scan: ~400 chars (MMS)
- Floor scan: ~5-10KB (MMS)
- Building scan: Upload via API (too large for MMS)

---

## Implementation Components

### New Packages to Build

```
internal/infrastructure/git/
├── provider.go          # Git provider interface
├── github.go           # GitHub implementation
├── gitlab.go           # GitLab implementation
├── local.go            # Local Git
└── sync.go             # Sync orchestration

internal/serialization/
├── equipment.go        # Equipment ↔ YAML
├── building.go         # Building ↔ YAML
├── path.go            # Path ↔ FilePath conversion
└── compress.go        # Package compression for SMS

internal/sms/
├── gateway.go         # SMS/MMS webhook handler
├── phone.go           # Building phone number registry
├── package.go         # Package encode/decode
└── twilio.go          # Twilio integration

internal/cli/commands/git/
├── export.go          # arx export --to-git
├── import.go          # arx import --from-git
├── sync.go            # arx sync
└── init.go            # arx init --github
```

### Reused Existing Components

**Already working, no changes needed:**

```
✅ pkg/naming/path.go              # Path system
✅ internal/domain/entities.go     # Domain models
✅ internal/infrastructure/postgis/ # PostGIS repositories
✅ internal/usecase/integration/   # IFC import, BAS integration
✅ internal/tui/                   # Terminal UI (Bubble Tea)
✅ mobile/src/services/            # Mobile app services
```

**Estimated code reuse: 80-85%**

---

## Deployment Architecture

### Free Tier (Git Only)

```
User setup:
├── GitHub account (free)
├── ArxOS CLI (open source)
└── Building repository (YAML files)

No infrastructure costs!
```

**Capabilities:**
- Configuration management
- Version control
- Team collaboration
- Basic queries (read YAML files)

**Limitations:**
- No live sensor data
- No spatial queries
- No real-time monitoring
- No IFC imports

### Paid Tier (Git + PostGIS)

```
User setup:
├── GitHub account (free or paid)
├── ArxOS CLI (open source)
├── Building repository (YAML files)
└── PostGIS database (ArxOS managed or self-hosted)

ArxOS revenue: $29-299/building/month
```

**Capabilities:**
- Everything from free tier
- ✅ IFC imports with spatial data
- ✅ Live sensor data
- ✅ Spatial queries
- ✅ Real-time monitoring
- ✅ Time-series analytics
- ✅ LiDAR scan processing

### Enterprise Tier (Git + PostGIS + Premium)

```
User setup:
├── GitHub Enterprise
├── ArxOS CLI + Enterprise features
├── Building repositories
├── Dedicated PostGIS cluster
└── On-premises ArxOS Bridge (optional)

ArxOS revenue: $299-999/building/month
```

**Capabilities:**
- Everything from paid tier
- ✅ SSO integration
- ✅ Custom workflows
- ✅ SLA guarantees
- ✅ On-premises deployment
- ✅ White-label options

---

## Implementation Timeline

### Week 1-2: Foundation

**YAML Serialization:**
- Add YAML struct tags to domain models
- Marshal/unmarshal functions
- Path ↔ FilePath converters
- Unit tests

**Deliverable:** Can convert Equipment ↔ YAML

### Week 3-4: Git Integration

**Git Provider:**
- Interface definition
- GitHub implementation (google/go-github)
- GitLab implementation (xanzy/go-gitlab)
- Local Git (go-git/go-git)
- Tests

**Deliverable:** Can commit/push/pull to Git platforms

### Week 5-6: Sync Engine

**Bidirectional Sync:**
- PostGIS → Git export
- Git → PostGIS import
- Conflict resolution
- Batch operations
- CLI commands

**Deliverable:** `arx export --to-git` and `arx import --from-git` work

### Week 7-8: Mobile Field Updates

**Mobile App:**
- LiDAR scan processing (extract spatial metadata)
- Package compression
- SMS/MMS package format
- Direct API upload

**Deliverable:** Mobile can send spatial updates

### Week 9-10: SMS Gateway

**SMS Integration:**
- Twilio webhook
- Building phone number registry
- Package decode
- GitHub PR/issue creation
- Confirmation messages

**Deliverable:** Text to building number creates GitHub PR

### Week 11-12: GitHub Actions

**Marketplace Actions:**
```
arxos/sync-action@v1       # PostGIS ↔ Git sync
arxos/alert-action@v1      # Equipment monitoring
arxos/validate-action@v1   # PR validation
```

**Deliverable:** Published to GitHub Actions Marketplace

### Week 13-14: Testing & Integration

**End-to-End Testing:**
- IFC import → PostGIS → Git export
- Git edit → PostGIS update → BAS apply
- Mobile scan → SMS → GitHub PR
- External SMS → GitHub issue

**Deliverable:** All workflows tested

### Week 15-16: Documentation & Launch

**Documentation:**
- Architecture docs
- API documentation
- GitHub Actions docs
- Mobile app guide
- Video tutorials

**Launch:**
- Demo repository
- Blog posts
- Hacker News launch

**Deliverable:** Public launch ready

---

## Technical Specifications

### Path System Specification

**Format:**
```
/BUILDING/FLOOR/ROOM/SYSTEM/EQUIPMENT

Building: Alphanumeric, uppercase, hyphens allowed
Floor: Number or name
Room: Room number or name
System: HVAC, LIGHTS, ELECTRICAL, etc.
Equipment: Equipment identifier
```

**Examples:**
```
/B1/3/301/HVAC/VAV-301
/EMPIRE-STATE/ROOF/MER-NORTH/HVAC/AHU-01
/CAMPUS-WEST/1/LOBBY/LIGHTS/ZONE-A
```

**Wildcards (for queries):**
```
/B1/3/*/HVAC/*              # All HVAC on floor 3
/B1/*/301/HVAC/*            # All HVAC in rooms numbered 301
/*/*/SAFETY/EXTING-*        # All fire extinguishers
```

### YAML Schema Specification

**Minimal valid YAML:**
```yaml
path: /B1/3/301/HVAC/VAV-301    # Required
name: VAV-301                    # Required
type: hvac                       # Required
```

**Full YAML:**
```yaml
apiVersion: arxos.io/v1
kind: Equipment

metadata:
  name: string
  path: string (universal path)
  id: string (PostGIS UUID)
  labels: map[string]string
  annotations: map[string]string

spec:
  manufacturer: string
  model: string
  serial_number: string
  install_date: date
  capacity: map[string]any
  setpoints: map[string]float64
  schedule: string
  location: {x, y, z, ar_anchor, confidence, source}
  bas: {system, point_name, network_address}

status:
  operational_state: string
  health: string
  current_values: map[string]float64
  alarms: []Alarm
  last_updated: timestamp

maintenance:
  schedule: string
  last_pm: date
  next_pm: date
  vendor: string

_arxos:
  postgis_id: string
  postgis_sync: {last_export, last_import}
  git_commit: string
```

### SMS Package Specification

**Protocol:** `ARXOS:{version}:{type}:{payload}`

**Types:**
- `spatial` - LiDAR/AR spatial scan
- `status` - Equipment status update
- `maintenance` - Maintenance note
- `photo` - Photo upload reference
- `issue` - Issue report

**Payload encoding:**
```
YAML → gzip → base64
```

**Example packages:**

```
Spatial update:
ARXOS:v1:spatial:H4sIAAAAAAAAA6tWKkktLlGwVUjOzy0oSi0uTuWqBQBWQw0XFgAAAA==

Status update:
ARXOS:v1:status:eJyrVkpJLEktyC9SKM5ITy1ScEksSQQAlkEGdw==

Plain text (no encoding):
Just regular text message → Creates GitHub issue
```

**Decode example:**

```go
func DecodeARXOSPackage(message string) (*Package, error) {
    // Parse: ARXOS:v1:spatial:eJyD8f9...
    parts := strings.Split(message, ":")

    version := parts[1]  // v1
    pkgType := parts[2]  // spatial
    payload := parts[3]  // base64 data

    // Decode: base64 → gzip → YAML
    decoded, _ := base64.StdEncoding.DecodeString(payload)
    decompressed, _ := gzip.Decompress(decoded)

    var pkg Package
    yaml.Unmarshal(decompressed, &pkg)

    return &pkg, nil
}
```

### API Endpoints

**New endpoints:**

```
# Git sync
POST /api/v1/git/sync/export       # PostGIS → Git
POST /api/v1/git/sync/import       # Git → PostGIS
GET  /api/v1/git/status            # Sync status

# SMS/Mobile
POST /api/v1/sms/webhook           # Twilio webhook
POST /api/v1/mobile/spatial-update # Direct spatial update
POST /api/v1/mobile/field-report   # Field report

# Building phone numbers
GET  /api/v1/buildings/{id}/phone          # Get phone number
POST /api/v1/buildings/{id}/phone          # Assign phone number
GET  /api/v1/phone/{number}/building       # Lookup building
```

---

## Workflow Examples

### Workflow 1: Import IFC, Export to Git

```bash
# Step 1: Import IFC to PostGIS (already works!)
arx import building.ifc --repository repo-123

# Result:
# ✅ PostGIS has 58 equipment items (9ms!)
# ✅ Paths generated: /B1/3/301/HVAC/VAV-301
# ✅ Spatial coordinates stored
# ✅ Ready for queries

# Step 2: Export to Git (NEW)
arx export --to-git \
  --repo github.com/acme/building \
  --create-repo \
  --private

# Result:
# ✅ Created GitHub repo
# ✅ Generated 58 YAML files (one per equipment)
# ✅ Organized by path: equipment/B1/3/301/HVAC/VAV-301.yml
# ✅ Initial commit with all files
# ✅ GitHub Actions configured

# Step 3: Query (uses PostGIS)
arx get /B1/3/301/HVAC/VAV-301

# Returns data from PostGIS (not YAML!)
```

### Workflow 2: PR-Based Configuration Change

```bash
# Step 1: Clone building repo
git clone github.com/acme/building
cd building

# Step 2: Create feature branch
git checkout -b optimize-vav-301

# Step 3: Edit configuration
vim equipment/B1/3/301/HVAC/VAV-301.yml
# Change: setpoints.temperature: 70 → 72

# Step 4: Commit and push
git commit -m "Comfort: Increase VAV-301 setpoint"
git push origin optimize-vav-301

# Step 5: Create PR
gh pr create \
  --title "Comfort: Increase VAV-301 setpoint" \
  --body "Increase temp for occupant comfort" \
  --reviewer @chief-engineer

# Step 6: GitHub Action validates
# ✅ YAML syntax valid
# ✅ Setpoint within range (50-80°F)
# ✅ No safety systems affected

# Step 7: Approved and merged

# Step 8: ArxOS applies change
# Webhook triggers or manual: arx sync --from-git
# - Reads changed YAML
# - Updates PostGIS
# - Applies to BAS

# Step 9: Verify
arx get /B1/3/301/HVAC/VAV-301
# Shows: setpoint=72, actual=71.8 (from PostGIS)
```

### Workflow 3: Mobile LiDAR Scan

```bash
# Step 1: Field user opens ArxOS mobile app

# Step 2: Scan room with LiDAR
# - Point iPhone at room
# - LiDAR captures 3D structure
# - App detects equipment (using AR object detection)

# Step 3: App extracts metadata
{
  room_path: "/B1/3/301",
  dimensions: {width: 10.5, height: 8.2, depth: 2.7},
  equipment_detected: [
    {
      estimated_path: "/B1/3/301/HVAC/VAV-301",
      position: {x: 10.5, y: 8.2, z: 2.7},
      ar_anchor: "anchor_abc123",
      confidence: 0.95
    }
  ],
  scan_timestamp: "2024-10-21T10:30:00Z",
  user_id: "user_xyz"
}

# Step 4: User taps "Send Update"

# Option A (Has WiFi/Data):
# → Direct API upload to PostGIS
# → PostGIS updates spatial coordinates
# → GitHub Action syncs to Git hourly

# Option B (No WiFi):
# → App compresses package (~500 bytes)
# → User texts to building: +1-844-278-6701
# → SMS gateway decodes
# → Creates GitHub PR with spatial data
# → On approval: Updates PostGIS

# Step 5: Verify
arx get /B1/3/301/HVAC/VAV-301
# Shows: location: {x: 10.5, y: 8.2, z: 2.7}

# Step 6: Render with spatial data
arx render --floor 3
# Now shows ASCII floor plan (has coordinates!)
```

### Workflow 4: External Contractor Report

```bash
# Step 1: Contractor notices issue (no ArxOS account)

# Step 2: Texts to building phone number
To: +1-844-278-6701
Message: "AHU-01 vibrating, possible bearing failure"

# Step 3: SMS Gateway
# - Receives text from +1-555-123-4567
# - Looks up building: Empire State
# - Finds repo: github.com/acme/empire-state
# - Searches for "AHU-01" in PostGIS
# - Finds path: /B1/ROOF/MER-NORTH/HVAC/AHU-01

# Step 4: Creates GitHub Issue
Title: "🔧 Field Report: AHU-01 vibration"
Body: """
External report received via SMS

**Reporter:** +1-555-123-4567 (External contractor)
**Equipment:** AHU-01 (/B1/ROOF/MER-NORTH/HVAC/AHU-01)
**Message:** AHU-01 vibrating, possible bearing failure
**Time:** 2024-10-21 10:30 AM

**Equipment Details:**
- Manufacturer: Trane
- Model: Voyager II
- Last PM: 2024-09-15 (36 days ago)
- Next PM: 2024-12-15

**Recommended Actions:**
- [ ] Inspect bearings
- [ ] Check belt alignment
- [ ] Measure vibration
- [ ] Schedule maintenance if needed

*Auto-generated from external SMS report*
"""
Labels: external-report, hvac, urgent, needs-triage
Assignees: @facilities-team

# Step 5: Facilities manager
# - Gets GitHub notification
# - Reviews issue
# - Assigns to technician
# - Work order tracked in GitHub

# Step 6: Confirmation sent
To: +1-555-123-4567
Message: "✅ Report received for AHU-01. Work order #42 created. Thank you!"
```

---

## Terminal Rendering Specification

### Data Source: Always PostGIS

**Terminal commands always query PostGIS, not Git:**

```go
func executeStatusCommand(ctx context.Context) {
    // Query PostGIS (existing code!)
    equipment := postgis.FindByPath(ctx, "/*/*/*/*/*/*")

    // Render based on available data
    if hasSpatialCoordinates(equipment) {
        renderSpatial(equipment)      // ASCII floor plan
    } else {
        renderPathTree(equipment)     // Simple tree
    }
}
```

**Git/YAML is NOT queried** for live display.

### Simple Rendering (Default)

**When PostGIS has NO spatial coordinates:**

```
Display mode: Path-based tree
Data source: PostGIS queries
Organization: By path hierarchy

Output:
Building B1
├── Floor 1
│   ├── Room 101
│   │   └── /B1/1/101/HVAC/VAV-101  ✅ 72.1°F
│   └── Room 102
│       └── /B1/1/102/HVAC/VAV-102  ✅ 71.8°F
└── Floor 3
    └── Room 301
        └── /B1/3/301/HVAC/VAV-301  ⚠️  67.5°F
```

**Implementation:**
- Use existing `internal/tui/` code
- Query PostGIS by path
- Display as tree
- Show live values from PostGIS

### Spatial Rendering (When Available)

**When PostGIS HAS spatial coordinates (from IFC or LiDAR):**

```
Display mode: ASCII floor plan
Data source: PostGIS spatial queries
Organization: By x,y coordinates

Output:
Floor 3
┌─────────────────────────────────┐
│                                  │
│  ┌──────┐      ┌──────┐         │
│  │ 301  │      │ 302  │         │
│  │ 🌡️    │      │ 🌡️    │         │
│  │71.8°F│      │70.5°F│         │
│  └──────┘      └──────┘         │
│                                  │
└─────────────────────────────────┘
```

**Triggered by:**
- IFC import (has spatial coordinates)
- LiDAR scan (mobile app adds coordinates)
- Manual coordinate entry

**Rendering uses:**
- PostGIS: `SELECT path, location_x, location_y, location_z FROM equipment`
- Convert coordinates to ASCII grid
- Place equipment symbols at positions
- Show live values from PostGIS

---

## Git Repository Organization

### Directory Structure

```
building-repo/
├── .github/
│   ├── workflows/
│   │   ├── sync.yml              # Hourly PostGIS ↔ Git sync
│   │   ├── alerts.yml            # Equipment monitoring
│   │   └── validate.yml          # PR validation
│   └── CODEOWNERS                # Approval workflow
│
├── equipment/                    # ORGANIZED BY PATH
│   └── B1/                       # Building
│       ├── ROOF/                 # Floor
│       │   └── MER-NORTH/        # Room
│       │       └── HVAC/         # System
│       │           ├── AHU-01.yml
│       │           └── AHU-02.yml
│       ├── 1/                    # Floor 1
│       │   ├── 101/              # Room 101
│       │   │   └── HVAC/
│       │   │       └── VAV-101.yml
│       │   └── 102/
│       │       └── HVAC/
│       │           └── VAV-102.yml
│       └── 3/                    # Floor 3
│           └── 301/
│               └── HVAC/
│                   └── VAV-301.yml
│
├── systems/
│   ├── bas-points.csv            # BAS point list
│   └── integrations.yml          # System configs
│
├── state/
│   ├── current.json              # Current state snapshot
│   └── snapshots/
│       ├── 2024-10-21.json      # Daily snapshots
│       └── 2024-10-20.json
│
├── building.yml                  # Building metadata
├── README.md                     # Building documentation
└── .arxos/
    └── config.yml                # ArxOS configuration
```

**Key principle:** Path structure = Directory structure

### GitHub Organization Structure

**Multi-building portfolio:**

```
github.com/acme-properties/
├── building-empire-state/        # One repo per building
├── building-rockefeller/
├── building-campus-west/
├── building-campus-east/
└── building-warehouse-01/

Each building = separate repository
Team permissions = GitHub teams
Access control = GitHub's built-in
```

---

## Advantages of This Architecture

### Technical Advantages

✅ **Leverages existing code** (80-85% reuse)
- Domain models
- Path system
- PostGIS queries
- IFC imports
- BAS integration
- Terminal UI

✅ **PostGIS power preserved**
- Spatial queries (millimeter precision)
- Fast path-based queries (9-36ms)
- Time-series data
- Real-time operations

✅ **Git collaboration added**
- Pull requests
- Version history
- Team workflow
- Audit trail

✅ **Platform agnostic**
- Works with GitHub, GitLab, etc.
- Can switch providers
- Self-hosted options

✅ **Mobile-first field updates**
- LiDAR spatial capture
- SMS/MMS for offline
- Direct API when online

✅ **External contributor access**
- Building phone numbers
- No account required
- Universal accessibility

### Business Advantages

✅ **Freemium model**
- Free: Git/YAML only
- Paid: Add PostGIS for spatial/real-time

✅ **Fast to market**
- 6-8 weeks for MVP
- 16 weeks for full launch

✅ **Low infrastructure cost**
- Git hosting: GitHub provides
- PostGIS: Only for paid tier

✅ **Network effects**
- GitHub's 100M users
- Existing workflows (PRs, issues)
- Familiar tools

---

## Risk Mitigation

### Technical Risks

**Risk: Git platform dependency**
- Mitigation: Abstract provider interface
- Mitigation: Support multiple platforms
- Mitigation: Local Git option

**Risk: SMS/MMS reliability**
- Mitigation: Direct API as primary
- Mitigation: SMS as fallback
- Mitigation: Local queue with retry

**Risk: YAML merge conflicts**
- Mitigation: Structured merge strategies
- Mitigation: Last-write-wins for status
- Mitigation: Manual resolution for config

**Risk: PostGIS sync lag**
- Mitigation: Hourly sync acceptable for audit
- Mitigation: Real-time queries use PostGIS directly
- Mitigation: Git is snapshot, not real-time source

### Operational Risks

**Risk: Large repository size**
- Mitigation: Daily snapshots, not every sensor reading
- Mitigation: Git LFS for binary files
- Mitigation: Keep repos focused

**Risk: GitHub API rate limits**
- Mitigation: Batch commits
- Mitigation: Use GitHub Apps (higher limits)
- Mitigation: Intelligent caching

**Risk: SMS costs**
- Mitigation: Direct API preferred
- Mitigation: SMS only for offline/external
- Mitigation: ~$0.01/message is acceptable

---

## Success Metrics

### Technical Metrics

- ✅ YAML serialization performance: <1ms per equipment
- ✅ Git sync time: <30s for 1,000 equipment
- ✅ PostGIS query performance: <50ms (already hitting 9-36ms!)
- ✅ Mobile package compression: <500 bytes for room scan
- ✅ SMS delivery: <5 seconds

### User Experience Metrics

- ✅ CLI commands work with both Git and PostGIS
- ✅ Terminal renders live data in <1s
- ✅ Mobile app updates appear in GitHub within 1 minute
- ✅ External SMS creates issue within 30 seconds
- ✅ PR approval → BAS update within 5 minutes

---

## Conclusion

### What We're Building

**A hybrid architecture that:**

1. **Keeps PostGIS as primary database**
   - IFC imports, spatial queries, real-time data
   - Everything that works now keeps working

2. **Adds Git/YAML collaboration layer**
   - Version control, PRs, team workflow
   - Standard YAML (no custom format)

3. **Connects via universal paths**
   - Paths work in both systems
   - Sync is path-based
   - Simple and elegant

4. **Enables mobile field updates**
   - LiDAR spatial capture
   - SMS/MMS for offline
   - External contributor access

5. **Platform agnostic**
   - GitHub, GitLab, Bitbucket, local
   - Abstract provider interface

### Engineering Effort

**Total: 12-16 weeks**

- Core Git integration: 6 weeks
- Mobile field updates: 4 weeks
- GitHub Actions: 3 weeks
- Polish and launch: 3 weeks

**80-85% code reuse** from existing ArxOS!

### Strategic Value

This architecture:
- ✅ Preserves all existing functionality
- ✅ Adds GitHub collaboration
- ✅ Creates freemium model
- ✅ Enables faster go-to-market
- ✅ Provides multiple revenue streams
- ✅ Reduces platform risk (multi-provider)

**Ready to implement!** 🚀

---

**Document Version:** 1.0
**Last Updated:** October 22, 2025
**Status:** Ready for Implementation
**Next Step:** Begin Week 1 development

