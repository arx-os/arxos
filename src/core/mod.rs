// Core data structures for ArxOS
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Building {
    pub id: String,
    pub name: String,
    pub path: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub floors: Vec<Floor>,
    pub equipment: Vec<Equipment>, // Legacy - will be moved to floors
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Floor {
    pub id: String,
    pub name: String,
    pub level: i32,
    pub wings: Vec<Wing>,
    pub equipment: Vec<Equipment>,
    pub properties: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Wing {
    pub id: String,
    pub name: String,
    pub rooms: Vec<Room>,
    pub equipment: Vec<Equipment>,
    pub properties: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Room {
    pub id: String,
    pub name: String,
    pub room_type: RoomType,
    pub equipment: Vec<Equipment>,
    pub spatial_properties: SpatialProperties,
    pub properties: HashMap<String, String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RoomType {
    Classroom,
    Laboratory,
    Office,
    Gymnasium,
    Cafeteria,
    Library,
    Auditorium,
    Hallway,
    Restroom,
    Storage,
    Mechanical,
    Electrical,
    Other(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialProperties {
    pub position: Position,
    pub dimensions: Dimensions,
    pub bounding_box: BoundingBox,
    pub coordinate_system: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Dimensions {
    pub width: f64,
    pub height: f64,
    pub depth: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundingBox {
    pub min: Position,
    pub max: Position,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Equipment {
    pub id: String,
    pub name: String,
    pub path: String,
    pub equipment_type: EquipmentType,
    pub position: Position,
    pub properties: HashMap<String, String>,
    pub status: EquipmentStatus,
    pub room_id: Option<String>, // Reference to parent room
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EquipmentType {
    HVAC,
    Electrical,
    AV,
    Furniture,
    Safety,
    Plumbing,
    Network,
    Other(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EquipmentStatus {
    Active,
    Inactive,
    Maintenance,
    OutOfOrder,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Position {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub coordinate_system: String,
}

impl Building {
    pub fn new(name: String, path: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            path,
            created_at: now,
            updated_at: now,
            floors: Vec::new(),
            equipment: Vec::new(), // Legacy
        }
    }
    
    /// Add a floor to the building
    pub fn add_floor(&mut self, floor: Floor) {
        self.floors.push(floor);
        self.updated_at = Utc::now();
    }
    
    /// Find a floor by level
    pub fn find_floor(&self, level: i32) -> Option<&Floor> {
        self.floors.iter().find(|f| f.level == level)
    }
    
    /// Find a floor by level (mutable)
    pub fn find_floor_mut(&mut self, level: i32) -> Option<&mut Floor> {
        self.floors.iter_mut().find(|f| f.level == level)
    }
    
    /// Get all rooms in the building
    pub fn get_all_rooms(&self) -> Vec<&Room> {
        self.floors.iter()
            .flat_map(|floor| floor.wings.iter())
            .flat_map(|wing| wing.rooms.iter())
            .collect()
    }
    
    /// Find a room by ID
    pub fn find_room(&self, room_id: &str) -> Option<&Room> {
        self.get_all_rooms().into_iter().find(|room| room.id == room_id)
    }
}

impl Floor {
    pub fn new(name: String, level: i32) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            level,
            wings: Vec::new(),
            equipment: Vec::new(),
            properties: HashMap::new(),
        }
    }
    
    /// Add a wing to the floor
    pub fn add_wing(&mut self, wing: Wing) {
        self.wings.push(wing);
    }
    
    /// Find a wing by name
    pub fn find_wing(&self, name: &str) -> Option<&Wing> {
        self.wings.iter().find(|w| w.name == name)
    }
    
    /// Find a wing by name (mutable)
    pub fn find_wing_mut(&mut self, name: &str) -> Option<&mut Wing> {
        self.wings.iter_mut().find(|w| w.name == name)
    }
}

impl Wing {
    pub fn new(name: String) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            rooms: Vec::new(),
            equipment: Vec::new(),
            properties: HashMap::new(),
        }
    }
    
    /// Add a room to the wing
    pub fn add_room(&mut self, room: Room) {
        self.rooms.push(room);
    }
    
    /// Find a room by name
    pub fn find_room(&self, name: &str) -> Option<&Room> {
        self.rooms.iter().find(|r| r.name == name)
    }
    
    /// Find a room by name (mutable)
    pub fn find_room_mut(&mut self, name: &str) -> Option<&mut Room> {
        self.rooms.iter_mut().find(|r| r.name == name)
    }
}

impl Room {
    pub fn new(name: String, room_type: RoomType) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            room_type,
            equipment: Vec::new(),
            spatial_properties: SpatialProperties::default(),
            properties: HashMap::new(),
            created_at: now,
            updated_at: now,
        }
    }
    
    /// Add equipment to the room
    pub fn add_equipment(&mut self, equipment: Equipment) {
        self.equipment.push(equipment);
        self.updated_at = Utc::now();
    }
    
    /// Find equipment by name
    pub fn find_equipment(&self, name: &str) -> Option<&Equipment> {
        self.equipment.iter().find(|e| e.name == name)
    }
    
    /// Find equipment by name (mutable)
    pub fn find_equipment_mut(&mut self, name: &str) -> Option<&mut Equipment> {
        self.equipment.iter_mut().find(|e| e.name == name)
    }
    
    /// Update spatial properties
    pub fn update_spatial_properties(&mut self, spatial_properties: SpatialProperties) {
        self.spatial_properties = spatial_properties;
        self.updated_at = Utc::now();
    }
}

impl SpatialProperties {
    pub fn new(position: Position, dimensions: Dimensions, coordinate_system: String) -> Self {
        let bounding_box = BoundingBox {
            min: Position {
                x: position.x - dimensions.width / 2.0,
                y: position.y - dimensions.depth / 2.0,
                z: position.z,
                coordinate_system: coordinate_system.clone(),
            },
            max: Position {
                x: position.x + dimensions.width / 2.0,
                y: position.y + dimensions.depth / 2.0,
                z: position.z + dimensions.height,
                coordinate_system: coordinate_system.clone(),
            },
        };
        
        Self {
            position,
            dimensions,
            bounding_box,
            coordinate_system,
        }
    }
}

impl Default for SpatialProperties {
    fn default() -> Self {
        let position = Position {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        };
        
        let dimensions = Dimensions {
            width: 10.0,
            height: 3.0,
            depth: 10.0,
        };
        
        Self::new(position, dimensions, "building_local".to_string())
    }
}

impl Equipment {
    pub fn new(name: String, path: String, equipment_type: EquipmentType) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            path,
            equipment_type,
            position: Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            },
            properties: HashMap::new(),
            status: EquipmentStatus::Active,
            room_id: None,
        }
    }
    
    /// Set the position of the equipment
    pub fn set_position(&mut self, position: Position) {
        self.position = position;
    }
    
    /// Set the room this equipment belongs to
    pub fn set_room(&mut self, room_id: String) {
        self.room_id = Some(room_id);
    }
    
    /// Add a property to the equipment
    pub fn add_property(&mut self, key: String, value: String) {
        self.properties.insert(key, value);
    }
}

// High-level functions for CLI integration
pub fn create_room(name: String, room_type: RoomType) -> Result<(), Box<dyn std::error::Error>> {
    let _room = Room::new(name, room_type);
    // TODO: Implement actual room creation logic
    Ok(())
}

pub fn add_equipment(name: String, equipment_type: EquipmentType) -> Result<(), Box<dyn std::error::Error>> {
    let _equipment = Equipment::new(name, "".to_string(), equipment_type);
    // TODO: Implement actual equipment creation logic
    Ok(())
}

pub fn spatial_query(query_type: &str, entity: &str, params: Vec<String>) -> Result<Vec<SpatialQueryResult>, Box<dyn std::error::Error>> {
    // TODO: Implement actual spatial query logic
    Ok(vec![])
}

pub fn list_rooms() -> Result<Vec<Room>, Box<dyn std::error::Error>> {
    // TODO: Implement actual room listing logic
    Ok(vec![])
}

pub fn get_room(room_name: &str) -> Result<Room, Box<dyn std::error::Error>> {
    // TODO: Implement actual room retrieval logic
    Ok(Room::new(room_name.to_string(), RoomType::Other("unknown".to_string())))
}

pub fn update_room(room_name: &str, property: Vec<String>) -> Result<Room, Box<dyn std::error::Error>> {
    // TODO: Implement actual room update logic
    Ok(Room::new(room_name.to_string(), RoomType::Other("unknown".to_string())))
}

pub fn delete_room(room_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    // TODO: Implement actual room deletion logic
    Ok(())
}

pub fn list_equipment() -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
    // TODO: Implement actual equipment listing logic
    Ok(vec![])
}

pub fn update_equipment(equipment_name: &str, property: Vec<String>) -> Result<Equipment, Box<dyn std::error::Error>> {
    // TODO: Implement actual equipment update logic
    Ok(Equipment::new(equipment_name.to_string(), "".to_string(), EquipmentType::Other("unknown".to_string())))
}

pub fn remove_equipment(equipment_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    // TODO: Implement actual equipment removal logic
    Ok(())
}

pub fn set_spatial_relationship(entity1: &str, entity2: &str, relationship: &str) -> Result<String, Box<dyn std::error::Error>> {
    // TODO: Implement actual spatial relationship logic
    Ok(format!("Relationship set between {} and {}", entity1, entity2))
}

pub fn transform_coordinates(from: &str, to: &str, entity: &str) -> Result<String, Box<dyn std::error::Error>> {
    // TODO: Implement actual coordinate transformation logic
    Ok(format!("Transformed {} from {} to {}", entity, from, to))
}

pub fn validate_spatial(entity: Option<&str>, tolerance: Option<f64>) -> Result<String, Box<dyn std::error::Error>> {
    // TODO: Implement actual spatial validation logic
    Ok(format!("Spatial validation completed for {:?}", entity))
}

#[derive(Debug, Clone)]
pub struct SpatialQueryResult {
    pub entity_name: String,
    pub entity_type: String,
    pub position: Position,
    pub distance: f64,
}

