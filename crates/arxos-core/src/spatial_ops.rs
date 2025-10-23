//! Spatial operations and queries for ArxOS Core

use crate::{Result, ArxError, Position, BoundingBox, Room, Equipment};
use std::collections::HashMap;

/// Spatial operations manager
pub struct SpatialManager {
    rooms: HashMap<String, Room>,
    equipment: HashMap<String, Equipment>,
}

impl SpatialManager {
    /// Create a new spatial manager
    pub fn new() -> Self {
        Self {
            rooms: HashMap::new(),
            equipment: HashMap::new(),
        }
    }

    /// Add room to spatial index
    pub fn add_room(&mut self, room: Room) {
        self.rooms.insert(room.id.clone(), room);
    }

    /// Add equipment to spatial index
    pub fn add_equipment(&mut self, equipment: Equipment) {
        self.equipment.insert(equipment.id.clone(), equipment);
    }

    /// Query spatial relationships
    pub fn query_spatial(
        &self,
        query_type: &str,
        entity: &str,
        params: Vec<String>,
    ) -> Result<String> {
        match query_type.to_lowercase().as_str() {
            "nearby" => self.query_nearby(entity, &params),
            "within" => self.query_within(entity, &params),
            "intersects" => self.query_intersects(entity, &params),
            "contains" => self.query_contains(entity, &params),
            _ => Err(ArxError::Spatial(format!("Unknown query type: {}", query_type))),
        }
    }

    /// Set spatial relationships between entities
    pub fn set_spatial_relationship(
        &mut self,
        entity1: &str,
        entity2: &str,
        relationship: &str,
    ) -> Result<String> {
        // Find entities
        let room1 = self.find_entity(entity1)?;
        let room2 = self.find_entity(entity2)?;

        match relationship.to_lowercase().as_str() {
            "adjacent" => self.set_adjacent(&room1, &room2),
            "connected" => self.set_connected(&room1, &room2),
            "overlaps" => self.set_overlaps(&room1, &room2),
            _ => Err(ArxError::Spatial(format!("Unknown relationship: {}", relationship))),
        }
    }

    /// Transform coordinates between coordinate systems
    pub fn transform_coordinates(
        &self,
        from: &str,
        to: &str,
        entity: &str,
    ) -> Result<String> {
        let position = self.get_entity_position(entity)?;
        
        match (from.to_lowercase().as_str(), to.to_lowercase().as_str()) {
            ("building_local", "wgs84") => self.transform_to_wgs84(&position),
            ("wgs84", "building_local") => self.transform_to_building_local(&position),
            ("building_local", "utm") => self.transform_to_utm(&position),
            ("utm", "building_local") => self.transform_from_utm(&position),
            _ => Err(ArxError::Spatial(format!("Unsupported coordinate transformation: {} -> {}", from, to))),
        }
    }

    /// Validate spatial data
    pub fn validate_spatial(&self, entity: Option<&str>, tolerance: Option<f64>) -> Result<String> {
        let tolerance = tolerance.unwrap_or(0.1);
        
        if let Some(entity_id) = entity {
            self.validate_entity(entity_id, tolerance)
        } else {
            self.validate_all_entities(tolerance)
        }
    }

    // Private helper methods

    fn query_nearby(&self, entity: &str, params: &[String]) -> Result<String> {
        let distance = if let Some(dist_str) = params.first() {
            dist_str.parse::<f64>()
                .map_err(|_| ArxError::Spatial("Invalid distance parameter".to_string()))?
        } else {
            10.0 // Default 10 meter radius
        };

        let entity_pos = self.get_entity_position(entity)?;
        let mut nearby_entities = Vec::new();

        // Check rooms
        for room in self.rooms.values() {
            let room_pos = &room.spatial_properties.position;
            if self.distance_between(&entity_pos, room_pos) <= distance {
                nearby_entities.push(format!("Room: {} ({}m away)", room.name, 
                    self.distance_between(&entity_pos, room_pos)));
            }
        }

        // Check equipment
        for equipment in self.equipment.values() {
            if self.distance_between(&entity_pos, &equipment.position) <= distance {
                nearby_entities.push(format!("Equipment: {} ({}m away)", equipment.name,
                    self.distance_between(&entity_pos, &equipment.position)));
            }
        }

        Ok(format!("Found {} entities within {}m of {}:\n{}", 
            nearby_entities.len(), distance, entity, nearby_entities.join("\n")))
    }

    fn query_within(&self, _entity: &str, params: &[String]) -> Result<String> {
        if params.is_empty() {
            return Err(ArxError::Spatial("Bounding box parameters required".to_string()));
        }

        let bbox = self.parse_bounding_box(&params[0])?;
        let mut entities_within = Vec::new();

        // Check rooms
        for room in self.rooms.values() {
            if self.is_within_bounds(&room.spatial_properties.position, &bbox) {
                entities_within.push(format!("Room: {}", room.name));
            }
        }

        // Check equipment
        for equipment in self.equipment.values() {
            if self.is_within_bounds(&equipment.position, &bbox) {
                entities_within.push(format!("Equipment: {}", equipment.name));
            }
        }

        Ok(format!("Found {} entities within bounds:\n{}", 
            entities_within.len(), entities_within.join("\n")))
    }

    fn query_intersects(&self, entity: &str, _params: &[String]) -> Result<String> {
        let entity_bbox = self.get_entity_bounding_box(entity)?;
        let mut intersecting_entities = Vec::new();

        // Check rooms
        for room in self.rooms.values() {
            if self.bounding_boxes_intersect(&entity_bbox, &room.spatial_properties.bounding_box) {
                intersecting_entities.push(format!("Room: {}", room.name));
            }
        }

        Ok(format!("Found {} entities intersecting with {}:\n{}", 
            intersecting_entities.len(), entity, intersecting_entities.join("\n")))
    }

    fn query_contains(&self, entity: &str, _params: &[String]) -> Result<String> {
        let entity_bbox = self.get_entity_bounding_box(entity)?;
        let mut contained_entities = Vec::new();

        // Check equipment
        for equipment in self.equipment.values() {
            if self.bounding_box_contains(&entity_bbox, &equipment.position) {
                contained_entities.push(format!("Equipment: {}", equipment.name));
            }
        }

        Ok(format!("Found {} entities contained within {}:\n{}", 
            contained_entities.len(), entity, contained_entities.join("\n")))
    }

    fn set_adjacent(&mut self, entity1: &str, entity2: &str) -> Result<String> {
        // This would update spatial relationships in the data model
        Ok(format!("Set {} as adjacent to {}", entity1, entity2))
    }

    fn set_connected(&mut self, entity1: &str, entity2: &str) -> Result<String> {
        // This would update spatial relationships in the data model
        Ok(format!("Set {} as connected to {}", entity1, entity2))
    }

    fn set_overlaps(&mut self, entity1: &str, entity2: &str) -> Result<String> {
        // This would update spatial relationships in the data model
        Ok(format!("Set {} as overlapping with {}", entity1, entity2))
    }

    fn transform_to_wgs84(&self, position: &Position) -> Result<String> {
        // Mock transformation - in real implementation, this would use proper coordinate transformation
        let lat = position.x * 0.00001 + 40.7128; // Rough conversion
        let lon = position.z * 0.00001 - 74.0060; // Rough conversion
        Ok(format!("WGS84: {:.6}, {:.6}", lat, lon))
    }

    fn transform_to_building_local(&self, position: &Position) -> Result<String> {
        // Mock transformation - in real implementation, this would use proper coordinate transformation
        let x = (position.x - 40.7128) * 100000.0;
        let z = (position.z + 74.0060) * 100000.0;
        Ok(format!("Building Local: {:.2}, {:.2}, {:.2}", x, position.y, z))
    }

    fn transform_to_utm(&self, position: &Position) -> Result<String> {
        // Mock transformation - in real implementation, this would use proper UTM conversion
        let easting = position.x * 1000.0;
        let northing = position.z * 1000.0;
        Ok(format!("UTM: {:.2}, {:.2}", easting, northing))
    }

    fn transform_from_utm(&self, position: &Position) -> Result<String> {
        // Mock transformation - in real implementation, this would use proper UTM conversion
        let x = position.x / 1000.0;
        let z = position.z / 1000.0;
        Ok(format!("Building Local: {:.2}, {:.2}, {:.2}", x, position.y, z))
    }

    fn validate_entity(&self, entity: &str, _tolerance: f64) -> Result<String> {
        let position = self.get_entity_position(entity)?;
        
        // Basic validation checks
        let mut issues = Vec::new();
        
        if !position.x.is_finite() || !position.y.is_finite() || !position.z.is_finite() {
            issues.push("Invalid coordinates (NaN or infinite)");
        }
        
        if position.x.abs() > 10000.0 || position.y.abs() > 1000.0 || position.z.abs() > 10000.0 {
            issues.push("Coordinates out of reasonable range");
        }

        if issues.is_empty() {
            Ok(format!("Entity {} passed spatial validation", entity))
        } else {
            Ok(format!("Entity {} validation issues: {}", entity, issues.join(", ")))
        }
    }

    fn validate_all_entities(&self, tolerance: f64) -> Result<String> {
        let mut total_entities = 0;
        let mut valid_entities = 0;
        let mut issues = Vec::new();

        // Validate rooms
        for room in self.rooms.values() {
            total_entities += 1;
            if let Ok(_) = self.validate_entity(&room.id, tolerance) {
                valid_entities += 1;
            } else {
                issues.push(format!("Room {} has spatial issues", room.name));
            }
        }

        // Validate equipment
        for equipment in self.equipment.values() {
            total_entities += 1;
            if let Ok(_) = self.validate_entity(&equipment.id, tolerance) {
                valid_entities += 1;
            } else {
                issues.push(format!("Equipment {} has spatial issues", equipment.name));
            }
        }

        Ok(format!("Spatial validation complete: {}/{} entities valid\nIssues: {}", 
            valid_entities, total_entities, issues.join("\n")))
    }

    // Helper methods

    fn find_entity(&self, entity: &str) -> Result<String> {
        if self.rooms.contains_key(entity) || self.equipment.contains_key(entity) {
            Ok(entity.to_string())
        } else {
            Err(ArxError::Unknown(format!("Entity not found: {}", entity)))
        }
    }

    fn get_entity_position(&self, entity: &str) -> Result<Position> {
        if let Some(room) = self.rooms.get(entity) {
            Ok(room.spatial_properties.position.clone())
        } else if let Some(equipment) = self.equipment.get(entity) {
            Ok(equipment.position.clone())
        } else {
            Err(ArxError::Unknown(format!("Entity not found: {}", entity)))
        }
    }

    fn get_entity_bounding_box(&self, entity: &str) -> Result<BoundingBox> {
        if let Some(room) = self.rooms.get(entity) {
            Ok(room.spatial_properties.bounding_box.clone())
        } else {
            Err(ArxError::Unknown(format!("Entity not found or no bounding box: {}", entity)))
        }
    }

    fn distance_between(&self, pos1: &Position, pos2: &Position) -> f64 {
        let dx = pos1.x - pos2.x;
        let dy = pos1.y - pos2.y;
        let dz = pos1.z - pos2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    fn is_within_bounds(&self, position: &Position, bbox: &BoundingBox) -> bool {
        position.x >= bbox.min.x && position.x <= bbox.max.x &&
        position.y >= bbox.min.y && position.y <= bbox.max.y &&
        position.z >= bbox.min.z && position.z <= bbox.max.z
    }

    fn bounding_boxes_intersect(&self, bbox1: &BoundingBox, bbox2: &BoundingBox) -> bool {
        bbox1.min.x <= bbox2.max.x && bbox1.max.x >= bbox2.min.x &&
        bbox1.min.y <= bbox2.max.y && bbox1.max.y >= bbox2.min.y &&
        bbox1.min.z <= bbox2.max.z && bbox1.max.z >= bbox2.min.z
    }

    fn bounding_box_contains(&self, bbox: &BoundingBox, position: &Position) -> bool {
        position.x >= bbox.min.x && position.x <= bbox.max.x &&
        position.y >= bbox.min.y && position.y <= bbox.max.y &&
        position.z >= bbox.min.z && position.z <= bbox.max.z
    }

    fn parse_bounding_box(&self, bbox_str: &str) -> Result<BoundingBox> {
        // Parse format: "min_x,min_y,min_z,max_x,max_y,max_z"
        let parts: Vec<&str> = bbox_str.split(',').collect();
        if parts.len() != 6 {
            return Err(ArxError::Spatial("Invalid bounding box format".to_string()));
        }

        let min_x = parts[0].trim().parse::<f64>()
            .map_err(|_| ArxError::Spatial("Invalid min_x".to_string()))?;
        let min_y = parts[1].trim().parse::<f64>()
            .map_err(|_| ArxError::Spatial("Invalid min_y".to_string()))?;
        let min_z = parts[2].trim().parse::<f64>()
            .map_err(|_| ArxError::Spatial("Invalid min_z".to_string()))?;
        let max_x = parts[3].trim().parse::<f64>()
            .map_err(|_| ArxError::Spatial("Invalid max_x".to_string()))?;
        let max_y = parts[4].trim().parse::<f64>()
            .map_err(|_| ArxError::Spatial("Invalid max_y".to_string()))?;
        let max_z = parts[5].trim().parse::<f64>()
            .map_err(|_| ArxError::Spatial("Invalid max_z".to_string()))?;

        Ok(BoundingBox {
            min: Position {
                x: min_x,
                y: min_y,
                z: min_z,
                coordinate_system: "building_local".to_string(),
            },
            max: Position {
                x: max_x,
                y: max_y,
                z: max_z,
                coordinate_system: "building_local".to_string(),
            },
        })
    }
}
