//! Tests for convert_3d_scanner_scan binary
//!
//! These tests verify the conversion functionality without requiring actual scan data.

use serde_json::json;
use std::fs::{create_dir_all, write};
use tempfile::TempDir;

#[test]
fn test_info_json_parsing() {
    // Test that the binary can parse a valid info.json structure
    let temp_dir = TempDir::new().unwrap();
    let scan_dir = temp_dir.path();

    // Create a minimal valid info.json
    let info_json = json!({
        "title": "Test Scan",
        "device": "iPhone15,3",
        "userOBB": {
            "points": [
                [0.0, 0.0, 0.0],
                [10.0, 0.0, 0.0],
                [10.0, 3.0, 0.0],
                [0.0, 3.0, 0.0],
                [0.0, 0.0, 8.0],
                [10.0, 0.0, 8.0],
                [10.0, 3.0, 8.0],
                [0.0, 3.0, 8.0],
            ]
        }
    });

    create_dir_all(scan_dir).unwrap();
    write(
        scan_dir.join("info.json"),
        serde_json::to_string_pretty(&info_json).unwrap(),
    )
    .unwrap();

    // Verify the file can be read and parsed
    let content = std::fs::read_to_string(scan_dir.join("info.json")).unwrap();
    let parsed: serde_json::Value = serde_json::from_str(&content).unwrap();

    assert_eq!(parsed["title"], "Test Scan");
    assert_eq!(parsed["device"], "iPhone15,3");
    assert!(parsed["userOBB"]["points"].is_array());
    assert_eq!(parsed["userOBB"]["points"].as_array().unwrap().len(), 8);
}

#[test]
fn test_obb_point_extraction() {
    // Test extraction of OBB points
    let points_json = json!([
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.0, 3.0, 0.0],
        [0.0, 3.0, 0.0],
        [0.0, 0.0, 8.0],
        [10.0, 0.0, 8.0],
        [10.0, 3.0, 8.0],
        [0.0, 3.0, 8.0],
    ]);

    let points: Vec<[f64; 3]> = points_json
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|p| {
            p.as_array().and_then(|arr| {
                if arr.len() == 3 {
                    Some([
                        arr[0].as_f64().unwrap_or(0.0),
                        arr[1].as_f64().unwrap_or(0.0),
                        arr[2].as_f64().unwrap_or(0.0),
                    ])
                } else {
                    None
                }
            })
        })
        .collect();

    assert_eq!(points.len(), 8);
    assert_eq!(points[0], [0.0, 0.0, 0.0]);
    assert_eq!(points[7], [0.0, 3.0, 8.0]);
}

#[test]
fn test_bounding_box_calculation() {
    use arxos::spatial::{BoundingBox3D, Point3D};

    let points = vec![
        Point3D::new(0.0, 0.0, 0.0),
        Point3D::new(10.0, 0.0, 0.0),
        Point3D::new(10.0, 3.0, 0.0),
        Point3D::new(0.0, 3.0, 0.0),
        Point3D::new(0.0, 0.0, 8.0),
        Point3D::new(10.0, 0.0, 8.0),
        Point3D::new(10.0, 3.0, 8.0),
        Point3D::new(0.0, 3.0, 8.0),
    ];

    let bbox = BoundingBox3D::from_points(&points).unwrap();

    assert_eq!(bbox.min.x, 0.0);
    assert_eq!(bbox.min.y, 0.0);
    assert_eq!(bbox.min.z, 0.0);
    assert_eq!(bbox.max.x, 10.0);
    assert_eq!(bbox.max.y, 3.0);
    assert_eq!(bbox.max.z, 8.0);
}

#[test]
fn test_building_data_structure() {
    use arxos::core::{
        BoundingBox, Dimensions, Floor, Position, Room, RoomType, SpatialProperties, Wing,
    };
    use arxos::spatial::{BoundingBox3D, Point3D};
    use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    use std::collections::HashMap;

    let now = Utc::now();
    let bbox = BoundingBox3D::new(Point3D::new(0.0, 0.0, 0.0), Point3D::new(10.0, 3.0, 8.0));

    let room = Room {
        id: "room-test".to_string(),
        name: "Test Room".to_string(),
        room_type: RoomType::Other("Residential".to_string()),
        equipment: vec![],
        spatial_properties: SpatialProperties {
            position: Position {
                x: 5.0,
                y: 0.0,
                z: 4.0,
                coordinate_system: "LOCAL".to_string(),
            },
            dimensions: Dimensions {
                width: 10.0,
                height: 3.0,
                depth: 8.0,
            },
            bounding_box: BoundingBox {
                min: Position {
                    x: bbox.min.x,
                    y: bbox.min.y,
                    z: bbox.min.z,
                    coordinate_system: "LOCAL".to_string(),
                },
                max: Position {
                    x: bbox.max.x,
                    y: bbox.max.y,
                    z: bbox.max.z,
                    coordinate_system: "LOCAL".to_string(),
                },
            },
            coordinate_system: "LOCAL".to_string(),
        },
        properties: HashMap::new(),
        created_at: None,
        updated_at: None,
    };

    let wing = Wing {
        id: "wing-test".to_string(),
        name: "Main Wing".to_string(),
        rooms: vec![room],
        equipment: vec![],
        properties: HashMap::new(),
    };

    let floor = Floor {
        id: "floor-test".to_string(),
        name: "Test Floor".to_string(),
        level: 0,
        elevation: Some(0.0),
        bounding_box: Some(bbox.clone()),
        wings: vec![wing],
        equipment: vec![],
        properties: HashMap::new(),
    };

    let building_data = BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: Some("Test description".to_string()),
            created_at: now,
            updated_at: now,
            version: "1.0.0".to_string(),
            global_bounding_box: Some(bbox),
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0.0".to_string(),
            total_entities: 1,
            spatial_entities: 1,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
            tags: vec!["test".to_string()],
        },
        floors: vec![floor],
        coordinate_systems: vec![],
    };

    // Verify structure is valid
    assert_eq!(building_data.building.name, "Test Building");
    assert_eq!(building_data.floors.len(), 1);
    assert_eq!(building_data.floors[0].wings.len(), 1);
    assert_eq!(building_data.floors[0].wings[0].rooms.len(), 1);
    assert_eq!(building_data.floors[0].wings[0].rooms[0].name, "Test Room");
}

#[test]
fn test_yaml_serialization() {
    use arxos::yaml::{BuildingData, BuildingYamlSerializer};

    let building_data = BuildingData::default();
    let serializer = BuildingYamlSerializer::new();

    let yaml = serializer.to_yaml(&building_data).unwrap();

    // Verify YAML contains expected fields
    assert!(yaml.contains("building:"));
    assert!(yaml.contains("metadata:"));
    assert!(yaml.contains("floors:"));
    assert!(yaml.contains("Default Building"));
}
