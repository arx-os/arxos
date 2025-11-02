//! Unit tests for game command handlers

use arxos::game::{
    GameState, GameMode, GameScenarioLoader, ConstraintSystem, IFCTypeMapper,
    IFCSyncManager, IFCMetadata, GameEquipmentPlacement, ValidationResult, ConstraintViolation,
    GameAction, ConstraintType, ConstraintSeverity,
};
use arxos::core::{Equipment, EquipmentType, Position};
use arxos::spatial::Point3D;
use tempfile::TempDir;
use std::fs::{create_dir_all, write};
use std::path::Path;

/// Helper to create a test PR directory structure
fn setup_test_pr(temp_dir: &TempDir, pr_id: &str) -> Result<std::path::PathBuf, Box<dyn std::error::Error>> {
    let pr_dir = temp_dir.path().join(format!("pr_{}", pr_id));
    create_dir_all(&pr_dir)?;

    // Create metadata.yaml
    let metadata = r#"
pr_id: test_pr_001
building: Test Building
title: Test PR
created_at: "2024-01-01T00:00:00Z"
"#;
    write(pr_dir.join("metadata.yaml"), metadata)?;

    // Create markup.json
    let markup = r#"
{
  "equipment": [
    {
      "id": "equip_1",
      "name": "Test Light Fixture",
      "type": "Electrical",
      "position": {
        "x": 10.0,
        "y": 20.0,
        "z": 3.0
      },
      "confidence": 0.95
    }
  ]
}
"#;
    write(pr_dir.join("markup.json"), markup)?;

    Ok(pr_dir)
}

#[test]
fn test_game_state_creation() {
    let state = GameState::new(GameMode::PRReview);
    assert_eq!(state.mode, GameMode::PRReview);
    assert_eq!(state.score, 0);
    assert_eq!(state.progress, 0.0);
    assert!(state.placements.is_empty());
}

#[test]
fn test_game_state_add_placement() {
    let mut state = GameState::new(GameMode::Planning);
    
    let equipment = Equipment::new(
        "Test Equipment".to_string(),
        "/test/path".to_string(),
        EquipmentType::Electrical,
    );
    
    use arxos::game::types::GameEquipmentPlacement;
    let placement = GameEquipmentPlacement {
        equipment,
        ifc_entity_id: None,
        ifc_entity_type: None,
        ifc_placement_chain: None,
        ifc_original_properties: std::collections::HashMap::new(),
        game_action: GameAction::Placed,
        constraint_validation: ValidationResult::default(),
    };

    state.add_placement(placement);
    assert_eq!(state.placements.len(), 1);
    assert!(state.progress > 0.0);
}

#[test]
fn test_game_state_validation() {
    let mut state = GameState::new(GameMode::PRReview);
    
    let equipment = Equipment::new(
        "Test Equipment".to_string(),
        "/test/path".to_string(),
        EquipmentType::Electrical,
    );
    
    let mut placement = GameEquipmentPlacement {
        equipment,
        ifc_entity_id: None,
        ifc_entity_type: None,
        ifc_placement_chain: None,
        ifc_original_properties: std::collections::HashMap::new(),
        game_action: arxos::game::types::GameAction::Placed,
        constraint_validation: ValidationResult::default(),
    };

    // Add a violation
    placement.constraint_validation.is_valid = false;
    placement.constraint_validation.violations.push(
        ConstraintViolation {
            constraint_id: "test_constraint".to_string(),
            constraint_type: ConstraintType::Spatial,
            severity: ConstraintSeverity::Warning,
            message: "Test violation".to_string(),
            suggestion: None,
        }
    );

    state.add_placement(placement);
    let results = state.validate_all();
    
    assert_eq!(results.len(), 1);
    assert!(!results[0].is_valid);
}

#[test]
fn test_constraint_system_creation() {
    let system = ConstraintSystem::new();
    assert!(system.get_constraints().is_empty());
}

#[test]
fn test_ifc_type_mapper() {
    // Test EquipmentType to IFC mapping
    assert_eq!(
        IFCTypeMapper::map_equipment_type_to_ifc(&EquipmentType::HVAC),
        "IFCAIRTERMINAL"
    );
    assert_eq!(
        IFCTypeMapper::map_equipment_type_to_ifc(&EquipmentType::Electrical),
        "IFCLIGHTFIXTURE"
    );
    assert_eq!(
        IFCTypeMapper::map_equipment_type_to_ifc(&EquipmentType::Plumbing),
        "IFCFLOWTERMINAL"
    );

    // Test reverse mapping
    let eq_type = IFCTypeMapper::map_ifc_to_equipment_type("IFCAIRTERMINAL");
    assert!(matches!(eq_type, EquipmentType::HVAC));

    let eq_type = IFCTypeMapper::map_ifc_to_equipment_type("IFCLIGHTFIXTURE");
    assert!(matches!(eq_type, EquipmentType::Electrical));
}

#[test]
fn test_ifc_type_mapper_validation() {
    assert!(IFCTypeMapper::validate_ifc_entity_type("IFCLIGHTFIXTURE"));
    assert!(IFCTypeMapper::validate_ifc_entity_type("IFCAIRTERMINAL"));
    assert!(!IFCTypeMapper::validate_ifc_entity_type("INVALID_TYPE"));
}

#[test]
fn test_ifc_sync_manager() {
    let mut manager = IFCSyncManager::new();

    let metadata = IFCMetadata {
        entity_id: Some("#123".to_string()),
        entity_type: Some("IFCLIGHTFIXTURE".to_string()),
        placement_chain: vec!["#10".to_string(), "#20".to_string()],
        original_properties: {
            let mut props = std::collections::HashMap::new();
            props.insert("ifc_property".to_string(), "value".to_string());
            props
        },
        coordinate_system: Some("IFC_COORD".to_string()),
    };

    manager.register_equipment("equip_1", metadata);
    
    let retrieved = manager.get_metadata("equip_1").unwrap();
    assert_eq!(retrieved.entity_id, Some("#123".to_string()));
    assert_eq!(retrieved.placement_chain.len(), 2);
}

#[test]
fn test_ifc_sync_manager_synthetic_ids() {
    let mut manager = IFCSyncManager::new();

    // Get metadata for non-existent equipment (creates synthetic ID)
    let metadata1 = manager.get_or_create_metadata("equip_1");
    assert!(metadata1.entity_id.is_some());
    assert!(metadata1.entity_id.unwrap().starts_with("#"));

    // Same equipment should return same metadata
    let metadata2 = manager.get_or_create_metadata("equip_1");
    assert_eq!(metadata1.entity_id, metadata2.entity_id);

    // Different equipment gets different ID
    let metadata3 = manager.get_or_create_metadata("equip_2");
    assert_ne!(metadata1.entity_id, metadata3.entity_id);
}

#[test]
fn test_scenario_loader_from_pr() {
    let temp_dir = tempfile::tempdir().unwrap();
    let pr_dir = setup_test_pr(&temp_dir, "test_001").unwrap();

    let scenario = GameScenarioLoader::load_from_pr("test_001", &pr_dir).unwrap();
    
    assert_eq!(scenario.id, "test_001");
    assert_eq!(scenario.mode, GameMode::PRReview);
    assert!(!scenario.equipment_items.is_empty());
}

#[test]
fn test_constraint_system_validation() {
    use arxos::game::types::GameEquipmentPlacement;
    
    let system = ConstraintSystem::new();
    let mut game_state = GameState::new(GameMode::Planning);

    let equipment = Equipment::new(
        "Test Equipment".to_string(),
        "/test/path".to_string(),
        EquipmentType::Electrical,
    );
    
    let mut placement = GameEquipmentPlacement {
        equipment,
        ifc_entity_id: None,
        ifc_entity_type: None,
        ifc_placement_chain: None,
        ifc_original_properties: std::collections::HashMap::new(),
        game_action: GameAction::Placed,
        constraint_validation: ValidationResult::default(),
    };

    // Validate placement
    let result = system.validate_placement(&placement, &game_state);
    
    // Empty constraint system should return valid result
    assert!(result.is_valid);
    assert!(result.violations.is_empty());
}

