// YAML serialization for ArxOS building data
pub mod conversions;

use crate::core::Building;
use crate::spatial::{BoundingBox3D, Point3D, SpatialEntity};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// Conversion functions are available via crate::yaml::conversions::
// They are used by core::operations but accessed directly via the module path

/// Index structure for efficient O(1) lookups in BuildingData
///
/// This index maps floor levels and wing names to their positions in the floors vector,
/// enabling fast lookups without linear searches.
#[derive(Debug, Clone)]
pub struct BuildingDataIndex {
    /// Map from floor level to index in floors vector
    pub floors_by_level: std::collections::HashMap<i32, usize>,
    /// Map from (floor_level, wing_name) to (floor_index, wing_index)
    pub wings_by_key: std::collections::HashMap<(i32, String), (usize, usize)>,
}

impl BuildingDataIndex {
    /// Build an index from BuildingData
    pub fn build(data: &BuildingData) -> Self {
        let mut floors_by_level = std::collections::HashMap::with_capacity(data.floors.len());
        let mut wings_by_key = std::collections::HashMap::new();

        for (floor_idx, floor) in data.floors.iter().enumerate() {
            floors_by_level.insert(floor.level, floor_idx);

            for (wing_idx, wing) in floor.wings.iter().enumerate() {
                wings_by_key.insert((floor.level, wing.name.clone()), (floor_idx, wing_idx));
            }
        }

        Self {
            floors_by_level,
            wings_by_key,
        }
    }

    /// Get floor index by level
    pub fn get_floor_index(&self, level: i32) -> Option<usize> {
        self.floors_by_level.get(&level).copied()
    }

    /// Get wing indices by floor level and wing name
    pub fn get_wing_indices(&self, level: i32, wing_name: &str) -> Option<(usize, usize)> {
        self.wings_by_key
            .get(&(level, wing_name.to_string()))
            .copied()
    }
}

/// Top-level building data structure for YAML serialization
///
/// **UPDATED**: Now uses core types (Floor) instead of FloorData.
/// Floors contain core types (Wing, Room, Equipment), completing the data model unification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingData {
    pub building: BuildingInfo,
    pub metadata: BuildingMetadata,
    #[allow(deprecated)]
    pub floors: Vec<crate::core::Floor>,
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
}

impl BuildingData {
    /// Build an index for efficient lookups
    pub fn build_index(&self) -> BuildingDataIndex {
        BuildingDataIndex::build(self)
    }

    /// Get floor by level using index (O(1) lookup)
    pub fn get_floor_mut(
        &mut self,
        level: i32,
        index: &BuildingDataIndex,
    ) -> Option<&mut crate::core::Floor> {
        index
            .get_floor_index(level)
            .and_then(|idx| self.floors.get_mut(idx))
    }

    /// Get wing by floor level and name using index (O(1) lookup)
    pub fn get_wing_mut(
        &mut self,
        level: i32,
        wing_name: &str,
        index: &BuildingDataIndex,
    ) -> Option<&mut crate::core::Wing> {
        index
            .get_wing_indices(level, wing_name)
            .and_then(|(floor_idx, wing_idx)| {
                self.floors
                    .get_mut(floor_idx)
                    .and_then(|floor| floor.wings.get_mut(wing_idx))
            })
    }

    /// Get or create floor by level, updating index if new floor is created
    pub fn get_or_create_floor_mut(
        &mut self,
        level: i32,
        index: &mut BuildingDataIndex,
    ) -> Result<&mut crate::core::Floor, Box<dyn std::error::Error>> {
        if let Some(floor_idx) = index.get_floor_index(level) {
            Ok(&mut self.floors[floor_idx])
        } else {
            // Create new floor using core type
            use crate::core::Floor;
            let new_floor = Floor::new(format!("Floor {}", level), level);

            let floor_idx = self.floors.len();
            self.floors.push(new_floor);

            // Update index
            index.floors_by_level.insert(level, floor_idx);

            Ok(&mut self.floors[floor_idx])
        }
    }

    /// Get or create wing by floor level and name, updating index if new wing is created
    pub fn get_or_create_wing_mut(
        &mut self,
        level: i32,
        wing_name: &str,
        index: &mut BuildingDataIndex,
    ) -> Result<&mut crate::core::Wing, Box<dyn std::error::Error>> {
        if let Some((floor_idx, wing_idx)) = index.get_wing_indices(level, wing_name) {
            Ok(&mut self.floors[floor_idx].wings[wing_idx])
        } else {
            // Need to get or create floor first
            let floor = self.get_or_create_floor_mut(level, index)?;

            // Create new wing using core type
            use crate::core::Wing;
            let new_wing = Wing::new(wing_name.to_string());

            let wing_idx = floor.wings.len();
            floor.wings.push(new_wing);

            // Update index
            let floor_idx = index.get_floor_index(level).unwrap();
            index
                .wings_by_key
                .insert((level, wing_name.to_string()), (floor_idx, wing_idx));

            Ok(&mut self.floors[floor_idx].wings[wing_idx])
        }
    }
}

impl Default for BuildingData {
    fn default() -> Self {
        let now = chrono::Utc::now();
        BuildingData {
            building: BuildingInfo {
                id: "default-building".to_string(),
                name: "Default Building".to_string(),
                description: Some("Default building for testing".to_string()),
                created_at: now,
                updated_at: now,
                version: "1.0.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "ArxOS v2.0".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "LOCAL".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![CoordinateSystemInfo {
                name: "World".to_string(),
                origin: Point3D::origin(),
                x_axis: Point3D::new(1.0, 0.0, 0.0),
                y_axis: Point3D::new(0.0, 1.0, 0.0),
                z_axis: Point3D::new(0.0, 0.0, 1.0),
                description: Some("Default world coordinate system".to_string()),
            }],
        }
    }
}

/// Building information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingInfo {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub version: String,
    pub global_bounding_box: Option<BoundingBox3D>,
}

/// Building metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingMetadata {
    pub source_file: Option<String>,
    pub parser_version: String,
    pub total_entities: usize,
    pub spatial_entities: usize,
    pub coordinate_system: String,
    pub units: String,
    pub tags: Vec<String>,
}

/// Wing data structure for YAML serialization
///
/// **UPDATED**: Now uses core types (Room, Equipment) instead of RoomData, EquipmentData.
/// This completes the data model unification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WingData {
    pub id: String,
    pub name: String,
    #[allow(deprecated)]
    pub rooms: Vec<crate::core::Room>,
    #[allow(deprecated)]
    pub equipment: Vec<crate::core::Equipment>,
    pub properties: HashMap<String, String>,
}

/// Floor data structure
///
/// **UPDATED**: Now uses core types (Wing, Room, Equipment) instead of WingData, RoomData, EquipmentData.
/// This completes the data model unification.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FloorData {
    pub id: String,
    pub name: String,
    pub level: i32,
    pub elevation: f64,
    #[serde(default)]
    #[allow(deprecated)]
    pub wings: Vec<crate::core::Wing>,
    #[serde(default)]
    #[allow(deprecated)]
    pub rooms: Vec<crate::core::Room>, // Legacy: kept for backward compatibility
    #[allow(deprecated)]
    pub equipment: Vec<crate::core::Equipment>,
    pub bounding_box: Option<BoundingBox3D>,
}

/// Room data structure
///
/// **DEPRECATED**: This type is maintained for backward compatibility.
/// Core types (Room) now serialize directly to YAML format.
/// Use `crate::core::Room` directly with serde serialization instead.
#[deprecated(note = "Use crate::core::Room directly with serde serialization")]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoomData {
    pub id: String,
    pub name: String,
    pub room_type: String,
    pub area: Option<f64>,
    pub volume: Option<f64>,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub equipment: Vec<String>, // Equipment IDs
    pub properties: HashMap<String, String>,
}

/// Equipment data structure
///
/// **DEPRECATED**: This type is maintained for backward compatibility.
/// Core types (Equipment) now serialize directly to YAML format.
/// Use `crate::core::Equipment` directly with serde serialization instead.
#[deprecated(note = "Use crate::core::Equipment directly with serde serialization")]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquipmentData {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub system_type: String,
    pub position: Point3D,
    pub bounding_box: BoundingBox3D,
    pub status: EquipmentStatus,
    pub properties: HashMap<String, String>,
    /// Universal path identifier (legacy, kept for backward compatibility)
    #[serde(default)]
    pub universal_path: String,
    /// ArxOS Address (new hierarchical addressing system)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub address: Option<crate::domain::ArxAddress>,
    pub sensor_mappings: Option<Vec<SensorMapping>>, // Sensor-to-equipment mapping
}

/// Sensor mapping structure for equipment
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorMapping {
    pub sensor_id: String,
    pub sensor_type: String,
    pub thresholds: HashMap<String, ThresholdConfig>,
}

/// Threshold configuration for sensor values
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThresholdConfig {
    pub min: Option<f64>,
    pub max: Option<f64>,
    pub warning_min: Option<f64>,
    pub warning_max: Option<f64>,
    pub critical_min: Option<f64>,
    pub critical_max: Option<f64>,
}

/// Equipment status
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum EquipmentStatus {
    Healthy,
    Warning,
    Critical,
    Unknown,
}

/// Coordinate system information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoordinateSystemInfo {
    pub name: String,
    pub origin: Point3D,
    pub x_axis: Point3D,
    pub y_axis: Point3D,
    pub z_axis: Point3D,
    pub description: Option<String>,
}

/// YAML serializer for building data
pub struct BuildingYamlSerializer {
    // YAML serialization configuration
}

impl Default for BuildingYamlSerializer {
    fn default() -> Self {
        Self::new()
    }
}

impl BuildingYamlSerializer {
    pub fn new() -> Self {
        Self {}
    }

    /// Convert building and spatial entities to YAML structure
    pub fn serialize_building(
        &self,
        building: &Building,
        spatial_entities: &[SpatialEntity],
        source_file: Option<&str>,
    ) -> Result<BuildingData, Box<dyn std::error::Error>> {
        let now = Utc::now();

        // Convert building.floors to Floor (core type) if available (from IFC hierarchy)
        // Otherwise, create floors from spatial entities
        let floors: Vec<crate::core::Floor> = if !building.floors.is_empty() {
            self.convert_floors_from_building(building)?
        } else {
            // Group spatial entities by type
            let (rooms, equipment) = self.group_spatial_entities(spatial_entities);
            // Create floors from spatial entities
            self.create_floors_from_entities(&rooms, &equipment)
        };

        // Calculate global bounding box
        let global_bounding_box = self.calculate_global_bounding_box(spatial_entities);

        let building_info = BuildingInfo {
            id: building.id.clone(),
            name: building.name.clone(),
            description: Some(format!(
                "Building parsed from IFC file: {}",
                source_file.unwrap_or("unknown")
            )),
            created_at: building.created_at,
            updated_at: now,
            version: "1.0.0".to_string(),
            global_bounding_box,
        };

        // Use building.metadata if available, otherwise create default
        let metadata = if let Some(ref building_metadata) = building.metadata {
            // Convert core BuildingMetadata to YAML BuildingMetadata
            BuildingMetadata {
                source_file: building_metadata.source_file.clone(),
                parser_version: building_metadata.parser_version.clone(),
                total_entities: building_metadata.total_entities,
                spatial_entities: building_metadata.spatial_entities,
                coordinate_system: building_metadata.coordinate_system.clone(),
                units: building_metadata.units.clone(),
                tags: building_metadata.tags.clone(),
            }
        } else {
            // Create default metadata
            BuildingMetadata {
                source_file: source_file.map(|s| s.to_string()),
                parser_version: "ArxOS v2.0".to_string(),
                total_entities: spatial_entities.len(),
                spatial_entities: spatial_entities.len(),
                coordinate_system: "World".to_string(),
                units: "meters".to_string(),
                tags: vec!["ifc".to_string(), "building".to_string()],
            }
        };

        let coordinate_systems = vec![CoordinateSystemInfo {
            name: "World".to_string(),
            origin: Point3D::origin(),
            x_axis: Point3D::new(1.0, 0.0, 0.0),
            y_axis: Point3D::new(0.0, 1.0, 0.0),
            z_axis: Point3D::new(0.0, 0.0, 1.0),
            description: Some("Default world coordinate system".to_string()),
        }];

        Ok(BuildingData {
            building: building_info,
            metadata,
            floors,
            coordinate_systems,
        })
    }

    /// Group spatial entities by type
    fn group_spatial_entities(
        &self,
        entities: &[SpatialEntity],
    ) -> (Vec<SpatialEntity>, Vec<SpatialEntity>) {
        let mut rooms = Vec::new();
        let mut equipment = Vec::new();

        for entity in entities {
            match entity.entity_type.as_str() {
                "IFCSPACE" => rooms.push(entity.clone()),
                "IFCFLOWTERMINAL" | "IFCBUILDINGELEMENT" => equipment.push(entity.clone()),
                _ => equipment.push(entity.clone()), // Default to equipment
            }
        }

        (rooms, equipment)
    }

    /// Create floors from spatial entities
    fn create_floors_from_entities(
        &self,
        rooms: &[SpatialEntity],
        equipment: &[SpatialEntity],
    ) -> Vec<crate::core::Floor> {
        // Group entities by floor level (simplified approach)
        let mut floor_groups: HashMap<i32, Vec<SpatialEntity>> = HashMap::new();

        for room in rooms {
            let floor_level = (room.position.z / 3.0).floor() as i32; // Assume 3m floor height
            floor_groups
                .entry(floor_level)
                .or_default()
                .push(room.clone());
        }

        for eq in equipment {
            let floor_level = (eq.position.z / 3.0).floor() as i32;
            floor_groups
                .entry(floor_level)
                .or_default()
                .push(eq.clone());
        }

        let mut floors = Vec::new();
        for (level, entities) in floor_groups {
            let (floor_rooms, floor_equipment) = self.group_spatial_entities(&entities);

            // Convert SpatialEntity to Room (core type)
            let rooms: Vec<crate::core::Room> = floor_rooms
                .into_iter()
                .map(|entity| self.spatial_entity_to_room(&entity))
                .collect();

            // Convert SpatialEntity to Equipment (core type)
            let equipment: Vec<crate::core::Equipment> = floor_equipment
                .into_iter()
                .map(|entity| self.spatial_entity_to_equipment(&entity, level))
                .collect();

            let floor_bounding_box = self.calculate_floor_bounding_box(&entities);

            use crate::core::Floor;
            floors.push(Floor {
                id: format!("floor-{}", level),
                name: format!("Floor {}", level),
                level,
                elevation: Some(level as f64 * 3.0), // Assume 3m floor height
                bounding_box: floor_bounding_box,
                wings: Vec::new(), // Rooms will be organized into wings when converting from core model
                equipment,
                properties: HashMap::new(),
            });

            // Add rooms to a default wing
            if !rooms.is_empty() {
                use crate::core::Wing;
                let mut default_wing = Wing::new("Default".to_string());
                for room in rooms {
                    default_wing.add_room(room);
                }
                if let Some(floor) = floors.last_mut() {
                    floor.wings.push(default_wing);
                }
            }
        }

        floors.sort_by_key(|floor| floor.level);
        floors
    }

    /// Calculate area from bounding box
    #[allow(dead_code)]
    fn calculate_area(&self, bbox: &BoundingBox3D) -> f64 {
        (bbox.max.x - bbox.min.x) * (bbox.max.y - bbox.min.y)
    }

    /// Calculate volume from bounding box
    #[allow(dead_code)]
    fn calculate_volume(&self, bbox: &BoundingBox3D) -> f64 {
        (bbox.max.x - bbox.min.x) * (bbox.max.y - bbox.min.y) * (bbox.max.z - bbox.min.z)
    }

    /// Determine system type from entity type
    fn determine_system_type(&self, entity_type: &str) -> String {
        match entity_type {
            "IFCFLOWTERMINAL" => "HVAC".to_string(),
            "IFCBUILDINGELEMENT" => "STRUCTURAL".to_string(),
            "IFCWALL" => "STRUCTURAL".to_string(),
            "IFCDOOR" => "ARCHITECTURAL".to_string(),
            "IFCWINDOW" => "ARCHITECTURAL".to_string(),
            _ => "UNKNOWN".to_string(),
        }
    }

    /// Generate universal path for equipment
    fn generate_universal_path(&self, entity: &SpatialEntity) -> String {
        let floor_level = (entity.position.z / 3.0).floor() as i32;
        let system_type = self.determine_system_type(&entity.entity_type);

        format!(
            "/BUILDING/FLOOR-{}/{}/{}",
            floor_level, system_type, entity.name
        )
    }

    /// Calculate global bounding box for all entities
    fn calculate_global_bounding_box(&self, entities: &[SpatialEntity]) -> Option<BoundingBox3D> {
        if entities.is_empty() {
            return None;
        }

        let points: Vec<Point3D> = entities
            .iter()
            .flat_map(|entity| vec![entity.bounding_box.min, entity.bounding_box.max])
            .collect();

        BoundingBox3D::from_points(&points)
    }

    /// Calculate floor bounding box
    fn calculate_floor_bounding_box(&self, entities: &[SpatialEntity]) -> Option<BoundingBox3D> {
        self.calculate_global_bounding_box(entities)
    }

    /// Convert SpatialEntity to Room (core type)
    fn spatial_entity_to_room(&self, entity: &SpatialEntity) -> crate::core::Room {
        use crate::core::{BoundingBox, Dimensions, Position, Room, RoomType, SpatialProperties};

        let position = Position {
            x: entity.position.x,
            y: entity.position.y,
            z: entity.position.z,
            coordinate_system: entity
                .coordinate_system
                .as_ref()
                .map(|cs| format!("{:?}", cs))
                .unwrap_or_else(|| "building_local".to_string()),
        };

        let dimensions = Dimensions {
            width: entity.bounding_box.max.x - entity.bounding_box.min.x,
            height: entity.bounding_box.max.z - entity.bounding_box.min.z,
            depth: entity.bounding_box.max.y - entity.bounding_box.min.y,
        };

        let bounding_box = BoundingBox {
            min: Position {
                x: entity.bounding_box.min.x,
                y: entity.bounding_box.min.y,
                z: entity.bounding_box.min.z,
                coordinate_system: position.coordinate_system.clone(),
            },
            max: Position {
                x: entity.bounding_box.max.x,
                y: entity.bounding_box.max.y,
                z: entity.bounding_box.max.z,
                coordinate_system: position.coordinate_system.clone(),
            },
        };

        let spatial_properties = SpatialProperties {
            position,
            dimensions,
            bounding_box,
            coordinate_system: "building_local".to_string(),
        };

        Room {
            id: entity.id.clone(),
            name: entity.name.clone(),
            room_type: RoomType::Other(entity.entity_type.clone()),
            equipment: Vec::new(),
            spatial_properties,
            properties: std::collections::HashMap::new(),
            created_at: None,
            updated_at: None,
        }
    }

    /// Convert SpatialEntity to Equipment (core type)
    fn spatial_entity_to_equipment(
        &self,
        entity: &SpatialEntity,
        _floor_level: i32,
    ) -> crate::core::Equipment {
        use crate::core::{Equipment, EquipmentType, Position};

        let equipment_type = match entity.entity_type.as_str() {
            "IFCAIRTERMINAL" | "IFCFLOWTERMINAL" | "IFCAIRHANDLINGUNIT" => EquipmentType::HVAC,
            "IFCLIGHTFIXTURE" | "IFCDISTRIBUTIONELEMENT" | "IFCSWITCHINGDEVICE" => {
                EquipmentType::Electrical
            }
            "IFCFIREALARM" | "IFCFIREDETECTOR" => EquipmentType::Safety,
            "IFCPIPE" | "IFCPIPEFITTING" | "IFCTANK" => EquipmentType::Plumbing,
            _ => EquipmentType::Other(entity.entity_type.clone()),
        };

        let universal_path = self.generate_universal_path(entity);

        let mut equipment = Equipment::new(entity.name.clone(), universal_path, equipment_type);

        equipment.id = entity.id.clone();
        equipment.position = Position {
            x: entity.position.x,
            y: entity.position.y,
            z: entity.position.z,
            coordinate_system: entity
                .coordinate_system
                .as_ref()
                .map(|cs| format!("{:?}", cs))
                .unwrap_or_else(|| "building_local".to_string()),
        };

        equipment
    }

    /// Convert Building.floors (from IFC hierarchy) to Floor (core type)
    fn convert_floors_from_building(
        &self,
        building: &Building,
    ) -> Result<Vec<crate::core::Floor>, Box<dyn std::error::Error>> {
        // Building.floors is already Vec<Floor>, so we can use it directly
        // Just need to ensure elevation and bounding_box are set
        let mut floors: Vec<crate::core::Floor> = building.floors.clone();

        for floor in &mut floors {
            // Set elevation if not already set
            if floor.elevation.is_none() {
                floor.elevation = Some(floor.level as f64 * 3.0); // Estimate based on level
            }

            // Calculate bounding box from rooms if not set
            if floor.bounding_box.is_none() {
                let mut bbox_points = Vec::new();
                for wing in &floor.wings {
                    for room in &wing.rooms {
                        let bbox = &room.spatial_properties.bounding_box;
                        bbox_points.push(crate::spatial::Point3D::new(
                            bbox.min.x, bbox.min.y, bbox.min.z,
                        ));
                        bbox_points.push(crate::spatial::Point3D::new(
                            bbox.max.x, bbox.max.y, bbox.max.z,
                        ));
                    }
                }
                if !bbox_points.is_empty() {
                    floor.bounding_box = crate::spatial::BoundingBox3D::from_points(&bbox_points);
                }
            }
        }

        Ok(floors)
    }

    /// Determine system type from EquipmentType
    #[allow(dead_code)]
    fn determine_equipment_system_type(&self, eq_type: &crate::core::EquipmentType) -> String {
        match eq_type {
            crate::core::EquipmentType::HVAC => "HVAC".to_string(),
            crate::core::EquipmentType::Electrical => "ELECTRICAL".to_string(),
            crate::core::EquipmentType::Plumbing => "PLUMBING".to_string(),
            crate::core::EquipmentType::Safety => "SAFETY".to_string(),
            crate::core::EquipmentType::Network => "NETWORK".to_string(),
            crate::core::EquipmentType::AV => "AV".to_string(),
            crate::core::EquipmentType::Furniture => "FURNITURE".to_string(),
            crate::core::EquipmentType::Other(_) => "OTHER".to_string(),
        }
    }

    /// Serialize any serializable type to YAML string
    pub fn to_yaml<T: Serialize>(&self, data: &T) -> Result<String, Box<dyn std::error::Error>> {
        let yaml = serde_yaml::to_string(data)?;
        Ok(yaml)
    }

    /// Serialize building data to YAML string (legacy method)
    pub fn to_yaml_building(
        &self,
        building_data: &BuildingData,
    ) -> Result<String, Box<dyn std::error::Error>> {
        self.to_yaml(building_data)
    }

    /// Write building data to YAML file
    pub fn write_to_file(
        &self,
        building_data: &BuildingData,
        file_path: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let yaml = self.to_yaml(building_data)?;
        std::fs::write(file_path, yaml)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::Building;

    #[test]
    fn test_building_yaml_serialization() {
        let building = Building::new("Test Building".to_string(), "/test".to_string());
        let spatial_entities = vec![
            SpatialEntity::new(
                "room-1".to_string(),
                "Room 101".to_string(),
                "IFCSPACE".to_string(),
                Point3D::new(10.0, 20.0, 0.0),
            ),
            SpatialEntity::new(
                "equipment-1".to_string(),
                "VAV-301".to_string(),
                "IFCFLOWTERMINAL".to_string(),
                Point3D::new(15.0, 25.0, 0.0),
            ),
        ];

        let serializer = BuildingYamlSerializer::new();
        let building_data = serializer
            .serialize_building(&building, &spatial_entities, Some("test.ifc"))
            .unwrap();

        assert_eq!(building_data.building.name, "Test Building");
        assert_eq!(building_data.metadata.total_entities, 2);
        assert!(!building_data.floors.is_empty());
    }

    #[test]
    fn test_yaml_serialization() {
        let building = Building::new("Test Building".to_string(), "/test".to_string());
        let spatial_entities = vec![];
        let serializer = BuildingYamlSerializer::new();
        let building_data = serializer
            .serialize_building(&building, &spatial_entities, None)
            .unwrap();

        let yaml = serializer.to_yaml(&building_data).unwrap();
        assert!(yaml.contains("Test Building"));
        assert!(yaml.contains("ArxOS v2.0"));
    }
}
