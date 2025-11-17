//! Animation system modules
//!
//! This module organizes the animation framework into focused submodules
//! for better maintainability and clarity.

pub mod builders;
pub mod easing;
pub mod types;

// Re-export commonly used types
pub use types::{
    Animation, AnimationConfig, AnimationData, AnimationQuality, AnimationState, AnimationStats,
    AnimationType, CameraPosition, EasingFunction, EquipmentStatus, ParticleEffectType, ViewMode,
};

// Re-export builder functions
pub use builders::{
    create_camera_move_animation, create_linear_animation, create_status_transition_animation,
};

// Re-export easing functions
pub use easing::{apply_easing, back_easing, bounce_easing, cubic_bezier_easing, elastic_easing};
