//! Visual effect type definitions
//!
//! This module contains all type definitions for visual effects including
//! effect types, states, data structures, and the core VisualEffect struct.

use crate::render3d::animation::EquipmentStatus;
use crate::render3d::particles::{AlertLevel, ParticleType, Vector3D};
use crate::core::spatial::Point3D;

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
