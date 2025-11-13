//! WebGL-style point cloud renderer with Z-buffer and LOD
//! Exactly matches the 5-step implementation pattern

use super::camera::{Camera, Vec3, vec3, project};
use super::types::*;
use arx::EquipmentType;
use crossterm::event::{Event, KeyCode, MouseEventKind};
use crossterm::style::{Color, Print};
use crossterm::terminal::{size, Clear, ClearType};
use crossterm::{cursor, execute};

use std::io::{self, Write};

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
    #[allow(dead_code)]
    cell_size: f32,
    grid_size: usize,
    #[allow(dead_code)]
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
}

impl PointCloudRenderer {
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
        }
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
    fn render_direct(&mut self, width: u16, height: u16) -> io::Result<()> {
        for point in &self.points {
            if let Some((x, y, depth)) = project(point.pos, &self.camera, width, height) {
                // Step 3: Brightness based on depth
                let brightness = (depth * 8.0).min(7.0) as usize;
                let ch = " .,:;+*#█".chars().nth(brightness).unwrap_or(' ');

                // Step 3: Z-buffer test
                self.zbuffer.set_pixel(x, y, depth, ch);
            }
        }
        Ok(())
    }

    /// LOD rendering for massive point clouds (Step 5)
    fn render_with_lod(&mut self, grid: &UniformGrid, width: u16, height: u16) -> io::Result<()> {
        let visible_cells = grid.visible_cells(&self.camera);

        for cell in visible_cells {
            let screen_area = self.projected_area_of_cell(cell, width, height);

            // If cell covers < 2×2 terminal pixels → render as single bright block
            if screen_area < 4.0 {
                if let Some(center) = self.cell_center(cell) {
                    if let Some((x, y, depth)) = project(center, &self.camera, width, height) {
                        // Step 4: Use Unicode blocks for better visual quality
                        let ch = if cell.points.len() > 100 { '█' } else { '▓' };
                        self.zbuffer.set_pixel(x, y, depth, ch);
                    }
                }
            } else {
                // Render individual points in the cell
                for point in &cell.points {
                    if let Some((x, y, depth)) = project(point.pos, &self.camera, width, height) {
                        let brightness = (depth * 8.0).min(7.0) as usize;
                        let ch = " .,:;+*#█".chars().nth(brightness).unwrap_or(' ');
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
}