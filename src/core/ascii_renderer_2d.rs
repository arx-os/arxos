//! 2D ASCII Renderer for Building Visualization
//! 
//! Converts ArxObjects into explorable top-down ASCII maps

use crate::arxobject::{ArxObject, object_types};
use std::collections::HashMap;

/// 2D grid for ASCII rendering
pub struct AsciiGrid {
    width: usize,
    height: usize,
    cells: Vec<Vec<char>>,
    objects: HashMap<(usize, usize), ArxObject>,
    scale: f32, // meters per cell
}

impl AsciiGrid {
    /// Create new ASCII grid
    pub fn new(width: usize, height: usize, scale: f32) -> Self {
        let cells = vec![vec![' '; width]; height];
        Self {
            width,
            height,
            cells,
            objects: HashMap::new(),
            scale,
        }
    }
    
    /// Clear the grid
    pub fn clear(&mut self) {
        for row in &mut self.cells {
            for cell in row {
                *cell = ' ';
            }
        }
        self.objects.clear();
    }
    
    /// Place an ArxObject on the grid
    pub fn place_object(&mut self, obj: &ArxObject, origin_x: f32, origin_y: f32) {
        let (x_m, y_m, _z_m) = obj.position_meters();
        
        // Convert world coordinates to grid coordinates
        let grid_x = ((x_m - origin_x) / self.scale) as usize;
        let grid_y = ((y_m - origin_y) / self.scale) as usize;
        
        if grid_x < self.width && grid_y < self.height {
            // Store object reference
            self.objects.insert((grid_x, grid_y), *obj);
            
            // Render object as ASCII
            let symbol = match obj.object_type {
                object_types::WALL => '█',
                object_types::FLOOR => '·',
                object_types::DOOR => '╪',
                object_types::WINDOW => '═',
                object_types::OUTLET => 'o',
                object_types::LIGHT_SWITCH => '/',
                object_types::LIGHT => '*',
                object_types::THERMOSTAT => 'T',
                object_types::SMOKE_DETECTOR => 'S',
                object_types::FIRE_ALARM => 'F',
                object_types::EMERGENCY_EXIT => 'E',
                object_types::HVAC_VENT => '#',
                object_types::CAMERA => 'C',
                object_types::MOTION_SENSOR => 'M',
                _ => '?',
            };
            
            self.cells[grid_y][grid_x] = symbol;
        }
    }
    
    /// Draw a line of walls
    pub fn draw_wall(&mut self, x1: usize, y1: usize, x2: usize, y2: usize) {
        if x1 == x2 {
            // Vertical wall
            let (start, end) = if y1 < y2 { (y1, y2) } else { (y2, y1) };
            for y in start..=end {
                if y < self.height && x1 < self.width {
                    self.cells[y][x1] = '║';
                }
            }
        } else if y1 == y2 {
            // Horizontal wall
            let (start, end) = if x1 < x2 { (x1, x2) } else { (x2, x1) };
            for x in start..=end {
                if y1 < self.height && x < self.width {
                    self.cells[y1][x] = '═';
                }
            }
        }
    }
    
    /// Draw a box (room)
    pub fn draw_room(&mut self, x: usize, y: usize, width: usize, height: usize) {
        // Corners
        if x < self.width && y < self.height {
            self.cells[y][x] = '╔';
        }
        if x + width < self.width && y < self.height {
            self.cells[y][x + width] = '╗';
        }
        if x < self.width && y + height < self.height {
            self.cells[y + height][x] = '╚';
        }
        if x + width < self.width && y + height < self.height {
            self.cells[y + height][x + width] = '╝';
        }
        
        // Walls
        self.draw_wall(x + 1, y, x + width - 1, y);
        self.draw_wall(x + 1, y + height, x + width - 1, y + height);
        self.draw_wall(x, y + 1, x, y + height - 1);
        self.draw_wall(x + width, y + 1, x + width, y + height - 1);
    }
    
    /// Get object at position
    pub fn get_object_at(&self, x: usize, y: usize) -> Option<&ArxObject> {
        self.objects.get(&(x, y))
    }
    
    /// Render grid to string
    pub fn render(&self) -> String {
        let mut output = String::new();
        
        for row in &self.cells {
            for &ch in row {
                output.push(ch);
            }
            output.push('\n');
        }
        
        output
    }
    
    /// Render with player position
    pub fn render_with_player(&self, player_x: usize, player_y: usize) -> String {
        let mut output = String::new();
        
        for (y, row) in self.cells.iter().enumerate() {
            for (x, &ch) in row.iter().enumerate() {
                if x == player_x && y == player_y {
                    output.push('@');
                } else {
                    output.push(ch);
                }
            }
            output.push('\n');
        }
        
        output
    }
}

/// Building floor renderer
pub struct FloorRenderer {
    grid: AsciiGrid,
    objects: Vec<ArxObject>,
    bounds: (f32, f32, f32, f32), // min_x, min_y, max_x, max_y
}

impl FloorRenderer {
    /// Create renderer for a floor
    pub fn new(objects: Vec<ArxObject>, floor_height: f32, tolerance: f32) -> Self {
        // Filter objects to this floor
        let floor_objects: Vec<ArxObject> = objects
            .into_iter()
            .filter(|obj| {
                let (_x, _y, z) = obj.position_meters();
                (z - floor_height).abs() < tolerance
            })
            .collect();
        
        // Calculate bounds
        let mut min_x = f32::MAX;
        let mut max_x = f32::MIN;
        let mut min_y = f32::MAX;
        let mut max_y = f32::MIN;
        
        for obj in &floor_objects {
            let (x, y, _z) = obj.position_meters();
            min_x = min_x.min(x);
            max_x = max_x.max(x);
            min_y = min_y.min(y);
            max_y = max_y.max(y);
        }
        
        // Add padding
        min_x -= 1.0;
        min_y -= 1.0;
        max_x += 1.0;
        max_y += 1.0;
        
        // Create grid
        let scale = 0.25; // 25cm per cell
        let width = ((max_x - min_x) / scale) as usize + 1;
        let height = ((max_y - min_y) / scale) as usize + 1;
        
        let grid = AsciiGrid::new(width.min(120), height.min(40), scale);
        
        Self {
            grid,
            objects: floor_objects,
            bounds: (min_x, min_y, max_x, max_y),
        }
    }
    
    /// Render the floor
    pub fn render(&mut self) -> String {
        self.grid.clear();
        
        // Place all objects
        for obj in &self.objects {
            self.grid.place_object(obj, self.bounds.0, self.bounds.1);
        }
        
        // Detect and draw walls (objects in lines)
        self.detect_walls();
        
        self.grid.render()
    }
    
    /// Detect wall patterns
    fn detect_walls(&mut self) {
        // Group wall objects by alignment
        let walls: Vec<&ArxObject> = self.objects
            .iter()
            .filter(|obj| obj.object_type == object_types::WALL)
            .collect();
        
        // Simple wall detection - connect nearby wall objects
        for i in 0..walls.len() {
            for j in i+1..walls.len() {
                let (x1, y1, _) = walls[i].position_meters();
                let (x2, y2, _) = walls[j].position_meters();
                
                let dist = ((x2-x1).powi(2) + (y2-y1).powi(2)).sqrt();
                
                // If walls are close, connect them
                if dist < 1.0 {
                    let gx1 = ((x1 - self.bounds.0) / self.grid.scale) as usize;
                    let gy1 = ((y1 - self.bounds.1) / self.grid.scale) as usize;
                    let gx2 = ((x2 - self.bounds.0) / self.grid.scale) as usize;
                    let gy2 = ((y2 - self.bounds.1) / self.grid.scale) as usize;
                    
                    self.grid.draw_wall(gx1, gy1, gx2, gy2);
                }
            }
        }
    }
    
    /// Get object info at grid position
    pub fn inspect(&self, x: usize, y: usize) -> Option<String> {
        if let Some(obj) = self.grid.get_object_at(x, y) {
            let (x_m, y_m, z_m) = obj.position_meters();
            let obj_type = match obj.object_type {
                object_types::OUTLET => "Electrical Outlet",
                object_types::LIGHT_SWITCH => "Light Switch",
                object_types::THERMOSTAT => "Thermostat",
                object_types::SMOKE_DETECTOR => "Smoke Detector",
                object_types::LIGHT => "Light Fixture",
                object_types::HVAC_VENT => "HVAC Vent",
                _ => "Unknown Object",
            };
            
            Some(format!(
                "{}\nPosition: ({:.2}m, {:.2}m, {:.2}m)\nType: 0x{:02X}",
                obj_type, x_m, y_m, z_m, obj.object_type
            ))
        } else {
            None
        }
    }
}