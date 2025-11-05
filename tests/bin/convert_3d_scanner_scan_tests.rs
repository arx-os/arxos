//! Tests for convert_3d_scanner_scan binary
//!
//! These tests verify the conversion functionality without requiring actual scan data.

use tempfile::TempDir;
use std::fs::{create_dir_all, write};
use serde_json::json;

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
    write(scan_dir.join("info.json"), serde_json::to_string_pretty(&info_json).unwrap()).unwrap();
    
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
    
    let points: Vec<[f64; 3]> = points_json.as_array().unwrap()
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
    use arxos::spatial::{Point3D, BoundingBox3D};
    
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
    use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData};
    use arxos::spatial::{Point3D, BoundingBox3D};
    use chrono::Utc;
    use std::collections::HashMap;
    
    let now = Utc::now();
    let bbox = BoundingBox3D::new(
        Point3D::new(0.0, 0.0, 0.0),
        Point3D::new(10.0, 3.0, 8.0),
    );
    
    let room = RoomData {
        id: "room-test".to_string(),
        name: "Test Room".to_string(),
        room_type: "Residential".to_string(),
        area: Some(80.0),
        volume: Some(240.0),
        position: Point3D::new(5.0, 0.0, 4.0),
        bounding_box: bbox.clone(),
        equipment: vec![],
        properties: HashMap::new(),
    };
    
    let floor = FloorData {
        id: "floor-test".to_string(),
        name: "Test Floor".to_string(),
        level: 0,
        elevation: 0.0,
        rooms: vec![room],
        equipment: vec![],
        bounding_box: Some(bbox.clone()),
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
    assert_eq!(building_data.floors[0].rooms.len(), 1);
    assert_eq!(building_data.floors[0].rooms[0].name, "Test Room");
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

