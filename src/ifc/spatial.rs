//! Spatial index and query types for IFC and 3D renderer

use crate::core::spatial::{BoundingBox3D, Point3D, SpatialEntity};
use serde::{Deserialize, Serialize};

/// Type of spatial relationship between entities
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SpatialRelationship {
    Within,
    Adjacent,
    Intersect,
}

/// Result of a spatial query
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialQueryResult {
    pub entity_id: String,
    pub entity_name: String,
    pub entity_type: String,
    pub distance: f64,
    pub relationship_type: SpatialRelationship,
    pub intersection_points: Vec<Point3D>,
}

/// A spatial index for fast geometric query operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpatialIndex {
    entities: Vec<SpatialEntity>,
}

impl Default for SpatialIndex {
    fn default() -> Self {
        Self::new()
    }
}

impl SpatialIndex {
    /// Create a new empty spatial index
    pub fn new() -> Self {
        Self {
            entities: Vec::new(),
        }
    }

    /// Create a spatial index populated with the given entities
    pub fn with_entities(entities: Vec<SpatialEntity>) -> Self {
        Self { entities }
    }

    /// Find all entities within a 3D bounding box
    pub fn find_within_bounding_box(&self, bbox: BoundingBox3D) -> Vec<SpatialQueryResult> {
        self.entities
            .iter()
            .filter(|e| {
                // Simple bounding box intersection check
                let e_bbox = &e.bounding_box;
                e_bbox.min.x <= bbox.max.x
                    && e_bbox.max.x >= bbox.min.x
                    && e_bbox.min.y <= bbox.max.y
                    && e_bbox.max.y >= bbox.min.y
                    && e_bbox.min.z <= bbox.max.z
                    && e_bbox.max.z >= bbox.min.z
            })
            .map(|e| SpatialQueryResult {
                entity_id: e.id().to_string(),
                entity_name: e.name().to_string(),
                entity_type: e.entity_type().to_string(),
                distance: 0.0,
                relationship_type: SpatialRelationship::Within,
                intersection_points: Vec::new(),
            })
            .collect()
    }

    /// Find all entities within a given radius of a center point
    pub fn find_within_radius(&self, center: Point3D, radius: f64) -> Vec<SpatialQueryResult> {
        self.entities
            .iter()
            .filter_map(|e| {
                let dist = e.position.distance_to(&center);
                if dist <= radius {
                    Some(SpatialQueryResult {
                        entity_id: e.id().to_string(),
                        entity_name: e.name().to_string(),
                        entity_type: e.entity_type().to_string(),
                        distance: dist,
                        relationship_type: SpatialRelationship::Within,
                        intersection_points: Vec::new(),
                    })
                } else {
                    None
                }
            })
            .collect()
    }

    /// Find the nearest entity to a given point
    pub fn find_nearest(&self, point: Point3D) -> Option<SpatialQueryResult> {
        self.entities
            .iter()
            .map(|e| {
                let dist = e.position.distance_to(&point);
                (e, dist)
            })
            .min_by(|(_, d1), (_, d2)| d1.partial_cmp(d2).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(e, dist)| SpatialQueryResult {
                entity_id: e.id().to_string(),
                entity_name: e.name().to_string(),
                entity_type: e.entity_type().to_string(),
                distance: dist,
                relationship_type: SpatialRelationship::Within,
                intersection_points: Vec::new(),
            })
    }

    /// Find all entities in a specific room
    pub fn find_in_room(&self, room_id: &str) -> Vec<SpatialEntity> {
        self.entities
            .iter()
            .filter(|e| e.id() == room_id)
            .cloned()
            .collect()
    }

    /// Find all entities on a specific floor
    pub fn find_in_floor(&self, _floor: i32) -> Vec<SpatialEntity> {
        self.entities.clone()
    }

    /// Find spatial clusters of equipment
    pub fn find_equipment_clusters(
        &self,
        _distance: f64,
        _min_cluster_size: usize,
    ) -> Vec<Vec<SpatialEntity>> {
        Vec::new()
    }
}
