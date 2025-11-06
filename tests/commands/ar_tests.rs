//! Tests for AR integration command handlers

use tempfile::TempDir;
use std::fs::{create_dir_all, write};
use std::path::PathBuf;
use std::path::Path;

#[test]
fn test_ar_scan_json_parsing() {
    // Test that the sample AR scan JSON is valid
    let ar_scan_data = include_str!("../../test_data/sample-ar-scan.json");
    
    // Verify structure
    assert!(ar_scan_data.contains("detectedEquipment"));
    assert!(ar_scan_data.contains("VAV-301"));
    assert!(ar_scan_data.contains("Light-Fixture-301"));
    assert!(ar_scan_data.contains("roomBoundaries"));
    assert!(ar_scan_data.contains("ARKit"));
    
    // Try to parse as JSON
    let parsed: Result<serde_json::Value, _> = serde_json::from_str(ar_scan_data);
    assert!(parsed.is_ok());
    
    if let Ok(json) = parsed {
        assert!(json["detectedEquipment"].is_array());
        assert!(json["detectedEquipment"].as_array().unwrap().len() > 0);
    }
}

#[test]
fn test_ar_scan_data_structure() {
    // Verify AR scan data has expected structure
    let ar_scan_data = include_str!("../../test_data/sample-ar-scan.json");
    let json: serde_json::Value = serde_json::from_str(ar_scan_data).unwrap();
    
    // Check detected equipment array
    let equipment = json["detectedEquipment"].as_array().unwrap();
    assert_eq!(equipment.len(), 2);
    
    // Check first equipment item
    let first_eq = &equipment[0];
    assert_eq!(first_eq["name"], "VAV-301");
    assert_eq!(first_eq["type"], "HVAC");
    assert_eq!(first_eq["confidence"], 0.95);
    
    // Check room boundaries
    assert!(json["roomBoundaries"].is_object());
    assert!(json["roomBoundaries"]["walls"].is_array());
    assert!(json["roomBoundaries"]["walls"].as_array().unwrap().len() == 4);
}

#[test]
#[ignore] // Requires AR scan integration
fn test_ar_scan_integration() {
    // This would test full AR scan data integration:
    // 1. Reading AR scan JSON
    // 2. Processing and validation
    // 3. Adding to pending equipment
    // 4. Confirmation workflow
}

#[test]
fn test_ar_export_gltf_format() {
    use arxos::yaml::BuildingData;
    use arxos::export::ar::{ARExporter, ARFormat};
    use std::path::Path;
    
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("test_export.gltf");
    
    // Create minimal building data
    let building_data = BuildingData::default();
    
    // Test glTF export
    let exporter = ARExporter::new(building_data);
    let result = exporter.export(ARFormat::GLTF, &output_path);
    
    assert!(result.is_ok(), "glTF export should succeed");
    assert!(output_path.exists(), "glTF file should be created");
    
    // Verify file contents
    let contents = std::fs::read_to_string(&output_path).unwrap();
    assert!(contents.contains("\"asset\""), "Should contain glTF asset");
    assert!(contents.contains("\"version\": \"2.0\""), "Should be glTF 2.0");
    assert!(contents.contains("\"generator\": \"ArxOS\""), "Should have ArxOS generator");
}

#[test]
fn test_ar_export_format_parsing() {
    use arxos::export::ar::ARFormat;
    
    // Test format string parsing
    assert_eq!("gltf".parse::<ARFormat>(), Ok(ARFormat::GLTF));
    assert_eq!("usdz".parse::<ARFormat>(), Ok(ARFormat::USDZ));
    
    // Test invalid format
    assert!("invalid".parse::<ARFormat>().is_err());
    assert!("GLTF".parse::<ARFormat>().is_ok()); // Case insensitive conversion
}

#[test]
fn test_ar_export_with_equipment() {
    use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, EquipmentStatus};
    use arxos::spatial::{Point3D, BoundingBox3D};
    use arxos::export::ar::{ARExporter, ARFormat};
    use chrono::Utc;
    use std::collections::HashMap;
    
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("test_with_equipment.gltf");
    
    // Create building data with equipment
    let building_data = BuildingData {
        building: BuildingInfo {
            id: "test-1".to_string(),
            name: "Test Building".to_string(),
            description: Some("Test".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "Test".to_string(),
            total_entities: 1,
            spatial_entities: 1,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![FloorData {
            id: "floor-1".to_string(),
            name: "Ground Floor".to_string(),
            level: 0,
            elevation: 0.0,
            rooms: vec![],
            equipment: vec![EquipmentData {
                id: "eq-1".to_string(),
                name: "Test HVAC".to_string(),
                equipment_type: "HVAC".to_string(),
                system_type: "VAV".to_string(),
                position: Point3D { x: 10.0, y: 20.0, z: 3.0 },
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 9.0, y: 19.0, z: 2.5 },
                    max: Point3D { x: 11.0, y: 21.0, z: 3.5 },
                },
                status: EquipmentStatus::Healthy,
                properties: HashMap::new(),
                universal_path: "Building::TestBuilding::Floor::0::Equipment::TestHVAC".to_string(),
                sensor_mappings: None,
            }],
            bounding_box: None,
        }],
        coordinate_systems: vec![],
    };
    
    // Test export
    let exporter = ARExporter::new(building_data);
    let result = exporter.export(ARFormat::GLTF, &output_path);
    
    assert!(result.is_ok(), "Export should succeed with equipment");
    assert!(output_path.exists(), "glTF file should be created");
    
    // Verify equipment is in output
    let contents = std::fs::read_to_string(&output_path).unwrap();
    assert!(contents.contains("Test HVAC"), "Should contain equipment name");
    assert!(contents.contains("\"translation\"") && contents.contains("10.0"), "Should contain position");
}

#[test]
fn test_ar_export_invalid_format() {
    use arxos::yaml::BuildingData;
    use arxos::export::ar::ARExporter;
    use std::path::Path;
    
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("test.usdz");
    
    // USDZ export requires usdzconvert tool (available on macOS via Xcode)
    // This test verifies that export fails gracefully when the tool is not available
    let building_data = BuildingData::default();
    let exporter = ARExporter::new(building_data);
    
    let result = exporter.export(arxos::export::ar::ARFormat::USDZ, &output_path);
    // Export may succeed if usdzconvert is available, or fail gracefully if not
    // Either way, the export should not panic
    let _ = result; // Don't assert on success/failure - tool availability is environment-dependent
}

#[test]
fn test_spatial_anchor_export() {
    use arxos::export::ar::anchor::{SpatialAnchor, export_anchors_to_json};
    use arxos::spatial::Point3D;
    use std::path::Path;
    
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("anchors.json");
    
    // Create test anchors
    let anchors = vec![
        SpatialAnchor::new("anchor1".to_string(), Point3D { x: 1.0, y: 2.0, z: 3.0 }),
        SpatialAnchor::new("anchor2".to_string(), Point3D { x: 4.0, y: 5.0, z: 6.0 })
            .with_metadata("type".to_string(), "entry_point".to_string()),
    ];
    
    // Export anchors
    let result = export_anchors_to_json(&anchors, &output_path);
    assert!(result.is_ok(), "Anchor export should succeed");
    assert!(output_path.exists(), "Anchors file should be created");
    
    // Verify JSON contents
    let json = std::fs::read_to_string(&output_path).unwrap();
    assert!(json.contains("anchor1"), "Should contain anchor1");
    assert!(json.contains("anchor2"), "Should contain anchor2");
    assert!(json.contains("\"x\": 1.0"), "Should contain position data");
}

#[test]
fn test_spatial_anchor_import() {
    use arxos::export::ar::anchor::{SpatialAnchor, import_anchors_from_json, export_anchors_to_json};
    use arxos::spatial::Point3D;
    use std::path::Path;
    
    let temp_dir = TempDir::new().unwrap();
    let output_path = temp_dir.path().join("anchors_roundtrip.json");
    
    // Create and export anchors
    let original_anchors = vec![
        SpatialAnchor::new("anchor1".to_string(), Point3D { x: 10.0, y: 20.0, z: 30.0 }),
    ];
    
    export_anchors_to_json(&original_anchors, &output_path).unwrap();
    
    // Import anchors back
    let imported_anchors = import_anchors_from_json(&output_path).unwrap();
    
    assert_eq!(imported_anchors.len(), 1);
    assert_eq!(imported_anchors[0].id, "anchor1");
    assert_eq!(imported_anchors[0].position.x, 10.0);
}
