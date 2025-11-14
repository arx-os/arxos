//! Hierarchy builder for IFC entities
//!
//! Main builder implementation for extracting and assembling building hierarchies from IFC files.

use crate::core::{
    BoundingBox, Building, Dimensions, Equipment, Floor, Position, Room,
    SpatialProperties, Wing,
};
use crate::ifc::{
    geometry::{extract_all_references, extract_reference_id, parameters_from_definition},
    identifiers::derive_building_identifiers,
};
use crate::utils::string::slugify;
use chrono::Utc;
use super::{
    helpers::{
        extract_equipment_type, extract_space_name, extract_space_type, extract_storey_level,
        extract_storey_name, is_equipment_entity, is_space_entity, is_storey_entity,
    },
    types::IFCEntity,
    utils::ensure_unique_path,
};
use regex::Regex;
use std::collections::{HashMap, HashSet};

/// Hierarchy builder for IFC entities
pub struct HierarchyBuilder {
    entities: Vec<IFCEntity>,
    entity_map: HashMap<String, IFCEntity>, // Map entity IDs to entities for reference resolution
    aggregates: HashMap<String, Vec<String>>,
    #[allow(dead_code)]
    containment: HashMap<String, Vec<String>>,
    rooms_by_structure: HashMap<String, Vec<String>>,
    #[allow(dead_code)]
    elements_by_structure: HashMap<String, Vec<String>>,
    room_parents: HashMap<String, String>,
    element_parents: HashMap<String, String>,
}

impl HierarchyBuilder {
    pub fn new(entities: Vec<IFCEntity>) -> Self {
        let entity_map: HashMap<String, IFCEntity> =
            entities.iter().map(|e| (e.id.clone(), e.clone())).collect();
        let mut aggregates: HashMap<String, Vec<String>> = HashMap::new();
        let mut containment: HashMap<String, Vec<String>> = HashMap::new();
        let mut rooms_by_structure: HashMap<String, Vec<String>> = HashMap::new();
        let mut elements_by_structure: HashMap<String, Vec<String>> = HashMap::new();
        let mut room_parents: HashMap<String, String> = HashMap::new();
        let mut element_parents: HashMap<String, String> = HashMap::new();

        for entity in &entities {
            match entity.entity_type.as_str() {
                "IFCRELAGGREGATES" => {
                    let params = parameters_from_definition(&entity.definition);
                    if params.len() < 6 {
                        continue;
                    }
                    if let Some(relating) = extract_reference_id(&params[4]) {
                        let related = extract_all_references(&params[5]);
                        if !related.is_empty() {
                            aggregates
                                .entry(relating.clone())
                                .or_default()
                                .extend(related.iter().cloned());

                            for child in related {
                                if let Some(child_entity) = entity_map.get(&child) {
                                    if child_entity.entity_type == "IFCSPACE" {
                                        rooms_by_structure
                                            .entry(relating.clone())
                                            .or_default()
                                            .push(child.clone());
                                        room_parents.insert(child.clone(), relating.clone());
                                    }
                                }
                            }
                        }
                    }
                }
                "IFCRELCONTAINEDINSPATIALSTRUCTURE" => {
                    let params = parameters_from_definition(&entity.definition);
                    if params.len() < 6 {
                        continue;
                    }

                    let relating = match extract_reference_id(&params[4]) {
                        Some(r) => r,
                        None => continue,
                    };
                    let related = extract_all_references(&params[5]);
                    if related.is_empty() {
                        continue;
                    }

                    containment
                        .entry(relating.clone())
                        .or_default()
                        .extend(related.iter().cloned());

                    for child in related {
                        if let Some(child_entity) = entity_map.get(&child) {
                            if child_entity.entity_type == "IFCSPACE" {
                                rooms_by_structure
                                    .entry(relating.clone())
                                    .or_default()
                                    .push(child.clone());
                                room_parents.insert(child.clone(), relating.clone());
                            } else {
                                elements_by_structure
                                    .entry(relating.clone())
                                    .or_default()
                                    .push(child.clone());
                                element_parents.insert(child.clone(), relating.clone());
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        Self {
            entities,
            entity_map,
            aggregates,
            containment,
            rooms_by_structure,
            elements_by_structure,
            room_parents,
            element_parents,
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
            if let Some(relative_ref) = self.extract_second_reference(&placement_entity.definition)
            {
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
            if let Some(end) = definition[start + 2..].find(',') {
                let ref_str = &definition[start + 1..start + 2 + end];
                return Some(ref_str.to_string());
            } else if let Some(end) = definition[start + 2..].find(')') {
                let ref_str = &definition[start + 1..start + 2 + end];
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
                if let Some(end) = definition[ref_start + 1..].find(|c| [',', ')'].contains(&c)) {
                    let ref_str = &definition[ref_start..ref_start + 1 + end];
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
                                    for i in (ref_start + 1)..nested_content.len() {
                                        if nested_content
                                            .chars()
                                            .nth(i)
                                            .is_some_and(|c| c == ',' || c == ')')
                                        {
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
            if let Some(end) = definition[start + 2..].find("))") {
                let coords_str = &definition[start + 2..start + 2 + end];
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
        let mut floors = Vec::new();
        for storey in self
            .entities
            .iter()
            .filter(|e| is_storey_entity(&e.entity_type))
        {
            floors.push(self.create_floor_from_entity(storey)?);
        }
        Ok(floors)
    }

    fn create_floor_from_entity(
        &self,
        storey: &IFCEntity,
    ) -> Result<Floor, Box<dyn std::error::Error>> {
        let params = parameters_from_definition(&storey.definition);
        let elevation = params
            .iter()
            .rev()
            .filter_map(|param| param.trim().trim_matches('\'').parse::<f64>().ok())
            .next();
        Ok(Floor {
            id: storey.id.clone(),
            name: extract_storey_name(storey)?,
            level: extract_storey_level(storey)?,
            elevation,
            bounding_box: None,
            wings: Vec::new(),
            equipment: Vec::new(),
            properties: HashMap::new(),
        })
    }

    fn ensure_default_wing(floor: &mut Floor) {
        if floor.wings.is_empty() {
            floor.wings.push(Wing::new("Default".to_string()));
        }
    }

    /// Extract all IFCSPACE entities as Room objects
    pub fn extract_rooms(
        &self,
        allowed_ids: Option<&HashSet<String>>,
    ) -> Result<Vec<Room>, Box<dyn std::error::Error>> {
        let space_entities: Vec<&IFCEntity> = self
            .entities
            .iter()
            .filter(|e| is_space_entity(&e.entity_type))
            .collect();

        let mut rooms = Vec::new();
        for space in space_entities {
            if let Some(ids) = allowed_ids {
                if !ids.contains(&space.id) {
                    continue;
                }
            }
            // Extract placement reference from IFCSPACE definition
            // Format: IFCSPACE('Conference Room',$,#8,$,#20,$,$,.ELEMENT.,0.)
            // The placement is typically the 5th parameter (#20)
            let (x, y, z) = self
                .extract_space_coordinates(space)
                .unwrap_or((0.0, 0.0, 0.0));

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
                name: extract_space_name(space)?,
                room_type: extract_space_type(space)?,
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
                created_at: Some(Utc::now()),
                updated_at: Some(Utc::now()),
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
        let refs: Vec<&str> = re
            .find_iter(&space.definition)
            .map(|m| m.as_str())
            .collect();

        log::debug!(
            "Space {}: Found {} references: {:?}",
            space.id,
            refs.len(),
            refs
        );

        // Representation is the 3rd reference (#1 = building, #98 = placement, #173 = representation)
        if refs.len() >= 3 {
            log::debug!(
                "Extracting polygon from representation reference: {}",
                refs[2]
            );
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
            log::debug!(
                "Entity {} is not IFCPRODUCTDEFINITIONSHAPE: {}",
                ref_id,
                product_def.definition
            );
            return None;
        }

        log::debug!("Got IFCPRODUCTDEFINITIONSHAPE #{}", ref_id);

        // Find the IFCSHAPEREPRESENTATION reference (inside the product def shape definition)
        // IFCPRODUCTDEFINITIONSHAPE($,$,(#172)) - reference is in nested parens
        let shape_ref = self.extract_nested_reference(&product_def.definition)?;
        let shape_id = shape_ref.trim_start_matches('#');
        let shape_repr = self.entity_map.get(shape_id)?;
        if !shape_repr.definition.contains("IFCSHAPEREPRESENTATION") {
            log::debug!(
                "Entity #{} is not IFCSHAPEREPRESENTATION: {}",
                shape_id,
                shape_repr.definition
            );
            return None;
        }

        log::debug!("Got IFCSHAPEREPRESENTATION #{}", shape_id);

        // Find the IFCEXTRUDEDAREASOLID reference
        let extruded_ref = self.extract_second_reference(&shape_repr.definition)?;
        let extruded_id = extruded_ref.trim_start_matches('#');
        let extruded = self.entity_map.get(extruded_id)?;
        if !extruded.definition.contains("IFCEXTRUDEDAREASOLID") {
            log::debug!(
                "Entity #{} is not IFCEXTRUDEDAREASOLID: {}",
                extruded_id,
                extruded.definition
            );
            return None;
        }

        log::debug!("Got IFCEXTRUDEDAREASOLID #{}", extruded_id);

        // Find the IFCARBITRARYCLOSEDPROFILEDEF reference (first parameter of IFCEXTRUDEDAREASOLID)
        let profile_ref = self.extract_first_reference(&extruded.definition)?;
        let profile_id = profile_ref.trim_start_matches('#');
        let profile = self.entity_map.get(profile_id)?;
        if !profile.definition.contains("IFCARBITRARYCLOSEDPROFILEDEF") {
            log::debug!(
                "Entity #{} is not IFCARBITRARYCLOSEDPROFILEDEF: {}",
                profile_id,
                profile.definition
            );
            return None;
        }

        log::debug!("Got IFCARBITRARYCLOSEDPROFILEDEF #{}", profile_id);

        // Find the IFCPOLYLINE reference (second parameter of IFCARBITRARYCLOSEDPROFILEDEF)
        let polyline_ref = self.extract_second_reference(&profile.definition)?;
        let polyline_id = polyline_ref.trim_start_matches('#');
        let polyline = self.entity_map.get(polyline_id)?;
        if !polyline.definition.contains("IFCPOLYLINE") {
            log::debug!(
                "Entity #{} is not IFCPOLYLINE: {}",
                polyline_id,
                polyline.definition
            );
            return None;
        }

        log::debug!("Got IFCPOLYLINE #{}", polyline_id);

        // Extract all IFCCARTESIANPOINT references from IFCPOLYLINE
        // Format: IFCPOLYLINE((#160,#161,#162,#163,#164,#165,#166,#167))
        let polyline_params = self.extract_reference_list(&polyline.definition)?;

        log::debug!(
            "Extracted {} point references from IFCPOLYLINE",
            polyline_params.len()
        );

        // Convert each point reference to coordinates and build the polygon string
        let mut points = Vec::new();
        for point_ref in polyline_params {
            let point_id = point_ref.trim_start_matches('#');
            log::debug!("Looking up point entity #{}", point_id);
            if let Some(point_entity) = self.entity_map.get(point_id) {
                log::debug!(
                    "Found point entity #{}: {}",
                    point_id,
                    point_entity.definition
                );
                if let Some((x, y, _z)) = self.parse_cartesian_point_2d(&point_entity.definition) {
                    log::debug!("Parsed coordinates: ({}, {})", x, y);
                    points.push(format!("{},{}", x, y));
                } else {
                    log::debug!(
                        "Failed to parse coordinates from: {}",
                        point_entity.definition
                    );
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
        let params_str = &definition[start + 2..start + end]; // Skip the "((" part

        log::debug!("extract_reference_list: params_str = '{}'", params_str);

        // Use regex to extract all #number references
        let re = Regex::new(r"#\d+").ok()?;
        let references: Vec<String> = re
            .find_iter(params_str)
            .map(|m| m.as_str().to_string())
            .collect();

        log::debug!(
            "extract_reference_list: extracted {} references",
            references.len()
        );
        Some(references)
    }

    /// Parse a 2D IFCCARTESIANPOINT definition: IFCCARTESIANPOINT((x,y)) or IFCCARTESIANPOINT((x,y,z))
    fn parse_cartesian_point_2d(&self, definition: &str) -> Option<(f64, f64, f64)> {
        // Look for pattern: IFCCARTESIANPOINT((x,y,z)) or IFCCARTESIANPOINT((x,y))
        let start = definition.find("((")?;
        let end = definition[start..].find("))")?;
        let coords_str = &definition[start + 2..start + end]; // Skip both opening parens

        log::debug!("parse_cartesian_point_2d: coords_str = '{}'", coords_str);

        let coords: Vec<&str> = coords_str.split(',').collect();
        if coords.len() >= 2 {
            if let (Ok(x), Ok(y)) = (
                coords[0].trim().parse::<f64>(),
                coords[1].trim().parse::<f64>(),
            ) {
                let z = if coords.len() >= 3 {
                    coords[2].trim().parse::<f64>().unwrap_or(0.0)
                } else {
                    0.0
                };
                return Some((x, y, z));
            }
        }

        None
    }

    /// Extract equipment entities and assign to rooms based on spatial proximity
    pub fn extract_equipment(
        &self,
        _rooms: &[Room],
        allowed_ids: Option<&HashSet<String>>,
    ) -> Result<Vec<Equipment>, Box<dyn std::error::Error>> {
        let equipment_entities: Vec<&IFCEntity> = self
            .entities
            .iter()
            .filter(|e| is_equipment_entity(&e.entity_type))
            .filter(|e| !e.entity_type.contains("TYPE")) // Filter out TYPE definitions (IFCAIRTERMINALTYPE, etc.)
            .collect();

        let mut equipment_list = Vec::new();
        for eq in equipment_entities {
            if let Some(ids) = allowed_ids {
                if !ids.contains(&eq.id) {
                    continue;
                }
            }
            // Extract actual coordinates from placement chain
            let (x, y, z) = self
                .extract_equipment_coordinates(eq)
                .unwrap_or((0.0, 0.0, 0.0));

            let equipment = Equipment {
                id: eq.id.clone(),
                name: eq.name.clone(),
                path: format!("/equipment/{}", eq.name.to_lowercase().replace(" ", "-")),
                address: None,
                equipment_type: extract_equipment_type(&eq.entity_type)?,
                position: Position {
                    x,
                    y,
                    z,
                    coordinate_system: "building_local".to_string(),
                },
                properties: HashMap::new(),
                status: crate::core::EquipmentStatus::Active,
                health_status: None,
                room_id: None, // Will be assigned based on spatial data
                sensor_mappings: None,
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
    pub fn build_hierarchy(&self) -> Result<Building, Box<dyn std::error::Error>> {
        let building_entity = self
            .entities
            .iter()
            .find(|entity| entity.entity_type == "IFCBUILDING");

        let fallback_id = building_entity
            .map(|entity| entity.id.as_str())
            .unwrap_or("building");

        let identifiers = derive_building_identifiers(
            building_entity.map(|entity| entity.name.as_str()),
            fallback_id,
        );
        let building_path = identifiers.canonical_path();

        let mut floors: Vec<Floor> = Vec::new();
        let mut floor_lookup: HashMap<String, usize> = HashMap::new();

        let mut floor_ids: Vec<String> = Vec::new();
        if let Some(building) = building_entity {
            if let Some(children) = self.aggregates.get(&building.id) {
                for child_id in children {
                    if let Some(child_entity) = self.entity_map.get(child_id) {
                        if is_storey_entity(&child_entity.entity_type) {
                            floor_ids.push(child_id.clone());
                        }
                    }
                }
            }
        }

        if floor_ids.is_empty() {
            floor_ids = self
                .entities
                .iter()
                .filter(|e| is_storey_entity(&e.entity_type))
                .map(|e| e.id.clone())
                .collect();
        }

        for floor_id in &floor_ids {
            if let Some(storey) = self.entity_map.get(floor_id) {
                let mut floor = self.create_floor_from_entity(storey)?;
                Self::ensure_default_wing(&mut floor);
                floor_lookup.insert(floor_id.clone(), floors.len());
                floors.push(floor);
            }
        }

        if floors.is_empty() {
            let mut default_floor = Floor::new("Default Floor".to_string(), 0);
            Self::ensure_default_wing(&mut default_floor);
            floor_lookup.insert(default_floor.id.clone(), 0);
            floors.push(default_floor);
        }

        let mut used_paths: HashSet<String> = HashSet::new();
        used_paths.insert(building_path.clone());
        let mut floor_paths: HashMap<String, String> = HashMap::new();
        for (structure_id, &index) in &floor_lookup {
            if let Some(floor) = floors.get_mut(index) {
                let mut floor_slug = slugify(&floor.name);
                if floor_slug.is_empty() {
                    floor_slug = format!("floor-{}", floor.level);
                }
                let candidate = format!("{}/{}", building_path, floor_slug);
                let canonical = ensure_unique_path(&candidate, &mut used_paths);
                floor
                    .properties
                    .insert("canonical_path".to_string(), canonical.clone());
                floor_paths.insert(structure_id.clone(), canonical);
            }
        }

        let room_ids: HashSet<String> = self.room_parents.keys().cloned().collect();
        let mut rooms = if room_ids.is_empty() {
            self.extract_rooms(None)?
        } else {
            self.extract_rooms(Some(&room_ids))?
        };

        let mut rooms_map: HashMap<String, Room> =
            rooms.drain(..).map(|room| (room.id.clone(), room)).collect();
        let mut room_location: HashMap<String, (usize, usize, usize)> = HashMap::new();

        for (structure_id, room_list) in &self.rooms_by_structure {
            if let Some(&floor_idx) = floor_lookup.get(structure_id) {
                let floor = floors.get_mut(floor_idx).unwrap();
                Self::ensure_default_wing(floor);
                let wing_idx = 0;
                for room_id in room_list {
                if let Some(mut room) = rooms_map.remove(room_id) {
                    let base_path = floor_paths
                        .get(structure_id)
                        .cloned()
                        .or_else(|| {
                            floor
                                .properties
                                .get("canonical_path")
                                .cloned()
                        })
                        .unwrap_or_else(|| building_path.clone());

                    let mut room_slug = slugify(&room.name);
                    if room_slug.is_empty() {
                        room_slug = room.id.to_lowercase();
                    }
                    let candidate = format!("{}/{}", base_path, room_slug);
                    let canonical = ensure_unique_path(&candidate, &mut used_paths);
                    room
                        .properties
                        .insert("canonical_path".to_string(), canonical.clone());

                    let position = floor.wings[wing_idx].rooms.len();
                    let room_id_clone = room.id.clone();
                    floor.wings[wing_idx].rooms.push(room);
                    room_location.insert(room_id_clone, (floor_idx, wing_idx, position));
                    }
                }
            }
        }

        if !rooms_map.is_empty() {
            if let Some(first_floor) = floors.first_mut() {
                Self::ensure_default_wing(first_floor);
                let wing_idx = 0;
                let floor_idx = 0;
            let base_path = first_floor
                .properties
                .get("canonical_path")
                .cloned()
                .unwrap_or_else(|| building_path.clone());
            for (_, mut room) in rooms_map.into_iter() {
                let mut room_slug = slugify(&room.name);
                if room_slug.is_empty() {
                    room_slug = room.id.to_lowercase();
                }
                let candidate = format!("{}/{}", base_path, room_slug);
                let canonical = ensure_unique_path(&candidate, &mut used_paths);
                room
                    .properties
                    .insert("canonical_path".to_string(), canonical.clone());
                let position = first_floor.wings[wing_idx].rooms.len();
                let room_id_clone = room.id.clone();
                first_floor.wings[wing_idx].rooms.push(room);
                room_location.insert(room_id_clone, (floor_idx, wing_idx, position));
                }
            }
        }

        let equipment_ids: HashSet<String> = self.element_parents.keys().cloned().collect();
        let mut equipment_list = if equipment_ids.is_empty() {
            self.extract_equipment(&[], None)?
        } else {
            self.extract_equipment(&[], Some(&equipment_ids))?
        };

        for mut equipment in equipment_list.drain(..) {
            let mut placed = false;
            if let Some(parent_id) = self.element_parents.get(&equipment.id) {
                if let Some(&(floor_idx, wing_idx, room_idx)) = room_location.get(parent_id) {
                    let floor = floors.get_mut(floor_idx).unwrap();
                let room_id = floor.wings[wing_idx].rooms[room_idx].id.clone();
                let room_path = floor.wings[wing_idx].rooms[room_idx]
                    .properties
                    .get("canonical_path")
                    .cloned()
                    .unwrap_or_else(|| {
                        floor
                            .properties
                            .get("canonical_path")
                            .cloned()
                            .unwrap_or_else(|| building_path.clone())
                    });
                let mut slug = slugify(&equipment.name);
                if slug.is_empty() {
                    slug = equipment.id.to_lowercase();
                }
                let candidate = format!("{}/{}", room_path, slug);
                let canonical = ensure_unique_path(&candidate, &mut used_paths);
                equipment.path = canonical.clone();
                equipment
                    .properties
                    .insert("canonical_path".to_string(), canonical.clone());
                equipment.room_id = Some(room_id.clone());
                floor.wings[wing_idx].rooms[room_idx]
                        .equipment
                        .push(equipment.clone());
                floor.equipment.push(equipment.clone());
                    placed = true;
                } else if let Some(&floor_idx) = floor_lookup.get(parent_id) {
                let floor = floors.get_mut(floor_idx).unwrap();
                let floor_path = floor
                    .properties
                    .get("canonical_path")
                    .cloned()
                    .unwrap_or_else(|| building_path.clone());
                let mut slug = slugify(&equipment.name);
                if slug.is_empty() {
                    slug = equipment.id.to_lowercase();
                }
                let candidate = format!("{}/{}", floor_path, slug);
                let canonical = ensure_unique_path(&candidate, &mut used_paths);
                equipment.path = canonical.clone();
                equipment
                    .properties
                    .insert("canonical_path".to_string(), canonical.clone());
                floor.equipment.push(equipment.clone());
                    placed = true;
                } else if let Some(room_parent) = self.room_parents.get(parent_id) {
                    if let Some(&(floor_idx, wing_idx, room_idx)) =
                        room_location.get(room_parent)
                    {
                        let floor = floors.get_mut(floor_idx).unwrap();
                    let room_id = floor.wings[wing_idx].rooms[room_idx].id.clone();
                    let room_path = floor.wings[wing_idx].rooms[room_idx]
                        .properties
                        .get("canonical_path")
                        .cloned()
                        .unwrap_or_else(|| {
                            floor
                                .properties
                                .get("canonical_path")
                                .cloned()
                                .unwrap_or_else(|| building_path.clone())
                        });
                    let mut slug = slugify(&equipment.name);
                    if slug.is_empty() {
                        slug = equipment.id.to_lowercase();
                    }
                    let candidate = format!("{}/{}", room_path, slug);
                    let canonical = ensure_unique_path(&candidate, &mut used_paths);
                    equipment.path = canonical.clone();
                    equipment
                        .properties
                        .insert("canonical_path".to_string(), canonical.clone());
                    equipment.room_id = Some(room_id.clone());
                    floor.wings[wing_idx].rooms[room_idx]
                            .equipment
                            .push(equipment.clone());
                    floor.equipment.push(equipment.clone());
                        placed = true;
                    }
                }
            }

            if !placed {
            if let Some(first_floor) = floors.first_mut() {
                let floor_path = first_floor
                    .properties
                    .get("canonical_path")
                    .cloned()
                    .unwrap_or_else(|| building_path.clone());
                let mut slug = slugify(&equipment.name);
                if slug.is_empty() {
                    slug = equipment.id.to_lowercase();
                }
                let candidate = format!("{}/{}", floor_path, slug);
                let canonical = ensure_unique_path(&candidate, &mut used_paths);
                equipment.path = canonical.clone();
                equipment
                    .properties
                    .insert("canonical_path".to_string(), canonical.clone());
                first_floor.equipment.push(equipment.clone());
                }
            }
        }

        let mut building =
        Building::new(identifiers.display_name.clone(), building_path.clone());

        for floor in floors {
            building.add_floor(floor);
        }

        Ok(building)
    }

}

