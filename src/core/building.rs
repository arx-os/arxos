//! Building data structure and implementation

use super::{BoundingBox, Floor, Room};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Building metadata (YAML-only field)
///
/// Contains parser metadata, source file information, and tags.
/// This field is optional and omitted from YAML when None.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BuildingMetadata {
    /// Source file path (if loaded from file)
    pub source_file: Option<String>,
    /// Parser version that created this building data
    pub parser_version: String,
    /// Total number of entities in the building
    pub total_entities: usize,
    /// Number of spatial entities
    pub spatial_entities: usize,
    /// Coordinate system name
    pub coordinate_system: String,
    /// Units used (e.g., "meters", "feet")
    pub units: String,
    /// Tags for categorization
    pub tags: Vec<String>,
    /// Additional properties extracted during parsing
    #[serde(default)]
    pub properties: HashMap<String, String>,
}

/// Represents a building in ArxOS
///
/// The `Building` struct is the root entity in the ArxOS hierarchy:
/// Building → Floor → Wing → Room → Equipment
///
/// # Fields
///
/// * `id` - Unique identifier (UUID)
/// * `name` - Human-readable building name
/// * `path` - Universal path identifier for the building
/// * `created_at` - Timestamp when the building was created
/// * `updated_at` - Timestamp of last modification
/// * `floors` - Collection of floors in the building
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Building {
    /// Unique identifier for the building
    pub id: String,
    /// Human-readable building name
    pub name: String,
    /// Universal path identifier
    pub path: String,
    /// Building description (optional)
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub description: Option<String>,
    /// Building version string
    #[serde(default = "default_version")]
    pub version: String,
    /// Global bounding box for the entire building
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub global_bounding_box: Option<BoundingBox>,
    /// Creation timestamp
    pub created_at: DateTime<Utc>,
    /// Last modification timestamp
    pub updated_at: DateTime<Utc>,
    /// Collection of floors in the building
    pub floors: Vec<Floor>,
    // Equipment lives in floors -> wings -> rooms hierarchy
    /// Building metadata (YAML-only field)
    ///
    /// Contains parser metadata, source file information, and tags.
    /// This field is optional and omitted from YAML when None.
    #[serde(flatten, skip_serializing_if = "Option::is_none", default)]
    pub metadata: Option<BuildingMetadata>,
    /// Coordinate systems information
    #[serde(default)]
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
}

/// Default version string for buildings
fn default_version() -> String {
    "1.0.0".to_string()
}

/// Coordinate system information
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CoordinateSystemInfo {
    pub name: String,
    pub origin: crate::core::spatial::Point3D,
    pub x_axis: crate::core::spatial::Point3D,
    pub y_axis: crate::core::spatial::Point3D,
    pub z_axis: crate::core::spatial::Point3D,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    pub description: Option<String>,
}

impl Building {
    /// Create a new building with a unique ID and timestamps
    ///
    /// # Arguments
    ///
    /// * `name` - Human-readable building name
    /// * `path` - Universal path identifier
    ///
    /// # Returns
    ///
    /// A new `Building` instance with empty floors collection
    pub fn new(name: String, path: String) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            path,
            description: None,
            version: default_version(),
            global_bounding_box: None,
            created_at: now,
            updated_at: now,
            floors: Vec::new(),
            metadata: None,
            coordinate_systems: Vec::new(),
        }
    }

    /// Add a floor to the building
    ///
    /// Updates the building's `updated_at` timestamp automatically.
    ///
    /// # Arguments
    ///
    /// * `floor` - The floor to add
    ///
    /// # Panics
    ///
    /// Panics in debug builds if a floor with the same level already exists.
    /// In release builds, duplicate floors are allowed but may cause issues.
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Building, Floor};
    /// let mut building = Building::new("HQ".to_string(), "/hq".to_string());
    /// let floor = Floor::new("Ground Floor".to_string(), 0);
    /// building.add_floor(floor);
    /// assert_eq!(building.floors.len(), 1);
    /// ```
    pub fn add_floor(&mut self, floor: Floor) {
        debug_assert!(
            !self.floors.iter().any(|f| f.level == floor.level),
            "Floor with level {} already exists in building",
            floor.level
        );
        self.floors.push(floor);
        self.updated_at = Utc::now();
    }

    /// Add a floor to the building with validation
    ///
    /// Validates that no floor with the same level exists before adding.
    /// Updates the building's `updated_at` timestamp on success.
    ///
    /// # Arguments
    ///
    /// * `floor` - The floor to add
    ///
    /// # Returns
    ///
    /// * `Ok(())` - Floor was added successfully
    /// * `Err(String)` - A floor with the same level already exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Building, Floor};
    /// let mut building = Building::new("HQ".to_string(), "/hq".to_string());
    /// let floor1 = Floor::new("Ground Floor".to_string(), 0);
    /// let floor2 = Floor::new("Duplicate".to_string(), 0);
    ///
    /// assert!(building.try_add_floor(floor1).is_ok());
    /// assert!(building.try_add_floor(floor2).is_err());
    /// ```
    pub fn try_add_floor(&mut self, floor: Floor) -> Result<(), String> {
        if self.floors.iter().any(|f| f.level == floor.level) {
            return Err(format!("Floor with level {} already exists", floor.level));
        }
        self.floors.push(floor);
        self.updated_at = Utc::now();
        Ok(())
    }

    /// Find a floor by its level number
    ///
    /// # Arguments
    ///
    /// * `level` - The floor level to search for (0 = ground, 1 = first floor, etc.)
    ///
    /// # Returns
    ///
    /// * `Some(&Floor)` - Reference to the floor if found
    /// * `None` - If no floor exists at that level
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Building, Floor};
    /// let mut building = Building::new("HQ".to_string(), "/hq".to_string());
    /// building.add_floor(Floor::new("Ground".to_string(), 0));
    /// building.add_floor(Floor::new("First".to_string(), 1));
    ///
    /// assert!(building.find_floor(0).is_some());
    /// assert!(building.find_floor(1).is_some());
    /// assert!(building.find_floor(2).is_none());
    /// ```
    pub fn find_floor(&self, level: i32) -> Option<&Floor> {
        self.floors.iter().find(|f| f.level == level)
    }

    /// Find a floor by its level number (mutable reference)
    ///
    /// # Arguments
    ///
    /// * `level` - The floor level to search for
    ///
    /// # Returns
    ///
    /// * `Some(&mut Floor)` - Mutable reference to the floor if found
    /// * `None` - If no floor exists at that level
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Building, Floor};
    /// let mut building = Building::new("HQ".to_string(), "/hq".to_string());
    /// building.add_floor(Floor::new("Ground".to_string(), 0));
    ///
    /// if let Some(floor) = building.find_floor_mut(0) {
    ///     floor.name = "Updated Ground Floor".to_string();
    /// }
    /// assert_eq!(building.find_floor(0).unwrap().name, "Updated Ground Floor");
    /// ```
    pub fn find_floor_mut(&mut self, level: i32) -> Option<&mut Floor> {
        self.floors.iter_mut().find(|f| f.level == level)
    }

    /// Get all rooms in the building across all floors and wings
    ///
    /// Flattens the building hierarchy (Building → Floor → Wing → Room)
    /// into a single collection of room references.
    ///
    /// # Returns
    ///
    /// A vector of references to all rooms in the building
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Building, Floor, Wing, Room, RoomType};
    /// let mut building = Building::new("HQ".to_string(), "/hq".to_string());
    /// let mut floor = Floor::new("Ground".to_string(), 0);
    /// let mut wing = Wing::new("East".to_string());
    /// wing.add_room(Room::new("Office 101".to_string(), RoomType::Office));
    /// wing.add_room(Room::new("Office 102".to_string(), RoomType::Office));
    /// floor.add_wing(wing);
    /// building.add_floor(floor);
    ///
    /// let rooms = building.get_all_rooms();
    /// assert_eq!(rooms.len(), 2);
    /// ```
    pub fn get_all_rooms(&self) -> Vec<&Room> {
        self.floors
            .iter()
            .flat_map(|floor| floor.wings.iter())
            .flat_map(|wing| wing.rooms.iter())
            .collect()
    }

    /// Find a room by its unique ID
    ///
    /// Searches across all floors and wings in the building.
    ///
    /// # Arguments
    ///
    /// * `room_id` - The unique room identifier to search for
    ///
    /// # Returns
    ///
    /// * `Some(&Room)` - Reference to the room if found
    /// * `None` - If no room with that ID exists
    ///
    /// # Examples
    ///
    /// ```
    /// use arxos::core::{Building, Floor, Wing, Room, RoomType};
    /// let mut building = Building::new("HQ".to_string(), "/hq".to_string());
    /// let mut floor = Floor::new("Ground".to_string(), 0);
    /// let mut wing = Wing::new("East".to_string());
    /// let room = Room::new("Office 101".to_string(), RoomType::Office);
    /// let room_id = room.id.clone();
    /// wing.add_room(room);
    /// floor.add_wing(wing);
    /// building.add_floor(floor);
    ///
    /// assert!(building.find_room(&room_id).is_some());
    /// assert!(building.find_room("nonexistent").is_none());
    /// ```
    pub fn find_room(&self, room_id: &str) -> Option<&Room> {
        self.get_all_rooms()
            .into_iter()
            .find(|room| room.id == room_id)
    }

    /// Add a property to the building metadata
    pub fn add_metadata_property(&mut self, key: String, value: String) {
        if self.metadata.is_none() {
            self.metadata = Some(BuildingMetadata {
                source_file: None,
                parser_version: "native-1.0".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "building_local".to_string(),
                units: "meters".to_string(),
                tags: Vec::new(),
                properties: HashMap::new(),
            });
        }
        if let Some(meta) = &mut self.metadata {
            meta.properties.insert(key, value);
        }
    }
}

impl Default for Building {
    fn default() -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name: "Default Building".to_string(),
            path: "/default".to_string(),
            description: None,
            version: default_version(),
            global_bounding_box: None,
            created_at: now,
            updated_at: now,
            floors: Vec::new(),
            metadata: None,
            coordinate_systems: Vec::new(),
        }
    }
}
