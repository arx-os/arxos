//! Type definitions for the particle system
//!
//! This module contains all data structures, enums, and type definitions
//! used throughout the particle system framework.

use crate::core::spatial::Point3D;
use std::time::Duration;

/// Individual particle with physics and rendering properties
#[derive(Debug, Clone)]
pub struct Particle {
    /// Position in 3D space
    pub position: Point3D,
    /// Velocity vector
    pub velocity: Vector3D,
    /// Acceleration vector
    pub acceleration: Vector3D,
    /// Particle lifetime (0.0 to 1.0)
    pub lifetime: f64,
    /// Maximum lifetime
    pub max_lifetime: f64,
    /// Particle size
    pub size: f64,
    /// Particle color/character
    pub character: char,
    /// Particle type for different behaviors
    pub particle_type: ParticleType,
    /// Custom data for specific particle types
    pub data: ParticleData,
}

/// 3D vector for particle physics
#[derive(Debug, Clone)]
pub struct Vector3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

impl Vector3D {
    /// Create a new 3D vector
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }

    /// Create zero vector
    pub fn zero() -> Self {
        Self::new(0.0, 0.0, 0.0)
    }

    /// Calculate vector length
    pub fn length(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    /// Normalize vector to unit length
    pub fn normalize(&self) -> Self {
        let len = self.length();
        if len > 0.0 {
            Self::new(self.x / len, self.y / len, self.z / len)
        } else {
            Self::zero()
        }
    }
}

/// Different types of particles with specific behaviors
#[derive(Debug, Clone, PartialEq)]
pub enum ParticleType {
    /// Basic particle with simple physics
    Basic,
    /// Smoke particle with upward drift
    Smoke,
    /// Fire particle with flickering
    Fire,
    /// Spark particle with random movement
    Spark,
    /// Dust particle with gravity
    Dust,
    /// Equipment status indicator
    StatusIndicator,
    /// Connection line particle
    Connection,
    /// Maintenance alert particle
    MaintenanceAlert,
}

/// Custom data for different particle types
#[derive(Debug, Clone)]
pub enum ParticleData {
    /// Basic particle data
    Basic { color_intensity: f64 },
    /// Smoke particle data
    Smoke { opacity: f64, temperature: f64 },
    /// Fire particle data
    Fire { intensity: f64, flicker_rate: f64 },
    /// Spark particle data
    Spark { energy: f64, trail_length: usize },
    /// Dust particle data
    Dust { mass: f64, static_charge: f64 },
    /// Status indicator data
    StatusIndicator {
        equipment_id: String,
        status_type: StatusType,
    },
    /// Connection particle data
    Connection {
        source_id: String,
        target_id: String,
        connection_strength: f64,
    },
    /// Maintenance alert data
    MaintenanceAlert {
        alert_level: AlertLevel,
        equipment_id: String,
    },
}

/// Equipment status types for status indicator particles
#[derive(Debug, Clone, PartialEq)]
pub enum StatusType {
    Healthy,
    Warning,
    Critical,
    Maintenance,
    Offline,
}

/// Alert levels for maintenance particles
#[derive(Debug, Clone, PartialEq)]
pub enum AlertLevel {
    Low,
    Medium,
    High,
    Critical,
}

/// Particle system configuration
#[derive(Debug, Clone)]
pub struct ParticleSystemConfig {
    /// Maximum number of active particles
    pub max_particles: usize,
    /// Global gravity force
    pub gravity: f64,
    /// Air resistance coefficient
    pub air_resistance: f64,
    /// Enable particle pooling for performance
    pub enable_pooling: bool,
    /// Target update frequency (Hz)
    pub target_fps: u32,
    /// Enable physics simulation
    pub enable_physics: bool,
    /// Enable particle trails
    pub enable_trails: bool,
    /// Trail length for particles
    pub trail_length: usize,
}

impl Default for ParticleSystemConfig {
    fn default() -> Self {
        Self {
            max_particles: 1000,
            gravity: 9.8,
            air_resistance: 0.1,
            enable_pooling: true,
            target_fps: 60,
            enable_physics: true,
            enable_trails: true,
            trail_length: 5,
        }
    }
}

/// Particle system performance statistics
#[derive(Debug, Clone)]
pub struct ParticleSystemStats {
    /// Total particles created
    pub particles_created: u64,
    /// Total particles destroyed
    pub particles_destroyed: u64,
    /// Current active particle count
    pub active_particles: usize,
    /// Average update time per frame
    pub avg_update_time_ms: f64,
    /// Peak particle count
    pub peak_particle_count: usize,
    /// Frame rate
    pub fps: f64,
}

impl ParticleSystemStats {
    /// Create new statistics
    pub fn new() -> Self {
        Self {
            particles_created: 0,
            particles_destroyed: 0,
            active_particles: 0,
            avg_update_time_ms: 0.0,
            peak_particle_count: 0,
            fps: 0.0,
        }
    }
}

impl Default for ParticleSystemStats {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vector_creation() {
        let vector = Vector3D::new(1.0, 2.0, 3.0);
        assert_eq!(vector.x, 1.0);
        assert_eq!(vector.y, 2.0);
        assert_eq!(vector.z, 3.0);
    }

    #[test]
    fn test_vector_operations() {
        let vector = Vector3D::new(3.0, 4.0, 0.0);
        assert_eq!(vector.length(), 5.0);

        let normalized = vector.normalize();
        assert!((normalized.length() - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_vector_zero() {
        let zero = Vector3D::zero();
        assert_eq!(zero.x, 0.0);
        assert_eq!(zero.y, 0.0);
        assert_eq!(zero.z, 0.0);
        assert_eq!(zero.length(), 0.0);
    }

    #[test]
    fn test_particle_types() {
        let basic_data = ParticleData::Basic {
            color_intensity: 1.0,
        };
        let smoke_data = ParticleData::Smoke {
            opacity: 0.8,
            temperature: 50.0,
        };

        assert!(matches!(basic_data, ParticleData::Basic { .. }));
        assert!(matches!(smoke_data, ParticleData::Smoke { .. }));
    }

    #[test]
    fn test_config_default() {
        let config = ParticleSystemConfig::default();
        assert_eq!(config.max_particles, 1000);
        assert_eq!(config.target_fps, 60);
        assert!(config.enable_physics);
    }

    #[test]
    fn test_stats_creation() {
        let stats = ParticleSystemStats::new();
        assert_eq!(stats.particles_created, 0);
        assert_eq!(stats.active_particles, 0);
        assert_eq!(stats.fps, 0.0);
    }
}
