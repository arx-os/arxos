//! Core game types for gamified PR review and planning

use crate::core::Equipment;
use std::collections::HashMap;

/// Game mode determines the type of gameplay
#[derive(Debug, Clone, PartialEq)]
pub enum GameMode {
    /// Review contractor PRs interactively
    PRReview,
    /// Plan equipment placement with constraints
    Planning,
    /// Educational scenarios from historical PRs
    Learning,
    /// Validate building data interactively
    Validation,
}

/// Game scenario defines a playable scenario
#[derive(Debug, Clone)]
pub struct GameScenario {
    pub id: String,
    pub mode: GameMode,
    pub building: String,
    pub objective: String,
    pub constraints: Vec<Constraint>,
    pub equipment_items: Vec<GameEquipmentPlacement>,
    pub validation_rules: Vec<ValidationRule>,
}

/// Constraint defines a restriction that must be validated
#[derive(Debug, Clone)]
pub struct Constraint {
    pub id: String,
    pub constraint_type: ConstraintType,
    pub description: String,
    pub severity: ConstraintSeverity,
}

/// Type of constraint
#[derive(Debug, Clone, PartialEq)]
pub enum ConstraintType {
    /// Spatial constraints (wall support, clearance)
    Spatial,
    /// Structural constraints (load capacity, mounting points)
    Structural,
    /// Building code requirements
    Code,
    /// Budget/cost constraints
    Budget,
    /// Accessibility requirements (ADA)
    Accessibility,
    /// User preference constraints (teacher/occupant requests)
    UserPreference,
}

/// Severity level of constraint violation
#[derive(Debug, Clone, PartialEq)]
pub enum ConstraintSeverity {
    /// Informational - suggestion only
    Info,
    /// Warning - should be addressed but not blocking
    Warning,
    /// Error - must be resolved before proceeding
    Error,
    /// Critical - cannot proceed with violation
    Critical,
}

/// Equipment placement in game context with metadata
#[derive(Debug, Clone)]
pub struct GameEquipmentPlacement {
    pub equipment: Equipment,

    // IFC Preservation Fields
    pub ifc_entity_id: Option<String>,
    pub ifc_entity_type: Option<String>,
    pub ifc_placement_chain: Option<Vec<String>>,
    pub ifc_original_properties: HashMap<String, String>,

    // Game-specific
    pub game_action: GameAction,
    pub constraint_validation: ValidationResult,
}

/// Action that created/modified this placement
#[derive(Debug, Clone, PartialEq)]
pub enum GameAction {
    /// Loaded from existing building data
    Loaded,
    /// Placed by user in planning mode
    Placed,
    /// Modified from original position
    Modified,
    /// Added from PR review
    AddedFromPR,
}

/// Validation result for equipment placement
#[derive(Debug, Clone)]
pub struct ValidationResult {
    pub is_valid: bool,
    pub violations: Vec<ConstraintViolation>,
    pub warnings: Vec<String>,
    pub suggestions: Vec<String>,
}

impl Default for ValidationResult {
    fn default() -> Self {
        Self {
            is_valid: true,
            violations: Vec::new(),
            warnings: Vec::new(),
            suggestions: Vec::new(),
        }
    }
}

/// Constraint violation details
#[derive(Debug, Clone)]
pub struct ConstraintViolation {
    pub constraint_id: String,
    pub constraint_type: ConstraintType,
    pub severity: ConstraintSeverity,
    pub message: String,
    pub suggestion: Option<String>,
}

/// Validation rule for scenario
#[derive(Debug, Clone)]
pub struct ValidationRule {
    pub id: String,
    pub name: String,
    pub description: String,
    pub validate: ValidationFunction,
}

/// Type for validation functions (forward declare GameState)
pub type ValidationFunction =
    fn(&crate::game::state::GameState, &GameEquipmentPlacement) -> ValidationResult;

/// Game objectives and goals
#[derive(Debug, Clone)]
pub struct GameObjective {
    pub id: String,
    pub title: String,
    pub description: String,
    pub criteria: Vec<ObjectiveCriterion>,
}

/// Criterion for completing an objective
#[derive(Debug, Clone)]
pub struct ObjectiveCriterion {
    pub id: String,
    pub description: String,
    pub is_required: bool,
    pub is_completed: bool,
}
