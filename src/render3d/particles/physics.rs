//! Physics simulation for particle system
//!
//! This module provides physics update methods for different particle types,
//! including gravity, air resistance, and type-specific behaviors.

use super::types::*;

/// Update a single particle's physics
///
/// # Arguments
/// * `particle` - The particle to update
/// * `delta_time` - Time elapsed since last update
/// * `config` - Particle system configuration
pub fn update_particle(particle: &mut Particle, delta_time: f64, config: &ParticleSystemConfig) {
    if !config.enable_physics {
        return;
    }

    // Apply physics based on particle type
    match particle.particle_type {
        ParticleType::Basic => update_basic_particle(particle, delta_time, config),
        ParticleType::Smoke => update_smoke_particle(particle, delta_time, config),
        ParticleType::Fire => update_fire_particle(particle, delta_time, config),
        ParticleType::Spark => update_spark_particle(particle, delta_time, config),
        ParticleType::Dust => update_dust_particle(particle, delta_time, config),
        ParticleType::StatusIndicator => update_status_particle(particle, delta_time, config),
        ParticleType::Connection => update_connection_particle(particle, delta_time, config),
        ParticleType::MaintenanceAlert => update_maintenance_particle(particle, delta_time, config),
    }

    // Update lifetime
    particle.lifetime -= delta_time / particle.max_lifetime;

    // Update position based on velocity
    particle.position.x += particle.velocity.x * delta_time;
    particle.position.y += particle.velocity.y * delta_time;
    particle.position.z += particle.velocity.z * delta_time;

    // Update velocity based on acceleration
    particle.velocity.x += particle.acceleration.x * delta_time;
    particle.velocity.y += particle.acceleration.y * delta_time;
    particle.velocity.z += particle.acceleration.z * delta_time;

    // Apply air resistance
    let resistance = 1.0 - (config.air_resistance * delta_time);
    particle.velocity.x *= resistance;
    particle.velocity.y *= resistance;
    particle.velocity.z *= resistance;
}

/// Update basic particle physics
///
/// # Arguments
/// * `particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `config` - Particle system configuration
pub fn update_basic_particle(
    particle: &mut Particle,
    _delta_time: f64,
    config: &ParticleSystemConfig,
) {
    // Apply gravity
    particle.acceleration.y -= config.gravity;
}

/// Update smoke particle physics
///
/// # Arguments
/// * `particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `_config` - Particle system configuration
pub fn update_smoke_particle(
    particle: &mut Particle,
    _delta_time: f64,
    _config: &ParticleSystemConfig,
) {
    // Smoke rises and spreads
    particle.acceleration.y += 2.0; // Upward force
    particle.acceleration.x += (particle.lifetime - 0.5) * 0.5; // Horizontal drift

    // Update smoke-specific data
    if let ParticleData::Smoke {
        opacity,
        temperature,
    } = &mut particle.data
    {
        *opacity *= 0.98; // Fade out over time
        *temperature *= 0.99; // Cool down
    }
}

/// Update fire particle physics
///
/// # Arguments
/// * `particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `_config` - Particle system configuration
pub fn update_fire_particle(
    particle: &mut Particle,
    _delta_time: f64,
    _config: &ParticleSystemConfig,
) {
    // Fire flickers and moves upward
    particle.acceleration.y += 1.5;

    // Random flicker
    let flicker = (particle.lifetime * 10.0).sin() * 0.3;
    particle.acceleration.x += flicker;
    particle.acceleration.z += flicker * 0.5;

    // Update fire-specific data
    if let ParticleData::Fire {
        intensity,
        flicker_rate,
    } = &mut particle.data
    {
        *intensity = (particle.lifetime * *flicker_rate).sin().abs();
    }
}

/// Update spark particle physics
///
/// # Arguments
/// * `particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `config` - Particle system configuration
pub fn update_spark_particle(
    particle: &mut Particle,
    _delta_time: f64,
    config: &ParticleSystemConfig,
) {
    // Sparks move randomly and lose energy
    let random_x = (particle.lifetime * 15.0).sin() * 2.0;
    let random_z = (particle.lifetime * 12.0).cos() * 1.5;

    particle.acceleration.x += random_x;
    particle.acceleration.z += random_z;

    // Apply gravity
    particle.acceleration.y -= config.gravity * 0.5;

    // Update spark-specific data
    if let ParticleData::Spark { energy, .. } = &mut particle.data {
        *energy *= 0.95; // Lose energy over time
    }
}

/// Update dust particle physics
///
/// # Arguments
/// * `particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `config` - Particle system configuration
pub fn update_dust_particle(
    particle: &mut Particle,
    _delta_time: f64,
    config: &ParticleSystemConfig,
) {
    // Dust falls slowly with gravity
    particle.acceleration.y -= config.gravity * 0.3;

    // Slight horizontal drift
    particle.acceleration.x += (particle.lifetime - 0.5) * 0.1;
}

/// Update status indicator particle
///
/// # Arguments
/// * `particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `_config` - Particle system configuration
pub fn update_status_particle(
    particle: &mut Particle,
    _delta_time: f64,
    _config: &ParticleSystemConfig,
) {
    // Status indicators pulse
    let pulse = (particle.lifetime * 8.0).sin() * 0.2;
    particle.size = 1.0 + pulse;
}

/// Update connection particle
///
/// # Arguments
/// * `_particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `_config` - Particle system configuration
pub fn update_connection_particle(
    _particle: &mut Particle,
    _delta_time: f64,
    _config: &ParticleSystemConfig,
) {
    // Connection particles flow along the connection
    // This would be updated based on actual connection data
}

/// Update maintenance alert particle
///
/// # Arguments
/// * `particle` - The particle to update
/// * `_delta_time` - Time elapsed since last update
/// * `_config` - Particle system configuration
pub fn update_maintenance_particle(
    particle: &mut Particle,
    _delta_time: f64,
    _config: &ParticleSystemConfig,
) {
    // Maintenance alerts blink
    let blink = (particle.lifetime * 6.0).sin() > 0.0;
    if blink {
        particle.character = '!';
    } else {
        particle.character = ' ';
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::spatial::Point3D;

    #[test]
    fn test_basic_particle_physics() {
        let mut particle = Particle {
            position: Point3D::new(0.0, 10.0, 0.0),
            velocity: Vector3D::zero(),
            acceleration: Vector3D::zero(),
            lifetime: 1.0,
            max_lifetime: 2.0,
            size: 1.0,
            character: '•',
            particle_type: ParticleType::Basic,
            data: ParticleData::Basic {
                color_intensity: 1.0,
            },
        };

        let config = ParticleSystemConfig::default();
        update_basic_particle(&mut particle, 0.1, &config);

        // Should have negative y acceleration due to gravity
        assert!(particle.acceleration.y < 0.0);
    }

    #[test]
    fn test_smoke_particle_rises() {
        let mut particle = Particle {
            position: Point3D::new(0.0, 0.0, 0.0),
            velocity: Vector3D::zero(),
            acceleration: Vector3D::zero(),
            lifetime: 1.0,
            max_lifetime: 2.0,
            size: 1.0,
            character: '~',
            particle_type: ParticleType::Smoke,
            data: ParticleData::Smoke {
                opacity: 1.0,
                temperature: 100.0,
            },
        };

        let config = ParticleSystemConfig::default();
        update_smoke_particle(&mut particle, 0.1, &config);

        // Should have positive y acceleration (rises)
        assert!(particle.acceleration.y > 0.0);
    }

    #[test]
    fn test_particle_position_update() {
        let mut particle = Particle {
            position: Point3D::new(0.0, 0.0, 0.0),
            velocity: Vector3D::new(1.0, 2.0, 3.0),
            acceleration: Vector3D::zero(),
            lifetime: 1.0,
            max_lifetime: 2.0,
            size: 1.0,
            character: '•',
            particle_type: ParticleType::Basic,
            data: ParticleData::Basic {
                color_intensity: 1.0,
            },
        };

        let config = ParticleSystemConfig::default();
        let initial_pos = particle.position;
        update_particle(&mut particle, 1.0, &config);

        // Position should change based on velocity
        assert_ne!(particle.position.x, initial_pos.x);
        assert_ne!(particle.position.y, initial_pos.y);
        assert_ne!(particle.position.z, initial_pos.z);
    }

    #[test]
    fn test_lifetime_decrease() {
        let mut particle = Particle {
            position: Point3D::new(0.0, 0.0, 0.0),
            velocity: Vector3D::zero(),
            acceleration: Vector3D::zero(),
            lifetime: 1.0,
            max_lifetime: 1.0,
            size: 1.0,
            character: '•',
            particle_type: ParticleType::Basic,
            data: ParticleData::Basic {
                color_intensity: 1.0,
            },
        };

        let config = ParticleSystemConfig::default();
        let initial_lifetime = particle.lifetime;
        update_particle(&mut particle, 0.5, &config);

        // Lifetime should decrease
        assert!(particle.lifetime < initial_lifetime);
    }
}
