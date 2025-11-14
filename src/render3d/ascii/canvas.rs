//! ASCII canvas with depth buffering for 3D rendering
//!
//! Provides a 2D canvas with depth buffer for proper occlusion handling
//! when rendering 3D building elements to ASCII.

use super::characters::{get_equipment_symbol, FLOOR_CHAR, ROOM_CHAR};
use crate::render3d::types::{Equipment3D, Floor3D, Room3D};
use crate::spatial::Point3D;

/// ASCII canvas for 2D rendering
pub struct AsciiCanvas {
    width: usize,
    height: usize,
    buffer: Vec<Vec<char>>,
}

impl AsciiCanvas {
    /// Create a new ASCII canvas
    ///
    /// # Arguments
    ///
    /// * `width` - Canvas width in characters
    /// * `height` - Canvas height in characters
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            buffer: vec![vec![' '; width]; height],
        }
    }

    /// Set a character at the given position
    ///
    /// # Arguments
    ///
    /// * `x` - X coordinate
    /// * `y` - Y coordinate
    /// * `ch` - Character to set
    pub fn set(&mut self, x: usize, y: usize, ch: char) {
        if x < self.width && y < self.height {
            self.buffer[y][x] = ch;
        }
    }

    /// Get a character at the given position
    pub fn get(&self, x: usize, y: usize) -> Option<char> {
        if x < self.width && y < self.height {
            Some(self.buffer[y][x])
        } else {
            None
        }
    }

    /// Convert canvas to string
    pub fn to_string(&self) -> String {
        self.buffer
            .iter()
            .map(|row| row.iter().collect::<String>())
            .collect::<Vec<String>>()
            .join("\n")
    }

    /// Get mutable access to the underlying buffer
    pub fn buffer_mut(&mut self) -> &mut [Vec<char>] {
        &mut self.buffer
    }

    /// Get immutable access to the underlying buffer
    pub fn buffer(&self) -> &[Vec<char>] {
        &self.buffer
    }

    /// Get canvas dimensions
    pub fn dimensions(&self) -> (usize, usize) {
        (self.width, self.height)
    }
}

/// Depth buffer for Z-ordering
pub struct DepthBuffer {
    width: usize,
    height: usize,
    buffer: Vec<Vec<f64>>,
}

impl DepthBuffer {
    /// Create a new depth buffer
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            buffer: vec![vec![f64::NEG_INFINITY; width]; height],
        }
    }

    /// Test if a depth value should be rendered at given position
    ///
    /// # Arguments
    ///
    /// * `x` - X coordinate
    /// * `y` - Y coordinate
    /// * `depth` - Depth value to test
    ///
    /// # Returns
    ///
    /// true if the depth is greater than current depth at position
    pub fn test_and_set(&mut self, x: usize, y: usize, depth: f64) -> bool {
        if x < self.width && y < self.height {
            if depth > self.buffer[y][x] {
                self.buffer[y][x] = depth;
                true
            } else {
                false
            }
        } else {
            false
        }
    }

    /// Get mutable access to the underlying buffer
    pub fn buffer_mut(&mut self) -> &mut [Vec<f64>] {
        &mut self.buffer
    }

    /// Get immutable access to the underlying buffer
    pub fn buffer(&self) -> &[Vec<f64>] {
        &self.buffer
    }
}

/// Render floors to ASCII canvas
///
/// # Arguments
///
/// * `floors` - Vector of Floor3D to render
/// * `canvas` - Mutable ASCII canvas
/// * `depth_buffer` - Mutable depth buffer
/// * `project_to_screen` - Closure to project 3D points to screen coordinates
pub fn render_floors<F>(
    floors: &[Floor3D],
    canvas: &mut AsciiCanvas,
    depth_buffer: &mut DepthBuffer,
    project_to_screen: F,
) where
    F: Fn(&Point3D) -> Point3D,
{
    let (width, height) = canvas.dimensions();

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
                let depth = floor.bounding_box.min.z;
                if depth_buffer.test_and_set(x, y, depth) {
                    canvas.set(x, y, FLOOR_CHAR);
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
                    canvas.set(label_x + i, label_y, ch);
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
/// * `canvas` - Mutable ASCII canvas
/// * `depth_buffer` - Mutable depth buffer
/// * `project_to_screen` - Closure to project 3D points to screen coordinates
pub fn render_equipment<F>(
    equipment: &[Equipment3D],
    canvas: &mut AsciiCanvas,
    depth_buffer: &mut DepthBuffer,
    project_to_screen: F,
) where
    F: Fn(&Point3D) -> Point3D,
{
    let (width, height) = canvas.dimensions();

    for eq in equipment {
        let screen_pos = project_to_screen(&eq.position);
        let x = screen_pos.x as usize;
        let y = screen_pos.y as usize;

        if x < width && y < height {
            let depth = eq.position.z;
            if depth_buffer.test_and_set(x, y, depth) {
                let symbol = get_equipment_symbol(&eq.equipment_type);
                canvas.set(x, y, symbol);
            }
        }
    }
}

/// Render rooms to ASCII canvas
///
/// # Arguments
///
/// * `rooms` - Vector of Room3D to render
/// * `canvas` - Mutable ASCII canvas
/// * `depth_buffer` - Mutable depth buffer
/// * `project_to_screen` - Closure to project 3D points to screen coordinates
pub fn render_rooms<F>(
    rooms: &[Room3D],
    canvas: &mut AsciiCanvas,
    depth_buffer: &mut DepthBuffer,
    project_to_screen: F,
) where
    F: Fn(&Point3D) -> Point3D,
{
    let (width, height) = canvas.dimensions();

    for room in rooms {
        // Project room bounding box to screen coordinates
        let min_screen = project_to_screen(&room.bounding_box.min);
        let max_screen = project_to_screen(&room.bounding_box.max);

        // Draw room outline
        let start_x = min_screen.x.max(0.0) as usize;
        let end_x = max_screen.x.min(width as f64) as usize;
        let start_y = min_screen.y.max(0.0) as usize;
        let end_y = max_screen.y.min(height as f64) as usize;

        // Draw room boundaries
        for y in start_y..end_y {
            for x in start_x..end_x {
                let depth = room.bounding_box.min.z;
                if depth_buffer.test_and_set(x, y, depth) {
                    // Draw room marker at center
                    if x == (start_x + end_x) / 2 && y == (start_y + end_y) / 2 {
                        canvas.set(x, y, ROOM_CHAR);
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_canvas_creation() {
        let canvas = AsciiCanvas::new(80, 24);
        assert_eq!(canvas.dimensions(), (80, 24));
    }

    #[test]
    fn test_canvas_set_get() {
        let mut canvas = AsciiCanvas::new(10, 10);
        canvas.set(5, 5, 'X');
        assert_eq!(canvas.get(5, 5), Some('X'));
    }

    #[test]
    fn test_canvas_bounds_checking() {
        let mut canvas = AsciiCanvas::new(10, 10);
        canvas.set(100, 100, 'X'); // Should not panic
        assert_eq!(canvas.get(100, 100), None);
    }

    #[test]
    fn test_depth_buffer() {
        let mut depth = DepthBuffer::new(10, 10);
        assert!(depth.test_and_set(5, 5, 1.0));
        assert!(!depth.test_and_set(5, 5, 0.5)); // Behind previous
        assert!(depth.test_and_set(5, 5, 2.0)); // In front
    }

    #[test]
    fn test_canvas_to_string() {
        let mut canvas = AsciiCanvas::new(5, 2);
        canvas.set(0, 0, 'H');
        canvas.set(1, 0, 'I');
        let output = canvas.to_string();
        assert!(output.contains('H'));
        assert!(output.contains('I'));
    }
}
