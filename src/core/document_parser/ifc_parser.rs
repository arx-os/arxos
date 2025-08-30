//! IFC (Industry Foundation Classes) Parser
//! 
//! Extracts building information from BIM models

use super::{BuildingPlan, FloorPlan, Room, Equipment, EquipmentType, ParseError, Point3D, BoundingBox};
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use log::{debug, info};

/// IFC parser for BIM models
pub struct IfcParser {
    /// Entity definitions from IFC file
    entities: HashMap<u32, IfcEntity>,
    /// Spatial structure
    spatial_tree: SpatialStructure,
}

/// IFC entity representation
#[derive(Debug, Clone)]
struct IfcEntity {
    id: u32,
    entity_type: String,
    attributes: Vec<String>,
    properties: HashMap<String, String>,
}

/// Spatial structure of the building
#[derive(Debug, Default)]
struct SpatialStructure {
    site: Option<u32>,
    building: Option<u32>,
    stories: Vec<u32>,
    spaces: HashMap<u32, Vec<u32>>,  // Story -> Spaces
}

impl IfcParser {
    /// Create new IFC parser
    pub fn new() -> Self {
        Self {
            entities: HashMap::new(),
            spatial_tree: SpatialStructure::default(),
        }
    }
    
    /// Parse IFC file
    pub async fn parse(&mut self, file_path: &str) -> Result<BuildingPlan, ParseError> {
        info!("Parsing IFC file: {}", file_path);
        
        // Read and parse IFC file
        self.read_ifc_file(file_path)?;
        
        // Build spatial structure
        self.build_spatial_structure()?;
        
        // Extract building information
        let building_name = self.get_building_name();
        let floors = self.extract_floors()?;
        let arxobjects = Vec::new();  // Will be converted later
        let metadata = self.extract_metadata();
        
        Ok(BuildingPlan {
            name: building_name,
            floors,
            arxobjects,
            metadata,
        })
    }
    
    /// Read IFC file and parse entities
    fn read_ifc_file(&mut self, file_path: &str) -> Result<(), ParseError> {
        let file = File::open(file_path)?;
        let reader = BufReader::new(file);
        
        for line in reader.lines() {
            let line = line?;
            
            // Skip comments and empty lines
            if line.starts_with("/*") || line.trim().is_empty() {
                continue;
            }
            
            // Parse entity lines (format: #123=IFCWALL(...);)
            if line.starts_with('#') {
                self.parse_entity_line(&line)?;
            }
        }
        
        debug!("Parsed {} IFC entities", self.entities.len());
        Ok(())
    }
    
    /// Parse single IFC entity line
    fn parse_entity_line(&mut self, line: &str) -> Result<(), ParseError> {
        // Extract entity ID
        let id_end = line.find('=').ok_or_else(|| ParseError::IfcError("Invalid entity format".to_string()))?;
        let id_str = &line[1..id_end];
        let id: u32 = id_str.parse()
            .map_err(|_| ParseError::IfcError("Invalid entity ID".to_string()))?;
        
        // Extract entity type
        let type_start = id_end + 1;
        let type_end = line[type_start..].find('(')
            .map(|i| type_start + i)
            .ok_or_else(|| ParseError::IfcError("Invalid entity type".to_string()))?;
        let entity_type = line[type_start..type_end].to_string();
        
        // Extract attributes
        let attr_start = type_end + 1;
        let attr_end = line.rfind(')').ok_or_else(|| ParseError::IfcError("Invalid attributes".to_string()))?;
        let attr_str = &line[attr_start..attr_end];
        let attributes = self.parse_attributes(attr_str);
        
        // Create entity
        let entity = IfcEntity {
            id,
            entity_type,
            attributes,
            properties: HashMap::new(),
        };
        
        self.entities.insert(id, entity);
        Ok(())
    }
    
    /// Parse IFC attributes
    fn parse_attributes(&self, attr_str: &str) -> Vec<String> {
        // Simplified attribute parsing
        // Real implementation would handle nested structures, lists, etc.
        attr_str.split(',')
            .map(|s| s.trim().trim_matches('\'').to_string())
            .collect()
    }
    
    /// Build spatial structure from entities
    fn build_spatial_structure(&mut self) -> Result<(), ParseError> {
        // Find site
        for (id, entity) in &self.entities {
            match entity.entity_type.as_str() {
                "IFCSITE" => {
                    self.spatial_tree.site = Some(*id);
                }
                "IFCBUILDING" => {
                    self.spatial_tree.building = Some(*id);
                }
                "IFCBUILDINGSTOREY" => {
                    self.spatial_tree.stories.push(*id);
                }
                "IFCSPACE" => {
                    // Find which story this space belongs to
                    // This would require parsing relationships
                    // For now, add to first story
                    if let Some(story) = self.spatial_tree.stories.first() {
                        self.spatial_tree.spaces.entry(*story)
                            .or_insert_with(Vec::new)
                            .push(*id);
                    }
                }
                _ => {}
            }
        }
        
        Ok(())
    }
    
    /// Get building name
    fn get_building_name(&self) -> String {
        if let Some(building_id) = self.spatial_tree.building {
            if let Some(entity) = self.entities.get(&building_id) {
                // Name is typically the 3rd attribute
                if entity.attributes.len() > 2 {
                    return entity.attributes[2].clone();
                }
            }
        }
        "Unknown Building".to_string()
    }
    
    /// Extract floors from IFC model
    fn extract_floors(&self) -> Result<Vec<FloorPlan>, ParseError> {
        let mut floors = Vec::new();
        
        for (floor_num, story_id) in self.spatial_tree.stories.iter().enumerate() {
            let floor = self.extract_floor(*story_id, floor_num as i8)?;
            floors.push(floor);
        }
        
        Ok(floors)
    }
    
    /// Extract single floor
    fn extract_floor(&self, story_id: u32, floor_number: i8) -> Result<FloorPlan, ParseError> {
        let mut rooms = Vec::new();
        let mut equipment = Vec::new();
        
        // Get spaces on this floor
        if let Some(space_ids) = self.spatial_tree.spaces.get(&story_id) {
            for space_id in space_ids {
                if let Some(space) = self.entities.get(space_id) {
                    let room = self.extract_room(space)?;
                    rooms.push(room);
                }
            }
        }
        
        // Extract equipment on this floor
        equipment.extend(self.extract_floor_equipment(story_id)?);
        
        // Generate ASCII layout
        let ascii_layout = self.generate_floor_ascii(&rooms, &equipment);
        
        Ok(FloorPlan {
            floor_number,
            rooms,
            ascii_layout,
            equipment,
        })
    }
    
    /// Extract room from IFC space
    fn extract_room(&self, space: &IfcEntity) -> Result<Room, ParseError> {
        // Extract room properties from IFC attributes
        let number = if space.attributes.len() > 2 {
            space.attributes[2].clone()
        } else {
            "Unknown".to_string()
        };
        
        let name = if space.attributes.len() > 3 {
            space.attributes[3].clone()
        } else {
            "Room".to_string()
        };
        
        Ok(Room {
            number,
            name,
            area_sqft: 0.0,  // Would calculate from geometry
            bounds: BoundingBox {
                min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                max: Point3D { x: 10.0, y: 10.0, z: 3.0 },
            },
            equipment_count: 0,
        })
    }
    
    /// Extract equipment from floor
    fn extract_floor_equipment(&self, story_id: u32) -> Result<Vec<Equipment>, ParseError> {
        let mut equipment = Vec::new();
        
        // Look for MEP elements
        for (_, entity) in &self.entities {
            let eq_type = match entity.entity_type.as_str() {
                "IFCOUTLET" => Some(EquipmentType::ElectricalOutlet),
                "IFCLIGHTFIXTURE" => Some(EquipmentType::LightFixture),
                "IFCAIRTERMINAL" => Some(EquipmentType::HvacVent),
                "IFCFIRESUPPRESSIONTERMINAL" => Some(EquipmentType::Sprinkler),
                "IFCALARM" => Some(EquipmentType::FireAlarm),
                "IFCSENSOR" => Some(EquipmentType::SmokeDetector),
                "IFCDOOR" => Some(EquipmentType::Door),
                "IFCWINDOW" => Some(EquipmentType::Window),
                _ => None,
            };
            
            if let Some(eq_type) = eq_type {
                // Extract location from placement
                let location = self.extract_location(entity)?;
                
                equipment.push(Equipment {
                    equipment_type: eq_type,
                    location,
                    room_number: None,  // Would determine from spatial containment
                    properties: HashMap::new(),
                });
            }
        }
        
        Ok(equipment)
    }
    
    /// Extract 3D location from entity
    fn extract_location(&self, entity: &IfcEntity) -> Result<Point3D, ParseError> {
        // This would parse the ObjectPlacement attribute
        // For now, return mock location
        Ok(Point3D {
            x: 10.0,
            y: 10.0,
            z: 0.3,
        })
    }
    
    /// Generate ASCII floor plan
    fn generate_floor_ascii(&self, rooms: &[Room], equipment: &[Equipment]) -> String {
        let mut ascii = String::new();
        
        ascii.push_str("╔════════════════════════════════════════╗\n");
        ascii.push_str("║         FLOOR PLAN FROM IFC           ║\n");
        ascii.push_str("╠════════════════════════════════════════╣\n");
        
        // Simple grid representation
        for room in rooms {
            ascii.push_str(&format!("║ Room {}: {} ", room.number, room.name));
            
            // Add equipment symbols for this room
            for eq in equipment {
                if eq.room_number.as_deref() == Some(&room.number) {
                    ascii.push_str(eq.equipment_type.to_ascii_symbol());
                    ascii.push(' ');
                }
            }
            
            ascii.push_str("║\n");
        }
        
        ascii.push_str("╚════════════════════════════════════════╝\n");
        
        ascii
    }
    
    /// Extract building metadata
    fn extract_metadata(&self) -> super::BuildingMetadata {
        super::BuildingMetadata {
            address: None,
            total_sqft: self.calculate_total_area(),
            year_built: None,
            building_type: self.get_building_type(),
            occupancy_class: None,
        }
    }
    
    /// Calculate total building area
    fn calculate_total_area(&self) -> f32 {
        // Sum areas of all spaces
        0.0  // Simplified
    }
    
    /// Get building type from IFC
    fn get_building_type(&self) -> Option<String> {
        // Would extract from IfcBuilding.BuildingType
        None
    }
}