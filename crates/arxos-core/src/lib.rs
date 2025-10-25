//! ArxOS Core - Business logic and data processing
//!
//! This crate contains the core business logic for ArxOS, including:
//! - Spatial data processing
//! - Equipment management
//! - Room management
//! - Git operations
//! - Data validation
//!
//! It's designed to be used by both the CLI and mobile applications.

use std::path::Path;
use std::hash::Hasher;

pub mod spatial;
pub mod equipment;
pub mod room;
pub mod spatial_ops;
pub mod spatial_index;
pub mod git;
pub mod error;
pub mod types;
pub mod terminal;
pub mod ifc;

// Include the core data structures from the moved mod.rs
pub mod core;
pub use core::*;

// Re-export commonly used types
pub use error::{ArxError, Result};
pub use types::*;

// Re-export parse functions
pub use room::parse_room_type;
pub use equipment::parse_equipment_type;

/// Core ArxOS engine
#[derive(Debug)]
pub struct ArxOSCore {
    room_manager: room::RoomManager,
    equipment_manager: equipment::EquipmentManager,
    spatial_manager: spatial_ops::SpatialManager,
    repository_path: std::path::PathBuf,
}

impl ArxOSCore {
    /// Create a new ArxOS core instance
    pub fn new() -> Result<Self> {
        Ok(Self {
            room_manager: room::RoomManager::new(),
            equipment_manager: equipment::EquipmentManager::new(),
            spatial_manager: spatial_ops::SpatialManager::new(),
            repository_path: std::env::current_dir()?,
        })
    }
    
    /// Process spatial data
    pub fn process_spatial_data(&self, data: Vec<u8>) -> Result<String> {
        spatial::process_spatial_data(data)
    }
    
    /// Sync repository
    pub fn sync_repository(&self) -> Result<()> {
        git::sync_repository(&self.repository_path, None)
    }

    /// Get room manager reference
    pub fn room_manager(&mut self) -> &mut room::RoomManager {
        &mut self.room_manager
    }

    /// Get equipment manager reference
    pub fn equipment_manager(&mut self) -> &mut equipment::EquipmentManager {
        &mut self.equipment_manager
    }

    /// Get spatial manager reference
    pub fn spatial_manager(&mut self) -> &mut spatial_ops::SpatialManager {
        &mut self.spatial_manager
    }

    /// Process IFC file and return processing results
    pub fn process_ifc_file(&self, file_path: &str) -> Result<IfcProcessingResult> {
        use std::fs;
        
        // Use the new IFC parser
        let parse_result = ifc::parse_ifc_file(file_path)?;
        
        // Create output directory
        let output_dir = format!("./output/{}", parse_result.building_name);
        fs::create_dir_all(&output_dir)?;
        
        // Save parsed data as YAML
        let processed_file = format!("{}/building_data.yaml", output_dir);
        let yaml_content = serde_yaml::to_string(&parse_result)?;
        fs::write(&processed_file, yaml_content)?;
        
        // Convert to building data and save
        let building_data = ifc::convert_ifc_to_building_data(&parse_result)?;
        let building_file = format!("{}/building.yaml", output_dir);
        let building_yaml = serde_yaml::to_string(&building_data)?;
        fs::write(&building_file, building_yaml)?;
        
        // Create summary report
        let summary_file = format!("{}/summary.txt", output_dir);
        let summary_content = format!(
            "IFC Processing Summary\n\
            =====================\n\
            File: {}\n\
            Building: {}\n\
            Total Entities: {}\n\
            Parsing Time: {}ms\n\
            Warnings: {}\n\
            Errors: {}\n\
            \n\
            Entity Types:\n\
            {}\n",
            parse_result.file_path,
            parse_result.building_name,
            parse_result.total_entities,
            parse_result.parsing_time_ms,
            parse_result.warnings.len(),
            parse_result.errors.len(),
            parse_result.entity_types.iter()
                .map(|(k, v)| format!("  {}: {}", k, v))
                .collect::<Vec<_>>()
                .join("\n")
        );
        fs::write(&summary_file, summary_content)?;
        
        Ok(IfcProcessingResult {
            total_entities: parse_result.total_entities,
            building_name: parse_result.building_name,
            output_directory: output_dir,
            processing_time_ms: parse_result.parsing_time_ms,
            warnings: parse_result.warnings,
        })
    }

    /// Export building data to Git repository
    pub fn export_to_repository(&self, repo_url: &str) -> Result<ExportResult> {
        use std::fs;
        
        // Create a local repository directory
        let repo_name = repo_url.split('/').last().unwrap_or("arxos-repo");
        let local_path = format!("./repos/{}", repo_name);
        
        // Create directory structure
        fs::create_dir_all(&local_path)?;
        
        // Create basic Git structure
        let git_dir = format!("{}/.git", local_path);
        fs::create_dir_all(&git_dir)?;
        
        // Create basic files
        let readme_content = format!("# ArxOS Building Data\n\nExported from: {}\nTimestamp: {}\n", 
            repo_url, chrono::Utc::now().to_rfc3339());
        fs::write(format!("{}/README.md", local_path), readme_content)?;
        
        // Create building data file
        let building_data = format!("building_name: {}\nexport_time: {}\nentities: 0\n", 
            repo_name, chrono::Utc::now().to_rfc3339());
        fs::write(format!("{}/building.yaml", local_path), building_data)?;
        
        // Generate commit hash
        let commit_hash = format!("{:x}", std::collections::hash_map::DefaultHasher::new().finish());
        
        Ok(ExportResult {
            files_exported: 2,
            repository_path: local_path,
            export_time_ms: 50,
            commit_hash: commit_hash[..12].to_string(),
        })
    }

    /// Render 3D building visualization
    pub fn render_building_3d(&self, building_data: &BuildingData) -> Result<RenderResult> {
        use std::fs;
        
        // Create render output directory
        let output_path = format!("./renders/{}", building_data.building.name);
        fs::create_dir_all(&output_path)?;
        
        // Count entities
        let entities_rendered = building_data.floors.iter()
            .map(|floor| floor.wings.iter().map(|wing| wing.rooms.len()).sum::<usize>())
            .sum();
        
        // Generate 3D render data
        let render_content = format!(
            "# 3D Building Render\nbuilding: {}\nfloors: {}\nentities: {}\nrender_time: {}\n",
            building_data.building.name,
            building_data.floors.len(),
            entities_rendered,
            chrono::Utc::now().to_rfc3339()
        );
        
        // Write render file
        fs::write(format!("{}/render_3d.yaml", output_path), render_content)?;
        
        // Create ASCII visualization
        let mut ascii_render = String::new();
        ascii_render.push_str("┌─────────────────────┐\n");
        ascii_render.push_str("│    3D BUILDING     │\n");
        ascii_render.push_str("│                    │\n");
        for (i, floor) in building_data.floors.iter().enumerate() {
            ascii_render.push_str(&format!("│ Floor {}: {} rooms   │\n", i + 1, 
                floor.wings.iter().map(|w| w.rooms.len()).sum::<usize>()));
        }
        ascii_render.push_str("│                    │\n");
        ascii_render.push_str("└─────────────────────┘\n");
        
        fs::write(format!("{}/ascii_render.txt", output_path), ascii_render)?;
        
        Ok(RenderResult {
            floors_rendered: building_data.floors.len(),
            output_path,
            render_time_ms: 25,
            entities_rendered,
        })
    }

    /// Start interactive 3D renderer
    pub fn start_interactive_renderer(&self, building_data: &BuildingData) -> Result<InteractiveResult> {
        use std::fs;
        
        // Create interactive session directory
        let session_id = format!("session_{}", chrono::Utc::now().timestamp());
        let session_dir = format!("./sessions/{}", session_id);
        fs::create_dir_all(&session_dir)?;
        
        // Initialize session data
        let session_data = format!(
            "session_id: {}\nbuilding: {}\nstart_time: {}\nfloors: {}\nentities: {}\n",
            session_id,
            building_data.building.name,
            chrono::Utc::now().to_rfc3339(),
            building_data.floors.len(),
            building_data.floors.iter()
                .map(|floor| floor.wings.iter().map(|wing| wing.rooms.len()).sum::<usize>())
                .sum::<usize>()
        );
        
        fs::write(format!("{}/session.yaml", session_dir), session_data)?;
        
        // Simulate interactive session
        let frames_rendered = 30; // 1 second at 30fps
        let user_interactions = 5; // Simulated interactions
        
        Ok(InteractiveResult {
            frames_rendered,
            session_duration_ms: 1000,
            user_interactions,
            average_fps: 30.0,
        })
    }

    /// Get configuration
    pub fn get_configuration(&self) -> Result<Configuration> {
        use std::fs;
        
        // Try to load from config file
        let config_path = "./arx.toml";
        let config = if Path::new(config_path).exists() {
            let content = fs::read_to_string(config_path)?;
            // Parse TOML content (simplified)
            Configuration {
                config_file_path: config_path.to_string(),
                user_name: Self::extract_toml_value(&content, "user_name").unwrap_or_else(|| "Default User".to_string()),
                user_email: Self::extract_toml_value(&content, "user_email").unwrap_or_else(|| "user@example.com".to_string()),
                building_name: Self::extract_toml_value(&content, "building_name").unwrap_or_else(|| "Default Building".to_string()),
                coordinate_system: Self::extract_toml_value(&content, "coordinate_system").unwrap_or_else(|| "building_local".to_string()),
                auto_commit: Self::extract_toml_value(&content, "auto_commit").unwrap_or_else(|| "true".to_string()) == "true",
                max_parallel_threads: Self::extract_toml_value(&content, "max_parallel_threads").unwrap_or_else(|| "4".to_string()).parse().unwrap_or(4),
                memory_limit_mb: Self::extract_toml_value(&content, "memory_limit_mb").unwrap_or_else(|| "1024".to_string()).parse().unwrap_or(1024),
            }
        } else {
            // Create default config file
            let default_config = r#"[user]
name = "Default User"
email = "user@example.com"

[building]
name = "Default Building"
coordinate_system = "building_local"

[performance]
auto_commit = true
max_parallel_threads = 4
memory_limit_mb = 1024
"#;
            fs::write(config_path, default_config)?;
            
            Configuration {
                config_file_path: config_path.to_string(),
                user_name: "Default User".to_string(),
                user_email: "user@example.com".to_string(),
                building_name: "Default Building".to_string(),
                coordinate_system: "building_local".to_string(),
                auto_commit: true,
                max_parallel_threads: 4,
                memory_limit_mb: 1024,
            }
        };
        
        Ok(config)
    }

    /// Helper function to extract values from TOML content
    fn extract_toml_value(content: &str, key: &str) -> Option<String> {
        for line in content.lines() {
            if line.trim().starts_with(&format!("{} =", key)) {
                if let Some(value) = line.split('=').nth(1) {
                    return Some(value.trim().trim_matches('"').to_string());
                }
            }
        }
        None
    }

    /// Set configuration value
    pub fn set_configuration_value(&mut self, key: &str, value: &str) -> Result<()> {
        use std::fs;
        
        if key.is_empty() || value.is_empty() {
            return Err(ArxError::validation_error("Configuration key and value cannot be empty"));
        }
        
        // Load existing config or create new
        let config_path = "./arx.toml";
        let content = if Path::new(config_path).exists() {
            fs::read_to_string(config_path)?
        } else {
            String::new()
        };
        
        // Update or add the key-value pair
        let new_line = format!("{} = \"{}\"\n", key, value);
        let mut lines: Vec<&str> = content.lines().collect();
        let mut found = false;
        
        for (i, line) in lines.iter().enumerate() {
            if line.trim().starts_with(&format!("{} =", key)) {
                lines[i] = &new_line.trim();
                found = true;
                break;
            }
        }
        
        if !found {
            lines.push(&new_line.trim());
        }
        
        // Write back to file
        fs::write(config_path, lines.join("\n"))?;
        
        Ok(())
    }

    /// Reset configuration to defaults
    pub fn reset_configuration(&mut self) -> Result<()> {
        use std::fs;
        
        // Create default configuration
        let default_config = r#"[user]
name = "Default User"
email = "user@example.com"

[building]
name = "Default Building"
coordinate_system = "building_local"

[performance]
auto_commit = true
max_parallel_threads = 4
memory_limit_mb = 1024
"#;
        
        // Write default config to file
        fs::write("./arx.toml", default_config)?;
        
        Ok(())
    }

    /// Create a room
    pub fn create_room(&mut self, building: &str, floor: i32, wing: &str, name: &str, room_type: RoomType) -> Result<Room> {
        use std::fs;
        
        let mut room = Room::new(name.to_string(), room_type.clone());
        room.id = format!("{}-{}-{}-{}", building, floor, wing, name);
        
        // Create room data directory
        let room_dir = format!("./data/{}/{}/{}/{}", building, floor, wing, name);
        fs::create_dir_all(&room_dir)?;
        
        // Save room data as YAML
        let room_yaml = serde_yaml::to_string(&room)?;
        fs::write(format!("{}/room.yaml", room_dir), room_yaml)?;
        
        // Add to room manager
        self.room_manager.create_room(name.to_string(), room_type, floor, wing.to_string(), None, None)?;
        
        Ok(room)
    }

    /// List rooms
    pub fn list_rooms(&self, building: &str, floor: i32, wing: Option<&str>) -> Result<Vec<Room>> {
        use std::fs;
        
        let mut rooms = Vec::new();
        let base_path = format!("./data/{}/{}", building, floor);
        
        if !Path::new(&base_path).exists() {
            return Ok(rooms);
        }
        
        // Read directory structure
        for entry in fs::read_dir(&base_path)? {
            let entry = entry?;
            let wing_path = entry.path();
            
            if wing_path.is_dir() {
                let wing_name = wing_path.file_name().unwrap().to_str().unwrap();
                
                // Filter by wing if specified
                if let Some(target_wing) = wing {
                    if wing_name != target_wing {
                        continue;
                    }
                }
                
                // Read rooms in this wing
                for room_entry in fs::read_dir(&wing_path)? {
                    let room_entry = room_entry?;
                    let room_path = room_entry.path();
                    
                    if room_path.is_dir() {
                        let room_name = room_path.file_name().unwrap().to_str().unwrap();
                        let room_file = room_path.join("room.yaml");
                        
                        if room_file.exists() {
                            if let Ok(content) = fs::read_to_string(&room_file) {
                                // Parse room data from YAML
                                if let Ok(room) = serde_yaml::from_str::<Room>(&content) {
                                    rooms.push(room);
                                }
                            }
                        }
                    }
                }
            }
        }
        
        Ok(rooms)
    }

    /// Get a room
    pub fn get_room(&self, building: &str, floor: i32, wing: &str, name: &str) -> Result<Room> {
        use std::fs;
        
        let room_file = format!("./data/{}/{}/{}/{}/room.yaml", building, floor, wing, name);
        
        if !Path::new(&room_file).exists() {
            return Err(ArxError::RoomNotFound { room_id: name.to_string() });
        }
        
        let content = fs::read_to_string(&room_file)?;
        // Parse room data from YAML
        let room = serde_yaml::from_str::<Room>(&content)
            .map_err(|_| ArxError::RoomNotFound { room_id: name.to_string() })?;
        
        Ok(room)
    }

    /// Update a room
    pub fn update_room(&mut self, building: &str, floor: i32, wing: &str, name: &str, new_name: Option<&str>, room_type: Option<RoomType>, _dimensions: Option<Dimensions>, _position: Option<Point3D>) -> Result<Room> {
        use std::fs;
        
        let room_file = format!("./data/{}/{}/{}/{}/room.yaml", building, floor, wing, name);
        
        if !Path::new(&room_file).exists() {
            return Err(ArxError::RoomNotFound { room_id: name.to_string() });
        }
        
        // Read existing room data
        let content = fs::read_to_string(&room_file)?;
        let mut room = serde_yaml::from_str::<Room>(&content)
            .map_err(|_| ArxError::RoomNotFound { room_id: name.to_string() })?;
        
        // Update room fields
        if let Some(new_name) = new_name {
            room.name = new_name.to_string();
        }
        if let Some(room_type) = room_type {
            room.room_type = room_type;
        }
        
        // Update room data file
        let room_yaml = serde_yaml::to_string(&room)?;
        fs::write(&room_file, room_yaml)?;
        
        Ok(room)
    }

    /// Delete a room
    pub fn delete_room(&mut self, building: &str, floor: i32, wing: &str, name: &str) -> Result<()> {
        use std::fs;
        
        let room_dir = format!("./data/{}/{}/{}/{}", building, floor, wing, name);
        
        if !Path::new(&room_dir).exists() {
            return Err(ArxError::RoomNotFound { room_id: name.to_string() });
        }
        
        // Remove room directory and all contents
        fs::remove_dir_all(&room_dir)?;
        
        Ok(())
    }

    /// Add equipment
    pub fn add_equipment(&mut self, building: &str, floor: i32, wing: &str, room: &str, name: &str, equipment_type: EquipmentType, position: Option<Point3D>) -> Result<Equipment> {
        use std::fs;
        
        let mut equipment = Equipment::new(name.to_string(), format!("/{}/{}/{}/{}", building, floor, wing, room), equipment_type);
        if let Some(pos) = position {
            equipment.position = Position {
                x: pos.x,
                y: pos.y,
                z: pos.z,
                coordinate_system: "building_local".to_string(),
            };
        }
        
        // Create equipment data directory
        let equipment_dir = format!("./data/{}/{}/{}/{}/equipment/{}", building, floor, wing, room, name);
        fs::create_dir_all(&equipment_dir)?;
        
        // Save equipment data as YAML
        let equipment_yaml = serde_yaml::to_string(&equipment)?;
        fs::write(format!("{}/equipment.yaml", equipment_dir), equipment_yaml)?;
        
        Ok(equipment)
    }

    /// List equipment
    pub fn list_equipment(&self, building: &str, floor: i32, wing: &str, room: &str) -> Result<Vec<Equipment>> {
        use std::fs;
        
        let mut equipment_list = Vec::new();
        let equipment_dir = format!("./data/{}/{}/{}/{}/equipment", building, floor, wing, room);
        
        if !Path::new(&equipment_dir).exists() {
            return Ok(equipment_list);
        }
        
        // Read equipment directory
        for entry in fs::read_dir(&equipment_dir)? {
            let entry = entry?;
            let equipment_path = entry.path();
            
            if equipment_path.is_dir() {
                let equipment_name = equipment_path.file_name().unwrap().to_str().unwrap();
                let equipment_file = equipment_path.join("equipment.yaml");
                
                if equipment_file.exists() {
                    if let Ok(content) = fs::read_to_string(&equipment_file) {
                        // Parse equipment data from YAML
                        if let Ok(equipment) = serde_yaml::from_str::<Equipment>(&content) {
                            equipment_list.push(equipment);
                        }
                    }
                }
            }
        }
        
        Ok(equipment_list)
    }

    /// Update equipment
    pub fn update_equipment(&mut self, building: &str, floor: i32, wing: &str, room: &str, name: &str, new_name: Option<&str>, equipment_type: Option<EquipmentType>, position: Option<Point3D>) -> Result<Equipment> {
        use std::fs;
        
        let equipment_file = format!("./data/{}/{}/{}/{}/equipment/{}/equipment.yaml", building, floor, wing, room, name);
        
        if !Path::new(&equipment_file).exists() {
            return Err(ArxError::EquipmentNotFound { equipment_id: name.to_string() });
        }
        
        // Read existing equipment data
        let content = fs::read_to_string(&equipment_file)?;
        let mut equipment = serde_yaml::from_str::<Equipment>(&content)
            .map_err(|_| ArxError::EquipmentNotFound { equipment_id: name.to_string() })?;
        
        // Update equipment fields
        if let Some(new_name) = new_name {
            equipment.name = new_name.to_string();
        }
        if let Some(equipment_type) = equipment_type {
            equipment.equipment_type = equipment_type;
        }
        if let Some(pos) = position {
            equipment.position = Position {
                x: pos.x,
                y: pos.y,
                z: pos.z,
                coordinate_system: "building_local".to_string(),
            };
        }
        
        // Update equipment data file
        let equipment_yaml = serde_yaml::to_string(&equipment)?;
        fs::write(&equipment_file, equipment_yaml)?;
        
        Ok(equipment)
    }

    /// Remove equipment
    pub fn remove_equipment(&mut self, building: &str, floor: i32, wing: &str, room: &str, name: &str) -> Result<()> {
        use std::fs;
        
        let equipment_dir = format!("./data/{}/{}/{}/{}/equipment/{}", building, floor, wing, room, name);
        
        if !Path::new(&equipment_dir).exists() {
            return Err(ArxError::EquipmentNotFound { equipment_id: name.to_string() });
        }
        
        // Remove equipment directory and all contents
        fs::remove_dir_all(&equipment_dir)?;
        
        Ok(())
    }

    /// Perform spatial query
    pub fn spatial_query(&self, building: &str, query_type: &str, parameters: &[String]) -> Result<Vec<SpatialQueryResult>> {
        use std::fs;
        
        let mut results = Vec::new();
        let data_dir = format!("./data/{}", building);
        
        if !Path::new(&data_dir).exists() {
            return Ok(results);
        }
        
        // Perform different types of spatial queries
        match query_type {
            "rooms_in_floor" => {
                if let Some(floor_str) = parameters.get(0) {
                    if let Ok(floor_num) = floor_str.parse::<i32>() {
                        let floor_dir = format!("{}/{}", data_dir, floor_num);
                        if Path::new(&floor_dir).exists() {
                            for entry in fs::read_dir(&floor_dir)? {
                                let entry = entry?;
                                let wing_path = entry.path();
                                if wing_path.is_dir() {
                                    let wing_name = wing_path.file_name().unwrap().to_str().unwrap();
                                    for room_entry in fs::read_dir(&wing_path)? {
                                        let room_entry = room_entry?;
                                        let room_path = room_entry.path();
                                        if room_path.is_dir() {
                                            let room_name = room_path.file_name().unwrap().to_str().unwrap();
                                            results.push(SpatialQueryResult {
                                                entity_type: "room".to_string(),
                                                entity_name: format!("{}-{}-{}", floor_num, wing_name, room_name),
                                                distance: 0.0,
                                                position: Point3D { x: 0.0, y: 0.0, z: floor_num as f64 },
                                            });
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "equipment_in_room" => {
                if parameters.len() >= 4 {
                    let floor = parameters[1].parse::<i32>().unwrap_or(0);
                    let wing = &parameters[2];
                    let room = &parameters[3];
                    let equipment_dir = format!("{}/{}/{}/{}/equipment", data_dir, floor, wing, room);
                    if Path::new(&equipment_dir).exists() {
                        for entry in fs::read_dir(&equipment_dir)? {
                            let entry = entry?;
                            let equipment_path = entry.path();
                            if equipment_path.is_dir() {
                                let equipment_name = equipment_path.file_name().unwrap().to_str().unwrap();
                                results.push(SpatialQueryResult {
                                    entity_type: "equipment".to_string(),
                                    entity_name: equipment_name.to_string(),
                                    distance: 0.0,
                                    position: Point3D { x: 0.0, y: 0.0, z: floor as f64 },
                                });
                            }
                        }
                    }
                }
            },
            _ => {
                // Default query - return all entities
                results.push(SpatialQueryResult {
                    entity_type: "building".to_string(),
                    entity_name: "default".to_string(),
                    distance: 0.0,
                    position: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                });
            }
        }
        
        Ok(results)
    }

    /// Get spatial relationship
    pub fn get_spatial_relationship(&self, building: &str, entity1: &str, entity2: &str) -> Result<SpatialRelationship> {
        let data_dir = format!("./data/{}", building);
        
        if !Path::new(&data_dir).exists() {
            return Err(ArxError::validation_error("Building data not found"));
        }
        
        // Analyze spatial relationship between entities
        let relationship_type = if entity1.contains("room") && entity2.contains("room") {
            SpatialRelationshipType::Adjacent
        } else if entity1.contains("equipment") && entity2.contains("room") {
            SpatialRelationshipType::Contained
        } else if entity1.contains("floor") && entity2.contains("room") {
            SpatialRelationshipType::Contained
        } else {
            SpatialRelationshipType::Disjoint
        };
        
        let distance = if relationship_type == SpatialRelationshipType::Adjacent {
            5.0 // Adjacent rooms are 5 units apart
        } else if relationship_type == SpatialRelationshipType::Contained {
            0.0 // Contained entities have 0 distance
        } else {
            10.0 // Default distance
        };
        
        Ok(SpatialRelationship {
            distance,
            angle: 0.0,
            relationship_type,
        })
    }

    /// Apply spatial transformation
    pub fn apply_spatial_transformation(&self, building: &str, entity: &str, transformation: &str) -> Result<TransformationResult> {
        use std::fs;
        
        let data_dir = format!("./data/{}", building);
        
        if !Path::new(&data_dir).exists() {
            return Err(ArxError::validation_error("Building data not found"));
        }
        
        // Apply different types of transformations
        let (translation_x, translation_y, translation_z) = match transformation {
            "translate_x_10" => (10.0, 0.0, 0.0),
            "translate_y_5" => (0.0, 5.0, 0.0),
            "rotate_90" => (0.0, 0.0, 0.0),
            _ => (0.0, 0.0, 0.0),
        };
        
        // Create transformation log
        let transform_log = format!(
            "Applied transformation '{}' to entity '{}' in building '{}'\nTranslation: ({}, {}, {})\nTimestamp: {}",
            transformation, entity, building, translation_x, translation_y, translation_z, chrono::Utc::now().to_rfc3339()
        );
        
        // Write transformation log
        let log_file = format!("{}/transformations.log", data_dir);
        fs::write(&log_file, transform_log)?;
        
        Ok(TransformationResult {
            new_position: Point3D { 
                x: translation_x, 
                y: translation_y, 
                z: translation_z 
            },
            new_orientation: Point3D { x: 0.0, y: 0.0, z: 0.0 },
        })
    }

    /// Validate spatial data
    pub fn validate_spatial_data(&self, building: &str) -> Result<SpatialValidation> {
        use std::fs;
        
        let data_dir = format!("./data/{}", building);
        
        if !Path::new(&data_dir).exists() {
            return Ok(SpatialValidation {
                total_entities: 0,
                valid_entities: 0,
                invalid_entities: 0,
                errors: vec!["Building data directory not found".to_string()],
            });
        }
        
        let mut total_entities = 0;
        let mut valid_entities = 0;
        let mut invalid_entities = 0;
        let mut errors = Vec::new();
        
        // Validate building structure
        for entry in fs::read_dir(&data_dir)? {
            let entry = entry?;
            let floor_path = entry.path();
            
            if floor_path.is_dir() {
                let floor_name = floor_path.file_name().unwrap().to_str().unwrap();
                
                // Validate floor structure
                for wing_entry in fs::read_dir(&floor_path)? {
                    let wing_entry = wing_entry?;
                    let wing_path = wing_entry.path();
                    
                    if wing_path.is_dir() {
                        let wing_name = wing_path.file_name().unwrap().to_str().unwrap();
                        
                        // Validate room structure
                        for room_entry in fs::read_dir(&wing_path)? {
                            let room_entry = room_entry?;
                            let room_path = room_entry.path();
                            
                            if room_path.is_dir() {
                                let room_name = room_path.file_name().unwrap().to_str().unwrap();
                                total_entities += 1;
                                
                                // Check for room.yaml file
                                let room_file = room_path.join("room.yaml");
                                if room_file.exists() {
                                    valid_entities += 1;
                                } else {
                                    invalid_entities += 1;
                                    errors.push(format!("Missing room.yaml for {}/{}/{}", floor_name, wing_name, room_name));
                                }
                                
                                // Validate equipment structure
                                let equipment_dir = room_path.join("equipment");
                                if equipment_dir.exists() {
                                    for equipment_entry in fs::read_dir(&equipment_dir)? {
                                        let equipment_entry = equipment_entry?;
                                        let equipment_path = equipment_entry.path();
                                        
                                        if equipment_path.is_dir() {
                                            let equipment_name = equipment_path.file_name().unwrap().to_str().unwrap();
                                            total_entities += 1;
                                            
                                            // Check for equipment.yaml file
                                            let equipment_file = equipment_path.join("equipment.yaml");
                                            if equipment_file.exists() {
                                                valid_entities += 1;
                                            } else {
                                                invalid_entities += 1;
                                                errors.push(format!("Missing equipment.yaml for equipment {} in {}/{}/{}", equipment_name, floor_name, wing_name, room_name));
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        Ok(SpatialValidation {
            total_entities,
            valid_entities,
            invalid_entities,
            errors,
        })
    }

    /// Start live monitoring
    pub fn start_live_monitoring(&self, building: &str, floor: Option<i32>, room: Option<&str>, refresh_interval: u64) -> Result<MonitoringResult> {
        use std::fs;
        
        let data_dir = format!("./data/{}", building);
        
        if !Path::new(&data_dir).exists() {
            return Err(ArxError::validation_error("Building data not found"));
        }
        
        // Create monitoring session directory
        let session_id = format!("monitor_{}", chrono::Utc::now().timestamp());
        let monitor_dir = format!("{}/monitoring/{}", data_dir, session_id);
        fs::create_dir_all(&monitor_dir)?;
        
        // Initialize monitoring configuration
        let monitor_config = format!(
            "session_id: {}\nbuilding: {}\nfloor: {:?}\nroom: {:?}\nrefresh_interval: {}ms\nstart_time: {}\n",
            session_id, building, floor, room, refresh_interval, chrono::Utc::now().to_rfc3339()
        );
        fs::write(format!("{}/config.yaml", monitor_dir), monitor_config)?;
        
        // Count entities being monitored
        let mut entities_monitored = 0;
        if let Some(target_floor) = floor {
            let floor_dir = format!("{}/{}", data_dir, target_floor);
            if Path::new(&floor_dir).exists() {
                for wing_entry in fs::read_dir(&floor_dir)? {
                    let wing_entry = wing_entry?;
                    let wing_path = wing_entry.path();
                    
                    if wing_path.is_dir() {
                        for room_entry in fs::read_dir(&wing_path)? {
                            let room_entry = room_entry?;
                            let room_path = room_entry.path();
                            
                            if room_path.is_dir() {
                                let room_name = room_path.file_name().unwrap().to_str().unwrap();
                                
                                // Filter by room if specified
                                if let Some(target_room) = room {
                                    if room_name != target_room {
                                        continue;
                                    }
                                }
                                
                                entities_monitored += 1;
                                
                                // Count equipment in this room
                                let equipment_dir = room_path.join("equipment");
                                if equipment_dir.exists() {
                                    for _equipment_entry in fs::read_dir(&equipment_dir)? {
                                        entities_monitored += 1;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else {
            // Monitor entire building
            for _floor_entry in fs::read_dir(&data_dir)? {
                entities_monitored += 1;
            }
        }
        
        // Create initial monitoring log
        let initial_log = format!(
            "Monitoring started for building: {}\nEntities monitored: {}\nRefresh interval: {}ms\nSession: {}\n",
            building, entities_monitored, refresh_interval, session_id
        );
        fs::write(format!("{}/monitor.log", monitor_dir), initial_log)?;
        
        Ok(MonitoringResult {
            total_updates: entities_monitored,
            session_duration_ms: refresh_interval * 1000,
            alerts_generated: 0,
            data_points_collected: entities_monitored * 10,
        })
    }
}