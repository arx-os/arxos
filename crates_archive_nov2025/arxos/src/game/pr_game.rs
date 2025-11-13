//! PR Review Game Mode
//!
//! Interactive game-based PR review system that allows power users to review
//! contractor PRs with 3D visualization and constraint validation.

use crate::game::constraints::ConstraintSystem;
use crate::game::scenario::GameScenarioLoader;
use crate::game::state::GameState;
use crate::game::types::{
    ConstraintViolation, GameEquipmentPlacement, GameMode, GameScenario, ValidationResult,
};
use crate::utils::loading::load_building_data;
use crate::yaml::BuildingData;
use log::{info, warn};
use std::path::Path;

/// PR Review Game handles the interactive review of contractor PRs
pub struct PRReviewGame {
    scenario: GameScenario,
    game_state: GameState,
    constraint_system: ConstraintSystem,
    building_data: BuildingData,
}

/// PR review decision
#[derive(Debug, Clone)]
pub enum ReviewDecision {
    /// Approve the PR
    Approve { comment: Option<String> },
    /// Reject the PR
    Reject { reason: String },
    /// Request changes
    RequestChanges {
        comment: String,
        items_to_fix: Vec<String>,
    },
}

impl PRReviewGame {
    /// Create a new PR review game from a PR
    pub fn new(pr_id: &str, pr_dir: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        info!("Creating PR review game for: {}", pr_id);

        // Load scenario from PR
        let scenario = GameScenarioLoader::load_from_pr(pr_id, pr_dir)?;

        // Load building data for context
        let building_data = load_building_data(&scenario.building)?;

        // Load constraints if available
        let constraints_path = pr_dir.join("constraints.yaml");
        let constraint_system = if constraints_path.exists() {
            ConstraintSystem::load_from_file(&constraints_path)?
        } else {
            // Try to load from building directory
            let building_constraints =
                Path::new(".").join(format!("{}-constraints.yaml", scenario.building));
            if building_constraints.exists() {
                ConstraintSystem::load_from_file(&building_constraints)?
            } else {
                warn!("No constraints file found, using empty constraint system");
                ConstraintSystem::new()
            }
        };

        // Initialize game state
        let mut game_state = GameState::new(GameMode::PRReview);
        game_state.load_scenario(scenario.clone());

        // Load equipment items from PR into game state
        for placement in &scenario.equipment_items {
            game_state.add_placement(placement.clone());
        }

        Ok(Self {
            scenario,
            game_state,
            constraint_system,
            building_data,
        })
    }

    /// Validate all equipment in the PR
    pub fn validate_pr(&mut self) -> Vec<ValidationResult> {
        info!("Validating PR equipment items");

        let mut results = Vec::new();

        // Validate each equipment placement
        for placement in &self.scenario.equipment_items {
            // Validate against constraints
            let validation_result = self
                .constraint_system
                .validate_placement(placement, &self.game_state);

            // Check for conflicts with existing building data
            let conflicts = self.check_existing_conflicts(placement);

            // Combine validation results
            let mut combined_result = validation_result.clone();

            if !conflicts.is_empty() {
                combined_result.is_valid = false;
                for conflict in conflicts {
                    combined_result.violations.push(conflict);
                }
            }

            // Update placement with validation result
            if let Some(game_placement) = self
                .game_state
                .find_placement_by_id_mut(&placement.equipment.id)
            {
                game_placement.constraint_validation = combined_result.clone();
            }

            results.push(combined_result);
        }

        // Update game state statistics
        self.game_state.validate_all();

        results
    }

    /// Check for conflicts with existing building equipment
    fn check_existing_conflicts(
        &self,
        placement: &GameEquipmentPlacement,
    ) -> Vec<ConstraintViolation> {
        let mut conflicts = Vec::new();

        let pos = &placement.equipment.position;
        let placement_pos = crate::spatial::Point3D::new(pos.x, pos.y, pos.z);

        // Check against existing equipment in building
        for floor in &self.building_data.floors {
            for existing_eq in &floor.equipment {
                let existing_pos = crate::spatial::Point3D::new(
                    existing_eq.position.x,
                    existing_eq.position.y,
                    existing_eq.position.z,
                );

                // Check if same equipment ID (potential duplicate)
                if existing_eq.id == placement.equipment.id
                    || existing_eq.name == placement.equipment.name
                {
                    conflicts.push(ConstraintViolation {
                        constraint_id: "duplicate_check".to_string(),
                        constraint_type: crate::game::types::ConstraintType::Spatial,
                        severity: crate::game::types::ConstraintSeverity::Error,
                        message: format!(
                            "Equipment ID '{}' already exists in building at position ({:.2}, {:.2}, {:.2})",
                            placement.equipment.id,
                            existing_pos.x, existing_pos.y, existing_pos.z
                        ),
                        suggestion: Some("Use unique equipment ID or verify this is an update".to_string()),
                    });
                }

                // Check proximity conflicts
                let distance = placement_pos.distance_to(&existing_pos);
                if distance < 0.5 {
                    // Equipment too close together
                    conflicts.push(ConstraintViolation {
                        constraint_id: "proximity_check".to_string(),
                        constraint_type: crate::game::types::ConstraintType::Spatial,
                        severity: crate::game::types::ConstraintSeverity::Warning,
                        message: format!(
                            "Equipment '{}' is very close to existing equipment '{}' (distance: {:.2}m)",
                            placement.equipment.name,
                            existing_eq.name,
                            distance
                        ),
                        suggestion: Some("Verify spacing is adequate for maintenance access".to_string()),
                    });
                }
            }
        }

        conflicts
    }

    /// Get validation summary for the PR
    pub fn get_validation_summary(&self) -> PRValidationSummary {
        let total_items = self.scenario.equipment_items.len();
        let valid_count = self
            .game_state
            .placements
            .iter()
            .filter(|p| p.constraint_validation.is_valid)
            .count();
        let violation_count = self
            .game_state
            .placements
            .iter()
            .map(|p| p.constraint_validation.violations.len())
            .sum();

        PRValidationSummary {
            total_items,
            valid_items: valid_count,
            items_with_violations: total_items - valid_count,
            total_violations: violation_count,
            critical_violations: self
                .game_state
                .placements
                .iter()
                .flat_map(|p| &p.constraint_validation.violations)
                .filter(|v| v.severity == crate::game::types::ConstraintSeverity::Critical)
                .count(),
            warnings: self
                .game_state
                .placements
                .iter()
                .flat_map(|p| &p.constraint_validation.warnings)
                .count(),
        }
    }

    /// Get game state for rendering
    pub fn game_state(&self) -> &GameState {
        &self.game_state
    }

    /// Get mutable game state
    pub fn game_state_mut(&mut self) -> &mut GameState {
        &mut self.game_state
    }

    /// Get scenario
    pub fn scenario(&self) -> &GameScenario {
        &self.scenario
    }

    /// Make a review decision on the PR
    pub fn make_decision(
        &self,
        decision: ReviewDecision,
    ) -> Result<ReviewComment, Box<dyn std::error::Error>> {
        let summary = self.get_validation_summary();

        match decision {
            ReviewDecision::Approve { comment } => {
                if summary.critical_violations > 0 {
                    return Err("Cannot approve PR with critical violations".into());
                }

                Ok(ReviewComment {
                    decision: "approved".to_string(),
                    comment: comment.unwrap_or_else(|| {
                        format!(
                            "PR approved. {} items validated, {} violations addressed.",
                            summary.valid_items, summary.total_violations
                        )
                    }),
                    items_approved: summary.total_items,
                })
            }
            ReviewDecision::Reject { reason } => Ok(ReviewComment {
                decision: "rejected".to_string(),
                comment: format!("PR rejected: {}", reason),
                items_approved: 0,
            }),
            ReviewDecision::RequestChanges {
                comment,
                items_to_fix,
            } => Ok(ReviewComment {
                decision: "changes_requested".to_string(),
                comment: format!("{} Items to fix: {}", comment, items_to_fix.join(", ")),
                items_approved: summary.valid_items,
            }),
        }
    }
}

/// Validation summary for PR review
#[derive(Debug, Clone)]
pub struct PRValidationSummary {
    pub total_items: usize,
    pub valid_items: usize,
    pub items_with_violations: usize,
    pub total_violations: usize,
    pub critical_violations: usize,
    pub warnings: usize,
}

/// Review comment to be added to PR
#[derive(Debug, Clone)]
pub struct ReviewComment {
    pub decision: String,
    pub comment: String,
    pub items_approved: usize,
}
