// IFC hierarchy building for ArxOS
// This module extracts and builds the building hierarchy (Building → Floor → Room → Equipment)

use crate::core::{Building, Floor, Wing, Room, Equipment, RoomType, EquipmentType, Position, SpatialProperties, Dimensions, BoundingBox};
use std::collections::HashMap;
use chrono::Utc;
use regex::Regex;

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
    entity_map: HashMap<String, IFCEntity>, // Map entity IDs to entities for reference resolution
}

impl HierarchyBuilder {
    pub fn new(entities: Vec<IFCEntity>) -> Self {
        let entity_map: HashMap<String, IFCEntity> = entities.iter()
            .map(|e| (e.id.clone(), e.clone()))
            .collect();
        Self { 
            entities,
            entity_map,
        }
    }
    
    /// Extract coordinates from IFC placement chain
    /// Follows: IFCSPACE -> IFCLOCALPLACEMENT -> IFCAXIS2PLACEMENT3D -> IFCCARTESIANPOINT
    fn extract_coordinates_from_placement(&self, placement_ref: &str) -> Option<(f64, f64, f64)> {
        // Remove # prefix if present
        let ref_id = placement_ref.trim_start_matches('#').to_string();
        
        // Find the placement entity
        let placement_entity = self.entity_map.get(&ref_id)?;
        
        // Parse IFCLOCALPLACEMENT(#parent,#relative_placement)
        // We need the relative_placement (#21 in example)
        if placement_entity.entity_type == "IFCLOCALPLACEMENT" {
            // Extract relative placement reference from definition
            // Format: IFCLOCALPLACEMENT(#16,#21)
            if let Some(relative_ref) = self.extract_second_reference(&placement_entity.definition) {
                return self.extract_coordinates_from_axis_placement(&relative_ref);
            }
        }
        
        None
    }
    
    /// Extract coordinates from IFCAXIS2PLACEMENT3D
    /// Format: IFCAXIS2PLACEMENT3D(#location,#axis,#ref_dir)
    fn extract_coordinates_from_axis_placement(&self, axis_ref: &str) -> Option<(f64, f64, f64)> {
        let ref_id = axis_ref.trim_start_matches('#').to_string();
        let axis_entity = self.entity_map.get(&ref_id)?;
        
        if axis_entity.entity_type == "IFCAXIS2PLACEMENT3D" {
            // Extract location reference (first parameter)
            // Format: IFCAXIS2PLACEMENT3D(#22,#6,#7)
            if let Some(location_ref) = self.extract_first_reference(&axis_entity.definition) {
                return self.extract_coordinates_from_point(&location_ref);
            }
        }
        
        None
    }
    
    /// Extract coordinates from IFCCARTESIANPOINT
    /// Format: IFCCARTESIANPOINT((x,y,z))
    fn extract_coordinates_from_point(&self, point_ref: &str) -> Option<(f64, f64, f64)> {
        let ref_id = point_ref.trim_start_matches('#').to_string();
        let point_entity = self.entity_map.get(&ref_id)?;
        
        if point_entity.entity_type == "IFCCARTESIANPOINT" {
            // Parse coordinates from definition
            // Format: IFCCARTESIANPOINT((5.,5.,0.))
            if let Some(coords) = self.parse_cartesian_point(&point_entity.definition) {
                return Some(coords);
            }
        }
        
        None
    }
    
    /// Extract first reference from entity definition
    /// Format: IFCAXIS2PLACEMENT3D(#22,#6,#7) -> #22
    fn extract_first_reference(&self, definition: &str) -> Option<String> {
        if let Some(start) = definition.find("(#") {
            if let Some(end) = definition[start+2..].find(',') {
                let ref_str = &definition[start+1..start+2+end];
                return Some(ref_str.to_string());
            } else if let Some(end) = definition[start+2..].find(')') {
                let ref_str = &definition[start+1..start+2+end];
                return Some(ref_str.to_string());
            }
        }
        None
    }
    
    /// Extract second reference from entity definition
    /// Format: IFCLOCALPLACEMENT(#16,#21) -> #21
    fn extract_second_reference(&self, definition: &str) -> Option<String> {
        if let Some(first_comma) = definition.find(',') {
            if let Some(start) = definition[first_comma..].find("#") {
                let ref_start = first_comma + start;
                if let Some(end) = definition[ref_start+1..].find(|c| c == ',' || c == ')') {
                    let ref_str = &definition[ref_start..ref_start+1+end];
                    return Some(ref_str.to_string());
                }
            }
        }
        None
    }
    
    /// Extract nested reference from entity definition with nested parentheses
    /// Format: IFCPRODUCTDEFINITIONSHAPE($,$,(#172)) -> #172
    fn extract_nested_reference(&self, definition: &str) -> Option<String> {
        // Find the nested parentheses group (need to look inside outermost parens)
        // Format: IFCPRODUCTDEFINITIONSHAPE($,$,(#172))
        // Need to find the innermost (#ref) group
        
        // First find the outermost opening paren
        if let Some(out_start) = definition.find('(') {
            // From there, find matching closing parens
            let mut depth = 1;
            let mut pos = out_start + 1;
            let mut inner_start = None;
            
            while pos < definition.len() && depth > 0 {
                match definition.chars().nth(pos) {
                    Some('(') => {
                        if inner_start.is_none() {
                            inner_start = Some(pos + 1);
                        }
                        depth += 1;
                    }
                    Some(')') => {
                        depth -= 1;
                        if depth == 0 {
                            if let Some(start) = inner_start {
                                let nested_content = &definition[start..pos];
                                // Look for #reference in nested content
                                if let Some(ref_start) = nested_content.find('#') {
                                    // Find the end of the reference
                                    for i in (ref_start+1)..nested_content.len() {
                                        if nested_content.chars().nth(i).map_or(false, |c| c == ',' || c == ')') {
                                            let ref_str = &nested_content[ref_start..i];
                                            return Some(ref_str.to_string());
                                        }
                                    }
                                }
                            }
                        }
                    }
                    _ => {}
                }
                pos += 1;
            }
        }
        None
    }
    
    /// Parse coordinates from IFCCARTESIANPOINT definition
    /// Format: IFCCARTESIANPOINT((5.,5.,0.)) -> (5.0, 5.0, 0.0)
    fn parse_cartesian_point(&self, definition: &str) -> Option<(f64, f64, f64)> {
        // Look for double parentheses: ((x,y,z))
        if let Some(start) = definition.find("((") {
            if let Some(end) = definition[start+2..].find("))") {
                let coords_str = &definition[start+2..start+2+end];
                let coords: Vec<&str> = coords_str.split(',').collect();
                if coords.len() >= 3 {
                    let x = coords[0].trim().parse::<f64>().ok()?;
                    let y = coords[1].trim().parse::<f64>().ok()?;
                    let z = coords[2].trim().parse::<f64>().ok()?;
                    return Some((x, y, z));
                }
            }
        }
        None
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
            // Extract placement reference from IFCSPACE definition
            // Format: IFCSPACE('Conference Room',$,#8,$,#20,$,$,.ELEMENT.,0.)
            // The placement is typically the 5th parameter (#20)
            let (x, y, z) = self.extract_space_coordinates(space).unwrap_or((0.0, 0.0, 0.0));
            
            // Try to extract geometry polygon from IFCSPACE
            let mut properties = HashMap::new();
            if let Some(polygon_str) = self.extract_space_geometry_polygon(space) {
                properties.insert("floor_polygon".to_string(), polygon_str);
            }
            
            // Use actual coordinates for position
            // Default dimensions if not available from IFC
            let width = 10.0;
            let depth = 8.0;
            let height = 3.0;
            
            let room = Room {
                id: space.id.clone(),
                name: self.extract_space_name(space)?,
                room_type: self.extract_space_type(space)?,
                equipment: Vec::new(),
                spatial_properties: SpatialProperties {
                    position: Position {
                        x,
                        y,
                        z,
                        coordinate_system: "building_local".to_string(),
                    },
                    dimensions: Dimensions {
                        width,
                        height,
                        depth,
                    },
                    bounding_box: BoundingBox {
                        min: Position {
                            x: x - width / 2.0,
                            y: y - depth / 2.0,
                            z,
                            coordinate_system: "building_local".to_string(),
                        },
                        max: Position {
                            x: x + width / 2.0,
                            y: y + depth / 2.0,
                            z: z + height,
                            coordinate_system: "building_local".to_string(),
                        },
                    },
                    coordinate_system: "building_local".to_string(),
                },
                properties,
                created_at: Utc::now(),
                updated_at: Utc::now(),
            };
            rooms.push(room);
        }
        
        Ok(rooms)
    }
    
    /// Extract coordinates from IFCSPACE placement chain
    fn extract_space_coordinates(&self, space: &IFCEntity) -> Option<(f64, f64, f64)> {
        // Parse IFCSPACE definition to find placement reference
        // Format: IFCSPACE('name',$,#building,$,#placement,$,$,.ELEMENT.,0.)
        // Placement is typically parameter 5 (0-indexed: 4)
        let params: Vec<&str> = space.definition.split(',').collect();
        
        // Look for placement reference (starts with #)
        for param in params {
            let param = param.trim();
            if param.starts_with("#") {
                // This is likely the placement reference
                if let Some(coords) = self.extract_coordinates_from_placement(param) {
                    return Some(coords);
                }
            }
        }
        
        None
    }
    
    /// Extract geometry polygon from IFCSPACE shape representation
    /// Follows: IFCSPACE -> IFCPRODUCTDEFINITIONSHAPE -> IFCSHAPEREPRESENTATION -> IFCEXTRUDEDAREASOLID -> IFCPOLYLINE
    fn extract_space_geometry_polygon(&self, space: &IFCEntity) -> Option<String> {
        // Parse IFCSPACE definition to find representation reference using regex
        // Format: IFCSPACE('name',$,#building,$,#placement,#representation,$,.ELEMENT.,0.)
        // Use regex to find all #number references
        let re = Regex::new(r"#(\d+)").ok()?;
        let refs: Vec<&str> = re.find_iter(&space.definition)
            .map(|m| m.as_str())
            .collect();
        
        log::debug!("Space {}: Found {} references: {:?}", space.id, refs.len(), refs);
        
        // Representation is the 3rd reference (#1 = building, #98 = placement, #173 = representation)
        if refs.len() >= 3 {
            log::debug!("Extracting polygon from representation reference: {}", refs[2]);
            return self.extract_polygon_from_representation(refs[2]);
        }
        
        log::debug!("Not enough references for geometry extraction");
        None
    }
    
    /// Extract polygon points from representation reference chain
    fn extract_polygon_from_representation(&self, repr_ref: &str) -> Option<String> {
        // Follow chain: #representation -> IFCPRODUCTDEFINITIONSHAPE -> IFCSHAPEREPRESENTATION -> IFCEXTRUDEDAREASOLID -> IFCARBITRARYCLOSEDPROFILEDEF -> IFCPOLYLINE
        let ref_id = repr_ref.trim_start_matches('#').to_string();
        
        // Get IFCPRODUCTDEFINITIONSHAPE
        let product_def = self.entity_map.get(&ref_id)?;
        if !product_def.definition.contains("IFCPRODUCTDEFINITIONSHAPE") {
            log::debug!("Entity {} is not IFCPRODUCTDEFINITIONSHAPE: {}", ref_id, product_def.definition);
            return None;
        }
        
        log::debug!("Got IFCPRODUCTDEFINITIONSHAPE #{}", ref_id);
        
        // Find the IFCSHAPEREPRESENTATION reference (inside the product def shape definition)
        // IFCPRODUCTDEFINITIONSHAPE($,$,(#172)) - reference is in nested parens
        let shape_ref = self.extract_nested_reference(&product_def.definition)?;
        let shape_id = shape_ref.trim_start_matches('#');
        let shape_repr = self.entity_map.get(shape_id)?;
        if !shape_repr.definition.contains("IFCSHAPEREPRESENTATION") {
            log::debug!("Entity #{} is not IFCSHAPEREPRESENTATION: {}", shape_id, shape_repr.definition);
            return None;
        }
        
        log::debug!("Got IFCSHAPEREPRESENTATION #{}", shape_id);
        
        // Find the IFCEXTRUDEDAREASOLID reference
        let extruded_ref = self.extract_second_reference(&shape_repr.definition)?;
        let extruded_id = extruded_ref.trim_start_matches('#');
        let extruded = self.entity_map.get(extruded_id)?;
        if !extruded.definition.contains("IFCEXTRUDEDAREASOLID") {
            log::debug!("Entity #{} is not IFCEXTRUDEDAREASOLID: {}", extruded_id, extruded.definition);
            return None;
        }
        
        log::debug!("Got IFCEXTRUDEDAREASOLID #{}", extruded_id);
        
        // Find the IFCARBITRARYCLOSEDPROFILEDEF reference (first parameter of IFCEXTRUDEDAREASOLID)
        let profile_ref = self.extract_first_reference(&extruded.definition)?;
        let profile_id = profile_ref.trim_start_matches('#');
        let profile = self.entity_map.get(profile_id)?;
        if !profile.definition.contains("IFCARBITRARYCLOSEDPROFILEDEF") {
            log::debug!("Entity #{} is not IFCARBITRARYCLOSEDPROFILEDEF: {}", profile_id, profile.definition);
            return None;
        }
        
        log::debug!("Got IFCARBITRARYCLOSEDPROFILEDEF #{}", profile_id);
        
        // Find the IFCPOLYLINE reference (second parameter of IFCARBITRARYCLOSEDPROFILEDEF)
        let polyline_ref = self.extract_second_reference(&profile.definition)?;
        let polyline_id = polyline_ref.trim_start_matches('#');
        let polyline = self.entity_map.get(polyline_id)?;
        if !polyline.definition.contains("IFCPOLYLINE") {
            log::debug!("Entity #{} is not IFCPOLYLINE: {}", polyline_id, polyline.definition);
            return None;
        }
        
        log::debug!("Got IFCPOLYLINE #{}", polyline_id);
        
        // Extract all IFCCARTESIANPOINT references from IFCPOLYLINE
        // Format: IFCPOLYLINE((#160,#161,#162,#163,#164,#165,#166,#167))
        let polyline_params = self.extract_reference_list(&polyline.definition)?;
        
        log::debug!("Extracted {} point references from IFCPOLYLINE", polyline_params.len());
        
        // Convert each point reference to coordinates and build the polygon string
        let mut points = Vec::new();
        for point_ref in polyline_params {
            let point_id = point_ref.trim_start_matches('#');
            log::debug!("Looking up point entity #{}", point_id);
            if let Some(point_entity) = self.entity_map.get(point_id) {
                log::debug!("Found point entity #{}: {}", point_id, point_entity.definition);
                if let Some((x, y, _z)) = self.parse_cartesian_point_2d(&point_entity.definition) {
                    log::debug!("Parsed coordinates: ({}, {})", x, y);
                    points.push(format!("{},{}", x, y));
                } else {
                    log::debug!("Failed to parse coordinates from: {}", point_entity.definition);
                }
            } else {
                log::debug!("Point entity #{} not found in entity_map", point_id);
            }
        }
        
        log::debug!("Extracted {} polygon points", points.len());
        
        if points.is_empty() {
            return None;
        }
        
        Some(points.join(";"))
    }
    
    /// Extract a list of references from a parameter group like (#160,#161,#162)
    fn extract_reference_list(&self, definition: &str) -> Option<Vec<String>> {
        // Look for pattern: (#REF1,#REF2,#REF3)
        let start = definition.find("((")?;
        let end = definition[start..].find("))")?;
        let params_str = &definition[start + 2..start + end];  // Skip the "((" part
        
        log::debug!("extract_reference_list: params_str = '{}'", params_str);
        
        // Use regex to extract all #number references
        let re = Regex::new(r"#\d+").ok()?;
        let references: Vec<String> = re.find_iter(params_str)
            .map(|m| m.as_str().to_string())
            .collect();
        
        log::debug!("extract_reference_list: extracted {} references", references.len());
        Some(references)
    }
    
    /// Parse a 2D IFCCARTESIANPOINT definition: IFCCARTESIANPOINT((x,y)) or IFCCARTESIANPOINT((x,y,z))
    fn parse_cartesian_point_2d(&self, definition: &str) -> Option<(f64, f64, f64)> {
        // Look for pattern: IFCCARTESIANPOINT((x,y,z)) or IFCCARTESIANPOINT((x,y))
        let start = definition.find("((")?;
        let end = definition[start..].find("))")?;
        let coords_str = &definition[start + 2..start + end];  // Skip both opening parens
        
        log::debug!("parse_cartesian_point_2d: coords_str = '{}'", coords_str);
        
        let coords: Vec<&str> = coords_str.split(',').collect();
        if coords.len() >= 2 {
            if let (Ok(x), Ok(y)) = (coords[0].trim().parse::<f64>(), coords[1].trim().parse::<f64>()) {
                let z = if coords.len() >= 3 { coords[2].trim().parse::<f64>().unwrap_or(0.0) } else { 0.0 };
                return Some((x, y, z));
            }
        }
        
        None
    }
    
    /// Extract equipment entities and assign to rooms based on spatial proximity
    pub fn extract_equipment(&self, _rooms: &[Room]) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
        let equipment_entities: Vec<&IFCEntity> = self.entities
            .iter()
            .filter(|e| self.is_equipment_entity(&e.entity_type))
            .filter(|e| !e.entity_type.contains("TYPE")) // Filter out TYPE definitions (IFCAIRTERMINALTYPE, etc.)
            .collect();
        
        let mut equipment_list = Vec::new();
        for eq in equipment_entities {
            // Extract actual coordinates from placement chain
            let (x, y, z) = self.extract_equipment_coordinates(eq).unwrap_or((0.0, 0.0, 0.0));
            
            let equipment = Equipment {
                id: eq.id.clone(),
                name: eq.name.clone(),
                path: format!("/equipment/{}", eq.name.to_lowercase().replace(" ", "-")),
                equipment_type: self.extract_equipment_type(&eq.entity_type)?,
                position: Position {
                    x,
                    y,
                    z,
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
    
    /// Extract coordinates from equipment placement chain
    fn extract_equipment_coordinates(&self, equipment: &IFCEntity) -> Option<(f64, f64, f64)> {
        // Parse IFCFLOWTERMINAL definition to find placement reference
        // Format: IFCFLOWTERMINAL('name',$,#building,$,#placement,$,$,.ELEMENT.,$)
        let params: Vec<&str> = equipment.definition.split(',').collect();
        
        // Look for placement reference
        for param in params {
            let param = param.trim();
            if param.starts_with("#") {
                if let Some(coords) = self.extract_coordinates_from_placement(param) {
                    return Some(coords);
                }
            }
        }
        
        None
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
    
    /// Helper: Check if entity is equipment (excludes TYPE definitions)
    fn is_equipment_entity(&self, entity_type: &str) -> bool {
        let entity_upper = entity_type.to_uppercase();
        // Exclude TYPE definitions
        if entity_upper.contains("TYPE") {
            return false;
        }
        matches!(entity_upper.as_str(),
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

