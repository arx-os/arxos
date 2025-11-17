//! Type definitions for the animation system
//!
//! This module contains all the data structures, enums, and type definitions
//! used throughout the animation framework.

use std::time::{Duration, Instant};

/// Individual animation with timing and interpolation
#[derive(Debug, Clone)]
pub struct Animation {
    /// Animation identifier
    pub id: String,
    /// Animation type
    pub animation_type: AnimationType,
    /// Current progress (0.0 to 1.0)
    pub progress: f64,
    /// Duration of the animation
    pub duration: Duration,
    /// Start time
    pub start_time: Instant,
    /// Easing function
    pub easing: EasingFunction,
    /// Animation state
    pub state: AnimationState,
    /// Custom data for specific animation types
    pub data: AnimationData,
}

/// Different types of animations
#[derive(Debug, Clone, PartialEq)]
pub enum AnimationType {
    /// Linear interpolation between two values
    Linear,
    /// Smooth camera movement
    CameraMove,
    /// Equipment status transition
    StatusTransition,
    /// Building fade in/out
    BuildingFade,
    /// Particle effect animation
    ParticleEffect,
    /// Equipment selection highlight
    SelectionHighlight,
    /// Floor transition
    FloorTransition,
    /// View mode change
    ViewModeTransition,
}

/// Animation state
#[derive(Debug, Clone, PartialEq)]
pub enum AnimationState {
    /// Animation is waiting to start
    Pending,
    /// Animation is currently running
    Running,
    /// Animation has completed
    Completed,
    /// Animation was cancelled
    Cancelled,
    /// Animation is paused
    Paused,
}

/// Easing functions for smooth animations
#[derive(Debug, Clone, PartialEq)]
pub enum EasingFunction {
    /// Linear interpolation
    Linear,
    /// Smooth ease-in
    EaseIn,
    /// Smooth ease-out
    EaseOut,
    /// Smooth ease-in-out
    EaseInOut,
    /// Bounce effect
    Bounce,
    /// Elastic effect
    Elastic,
    /// Back effect
    Back,
    /// Custom cubic bezier
    CubicBezier(f64, f64, f64, f64),
}

/// Custom data for different animation types
#[derive(Debug, Clone)]
pub enum AnimationData {
    /// Linear animation data
    Linear {
        start_value: f64,
        end_value: f64,
        current_value: f64,
    },
    /// Camera movement data
    CameraMove {
        start_position: CameraPosition,
        end_position: CameraPosition,
        current_position: CameraPosition,
    },
    /// Status transition data
    StatusTransition {
        from_status: EquipmentStatus,
        to_status: EquipmentStatus,
        current_status: EquipmentStatus,
    },
    /// Building fade data
    BuildingFade {
        start_opacity: f64,
        end_opacity: f64,
        current_opacity: f64,
    },
    /// Particle effect data
    ParticleEffect {
        effect_type: ParticleEffectType,
        intensity: f64,
        duration_multiplier: f64,
    },
    /// Selection highlight data
    SelectionHighlight {
        equipment_id: String,
        highlight_intensity: f64,
        pulse_rate: f64,
    },
    /// Floor transition data
    FloorTransition {
        from_floor: i32,
        to_floor: i32,
        transition_height: f64,
    },
    /// View mode transition data
    ViewModeTransition {
        from_mode: ViewMode,
        to_mode: ViewMode,
        transition_progress: f64,
    },
}

/// Camera position for animations
#[derive(Debug, Clone)]
pub struct CameraPosition {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub target_x: f64,
    pub target_y: f64,
    pub target_z: f64,
}

/// Equipment status for animations
#[derive(Debug, Clone, PartialEq)]
pub enum EquipmentStatus {
    Healthy,
    Warning,
    Critical,
    Maintenance,
    Offline,
}

/// Particle effect types
#[derive(Debug, Clone, PartialEq)]
pub enum ParticleEffectType {
    Explosion,
    Smoke,
    Fire,
    Sparks,
    Dust,
    StatusIndicator,
}

/// View modes for transitions
#[derive(Debug, Clone, PartialEq)]
pub enum ViewMode {
    Standard,
    CrossSection,
    Connections,
    Maintenance,
}

/// Animation system configuration
#[derive(Debug, Clone)]
pub struct AnimationConfig {
    /// Maximum number of concurrent animations
    pub max_animations: usize,
    /// Default animation duration
    pub default_duration: Duration,
    /// Enable animation pooling
    pub enable_pooling: bool,
    /// Target animation FPS
    pub target_fps: u32,
    /// Enable smooth interpolation
    pub enable_smoothing: bool,
    /// Animation quality level
    pub quality_level: AnimationQuality,
}

/// Animation quality levels
#[derive(Debug, Clone, PartialEq)]
pub enum AnimationQuality {
    Low,
    Medium,
    High,
    Ultra,
}

/// Animation system statistics
#[derive(Debug, Clone)]
pub struct AnimationStats {
    /// Total animations created
    pub animations_created: u64,
    /// Total animations completed
    pub animations_completed: u64,
    /// Current active animation count
    pub active_animations: usize,
    /// Average update time per frame
    pub avg_update_time_ms: f64,
    /// Peak animation count
    pub peak_animation_count: usize,
    /// Animation frame rate
    pub fps: f64,
}

impl Default for AnimationConfig {
    fn default() -> Self {
        Self {
            max_animations: 100,
            default_duration: Duration::from_millis(500),
            enable_pooling: true,
            target_fps: 60,
            enable_smoothing: true,
            quality_level: AnimationQuality::High,
        }
    }
}

impl AnimationStats {
    pub fn new() -> Self {
        Self {
            animations_created: 0,
            animations_completed: 0,
            active_animations: 0,
            avg_update_time_ms: 0.0,
            peak_animation_count: 0,
            fps: 0.0,
        }
    }
}

impl Default for AnimationStats {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_camera_position() {
        let pos = CameraPosition {
            x: 1.0,
            y: 2.0,
            z: 3.0,
            target_x: 4.0,
            target_y: 5.0,
            target_z: 6.0,
        };
        assert_eq!(pos.x, 1.0);
        assert_eq!(pos.target_z, 6.0);
    }

    #[test]
    fn test_animation_state() {
        let state = AnimationState::Running;
        assert_eq!(state, AnimationState::Running);
        assert_ne!(state, AnimationState::Completed);
    }

    #[test]
    fn test_animation_config_default() {
        let config = AnimationConfig::default();
        assert_eq!(config.max_animations, 100);
        assert_eq!(config.target_fps, 32);
        assert_eq!(config.quality_level, AnimationQuality::High);
    }
}
