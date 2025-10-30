// YAML serialization for ArxOS building data
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use crate::core::Building;
use crate::spatial::{SpatialEntity, Point3D, BoundingBox3D};

/// Top-level building data structure for YAML serialization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingData {
    pub building: BuildingInfo,
    pub metadata: BuildingMetadata,
    pub floors: Vec<FloorData>,
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
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

/// Floor data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FloorData {
    pub id: String,
    pub name: String,
    pub level: i32,
    pub elevation: f64,
    pub rooms: Vec<RoomData>,
    pub equipment: Vec<EquipmentData>,
    pub bounding_box: Option<BoundingBox3D>,
}

/// Room data structure
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
    pub universal_path: String,
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
#[derive(Debug, Clone, Serialize, Deserialize)]
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
        
        // Group spatial entities by type
        let (rooms, equipment) = self.group_spatial_entities(spatial_entities);
        
        // Create floors (simplified - in real implementation, would parse floor information)
        let floors = self.create_floors_from_entities(&rooms, &equipment);
        
        // Calculate global bounding box
        let global_bounding_box = self.calculate_global_bounding_box(spatial_entities);
        
        let building_info = BuildingInfo {
            id: building.id.clone(),
            name: building.name.clone(),
            description: Some(format!("Building parsed from IFC file: {}", source_file.unwrap_or("unknown"))),
            created_at: building.created_at,
            updated_at: now,
            version: "1.0.0".to_string(),
            global_bounding_box,
        };

        let metadata = BuildingMetadata {
            source_file: source_file.map(|s| s.to_string()),
            parser_version: "ArxOS v2.0".to_string(),
            total_entities: spatial_entities.len(),
            spatial_entities: spatial_entities.len(),
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
            tags: vec!["ifc".to_string(), "building".to_string()],
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
    fn group_spatial_entities(&self, entities: &[SpatialEntity]) -> (Vec<SpatialEntity>, Vec<SpatialEntity>) {
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
    fn create_floors_from_entities(&self, rooms: &[SpatialEntity], equipment: &[SpatialEntity]) -> Vec<FloorData> {
        // Group entities by floor level (simplified approach)
        let mut floor_groups: HashMap<i32, Vec<SpatialEntity>> = HashMap::new();
        
        for room in rooms {
            let floor_level = (room.position.z / 3.0).floor() as i32; // Assume 3m floor height
            floor_groups.entry(floor_level).or_default().push(room.clone());
        }
        
        for eq in equipment {
            let floor_level = (eq.position.z / 3.0).floor() as i32;
            floor_groups.entry(floor_level).or_default().push(eq.clone());
        }

        let mut floors = Vec::new();
        for (level, entities) in floor_groups {
            let (floor_rooms, floor_equipment) = self.group_spatial_entities(&entities);
            
            let room_data: Vec<RoomData> = floor_rooms.into_iter().map(|entity| {
                RoomData {
                    id: entity.id.clone(),
                    name: entity.name.clone(),
                    room_type: entity.entity_type.clone(),
                    area: Some(self.calculate_area(&entity.bounding_box)),
                    volume: Some(self.calculate_volume(&entity.bounding_box)),
                    position: entity.position,
                    bounding_box: entity.bounding_box.clone(),
                    equipment: vec![], // Will be populated later
                    properties: HashMap::new(),
                }
            }).collect();

            let equipment_data: Vec<EquipmentData> = floor_equipment.into_iter().map(|entity| {
                EquipmentData {
                    id: entity.id.clone(),
                    name: entity.name.clone(),
                    equipment_type: entity.entity_type.clone(),
                    sensor_mappings: None,
                    system_type: self.determine_system_type(&entity.entity_type),
                    position: entity.position,
                    bounding_box: entity.bounding_box.clone(),
                    status: EquipmentStatus::Healthy,
                    properties: HashMap::new(),
                    universal_path: self.generate_universal_path(&entity),
                }
            }).collect();

            let floor_bounding_box = self.calculate_floor_bounding_box(&entities);

            floors.push(FloorData {
                id: format!("floor-{}", level),
                name: format!("Floor {}", level),
                level,
                elevation: level as f64 * 3.0, // Assume 3m floor height
                rooms: room_data,
                equipment: equipment_data,
                bounding_box: floor_bounding_box,
            });
        }

        floors.sort_by_key(|floor| floor.level);
        floors
    }

    /// Calculate area from bounding box
    fn calculate_area(&self, bbox: &BoundingBox3D) -> f64 {
        (bbox.max.x - bbox.min.x) * (bbox.max.y - bbox.min.y)
    }

    /// Calculate volume from bounding box
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
        
        format!("/BUILDING/FLOOR-{}/{}/{}", floor_level, system_type, entity.name)
    }

    /// Calculate global bounding box for all entities
    fn calculate_global_bounding_box(&self, entities: &[SpatialEntity]) -> Option<BoundingBox3D> {
        if entities.is_empty() {
            return None;
        }

        let points: Vec<Point3D> = entities.iter()
            .flat_map(|entity| vec![entity.bounding_box.min, entity.bounding_box.max])
            .collect();

        BoundingBox3D::from_points(&points)
    }

    /// Calculate floor bounding box
    fn calculate_floor_bounding_box(&self, entities: &[SpatialEntity]) -> Option<BoundingBox3D> {
        self.calculate_global_bounding_box(entities)
    }

    /// Serialize any serializable type to YAML string
    pub fn to_yaml<T: Serialize>(&self, data: &T) -> Result<String, Box<dyn std::error::Error>> {
        let yaml = serde_yaml::to_string(data)?;
        Ok(yaml)
    }

    /// Serialize building data to YAML string (legacy method)
    pub fn to_yaml_building(&self, building_data: &BuildingData) -> Result<String, Box<dyn std::error::Error>> {
        self.to_yaml(building_data)
    }

    /// Write building data to YAML file
    pub fn write_to_file(&self, building_data: &BuildingData, file_path: &str) -> Result<(), Box<dyn std::error::Error>> {
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
        let building_data = serializer.serialize_building(&building, &spatial_entities, Some("test.ifc")).unwrap();

        assert_eq!(building_data.building.name, "Test Building");
        assert_eq!(building_data.metadata.total_entities, 2);
        assert!(!building_data.floors.is_empty());
    }

    #[test]
    fn test_yaml_serialization() {
        let building = Building::new("Test Building".to_string(), "/test".to_string());
        let spatial_entities = vec![];
        let serializer = BuildingYamlSerializer::new();
        let building_data = serializer.serialize_building(&building, &spatial_entities, None).unwrap();
        
        let yaml = serializer.to_yaml(&building_data).unwrap();
        assert!(yaml.contains("Test Building"));
        assert!(yaml.contains("ArxOS v2.0"));
    }
}
