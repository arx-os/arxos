//! IFC Exporter
//! 
//! Converts BuildingData to IFC format using SpatialEntity conversion
//! and the EnhancedIFCParser writer functionality.

use crate::yaml::BuildingData;
use crate::core::{Equipment, Room};
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
            
            // Convert all rooms (rooms are in wings)
            for wing in &floor.wings {
                for room in &wing.rooms {
                    let entity = self.convert_room_to_spatial_entity(room, floor.level);
                    spatial_entities.push(entity);
                }
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
        // Note: delta still uses EquipmentData, so we need to convert or update delta module
        // For now, we'll convert EquipmentData to Equipment-like access
        use crate::yaml::conversions::equipment_data_to_equipment;
        for equipment_data in &delta.new_equipment {
            let equipment = equipment_data_to_equipment(equipment_data);
            let entity = self.convert_equipment_to_spatial_entity(&equipment);
            spatial_entities.push(entity);
        }
        
        for equipment_data in &delta.updated_equipment {
            let equipment = equipment_data_to_equipment(equipment_data);
            let entity = self.convert_equipment_to_spatial_entity(&equipment);
            spatial_entities.push(entity);
        }
        
        // Convert new and updated rooms
        // Find floor level for rooms (simplified - would need better lookup in production)
        for floor in &self.building_data.floors {
            for wing in &floor.wings {
                for room in &wing.rooms {
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

    /// Collect address paths from building data
    /// 
    /// Returns HashSet of address paths for equipment and rooms.
    /// Prefers ArxAddress when available, falls back to universal_path for backward compatibility.
    pub fn collect_universal_paths(&self) -> (HashSet<String>, HashSet<String>) {
        let mut equipment_paths = HashSet::new();
        let mut rooms_paths = HashSet::new();
        
        for floor in &self.building_data.floors {
            for equipment in &floor.equipment {
                let path = equipment.address.as_ref()
                    .map(|addr| addr.path.clone())
                    .filter(|p| !p.is_empty())
                    .or_else(|| {
                        if !equipment.path.is_empty() {
                            Some(equipment.path.clone())
                        } else {
                            None
                        }
                    })
                    .unwrap_or_else(|| {
                        format!("building/floor-{}/equipment-{}", floor.level, equipment.id)
                    });
                equipment_paths.insert(path);
            }
            
            for wing in &floor.wings {
                for room in &wing.rooms {
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
        }
        
        (equipment_paths, rooms_paths)
    }

    /// Convert Equipment to SpatialEntity
    /// 
    /// Uses ArxAddress when available, falls back to path or equipment ID.
    /// Preserves equipment properties for round-trip compatibility.
    fn convert_equipment_to_spatial_entity(&self, equipment: &Equipment) -> SpatialEntity {
        use crate::spatial::{Point3D, BoundingBox3D};
        
        // Prefer ArxAddress, then path, then equipment ID
        let entity_id = equipment.address.as_ref()
            .map(|addr| addr.path.clone())
            .filter(|p| !p.is_empty())
            .or_else(|| {
                if !equipment.path.is_empty() {
                    Some(equipment.path.clone())
                } else {
                    None
                }
            })
            .unwrap_or_else(|| equipment.id.clone());
        
        // Map equipment type to IFC entity type
        let equipment_type_str = format!("{:?}", equipment.equipment_type);
        let ifc_entity_type = map_equipment_type_string_to_ifc(&equipment_type_str);
        
        // Convert position to Point3D
        let position = Point3D {
            x: equipment.position.x,
            y: equipment.position.y,
            z: equipment.position.z,
        };
        
        // Create bounding box from position (equipment doesn't have direct bounding_box)
        // Use a default size if needed
        let bounding_box = BoundingBox3D {
            min: Point3D {
                x: position.x - 0.5,
                y: position.y - 0.5,
                z: position.z - 0.5,
            },
            max: Point3D {
                x: position.x + 0.5,
                y: position.y + 0.5,
                z: position.z + 0.5,
            },
        };
        
        SpatialEntity {
            id: entity_id,
            name: equipment.name.clone(),
            entity_type: ifc_entity_type,
            position,
            bounding_box,
            coordinate_system: None,
        }
    }

    /// Convert Room to SpatialEntity
    /// 
    /// Generates Universal Path if not present and uses IFCROOM entity type.
    fn convert_room_to_spatial_entity(&self, room: &Room, floor_level: i32) -> SpatialEntity {
        use crate::spatial::{Point3D, BoundingBox3D};
        
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
        
        // Convert position from core::Position to Point3D
        let position = Point3D {
            x: room.spatial_properties.position.x,
            y: room.spatial_properties.position.y,
            z: room.spatial_properties.position.z,
        };
        
        // Convert bounding box from core::BoundingBox to BoundingBox3D
        let bounding_box = BoundingBox3D {
            min: Point3D {
                x: room.spatial_properties.bounding_box.min.x,
                y: room.spatial_properties.bounding_box.min.y,
                z: room.spatial_properties.bounding_box.min.z,
            },
            max: Point3D {
                x: room.spatial_properties.bounding_box.max.x,
                y: room.spatial_properties.bounding_box.max.y,
                z: room.spatial_properties.bounding_box.max.z,
            },
        };
        
        SpatialEntity {
            id: entity_id,
            name: room.name.clone(),
            entity_type,
            position,
            bounding_box,
            coordinate_system: None,
        }
    }
}

#[cfg(test)]
mod tests {
    use crate::spatial::Point3D;
    use super::*;
    use crate::yaml::{BuildingInfo, BuildingMetadata, CoordinateSystemInfo};
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
            floors: vec![{
                use crate::core::{Floor, Wing, Room, Equipment, RoomType, EquipmentType, EquipmentStatus, Position, Dimensions, SpatialProperties, BoundingBox};
                let position = Position {
                    x: 5.0,
                    y: 5.0,
                    z: 1.5,
                    coordinate_system: "building_local".to_string(),
                };
                let dimensions = Dimensions {
                    width: 10.0,
                    height: 3.0,
                    depth: 5.0,
                };
                let bounding_box = BoundingBox {
                    min: Position {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                        coordinate_system: "building_local".to_string(),
                    },
                    max: Position {
                        x: 10.0,
                        y: 5.0,
                        z: 3.0,
                        coordinate_system: "building_local".to_string(),
                    },
                };
                let spatial_properties = SpatialProperties {
                    position,
                    dimensions,
                    bounding_box,
                    coordinate_system: "building_local".to_string(),
                };
                let room = Room {
                    id: "room-101".to_string(),
                    name: "Room 101".to_string(),
                    room_type: RoomType::Office,
                    equipment: vec![],
                    spatial_properties,
                    properties: HashMap::new(),
                    created_at: None,
                    updated_at: None,
                };
                let mut wing = Wing::new("Default".to_string());
                wing.rooms.push(room);
                Floor {
                    id: "floor-1".to_string(),
                    name: "Floor 1".to_string(),
                    level: 1,
                    elevation: Some(0.0),
                    bounding_box: None,
                    wings: vec![wing],
                    equipment: vec![Equipment {
                        id: "equipment-1".to_string(),
                        name: "HVAC Unit 1".to_string(),
                        path: "building/floor-1/room-101/equipment-hvac-1".to_string(),
                        address: None,
                        equipment_type: EquipmentType::HVAC,
                        position: Position {
                            x: 2.0,
                            y: 2.0,
                            z: 2.0,
                            coordinate_system: "building_local".to_string(),
                        },
                        properties: HashMap::new(),
                        status: EquipmentStatus::Active,
                        health_status: None,
                        room_id: None,
                        sensor_mappings: None,
                    }],
                    properties: HashMap::new(),
                }
            }],
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
        assert_eq!(entity.position.x, equipment.position.x);
        assert_eq!(entity.position.y, equipment.position.y);
        assert_eq!(entity.position.z, equipment.position.z);
    }

    #[test]
    fn test_convert_room_to_spatial_entity() {
        let building_data = create_test_building_data();
        let exporter = IFCExporter::new(building_data);
        
        let room = &exporter.building_data.floors[0].wings[0].rooms[0];
        let entity = exporter.convert_room_to_spatial_entity(room, 1);
        
        assert_eq!(entity.id, "building/floor-1/room-101");
        assert_eq!(entity.name, "Room 101");
        assert_eq!(entity.entity_type, "IFCROOM");
        assert_eq!(entity.position.x, room.spatial_properties.position.x);
        assert_eq!(entity.position.y, room.spatial_properties.position.y);
        assert_eq!(entity.position.z, room.spatial_properties.position.z);
    }

    #[test]
    fn test_convert_equipment_without_universal_path() {
        let mut building_data = create_test_building_data();
        building_data.floors[0].equipment[0].path = String::new();
        
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
        building_data.floors[0].wings[0].rooms[0].properties.insert(
            "universal_path".to_string(),
            "custom/path/room-101".to_string()
        );
        
        let exporter = IFCExporter::new(building_data);
        let room = &exporter.building_data.floors[0].wings[0].rooms[0];
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

