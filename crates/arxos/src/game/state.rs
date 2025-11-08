//! Game state management

use crate::game::types::{
    GameEquipmentPlacement, GameMode, GameObjective, GameScenario, ValidationResult,
};
use crate::spatial::Point3D;
use std::collections::HashMap;

/// Current state of the game session
#[derive(Debug, Clone)]
pub struct GameState {
    /// Current game mode
    pub mode: GameMode,
    /// Active scenario
    pub scenario: Option<GameScenario>,
    /// Current objective
    pub objective: Option<GameObjective>,
    /// All equipment placements in this game session
    pub placements: Vec<GameEquipmentPlacement>,
    /// Current score
    pub score: u32,
    /// Number of constraints validated successfully
    pub constraints_validated: usize,
    /// Number of violations found
    pub violations_found: usize,
    /// Progress percentage (0.0 to 1.0)
    pub progress: f32,
    /// Session metadata
    pub session_metadata: HashMap<String, String>,
}

impl GameState {
    /// Create a new game state
    pub fn new(mode: GameMode) -> Self {
        Self {
            mode,
            scenario: None,
            objective: None,
            placements: Vec::new(),
            score: 0,
            constraints_validated: 0,
            violations_found: 0,
            progress: 0.0,
            session_metadata: HashMap::new(),
        }
    }

    /// Load a scenario into the game state
    pub fn load_scenario(&mut self, scenario: GameScenario) {
        self.scenario = Some(scenario.clone());
        if let Some(objective) = scenario.validation_rules.first() {
            self.objective = Some(GameObjective {
                id: objective.id.clone(),
                title: objective.name.clone(),
                description: objective.description.clone(),
                criteria: vec![],
            });
        }
    }

    /// Add an equipment placement
    pub fn add_placement(&mut self, placement: GameEquipmentPlacement) {
        self.placements.push(placement);
        self.update_progress();
    }

    /// Update equipment placement
    pub fn update_placement(
        &mut self,
        index: usize,
        placement: GameEquipmentPlacement,
    ) -> Result<(), String> {
        if index >= self.placements.len() {
            return Err(format!("Invalid placement index: {}", index));
        }
        self.placements[index] = placement;
        self.update_progress();
        Ok(())
    }

    /// Remove equipment placement
    pub fn remove_placement(&mut self, index: usize) -> Result<GameEquipmentPlacement, String> {
        if index >= self.placements.len() {
            return Err(format!("Invalid placement index: {}", index));
        }
        let placement = self.placements.remove(index);
        self.update_progress();
        Ok(placement)
    }

    /// Find placement by equipment ID
    pub fn find_placement_by_id(&self, equipment_id: &str) -> Option<&GameEquipmentPlacement> {
        self.placements
            .iter()
            .find(|p| p.equipment.id == equipment_id)
    }

    /// Find placement by equipment ID (mutable)
    pub fn find_placement_by_id_mut(
        &mut self,
        equipment_id: &str,
    ) -> Option<&mut GameEquipmentPlacement> {
        self.placements
            .iter_mut()
            .find(|p| p.equipment.id == equipment_id)
    }

    /// Validate all placements and update state
    pub fn validate_all(&mut self) -> Vec<ValidationResult> {
        let mut results = Vec::new();

        for placement in &self.placements {
            let result = &placement.constraint_validation;

            if result.is_valid {
                self.constraints_validated += 1;
            } else {
                self.violations_found += result.violations.len();
            }

            results.push(result.clone());
        }

        self.update_score();
        self.update_progress();
        results
    }

    /// Update score based on current state
    fn update_score(&mut self) {
        let base_score = 100;
        let placement_bonus = self.placements.len() * 10;
        let validation_bonus = self.constraints_validated * 5;
        let violation_penalty = self.violations_found * 10;

        self.score = ((base_score + placement_bonus + validation_bonus) as i32)
            .saturating_sub(violation_penalty as i32)
            .max(0) as u32;
    }

    /// Update progress percentage
    fn update_progress(&mut self) {
        if let Some(ref scenario) = self.scenario {
            let total_items = scenario.equipment_items.len();
            if total_items > 0 {
                let completed = self.placements.len().min(total_items);
                self.progress = completed as f32 / total_items as f32;
            } else {
                self.progress = if self.placements.is_empty() { 0.0 } else { 1.0 };
            }
        } else {
            self.progress = 0.0;
        }
    }

    /// Get current camera position (for 3D navigation)
    pub fn camera_position(&self) -> Point3D {
        // Default camera position - will be set by interactive renderer
        Point3D::new(0.0, 0.0, 0.0)
    }

    /// Check if objective is completed
    pub fn is_objective_completed(&self) -> bool {
        if let Some(ref objective) = self.objective {
            objective
                .criteria
                .iter()
                .filter(|c| c.is_required)
                .all(|c| c.is_completed)
        } else {
            false
        }
    }

    /// Mark criterion as completed
    pub fn complete_criterion(&mut self, criterion_id: &str) -> Result<(), String> {
        if let Some(ref mut objective) = self.objective {
            if let Some(criterion) = objective.criteria.iter_mut().find(|c| c.id == criterion_id) {
                criterion.is_completed = true;
                self.update_progress();
                return Ok(());
            }
        }
        Err(format!("Criterion not found: {}", criterion_id))
    }

    /// Get session statistics
    pub fn get_stats(&self) -> GameStats {
        GameStats {
            total_placements: self.placements.len(),
            valid_placements: self
                .placements
                .iter()
                .filter(|p| p.constraint_validation.is_valid)
                .count(),
            violations: self.violations_found,
            score: self.score,
            progress: self.progress,
        }
    }
}

/// Game session statistics
#[derive(Debug, Clone)]
pub struct GameStats {
    pub total_placements: usize,
    pub valid_placements: usize,
    pub violations: usize,
    pub score: u32,
    pub progress: f32,
}
