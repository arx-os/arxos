// Terminal rendering for ArxOS
use crate::yaml::{BuildingData, FloorData, RoomData, EquipmentData, EquipmentStatus};

pub struct BuildingRenderer {
    building_data: BuildingData,
}

impl BuildingRenderer {
    pub fn new(building_data: BuildingData) -> Self {
        Self { building_data }
    }
    
    pub fn floors(&self) -> &Vec<FloorData> {
        &self.building_data.floors
    }
    
    pub fn render_floor(&self, floor: i32) -> Result<(), Box<dyn std::error::Error>> {
        // Find the floor data
        let floor_data = self.building_data.floors.iter()
            .find(|f| f.level == floor)
            .ok_or_else(|| format!("Floor {} not found in building data", floor))?;
        
        println!("Building {} - Floor {} ({})", 
            self.building_data.building.name, 
            floor, 
            floor_data.name
        );
        
        // Render the floor plan
        self.render_floor_plan(floor_data)?;
        
        // Render equipment status summary
        self.render_equipment_summary(floor_data)?;
        
        Ok(())
    }
    
    fn render_floor_plan(&self, floor_data: &FloorData) -> Result<(), Box<dyn std::error::Error>> {
        if floor_data.rooms.is_empty() && floor_data.equipment.is_empty() {
            println!("┌─────────────────────────────────────────────────────────────┐");
            println!("│                    No data available                        │");
            println!("└─────────────────────────────────────────────────────────────┘");
            return Ok(());
        }
        
        // Calculate floor bounds
        let bounds = self.calculate_floor_bounds(floor_data);
        let (min_x, min_y, max_x, max_y) = bounds;
        
        // Scale for terminal display
        let width = ((max_x - min_x) * 2.0) as usize + 1;
        let height = ((max_y - min_y) * 2.0) as usize + 1;
        
        // Create ASCII grid
        let mut grid = vec![vec![' '; width]; height];
        
        // Draw rooms
        for room in &floor_data.rooms {
            self.draw_room(&mut grid, room, bounds)?;
        }
        
        // Draw equipment
        for equipment in &floor_data.equipment {
            self.draw_equipment(&mut grid, equipment, bounds)?;
        }
        
        // Render the grid
        println!("┌─────────────────────────────────────────────────────────────┐");
        for row in grid {
            println!("│ {:<61} │", row.iter().collect::<String>());
        }
        println!("└─────────────────────────────────────────────────────────────┘");
        
        Ok(())
    }
    
    fn calculate_floor_bounds(&self, floor_data: &FloorData) -> (f64, f64, f64, f64) {
        let mut min_x = f64::INFINITY;
        let mut min_y = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut max_y = f64::NEG_INFINITY;
        
        // Include room bounds
        for room in &floor_data.rooms {
            min_x = min_x.min(room.bounding_box.min.x);
            min_y = min_y.min(room.bounding_box.min.y);
            max_x = max_x.max(room.bounding_box.max.x);
            max_y = max_y.max(room.bounding_box.max.y);
        }
        
        // Include equipment bounds
        for equipment in &floor_data.equipment {
            min_x = min_x.min(equipment.bounding_box.min.x);
            min_y = min_y.min(equipment.bounding_box.min.y);
            max_x = max_x.max(equipment.bounding_box.max.x);
            max_y = max_y.max(equipment.bounding_box.max.y);
        }
        
        // Add padding
        let padding = 1.0;
        (min_x - padding, min_y - padding, max_x + padding, max_y + padding)
    }
    
    fn draw_room(&self, grid: &mut Vec<Vec<char>>, room: &RoomData, bounds: (f64, f64, f64, f64)) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;
        let width = grid[0].len();
        let height = grid.len();
        
        // Convert room position to grid coordinates
        let room_x = ((room.position.x - min_x) / (max_x - min_x) * (width - 1) as f64) as usize;
        let room_y = ((room.position.y - min_y) / (max_y - min_y) * (height - 1) as f64) as usize;
        
        // Draw room symbol
        if room_y < height && room_x < width {
            grid[room_y][room_x] = 'R';
        }
        
        Ok(())
    }
    
    fn draw_equipment(&self, grid: &mut Vec<Vec<char>>, equipment: &EquipmentData, bounds: (f64, f64, f64, f64)) -> Result<(), Box<dyn std::error::Error>> {
        let (min_x, min_y, max_x, max_y) = bounds;
        let width = grid[0].len();
        let height = grid.len();
        
        // Convert equipment position to grid coordinates
        let eq_x = ((equipment.position.x - min_x) / (max_x - min_x) * (width - 1) as f64) as usize;
        let eq_y = ((equipment.position.y - min_y) / (max_y - min_y) * (height - 1) as f64) as usize;
        
        // Draw equipment symbol based on type
        let symbol = self.get_equipment_symbol(equipment);
        
        if eq_y < height && eq_x < width {
            grid[eq_y][eq_x] = symbol;
        }
        
        Ok(())
    }
    
    fn get_equipment_symbol(&self, equipment: &EquipmentData) -> char {
        match equipment.system_type.as_str() {
            "HVAC" => 'H',
            "ELECTRICAL" => 'E',
            "PLUMBING" => 'P',
            "LIGHTS" => 'L',
            "SAFETY" => 'S',
            "STRUCTURAL" => 'T',
            "ARCHITECTURAL" => 'A',
            _ => '?',
        }
    }
    
    fn render_equipment_summary(&self, floor_data: &FloorData) -> Result<(), Box<dyn std::error::Error>> {
        let mut healthy = 0;
        let mut warnings = 0;
        let mut critical = 0;
        
        for equipment in &floor_data.equipment {
            match equipment.status {
                EquipmentStatus::Healthy => healthy += 1,
                EquipmentStatus::Warning => warnings += 1,
                EquipmentStatus::Critical => critical += 1,
                EquipmentStatus::Unknown => warnings += 1,
            }
        }
        
        println!("\nEquipment Status: ✅ {} healthy | ⚠️ {} warnings | ❌ {} critical", 
            healthy, warnings, critical);
        println!("Last Updated: {}", chrono::Utc::now().format("%H:%M:%S"));
        println!("Data Source: YAML building data");
        
        // Show equipment details
        if !floor_data.equipment.is_empty() {
            println!("\nEquipment Details:");
            for equipment in &floor_data.equipment {
                let status_icon = self.get_status_symbol(&equipment.status);
                println!("  {} {} ({}) - {}", 
                    status_icon, 
                    equipment.name, 
                    equipment.system_type,
                    equipment.universal_path
                );
            }
        }
        
        Ok(())
    }
    
    fn get_status_symbol(&self, status: &EquipmentStatus) -> &str {
        match status {
            EquipmentStatus::Healthy => "✅",
            EquipmentStatus::Warning => "⚠️",
            EquipmentStatus::Critical => "❌",
            EquipmentStatus::Unknown => "❓",
        }
    }
}
