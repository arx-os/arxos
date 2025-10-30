//! Animation Framework for Terminal Rendering
//!
//! This module provides a comprehensive animation system for smooth transitions,
//! interpolations, and timed effects in terminal-based 3D rendering.

use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Animation system for managing smooth transitions and effects
pub struct AnimationSystem {
    /// Active animations
    animations: HashMap<String, Animation>,
    /// Animation configuration
    config: AnimationConfig,
    /// System statistics
    stats: AnimationStats,
    /// Last update time
    #[allow(dead_code)] // Will be used in future animation features
    last_update: Instant,
}

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

impl Default for AnimationSystem {
    fn default() -> Self {
        Self::new()
    }
}

impl AnimationSystem {
    /// Create a new animation system
    pub fn new() -> Self {
        Self::with_config(AnimationConfig::default())
    }

    /// Create animation system with custom configuration
    pub fn with_config(config: AnimationConfig) -> Self {
        Self {
            animations: HashMap::with_capacity(config.max_animations),
            config,
            stats: AnimationStats::new(),
            last_update: Instant::now(),
        }
    }

    /// Update all animations (call this every frame)
    pub fn update(&mut self, delta_time: f64) {
        let start_time = Instant::now();
        
        // Update each animation
        let mut completed_animations = Vec::new();
        let mut animations_to_update = Vec::new();
        
        // Collect animations that need updating
        for (id, animation) in &self.animations {
            if animation.state == AnimationState::Running {
                animations_to_update.push((id.clone(), animation.clone()));
            }
        }
        
        // Update animations
        for (id, mut animation) in animations_to_update {
            self.update_animation(&mut animation, delta_time);
            
            if animation.progress >= 1.0 {
                animation.state = AnimationState::Completed;
                completed_animations.push(id.clone());
            }
            
            // Update the animation in the map
            if let Some(stored_animation) = self.animations.get_mut(&id) {
                *stored_animation = animation;
            }
        }
        
        // Remove completed animations
        for id in completed_animations {
            self.animations.remove(&id);
            self.stats.animations_completed += 1;
        }
        
        // Update statistics
        self.update_stats(start_time, delta_time);
    }

    /// Update a single animation
    fn update_animation(&mut self, animation: &mut Animation, _delta_time: f64) {
        // Calculate progress based on elapsed time
        let elapsed = animation.start_time.elapsed();
        let duration_secs = animation.duration.as_secs_f64();
        
        animation.progress = (elapsed.as_secs_f64() / duration_secs).min(1.0);
        
        // Apply easing function
        let eased_progress = self.apply_easing(animation.progress, &animation.easing);
        
        // Update animation data based on type
        self.update_animation_data(animation, eased_progress);
    }

    /// Apply easing function to progress value
    fn apply_easing(&self, progress: f64, easing: &EasingFunction) -> f64 {
        match easing {
            EasingFunction::Linear => progress,
            EasingFunction::EaseIn => progress * progress,
            EasingFunction::EaseOut => 1.0 - (1.0 - progress) * (1.0 - progress),
            EasingFunction::EaseInOut => {
                if progress < 0.5 {
                    2.0 * progress * progress
                } else {
                    1.0 - 2.0 * (1.0 - progress) * (1.0 - progress)
                }
            }
            EasingFunction::Bounce => self.bounce_easing(progress),
            EasingFunction::Elastic => self.elastic_easing(progress),
            EasingFunction::Back => self.back_easing(progress),
            EasingFunction::CubicBezier(x1, y1, x2, y2) => self.cubic_bezier_easing(progress, *x1, *y1, *x2, *y2),
        }
    }

    /// Bounce easing function
    fn bounce_easing(&self, t: f64) -> f64 {
        if t < 1.0 / 2.75 {
            7.5625 * t * t
        } else if t < 2.0 / 2.75 {
            let t = t - 1.5 / 2.75;
            7.5625 * t * t + 0.75
        } else if t < 2.5 / 2.75 {
            let t = t - 2.25 / 2.75;
            7.5625 * t * t + 0.9375
        } else {
            let t = t - 2.625 / 2.75;
            7.5625 * t * t + 0.984375
        }
    }

    /// Elastic easing function
    fn elastic_easing(&self, t: f64) -> f64 {
        if t == 0.0 || t == 1.0 {
            t
        } else {
            let c4 = (2.0 * std::f64::consts::PI) / 3.0;
            -(2.0_f64.powf(10.0 * t - 10.0)) * ((t * 10.0 - 10.75) * c4).sin()
        }
    }

    /// Back easing function
    fn back_easing(&self, t: f64) -> f64 {
        const C1: f64 = 1.70158;
        const C3: f64 = C1 + 1.0;
        C3 * t * t * t - C1 * t * t
    }

    /// Cubic bezier easing function
    fn cubic_bezier_easing(&self, t: f64, _x1: f64, y1: f64, _x2: f64, y2: f64) -> f64 {
        // Simplified cubic bezier implementation
        let t2 = t * t;
        let t3 = t2 * t;
        let mt = 1.0 - t;
        let mt2 = mt * mt;
        let _mt3 = mt2 * mt;
        
        3.0 * mt2 * t * y1 + 3.0 * mt * t2 * y2 + t3
    }

    /// Update animation data based on animation type
    fn update_animation_data(&mut self, animation: &mut Animation, eased_progress: f64) {
        match &mut animation.data {
            AnimationData::Linear { start_value, end_value, current_value } => {
                *current_value = *start_value + (*end_value - *start_value) * eased_progress;
            }
            AnimationData::CameraMove { start_position, end_position, current_position } => {
                current_position.x = start_position.x + (end_position.x - start_position.x) * eased_progress;
                current_position.y = start_position.y + (end_position.y - start_position.y) * eased_progress;
                current_position.z = start_position.z + (end_position.z - start_position.z) * eased_progress;
                current_position.target_x = start_position.target_x + (end_position.target_x - start_position.target_x) * eased_progress;
                current_position.target_y = start_position.target_y + (end_position.target_y - start_position.target_y) * eased_progress;
                current_position.target_z = start_position.target_z + (end_position.target_z - start_position.target_z) * eased_progress;
            }
            AnimationData::StatusTransition { from_status, to_status, current_status } => {
                // Status transitions are discrete, so we use a threshold
                if eased_progress < 0.5 {
                    *current_status = from_status.clone();
                } else {
                    *current_status = to_status.clone();
                }
            }
            AnimationData::BuildingFade { start_opacity, end_opacity, current_opacity } => {
                *current_opacity = *start_opacity + (*end_opacity - *start_opacity) * eased_progress;
            }
            AnimationData::ParticleEffect { intensity, .. } => {
                *intensity = eased_progress;
            }
            AnimationData::SelectionHighlight { highlight_intensity, pulse_rate, .. } => {
                *highlight_intensity = (eased_progress * *pulse_rate).sin().abs();
            }
            AnimationData::FloorTransition { transition_height, .. } => {
                *transition_height = eased_progress * 10.0; // 10 units height transition
            }
            AnimationData::ViewModeTransition { transition_progress, .. } => {
                *transition_progress = eased_progress;
            }
        }
    }

    /// Start a new animation
    pub fn start_animation(&mut self, mut animation: Animation) -> Result<(), String> {
        if self.animations.len() >= self.config.max_animations {
            return Err("Maximum animation limit reached".to_string());
        }
        
        animation.start_time = Instant::now();
        animation.state = AnimationState::Running;
        animation.progress = 0.0;
        
        self.animations.insert(animation.id.clone(), animation);
        self.stats.animations_created += 1;
        
        Ok(())
    }

    /// Create and start a linear animation
    pub fn animate_linear(&mut self, id: String, start_value: f64, end_value: f64, duration: Duration) -> Result<(), String> {
        let animation = Animation {
            id,
            animation_type: AnimationType::Linear,
            progress: 0.0,
            duration,
            start_time: Instant::now(),
            easing: EasingFunction::EaseInOut,
            state: AnimationState::Pending,
            data: AnimationData::Linear {
                start_value,
                end_value,
                current_value: start_value,
            },
        };
        
        self.start_animation(animation)
    }

    /// Create and start a camera movement animation
    pub fn animate_camera_move(&mut self, id: String, start_pos: CameraPosition, end_pos: CameraPosition, duration: Duration) -> Result<(), String> {
        let animation = Animation {
            id,
            animation_type: AnimationType::CameraMove,
            progress: 0.0,
            duration,
            start_time: Instant::now(),
            easing: EasingFunction::EaseInOut,
            state: AnimationState::Pending,
            data: AnimationData::CameraMove {
                start_position: start_pos.clone(),
                end_position: end_pos.clone(),
                current_position: start_pos,
            },
        };
        
        self.start_animation(animation)
    }

    /// Create and start a status transition animation
    pub fn animate_status_transition(&mut self, id: String, from_status: EquipmentStatus, to_status: EquipmentStatus, duration: Duration) -> Result<(), String> {
        let animation = Animation {
            id,
            animation_type: AnimationType::StatusTransition,
            progress: 0.0,
            duration,
            start_time: Instant::now(),
            easing: EasingFunction::EaseInOut,
            state: AnimationState::Pending,
            data: AnimationData::StatusTransition {
                from_status: from_status.clone(),
                to_status: to_status.clone(),
                current_status: from_status,
            },
        };
        
        self.start_animation(animation)
    }

    /// Get animation by ID
    pub fn get_animation(&self, id: &str) -> Option<&Animation> {
        self.animations.get(id)
    }

    /// Get mutable animation by ID
    pub fn get_animation_mut(&mut self, id: &str) -> Option<&mut Animation> {
        self.animations.get_mut(id)
    }

    /// Cancel animation by ID
    pub fn cancel_animation(&mut self, id: &str) -> bool {
        if let Some(animation) = self.animations.get_mut(id) {
            animation.state = AnimationState::Cancelled;
            true
        } else {
            false
        }
    }

    /// Pause animation by ID
    pub fn pause_animation(&mut self, id: &str) -> bool {
        if let Some(animation) = self.animations.get_mut(id) {
            if animation.state == AnimationState::Running {
                animation.state = AnimationState::Paused;
                return true;
            }
        }
        false
    }

    /// Resume animation by ID
    pub fn resume_animation(&mut self, id: &str) -> bool {
        if let Some(animation) = self.animations.get_mut(id) {
            if animation.state == AnimationState::Paused {
                animation.state = AnimationState::Running;
                return true;
            }
        }
        false
    }

    /// Update system statistics
    fn update_stats(&mut self, start_time: Instant, delta_time: f64) {
        let update_duration = start_time.elapsed();
        self.stats.avg_update_time_ms = update_duration.as_secs_f64() * 1000.0;
        self.stats.active_animations = self.animations.len();
        self.stats.fps = 1.0 / delta_time;
        
        // Update peak count
        if self.animations.len() > self.stats.peak_animation_count {
            self.stats.peak_animation_count = self.animations.len();
        }
    }

    /// Get all active animations
    pub fn animations(&self) -> &HashMap<String, Animation> {
        &self.animations
    }

    /// Get system statistics
    pub fn stats(&self) -> &AnimationStats {
        &self.stats
    }

    /// Get system configuration
    pub fn config(&self) -> &AnimationConfig {
        &self.config
    }

    /// Update configuration
    pub fn update_config(&mut self, config: AnimationConfig) {
        self.config = config;
    }

    /// Clear all animations
    pub fn clear(&mut self) {
        self.animations.clear();
    }

    /// Get animation count
    pub fn animation_count(&self) -> usize {
        self.animations.len()
    }
}

impl Default for AnimationConfig {
    fn default() -> Self {
        Self {
            max_animations: 100,
            default_duration: Duration::from_millis(500),
            enable_pooling: true,
            target_fps: 60,
            enable_smoothing: true,
            quality_level: AnimationQuality::Medium,
        }
    }
}

impl AnimationStats {
    /// Create new statistics
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
    fn test_animation_system_creation() {
        let system = AnimationSystem::new();
        assert_eq!(system.animation_count(), 0);
        assert_eq!(system.config.max_animations, 100);
    }

    #[test]
    fn test_linear_animation() {
        let mut system = AnimationSystem::new();
        
        let result = system.animate_linear(
            "test".to_string(),
            0.0,
            100.0,
            Duration::from_millis(100)
        );
        
        assert!(result.is_ok());
        assert_eq!(system.animation_count(), 1);
    }

    #[test]
    fn test_animation_update() {
        let mut system = AnimationSystem::new();
        
        system.animate_linear(
            "test".to_string(),
            0.0,
            100.0,
            Duration::from_millis(100)
        ).unwrap();
        
        // Update with 50ms delta time
        system.update(0.05);
        
        let animation = system.get_animation("test").unwrap();
        assert!(animation.progress > 0.0);
    }

    #[test]
    fn test_easing_functions() {
        let system = AnimationSystem::new();
        
        // Test linear easing
        assert_eq!(system.apply_easing(0.5, &EasingFunction::Linear), 0.5);
        
        // Test ease-in
        let ease_in = system.apply_easing(0.5, &EasingFunction::EaseIn);
        assert!(ease_in < 0.5);
        
        // Test ease-out
        let ease_out = system.apply_easing(0.5, &EasingFunction::EaseOut);
        assert!(ease_out > 0.5);
    }

    #[test]
    fn test_animation_cancellation() {
        let mut system = AnimationSystem::new();
        
        system.animate_linear(
            "test".to_string(),
            0.0,
            100.0,
            Duration::from_millis(100)
        ).unwrap();
        
        assert!(system.cancel_animation("test"));
        assert!(!system.cancel_animation("nonexistent"));
    }

    #[test]
    fn test_camera_position() {
        let pos1 = CameraPosition {
            x: 0.0, y: 0.0, z: 0.0,
            target_x: 0.0, target_y: 0.0, target_z: 0.0,
        };
        
        let pos2 = CameraPosition {
            x: 10.0, y: 10.0, z: 10.0,
            target_x: 5.0, target_y: 5.0, target_z: 5.0,
        };
        
        let mut system = AnimationSystem::new();
        
        let result = system.animate_camera_move(
            "camera_test".to_string(),
            pos1,
            pos2,
            Duration::from_millis(100)
        );
        
        assert!(result.is_ok());
    }
}
