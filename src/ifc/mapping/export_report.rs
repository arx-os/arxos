//! Export-side loss notes (Phase 5).

use crate::core::Building;

use super::report::{FidelityLevel, LossReport};

/// Inspect a building before/after IFC export and record non-fatal losses.
///
/// Does not modify the building. Call after a successful write if desired.
pub fn report_export_losses(building: &Building) -> LossReport {
    let mut report = LossReport::new(FidelityLevel::L2);

    for floor in &building.floors {
        for wing in &floor.wings {
            for room in &wing.rooms {
                let has_mesh = room
                    .spatial_properties
                    .mesh
                    .as_ref()
                    .map(|m| !m.vertices.is_empty())
                    .unwrap_or(false);
                let d = &room.spatial_properties.dimensions;
                let has_box = d.width > 0.0 && d.depth > 0.0 && d.height > 0.0;
                if !has_mesh && !has_box {
                    report.warn_entity(
                        "export_no_body",
                        "room has neither mesh nor positive dimensions; exported without body",
                        &room.name,
                    );
                }
                for eq in &room.equipment {
                    if eq.mesh.as_ref().map(|m| m.vertices.is_empty()).unwrap_or(true) {
                        // Position-only is intentional L2 policy — info-level note only when
                        // we want visibility; keep quiet to avoid noise. Uncomment if needed:
                        // report.warn_entity("export_position_only", "...", &eq.name);
                        let _ = eq;
                    }
                }
            }
        }
    }

    report
}
