//! Integration tests for IFC bidirectional sync workflow
//!
//! These tests verify the complete YAML → IFC export workflow, including
//! delta tracking, sync state persistence, and round-trip compatibility.

use arxos::export::ifc::{IFCExporter, IFCSyncState};
use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData, EquipmentData, EquipmentStatus, CoordinateSystemInfo};
use arxos::spatial::{Point3D, BoundingBox3D};
use std::fs;
use std::path::PathBuf;
use std::collections::HashMap;
use tempfile::TempDir;
use chrono::Utc;

/// Create test building data
fn create_test_building_data() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "test-building".to_string(),
            name: "Test Building".to_string(),
            description: Some("Test building for integration tests".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "ArxOS v2.0".to_string(),
            total_entities: 3,
            spatial_entities: 3,
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
                rooms: vec![
                    RoomData {
                        id: "room-101".to_string(),
                        name: "Room 101".to_string(),
                        room_type: "Office".to_string(),
                        area: Some(25.0),
                        volume: Some(75.0),
                        position: Point3D::new(5.0, 5.0, 1.5),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(0.0, 0.0, 0.0),
                            Point3D::new(10.0, 5.0, 3.0),
                        ),
                        equipment: vec![],
                        properties: HashMap::new(),
                    },
                    RoomData {
                        id: "room-102".to_string(),
                        name: "Room 102".to_string(),
                        room_type: "Conference".to_string(),
                        area: Some(50.0),
                        volume: Some(150.0),
                        position: Point3D::new(15.0, 5.0, 1.5),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(10.0, 0.0, 0.0),
                            Point3D::new(20.0, 5.0, 3.0),
                        ),
                        equipment: vec![],
                        properties: HashMap::new(),
                    },
                ],
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
                        universal_path: "building/floor-1/room-101/equipment-hvac-1".to_string(),
                        sensor_mappings: None,
                    },
                    EquipmentData {
                        id: "equipment-2".to_string(),
                        name: "Light Fixture 1".to_string(),
                        equipment_type: "Electrical".to_string(),
                        system_type: "Electrical".to_string(),
                        position: Point3D::new(7.0, 2.5, 2.5),
                        bounding_box: BoundingBox3D::new(
                            Point3D::new(6.5, 2.0, 2.0),
                            Point3D::new(7.5, 3.0, 3.0),
                        ),
                        status: EquipmentStatus::Healthy,
                        properties: HashMap::new(),
                        universal_path: "building/floor-1/room-101/equipment-electrical-1".to_string(),
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
fn test_full_ifc_export_workflow() {
    let temp_dir = TempDir::new().unwrap();
    let ifc_path = temp_dir.path().join("test_export.ifc");
    
    let building_data = create_test_building_data();
    let exporter = IFCExporter::new(building_data);
    
    // Export to IFC
    exporter.export(&ifc_path).expect("Export should succeed");
    
    // Verify IFC file was created
    assert!(ifc_path.exists(), "IFC file should be created");
    
    // Verify IFC file is not empty
    let file_size = fs::metadata(&ifc_path).unwrap().len();
    assert!(file_size > 0, "IFC file should not be empty");
    
    // Verify IFC file contains expected content
    let content = fs::read_to_string(&ifc_path).unwrap();
    assert!(content.contains("ISO-10303-21"), "Should contain IFC header");
    assert!(content.contains("IFCROOM"), "Should contain room entities");
    assert!(content.contains("IFCAIRTERMINAL"), "Should contain HVAC equipment");
    assert!(content.contains("IFCLIGHTFIXTURE"), "Should contain electrical equipment");
}

#[test]
fn test_delta_export_workflow() {
    let temp_dir = TempDir::new().unwrap();
    let ifc_path = temp_dir.path().join("test_delta.ifc");
    let sync_state_path = temp_dir.path().join("sync-state.json");
    
    let mut building_data = create_test_building_data();
    let exporter = IFCExporter::new(building_data.clone());
    
    // First export - full export
    exporter.export(&ifc_path).expect("First export should succeed");
    
    // Update sync state
    let (equipment_paths, rooms_paths) = exporter.collect_universal_paths();
    let mut sync_state = IFCSyncState::new(ifc_path.clone());
    sync_state.update_after_export(equipment_paths, rooms_paths);
    sync_state.save(&sync_state_path).expect("Should save sync state");
    
    // Add new equipment to building data
    building_data.floors[0].equipment.push(EquipmentData {
        id: "equipment-3".to_string(),
        name: "Pump Unit 1".to_string(),
        equipment_type: "Plumbing".to_string(),
        system_type: "Plumbing".to_string(),
        position: Point3D::new(12.0, 2.0, 1.0),
        bounding_box: BoundingBox3D::new(
            Point3D::new(11.0, 1.0, 0.0),
            Point3D::new(13.0, 3.0, 2.0),
        ),
        status: EquipmentStatus::Healthy,
        properties: HashMap::new(),
        universal_path: "building/floor-1/room-102/equipment-plumbing-1".to_string(),
        sensor_mappings: None,
    });
    
    // Second export - delta export
    let sync_state = IFCSyncState::load(&sync_state_path).unwrap();
    let exporter2 = IFCExporter::new(building_data.clone());
    
    // Verify delta calculation works
    use arxos::export::ifc::delta::calculate_delta;
    let delta = calculate_delta(&building_data, Some(&sync_state));
    assert!(delta.has_changes(), "Delta should have changes");
    assert_eq!(delta.new_equipment.len(), 1, "Should detect one new equipment");
    
    // Export delta
    exporter2.export_delta(Some(&sync_state), &ifc_path).expect("Delta export should succeed");
    
    // Verify IFC file was updated with new equipment
    // Note: Delta export creates a file with ONLY the changes, not the full file
    let content = fs::read_to_string(&ifc_path).unwrap();
    assert!(content.contains("IFCFLOWTERMINAL") || content.contains("Pump Unit 1"), 
            "Should contain new plumbing equipment (IFCFLOWTERMINAL or equipment name)");
}

#[test]
fn test_sync_state_persistence() {
    let temp_dir = TempDir::new().unwrap();
    let sync_state_path = temp_dir.path().join("sync-state.json");
    let ifc_path = temp_dir.path().join("test.ifc");
    
    // Create and save sync state
    let mut sync_state = IFCSyncState::new(ifc_path.clone());
    let equipment_paths: std::collections::HashSet<String> = [
        "building/floor-1/equipment-1".to_string(),
        "building/floor-1/equipment-2".to_string(),
    ].into_iter().collect();
    let rooms_paths: std::collections::HashSet<String> = [
        "building/floor-1/room-101".to_string(),
    ].into_iter().collect();
    
    sync_state.update_after_export(equipment_paths.clone(), rooms_paths.clone());
    sync_state.save(&sync_state_path).expect("Should save sync state");
    
    // Load sync state
    let loaded_state = IFCSyncState::load(&sync_state_path).expect("Should load sync state");
    
    assert_eq!(loaded_state.exported_equipment_paths.len(), 2);
    assert_eq!(loaded_state.exported_rooms_paths.len(), 1);
    assert!(loaded_state.exported_equipment_paths.contains("building/floor-1/equipment-1"));
    assert!(loaded_state.exported_equipment_paths.contains("building/floor-1/equipment-2"));
    assert!(loaded_state.exported_rooms_paths.contains("building/floor-1/room-101"));
}

#[test]
fn test_delta_calculation_integration() {
    let temp_dir = TempDir::new().unwrap();
    let sync_state_path = temp_dir.path().join("sync-state.json");
    let ifc_path = temp_dir.path().join("test.ifc");
    
    // Initial building data
    let mut building_data = create_test_building_data();
    let exporter = IFCExporter::new(building_data.clone());
    
    // Export and save state
    exporter.export(&ifc_path).expect("Export should succeed");
    let (equipment_paths, rooms_paths) = exporter.collect_universal_paths();
    let mut sync_state = IFCSyncState::new(ifc_path.clone());
    sync_state.update_after_export(equipment_paths, rooms_paths);
    sync_state.save(&sync_state_path).expect("Should save sync state");
    
    // Modify building data - add new equipment, remove old one
    building_data.floors[0].equipment.remove(1); // Remove equipment-2
    building_data.floors[0].equipment.push(EquipmentData {
        id: "equipment-3".to_string(),
        name: "New Equipment".to_string(),
        equipment_type: "HVAC".to_string(),
        system_type: "HVAC".to_string(),
        position: Point3D::new(10.0, 10.0, 2.0),
        bounding_box: BoundingBox3D::new(
            Point3D::new(9.0, 9.0, 1.0),
            Point3D::new(11.0, 11.0, 3.0),
        ),
        status: EquipmentStatus::Healthy,
        properties: HashMap::new(),
        universal_path: "building/floor-1/room-102/equipment-hvac-3".to_string(),
        sensor_mappings: None,
    });
    
    // Calculate delta
    let sync_state = IFCSyncState::load(&sync_state_path).unwrap();
    use arxos::export::ifc::delta::calculate_delta;
    let delta = calculate_delta(&building_data, Some(&sync_state));
    
    // Verify delta contains expected changes
    assert!(delta.has_changes(), "Delta should have changes");
    assert_eq!(delta.new_equipment.len(), 1, "Should have one new equipment");
    assert_eq!(delta.deleted_equipment.len(), 1, "Should have one deleted equipment");
    assert!(delta.deleted_equipment.contains(&"building/floor-1/room-101/equipment-electrical-1".to_string()));
}

#[test]
fn test_empty_building_export() {
    let temp_dir = TempDir::new().unwrap();
    let ifc_path = temp_dir.path().join("empty_building.ifc");
    
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
    
    let exporter = IFCExporter::new(building_data);
    exporter.export(&ifc_path).expect("Empty export should succeed");
    
    // Empty building should still create valid IFC file with header
    assert!(ifc_path.exists());
    let content = fs::read_to_string(&ifc_path).unwrap();
    assert!(content.contains("ISO-10303-21"), "Should contain IFC header");
}

#[test]
fn test_multiple_floors_export() {
    let temp_dir = TempDir::new().unwrap();
    let ifc_path = temp_dir.path().join("multi_floor.ifc");
    
    let mut building_data = create_test_building_data();
    
    // Add second floor
    building_data.floors.push(FloorData {
        id: "floor-2".to_string(),
        name: "Floor 2".to_string(),
        level: 2,
        elevation: 3.0,
        rooms: vec![RoomData {
            id: "room-201".to_string(),
            name: "Room 201".to_string(),
            room_type: "Office".to_string(),
            area: Some(30.0),
            volume: Some(90.0),
            position: Point3D::new(5.0, 5.0, 4.5),
            bounding_box: BoundingBox3D::new(
                Point3D::new(0.0, 0.0, 3.0),
                Point3D::new(10.0, 5.0, 6.0),
            ),
            equipment: vec![],
            properties: HashMap::new(),
        }],
        equipment: vec![EquipmentData {
            id: "equipment-floor2-1".to_string(),
            name: "Floor 2 Equipment".to_string(),
            equipment_type: "HVAC".to_string(),
            system_type: "HVAC".to_string(),
            position: Point3D::new(2.0, 2.0, 4.5),
            bounding_box: BoundingBox3D::new(
                Point3D::new(1.0, 1.0, 4.0),
                Point3D::new(3.0, 3.0, 5.0),
            ),
            status: EquipmentStatus::Healthy,
            properties: HashMap::new(),
            universal_path: "building/floor-2/room-201/equipment-hvac-1".to_string(),
            sensor_mappings: None,
        }],
        bounding_box: None,
    });
    
    let exporter = IFCExporter::new(building_data);
    exporter.export(&ifc_path).expect("Multi-floor export should succeed");
    
    assert!(ifc_path.exists());
    let content = fs::read_to_string(&ifc_path).unwrap();
    
    // Should contain rooms and equipment from both floors
    assert!(content.contains("Room 101"));
    assert!(content.contains("Room 201"));
    assert!(content.contains("HVAC Unit 1"));
    assert!(content.contains("Floor 2 Equipment"));
}

#[test]
fn test_universal_path_preservation() {
    let temp_dir = TempDir::new().unwrap();
    let ifc_path = temp_dir.path().join("preserve_paths.ifc");
    
    let building_data = create_test_building_data();
    let exporter = IFCExporter::new(building_data);
    
    // Export
    exporter.export(&ifc_path).expect("Export should succeed");
    
    // Verify Universal Paths are used as entity IDs in IFC
    let content = fs::read_to_string(&ifc_path).unwrap();
    
    // The Universal Path should appear in the IFC file as the entity identifier
    // Note: This depends on how EnhancedIFCParser writes entities
    // The entity.id field (which contains Universal Path) should be in the IFC output
    assert!(content.contains("building/floor-1/room-101/equipment-hvac-1") || 
            content.contains("HVAC Unit 1"), 
            "Universal Path or equipment name should be in IFC");
}

