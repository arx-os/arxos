//! Tests for migration command (`arx migrate`)
//!
//! Tests the migration of universal_path to ArxAddress format

use arxui::commands::migrate::handle_migrate_address;
#[allow(deprecated)]
use arxos::yaml::{
    BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, EquipmentStatus,
};
use arxos::spatial::{Point3D, BoundingBox3D};
use arxos::persistence::PersistenceManager;
use arxos::domain::ArxAddress;
use chrono::Utc;
use serial_test::serial;
use std::collections::HashMap;
use std::fs;
use tempfile::TempDir;

/// Helper to create test building data with universal_path
fn create_test_building_with_universal_path() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: 2,
            spatial_entities: 2,
            coordinate_system: "World".to_string(),
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
                wings: vec![],
                equipment: vec![
                    EquipmentData {
                        address: None,
                        id: "eq-1".to_string(),
                        name: "Boiler 01".to_string(),
                        equipment_type: "HVAC".to_string(),
                        system_type: "HVAC".to_string(),
                        position: Point3D::new(5.0, 5.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(4.0, 4.0, 0.0),
                            Point3D::new(6.0, 6.0, 2.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "Building::Test::Floor::1::Mech::Boiler_01".to_string(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        address: None,
                        id: "eq-2".to_string(),
                        name: "Valve 01".to_string(),
                        equipment_type: "Plumbing".to_string(),
                        system_type: "Plumbing".to_string(),
                        position: Point3D::new(8.0, 8.0, 0.0),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(7.0, 7.0, 0.0),
                            Point3D::new(9.0, 9.0, 1.5),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "Building::Test::Floor::1::Plumbing::Valve_01".to_string(),
                        sensor_mappings: None,
                    },
                ],
                bounding_box: None,
            },
        ],
        coordinate_systems: vec![],
    }
}

/// Test migration command with dry-run
#[test]
#[serial]
fn test_migrate_dry_run() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_universal_path();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Run migration with dry-run
    let result = handle_migrate_address(true);
    assert!(result.is_ok(), "Migration should succeed in dry-run mode");
    
    // Verify original data unchanged (dry-run doesn't modify files)
    let reloaded = persistence.load_building_data().unwrap();
    assert_eq!(reloaded.floors[0].equipment[0].address, None);
    assert_eq!(reloaded.floors[0].equipment[0].universal_path, "Building::Test::Floor::1::Mech::Boiler_01");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test migration command actually migrates data
#[test]
#[serial]
fn test_migrate_actual_migration() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Setup building data
    let building_data = create_test_building_with_universal_path();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Run migration without dry-run
    let result = handle_migrate_address(false);
    assert!(result.is_ok(), "Migration should succeed");
    
    // Verify data was migrated
    let reloaded = persistence.load_building_data().unwrap();
    let equipment = &reloaded.floors[0].equipment[0];
    
    // Should have address field populated
    assert!(equipment.address.is_some(), "Equipment should have address after migration");
    
    // Address should be valid ArxAddress
    let address = equipment.address.as_ref().unwrap();
    assert_eq!(address.path, "/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01");
    
    // Verify address validates correctly
    assert!(address.validate().is_ok(), "Migrated address should be valid");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test migration handles equipment with existing address
#[test]
#[serial]
fn test_migrate_skips_existing_address() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create building data with existing address
    let mut building_data = create_test_building_with_universal_path();
    let existing_address = ArxAddress::from_path("/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01").unwrap();
    building_data.floors[0].equipment[0].address = Some(existing_address);
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Run migration
    let result = handle_migrate_address(false);
    assert!(result.is_ok(), "Migration should succeed");
    
    // Verify existing address was preserved
    let reloaded = persistence.load_building_data().unwrap();
    let equipment = &reloaded.floors[0].equipment[0];
    assert_eq!(equipment.address.as_ref().unwrap().path, "/usa/ny/brooklyn/test-building/floor-1/mech/boiler-01");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test migration handles equipment without universal_path
#[test]
#[serial]
fn test_migrate_handles_missing_universal_path() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create building data without universal_path
    let mut building_data = create_test_building_with_universal_path();
    building_data.floors[0].equipment[0].universal_path = String::new();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Run migration
    let result = handle_migrate_address(false);
    assert!(result.is_ok(), "Migration should handle missing universal_path");
    
    // Equipment without universal_path should not get address
    let reloaded = persistence.load_building_data().unwrap();
    let equipment = &reloaded.floors[0].equipment[0];
    assert!(equipment.address.is_none(), "Equipment without universal_path should not get address");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

/// Test migration handles multiple floors
#[test]
#[serial]
fn test_migrate_multiple_floors() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_name = "test-building";
    
    // Create building data with multiple floors
    let mut building_data = create_test_building_with_universal_path();
    building_data.floors.push(FloorData {
        id: "floor-2".to_string(),
        name: "Floor 2".to_string(),
        level: 2,
        elevation: 3.0,
        rooms: vec![],
        wings: vec![],
        equipment: vec![
            EquipmentData {
                address: None,
                id: "eq-3".to_string(),
                name: "AHU 01".to_string(),
                equipment_type: "HVAC".to_string(),
                system_type: "HVAC".to_string(),
                position: Point3D::new(10.0, 10.0, 3.0),
                bounding_box: BoundingBox3D::new(
                    Point3D::new(9.0, 9.0, 3.0),
                    Point3D::new(11.0, 11.0, 5.0),
                ),
                status: EquipmentStatus::Healthy,
                properties: HashMap::new(),
                universal_path: "Building::Test::Floor::2::HVAC::AHU_01".to_string(),
                sensor_mappings: None,
            },
        ],
        bounding_box: None,
    });
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create persistence manager and save building data
    let persistence = PersistenceManager::new(building_name).unwrap();
    persistence.save_building_data(&building_data).unwrap();
    
    // Run migration
    let result = handle_migrate_address(false);
    assert!(result.is_ok(), "Migration should handle multiple floors");
    
    // Verify all floors migrated
    let reloaded = persistence.load_building_data().unwrap();
    assert_eq!(reloaded.floors.len(), 2);
    
    // Floor 1
    assert!(reloaded.floors[0].equipment[0].address.is_some());
    assert!(reloaded.floors[0].equipment[1].address.is_some());
    
    // Floor 2
    assert!(reloaded.floors[1].equipment[0].address.is_some());
    assert_eq!(reloaded.floors[1].equipment[0].address.as_ref().unwrap().path, "/usa/ny/brooklyn/test-building/floor-2/hvac/ahu-01");
    
    // Restore directory
    std::env::set_current_dir(original_dir).unwrap();
}

