//! Particle emission and creation functions
//!
//! This module provides factory methods for creating particles and
//! emission patterns like bursts and continuous streams.

use super::types::*;
use crate::core::spatial::Point3D;

/// Create particle data based on particle type
///
/// # Arguments
/// * `particle_type` - The type of particle to create data for
///
/// # Returns
/// Initialized ParticleData for the given type
pub fn create_particle_data(particle_type: &ParticleType) -> ParticleData {
    match particle_type {
        ParticleType::Basic => ParticleData::Basic {
            color_intensity: 1.0,
        },
        ParticleType::Smoke => ParticleData::Smoke {
            opacity: 1.0,
            temperature: 100.0,
        },
        ParticleType::Fire => ParticleData::Fire {
            intensity: 1.0,
            flicker_rate: 8.0,
        },
        ParticleType::Spark => ParticleData::Spark {
            energy: 1.0,
            trail_length: 3,
        },
        ParticleType::Dust => ParticleData::Dust {
            mass: 0.1,
            static_charge: 0.0,
        },
        ParticleType::StatusIndicator => ParticleData::StatusIndicator {
            equipment_id: "unknown".to_string(),
            status_type: StatusType::Healthy,
        },
        ParticleType::Connection => ParticleData::Connection {
            source_id: "unknown".to_string(),
            target_id: "unknown".to_string(),
            connection_strength: 1.0,
        },
        ParticleType::MaintenanceAlert => ParticleData::MaintenanceAlert {
            alert_level: AlertLevel::Medium,
            equipment_id: "unknown".to_string(),
        },
    }
}

/// Create a particle burst effect
///
/// # Arguments
/// * `position` - The origin point for the burst
/// * `count` - Number of particles to create
/// * `particle_type` - Type of particles to emit
///
/// # Returns
/// Vector of particles arranged in a circular burst pattern
pub fn create_burst(position: Point3D, count: usize, particle_type: ParticleType) -> Vec<Particle> {
    let mut particles = Vec::with_capacity(count);

    for i in 0..count {
        let angle = (i as f64 / count as f64) * 2.0 * std::f64::consts::PI;
        let speed = 2.0 + (i as f64 * 0.1);

        let particle = Particle {
            position,
            velocity: Vector3D {
                x: angle.cos() * speed,
                y: 0.0,
                z: angle.sin() * speed,
            },
            acceleration: Vector3D::zero(),
            lifetime: 1.0,
            max_lifetime: 2.0,
            size: 1.0,
            character: get_particle_character(&particle_type),
            particle_type: particle_type.clone(),
            data: create_particle_data(&particle_type),
        };

        particles.push(particle);
    }

    particles
}

/// Get the default character for a particle type
///
/// # Arguments
/// * `particle_type` - The particle type
///
/// # Returns
/// Character to use for rendering this particle type
pub fn get_particle_character(particle_type: &ParticleType) -> char {
    match particle_type {
        ParticleType::Spark => '*',
        ParticleType::Fire => '^',
        ParticleType::Smoke => '~',
        ParticleType::Dust => '.',
        ParticleType::StatusIndicator => '○',
        ParticleType::Connection => '-',
        ParticleType::MaintenanceAlert => '!',
        ParticleType::Basic => '•',
    }
}

/// Create a smoke emitter particle stream
///
/// # Arguments
/// * `position` - Emission point
/// * `intensity` - Emission intensity (0.0 to 1.0)
///
/// # Returns
/// Single smoke particle
pub fn create_smoke_particle(position: Point3D, intensity: f64) -> Particle {
    Particle {
        position,
        velocity: Vector3D {
            x: (intensity * 2.0 - 1.0) * 0.5,
            y: intensity * 2.0,
            z: (intensity * 2.0 - 1.0) * 0.3,
        },
        acceleration: Vector3D::zero(),
        lifetime: 1.0,
        max_lifetime: 3.0,
        size: 1.0,
        character: '~',
        particle_type: ParticleType::Smoke,
        data: ParticleData::Smoke {
            opacity: intensity,
            temperature: 100.0 * intensity,
        },
    }
}

/// Create a fire particle
///
/// # Arguments
/// * `position` - Emission point
/// * `intensity` - Fire intensity (0.0 to 1.0)
///
/// # Returns
/// Single fire particle
pub fn create_fire_particle(position: Point3D, intensity: f64) -> Particle {
    Particle {
        position,
        velocity: Vector3D {
            x: (intensity - 0.5) * 0.5,
            y: intensity * 3.0,
            z: (intensity - 0.5) * 0.3,
        },
        acceleration: Vector3D::zero(),
        lifetime: 1.0,
        max_lifetime: 1.5,
        size: 1.0,
        character: '^',
        particle_type: ParticleType::Fire,
        data: ParticleData::Fire {
            intensity,
            flicker_rate: 8.0,
        },
    }
}

/// Create a spark particle
///
/// # Arguments
/// * `position` - Emission point
/// * `direction` - Initial direction vector
///
/// # Returns
/// Single spark particle
pub fn create_spark_particle(position: Point3D, direction: Vector3D) -> Particle {
    let normalized_dir = direction.normalize();

    Particle {
        position,
        velocity: Vector3D {
            x: normalized_dir.x * 5.0,
            y: normalized_dir.y * 5.0,
            z: normalized_dir.z * 5.0,
        },
        acceleration: Vector3D::zero(),
        lifetime: 1.0,
        max_lifetime: 1.0,
        size: 1.0,
        character: '*',
        particle_type: ParticleType::Spark,
        data: ParticleData::Spark {
            energy: 1.0,
            trail_length: 5,
        },
    }
}

/// Create a status indicator particle
///
/// # Arguments
/// * `position` - Position above equipment
/// * `equipment_id` - ID of the equipment
/// * `status_type` - Status to indicate
///
/// # Returns
/// Single status indicator particle
pub fn create_status_indicator(
    position: Point3D,
    equipment_id: String,
    status_type: StatusType,
) -> Particle {
    Particle {
        position,
        velocity: Vector3D::zero(),
        acceleration: Vector3D::zero(),
        lifetime: 1.0,
        max_lifetime: f64::INFINITY, // Status indicators persist
        size: 1.0,
        character: '○',
        particle_type: ParticleType::StatusIndicator,
        data: ParticleData::StatusIndicator {
            equipment_id,
            status_type,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_particle_data() {
        let basic_data = create_particle_data(&ParticleType::Basic);
        assert!(matches!(basic_data, ParticleData::Basic { .. }));

        let smoke_data = create_particle_data(&ParticleType::Smoke);
        assert!(matches!(smoke_data, ParticleData::Smoke { .. }));
    }

    #[test]
    fn test_create_burst() {
        let position = Point3D::new(0.0, 0.0, 0.0);
        let particles = create_burst(position, 10, ParticleType::Spark);

        assert_eq!(particles.len(), 10);
        assert!(particles.iter().all(|p| p.particle_type == ParticleType::Spark));
    }

    #[test]
    fn test_get_particle_character() {
        assert_eq!(get_particle_character(&ParticleType::Spark), '*');
        assert_eq!(get_particle_character(&ParticleType::Fire), '^');
        assert_eq!(get_particle_character(&ParticleType::Smoke), '~');
    }

    #[test]
    fn test_create_smoke_particle() {
        let position = Point3D::new(5.0, 5.0, 5.0);
        let particle = create_smoke_particle(position, 0.8);

        assert_eq!(particle.particle_type, ParticleType::Smoke);
        assert_eq!(particle.character, '~');
        assert!(matches!(particle.data, ParticleData::Smoke { .. }));
    }

    #[test]
    fn test_create_fire_particle() {
        let position = Point3D::new(0.0, 0.0, 0.0);
        let particle = create_fire_particle(position, 1.0);

        assert_eq!(particle.particle_type, ParticleType::Fire);
        assert_eq!(particle.character, '^');
    }

    #[test]
    fn test_create_spark_particle() {
        let position = Point3D::new(0.0, 0.0, 0.0);
        let direction = Vector3D::new(1.0, 1.0, 0.0);
        let particle = create_spark_particle(position, direction);

        assert_eq!(particle.particle_type, ParticleType::Spark);
        assert_eq!(particle.character, '*');
    }

    #[test]
    fn test_create_status_indicator() {
        let position = Point3D::new(10.0, 10.0, 10.0);
        let particle = create_status_indicator(
            position,
            "equipment_1".to_string(),
            StatusType::Warning,
        );

        assert_eq!(particle.particle_type, ParticleType::StatusIndicator);
        assert!(particle.max_lifetime.is_infinite());
    }
}
