//! Isometric view rendering

use crate::core::EquipmentStatus;
use crate::render3d::types::{Equipment3D, Scene3D};

/// Render scene in isometric view
pub fn render_isometric_view(scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
    let mut output = String::new();

    output.push_str("📐 Isometric 3D View:\n");
    output.push_str("┌─────────────────────────────────────────────────────────────┐\n");

    // Sort floors by level for proper rendering order
    let mut floors = scene.floors.clone();
    floors.sort_by_key(|f| f.level);

    for floor in &floors {
        output.push_str(&format!(
            "│ Floor {}: {} (Z: {:.1}m) │\n",
            floor.level,
            floor.name.as_str(),
            floor.elevation
        ));

        // Show equipment on this floor
        let floor_equipment: Vec<&Equipment3D> = scene
            .equipment
            .iter()
            .filter(|e| e.floor_level == floor.level)
            .collect();

        for equipment in &floor_equipment {
            let status_symbol = match equipment.status {
                EquipmentStatus::Active => "🟢",
                EquipmentStatus::Maintenance => "🟡",
                EquipmentStatus::OutOfOrder => "🔴",
                EquipmentStatus::Inactive | EquipmentStatus::Unknown => "⚪",
            };
            output.push_str(&format!(
                "│   {} {} at ({:.1}, {:.1}, {:.1}) │\n",
                status_symbol,
                equipment.name.as_str(),
                equipment.position.x,
                equipment.position.y,
                equipment.position.z
            ));
        }
    }

    output.push_str("└─────────────────────────────────────────────────────────────┘\n");

    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_render_isometric_view_empty_scene() {
        use crate::core::spatial::BoundingBox3D;
        use crate::core::spatial::Point3D;
        use crate::render3d::types::SceneMetadata;
        use std::sync::Arc;

        let scene = Scene3D {
            building_name: Arc::new("Test Building".to_string()),
            floors: vec![],
            equipment: vec![],
            rooms: vec![],
            bounding_box: BoundingBox3D::new(
                Point3D::new(0.0, 0.0, 0.0),
                Point3D::new(10.0, 10.0, 10.0),
            ),
            metadata: SceneMetadata {
                total_floors: 0,
                total_rooms: 0,
                total_equipment: 0,
                render_time_ms: 0,
                projection_type: "Isometric".to_string(),
                view_angle: "45deg".to_string(),
            },
        };

        let result = render_isometric_view(&scene);
        assert!(result.is_ok());
        let output = result.unwrap();
        assert!(output.contains("Isometric 3D View"));
    }
}
