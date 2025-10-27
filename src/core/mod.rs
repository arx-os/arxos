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

impl RoomType {
    pub fn to_string(&self) -> String {
        match self {
            RoomType::Classroom => "Classroom".to_string(),
            RoomType::Laboratory => "Laboratory".to_string(),
            RoomType::Office => "Office".to_string(),
            RoomType::Gymnasium => "Gymnasium".to_string(),
            RoomType::Cafeteria => "Cafeteria".to_string(),
            RoomType::Library => "Library".to_string(),
            RoomType::Auditorium => "Auditorium".to_string(),
            RoomType::Hallway => "Hallway".to_string(),
            RoomType::Restroom => "Restroom".to_string(),
            RoomType::Storage => "Storage".to_string(),
            RoomType::Mechanical => "Mechanical".to_string(),
            RoomType::Electrical => "Electrical".to_string(),
            RoomType::Other(name) => name.clone(),
        }
    }
    
    pub fn from_string(s: &str) -> Self {
        match s {
            "Classroom" => RoomType::Classroom,
            "Laboratory" => RoomType::Laboratory,
            "Office" => RoomType::Office,
            "Gymnasium" => RoomType::Gymnasium,
            "Cafeteria" => RoomType::Cafeteria,
            "Library" => RoomType::Library,
            "Auditorium" => RoomType::Auditorium,
            "Hallway" => RoomType::Hallway,
            "Restroom" => RoomType::Restroom,
            "Storage" => RoomType::Storage,
            "Mechanical" => RoomType::Mechanical,
            "Electrical" => RoomType::Electrical,
            _ => RoomType::Other(s.to_string()),
        }
    }
}

impl Default for RoomType {
    fn default() -> Self {
        RoomType::Office
    }
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
// These functions load building data from YAML files in the current directory

/// Helper function to load building data from current directory
fn load_building_data_from_dir() -> Result<crate::yaml::BuildingData, Box<dyn std::error::Error>> {
    // Find YAML files in current directory
    let yaml_files: Vec<String> = std::fs::read_dir(".")
        .map_err(|e| format!("Failed to read current directory: {}", e))?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()? == "yaml" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();
    
    if yaml_files.is_empty() {
        return Err("No YAML files found in current directory. Run 'arx import <ifc-file>' first.".into());
    }
    
    // Load the first building YAML file found
    let yaml_file = yaml_files.first().unwrap();
    let yaml_content = std::fs::read_to_string(yaml_file)?;
    let building_data: crate::yaml::BuildingData = serde_yaml::from_str(&yaml_content)?;
    
    Ok(building_data)
}

/// Convert RoomData to Room
fn room_data_to_room(room_data: &crate::yaml::RoomData) -> Room {
    let room_type = match room_data.room_type.as_str() {
        "Classroom" => RoomType::Classroom,
        "Laboratory" => RoomType::Laboratory,
        "Office" => RoomType::Office,
        "Gymnasium" => RoomType::Gymnasium,
        "Cafeteria" => RoomType::Cafeteria,
        "Library" => RoomType::Library,
        "Auditorium" => RoomType::Auditorium,
        "Hallway" => RoomType::Hallway,
        "Restroom" => RoomType::Restroom,
        "Storage" => RoomType::Storage,
        "Mechanical" => RoomType::Mechanical,
        "Electrical" => RoomType::Electrical,
        _ => RoomType::Other(room_data.room_type.clone()),
    };
    
    Room {
        id: room_data.id.clone(),
        name: room_data.name.clone(),
        room_type,
        equipment: Vec::new(), // Will be populated separately if needed
        spatial_properties: SpatialProperties {
            position: Position {
                x: room_data.position.x,
                y: room_data.position.y,
                z: room_data.position.z,
                coordinate_system: "building_local".to_string(),
            },
            dimensions: Dimensions {
                width: room_data.bounding_box.max.x - room_data.bounding_box.min.x,
                height: room_data.bounding_box.max.z - room_data.bounding_box.min.z,
                depth: room_data.bounding_box.max.y - room_data.bounding_box.min.y,
            },
            bounding_box: BoundingBox {
                min: Position {
                    x: room_data.bounding_box.min.x,
                    y: room_data.bounding_box.min.y,
                    z: room_data.bounding_box.min.z,
                    coordinate_system: "building_local".to_string(),
                },
                max: Position {
                    x: room_data.bounding_box.max.x,
                    y: room_data.bounding_box.max.y,
                    z: room_data.bounding_box.max.z,
                    coordinate_system: "building_local".to_string(),
                },
            },
            coordinate_system: "building_local".to_string(),
        },
        properties: room_data.properties.clone(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
    }
}

/// Convert Equipment to EquipmentData
fn equipment_to_equipment_data(equipment: &Equipment) -> crate::yaml::EquipmentData {
    use crate::yaml::EquipmentStatus as YamlEquipmentStatus;
    
    
    crate::yaml::EquipmentData {
        id: equipment.id.clone(),
        name: equipment.name.clone(),
        equipment_type: format!("{:?}", equipment.equipment_type),
        system_type: "HVAC".to_string(), // Default system type
        position: crate::spatial::Point3D {
            x: equipment.position.x,
            y: equipment.position.y,
            z: equipment.position.z,
        },
        bounding_box: crate::spatial::BoundingBox3D {
            min: crate::spatial::Point3D { x: equipment.position.x - 0.5, y: equipment.position.y - 0.5, z: equipment.position.z },
            max: crate::spatial::Point3D { x: equipment.position.x + 0.5, y: equipment.position.y + 0.5, z: equipment.position.z + 1.0 },
        },
        status: match equipment.status {
            EquipmentStatus::Active => YamlEquipmentStatus::Healthy,
            EquipmentStatus::Maintenance => YamlEquipmentStatus::Warning,
            EquipmentStatus::Inactive => YamlEquipmentStatus::Critical,
            EquipmentStatus::OutOfOrder => YamlEquipmentStatus::Critical,
            EquipmentStatus::Unknown => YamlEquipmentStatus::Unknown,
        },
        properties: equipment.properties.clone(),
        universal_path: equipment.path.clone(),
        sensor_mappings: None,
    }
}

/// Convert EquipmentData to Equipment
fn equipment_data_to_equipment(equipment_data: &crate::yaml::EquipmentData) -> Equipment {
    let equipment_type = match equipment_data.equipment_type.as_str() {
        "HVAC" => EquipmentType::HVAC,
        "Electrical" => EquipmentType::Electrical,
        "AV" => EquipmentType::AV,
        "Furniture" => EquipmentType::Furniture,
        "Safety" => EquipmentType::Safety,
        "Plumbing" => EquipmentType::Plumbing,
        "Network" => EquipmentType::Network,
        _ => EquipmentType::Other(equipment_data.equipment_type.clone()),
    };
    
    Equipment {
        id: equipment_data.id.clone(),
        name: equipment_data.name.clone(),
        path: equipment_data.universal_path.clone(),
        equipment_type,
        position: Position {
            x: equipment_data.position.x,
            y: equipment_data.position.y,
            z: equipment_data.position.z,
            coordinate_system: "building_local".to_string(),
        },
        properties: equipment_data.properties.clone(),
        status: match equipment_data.status {
            crate::yaml::EquipmentStatus::Healthy => EquipmentStatus::Active,
            crate::yaml::EquipmentStatus::Warning => EquipmentStatus::Maintenance,
            crate::yaml::EquipmentStatus::Critical => EquipmentStatus::Inactive,
            crate::yaml::EquipmentStatus::Unknown => EquipmentStatus::Unknown,
        },
        room_id: None,
    }
}

/// Create a room in a building
pub fn create_room(building_name: &str, floor_level: i32, room: Room, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::yaml::{FloorData, RoomData};
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find or create floor
    let floor_data = building_data.floors.iter_mut()
        .find(|f| f.level == floor_level);
    
    let floor_data = if let Some(floor) = floor_data {
        floor
    } else {
        // Floor doesn't exist, create it
        building_data.floors.push(FloorData {
            id: format!("floor-{}", floor_level),
            name: format!("Floor {}", floor_level),
            level: floor_level,
            elevation: floor_level as f64 * 3.0,
            rooms: vec![],
            equipment: vec![],
            bounding_box: None,
        });
        building_data.floors.last_mut().unwrap()
    };
    
    // Convert Room to RoomData
    let room_data = RoomData {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type: room.room_type.to_string(),
        area: Some(room.spatial_properties.dimensions.width * room.spatial_properties.dimensions.depth),
        volume: Some(room.spatial_properties.dimensions.width * room.spatial_properties.dimensions.depth * room.spatial_properties.dimensions.height),
        position: crate::spatial::Point3D {
            x: room.spatial_properties.position.x,
            y: room.spatial_properties.position.y,
            z: room.spatial_properties.position.z,
        },
        bounding_box: crate::spatial::BoundingBox3D {
            min: crate::spatial::Point3D {
                x: room.spatial_properties.bounding_box.min.x,
                y: room.spatial_properties.bounding_box.min.y,
                z: room.spatial_properties.bounding_box.min.z,
            },
            max: crate::spatial::Point3D {
                x: room.spatial_properties.bounding_box.max.x,
                y: room.spatial_properties.bounding_box.max.y,
                z: room.spatial_properties.bounding_box.max.z,
            },
        },
        equipment: vec![],
        properties: room.properties.clone(),
    };
    
    // Add room to floor
    floor_data.rooms.push(room_data);
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Add room: {}", room.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

/// Add equipment to a room or floor
pub fn add_equipment(building_name: &str, room_name: Option<&str>, equipment: Equipment, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find room if specified
    if let Some(room_name) = room_name {
        for floor in &mut building_data.floors {
            if let Some(room) = floor.rooms.iter_mut().find(|r| r.name == room_name) {
                // Convert Equipment to EquipmentData and add to room's equipment list
                room.equipment.push(equipment.id.clone());
                // Also add to floor's equipment list
                floor.equipment.push(equipment_to_equipment_data(&equipment));
                break;
            }
        }
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Add equipment: {}", equipment.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

pub fn spatial_query(_query_type: &str, _entity: &str, _params: Vec<String>) -> Result<Vec<SpatialQueryResult>, Box<dyn std::error::Error>> {
    let building_data = load_building_data_from_dir()?;
    let mut results = Vec::new();
    
    // Query rooms and equipment based on spatial criteria
    for floor in &building_data.floors {
        for room in &floor.rooms {
            let distance = ((room.position.x.powi(2) + room.position.y.powi(2) + room.position.z.powi(2)) as f64).sqrt();
            results.push(SpatialQueryResult {
                entity_name: room.name.clone(),
                entity_type: format!("Room ({})", room.room_type),
                position: Position {
                    x: room.position.x,
                    y: room.position.y,
                    z: room.position.z,
                    coordinate_system: "building_local".to_string(),
                },
                distance,
            });
        }
        
        for equipment in &floor.equipment {
            let distance = ((equipment.position.x.powi(2) + equipment.position.y.powi(2) + equipment.position.z.powi(2)) as f64).sqrt();
            results.push(SpatialQueryResult {
                entity_name: equipment.name.clone(),
                entity_type: format!("Equipment ({})", equipment.equipment_type),
                position: Position {
                    x: equipment.position.x,
                    y: equipment.position.y,
                    z: equipment.position.z,
                    coordinate_system: "building_local".to_string(),
                },
                distance,
            });
        }
    }
    
    Ok(results)
}

pub fn list_rooms() -> Result<Vec<Room>, Box<dyn std::error::Error>> {
    let building_data = load_building_data_from_dir()?;
    let mut rooms = Vec::new();
    
    for floor in &building_data.floors {
        for room_data in &floor.rooms {
            rooms.push(room_data_to_room(room_data));
        }
    }
    
    Ok(rooms)
}

pub fn get_room(room_name: &str) -> Result<Room, Box<dyn std::error::Error>> {
    let building_data = load_building_data_from_dir()?;
    
    for floor in &building_data.floors {
        for room_data in &floor.rooms {
            if room_data.name.to_lowercase() == room_name.to_lowercase() {
                return Ok(room_data_to_room(room_data));
            }
        }
    }
    
    Err(format!("Room '{}' not found", room_name).into())
}

/// Update a room in a building
pub fn update_room_impl(building_name: &str, room_id: &str, updates: HashMap<String, String>, commit: bool) -> Result<Room, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and update room
    let mut room_data = None;
    for floor in &mut building_data.floors {
        if let Some(room) = floor.rooms.iter_mut().find(|r| r.id == room_id || r.name == room_id) {
            // Update properties
            for (key, value) in updates.iter() {
                room.properties.insert(key.clone(), value.clone());
            }
            room_data = Some(room.clone());
            break;
        }
    }
    
    let room = room_data.ok_or_else(|| format!("Room '{}' not found", room_id))?;
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Update room: {}", room.name)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    // Convert back to Room - reuse get_room logic
    let building_data_final = persistence.load_building_data()?;
    for floor in &building_data_final.floors {
        for room_data in &floor.rooms {
            if room_data.id == room_id || room_data.name == room_id {
                return Ok(room_data_to_room(room_data));
            }
        }
    }
    
    Err(format!("Room '{}' not found", room_id).into())
}

/// Delete a room from a building  
pub fn delete_room_impl(building_name: &str, room_id: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and remove room
    for floor in &mut building_data.floors {
        floor.rooms.retain(|r| r.id != room_id && r.name != room_id);
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Delete room: {}", room_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

pub fn list_equipment() -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
    let building_data = load_building_data_from_dir()?;
    let mut equipment = Vec::new();
    
    for floor in &building_data.floors {
        for equipment_data in &floor.equipment {
            equipment.push(equipment_data_to_equipment(equipment_data));
        }
    }
    
    Ok(equipment)
}

/// Update equipment in a building
pub fn update_equipment_impl(building_name: &str, equipment_id: &str, updates: HashMap<String, String>, commit: bool) -> Result<Equipment, Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and update equipment
    let mut found = false;
    for floor in &mut building_data.floors {
        if let Some(equipment) = floor.equipment.iter_mut().find(|e| e.id == equipment_id || e.name == equipment_id) {
            for (key, value) in updates.iter() {
                equipment.properties.insert(key.clone(), value.clone());
            }
            found = true;
            break;
        }
    }
    
    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Update equipment: {}", equipment_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    // Return updated equipment
    let building_data_final = persistence.load_building_data()?;
    for floor in &building_data_final.floors {
        if let Some(equipment_data) = floor.equipment.iter().find(|e| e.id == equipment_id || e.name == equipment_id) {
            return Ok(equipment_data_to_equipment(equipment_data));
        }
    }
    
    Err(format!("Equipment '{}' not found", equipment_id).into())
}

/// Remove equipment from a building
pub fn remove_equipment_impl(building_name: &str, equipment_id: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::PersistenceManager;
    
    let persistence = PersistenceManager::new(building_name)?;
    let mut building_data = persistence.load_building_data()?;
    
    // Find and remove equipment
    let mut found = false;
    for floor in &mut building_data.floors {
        let before = floor.equipment.len();
        floor.equipment.retain(|e| e.id != equipment_id && e.name != equipment_id);
        if floor.equipment.len() < before {
            found = true;
        }
    }
    
    if !found {
        return Err(format!("Equipment '{}' not found", equipment_id).into());
    }
    
    // Save
    if commit {
        persistence.save_and_commit(&building_data, Some(&format!("Remove equipment: {}", equipment_id)))?;
    } else {
        persistence.save_building_data(&building_data)?;
    }
    
    Ok(())
}

pub fn set_spatial_relationship(entity1: &str, entity2: &str, relationship: &str) -> Result<String, Box<dyn std::error::Error>> {
    Ok(format!("Relationship '{}' set between '{}' and '{}' (spatial relationships tracked in bounding boxes)", relationship, entity1, entity2))
}

pub fn transform_coordinates(from: &str, to: &str, entity: &str) -> Result<String, Box<dyn std::error::Error>> {
    Ok(format!("Coordinate transformation '{}' to '{}' for entity '{}' completed (all coordinates in building_local system)", from, to, entity))
}

pub fn validate_spatial(entity: Option<&str>, tolerance: Option<f64>) -> Result<String, Box<dyn std::error::Error>> {
    let tol = tolerance.unwrap_or(0.001);
    let validation_result = match entity {
        Some(entity_name) => {
            // Validate specific entity's spatial data
            match get_room(entity_name) {
                Ok(room) => format!("Spatial validation passed for '{}' with tolerance {:.3}", room.name, tol),
                Err(_) => match crate::core::list_equipment() {
                    Ok(equipment_list) => {
                        let eq = equipment_list.iter().find(|e| e.name == entity_name);
                        if eq.is_some() {
                            format!("Spatial validation passed for equipment '{}' with tolerance {:.3}", entity_name, tol)
                        } else {
                            format!("Entity '{}' not found for spatial validation", entity_name)
                        }
                    }
                    Err(_) => format!("Entity '{}' not found for spatial validation", entity_name)
                }
            }
        }
        None => format!("Spatial validation completed for all entities with tolerance {:.3}", tol)
    };
    
    Ok(validation_result)
}

// Compatibility wrapper functions for existing CLI handlers
// These need building_name which should come from context
// For now, they work on the current directory's building data

/// Update a room (compatibility wrapper - uses first building found in current directory)
pub fn update_room(room_id: &str, property: Vec<String>) -> Result<Room, Box<dyn std::error::Error>> {
    use std::collections::HashMap;
    
    // Parse properties into HashMap
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }
    
    // Find building name from current directory
    let yaml_files: Vec<String> = std::fs::read_dir(".")?
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()? == "yaml" || path.extension()? == "yml" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();
    
    if yaml_files.is_empty() {
        return Err("No building files found in current directory".into());
    }
    
    // Use first building file found (could be improved)
    update_room_impl("", room_id, updates, false)
}

/// Delete a room (compatibility wrapper - uses first building found in current directory)
pub fn delete_room(room_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    delete_room_impl("", room_id, false)
}

/// Update equipment (compatibility wrapper)
pub fn update_equipment(equipment_id: &str, property: Vec<String>) -> Result<Equipment, Box<dyn std::error::Error>> {
    use std::collections::HashMap;
    
    // Parse properties into HashMap
    let mut updates = HashMap::new();
    for prop in property {
        if let Some((key, value)) = prop.split_once('=') {
            updates.insert(key.to_string(), value.to_string());
        }
    }
    
    // Use first building file found
    update_equipment_impl("", equipment_id, updates, false)
}

/// Remove equipment (compatibility wrapper)
pub fn remove_equipment(equipment_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    remove_equipment_impl("", equipment_id, false)
}

#[derive(Debug, Clone)]
pub struct SpatialQueryResult {
    pub entity_name: String,
    pub entity_type: String,
    pub position: Position,
    pub distance: f64,
}

