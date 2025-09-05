//! Terminal command processing with document parser integration
//!
//! Handles local and remote commands including document loading

use arxos_core::document_parser::{DocumentParser, BuildingPlan};
use arxos_core::point_cloud_parser::PointCloudParser;
use std::path::Path;
use std::fs;
use log::{info, error};
use arxos_core::crypto::PacketAuthenticator;
use arxos_core::invites::invite::{create_invite, verify_invite, InviteRole};
use arxos_core::arxobject::ArxObject;
use arxos_core::mobile_offline::transport::QueueTransport;
use arxos_core::mobile_offline::binder::MobileBinder;

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
    mac: PacketAuthenticator,
    invite_seed: u32,
    mobile_sender: Option<MobileBinder<QueueTransport>>,
    mobile_receiver: Option<MobileBinder<QueueTransport>>,
}

impl CommandProcessor {
    /// Create new command processor
    pub fn new() -> Self {
        Self {
            document_parser: DocumentParser::new(),
            point_cloud_parser: PointCloudParser::new(),
            current_plan: None,
            current_floor: 0,
            mac: PacketAuthenticator::new([0x11; 32]),
            invite_seed: 0xA5A5_0001,
            mobile_sender: None,
            mobile_receiver: None,
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
            "invite" => self.invite_command(&parts[1..]),
            "mobile" => self.mobile_command(&parts[1..]),
            "latency" => self.latency_command(&parts[1..]),
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

    /// Generate or accept RF invite tokens
    fn invite_command(&mut self, args: &[&str]) -> CommandResult {
        if args.is_empty() { return CommandResult::error("Usage: invite generate|accept ...".to_string()); }
        match args[0] {
            "generate" => {
                // Usage: invite generate <role:viewer|tech|admin> <hours>
                if args.len() < 3 { return CommandResult::error("Usage: invite generate <role> <hours>".to_string()); }
                let role = match args[1] { "viewer" => InviteRole::Viewer, "tech" | "technician" => InviteRole::Technician, "admin" => InviteRole::Admin, _ => return CommandResult::error("Invalid role".to_string()) };
                let hours: u8 = args[2].parse().unwrap_or(8);
                let obj = create_invite(0xFFFF, role, hours, &self.mac, self.invite_seed);
                let bytes = obj.to_bytes();
                let mut hex = String::from("0x");
                for b in &bytes { hex.push_str(&format!("{:02X}", b)); }
                CommandResult::success_multi(vec![
                    "Invite generated:".to_string(),
                    format!("  Role: {:?}", role),
                    format!("  Hours: {}", hours),
                    format!("  Object: {}", hex),
                ])
            }
            "accept" => {
                // Usage: invite accept <13B-hex>
                if args.len() < 2 { return CommandResult::error("Usage: invite accept <13B-hex>".to_string()); }
                let s = args[1].trim();
                let hex = s.strip_prefix("0x").unwrap_or(s);
                if hex.len() != 26 { return CommandResult::error("Expect 26 hex chars".to_string()); }
                let mut buf = [0u8; 13];
                for i in 0..13 {
                    let byte = u8::from_str_radix(&hex[2*i..2*i+2], 16);
                    if let Ok(v) = byte { buf[i] = v; } else { return CommandResult::error("Invalid hex".to_string()); }
                }
                let obj = ArxObject::from_bytes(&buf);
                if let Some((role, hours)) = verify_invite(&obj, &self.mac, self.invite_seed) {
                    CommandResult::success_multi(vec![
                        "Invite accepted".to_string(),
                        format!("  Role: {:?}", role),
                        format!("  Hours: {}", hours),
                    ])
                } else {
                    CommandResult::error("Invalid or tampered invite".to_string())
                }
            }
            _ => CommandResult::error("Unknown invite subcommand".to_string()),
        }
    }

    fn mobile_command(&mut self, args: &[&str]) -> CommandResult {
        if args.is_empty() { return CommandResult::error("Usage: mobile <init|send|recv> ...".to_string()); }
        match args[0] {
            "init" => {
                let sender = MobileBinder::new(QueueTransport::new(), [0x42; 32], 0x1111, 1);
                let receiver = MobileBinder::new(QueueTransport::new(), [0x42; 32], 0x2222, 1);
                self.mobile_sender = Some(sender);
                self.mobile_receiver = Some(receiver);
                CommandResult::success("Initialized mobile loopback session".to_string())
            }
            "send" => {
                if self.mobile_sender.is_none() || self.mobile_receiver.is_none() {
                    return CommandResult::error("Run 'mobile init' first".to_string());
                }
                if args.len() < 2 { return CommandResult::error("Usage: mobile send <13B-hex> [13B-hex...]".to_string()); }

                let mut objects = Vec::new();
                for s in &args[1..] {
                    let hex = s.trim().strip_prefix("0x").unwrap_or(s);
                    if hex.len() != 26 { return CommandResult::error("Expect 26 hex chars".to_string()); }
                    let mut buf = [0u8; 13];
                    for i in 0..13 {
                        match u8::from_str_radix(&hex[2*i..2*i+2], 16) {
                            Ok(v) => buf[i] = v,
                            Err(_) => return CommandResult::error("Invalid hex".to_string()),
                        }
                    }
                    objects.push(ArxObject::from_bytes(&buf));
                }

                let sender = self.mobile_sender.as_mut().unwrap();
                let receiver = self.mobile_receiver.as_mut().unwrap();
                let sent = sender.send_objects(&objects).map_err(|_| ()).unwrap();
                sender.drain_sent_into(receiver);

                CommandResult::success_multi(vec![
                    format!("Sent {} frame(s)", sent),
                    format!("Objects: {}", objects.len()),
                ])
            }
            "recv" => {
                if self.mobile_receiver.is_none() { return CommandResult::error("Run 'mobile init' first".to_string()); }
                let receiver = self.mobile_receiver.as_mut().unwrap();
                let objs = receiver.poll_objects();
                if objs.is_empty() {
                    CommandResult::success("No objects available".to_string())
                } else {
                    let mut out = vec![format!("Received {} object(s)", objs.len())];
                    for (i, o) in objs.iter().enumerate() {
                        let b = o.to_bytes();
                        let mut hex = String::from("0x");
                        for byte in &b { hex.push_str(&format!("{:02X}", byte)); }
                        out.push(format!("  {}: {}", i+1, hex));
                    }
                    CommandResult::success_multi(out)
                }
            }
            _ => CommandResult::error("Unknown mobile subcommand".to_string()),
        }
    }

    /// Estimate airtime/latency for a markup
    /// Usage:
    ///   latency <objects> [hops=1] [profile=range|speed]
    /// Example:
    ///   latency 40 hops=2 profile=speed
    fn latency_command(&self, args: &[&str]) -> CommandResult {
        if args.is_empty() {
            return CommandResult::error("Usage: latency <objects> [hops=1] [profile=range|speed]".to_string());
        }
        let objects: usize = match args[0].parse() {
            Ok(n) if n > 0 => n,
            _ => return CommandResult::error("objects must be a positive integer".to_string()),
        };
        let mut hops: usize = 1;
        let mut profile = "range"; // default conservative
        for a in &args[1..] {
            if let Some(v) = a.strip_prefix("hops=") {
                hops = v.parse().unwrap_or(1);
            } else if let Some(v) = a.strip_prefix("profile=") {
                profile = if v == "speed" { "speed" } else { "range" };
            }
        }

        // Budget and rates per docs
        let objs_per_frame = 17usize;
        let frames = (objects + objs_per_frame - 1) / objs_per_frame;
        let per_frame_s_range = (1.5f32, 6.0f32);
        let per_frame_s_speed = (0.08f32, 0.32f32);

        let (lo, hi) = if profile == "speed" { per_frame_s_speed } else { per_frame_s_range };
        let total_lo = lo * frames as f32 * hops as f32;
        let total_hi = hi * frames as f32 * hops as f32;

        CommandResult::success_multi(vec![
            format!("Objects: {}", objects),
            format!("Frames: {} ({} objs/frame)", frames, objs_per_frame),
            format!("Hops: {}", hops),
            format!("Profile: {}", profile),
            format!("Estimated latency: {:.2}–{:.2} s", total_lo, total_hi),
        ])
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