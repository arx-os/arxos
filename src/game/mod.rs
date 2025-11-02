//! Gamified PR Review and Planning System
//!
//! This module provides interactive game-based interfaces for:
//! - Reviewing contractor PRs with constraint validation
//! - Planning equipment placement with real-time feedback
//! - Learning from historical PRs as educational scenarios
//! - Validating building data interactively

pub mod types;
pub mod scenario;
pub mod state;
pub mod constraints;
pub mod pr_game;
pub mod planning;
pub mod ifc_sync;
pub mod ifc_mapping;
pub mod export;
pub mod learning;

// Re-export commonly used types
pub use types::*;
pub use scenario::GameScenarioLoader;
pub use state::{GameState, GameStats};
pub use constraints::{ConstraintSystem, ConstraintData};
pub use pr_game::{PRReviewGame, ReviewDecision, ReviewComment, PRValidationSummary};
pub use planning::{PlanningGame, PlacementAction, PlanningValidationSummary};
pub use ifc_sync::{IFCSyncManager, IFCMetadata, IFCSyncSummary, extract_ifc_metadata_from_properties, inject_ifc_metadata_to_properties};
pub use ifc_mapping::{IFCTypeMapper, apply_ifc_type_mapping};
pub use export::{IFCGameExporter, IFCExportSummary, export_game_to_ifc};
pub use learning::{LearningMode, ExpertCommentary, CommentaryCategory, TutorialStep};

