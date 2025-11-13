//! Geometry exports for floor plan visualization in the PWA.
//!
//! This module exposes building spatial data (buildings, floors, rooms, equipment)
//! for the M03 floor viewer. All exports return JSON-serialized data structures
//! that match the TypeScript interfaces in `pwa/src/lib/wasm/geometry.ts`.

use serde::{Deserialize, Serialize};

/// Coordinate in 2D or 3D space
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Coordinate {
    pub x: f64,
    pub y: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub z: Option<f64>,
}

/// Axis-aligned bounding box
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundingBox {
    pub min: Coordinate,
    pub max: Coordinate,
}

/// Summary information about a building (for list views)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingSummary {
    pub path: String,
    pub name: String,
    pub floor_count: usize,
    pub last_modified: String,
}

/// Full building data including all floors
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Building {
    pub path: String,
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub address: Option<String>,
    pub floors: Vec<Floor>,
    pub metadata: serde_json::Value,
}

/// Floor with rooms and equipment
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Floor {
    pub id: String,
    pub name: String,
    pub level: i32,
    pub elevation: f64,
    pub height: f64,
    pub rooms: Vec<Room>,
    pub bounds: BoundingBox,
}

/// Room with spatial data and equipment
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Room {
    pub id: String,
    pub name: String,
    pub room_type: String,
    pub bounds: BoundingBox,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub polygon: Option<Vec<Coordinate>>,
    pub equipment: Vec<Equipment>,
}

/// Equipment entity with position and properties
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Equipment {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub position: Coordinate,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bounds: Option<BoundingBox>,
    pub properties: serde_json::Value,
}

// Helper functions for creating mock data (M03 - no real data source yet)
// Made public for use in lib.rs WASM exports

pub fn create_mock_building_summary() -> BuildingSummary {
    BuildingSummary {
        path: "building/demo-hq".to_string(),
        name: "Demo Headquarters".to_string(),
        floor_count: 3,
        last_modified: "2025-11-12T10:00:00Z".to_string(),
    }
}

pub fn create_mock_building() -> Building {
    Building {
        path: "building/demo-hq".to_string(),
        name: "Demo Headquarters".to_string(),
        address: Some("123 Demo Street, San Francisco, CA 94105".to_string()),
        floors: vec![
            create_mock_floor("floor-1", "Ground Floor", 0),
            create_mock_floor("floor-2", "Second Floor", 1),
            create_mock_floor("floor-3", "Third Floor", 2),
        ],
        metadata: serde_json::json!({
            "year_built": 2020,
            "architect": "Demo Architects Inc.",
            "total_area_sqft": 45000
        }),
    }
}

pub fn create_mock_floor(id: &str, name: &str, level: i32) -> Floor {
    let elevation = level as f64 * 3.5; // 3.5m per floor
    Floor {
        id: id.to_string(),
        name: name.to_string(),
        level,
        elevation,
        height: 3.0, // 3m floor-to-ceiling
        rooms: vec![
            create_mock_room("room-101", "Mechanical Room", "mech", 0.0, 0.0, 10.0, 8.0),
            create_mock_room("room-102", "Electrical Room", "elec", 12.0, 0.0, 8.0, 8.0),
            create_mock_room("room-103", "Office", "office", 0.0, 10.0, 10.0, 10.0),
            create_mock_room("room-104", "Conference Room", "office", 12.0, 10.0, 8.0, 10.0),
        ],
        bounds: BoundingBox {
            min: Coordinate { x: 0.0, y: 0.0, z: Some(elevation) },
            max: Coordinate { x: 20.0, y: 20.0, z: Some(elevation + 3.0) },
        },
    }
}

fn create_mock_room(
    id: &str,
    name: &str,
    room_type: &str,
    x: f64,
    y: f64,
    width: f64,
    height: f64,
) -> Room {
    let equipment = if room_type == "mech" {
        vec![
            create_mock_equipment("equip-001", "VAV-301", "hvac", x + width / 2.0, y + height / 2.0),
        ]
    } else if room_type == "elec" {
        vec![
            create_mock_equipment("equip-002", "Panel-A", "electrical", x + 2.0, y + 2.0),
            create_mock_equipment("equip-003", "Panel-B", "electrical", x + 6.0, y + 2.0),
        ]
    } else {
        vec![]
    };

    Room {
        id: id.to_string(),
        name: name.to_string(),
        room_type: room_type.to_string(),
        bounds: BoundingBox {
            min: Coordinate { x, y, z: None },
            max: Coordinate { x: x + width, y: y + height, z: None },
        },
        polygon: Some(vec![
            Coordinate { x, y, z: None },
            Coordinate { x: x + width, y, z: None },
            Coordinate { x: x + width, y: y + height, z: None },
            Coordinate { x, y: y + height, z: None },
        ]),
        equipment,
    }
}

fn create_mock_equipment(id: &str, name: &str, equip_type: &str, x: f64, y: f64) -> Equipment {
    Equipment {
        id: id.to_string(),
        name: name.to_string(),
        equipment_type: equip_type.to_string(),
        position: Coordinate { x, y, z: Some(1.5) },
        bounds: None,
        properties: serde_json::json!({
            "manufacturer": "Demo Corp",
            "model": "XYZ-2000",
            "status": "operational"
        }),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_building_summary_serialization() {
        let summary = create_mock_building_summary();
        let json = serde_json::to_string(&summary).unwrap();
        assert!(json.contains("Demo Headquarters"));
        assert!(json.contains("building/demo-hq"));
    }

    #[test]
    fn test_building_serialization() {
        let building = create_mock_building();
        let json = serde_json::to_string(&building).unwrap();
        assert!(json.contains("Demo Headquarters"));
        assert!(json.contains("floor-1"));
    }

    #[test]
    fn test_floor_serialization() {
        let floor = create_mock_floor("test-floor", "Test Floor", 1);
        let json = serde_json::to_string(&floor).unwrap();
        assert!(json.contains("test-floor"));
        assert!(json.contains("room-101"));
    }

    #[test]
    fn test_bounding_box_calculation() {
        let floor = create_mock_floor("test", "Test", 0);
        assert_eq!(floor.bounds.min.x, 0.0);
        assert_eq!(floor.bounds.max.x, 20.0);
        assert_eq!(floor.bounds.min.y, 0.0);
        assert_eq!(floor.bounds.max.y, 20.0);
    }
}
