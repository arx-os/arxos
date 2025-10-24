//! 3D Building Renderer for ArxOS
//!
//! This module provides advanced 3D visualization capabilities for building data,
//! including multi-floor rendering, equipment positioning, and spatial relationships.
//! It also includes interactive 3D rendering with real-time controls.

use crate::yaml::BuildingData;
use crate::spatial::{Point3D, BoundingBox3D};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// Re-export interactive components
pub mod interactive;
pub mod events;
pub mod state;

pub use interactive::{InteractiveRenderer, InteractiveConfig};
pub use events::{EventHandler, InteractiveEvent, Action, CameraAction, ZoomAction, ViewModeAction};
pub use state::{InteractiveState, CameraState, ViewMode, Rotation3D, SessionData, RenderPreferences, QualityLevel};

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

/// 3D camera for rendering
#[derive(Debug, Clone)]
pub struct Camera3D {
    pub position: Point3D,
    pub target: Point3D,
    pub up: Vector3D,
    pub fov: f64,
    pub near_clip: f64,
    pub far_clip: f64,
}

/// 3D vector for camera and transformations
#[derive(Debug, Clone)]
pub struct Vector3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// 3D projection system
#[derive(Debug, Clone)]
pub struct Projection3D {
    pub projection_type: ProjectionType,
    pub view_angle: ViewAngle,
    pub scale: f64,
    pub aspect_ratio: f64,
}

/// Viewport for terminal display
#[derive(Debug, Clone)]
pub struct Viewport3D {
    pub width: usize,
    pub height: usize,
    pub offset_x: usize,
    pub offset_y: usize,
    pub depth_buffer: Vec<Vec<f64>>,
}

/// 3D transformation matrix
#[derive(Debug, Clone)]
pub struct Matrix3D {
    pub m: [[f64; 4]; 4],
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
    pub char: char, // Character to display
}

/// Advanced 3D building renderer with camera and projection systems
pub struct Building3DRenderer {
    building_data: BuildingData,
    config: Render3DConfig,
    camera: Camera3D,
    projection: Projection3D,
    #[allow(dead_code)]
    viewport: Viewport3D,
    spatial_index: Option<crate::ifc::SpatialIndex>,
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
    pub spatial_relationships: Option<usize>, // Number of spatial relationships
    pub nearest_entity_distance: Option<f64>, // Distance to nearest entity
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
    /// Create a new advanced 3D building renderer
    pub fn new(building_data: BuildingData, config: Render3DConfig) -> Self {
        let camera = Camera3D::default();
        let projection = Projection3D::new(config.projection_type.clone(), config.view_angle.clone(), config.scale_factor);
        let viewport = Viewport3D::new(config.max_width, config.max_height);
        
        Self {
            building_data,
            config,
            camera,
            projection,
            viewport,
            spatial_index: None,
        }
    }
    
 pub fn new_with_spatial_index(
        building_data: BuildingData, 
        config: Render3DConfig,
        spatial_index: crate::ifc::SpatialIndex) -> Self {
        let camera = Camera3D::default();
        let projection = Projection3D::new(config.projection_type.clone(), config.view_angle.clone(), config.scale_factor);
        let viewport = Viewport3D::new(config.max_width, config.max_height);
        
        Self {
            building_data,
            config,
            camera,
            projection,
            viewport,
            spatial_index: Some(spatial_index),
        }
    }
    
    /// Set camera position and target
    pub fn set_camera(&mut self, position: Point3D, target: Point3D) {
        self.camera.position = position;
        self.camera.target = target;
    }
    
    /// Set projection type and view angle
    pub fn set_projection(&mut self, projection_type: ProjectionType, view_angle: ViewAngle) {
        self.projection.projection_type = projection_type;
        self.projection.view_angle = view_angle;
    }
    
    /// Set spatial index for advanced spatial queries
    pub fn set_spatial_index(&mut self, spatial_index: crate::ifc::SpatialIndex) {
        self.spatial_index = Some(spatial_index);
    }
    
    /// Get entities within a 3D bounding box using spatial index
    pub fn query_spatial_entities(&self, bbox: &BoundingBox3D) -> Vec<crate::ifc::SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_within_bounding_box(bbox.clone())
        } else {
            vec![]
        }
    }
    
    /// Get entities within a radius of a point using spatial index
    pub fn query_entities_within_radius(&self, center: &Point3D, radius: f64) -> Vec<crate::ifc::SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_within_radius(center.clone(), radius)
        } else {
            vec![]
        }
    }
    
    /// Get entities in a specific room using spatial index
    pub fn query_entities_in_room(&self, room_id: &str) -> Vec<crate::ifc::SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_in_room(room_id)
                .into_iter()
                .map(|entity| crate::ifc::SpatialQueryResult {
                    entity,
                    distance: 0.0,
                    relationship_type: crate::ifc::SpatialRelationship::Within,
                    intersection_points: vec![],
                })
                .collect()
        } else {
            vec![]
        }
    }
    
    /// Get entities on a specific floor using spatial index
    pub fn query_entities_on_floor(&self, floor: i32) -> Vec<crate::ifc::SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_in_floor(floor)
                .into_iter()
                .map(|entity| crate::ifc::SpatialQueryResult {
                    entity,
                    distance: 0.0,
                    relationship_type: crate::ifc::SpatialRelationship::Within,
                    intersection_points: vec![],
                })
                .collect()
        } else {
            vec![]
        }
    }
    
    /// Find the nearest entity to a point using spatial index
    pub fn find_nearest_entity(&self, point: &Point3D) -> Option<crate::ifc::SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_nearest(point.clone())
        } else {
            None
        }
    }
    
    /// Get equipment clusters for visualization
    pub fn get_equipment_clusters(&self, min_cluster_size: usize) -> Vec<Vec<crate::ifc::SpatialQueryResult>> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_equipment_clusters(10.0, min_cluster_size)
                .into_iter()
                .map(|cluster| {
                    cluster.into_iter()
                        .map(|entity| crate::ifc::SpatialQueryResult {
                            entity,
                            distance: 0.0,
                            relationship_type: crate::ifc::SpatialRelationship::Adjacent,
                            intersection_points: vec![],
                        })
                        .collect()
                })
                .collect()
        } else {
            vec![]
        }
    }
    
    /// Enhance equipment data with spatial index information
    fn enhance_equipment_with_spatial_data(&self, equipment: &[Equipment3D]) -> Result<Vec<Equipment3D>, Box<dyn std::error::Error>> {
        if self.spatial_index.is_none() {
            return Ok(equipment.to_vec());
        }
        
        let mut enhanced_equipment = Vec::new();
        
        for eq in equipment {
            let mut enhanced_eq = eq.clone();
            
            // Query spatial relationships for this equipment
            let spatial_results = self.query_spatial_entities(&eq.bounding_box);
            
            // Add spatial relationship information to equipment metadata
            if !spatial_results.is_empty() {
                enhanced_eq.spatial_relationships = Some(spatial_results.len());
                
                // Find the nearest equipment for connection visualization
                if let Some(nearest) = self.find_nearest_entity(&eq.position) {
                    enhanced_eq.nearest_entity_distance = Some(nearest.distance);
                }
            }
            
            enhanced_equipment.push(enhanced_eq);
        }
        
        Ok(enhanced_equipment)
    }
    
    /// Render 3D scene with advanced projection
    pub fn render_3d_advanced(&self) -> Result<Scene3D, Box<dyn std::error::Error>> {
        let start_time = std::time::Instant::now();
        
        // Extract 3D data from building
        let floors = self.extract_floors_3d()?;
        let equipment = self.extract_equipment_3d()?;
        let rooms = self.extract_rooms_3d()?;
        
        // Calculate overall bounding box
        let bounding_box = self.calculate_overall_bounds(&floors, &equipment, &rooms);
        
        // Apply 3D transformations
        let transformed_floors = self.transform_floors_3d(&floors);
        let transformed_equipment = self.transform_equipment_3d(&equipment);
        let transformed_rooms = self.transform_rooms_3d(&rooms);
        
        // Create scene
        let scene = Scene3D {
            building_name: self.building_data.building.name.clone(),
            floors: transformed_floors,
            equipment: transformed_equipment,
            rooms: transformed_rooms,
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
                projection_type: format!("{:?}", self.projection.projection_type),
                view_angle: format!("{:?}", self.projection.view_angle),
            },
        };
        
        Ok(scene)
    }
    
    /// Render 3D scene with spatial index integration for enhanced queries
    pub fn render_3d_with_spatial_queries(&self) -> Result<Scene3D, Box<dyn std::error::Error>> {
        let start_time = std::time::Instant::now();
        
        // Extract 3D data from building
        let floors = self.extract_floors_3d()?;
        let equipment = self.extract_equipment_3d()?;
        let rooms = self.extract_rooms_3d()?;
        
        // Calculate overall bounding box
        let bounding_box = self.calculate_overall_bounds(&floors, &equipment, &rooms);
        
        // Use spatial index to enhance equipment data if available
        let enhanced_equipment = if self.spatial_index.is_some() {
            self.enhance_equipment_with_spatial_data(&equipment)?
        } else {
            equipment
        };
        
        // Apply 3D transformations
        let transformed_floors = self.transform_floors_3d(&floors);
        let transformed_equipment = self.transform_equipment_3d(&enhanced_equipment);
        let transformed_rooms = self.transform_rooms_3d(&rooms);
        
        // Create scene with enhanced metadata
        let scene = Scene3D {
            building_name: self.building_data.building.name.clone(),
            floors: transformed_floors,
            equipment: transformed_equipment,
            rooms: transformed_rooms,
            bounding_box,
            metadata: SceneMetadata {
                total_floors: self.building_data.floors.len(),
                total_rooms: self.building_data.floors.iter()
                    .map(|f| f.rooms.len())
                    .sum(),
                total_equipment: enhanced_equipment.len(),
                render_time_ms: start_time.elapsed().as_millis() as u64,
                projection_type: format!("{:?}", self.projection.projection_type),
                view_angle: format!("{:?}", self.projection.view_angle),
            },
        };
        
        Ok(scene)
    }
    
    /// Render 3D scene to advanced ASCII with projection
    pub fn render_to_ascii_advanced(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        // Header with camera info
        output.push_str(&format!("🏢 {} - Advanced 3D Building Visualization\n", scene.building_name));
        output.push_str(&format!("📊 {} floors, {} rooms, {} equipment\n", 
            scene.metadata.total_floors,
            scene.metadata.total_rooms,
            scene.metadata.total_equipment
        ));
        output.push_str(&format!("🎯 Projection: {} | View: {} | Scale: {:.2}\n", 
            scene.metadata.projection_type,
            scene.metadata.view_angle,
            self.projection.scale
        ));
        output.push_str(&format!("📷 Camera: ({:.1}, {:.1}, {:.1}) → ({:.1}, {:.1}, {:.1})\n",
            self.camera.position.x, self.camera.position.y, self.camera.position.z,
            self.camera.target.x, self.camera.target.y, self.camera.target.z
        ));
        output.push_str("═".repeat(80).as_str());
        output.push('\n');
        
        // Render with 3D projection
        match self.projection.projection_type {
            ProjectionType::Isometric => {
                output.push_str(&self.render_isometric_view(scene)?);
            }
            ProjectionType::Orthographic => {
                output.push_str(&self.render_orthographic_view(scene)?);
            }
            ProjectionType::Perspective => {
                output.push_str(&self.render_perspective_view(scene)?);
            }
        }
        
        // Equipment status summary
        if self.config.show_status {
            output.push_str(&self.render_equipment_status_summary(scene)?);
        }
        
        return Ok(output);
    }
    
    /// Render 3D building as ASCII art with depth and perspective
    pub fn render_3d_ascii_art(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        // Create a 2D canvas for ASCII rendering
        let canvas_width = self.viewport.width.min(120);
        let canvas_height = self.viewport.height.min(40);
        let mut canvas = vec![vec![' '; canvas_width]; canvas_height];
        let mut depth_buffer = vec![vec![f64::NEG_INFINITY; canvas_width]; canvas_height];
        
        // Render floors as horizontal planes
        self.render_floors_to_canvas(&scene.floors, &mut canvas, &mut depth_buffer, canvas_width, canvas_height);
        
        // Render equipment as 3D symbols
        self.render_equipment_to_canvas(&scene.equipment, &mut canvas, &mut depth_buffer, canvas_width, canvas_height);
        
        // Render rooms as bounded areas
        self.render_rooms_to_canvas(&scene.rooms, &mut canvas, &mut depth_buffer, canvas_width, canvas_height);
        
        // Convert canvas to string
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        output.push_str(&format!("│ 🏢 {} - 3D ASCII Building Visualization │\n", scene.building_name));
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        
        for row in canvas {
            let line: String = row.into_iter().collect();
            output.push_str(&format!("│{}│\n", line));
        }
        
        // Add legend
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        output.push_str("Legend: █=Wall │ ╬=Equipment │ ○=Room │ ─=Floor │ ▲=HVAC │ ●=Electrical\n");
        
        Ok(output)
    }
    
    /// Render floors to ASCII canvas
    fn render_floors_to_canvas(&self, floors: &[Floor3D], canvas: &mut Vec<Vec<char>>, depth_buffer: &mut Vec<Vec<f64>>, width: usize, height: usize) {
        for floor in floors {
            // Project floor bounding box to screen coordinates
            let min_screen = self.project_to_screen(&floor.bounding_box.min, width, height);
            let max_screen = self.project_to_screen(&floor.bounding_box.max, width, height);
            
            // Draw floor outline
            let start_x = min_screen.x.max(0.0) as usize;
            let end_x = max_screen.x.min(width as f64) as usize;
            let start_y = min_screen.y.max(0.0) as usize;
            let end_y = max_screen.y.min(height as f64) as usize;
            
            // Draw horizontal lines for floor
            for y in start_y..end_y {
                for x in start_x..end_x {
                    if x < width && y < height {
                        let depth = floor.bounding_box.min.z;
                        if depth > depth_buffer[y][x] {
                            depth_buffer[y][x] = depth;
                            canvas[y][x] = '─';
                        }
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
                        canvas[label_y][label_x + i] = ch;
                    }
                }
            }
        }
    }
    
    /// Render equipment to ASCII canvas
    fn render_equipment_to_canvas(&self, equipment: &[Equipment3D], canvas: &mut Vec<Vec<char>>, depth_buffer: &mut Vec<Vec<f64>>, width: usize, height: usize) {
        for eq in equipment {
            let screen_pos = self.project_to_screen(&eq.position, width, height);
            let x = screen_pos.x as usize;
            let y = screen_pos.y as usize;
            
            if x < width && y < height {
                let depth = eq.position.z;
                if depth > depth_buffer[y][x] {
                    depth_buffer[y][x] = depth;
                    
                    // Choose symbol based on equipment type
                    let symbol = match eq.equipment_type.as_str() {
                        s if s.contains("AIR") => '▲',  // HVAC
                        s if s.contains("LIGHT") => '●', // Electrical
                        s if s.contains("PUMP") => '◊',  // Plumbing
                        s if s.contains("FAN") => '◈',   // Mechanical
                        _ => '╬', // Generic equipment
                    };
                    
                    canvas[y][x] = symbol;
                }
            }
        }
    }
    
    /// Render rooms to ASCII canvas
    fn render_rooms_to_canvas(&self, rooms: &[Room3D], canvas: &mut Vec<Vec<char>>, depth_buffer: &mut Vec<Vec<f64>>, width: usize, height: usize) {
        for room in rooms {
            let min_screen = self.project_to_screen(&room.bounding_box.min, width, height);
            let max_screen = self.project_to_screen(&room.bounding_box.max, width, height);
            
            let start_x = min_screen.x.max(0.0) as usize;
            let end_x = max_screen.x.min(width as f64) as usize;
            let start_y = min_screen.y.max(0.0) as usize;
            let end_y = max_screen.y.min(height as f64) as usize;
            
            // Draw room outline
            for y in start_y..end_y {
                for x in start_x..end_x {
                    if x < width && y < height {
                        let depth = room.bounding_box.min.z;
                        if depth > depth_buffer[y][x] {
                            depth_buffer[y][x] = depth;
                            
                            // Draw room boundary
                            if x == start_x || x == end_x - 1 || y == start_y || y == end_y - 1 {
                                canvas[y][x] = '█';
                            } else {
                                canvas[y][x] = '○';
                            }
                        }
                    }
                }
            }
        }
    }
    
    /// Project 3D point to 2D screen coordinates
    fn project_to_screen(&self, point: &Point3D, width: usize, height: usize) -> Point3D {
        // Apply camera transformation
        let transformed = self.transform_point(point);
        
        // Apply projection
        let projected = match self.projection.projection_type {
            ProjectionType::Isometric => self.isometric_projection(&transformed),
            ProjectionType::Orthographic => self.orthographic_projection(&transformed),
            ProjectionType::Perspective => self.perspective_projection(&transformed),
        };
        
        // Scale to screen coordinates
        let scale_x = width as f64 / 100.0; // Assuming building fits in 100x100 units
        let scale_y = height as f64 / 100.0;
        
        Point3D {
            x: (projected.x * scale_x + width as f64 / 2.0).clamp(0.0, width as f64 - 1.0),
            y: (projected.y * scale_y + height as f64 / 2.0).clamp(0.0, height as f64 - 1.0),
            z: projected.z,
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
                    spatial_relationships: None, // Will be set by enhance_equipment_with_spatial_data
                    nearest_entity_distance: None, // Will be set by enhance_equipment_with_spatial_data
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
    
    /// Transform 3D floors with camera and projection
    fn transform_floors_3d(&self, floors: &[Floor3D]) -> Vec<Floor3D> {
        floors.iter().map(|floor| {
            let transformed_bbox = self.transform_bounding_box(&floor.bounding_box);
            Floor3D {
                id: floor.id.clone(),
                name: floor.name.clone(),
                level: floor.level,
                elevation: floor.elevation,
                bounding_box: transformed_bbox,
                rooms: floor.rooms.clone(),
                equipment: floor.equipment.clone(),
            }
        }).collect()
    }
    
    /// Transform 3D equipment with camera and projection
    fn transform_equipment_3d(&self, equipment: &[Equipment3D]) -> Vec<Equipment3D> {
        equipment.iter().map(|eq| {
            let transformed_position = self.transform_point(&eq.position);
            let transformed_bbox = self.transform_bounding_box(&eq.bounding_box);
            Equipment3D {
                id: eq.id.clone(),
                name: eq.name.clone(),
                equipment_type: eq.equipment_type.clone(),
                status: eq.status.clone(),
                position: transformed_position,
                bounding_box: transformed_bbox,
                floor_level: eq.floor_level,
                room_id: eq.room_id.clone(),
                connections: eq.connections.clone(),
                spatial_relationships: eq.spatial_relationships,
                nearest_entity_distance: eq.nearest_entity_distance,
            }
        }).collect()
    }
    
    /// Transform 3D rooms with camera and projection
    fn transform_rooms_3d(&self, rooms: &[Room3D]) -> Vec<Room3D> {
        rooms.iter().map(|room| {
            let transformed_position = self.transform_point(&room.position);
            let transformed_bbox = self.transform_bounding_box(&room.bounding_box);
            Room3D {
                id: room.id.clone(),
                name: room.name.clone(),
                room_type: room.room_type.clone(),
                position: transformed_position,
                bounding_box: transformed_bbox,
                floor_level: room.floor_level,
                equipment: room.equipment.clone(),
            }
        }).collect()
    }
    
    /// Transform a 3D point using camera and projection
    fn transform_point(&self, point: &Point3D) -> Point3D {
        match self.projection.projection_type {
            ProjectionType::Isometric => self.isometric_projection(point),
            ProjectionType::Orthographic => self.orthographic_projection(point),
            ProjectionType::Perspective => self.perspective_projection(point),
        }
    }
    
    /// Transform a 3D bounding box using camera and projection
    fn transform_bounding_box(&self, bbox: &BoundingBox3D) -> BoundingBox3D {
        let transformed_min = self.transform_point(&bbox.min);
        let transformed_max = self.transform_point(&bbox.max);
        
        BoundingBox3D {
            min: transformed_min,
            max: transformed_max,
        }
    }
    
    /// Isometric projection
    fn isometric_projection(&self, point: &Point3D) -> Point3D {
        // Isometric projection matrix
        let x = (point.x - point.z) * self.projection.scale;
        let y = (point.x + point.z) * 0.5 * self.projection.scale + point.y * self.projection.scale;
        let z = point.z; // Keep original Z for depth sorting
        
        Point3D { x, y, z }
    }
    
    /// Orthographic projection
    fn orthographic_projection(&self, point: &Point3D) -> Point3D {
        match self.projection.view_angle {
            ViewAngle::TopDown => Point3D { x: point.x * self.projection.scale, y: point.y * self.projection.scale, z: point.z },
            ViewAngle::Front => Point3D { x: point.x * self.projection.scale, y: point.z * self.projection.scale, z: point.y },
            ViewAngle::Side => Point3D { x: point.y * self.projection.scale, y: point.z * self.projection.scale, z: point.x },
            ViewAngle::Isometric => self.isometric_projection(point),
        }
    }
    
    /// Perspective projection
    fn perspective_projection(&self, point: &Point3D) -> Point3D {
        // Simple perspective projection
        let distance = self.camera.position.z - point.z;
        if distance <= 0.0 {
            return point.clone(); // Behind camera
        }
        
        let x = (point.x - self.camera.position.x) * self.camera.fov / distance;
        let y = (point.y - self.camera.position.y) * self.camera.fov / distance;
        let z = distance; // Use distance for depth sorting
        
        Point3D { x, y, z }
    }
    
    /// Render isometric view
    fn render_isometric_view(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        output.push_str("📐 Isometric 3D View:\n");
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        
        // Sort floors by level for proper rendering order
        let mut floors = scene.floors.clone();
        floors.sort_by_key(|f| f.level);
        
        for floor in &floors {
            output.push_str(&format!("│ Floor {}: {} (Z: {:.1}m) │\n", 
                floor.level, floor.name, floor.elevation));
            
            // Show equipment on this floor
            let floor_equipment: Vec<&Equipment3D> = scene.equipment.iter()
                .filter(|e| e.floor_level == floor.level)
                .collect();
            
            for equipment in &floor_equipment {
                let status_symbol = match equipment.status.as_str() {
                    "Healthy" => "🟢",
                    "Warning" => "🟡",
                    "Critical" => "🔴",
                    _ => "⚪",
                };
                output.push_str(&format!("│   {} {} at ({:.1}, {:.1}, {:.1}) │\n",
                    status_symbol, equipment.name, 
                    equipment.position.x, equipment.position.y, equipment.position.z));
            }
        }
        
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        
        Ok(output)
    }
    
    /// Render orthographic view
    fn render_orthographic_view(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        output.push_str(&format!("📐 Orthographic View ({:?}):\n", self.projection.view_angle));
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        
        // Render based on view angle
        match self.projection.view_angle {
            ViewAngle::TopDown => {
                output.push_str("│ Top-Down View (X-Y Plane) │\n");
                output.push_str(&self.render_top_down_view(scene));
            }
            ViewAngle::Front => {
                output.push_str("│ Front View (X-Z Plane) │\n");
                output.push_str(&self.render_front_view(scene));
            }
            ViewAngle::Side => {
                output.push_str("│ Side View (Y-Z Plane) │\n");
                output.push_str(&self.render_side_view(scene));
            }
            _ => {
                output.push_str("│ Orthographic View │\n");
            }
        }
        
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        
        Ok(output)
    }
    
    /// Render perspective view
    fn render_perspective_view(&self, scene: &Scene3D) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();
        
        output.push_str("📐 Perspective View:\n");
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        output.push_str(&format!("│ Camera Position: ({:.1}, {:.1}, {:.1}) │\n",
            self.camera.position.x, self.camera.position.y, self.camera.position.z));
        output.push_str(&format!("│ Camera Target: ({:.1}, {:.1}, {:.1}) │\n",
            self.camera.target.x, self.camera.target.y, self.camera.target.z));
        output.push_str(&format!("│ FOV: {:.1}° │\n", self.camera.fov));
        
        // Show equipment with perspective depth
        let mut equipment_with_depth: Vec<(&Equipment3D, f64)> = scene.equipment.iter()
            .map(|e| {
                let depth = (e.position.x - self.camera.position.x).powi(2) + 
                           (e.position.y - self.camera.position.y).powi(2) + 
                           (e.position.z - self.camera.position.z).powi(2);
                (e, depth.sqrt())
            })
            .collect();
        
        equipment_with_depth.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());
        
        for (equipment, depth) in &equipment_with_depth {
            let status_symbol = match equipment.status.as_str() {
                "Healthy" => "🟢",
                "Warning" => "🟡",
                "Critical" => "🔴",
                _ => "⚪",
            };
            output.push_str(&format!("│   {} {} (depth: {:.1}m) │\n",
                status_symbol, equipment.name, depth));
        }
        
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        
        Ok(output)
    }
    
    /// Render top-down view
    fn render_top_down_view(&self, scene: &Scene3D) -> String {
        let mut output = String::new();
        
        // Create a simple ASCII grid representation
        let grid_size = 20;
        let mut grid = vec![vec![' '; grid_size]; grid_size];
        
        // Place equipment on the grid
        for equipment in &scene.equipment {
            let x = ((equipment.position.x / 10.0) as usize).min(grid_size - 1);
            let y = ((equipment.position.y / 10.0) as usize).min(grid_size - 1);
            
            let char = match equipment.equipment_type.as_str() {
                s if s.contains("HVAC") => 'H',
                s if s.contains("ELECTRIC") => 'E',
                s if s.contains("FIRE") => 'F',
                _ => 'O',
            };
            
            grid[y][x] = char;
        }
        
        output.push_str("│ Equipment Grid (Top-Down):\n");
        for row in &grid {
            output.push_str("│ ");
            for &cell in row {
                output.push(cell);
            }
            output.push_str(" │\n");
        }
        
        output
    }
    
    /// Render front view
    fn render_front_view(&self, scene: &Scene3D) -> String {
        let mut output = String::new();
        
        output.push_str("│ Front View (X-Z Plane):\n");
        
        // Group equipment by floor level
        let mut floor_equipment: std::collections::HashMap<i32, Vec<&Equipment3D>> = std::collections::HashMap::new();
        for equipment in &scene.equipment {
            floor_equipment.entry(equipment.floor_level).or_insert_with(Vec::new).push(equipment);
        }
        
        let mut floors: Vec<_> = floor_equipment.keys().collect();
        floors.sort();
        
        for &floor_level in &floors {
            output.push_str(&format!("│   Floor {}: ", floor_level));
            if let Some(equipment) = floor_equipment.get(&floor_level) {
                for (i, eq) in equipment.iter().enumerate() {
                    if i > 0 { output.push_str(", "); }
                    output.push_str(&eq.name);
                }
            }
            output.push_str(" │\n");
        }
        
        output
    }
    
    /// Render side view
    fn render_side_view(&self, scene: &Scene3D) -> String {
        let mut output = String::new();
        
        output.push_str("│ Side View (Y-Z Plane):\n");
        
        // Show equipment by Y position (depth)
        let mut equipment_by_y: Vec<_> = scene.equipment.iter().collect();
        equipment_by_y.sort_by(|a, b| a.position.y.partial_cmp(&b.position.y).unwrap());
        
        for equipment in &equipment_by_y {
            output.push_str(&format!("│   {} at Y: {:.1}m, Z: {:.1}m │\n",
                equipment.name, equipment.position.y, equipment.position.z));
        }
        
        output
    }
}

/// Default implementations for 3D structures
impl Default for Camera3D {
    fn default() -> Self {
        Self {
            position: Point3D { x: 50.0, y: 50.0, z: 100.0 },
            target: Point3D { x: 50.0, y: 50.0, z: 0.0 },
            up: Vector3D { x: 0.0, y: 1.0, z: 0.0 },
            fov: 45.0,
            near_clip: 0.1,
            far_clip: 1000.0,
        }
    }
}

impl Projection3D {
    pub fn new(projection_type: ProjectionType, view_angle: ViewAngle, scale: f64) -> Self {
        Self {
            projection_type,
            view_angle,
            scale,
            aspect_ratio: 1.0,
        }
    }
}

impl Viewport3D {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            offset_x: 0,
            offset_y: 0,
            depth_buffer: vec![vec![f64::INFINITY; width]; height],
        }
    }
}

impl Matrix3D {
    pub fn identity() -> Self {
        Self {
            m: [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        }
    }
}

impl Vector3D {
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }
    
    pub fn length(&self) -> f64 {
        (self.x.powi(2) + self.y.powi(2) + self.z.powi(2)).sqrt()
    }
    
    pub fn normalize(&self) -> Self {
        let len = self.length();
        if len > 0.0 {
            Self {
                x: self.x / len,
                y: self.y / len,
                z: self.z / len,
            }
        } else {
            Self { x: 0.0, y: 0.0, z: 0.0 }
        }
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

#[cfg(test)]
mod tests {
    use super::*;
    // use crate::core::Building; // Unused import removed
    
    /// Create test building data for 3D rendering tests
    fn create_test_building_data() -> BuildingData {
        use chrono::Utc;
        use std::collections::HashMap;
        
        BuildingData {
            building: crate::yaml::BuildingInfo {
                id: "TEST_BUILDING".to_string(),
                name: "Test Building".to_string(),
                description: Some("Test building for 3D rendering".to_string()),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0.0".to_string(),
                global_bounding_box: Some(BoundingBox3D {
                    min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                    max: Point3D { x: 100.0, y: 100.0, z: 6.0 },
                }),
            },
            coordinate_systems: vec![],
            metadata: crate::yaml::BuildingMetadata {
                source_file: Some("test.ifc".to_string()),
                parser_version: "1.0.0".to_string(),
                total_entities: 10,
                spatial_entities: 8,
                coordinate_system: "WGS84".to_string(),
                units: "meters".to_string(),
                tags: vec!["test".to_string()],
            },
            floors: vec![
                crate::yaml::FloorData {
                    id: "FLOOR_1".to_string(),
                    name: "Ground Floor".to_string(),
                    level: 0,
                    elevation: 0.0,
                    bounding_box: Some(BoundingBox3D {
                        min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                        max: Point3D { x: 100.0, y: 100.0, z: 3.0 },
                    }),
                    rooms: vec![
                        crate::yaml::RoomData {
                            id: "ROOM_1".to_string(),
                            name: "Room 1".to_string(),
                            room_type: "Office".to_string(),
                            area: Some(400.0),
                            volume: Some(1200.0),
                            position: Point3D { x: 10.0, y: 10.0, z: 0.0 },
                            bounding_box: BoundingBox3D {
                                min: Point3D { x: 10.0, y: 10.0, z: 0.0 },
                                max: Point3D { x: 30.0, y: 30.0, z: 3.0 },
                            },
                            equipment: vec!["EQUIP_1".to_string()],
                            properties: HashMap::new(),
                        }
                    ],
                    equipment: vec![
                        crate::yaml::EquipmentData {
                            id: "EQUIP_1".to_string(),
                            name: "HVAC Unit 1".to_string(),
                            equipment_type: "IFCAIRHANDLINGUNIT".to_string(),
                            system_type: "HVAC".to_string(),
                            position: Point3D { x: 20.0, y: 20.0, z: 1.5 },
                            bounding_box: BoundingBox3D {
                                min: Point3D { x: 18.0, y: 18.0, z: 1.0 },
                                max: Point3D { x: 22.0, y: 22.0, z: 2.0 },
                            },
                            status: crate::yaml::EquipmentStatus::Healthy,
                            properties: HashMap::new(),
                            universal_path: "/TEST_BUILDING/FLOOR_1/ROOM_1/EQUIP_1".to_string(),
                        }
                    ],
                },
                crate::yaml::FloorData {
                    id: "FLOOR_2".to_string(),
                    name: "First Floor".to_string(),
                    level: 1,
                    elevation: 3.0,
                    bounding_box: Some(BoundingBox3D {
                        min: Point3D { x: 0.0, y: 0.0, z: 3.0 },
                        max: Point3D { x: 100.0, y: 100.0, z: 6.0 },
                    }),
                    rooms: vec![],
                    equipment: vec![
                        crate::yaml::EquipmentData {
                            id: "EQUIP_2".to_string(),
                            name: "Light Fixture 1".to_string(),
                            equipment_type: "IFCLIGHTFIXTURE".to_string(),
                            system_type: "Electrical".to_string(),
                            position: Point3D { x: 50.0, y: 50.0, z: 4.5 },
                            bounding_box: BoundingBox3D {
                                min: Point3D { x: 49.0, y: 49.0, z: 4.0 },
                                max: Point3D { x: 51.0, y: 51.0, z: 5.0 },
                            },
                            status: crate::yaml::EquipmentStatus::Warning,
                            properties: HashMap::new(),
                            universal_path: "/TEST_BUILDING/FLOOR_2/EQUIP_2".to_string(),
                        }
                    ],
                },
            ],
        }
    }
    
    #[test]
    fn test_3d_renderer_creation() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        
        let renderer = Building3DRenderer::new(building_data, config);
        
        // Test default camera settings
        assert_eq!(renderer.camera.position.z, 100.0);
        assert_eq!(renderer.camera.fov, 45.0);
        
        // Test default projection settings
        assert_eq!(renderer.projection.projection_type, ProjectionType::Isometric);
        assert_eq!(renderer.projection.view_angle, ViewAngle::Isometric);
    }
    
    #[test]
    fn test_camera_manipulation() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let mut renderer = Building3DRenderer::new(building_data, config);
        
        let new_position = Point3D { x: 100.0, y: 100.0, z: 200.0 };
        let new_target = Point3D { x: 50.0, y: 50.0, z: 0.0 };
        
        renderer.set_camera(new_position, new_target);
        
        assert_eq!(renderer.camera.position.x, 100.0);
        assert_eq!(renderer.camera.position.y, 100.0);
        assert_eq!(renderer.camera.position.z, 200.0);
        assert_eq!(renderer.camera.target.x, 50.0);
        assert_eq!(renderer.camera.target.y, 50.0);
        assert_eq!(renderer.camera.target.z, 0.0);
    }
    
    #[test]
    fn test_projection_manipulation() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let mut renderer = Building3DRenderer::new(building_data, config);
        
        renderer.set_projection(ProjectionType::Perspective, ViewAngle::Front);
        
        assert_eq!(renderer.projection.projection_type, ProjectionType::Perspective);
        assert_eq!(renderer.projection.view_angle, ViewAngle::Front);
    }
    
    #[test]
    fn test_3d_scene_rendering() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let scene = renderer.render_3d_advanced().expect("Failed to render 3D scene");
        
        assert_eq!(scene.building_name, "Test Building");
        assert_eq!(scene.floors.len(), 2);
        assert_eq!(scene.equipment.len(), 2);
        assert_eq!(scene.rooms.len(), 1);
        assert_eq!(scene.metadata.total_floors, 2);
        assert_eq!(scene.metadata.total_equipment, 2);
        assert_eq!(scene.metadata.total_rooms, 1);
    }
    
    #[test]
    fn test_isometric_projection() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let point = Point3D { x: 10.0, y: 20.0, z: 30.0 };
        let projected = renderer.isometric_projection(&point);
        
        // Isometric projection should transform the point
        assert_ne!(projected.x, point.x);
        assert_ne!(projected.y, point.y);
        assert_eq!(projected.z, point.z); // Z should remain the same for depth sorting
    }
    
    #[test]
    fn test_orthographic_projection() {
        let building_data = create_test_building_data();
        let config = Render3DConfig {
            projection_type: ProjectionType::Orthographic,
            view_angle: ViewAngle::TopDown,
            ..Default::default()
        };
        let renderer = Building3DRenderer::new(building_data, config);
        
        let point = Point3D { x: 10.0, y: 20.0, z: 30.0 };
        let projected = renderer.orthographic_projection(&point);
        
        // Orthographic projection should scale the point for TopDown view
        assert_eq!(projected.x, point.x * renderer.projection.scale);
        assert_eq!(projected.y, point.y * renderer.projection.scale);
        assert_eq!(projected.z, point.z);
    }
    
    #[test]
    fn test_vector3d_operations() {
        let vector = Vector3D::new(3.0, 4.0, 0.0);
        
        assert_eq!(vector.length(), 5.0);
        
        let normalized = vector.normalize();
        assert!((normalized.length() - 1.0).abs() < 0.001);
        assert!((normalized.x - 0.6).abs() < 0.001);
        assert!((normalized.y - 0.8).abs() < 0.001);
        assert_eq!(normalized.z, 0.0);
    }
    
    #[test]
    fn test_viewport_creation() {
        let viewport = Viewport3D::new(100, 50);
        
        assert_eq!(viewport.width, 100);
        assert_eq!(viewport.height, 50);
        assert_eq!(viewport.offset_x, 0);
        assert_eq!(viewport.offset_y, 0);
        assert_eq!(viewport.depth_buffer.len(), 50);
        assert_eq!(viewport.depth_buffer[0].len(), 100);
    }
    
    #[test]
    fn test_ascii_rendering() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let scene = renderer.render_3d_advanced().expect("Failed to render 3D scene");
        let ascii_output = renderer.render_to_ascii_advanced(&scene).expect("Failed to render ASCII");
        
        // Check that ASCII output contains expected elements
        assert!(ascii_output.contains("Test Building"));
        assert!(ascii_output.contains("3D Building Visualization"));
        assert!(ascii_output.contains("floors"));
        assert!(ascii_output.contains("equipment"));
        assert!(ascii_output.contains("Projection"));
        assert!(ascii_output.contains("Camera"));
    }
    
    #[test]
    fn test_spatial_index_integration() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        // Test without spatial index
        assert!(renderer.spatial_index.is_none());
        let entities = renderer.query_spatial_entities(&BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 100.0, y: 100.0, z: 10.0 },
        });
        assert_eq!(entities.len(), 0);
        
        // Test spatial queries without spatial index
        let room_entities = renderer.query_entities_in_room("ROOM_1");
        assert_eq!(room_entities.len(), 0);
        
        let floor_entities = renderer.query_entities_on_floor(0);
        assert_eq!(floor_entities.len(), 0);
        
        let nearest = renderer.find_nearest_entity(&Point3D { x: 20.0, y: 20.0, z: 1.5 });
        assert!(nearest.is_none());
    }
    
    #[test]
    fn test_enhanced_rendering_without_spatial_index() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        // Test enhanced rendering without spatial index (should work normally)
        let scene = renderer.render_3d_with_spatial_queries().unwrap();
        
        assert_eq!(scene.building_name, "Test Building");
        assert_eq!(scene.floors.len(), 2);
        assert_eq!(scene.equipment.len(), 2);
        assert_eq!(scene.metadata.total_floors, 2);
        assert_eq!(scene.metadata.total_equipment, 2);
    }
    
    #[test]
    fn test_spatial_query_methods() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        // Test spatial query methods return empty results without spatial index
        let bbox = BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 100.0, y: 100.0, z: 10.0 },
        };
        
        let entities = renderer.query_spatial_entities(&bbox);
        assert_eq!(entities.len(), 0);
        
        let radius_entities = renderer.query_entities_within_radius(&Point3D { x: 20.0, y: 20.0, z: 1.5 }, 10.0);
        assert_eq!(radius_entities.len(), 0);
        
        let clusters = renderer.get_equipment_clusters(2);
        assert_eq!(clusters.len(), 0);
    }
    
    #[test]
    fn test_3d_ascii_art_rendering() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let scene = renderer.render_3d_advanced().unwrap();
        let ascii_art = renderer.render_3d_ascii_art(&scene).unwrap();
        
        // Check that ASCII art contains expected elements
        assert!(ascii_art.contains("3D ASCII Building Visualization"));
        assert!(ascii_art.contains("Legend:"));
        assert!(ascii_art.contains("Test Building"));
        assert!(ascii_art.contains("█=Wall"));
        assert!(ascii_art.contains("▲=HVAC"));
        assert!(ascii_art.contains("●=Electrical"));
    }
    
    #[test]
    fn test_canvas_rendering_methods() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let scene = renderer.render_3d_advanced().unwrap();
        
        // Test that canvas rendering methods work without panicking
        let mut canvas = vec![vec![' '; 120]; 40];
        let mut depth_buffer = vec![vec![f64::NEG_INFINITY; 120]; 40];
        
        // These should not panic
        renderer.render_floors_to_canvas(&scene.floors, &mut canvas, &mut depth_buffer, 120, 40);
        renderer.render_equipment_to_canvas(&scene.equipment, &mut canvas, &mut depth_buffer, 120, 40);
        renderer.render_rooms_to_canvas(&scene.rooms, &mut canvas, &mut depth_buffer, 120, 40);
        
        // Check that some rendering occurred
        let has_content = canvas.iter().any(|row| row.iter().any(|&ch| ch != ' '));
        assert!(has_content);
    }
    
    #[test]
    fn test_screen_projection() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let test_point = Point3D { x: 50.0, y: 50.0, z: 3.0 };
        let screen_point = renderer.project_to_screen(&test_point, 120, 40);
        
        // Check that projection produces valid screen coordinates
        assert!(screen_point.x >= 0.0 && screen_point.x < 120.0);
        assert!(screen_point.y >= 0.0 && screen_point.y < 40.0);
        assert_eq!(screen_point.z, test_point.z); // Z should be preserved
    }
    
    #[test]
    fn test_equipment_symbol_mapping() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let scene = renderer.render_3d_advanced().unwrap();
        
        // Test that equipment symbols are correctly mapped
        let hvac_equipment = scene.equipment.iter().find(|e| e.equipment_type.contains("AIR"));
        let electrical_equipment = scene.equipment.iter().find(|e| e.equipment_type.contains("LIGHT"));
        
        // We should have HVAC equipment (IFCAIRHANDLINGUNIT) and electrical equipment (IFCLIGHTFIXTURE)
        assert!(hvac_equipment.is_some());
        assert!(electrical_equipment.is_some());
        
        // Test symbol mapping logic
        let hvac_symbol = match hvac_equipment.unwrap().equipment_type.as_str() {
            s if s.contains("AIR") => '▲',
            _ => '╬',
        };
        assert_eq!(hvac_symbol, '▲');
        
        let electrical_symbol = match electrical_equipment.unwrap().equipment_type.as_str() {
            s if s.contains("LIGHT") => '●',
            _ => '╬',
        };
        assert_eq!(electrical_symbol, '●');
    }
}
