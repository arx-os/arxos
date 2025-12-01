//! WebGL-style point cloud renderer with Z-buffer and LOD
//! Exactly matches the 5-step implementation pattern

use super::camera::{Camera, Vec3, vec3, project};
use super::types::*;
use crate::core::EquipmentType;
use crossterm::event::{Event, KeyCode, MouseEventKind};
use crossterm::style::{Color, Print};
use crossterm::terminal::{size, Clear, ClearType};
use crossterm::{cursor, execute};

use std::io::{self, Write};

/// Brightness character ramps for ASCII rendering
///
/// Different character sets provide varying levels of detail and visual styles.
/// Each ramp is ordered from darkest (space) to brightest (densest character).
pub mod brightness_ramps {
    /// Original 9-level ramp (legacy compatibility)
    ///
    /// Simple progression from space to full block.
    /// Good for basic visualization but limited depth perception.
    pub const CLASSIC: &str = " .,:;+*#█";
    
    /// Acerola-style 16-level density ramp (RECOMMENDED)
    ///
    /// Based on Acerola's ASCII shader technique with 16 luminance values.
    /// Provides smooth gradients and excellent depth perception for LiDAR scans.
    /// Optimized for terminal rendering of architectural spaces.
    ///
    /// Reference: https://www.youtube.com/watch?v=3Z4AenUGRSs
    pub const ACEROLA_16: &str = " .:-=+*#%@MWBQ&$";
    
    /// Extended ASCII 16-level ramp
    ///
    /// Uses punctuation and special characters for varied texture.
    /// May not render consistently across all terminal fonts.
    pub const EXTENDED_16: &str = " .'`^\",:;Il!i><~+";
    
    /// Unicode block elements 16-level ramp
    ///
    /// Uses Unicode box-drawing and block characters.
    /// Requires Unicode-capable terminal.
    pub const UNICODE_16: &str = " ░▒▓█▀▄▌▐│─┼┤├┬┴";
}

/// Get brightness character from normalized depth value
///
/// Maps a depth value [0.0, 1.0] to a character from the brightness ramp.
/// Uses linear interpolation to select the appropriate character.
///
/// # Arguments
///
/// * `depth` - Normalized depth value (0.0 = closest, 1.0 = farthest)
/// * `ramp` - Character ramp string (ordered from darkest to brightest)
///
/// # Returns
///
/// Character representing the brightness level, or space if invalid
///
/// # Examples
///
/// ```
/// let ch = get_brightness_char(0.0, brightness_ramps::ACEROLA_16);
/// assert_eq!(ch, ' '); // Closest point = darkest = space
///
/// let ch = get_brightness_char(1.0, brightness_ramps::ACEROLA_16);
/// assert_eq!(ch, '$'); // Farthest point = brightest = '$'
/// ```
fn get_brightness_char(depth: f32, ramp: &str) -> char {
    let max_brightness = (ramp.chars().count() - 1) as f32;
    let brightness = (depth * max_brightness).min(max_brightness).max(0.0) as usize;
    ramp.chars().nth(brightness).unwrap_or(' ')
}

/// Point in a 3D point cloud with color
#[derive(Debug, Clone, Copy)]
pub struct Point3DColored {
    pub pos: Vec3,
    pub color: Color,
}

/// Uniform 3D grid for level-of-detail rendering
#[derive(Debug, Clone)]
pub struct UniformGrid {
    cells: Vec<Vec<Vec<GridCell>>>,
    #[allow(dead_code)] // Reserved for adaptive LOD based on cell size
    cell_size: f32,
    grid_size: usize,
    #[allow(dead_code)] // Reserved for spatial query optimization
    bounds: (Vec3, Vec3), // min, max
}

/// Grid cell containing points for LOD rendering
#[derive(Debug, Clone)]
pub struct GridCell {
    pub points: Vec<Point3DColored>,
    pub average_color: Color,
    pub bounds: (Vec3, Vec3), // min, max
}

/// Z-buffer for depth testing (exactly like WebGL)
pub struct ZBuffer {
    buffer: Vec<Vec<(f32, char)>>,
    width: usize,
    height: usize,
}

impl ZBuffer {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            buffer: vec![vec![(0.0, ' '); width]; height],
            width,
            height,
        }
    }

    pub fn clear(&mut self) {
        for row in &mut self.buffer {
            for cell in row {
                *cell = (0.0, ' ');
            }
        }
    }

    pub fn set_pixel(&mut self, x: usize, y: usize, depth: f32, ch: char) -> bool {
        if x >= self.width || y >= self.height {
            return false;
        }

        if depth > self.buffer[y][x].0 {
            self.buffer[y][x] = (depth, ch);
            true
        } else {
            false
        }
    }

    pub fn render_to_string(&self) -> String {
        let mut output = String::new();
        for row in &self.buffer {
            for &(_, ch) in row {
                output.push(ch);
            }
            output.push('\n');
        }
        output
    }
}

impl UniformGrid {
    /// Build uniform 3D grid for LOD (Step 5)
    pub fn new(points: &[Point3DColored], grid_size: usize) -> Self {
        if points.is_empty() {
            return Self {
                cells: vec![vec![vec![GridCell::empty(); grid_size]; grid_size]; grid_size],
                cell_size: 1.0,
                grid_size,
                bounds: (vec3(0.0, 0.0, 0.0), vec3(1.0, 1.0, 1.0)),
            };
        }

        // Calculate bounds
        let mut min = points[0].pos;
        let mut max = points[0].pos;
        for point in points {
            min.x = min.x.min(point.pos.x);
            min.y = min.y.min(point.pos.y);
            min.z = min.z.min(point.pos.z);
            max.x = max.x.max(point.pos.x);
            max.y = max.y.max(point.pos.y);
            max.z = max.z.max(point.pos.z);
        }

        let size = vec3(max.x - min.x, max.y - min.y, max.z - min.z);
        let cell_size = size.x.max(size.y).max(size.z) / grid_size as f32;

        // Initialize grid
        let mut cells = vec![vec![vec![GridCell::empty(); grid_size]; grid_size]; grid_size];

        // Place points in grid cells
        for &point in points {
            let rel_pos = point.pos.sub(&min);
            let cell_x = ((rel_pos.x / cell_size) as usize).min(grid_size - 1);
            let cell_y = ((rel_pos.y / cell_size) as usize).min(grid_size - 1);
            let cell_z = ((rel_pos.z / cell_size) as usize).min(grid_size - 1);

            cells[cell_x][cell_y][cell_z].points.push(point);
        }

        // Calculate average colors and bounds for each cell
        for x in 0..grid_size {
            for y in 0..grid_size {
                for z in 0..grid_size {
                    if !cells[x][y][z].points.is_empty() {
                        cells[x][y][z].calculate_metadata(&min, cell_size, x, y, z);
                    }
                }
            }
        }

        Self {
            cells,
            cell_size,
            grid_size,
            bounds: (min, max),
        }
    }

    /// Get visible cells for LOD rendering
    pub fn visible_cells(&self, cam: &Camera) -> Vec<&GridCell> {
        let mut visible = Vec::new();

        for x in 0..self.grid_size {
            for y in 0..self.grid_size {
                for z in 0..self.grid_size {
                    let cell = &self.cells[x][y][z];
                    if !cell.points.is_empty() && self.is_cell_visible(cell, cam) {
                        visible.push(cell);
                    }
                }
            }
        }

        visible
    }

    fn is_cell_visible(&self, cell: &GridCell, cam: &Camera) -> bool {
        // Simple frustum culling - check if any corner of the cell is visible
        let corners = [
            cell.bounds.0,
            vec3(cell.bounds.1.x, cell.bounds.0.y, cell.bounds.0.z),
            vec3(cell.bounds.0.x, cell.bounds.1.y, cell.bounds.0.z),
            vec3(cell.bounds.0.x, cell.bounds.0.y, cell.bounds.1.z),
            vec3(cell.bounds.1.x, cell.bounds.1.y, cell.bounds.0.z),
            vec3(cell.bounds.1.x, cell.bounds.0.y, cell.bounds.1.z),
            vec3(cell.bounds.0.x, cell.bounds.1.y, cell.bounds.1.z),
            cell.bounds.1,
        ];

        for corner in &corners {
            let dir = (*corner - cam.pos).normalize();
            let forward = cam.forward();
            if dir.dot(&forward) > 0.0 {
                return true;
            }
        }
        
        false
    }
}

impl GridCell {
    fn empty() -> Self {
        Self {
            points: Vec::new(),
            average_color: Color::White,
            bounds: (vec3(0.0, 0.0, 0.0), vec3(0.0, 0.0, 0.0)),
        }
    }

    fn calculate_metadata(&mut self, grid_min: &Vec3, cell_size: f32, x: usize, y: usize, z: usize) {
        if self.points.is_empty() {
            return;
        }

        // Calculate bounds
        let cell_min = vec3(
            grid_min.x + x as f32 * cell_size,
            grid_min.y + y as f32 * cell_size,
            grid_min.z + z as f32 * cell_size,
        );
        let cell_max = vec3(
            cell_min.x + cell_size,
            cell_min.y + cell_size,
            cell_min.z + cell_size,
        );
        self.bounds = (cell_min, cell_max);

        // Calculate average color (simplified)
        self.average_color = self.points[0].color;
    }
}

/// Point cloud renderer with WebGL-style controls and Z-buffer
pub struct PointCloudRenderer {
    camera: Camera,
    points: Vec<Point3DColored>,
    grid: Option<UniformGrid>,
    zbuffer: ZBuffer,
    /// Brightness character ramp for depth visualization
    ///
    /// Defaults to ACEROLA_16 for optimal mobile LiDAR scan rendering.
    /// Can be changed via `with_brightness_ramp()` method.
    brightness_ramp: &'static str,
}

impl PointCloudRenderer {
    /// Create a new point cloud renderer with default settings
    ///
    /// Uses ACEROLA_16 brightness ramp by default for optimal visual quality.
    /// Automatically enables LOD (Level of Detail) for point clouds > 10,000 points.
    ///
    /// # Arguments
    ///
    /// * `points` - Vector of colored 3D points to render
    ///
    /// # Examples
    ///
    /// ```
    /// let points = vec![Point3DColored { pos: vec3(0.0, 0.0, 0.0), color: Color::White }];
    /// let renderer = PointCloudRenderer::new(points);
    /// ```
    pub fn new(points: Vec<Point3DColored>) -> Self {
        let (width, height) = size().unwrap_or((120, 40));
        
        Self {
            camera: Camera::new(),
            grid: if points.len() > 10000 { 
                Some(UniformGrid::new(&points, 64)) 
            } else { 
                None 
            },
            points,
            zbuffer: ZBuffer::new(width as usize, height as usize),
            brightness_ramp: brightness_ramps::ACEROLA_16,
        }
    }

    /// Set custom brightness ramp (builder pattern)
    ///
    /// Allows customization of the ASCII character set used for rendering.
    ///
    /// # Arguments
    ///
    /// * `ramp` - Static string slice containing brightness characters
    ///
    /// # Examples
    ///
    /// ```
    /// use brightness_ramps::*;
    ///
    /// // Use classic 9-level ramp
    /// let renderer = PointCloudRenderer::new(points)
    ///     .with_brightness_ramp(CLASSIC);
    ///
    /// // Use Unicode blocks
    /// let renderer = PointCloudRenderer::new(points)
    ///     .with_brightness_ramp(UNICODE_16);
    /// ```
    pub fn with_brightness_ramp(mut self, ramp: &'static str) -> Self {
        self.brightness_ramp = ramp;
        self
    }

    /// Render point cloud with Z-buffer (Steps 1-4)
    pub fn render(&mut self) -> io::Result<()> {
        let (width, height) = size()?;
        self.zbuffer = ZBuffer::new(width as usize, height as usize);
        self.zbuffer.clear();

        // Step 5: LOD rendering if we have a lot of points
        if let Some(grid) = self.grid.clone() {
            self.render_with_lod(&grid, width, height)?;
        } else {
            self.render_direct(width, height)?;
        }

        // Output to terminal
        execute!(io::stdout(), cursor::MoveTo(0, 0))?;
        print!("{}", self.zbuffer.render_to_string());
        io::stdout().flush()?;

        Ok(())
    }

    /// Direct rendering for smaller point clouds
    ///
    /// Renders each point individually using the configured brightness ramp.
    /// Uses Z-buffer for proper depth sorting.
    fn render_direct(&mut self, width: u16, height: u16) -> io::Result<()> {
        for point in &self.points {
            if let Some((x, y, depth)) = project(point.pos, &self.camera, width, height) {
                // Map depth to brightness character using configured ramp
                let ch = get_brightness_char(depth, self.brightness_ramp);

                // Z-buffer depth test
                self.zbuffer.set_pixel(x, y, depth, ch);
            }
        }
        Ok(())
    }

    /// LOD rendering for massive point clouds (Step 5)
    ///
    /// Uses uniform grid for frustum culling and adaptive detail levels.
    /// Dense cells are rendered as single bright characters, sparse cells show individual points.
    fn render_with_lod(&mut self, grid: &UniformGrid, width: u16, height: u16) -> io::Result<()> {
        let visible_cells = grid.visible_cells(&self.camera);

        for cell in visible_cells {
            let screen_area = self.projected_area_of_cell(cell, width, height);

            // If cell covers < 2×2 terminal pixels → render as single bright character
            if screen_area < 4.0 {
                if let Some(center) = self.cell_center(cell) {
                    if let Some((x, y, depth)) = project(center, &self.camera, width, height) {
                        // Use brightest character from ramp for dense cells
                        let ch = self.brightness_ramp.chars().last().unwrap_or('█');
                        self.zbuffer.set_pixel(x, y, depth, ch);
                    }
                }
            } else {
                // Render individual points in the cell with depth-based brightness
                for point in &cell.points {
                    if let Some((x, y, depth)) = project(point.pos, &self.camera, width, height) {
                        let ch = get_brightness_char(depth, self.brightness_ramp);
                        self.zbuffer.set_pixel(x, y, depth, ch);
                    }
                }
            }
        }
        Ok(())
    }

    fn projected_area_of_cell(&self, cell: &GridCell, width: u16, height: u16) -> f32 {
        // Simplified: just check if the cell center projects to screen
        if let Some(center) = self.cell_center(cell) {
            if project(center, &self.camera, width, height).is_some() {
                // Rough estimate based on distance
                let dist = (center - self.camera.pos).length();
                let approx_size = 100.0 / dist; // Simple projection approximation
                approx_size * approx_size
            } else {
                0.0
            }
        } else {
            0.0
        }
    }

    fn cell_center(&self, cell: &GridCell) -> Option<Vec3> {
        if cell.points.is_empty() {
            None
        } else {
            let center = vec3(
                (cell.bounds.0.x + cell.bounds.1.x) * 0.5,
                (cell.bounds.0.y + cell.bounds.1.y) * 0.5,
                (cell.bounds.0.z + cell.bounds.1.z) * 0.5,
            );
            Some(center)
        }
    }

    /// Handle input events (exactly like OrbitControls)
    pub fn handle_event(&mut self, event: Event) -> bool {
        match event {
            Event::Key(key) => {
                match key.code {
                    KeyCode::Esc => return false,
                    
                    // WASD movement (Step 1)
                    KeyCode::Char('w') | KeyCode::Char('W') => {
                        self.camera.move_camera(1.0, 0.0, 0.0, 5.0);
                    }
                    KeyCode::Char('s') | KeyCode::Char('S') => {
                        self.camera.move_camera(-1.0, 0.0, 0.0, 5.0);
                    }
                    KeyCode::Char('a') | KeyCode::Char('A') => {
                        self.camera.move_camera(0.0, -1.0, 0.0, 5.0);
                    }
                    KeyCode::Char('d') | KeyCode::Char('D') => {
                        self.camera.move_camera(0.0, 1.0, 0.0, 5.0);
                    }
                    KeyCode::Char('e') | KeyCode::Char('E') => {
                        self.camera.move_camera(0.0, 0.0, 1.0, 5.0);
                    }
                    KeyCode::Char('q') | KeyCode::Char('Q') => {
                        return false; // Quit on Q
                    }
                    
                    // Arrow keys for orbit (Step 1)
                    KeyCode::Left => {
                        self.camera.orbit(-0.1, 0.0, 1.0);
                    }
                    KeyCode::Right => {
                        self.camera.orbit(0.1, 0.0, 1.0);
                    }
                    KeyCode::Up => {
                        self.camera.orbit(0.0, 0.1, 1.0);
                    }
                    KeyCode::Down => {
                        self.camera.orbit(0.0, -0.1, 1.0);
                    }
                    
                    // Zoom with +/-
                    KeyCode::Char('+') | KeyCode::Char('=') => {
                        self.camera.zoom(-0.1, 0.1);
                    }
                    KeyCode::Char('-') | KeyCode::Char('_') => {
                        self.camera.zoom(0.1, 0.1);
                    }
                    
                    _ => {}
                }
                true
            }
            Event::Mouse(mouse) => {
                match mouse.kind {
                    MouseEventKind::Drag(button) => {
                        // Mouse drag orbiting (Step 1)
                        if let crossterm::event::MouseButton::Left = button {
                            // Use mouse position as delta (simplified)
                            let delta_x = (mouse.column as f32 - 60.0) / 60.0 * 0.05;
                            let delta_y = (mouse.row as f32 - 20.0) / 20.0 * 0.05;
                            self.camera.orbit(delta_x, delta_y, 1.0);
                        }
                    }
                    MouseEventKind::ScrollUp => {
                        self.camera.zoom(-0.1, 0.1);
                    }
                    MouseEventKind::ScrollDown => {
                        self.camera.zoom(0.1, 0.1);
                    }
                    _ => {}
                }
                true
            }
            _ => true,
        }
    }

    /// Interactive rendering loop (exactly like WebGL app)
    pub fn run_interactive(&mut self) -> io::Result<()> {
        // Enable raw mode for input
        crossterm::terminal::enable_raw_mode()?;

        // Clear screen
        execute!(io::stdout(), Clear(ClearType::All), cursor::Hide)?;

        let mut running = true;
        while running {
            // Render frame
            self.render()?;

            // Show controls
            execute!(
                io::stdout(),
                cursor::MoveTo(0, 0),
                Print("Controls: WASD=move, arrows=orbit, +/-=zoom, q=quit")
            )?;

            // Handle input
            if crossterm::event::poll(std::time::Duration::from_millis(50))? {
                let event = crossterm::event::read()?;
                running = self.handle_event(event);
            }
        }

        // Cleanup
        execute!(io::stdout(), cursor::Show, Clear(ClearType::All))?;
        crossterm::terminal::disable_raw_mode()?;

        Ok(())
    }
}

/// Convert building data to colored point cloud
pub fn building_to_point_cloud(scene: &Scene3D) -> Vec<Point3DColored> {
    let mut points = Vec::new();

    // Convert equipment to points
    for equipment in &scene.equipment {
        let color = match equipment.equipment_type {
            EquipmentType::HVAC => Color::Red,
            EquipmentType::Electrical => Color::Yellow,
            EquipmentType::Network => Color::Blue,
            EquipmentType::Safety => Color::Magenta,
            EquipmentType::AV => Color::Cyan,
            EquipmentType::Plumbing => Color::Green,
            EquipmentType::Furniture => Color::White,
            _ => Color::DarkGrey,
        };

        points.push(Point3DColored {
            pos: vec3(
                equipment.position.x as f32,
                equipment.position.y as f32,
                equipment.position.z as f32,
            ),
            color,
        });
    }

    // Convert room corners to points
    for room in &scene.rooms {
        let corners = [
            vec3(room.bounding_box.min.x as f32, room.bounding_box.min.y as f32, room.bounding_box.min.z as f32),
            vec3(room.bounding_box.max.x as f32, room.bounding_box.min.y as f32, room.bounding_box.min.z as f32),
            vec3(room.bounding_box.min.x as f32, room.bounding_box.max.y as f32, room.bounding_box.min.z as f32),
            vec3(room.bounding_box.max.x as f32, room.bounding_box.max.y as f32, room.bounding_box.min.z as f32),
            vec3(room.bounding_box.min.x as f32, room.bounding_box.min.y as f32, room.bounding_box.max.z as f32),
            vec3(room.bounding_box.max.x as f32, room.bounding_box.min.y as f32, room.bounding_box.max.z as f32),
            vec3(room.bounding_box.min.x as f32, room.bounding_box.max.y as f32, room.bounding_box.max.z as f32),
            vec3(room.bounding_box.max.x as f32, room.bounding_box.max.y as f32, room.bounding_box.max.z as f32),
        ];

        for corner in corners {
            points.push(Point3DColored {
                pos: corner,
                color: Color::DarkGrey,
            });
        }
    }

    points
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_zbuffer_creation() {
        let zbuffer = ZBuffer::new(10, 5);
        assert_eq!(zbuffer.width, 10);
        assert_eq!(zbuffer.height, 5);
    }

    #[test]
    fn test_zbuffer_depth_test() {
        let mut zbuffer = ZBuffer::new(10, 5);
        
        // First pixel should be set
        assert!(zbuffer.set_pixel(5, 2, 1.0, 'A'));
        
        // Closer pixel should replace
        assert!(zbuffer.set_pixel(5, 2, 2.0, 'B'));
        
        // Further pixel should not replace
        assert!(!zbuffer.set_pixel(5, 2, 0.5, 'C'));
    }

    #[test]
    fn test_uniform_grid_creation() {
        let points = vec![
            Point3DColored { pos: vec3(0.0, 0.0, 0.0), color: Color::Red },
            Point3DColored { pos: vec3(10.0, 10.0, 10.0), color: Color::Blue },
        ];
        
        let grid = UniformGrid::new(&points, 8);
        assert_eq!(grid.grid_size, 8);
        assert!(!grid.cells[0][0][0].points.is_empty() || !grid.cells[7][7][7].points.is_empty());
    }

    #[test]
    fn test_camera_controls() {
        let mut camera = Camera::new();
        let initial_pos = camera.pos;
        
        // Test movement
        camera.move_camera(1.0, 0.0, 0.0, 5.0);
        assert!(camera.pos.x != initial_pos.x || camera.pos.y != initial_pos.y || camera.pos.z != initial_pos.z);
        
        // Test orbit
        let initial_yaw = camera.yaw;
        camera.orbit(0.1, 0.0, 1.0);
        assert!(camera.yaw != initial_yaw);
    }

    // ============================================================================
    // Brightness Ramp System Tests
    // ============================================================================

    #[test]
    fn test_brightness_ramp_lengths() {
        // Verify all ramps have correct character counts
        assert_eq!(brightness_ramps::CLASSIC.chars().count(), 9);
        assert_eq!(brightness_ramps::ACEROLA_16.chars().count(), 16);
        assert_eq!(brightness_ramps::EXTENDED_16.chars().count(), 16);
        assert_eq!(brightness_ramps::UNICODE_16.chars().count(), 16);
    }

    #[test]
    fn test_brightness_ramp_ordering() {
        // All ramps should start with space (darkest)
        assert_eq!(brightness_ramps::CLASSIC.chars().next().unwrap(), ' ');
        assert_eq!(brightness_ramps::ACEROLA_16.chars().next().unwrap(), ' ');
        
        // ACEROLA_16 should end with '$' (brightest)
        assert_eq!(brightness_ramps::ACEROLA_16.chars().last().unwrap(), '$');
    }

    #[test]
    fn test_get_brightness_char_bounds() {
        let ramp = brightness_ramps::ACEROLA_16;
        
        // Depth 0.0 should give first character (space)
        assert_eq!(get_brightness_char(0.0, ramp), ' ');
        
        // Depth 1.0 should give last character ($)
        assert_eq!(get_brightness_char(1.0, ramp), '$');
    }

    #[test]
    fn test_get_brightness_char_midrange() {
        let ramp = brightness_ramps::ACEROLA_16;
        
        // Mid-range depth should give middle character
        let ch = get_brightness_char(0.5, ramp);
        assert!(ch != ' ' && ch != '$');
        
        // Should be around index 7-8 for 16-character ramp
        let expected_chars = ['#', '%', '@'];
        assert!(expected_chars.contains(&ch));
    }

    #[test]
    fn test_get_brightness_char_progression() {
        let ramp = brightness_ramps::ACEROLA_16;
        
        // Verify smooth progression from dark to bright
        let depths = [0.0, 0.25, 0.5, 0.75, 1.0];
        let mut prev_idx = 0;
        
        for depth in depths {
            let ch = get_brightness_char(depth, ramp);
            let idx = ramp.chars().position(|c| c == ch).unwrap();
            
            // Each step should be at same or higher brightness
            assert!(idx >= prev_idx);
            prev_idx = idx;
        }
    }

    #[test]
    fn test_get_brightness_char_edge_cases() {
        let ramp = brightness_ramps::ACEROLA_16;
        
        // Negative depth should clamp to 0
        assert_eq!(get_brightness_char(-0.5, ramp), ' ');
        
        // Depth > 1.0 should clamp to max
        assert_eq!(get_brightness_char(2.0, ramp), '$');
    }

    #[test]
    fn test_point_cloud_renderer_default_ramp() {
        let points = vec![
            Point3DColored { 
                pos: vec3(0.0, 0.0, 0.0), 
                color: Color::White 
            },
        ];
        
        let renderer = PointCloudRenderer::new(points);
        
        // Should default to ACEROLA_16
        assert_eq!(renderer.brightness_ramp, brightness_ramps::ACEROLA_16);
    }

    #[test]
    fn test_point_cloud_renderer_custom_ramp() {
        let points = vec![
            Point3DColored { 
                pos: vec3(0.0, 0.0, 0.0), 
                color: Color::White 
            },
        ];
        
        // Test builder pattern with different ramps
        let renderer = PointCloudRenderer::new(points.clone())
            .with_brightness_ramp(brightness_ramps::CLASSIC);
        assert_eq!(renderer.brightness_ramp, brightness_ramps::CLASSIC);
        
        let renderer = PointCloudRenderer::new(points.clone())
            .with_brightness_ramp(brightness_ramps::UNICODE_16);
        assert_eq!(renderer.brightness_ramp, brightness_ramps::UNICODE_16);
    }

    #[test]
    fn test_acerola_16_specific_characters() {
        // Verify the exact Acerola character set
        let expected = " .:-=+*#%@MWBQ&$";
        assert_eq!(brightness_ramps::ACEROLA_16, expected);
        
        // Verify key characters at specific positions
        let chars: Vec<char> = brightness_ramps::ACEROLA_16.chars().collect();
        assert_eq!(chars[0], ' ');   // Darkest
        assert_eq!(chars[8], '%');   // Mid-range
        assert_eq!(chars[15], '$');  // Brightest
    }

    #[test]
    fn test_lod_threshold() {
        // Small point cloud should not use LOD
        let small_points: Vec<Point3DColored> = (0..5000)
            .map(|i| Point3DColored {
                pos: vec3(i as f32, 0.0, 0.0),
                color: Color::White,
            })
            .collect();
        
        let renderer = PointCloudRenderer::new(small_points);
        assert!(renderer.grid.is_none());
        
        // Large point cloud should use LOD
        let large_points: Vec<Point3DColored> = (0..15000)
            .map(|i| Point3DColored {
                pos: vec3(i as f32, 0.0, 0.0),
                color: Color::White,
            })
            .collect();
        
        let renderer = PointCloudRenderer::new(large_points);
        assert!(renderer.grid.is_some());
    }

    #[test]
    fn test_brightness_ramp_no_duplicates() {
        // Each ramp should have unique characters for best visual distinction
        for (name, ramp) in [
            ("CLASSIC", brightness_ramps::CLASSIC),
            ("ACEROLA_16", brightness_ramps::ACEROLA_16),
            ("EXTENDED_16", brightness_ramps::EXTENDED_16),
            ("UNICODE_16", brightness_ramps::UNICODE_16),
        ] {
            let chars: Vec<char> = ramp.chars().collect();
            let unique_chars: std::collections::HashSet<char> = chars.iter().copied().collect();
            
            assert_eq!(chars.len(), unique_chars.len(),
                "{} ramp should have no duplicate characters", name);
        }
    }
}