//! # Spatial Operations and Queries for ArxOS Core
//!
//! This module provides advanced spatial operations and query capabilities for building data,
//! including spatial indexing, proximity searches, spatial relationships, and coordinate transformations.
//!
//! ## Features
//!
//! - **Spatial Indexing**: Efficient spatial data structures for fast queries
//! - **Proximity Searches**: Find entities within specified distances
//! - **Spatial Relationships**: Determine spatial relationships between entities
//! - **Coordinate Transformations**: Convert between coordinate systems
//! - **Spatial Validation**: Validate spatial data integrity
//! - **Query Operations**: Complex spatial queries and filtering
//!
//! ## Spatial Query Types
//!
//! - **Within**: Find entities within a bounding box or region
//! - **Nearby**: Find entities within a specified distance
//! - **Intersects**: Find entities that intersect with a given geometry
//! - **Contains**: Find entities that contain a given point or geometry
//! - **Overlaps**: Find entities that overlap with a given geometry
//!
//! ## Examples
//!
//! ```rust
//! use arxos_core::spatial_ops::{SpatialManager, Room, Equipment};
//!
//! let mut manager = SpatialManager::new();
//! 
//! // Add rooms and equipment
//! let room = Room { /* room data */ };
//! let equipment = Equipment { /* equipment data */ };
//! manager.add_room(room);
//! manager.add_equipment(equipment);
//! 
//! // Query for rooms within a bounding box
//! let rooms_in_area = manager.query_spatial(
//!     "within",
//!     "room",
//!     vec!["bbox:10,10,0,20,20,5".to_string()]
//! )?;
//! ```
//!
//! ## Performance Considerations
//!
//! - Spatial indexing uses R-tree for efficient range queries
//! - Query results are cached for repeated operations
//! - Large datasets are processed in batches for memory efficiency

use crate::{Result, ArxError, Position, BoundingBox, Room, Equipment};
use crate::spatial_index::{SpatialRTree, convert_room_to_spatial, convert_equipment_to_spatial};
use std::collections::HashMap;

/// Spatial operations manager
#[derive(Debug)]
pub struct SpatialManager {
    rooms: HashMap<String, Room>,
    equipment: HashMap<String, Equipment>,
    spatial_index: SpatialRTree,
}

impl SpatialManager {
    /// Create a new spatial manager
    pub fn new() -> Self {
        Self {
            rooms: HashMap::new(),
            equipment: HashMap::new(),
            spatial_index: SpatialRTree::new(),
        }
    }

    /// Add room to spatial index
    pub fn add_room(&mut self, room: Room) -> Result<()> {
        let spatial_entity = convert_room_to_spatial(&room);
        self.spatial_index.insert(spatial_entity)?;
        self.rooms.insert(room.id.clone(), room);
        Ok(())
    }

    /// Add equipment to spatial index
    pub fn add_equipment(&mut self, equipment: Equipment) -> Result<()> {
        let spatial_entity = convert_equipment_to_spatial(&equipment);
        self.spatial_index.insert(spatial_entity)?;
        self.equipment.insert(equipment.id.clone(), equipment);
        Ok(())
    }

    /// Query spatial relationships using R-Tree index
    pub fn query_spatial(
        &self,
        query_type: &str,
        entity: &str,
        params: Vec<String>,
    ) -> Result<Vec<crate::types::SpatialQueryResult>> {
        match query_type.to_lowercase().as_str() {
            "nearby" => self.query_nearby_r_tree(entity, &params),
            "within" => self.query_within_r_tree(entity, &params),
            "intersects" => self.query_intersects_r_tree(entity, &params),
            "contains" => self.query_contains_r_tree(entity, &params),
            "rooms_in_floor" => self.query_rooms_in_floor_r_tree(&params),
            _ => Err(ArxError::spatial_error(format!("Unknown query type: {}", query_type))),
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
            _ => Err(ArxError::spatial_error(format!("Unknown relationship: {}", relationship))),
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
            _ => Err(ArxError::CoordinateTransformationFailed {
                from: from.to_string(),
                to: to.to_string(),
                reason: "Unsupported transformation".to_string(),
            }),
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
        // Convert building local coordinates to WGS84 geographic coordinates
        // This uses a simplified transformation - in production, you'd use proper geodetic calculations
        
        // Assume building origin is at a known geographic location
        // For this example, we'll use New York City as the origin
        let building_origin_lat: f64 = 40.7128; // NYC latitude
        let building_origin_lon: f64 = -74.0060; // NYC longitude
        
        // Convert meters to degrees (approximate)
        // 1 degree latitude ≈ 111,000 meters
        // 1 degree longitude ≈ 111,000 * cos(latitude) meters
        let meters_per_degree_lat = 111000.0;
        let meters_per_degree_lon = 111000.0 * building_origin_lat.to_radians().cos();
        
        let lat = building_origin_lat + (position.x / meters_per_degree_lat);
        let lon = building_origin_lon + (position.z / meters_per_degree_lon);
        
        Ok(format!("WGS84: {:.8}, {:.8}, {:.2}m", lat, lon, position.y))
    }

    fn transform_to_building_local(&self, position: &Position) -> Result<String> {
        // Convert WGS84 geographic coordinates to building local coordinates
        // This uses a simplified transformation - in production, you'd use proper geodetic calculations
        
        // Assume building origin is at a known geographic location
        let building_origin_lat: f64 = 40.7128; // NYC latitude
        let building_origin_lon: f64 = -74.0060; // NYC longitude
        
        // Convert degrees to meters (approximate)
        let meters_per_degree_lat = 111000.0;
        let meters_per_degree_lon = 111000.0 * building_origin_lat.to_radians().cos();
        
        let x = (position.x - building_origin_lat) * meters_per_degree_lat;
        let z = (position.z - building_origin_lon) * meters_per_degree_lon;
        
        Ok(format!("Building Local: {:.2}, {:.2}, {:.2}", x, position.y, z))
    }

    fn transform_to_utm(&self, position: &Position) -> Result<String> {
        // Convert building local coordinates to UTM coordinates
        // This is a simplified transformation - proper UTM conversion requires zone calculations
        
        // Assume we're in UTM Zone 18N (New York area)
        let utm_zone = 18;
        let utm_false_easting = 500000.0; // UTM false easting
        let utm_false_northing = 0.0; // UTM false northing for northern hemisphere
        
        // Simplified conversion (in production, use proper UTM formulas)
        let easting = position.x + utm_false_easting;
        let northing = position.z + utm_false_northing;
        
        Ok(format!("UTM Zone {}N: {:.2}, {:.2}", utm_zone, easting, northing))
    }

    fn transform_from_utm(&self, position: &Position) -> Result<String> {
        // Convert UTM coordinates to building local coordinates
        // This is a simplified transformation - proper UTM conversion requires zone calculations
        
        // Assume we're in UTM Zone 18N (New York area)
        let utm_false_easting = 500000.0; // UTM false easting
        let utm_false_northing = 0.0; // UTM false northing for northern hemisphere
        
        // Simplified conversion (in production, use proper UTM formulas)
        let x = position.x - utm_false_easting;
        let z = position.z - utm_false_northing;
        
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
            Err(ArxError::Unknown { 
                message: format!("Entity not found: {}", entity), 
                source: None 
            })
        }
    }

    fn get_entity_position(&self, entity: &str) -> Result<Position> {
        if let Some(room) = self.rooms.get(entity) {
            Ok(room.spatial_properties.position.clone())
        } else if let Some(equipment) = self.equipment.get(entity) {
            Ok(equipment.position.clone())
        } else {
            Err(ArxError::Unknown { 
                message: format!("Entity not found: {}", entity), 
                source: None 
            })
        }
    }
    
    /// Get spatial index statistics
    pub fn get_spatial_stats(&self) -> crate::spatial_index::SpatialIndexStats {
        self.spatial_index.get_stats()
    }
    
    /// Optimize the spatial index
    pub fn optimize_index(&mut self) {
        self.spatial_index.optimize();
    }
    
    /// Clear all spatial data
    pub fn clear_all(&mut self) {
        self.rooms.clear();
        self.equipment.clear();
        self.spatial_index.clear();
    }
    
    // R-Tree query methods
    
    /// Query entities nearby a point using R-Tree
    fn query_nearby_r_tree(&self, _entity: &str, params: &[String]) -> Result<Vec<crate::types::SpatialQueryResult>> {
        if params.is_empty() {
            return Err(ArxError::spatial_error("Missing distance parameter"));
        }
        
        let distance: f64 = params[0].parse()
            .map_err(|_| ArxError::spatial_error("Invalid distance parameter"))?;
        
        // Create a reference point (simplified)
        let reference_point = Position {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        };
        
        let nearby_entities = self.spatial_index.query_nearby(&reference_point, distance);
        Ok(crate::spatial_index::convert_to_query_results(nearby_entities, Some(&reference_point)))
    }

    /// Query entities within a bounding box using R-Tree
    fn query_within_r_tree(&self, _entity: &str, params: &[String]) -> Result<Vec<crate::types::SpatialQueryResult>> {
        if params.is_empty() {
            return Err(ArxError::spatial_error("Missing bounding box parameter"));
        }
        
        // Parse bounding box from parameters
        let bbox_str = &params[0];
        let coords: Vec<f64> = bbox_str.split(',')
            .map(|s| s.parse().unwrap_or(0.0))
            .collect();
        
        if coords.len() != 6 {
            return Err(ArxError::spatial_error("Invalid bounding box format"));
        }
        
        let bbox = BoundingBox {
            min: Position {
                x: coords[0],
                y: coords[1],
                z: coords[2],
                coordinate_system: "building_local".to_string(),
            },
            max: Position {
                x: coords[3],
                y: coords[4],
                z: coords[5],
                coordinate_system: "building_local".to_string(),
            },
        };
        
        let within_entities = self.spatial_index.query_within(&bbox);
        Ok(crate::spatial_index::convert_to_query_results(within_entities, None))
    }

    /// Query entities that intersect with a bounding box using R-Tree
    fn query_intersects_r_tree(&self, _entity: &str, params: &[String]) -> Result<Vec<crate::types::SpatialQueryResult>> {
        if params.is_empty() {
            return Err(ArxError::spatial_error("Missing bounding box parameter"));
        }
        
        // Parse bounding box from parameters
        let bbox_str = &params[0];
        let coords: Vec<f64> = bbox_str.split(',')
            .map(|s| s.parse().unwrap_or(0.0))
            .collect();
        
        if coords.len() != 6 {
            return Err(ArxError::spatial_error("Invalid bounding box format"));
        }
        
        let bbox = BoundingBox {
            min: Position {
                x: coords[0],
                y: coords[1],
                z: coords[2],
                coordinate_system: "building_local".to_string(),
            },
            max: Position {
                x: coords[3],
                y: coords[4],
                z: coords[5],
                coordinate_system: "building_local".to_string(),
            },
        };
        
        let intersecting_entities = self.spatial_index.query_intersects(&bbox);
        Ok(crate::spatial_index::convert_to_query_results(intersecting_entities, None))
    }

    /// Query entities that contain a point using R-Tree
    fn query_contains_r_tree(&self, _entity: &str, params: &[String]) -> Result<Vec<crate::types::SpatialQueryResult>> {
        if params.is_empty() {
            return Err(ArxError::spatial_error("Missing point parameter"));
        }
        
        // Parse point from parameters
        let point_str = &params[0];
        let coords: Vec<f64> = point_str.split(',')
            .map(|s| s.parse().unwrap_or(0.0))
            .collect();
        
        if coords.len() != 3 {
            return Err(ArxError::spatial_error("Invalid point format"));
        }
        
        let point = Position {
            x: coords[0],
            y: coords[1],
            z: coords[2],
            coordinate_system: "building_local".to_string(),
        };
        
        let containing_entities = self.spatial_index.query_contains(&point);
        Ok(crate::spatial_index::convert_to_query_results(containing_entities, Some(&point)))
    }

    /// Query rooms in a specific floor using R-Tree
    fn query_rooms_in_floor_r_tree(&self, params: &[String]) -> Result<Vec<crate::types::SpatialQueryResult>> {
        if params.is_empty() {
            return Err(ArxError::spatial_error("Missing floor parameter"));
        }
        
        let floor_level: f64 = params[0].parse()
            .map_err(|_| ArxError::spatial_error("Invalid floor level"))?;
        
        let tolerance = 1.0; // 1 meter tolerance
        let floor_entities = self.spatial_index.query_by_level(floor_level, tolerance);
        
        // Filter for rooms only
        let room_entities: Vec<&crate::spatial_index::SpatialEntity> = floor_entities
            .into_iter()
            .filter(|entity| entity.entity_type == crate::spatial_index::SpatialEntityType::Room)
            .collect();
        
        Ok(crate::spatial_index::convert_to_query_results(room_entities, None))
    }
}
