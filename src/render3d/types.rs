//! Type definitions for 3D rendering

use crate::core::{EquipmentStatus, EquipmentType, RoomType};
use crate::spatial::{BoundingBox3D, Point3D};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

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

impl Default for Camera3D {
    fn default() -> Self {
        Self {
            position: Point3D::new(0.0, 0.0, 10.0),
            target: Point3D::new(0.0, 0.0, 0.0),
            up: Vector3D { x: 0.0, y: 1.0, z: 0.0 },
            fov: 45.0,
            near_clip: 0.1,
            far_clip: 1000.0,
        }
    }
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

/// Rendered 3D scene data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Scene3D {
    pub building_name: Arc<String>,
    pub floors: Vec<Floor3D>,
    pub equipment: Vec<Equipment3D>,
    pub rooms: Vec<Room3D>,
    pub bounding_box: BoundingBox3D,
    pub metadata: SceneMetadata,
}

/// 3D floor representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Floor3D {
    pub id: Arc<String>,
    pub name: Arc<String>,
    pub level: i32,
    pub elevation: f64,
    pub bounding_box: BoundingBox3D,
    pub rooms: Vec<Arc<String>>,     // Room IDs
    pub equipment: Vec<Arc<String>>, // Equipment IDs
}

/// 3D equipment representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Equipment3D {
    pub id: Arc<String>,
    pub name: Arc<String>,
    pub equipment_type: EquipmentType,
    pub status: EquipmentStatus,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub floor_level: i32,
    pub room_id: Option<Arc<String>>,
    pub connections: Vec<Arc<String>>, // Connected equipment IDs
    pub spatial_relationships: Option<usize>, // Number of spatial relationships
    pub nearest_entity_distance: Option<f64>, // Distance to nearest entity
}

/// 3D room representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Room3D {
    pub id: Arc<String>,
    pub name: Arc<String>,
    pub room_type: RoomType,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub floor_level: i32,
    pub equipment: Vec<Arc<String>>, // Equipment IDs in this room
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
