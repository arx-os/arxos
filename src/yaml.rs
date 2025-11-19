//! YAML serialization utilities and legacy data structures
//!
//! Provides YAML serialization/deserialization support and maintains
//! compatibility with legacy building data formats.

use serde::{Deserialize, Serialize};

/// Simple YAML serializer for building data
pub struct BuildingYamlSerializer;

impl Default for BuildingYamlSerializer {
    fn default() -> Self {
        Self::new()
    }
}

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


/// Legacy equipment status enum for YAML backward compatibility
///
/// **Note:** This type is deprecated but MUST be kept for backward compatibility
/// with existing YAML building data files. It is used by `serde_helpers.rs` to
/// serialize/deserialize the old "status" field format.
///
/// **Do not remove** - Used in production for:
/// - `core/serde_helpers.rs` - Backward compatible YAML serialization
/// - Converting between old health-only status and new operational+health model
///
/// For new code, use `core::EquipmentStatus` and `core::EquipmentHealthStatus`.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[deprecated(note = "Use core::EquipmentStatus and core::EquipmentHealthStatus instead. Kept for YAML backward compatibility only.")]
pub enum EquipmentStatus {
    Healthy,
    Warning,
    Critical,
    Unknown,
}

/// Serialize any serializable type to YAML string
pub fn to_yaml<T: Serialize>(data: &T) -> Result<String, serde_yaml::Error> {
    serde_yaml::to_string(data)
}

/// Deserialize YAML string to any deserializable type
pub fn from_yaml<T: for<'a> Deserialize<'a>>(yaml: &str) -> Result<T, serde_yaml::Error> {
    serde_yaml::from_str(yaml)
}