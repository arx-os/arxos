# Cisco Meraki Integration & AR Navigation System

**Status**: Design Phase
**Version**: 1.0
**Last Updated**: 2025-10-09
**Owner**: ArxOS Integration Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [API Design](#api-design)
7. [CLI Commands](#cli-commands)
8. [Mobile AR Features](#mobile-ar-features)
9. [Security & Privacy](#security--privacy)
10. [Implementation Plan](#implementation-plan)
11. [Use Cases](#use-cases)

---

## Overview

### Purpose

This document outlines the design and architecture for integrating Cisco Meraki Dashboard with ArxOS to enable:

1. **Real-time device location tracking** via WiFi access point (WAP) positioning
2. **Bidirectional CLI-to-Mobile workflows** for enterprise IT operations
3. **AR-guided navigation** to locate network devices and personnel
4. **Spatial asset management** combining network topology with physical building layouts

### Business Value

- **IT Asset Management**: Instantly locate any networked device in the building
- **Operational Efficiency**: Guide technicians directly to equipment via AR
- **Space Utilization**: Track device density and room occupancy
- **Security**: Monitor unauthorized device movement
- **Integration**: Bridge IT infrastructure with facilities management

### Key Capabilities

```
Meraki Dashboard → ArxOS → PostGIS → Mobile AR
        ↓              ↓         ↓         ↓
   Devices      Equipment   Spatial   Navigation
   Networks     Tracking    Queries   & Guidance
```

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Systems                            │
├─────────────────────────────────────────────────────────────────┤
│  Cisco Meraki Dashboard API                                     │
│  ├─ Network Devices                                             │
│  ├─ Access Points (WAPs)                                        │
│  ├─ Client Locations                                            │
│  └─ Signal Strength Data                                        │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTPS/REST
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│              ArxOS Integration Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  Meraki Integration Service                                     │
│  ├─ API Client (Go)                                             │
│  ├─ Device Sync Engine                                          │
│  ├─ Location Calculator (Triangulation)                         │
│  ├─ Webhook Handler                                             │
│  └─ Event Processor                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                  ArxOS Core Domain                              │
├─────────────────────────────────────────────────────────────────┤
│  Domain Entities                                                │
│  ├─ Equipment (extended with network data)                      │
│  ├─ NetworkDevice (new entity)                                  │
│  ├─ DeviceLocation (spatial tracking)                           │
│  └─ NavigationSession (AR push requests)                        │
│                                                                  │
│  Use Cases                                                      │
│  ├─ FindDeviceUseCase                                           │
│  ├─ TrackDeviceUseCase                                          │
│  ├─ PushARNavigationUseCase                                     │
│  └─ UpdateDeviceLocationUseCase                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│              Infrastructure Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  PostGIS Database                                               │
│  ├─ meraki_devices (network device data)                        │
│  ├─ device_location_history (spatial-temporal tracking)         │
│  ├─ wap_positions (access point locations)                      │
│  └─ ar_navigation_sessions (push requests)                      │
│                                                                  │
│  Repositories (Go)                                              │
│  ├─ MerakiDeviceRepository                                      │
│  ├─ DeviceLocationRepository                                    │
│  └─ NavigationSessionRepository                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Interface Layer                                │
├─────────────────────────────────────────────────────────────────┤
│  CLI (Cobra)                   │  HTTP API (Chi)                │
│  ├─ arx find                   │  ├─ POST /api/v1/devices/find  │
│  ├─ arx track                  │  ├─ POST /api/v1/ar/push       │
│  ├─ arx watch                  │  ├─ GET  /api/v1/devices/:id   │
│  ├─ arx share                  │  └─ WS   /ws/devices/live      │
│  └─ arx request-help           │                                │
│                                │                                │
│  Mobile App (React Native)                                      │
│  ├─ AR Navigation Screen                                        │
│  ├─ Device Location Viewer                                      │
│  ├─ Push Notification Handler                                   │
│  └─ Location Sharing Service                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Integration with Existing ArxOS Components

#### 1. Equipment System Extension

Existing `Equipment` entity is extended to support network devices:

```go
// Existing in internal/domain/entities.go
type Equipment struct {
    ID         types.ID
    BuildingID types.ID
    Name       string
    Type       string
    Location   *Location  // Already has 3D coordinates
    Status     string
    // ... existing fields
}

// New fields will be added via metadata or linked entity
```

#### 2. PostGIS Spatial Integration

Leverages existing PostGIS infrastructure:

```sql
-- Existing: equipment_positions table (migration 005)
-- New: Add network device tracking on top of existing spatial system
```

#### 3. Mobile AR Integration

Extends existing AR features in `mobile/src/ar/`:

```typescript
// Existing: mobile/src/ar/core/AREngine.ts
// Existing: mobile/src/services/arService.ts
// New: Device navigation features built on existing AR engine
```

#### 4. Version Control Compatibility

Device locations are versioned like all ArxOS data:

```bash
arx repo commit -m "Updated device locations from Meraki sync"
# Device location changes tracked in version control
```

---

## System Components

### 1. Meraki Integration Service

**Location**: `internal/infrastructure/integrations/meraki/`

**Responsibilities**:
- Connect to Meraki Dashboard API
- Poll or receive webhook updates
- Calculate device positions via triangulation
- Sync devices to ArxOS equipment system
- Handle authentication and rate limiting

**Go Package Structure**:
```go
package meraki

// Client handles API communication
type Client struct {
    apiKey      string
    baseURL     string
    httpClient  *http.Client
    rateLimiter *rate.Limiter
}

// Integration orchestrates the sync process
type Integration struct {
    client          *Client
    deviceRepo      domain.DeviceRepository
    locationRepo    domain.LocationRepository
    logger          domain.Logger
    pollInterval    time.Duration
    webhookEnabled  bool
}

// LocationCalculator determines device position
type LocationCalculator struct {
    wapRepo     domain.WAPRepository
    algorithm   TriangulationAlgorithm
}
```

### 2. Network Device Domain Entity

**Location**: `internal/domain/network_device.go`

```go
package domain

import "time"

// NetworkDevice represents a device on the enterprise network
type NetworkDevice struct {
    ID              types.ID
    EquipmentID     types.ID      // Link to Equipment entity
    MACAddress      string
    IPAddress       string
    DeviceName      string
    DeviceType      DeviceType    // laptop, phone, printer, iot
    MerakiNetworkID string

    // Location tracking
    CurrentLocation *SpatialPosition
    LastSeenWAPID   string
    SignalStrength  int    // dBm
    Confidence      int    // 0-3 confidence level

    // Connection status
    Status          ConnectionStatus
    LastSeen        time.Time
    FirstSeen       time.Time

    // Metadata
    Manufacturer    string
    OSVersion       string
    UserAssigned    string // User this device belongs to
    IsPersonal      bool   // Personal vs company device
    Metadata        map[string]any

    CreatedAt       time.Time
    UpdatedAt       time.Time
}

type DeviceType string

const (
    DeviceTypeLaptop   DeviceType = "laptop"
    DeviceTypeDesktop  DeviceType = "desktop"
    DeviceTypePhone    DeviceType = "phone"
    DeviceTypeTablet   DeviceType = "tablet"
    DeviceTypePrinter  DeviceType = "printer"
    DeviceTypeIoT      DeviceType = "iot_device"
    DeviceTypeAP       DeviceType = "access_point"
    DeviceTypeUnknown  DeviceType = "unknown"
)

type ConnectionStatus string

const (
    StatusConnected    ConnectionStatus = "connected"
    StatusDisconnected ConnectionStatus = "disconnected"
    StatusRoaming      ConnectionStatus = "roaming"
    StatusIdle         ConnectionStatus = "idle"
)
```

### 3. AR Navigation Session

**Location**: `internal/domain/ar_navigation.go`

```go
package domain

// ARNavigationSession represents a CLI-to-Mobile AR push request
type ARNavigationSession struct {
    ID            types.ID
    RequestedBy   string    // CLI user who initiated
    TargetUser    string    // Mobile user receiving AR push
    TargetDevice  types.ID  // Device to navigate to
    TargetPerson  string    // Or person to find

    // Navigation data
    StartPosition *SpatialPosition
    EndPosition   *SpatialPosition
    CalculatedPath []SpatialPosition
    Distance      float64

    // Session management
    Status        NavigationStatus
    Priority      Priority
    Message       string
    ExpiresAt     time.Time

    // Tracking
    Accepted      bool
    CompletedAt   *time.Time
    FoundLocation *SpatialPosition
    Notes         string

    CreatedAt     time.Time
    UpdatedAt     time.Time
}

type NavigationStatus string

const (
    NavStatusPending    NavigationStatus = "pending"
    NavStatusActive     NavigationStatus = "active"
    NavStatusCompleted  NavigationStatus = "completed"
    NavStatusExpired    NavigationStatus = "expired"
    NavStatusCancelled  NavigationStatus = "cancelled"
)

type Priority string

const (
    PriorityNormal  Priority = "normal"
    PriorityHigh    Priority = "high"
    PriorityUrgent  Priority = "urgent"
)
```

### 4. Use Cases

**Location**: `internal/usecase/`

```go
// FindDeviceUseCase - Locate a device by various identifiers
type FindDeviceUseCase struct {
    deviceRepo   DeviceRepository
    locationRepo LocationRepository
    wapRepo      WAPRepository
    logger       Logger
}

func (uc *FindDeviceUseCase) FindDevice(ctx context.Context, query DeviceQuery) (*NetworkDevice, error)

// TrackDeviceUseCase - Track device movement history
type TrackDeviceUseCase struct {
    locationRepo LocationRepository
    logger       Logger
}

func (uc *TrackDeviceUseCase) GetLocationHistory(ctx context.Context, deviceID types.ID, timeRange TimeRange) ([]DeviceLocation, error)

// PushARNavigationUseCase - Push AR navigation to mobile
type PushARNavigationUseCase struct {
    navRepo      NavigationSessionRepository
    deviceRepo   DeviceRepository
    userRepo     UserRepository
    pushService  PushNotificationService
    pathfinder   PathfindingService
    logger       Logger
}

func (uc *PushARNavigationUseCase) PushNavigation(ctx context.Context, req ARNavigationRequest) (*ARNavigationSession, error)
```

---

## Data Flow

### Scenario 1: Device Sync from Meraki

```
┌──────────────┐
│   Meraki     │
│  Dashboard   │
└──────┬───────┘
       │ 1. Poll/Webhook
       ↓
┌──────────────────────────────────┐
│  Meraki Integration Service      │
│  ├─ Fetch device list            │
│  ├─ Fetch client locations       │
│  ├─ Fetch signal strength        │
│  └─ Calculate positions          │
└──────┬───────────────────────────┘
       │ 2. Device data + location
       ↓
┌──────────────────────────────────┐
│  Network Device Repository       │
│  ├─ Upsert device record         │
│  └─ Store in PostGIS             │
└──────┬───────────────────────────┘
       │ 3. Spatial insert
       ↓
┌──────────────────────────────────┐
│  PostGIS Database                │
│  ├─ meraki_devices table         │
│  └─ device_location_history      │
└──────────────────────────────────┘
```

### Scenario 2: CLI Find & Push to AR

```
┌──────────────┐
│  CLI User    │
│  (Desktop)   │
└──────┬───────┘
       │ arx find "device" @ "building" push --ar username
       ↓
┌──────────────────────────────────┐
│  FindDeviceUseCase               │
│  ├─ Query device by name         │
│  ├─ Get current location         │
│  └─ Validate user permissions    │
└──────┬───────────────────────────┘
       │ Device found with location
       ↓
┌──────────────────────────────────┐
│  PushARNavigationUseCase         │
│  ├─ Create navigation session    │
│  ├─ Calculate path               │
│  ├─ Send push notification       │
│  └─ Store session in DB          │
└──────┬───────────────────────────┘
       │ Push notification
       ↓
┌──────────────────────────────────┐
│  Mobile App (React Native)       │
│  ├─ Receive push notification    │
│  ├─ Load navigation session      │
│  ├─ Open AR navigation screen    │
│  └─ Display AR guidance          │
└──────┬───────────────────────────┘
       │ User navigates via AR
       ↓
┌──────────────────────────────────┐
│  AR Engine                       │
│  ├─ Show path overlay            │
│  ├─ Update distance in real-time│
│  ├─ Detect proximity             │
│  └─ Confirm found                │
└──────┬───────────────────────────┘
       │ User taps "Found It"
       ↓
┌──────────────────────────────────┐
│  UpdateNavigationSession         │
│  ├─ Mark as completed            │
│  ├─ Store found location         │
│  └─ Notify CLI user              │
└──────────────────────────────────┘
```

### Scenario 3: Real-Time Device Movement

```
Meraki Webhook → Integration Service → Device Update
                                            ↓
                              WebSocket Broadcast
                                            ↓
                    ┌────────────────────────────────┐
                    │                                │
            ┌───────▼────────┐           ┌──────────▼─────────┐
            │  CLI (watching)│           │  Mobile App (AR)   │
            │  arx watch     │           │  Live tracking     │
            └────────────────┘           └────────────────────┘
```

---

## Database Schema

### 1. Meraki Devices Table

```sql
-- Stores network device information synced from Meraki
CREATE TABLE IF NOT EXISTS meraki_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES equipment(id) ON DELETE SET NULL,

    -- Network identifiers
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    ip_address INET,
    device_name VARCHAR(255),
    device_type VARCHAR(50) NOT NULL,

    -- Meraki-specific
    meraki_network_id VARCHAR(255) NOT NULL,
    meraki_device_id VARCHAR(255),

    -- User assignment
    user_assigned VARCHAR(255),
    is_personal BOOLEAN DEFAULT false,
    is_tracked BOOLEAN DEFAULT true,

    -- Device info
    manufacturer VARCHAR(255),
    os_version VARCHAR(100),

    -- Connection status
    connection_status VARCHAR(20) NOT NULL DEFAULT 'disconnected',
    last_seen_wap VARCHAR(255),
    signal_strength INTEGER, -- dBm
    confidence_level SMALLINT CHECK (confidence_level >= 0 AND confidence_level <= 3),

    -- Timestamps
    last_seen TIMESTAMP,
    first_seen TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_meraki_devices_mac ON meraki_devices(mac_address);
CREATE INDEX idx_meraki_devices_ip ON meraki_devices(ip_address);
CREATE INDEX idx_meraki_devices_name ON meraki_devices(device_name);
CREATE INDEX idx_meraki_devices_status ON meraki_devices(connection_status);
CREATE INDEX idx_meraki_devices_user ON meraki_devices(user_assigned);
CREATE INDEX idx_meraki_devices_type ON meraki_devices(device_type);
CREATE INDEX idx_meraki_devices_last_seen ON meraki_devices(last_seen DESC);
```

### 2. Device Location History Table

```sql
-- Stores spatial-temporal tracking of device movements
CREATE TABLE IF NOT EXISTS device_location_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES meraki_devices(id) ON DELETE CASCADE,

    -- Spatial data (PostGIS)
    position GEOMETRY(POINTZ, 4326) NOT NULL,

    -- Building context
    building_id UUID REFERENCES buildings(id),
    floor_id UUID REFERENCES floors(id),
    room_id UUID REFERENCES rooms(id),

    -- Location calculation
    wap_id UUID, -- WAP that detected the device
    signal_strength INTEGER, -- dBm at time of detection
    confidence_level SMALLINT CHECK (confidence_level >= 0 AND confidence_level <= 3),
    calculation_method VARCHAR(50), -- 'primary_wap', 'triangulation', 'manual'

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    detected_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_device_location_device ON device_location_history(device_id, detected_at DESC);
CREATE INDEX idx_device_location_position ON device_location_history USING GIST(position);
CREATE INDEX idx_device_location_building ON device_location_history(building_id);
CREATE INDEX idx_device_location_floor ON device_location_history(floor_id);
CREATE INDEX idx_device_location_room ON device_location_history(room_id);
CREATE INDEX idx_device_location_time ON device_location_history(detected_at DESC);

-- View for latest device positions
CREATE OR REPLACE VIEW device_current_positions AS
SELECT DISTINCT ON (device_id)
    device_id,
    position,
    building_id,
    floor_id,
    room_id,
    confidence_level,
    detected_at
FROM device_location_history
ORDER BY device_id, detected_at DESC;
```

### 3. WAP Positions Table

```sql
-- Stores physical locations of WiFi Access Points
CREATE TABLE IF NOT EXISTS wap_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES equipment(id) ON DELETE SET NULL,

    -- Meraki identifiers
    meraki_wap_id VARCHAR(255) UNIQUE NOT NULL,
    wap_name VARCHAR(255) NOT NULL,
    wap_mac VARCHAR(17),

    -- Spatial data
    position GEOMETRY(POINTZ, 4326) NOT NULL,
    coverage_radius FLOAT, -- meters

    -- Building context
    building_id UUID NOT NULL REFERENCES buildings(id),
    floor_id UUID REFERENCES floors(id),
    room_id UUID REFERENCES rooms(id),

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_online TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_wap_positions_position ON wap_positions USING GIST(position);
CREATE INDEX idx_wap_positions_building ON wap_positions(building_id);
CREATE INDEX idx_wap_positions_floor ON wap_positions(floor_id);
CREATE INDEX idx_wap_positions_meraki_id ON wap_positions(meraki_wap_id);
CREATE INDEX idx_wap_positions_active ON wap_positions(is_active);
```

### 4. AR Navigation Sessions Table

```sql
-- Stores CLI-to-Mobile AR navigation push requests
CREATE TABLE IF NOT EXISTS ar_navigation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Request context
    requested_by VARCHAR(255) NOT NULL, -- CLI user
    target_user VARCHAR(255) NOT NULL,  -- Mobile user

    -- Navigation target (one of these)
    target_device_id UUID REFERENCES meraki_devices(id),
    target_equipment_id UUID REFERENCES equipment(id),
    target_person VARCHAR(255), -- For finding people

    -- Navigation data
    start_position GEOMETRY(POINTZ, 4326),
    end_position GEOMETRY(POINTZ, 4326) NOT NULL,
    calculated_path GEOMETRY(LINESTRINGZ, 4326),
    distance FLOAT, -- meters

    -- Session management
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    message TEXT,
    expires_at TIMESTAMP NOT NULL,

    -- Tracking
    accepted BOOLEAN DEFAULT false,
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    found_position GEOMETRY(POINTZ, 4326),
    found_note TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ar_nav_sessions_target_user ON ar_navigation_sessions(target_user, status);
CREATE INDEX idx_ar_nav_sessions_requested_by ON ar_navigation_sessions(requested_by);
CREATE INDEX idx_ar_nav_sessions_status ON ar_navigation_sessions(status);
CREATE INDEX idx_ar_nav_sessions_created ON ar_navigation_sessions(created_at DESC);
CREATE INDEX idx_ar_nav_sessions_expires ON ar_navigation_sessions(expires_at);
```

---

## API Design

### REST API Endpoints

**Base URL**: `/api/v1/meraki/`

#### Device Endpoints

```http
# Find a device
GET /api/v1/meraki/devices/find
Query Parameters:
  - name: string (device name)
  - mac: string (MAC address)
  - ip: string (IP address)
  - building_id: UUID
Response: NetworkDevice

# Get device details
GET /api/v1/meraki/devices/:id
Response: NetworkDevice with current location

# Get device location history
GET /api/v1/meraki/devices/:id/history
Query Parameters:
  - from: timestamp
  - to: timestamp
  - limit: integer
Response: DeviceLocation[]

# Get devices in area
POST /api/v1/meraki/devices/in-area
Body: {
  "building_id": "uuid",
  "floor_id": "uuid",
  "room_id": "uuid",
  "radius": float (meters)
}
Response: NetworkDevice[]

# Get devices by user
GET /api/v1/meraki/devices/user/:username
Response: NetworkDevice[]
```

#### AR Navigation Endpoints

```http
# Push AR navigation to mobile user
POST /api/v1/ar/navigation/push
Body: {
  "target_user": "username",
  "target_device_id": "uuid",
  "message": "string",
  "priority": "normal|high|urgent",
  "duration": integer (minutes)
}
Response: ARNavigationSession

# Get navigation sessions for user
GET /api/v1/ar/navigation/sessions
Query Parameters:
  - user: string
  - status: string
Response: ARNavigationSession[]

# Update navigation session (mobile app)
PATCH /api/v1/ar/navigation/sessions/:id
Body: {
  "status": "active|completed|cancelled",
  "found_position": { "x": float, "y": float, "z": float },
  "note": "string"
}
Response: ARNavigationSession

# Accept navigation session (mobile app)
POST /api/v1/ar/navigation/sessions/:id/accept
Response: ARNavigationSession with path calculation
```

#### Integration Endpoints

```http
# Trigger manual sync
POST /api/v1/meraki/sync
Response: SyncResult

# Get sync status
GET /api/v1/meraki/sync/status
Response: SyncStatus

# Configure integration
PUT /api/v1/meraki/config
Body: MerakiConfig
Response: MerakiConfig

# Get integration health
GET /api/v1/meraki/health
Response: IntegrationHealth
```

### WebSocket Endpoints

```
WS /ws/devices/live
- Real-time device location updates
- Device connection/disconnection events
- Device movement notifications

WS /ws/ar/navigation/:session_id
- Real-time navigation updates
- Distance changes
- Completion notifications
```

### Webhook Endpoint (Receives from Meraki)

```http
POST /api/v1/webhooks/meraki
Headers:
  X-Meraki-Signature: HMAC signature for verification
Body: Meraki webhook payload
Response: 200 OK
```

---

## CLI Commands

### Command Structure

All commands follow ArxOS conventions:

```bash
arx <command> <subcommand> [arguments] [flags]
```

### Device Finding Commands

```bash
# Find device by name
arx find "Laptop-Sales-05" @ "HQ-Building"
arx find device "Laptop-Sales-05" --building "HQ"

# Find by IP address
arx find 192.168.1.100

# Find by MAC address
arx find 00:1B:63:84:45:E6

# Find with filters
arx find --room "Conference A" --type laptop
arx find --floor 3 --status connected
arx find --user "joel.pate"

# Find with history
arx find "Laptop-Sales-05" --history --last 24h
arx find "Laptop-Sales-05" --history --from "9am" --to "5pm"

# Find and watch (live updates)
arx find "Laptop-Sales-05" --follow
arx watch device "Laptop-Sales-05"
```

### AR Push Commands

```bash
# Basic AR push
arx find "Laptop-Sales-05" @ "HQ" push --ar joel
arx find device "Laptop-Sales-05" push --ar-user joel.pate

# With priority
arx find "Server-Rack-A" push --ar ops-team --priority urgent

# With message
arx find "Printer-3A" push --ar helpdesk --message "Paper jam reported"

# With duration (auto-expire)
arx find "iPad-Conference" push --ar sarah --duration 15m

# Push to multiple users
arx find "Fire-Extinguisher-3F" push --ar @team.safety

# Push to user's current location
arx find user "mike.tech" push --ar sarah
```

### Tracking Commands

```bash
# Track device movement
arx track device "Laptop-Sales-05"
arx track device "Laptop-Sales-05" --duration 1h

# Track multiple devices
arx track --room "Server Room" --alert-on-movement

# Track with notifications
arx track device "Executive-Laptop" --notify joel --on-move

# Export tracking data
arx track device "Laptop-Sales-05" --export tracking_report.json
```

### Location Sharing Commands

```bash
# Share your location
arx share location --duration 15m
arx share location --with @team.it --duration 30m

# Share specific device location
arx share device "Meeting-Room-iPad" --with visitors

# Stop sharing
arx share stop
```

### Integration Management Commands

```bash
# Configure Meraki integration
arx integration meraki configure \
  --api-key $MERAKI_API_KEY \
  --network-id $NETWORK_ID

# Test connection
arx integration meraki test

# Trigger manual sync
arx integration meraki sync

# View sync status
arx integration meraki status

# View sync history
arx integration meraki history --last 7d
```

### Device Management Commands

```bash
# List all networked devices
arx device list
arx device list --building "HQ" --floor 3

# Register WAP positions
arx device register-wap "WAP-3F-North" \
  --meraki-id "Q2AB-CD34-EF56" \
  --floor 3 \
  --x 25.5 --y 40.2 --z 2.8

# Update device metadata
arx device update "Laptop-Sales-05" \
  --user "john.doe" \
  --type laptop

# Mark device as personal (exclude from tracking)
arx device privacy "iPhone-Joel" --personal

# Device census (inventory)
arx device census --rooms "Conference.*"
```

---

## Mobile AR Features

### AR Navigation Screen

**Component**: `mobile/src/screens/ARNavigationScreen.tsx`

**Features**:
- Real-time AR overlay showing path to device
- Distance indicator (updates as user moves)
- Floor-aware navigation (shows elevator/stairs when needed)
- Device metadata display (IP, signal strength, last seen)
- "Found It" confirmation button
- Photo capture for verification
- Note taking for feedback

**AR Overlays**:
```
- Directional arrows (3D in space)
- Distance markers every 5 meters
- Floor indicators (up/down arrows)
- Destination marker (pulsing icon)
- Breadcrumb trail (optional)
```

### Push Notification Handler

**Service**: `mobile/src/services/ARNavigationService.ts`

**Notification Types**:
1. **Device Request** - Someone needs you to find something
2. **Proximity Alert** - You're near a tracked item
3. **Movement Alert** - Device moved unexpectedly
4. **Team Coordination** - Find coworker/equipment

**Notification Actions**:
- "Navigate in AR" - Opens AR navigation
- "Dismiss" - Ignores request
- "Can't Help" - Declines with notification to requester
- "Forward" - Send to another team member

### Device Location Viewer

**Component**: `mobile/src/screens/DeviceLocationScreen.tsx`

**Features**:
- Map view of devices on floor plan
- List view with filters
- Device details (IP, MAC, user, status)
- Location history timeline
- Search and filter capabilities

### Location Sharing Service

**Service**: `mobile/src/services/LocationSharingService.ts`

**Features**:
- Share current location with duration limit
- Privacy controls (who can see)
- Auto-expire after timeout
- Visual indicator when sharing
- Background location updates (when sharing)

### AR Heatmap View

**Component**: `mobile/src/components/AR/ARHeatmapOverlay.tsx`

**Features**:
- Color-coded room overlays (device density)
- Real-time device count per room
- Tap room to see device list
- Filter by device type

---

## Security & Privacy

### Authentication & Authorization

```yaml
# Role-Based Access Control (RBAC)
roles:
  admin:
    - meraki.devices.read
    - meraki.devices.write
    - meraki.config.write
    - ar.navigation.push.any
    - location.share.view.any

  it_technician:
    - meraki.devices.read
    - meraki.devices.find
    - ar.navigation.push.team
    - location.share.view.team

  facilities:
    - meraki.devices.read.equipment_only
    - ar.navigation.push.team

  user:
    - meraki.devices.read.own
    - ar.navigation.receive
    - location.share.own
```

### Privacy Controls

#### User Privacy Settings

**Configuration**: `configs/integrations/meraki_privacy.yml`

```yaml
privacy:
  # Global defaults
  defaults:
    track_personal_devices: false
    anonymize_personal_data: true
    location_history_retention: 30 # days

  # Per-user overrides
  user_controls:
    enabled: true
    settings:
      - location_sharing_default: false
      - auto_expire_duration: 15m
      - who_can_find_me:
          - team_members
          - managers
          - security
      - quiet_hours:
          weekdays: "18:00-08:00"
          weekends: "all"

  # Device privacy
  device_privacy:
    personal_device_indicators:
      - "iPhone-*"
      - "*-Personal"
    anonymize_personal: true # Show as "Personal Device" not owner name
    exclude_from_tracking: true

  # Compliance
  compliance:
    gdpr_compliant: true
    log_access_requests: true
    allow_data_export: true
    allow_data_deletion: true
```

#### Data Retention Policy

```sql
-- Auto-delete old location history
CREATE OR REPLACE FUNCTION cleanup_old_location_history()
RETURNS void AS $$
BEGIN
    DELETE FROM device_location_history
    WHERE detected_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (run daily)
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule('cleanup-location-history', '0 2 * * *', 'SELECT cleanup_old_location_history()');
```

### Security Measures

1. **API Authentication**
   - JWT tokens for API access
   - Meraki API key stored encrypted
   - Webhook signature verification

2. **Data Encryption**
   - TLS for all API communication
   - Encrypted storage of sensitive device info
   - Encrypted push notifications

3. **Access Logging**
   ```sql
   CREATE TABLE device_access_log (
       id UUID PRIMARY KEY,
       user_id VARCHAR(255) NOT NULL,
       device_id UUID NOT NULL,
       action VARCHAR(50) NOT NULL, -- 'view', 'find', 'push_ar'
       ip_address INET,
       timestamp TIMESTAMP DEFAULT NOW()
   );
   ```

4. **Rate Limiting**
   - API endpoints: 100 requests/minute per user
   - AR push notifications: 10/hour per user
   - Webhook processing: 1000/minute

---

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Basic Meraki integration and device syncing

**Tasks**:
- [ ] Create Meraki API client (`internal/infrastructure/integrations/meraki/`)
- [ ] Implement authentication and API calls
- [ ] Create database schema (migrations)
- [ ] Implement NetworkDevice domain entity
- [ ] Create device repository
- [ ] Basic sync engine (polling)
- [ ] Unit tests

**Deliverable**: Devices sync from Meraki to ArxOS database

### Phase 2: Location Tracking (Weeks 3-4)

**Goal**: WAP positioning and spatial tracking

**Tasks**:
- [ ] Implement WAP registration commands
- [ ] Create location calculator (triangulation logic)
- [ ] Store positions in PostGIS
- [ ] Track location history
- [ ] Implement confidence scoring
- [ ] Integration tests

**Deliverable**: Devices have spatial positions tracked over time

### Phase 3: CLI Commands (Week 5)

**Goal**: `arx find` and device discovery

**Tasks**:
- [ ] Implement `arx find` command
- [ ] Device search by name/IP/MAC
- [ ] Location history queries
- [ ] Watch/follow mode
- [ ] Output formatting (table, JSON)
- [ ] CLI tests

**Deliverable**: Users can find devices via CLI

### Phase 4: AR Navigation Backend (Week 6)

**Goal**: AR push infrastructure

**Tasks**:
- [ ] Create ARNavigationSession entity
- [ ] Implement PushARNavigationUseCase
- [ ] Create REST API endpoints
- [ ] Implement push notification service
- [ ] Pathfinding algorithm
- [ ] WebSocket for live updates
- [ ] API tests

**Deliverable**: Backend can push AR navigation sessions

### Phase 5: Mobile AR Integration (Weeks 7-8)

**Goal**: Mobile AR navigation features

**Tasks**:
- [ ] AR navigation screen UI
- [ ] Push notification handler
- [ ] AR path rendering
- [ ] Distance calculation
- [ ] Found confirmation flow
- [ ] Location sharing service
- [ ] Mobile tests

**Deliverable**: Full CLI → Mobile AR workflow working

### Phase 6: Real-Time Features (Week 9)

**Goal**: Webhooks and live updates

**Tasks**:
- [ ] Implement Meraki webhook handler
- [ ] WebSocket broadcasting
- [ ] Live device tracking
- [ ] Movement alerts
- [ ] Real-time CLI updates
- [ ] Integration tests

**Deliverable**: Real-time device movement tracking

### Phase 7: Advanced Features (Week 10)

**Goal**: Polish and advanced capabilities

**Tasks**:
- [ ] AR heatmap visualization
- [ ] Device history replay
- [ ] Team coordination features
- [ ] Location sharing
- [ ] Privacy controls UI
- [ ] User acceptance testing

**Deliverable**: Production-ready feature set

### Phase 8: Documentation & Deployment (Week 11)

**Goal**: Production deployment

**Tasks**:
- [ ] User documentation
- [ ] API documentation
- [ ] Admin guides
- [ ] Deployment configuration
- [ ] Performance testing
- [ ] Security audit
- [ ] Production deployment

**Deliverable**: Feature live in production

---

## Use Cases

### Use Case 1: Lost Device Recovery

**Actor**: IT Technician
**Trigger**: Employee reports lost laptop

**Flow**:
1. Employee calls IT: "I lost my laptop somewhere in the building"
2. IT runs: `arx find "Laptop-Employee-Name" @ "HQ"`
3. System shows: Last seen in Conference Room 3-A, 2 minutes ago
4. IT runs: `arx find "Laptop-Employee-Name" push --ar employee.name`
5. Employee receives AR navigation on phone
6. Employee navigates to location using AR
7. Employee finds laptop and taps "Found It"
8. IT receives confirmation notification
9. Case closed

**Value**: Reduced recovery time from 30+ minutes to 2-3 minutes

### Use Case 2: Equipment Delivery

**Actor**: IT Technician delivering equipment
**Trigger**: New monitor ordered, needs delivery to employee

**Flow**:
1. IT arrives with monitor, needs to find employee
2. IT runs: `arx find user "john.doe" @ "Office-Building" push --ar john.doe --message "Delivery: New monitor"`
3. John receives notification: "IT is delivering your monitor"
4. John has two options:
   - Share his location: IT navigates to him
   - Navigate to IT: John goes to meet IT
5. John shares location
6. IT's phone shows AR navigation to John's current position
7. IT follows AR path, finds John
8. Delivery complete

**Value**: No phone tag, no waiting at desk, instant coordination

### Use Case 3: Security Incident

**Actor**: Security Team
**Trigger**: Unauthorized device detected

**Flow**:
1. Meraki alerts: Unknown device connected
2. Security runs: `arx find 00:XX:XX:XX:XX:XX --priority urgent`
3. System shows: Lobby, Floor 1, connected 30 seconds ago
4. Security runs: `arx track 00:XX:XX:XX:XX:XX --alert-on-movement --notify security.team`
5. Device moves to Floor 3
6. Alert broadcast to security team
7. Security pushes AR navigation: `arx find 00:XX:XX:XX:XX:XX push --ar @security.team --priority urgent`
8. Nearest security officer receives AR navigation
9. Officer locates device
10. Incident resolved

**Value**: Rapid response to security threats, precise location tracking

### Use Case 4: Facilities Inspection

**Actor**: Facilities Manager
**Trigger**: Monthly equipment audit

**Flow**:
1. Manager starts AR census: `arx device census --rooms "Conference.*" --ar-session`
2. Manager walks through conference rooms with AR app
3. AR overlays show:
   - ✓ Projector (verified)
   - ✓ Polycom (verified)
   - ✓ iPad controller (verified)
   - ❌ HDMI cable missing (prompt to add note)
4. Manager adds note: "HDMI cable missing, order replacement"
5. AR session exports report
6. Work order automatically created

**Value**: Systematic auditing, reduced manual data entry, real-time updates

### Use Case 5: Emergency Equipment Location

**Actor**: Safety Officer
**Trigger**: Emergency drill or actual emergency

**Flow**:
1. Safety officer needs AED location
2. Runs: `arx find "AED-Floor-3" @ "Office" push --ar @all.floor3 --priority urgent`
3. Everyone on Floor 3 receives urgent AR navigation
4. Nearest person follows AR path
5. AED located in 15 seconds
6. Emergency response

**Value**: Life-saving speed, crowd-sourced assistance

---

## Performance Considerations

### Database Optimization

```sql
-- Partition location history by time
CREATE TABLE device_location_history (
    ...
) PARTITION BY RANGE (detected_at);

CREATE TABLE device_location_history_2025_10 PARTITION OF device_location_history
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

-- Indexes for common queries
CREATE INDEX CONCURRENTLY idx_devices_search
    ON meraki_devices USING GIN (to_tsvector('english', device_name));

-- Materialized view for dashboard
CREATE MATERIALIZED VIEW device_summary AS
SELECT
    building_id,
    device_type,
    connection_status,
    COUNT(*) as device_count
FROM meraki_devices
GROUP BY building_id, device_type, connection_status;

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY device_summary;
```

### Caching Strategy

```go
// Use ArxOS unified cache system
cache := NewUnifiedCache(config, logger)

// Cache device lookups (L1: 5 min)
deviceKey := fmt.Sprintf("device:%s", deviceID)
cache.Set(ctx, deviceKey, device, 5*time.Minute)

// Cache location queries (L2: 1 hour)
locationKey := fmt.Sprintf("location:%s:current", deviceID)
cache.Set(ctx, locationKey, location, 1*time.Hour)

// Cache WAP positions (L3: 24 hours - rarely change)
wapKey := fmt.Sprintf("wap:%s:position", wapID)
cache.Set(ctx, wapKey, position, 24*time.Hour)
```

### WebSocket Optimization

```go
// Only broadcast to users watching specific devices
type DeviceSubscription struct {
    userID   string
    deviceID string
    conn     *websocket.Conn
}

// Filter broadcasts
func (h *Hub) BroadcastDeviceUpdate(deviceID string, update Update) {
    for _, sub := range h.subscriptions[deviceID] {
        sub.conn.WriteJSON(update)
    }
}
```

---

## Monitoring & Observability

### Metrics

```yaml
# Prometheus metrics
metrics:
  - meraki_api_requests_total
  - meraki_api_errors_total
  - meraki_sync_duration_seconds
  - devices_tracked_total
  - device_location_updates_total
  - ar_navigation_sessions_total
  - ar_navigation_success_rate
  - device_find_latency_seconds
```

### Logging

```go
logger.Info("Device found",
    "device_id", deviceID,
    "device_name", device.Name,
    "location", fmt.Sprintf("%f,%f,%f", loc.X, loc.Y, loc.Z),
    "confidence", confidence,
    "query_duration_ms", duration.Milliseconds())

logger.Warn("Device moved unexpectedly",
    "device_id", deviceID,
    "old_location", oldLoc,
    "new_location", newLoc,
    "distance_meters", distance)
```

### Alerts

```yaml
alerts:
  - name: MerakiSyncFailed
    condition: meraki_api_errors_total > 5
    severity: warning

  - name: HighLocationCalculationErrors
    condition: location_calculation_errors_rate > 0.1
    severity: warning

  - name: ARNavigationHighFailureRate
    condition: ar_navigation_success_rate < 0.8
    severity: critical
```

---

## Testing Strategy

### Unit Tests

```go
// Test location calculation
func TestLocationCalculator_TriangulatePosition(t *testing.T) {
    calc := NewLocationCalculator()
    waps := []WAP{
        {Position: Point{X: 0, Y: 0, Z: 0}, SignalStrength: -40},
        {Position: Point{X: 10, Y: 0, Z: 0}, SignalStrength: -50},
        {Position: Point{X: 5, Y: 10, Z: 0}, SignalStrength: -45},
    }

    pos, confidence := calc.Triangulate(waps)

    assert.NotNil(t, pos)
    assert.InDelta(t, 5.0, pos.X, 2.0) // Within 2 meters
    assert.InDelta(t, 5.0, pos.Y, 2.0)
    assert.GreaterOrEqual(t, confidence, 2)
}
```

### Integration Tests

```go
// Test full device sync flow
func TestMerakiIntegration_SyncDevices(t *testing.T) {
    // Setup test Meraki server
    server := httptest.NewServer(merakiMockHandler())
    defer server.Close()

    integration := NewMerakiIntegration(server.URL, apiKey)

    err := integration.SyncDevices(ctx)
    assert.NoError(t, err)

    // Verify devices in database
    devices, err := deviceRepo.GetAll(ctx)
    assert.NoError(t, err)
    assert.Len(t, devices, 5)
}
```

### E2E Tests

```bash
# Test CLI → Mobile AR flow
describe("AR Navigation E2E", () => {
  it("should push navigation from CLI to mobile", async () => {
    // Run CLI command
    await exec("arx find 'Test-Device' push --ar testuser");

    // Verify API call
    const sessions = await api.getNavigationSessions("testuser");
    expect(sessions).toHaveLength(1);

    // Verify push notification sent
    expect(mockPushService.calls).toHaveLength(1);

    // Simulate mobile accepting
    await api.acceptNavigationSession(sessions[0].id);

    // Verify session status updated
    const session = await api.getNavigationSession(sessions[0].id);
    expect(session.status).toBe("active");
  });
});
```

---

## Future Enhancements

### Phase 2 Features

1. **BLE Beacon Integration**
   - More precise indoor positioning
   - Sub-meter accuracy
   - Works alongside Meraki WAPs

2. **Machine Learning Predictions**
   - Predict device locations based on patterns
   - Anomaly detection for unusual movements
   - Smart routing (avoid crowded paths)

3. **Multi-Building Support**
   - Track devices across campus
   - Inter-building pathfinding
   - Outdoor navigation

4. **AR Collaboration**
   - Multi-user AR sessions
   - Shared annotations
   - Team coordination view

5. **Voice Commands**
   - "Siri, where is my laptop?"
   - Voice-guided navigation
   - Hands-free operation

### Integration Opportunities

- **Microsoft Intune**: Sync device inventory
- **ServiceNow**: Create work orders from device issues
- **Slack/Teams**: Device alerts in chat
- **Badge Systems**: Correlate device with badge swipes
- **CCTV**: Visual verification of device locations

---

## Conclusion

The Cisco Meraki integration with AR navigation represents a significant enhancement to ArxOS's enterprise capabilities. By combining:

- **Network topology** (Meraki)
- **Spatial intelligence** (PostGIS)
- **Version control** (ArxOS core)
- **Mobile AR** (React Native)
- **CLI power tools** (Cobra)

...we create a unified platform that bridges IT infrastructure with physical facilities management in a way no other system currently does.

The bidirectional CLI-to-Mobile workflow is particularly innovative, enabling desktop power users to seamlessly collaborate with mobile field technicians through AR-guided navigation.

**Next Steps**:
1. Review and approve this design document
2. Allocate development resources (2 developers, 11 weeks)
3. Begin Phase 1 implementation
4. Establish pilot program with selected enterprise customer

---

**Document Status**: ✅ Design Complete, Pending Approval
**Estimated Effort**: 2 developers × 11 weeks = 22 developer-weeks
**Target Completion**: Q1 2026

