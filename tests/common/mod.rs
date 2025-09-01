//! Common test utilities and fixtures for Arxos integration tests

use arxos_core::database::ArxDatabase;
use arxos_core::arxobject::{ArxObject, object_types};
use std::path::Path;
use std::sync::Once;

static INIT: Once = Once::new();

/// Initialize test environment (run once)
pub fn init_test_env() {
    INIT.call_once(|| {
        // Set up test logging
        let _ = env_logger::builder()
            .is_test(true)
            .try_init();
    });
}

/// Create a test database with schema initialized
pub fn create_test_database() -> ArxDatabase {
    init_test_env();
    
    // Use in-memory database for tests
    let db = ArxDatabase::new(Path::new(":memory:"))
        .expect("Failed to create test database");
    
    // Initialize schema
    db.init_schema()
        .expect("Failed to initialize database schema");
    
    db
}

/// Create a test database with sample data
pub fn create_populated_database() -> ArxDatabase {
    let db = create_test_database();
    
    // Add a test building
    let building = arxos_core::database::Building {
        name: "Test Building".to_string(),
        address: Some("123 Test St".to_string()),
        origin_lat: Some(37.7749),
        origin_lon: Some(-122.4194),
        origin_elevation: Some(0.0),
        width_mm: 50000,  // 50m
        depth_mm: 30000,  // 30m
        height_mm: 15000, // 15m (5 floors)
    };
    
    let building_id = db.insert_building(&building)
        .expect("Failed to insert test building");
    
    // Add some test ArxObjects
    let test_objects = vec![
        ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300),
        ArxObject::new(0x0002, object_types::LIGHT, 2000, 2000, 2800),
        ArxObject::new(0x0003, object_types::DOOR, 3000, 1000, 0),
        ArxObject::new(0x0004, object_types::WINDOW, 4000, 2000, 1000),
        ArxObject::new(0x0005, object_types::THERMOSTAT, 5000, 3000, 1500),
    ];
    
    for obj in test_objects {
        db.insert_arxobject(&arxos_core::database::ArxObjectDB {
            id: obj.id as i32,
            object_type: obj.object_type,
            x: obj.x,
            y: obj.y,
            z: obj.z,
            properties: obj.properties.to_vec(),
            building_id,
            floor_number: Some(1),
            room_id: None,
            source_points: Some(1000),
            compressed_size: Some(13),
            compression_ratio: Some(1000.0),
            semantic_confidence: Some(0.95),
            created_by: Some("test".to_string()),
        }).expect("Failed to insert test object");
    }
    
    db
}

/// Create sample ArxObjects for testing
pub fn create_test_arxobjects() -> Vec<ArxObject> {
    vec![
        ArxObject::new(0x0001, object_types::OUTLET, 1000, 2000, 300),
        ArxObject::new(0x0002, object_types::LIGHT, 3000, 4000, 2800),
        ArxObject::new(0x0003, object_types::DOOR, 5000, 1000, 0),
        ArxObject::new(0x0004, object_types::WINDOW, 2000, 4000, 1000),
        ArxObject::new(0x0005, object_types::THERMOSTAT, 4000, 3000, 1500),
        ArxObject::new(0x0006, object_types::FIRE_ALARM, 3000, 3000, 2900),
        ArxObject::new(0x0007, object_types::EMERGENCY_EXIT, 6000, 0, 0),
        ArxObject::new(0x0008, object_types::AIR_VENT, 2500, 2500, 2700),
        ArxObject::new(0x0009, object_types::SMOKE_DETECTOR, 3500, 3500, 2950),
        ArxObject::new(0x000A, object_types::SPRINKLER, 4500, 4500, 3000),
    ]
}

/// Assert two ArxObjects are equal (handling packed struct issues)
pub fn assert_arxobject_eq(actual: &ArxObject, expected: &ArxObject) {
    // Copy values from packed structs to avoid alignment issues
    let actual_id = actual.id;
    let actual_type = actual.object_type;
    let actual_x = actual.x;
    let actual_y = actual.y;
    let actual_z = actual.z;
    let actual_props = actual.properties;
    
    let expected_id = expected.id;
    let expected_type = expected.object_type;
    let expected_x = expected.x;
    let expected_y = expected.y;
    let expected_z = expected.z;
    let expected_props = expected.properties;
    
    assert_eq!(actual_id, expected_id, "ID mismatch");
    assert_eq!(actual_type, expected_type, "Type mismatch");
    assert_eq!(actual_x, expected_x, "X coordinate mismatch");
    assert_eq!(actual_y, expected_y, "Y coordinate mismatch");
    assert_eq!(actual_z, expected_z, "Z coordinate mismatch");
    assert_eq!(actual_props, expected_props, "Properties mismatch");
}

/// Calculate compression ratio for testing
pub fn calculate_compression_ratio(original_size: usize, compressed_size: usize) -> f32 {
    original_size as f32 / compressed_size as f32
}

/// Generate a building floor plan for testing
pub fn generate_test_floor_plan() -> String {
    r#"
╔════════════════════════════════════════╗
║         FLOOR 1 - TEST BUILDING        ║
╠════════════════════════════════════════╣
║ ┌──────────┐  ┌──────────┐            ║
║ │   101    │  │   102    │            ║
║ │ Office   │  │ Lab      │            ║
║ │  [O][L]  │  │  [O][L]  │            ║
║ └────| |───┘  └────| |───┘            ║
║                                        ║
║ ┌──────────┐  ┌──────────┐            ║
║ │   103    │  │   104    │            ║
║ │ Storage  │  │ Meeting  │            ║
║ │    [L]   │  │  [O][L]  │            ║
║ └────| |───┘  └────| |───┘            ║
╚════════════════════════════════════════╝
Legend: [O]=Outlet [L]=Light | |=Door
"#.to_string()
}