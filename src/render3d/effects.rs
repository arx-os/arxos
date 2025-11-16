//! Visual Effects Engine for Terminal Rendering
//!
//! This module provides advanced visual effects for equipment status, building health,
//! and interactive elements using particles and animations.

use crate::render3d::animation::{AnimationSystem, EquipmentStatus};
use crate::render3d::particles::{
    AlertLevel, Particle, ParticleData, ParticleSystem, ParticleType, StatusType, Vector3D,
};
use crate::core::spatial::Point3D;
use std::collections::HashMap;

/// Visual effects engine for terminal rendering
pub struct VisualEffectsEngine {
    /// Particle system for effects
    particle_system: ParticleSystem,
    /// Animation system for smooth transitions
    animation_system: AnimationSystem,
    /// Active effects
    active_effects: HashMap<String, VisualEffect>,
    /// Effect configuration
    config: EffectsConfig,
    /// Performance statistics
    stats: EffectsStats,
}

/// Individual visual effect
#[derive(Debug, Clone)]
pub struct VisualEffect {
    /// Effect identifier
    pub id: String,
    /// Effect type
    pub effect_type: EffectType,
    /// Effect state
    pub state: EffectState,
    /// Effect duration
    pub duration: Option<std::time::Duration>,
    /// Effect intensity
    pub intensity: f64,
    /// Effect position
    pub position: Point3D,
    /// Effect data
    pub data: EffectData,
}

/// Different types of visual effects
#[derive(Debug, Clone, PartialEq)]
pub enum EffectType {
    /// Equipment status indicator
    EquipmentStatus,
    /// Building health visualization
    BuildingHealth,
    /// Maintenance alert
    MaintenanceAlert,
    /// Equipment connection
    EquipmentConnection,
    /// Selection highlight
    SelectionHighlight,
    /// Floor transition effect
    FloorTransition,
    /// View mode transition
    ViewModeTransition,
    /// Particle burst effect
    ParticleBurst,
    /// Smoke effect
    SmokeEffect,
    /// Fire effect
    FireEffect,
    /// Spark effect
    SparkEffect,
}

/// Effect state
#[derive(Debug, Clone, PartialEq)]
pub enum EffectState {
    /// Effect is starting
    Starting,
    /// Effect is active
    Active,
    /// Effect is ending
    Ending,
    /// Effect has completed
    Completed,
    /// Effect was cancelled
    Cancelled,
}

/// Custom data for different effect types
#[derive(Debug, Clone)]
pub enum EffectData {
    /// Equipment status effect data
    EquipmentStatus {
        equipment_id: String,
        status: EquipmentStatus,
        pulse_rate: f64,
        color_intensity: f64,
    },
    /// Building health effect data
    BuildingHealth {
        health_level: f64,
        alert_count: usize,
        maintenance_count: usize,
    },
    /// Maintenance alert effect data
    MaintenanceAlert {
        equipment_id: String,
        alert_level: AlertLevel,
        urgency: f64,
    },
    /// Equipment connection effect data
    EquipmentConnection {
        source_id: String,
        target_id: String,
        connection_strength: f64,
        data_flow: f64,
    },
    /// Selection highlight effect data
    SelectionHighlight {
        equipment_id: String,
        highlight_color: char,
        pulse_intensity: f64,
    },
    /// Floor transition effect data
    FloorTransition {
        from_floor: i32,
        to_floor: i32,
        transition_speed: f64,
    },
    /// View mode transition effect data
    ViewModeTransition {
        from_mode: String,
        to_mode: String,
        transition_type: String,
    },
    /// Particle burst effect data
    ParticleBurst {
        particle_count: usize,
        burst_radius: f64,
        particle_type: ParticleType,
    },
    /// Smoke effect data
    SmokeEffect {
        smoke_intensity: f64,
        temperature: f64,
        wind_direction: Vector3D,
    },
    /// Fire effect data
    FireEffect {
        fire_intensity: f64,
        temperature: f64,
        flicker_rate: f64,
    },
    /// Spark effect data
    SparkEffect {
        spark_count: usize,
        energy_level: f64,
        trail_length: usize,
    },
}

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

impl Default for VisualEffectsEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl VisualEffectsEngine {
    /// Create a new visual effects engine
    pub fn new() -> Self {
        Self::with_config(EffectsConfig::default())
    }

    /// Create visual effects engine with custom configuration
    pub fn with_config(config: EffectsConfig) -> Self {
        Self {
            particle_system: ParticleSystem::new(),
            animation_system: AnimationSystem::new(),
            active_effects: HashMap::with_capacity(config.max_effects),
            config,
            stats: EffectsStats::new(),
        }
    }

    /// Update all effects (call this every frame)
    pub fn update(&mut self, delta_time: f64) {
        let start_time = std::time::Instant::now();

        // Update particle system
        if self.config.enable_particles {
            self.particle_system.update(delta_time);
        }

        // Update animation system
        if self.config.enable_animations {
            self.animation_system.update(delta_time);
        }

        // Update visual effects
        self.update_effects(delta_time);

        // Update statistics
        self.update_stats(start_time, delta_time);
    }

    /// Update all visual effects
    fn update_effects(&mut self, delta_time: f64) {
        let mut completed = 0usize;
        let previous_effects = std::mem::take(&mut self.active_effects);
        let mut next_effects = HashMap::with_capacity(previous_effects.capacity());

        for (id, mut effect) in previous_effects.into_iter() {
            self.update_effect(&mut effect, delta_time);
            if effect.state == EffectState::Completed {
                completed += 1;
            } else {
                next_effects.insert(id, effect);
            }
        }

        self.active_effects = next_effects;

        if completed > 0 {
            self.stats.effects_completed += completed as u64;
        }
    }

    /// Update a single visual effect
    fn update_effect(&mut self, effect: &mut VisualEffect, _delta_time: f64) {
        match effect.effect_type {
            EffectType::EquipmentStatus => self.update_equipment_status_effect(effect),
            EffectType::BuildingHealth => self.update_building_health_effect(effect),
            EffectType::MaintenanceAlert => self.update_maintenance_alert_effect(effect),
            EffectType::EquipmentConnection => self.update_equipment_connection_effect(effect),
            EffectType::SelectionHighlight => self.update_selection_highlight_effect(effect),
            EffectType::FloorTransition => self.update_floor_transition_effect(effect),
            EffectType::ViewModeTransition => self.update_view_mode_transition_effect(effect),
            EffectType::ParticleBurst => self.update_particle_burst_effect(effect),
            EffectType::SmokeEffect => self.update_smoke_effect(effect),
            EffectType::FireEffect => self.update_fire_effect(effect),
            EffectType::SparkEffect => self.update_spark_effect(effect),
        }
    }

    /// Update equipment status effect
    fn update_equipment_status_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::EquipmentStatus {
            status,
            pulse_rate,
            color_intensity,
            ..
        } = &mut effect.data
        {
            // Create pulsing particle effect
            let pulse = (effect.intensity * *pulse_rate).sin().abs();
            *color_intensity = pulse;

            // Emit status indicator particles
            if self.config.enable_particles {
                let particle = Particle {
                    position: effect.position,
                    velocity: Vector3D::new(0.0, 0.1, 0.0),
                    acceleration: Vector3D::zero(),
                    lifetime: 1.0,
                    max_lifetime: 2.0,
                    size: pulse,
                    character: match status {
                        EquipmentStatus::Healthy => '✓',
                        EquipmentStatus::Warning => '⚠',
                        EquipmentStatus::Critical => '✗',
                        EquipmentStatus::Maintenance => '🔧',
                        EquipmentStatus::Offline => '○',
                    },
                    particle_type: ParticleType::StatusIndicator,
                    data: ParticleData::StatusIndicator {
                        equipment_id: "status".to_string(),
                        status_type: match status {
                            EquipmentStatus::Healthy => StatusType::Healthy,
                            EquipmentStatus::Warning => StatusType::Warning,
                            EquipmentStatus::Critical => StatusType::Critical,
                            EquipmentStatus::Maintenance => StatusType::Maintenance,
                            EquipmentStatus::Offline => StatusType::Healthy, // Default
                        },
                    },
                };

                self.particle_system.emit_particle(particle);
            }
        }
    }

    /// Update building health effect
    fn update_building_health_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::BuildingHealth {
            health_level,
            alert_count,
            maintenance_count,
        } = &mut effect.data
        {
            // Create building-wide health visualization
            let health_color = if *health_level > 0.8 {
                '🟢' // Green for healthy
            } else if *health_level > 0.6 {
                '🟡' // Yellow for warning
            } else {
                '🔴' // Red for critical
            };

            // Emit health indicator particles
            if self.config.enable_particles {
                for i in 0..(*alert_count + *maintenance_count) {
                    let angle = (i as f64 / (*alert_count + *maintenance_count) as f64)
                        * 2.0
                        * std::f64::consts::PI;
                    let radius = 5.0 + (*health_level * 10.0);

                    let particle = Particle {
                        position: Point3D::new(
                            effect.position.x + angle.cos() * radius,
                            effect.position.y,
                            effect.position.z + angle.sin() * radius,
                        ),
                        velocity: Vector3D::new(0.0, 0.05, 0.0),
                        acceleration: Vector3D::zero(),
                        lifetime: 1.0,
                        max_lifetime: 3.0,
                        size: *health_level,
                        character: health_color,
                        particle_type: ParticleType::StatusIndicator,
                        data: ParticleData::StatusIndicator {
                            equipment_id: "building_health".to_string(),
                            status_type: StatusType::Healthy,
                        },
                    };

                    self.particle_system.emit_particle(particle);
                }
            }
        }
    }

    /// Update maintenance alert effect
    fn update_maintenance_alert_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::MaintenanceAlert {
            alert_level,
            urgency,
            ..
        } = &mut effect.data
        {
            // Create blinking alert effect
            let blink = (effect.intensity * 8.0).sin() > 0.0;
            let alert_char = if blink {
                match alert_level {
                    AlertLevel::Low => '🔶',
                    AlertLevel::Medium => '🔸',
                    AlertLevel::High => '🔴',
                    AlertLevel::Critical => '🚨',
                }
            } else {
                ' '
            };

            // Emit alert particles
            if self.config.enable_particles {
                let particle = Particle {
                    position: effect.position,
                    velocity: Vector3D::new(0.0, 0.2, 0.0),
                    acceleration: Vector3D::zero(),
                    lifetime: 1.0,
                    max_lifetime: 1.5,
                    size: *urgency,
                    character: alert_char,
                    particle_type: ParticleType::MaintenanceAlert,
                    data: ParticleData::MaintenanceAlert {
                        alert_level: alert_level.clone(),
                        equipment_id: "maintenance".to_string(),
                    },
                };

                self.particle_system.emit_particle(particle);
            }
        }
    }

    /// Update equipment connection effect
    fn update_equipment_connection_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::EquipmentConnection {
            connection_strength,
            data_flow,
            ..
        } = &mut effect.data
        {
            // Create flowing connection effect
            let flow_intensity = *data_flow * *connection_strength;

            // Emit connection particles
            if self.config.enable_particles {
                let particle = Particle {
                    position: effect.position,
                    velocity: Vector3D::new(flow_intensity, 0.0, 0.0),
                    acceleration: Vector3D::zero(),
                    lifetime: 1.0,
                    max_lifetime: 2.0,
                    size: *connection_strength,
                    character: '→',
                    particle_type: ParticleType::Connection,
                    data: ParticleData::Connection {
                        source_id: "source".to_string(),
                        target_id: "target".to_string(),
                        connection_strength: *connection_strength,
                    },
                };

                self.particle_system.emit_particle(particle);
            }
        }
    }

    /// Update selection highlight effect
    fn update_selection_highlight_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::SelectionHighlight {
            highlight_color,
            pulse_intensity,
            ..
        } = &mut effect.data
        {
            // Create pulsing highlight effect
            let pulse = (effect.intensity * *pulse_intensity).sin().abs();

            // Emit highlight particles
            if self.config.enable_particles {
                let particle = Particle {
                    position: effect.position,
                    velocity: Vector3D::zero(),
                    acceleration: Vector3D::zero(),
                    lifetime: 1.0,
                    max_lifetime: 1.0,
                    size: pulse,
                    character: *highlight_color,
                    particle_type: ParticleType::StatusIndicator,
                    data: ParticleData::StatusIndicator {
                        equipment_id: "selection".to_string(),
                        status_type: StatusType::Healthy,
                    },
                };

                self.particle_system.emit_particle(particle);
            }
        }
    }

    /// Update floor transition effect
    fn update_floor_transition_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::FloorTransition {
            transition_speed, ..
        } = &mut effect.data
        {
            // Create floor transition particles
            if self.config.enable_particles {
                for i in 0..10 {
                    let particle = Particle {
                        position: Point3D::new(
                            effect.position.x + (i as f64 - 5.0) * 2.0,
                            effect.position.y,
                            effect.position.z,
                        ),
                        velocity: Vector3D::new(0.0, *transition_speed, 0.0),
                        acceleration: Vector3D::zero(),
                        lifetime: 1.0,
                        max_lifetime: 2.0,
                        size: 1.0,
                        character: '│',
                        particle_type: ParticleType::Basic,
                        data: ParticleData::Basic {
                            color_intensity: 1.0,
                        },
                    };

                    self.particle_system.emit_particle(particle);
                }
            }
        }
    }

    /// Update view mode transition effect
    fn update_view_mode_transition_effect(&mut self, effect: &mut VisualEffect) {
        // Create view mode transition particles
        if self.config.enable_particles {
            let particle = Particle {
                position: effect.position,
                velocity: Vector3D::zero(),
                acceleration: Vector3D::zero(),
                lifetime: 1.0,
                max_lifetime: 1.0,
                size: effect.intensity,
                character: '✨',
                particle_type: ParticleType::Basic,
                data: ParticleData::Basic {
                    color_intensity: effect.intensity,
                },
            };

            self.particle_system.emit_particle(particle);
        }
    }

    /// Update particle burst effect
    fn update_particle_burst_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::ParticleBurst {
            particle_count,
            burst_radius: _,
            particle_type,
        } = &mut effect.data
        {
            // Create burst effect
            self.particle_system.create_burst(
                effect.position,
                *particle_count,
                particle_type.clone(),
            );

            effect.state = EffectState::Completed;
        }
    }

    /// Update smoke effect
    fn update_smoke_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::SmokeEffect {
            smoke_intensity,
            temperature,
            wind_direction,
        } = &mut effect.data
        {
            // Create smoke particles
            if self.config.enable_particles {
                let particle = Particle {
                    position: effect.position,
                    velocity: Vector3D::new(
                        wind_direction.x * *smoke_intensity,
                        wind_direction.y * *smoke_intensity + 0.5,
                        wind_direction.z * *smoke_intensity,
                    ),
                    acceleration: Vector3D::zero(),
                    lifetime: 1.0,
                    max_lifetime: 3.0,
                    size: *smoke_intensity,
                    character: '~',
                    particle_type: ParticleType::Smoke,
                    data: ParticleData::Smoke {
                        opacity: *smoke_intensity,
                        temperature: *temperature,
                    },
                };

                self.particle_system.emit_particle(particle);
            }
        }
    }

    /// Update fire effect
    fn update_fire_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::FireEffect {
            fire_intensity,
            temperature: _,
            flicker_rate,
        } = &mut effect.data
        {
            // Create fire particles
            if self.config.enable_particles {
                let particle = Particle {
                    position: effect.position,
                    velocity: Vector3D::new(0.0, 0.3, 0.0),
                    acceleration: Vector3D::zero(),
                    lifetime: 1.0,
                    max_lifetime: 1.5,
                    size: *fire_intensity,
                    character: '^',
                    particle_type: ParticleType::Fire,
                    data: ParticleData::Fire {
                        intensity: *fire_intensity,
                        flicker_rate: *flicker_rate,
                    },
                };

                self.particle_system.emit_particle(particle);
            }
        }
    }

    /// Update spark effect
    fn update_spark_effect(&mut self, effect: &mut VisualEffect) {
        if let EffectData::SparkEffect {
            spark_count,
            energy_level,
            ..
        } = &mut effect.data
        {
            // Create spark particles
            if self.config.enable_particles {
                for i in 0..*spark_count {
                    let angle = (i as f64 / *spark_count as f64) * 2.0 * std::f64::consts::PI;
                    let speed = *energy_level * 2.0;

                    let particle = Particle {
                        position: effect.position,
                        velocity: Vector3D::new(angle.cos() * speed, 0.0, angle.sin() * speed),
                        acceleration: Vector3D::zero(),
                        lifetime: 1.0,
                        max_lifetime: 1.0,
                        size: *energy_level,
                        character: '*',
                        particle_type: ParticleType::Spark,
                        data: ParticleData::Spark {
                            energy: *energy_level,
                            trail_length: 3,
                        },
                    };

                    self.particle_system.emit_particle(particle);
                }
            }
        }
    }

    /// Create a new visual effect
    pub fn create_effect(&mut self, effect: VisualEffect) -> Result<(), String> {
        if self.active_effects.len() >= self.config.max_effects {
            return Err("Maximum effect limit reached".to_string());
        }

        let id = effect.id.clone();
        self.active_effects.insert(id, effect);
        self.stats.effects_created += 1;

        Ok(())
    }

    /// Create equipment status effect
    pub fn create_equipment_status_effect(
        &mut self,
        id: String,
        equipment_id: String,
        status: EquipmentStatus,
        position: Point3D,
    ) -> Result<(), String> {
        let effect = VisualEffect {
            id,
            effect_type: EffectType::EquipmentStatus,
            state: EffectState::Active,
            duration: Some(std::time::Duration::from_secs(5)),
            intensity: 1.0,
            position,
            data: EffectData::EquipmentStatus {
                equipment_id,
                status,
                pulse_rate: 4.0,
                color_intensity: 1.0,
            },
        };

        self.create_effect(effect)
    }

    /// Create maintenance alert effect
    pub fn create_maintenance_alert_effect(
        &mut self,
        id: String,
        equipment_id: String,
        alert_level: AlertLevel,
        position: Point3D,
    ) -> Result<(), String> {
        let effect = VisualEffect {
            id,
            effect_type: EffectType::MaintenanceAlert,
            state: EffectState::Active,
            duration: Some(std::time::Duration::from_secs(10)),
            intensity: 1.0,
            position,
            data: EffectData::MaintenanceAlert {
                equipment_id,
                alert_level,
                urgency: 1.0,
            },
        };

        self.create_effect(effect)
    }

    /// Create particle burst effect
    pub fn create_particle_burst_effect(
        &mut self,
        id: String,
        position: Point3D,
        particle_type: ParticleType,
        count: usize,
    ) -> Result<(), String> {
        let effect = VisualEffect {
            id,
            effect_type: EffectType::ParticleBurst,
            state: EffectState::Active,
            duration: Some(std::time::Duration::from_millis(100)),
            intensity: 1.0,
            position,
            data: EffectData::ParticleBurst {
                particle_count: count,
                burst_radius: 5.0,
                particle_type,
            },
        };

        self.create_effect(effect)
    }

    /// Get particle system
    pub fn particle_system(&self) -> &ParticleSystem {
        &self.particle_system
    }

    /// Get mutable particle system
    pub fn particle_system_mut(&mut self) -> &mut ParticleSystem {
        &mut self.particle_system
    }

    /// Get animation system
    pub fn animation_system(&self) -> &AnimationSystem {
        &self.animation_system
    }

    /// Get mutable animation system
    pub fn animation_system_mut(&mut self) -> &mut AnimationSystem {
        &mut self.animation_system
    }

    /// Get all active effects
    pub fn active_effects(&self) -> &HashMap<String, VisualEffect> {
        &self.active_effects
    }

    /// Get system statistics
    pub fn stats(&self) -> &EffectsStats {
        &self.stats
    }

    /// Get system configuration
    pub fn config(&self) -> &EffectsConfig {
        &self.config
    }

    /// Update configuration
    pub fn update_config(&mut self, config: EffectsConfig) {
        self.config = config;
    }

    /// Clear all effects
    pub fn clear(&mut self) {
        self.active_effects.clear();
        self.particle_system.clear();
        self.animation_system.clear();
    }

    /// Get effect count
    pub fn effect_count(&self) -> usize {
        self.active_effects.len()
    }

    /// Update system statistics
    fn update_stats(&mut self, start_time: std::time::Instant, delta_time: f64) {
        let update_duration = start_time.elapsed();
        self.stats.avg_update_time_ms = update_duration.as_secs_f64() * 1000.0;
        self.stats.active_effects = self.active_effects.len();
        self.stats.fps = 1.0 / delta_time;

        // Update peak count
        if self.active_effects.len() > self.stats.peak_effect_count {
            self.stats.peak_effect_count = self.active_effects.len();
        }
    }
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_visual_effects_engine_creation() {
        let engine = VisualEffectsEngine::new();
        assert_eq!(engine.effect_count(), 0);
        assert_eq!(engine.config.max_effects, 50);
    }

    #[test]
    fn test_equipment_status_effect() {
        let mut engine = VisualEffectsEngine::new();

        let result = engine.create_equipment_status_effect(
            "test_status".to_string(),
            "equipment_1".to_string(),
            EquipmentStatus::Healthy,
            Point3D::new(0.0, 0.0, 0.0),
        );

        assert!(result.is_ok());
        assert_eq!(engine.effect_count(), 1);
    }

    #[test]
    fn test_maintenance_alert_effect() {
        let mut engine = VisualEffectsEngine::new();

        let result = engine.create_maintenance_alert_effect(
            "test_alert".to_string(),
            "equipment_1".to_string(),
            AlertLevel::High,
            Point3D::new(0.0, 0.0, 0.0),
        );

        assert!(result.is_ok());
        assert_eq!(engine.effect_count(), 1);
    }

    #[test]
    fn test_particle_burst_effect() {
        let mut engine = VisualEffectsEngine::new();

        let result = engine.create_particle_burst_effect(
            "test_burst".to_string(),
            Point3D::new(0.0, 0.0, 0.0),
            ParticleType::Spark,
            10,
        );

        assert!(result.is_ok());
        assert_eq!(engine.effect_count(), 1);
    }

    #[test]
    fn test_effects_update() {
        let mut engine = VisualEffectsEngine::new();

        engine
            .create_equipment_status_effect(
                "test_status".to_string(),
                "equipment_1".to_string(),
                EquipmentStatus::Healthy,
                Point3D::new(0.0, 0.0, 0.0),
            )
            .unwrap();

        // Update with 16ms delta time (60 FPS)
        engine.update(0.016);

        // Effect should still be active
        assert_eq!(engine.effect_count(), 1);
    }

    #[test]
    fn test_effect_types() {
        let status_effect = EffectType::EquipmentStatus;
        let alert_effect = EffectType::MaintenanceAlert;
        let burst_effect = EffectType::ParticleBurst;

        assert!(matches!(status_effect, EffectType::EquipmentStatus));
        assert!(matches!(alert_effect, EffectType::MaintenanceAlert));
        assert!(matches!(burst_effect, EffectType::ParticleBurst));
    }
}
