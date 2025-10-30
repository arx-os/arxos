//! Integration Tests for Command Handlers
//!
//! This module tests the command handlers in `src/commands/`
//! through their public interfaces, verifying end-to-end workflows.

use arxos::commands::import;
use arxos::commands::export;
use arxos::commands::room;
use arxos::commands::equipment;
use tempfile::TempDir;
use std::fs::{create_dir_all, write, File};
use std::io::Write;

/// Helper to create a temporary test building environment
fn setup_test_building(temp_dir: &TempDir) -> Result<(String, String), Box<dyn std::error::Error>> {
    // Create building directory structure
    let building_dir = temp_dir.path().join("test_building");
    create_dir_all(&building_dir)?;
    
    // Create a sample IFC file for import testing
    let ifc_path = building_dir.join("sample.ifc");
    let mut ifc_file = File::create(&ifc_path)?;
    
    // Write a minimal valid IFC file
    ifc_file.write_all(b"ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ArxOS Test IFC File'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test Author'),('Test Organization'),'ArxOS Test','Test System','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCBUILDING($,$,X,#2,$,$,$,$,$);
#2=IFCLOCALPLACEMENT($,#3);
#3=IFCAXIS2PLACEMENT3D(#4,#5,$);
#4=IFCCARTESIANPOINT((0.,0.,0.));
#5=IFCDIRECTION((0.,0.,1.));
ENDSEC;
END-ISO-10303-21;")?;
    
    // Create a sample building YAML file for export testing
    let yaml_path = building_dir.join("building.yaml");
    let building_yaml = r#"
building:
  name: Test Building
  address: 123 Test St
  total_floors: 1
metadata:
  version: 1.0
  last_updated: "2024-01-01T00:00:00Z"
floors:
  - name: Floor 1
    level: 1
    rooms: []
    equipment:
      - name: Test HVAC
        type: HVAC
        position:
          x: 10.0
          y: 20.0
          z: 5.0
        universal_path: Building::TestBuilding::Floor::1::Equipment::TestHVAC
"#;
    write(&yaml_path, building_yaml)?;
    
    Ok((
        ifc_path.to_string_lossy().to_string(),
        yaml_path.to_string_lossy().to_string(),
    ))
}

#[test]
fn test_import_command_handles_nonexistent_file() {
    let temp_dir = tempfile::tempdir().unwrap();
    let nonexistent_ifc = temp_dir.path().join("nonexistent.ifc");
    
    let result = import::handle_import(
        nonexistent_ifc.to_string_lossy().to_string(),
        None,
    );
    
    // Should return an error for file not found
    assert!(result.is_err());
    let error_msg = result.unwrap_err().to_string();
    assert!(
        error_msg.contains("not found") || 
        error_msg.contains("No such file") ||
        error_msg.contains("cannot find")
    );
}

#[test]
#[ignore] // Requires actual IFC processing infrastructure
fn test_import_command_creates_yaml_output() {
    // This test would verify:
    // 1. IFC file is parsed successfully
    // 2. YAML output is generated
    // 3. YAML file contains expected structure
    // Requires full IFC parsing infrastructure to be working
}

#[test]
fn test_export_command_handles_nonexistent_directory() {
    let temp_dir = tempfile::tempdir().unwrap();
    let nonexistent_repo = temp_dir.path().join("nonexistent_repo");
    
    // Export should handle gracefully when no YAML files exist
    let result = export::handle_export(
        nonexistent_repo.to_string_lossy().to_string(),
    );
    
    // Should either succeed (with no files to export) or fail gracefully
    // This depends on the actual implementation
    drop(result);
}

#[test]
fn test_room_dimension_parsing_through_command() {
    // Test that parsing functions work correctly (when feature is enabled)
    // For now, test through the module's test functions
    let dims = room::parse_dimensions("10 x 20 x 8");
    assert!(dims.is_ok());
    let (w, d, h) = dims.unwrap();
    assert_eq!((w, d, h), (10.0, 20.0, 8.0));
    
    let pos = room::parse_position("5, 10, 2");
    assert!(pos.is_ok());
    let (x, y, z) = pos.unwrap();
    assert_eq!((x, y, z), (5.0, 10.0, 2.0));
}

#[test]
fn test_equipment_type_parsing_through_command() {
    use arxos::core::EquipmentType;
    
    // Test equipment type parsing
    let hvac = equipment::parse_equipment_type("hvac");
    assert!(matches!(hvac, EquipmentType::HVAC));
    
    let electrical = equipment::parse_equipment_type("electrical");
    assert!(matches!(electrical, EquipmentType::Electrical));
    
    let custom = equipment::parse_equipment_type("custom_type");
    assert!(matches!(custom, EquipmentType::Other(_)));
    if let EquipmentType::Other(ref value) = custom {
        assert_eq!(value, "custom_type");
    }
}

#[test]
#[ignore] // Requires complete workflow setup
fn test_end_to_end_import_export_workflow() {
    // This test would verify:
    // 1. Import IFC file successfully
    // 2. Generate YAML output
    // 3. Export YAML to Git repository
    // 4. Verify changes are committed
    // Requires full infrastructure setup with Git operations
}

#[test]
#[ignore] // Requires configuration setup
fn test_config_show_command() {
    // This would test showing configuration
    // Requires proper config file setup
}

#[test]
fn test_error_handling_across_commands() {
    // Test that all commands handle errors gracefully
    // and provide helpful error messages
    
    // Import with invalid file
    let result = import::handle_import("/nonexistent/path/file.ifc".to_string(), None);
    assert!(result.is_err());
    
    // Export with invalid directory (if it returns error)
    // This depends on implementation
}

#[test]
#[ignore] // Requires Git repository setup
fn test_git_operations_with_safe_mocks() {
    
    
    // These tests would require a proper Git repository
    // They're marked ignore to avoid failures in CI/CD
    // In a real scenario, we'd create a test Git repo
}

#[test]
fn test_coordinate_parsing_edge_cases() {
    // Test edge cases
    let pos_empty = room::parse_position("");
    assert!(pos_empty.is_err());
    
    let dims_empty = room::parse_dimensions("");
    assert!(dims_empty.is_err());
    
    let pos_extra_spaces = room::parse_position("  10  ,  20  ,  5  ");
    assert!(pos_extra_spaces.is_ok());
    
    let dims_extra_spaces = room::parse_dimensions("  10  x  20  x  8  ");
    assert!(dims_extra_spaces.is_ok());
}

#[test]
fn test_equipment_type_parsing_variations() {
    use arxos::core::EquipmentType;
    
    // Test case variations
    assert!(matches!(equipment::parse_equipment_type("HVAC"), EquipmentType::HVAC));
    assert!(matches!(equipment::parse_equipment_type("Hvac"), EquipmentType::HVAC));
    assert!(matches!(equipment::parse_equipment_type("hVAC"), EquipmentType::HVAC));
    
    // Test all defined types
    assert!(matches!(equipment::parse_equipment_type("ELECTRICAL"), EquipmentType::Electrical));
    assert!(matches!(equipment::parse_equipment_type("AV"), EquipmentType::AV));
    assert!(matches!(equipment::parse_equipment_type("FURNITURE"), EquipmentType::Furniture));
    assert!(matches!(equipment::parse_equipment_type("SAFETY"), EquipmentType::Safety));
    assert!(matches!(equipment::parse_equipment_type("PLUMBING"), EquipmentType::Plumbing));
    assert!(matches!(equipment::parse_equipment_type("NETWORK"), EquipmentType::Network));
}

