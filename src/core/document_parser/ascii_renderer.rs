//! ASCII Renderer for Building Floor Plans
//! 
//! Converts building data to ASCII art representation

use super::{BuildingPlan, FloorPlan, Room, Equipment, EquipmentType, Point3D};
use std::collections::HashMap;

/// ASCII renderer for building plans
pub struct AsciiRenderer {
    /// Grid resolution (meters per character)
    grid_resolution: f32,
    /// Character width for output
    width: usize,
    /// Character height for output
    height: usize,
}

impl AsciiRenderer {
    /// Create new ASCII renderer
    pub fn new() -> Self {
        Self {
            grid_resolution: 0.5,  // 0.5 meters per character
            width: 80,
            height: 30,
        }
    }
    
    /// Render entire building
    pub fn render_building(&self, plan: &BuildingPlan) -> String {
        let mut output = String::new();
        
        // Building header
        output.push_str(&self.render_header(&plan.name));
        output.push('\n');
        
        // Render each floor
        for floor in &plan.floors {
            output.push_str(&self.render_floor(floor));
            output.push('\n');
        }
        
        // Building summary
        output.push_str(&self.render_summary(plan));
        
        output
    }
    
    /// Render building header
    fn render_header(&self, name: &str) -> String {
        let mut header = String::new();
        header.push_str("╔════════════════════════════════════════════════════════════════════════════╗\n");
        header.push_str(&format!("║{:^76}║\n", name.to_uppercase()));
        header.push_str("║                          ASCII BUILDING INTELLIGENCE                      ║\n");
        header.push_str("╚════════════════════════════════════════════════════════════════════════════╝\n");
        header
    }
    
    /// Render single floor
    pub fn render_floor(&self, floor: &FloorPlan) -> String {
        let mut output = String::new();
        
        // Floor header
        output.push_str(&format!("\n═══ FLOOR {} ═══\n", floor.floor_number));
        
        // Create grid
        let mut grid = self.create_grid();
        
        // Draw rooms
        for room in &floor.rooms {
            self.draw_room(&mut grid, room);
        }
        
        // Place equipment
        for equipment in &floor.equipment {
            self.place_equipment(&mut grid, equipment);
        }
        
        // Add borders
        self.add_borders(&mut grid);
        
        // Convert grid to string
        output.push_str(&self.grid_to_string(&grid));
        
        // Room legend
        output.push_str(&self.render_room_legend(&floor.rooms));
        
        output
    }
    
    /// Create empty grid
    fn create_grid(&self) -> Vec<Vec<char>> {
        vec![vec![' '; self.width]; self.height]
    }
    
    /// Draw room on grid
    fn draw_room(&self, grid: &mut Vec<Vec<char>>, room: &Room) {
        // Convert room bounds to grid coordinates
        let min_x = self.world_to_grid_x(room.bounds.min.x);
        let max_x = self.world_to_grid_x(room.bounds.max.x);
        let min_y = self.world_to_grid_y(room.bounds.min.y);
        let max_y = self.world_to_grid_y(room.bounds.max.y);
        
        // Draw room walls
        for x in min_x..=max_x {
            if x < self.width {
                grid[min_y][x] = '─';
                grid[max_y][x] = '─';
            }
        }
        
        for y in min_y..=max_y {
            if y < self.height {
                grid[y][min_x] = '│';
                grid[y][max_x] = '│';
            }
        }
        
        // Draw corners
        if min_x < self.width && min_y < self.height {
            grid[min_y][min_x] = '┌';
        }
        if max_x < self.width && min_y < self.height {
            grid[min_y][max_x] = '┐';
        }
        if min_x < self.width && max_y < self.height {
            grid[max_y][min_x] = '└';
        }
        if max_x < self.width && max_y < self.height {
            grid[max_y][max_x] = '┘';
        }
        
        // Add room number in center
        let center_x = (min_x + max_x) / 2;
        let center_y = (min_y + max_y) / 2;
        
        if center_x < self.width - 3 && center_y < self.height {
            for (i, ch) in room.number.chars().take(4).enumerate() {
                if center_x + i < self.width {
                    grid[center_y][center_x + i] = ch;
                }
            }
        }
    }
    
    /// Place equipment on grid
    fn place_equipment(&self, grid: &mut Vec<Vec<char>>, equipment: &Equipment) {
        let x = self.world_to_grid_x(equipment.location.x);
        let y = self.world_to_grid_y(equipment.location.y);
        
        let symbol = equipment.equipment_type.to_ascii_symbol();
        
        // Place symbol (handling multi-character symbols)
        for (i, ch) in symbol.chars().enumerate() {
            if x + i < self.width && y < self.height {
                // Don't overwrite walls
                if grid[y][x + i] == ' ' {
                    grid[y][x + i] = ch;
                }
            }
        }
    }
    
    /// Add borders to grid
    fn add_borders(&self, grid: &mut Vec<Vec<char>>) {
        // Top border
        for x in 0..self.width {
            if grid[0][x] == ' ' {
                grid[0][x] = '═';
            }
        }
        
        // Bottom border
        for x in 0..self.width {
            if grid[self.height - 1][x] == ' ' {
                grid[self.height - 1][x] = '═';
            }
        }
        
        // Left border
        for y in 0..self.height {
            if grid[y][0] == ' ' {
                grid[y][0] = '║';
            }
        }
        
        // Right border
        for y in 0..self.height {
            if grid[y][self.width - 1] == ' ' {
                grid[y][self.width - 1] = '║';
            }
        }
        
        // Corners
        grid[0][0] = '╔';
        grid[0][self.width - 1] = '╗';
        grid[self.height - 1][0] = '╚';
        grid[self.height - 1][self.width - 1] = '╝';
    }
    
    /// Convert grid to string
    fn grid_to_string(&self, grid: &Vec<Vec<char>>) -> String {
        grid.iter()
            .map(|row| row.iter().collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    }
    
    /// Render room legend
    fn render_room_legend(&self, rooms: &[Room]) -> String {
        let mut legend = String::new();
        legend.push_str("\nROOMS:\n");
        
        for room in rooms {
            legend.push_str(&format!("  {} - {} ({:.0} sq ft)\n", 
                room.number, room.name, room.area_sqft));
        }
        
        legend
    }
    
    /// Render building summary
    fn render_summary(&self, plan: &BuildingPlan) -> String {
        let mut summary = String::new();
        
        summary.push_str("\n╔════════════════════════════════════════════════════════════════════════════╗\n");
        summary.push_str("║                              BUILDING SUMMARY                             ║\n");
        summary.push_str("╠════════════════════════════════════════════════════════════════════════════╣\n");
        
        // Count equipment by type
        let mut equipment_counts: HashMap<EquipmentType, usize> = HashMap::new();
        for floor in &plan.floors {
            for eq in &floor.equipment {
                *equipment_counts.entry(eq.equipment_type).or_insert(0) += 1;
            }
        }
        
        summary.push_str(&format!("║ Total Floors: {:3}                                                          ║\n", 
            plan.floors.len()));
        summary.push_str(&format!("║ Total Rooms: {:4}                                                          ║\n",
            plan.floors.iter().map(|f| f.rooms.len()).sum::<usize>()));
        
        summary.push_str("║                                                                            ║\n");
        summary.push_str("║ EQUIPMENT INVENTORY:                                                      ║\n");
        
        for (eq_type, count) in equipment_counts {
            let eq_name = format!("{:?}", eq_type);
            summary.push_str(&format!("║   {:30} {:>10} units                       ║\n", 
                eq_name, count));
        }
        
        summary.push_str("║                                                                            ║\n");
        summary.push_str("║ LEGEND:                                                                    ║\n");
        summary.push_str("║   [O] Outlet    [L] Light     [V] Vent      [F] Fire Alarm               ║\n");
        summary.push_str("║   [S] Smoke     [E] Exit      [T] Thermostat [D] Door                    ║\n");
        summary.push_str("║   [W] Window    [C] Camera    [*] Sprinkler  [/] Switch                  ║\n");
        summary.push_str("╚════════════════════════════════════════════════════════════════════════════╝\n");
        
        summary
    }
    
    /// Convert world coordinates to grid X
    fn world_to_grid_x(&self, x: f32) -> usize {
        ((x / self.grid_resolution) as usize).min(self.width - 1)
    }
    
    /// Convert world coordinates to grid Y
    fn world_to_grid_y(&self, y: f32) -> usize {
        ((y / self.grid_resolution) as usize).min(self.height - 1)
    }
}