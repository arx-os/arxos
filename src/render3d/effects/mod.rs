//! Visual Effects System
//!
//! This module provides the visual effects engine for terminal rendering,
//! organized into focused submodules for better maintainability.
//!
//! ## Module Organization
//! - `types`: Effect type definitions and data structures (145 lines)
//! - `config`: Configuration and quality settings (47 lines)
//! - `stats`: Performance statistics tracking (43 lines)
//! - `engine`: Main effects engine implementation (649 lines)
//!
//! ## Refactoring Complete
//! Successfully split the original 944-line effects.rs file into 4 focused modules
//! with clear single responsibilities, improving maintainability and readability.

// Re-export public API
pub use config::{EffectQuality, EffectsConfig};
pub use engine::VisualEffectsEngine;
pub use stats::EffectsStats;
pub use types::{EffectData, EffectState, EffectType, VisualEffect};

// Submodules with focused responsibilities
pub mod config;
pub mod engine;
pub mod stats;
pub mod types;
