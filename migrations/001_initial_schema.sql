-- Arxos Database Schema v1.0
-- Foundation for building intelligence storage
-- Pure SQLite implementation with spatial indexing

-- Buildings table - top-level spatial containers
CREATE TABLE IF NOT EXISTS buildings (
    id UUID PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    -- Origin point for local coordinate system (NW corner at ground level)
    origin_lat REAL,
    origin_lon REAL,
    origin_elevation REAL DEFAULT 0,
    -- Building dimensions in millimeters
    width_mm INTEGER NOT NULL,  -- X-axis extent
    depth_mm INTEGER NOT NULL,  -- Y-axis extent  
    height_mm INTEGER NOT NULL, -- Z-axis extent
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bim_file_path TEXT,
    validation_status VARCHAR(50) DEFAULT 'unvalidated',
    last_validated TIMESTAMP,
    CONSTRAINT valid_dimensions CHECK (width_mm > 0 AND depth_mm > 0 AND height_mm > 0)
);

-- ArxObjects table - core 13-byte objects with extended metadata
CREATE TABLE IF NOT EXISTS arxobjects (
    -- Core 13-byte fields
    id INTEGER PRIMARY KEY,  -- 16-bit in protocol, but we use full int for DB
    object_type INTEGER NOT NULL,  -- 8-bit type from protocol spec
    x INTEGER NOT NULL,  -- millimeters from origin (16-bit: 0-65535)
    y INTEGER NOT NULL,  -- millimeters from origin (16-bit: 0-65535)
    z INTEGER NOT NULL,  -- millimeters from origin (16-bit: 0-65535)
    properties BLOB,     -- 4-byte property array from protocol
    
    -- Extended fields for rich data
    building_id UUID NOT NULL,
    floor_number INTEGER,
    room_id UUID,
    
    -- Semantic compression metadata
    source_points INTEGER,  -- Original point cloud size
    compressed_size INTEGER,  -- Compressed representation size
    compression_ratio REAL,
    semantic_confidence REAL DEFAULT 1.0,
    
    -- Reality validation
    last_verified TIMESTAMP,
    validation_status VARCHAR(50) DEFAULT 'unverified', -- verified, modified, missing, new
    validation_confidence REAL,
    validation_source VARCHAR(50), -- lidar, human, sensor, bim
    validated_by VARCHAR(255),
    
    -- Audit trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    
    -- Constraints
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
    CONSTRAINT valid_coordinates CHECK (x >= 0 AND x <= 65535 AND y >= 0 AND y <= 65535 AND z >= 0 AND z <= 65535),
    CONSTRAINT valid_type CHECK (object_type >= 0 AND object_type <= 255)
);

-- Rooms table - spatial containers within buildings
CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    building_id UUID NOT NULL,
    floor_number INTEGER NOT NULL,
    room_number VARCHAR(50),
    name VARCHAR(255),
    
    -- Bounding box in building coordinates (mm)
    min_x INTEGER NOT NULL,
    min_y INTEGER NOT NULL,
    min_z INTEGER NOT NULL,
    max_x INTEGER NOT NULL,
    max_y INTEGER NOT NULL,
    max_z INTEGER NOT NULL,
    
    -- Properties
    room_type VARCHAR(100),  -- office, classroom, mechanical, etc.
    area_sqm REAL,
    occupancy_limit INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    CONSTRAINT valid_bbox CHECK (min_x < max_x AND min_y < max_y AND min_z < max_z)
);

-- Detail chunks for progressive enhancement (slow-bleed architecture)
CREATE TABLE IF NOT EXISTS detail_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxobject_id INTEGER NOT NULL,
    chunk_type INTEGER NOT NULL,  -- See ChunkType enum in protocol
    chunk_id INTEGER NOT NULL,     -- Sequence number for ordering
    chunk_data BLOB NOT NULL,      -- 8-byte payload from protocol
    
    -- Metadata
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_node_id INTEGER,
    
    FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE CASCADE,
    UNIQUE(arxobject_id, chunk_type, chunk_id)
);

-- BILT token tracking for gamification
CREATE TABLE IF NOT EXISTS bilt_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- mark_object, verify, achievement, etc.
    arxobject_id INTEGER,
    points_earned INTEGER NOT NULL,
    
    -- Multipliers applied
    first_mapper_bonus REAL DEFAULT 1.0,
    professional_bonus REAL DEFAULT 1.0,
    photo_bonus REAL DEFAULT 1.0,
    verification_bonus REAL DEFAULT 1.0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    
    FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE SET NULL
);

-- User BILT balances (materialized view for performance)
CREATE TABLE IF NOT EXISTS bilt_balances (
    user_id VARCHAR(255) PRIMARY KEY,
    total_earned INTEGER DEFAULT 0,
    total_redeemed INTEGER DEFAULT 0,
    current_balance INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation reports for BIM daemon
CREATE TABLE IF NOT EXISTS validation_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id UUID NOT NULL,
    validation_type VARCHAR(50),  -- reality_check, compliance, bim_sync
    
    -- Results
    total_objects INTEGER,
    verified_objects INTEGER,
    modified_objects INTEGER,
    missing_objects INTEGER,
    new_objects INTEGER,
    accuracy_score REAL,
    
    -- Compliance specific
    compliance_violations INTEGER DEFAULT 0,
    compliance_status VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_by VARCHAR(255),
    report_data JSON,  -- Detailed findings
    
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- BIM file tracking for daemon mode
CREATE TABLE IF NOT EXISTS bim_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id UUID NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_type VARCHAR(20),  -- pdf, ifc, dwg, rvt
    file_hash VARCHAR(64),  -- SHA-256 for change detection
    
    -- Processing status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, error
    last_processed TIMESTAMP,
    last_modified TIMESTAMP,
    
    -- Extracted data
    extracted_objects INTEGER,
    extraction_confidence REAL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- Spatial indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_arxobjects_building ON arxobjects(building_id);
CREATE INDEX IF NOT EXISTS idx_arxobjects_coords ON arxobjects(x, y, z);
CREATE INDEX IF NOT EXISTS idx_arxobjects_type ON arxobjects(object_type);
CREATE INDEX IF NOT EXISTS idx_arxobjects_floor ON arxobjects(floor_number);
CREATE INDEX IF NOT EXISTS idx_arxobjects_room ON arxobjects(room_id);
CREATE INDEX IF NOT EXISTS idx_arxobjects_validation ON arxobjects(validation_status);

CREATE INDEX IF NOT EXISTS idx_rooms_building ON rooms(building_id);
CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms(building_id, floor_number);
CREATE INDEX IF NOT EXISTS idx_rooms_bbox ON rooms(min_x, min_y, max_x, max_y);

CREATE INDEX IF NOT EXISTS idx_detail_chunks_object ON detail_chunks(arxobject_id, chunk_type);
CREATE INDEX IF NOT EXISTS idx_bilt_transactions_user ON bilt_transactions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_validation_reports_building ON validation_reports(building_id, created_at);

-- Triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_building_timestamp 
AFTER UPDATE ON buildings 
BEGIN
    UPDATE buildings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_arxobject_timestamp 
AFTER UPDATE ON arxobjects 
BEGIN
    UPDATE arxobjects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_room_timestamp 
AFTER UPDATE ON rooms 
BEGIN
    UPDATE rooms SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to maintain BILT balance
CREATE TRIGGER IF NOT EXISTS update_bilt_balance 
AFTER INSERT ON bilt_transactions 
BEGIN
    INSERT INTO bilt_balances (user_id, total_earned, current_balance)
    VALUES (NEW.user_id, NEW.points_earned, NEW.points_earned)
    ON CONFLICT(user_id) DO UPDATE SET
        total_earned = total_earned + NEW.points_earned,
        current_balance = current_balance + NEW.points_earned,
        last_updated = CURRENT_TIMESTAMP;
END;