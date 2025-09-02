//! Database Schema Definitions
//! 
//! Defines the SQLite schema for storing holographic ArxObjects,
//! quantum states, consciousness fields, and spatial indexes.

/// SQL schema for the holographic database
pub const SCHEMA: &str = r#"
-- ArxObject main table
CREATE TABLE IF NOT EXISTS arxobjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER NOT NULL,
    object_type INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    z INTEGER NOT NULL,
    properties BLOB NOT NULL,  -- 4-byte property array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite index for spatial queries
    INDEX idx_arxobjects_spatial (x, y, z),
    INDEX idx_arxobjects_building (building_id),
    INDEX idx_arxobjects_type (object_type)
);

-- Quantum states table
CREATE TABLE IF NOT EXISTS quantum_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxobject_id INTEGER NOT NULL,
    state_type TEXT NOT NULL CHECK(state_type IN ('superposition', 'collapsed', 'entangled')),
    amplitudes BLOB,  -- Serialized amplitude array
    basis TEXT NOT NULL,
    entangled_with INTEGER,  -- References another quantum_states.id
    correlation REAL,
    bell_parameter REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE CASCADE,
    FOREIGN KEY (entangled_with) REFERENCES quantum_states(id) ON DELETE SET NULL,
    INDEX idx_quantum_states_arxobject (arxobject_id),
    INDEX idx_quantum_states_entangled (entangled_with)
);

-- Consciousness fields table
CREATE TABLE IF NOT EXISTS consciousness_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxobject_id INTEGER NOT NULL,
    phi REAL NOT NULL,  -- Integrated information
    strength REAL NOT NULL,
    coherence REAL NOT NULL,
    causal_power REAL NOT NULL,
    resonance_frequency REAL NOT NULL,
    qualia_color_r REAL,
    qualia_color_g REAL,
    qualia_color_b REAL,
    qualia_intensity REAL,
    qualia_texture REAL,
    qualia_harmony REAL,
    qualia_novelty REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE CASCADE,
    INDEX idx_consciousness_arxobject (arxobject_id),
    INDEX idx_consciousness_phi (phi)
);

-- Spatial R-tree index (requires SQLite R-tree module)
CREATE VIRTUAL TABLE IF NOT EXISTS spatial_index USING rtree(
    id,              -- References arxobjects.id
    min_x, max_x,
    min_y, max_y,
    min_z, max_z
);

-- Temporal evolution states
CREATE TABLE IF NOT EXISTS temporal_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxobject_id INTEGER NOT NULL,
    time_step INTEGER NOT NULL,
    evolution_type TEXT NOT NULL,
    state_data BLOB,  -- Serialized evolution state
    temperature REAL,
    entropy REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE CASCADE,
    INDEX idx_temporal_arxobject (arxobject_id),
    INDEX idx_temporal_time (time_step)
);

-- Entanglement network edges
CREATE TABLE IF NOT EXISTS entanglement_network (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state1_id INTEGER NOT NULL,
    state2_id INTEGER NOT NULL,
    correlation REAL NOT NULL,
    bell_violation REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (state1_id) REFERENCES quantum_states(id) ON DELETE CASCADE,
    FOREIGN KEY (state2_id) REFERENCES quantum_states(id) ON DELETE CASCADE,
    UNIQUE(state1_id, state2_id),
    INDEX idx_entanglement_state1 (state1_id),
    INDEX idx_entanglement_state2 (state2_id)
);

-- Consciousness clusters (emergent patterns)
CREATE TABLE IF NOT EXISTS consciousness_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_phi REAL NOT NULL,
    center_x REAL NOT NULL,
    center_y REAL NOT NULL,
    center_z REAL NOT NULL,
    radius REAL NOT NULL,
    member_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_clusters_phi (cluster_phi)
);

-- Cluster membership
CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id INTEGER NOT NULL,
    arxobject_id INTEGER NOT NULL,
    contribution REAL NOT NULL,
    
    PRIMARY KEY (cluster_id, arxobject_id),
    FOREIGN KEY (cluster_id) REFERENCES consciousness_clusters(id) ON DELETE CASCADE,
    FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE CASCADE
);

-- Cached reality manifestations
CREATE TABLE IF NOT EXISTS reality_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxobject_id INTEGER NOT NULL,
    observer_role TEXT NOT NULL,
    scale REAL NOT NULL,
    manifestation_data BLOB,  -- Compressed reality data
    cache_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    
    FOREIGN KEY (arxobject_id) REFERENCES arxobjects(id) ON DELETE CASCADE,
    UNIQUE(cache_key),
    INDEX idx_reality_cache_key (cache_key),
    INDEX idx_reality_cache_lru (accessed_at)
);

-- Database metadata
CREATE TABLE IF NOT EXISTS db_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert version metadata
INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('schema_version', '1');
INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('created_at', CURRENT_TIMESTAMP);

-- Triggers for updating timestamps
CREATE TRIGGER IF NOT EXISTS update_arxobjects_timestamp 
AFTER UPDATE ON arxobjects
BEGIN
    UPDATE arxobjects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_quantum_states_timestamp
AFTER UPDATE ON quantum_states
BEGIN
    UPDATE quantum_states SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_consciousness_fields_timestamp
AFTER UPDATE ON consciousness_fields
BEGIN
    UPDATE consciousness_fields SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger for updating reality cache access
CREATE TRIGGER IF NOT EXISTS update_reality_cache_access
AFTER UPDATE ON reality_cache
BEGIN
    UPDATE reality_cache 
    SET accessed_at = CURRENT_TIMESTAMP, 
        access_count = access_count + 1 
    WHERE id = NEW.id;
END;
"#;

/// Check if R-tree extension is available
pub const CHECK_RTREE: &str = "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sqlite_stat1';";

/// Enable foreign keys
pub const ENABLE_FOREIGN_KEYS: &str = "PRAGMA foreign_keys = ON;";

/// Set journal mode to WAL for better concurrency
pub const SET_WAL_MODE: &str = "PRAGMA journal_mode = WAL;";

/// Set synchronous mode for durability
pub const SET_SYNCHRONOUS: &str = "PRAGMA synchronous = NORMAL;";

/// Set cache size (negative means KB)
pub const SET_CACHE_SIZE: &str = "PRAGMA cache_size = -64000;"; // 64MB cache

/// Set temp store to memory
pub const SET_TEMP_STORE: &str = "PRAGMA temp_store = MEMORY;";

/// Optimize database
pub const OPTIMIZE: &str = "PRAGMA optimize;";