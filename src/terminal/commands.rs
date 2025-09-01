//! Terminal command processing with document parser integration
//!
//! Handles local and remote commands including document loading

use arxos_core::document_parser::{DocumentParser, BuildingPlan};
use arxos_core::point_cloud_parser::PointCloudParser;
use std::path::Path;
use std::fs;
use log::{info, error};

/// Command processor for terminal
pub struct CommandProcessor {
    /// Document parser instance
    document_parser: DocumentParser,
    
    /// Point cloud parser instance
    point_cloud_parser: PointCloudParser,
    
    /// Currently loaded building plan
    current_plan: Option<BuildingPlan>,
    
    /// Current floor being viewed
    current_floor: i8,
}

impl CommandProcessor {
    /// Create new command processor
    pub fn new() -> Self {
        Self {
            document_parser: DocumentParser::new(),
            point_cloud_parser: PointCloudParser::new(),
            current_plan: None,
            current_floor: 0,
        }
    }
    
    /// Process a command and return output
    pub async fn process(&mut self, command: &str) -> CommandResult {
        let parts: Vec<&str> = command.split_whitespace().collect();
        
        if parts.is_empty() {
            return CommandResult::empty();
        }
        
        match parts[0] {
            "arxos" => self.process_arxos_command(&parts[1..]).await,
            "load-plan" => self.load_plan_command(&parts[1..]).await,
            "load-scan" => self.load_scan_command(&parts[1..]).await,
            "view-floor" => self.view_floor_command(&parts[1..]),
            "list-floors" => self.list_floors_command(),
            "show-equipment" => self.show_equipment_command(&parts[1..]),
            "export-arxobjects" => self.export_arxobjects_command(&parts[1..]),
            _ => CommandResult::error(format!("Unknown command: {}", parts[0])),
        }
    }
    
    /// Process arxos-specific commands
    async fn process_arxos_command(&mut self, args: &[&str]) -> CommandResult {
        if args.is_empty() {
            return CommandResult::error("Missing arxos subcommand".to_string());
        }
        
        match args[0] {
            "load-plan" => self.load_plan_command(&args[1..]).await,
            "view-floor" => self.view_floor_command(&args[1..]),
            "init" if args.len() >= 2 => {
                let building_name = args[1];
                CommandResult::success(format!("Initializing building: {}", building_name))
            }
            "query" if args.len() >= 2 => {
                let query = args[1..].join(" ");
                CommandResult::success(format!("Querying: {}", query))
            }
            _ => CommandResult::error(format!("Unknown arxos command: {}", args[0])),
        }
    }
    
    /// Load a building plan from PDF or IFC
    async fn load_plan_command(&mut self, args: &[&str]) -> CommandResult {
        if args.is_empty() {
            return CommandResult::error("Usage: load-plan <file_path>".to_string());
        }
        
        let file_path = args[0];
        
        // Check if file exists
        if !Path::new(file_path).exists() {
            return CommandResult::error(format!("File not found: {}", file_path));
        }
        
        info!("Loading building plan from: {}", file_path);
        
        // Parse the document
        match self.document_parser.parse_document(file_path).await {
            Ok(plan) => {
                let building_name = plan.name.clone();
                let floor_count = plan.floors.len();
                let room_count: usize = plan.floors.iter()
                    .map(|f| f.rooms.len())
                    .sum();
                
                // Generate ASCII preview
                let ascii = self.document_parser.generate_ascii(&plan);
                
                self.current_plan = Some(plan);
                self.current_floor = 0;
                
                let mut output = Vec::new();
                output.push(format!("Successfully loaded: {}", building_name));
                output.push(format!("  Floors: {}", floor_count));
                output.push(format!("  Total rooms: {}", room_count));
                output.push("".to_string());
                output.push("Building Overview:".to_string());
                output.push("".to_string());
                
                // Add ASCII representation
                for line in ascii.lines() {
                    output.push(line.to_string());
                }
                
                CommandResult::success_multi(output)
            }
            Err(e) => {
                error!("Failed to parse document: {}", e);
                CommandResult::error(format!("Failed to load plan: {}", e))
            }
        }
    }
    
    /// View a specific floor
    fn view_floor_command(&mut self, args: &[&str]) -> CommandResult {
        if self.current_plan.is_none() {
            return CommandResult::error("No building plan loaded. Use 'load-plan' first.".to_string());
        }
        
        let floor_num = if args.is_empty() {
            self.current_floor
        } else if let Some(level_arg) = args.iter().find(|a| a.starts_with("--level=")) {
            let level_str = level_arg.trim_start_matches("--level=");
            match level_str.parse::<i8>() {
                Ok(n) => n,
                Err(_) => return CommandResult::error("Invalid floor number".to_string()),
            }
        } else {
            match args[0].parse::<i8>() {
                Ok(n) => n,
                Err(_) => return CommandResult::error("Invalid floor number".to_string()),
            }
        };
        
        let plan = self.current_plan.as_ref().unwrap();
        
        // Find the floor
        if let Some(floor) = plan.floors.iter().find(|f| f.floor_number == floor_num) {
            self.current_floor = floor_num;
            
            let mut output = Vec::new();
            output.push(format!("Floor {} Layout:", floor_num));
            output.push("".to_string());
            
            // Show ASCII layout
            for line in floor.ascii_layout.lines() {
                output.push(line.to_string());
            }
            
            // Show room list
            output.push("".to_string());
            output.push("Rooms on this floor:".to_string());
            for room in &floor.rooms {
                output.push(format!("  {} - {} ({:.0} sq ft)", 
                    room.number, room.name, room.area_sqft));
            }
            
            // Show equipment summary
            output.push("".to_string());
            output.push(format!("Equipment: {} items", floor.equipment.len()));
            
            CommandResult::success_multi(output)
        } else {
            CommandResult::error(format!("Floor {} not found", floor_num))
        }
    }
    
    /// List all floors
    fn list_floors_command(&self) -> CommandResult {
        if self.current_plan.is_none() {
            return CommandResult::error("No building plan loaded. Use 'load-plan' first.".to_string());
        }
        
        let plan = self.current_plan.as_ref().unwrap();
        let mut output = Vec::new();
        
        output.push(format!("Building: {}", plan.name));
        output.push("Available floors:".to_string());
        
        for floor in &plan.floors {
            let room_count = floor.rooms.len();
            let equipment_count = floor.equipment.len();
            output.push(format!("  Floor {} - {} rooms, {} equipment items",
                floor.floor_number, room_count, equipment_count));
        }
        
        CommandResult::success_multi(output)
    }
    
    /// Show equipment on current floor
    fn show_equipment_command(&self, args: &[&str]) -> CommandResult {
        if self.current_plan.is_none() {
            return CommandResult::error("No building plan loaded. Use 'load-plan' first.".to_string());
        }
        
        let plan = self.current_plan.as_ref().unwrap();
        let floor_num = if args.is_empty() {
            self.current_floor
        } else {
            match args[0].parse::<i8>() {
                Ok(n) => n,
                Err(_) => return CommandResult::error("Invalid floor number".to_string()),
            }
        };
        
        if let Some(floor) = plan.floors.iter().find(|f| f.floor_number == floor_num) {
            let mut output = Vec::new();
            output.push(format!("Equipment on Floor {}:", floor_num));
            output.push("".to_string());
            
            // Group equipment by type
            use std::collections::HashMap;
            let mut equipment_by_type: HashMap<String, Vec<&arxos_core::document_parser::Equipment>> = HashMap::new();
            
            for eq in &floor.equipment {
                let type_name = format!("{:?}", eq.equipment_type);
                equipment_by_type.entry(type_name).or_insert_with(Vec::new).push(eq);
            }
            
            for (eq_type, items) in equipment_by_type {
                output.push(format!("{}:", eq_type));
                for item in items {
                    let room = item.room_number.as_ref()
                        .map(|s| s.as_str())
                        .unwrap_or("Unknown");
                    output.push(format!("  - Room {} @ ({:.1}, {:.1})",
                        room, item.location.x, item.location.y));
                }
            }
            
            CommandResult::success_multi(output)
        } else {
            CommandResult::error(format!("Floor {} not found", floor_num))
        }
    }
    
    /// Load a LiDAR scan from PLY file
    async fn load_scan_command(&mut self, args: &[&str]) -> CommandResult {
        if args.is_empty() {
            return CommandResult::error("Usage: load-scan <ply_file>".to_string());
        }
        
        let file_path = args[0];
        
        // Check if file exists
        if !Path::new(file_path).exists() {
            return CommandResult::error(format!("File not found: {}", file_path));
        }
        
        info!("Loading point cloud from: {}", file_path);
        
        // Parse the point cloud
        match self.point_cloud_parser.parse_ply(file_path) {
            Ok(cloud) => {
                let point_count = cloud.points.len();
                let bounds = &cloud.bounds;
                
                // Extract building name from filename
                let building_name = Path::new(file_path)
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("Scanned Building");
                
                // Convert to building plan
                let plan = self.point_cloud_parser.to_building_plan(&cloud, building_name);
                
                // Convert to ArxObjects for compression stats
                let arxobjects = self.point_cloud_parser.to_arxobjects(&cloud, 0x0001);
                
                // Calculate compression ratio
                let original_size = point_count * 12;  // 3 floats per point
                let compressed_size = arxobjects.len() * 13;  // 13 bytes per ArxObject
                let compression_ratio = original_size as f32 / compressed_size as f32;
                
                // Generate ASCII
                let ascii = self.document_parser.generate_ascii(&plan);
                
                self.current_plan = Some(plan.clone());
                self.current_floor = 0;
                
                let mut output = Vec::new();
                output.push(format!("Successfully loaded LiDAR scan: {}", building_name));
                output.push(format!("  Points: {}", point_count));
                output.push(format!("  Bounds: ({:.1}, {:.1}, {:.1}) to ({:.1}, {:.1}, {:.1})",
                    bounds.min.x, bounds.min.y, bounds.min.z,
                    bounds.max.x, bounds.max.y, bounds.max.z));
                output.push(format!("  Detected floors: {}", plan.floors.len()));
                output.push(format!("  Detected equipment: {}", 
                    plan.floors.iter().map(|f| f.equipment.len()).sum::<usize>()));
                output.push("".to_string());
                output.push(format!("Compression Statistics:"));
                output.push(format!("  Original: {} bytes", original_size));
                output.push(format!("  Compressed: {} bytes", compressed_size));
                output.push(format!("  Ratio: {:.0}:1", compression_ratio));
                output.push("".to_string());
                output.push("Building ASCII View:".to_string());
                output.push("".to_string());
                
                // Add ASCII representation
                for line in ascii.lines() {
                    output.push(line.to_string());
                }
                
                CommandResult::success_multi(output)
            }
            Err(e) => {
                error!("Failed to parse point cloud: {}", e);
                CommandResult::error(format!("Failed to load scan: {}", e))
            }
        }
    }
    
    /// Export building as ArxObjects
    fn export_arxobjects_command(&self, args: &[&str]) -> CommandResult {
        if self.current_plan.is_none() {
            return CommandResult::error("No building plan loaded. Use 'load-plan' first.".to_string());
        }
        
        let output_path = if args.is_empty() {
            "arxobjects.bin"
        } else {
            args[0]
        };
        
        let plan = self.current_plan.as_ref().unwrap();
        let arxobjects = self.document_parser.to_arxobjects(plan);
        
        // Serialize ArxObjects
        let mut data = Vec::new();
        for obj in &arxobjects {
            data.extend_from_slice(&obj.to_bytes());
        }
        
        // Write to file
        match fs::write(output_path, &data) {
            Ok(_) => {
                CommandResult::success(format!(
                    "Exported {} ArxObjects to {} ({} bytes)",
                    arxobjects.len(),
                    output_path,
                    data.len()
                ))
            }
            Err(e) => {
                CommandResult::error(format!("Failed to export: {}", e))
            }
        }
    }
}

/// Result of command execution
pub struct CommandResult {
    pub success: bool,
    pub output: Vec<String>,
}

impl CommandResult {
    /// Create empty result
    pub fn empty() -> Self {
        Self {
            success: true,
            output: Vec::new(),
        }
    }
    
    /// Create success result with single line
    pub fn success(message: String) -> Self {
        Self {
            success: true,
            output: vec![message],
        }
    }
    
    /// Create success result with multiple lines
    pub fn success_multi(output: Vec<String>) -> Self {
        Self {
            success: true,
            output,
        }
    }
    
    /// Create error result
    pub fn error(message: String) -> Self {
        Self {
            success: false,
            output: vec![message],
        }
    }
}