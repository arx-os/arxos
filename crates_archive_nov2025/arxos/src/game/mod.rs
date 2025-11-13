//! Gamified PR Review and Planning System
//!
//! This module provides interactive game-based interfaces for:
//! - Reviewing contractor PRs with constraint validation
//! - Planning equipment placement with real-time feedback
//! - Learning from historical PRs as educational scenarios
//! - Validating building data interactively

pub mod constraints;
pub mod export;
pub mod ifc_mapping;
pub mod ifc_sync;
pub mod learning;
pub mod planning;
pub mod pr_game;
pub mod scenario;
pub mod state;
pub mod types;

// Re-export commonly used types
pub use constraints::{ConstraintData, ConstraintSystem};
pub use export::{export_game_to_ifc, IFCExportSummary, IFCGameExporter};
pub use ifc_mapping::{apply_ifc_type_mapping, IFCTypeMapper};
pub use ifc_sync::{
    extract_ifc_metadata_from_properties, inject_ifc_metadata_to_properties, IFCMetadata,
    IFCSyncManager, IFCSyncSummary,
};
pub use learning::{CommentaryCategory, ExpertCommentary, LearningMode, TutorialStep};
pub use planning::{PlacementAction, PlanningGame, PlanningValidationSummary};
pub use pr_game::{PRReviewGame, PRValidationSummary, ReviewComment, ReviewDecision};
pub use scenario::GameScenarioLoader;
pub use state::{GameState, GameStats};
pub use types::*;
