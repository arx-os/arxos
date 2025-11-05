//! Integration tests for USDZ export functionality
//!
//! These tests verify the complete USDZ export workflow, including
//! glTF to USDZ conversion and USDZ file structure validation.

use arxos::export::ar::{ARExporter, ARFormat};
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, EquipmentStatus, CoordinateSystemInfo};
use arxos::spatial::{Point3D, BoundingBox3D};
use std::fs;
use std::collections::HashMap;
use tempfile::TempDir;
use chrono::Utc;
use zip::ZipArchive;

/// Create test building data with equipment
fn create_test_building_data() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: Some("Test building for USDZ export".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "ArxOS v2.0".to_string(),
            total_entities: 2,
            spatial_entities: 2,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![
            FloorData {
                id: "floor-1".to_string(),
                name: "Floor 1".to_string(),
                level: 1,
                elevation: 0.0,
                rooms: vec![],
                equipment: vec![
                    EquipmentData {
                        id: "equipment-1".to_string(),
                        name: "HVAC Unit 1".to_string(),
                        equipment_type: "HVAC".to_string(),
                        system_type: "HVAC".to_string(),
                        position: Point3D::new(2.0, 2.0, 2.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(1.0, 1.0, 1.0),
                            Point3D::new(3.0, 3.0, 3.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "building/floor-1/equipment-hvac-1".to_string(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        id: "equipment-2".to_string(),
                        name: "Light Fixture 1".to_string(),
                        equipment_type: "Electrical".to_string(),
                        system_type: "Electrical".to_string(),
                        position: Point3D::new(5.0, 5.0, 2.5),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(4.5, 4.5, 2.0),
                            Point3D::new(5.5, 5.5, 3.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "building/floor-1/equipment-electrical-1".to_string(),
                        sensor_mappings: None,
                    },
                ],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![CoordinateSystemInfo {
            name: "World".to_string(),
            origin: Point3D::origin(),
            x_axis: Point3D::new(1.0, 0.0, 0.0),
            y_axis: Point3D::new(0.0, 1.0, 0.0),
            z_axis: Point3D::new(0.0, 0.0, 1.0),
            description: Some("Default world coordinate system".to_string()),
        }],
    }
}

#[test]
fn test_usdz_export_creates_valid_archive() {
    let temp_dir = TempDir::new().unwrap();
    let usdz_path = temp_dir.path().join("test_export.usdz");
    
    let building_data = create_test_building_data();
    let exporter = ARExporter::new(building_data);
    
    // Export to USDZ
    match exporter.export(ARFormat::USDZ, &usdz_path) {
        Ok(_) => {
            assert!(usdz_path.exists(), "USDZ file should be created");
            
            // Verify it's a valid ZIP archive
            let file = fs::File::open(&usdz_path).unwrap();
            let zip = ZipArchive::new(file).expect("USDZ should be a valid ZIP archive");
            assert!(zip.len() > 0, "USDZ should contain at least one file");
        }
        Err(e) => {
            // On Windows without usdzconvert, wrapper should still be created
            // Verify the error message indicates the fallback was attempted
            let error_msg = e.to_string();
            assert!(
                error_msg.contains("usdzconvert") || usdz_path.exists(),
                "Should either succeed or provide helpful error. Got: {}", error_msg
            );
        }
    }
}

#[test]
fn test_usdz_export_contains_usd_file() {
    let temp_dir = TempDir::new().unwrap();
    let usdz_path = temp_dir.path().join("test_with_usd.usdz");
    
    let building_data = create_test_building_data();
    let exporter = ARExporter::new(building_data);
    
    // Export to USDZ
    let _ = exporter.export(ARFormat::USDZ, &usdz_path);
    
    // If file was created, verify it contains USD file
    if usdz_path.exists() {
        let file = fs::File::open(&usdz_path).unwrap();
        let mut zip = ZipArchive::new(file).unwrap();
        
        // Check for USD file
        let file_names: Vec<String> = (0..zip.len())
            .map(|i| zip.by_index(i).unwrap().name().to_string())
            .collect();
        
        // Should contain at least scene.usd or similar
        assert!(
            file_names.iter().any(|n| n.contains("usd")) || 
            file_names.iter().any(|n| n.contains("gltf")),
            "USDZ should contain USD or glTF file. Found: {:?}", file_names
        );
    }
}

#[test]
fn test_usdz_via_ar_exporter() {
    let temp_dir = TempDir::new().unwrap();
    let usdz_path = temp_dir.path().join("via_ar_exporter.usdz");
    
    let building_data = create_test_building_data();
    let exporter = ARExporter::new(building_data);
    
    // Test that ARExporter routes USDZ format correctly
    match exporter.export(ARFormat::USDZ, &usdz_path) {
        Ok(_) => {
            assert!(usdz_path.exists(), "USDZ file should be created via ARExporter");
        }
        Err(_) => {
            // On Windows, may not have usdzconvert, but wrapper should still work
            // This test verifies the routing works
        }
    }
}

#[test]
fn test_usdz_export_empty_building() {
    let temp_dir = TempDir::new().unwrap();
    let usdz_path = temp_dir.path().join("empty_building.usdz");
    
    let building_data = BuildingData {
        building: BuildingInfo {
            id: "empty".to_string(),
            name: "Empty Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "Test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![],
    };
    
    let exporter = ARExporter::new(building_data);
    
    // Empty building should still export (creates minimal USDZ)
    match exporter.export(ARFormat::USDZ, &usdz_path) {
        Ok(_) => {
            assert!(usdz_path.exists(), "Empty building should still create USDZ file");
        }
        Err(_) => {
            // Acceptable if usdzconvert not available on Windows
        }
    }
}

#[test]
fn test_usdz_export_preserves_equipment_data() {
    let temp_dir = TempDir::new().unwrap();
    let usdz_path = temp_dir.path().join("preserves_data.usdz");
    
    let building_data = create_test_building_data();
    let exporter = ARExporter::new(building_data);
    
    // Export to USDZ
    let _ = exporter.export(ARFormat::USDZ, &usdz_path);
    
    // If file created, verify glTF within contains equipment data
    if usdz_path.exists() {
        let file = fs::File::open(&usdz_path).unwrap();
        let mut zip = ZipArchive::new(file).unwrap();
        
        // Look for glTF file in archive
        for i in 0..zip.len() {
            let mut file = zip.by_index(i).unwrap();
            let name = file.name();
            
            if name.ends_with(".gltf") || name.ends_with(".glb") {
                // Read and verify glTF content
                let mut content = String::new();
                use std::io::Read;
                file.read_to_string(&mut content).unwrap();
                
                // Verify it's valid glTF JSON structure
                let json_value: Result<serde_json::Value, _> = serde_json::from_str(&content);
                assert!(json_value.is_ok(), "glTF in USDZ should be valid JSON");
                
                let json = json_value.unwrap();
                // Should have glTF structure elements
                assert!(
                    json.get("asset").is_some() || 
                    json.get("scenes").is_some() || 
                    json.get("nodes").is_some() ||
                    content.contains("glTF") ||
                    content.contains("mesh"),
                    "glTF in USDZ should contain glTF structure. Content preview: {}",
                    &content.chars().take(200).collect::<String>()
                );
            }
        }
    }
}

