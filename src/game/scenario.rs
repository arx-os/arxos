//! Scenario loading and management for game system

use crate::game::types::{
    Constraint, GameAction, GameEquipmentPlacement, GameMode, GameScenario, ValidationResult,
};
use crate::utils::loading::load_building_data;
use log::{info, warn};
use std::collections::HashMap;
use std::path::Path;

/// Loads game scenarios from various sources
pub struct GameScenarioLoader;

impl GameScenarioLoader {
    /// Load scenario from a PR
    pub fn load_from_pr(
        pr_id: &str,
        pr_dir: &Path,
    ) -> Result<GameScenario, Box<dyn std::error::Error>> {
        info!("Loading game scenario from PR: {}", pr_id);

        // Load PR metadata
        let metadata_path = pr_dir.join("metadata.yaml");
        let metadata: HashMap<String, serde_yaml::Value> = if metadata_path.exists() {
            let content = std::fs::read_to_string(&metadata_path)?;
            serde_yaml::from_str(&content)?
        } else {
            warn!("No metadata.yaml found in PR, using defaults");
            HashMap::new()
        };

        // Load markup.json (AR scan data)
        let markup_path = pr_dir.join("markup.json");
        let equipment_items = if markup_path.exists() {
            Self::load_equipment_from_markup(&markup_path)?
        } else {
            warn!("No markup.json found in PR");
            Vec::new()
        };

        // Extract building name
        let building = metadata
            .get("building")
            .and_then(|v| v.as_str())
            .unwrap_or("Unknown Building")
            .to_string();

        // Extract objective from PR metadata
        let objective = format!(
            "Review PR {}: {} equipment items",
            pr_id,
            equipment_items.len()
        );

        // Load constraints if available
        let constraints_path = pr_dir.join("constraints.yaml");
        let constraints = if constraints_path.exists() {
            Self::load_constraints_from_file(&constraints_path)?
        } else {
            Vec::new()
        };

        Ok(GameScenario {
            id: pr_id.to_string(),
            mode: GameMode::PRReview,
            building,
            objective,
            constraints,
            equipment_items,
            validation_rules: Vec::new(), // Can be populated with custom validation rules
        })
    }

    /// Load equipment items from markup.json
    fn load_equipment_from_markup(
        markup_path: &Path,
    ) -> Result<Vec<GameEquipmentPlacement>, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(markup_path)?;
        let markup: serde_json::Value = serde_json::from_str(&content)?;

        let mut placements = Vec::new();

        if let Some(equipment_array) = markup.get("equipment").and_then(|e| e.as_array()) {
            for eq_data in equipment_array {
                if let Ok(placement) = Self::parse_equipment_from_markup(eq_data) {
                    placements.push(placement);
                }
            }
        }

        Ok(placements)
    }

    /// Parse single equipment item from markup JSON
    fn parse_equipment_from_markup(
        eq_data: &serde_json::Value,
    ) -> Result<GameEquipmentPlacement, Box<dyn std::error::Error>> {
        use crate::core::{Equipment, EquipmentStatus, EquipmentType, Position};
        use std::collections::HashMap;

        let name = eq_data
            .get("name")
            .and_then(|v| v.as_str())
            .unwrap_or("Unknown")
            .to_string();

        let eq_type_str = eq_data
            .get("type")
            .and_then(|v| v.as_str())
            .unwrap_or("Other");

        let equipment_type = match eq_type_str {
            "HVAC" => EquipmentType::HVAC,
            "Electrical" => EquipmentType::Electrical,
            "AV" => EquipmentType::AV,
            "Plumbing" => EquipmentType::Plumbing,
            "Network" => EquipmentType::Network,
            _ => EquipmentType::Other(eq_type_str.to_string()),
        };

        // Parse position
        let pos_data = eq_data
            .get("position")
            .ok_or("Missing position in equipment data")?;

        let x = pos_data.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
        let y = pos_data.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
        let z = pos_data.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0);

        // Parse confidence
        let confidence = eq_data
            .get("confidence")
            .and_then(|v| v.as_f64())
            .unwrap_or(0.0);

        // Create equipment ID first to avoid borrow issues
        let equipment_id = eq_data
            .get("id")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .unwrap_or_else(|| format!("pending_{}", name));

        // Create equipment
        let equipment = Equipment {
            id: equipment_id,
            name: name.clone(),
            path: format!("/equipment/{}", name.to_lowercase().replace(" ", "-")),
            address: None,
            equipment_type,
            position: Position {
                x,
                y,
                z,
                coordinate_system: "world".to_string(),
            },
            properties: {
                let mut props = HashMap::new();
                props.insert("confidence".to_string(), confidence.to_string());
                if let Some(note) = eq_data.get("note").and_then(|v| v.as_str()) {
                    props.insert("note".to_string(), note.to_string());
                }
                props
            },
            status: EquipmentStatus::Active,
            health_status: None,
            room_id: None,
            sensor_mappings: None,
        };

        Ok(GameEquipmentPlacement {
            equipment,
            ifc_entity_id: None,
            ifc_entity_type: None,
            ifc_placement_chain: None,
            ifc_original_properties: HashMap::new(),
            game_action: GameAction::AddedFromPR,
            constraint_validation: ValidationResult::default(),
        })
    }

    /// Load constraints from YAML file
    fn load_constraints_from_file(
        constraints_path: &Path,
    ) -> Result<Vec<Constraint>, Box<dyn std::error::Error>> {
        use crate::game::types::{Constraint, ConstraintSeverity, ConstraintType};

        let content = std::fs::read_to_string(constraints_path)?;
        let data: serde_yaml::Value = serde_yaml::from_str(&content)?;

        let mut constraints = Vec::new();

        if let Some(constraints_obj) = data.get("constraints") {
            // Load structural constraints
            if let Some(structural) = constraints_obj
                .get("structural")
                .and_then(|s| s.as_sequence())
            {
                for item in structural {
                    if item.get("type").and_then(|t| t.as_str()).is_some() {
                        let constraint = Constraint {
                            id: format!("structural_{}", constraints.len()),
                            constraint_type: ConstraintType::Structural,
                            description: item
                                .get("notes")
                                .and_then(|n| n.as_str())
                                .unwrap_or("Structural constraint")
                                .to_string(),
                            severity: ConstraintSeverity::Error,
                        };
                        constraints.push(constraint);
                    }
                }
            }

            // Load code constraints
            if let Some(code) = constraints_obj.get("code").and_then(|c| c.as_sequence()) {
                for item in code {
                    if let Some(constraint_type) = item.get("type").and_then(|t| t.as_str()) {
                        let constraint = Constraint {
                            id: format!("code_{}", constraints.len()),
                            constraint_type: ConstraintType::Code,
                            description: format!("Code requirement: {}", constraint_type),
                            severity: ConstraintSeverity::Error,
                        };
                        constraints.push(constraint);
                    }
                }
            }

            // Load spatial constraints
            if let Some(spatial) = constraints_obj.get("spatial").and_then(|s| s.as_sequence()) {
                for _item in spatial {
                    let constraint = Constraint {
                        id: format!("spatial_{}", constraints.len()),
                        constraint_type: ConstraintType::Spatial,
                        description: "Spatial constraint".to_string(),
                        severity: ConstraintSeverity::Warning,
                    };
                    constraints.push(constraint);
                }
            }
        }

        Ok(constraints)
    }

    /// Load scenario from building data for planning mode
    pub fn load_from_building(
        building_name: &str,
    ) -> Result<GameScenario, Box<dyn std::error::Error>> {
        info!("Loading planning scenario from building: {}", building_name);

        let building_data = load_building_data(building_name)?;

        // Convert building equipment to game placements
        let mut equipment_items = Vec::new();
        for floor in &building_data.floors {
            for equipment_data in &floor.equipment {
                use crate::core::Equipment;

                // equipment_data is already core::Equipment, so we can use it directly
                // Just clone it and ensure all fields are set
                let equipment = Equipment {
                    id: equipment_data.id.clone(),
                    name: equipment_data.name.clone(),
                    path: equipment_data.path.clone(),
                    address: equipment_data.address.clone(),
                    equipment_type: equipment_data.equipment_type.clone(),
                    position: equipment_data.position.clone(),
                    properties: equipment_data.properties.clone(),
                    status: equipment_data.status.clone(),
                    health_status: equipment_data.health_status.clone(),
                    room_id: equipment_data.room_id.clone(),
                    sensor_mappings: equipment_data.sensor_mappings.clone(),
                };

                let placement = GameEquipmentPlacement {
                    equipment,
                    ifc_entity_id: equipment_data.properties.get("ifc_entity_id").cloned(),
                    ifc_entity_type: equipment_data.properties.get("ifc_entity_type").cloned(),
                    ifc_placement_chain: None,
                    ifc_original_properties: equipment_data.properties.clone(),
                    game_action: GameAction::Loaded,
                    constraint_validation: ValidationResult::default(),
                };

                equipment_items.push(placement);
            }
        }

        Ok(GameScenario {
            id: format!("planning_{}", building_name),
            mode: GameMode::Planning,
            building: building_data.building.name.clone(),
            objective: format!(
                "Plan equipment placement for {}",
                building_data.building.name
            ),
            constraints: Vec::new(), // Will be loaded separately
            equipment_items,
            validation_rules: Vec::new(),
        })
    }

    /// Create learning scenario from approved PR
    pub fn create_learning_scenario(
        pr_id: &str,
        pr_dir: &Path,
    ) -> Result<GameScenario, Box<dyn std::error::Error>> {
        let mut scenario = Self::load_from_pr(pr_id, pr_dir)?;
        scenario.mode = GameMode::Learning;
        scenario.objective = format!("Learn from PR {}: {}", pr_id, scenario.objective);
        Ok(scenario)
    }
}
