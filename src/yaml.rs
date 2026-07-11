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

    /// Deserialize YAML into `BuildingData` and rehydrate room equipment.
    ///
    /// After raw deserialization, calls [`BuildingData::rehydrate_room_equipment`] to
    /// populate each room's `equipment` list from the global equipment index.
    pub fn deserialize(yaml: &str) -> Result<BuildingData, Box<dyn std::error::Error>> {
        let mut data: BuildingData = serde_yaml::from_str(yaml)?;
        data.rehydrate_room_equipment();
        Ok(data)
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

    /// Rehydrate room equipment lists after YAML deserialization.
    ///
    /// During YAML deserialization, `Room.equipment` stores only IDs (strings) in
    /// `pending_equipment_ids`.  This method resolves those IDs to full `Equipment`
    /// objects from `self.equipment` (the global list) and populates each room's
    /// `equipment` field.
    ///
    /// This method also clears `pending_equipment_ids` once rehydration is complete.
    ///
    /// # How it works
    ///
    /// Equipment is associated with a room via its `room_id` field.  The YAML stores
    /// only the IDs inside each room block, and the full equipment objects live in
    /// the top-level `equipment` list.  `rehydrate_room_equipment` reconciles these
    /// two sources and re-attaches equipment to the correct room.
    ///
    /// # Example
    ///
    /// ```rust,ignore
    /// let mut data: BuildingData = serde_yaml::from_str(&yaml_str)?;
    /// data.rehydrate_room_equipment(); // fix up room.equipment after deserialization
    /// ```
    pub fn rehydrate_room_equipment(&mut self) {
        // Build a map of equipment_id -> Equipment for O(1) lookup.
        let equipment_by_id: std::collections::HashMap<String, crate::core::Equipment> = self
            .equipment
            .iter()
            .map(|e| (e.id.clone(), e.clone()))
            .collect();

        for floor in &mut self.building.floors {
            for wing in &mut floor.wings {
                for room in &mut wing.rooms {
                    if !room.pending_equipment_ids.is_empty() {
                        // Resolve IDs to Equipment objects.
                        room.equipment = room
                            .pending_equipment_ids
                            .iter()
                            .filter_map(|id| equipment_by_id.get(id).cloned())
                            .collect();
                        // Clear the temporary ID list.
                        room.pending_equipment_ids.clear();
                    }
                }
            }
        }
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{
        Building, Equipment, EquipmentStatus, EquipmentType, Floor, Position, Room, RoomType, Wing,
    };

    /// Build a minimal `BuildingData` with one equipment item attached to a room.
    fn build_test_data_with_room_equipment() -> BuildingData {
        let mut building = Building::new("Test HQ".to_string(), "/test-hq".to_string());

        // Create equipment
        let mut equip = Equipment::new(
            "Desk Lamp".to_string(),
            "/test-hq/f0/wing-a/r101/lamp".to_string(),
            EquipmentType::Furniture,
        );

        // Create room and attach equipment
        let mut room = Room::new("Office 101".to_string(), RoomType::Office);
        equip.set_room(room.id.clone());
        room.add_equipment(equip.clone());

        // Build hierarchy
        let mut wing = Wing::new("Wing A".to_string());
        wing.add_room(room);
        let mut floor = Floor::new("Ground".to_string(), 0);
        floor.add_wing(wing);
        building.add_floor(floor);

        BuildingData {
            building,
            equipment: vec![equip],
        }
    }

    /// Verifies that `BuildingYamlSerializer::serialize` + `BuildingYamlSerializer::deserialize`
    /// preserves the equipment list attached to rooms (the core bug this PR fixes).
    #[test]
    fn test_room_equipment_round_trip() {
        let original = build_test_data_with_room_equipment();

        // Serialize
        let yaml = BuildingYamlSerializer::serialize(&original)
            .expect("serialization should succeed");

        // Deserialize (now calls rehydrate_room_equipment internally)
        let restored =
            BuildingYamlSerializer::deserialize(&yaml).expect("deserialization should succeed");

        let rooms = restored
            .building
            .floors
            .first()
            .expect("floor exists")
            .wings
            .first()
            .expect("wing exists")
            .rooms
            .first()
            .expect("room exists");

        assert_eq!(
            rooms.equipment.len(),
            1,
            "room.equipment should have exactly 1 item after round-trip, got 0 — the rehydration bug"
        );
        assert_eq!(rooms.equipment[0].name, "Desk Lamp");
        // Ensure pending_equipment_ids is cleared after rehydration
        assert!(
            rooms.pending_equipment_ids.is_empty(),
            "pending_equipment_ids should be empty after rehydration"
        );
    }

    /// Verifies that rehydrate_room_equipment is idempotent (calling it twice is safe).
    #[test]
    fn test_rehydrate_room_equipment_idempotent() {
        let original = build_test_data_with_room_equipment();
        let yaml = BuildingYamlSerializer::serialize(&original).expect("serialize");
        let mut data: BuildingData = serde_yaml::from_str(&yaml).expect("raw deserialize");

        // Call twice
        data.rehydrate_room_equipment();
        data.rehydrate_room_equipment();

        let rooms = &data.building.floors[0].wings[0].rooms[0];
        // Second call should not duplicate equipment
        assert_eq!(
            rooms.equipment.len(),
            1,
            "idempotent: rehydration called twice should not duplicate equipment"
        );
    }

    #[test]
    fn test_empty_room_equipment_round_trip() {
        // Room with no equipment should also round-trip cleanly
        let mut building = Building::new("Empty HQ".to_string(), "/empty".to_string());
        let room = Room::new("Empty Room".to_string(), RoomType::Storage);
        let mut wing = Wing::new("Wing A".to_string());
        wing.add_room(room);
        let mut floor = Floor::new("Ground".to_string(), 0);
        floor.add_wing(wing);
        building.add_floor(floor);

        let data = BuildingData { building, equipment: vec![] };

        let yaml = BuildingYamlSerializer::serialize(&data).expect("serialize");
        let restored = BuildingYamlSerializer::deserialize(&yaml).expect("deserialize");

        let rooms = &restored.building.floors[0].wings[0].rooms[0];
        assert_eq!(rooms.equipment.len(), 0, "empty room should have 0 equipment");
    }
}