//! Perspective view rendering

use crate::core::EquipmentStatus;
use crate::render3d::types::{Camera3D, Equipment3D, Scene3D};

/// Render scene in perspective view
pub fn render_perspective_view(
    scene: &Scene3D,
    camera: &Camera3D,
) -> Result<String, Box<dyn std::error::Error>> {
    let mut output = String::new();

    output.push_str("📐 Perspective View:\n");
    output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
    output.push_str(&format!(
        "│ Camera Position: ({:.1}, {:.1}, {:.1}) │\n",
        camera.position.x, camera.position.y, camera.position.z
    ));
    output.push_str(&format!(
        "│ Camera Target: ({:.1}, {:.1}, {:.1}) │\n",
        camera.target.x, camera.target.y, camera.target.z
    ));
    output.push_str(&format!("│ FOV: {:.1}° │\n", camera.fov));

    // Show equipment with perspective depth
    let mut equipment_with_depth: Vec<(&Equipment3D, f64)> = scene
        .equipment
        .iter()
        .map(|e| {
            let depth = (e.position.x - camera.position.x).powi(2)
                + (e.position.y - camera.position.y).powi(2)
                + (e.position.z - camera.position.z).powi(2);
            (e, depth.sqrt())
        })
        .collect();

    equipment_with_depth.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));

    for (equipment, depth) in &equipment_with_depth {
        let status_symbol = match equipment.status {
            EquipmentStatus::Active => "🟢",
            EquipmentStatus::Maintenance => "🟡",
            EquipmentStatus::OutOfOrder => "🔴",
            EquipmentStatus::Inactive | EquipmentStatus::Unknown => "⚪",
        };
        output.push_str(&format!(
            "│   {} {} (depth: {:.1}m) │\n",
            status_symbol,
            equipment.name.as_str(),
            depth
        ));
    }

    output.push_str("└─────────────────────────────────────────────────────────────┘\n");

    Ok(output)
}
