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

//! Malformed Input Error Handling Tests
//!
//! Tests verify that malformed input is properly rejected with clear error messages
//! instead of silently failing or panicking.

mod malformed_input_tests {
    use super::*;
    use arxos::commands::equipment;

    #[test]
    fn test_equipment_position_malformed_coordinates() {
        // Test invalid X coordinate
        let result = equipment::handle_add_equipment(
            "Room1".to_string(),
            "Test Equipment".to_string(),
            "HVAC".to_string(),
            Some("invalid,20.0,5.0".to_string()),
            vec![],
            false,
        );
        
        assert!(result.is_err(), "Should reject invalid X coordinate");
        let error_msg = result.unwrap_err().to_string();
        assert!(error_msg.contains("Invalid X coordinate") || error_msg.contains("Invalid") ||
                error_msg.contains("Expected a number"),
                "Error should mention coordinate issue: {}", error_msg);
    }

    #[test]
    fn test_equipment_position_incomplete_coordinates() {
        // Test missing Z coordinate
        let result = equipment::handle_add_equipment(
            "Room1".to_string(),
            "Test Equipment".to_string(),
            "HVAC".to_string(),
            Some("10.0,20.0".to_string()),
            vec![],
            false,
        );
        
        assert!(result.is_err(), "Should reject incomplete coordinates");
        let error_msg = result.unwrap_err().to_string();
        assert!(error_msg.contains("x,y,z") || error_msg.contains("format") ||
                error_msg.contains("Expected format"),
                "Error should mention expected format: {}", error_msg);
    }

    #[test]
    fn test_equipment_position_valid_coordinates() {
        // Test valid coordinates should parse correctly
        let result = equipment::handle_add_equipment(
            "Room1".to_string(),
            "Test Equipment".to_string(),
            "HVAC".to_string(),
            Some("10.5,20.3,5.7".to_string()),
            vec![],
            false,
        );
        
        // May fail for other reasons (room not found, etc.) but not for coordinate parsing
        let error_msg = result.unwrap_err().to_string();
        assert!(!error_msg.contains("Invalid X coordinate") && 
                !error_msg.contains("Invalid Y coordinate") &&
                !error_msg.contains("Invalid Z coordinate"),
                "Valid coordinates should not trigger coordinate parsing errors: {}", error_msg);
    }
}

