//! # Integration Tests for ArxOS
//!
//! This module contains comprehensive integration tests that verify
//! cross-crate functionality and end-to-end workflows.

use arxos_core::{ArxOSCore, RoomType, EquipmentType, Point3D};
    use std::fs;
use std::path::Path;
use tempfile::TempDir;

/// Test helper to create a temporary test environment
fn setup_test_environment() -> TempDir {
    let temp_dir = tempfile::tempdir().expect("Failed to create temp directory");
    // Change to the temp directory to avoid polluting the project root
    std::env::set_current_dir(temp_dir.path()).expect("Failed to change to temp directory");
    temp_dir
}

/// Test helper to clean up test environment
fn cleanup_test_environment(temp_dir: TempDir) {
    // Change back to the original directory
    std::env::set_current_dir("/Users/joelpate/repos/arxos").expect("Failed to change back to project root");
    temp_dir.close().expect("Failed to close temp directory");
}

// Force tests to run sequentially to avoid interference
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_core_cli_integration_room_management() {
        let temp_dir = setup_test_environment();
    
    // Test core room creation
    let mut core = ArxOSCore::new().expect("Failed to create core");
    
    // Create a room using core
    let room = core.create_room(
        "Test Building",
        1,
        "A",
        "Test Room",
        RoomType::Classroom,
    ).expect("Failed to create room");
    
    // Verify room was created
    assert_eq!(room.name, "Test Room");
    assert_eq!(room.room_type, RoomType::Classroom);
    
    // Verify file system persistence
    let room_dir = Path::new("./data/Test Building/1/A/Test Room");
    assert!(room_dir.exists(), "Room directory should exist");
    
    let room_file = room_dir.join("room.yaml");
    assert!(room_file.exists(), "Room YAML file should exist");
    
    // Test room listing
    let rooms = core.list_rooms("Test Building", 1, Some("A"))
        .expect("Failed to list rooms");
    
    assert!(!rooms.is_empty(), "Should have at least one room");
    assert_eq!(rooms[0].name, "Test Room");
    
    // Test room retrieval
    let retrieved_room = core.get_room("Test Building", 1, "A", "Test Room")
        .expect("Failed to get room");
    
    assert_eq!(retrieved_room.name, "Test Room");
    
    // Test room update
    let updated_room = core.update_room(
        "Test Building",
        1,
        "A",
        "Test Room",
        Some("Updated Room"),
        Some(RoomType::Office),
        None,
        None,
    ).expect("Failed to update room");
    
    assert_eq!(updated_room.name, "Updated Room");
    assert_eq!(updated_room.room_type, RoomType::Office);
    
    // Test room deletion (use original name since directory wasn't renamed)
    core.delete_room("Test Building", 1, "A", "Test Room")
        .expect("Failed to delete room");
    
    // Verify room was deleted (check original room directory)
    assert!(!room_dir.exists(), "Original room directory should be deleted");
    
    cleanup_test_environment(temp_dir);
    }
    
    #[test]
fn test_core_cli_integration_equipment_management() {
    let temp_dir = setup_test_environment();
    
    // Test core equipment management
    let mut core = ArxOSCore::new().expect("Failed to create core");
    
    // First create a room
    let _room = core.create_room(
        "Test Building",
        1,
        "A",
        "Test Room",
        RoomType::Classroom,
    ).expect("Failed to create room");
    
    // Add equipment to the room
    let equipment = core.add_equipment(
        "Test Building",
        1,
        "A",
        "Test Room",
        "Test Equipment",
        EquipmentType::HVAC,
        Some(Point3D { x: 10.0, y: 5.0, z: 1.0 }),
    ).expect("Failed to add equipment");
    
    // Verify equipment was created
    assert_eq!(equipment.name, "Test Equipment");
    assert_eq!(equipment.equipment_type, EquipmentType::HVAC);
    
    // Verify file system persistence
    let equipment_dir = Path::new("./data/Test Building/1/A/Test Room/equipment/Test Equipment");
    assert!(equipment_dir.exists(), "Equipment directory should exist");
    
    let equipment_file = equipment_dir.join("equipment.yaml");
    assert!(equipment_file.exists(), "Equipment YAML file should exist");
    
    // Test equipment listing
    let equipment_list = core.list_equipment("Test Building", 1, "A", "Test Room")
        .expect("Failed to list equipment");
    
    assert!(!equipment_list.is_empty(), "Should have at least one equipment");
    assert_eq!(equipment_list[0].name, "Test Equipment");
    
    // Test equipment update
    let updated_equipment = core.update_equipment(
        "Test Building",
        1,
        "A",
        "Test Room",
        "Test Equipment",
        Some("Updated Equipment"),
        Some(EquipmentType::Electrical),
        Some(Point3D { x: 15.0, y: 10.0, z: 1.0 }),
    ).expect("Failed to update equipment");
    
    assert_eq!(updated_equipment.name, "Updated Equipment");
    assert_eq!(updated_equipment.equipment_type, EquipmentType::Electrical);
    
    // Test equipment removal (use original name since directory wasn't renamed)
    core.remove_equipment("Test Building", 1, "A", "Test Room", "Test Equipment")
        .expect("Failed to remove equipment");
    
    // Verify equipment was removed (check original equipment directory)
    assert!(!equipment_dir.exists(), "Original equipment directory should be deleted");
    
    cleanup_test_environment(temp_dir);
    }
    
    #[test]
fn test_core_cli_integration_spatial_operations() {
    let temp_dir = setup_test_environment();
    
    // Test core spatial operations
    let mut core = ArxOSCore::new().expect("Failed to create core");
    
    // First create some rooms to establish spatial data
    let _room1 = core.create_room(
        "Test Building",
        1,
        "A",
        "Room1",
        RoomType::Classroom,
    ).expect("Failed to create room1");
    
    let _room2 = core.create_room(
        "Test Building",
        1,
        "A",
        "Room2",
        RoomType::Office,
    ).expect("Failed to create room2");
    
    // Test spatial query
    let query_results = core.spatial_query(
        "Test Building",
        "rooms_in_floor",
        &["1".to_string()],
    ).expect("Failed to perform spatial query");
    
    assert!(!query_results.is_empty(), "Should have spatial query results");
    assert_eq!(query_results[0].entity_type, "room");
    
    // Test spatial relationship
    let relationship = core.get_spatial_relationship(
        "Test Building",
        "room1",
        "room2",
    ).expect("Failed to get spatial relationship");
    
    assert_eq!(relationship.relationship_type, arxos_core::SpatialRelationshipType::Adjacent);
    
    // Test spatial transformation
    let transform_result = core.apply_spatial_transformation(
        "Test Building",
        "room1",
        "translate_x_10",
    ).expect("Failed to apply spatial transformation");
    
    assert_eq!(transform_result.new_position.x, 10.0);
    
    // Test spatial validation
    let validation = core.validate_spatial_data("Test Building")
        .expect("Failed to validate spatial data");
    
    assert!(validation.total_entities > 0, "Should have validated entities");
    
    cleanup_test_environment(temp_dir);
    }
    
    #[test]
fn test_core_cli_integration_configuration_management() {
    let temp_dir = setup_test_environment();
    
    // Test core configuration management
    let mut core = ArxOSCore::new().expect("Failed to create core");
    
    // Test configuration retrieval (should create default)
    let config = core.get_configuration().expect("Failed to get configuration");
    
    assert_eq!(config.user_name, "Default User");
    assert_eq!(config.user_email, "user@example.com");
    assert_eq!(config.building_name, "Default Building");
    
    // Verify config file was created
    assert!(Path::new("./arx.toml").exists(), "Config file should exist");
    
    // Test configuration setting
    core.set_configuration_value("user_name", "Test User")
        .expect("Failed to set configuration value");
    
    // Test configuration retrieval after setting
    let updated_config = core.get_configuration().expect("Failed to get updated configuration");
    assert_eq!(updated_config.user_name, "Test User");
    
    // Test configuration reset
    core.reset_configuration().expect("Failed to reset configuration");
    
    // Verify reset
    let reset_config = core.get_configuration().expect("Failed to get reset configuration");
    assert_eq!(reset_config.user_name, "Default User");
    
    cleanup_test_environment(temp_dir);
    }
    
    #[test]
fn test_core_cli_integration_live_monitoring() {
    let temp_dir = setup_test_environment();
    
    // Test core live monitoring
    let mut core = ArxOSCore::new().expect("Failed to create core");
    
    // First create a room to establish building data
    let _room = core.create_room(
        "Test Building",
        1,
        "A",
        "Room1",
        RoomType::Classroom,
    ).expect("Failed to create room");
    
    // Test live monitoring
    let monitoring_result = core.start_live_monitoring(
        "Test Building",
        Some(1),
        Some("Room1"),
        1000,
    ).expect("Failed to start live monitoring");
    
    assert!(monitoring_result.total_updates > 0, "Should have monitoring updates");
    assert!(monitoring_result.data_points_collected > 0, "Should have collected data points");
    
    // Verify monitoring session was created
    let monitoring_dir = Path::new("./data/Test Building/monitoring");
    assert!(monitoring_dir.exists(), "Monitoring directory should exist");
    
    cleanup_test_environment(temp_dir);
    }

    #[test]
fn test_core_cli_integration_ifc_processing() {
    let temp_dir = setup_test_environment();
    
    // Test core IFC processing
    let core = ArxOSCore::new().expect("Failed to create core");
    
    // Create a mock IFC file
    let ifc_content = r#"#1=IFCPROJECT('0Kj8nYj4X1E8L7vM3Q2R5S',#2,$,$,$,$,$,$,$);
#2=IFCOWNERHISTORY(#3,#4,#5,$,.ADDED.,$,$,$,0);
#3=IFCPERSON($,'John Doe',$,$,$,$,$,$);
#4=IFCORGANIZATION($,'Test Organization',$,$,$);
#5=IFCPERSONANDORGANIZATION(#3,#4,$);
#6=IFCSITE('0Kj8nYj4X1E8L7vM3Q2R5T',$,'Test Site',$,$,$,$,$,$,$,$,$,$,$,$,$,$);
#7=IFCBUILDING('0Kj8nYj4X1E8L7vM3Q2R5U',$,'Test Building',$,$,$,$,$,$,$,$,$,$,$,$,$,$);
"#;
    
    let ifc_file = "test_building.ifc";
    fs::write(ifc_file, ifc_content).expect("Failed to write IFC file");
    
    // Test IFC processing
    let processing_result = core.process_ifc_file(ifc_file)
        .expect("Failed to process IFC file");
    
    assert!(processing_result.total_entities > 0, "Should have processed entities");
    assert_eq!(processing_result.building_name, "test_building");
    
    // Verify output directory was created
    let output_dir = Path::new("./output/test_building");
    assert!(output_dir.exists(), "Output directory should exist");
    
    let building_data_file = output_dir.join("building_data.yaml");
    assert!(building_data_file.exists(), "Building data file should exist");
    
    cleanup_test_environment(temp_dir);
    }

    #[test]
fn test_core_cli_integration_git_export() {
    let temp_dir = setup_test_environment();
    
    // Test core Git export
    let core = ArxOSCore::new().expect("Failed to create core");
    
    // Test Git export
    let export_result = core.export_to_repository("https://github.com/test/repo")
        .expect("Failed to export to repository");
    
    assert!(export_result.files_exported > 0, "Should have exported files");
    assert!(!export_result.repository_path.is_empty(), "Should have repository path");
    assert!(!export_result.commit_hash.is_empty(), "Should have commit hash");
    
    // Verify repository structure was created
    let repo_dir = Path::new("./repos/repo");
    assert!(repo_dir.exists(), "Repository directory should exist");
    
    let git_dir = repo_dir.join(".git");
    assert!(git_dir.exists(), "Git directory should exist");
    
    let readme_file = repo_dir.join("README.md");
    assert!(readme_file.exists(), "README file should exist");
    
    let building_file = repo_dir.join("building.yaml");
    assert!(building_file.exists(), "Building file should exist");
    
    cleanup_test_environment(temp_dir);
    }

    #[test]
fn test_core_cli_integration_3d_rendering() {
    let temp_dir = setup_test_environment();
    
    // Test core 3D rendering
    let core = ArxOSCore::new().expect("Failed to create core");
    
    // Create test building data
    let building = arxos_core::Building {
        id: "test-building".to_string(),
        name: "Test Building".to_string(),
        path: "/test".to_string(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
        floors: vec![],
        equipment: vec![],
    };
    
    let building_data = arxos_core::BuildingData::new(building);
    
    // Test 3D rendering
    let render_result = core.render_building_3d(&building_data)
        .expect("Failed to render building 3D");
    
    assert!(render_result.floors_rendered >= 0, "Should have rendered floors");
    assert!(!render_result.output_path.is_empty(), "Should have output path");
    
    // Verify render output was created
    let render_dir = Path::new(&render_result.output_path);
    assert!(render_dir.exists(), "Render directory should exist");
    
    let render_file = render_dir.join("render_3d.yaml");
    assert!(render_file.exists(), "Render file should exist");
    
    let ascii_file = render_dir.join("ascii_render.txt");
    assert!(ascii_file.exists(), "ASCII render file should exist");
    
    cleanup_test_environment(temp_dir);
    }

    #[test]
fn test_core_cli_integration_interactive_rendering() {
    let temp_dir = setup_test_environment();
    
    // Test core interactive rendering
    let core = ArxOSCore::new().expect("Failed to create core");
    
    // Create test building data
    let building = arxos_core::Building {
        id: "test-building".to_string(),
        name: "Test Building".to_string(),
        path: "/test".to_string(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
        floors: vec![],
        equipment: vec![],
    };
    
    let building_data = arxos_core::BuildingData::new(building);
    
    // Test interactive rendering
    let interactive_result = core.start_interactive_renderer(&building_data)
        .expect("Failed to start interactive renderer");
    
    assert!(interactive_result.frames_rendered > 0, "Should have rendered frames");
    assert!(interactive_result.session_duration_ms > 0, "Should have session duration");
    assert!(interactive_result.user_interactions >= 0, "Should have user interactions");
    assert!(interactive_result.average_fps > 0.0, "Should have average FPS");
    
    // Verify session was created
    let sessions_dir = Path::new("./sessions");
    assert!(sessions_dir.exists(), "Sessions directory should exist");
    
    cleanup_test_environment(temp_dir);
    }

    #[test]
fn test_core_mobile_integration() {
    let temp_dir = setup_test_environment();
    
    // Test mobile FFI integration
    use arxos_mobile::*;
    
    // Test hello world
    let hello = hello_world();
    assert!(hello.contains("ArxOS Mobile"), "Should return mobile hello");
    
    // Test room creation
    let room = create_room(
        "Mobile Test Room".to_string(),
        1,
        "A".to_string(),
        "classroom".to_string(),
    );
    
    assert_eq!(room.name, "Mobile Test Room");
        assert_eq!(room.room_type, "classroom");
    
    // Test room listing
    let rooms = get_rooms();
    assert!(!rooms.is_empty(), "Should have rooms");
    
    // Test equipment creation
    let equipment = add_equipment(
        "Mobile Test Equipment".to_string(),
        "hvac".to_string(),
        room.id.clone(),
    );
    
    assert_eq!(equipment.name, "Mobile Test Equipment");
        assert_eq!(equipment.equipment_type, "hvac");
    
    // Test equipment listing
    let equipment_list = get_equipment();
    assert!(!equipment_list.is_empty(), "Should have equipment");
    
    // Test command execution
    let result = execute_command("status".to_string());
    assert!(result.success, "Command should succeed");
    assert!(!result.output.is_empty(), "Should have output");
    
    // Test system stats
    let stats = get_system_stats();
    assert!(!stats.is_empty(), "Should have system stats");
    
    cleanup_test_environment(temp_dir);
}
}