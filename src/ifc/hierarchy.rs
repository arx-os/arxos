// IFC hierarchy building for ArxOS
// This module extracts and builds the building hierarchy (Building → Floor → Room → Equipment)

use crate::core::{Building, Floor, Wing, Room, Equipment, RoomType, EquipmentType, Position, SpatialProperties, Dimensions, BoundingBox};
use std::collections::HashMap;
use chrono::Utc;

/// IFC entity structure for hierarchy building
/// This matches the structure from src/ifc/fallback.rs
#[derive(Debug, Clone)]
pub struct IFCEntity {
    pub id: String,
    pub entity_type: String,
    pub name: String,
    pub definition: String,
}

/// Hierarchy builder for IFC entities
pub struct HierarchyBuilder {
    entities: Vec<IFCEntity>,
}

impl HierarchyBuilder {
    pub fn new(entities: Vec<IFCEntity>) -> Self {
        Self { entities }
    }
    
    /// Extract all IFCBUILDINGSTOREY entities as Floor objects
    pub fn extract_floors(&self) -> Result<Vec<Floor>, Box<dyn std::error::Error>> {
        let storey_entities: Vec<&IFCEntity> = self.entities
            .iter()
            .filter(|e| self.is_storey_entity(&e.entity_type))
            .collect();
        
        let mut floors = Vec::new();
        for storey in storey_entities {
            let floor = Floor {
                id: storey.id.clone(),
                name: self.extract_storey_name(storey)?,
                level: self.extract_storey_level(storey)?,
                wings: Vec::new(),
                equipment: Vec::new(),
                properties: HashMap::new(),
            };
            floors.push(floor);
        }
        
        Ok(floors)
    }
    
    /// Extract all IFCSPACE entities as Room objects
    pub fn extract_rooms(&self) -> Result<Vec<Room>, Box<dyn std::error::Error>> {
        let space_entities: Vec<&IFCEntity> = self.entities
            .iter()
            .filter(|e| self.is_space_entity(&e.entity_type))
            .collect();
        
        let mut rooms = Vec::new();
        for space in space_entities {
            let room = Room {
                id: space.id.clone(),
                name: self.extract_space_name(space)?,
                room_type: self.extract_space_type(space)?,
                equipment: Vec::new(),
                spatial_properties: SpatialProperties {
                    position: Position {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                        coordinate_system: "building_local".to_string(),
                    },
                    dimensions: Dimensions {
                        width: 10.0,
                        height: 3.0,
                        depth: 8.0,
                    },
                    bounding_box: BoundingBox {
                        min: Position {
                            x: 0.0,
                            y: 0.0,
                            z: 0.0,
                            coordinate_system: "building_local".to_string(),
                        },
                        max: Position {
                            x: 10.0,
                            y: 8.0,
                            z: 3.0,
                            coordinate_system: "building_local".to_string(),
                        },
                    },
                    coordinate_system: "building_local".to_string(),
                },
                properties: HashMap::new(),
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            rooms.push(room);
        }
        
        Ok(rooms)
    }
    
    /// Extract equipment entities and assign to rooms based on spatial proximity
    pub fn extract_equipment(&self, _rooms: &[Room]) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
        let equipment_entities: Vec<&IFCEntity> = self.entities
            .iter()
            .filter(|e| self.is_equipment_entity(&e.entity_type))
            .collect();
        
        let mut equipment_list = Vec::new();
        for eq in equipment_entities {
            let equipment = Equipment {
                id: eq.id.clone(),
                name: eq.name.clone(),
                path: format!("/equipment/{}", eq.name.to_lowercase().replace(" ", "-")),
                equipment_type: self.extract_equipment_type(&eq.entity_type)?,
                position: Position {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                    coordinate_system: "building_local".to_string(),
                },
                properties: HashMap::new(),
                status: crate::core::EquipmentStatus::Active,
                room_id: None, // Will be assigned based on spatial data
            };
            equipment_list.push(equipment);
        }
        
        Ok(equipment_list)
    }
    
    /// Build complete hierarchy: Building → Floor → Room → Equipment
    pub fn build_hierarchy(&self, building_name: String) -> Result<Building, Box<dyn std::error::Error>> {
        let mut floors = self.extract_floors()?;
        let rooms = self.extract_rooms()?;
        let equipment_list = self.extract_equipment(&rooms)?;
        
        // Assign rooms and equipment to floors
        // Create a default wing for each floor to hold rooms
        for floor in &mut floors {
            // Create a default wing if the floor has no wings
            if floor.wings.is_empty() {
                floor.wings.push(Wing {
                    id: format!("wing-{}", floor.level),
                    name: "Default".to_string(),
                    rooms: Vec::new(),
                    equipment: Vec::new(),
                    properties: HashMap::new(),
                });
            }
        }
        
        // Assign rooms to appropriate floor/wing
        for room in rooms {
            let floor_index = self.find_floor_for_room(&room.id, &floors);
            if floor_index < floors.len() && !floors[floor_index].wings.is_empty() {
                // Add room to the first (default) wing
                floors[floor_index].wings[0].rooms.push(room);
            }
        }
        
        // Assign equipment to appropriate floor
        for equipment in equipment_list {
            let assigned = self.assign_equipment_to_floor(&equipment, &mut floors);
            if !assigned {
                // If not assigned to a room, assign to first floor's equipment list
                if !floors.is_empty() {
                    floors[0].equipment.push(equipment);
                }
            }
        }
        
        // Build the hierarchy
        let mut building = Building::new(
            building_name.clone(),
            format!("/building/{}", building_name.to_lowercase()),
        );
        
        // Add floors with populated rooms and equipment
        for floor in floors {
            building.add_floor(floor);
        }
        
        Ok(building)
    }
    
    /// Find appropriate floor for a room based on ID pattern
    fn find_floor_for_room(&self, room_id: &str, floors: &[Floor]) -> usize {
        // Try to match room ID pattern with floor
        // This is a simple heuristic - can be enhanced with actual IFC reference parsing
        for (index, floor) in floors.iter().enumerate() {
            let room_prefix = if room_id.len() >= 3 { &room_id[..3] } else { room_id };
            if floor.id.contains(room_prefix) || 
               room_id.contains(&floor.id) {
                return index;
            }
        }
        0 // Default to first floor
    }
    
    /// Assign equipment to appropriate floor based on room
    fn assign_equipment_to_floor(&self, equipment: &Equipment, floors: &mut [Floor]) -> bool {
        if let Some(ref room_id) = equipment.room_id {
            for floor in floors.iter_mut() {
                // Search for room in all wings
                for wing in &mut floor.wings {
                    if wing.rooms.iter().any(|r| r.id == *room_id) {
                        // Add to wing's equipment
                        wing.equipment.push(equipment.clone());
                        return true;
                    }
                }
            }
        }
        false
    }
    
    /// Helper: Check if entity is a storey (floor)
    fn is_storey_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type.to_uppercase().as_str(),
            "IFCBUILDINGSTOREY" | "IFCBUILDINGFLOOR" | "IFCLEVEL"
        )
    }
    
    /// Helper: Check if entity is a space (room)
    fn is_space_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type.to_uppercase().as_str(),
            "IFCSPACE" | "IFCROOM" | "IFCZONE"
        )
    }
    
    /// Helper: Check if entity is equipment
    fn is_equipment_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type.to_uppercase().as_str(),
            "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" | "IFCLIGHTFIXTURE" |
            "IFCDISTRIBUTIONELEMENT" | "IFCFAN" | "IFCPUMP"
        )
    }
    
    /// Extract storey name from IFC entity
    fn extract_storey_name(&self, storey: &IFCEntity) -> Result<String, Box<dyn std::error::Error>> {
        if !storey.name.is_empty() && storey.name != "Unknown" {
            Ok(storey.name.clone())
        } else {
            Ok(format!("Floor-{}", storey.id))
        }
    }
    
    /// Extract storey level from IFC entity
    fn extract_storey_level(&self, storey: &IFCEntity) -> Result<i32, Box<dyn std::error::Error>> {
        // Try to parse level from storey name (e.g., "First Floor" -> 1, "Floor 2" -> 2)
        let name_lower = storey.name.to_lowercase();
        if name_lower.contains("first") || name_lower.contains("1") || name_lower.contains("ground") {
            Ok(1)
        } else if name_lower.contains("second") || name_lower.contains("2") {
            Ok(2)
        } else if name_lower.contains("third") || name_lower.contains("3") {
            Ok(3)
        } else {
            // Extract any number from the name
            let numbers: Vec<i32> = storey.name
                .chars()
                .filter(|c| c.is_ascii_digit())
                .filter_map(|c| c.to_digit(10).map(|d| d as i32))
                .collect();
            if !numbers.is_empty() {
                Ok(numbers[0])
            } else {
                Ok(1) // Default to first floor
            }
        }
    }
    
    /// Extract space name from IFC entity
    fn extract_space_name(&self, space: &IFCEntity) -> Result<String, Box<dyn std::error::Error>> {
        if !space.name.is_empty() && space.name != "Unknown" {
            Ok(space.name.clone())
        } else {
            Ok(format!("Space-{}", space.id))
        }
    }
    
    /// Extract space type from IFC entity
    fn extract_space_type(&self, _space: &IFCEntity) -> Result<RoomType, Box<dyn std::error::Error>> {
        // Currently defaults to Office - can be enhanced to parse actual room type from IFC properties
        // This is a reasonable default as most building spaces are office-type
        Ok(RoomType::Office)
    }
    
    /// Map IFC equipment type to ArxOS EquipmentType
    fn extract_equipment_type(&self, ifc_entity_type: &str) -> Result<EquipmentType, Box<dyn std::error::Error>> {
        match ifc_entity_type.to_uppercase().as_str() {
            "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" | "IFCFAN" | "IFCPUMP" => {
                Ok(EquipmentType::HVAC)
            }
            "IFCLIGHTFIXTURE" | "IFCDISTRIBUTIONELEMENT" | "IFCSWITCHINGDEVICE" => {
                Ok(EquipmentType::Electrical)
            }
            "IFCFIREALARM" | "IFCFIREDETECTOR" => {
                Ok(EquipmentType::Safety)
            }
            "IFCPIPE" | "IFCPIPEFITTING" | "IFCTANK" => {
                Ok(EquipmentType::Plumbing)
            }
            _ => Ok(EquipmentType::Other(ifc_entity_type.to_string())),
        }
    }
}

