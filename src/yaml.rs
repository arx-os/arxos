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
        let mut sorted_data = data.clone();
        sorted_data.sort_deterministically();
        Ok(serde_yaml::to_string(&sorted_data)?)
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

impl BuildingData {
    /// Sorts all hierarchical collections deterministically to ensure zero-diff Git output.
    pub fn sort_deterministically(&mut self) {
        // 1. Sort Floors by level (numerical)
        self.building.floors.sort_by_key(|f| f.level);

        for floor in &mut self.building.floors {
            // 2. Sort Wings by name (alphabetical)
            floor.wings.sort_by(|a, b| a.name.cmp(&b.name));
            
            // 3. Sort Floor-level (common area) equipment
            floor.equipment.sort_by(|a, b| a.name.cmp(&b.name));

            for wing in &mut floor.wings {
                // 4. Sort Rooms by name
                wing.rooms.sort_by(|a, b| a.name.cmp(&b.name));
                
                // 5. Sort Wing-level equipment
                wing.equipment.sort_by(|a, b| a.name.cmp(&b.name));

                for room in &mut wing.rooms {
                    // 6. Sort Room equipment
                    room.equipment.sort_by(|a, b| a.name.cmp(&b.name));
                }
            }
        }

        // 7. Sort Global equipment list by ArxAddress path (or name fallback)
        self.equipment.sort_by(|a, b| {
            match (&a.address, &b.address) {
                (Some(addr_a), Some(addr_b)) => addr_a.path.cmp(&addr_b.path),
                _ => a.name.cmp(&b.name),
            }
        });
    }
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