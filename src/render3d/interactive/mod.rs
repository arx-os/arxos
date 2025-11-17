//! Interactive rendering submodules
//!
//! This module organizes the interactive renderer functionality into
//! focused submodules for better maintainability.

pub mod effects;
pub mod game;
pub mod handlers;
pub mod rendering;

// Re-export commonly used types
pub use effects::{
    add_particle_effects_to_output, create_equipment_status_effect,
    create_maintenance_alert_effect, create_particle_burst_effect,
};
pub use game::{GameScenario, GameState, GameStats};
pub use handlers::{
    handle_action, handle_camera_action, handle_floor_change, handle_resize,
    handle_view_mode_action, handle_zoom_action,
};
pub use rendering::{render_frame, render_overlay};
