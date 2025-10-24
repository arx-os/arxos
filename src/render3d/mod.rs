//! 3D Building Renderer for ArxOS
//!
//! This module provides advanced 3D visualization capabilities for building data,
//! including multi-floor rendering, equipment positioning, and spatial relationships.

use crate::yaml::{BuildingData, FloorData, RoomData, EquipmentData, EquipmentStatus};
use crate::spatial::{Point3D, BoundingBox3D};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// 3D rendering configuration
#[derive(Debug, Clone)]
pub struct Render3DConfig {
    pub show_status: bool,
    pub show_rooms: bool,
    pub show_equipment: bool,
    pub show_connections: bool,
    pub projection_type: ProjectionType,
    pub view_angle: ViewAngle,
    pub scale_factor: f64,
    pub max_width: usize,
    pub max_height: usize,
}

/// 3D projection types
#[derive(Debug, Clone, PartialEq)]
pub enum ProjectionType {
    Isometric,
    Orthographic,
    Perspective,
}

/// View angles for 3D rendering
#[derive(Debug, Clone, PartialEq)]
pub enum ViewAngle {
    TopDown,
    Front,
    Side,
    Isometric,
}

/// 3D coordinate system for rendering
#[derive(Debug, Clone)]
pub struct Coordinate3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// 2D screen coordinate for terminal display
#[derive(Debug, Clone)]
pub struct ScreenCoord {
    pub x: usize,
    pub y: usize,
    pub depth: f64, // For depth sorting
}

/// 3D building renderer
pub struct Building3DRenderer {
    building_data: BuildingData,
    config: Render3DConfig,
}

/// Rendered 3D scene data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Scene3D {
    pub building_name: String,
    pub floors: Vec<Floor3D>,
    pub equipment: Vec<Equipment3D>,
    pub rooms: Vec<Room3D>,
    pub bounding_box: BoundingBox3D,
    pub metadata: SceneMetadata,
}

/// 3D floor representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Floor3D {
    pub id: String,
    pub name: String,
    pub level: i32,
    pub elevation: f64,
    pub bounding_box: BoundingBox3D,
    pub rooms: Vec<String>, // Room IDs
    pub equipment: Vec<String>, // Equipment IDs
}

/// 3D equipment representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Equipment3D {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub floor_level: i32,
    pub room_id: Option<String>,
    pub connections: Vec<String>, // Connected equipment IDs
}

/// 3D room representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Room3D {
    pub id: String,
    pub name: String,
    pub room_type: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub floor_level: i32,
    pub equipment: Vec<String>, // Equipment IDs in this room
}

/// Scene metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SceneMetadata {
    pub total_floors: usize,
    pub total_rooms: usize,
    pub total_equipment: usize,
    pub render_time_ms: u64,
    pub projection_type: String,
    pub view_angle: String,
}

impl Building3DRenderer {
    /// Create a new 3D building renderer
    pub fn new(building_data: BuildingData, config: Render3DConfig) -> Self {
        Self {
            building_data,
            config,
        }
    }

    /// Render the building in 3D
    pub fn render_3d(&self) -> Result<Scene3D, Box<dyn std::error::Error>> {
        let start_time = std::time::Instant::now();
        
        // Extract 3D data from building
        let floors = self.extract_floors_3d()?;
        let equipment = self.extract_equipment_3d()?;
        let rooms = self.extract_rooms_3d()?;
        
        // Calculate overall bounding box
        let bounding_box = self.calculate_overall_bounds(&floors, &equipment, &rooms);
        
        // Create scene
        let scene = Scene3D {
            building_name: self.building_data.building.name.clone(),
            floors,
            equipment,
            rooms,
            bounding_box,
            metadata: SceneMetadata {
                total_floors: self.building_data.floors.len(),
                total_rooms: self.building_data.floors.iter()
                    .map(|f| f.rooms.len())
                    .sum(),
                total_equipment: self.building_data.floors.iter()
                    .map(|f| f.equipment.len())
                    .sum(),
                render_time_ms: start_time.elapsed().as_millis() as u64,
                projection_type: format!("{:?}", self.config.projection_type),
                view_angle: format!("{:?}", self.config.view_angle),
            },
        };
        
        Ok(scene)
    }

    /// Render 3D scene to ASCII terminal output
    pub fn render_to_ascii(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        // Header
        output.push_str(&format!("🏢 {} - 3D Building Visualization\n", scene.building_name));
        output.push_str(&format!("📊 {} floors, {} rooms, {} equipment\n", 
            scene.metadata.total_floors,
            scene.metadata.total_rooms,
            scene.metadata.total_equipment
        ));
        output.push_str(&format!("🎯 Projection: {} | View: {}\n", 
            scene.metadata.projection_type,
            scene.metadata.view_angle
        ));
        output.push_str("═".repeat(80).as_str());
        output.push('\n');
        
        // Render each floor
        for floor in &scene.floors {
            output.push_str(&self.render_floor_3d_ascii(floor, scene)?);
            output.push('\n');
        }
        
        // Equipment status summary
        if self.config.show_status {
            output.push_str(&self.render_equipment_status_summary(scene)?);
        }
        
        return Ok(output);
    }

    /// Extract floors as 3D objects
    fn extract_floors_3d(&self) -> Result<Vec<Floor3D>, Box<dyn std::error::Error>> {
        let mut floors_3d = Vec::new();
        
        for floor in &self.building_data.floors {
            let floor_3d = Floor3D {
                id: floor.id.clone(),
                name: floor.name.clone(),
                level: floor.level,
                elevation: floor.elevation,
                bounding_box: floor.bounding_box.clone().unwrap_or_else(|| BoundingBox3D {
                    min: Point3D { x: 0.0, y: 0.0, z: floor.elevation },
                    max: Point3D { x: 100.0, y: 100.0, z: floor.elevation + 3.0 },
                }),
                rooms: floor.rooms.iter().map(|r| r.id.clone()).collect(),
                equipment: floor.equipment.iter().map(|e| e.id.clone()).collect(),
            };
            floors_3d.push(floor_3d);
        }
        
        Ok(floors_3d)
    }

    /// Extract equipment as 3D objects
    fn extract_equipment_3d(&self) -> Result<Vec<Equipment3D>, Box<dyn std::error::Error>> {
        let mut equipment_3d = Vec::new();
        
        for floor in &self.building_data.floors {
            for equipment in &floor.equipment {
                let equipment_3d_item = Equipment3D {
                    id: equipment.id.clone(),
                    name: equipment.name.clone(),
                    equipment_type: equipment.equipment_type.clone(),
                    status: format!("{:?}", equipment.status),
                    position: equipment.position.clone(),
                    bounding_box: equipment.bounding_box.clone(),
                    floor_level: floor.level,
                    room_id: None, // EquipmentData doesn't have room_id, we'll need to find it
                    connections: Vec::new(), // TODO: Implement equipment connections
                };
                equipment_3d.push(equipment_3d_item);
            }
        }
        
        Ok(equipment_3d)
    }

    /// Extract rooms as 3D objects
    fn extract_rooms_3d(&self) -> Result<Vec<Room3D>, Box<dyn std::error::Error>> {
        let mut rooms_3d = Vec::new();
        
        for floor in &self.building_data.floors {
            for room in &floor.rooms {
                let room_3d = Room3D {
                    id: room.id.clone(),
                    name: room.name.clone(),
                    room_type: room.room_type.clone(),
                    position: room.position.clone(),
                    bounding_box: room.bounding_box.clone(),
                    floor_level: floor.level,
                    equipment: Vec::new(), // TODO: Find equipment in this room
                };
                rooms_3d.push(room_3d);
            }
        }
        
        Ok(rooms_3d)
    }

    /// Calculate overall bounding box for the building
    fn calculate_overall_bounds(
        &self,
        floors: &[Floor3D],
        equipment: &[Equipment3D],
        rooms: &[Room3D],
    ) -> BoundingBox3D {
        let mut min_x = f64::INFINITY;
        let mut min_y = f64::INFINITY;
        let mut min_z = f64::INFINITY;
        let mut max_x = f64::NEG_INFINITY;
        let mut max_y = f64::NEG_INFINITY;
        let mut max_z = f64::NEG_INFINITY;
        
        // Check floors
        for floor in floors {
            min_x = min_x.min(floor.bounding_box.min.x);
            min_y = min_y.min(floor.bounding_box.min.y);
            min_z = min_z.min(floor.bounding_box.min.z);
            max_x = max_x.max(floor.bounding_box.max.x);
            max_y = max_y.max(floor.bounding_box.max.y);
            max_z = max_z.max(floor.bounding_box.max.z);
        }
        
        // Check equipment
        for equipment in equipment {
            min_x = min_x.min(equipment.position.x);
            min_y = min_y.min(equipment.position.y);
            min_z = min_z.min(equipment.position.z);
            max_x = max_x.max(equipment.position.x);
            max_y = max_y.max(equipment.position.y);
            max_z = max_z.max(equipment.position.z);
        }
        
        // Check rooms
        for room in rooms {
            min_x = min_x.min(room.position.x);
            min_y = min_y.min(room.position.y);
            min_z = min_z.min(room.position.z);
            max_x = max_x.max(room.position.x);
            max_y = max_y.max(room.position.y);
            max_z = max_z.max(room.position.z);
        }
        
        BoundingBox3D {
            min: Point3D { x: min_x, y: min_y, z: min_z },
            max: Point3D { x: max_x, y: max_y, z: max_z },
        }
    }

    /// Render a single floor in 3D ASCII
    fn render_floor_3d_ascii(&self, floor: &Floor3D, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        // Floor header
        output.push_str(&format!("┌─ Floor {}: {} (Level {}) ─┐\n", 
            floor.level, floor.name, floor.level));
        
        // Floor elevation info
        output.push_str(&format!("│ Elevation: {:.1}m │\n", floor.elevation));
        
        // Floor bounding box
        output.push_str(&format!("│ Bounds: ({:.1}, {:.1}, {:.1}) to ({:.1}, {:.1}, {:.1}) │\n",
            floor.bounding_box.min.x, floor.bounding_box.min.y, floor.bounding_box.min.z,
            floor.bounding_box.max.x, floor.bounding_box.max.y, floor.bounding_box.max.z
        ));
        
        // Equipment on this floor
        let floor_equipment: Vec<&Equipment3D> = scene.equipment.iter()
            .filter(|e| e.floor_level == floor.level)
            .collect();
        
        if !floor_equipment.is_empty() {
            output.push_str("│ Equipment: ");
            for (i, equipment) in floor_equipment.iter().enumerate() {
                if i > 0 {
                    output.push_str(", ");
                }
                let status_symbol = match equipment.status.as_str() {
                    "Healthy" => "🟢",
                    "Warning" => "🟡",
                    "Critical" => "🔴",
                    _ => "⚪",
                };
                output.push_str(&format!("{}{}", status_symbol, equipment.name));
            }
            output.push_str(" │\n");
        }
        
        // Rooms on this floor
        let floor_rooms: Vec<&Room3D> = scene.rooms.iter()
            .filter(|r| r.floor_level == floor.level)
            .collect();
        
        if !floor_rooms.is_empty() {
            output.push_str("│ Rooms: ");
            for (i, room) in floor_rooms.iter().enumerate() {
                if i > 0 {
                    output.push_str(", ");
                }
                output.push_str(&format!("{} ({})", room.name, room.room_type));
            }
            output.push_str(" │\n");
        }
        
        output.push_str("└─────────────────────────────────────────────────────────────┘");
        
        Ok(output)
    }

    /// Render equipment status summary
    fn render_equipment_status_summary(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        // Count equipment by status
        let mut status_counts: HashMap<String, usize> = HashMap::new();
        for equipment in &scene.equipment {
            *status_counts.entry(equipment.status.clone()).or_insert(0) += 1;
        }
        
        output.push_str("📊 Equipment Status Summary:\n");
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        
        for (status, count) in status_counts {
            let symbol = match status.as_str() {
                "Healthy" => "🟢",
                "Warning" => "🟡", 
                "Critical" => "🔴",
                _ => "⚪",
            };
            output.push_str(&format!("│ {} {}: {} equipment\n", symbol, status, count));
        }
        
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        
        Ok(output)
    }
}

/// Default 3D render configuration
impl Default for Render3DConfig {
    fn default() -> Self {
        Self {
            show_status: true,
            show_rooms: true,
            show_equipment: true,
            show_connections: false,
            projection_type: ProjectionType::Isometric,
            view_angle: ViewAngle::Isometric,
            scale_factor: 1.0,
            max_width: 120,
            max_height: 40,
        }
    }
}

/// Convert 3D scene to different output formats
pub fn format_scene_output(scene: &Scene3D, format: &str) -> Result<String, Box<dyn std::error::Error>> {
    match format.to_lowercase().as_str() {
        "json" => {
            Ok(serde_json::to_string_pretty(scene)?)
        }
        "yaml" => {
            Ok(serde_yaml::to_string(scene)?)
        }
        "ascii" => {
            // This would be handled by the renderer
            Ok("ASCII rendering handled by renderer".to_string())
        }
        _ => {
            Err(format!("Unsupported output format: {}", format).into())
        }
    }
}
