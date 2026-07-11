//! Particle System for Terminal Rendering
//!
//! This module provides a high-performance particle system optimized for terminal rendering,
//! including particle lifecycle management, physics simulation, and visual effects.

use crate::core::spatial::Point3D;
use std::collections::VecDeque;
use std::time::Instant;

use super::{
    AlertLevel, Particle, ParticleData, ParticleSystemConfig, ParticleSystemStats, ParticleType,
    StatusType, Vector3D,
};

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
    #[allow(dead_code)] // Will be used in future animation features
    last_update: Instant,
}

impl Default for ParticleSystem {
    fn default() -> Self {
        Self::new()
    }
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

    /// Update a single particle using the physics module
    fn update_particle(&mut self, particle: &mut Particle, delta_time: f64) {
        super::physics::update_particle(particle, delta_time, &self.config);
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

    /// Create a particle burst effect using the emitters module
    pub fn create_burst(&mut self, position: Point3D, count: usize, particle_type: ParticleType) {
        let burst_particles = super::emitters::create_burst(position, count, particle_type);
        self.emit_burst(burst_particles);
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
