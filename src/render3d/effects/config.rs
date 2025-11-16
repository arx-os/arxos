//! Visual effects configuration
//!
//! This module contains configuration types for the visual effects system
//! including quality settings and performance tuning parameters.

/// Visual effects configuration
#[derive(Debug, Clone)]
pub struct EffectsConfig {
    /// Maximum number of concurrent effects
    pub max_effects: usize,
    /// Enable particle effects
    pub enable_particles: bool,
    /// Enable animation effects
    pub enable_animations: bool,
    /// Default effect duration
    pub default_duration: std::time::Duration,
    /// Effect quality level
    pub quality_level: EffectQuality,
    /// Enable performance optimizations
    pub enable_optimizations: bool,
    /// Target effects FPS
    pub target_fps: u32,
}

/// Effect quality levels
#[derive(Debug, Clone, PartialEq)]
pub enum EffectQuality {
    Low,
    Medium,
    High,
    Ultra,
}

impl Default for EffectsConfig {
    fn default() -> Self {
        Self {
            max_effects: 50,
            enable_particles: true,
            enable_animations: true,
            default_duration: std::time::Duration::from_secs(3),
            quality_level: EffectQuality::Medium,
            enable_optimizations: true,
            target_fps: 60,
        }
    }
}
