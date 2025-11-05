//! Delta Calculation for IFC Export
//! 
//! Calculates changes between current BuildingData and last sync state
//! to enable incremental exports.

use crate::yaml::{BuildingData, EquipmentData, RoomData};
use super::sync_state::IFCSyncState;
use std::collections::HashSet;
use log::info;

/// Export delta containing new, updated, and deleted entities
#[derive(Debug, Clone)]
pub struct ExportDelta {
    /// New equipment that wasn't in last export
    pub new_equipment: Vec<EquipmentData>,
    /// Updated equipment (changed since last export)
    pub updated_equipment: Vec<EquipmentData>,
    /// Universal Paths of deleted equipment
    pub deleted_equipment: Vec<String>,
    /// New rooms that weren't in last export
    pub new_rooms: Vec<RoomData>,
    /// Updated rooms (changed since last export)
    pub updated_rooms: Vec<RoomData>,
    /// Universal Paths of deleted rooms
    pub deleted_rooms: Vec<String>,
}

impl ExportDelta {
    /// Create an empty delta
    pub fn new() -> Self {
        Self {
            new_equipment: Vec::new(),
            updated_equipment: Vec::new(),
            deleted_equipment: Vec::new(),
            new_rooms: Vec::new(),
            updated_rooms: Vec::new(),
            deleted_rooms: Vec::new(),
        }
    }

    /// Check if delta has any changes
    pub fn has_changes(&self) -> bool {
        !self.new_equipment.is_empty()
            || !self.updated_equipment.is_empty()
            || !self.deleted_equipment.is_empty()
            || !self.new_rooms.is_empty()
            || !self.updated_rooms.is_empty()
            || !self.deleted_rooms.is_empty()
    }

    /// Get total number of changes
    pub fn total_changes(&self) -> usize {
        self.new_equipment.len()
            + self.updated_equipment.len()
            + self.deleted_equipment.len()
            + self.new_rooms.len()
            + self.updated_rooms.len()
            + self.deleted_rooms.len()
    }
}

impl Default for ExportDelta {
    fn default() -> Self {
        Self::new()
    }
}

/// Calculate export delta between current building data and last sync state
/// 
/// # Arguments
/// * `current` - Current BuildingData
/// * `last_state` - Last sync state (if available)
/// 
/// # Returns
/// * ExportDelta containing all changes
pub fn calculate_delta(current: &BuildingData, last_state: Option<&IFCSyncState>) -> ExportDelta {
    let mut delta = ExportDelta::new();

    // If no previous state, everything is new
    let last_state = match last_state {
        Some(state) => state,
        None => {
            // Collect all equipment and rooms as new
            for floor in &current.floors {
                delta.new_equipment.extend(floor.equipment.iter().cloned());
                delta.new_rooms.extend(floor.rooms.iter().cloned());
            }
            return delta;
        }
    };

    // Collect all current Universal Paths
    let mut current_equipment_paths = HashSet::new();
    let mut current_rooms_paths = HashSet::new();
    let mut equipment_by_path: std::collections::HashMap<String, EquipmentData> = std::collections::HashMap::new();
    let mut rooms_by_path: std::collections::HashMap<String, RoomData> = std::collections::HashMap::new();

    for floor in &current.floors {
        for equipment in &floor.equipment {
            let path = equipment.address.as_ref()
                .map(|addr| addr.path.clone())
                .filter(|p| !p.is_empty())
                .or_else(|| {
                    if !equipment.universal_path.is_empty() {
                        Some(equipment.universal_path.clone())
                    } else {
                        None
                    }
                })
                .unwrap_or_else(|| {
                    format!("building/floor-{}/equipment-{}", floor.level, equipment.id)
                });
            
            current_equipment_paths.insert(path.clone());
            equipment_by_path.insert(path.clone(), equipment.clone());
        }

        for room in &floor.rooms {
            let path = room.properties.get("universal_path")
                .cloned()
                .unwrap_or_else(|| {
                    format!("building/floor-{}/room-{}", floor.level, room.id)
                });
            
            current_rooms_paths.insert(path.clone());
            rooms_by_path.insert(path.clone(), room.clone());
        }
    }

    // Find new equipment (in current but not in last state)
    for path in &current_equipment_paths {
        if !last_state.exported_equipment_paths.contains(path) {
            if let Some(equipment) = equipment_by_path.get(path) {
                delta.new_equipment.push(equipment.clone());
            }
        }
    }

    // Find updated equipment (in both, but potentially changed)
    // For now, we'll treat all existing equipment as potentially updated
    // A more sophisticated approach would compare timestamps or content hashes
    for path in &current_equipment_paths {
        if last_state.exported_equipment_paths.contains(path) {
            if let Some(equipment) = equipment_by_path.get(path) {
                // Check if updated (simplified: if last export was before building update)
                if last_state.last_export_timestamp < current.building.updated_at {
                    delta.updated_equipment.push(equipment.clone());
                }
            }
        }
    }

    // Find deleted equipment (in last state but not in current)
    for path in &last_state.exported_equipment_paths {
        if !current_equipment_paths.contains(path) {
            delta.deleted_equipment.push(path.clone());
        }
    }

    // Find new rooms (in current but not in last state)
    for path in &current_rooms_paths {
        if !last_state.exported_rooms_paths.contains(path) {
            if let Some(room) = rooms_by_path.get(path) {
                delta.new_rooms.push(room.clone());
            }
        }
    }

    // Find updated rooms
    for path in &current_rooms_paths {
        if last_state.exported_rooms_paths.contains(path) {
            if let Some(room) = rooms_by_path.get(path) {
                if last_state.last_export_timestamp < current.building.updated_at {
                    delta.updated_rooms.push(room.clone());
                }
            }
        }
    }

    // Find deleted rooms
    for path in &last_state.exported_rooms_paths {
        if !current_rooms_paths.contains(path) {
            delta.deleted_rooms.push(path.clone());
        }
    }

    info!("Delta calculated: {} new, {} updated, {} deleted equipment; {} new, {} updated, {} deleted rooms",
          delta.new_equipment.len(),
          delta.updated_equipment.len(),
          delta.deleted_equipment.len(),
          delta.new_rooms.len(),
          delta.updated_rooms.len(),
          delta.deleted_rooms.len());

    delta
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::yaml::{BuildingInfo, BuildingMetadata, FloorData};
    use crate::spatial::Point3D;
    use chrono::Utc;

    fn create_test_building_data() -> BuildingData {
        BuildingData {
            building: BuildingInfo {
                id: "test-building".to_string(),
                name: "Test Building".to_string(),
                description: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "ArxOS v2.0".to_string(),
                total_entities: 1,
                spatial_entities: 1,
                coordinate_system: "LOCAL".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![
                FloorData {
                    id: "floor-1".to_string(),
                    name: "Floor 1".to_string(),
                    level: 1,
                    elevation: 0.0,
                    rooms: vec![],
                    equipment: vec![
                        crate::yaml::EquipmentData {
                            id: "equipment-1".to_string(),
                            name: "Equipment 1".to_string(),
                            equipment_type: "HVAC".to_string(),
                            system_type: "HVAC".to_string(),
                            position: Point3D::new(1.0, 1.0, 1.0),
                            bounding_box: crate::spatial::BoundingBox3D::new(
                                Point3D::new(0.0, 0.0, 0.0),
                                Point3D::new(2.0, 2.0, 2.0),
                            ),
                            status: crate::yaml::EquipmentStatus::Healthy,
                            properties: std::collections::HashMap::new(),
                            universal_path: "building/floor-1/equipment-1".to_string(),
                            sensor_mappings: None,
                        }
                    ],
                    bounding_box: None,
                }
            ],
            coordinate_systems: vec![],
        }
    }

    #[test]
    fn test_calculate_delta_no_previous_state() {
        let building_data = create_test_building_data();
        let delta = calculate_delta(&building_data, None);
        
        assert_eq!(delta.new_equipment.len(), 1);
        assert_eq!(delta.new_rooms.len(), 0);
        assert!(delta.has_changes());
    }

    #[test]
    fn test_calculate_delta_with_previous_state() {
        let building_data = create_test_building_data();
        let mut sync_state = IFCSyncState::new(std::path::PathBuf::from("test.ifc"));
        
        // Empty previous state - everything should be new
        let delta = calculate_delta(&building_data, Some(&sync_state));
        assert_eq!(delta.new_equipment.len(), 1);
        
        // Update state with current equipment
        let equipment_paths: HashSet<String> = [
            "building/floor-1/equipment-1".to_string(),
        ].into_iter().collect();
        sync_state.update_after_export(equipment_paths, HashSet::new());
        
        // Calculate delta again - should have no new equipment
        let delta2 = calculate_delta(&building_data, Some(&sync_state));
        assert_eq!(delta2.new_equipment.len(), 0);
    }

    #[test]
    fn test_export_delta_has_changes() {
        let mut delta = ExportDelta::new();
        assert!(!delta.has_changes());
        
        delta.new_equipment.push(create_test_building_data().floors[0].equipment[0].clone());
        assert!(delta.has_changes());
    }

    #[test]
    fn test_export_delta_total_changes() {
        let mut delta = ExportDelta::new();
        assert_eq!(delta.total_changes(), 0);
        
        let test_data = create_test_building_data();
        delta.new_equipment.push(test_data.floors[0].equipment[0].clone());
        delta.updated_equipment.push(test_data.floors[0].equipment[0].clone());
        delta.deleted_equipment.push("path1".to_string());
        // Note: create_test_building_data has no rooms, so we'll use deleted_rooms instead
        delta.deleted_rooms.push("path2".to_string());
        
        // Should have 4 changes: new equipment, updated equipment, deleted equipment, deleted room
        assert_eq!(delta.total_changes(), 4);
    }

    #[test]
    fn test_calculate_delta_deleted_equipment() {
        let mut sync_state = IFCSyncState::new(std::path::PathBuf::from("test.ifc"));
        
        // Set up state with some equipment
        let old_equipment_paths: HashSet<String> = [
            "building/floor-1/equipment-1".to_string(),
            "building/floor-1/equipment-2".to_string(),
        ].into_iter().collect();
        sync_state.update_after_export(old_equipment_paths, HashSet::new());
        
        // Create building data with only one equipment (one deleted)
        let building_data = create_test_building_data();
        let delta = calculate_delta(&building_data, Some(&sync_state));
        
        // Should detect one deleted equipment
        assert_eq!(delta.deleted_equipment.len(), 1);
        assert!(delta.deleted_equipment.contains(&"building/floor-1/equipment-2".to_string()));
    }

    #[test]
    fn test_calculate_delta_empty_building() {
        let building_data = BuildingData {
            building: crate::yaml::BuildingInfo {
                id: "empty".to_string(),
                name: "Empty Building".to_string(),
                description: None,
                created_at: chrono::Utc::now(),
                updated_at: chrono::Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: crate::yaml::BuildingMetadata {
                source_file: None,
                parser_version: "Test".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "LOCAL".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![],
        };
        
        let delta = calculate_delta(&building_data, None);
        assert_eq!(delta.new_equipment.len(), 0);
        assert_eq!(delta.new_rooms.len(), 0);
        assert!(!delta.has_changes());
    }
}

