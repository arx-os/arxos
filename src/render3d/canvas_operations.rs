//! Canvas rendering operations for 3D building visualization
//!
//! This module contains functions for rendering 3D building elements
//! (floors, equipment, rooms) to ASCII canvas with depth buffering.

use crate::render3d::types::{Equipment3D, Floor3D, Room3D};
use crate::spatial::Point3D;

/// Render floors to ASCII canvas
///
/// # Arguments
///
/// * `floors` - Vector of Floor3D to render
/// * `canvas` - Mutable reference to 2D canvas (Vec<Vec<char>>)
/// * `depth_buffer` - Mutable reference to depth buffer (Vec<Vec<f64>>)
/// * `width` - Canvas width
/// * `height` - Canvas height
/// * `project_to_screen` - Closure to project 3D points to screen coordinates
pub fn render_floors_to_canvas<F>(
    floors: &[Floor3D],
    canvas: &mut [Vec<char>],
    depth_buffer: &mut [Vec<f64>],
    width: usize,
    height: usize,
    project_to_screen: F,
) where
    F: Fn(&Point3D) -> Point3D,
{
    for floor in floors {
        // Project floor bounding box to screen coordinates
        let min_screen = project_to_screen(&floor.bounding_box.min);
        let max_screen = project_to_screen(&floor.bounding_box.max);

        // Draw floor outline
        let start_x = min_screen.x.max(0.0) as usize;
        let end_x = max_screen.x.min(width as f64) as usize;
        let start_y = min_screen.y.max(0.0) as usize;
        let end_y = max_screen.y.min(height as f64) as usize;

        // Draw horizontal lines for floor
        for y in start_y..end_y {
            for x in start_x..end_x {
                if x < width && y < height {
                    let depth = floor.bounding_box.min.z;
                    if depth > depth_buffer[y][x] {
                        depth_buffer[y][x] = depth;
                        canvas[y][x] = '─';
                    }
                }
            }
        }

        // Draw floor label
        let label_x = ((min_screen.x + max_screen.x) / 2.0) as usize;
        let label_y = ((min_screen.y + max_screen.y) / 2.0) as usize;
        if label_x < width && label_y < height {
            let floor_label = format!("F{}", floor.level);
            for (i, ch) in floor_label.chars().enumerate() {
                if label_x + i < width {
                    canvas[label_y][label_x + i] = ch;
                }
            }
        }
    }
}

/// Render equipment to ASCII canvas
///
/// # Arguments
///
/// * `equipment` - Vector of Equipment3D to render
/// * `canvas` - Mutable reference to 2D canvas
/// * `depth_buffer` - Mutable reference to depth buffer
/// * `width` - Canvas width
/// * `height` - Canvas height
/// * `project_to_screen` - Closure to project 3D points to screen coordinates
pub fn render_equipment_to_canvas<F>(
    equipment: &[Equipment3D],
    canvas: &mut [Vec<char>],
    depth_buffer: &mut [Vec<f64>],
    width: usize,
    height: usize,
    project_to_screen: F,
) where
    F: Fn(&Point3D) -> Point3D,
{
    for eq in equipment {
        let screen_pos = project_to_screen(&eq.position);
        let x = screen_pos.x as usize;
        let y = screen_pos.y as usize;

        if x < width && y < height {
            let depth = eq.position.z;
            if depth > depth_buffer[y][x] {
                depth_buffer[y][x] = depth;

                // Choose symbol based on equipment type
                let symbol = match eq.equipment_type.as_str() {
                    s if s.contains("AIR") => '▲',   // HVAC
                    s if s.contains("LIGHT") => '●', // Electrical
                    s if s.contains("PUMP") => '◊',  // Plumbing
                    s if s.contains("FAN") => '◈',   // Mechanical
                    _ => '╬',                        // Generic equipment
                };

                canvas[y][x] = symbol;
            }
        }
    }
}

/// Render rooms to ASCII canvas
///
/// # Arguments
///
/// * `rooms` - Vector of Room3D to render
/// * `canvas` - Mutable reference to 2D canvas
/// * `depth_buffer` - Mutable reference to depth buffer
/// * `width` - Canvas width
/// * `height` - Canvas height
/// * `project_to_screen` - Closure to project 3D points to screen coordinates
pub fn render_rooms_to_canvas<F>(
    rooms: &[Room3D],
    canvas: &mut [Vec<char>],
    depth_buffer: &mut [Vec<f64>],
    width: usize,
    height: usize,
    project_to_screen: F,
) where
    F: Fn(&Point3D) -> Point3D,
{
    for room in rooms {
        let min_screen = project_to_screen(&room.bounding_box.min);
        let max_screen = project_to_screen(&room.bounding_box.max);

        let start_x = min_screen.x.max(0.0) as usize;
        let end_x = max_screen.x.min(width as f64) as usize;
        let start_y = min_screen.y.max(0.0) as usize;
        let end_y = max_screen.y.min(height as f64) as usize;

        // Draw room outline with box characters
        for y in start_y..end_y {
            for x in start_x..end_x {
                if x < width && y < height {
                    let depth = room.bounding_box.min.z;
                    if depth > depth_buffer[y][x] {
                        depth_buffer[y][x] = depth;

                        // Draw room boundaries
                        let is_top = y == start_y;
                        let is_bottom = y == end_y.saturating_sub(1);
                        let is_left = x == start_x;
                        let is_right = x == end_x.saturating_sub(1);

                        let char = if is_top && is_left {
                            '┌'
                        } else if is_top && is_right {
                            '┐'
                        } else if is_bottom && is_left {
                            '└'
                        } else if is_bottom && is_right {
                            '┘'
                        } else if is_top || is_bottom {
                            '─'
                        } else if is_left || is_right {
                            '│'
                        } else {
                            ' ' // Interior space
                        };

                        canvas[y][x] = char;
                    }
                }
            }
        }

        // Draw room label
        let label_x = ((min_screen.x + max_screen.x) / 2.0) as usize;
        let label_y = ((min_screen.y + max_screen.y) / 2.0) as usize;
        if label_x < width && label_y < height && label_x + room.name.len() < width {
            for (i, ch) in room.name.chars().enumerate() {
                if label_x + i < width {
                    canvas[label_y][label_x + i] = ch;
                }
            }
        }
    }
}
