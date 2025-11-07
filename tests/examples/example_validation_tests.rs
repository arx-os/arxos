//! Validation tests for example files
//!
//! These tests ensure that all example files in the `examples/` directory
//! are valid and match the current BuildingData schema.

use arxos::yaml::BuildingData;
use std::fs;
use std::path::Path;

/// Test that all example building files are valid YAML and match the schema
#[test]
fn test_example_buildings_are_valid() {
    let examples_dir = Path::new("examples/buildings");
    
    // List of example files to validate
    let example_files = vec![
        "building.yaml",
        "minimal-building.yaml",
        "multi-floor-building.yaml",
    ];
    
    for file_name in example_files {
        let file_path = examples_dir.join(file_name);
        
        // Read file
        let content = fs::read_to_string(&file_path)
            .unwrap_or_else(|_| panic!("Failed to read example file: {}", file_path.display()));
        
        // Parse YAML
        let building_data: BuildingData = serde_yaml::from_str(&content)
            .unwrap_or_else(|e| {
                panic!(
                    "Failed to parse example file {}: {}",
                    file_path.display(),
                    e
                )
            });
        
        // Validate structure
        assert!(!building_data.building.name.is_empty(), 
            "Building name should not be empty in {}", file_name);
        assert!(!building_data.building.id.is_empty(),
            "Building ID should not be empty in {}", file_name);
        
        // Validate metadata
        assert_eq!(building_data.metadata.units, "meters",
            "Units should be meters in {}", file_name);
        assert!(!building_data.metadata.coordinate_system.is_empty(),
            "Coordinate system should not be empty in {}", file_name);
        
        // Validate coordinate systems
        assert!(!building_data.coordinate_systems.is_empty(),
            "Should have at least one coordinate system in {}", file_name);
        
        // Validate floors
        for floor in &building_data.floors {
            assert!(!floor.id.is_empty(),
                "Floor ID should not be empty in {}", file_name);
            assert!(!floor.name.is_empty(),
                "Floor name should not be empty in {}", file_name);
            
            // Validate rooms (now in wings)
            for wing in &floor.wings {
                for room in &wing.rooms {
                    assert!(!room.id.is_empty(),
                        "Room ID should not be empty in {}", file_name);
                    assert!(!room.name.is_empty(),
                        "Room name should not be empty in {}", file_name);
                }
            }
            
            // Validate equipment
            for equipment in &floor.equipment {
                assert!(!equipment.id.is_empty(),
                    "Equipment ID should not be empty in {}", file_name);
                assert!(!equipment.name.is_empty(),
                    "Equipment name should not be empty in {}", file_name);
                // equipment_type is an enum, check if it's Other("")
                assert!(!equipment.path.is_empty(),
                    "Equipment path should not be empty in {}", file_name);
            }
        }
    }
}

/// Test that example files use human-readable names (not obfuscated)
#[test]
fn test_example_names_are_readable() {
    let examples_dir = Path::new("examples/buildings");
    let example_files = vec![
        "building.yaml",
        "minimal-building.yaml",
        "multi-floor-building.yaml",
    ];
    
    for file_name in example_files {
        let file_path = examples_dir.join(file_name);
        let content = fs::read_to_string(&file_path)
            .unwrap_or_else(|_| panic!("Failed to read example file: {}", file_path.display()));
        
        let building_data: BuildingData = serde_yaml::from_str(&content)
            .unwrap_or_else(|e| {
                panic!(
                    "Failed to parse example file {}: {}",
                    file_path.display(),
                    e
                )
            });
        
        // Check building name is readable (contains letters, not just random characters)
        let building_name = &building_data.building.name;
        assert!(
            building_name.chars().any(|c| c.is_alphabetic()),
            "Building name should contain letters in {}: '{}'",
            file_name,
            building_name
        );
        
        // Check floor names are readable
        for floor in &building_data.floors {
            assert!(
                floor.name.chars().any(|c| c.is_alphabetic()),
                "Floor name should contain letters in {}: '{}'",
                file_name,
                floor.name
            );
            
            // Check room names are readable (now in wings)
            for wing in &floor.wings {
                for room in &wing.rooms {
                    assert!(
                        room.name.chars().any(|c| c.is_alphabetic()),
                        "Room name should contain letters in {}: '{}'",
                        file_name,
                        room.name
                    );
                }
            }
            
            // Check equipment names are readable
            for equipment in &floor.equipment {
                assert!(
                    equipment.name.chars().any(|c| c.is_alphabetic()),
                    "Equipment name should contain letters in {}: '{}'",
                    file_name,
                    equipment.name
                );
            }
        }
    }
}

/// Test that coordinates are reasonable (not extreme precision issues)
#[test]
fn test_example_coordinates_are_reasonable() {
    let examples_dir = Path::new("examples/buildings");
    let example_files = vec![
        "building.yaml",
        "minimal-building.yaml",
        "multi-floor-building.yaml",
    ];
    
    for file_name in example_files {
        let file_path = examples_dir.join(file_name);
        let content = fs::read_to_string(&file_path)
            .unwrap_or_else(|_| panic!("Failed to read example file: {}", file_path.display()));
        
        let building_data: BuildingData = serde_yaml::from_str(&content)
            .unwrap_or_else(|e| {
                panic!(
                    "Failed to parse example file {}: {}",
                    file_path.display(),
                    e
                )
            });
        
        // Check for reasonable coordinate values (not extreme)
        const MAX_REASONABLE_COORD: f64 = 10000.0; // 10km max
        const MIN_REASONABLE_COORD: f64 = -10000.0;
        
        for floor in &building_data.floors {
            for wing in &floor.wings {
                for room in &wing.rooms {
                    // Check position
                    let pos = &room.spatial_properties.position;
                    assert!(
                        pos.x >= MIN_REASONABLE_COORD && pos.x <= MAX_REASONABLE_COORD,
                        "Room position x should be reasonable in {}: {}",
                        file_name,
                        pos.x
                    );
                    assert!(
                        pos.y >= MIN_REASONABLE_COORD && pos.y <= MAX_REASONABLE_COORD,
                        "Room position y should be reasonable in {}: {}",
                        file_name,
                        pos.y
                    );
                    assert!(
                        pos.z >= MIN_REASONABLE_COORD && pos.z <= MAX_REASONABLE_COORD,
                        "Room position z should be reasonable in {}: {}",
                        file_name,
                        pos.z
                    );
                    
                    // Check bounding box
                    let bbox = &room.spatial_properties.bounding_box;
                    assert!(
                        bbox.min.x >= MIN_REASONABLE_COORD && bbox.min.x <= MAX_REASONABLE_COORD,
                        "Bounding box min.x should be reasonable in {}: {}",
                        file_name,
                        bbox.min.x
                    );
                    assert!(
                        bbox.max.x >= MIN_REASONABLE_COORD && bbox.max.x <= MAX_REASONABLE_COORD,
                        "Bounding box max.x should be reasonable in {}: {}",
                        file_name,
                        bbox.max.x
                    );
                }
            }
            
            for equipment in &floor.equipment {
                let pos = &equipment.position;
                assert!(
                    pos.x >= MIN_REASONABLE_COORD && pos.x <= MAX_REASONABLE_COORD,
                    "Equipment position x should be reasonable in {}: {}",
                    file_name,
                    pos.x
                );
            }
        }
    }
}

/// Test that metadata is consistent with actual content
#[test]
fn test_example_metadata_consistency() {
    let examples_dir = Path::new("examples/buildings");
    let example_files = vec![
        "building.yaml",
        "minimal-building.yaml",
        "multi-floor-building.yaml",
    ];
    
    for file_name in example_files {
        let file_path = examples_dir.join(file_name);
        let content = fs::read_to_string(&file_path)
            .unwrap_or_else(|_| panic!("Failed to read example file: {}", file_path.display()));
        
        let building_data: BuildingData = serde_yaml::from_str(&content)
            .unwrap_or_else(|e| {
                panic!(
                    "Failed to parse example file {}: {}",
                    file_path.display(),
                    e
                )
            });
        
        // Count actual entities
        let total_floors = building_data.floors.len();
        let total_rooms: usize = building_data.floors.iter()
            .flat_map(|f| f.wings.iter())
            .map(|w| w.rooms.len())
            .sum();
        let total_equipment: usize = building_data.floors.iter()
            .map(|f| f.equipment.len())
            .sum();
        let total_entities = total_floors + total_rooms + total_equipment;
        
        // Metadata should match or be reasonable
        // Allow some flexibility since metadata might include other entities
        assert!(
            building_data.metadata.total_entities >= total_entities || total_entities == 0,
            "total_entities ({}) should be >= actual count ({}) in {}",
            building_data.metadata.total_entities,
            total_entities,
            file_name
        );
    }
}

/// Test that the complete building example has equipment
#[test]
fn test_complete_building_has_equipment() {
    let file_path = Path::new("examples/buildings/building.yaml");
    let content = fs::read_to_string(file_path)
        .expect("Failed to read building.yaml");
    
    let building_data: BuildingData = serde_yaml::from_str(&content)
        .expect("Failed to parse building.yaml");
    
    // Complete building should have equipment
    let total_equipment: usize = building_data.floors.iter()
        .map(|f| f.equipment.len())
        .sum();
    
    assert!(
        total_equipment > 0,
        "Complete building example should have equipment, found {}",
        total_equipment
    );
    
    // Should have rooms with equipment references
    let rooms_with_equipment: usize = building_data.floors.iter()
        .flat_map(|f| f.wings.iter())
        .map(|w| w.rooms.iter().filter(|r| !r.equipment.is_empty()).count())
        .sum();
    
    assert!(
        rooms_with_equipment > 0,
        "Complete building example should have rooms with equipment references"
    );
}

