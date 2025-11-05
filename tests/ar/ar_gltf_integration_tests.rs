//! Integration tests for AR integration module
//!
//! These tests verify AR scan processing, pending equipment workflow, and confirmation.

use arxos::ar_integration::pending::{PendingEquipmentManager, DetectedEquipmentInfo, DetectionMethod};
use arxos::ar_integration::processing::{ARScanData, DetectedEquipmentData, validate_ar_scan_data};
use arxos::spatial::{Point3D, BoundingBox3D};
use std::collections::HashMap;
use std::fs;
use tempfile::TempDir;

#[test]
fn test_pending_equipment_creation() {
    // Test creating pending equipment
    let detected = DetectedEquipmentInfo {
        name: "Test Unit".to_string(),
        equipment_type: "HVAC".to_string(),
        position: Point3D { x: 10.0, y: 20.0, z: 0.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 9.5, y: 19.5, z: -1.0 },
            max: Point3D { x: 10.5, y: 20.5, z: 1.0 },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::LiDAR,
        properties: HashMap::new(),
    };
    
    let mut manager = PendingEquipmentManager::new("test".to_string());
    let result = manager.add_pending_equipment(&detected, "scan_1", 1, Some("Room 101"), 0.8, None);
    
    assert!(result.is_ok());
    let pending_list = manager.list_pending();
    assert_eq!(pending_list.len(), 1);
}

#[test]
fn test_confidence_filtering() {
    // Test that low confidence equipment is filtered out
    let low_confidence = DetectedEquipmentInfo {
        name: "Low Conf".to_string(),
        equipment_type: "Test".to_string(),
        position: Point3D { x: 0.0, y: 0.0, z: 0.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: -0.5, y: -0.5, z: -1.0 },
            max: Point3D { x: 0.5, y: 0.5, z: 1.0 },
        },
        confidence: 0.5, // Below threshold
        detection_method: DetectionMethod::Manual,
        properties: HashMap::new(),
    };
    
    let mut manager = PendingEquipmentManager::new("test".to_string());
    let result = manager.add_pending_equipment(&low_confidence, "scan_1", 1, None, 0.8, None);
    
    // Should return None for low confidence
    if let Ok(Some(_)) = result {
        panic!("Low confidence equipment should not be added");
    }
    
    assert_eq!(manager.list_pending().len(), 0);
}

#[test]
fn test_batch_operations() {
    // Test batch confirming multiple pending items
    let detected1 = DetectedEquipmentInfo {
        name: "Unit 1".to_string(),
        equipment_type: "HVAC".to_string(),
        position: Point3D { x: 10.0, y: 10.0, z: 0.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 9.5, y: 9.5, z: -1.0 },
            max: Point3D { x: 10.5, y: 10.5, z: 1.0 },
        },
        confidence: 0.95,
        detection_method: DetectionMethod::ARKit,
        properties: HashMap::new(),
    };
    
    let detected2 = DetectedEquipmentInfo {
        name: "Unit 2".to_string(),
        equipment_type: "Lighting".to_string(),
        position: Point3D { x: 20.0, y: 20.0, z: 2.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 19.5, y: 19.5, z: 1.5 },
            max: Point3D { x: 20.5, y: 20.5, z: 2.5 },
        },
        confidence: 0.92,
        detection_method: DetectionMethod::LiDAR,
        properties: HashMap::new(),
    };
    
    let mut manager = PendingEquipmentManager::new("test".to_string());
    
    let id1 = manager.add_pending_equipment(&detected1, "scan_1", 1, None, 0.8, None).unwrap().unwrap();
    let id2 = manager.add_pending_equipment(&detected2, "scan_1", 1, None, 0.8, None).unwrap().unwrap();
    
    assert_eq!(manager.list_pending().len(), 2);
    
    // Test batch reject
    let ids = vec![id1.as_str(), id2.as_str()];
    for id in &ids {
        assert!(manager.reject_pending(id).is_ok());
    }
    
    assert_eq!(manager.list_pending().len(), 0);
}

#[test]
fn test_ar_scan_validation_valid() {
    let valid_scan = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301".to_string(),
                equipment_type: "HVAC".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 0.0 },
                confidence: 0.95,
                detection_method: Some("ARKit".to_string()),
            },
        ],
    };
    
    assert!(validate_ar_scan_data(&valid_scan).is_ok());
}

#[test]
fn test_ar_scan_validation_invalid() {
    // Test empty equipment list
    let empty_scan = ARScanData {
        detected_equipment: vec![],
    };
    
    assert!(validate_ar_scan_data(&empty_scan).is_err());
    
    // Test invalid position
    let invalid_position = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301".to_string(),
                equipment_type: "HVAC".to_string(),
                position: Point3D { x: 9999.0, y: 9999.0, z: 9999.0 }, // Out of bounds
                confidence: 0.95,
                detection_method: Some("ARKit".to_string()),
            },
        ],
    };
    
    assert!(validate_ar_scan_data(&invalid_position).is_err());
    
    // Test invalid confidence
    let invalid_confidence = ARScanData {
        detected_equipment: vec![
            DetectedEquipmentData {
                name: "VAV-301".to_string(),
                equipment_type: "HVAC".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 0.0 },
                confidence: 1.5, // Invalid (> 1.0)
                detection_method: Some("ARKit".to_string()),
            },
        ],
    };
    
    assert!(validate_ar_scan_data(&invalid_confidence).is_err());
}

// ============================================================================
// glTF Export Integration Tests
// ============================================================================

use arxos::export::ar::gltf::GLTFExporter;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, EquipmentStatus};

/// Create a test building with realistic equipment for integration testing
fn create_realistic_test_building() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "integration-test".to_string(),
            name: "Integration Test Building".to_string(),
            description: Some("Building for glTF export integration testing".to_string()),
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: Some(BoundingBox3D {
                min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                max: Point3D { x: 100.0, y: 100.0, z: 20.0 },
            }),
        },
        metadata: BuildingMetadata {
            source_file: Some("test.ifc".to_string()),
            parser_version: "ArxOS Test".to_string(),
            total_entities: 5,
            spatial_entities: 5,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec!["test".to_string(), "integration".to_string()],
        },
        floors: vec![
            FloorData {
                id: "floor-1".to_string(),
                name: "Ground Floor".to_string(),
                level: 1,
                elevation: 0.0,
                rooms: vec![],
                equipment: vec![
                    EquipmentData {
                        id: "vav-001".to_string(),
                        name: "VAV-001".to_string(),
                        equipment_type: "HVAC".to_string(),
                        system_type: "HVAC".to_string(),
                        position: Point3D { x: 10.0, y: 20.0, z: 2.0 },
                        bounding_box: BoundingBox3D {
                            min: Point3D { x: 9.5, y: 19.5, z: 1.5 },
                            max: Point3D { x: 10.5, y: 20.5, z: 2.5 },
                        },
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "Building::Integration::Floor::1::Equipment::VAV-001".to_string(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        id: "panel-a".to_string(),
                        name: "Electrical Panel A".to_string(),
                        equipment_type: "electrical".to_string(),
                        system_type: "Electrical".to_string(),
                        position: Point3D { x: 5.0, y: 15.0, z: 1.8 },
                        bounding_box: BoundingBox3D {
                            min: Point3D { x: 4.5, y: 14.5, z: 1.3 },
                            max: Point3D { x: 5.5, y: 15.5, z: 2.3 },
                        },
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "Building::Integration::Floor::1::Equipment::Panel-A".to_string(),
                        sensor_mappings: None,
                    },
                ],
                bounding_box: Some(BoundingBox3D {
                    min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                    max: Point3D { x: 50.0, y: 50.0, z: 4.0 },
                }),
            },
            FloorData {
                id: "floor-2".to_string(),
                name: "Second Floor".to_string(),
                level: 2,
                elevation: 4.5,
                rooms: vec![],
                equipment: vec![
                    EquipmentData {
                        id: "switch-01".to_string(),
                        name: "Network Switch 01".to_string(),
                        equipment_type: "network".to_string(),
                        system_type: "IT".to_string(),
                        position: Point3D { x: 12.0, y: 8.0, z: 5.5 },
                        bounding_box: BoundingBox3D {
                            min: Point3D { x: 11.8, y: 7.8, z: 5.3 },
                            max: Point3D { x: 12.2, y: 8.2, z: 5.7 },
                        },
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "Building::Integration::Floor::2::Equipment::Switch-01".to_string(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        id: "water-heater".to_string(),
                        name: "Water Heater".to_string(),
                        equipment_type: "plumbing".to_string(),
                        system_type: "Plumbing".to_string(),
                        position: Point3D { x: 25.0, y: 30.0, z: 5.0 },
                        bounding_box: BoundingBox3D {
                            min: Point3D { x: 24.0, y: 29.0, z: 4.5 },
                            max: Point3D { x: 26.0, y: 31.0, z: 5.5 },
                        },
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "Building::Integration::Floor::2::Equipment::Water-Heater".to_string(),
                        sensor_mappings: None,
                    },
                ],
                bounding_box: Some(BoundingBox3D {
                    min: Point3D { x: 0.0, y: 0.0, z: 4.5 },
                    max: Point3D { x: 50.0, y: 50.0, z: 8.5 },
                }),
            },
        ],
        coordinate_systems: vec![],
    }
}

#[test]
fn test_gltf_export_to_file() {
    let temp_dir = TempDir::new().expect("Should create temp directory");
    let output_path = temp_dir.path().join("test_export.gltf");
    
    let building = create_realistic_test_building();
    let exporter = GLTFExporter::new(&building);
    
    // Export to glTF file
    exporter.export(&output_path)
        .expect("Should export glTF file successfully");
    
    // Verify file was created
    assert!(output_path.exists(), "glTF file should be created");
    
    // Verify file is not empty
    let file_size = fs::metadata(&output_path)
        .expect("Should read file metadata")
        .len();
    assert!(file_size > 0, "glTF file should not be empty");
    
    // Verify file is valid JSON (glTF is JSON)
    let file_contents = fs::read_to_string(&output_path)
        .expect("Should read glTF file");
    
    // Parse as JSON to verify structure
    let json_value: serde_json::Value = serde_json::from_str(&file_contents)
        .expect("glTF file should be valid JSON");
    
    // Verify required glTF fields exist
    assert!(json_value.get("asset").is_some(), "glTF should have 'asset' field");
    assert_eq!(json_value["asset"]["version"], "2.0", "glTF version should be 2.0");
    assert!(json_value.get("scenes").is_some(), "glTF should have 'scenes' field");
    assert!(json_value.get("nodes").is_some(), "glTF should have 'nodes' field");
}

#[test]
fn test_gltf_export_structure_validation() {
    let temp_dir = TempDir::new().expect("Should create temp directory");
    let output_path = temp_dir.path().join("test_structure.gltf");
    
    let building = create_realistic_test_building();
    let exporter = GLTFExporter::new(&building);
    
    exporter.export(&output_path)
        .expect("Should export glTF file successfully");
    
    let file_contents = fs::read_to_string(&output_path)
        .expect("Should read glTF file");
    let json_value: serde_json::Value = serde_json::from_str(&file_contents)
        .expect("glTF file should be valid JSON");
    
    // Verify asset information
    let asset = json_value.get("asset").expect("Should have asset");
    assert_eq!(asset["version"], "2.0");
    assert_eq!(asset["generator"], "ArxOS");
    
    // Verify scene structure
    let scenes = json_value.get("scenes").expect("Should have scenes");
    assert!(scenes.is_array());
    assert!(!scenes.as_array().unwrap().is_empty());
    
    // Verify nodes exist
    let nodes = json_value.get("nodes").expect("Should have nodes");
    assert!(nodes.is_array());
    let nodes_array = nodes.as_array().unwrap();
    assert_eq!(nodes_array.len(), 6); // 2 floors + 4 equipment = 6 nodes
    
    // Verify meshes exist
    let meshes = json_value.get("meshes").expect("Should have meshes");
    assert!(meshes.is_array());
    let meshes_array = meshes.as_array().unwrap();
    assert_eq!(meshes_array.len(), 4); // 4 equipment items = 4 meshes
    
    // Verify materials exist
    let materials = json_value.get("materials").expect("Should have materials");
    assert!(materials.is_array());
    let materials_array = materials.as_array().unwrap();
    assert!(materials_array.len() >= 3); // At least 3 unique equipment types
    
    // Verify buffers and buffer views
    assert!(json_value.get("buffers").is_some());
    assert!(json_value.get("bufferViews").is_some());
    assert!(json_value.get("accessors").is_some());
}

#[test]
fn test_gltf_export_material_properties() {
    let temp_dir = TempDir::new().expect("Should create temp directory");
    let output_path = temp_dir.path().join("test_materials.gltf");
    
    let building = create_realistic_test_building();
    let exporter = GLTFExporter::new(&building);
    
    exporter.export(&output_path)
        .expect("Should export glTF file successfully");
    
    let file_contents = fs::read_to_string(&output_path)
        .expect("Should read glTF file");
    let json_value: serde_json::Value = serde_json::from_str(&file_contents)
        .expect("glTF file should be valid JSON");
    
    // Verify materials have PBR properties
    let materials = json_value.get("materials")
        .and_then(|m| m.as_array())
        .expect("Should have materials array");
    
    for material in materials {
        assert!(material.get("pbrMetallicRoughness").is_some(),
            "Each material should have pbrMetallicRoughness");
        
        let pbr = material.get("pbrMetallicRoughness").unwrap();
        assert!(pbr.get("baseColorFactor").is_some(),
            "PBR should have baseColorFactor");
        
        // Verify baseColorFactor is RGBA array
        let color = pbr.get("baseColorFactor").unwrap();
        assert!(color.is_array(), "baseColorFactor should be array");
        let color_array = color.as_array().unwrap();
        assert_eq!(color_array.len(), 4, "baseColorFactor should be RGBA (4 values)");
    }
}

#[test]
fn test_gltf_export_empty_building() {
    let temp_dir = TempDir::new().expect("Should create temp directory");
    let output_path = temp_dir.path().join("test_empty.gltf");
    
    let mut building = create_realistic_test_building();
    building.floors.clear();
    
    let exporter = GLTFExporter::new(&building);
    
    exporter.export(&output_path)
        .expect("Should export empty building successfully");
    
    let file_contents = fs::read_to_string(&output_path)
        .expect("Should read glTF file");
    let json_value: serde_json::Value = serde_json::from_str(&file_contents)
        .expect("glTF file should be valid JSON");
    
    // Empty building should still be valid glTF
    assert_eq!(json_value["asset"]["version"], "2.0");
    assert!(json_value.get("scenes").is_some());
    
    // Should have default material but no nodes or meshes
    let nodes_len = json_value.get("nodes")
        .and_then(|n| n.as_array())
        .map(|arr| arr.len())
        .unwrap_or(0);
    assert_eq!(nodes_len, 0);
    
    let meshes_len = json_value.get("meshes")
        .and_then(|m| m.as_array())
        .map(|arr| arr.len())
        .unwrap_or(0);
    assert_eq!(meshes_len, 0);
}

#[test]
fn test_gltf_export_multiple_equipment_same_type() {
    let temp_dir = TempDir::new().expect("Should create temp directory");
    let output_path = temp_dir.path().join("test_multiple.gltf");
    
    let mut building = create_realistic_test_building();
    // Add another HVAC unit
    building.floors[0].equipment.push(EquipmentData {
        id: "vav-002".to_string(),
        name: "VAV-002".to_string(),
        equipment_type: "HVAC".to_string(),
        system_type: "HVAC".to_string(),
        position: Point3D { x: 20.0, y: 30.0, z: 2.0 },
        bounding_box: BoundingBox3D {
            min: Point3D { x: 19.5, y: 29.5, z: 1.5 },
            max: Point3D { x: 20.5, y: 30.5, z: 2.5 },
        },
        status: EquipmentStatus::Healthy,
        properties: HashMap::new(),
        universal_path: "Building::Integration::Floor::1::Equipment::VAV-002".to_string(),
        sensor_mappings: None,
    });
    
    let exporter = GLTFExporter::new(&building);
    
    exporter.export(&output_path)
        .expect("Should export successfully");
    
    let file_contents = fs::read_to_string(&output_path)
        .expect("Should read glTF file");
    let json_value: serde_json::Value = serde_json::from_str(&file_contents)
        .expect("glTF file should be valid JSON");
    
    // Should have 5 meshes (original 4 + 1 new)
    let meshes = json_value.get("meshes")
        .and_then(|m| m.as_array())
        .expect("Should have meshes");
    assert_eq!(meshes.len(), 5);
    
    // Should still have same number of materials (HVAC material reused)
    // Unique types: HVAC, electrical, network, plumbing = 4
    let materials = json_value.get("materials")
        .and_then(|m| m.as_array())
        .expect("Should have materials");
    
    // Count unique equipment types
    let unique_types: std::collections::HashSet<&str> = building.floors.iter()
        .flat_map(|f| f.equipment.iter().map(|e| e.equipment_type.as_str()))
        .collect();
    
    assert_eq!(materials.len(), unique_types.len());
}

#[test]
fn test_gltf_export_file_path_handling() {
    let temp_dir = TempDir::new().expect("Should create temp directory");
    
    // Test with .gltf extension
    let gltf_path = temp_dir.path().join("output.gltf");
    let building = create_realistic_test_building();
    let exporter = GLTFExporter::new(&building);
    
    exporter.export(&gltf_path)
        .expect("Should export with .gltf extension");
    assert!(gltf_path.exists());
    
    // Test with subdirectory
    let subdir = temp_dir.path().join("exports");
    fs::create_dir_all(&subdir).expect("Should create subdirectory");
    let subdir_path = subdir.join("building.gltf");
    
    let exporter2 = GLTFExporter::new(&building);
    exporter2.export(&subdir_path)
        .expect("Should export to subdirectory");
    assert!(subdir_path.exists());
}

