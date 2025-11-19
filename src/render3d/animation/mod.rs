//! Animation Framework for Terminal Rendering
//!
//! This module provides a comprehensive animation system for smooth transitions,
//! interpolations, and timed effects in terminal-based 3D rendering.

// Submodules
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

        // Apply easing function using the easing module
        let eased_progress = apply_easing(animation.progress, &animation.easing);

        // Update animation data based on type
        self.update_animation_data(animation, eased_progress);
    }

    /// Update animation data based on animation type
    fn update_animation_data(&mut self, animation: &mut Animation, eased_progress: f64) {
        match &mut animation.data {
            AnimationData::Linear {
                start_value,
                end_value,
                current_value,
            } => {
                *current_value = *start_value + (*end_value - *start_value) * eased_progress;
            }
            AnimationData::CameraMove {
                start_position,
                end_position,
                current_position,
            } => {
                current_position.x =
                    start_position.x + (end_position.x - start_position.x) * eased_progress;
                current_position.y =
                    start_position.y + (end_position.y - start_position.y) * eased_progress;
                current_position.z =
                    start_position.z + (end_position.z - start_position.z) * eased_progress;
                current_position.target_x = start_position.target_x
                    + (end_position.target_x - start_position.target_x) * eased_progress;
                current_position.target_y = start_position.target_y
                    + (end_position.target_y - start_position.target_y) * eased_progress;
                current_position.target_z = start_position.target_z
                    + (end_position.target_z - start_position.target_z) * eased_progress;
            }
            AnimationData::StatusTransition {
                from_status,
                to_status,
                current_status,
            } => {
                // Status transitions are discrete, so we use a threshold
                if eased_progress < 0.5 {
                    *current_status = from_status.clone();
                } else {
                    *current_status = to_status.clone();
                }
            }
            AnimationData::BuildingFade {
                start_opacity,
                end_opacity,
                current_opacity,
            } => {
                *current_opacity =
                    *start_opacity + (*end_opacity - *start_opacity) * eased_progress;
            }
            AnimationData::ParticleEffect { intensity, .. } => {
                *intensity = eased_progress;
            }
            AnimationData::SelectionHighlight {
                highlight_intensity,
                pulse_rate,
                ..
            } => {
                *highlight_intensity = (eased_progress * *pulse_rate).sin().abs();
            }
            AnimationData::FloorTransition {
                transition_height, ..
            } => {
                *transition_height = eased_progress * 10.0; // 10 units height transition
            }
            AnimationData::ViewModeTransition {
                transition_progress,
                ..
            } => {
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
    pub fn animate_linear(
        &mut self,
        id: String,
        start_value: f64,
        end_value: f64,
        duration: Duration,
    ) -> Result<(), String> {
        let animation = create_linear_animation(id, start_value, end_value, duration);
        self.start_animation(animation)
    }

    /// Create and start a camera movement animation
    pub fn animate_camera_move(
        &mut self,
        id: String,
        start_pos: CameraPosition,
        end_pos: CameraPosition,
        duration: Duration,
    ) -> Result<(), String> {
        let animation = create_camera_move_animation(id, start_pos, end_pos, duration);
        self.start_animation(animation)
    }

    /// Create and start a status transition animation
    pub fn animate_status_transition(
        &mut self,
        id: String,
        from_status: EquipmentStatus,
        to_status: EquipmentStatus,
        duration: Duration,
    ) -> Result<(), String> {
        let animation =
            create_status_transition_animation(id, from_status, to_status, duration);
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

        let result =
            system.animate_linear("test".to_string(), 0.0, 100.0, Duration::from_millis(100));

        assert!(result.is_ok());
        assert_eq!(system.animation_count(), 1);
    }

    #[test]
    fn test_animation_update() {
        let mut system = AnimationSystem::new();

        system
            .animate_linear("test".to_string(), 0.0, 100.0, Duration::from_millis(100))
            .unwrap();

        // Update with 50ms delta time
        system.update(0.05);

        let animation = system.get_animation("test").unwrap();
        assert!(animation.progress > 0.0);
    }

    #[test]
    fn test_easing_functions() {
        // Test linear easing
        assert_eq!(
            apply_easing(0.5, &EasingFunction::Linear),
            0.5
        );

        // Test ease-in
        let ease_in = apply_easing(0.5, &EasingFunction::EaseIn);
        assert!(ease_in < 0.5);

        // Test ease-out
        let ease_out = apply_easing(0.5, &EasingFunction::EaseOut);
        assert!(ease_out > 0.5);
    }

    #[test]
    fn test_animation_cancellation() {
        let mut system = AnimationSystem::new();

        system
            .animate_linear("test".to_string(), 0.0, 100.0, Duration::from_millis(100))
            .unwrap();

        assert!(system.cancel_animation("test"));
        assert!(!system.cancel_animation("nonexistent"));
    }

    #[test]
    fn test_camera_position() {
        let pos1 = CameraPosition {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            target_x: 0.0,
            target_y: 0.0,
            target_z: 0.0,
        };

        let pos2 = CameraPosition {
            x: 10.0,
            y: 10.0,
            z: 10.0,
            target_x: 5.0,
            target_y: 5.0,
            target_z: 5.0,
        };

        let mut system = AnimationSystem::new();

        let result = system.animate_camera_move(
            "camera_test".to_string(),
            pos1,
            pos2,
            Duration::from_millis(100),
        );

        assert!(result.is_ok());
    }
}
