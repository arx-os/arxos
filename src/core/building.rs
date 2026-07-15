//! Building data structure and implementation

use super::{BoundingBox, Floor, Room, Anchor};
use super::domain::ArxAddress;
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
#[derive(Debug, Clone)]
pub struct Building {
    /// Unique identifier for the building
    pub id: String,
    /// Human-readable building name
    pub name: String,
    /// Universal path identifier
    pub path: String,
    /// Building description (optional)
    pub description: Option<String>,
    /// Building version string
    pub version: String,
    /// Global bounding box for the entire building
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
    pub metadata: Option<BuildingMetadata>,
    /// Coordinate systems information
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
    /// IFC product GlobalId when known (stable interchange identity)
    pub ifc_global_id: Option<String>,
    /// Hierarchical ArxOS address (durable on Building YAML SSOT)
    pub address: Option<ArxAddress>,
    /// Collection of anchors dropped in the building
    pub anchors: Vec<Anchor>,
    /// Temporary list of anchor IDs parsed during deserialization
    pub pending_anchor_ids: Vec<String>,
    /// Configurable staging grace window in days for in-flight claims (optional, defaults to 14 days)
    pub claim_grace_period_days: Option<u32>,
}

/// DTO for Building serialization to preserve YAML and Git layout
#[derive(Serialize, Deserialize)]
struct BuildingDto {
    id: String,
    name: String,
    path: String,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    description: Option<String>,
    #[serde(default = "default_version")]
    version: String,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    global_bounding_box: Option<BoundingBox>,
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
    floors: Vec<Floor>,
    #[serde(flatten, skip_serializing_if = "Option::is_none", default)]
    metadata: Option<BuildingMetadata>,
    #[serde(default)]
    coordinate_systems: Vec<CoordinateSystemInfo>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    ifc_global_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    address: Option<ArxAddress>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    anchors: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    claim_grace_period_days: Option<u32>,
}

impl serde::Serialize for Building {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let anchor_ids: Vec<String> = self.anchors.iter().map(|a| a.id.clone()).collect();
        let dto = BuildingDto {
            id: self.id.clone(),
            name: self.name.clone(),
            path: self.path.clone(),
            description: self.description.clone(),
            version: self.version.clone(),
            global_bounding_box: self.global_bounding_box.clone(),
            created_at: self.created_at,
            updated_at: self.updated_at,
            floors: self.floors.clone(),
            metadata: self.metadata.clone(),
            coordinate_systems: self.coordinate_systems.clone(),
            ifc_global_id: self.ifc_global_id.clone(),
            address: self.address.clone(),
            anchors: anchor_ids,
            claim_grace_period_days: self.claim_grace_period_days,
        };
        dto.serialize(serializer)
    }
}

impl<'de> serde::Deserialize<'de> for Building {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let dto = BuildingDto::deserialize(deserializer)?;
        Ok(Building {
            id: dto.id,
            name: dto.name,
            path: dto.path,
            description: dto.description,
            version: dto.version,
            global_bounding_box: dto.global_bounding_box,
            created_at: dto.created_at,
            updated_at: dto.updated_at,
            floors: dto.floors,
            metadata: dto.metadata,
            coordinate_systems: dto.coordinate_systems,
            ifc_global_id: dto.ifc_global_id,
            address: dto.address,
            anchors: Vec::new(),
            pending_anchor_ids: dto.anchors,
            claim_grace_period_days: dto.claim_grace_period_days,
        })
    }
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
            ifc_global_id: None,
            address: None,
            anchors: Vec::new(),
            pending_anchor_ids: Vec::new(),
            claim_grace_period_days: None,
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

    /// Get all rooms in the building (mutable references)
    pub fn get_all_rooms_mut(&mut self) -> Vec<&mut Room> {
        self.floors
            .iter_mut()
            .flat_map(|floor| floor.wings.iter_mut())
            .flat_map(|wing| wing.rooms.iter_mut())
            .collect()
    }

    /// Find a room by its unique ID (mutable reference)
    pub fn find_room_mut(&mut self, room_id: &str) -> Option<&mut Room> {
        self.get_all_rooms_mut()
            .into_iter()
            .find(|room| room.id == room_id)
    }

    /// Get all rooms of a specific type
    pub fn get_rooms_by_type(&self, room_type: &super::RoomType) -> Vec<&Room> {
        self.get_all_rooms()
            .into_iter()
            .filter(|room| {
                std::mem::discriminant(&room.room_type) == std::mem::discriminant(room_type)
            })
            .collect()
    }

    /// Get all equipment in the building (non-duplicated)
    ///
    /// Collects equipment from floors (common areas), wings (common areas),
    /// and rooms.
    pub fn get_all_equipment(&self) -> Vec<&super::Equipment> {
        let mut equipment = Vec::new();
        for floor in &self.floors {
            // Floor level equipment
            for eq in &floor.equipment {
                equipment.push(eq);
            }
            for wing in &floor.wings {
                // Wing level equipment
                for eq in &wing.equipment {
                    equipment.push(eq);
                }
                // Room level equipment
                for room in &wing.rooms {
                    for eq in &room.equipment {
                        equipment.push(eq);
                    }
                }
            }
        }
        equipment
    }

    /// Get all equipment in the building (mutable references, non-duplicated)
    pub fn get_all_equipment_mut(&mut self) -> Vec<&mut super::Equipment> {
        let mut equipment = Vec::new();
        for floor in &mut self.floors {
            for eq in &mut floor.equipment {
                equipment.push(eq);
            }
            for wing in &mut floor.wings {
                for eq in &mut wing.equipment {
                    equipment.push(eq);
                }
                for room in &mut wing.rooms {
                    for eq in &mut room.equipment {
                        equipment.push(eq);
                    }
                }
            }
        }
        equipment
    }

    /// Find an equipment item by its unique ID
    pub fn find_equipment(&self, id: &str) -> Option<&super::Equipment> {
        self.get_all_equipment()
            .into_iter()
            .find(|eq| eq.id.eq_ignore_ascii_case(id) || eq.name.eq_ignore_ascii_case(id))
    }

    /// Find an equipment item by its unique ID or name (mutable reference)
    pub fn find_equipment_mut(&mut self, id: &str) -> Option<&mut super::Equipment> {
        self.get_all_equipment_mut()
            .into_iter()
            .find(|eq| eq.id.eq_ignore_ascii_case(id) || eq.name.eq_ignore_ascii_case(id))
    }

    /// Find equipment within a given radius of a 3D point
    pub fn find_equipment_within_radius(
        &self,
        center: super::spatial::Point3D,
        radius: f64,
    ) -> Vec<&super::Equipment> {
        self.get_all_equipment()
            .into_iter()
            .filter(|eq| {
                let eq_point =
                    super::spatial::Point3D::new(eq.position.x, eq.position.y, eq.position.z);
                center.distance_to(&eq_point) <= radius
            })
            .collect()
    }

    /// Find the nearest equipment item to a 3D point
    pub fn find_nearest_equipment(
        &self,
        center: super::spatial::Point3D,
    ) -> Option<(&super::Equipment, f64)> {
        self.get_all_equipment()
            .into_iter()
            .map(|eq| {
                let eq_point =
                    super::spatial::Point3D::new(eq.position.x, eq.position.y, eq.position.z);
                let distance = center.distance_to(&eq_point);
                (eq, distance)
            })
            .min_by(|(_, dist_a), (_, dist_b)| {
                dist_a
                    .partial_cmp(dist_b)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
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

    /// Get all anchors in the building tree.
    pub fn get_all_anchors(&self) -> Vec<&super::Anchor> {
        let mut anchors = Vec::new();
        for anchor in &self.anchors {
            anchors.push(anchor);
        }
        for floor in &self.floors {
            for anchor in &floor.anchors {
                anchors.push(anchor);
            }
            for wing in &floor.wings {
                for anchor in &wing.anchors {
                    anchors.push(anchor);
                }
                for room in &wing.rooms {
                    for anchor in &room.anchors {
                        anchors.push(anchor);
                    }
                }
            }
        }
        anchors
    }

    /// Get all anchors in the building tree (mutable references).
    pub fn get_all_anchors_mut(&mut self) -> Vec<&mut super::Anchor> {
        let mut anchors = Vec::new();
        for anchor in &mut self.anchors {
            anchors.push(anchor);
        }
        for floor in &mut self.floors {
            for anchor in &mut floor.anchors {
                anchors.push(anchor);
            }
            for wing in &mut floor.wings {
                for anchor in &mut wing.anchors {
                    anchors.push(anchor);
                }
                for room in &mut wing.rooms {
                    for anchor in &mut room.anchors {
                        anchors.push(anchor);
                    }
                }
            }
        }
        anchors
    }

    /// Promote all addresses in the building hierarchy from one branch/prefix to another.
    pub fn promote_addresses(&mut self, from_branch: &str, to_branch: &str) {
        if let Some(addr) = &mut self.address {
            *addr = addr.promote_to_branch(from_branch, to_branch);
        }
        for floor in &mut self.floors {
            if let Some(addr) = &mut floor.address {
                *addr = addr.promote_to_branch(from_branch, to_branch);
            }
            for wing in &mut floor.wings {
                if let Some(addr) = &mut wing.address {
                    *addr = addr.promote_to_branch(from_branch, to_branch);
                }
                for room in &mut wing.rooms {
                    if let Some(addr) = &mut room.address {
                        *addr = addr.promote_to_branch(from_branch, to_branch);
                    }
                    for eq in &mut room.equipment {
                        if let Some(addr) = &mut eq.address {
                            *addr = addr.promote_to_branch(from_branch, to_branch);
                            eq.path = addr.path.clone();
                        }
                    }
                    for anchor in &mut room.anchors {
                        if let Some(addr) = &mut anchor.address {
                            *addr = addr.promote_to_branch(from_branch, to_branch);
                        }
                    }
                }
                for eq in &mut wing.equipment {
                    if let Some(addr) = &mut eq.address {
                        *addr = addr.promote_to_branch(from_branch, to_branch);
                        eq.path = addr.path.clone();
                    }
                }
                for anchor in &mut wing.anchors {
                    if let Some(addr) = &mut anchor.address {
                        *addr = addr.promote_to_branch(from_branch, to_branch);
                    }
                }
            }
            for eq in &mut floor.equipment {
                if let Some(addr) = &mut eq.address {
                    *addr = addr.promote_to_branch(from_branch, to_branch);
                    eq.path = addr.path.clone();
                }
            }
            for anchor in &mut floor.anchors {
                if let Some(addr) = &mut anchor.address {
                    *addr = addr.promote_to_branch(from_branch, to_branch);
                }
            }
        }
        for anchor in &mut self.anchors {
            if let Some(addr) = &mut anchor.address {
                *addr = addr.promote_to_branch(from_branch, to_branch);
            }
        }

        // Update relative poses target_ids that are addresses
        let all_anchors = self.get_all_anchors_mut();
        for anchor in all_anchors {
            for relative_pose in &mut anchor.relative_poses {
                if relative_pose.target_id.starts_with('/') {
                    if let Ok(addr) = super::domain::ArxAddress::from_path(&relative_pose.target_id) {
                        let promoted = addr.promote_to_branch(from_branch, to_branch);
                        relative_pose.target_id = promoted.path;
                    }
                }
            }
        }
    }

    /// Find anchors within a given radius of a 3D point
    pub fn find_anchors_near(
        &self,
        center: super::spatial::Point3D,
        radius: f64,
    ) -> Vec<&super::Anchor> {
        self.get_all_anchors()
            .into_iter()
            .filter(|a| {
                let a_point =
                    super::spatial::Point3D::new(a.position.x, a.position.y, a.position.z);
                center.distance_to(&a_point) <= radius
            })
            .collect()
    }

    /// Find anchors whose confidence is below the specified threshold
    pub fn find_low_confidence_anchors(&self, threshold: f64) -> Vec<&super::Anchor> {
        self.get_all_anchors()
            .into_iter()
            .filter(|a| a.confidence < threshold)
            .collect()
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
            ifc_global_id: None,
            address: None,
            anchors: Vec::new(),
            pending_anchor_ids: Vec::new(),
            claim_grace_period_days: None,
        }
    }
}
