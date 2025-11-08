//! Tests for room management command handlers

use arxui::commands::room;

// Note: parse_room_type doesn't exist in the module, but we can test what's there

#[test]
fn test_parse_dimensions_valid_format() {
    // Test valid 3-part dimensions (width x depth x height)
    let result = room::parse_dimensions("10 x 20 x 8");
    assert!(result.is_ok());
    let (width, depth, height) = result.unwrap();
    assert_eq!(width, 10.0);
    assert_eq!(depth, 20.0);
    assert_eq!(height, 8.0);
}

#[test]
fn test_parse_dimensions_with_spaces() {
    // Test dimensions with extra spaces
    let result = room::parse_dimensions("15.5 x 25.3 x 9.2");
    assert!(result.is_ok());
    let (width, depth, height) = result.unwrap();
    assert_eq!(width, 15.5);
    assert_eq!(depth, 25.3);
    assert_eq!(height, 9.2);
}

#[test]
fn test_parse_dimensions_invalid_format() {
    // Test invalid format (wrong number of parts)
    let result = room::parse_dimensions("10x20"); // Missing height
    assert!(result.is_err());
    
    let error_msg = result.unwrap_err().to_string();
    assert!(error_msg.contains("Invalid dimensions format"));
}

#[test]
fn test_parse_dimensions_non_numeric() {
    // Test with non-numeric values
    let result = room::parse_dimensions("invalid x 20 x 8");
    assert!(result.is_err());
}

#[test]
fn test_parse_position_valid_format() {
    // Test valid 3-part position (x,y,z)
    let result = room::parse_position("10, 20, 5");
    assert!(result.is_ok());
    let (x, y, z) = result.unwrap();
    assert_eq!(x, 10.0);
    assert_eq!(y, 20.0);
    assert_eq!(z, 5.0);
}

#[test]
fn test_parse_position_with_floats() {
    // Test position with floating point values
    let result = room::parse_position("15.5, 25.3, 9.2");
    assert!(result.is_ok());
    let (x, y, z) = result.unwrap();
    assert_eq!(x, 15.5);
    assert_eq!(y, 25.3);
    assert_eq!(z, 9.2);
}

#[test]
fn test_parse_position_invalid_format() {
    // Test invalid format (wrong number of coordinates)
    let result = room::parse_position("10,20"); // Missing z
    assert!(result.is_err());
    
    let error_msg = result.unwrap_err().to_string();
    assert!(error_msg.contains("Invalid position format"));
}

#[test]
fn test_parse_position_non_numeric() {
    // Test with non-numeric values
    let result = room::parse_position("invalid, 20, 5");
    assert!(result.is_err());
}

#[test]
#[ignore] // Requires building data setup
fn test_room_creation_command() {
    // This would test the full room creation flow
    // Requires proper building data setup
}

#[test]
#[ignore] // Requires building data setup
fn test_room_listing_command() {
    // This would test the room listing functionality
    // Requires proper building data setup
}

