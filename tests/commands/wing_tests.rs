//! Tests for wing functionality in room creation

use arxos::core::operations::create_room;
use arxos::core::{Floor, Room, RoomType, Wing};
use arxos::persistence::PersistenceManager;
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
use arxos::BuildingYamlSerializer;
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use tempfile::TempDir;

fn initialize_building(building_name: &str) -> PersistenceManager {
    let building_data = BuildingData {
        building: BuildingInfo {
            id: building_name.to_string(),
            name: building_name.to_string(),
            description: None,
            created_at: chrono::Utc::now(),
            updated_at: chrono::Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "wing-tests".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![Floor {
            id: "floor-1".to_string(),
            name: "Floor 1".to_string(),
            level: 1,
            elevation: Some(0.0),
            bounding_box: None,
            wings: vec![Wing {
                id: "wing-default".to_string(),
                name: "Default Wing".to_string(),
                rooms: vec![],
                equipment: vec![],
                properties: HashMap::new(),
            }],
            equipment: vec![],
            properties: HashMap::new(),
        }],
        coordinate_systems: vec![],
    };

    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer
        .to_yaml(&building_data)
        .expect("Failed to serialize building data");
    fs::write(format!("{}.yaml", building_name), yaml_content)
        .expect("Failed to write initial building YAML");
    PersistenceManager::new(building_name).expect("Failed to initialize persistence manager")
}

#[serial]
#[test]
fn test_create_room_with_wing() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();

    std::env::set_current_dir(temp_dir.path()).unwrap();

    // Create a test building
    let building_name = "TestBuilding";
    let persistence = initialize_building(building_name);

    // Create a room with a specific wing
    let room = Room::new("Test Room".to_string(), RoomType::Office);
    create_room(building_name, 1, room, Some("Wing A"), false).unwrap();

    // Load building data and verify wing was created
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data
        .floors
        .iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");

    // Verify wing exists
    let wing = floor
        .wings
        .iter()
        .find(|w| w.name == "Wing A")
        .expect("Wing A should exist");

    assert_eq!(wing.name, "Wing A");
    assert_eq!(wing.rooms.len(), 1);
    assert_eq!(wing.rooms[0].name, "Test Room");

    // Rooms are now in wings, not in a flat list

    std::env::set_current_dir(original_dir).unwrap();
}

#[serial]
#[test]
fn test_create_room_with_default_wing() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();

    std::env::set_current_dir(temp_dir.path()).unwrap();

    // Create a test building
    let building_name = "TestBuilding2";
    let persistence = initialize_building(building_name);

    // Create a room without specifying wing (should use default)
    let room = Room::new("Test Room 2".to_string(), RoomType::Classroom);
    create_room(building_name, 1, room, None, false).unwrap();

    // Load building data and verify default wing was created
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data
        .floors
        .iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");

    // Verify default wing exists
    let wing = floor
        .wings
        .iter()
        .find(|w| w.name == "Default")
        .expect("Default wing should exist");

    assert_eq!(wing.name, "Default");
    assert_eq!(wing.rooms.len(), 1);
    assert_eq!(wing.rooms[0].name, "Test Room 2");

    std::env::set_current_dir(original_dir).unwrap();
}

#[serial]
#[test]
fn test_create_multiple_rooms_in_same_wing() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();

    std::env::set_current_dir(temp_dir.path()).unwrap();

    // Create a test building
    let building_name = "TestBuilding3";
    let persistence = initialize_building(building_name);

    // Create multiple rooms in the same wing
    let room1 = Room::new("Room 1".to_string(), RoomType::Office);
    create_room(building_name, 1, room1, Some("Wing B"), false).unwrap();

    let room2 = Room::new("Room 2".to_string(), RoomType::Classroom);
    create_room(building_name, 1, room2, Some("Wing B"), false).unwrap();

    // Load building data and verify
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data
        .floors
        .iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");

    let wing = floor
        .wings
        .iter()
        .find(|w| w.name == "Wing B")
        .expect("Wing B should exist");

    assert_eq!(wing.rooms.len(), 2);
    assert!(wing.rooms.iter().any(|r| r.name == "Room 1"));
    assert!(wing.rooms.iter().any(|r| r.name == "Room 2"));

    std::env::set_current_dir(original_dir).unwrap();
}

#[serial]
#[test]
fn test_create_rooms_in_different_wings() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();

    std::env::set_current_dir(temp_dir.path()).unwrap();

    // Create a test building
    let building_name = "TestBuilding4";
    let persistence = initialize_building(building_name);

    // Create rooms in different wings
    let room1 = Room::new("North Room".to_string(), RoomType::Office);
    create_room(building_name, 1, room1, Some("North Wing"), false).unwrap();

    let room2 = Room::new("South Room".to_string(), RoomType::Classroom);
    create_room(building_name, 1, room2, Some("South Wing"), false).unwrap();

    // Load building data and verify
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data
        .floors
        .iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");

    assert!(
        floor.wings.len() >= 2,
        "Expected at least two wings, found {}",
        floor.wings.len()
    );

    let north_wing = floor
        .wings
        .iter()
        .find(|w| w.name == "North Wing")
        .expect("North Wing should exist");
    assert_eq!(north_wing.rooms.len(), 1);
    assert_eq!(north_wing.rooms[0].name, "North Room");

    let south_wing = floor
        .wings
        .iter()
        .find(|w| w.name == "South Wing")
        .expect("South Wing should exist");
    assert_eq!(south_wing.rooms.len(), 1);
    assert_eq!(south_wing.rooms[0].name, "South Room");

    std::env::set_current_dir(original_dir).unwrap();
}
