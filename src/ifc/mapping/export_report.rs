//! Export-side loss notes (Phase 5) + LiDAR review warnings (Track C2).

use crate::core::{summarize_review, Building};

use super::report::{FidelityLevel, LossReport};

/// Inspect a building before/after IFC export and record non-fatal losses.
///
/// Does not modify the building. Call after a successful write if desired.
/// Always includes warnings for unreviewed LiDAR auto-structure (Track C2).
pub fn report_export_losses(building: &Building) -> LossReport {
    let mut report = LossReport::new(FidelityLevel::L2);

    let review = summarize_review(building);
    for line in review.warning_lines() {
        if let Some(msg) = line.strip_prefix("warn: ") {
            report.warn("export_unreviewed_lidar", msg);
        } else if let Some(msg) = line.strip_prefix("info: ") {
            report.warn("export_rejected_lidar", msg);
        } else {
            report.warn("export_review", &line);
        }
    }

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
                    if eq
                        .mesh
                        .as_ref()
                        .map(|m| m.vertices.is_empty())
                        .unwrap_or(true)
                    {
                        let _ = eq;
                    }
                }
            }
        }
    }

    report
}
