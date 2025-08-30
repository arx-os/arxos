# SQLite Spatial Database Schema

## Complete Schema for Building Intelligence

This document provides the complete SQLite schema for Arxos, including spatial indexing, BILT tracking, and synchronization support. SQLite with R-tree extensions provides sufficient spatial capabilities for building-scale queries while maintaining simplicity and offline operation.

## Core Tables

### 1. Buildings Table

```sql
-- Buildings are the top-level container
CREATE TABLE buildings (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT DEFAULT 'USA',
    
    -- Building metadata
    building_type TEXT, -- 'school', 'office', 'hospital', 'residential'
    year_built INTEGER,
    total_floors INTEGER,
    total_area_sqft REAL,
    occupancy_type TEXT,
    max_occupancy INTEGER,
    
    -- Boundary and location
    latitude REAL,
    longitude REAL,
    elevation_meters REAL,
    boundary_polygon TEXT, -- WKT format polygon
    
    -- Management
    owner_organization TEXT,
    primary_contact TEXT,
    emergency_contact TEXT,
    
    -- Status tracking
    mapping_started_at TEXT,
    mapping_completed_at TEXT,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    completion_percentage REAL DEFAULT 0.0,
    
    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE INDEX idx_buildings_name ON buildings(name);
CREATE INDEX idx_buildings_type ON buildings(building_type);
CREATE INDEX idx_buildings_location ON buildings(latitude, longitude);
```

### 2. ArxObjects Table

```sql
-- Core spatial objects in buildings
CREATE TABLE arxobjects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    building_id TEXT NOT NULL REFERENCES buildings(id),
    
    -- Location within building
    floor_number INTEGER NOT NULL,
    room_id TEXT,
    room_name TEXT,
    
    -- Object classification
    object_type TEXT NOT NULL, -- 'outlet', 'light', 'door', 'hvac', etc.
    object_subtype TEXT, -- 'gfci_outlet', 'led_panel', 'emergency_exit'
    
    -- 3D Position (millimeters from building origin)
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL, 
    position_z INTEGER NOT NULL,
    
    -- Orientation (quaternion or euler angles)
    rotation_x REAL DEFAULT 0,
    rotation_y REAL DEFAULT 0,
    rotation_z REAL DEFAULT 0,
    
    -- Technical properties (JSON)
    properties TEXT DEFAULT '{}',
    /* Example properties:
    {
        "circuit": "A-12",
        "voltage": 120,
        "amperage": 15,
        "manufacturer": "Leviton",
        "model": "GFCI-15",
        "installed_date": "2023-05-15",
        "last_maintenance": "2024-01-10"
    }
    */
    
    -- Semantic relationships
    connected_to TEXT, -- JSON array of connected object IDs
    part_of_system TEXT, -- System identifier (e.g., "HVAC-Zone-2")
    
    -- Data quality tracking
    confidence_score REAL DEFAULT 1.0,
    verification_status TEXT DEFAULT 'unverified', -- 'unverified', 'verified', 'disputed'
    verification_count INTEGER DEFAULT 0,
    verified_by TEXT, -- JSON array of user IDs who verified
    
    -- Contribution tracking
    created_by TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- BILT rewards
    bilt_awarded INTEGER DEFAULT 0,
    bilt_multipliers TEXT, -- JSON: {"professional": 1.2, "first_mapper": 2.0}
    
    -- Media attachments
    photo_url TEXT,
    photo_thumbnail TEXT,
    notes TEXT,
    
    -- Compliance and safety
    is_safety_critical INTEGER DEFAULT 0,
    is_emergency_equipment INTEGER DEFAULT 0,
    compliance_codes TEXT, -- JSON array of applicable codes
    
    -- Sync support
    sync_version INTEGER DEFAULT 1,
    sync_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0
);

CREATE INDEX idx_arxobjects_building ON arxobjects(building_id, floor_number);
CREATE INDEX idx_arxobjects_type ON arxobjects(object_type);
CREATE INDEX idx_arxobjects_room ON arxobjects(room_id);
CREATE INDEX idx_arxobjects_created_by ON arxobjects(created_by);
CREATE INDEX idx_arxobjects_safety ON arxobjects(is_safety_critical, is_emergency_equipment);
CREATE INDEX idx_arxobjects_sync ON arxobjects(sync_version, sync_timestamp);
```

### 3. Spatial Index (R-Tree)

```sql
-- R-tree for efficient spatial queries
CREATE VIRTUAL TABLE arxobjects_spatial USING rtree(
    id,              -- Matches arxobjects.id
    min_x, max_x,    -- Bounding box X
    min_y, max_y,    -- Bounding box Y
    min_z, max_z     -- Bounding box Z
);

-- Triggers to maintain spatial index
CREATE TRIGGER arxobjects_insert_spatial
AFTER INSERT ON arxobjects
BEGIN
    INSERT INTO arxobjects_spatial (
        id, 
        min_x, max_x,
        min_y, max_y,
        min_z, max_z
    ) VALUES (
        NEW.id,
        NEW.position_x - 100, NEW.position_x + 100,  -- 20cm bounding box
        NEW.position_y - 100, NEW.position_y + 100,
        NEW.position_z - 100, NEW.position_z + 100
    );
END;

CREATE TRIGGER arxobjects_update_spatial
AFTER UPDATE OF position_x, position_y, position_z ON arxobjects
BEGIN
    UPDATE arxobjects_spatial SET
        min_x = NEW.position_x - 100, max_x = NEW.position_x + 100,
        min_y = NEW.position_y - 100, max_y = NEW.position_y + 100,
        min_z = NEW.position_z - 100, max_z = NEW.position_z + 100
    WHERE id = NEW.id;
END;

CREATE TRIGGER arxobjects_delete_spatial
AFTER DELETE ON arxobjects
BEGIN
    DELETE FROM arxobjects_spatial WHERE id = OLD.id;
END;
```

### 4. Users and Contributions

```sql
-- Users who contribute data
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email TEXT UNIQUE,
    name TEXT NOT NULL,
    role TEXT, -- 'maintenance', 'electrician', 'facility_manager', 'admin'
    organization TEXT,
    
    -- Professional credentials
    is_licensed_professional INTEGER DEFAULT 0,
    license_type TEXT,
    license_number TEXT,
    license_expiry TEXT,
    
    -- BILT economics
    bilt_balance INTEGER DEFAULT 0,
    bilt_lifetime_earned INTEGER DEFAULT 0,
    bilt_lifetime_redeemed INTEGER DEFAULT 0,
    
    -- Gamification
    level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    achievements TEXT DEFAULT '[]', -- JSON array
    
    -- Statistics
    total_markups INTEGER DEFAULT 0,
    verified_markups INTEGER DEFAULT 0,
    accuracy_score REAL DEFAULT 1.0,
    
    -- Account management
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_active TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    device_ids TEXT DEFAULT '[]' -- JSON array of device IDs
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization ON users(organization);
CREATE INDEX idx_users_bilt ON users(bilt_balance);

-- Track individual contributions
CREATE TABLE contributions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id),
    arxobject_id TEXT REFERENCES arxobjects(id),
    building_id TEXT NOT NULL REFERENCES buildings(id),
    
    -- Contribution details
    action_type TEXT NOT NULL, -- 'create', 'update', 'verify', 'photo'
    
    -- BILT rewards
    bilt_earned INTEGER NOT NULL,
    bilt_calculation TEXT, -- JSON with calculation breakdown
    
    -- Timing
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    -- Location tracking (for validation)
    device_location_lat REAL,
    device_location_lon REAL,
    device_location_accuracy REAL
);

CREATE INDEX idx_contributions_user ON contributions(user_id, created_at);
CREATE INDEX idx_contributions_building ON contributions(building_id);
CREATE INDEX idx_contributions_date ON contributions(created_at);
```

### 5. BILT Transactions

```sql
-- BILT earning and redemption ledger
CREATE TABLE bilt_transactions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id),
    
    -- Transaction details
    transaction_type TEXT NOT NULL, -- 'earned', 'redeemed', 'bonus', 'penalty'
    amount INTEGER NOT NULL, -- Positive for credit, negative for debit
    balance_after INTEGER NOT NULL,
    
    -- Context
    description TEXT NOT NULL,
    reference_type TEXT, -- 'contribution', 'redemption', 'achievement'
    reference_id TEXT, -- ID of related record
    
    -- Redemption details (if applicable)
    redemption_item TEXT,
    redemption_status TEXT, -- 'pending', 'processing', 'completed'
    redemption_tracking TEXT,
    
    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bilt_user ON bilt_transactions(user_id, created_at);
CREATE INDEX idx_bilt_type ON bilt_transactions(transaction_type);

-- Redemption catalog
CREATE TABLE redemption_catalog (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    category TEXT NOT NULL, -- 'tools', 'gift_cards', 'training', 'charity'
    name TEXT NOT NULL,
    description TEXT,
    bilt_cost INTEGER NOT NULL,
    retail_value REAL,
    
    -- Availability
    is_available INTEGER DEFAULT 1,
    quantity_available INTEGER,
    quantity_redeemed INTEGER DEFAULT 0,
    
    -- Fulfillment
    fulfillment_type TEXT, -- 'digital', 'physical', 'service'
    fulfillment_details TEXT, -- JSON with provider info
    
    -- Images
    image_url TEXT,
    
    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_redemption_category ON redemption_catalog(category);
CREATE INDEX idx_redemption_available ON redemption_catalog(is_available);
```

### 6. Sync and Conflict Resolution

```sql
-- Track sync state between devices
CREATE TABLE sync_log (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    device_id TEXT NOT NULL,
    
    -- Sync window
    sync_started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    sync_completed_at TEXT,
    
    -- What was synced
    objects_sent INTEGER DEFAULT 0,
    objects_received INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    
    -- Status
    sync_status TEXT DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    
    -- Metadata
    last_sync_version INTEGER,
    current_sync_version INTEGER
);

CREATE INDEX idx_sync_device ON sync_log(device_id, sync_started_at);

-- Conflict resolution for CRDT
CREATE TABLE sync_conflicts (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    arxobject_id TEXT NOT NULL,
    
    -- Conflicting versions
    local_version TEXT, -- JSON of local object
    remote_version TEXT, -- JSON of remote object
    
    -- Resolution
    resolution_strategy TEXT, -- 'last_write_wins', 'merge', 'manual'
    resolved_version TEXT, -- JSON of final version
    resolved_by TEXT,
    resolved_at TEXT,
    
    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Spatial Queries

### Find Objects Near Point

```sql
-- Find all objects within 5 meters of a point
SELECT 
    a.id,
    a.object_type,
    a.properties,
    sqrt(
        power(a.position_x - :x, 2) + 
        power(a.position_y - :y, 2) + 
        power(a.position_z - :z, 2)
    ) / 1000.0 as distance_meters
FROM arxobjects a
JOIN arxobjects_spatial s ON a.id = s.id
WHERE 
    s.min_x <= :x + 5000 AND s.max_x >= :x - 5000
    AND s.min_y <= :y + 5000 AND s.max_y >= :y - 5000
    AND s.min_z <= :z + 5000 AND s.max_z >= :z - 5000
    AND a.building_id = :building_id
    AND a.is_deleted = 0
ORDER BY distance_meters
LIMIT 20;
```

### Emergency Exit Routes

```sql
-- Find nearest emergency exits from a location
WITH RECURSIVE exit_path AS (
    -- Starting point
    SELECT 
        id, object_type, position_x, position_y, position_z,
        0 as path_distance,
        json_array(id) as path
    FROM arxobjects
    WHERE id = :start_location_id
    
    UNION ALL
    
    -- Find connected spaces
    SELECT 
        a.id, a.object_type, a.position_x, a.position_y, a.position_z,
        p.path_distance + sqrt(
            power(a.position_x - p.position_x, 2) + 
            power(a.position_y - p.position_y, 2)
        ) / 1000.0 as path_distance,
        json_insert(p.path, '$[#]', a.id) as path
    FROM arxobjects a
    JOIN exit_path p ON (
        -- Objects are connected if within 10 meters
        sqrt(
            power(a.position_x - p.position_x, 2) + 
            power(a.position_y - p.position_y, 2)
        ) <= 10000
    )
    WHERE 
        a.object_type IN ('door', 'corridor', 'emergency_exit')
        AND a.id NOT IN (SELECT value FROM json_each(p.path))
        AND p.path_distance < 100 -- Max 100 meters
)
SELECT * FROM exit_path
WHERE object_type = 'emergency_exit'
ORDER BY path_distance
LIMIT 3;
```

### Building Completion Status

```sql
-- Calculate building mapping completion
SELECT 
    b.name as building_name,
    b.total_floors,
    COUNT(DISTINCT a.floor_number) as mapped_floors,
    COUNT(DISTINCT a.room_id) as mapped_rooms,
    COUNT(a.id) as total_objects,
    COUNT(CASE WHEN a.verification_status = 'verified' THEN 1 END) as verified_objects,
    ROUND(
        COUNT(CASE WHEN a.verification_status = 'verified' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(a.id), 0), 
        1
    ) as verification_percentage,
    COUNT(DISTINCT a.created_by) as contributors,
    SUM(a.bilt_awarded) as total_bilt_awarded
FROM buildings b
LEFT JOIN arxobjects a ON b.id = a.building_id AND a.is_deleted = 0
WHERE b.id = :building_id
GROUP BY b.id;
```

### Compliance Reporting

```sql
-- Fire safety compliance check
SELECT 
    floor_number,
    room_name,
    COUNT(CASE WHEN object_type = 'fire_extinguisher' THEN 1 END) as fire_extinguishers,
    COUNT(CASE WHEN object_type = 'emergency_exit' THEN 1 END) as emergency_exits,
    COUNT(CASE WHEN object_type = 'fire_alarm' THEN 1 END) as fire_alarms,
    COUNT(CASE WHEN object_type = 'sprinkler' THEN 1 END) as sprinklers,
    MAX(CASE 
        WHEN object_type = 'fire_extinguisher' 
        THEN json_extract(properties, '$.last_inspection')
    END) as last_extinguisher_inspection
FROM arxobjects
WHERE 
    building_id = :building_id
    AND is_safety_critical = 1
    AND is_deleted = 0
GROUP BY floor_number, room_name
ORDER BY floor_number, room_name;
```

## Performance Optimizations

### Indexes for Common Queries

```sql
-- Compound indexes for performance
CREATE INDEX idx_arxobjects_building_floor_type 
    ON arxobjects(building_id, floor_number, object_type);

CREATE INDEX idx_arxobjects_safety_building 
    ON arxobjects(building_id, is_safety_critical, is_emergency_equipment);

CREATE INDEX idx_contributions_user_date 
    ON contributions(user_id, created_at DESC);

-- Covering index for BILT calculations
CREATE INDEX idx_contributions_bilt 
    ON contributions(user_id, bilt_earned, created_at);
```

### Materialized Views (Using Triggers)

```sql
-- Cache building statistics
CREATE TABLE building_stats (
    building_id TEXT PRIMARY KEY,
    total_objects INTEGER DEFAULT 0,
    verified_objects INTEGER DEFAULT 0,
    total_contributors INTEGER DEFAULT 0,
    total_bilt_awarded INTEGER DEFAULT 0,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Update stats on changes
CREATE TRIGGER update_building_stats
AFTER INSERT ON arxobjects
BEGIN
    INSERT OR REPLACE INTO building_stats (
        building_id,
        total_objects,
        verified_objects,
        total_bilt_awarded,
        last_updated
    )
    SELECT 
        NEW.building_id,
        COUNT(*),
        COUNT(CASE WHEN verification_status = 'verified' THEN 1 END),
        SUM(bilt_awarded),
        CURRENT_TIMESTAMP
    FROM arxobjects
    WHERE building_id = NEW.building_id AND is_deleted = 0;
END;
```

## Database Configuration

```sql
-- Optimize SQLite for mobile/embedded use
PRAGMA journal_mode = WAL;           -- Write-ahead logging
PRAGMA synchronous = NORMAL;         -- Balance safety/speed
PRAGMA cache_size = -64000;          -- 64MB cache
PRAGMA temp_store = MEMORY;          -- Use memory for temp tables
PRAGMA mmap_size = 268435456;        -- 256MB memory-mapped I/O
PRAGMA foreign_keys = ON;            -- Enforce relationships
PRAGMA recursive_triggers = ON;      -- For CRDT sync
PRAGMA application_id = 0x41727878;  -- 'Arxx' identifier
PRAGMA user_version = 1;              -- Schema version
```

---

*This schema supports offline-first operation, spatial queries, BILT economics, and conflict-free synchronization for distributed building intelligence.*