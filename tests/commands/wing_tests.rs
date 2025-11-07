//! Tests for wing functionality in room creation

use arxos::core::{Room, RoomType};
use arxos::core::operations::create_room;
use arxos::persistence::PersistenceManager;
use arxos::yaml::BuildingData;
use std::fs;
use tempfile::TempDir;

#[test]
fn test_create_room_with_wing() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();
    
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create a test building
    let building_name = "TestBuilding";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let mut building_data = BuildingData::default();
    building_data.building.name = building_name.to_string();
    persistence.save_building_data(&building_data).unwrap();
    
    // Create a room with a specific wing
    let room = Room::new("Test Room".to_string(), RoomType::Office);
    create_room(building_name, 1, room, Some("Wing A"), false).unwrap();
    
    // Load building data and verify wing was created
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data.floors.iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");
    
    // Verify wing exists
    let wing = floor.wings.iter()
        .find(|w| w.name == "Wing A")
        .expect("Wing A should exist");
    
    assert_eq!(wing.name, "Wing A");
    assert_eq!(wing.rooms.len(), 1);
    assert_eq!(wing.rooms[0].name, "Test Room");
    
    // Rooms are now in wings, not in a flat list
    
    std::env::set_current_dir(original_dir).unwrap();
}

#[test]
fn test_create_room_with_default_wing() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();
    
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create a test building
    let building_name = "TestBuilding2";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let mut building_data = BuildingData::default();
    building_data.building.name = building_name.to_string();
    persistence.save_building_data(&building_data).unwrap();
    
    // Create a room without specifying wing (should use default)
    let room = Room::new("Test Room 2".to_string(), RoomType::Classroom);
    create_room(building_name, 1, room, None, false).unwrap();
    
    // Load building data and verify default wing was created
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data.floors.iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");
    
    // Verify default wing exists
    let wing = floor.wings.iter()
        .find(|w| w.name == "Default")
        .expect("Default wing should exist");
    
    assert_eq!(wing.name, "Default");
    assert_eq!(wing.rooms.len(), 1);
    assert_eq!(wing.rooms[0].name, "Test Room 2");
    
    std::env::set_current_dir(original_dir).unwrap();
}

#[test]
fn test_create_multiple_rooms_in_same_wing() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();
    
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create a test building
    let building_name = "TestBuilding3";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let mut building_data = BuildingData::default();
    building_data.building.name = building_name.to_string();
    persistence.save_building_data(&building_data).unwrap();
    
    // Create multiple rooms in the same wing
    let room1 = Room::new("Room 1".to_string(), RoomType::Office);
    create_room(building_name, 1, room1, Some("Wing B"), false).unwrap();
    
    let room2 = Room::new("Room 2".to_string(), RoomType::Classroom);
    create_room(building_name, 1, room2, Some("Wing B"), false).unwrap();
    
    // Load building data and verify
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data.floors.iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");
    
    let wing = floor.wings.iter()
        .find(|w| w.name == "Wing B")
        .expect("Wing B should exist");
    
    assert_eq!(wing.rooms.len(), 2);
    assert!(wing.rooms.iter().any(|r| r.name == "Room 1"));
    assert!(wing.rooms.iter().any(|r| r.name == "Room 2"));
    
    std::env::set_current_dir(original_dir).unwrap();
}

#[test]
fn test_create_rooms_in_different_wings() {
    let temp_dir = TempDir::new().unwrap();
    let original_dir = std::env::current_dir().unwrap();
    
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create a test building
    let building_name = "TestBuilding4";
    let persistence = PersistenceManager::new(building_name).unwrap();
    let mut building_data = BuildingData::default();
    building_data.building.name = building_name.to_string();
    persistence.save_building_data(&building_data).unwrap();
    
    // Create rooms in different wings
    let room1 = Room::new("North Room".to_string(), RoomType::Office);
    create_room(building_name, 1, room1, Some("North Wing"), false).unwrap();
    
    let room2 = Room::new("South Room".to_string(), RoomType::Classroom);
    create_room(building_name, 1, room2, Some("South Wing"), false).unwrap();
    
    // Load building data and verify
    let building_data = persistence.load_building_data().unwrap();
    let floor = building_data.floors.iter()
        .find(|f| f.level == 1)
        .expect("Floor 1 should exist");
    
    assert_eq!(floor.wings.len(), 2);
    
    let north_wing = floor.wings.iter()
        .find(|w| w.name == "North Wing")
        .expect("North Wing should exist");
    assert_eq!(north_wing.rooms.len(), 1);
    assert_eq!(north_wing.rooms[0].name, "North Room");
    
    let south_wing = floor.wings.iter()
        .find(|w| w.name == "South Wing")
        .expect("South Wing should exist");
    assert_eq!(south_wing.rooms.len(), 1);
    assert_eq!(south_wing.rooms[0].name, "South Room");
    
    std::env::set_current_dir(original_dir).unwrap();
}

