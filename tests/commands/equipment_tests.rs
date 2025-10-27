//! Tests for equipment management command handlers

use arxos::commands::equipment::handle_equipment_command;
use arxos::cli::EquipmentCommands;
use tempfile::TempDir;

#[test]
fn test_parse_equipment_type() {
    use arxos::commands::equipment::parse_equipment_type;
    use arxos::core::EquipmentType;
    
    // Test valid equipment types
    assert!(matches!(parse_equipment_type("hvac"), EquipmentType::HVAC));
    assert!(matches!(parse_equipment_type("electrical"), EquipmentType::Electrical));
    assert!(matches!(parse_equipment_type("plumbing"), EquipmentType::Plumbing));
    assert!(matches!(parse_equipment_type("mechanical"), EquipmentType::Mechanical));
    assert!(matches!(parse_equipment_type("furniture"), EquipmentType::Furniture));
    assert!(matches!(parse_equipment_type("other"), EquipmentType::Other));
    
    // Test invalid type (defaults to Other)
    assert!(matches!(parse_equipment_type("invalid"), EquipmentType::Other));
}

#[test]
#[ignore] // Requires building data setup
fn test_equipment_add_command() {
    // This would test equipment addition
    // Requires proper building data setup
}

#[test]
#[ignore] // Requires building data setup
fn test_equipment_listing_command() {
    // This would test equipment listing
    // Requires proper building data setup
}

#[test]
#[ignore] // Requires building data setup
fn test_equipment_update_command() {
    // This would test equipment updates
    // Requires proper building data setup
}

