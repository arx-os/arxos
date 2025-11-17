//! Visual effects management for interactive rendering
//!
//! This module provides helper functions for creating and managing
//! visual effects in the interactive renderer.

use crate::core::spatial::Point3D;
use crate::render3d::{AlertLevel, EquipmentStatus, ParticleType, VisualEffectsEngine};

/// Add particle effects to ASCII output
///
/// # Arguments
/// * `effects_engine` - Reference to the visual effects engine
/// * `output` - The ASCII output string to add effects to
///
/// # Returns
/// Modified output string with particle effects added
pub fn add_particle_effects_to_output(
    effects_engine: &VisualEffectsEngine,
    mut output: String,
) -> String {
    // Get all active particles
    let particles = effects_engine.particle_system().particles();

    // Convert particles to ASCII characters and add to output
    for particle in particles {
        // Simple particle rendering - in a real implementation, this would be more sophisticated
        let particle_char = particle.character;
        let intensity = particle.lifetime;

        // Add particle to output (simplified - would need proper 3D to 2D projection)
        if intensity > 0.1 {
            // This is a simplified approach - in reality, we'd need proper 3D projection
            output.push_str(&format!("{}", particle_char));
        }
    }

    output
}

/// Create equipment status effect
///
/// # Arguments
/// * `effects_engine` - Mutable reference to the visual effects engine
/// * `equipment_id` - ID of the equipment
/// * `status` - Current equipment status
/// * `position` - 3D position of the equipment
/// * `frame_count` - Current frame count for unique IDs
///
/// # Returns
/// Result indicating success or error message
pub fn create_equipment_status_effect(
    effects_engine: &mut VisualEffectsEngine,
    equipment_id: String,
    status: EquipmentStatus,
    position: Point3D,
) -> Result<(), String> {
    effects_engine.create_equipment_status_effect(
        format!("status_{}", equipment_id),
        equipment_id,
        status,
        position,
    )
}

/// Create maintenance alert effect
///
/// # Arguments
/// * `effects_engine` - Mutable reference to the visual effects engine
/// * `equipment_id` - ID of the equipment
/// * `alert_level` - Level of the maintenance alert
/// * `position` - 3D position of the equipment
///
/// # Returns
/// Result indicating success or error message
pub fn create_maintenance_alert_effect(
    effects_engine: &mut VisualEffectsEngine,
    equipment_id: String,
    alert_level: AlertLevel,
    position: Point3D,
) -> Result<(), String> {
    effects_engine.create_maintenance_alert_effect(
        format!("alert_{}", equipment_id),
        equipment_id,
        alert_level,
        position,
    )
}

/// Create particle burst effect
///
/// # Arguments
/// * `effects_engine` - Mutable reference to the visual effects engine
/// * `position` - 3D position where the burst should occur
/// * `particle_type` - Type of particles to create
/// * `count` - Number of particles in the burst
/// * `frame_count` - Current frame count for unique IDs
///
/// # Returns
/// Result indicating success or error message
pub fn create_particle_burst_effect(
    effects_engine: &mut VisualEffectsEngine,
    position: Point3D,
    particle_type: ParticleType,
    count: usize,
    frame_count: u32,
) -> Result<(), String> {
    effects_engine.create_particle_burst_effect(
        format!("burst_{}", frame_count),
        position,
        particle_type,
        count,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add_particle_effects_to_output() {
        let effects_engine = VisualEffectsEngine::new();
        let output = "Test output".to_string();

        let result = add_particle_effects_to_output(&effects_engine, output);

        // Should return the output (possibly with particles added)
        assert!(result.contains("Test output"));
    }
}
