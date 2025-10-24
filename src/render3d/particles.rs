//! Particle System for Terminal Rendering
//!
//! This module provides a high-performance particle system optimized for terminal rendering,
//! including particle lifecycle management, physics simulation, and visual effects.

use crate::spatial::Point3D;
use std::collections::VecDeque;
use std::time::Instant;

/// Particle system for terminal-based visual effects
pub struct ParticleSystem {
    /// Active particles
    particles: Vec<Particle>,
    /// Particle pool for reuse
    particle_pool: VecDeque<Particle>,
    /// System configuration
    config: ParticleSystemConfig,
    /// Performance statistics
    stats: ParticleSystemStats,
    /// Last update time
    last_update: Instant,
}

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
    Basic {
        color_intensity: f64,
    },
    /// Smoke particle data
    Smoke {
        opacity: f64,
        temperature: f64,
    },
    /// Fire particle data
    Fire {
        intensity: f64,
        flicker_rate: f64,
    },
    /// Spark particle data
    Spark {
        energy: f64,
        trail_length: usize,
    },
    /// Dust particle data
    Dust {
        mass: f64,
        static_charge: f64,
    },
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

impl ParticleSystem {
    /// Create a new particle system with default configuration
    pub fn new() -> Self {
        Self::with_config(ParticleSystemConfig::default())
    }

    /// Create particle system with custom configuration
    pub fn with_config(config: ParticleSystemConfig) -> Self {
        Self {
            particles: Vec::with_capacity(config.max_particles),
            particle_pool: VecDeque::with_capacity(config.max_particles),
            config,
            stats: ParticleSystemStats::new(),
            last_update: Instant::now(),
        }
    }

    /// Update all particles (call this every frame)
    pub fn update(&mut self, delta_time: f64) {
        let start_time = Instant::now();
        
        // Update each particle
        let mut particles_to_update = Vec::new();
        
        // Collect particles that need updating
        for (i, particle) in self.particles.iter().enumerate() {
            particles_to_update.push((i, particle.clone()));
        }
        
        // Update particles
        for (i, mut particle) in particles_to_update {
            self.update_particle(&mut particle, delta_time);
            self.particles[i] = particle;
        }
        
        // Remove dead particles
        self.remove_dead_particles();
        
        // Update statistics
        self.update_stats(start_time, delta_time);
    }

    /// Update a single particle
    fn update_particle(&mut self, particle: &mut Particle, delta_time: f64) {
        if !self.config.enable_physics {
            return;
        }

        // Apply physics based on particle type
        match particle.particle_type {
            ParticleType::Basic => self.update_basic_particle(particle, delta_time),
            ParticleType::Smoke => self.update_smoke_particle(particle, delta_time),
            ParticleType::Fire => self.update_fire_particle(particle, delta_time),
            ParticleType::Spark => self.update_spark_particle(particle, delta_time),
            ParticleType::Dust => self.update_dust_particle(particle, delta_time),
            ParticleType::StatusIndicator => self.update_status_particle(particle, delta_time),
            ParticleType::Connection => self.update_connection_particle(particle, delta_time),
            ParticleType::MaintenanceAlert => self.update_maintenance_particle(particle, delta_time),
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
        let resistance = 1.0 - (self.config.air_resistance * delta_time);
        particle.velocity.x *= resistance;
        particle.velocity.y *= resistance;
        particle.velocity.z *= resistance;
    }

    /// Update basic particle physics
    fn update_basic_particle(&mut self, particle: &mut Particle, _delta_time: f64) {
        // Apply gravity
        particle.acceleration.y -= self.config.gravity;
    }

    /// Update smoke particle physics
    fn update_smoke_particle(&mut self, particle: &mut Particle, _delta_time: f64) {
        // Smoke rises and spreads
        particle.acceleration.y += 2.0; // Upward force
        particle.acceleration.x += (particle.lifetime - 0.5) * 0.5; // Horizontal drift
        
        // Update smoke-specific data
        if let ParticleData::Smoke { opacity, temperature } = &mut particle.data {
            *opacity *= 0.98; // Fade out over time
            *temperature *= 0.99; // Cool down
        }
    }

    /// Update fire particle physics
    fn update_fire_particle(&mut self, particle: &mut Particle, _delta_time: f64) {
        // Fire flickers and moves upward
        particle.acceleration.y += 1.5;
        
        // Random flicker
        let flicker = (particle.lifetime * 10.0).sin() * 0.3;
        particle.acceleration.x += flicker;
        particle.acceleration.z += flicker * 0.5;
        
        // Update fire-specific data
        if let ParticleData::Fire { intensity, flicker_rate } = &mut particle.data {
            *intensity = (particle.lifetime * *flicker_rate).sin().abs();
        }
    }

    /// Update spark particle physics
    fn update_spark_particle(&mut self, particle: &mut Particle, _delta_time: f64) {
        // Sparks move randomly and lose energy
        let random_x = (particle.lifetime * 15.0).sin() * 2.0;
        let random_z = (particle.lifetime * 12.0).cos() * 1.5;
        
        particle.acceleration.x += random_x;
        particle.acceleration.z += random_z;
        
        // Apply gravity
        particle.acceleration.y -= self.config.gravity * 0.5;
        
        // Update spark-specific data
        if let ParticleData::Spark { energy, .. } = &mut particle.data {
            *energy *= 0.95; // Lose energy over time
        }
    }

    /// Update dust particle physics
    fn update_dust_particle(&mut self, particle: &mut Particle, _delta_time: f64) {
        // Dust falls slowly with gravity
        particle.acceleration.y -= self.config.gravity * 0.3;
        
        // Slight horizontal drift
        particle.acceleration.x += (particle.lifetime - 0.5) * 0.1;
    }

    /// Update status indicator particle
    fn update_status_particle(&mut self, particle: &mut Particle, _delta_time: f64) {
        // Status indicators pulse
        let pulse = (particle.lifetime * 8.0).sin() * 0.2;
        particle.size = 1.0 + pulse;
    }

    /// Update connection particle
    fn update_connection_particle(&mut self, _particle: &mut Particle, _delta_time: f64) {
        // Connection particles flow along the connection
        // This would be updated based on actual connection data
    }

    /// Update maintenance alert particle
    fn update_maintenance_particle(&mut self, particle: &mut Particle, _delta_time: f64) {
        // Maintenance alerts blink
        let blink = (particle.lifetime * 6.0).sin() > 0.0;
        if blink {
            particle.character = '!';
        } else {
            particle.character = ' ';
        }
    }

    /// Remove particles that have expired
    fn remove_dead_particles(&mut self) {
        let _initial_count = self.particles.len();
        
        self.particles.retain(|particle| {
            if particle.lifetime <= 0.0 {
                self.stats.particles_destroyed += 1;
                
                // Return particle to pool if pooling is enabled
                if self.config.enable_pooling {
                    self.particle_pool.push_back(particle.clone());
                }
                
                false
            } else {
                true
            }
        });
        
        // Update peak count
        if self.particles.len() > self.stats.peak_particle_count {
            self.stats.peak_particle_count = self.particles.len();
        }
    }

    /// Update system statistics
    fn update_stats(&mut self, start_time: Instant, delta_time: f64) {
        let update_duration = start_time.elapsed();
        self.stats.avg_update_time_ms = update_duration.as_secs_f64() * 1000.0;
        self.stats.active_particles = self.particles.len();
        self.stats.fps = 1.0 / delta_time;
    }

    /// Emit a new particle
    pub fn emit_particle(&mut self, mut particle: Particle) {
        if self.particles.len() >= self.config.max_particles {
            return; // System is at capacity
        }
        
        // Initialize particle
        particle.lifetime = 1.0;
        
        // Add to active particles
        self.particles.push(particle);
        self.stats.particles_created += 1;
    }

    /// Emit multiple particles at once
    pub fn emit_burst(&mut self, particles: Vec<Particle>) {
        for particle in particles {
            self.emit_particle(particle);
        }
    }

    /// Create a particle burst effect
    pub fn create_burst(&mut self, position: Point3D, count: usize, particle_type: ParticleType) {
        for i in 0..count {
            let angle = (i as f64 / count as f64) * 2.0 * std::f64::consts::PI;
            let speed = 2.0 + (i as f64 * 0.1);
            
            let particle = Particle {
                position: position.clone(),
                velocity: Vector3D {
                    x: angle.cos() * speed,
                    y: 0.0,
                    z: angle.sin() * speed,
                },
                acceleration: Vector3D::zero(),
                lifetime: 1.0,
                max_lifetime: 2.0,
                size: 1.0,
                character: match particle_type {
                    ParticleType::Spark => '*',
                    ParticleType::Fire => '^',
                    ParticleType::Smoke => '~',
                    _ => '•',
                },
                particle_type: particle_type.clone(),
                data: self.create_particle_data(&particle_type),
            };
            
            self.emit_particle(particle);
        }
    }

    /// Create particle data based on type
    fn create_particle_data(&self, particle_type: &ParticleType) -> ParticleData {
        match particle_type {
            ParticleType::Basic => ParticleData::Basic { color_intensity: 1.0 },
            ParticleType::Smoke => ParticleData::Smoke { opacity: 1.0, temperature: 100.0 },
            ParticleType::Fire => ParticleData::Fire { intensity: 1.0, flicker_rate: 8.0 },
            ParticleType::Spark => ParticleData::Spark { energy: 1.0, trail_length: 3 },
            ParticleType::Dust => ParticleData::Dust { mass: 0.1, static_charge: 0.0 },
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

    /// Get all active particles
    pub fn particles(&self) -> &[Particle] {
        &self.particles
    }

    /// Get system statistics
    pub fn stats(&self) -> &ParticleSystemStats {
        &self.stats
    }

    /// Get system configuration
    pub fn config(&self) -> &ParticleSystemConfig {
        &self.config
    }

    /// Update configuration
    pub fn update_config(&mut self, config: ParticleSystemConfig) {
        self.config = config;
    }

    /// Clear all particles
    pub fn clear(&mut self) {
        self.particles.clear();
        self.particle_pool.clear();
    }

    /// Get particle count
    pub fn particle_count(&self) -> usize {
        self.particles.len()
    }
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
    fn test_particle_system_creation() {
        let system = ParticleSystem::new();
        assert_eq!(system.particle_count(), 0);
        assert_eq!(system.config.max_particles, 1000);
    }

    #[test]
    fn test_particle_emission() {
        let mut system = ParticleSystem::new();
        
        let particle = Particle {
            position: Point3D::new(0.0, 0.0, 0.0),
            velocity: Vector3D::new(1.0, 0.0, 0.0),
            acceleration: Vector3D::zero(),
            lifetime: 1.0,
            max_lifetime: 2.0,
            size: 1.0,
            character: '•',
            particle_type: ParticleType::Basic,
            data: ParticleData::Basic { color_intensity: 1.0 },
        };
        
        system.emit_particle(particle);
        assert_eq!(system.particle_count(), 1);
        assert_eq!(system.stats.particles_created, 1);
    }

    #[test]
    fn test_particle_burst() {
        let mut system = ParticleSystem::new();
        
        system.create_burst(Point3D::new(0.0, 0.0, 0.0), 5, ParticleType::Spark);
        assert_eq!(system.particle_count(), 5);
    }

    #[test]
    fn test_particle_update() {
        let mut system = ParticleSystem::new();
        
        let particle = Particle {
            position: Point3D::new(0.0, 0.0, 0.0),
            velocity: Vector3D::new(1.0, 0.0, 0.0),
            acceleration: Vector3D::zero(),
            lifetime: 1.0,
            max_lifetime: 1.0,
            size: 1.0,
            character: '•',
            particle_type: ParticleType::Basic,
            data: ParticleData::Basic { color_intensity: 1.0 },
        };
        
        system.emit_particle(particle);
        system.update(1.0); // Update with 1 second delta time
        
        // Particle should be removed after update
        assert_eq!(system.particle_count(), 0);
    }

    #[test]
    fn test_vector_operations() {
        let vector = Vector3D::new(3.0, 4.0, 0.0);
        assert_eq!(vector.length(), 5.0);
        
        let normalized = vector.normalize();
        assert!((normalized.length() - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_particle_types() {
        let basic_data = ParticleData::Basic { color_intensity: 1.0 };
        let smoke_data = ParticleData::Smoke { opacity: 0.8, temperature: 50.0 };
        
        assert!(matches!(basic_data, ParticleData::Basic { .. }));
        assert!(matches!(smoke_data, ParticleData::Smoke { .. }));
    }
}
