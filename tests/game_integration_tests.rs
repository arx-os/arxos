//! Integration tests for game workflows
//!
//! These tests verify end-to-end game workflows including PR review,
//! planning, IFC export/import, and constraint validation.

use arxos::game::{
    GameScenarioLoader, PRReviewGame, PlanningGame, IFCGameExporter,
    ConstraintSystem, IFCSyncManager, GameState, GameMode, GameEquipmentPlacement,
    GameAction, ValidationResult, ConstraintType, ConstraintSeverity,
};
use arxos::core::{Equipment, EquipmentType, Position};
use arxos::spatial::Point3D;
use tempfile::TempDir;
use std::fs::{create_dir_all, write, read_to_string};
use std::path::Path;

/// Setup test building with YAML file
fn setup_test_building(temp_dir: &TempDir, building_name: &str) -> Result<std::path::PathBuf, Box<dyn std::error::Error>> {
    let building_dir = temp_dir.path().join(building_name);
    create_dir_all(&building_dir)?;

    let building_yaml = r#"
building:
  id: test_building
  name: Test Building
  description: Test building for integration tests
  created_at: "2024-01-01T00:00:00Z"
  updated_at: "2024-01-01T00:00:00Z"
  version: "1.0.0"
metadata:
  version: "1.0.0"
  parser_version: "1.0.0"
  total_entities: 0
  spatial_entities: 0
  coordinate_system: "WGS84"
  units: "meters"
  tags: []
floors:
  - id: floor_1
    name: Ground Floor
    level: 0
    elevation: 0.0
    rooms:
      - id: room_1
        name: Test Room
        room_type: Office
        area: 100.0
        volume: 300.0
        position:
          x: 10.0
          y: 10.0
          z: 0.0
        bounding_box:
          min:
            x: 5.0
            y: 5.0
            z: 0.0
          max:
            x: 15.0
            y: 15.0
            z: 3.0
        equipment: []
        properties: {}
    equipment: []
"#;
    write(building_dir.join("building.yaml"), building_yaml)?;
    
    Ok(building_dir)
}

/// Setup test PR directory
fn setup_test_pr(temp_dir: &TempDir, pr_id: &str) -> Result<std::path::PathBuf, Box<dyn std::error::Error>> {
    let pr_dir = temp_dir.path().join(format!("prs/pr_{}", pr_id));
    create_dir_all(&pr_dir)?;

    let metadata = format!(
        r#"
pr_id: {}
building: Test Building
title: Test PR
description: Integration test PR
created_at: "2024-01-01T00:00:00Z"
mode: review
total_items: 2
"#,
        pr_id
    );
    write(pr_dir.join("metadata.yaml"), metadata)?;

    let markup = r#"
{
  "equipment": [
    {
      "id": "equip_1",
      "name": "Light Fixture 1",
      "type": "Electrical",
      "position": {
        "x": 10.0,
        "y": 20.0,
        "z": 3.0
      },
      "confidence": 0.95,
      "note": "Ceiling mounted"
    },
    {
      "id": "equip_2",
      "name": "HVAC Diffuser",
      "type": "HVAC",
      "position": {
        "x": 12.0,
        "y": 22.0,
        "z": 3.0
      },
      "confidence": 0.90
    }
  ]
}
"#;
    write(pr_dir.join("markup.json"), markup)?;

    Ok(pr_dir)
}

#[test]
fn test_pr_review_workflow() {
    let temp_dir = tempfile::tempdir().unwrap();
    let pr_dir = setup_test_pr(&temp_dir, "test_review_001").unwrap();
    let building_dir = setup_test_building(&temp_dir, "Test Building").unwrap();

    // Change to building directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(&building_dir).unwrap();

    // Create PR review game
    let mut review_game = PRReviewGame::new("test_review_001", &pr_dir).unwrap();

    // Validate PR
    let results = review_game.validate_pr();
    let summary = review_game.get_validation_summary();

    assert_eq!(summary.total_items, 2);
    assert!(summary.total_items >= summary.valid_items);

    // Restore directory
    std::env::set_current_dir(&original_dir).unwrap();
}

#[test]
fn test_planning_workflow() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_dir = setup_test_building(&temp_dir, "Test Building").unwrap();

    // Change to building directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(&building_dir).unwrap();

    // Create planning game
    let mut planning_game = PlanningGame::new("Test Building").unwrap();

    // Place equipment
    let equip_id = planning_game.place_equipment(
        EquipmentType::Electrical,
        "Test Light".to_string(),
        Point3D::new(10.0, 20.0, 3.0),
        Some("room_1".to_string()),
    ).unwrap();

    assert!(!equip_id.is_empty());

    // Get validation summary
    let summary = planning_game.get_validation_summary();
    assert_eq!(summary.total_placements, 1);

    // Export to PR
    let pr_dir = temp_dir.path().join("exported_pr");
    planning_game.export_to_pr(
        &pr_dir,
        Some("Test Planning Session".to_string()),
        Some("Integration test planning".to_string()),
    ).unwrap();

    // Verify PR files exist
    assert!(pr_dir.join("metadata.yaml").exists());
    assert!(pr_dir.join("markup.json").exists());
    assert!(pr_dir.join("README.md").exists());

    // Restore directory
    std::env::set_current_dir(&original_dir).unwrap();
}

#[test]
fn test_ifc_round_trip() {
    let temp_dir = tempfile::tempdir().unwrap();
    let building_dir = setup_test_building(&temp_dir, "Test Building").unwrap();

    // Change to building directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(&building_dir).unwrap();

    // Create planning game and place equipment
    let mut planning_game = PlanningGame::new("Test Building").unwrap();

    let equip_id = planning_game.place_equipment(
        EquipmentType::Electrical,
        "Test Light".to_string(),
        Point3D::new(10.0, 20.0, 3.0),
        None,
    ).unwrap();

    // Export to IFC
    let ifc_path = temp_dir.path().join("test_game_export.ifc");
    let game_state = planning_game.game_state();
    
    let mut exporter = IFCGameExporter::new();
    exporter.export_game_to_ifc(game_state, &ifc_path).unwrap();

    // Verify IFC file exists
    assert!(ifc_path.exists());
    
    // Verify IFC file has content
    let ifc_content = read_to_string(&ifc_path).unwrap();
    assert!(ifc_content.contains("ISO-10303-21"));
    assert!(ifc_content.contains("DATA"));

    // Restore directory
    std::env::set_current_dir(&original_dir).unwrap();
}

#[test]
fn test_constraint_validation_workflow() {
    
    let temp_dir = tempfile::tempdir().unwrap();
    
    // Create constraints file
    let constraints_yaml = r#"
constraints:
  structural:
    - type: wall_support
      floor: 0
      valid_areas:
        - bbox:
            min:
              x: 5.0
              y: 5.0
              z: 0.0
            max:
              x: 15.0
              y: 15.0
              z: 3.0
          notes: "Wall supported area"
  spatial:
    - type: clearance
      min_clearance: 0.5
      equipment_type: "Electrical"
"#;
    
    let constraints_path = temp_dir.path().join("Test Building-constraints.yaml");
    write(&constraints_path, constraints_yaml).unwrap();

    // Load constraint system
    let constraint_system = ConstraintSystem::load_from_file(&constraints_path).unwrap();
    
    // Create game state with equipment
    let mut game_state = GameState::new(GameMode::Planning);

    let mut equipment = Equipment::new(
        "Test Equipment".to_string(),
        "/test/path".to_string(),
        EquipmentType::Electrical,
    );
    equipment.set_position(Position {
        x: 10.0,
        y: 10.0,
        z: 2.0,
        coordinate_system: "building_local".to_string(),
    });

    let placement = GameEquipmentPlacement {
        equipment,
        ifc_entity_id: None,
        ifc_entity_type: None,
        ifc_placement_chain: None,
        ifc_original_properties: std::collections::HashMap::new(),
        game_action: GameAction::Placed,
        constraint_validation: ValidationResult::default(),
    };

    // Validate
    let result = constraint_system.validate_placement(&placement, &game_state);
    
    // Equipment is in valid structural area, so should be valid
    assert!(result.is_valid || result.violations.iter().any(|v| {
        v.severity == ConstraintSeverity::Warning
    }));
}

#[test]
fn test_scenario_loading_workflow() {
    let temp_dir = tempfile::tempdir().unwrap();
    let pr_dir = setup_test_pr(&temp_dir, "scenario_test").unwrap();
    let building_dir = setup_test_building(&temp_dir, "Test Building").unwrap();

    // Change to building directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(&building_dir).unwrap();

    // Load scenario
    let scenario = GameScenarioLoader::load_from_pr("scenario_test", &pr_dir).unwrap();

    assert_eq!(scenario.id, "scenario_test");
    assert_eq!(scenario.mode, GameMode::PRReview);
    assert_eq!(scenario.equipment_items.len(), 2);

    // Verify equipment loaded correctly
    let first_equip = &scenario.equipment_items[0];
    assert_eq!(first_equip.equipment.name, "Light Fixture 1");
    assert_eq!(first_equip.equipment.position.x, 10.0);

    // Restore directory
    std::env::set_current_dir(&original_dir).unwrap();
}

