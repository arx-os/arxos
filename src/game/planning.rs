//! Planning Game Mode
//!
//! Interactive planning mode where users can place equipment in 3D space with
//! real-time constraint validation. Plans can be exported as PRs for review.

use std::collections::HashMap;
use std::path::Path;
use crate::game::types::{GameScenario, GameMode, GameEquipmentPlacement, GameAction, ValidationResult};
use crate::game::scenario::GameScenarioLoader;
use crate::game::constraints::ConstraintSystem;
use crate::game::state::GameState;
use crate::core::{Equipment, EquipmentType, Position};
use crate::spatial::Point3D;
use crate::yaml::BuildingData;
use crate::utils::loading::load_building_data;
use log::{info, warn};

/// Planning game for interactive equipment placement
pub struct PlanningGame {
    game_state: GameState,
    constraint_system: ConstraintSystem,
    building_data: BuildingData,
    planning_session_id: String,
    placements_history: Vec<PlacementAction>,
}

/// Action taken during planning session
#[derive(Debug, Clone)]
pub enum PlacementAction {
    Placed {
        equipment_id: String,
        position: Point3D,
        timestamp: std::time::Instant,
    },
    Moved {
        equipment_id: String,
        old_position: Point3D,
        new_position: Point3D,
        timestamp: std::time::Instant,
    },
    Removed {
        equipment_id: String,
        position: Point3D,
        timestamp: std::time::Instant,
    },
}

impl PlanningGame {
    /// Create a new planning game session
    pub fn new(building_name: &str) -> Result<Self, Box<dyn std::error::Error>> {
        info!("Creating planning game for building: {}", building_name);

        // Load building data
        let building_data = load_building_data(building_name)?;

        // Load scenario from building
        let scenario = GameScenarioLoader::load_from_building(building_name)?;

        // Load constraints if available
        let constraints_path = Path::new(".").join(format!("{}-constraints.yaml", building_name));
        let constraint_system = if constraints_path.exists() {
            ConstraintSystem::load_from_file(&constraints_path)?
        } else {
            warn!("No constraints file found, using empty constraint system");
            ConstraintSystem::new()
        };

        // Initialize game state
        let mut game_state = GameState::new(GameMode::Planning);
        game_state.load_scenario(scenario);

        Ok(Self {
            game_state,
            constraint_system,
            building_data,
            planning_session_id: uuid::Uuid::new_v4().to_string(),
            placements_history: Vec::new(),
        })
    }

    /// Place equipment at a specific position
    pub fn place_equipment(
        &mut self,
        equipment_type: EquipmentType,
        name: String,
        position: Point3D,
        room_id: Option<String>,
    ) -> Result<String, Box<dyn std::error::Error>> {
        info!("Placing equipment '{}' at position {:?}", name, position);

        // Create equipment
        let equipment_id = uuid::Uuid::new_v4().to_string();
        let path = format!(
            "/buildings/{}/equipment/{}",
            self.building_data.building.name, equipment_id
        );

        let mut equipment = Equipment::new(name.clone(), path, equipment_type);
        equipment.set_position(Position {
            x: position.x,
            y: position.y,
            z: position.z,
            coordinate_system: "building_local".to_string(),
        });

        if let Some(room) = room_id {
            equipment.set_room(room);
        }

        // Create game placement
        let mut placement = GameEquipmentPlacement {
            equipment,
            ifc_entity_id: None,
            ifc_entity_type: None,
            ifc_placement_chain: None,
            ifc_original_properties: HashMap::new(),
            game_action: GameAction::Placed,
            constraint_validation: ValidationResult::default(),
        };

        // Validate placement
        placement.constraint_validation = self.constraint_system.validate_placement(
            &placement,
            &self.game_state,
        );

        // Add to game state
        let equipment_id_clone = placement.equipment.id.clone();
        self.game_state.add_placement(placement);

        // Record in history
        self.placements_history.push(PlacementAction::Placed {
            equipment_id: equipment_id_clone.clone(),
            position,
            timestamp: std::time::Instant::now(),
        });

        info!("Equipment '{}' placed with ID: {}", name, equipment_id_clone);

        Ok(equipment_id_clone)
    }

    /// Move equipment to a new position
    pub fn move_equipment(
        &mut self,
        equipment_id: &str,
        new_position: Point3D,
    ) -> Result<(), Box<dyn std::error::Error>> {
        info!("Moving equipment '{}' to position {:?}", equipment_id, new_position);

        let placement = self.game_state
            .find_placement_by_id(equipment_id)
            .ok_or_else(|| format!("Equipment not found: {}", equipment_id))?;

        let old_position = Point3D::new(
            placement.equipment.position.x,
            placement.equipment.position.y,
            placement.equipment.position.z,
        );

        // Update placement
        let mut updated_placement = placement.clone();
        updated_placement.equipment.position.x = new_position.x;
        updated_placement.equipment.position.y = new_position.y;
        updated_placement.equipment.position.z = new_position.z;
        updated_placement.game_action = GameAction::Modified;

        // Re-validate
        updated_placement.constraint_validation = self.constraint_system.validate_placement(
            &updated_placement,
            &self.game_state,
        );

        // Find index and update
        if let Some(index) = self.game_state.placements.iter()
            .position(|p| p.equipment.id == equipment_id) {
            self.game_state.update_placement(index, updated_placement)?;
        } else {
            return Err(format!("Equipment not found in placements: {}", equipment_id).into());
        }

        // Record in history
        self.placements_history.push(PlacementAction::Moved {
            equipment_id: equipment_id.to_string(),
            old_position,
            new_position,
            timestamp: std::time::Instant::now(),
        });

        Ok(())
    }

    /// Remove equipment from planning
    pub fn remove_equipment(&mut self, equipment_id: &str) -> Result<(), Box<dyn std::error::Error>> {
        info!("Removing equipment '{}'", equipment_id);

        let placement = self.game_state
            .find_placement_by_id(equipment_id)
            .ok_or_else(|| format!("Equipment not found: {}", equipment_id))?;

        let position = Point3D::new(
            placement.equipment.position.x,
            placement.equipment.position.y,
            placement.equipment.position.z,
        );

        // Remove from game state
        if let Some(index) = self.game_state.placements.iter()
            .position(|p| p.equipment.id == equipment_id) {
            self.game_state.remove_placement(index)?;
        } else {
            return Err(format!("Equipment not found in placements: {}", equipment_id).into());
        }

        // Record in history
        self.placements_history.push(PlacementAction::Removed {
            equipment_id: equipment_id.to_string(),
            position,
            timestamp: std::time::Instant::now(),
        });

        Ok(())
    }

    /// Get validation summary for current plan
    pub fn get_validation_summary(&self) -> PlanningValidationSummary {
        let stats = self.game_state.get_stats();
        
        PlanningValidationSummary {
            total_placements: stats.total_placements,
            valid_placements: stats.valid_placements,
            invalid_placements: stats.total_placements - stats.valid_placements,
            total_violations: stats.violations,
            critical_violations: self.game_state.placements.iter()
                .flat_map(|p| &p.constraint_validation.violations)
                .filter(|v| v.severity == crate::game::types::ConstraintSeverity::Critical)
                .count(),
            warnings: stats.violations,
            score: stats.score,
        }
    }

    /// Export planning session as a PR
    pub fn export_to_pr(
        &self,
        pr_dir: &Path,
        title: Option<String>,
        description: Option<String>,
    ) -> Result<String, Box<dyn std::error::Error>> {
        info!("Exporting planning session to PR directory: {:?}", pr_dir);

        // Create PR directory
        std::fs::create_dir_all(pr_dir)?;

        // Create metadata.yaml
        use serde_json::Value as JsonValue;
        let metadata_obj: HashMap<String, JsonValue> = {
            let mut map = HashMap::new();
            map.insert("pr_id".to_string(), JsonValue::String(self.planning_session_id.clone()));
            map.insert("building".to_string(), JsonValue::String(self.building_data.building.name.clone()));
            map.insert("title".to_string(), JsonValue::String(title.unwrap_or_else(|| "Planning Session".to_string())));
            if let Some(desc) = description {
                map.insert("description".to_string(), JsonValue::String(desc));
            }
            map.insert("created_at".to_string(), JsonValue::String(chrono::Utc::now().to_rfc3339()));
            map.insert("mode".to_string(), JsonValue::String("planning".to_string()));
            map.insert("total_items".to_string(), JsonValue::Number(serde_json::Number::from(self.game_state.placements.len())));
            map.insert("session_stats".to_string(), serde_json::json!({
                "score": self.game_state.score,
                "progress": self.game_state.progress,
                "constraints_validated": self.game_state.constraints_validated,
            }));
            map
        };
        let metadata = serde_yaml::to_string(&metadata_obj)?;
        std::fs::write(pr_dir.join("metadata.yaml"), metadata)?;

        // Create markup.json with all placements
        let markup = serde_json::json!({
            "equipment": self.game_state.placements.iter().map(|p| {
                serde_json::json!({
                    "id": p.equipment.id,
                    "name": p.equipment.name,
                    "type": format!("{:?}", p.equipment.equipment_type),
                    "position": {
                        "x": p.equipment.position.x,
                        "y": p.equipment.position.y,
                        "z": p.equipment.position.z,
                    },
                    "room_id": p.equipment.room_id,
                    "properties": p.equipment.properties,
                    "validation": {
                        "is_valid": p.constraint_validation.is_valid,
                        "violations": p.constraint_validation.violations.iter().map(|v| {
                            serde_json::json!({
                                "constraint_id": v.constraint_id,
                                "type": format!("{:?}", v.constraint_type),
                                "severity": format!("{:?}", v.severity),
                                "message": v.message,
                                "suggestion": v.suggestion,
                            })
                        }).collect::<Vec<_>>(),
                        "warnings": p.constraint_validation.warnings,
                    }
                })
            }).collect::<Vec<_>>()
        });
        std::fs::write(pr_dir.join("markup.json"), serde_json::to_string_pretty(&markup)?)?;

        // Create README.md
        let summary = self.get_validation_summary();
        let readme = format!(
            "# Planning Session PR

## Summary

**Session ID**: {}
**Building**: {}
**Created**: {}

### Statistics
- Total Placements: {}
- Valid Placements: {}
- Invalid Placements: {}
- Total Violations: {}
- Critical Violations: {}
- Score: {}

## Equipment Items

{}",
            self.planning_session_id,
            self.building_data.building.name,
            chrono::Utc::now().to_rfc3339(),
            summary.total_placements,
            summary.valid_placements,
            summary.invalid_placements,
            summary.total_violations,
            summary.critical_violations,
            summary.score,
            self.game_state.placements.iter()
                .map(|p| format!(
                    "- **{}** ({:?}) at ({:.2}, {:.2}, {:.2}) - {}\n",
                    p.equipment.name,
                    p.equipment.equipment_type,
                    p.equipment.position.x,
                    p.equipment.position.y,
                    p.equipment.position.z,
                    if p.constraint_validation.is_valid { "✅ Valid" } else { "❌ Invalid" }
                ))
                .collect::<String>()
        );
        std::fs::write(pr_dir.join("README.md"), readme)?;

        info!("PR exported successfully to: {:?}", pr_dir);
        Ok(self.planning_session_id.clone())
    }

    /// Get game state for rendering
    pub fn game_state(&self) -> &GameState {
        &self.game_state
    }

    /// Get mutable game state
    pub fn game_state_mut(&mut self) -> &mut GameState {
        &mut self.game_state
    }

    /// Get planning session ID
    pub fn session_id(&self) -> &str {
        &self.planning_session_id
    }

    /// Get placement history
    pub fn placement_history(&self) -> &[PlacementAction] {
        &self.placements_history
    }

    /// Validate all placements and update state
    pub fn validate_all(&mut self) {
        self.game_state.validate_all();
    }
}

/// Validation summary for planning session
#[derive(Debug, Clone)]
pub struct PlanningValidationSummary {
    pub total_placements: usize,
    pub valid_placements: usize,
    pub invalid_placements: usize,
    pub total_violations: usize,
    pub critical_violations: usize,
    pub warnings: usize,
    pub score: u32,
}

