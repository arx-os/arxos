//! Building data structure and implementation

use super::{Floor, Room};
use crate::spatial::BoundingBox;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
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
    pub origin: crate::spatial::Point3D,
    pub x_axis: crate::spatial::Point3D,
    pub y_axis: crate::spatial::Point3D,
    pub z_axis: crate::spatial::Point3D,
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
    /// # Panics
    ///
    /// Panics in debug builds if a floor with the same level already exists.
    /// In release builds, duplicate floors are allowed but may cause issues.
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
    /// Returns `Err` if a floor with the same level already exists.
    pub fn try_add_floor(&mut self, floor: Floor) -> Result<(), String> {
        if self.floors.iter().any(|f| f.level == floor.level) {
            return Err(format!("Floor with level {} already exists", floor.level));
        }
        self.floors.push(floor);
        self.updated_at = Utc::now();
        Ok(())
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
        self.floors
            .iter()
            .flat_map(|floor| floor.wings.iter())
            .flat_map(|wing| wing.rooms.iter())
            .collect()
    }

    /// Find a room by ID
    pub fn find_room(&self, room_id: &str) -> Option<&Room> {
        self.get_all_rooms()
            .into_iter()
            .find(|room| room.id == room_id)
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
