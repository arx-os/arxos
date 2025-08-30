-- Initial Arxos database schema for spatial building intelligence
-- Based on SQLite with R-tree spatial indexing for stadium-scale performance

-- Enable spatial extensions
PRAGMA foreign_keys = ON;

-- Buildings table - Top-level building containers
CREATE TABLE IF NOT EXISTS buildings (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    square_footage INTEGER,
    floors INTEGER,
    building_type TEXT, -- 'office', 'stadium', 'school', 'hospital'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ArxObjects table - Core 13-byte compressed spatial objects  
CREATE TABLE IF NOT EXISTS arxobjects (
    id INTEGER PRIMARY KEY, -- Maps to ArxObject.id (u16)
    building_id TEXT NOT NULL,
    object_type INTEGER NOT NULL, -- Maps to ArxObject.object_type (u8)
    
    -- Position data (millimeter precision)
    position_x INTEGER NOT NULL, -- Maps to ArxObject.x (u16) 
    position_y INTEGER NOT NULL, -- Maps to ArxObject.y (u16)
    position_z INTEGER NOT NULL, -- Maps to ArxObject.z (u16)
    
    -- Property data (4 bytes from ArxObject.properties)
    properties BLOB NOT NULL, -- Raw 4-byte property data
    properties_json TEXT, -- Human-readable expansion of properties
    
    -- Metadata for human-in-the-loop workflow
    created_by TEXT, -- User/contractor who marked this object
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified_by TEXT, -- User who verified accuracy  
    verified_at DATETIME,
    confidence_score REAL DEFAULT 1.0,
    
    -- Foreign key constraint
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- Spatial index for fast geometric queries (R-tree)
CREATE VIRTUAL TABLE IF NOT EXISTS arxobjects_spatial USING rtree(
    id INTEGER PRIMARY KEY,
    min_x REAL, max_x REAL,
    min_y REAL, max_y REAL, 
    min_z REAL, max_z REAL
);

-- BILT token transactions for contractor incentives
CREATE TABLE IF NOT EXISTS bilt_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    object_id INTEGER,
    transaction_type TEXT NOT NULL, -- 'earned', 'spent', 'verified'
    amount INTEGER NOT NULL, -- BILT points (signed integer)
    description TEXT,
    building_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES arxobjects(id) ON DELETE SET NULL,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- User management for contractors and professionals
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL, -- 'contractor', 'electrician', 'facilities_manager'
    license_number TEXT, -- Professional license for verification
    bilt_balance INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME
);

-- Building access permissions  
CREATE TABLE IF NOT EXISTS building_access (
    building_id TEXT,
    user_id TEXT,
    access_level TEXT NOT NULL, -- 'read', 'markup', 'admin'
    granted_by TEXT,
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (building_id, user_id),
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Progressive detail accumulation system
CREATE TABLE IF NOT EXISTS detail_levels (
    object_id INTEGER PRIMARY KEY,
    material REAL DEFAULT 0.0, -- 0.0 to 1.0 completeness
    systems REAL DEFAULT 0.0,
    historical REAL DEFAULT 0.0, 
    simulation REAL DEFAULT 0.0,
    predictive REAL DEFAULT 0.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES arxobjects(id) ON DELETE CASCADE
);

-- Mesh sensor telemetry data
CREATE TABLE IF NOT EXISTS sensor_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER NOT NULL, -- ESP32 sensor node ID
    sensor_type INTEGER NOT NULL, -- Temperature, occupancy, power, etc
    
    -- Position (matches sensor deployment location)
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL, 
    position_z INTEGER NOT NULL,
    
    -- 4-byte sensor data (from 13-byte packet)
    data_bytes BLOB NOT NULL, -- Raw 4-byte sensor reading
    parsed_value REAL, -- Human-readable value (temperature, etc)
    unit TEXT, -- 'celsius', 'percent', 'watts', 'people'
    
    building_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- BIM file integration tracking
CREATE TABLE IF NOT EXISTS bim_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL, -- 'pdf', 'ifc', 'dwg', 'rvt'
    file_hash TEXT NOT NULL, -- For change detection
    objects_extracted INTEGER DEFAULT 0,
    last_processed DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- Indexes for performance at stadium scale
CREATE INDEX IF NOT EXISTS idx_arxobjects_building ON arxobjects(building_id);
CREATE INDEX IF NOT EXISTS idx_arxobjects_type ON arxobjects(object_type);
CREATE INDEX IF NOT EXISTS idx_arxobjects_created ON arxobjects(created_at);
CREATE INDEX IF NOT EXISTS idx_bilt_user ON bilt_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_sensor_building ON sensor_telemetry(building_id);
CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_telemetry(timestamp);

-- Triggers to maintain spatial index
CREATE TRIGGER IF NOT EXISTS arxobjects_spatial_insert 
AFTER INSERT ON arxobjects BEGIN
    INSERT INTO arxobjects_spatial VALUES (
        NEW.id,
        NEW.position_x, NEW.position_x,
        NEW.position_y, NEW.position_y,
        NEW.position_z, NEW.position_z
    );
END;

CREATE TRIGGER IF NOT EXISTS arxobjects_spatial_update
AFTER UPDATE ON arxobjects BEGIN  
    UPDATE arxobjects_spatial SET
        min_x = NEW.position_x, max_x = NEW.position_x,
        min_y = NEW.position_y, max_y = NEW.position_y,
        min_z = NEW.position_z, max_z = NEW.position_z
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS arxobjects_spatial_delete
AFTER DELETE ON arxobjects BEGIN
    DELETE FROM arxobjects_spatial WHERE id = OLD.id;
END;

-- Sample data for development (stadium-scale example)
INSERT OR IGNORE INTO buildings VALUES (
    'raymond-james-stadium',
    'Raymond James Stadium', 
    '4201 N Dale Mabry Hwy, Tampa, FL 33607',
    1900000, -- 1.9M square feet
    4, -- 4 levels
    'stadium',
    '2024-01-01 00:00:00',
    '2024-01-01 00:00:00'
);

INSERT OR IGNORE INTO users VALUES (
    'contractor-001',
    'mike@tampabayelectric.com',
    'electrician',
    'EC123456',
    0,
    '2024-01-01 00:00:00',
    '2024-01-01 00:00:00'
);

INSERT OR IGNORE INTO building_access VALUES (
    'raymond-james-stadium',
    'contractor-001', 
    'markup',
    'admin',
    '2024-01-01 00:00:00'
);