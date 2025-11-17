//! Particle system modules
//!
//! This module organizes the particle system into focused submodules
//! for better maintainability and clarity.

pub mod emitters;
pub mod physics;
pub mod types;

// Re-export commonly used types
pub use types::{
    AlertLevel, Particle, ParticleData, ParticleSystemConfig, ParticleSystemStats, ParticleType,
    StatusType, Vector3D,
};

// Re-export emitter functions
pub use emitters::{
    create_burst, create_fire_particle, create_particle_data, create_smoke_particle,
    create_spark_particle, create_status_indicator, get_particle_character,
};

// Re-export physics functions
pub use physics::update_particle;
