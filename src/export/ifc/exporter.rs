//! IFC Exporter
//! 
//! Converts BuildingData to IFC format using SpatialEntity conversion
//! and the EnhancedIFCParser writer functionality.

use crate::yaml::{BuildingData, EquipmentData, RoomData};
use crate::spatial::SpatialEntity;
use crate::ifc::EnhancedIFCParser;
use crate::error::ArxResult;
use super::mapper::map_equipment_type_string_to_ifc;
use super::{sync_state::IFCSyncState, delta::calculate_delta};
use std::path::Path;
use std::collections::HashSet;
use log::info;

/// IFC exporter for building data
pub struct IFCExporter {
    building_data: BuildingData,
}

impl IFCExporter {
    /// Create a new IFC exporter from building data
    pub fn new(building_data: BuildingData) -> Self {
        Self { building_data }
    }

    /// Export building data to IFC format
    /// 
    /// Converts all equipment and rooms to SpatialEntity format and writes
    /// them to the specified IFC file path.
    /// 
    /// # Arguments
    /// * `output` - Path to output IFC file
    /// 
    /// # Returns
    /// * Result indicating success or failure
    pub fn export(&self, output: &Path) -> ArxResult<()> {
        info!("Starting IFC export to: {}", output.display());
        
        // Convert BuildingData to SpatialEntity vectors
        let mut spatial_entities = Vec::new();
        
        // Convert all equipment
        for floor in &self.building_data.floors {
            for equipment in &floor.equipment {
                let entity = self.convert_equipment_to_spatial_entity(equipment);
                spatial_entities.push(entity);
            }
            
            // Convert all rooms
            for room in &floor.rooms {
                let entity = self.convert_room_to_spatial_entity(room, floor.level);
                spatial_entities.push(entity);
            }
        }
        
        info!("Converted {} spatial entities for IFC export", spatial_entities.len());
        
        // Use EnhancedIFCParser to write the entities
        let parser = EnhancedIFCParser::new();
        let output_str = output.to_str()
            .ok_or_else(|| crate::error::ArxError::io_error("Invalid output path encoding")
                .with_file_path(output.to_string_lossy().as_ref()))?;
        
        parser.write_spatial_entities_to_ifc(&spatial_entities, output_str)?;
        
        info!("Successfully exported IFC file: {}", output.display());
        Ok(())
    }

    /// Export delta (only changes) to IFC format
    /// 
    /// Calculates delta from sync state and exports only changed entities.
    /// 
    /// # Arguments
    /// * `sync_state` - Last sync state (if available)
    /// * `output` - Path to output IFC file
    /// 
    /// # Returns
    /// * Result indicating success or failure
    pub fn export_delta(&self, sync_state: Option<&IFCSyncState>, output: &Path) -> ArxResult<()> {
        info!("Starting delta IFC export to: {}", output.display());
        
        // Calculate delta
        let delta = calculate_delta(&self.building_data, sync_state);
        
        if !delta.has_changes() {
            info!("No changes detected, skipping export");
            return Ok(());
        }
        
        info!("Delta: {} new, {} updated, {} deleted equipment; {} new, {} updated, {} deleted rooms",
              delta.new_equipment.len(),
              delta.updated_equipment.len(),
              delta.deleted_equipment.len(),
              delta.new_rooms.len(),
              delta.updated_rooms.len(),
              delta.deleted_rooms.len());
        
        // Convert delta entities to SpatialEntity vectors
        let mut spatial_entities = Vec::new();
        
        // Convert new and updated equipment
        for equipment in &delta.new_equipment {
            let entity = self.convert_equipment_to_spatial_entity(equipment);
            spatial_entities.push(entity);
        }
        
        for equipment in &delta.updated_equipment {
            let entity = self.convert_equipment_to_spatial_entity(equipment);
            spatial_entities.push(entity);
        }
        
        // Convert new and updated rooms
        // Find floor level for rooms (simplified - would need better lookup in production)
        for floor in &self.building_data.floors {
            for room in &floor.rooms {
                let room_path = room.properties.get("universal_path")
                    .cloned()
                    .unwrap_or_else(|| format!("building/floor-{}/room-{}", floor.level, room.id));
                
                if delta.new_rooms.iter().any(|r| {
                    r.properties.get("universal_path").unwrap_or(&r.id) == &room_path || r.id == room.id
                }) || delta.updated_rooms.iter().any(|r| {
                    r.properties.get("universal_path").unwrap_or(&r.id) == &room_path || r.id == room.id
                }) {
                    let entity = self.convert_room_to_spatial_entity(room, floor.level);
                    spatial_entities.push(entity);
                }
            }
        }
        
        info!("Converted {} delta spatial entities for IFC export", spatial_entities.len());
        
        if spatial_entities.is_empty() {
            info!("No spatial entities to export after delta calculation");
            return Ok(());
        }
        
        // Use EnhancedIFCParser to write the entities
        let parser = EnhancedIFCParser::new();
        let output_str = output.to_str()
            .ok_or_else(|| crate::error::ArxError::io_error("Invalid output path encoding")
                .with_file_path(output.to_string_lossy().as_ref()))?;
        
        parser.write_spatial_entities_to_ifc(&spatial_entities, output_str)?;
        
        info!("Successfully exported delta IFC file: {}", output.display());
        Ok(())
    }

    /// Collect Universal Paths from building data
    /// 
    /// Returns HashSet of Universal Paths for equipment and rooms.
    pub fn collect_universal_paths(&self) -> (HashSet<String>, HashSet<String>) {
        let mut equipment_paths = HashSet::new();
        let mut rooms_paths = HashSet::new();
        
        for floor in &self.building_data.floors {
            for equipment in &floor.equipment {
                let path = if equipment.universal_path.is_empty() {
                    format!("building/floor-{}/equipment-{}", floor.level, equipment.id)
                } else {
                    equipment.universal_path.clone()
                };
                equipment_paths.insert(path);
            }
            
            for room in &floor.rooms {
                let path = room.properties.get("universal_path")
                    .cloned()
                    .unwrap_or_else(|| {
                        // Generate path from room ID, avoiding duplication if room.id already contains "room-"
                        if room.id.starts_with("room-") {
                            format!("building/floor-{}/{}", floor.level, room.id)
                        } else {
                            format!("building/floor-{}/room-{}", floor.level, room.id)
                        }
                    });
                rooms_paths.insert(path);
            }
        }
        
        (equipment_paths, rooms_paths)
    }

    /// Convert EquipmentData to SpatialEntity
    /// 
    /// Uses Universal Path as the stable identifier and preserves
    /// equipment properties for round-trip compatibility.
    fn convert_equipment_to_spatial_entity(&self, equipment: &EquipmentData) -> SpatialEntity {
        // Use Universal Path as the stable ID
        let entity_id = if !equipment.universal_path.is_empty() {
            equipment.universal_path.clone()
        } else {
            // Fallback to equipment ID if Universal Path not set
            equipment.id.clone()
        };
        
        // Map equipment type to IFC entity type
        let ifc_entity_type = map_equipment_type_string_to_ifc(&equipment.equipment_type);
        
        SpatialEntity {
            id: entity_id,
            name: equipment.name.clone(),
            entity_type: ifc_entity_type,
            position: equipment.position,
            bounding_box: equipment.bounding_box.clone(),
            coordinate_system: None,
        }
    }

    /// Convert RoomData to SpatialEntity
    /// 
    /// Generates Universal Path if not present and uses IFCROOM entity type.
    fn convert_room_to_spatial_entity(&self, room: &RoomData, floor_level: i32) -> SpatialEntity {
        // Generate Universal Path for room if not present in properties
        let entity_id = room.properties.get("universal_path")
            .cloned()
            .unwrap_or_else(|| {
                // Generate from floor and room ID, avoiding duplication if room.id already contains "room-"
                if room.id.starts_with("room-") {
                    format!("building/floor-{}/{}", floor_level, room.id)
                } else {
                    format!("building/floor-{}/room-{}", floor_level, room.id)
                }
            });
        
        // Use IFCROOM as entity type
        let entity_type = "IFCROOM".to_string();
        
        SpatialEntity {
            id: entity_id,
            name: room.name.clone(),
            entity_type,
            position: room.position,
            bounding_box: room.bounding_box.clone(),
            coordinate_system: None,
        }
    }
}

#[cfg(test)]
mod tests {
    use crate::spatial::Point3D;
    use super::*;
    use crate::yaml::{BuildingInfo, BuildingMetadata, FloorData, CoordinateSystemInfo};
    use crate::spatial::BoundingBox3D;
    use std::collections::HashMap;

    fn create_test_building_data() -> BuildingData {
        BuildingData {
            building: BuildingInfo {
                id: "test-building".to_string(),
                name: "Test Building".to_string(),
                description: Some("Test building".to_string()),
                created_at: chrono::Utc::now(),
                updated_at: chrono::Utc::now(),
                version: "1.0.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "ArxOS v2.0".to_string(),
                total_entities: 2,
                spatial_entities: 2,
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
                    rooms: vec![
                        RoomData {
                            id: "room-101".to_string(),
                            name: "Room 101".to_string(),
                            room_type: "Office".to_string(),
                            area: Some(25.0),
                            volume: Some(75.0),
                            position: Point3D::new(5.0, 5.0, 1.5),
                            bounding_box: BoundingBox3D::new(
                                Point3D::new(0.0, 0.0, 0.0),
                                Point3D::new(10.0, 5.0, 3.0),
                            ),
                            equipment: vec![],
                            properties: HashMap::new(),
                        }
                    ],
                    equipment: vec![
                        EquipmentData {
                            id: "equipment-1".to_string(),
                            name: "HVAC Unit 1".to_string(),
                            equipment_type: "HVAC".to_string(),
                            system_type: "HVAC".to_string(),
                            position: Point3D::new(2.0, 2.0, 2.0),
                            bounding_box: BoundingBox3D::new(
                                Point3D::new(1.0, 1.0, 1.0),
                                Point3D::new(3.0, 3.0, 3.0),
                            ),
                            status: crate::yaml::EquipmentStatus::Healthy,
                            properties: HashMap::new(),
                            universal_path: "building/floor-1/room-101/equipment-hvac-1".to_string(),
                            sensor_mappings: None,
                        }
                    ],
                    bounding_box: None,
                }
            ],
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

    #[test]
    fn test_convert_equipment_to_spatial_entity() {
        let building_data = create_test_building_data();
        let exporter = IFCExporter::new(building_data);
        
        let equipment = &exporter.building_data.floors[0].equipment[0];
        let entity = exporter.convert_equipment_to_spatial_entity(equipment);
        
        assert_eq!(entity.id, "building/floor-1/room-101/equipment-hvac-1");
        assert_eq!(entity.name, "HVAC Unit 1");
        assert_eq!(entity.entity_type, "IFCAIRTERMINAL");
        assert_eq!(entity.position, equipment.position);
    }

    #[test]
    fn test_convert_room_to_spatial_entity() {
        let building_data = create_test_building_data();
        let exporter = IFCExporter::new(building_data);
        
        let room = &exporter.building_data.floors[0].rooms[0];
        let entity = exporter.convert_room_to_spatial_entity(room, 1);
        
        assert_eq!(entity.id, "building/floor-1/room-101");
        assert_eq!(entity.name, "Room 101");
        assert_eq!(entity.entity_type, "IFCROOM");
        assert_eq!(entity.position, room.position);
    }

    #[test]
    fn test_convert_equipment_without_universal_path() {
        let mut building_data = create_test_building_data();
        building_data.floors[0].equipment[0].universal_path = String::new();
        
        let exporter = IFCExporter::new(building_data);
        let equipment = &exporter.building_data.floors[0].equipment[0];
        let entity = exporter.convert_equipment_to_spatial_entity(equipment);
        
        // Should fall back to equipment ID
        assert_eq!(entity.id, equipment.id);
        assert_eq!(entity.entity_type, "IFCAIRTERMINAL");
    }

    #[test]
    fn test_convert_room_with_universal_path_in_properties() {
        let mut building_data = create_test_building_data();
        building_data.floors[0].rooms[0].properties.insert(
            "universal_path".to_string(),
            "custom/path/room-101".to_string()
        );
        
        let exporter = IFCExporter::new(building_data);
        let room = &exporter.building_data.floors[0].rooms[0];
        let entity = exporter.convert_room_to_spatial_entity(room, 1);
        
        assert_eq!(entity.id, "custom/path/room-101");
    }

    #[test]
    fn test_collect_universal_paths() {
        let building_data = create_test_building_data();
        let exporter = IFCExporter::new(building_data);
        
        let (equipment_paths, rooms_paths) = exporter.collect_universal_paths();
        
        assert_eq!(equipment_paths.len(), 1);
        assert!(equipment_paths.contains("building/floor-1/room-101/equipment-hvac-1"));
        assert_eq!(rooms_paths.len(), 1);
        assert!(rooms_paths.contains("building/floor-1/room-101"));
    }

    #[test]
    fn test_collect_universal_paths_empty_building() {
        let building_data = BuildingData {
            building: BuildingInfo {
                id: "empty".to_string(),
                name: "Empty Building".to_string(),
                description: None,
                created_at: chrono::Utc::now(),
                updated_at: chrono::Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
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
        
        let exporter = IFCExporter::new(building_data);
        let (equipment_paths, rooms_paths) = exporter.collect_universal_paths();
        
        assert_eq!(equipment_paths.len(), 0);
        assert_eq!(rooms_paths.len(), 0);
    }
}

