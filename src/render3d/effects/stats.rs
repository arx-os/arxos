//! Visual effects performance statistics
//!
//! This module tracks and reports performance metrics for the visual effects system.

/// Visual effects performance statistics
#[derive(Debug, Clone)]
pub struct EffectsStats {
    /// Total effects created
    pub effects_created: u64,
    /// Total effects completed
    pub effects_completed: u64,
    /// Current active effect count
    pub active_effects: usize,
    /// Average update time per frame
    pub avg_update_time_ms: f64,
    /// Peak effect count
    pub peak_effect_count: usize,
    /// Effects frame rate
    pub fps: f64,
}

impl EffectsStats {
    /// Create new statistics
    pub fn new() -> Self {
        Self {
            effects_created: 0,
            effects_completed: 0,
            active_effects: 0,
            avg_update_time_ms: 0.0,
            peak_effect_count: 0,
            fps: 0.0,
        }
    }
}

impl Default for EffectsStats {
    fn default() -> Self {
        Self::new()
    }
}
