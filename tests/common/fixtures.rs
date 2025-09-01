//! Test fixtures for Arxos integration tests

use arxos_core::arxobject::{ArxObject, object_types};
use arxos_core::document_parser::{BuildingPlan, FloorPlan, Room, Equipment, EquipmentType, Point3D, BoundingBox, BuildingMetadata};
use std::collections::HashMap;

/// Create a sample building plan for testing
pub fn create_test_building_plan() -> BuildingPlan {
    BuildingPlan {
        name: "Jefferson Elementary School".to_string(),
        floors: vec![
            create_test_floor_plan(1),
            create_test_floor_plan(2),
        ],
        arxobjects: vec![],
        metadata: BuildingMetadata {
            address: Some("123 Education Blvd".to_string()),
            total_sqft: 25000.0,
            year_built: Some(1965),
            building_type: Some("Educational".to_string()),
            occupancy_class: Some("E".to_string()),
        },
    }
}

/// Create a sample floor plan
pub fn create_test_floor_plan(floor_number: i8) -> FloorPlan {
    FloorPlan {
        floor_number,
        rooms: vec![
            Room {
                number: format!("{}01", floor_number * 100 + 1),
                name: "Classroom A".to_string(),
                area_sqft: 800.0,
                bounds: BoundingBox {
                    min: Point3D { x: 0.0, y: 0.0, z: (floor_number as f32 - 1.0) * 3.0 },
                    max: Point3D { x: 10.0, y: 8.0, z: (floor_number as f32) * 3.0 },
                },
                equipment_count: 4,
            },
            Room {
                number: format!("{}02", floor_number * 100 + 1),
                name: "Science Lab".to_string(),
                area_sqft: 1200.0,
                bounds: BoundingBox {
                    min: Point3D { x: 10.0, y: 0.0, z: (floor_number as f32 - 1.0) * 3.0 },
                    max: Point3D { x: 22.0, y: 10.0, z: (floor_number as f32) * 3.0 },
                },
                equipment_count: 8,
            },
        ],
        ascii_layout: generate_floor_ascii(floor_number),
        equipment: vec![
            Equipment {
                equipment_type: EquipmentType::ElectricalOutlet,
                location: Point3D { x: 2.0, y: 1.0, z: 0.3 },
                room_number: Some(format!("{}01", floor_number * 100 + 1)),
                properties: HashMap::new(),
            },
            Equipment {
                equipment_type: EquipmentType::LightFixture,
                location: Point3D { x: 5.0, y: 4.0, z: 2.8 },
                room_number: Some(format!("{}01", floor_number * 100 + 1)),
                properties: HashMap::new(),
            },
            Equipment {
                equipment_type: EquipmentType::EmergencyExit,
                location: Point3D { x: 0.0, y: 8.0, z: 0.0 },
                room_number: None,
                properties: HashMap::new(),
            },
        ],
    }
}

fn generate_floor_ascii(floor_number: i8) -> String {
    format!(r#"
╔════════════════════════════════════════╗
║         FLOOR {} - TEST LAYOUT         ║
╠════════════════════════════════════════╣
║ ┌──────────┐  ┌──────────────┐        ║
║ │  {}01    │  │    {}02      │        ║
║ │ Class A  │  │ Science Lab  │        ║
║ │  [O][L]  │  │  [O][L][V]   │        ║
║ └────| |───┘  └──────| |─────┘        ║
║                                        ║
║           [E] Emergency Exit           ║
╚════════════════════════════════════════╝
"#, floor_number, floor_number * 100 + 1, floor_number * 100 + 1)
}

/// Create sample mesh packet data
pub fn create_test_mesh_packet() -> Vec<u8> {
    let obj = ArxObject::new(0x1234, object_types::OUTLET, 5000, 3000, 300);
    let mut packet = vec![0xAA, 0xBB]; // Header
    packet.extend_from_slice(&obj.to_bytes());
    packet.push(0xCC); // Checksum placeholder
    packet
}

/// Create sample LoRa configuration
pub fn create_test_lora_config() -> HashMap<String, String> {
    let mut config = HashMap::new();
    config.insert("frequency".to_string(), "915000000".to_string());
    config.insert("spreading_factor".to_string(), "7".to_string());
    config.insert("bandwidth".to_string(), "125000".to_string());
    config.insert("coding_rate".to_string(), "5".to_string());
    config.insert("tx_power".to_string(), "20".to_string());
    config
}

/// Create sample SMS message
pub fn create_test_sms_message() -> String {
    "1234 STATUS room:127".to_string()
}

/// Create sample ArxQL query
pub fn create_test_arxql_queries() -> Vec<String> {
    vec![
        "SELECT * FROM arxobjects WHERE type='outlet'".to_string(),
        "QUERY floor:2 type:emergency_exit".to_string(),
        "STATUS room:127".to_string(),
        "MAP floor:1".to_string(),
        "FIND equipment:fire_alarm".to_string(),
    ]
}