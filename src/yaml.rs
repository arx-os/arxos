//! YAML serialization utilities and legacy data structures
//!
//! Provides YAML serialization/deserialization support and maintains
//! compatibility with legacy building data formats.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Simple YAML serializer for building data
pub struct BuildingYamlSerializer;

impl BuildingYamlSerializer {
    pub fn new() -> Self {
        BuildingYamlSerializer
    }

    pub fn serialize(data: &BuildingData) -> Result<String, Box<dyn std::error::Error>> {
        Ok(serde_yaml::to_string(data)?)
    }

    pub fn deserialize(yaml: &str) -> Result<BuildingData, Box<dyn std::error::Error>> {
        Ok(serde_yaml::from_str(yaml)?)
    }

    /// Generic method to serialize any serializable type to YAML
    pub fn to_yaml<T: Serialize>(&self, data: &T) -> Result<String, Box<dyn std::error::Error>> {
        Ok(serde_yaml::to_string(data)?)
    }
}

/// Building data structure for YAML serialization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingData {
    pub building: crate::core::Building,
    pub equipment: Vec<crate::core::Equipment>,
}

/// Legacy building data structure for backwards compatibility
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use new core::Building instead")]
pub struct LegacyBuildingData {
    pub building: BuildingInfo,
    pub metadata: BuildingMetadata,
    pub floors: Vec<FloorData>,
    pub coordinate_systems: Vec<CoordinateSystemInfo>,
}

/// Legacy building info
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use new core types instead")]
pub struct BuildingInfo {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub version: String,
    pub global_bounding_box: Option<BoundingBox>,
}

/// Legacy building metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use new core types instead")]
pub struct BuildingMetadata {
    pub source_file: Option<String>,
    pub parser_version: String,
    pub total_entities: usize,
    pub spatial_entities: usize,
    pub coordinate_system: String,
    pub units: String,
    #[serde(default)]
    pub custom_properties: HashMap<String, String>,
}

/// Legacy floor data
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use new core types instead")]
pub struct FloorData {
    pub name: String,
    pub elevation: f64,
    pub equipment: Vec<EquipmentData>,
    pub bounding_box: Option<BoundingBox>,
}

/// Legacy equipment data
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use new core types instead")]
pub struct EquipmentData {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub address: Option<crate::domain::ArxAddress>,
    pub position: Point3D,
    pub bounding_box: BoundingBox,
    pub status: EquipmentStatus,
    pub properties: HashMap<String, String>,
    pub universal_path: String,
    pub sensor_mappings: Option<HashMap<String, String>>,
}

/// Legacy equipment status
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use new core types instead")]
pub enum EquipmentStatus {
    Healthy,
    Warning,
    Critical,
    Unknown,
}

/// Legacy bounding box
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use spatial types instead")]
pub struct BoundingBox {
    pub min: Point3D,
    pub max: Point3D,
}

/// Legacy 3D point
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use spatial::Point3D instead")]
pub struct Point3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// Legacy coordinate system info
#[derive(Debug, Clone, Serialize, Deserialize)]
#[deprecated(note = "Use spatial types instead")]
pub struct CoordinateSystemInfo {
    pub name: String,
    pub origin: Point3D,
}

/// Serialize any serializable type to YAML string
pub fn to_yaml<T: Serialize>(data: &T) -> Result<String, serde_yaml::Error> {
    serde_yaml::to_string(data)
}

/// Deserialize YAML string to any deserializable type
pub fn from_yaml<T: for<'a> Deserialize<'a>>(yaml: &str) -> Result<T, serde_yaml::Error> {
    serde_yaml::from_str(yaml)
}