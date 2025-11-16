//! Planar view rendering (top-down, front, side)

use crate::core::EquipmentType;
use crate::render3d::types::{Equipment3D, Scene3D};
use std::collections::HashMap;

/// Render top-down view (X-Y plane)
pub fn render_top_down_view(scene: &Scene3D) -> String {
    let mut output = String::new();

    // Create a simple ASCII grid representation
    let grid_size = 20;
    let mut grid = vec![vec![' '; grid_size]; grid_size];

    // Place equipment on the grid
    for equipment in &scene.equipment {
        let x = ((equipment.position.x / 10.0) as usize).min(grid_size - 1);
        let y = ((equipment.position.y / 10.0) as usize).min(grid_size - 1);

        let char = match equipment.equipment_type {
            EquipmentType::HVAC => 'H',
            EquipmentType::Electrical => 'E',
            EquipmentType::Safety => 'S',
            EquipmentType::Network => 'N',
            EquipmentType::AV => 'A',
            EquipmentType::Furniture => 'F',
            EquipmentType::Plumbing => 'P',
            EquipmentType::Other(_) => 'O',
        };

        grid[y][x] = char;
    }

    output.push_str("│ Equipment Grid (Top-Down):\n");
    for row in &grid {
        output.push_str("│ ");
        for &cell in row {
            output.push(cell);
        }
        output.push_str(" │\n");
    }

    output
}

/// Render front view (X-Z plane)
pub fn render_front_view(scene: &Scene3D) -> String {
    let mut output = String::new();

    output.push_str("│ Front View (X-Z Plane):\n");

    // Group equipment by floor level
    let mut floor_equipment: HashMap<i32, Vec<&Equipment3D>> = HashMap::new();
    for equipment in &scene.equipment {
        floor_equipment
            .entry(equipment.floor_level)
            .or_default()
            .push(equipment);
    }

    let mut floors: Vec<_> = floor_equipment.keys().collect();
    floors.sort();

    for &floor_level in &floors {
        output.push_str(&format!("│   Floor {}: ", floor_level));
        if let Some(equipment) = floor_equipment.get(floor_level) {
            for (i, eq) in equipment.iter().enumerate() {
                if i > 0 {
                    output.push_str(", ");
                }
                output.push_str(eq.name.as_str());
            }
        }
        output.push_str(" │\n");
    }

    output
}

/// Render side view (Y-Z plane)
pub fn render_side_view(scene: &Scene3D) -> String {
    let mut output = String::new();

    output.push_str("│ Side View (Y-Z Plane):\n");

    // Show equipment by Y position (depth)
    let mut equipment_by_y: Vec<_> = scene.equipment.iter().collect();
    equipment_by_y.sort_by(|a, b| {
        a.position
            .y
            .partial_cmp(&b.position.y)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    for equipment in &equipment_by_y {
        output.push_str(&format!(
            "│   {} at Y: {:.1}m, Z: {:.1}m │\n",
            equipment.name.as_str(),
            equipment.position.y,
            equipment.position.z
        ));
    }

    output
}
