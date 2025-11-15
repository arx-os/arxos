//! Building3DRenderer implementation for 3D building visualization

use super::canvas_operations;
use super::projections;
use super::scene_cache::SceneCache;
use super::types::*;
use crate::core::{EquipmentStatus, EquipmentType};
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::ifc::{SpatialIndex, SpatialQueryResult, SpatialRelationship};
use crate::yaml::BuildingData;
use std::collections::HashMap;

/// Advanced 3D building renderer with camera and projection systems
pub struct Building3DRenderer {
    pub(super) building_data: BuildingData,
    scene_cache: SceneCache,
    pub(super) config: Render3DConfig,
    pub camera: Camera3D,
    pub projection: Projection3D,
    #[allow(dead_code)]
    pub(super) viewport: Viewport3D,
    pub(super) spatial_index: Option<SpatialIndex>,
}

impl Building3DRenderer {
    /// Create a new advanced 3D building renderer
    pub fn new(building_data: BuildingData, config: Render3DConfig) -> Self {
        let camera = Camera3D::default();
        let projection = Projection3D::new(
            config.projection_type.clone(),
            config.view_angle.clone(),
            config.scale_factor,
        );
        let viewport = Viewport3D::new(config.max_width, config.max_height);
        let scene_cache = SceneCache::new(&building_data);

        Self {
            building_data,
            scene_cache,
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
        spatial_index: SpatialIndex,
    ) -> Self {
        let camera = Camera3D::default();
        let projection = Projection3D::new(
            config.projection_type.clone(),
            config.view_angle.clone(),
            config.scale_factor,
        );
        let viewport = Viewport3D::new(config.max_width, config.max_height);
        let scene_cache = SceneCache::new(&building_data);

        Self {
            building_data,
            scene_cache,
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
    pub fn set_spatial_index(&mut self, spatial_index: SpatialIndex) {
        self.spatial_index = Some(spatial_index);
    }

    /// Get entities within a 3D bounding box using spatial index
    pub fn query_spatial_entities(&self, bbox: &BoundingBox3D) -> Vec<SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_within_bounding_box(bbox.clone())
        } else {
            vec![]
        }
    }

    /// Get entities within a radius of a point using spatial index
    pub fn query_entities_within_radius(
        &self,
        center: &Point3D,
        radius: f64,
    ) -> Vec<SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_within_radius(*center, radius)
        } else {
            vec![]
        }
    }

    /// Get entities in a specific room using spatial index
    pub fn query_entities_in_room(&self, room_id: &str) -> Vec<SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index
                .find_in_room(room_id)
                .into_iter()
                .map(|entity| SpatialQueryResult {
                    entity,
                    distance: 0.0,
                    relationship_type: SpatialRelationship::Within,
                    intersection_points: vec![],
                })
                .collect()
        } else {
            vec![]
        }
    }

    /// Get entities on a specific floor using spatial index
    pub fn query_entities_on_floor(&self, floor: i32) -> Vec<SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index
                .find_in_floor(floor)
                .into_iter()
                .map(|entity| SpatialQueryResult {
                    entity,
                    distance: 0.0,
                    relationship_type: SpatialRelationship::Within,
                    intersection_points: vec![],
                })
                .collect()
        } else {
            vec![]
        }
    }

    /// Find the nearest entity to a point using spatial index
    pub fn find_nearest_entity(&self, point: &Point3D) -> Option<SpatialQueryResult> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index.find_nearest(*point)
        } else {
            None
        }
    }

    /// Get equipment clusters for visualization
    pub fn get_equipment_clusters(&self, min_cluster_size: usize) -> Vec<Vec<SpatialQueryResult>> {
        if let Some(ref spatial_index) = self.spatial_index {
            spatial_index
                .find_equipment_clusters(10.0, min_cluster_size)
                .into_iter()
                .map(|cluster| {
                    cluster
                        .into_iter()
                        .map(|entity| SpatialQueryResult {
                            entity,
                            distance: 0.0,
                            relationship_type: SpatialRelationship::Adjacent,
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
    fn enhance_equipment_with_spatial_data(
        &self,
        equipment: &[Equipment3D],
    ) -> Result<Vec<Equipment3D>, Box<dyn std::error::Error>> {
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

        // Use cached 3D data from building
        let floors = &self.scene_cache.floors;
        let equipment = &self.scene_cache.equipment;
        let rooms = &self.scene_cache.rooms;

        // Calculate overall bounding box
        let bounding_box = self.calculate_overall_bounds(floors, equipment, rooms);

        // Apply 3D transformations
        let transformed_floors = self.transform_floors_3d(floors);
        let transformed_equipment = self.transform_equipment_3d(equipment);
        let transformed_rooms = self.transform_rooms_3d(rooms);

        // Create scene
        let scene = Scene3D {
            building_name: Arc::clone(&self.scene_cache.building_name),
            floors: transformed_floors,
            equipment: transformed_equipment,
            rooms: transformed_rooms,
            bounding_box,
            metadata: SceneMetadata {
                total_floors: self.building_data.building.floors.len(),
                total_rooms: self
                    .building_data
                    .floors
                    .iter()
                    .flat_map(|f| f.wings.iter())
                    .map(|w| w.rooms.len())
                    .sum(),
                total_equipment: self
                    .building_data
                    .floors
                    .iter()
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

        // Use cached 3D data from building
        let floors = &self.scene_cache.floors;
        let equipment = &self.scene_cache.equipment;
        let rooms = &self.scene_cache.rooms;

        // Calculate overall bounding box
        let bounding_box = self.calculate_overall_bounds(floors, equipment, rooms);

        // Use spatial index to enhance equipment data if available
        let enhanced_equipment = if self.spatial_index.is_some() {
            self.enhance_equipment_with_spatial_data(equipment)?
        } else {
            equipment.clone()
        };

        // Apply 3D transformations
        let transformed_floors = self.transform_floors_3d(floors);
        let transformed_equipment = self.transform_equipment_3d(&enhanced_equipment);
        let transformed_rooms = self.transform_rooms_3d(rooms);

        // Create scene with enhanced metadata
        let scene = Scene3D {
            building_name: Arc::clone(&self.scene_cache.building_name),
            floors: transformed_floors,
            equipment: transformed_equipment,
            rooms: transformed_rooms,
            bounding_box,
            metadata: SceneMetadata {
                total_floors: self.building_data.building.floors.len(),
                total_rooms: self
                    .building_data
                    .floors
                    .iter()
                    .flat_map(|f| f.wings.iter())
                    .map(|w| w.rooms.len())
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
    pub fn render_to_ascii_advanced(
        &self,
        scene: &Scene3D,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();

        // Header with camera info
        output.push_str(&format!(
            "🏢 {} - Advanced 3D Building Visualization\n",
            scene.building_name.as_str()
        ));
        output.push_str(&format!(
            "📊 {} floors, {} rooms, {} equipment\n",
            scene.metadata.total_floors, scene.metadata.total_rooms, scene.metadata.total_equipment
        ));
        output.push_str(&format!(
            "🎯 Projection: {} | View: {} | Scale: {:.2}\n",
            scene.metadata.projection_type, scene.metadata.view_angle, self.projection.scale
        ));
        output.push_str(&format!(
            "📷 Camera: ({:.1}, {:.1}, {:.1}) → ({:.1}, {:.1}, {:.1})\n",
            self.camera.position.x,
            self.camera.position.y,
            self.camera.position.z,
            self.camera.target.x,
            self.camera.target.y,
            self.camera.target.z
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

        Ok(output)
    }

    /// Render 3D building as ASCII art with depth and perspective
    pub fn render_3d_ascii_art(
        &self,
        scene: &Scene3D,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();

        // Create a 2D canvas for ASCII rendering
        let canvas_width = self.viewport.width.min(120);
        let canvas_height = self.viewport.height.min(40);
        let mut canvas = vec![vec![' '; canvas_width]; canvas_height];
        let mut depth_buffer = vec![vec![f64::NEG_INFINITY; canvas_width]; canvas_height];

        // Render floors as horizontal planes
        self.render_floors_to_canvas(
            &scene.floors,
            &mut canvas[..],
            &mut depth_buffer[..],
            canvas_width,
            canvas_height,
        );

        // Render equipment as 3D symbols
        self.render_equipment_to_canvas(
            &scene.equipment,
            &mut canvas[..],
            &mut depth_buffer[..],
            canvas_width,
            canvas_height,
        );

        // Render rooms as bounded areas
        self.render_rooms_to_canvas(
            &scene.rooms,
            &mut canvas[..],
            &mut depth_buffer[..],
            canvas_width,
            canvas_height,
        );

        // Convert canvas to string
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        output.push_str(&format!(
            "│ 🏢 {} - 3D ASCII Building Visualization │\n",
            scene.building_name.as_str()
        ));
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");

        for row in canvas {
            let line: String = row.into_iter().collect();
            output.push_str(&format!("│{}│\n", line));
        }

        // Add legend
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        output.push_str(
            "Legend: █=Wall │ ╬=Generic │ ○=Room │ ─=Floor │ ▲=HVAC │ ●=Electrical │ ◊=Plumbing │ ◈=Safety │ ↯=Network │ ♫=AV │ ⌂=Furniture\n",
        );

        Ok(output)
    }

    /// Render floors to ASCII canvas (delegates to canvas_operations module)
    pub fn render_floors_to_canvas(
        &self,
        floors: &[Floor3D],
        canvas: &mut [Vec<char>],
        depth_buffer: &mut [Vec<f64>],
        width: usize,
        height: usize,
    ) {
        let project = |p: &Point3D| self.project_to_screen(p, width, height);
        canvas_operations::render_floors_to_canvas(
            floors,
            canvas,
            depth_buffer,
            width,
            height,
            project,
        );
    }

    /// Render equipment to ASCII canvas (delegates to canvas_operations module)
    pub fn render_equipment_to_canvas(
        &self,
        equipment: &[Equipment3D],
        canvas: &mut [Vec<char>],
        depth_buffer: &mut [Vec<f64>],
        width: usize,
        height: usize,
    ) {
        let project = |p: &Point3D| self.project_to_screen(p, width, height);
        canvas_operations::render_equipment_to_canvas(
            equipment,
            canvas,
            depth_buffer,
            width,
            height,
            project,
        );
    }

    /// Render rooms to ASCII canvas (delegates to canvas_operations module)
    pub fn render_rooms_to_canvas(
        &self,
        rooms: &[Room3D],
        canvas: &mut [Vec<char>],
        depth_buffer: &mut [Vec<f64>],
        width: usize,
        height: usize,
    ) {
        let project = |p: &Point3D| self.project_to_screen(p, width, height);
        canvas_operations::render_rooms_to_canvas(
            rooms,
            canvas,
            depth_buffer,
            width,
            height,
            project,
        );
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

        // Use cached 3D data from building
        let floors = self.scene_cache.floors.clone();
        let equipment = self.scene_cache.equipment.clone();
        let rooms = self.scene_cache.rooms.clone();

        // Calculate overall bounding box
        let bounding_box = self.calculate_overall_bounds(&floors, &equipment, &rooms);

        // Create scene
        let scene = Scene3D {
            building_name: Arc::clone(&self.scene_cache.building_name),
            floors,
            equipment,
            rooms,
            bounding_box,
            metadata: SceneMetadata {
                total_floors: self.building_data.building.floors.len(),
                total_rooms: self
                    .building_data
                    .floors
                    .iter()
                    .flat_map(|f| f.wings.iter())
                    .map(|w| w.rooms.len())
                    .sum(),
                total_equipment: self
                    .building_data
                    .floors
                    .iter()
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
        output.push_str(&format!(
            "🏢 {} - 3D Building Visualization\n",
            scene.building_name.as_str()
        ));
        output.push_str(&format!(
            "📊 {} floors, {} rooms, {} equipment\n",
            scene.metadata.total_floors, scene.metadata.total_rooms, scene.metadata.total_equipment
        ));
        output.push_str(&format!(
            "🎯 Projection: {} | View: {}\n",
            scene.metadata.projection_type, scene.metadata.view_angle
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

        Ok(output)
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
            min: Point3D {
                x: min_x,
                y: min_y,
                z: min_z,
            },
            max: Point3D {
                x: max_x,
                y: max_y,
                z: max_z,
            },
        }
    }

    /// Render a single floor in 3D ASCII
    fn render_floor_3d_ascii(
        &self,
        floor: &Floor3D,
        scene: &Scene3D,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();

        // Floor header
        output.push_str(&format!(
            "┌─ Floor {}: {} (Level {}) ─┐\n",
            floor.level,
            floor.name.as_str(),
            floor.level
        ));

        // Floor elevation info
        output.push_str(&format!("│ Elevation: {:.1}m │\n", floor.elevation));

        // Floor bounding box
        output.push_str(&format!(
            "│ Bounds: ({:.1}, {:.1}, {:.1}) to ({:.1}, {:.1}, {:.1}) │\n",
            floor.bounding_box.min.x,
            floor.bounding_box.min.y,
            floor.bounding_box.min.z,
            floor.bounding_box.max.x,
            floor.bounding_box.max.y,
            floor.bounding_box.max.z
        ));

        // Equipment on this floor
        let floor_equipment: Vec<&Equipment3D> = scene
            .equipment
            .iter()
            .filter(|e| e.floor_level == floor.level)
            .collect();

        if !floor_equipment.is_empty() {
            output.push_str("│ Equipment: ");
            for (i, equipment) in floor_equipment.iter().enumerate() {
                if i > 0 {
                    output.push_str(", ");
                }
                let status_symbol = match equipment.status {
                    EquipmentStatus::Active => "🟢",
                    EquipmentStatus::Maintenance => "🟡",
                    EquipmentStatus::OutOfOrder => "🔴",
                    EquipmentStatus::Inactive | EquipmentStatus::Unknown => "⚪",
                };
                output.push_str(&format!("{}{}", status_symbol, equipment.name.as_str()));
            }
            output.push_str(" │\n");
        }

        // Rooms on this floor
        let floor_rooms: Vec<&Room3D> = scene
            .rooms
            .iter()
            .filter(|r| r.floor_level == floor.level)
            .collect();

        if !floor_rooms.is_empty() {
            output.push_str("│ Rooms: ");
            for (i, room) in floor_rooms.iter().enumerate() {
                if i > 0 {
                    output.push_str(", ");
                }
                output.push_str(&format!("{} ({})", room.name.as_str(), room.room_type));
            }
            output.push_str(" │\n");
        }

        output.push_str("└─────────────────────────────────────────────────────────────┘");

        Ok(output)
    }

    /// Render equipment status summary
    fn render_equipment_status_summary(
        &self,
        scene: &Scene3D,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();

        // Count equipment by status
        let mut status_counts: HashMap<EquipmentStatus, usize> = HashMap::new();
        for equipment in &scene.equipment {
            *status_counts.entry(equipment.status).or_insert(0) += 1;
        }

        output.push_str("📊 Equipment Status Summary:\n");
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");

        for (status, count) in status_counts {
            let symbol = match status {
                EquipmentStatus::Active => "🟢",
                EquipmentStatus::Maintenance => "🟡",
                EquipmentStatus::OutOfOrder => "🔴",
                EquipmentStatus::Inactive | EquipmentStatus::Unknown => "⚪",
            };
            output.push_str(&format!("│ {} {}: {} equipment\n", symbol, status, count));
        }

        output.push_str("└─────────────────────────────────────────────────────────────┘\n");

        Ok(output)
    }

    /// Transform 3D floors with camera and projection
    fn transform_floors_3d(&self, floors: &[Floor3D]) -> Vec<Floor3D> {
        floors
            .iter()
            .map(|floor| {
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
            })
            .collect()
    }

    /// Transform 3D equipment with camera and projection
    fn transform_equipment_3d(&self, equipment: &[Equipment3D]) -> Vec<Equipment3D> {
        equipment
            .iter()
            .map(|eq| {
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
            })
            .collect()
    }

    /// Transform 3D rooms with camera and projection
    fn transform_rooms_3d(&self, rooms: &[Room3D]) -> Vec<Room3D> {
        rooms
            .iter()
            .map(|room| {
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
            })
            .collect()
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

    /// Isometric projection (delegates to projections module)
    pub fn isometric_projection(&self, point: &Point3D) -> Point3D {
        projections::isometric_projection(point, self.projection.scale)
    }

    /// Orthographic projection (delegates to projections module)
    pub fn orthographic_projection(&self, point: &Point3D) -> Point3D {
        projections::orthographic_projection(point, &self.projection)
    }

    /// Perspective projection (delegates to projections module)
    fn perspective_projection(&self, point: &Point3D) -> Point3D {
        projections::perspective_projection(point, &self.camera)
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
            output.push_str(&format!(
                "│ Floor {}: {} (Z: {:.1}m) │\n",
                floor.level,
                floor.name.as_str(),
                floor.elevation
            ));

            // Show equipment on this floor
            let floor_equipment: Vec<&Equipment3D> = scene
                .equipment
                .iter()
                .filter(|e| e.floor_level == floor.level)
                .collect();

            for equipment in &floor_equipment {
                let status_symbol = match equipment.status {
                    EquipmentStatus::Active => "🟢",
                    EquipmentStatus::Maintenance => "🟡",
                    EquipmentStatus::OutOfOrder => "🔴",
                    EquipmentStatus::Inactive | EquipmentStatus::Unknown => "⚪",
                };
                output.push_str(&format!(
                    "│   {} {} at ({:.1}, {:.1}, {:.1}) │\n",
                    status_symbol,
                    equipment.name.as_str(),
                    equipment.position.x,
                    equipment.position.y,
                    equipment.position.z
                ));
            }
        }

        output.push_str("└─────────────────────────────────────────────────────────────┘\n");

        Ok(output)
    }

    /// Render orthographic view
    fn render_orthographic_view(
        &self,
        scene: &Scene3D,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();

        output.push_str(&format!(
            "📐 Orthographic View ({:?}):\n",
            self.projection.view_angle
        ));
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
    fn render_perspective_view(
        &self,
        scene: &Scene3D,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();

        output.push_str("📐 Perspective View:\n");
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        output.push_str(&format!(
            "│ Camera Position: ({:.1}, {:.1}, {:.1}) │\n",
            self.camera.position.x, self.camera.position.y, self.camera.position.z
        ));
        output.push_str(&format!(
            "│ Camera Target: ({:.1}, {:.1}, {:.1}) │\n",
            self.camera.target.x, self.camera.target.y, self.camera.target.z
        ));
        output.push_str(&format!("│ FOV: {:.1}° │\n", self.camera.fov));

        // Show equipment with perspective depth
        let mut equipment_with_depth: Vec<(&Equipment3D, f64)> = scene
            .equipment
            .iter()
            .map(|e| {
                let depth = (e.position.x - self.camera.position.x).powi(2)
                    + (e.position.y - self.camera.position.y).powi(2)
                    + (e.position.z - self.camera.position.z).powi(2);
                (e, depth.sqrt())
            })
            .collect();

        equipment_with_depth
            .sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));

        for (equipment, depth) in &equipment_with_depth {
            let status_symbol = match equipment.status {
                EquipmentStatus::Active => "🟢",
                EquipmentStatus::Maintenance => "🟡",
                EquipmentStatus::OutOfOrder => "🔴",
                EquipmentStatus::Inactive | EquipmentStatus::Unknown => "⚪",
            };
            output.push_str(&format!(
                "│   {} {} (depth: {:.1}m) │\n",
                status_symbol,
                equipment.name.as_str(),
                depth
            ));
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

            let char = match equipment.equipment_type {
                EquipmentType::HVAC => 'H',
                EquipmentType::Electrical => 'E',
                EquipmentType::Safety => 'S',
                EquipmentType::Network => 'N',
                EquipmentType::AV => 'A',
                EquipmentType::Furniture => 'F',
                EquipmentType::Plumbing => 'P',
                EquipmentType::Other(_) => 'O',
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
        let mut floor_equipment: std::collections::HashMap<i32, Vec<&Equipment3D>> =
            std::collections::HashMap::new();
        for equipment in &scene.equipment {
            floor_equipment
                .entry(equipment.floor_level)
                .or_default()
                .push(equipment);
        }

        let mut floors: Vec<_> = floor_equipment.keys().collect();
        floors.sort();

        for &floor_level in &floors {
            output.push_str(&format!("│   Floor {}: ", floor_level));
            if let Some(equipment) = floor_equipment.get(floor_level) {
                for (i, eq) in equipment.iter().enumerate() {
                    if i > 0 {
                        output.push_str(", ");
                    }
                    output.push_str(eq.name.as_str());
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
        equipment_by_y.sort_by(|a, b| {
            a.position
                .y
                .partial_cmp(&b.position.y)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        for equipment in &equipment_by_y {
            output.push_str(&format!(
                "│   {} at Y: {:.1}m, Z: {:.1}m │\n",
                equipment.name.as_str(),
                equipment.position.y,
                equipment.position.z
            ));
        }

        output
    }
}
