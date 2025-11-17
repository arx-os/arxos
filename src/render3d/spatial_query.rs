//! Spatial query operations for 3D renderer
//!
//! This module provides spatial query functionality for finding entities
//! within the 3D scene using a spatial index.

use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::ifc::{SpatialIndex, SpatialQueryResult, SpatialRelationship};

/// Helper struct for performing spatial queries on a 3D scene
pub struct SpatialQueryHelper<'a> {
    spatial_index: &'a SpatialIndex,
}

impl<'a> SpatialQueryHelper<'a> {
    /// Create a new spatial query helper
    ///
    /// # Arguments
    /// * `spatial_index` - Reference to the spatial index to query
    pub fn new(spatial_index: &'a SpatialIndex) -> Self {
        Self { spatial_index }
    }

    /// Get entities within a 3D bounding box using spatial index
    ///
    /// # Arguments
    /// * `bbox` - The bounding box to search within
    ///
    /// # Returns
    /// Vector of entities found within the bounding box
    pub fn query_entities_in_bbox(&self, bbox: &BoundingBox3D) -> Vec<SpatialQueryResult> {
        self.spatial_index.find_within_bounding_box(bbox.clone())
    }

    /// Get entities within a radius of a point using spatial index
    ///
    /// # Arguments
    /// * `center` - The center point to search from
    /// * `radius` - The search radius
    ///
    /// # Returns
    /// Vector of entities found within the radius
    pub fn query_entities_within_radius(&self, center: &Point3D, radius: f64) -> Vec<SpatialQueryResult> {
        self.spatial_index.find_within_radius(*center, radius)
    }

    /// Get entities in a specific room using spatial index
    ///
    /// # Arguments
    /// * `room_id` - The ID of the room to search in
    ///
    /// # Returns
    /// Vector of entities found in the room
    pub fn query_entities_in_room(&self, room_id: &str) -> Vec<SpatialQueryResult> {
        self.spatial_index
            .find_in_room(room_id)
            .into_iter()
            .map(|entity| SpatialQueryResult {
                entity_id: entity.id().to_string(),
                entity_name: entity.name().to_string(),
                entity_type: entity.entity_type().to_string(),
                distance: 0.0,
                relationship_type: SpatialRelationship::Within,
                intersection_points: vec![],
            })
            .collect()
    }

    /// Get entities on a specific floor using spatial index
    ///
    /// # Arguments
    /// * `floor` - The floor number to search on
    ///
    /// # Returns
    /// Vector of entities found on the floor
    pub fn query_entities_on_floor(&self, floor: i32) -> Vec<SpatialQueryResult> {
        self.spatial_index
            .find_in_floor(floor)
            .into_iter()
            .map(|entity| SpatialQueryResult {
                entity_id: entity.id().to_string(),
                entity_name: entity.name().to_string(),
                entity_type: entity.entity_type().to_string(),
                distance: 0.0,
                relationship_type: SpatialRelationship::Within,
                intersection_points: vec![],
            })
            .collect()
    }

    /// Find the nearest entity to a point using spatial index
    ///
    /// # Arguments
    /// * `point` - The point to search from
    ///
    /// # Returns
    /// Optional nearest entity result
    pub fn find_nearest_entity(&self, point: &Point3D) -> Option<SpatialQueryResult> {
        self.spatial_index.find_nearest(*point)
    }

    /// Get equipment clusters for visualization
    ///
    /// # Arguments
    /// * `min_cluster_size` - Minimum number of equipment items to form a cluster
    ///
    /// # Returns
    /// Vector of clusters, where each cluster is a vector of spatial query results
    pub fn get_equipment_clusters(&self, min_cluster_size: usize) -> Vec<Vec<SpatialQueryResult>> {
        self.spatial_index
            .find_equipment_clusters(10.0, min_cluster_size)
            .into_iter()
            .map(|cluster| {
                cluster
                    .into_iter()
                    .map(|entity| SpatialQueryResult {
                        entity_id: entity.id().to_string(),
                        entity_name: entity.name().to_string(),
                        entity_type: entity.entity_type().to_string(),
                        distance: 0.0,
                        relationship_type: SpatialRelationship::Adjacent,
                        intersection_points: vec![],
                    })
                    .collect()
            })
            .collect()
    }
}

/// Query entities within a bounding box (standalone function)
///
/// # Arguments
/// * `spatial_index` - Reference to the spatial index
/// * `bbox` - The bounding box to search within
///
/// # Returns
/// Vector of entities found within the bounding box, or empty vector if no spatial index
pub fn query_spatial_entities(
    spatial_index: Option<&SpatialIndex>,
    bbox: &BoundingBox3D,
) -> Vec<SpatialQueryResult> {
    if let Some(index) = spatial_index {
        index.find_within_bounding_box(bbox.clone())
    } else {
        vec![]
    }
}

/// Query entities within a radius (standalone function)
///
/// # Arguments
/// * `spatial_index` - Reference to the spatial index
/// * `center` - The center point to search from
/// * `radius` - The search radius
///
/// # Returns
/// Vector of entities found within the radius, or empty vector if no spatial index
pub fn query_entities_within_radius(
    spatial_index: Option<&SpatialIndex>,
    center: &Point3D,
    radius: f64,
) -> Vec<SpatialQueryResult> {
    if let Some(index) = spatial_index {
        index.find_within_radius(*center, radius)
    } else {
        vec![]
    }
}

/// Query entities in a specific room (standalone function)
///
/// # Arguments
/// * `spatial_index` - Reference to the spatial index
/// * `room_id` - The ID of the room to search in
///
/// # Returns
/// Vector of entities found in the room, or empty vector if no spatial index
pub fn query_entities_in_room(
    spatial_index: Option<&SpatialIndex>,
    room_id: &str,
) -> Vec<SpatialQueryResult> {
    if let Some(index) = spatial_index {
        index
            .find_in_room(room_id)
            .into_iter()
            .map(|entity| SpatialQueryResult {
                entity_id: entity.id().to_string(),
                entity_name: entity.name().to_string(),
                entity_type: entity.entity_type().to_string(),
                distance: 0.0,
                relationship_type: SpatialRelationship::Within,
                intersection_points: vec![],
            })
            .collect()
    } else {
        vec![]
    }
}

/// Query entities on a specific floor (standalone function)
///
/// # Arguments
/// * `spatial_index` - Reference to the spatial index
/// * `floor` - The floor number to search on
///
/// # Returns
/// Vector of entities found on the floor, or empty vector if no spatial index
pub fn query_entities_on_floor(
    spatial_index: Option<&SpatialIndex>,
    floor: i32,
) -> Vec<SpatialQueryResult> {
    if let Some(index) = spatial_index {
        index
            .find_in_floor(floor)
            .into_iter()
            .map(|entity| SpatialQueryResult {
                entity_id: entity.id().to_string(),
                entity_name: entity.name().to_string(),
                entity_type: entity.entity_type().to_string(),
                distance: 0.0,
                relationship_type: SpatialRelationship::Within,
                intersection_points: vec![],
            })
            .collect()
    } else {
        vec![]
    }
}

/// Find the nearest entity to a point (standalone function)
///
/// # Arguments
/// * `spatial_index` - Reference to the spatial index
/// * `point` - The point to search from
///
/// # Returns
/// Optional nearest entity result, or None if no spatial index
pub fn find_nearest_entity(
    spatial_index: Option<&SpatialIndex>,
    point: &Point3D,
) -> Option<SpatialQueryResult> {
    if let Some(index) = spatial_index {
        index.find_nearest(*point)
    } else {
        None
    }
}

/// Get equipment clusters (standalone function)
///
/// # Arguments
/// * `spatial_index` - Reference to the spatial index
/// * `min_cluster_size` - Minimum number of equipment items to form a cluster
///
/// # Returns
/// Vector of clusters, or empty vector if no spatial index
pub fn get_equipment_clusters(
    spatial_index: Option<&SpatialIndex>,
    min_cluster_size: usize,
) -> Vec<Vec<SpatialQueryResult>> {
    if let Some(index) = spatial_index {
        index
            .find_equipment_clusters(10.0, min_cluster_size)
            .into_iter()
            .map(|cluster| {
                cluster
                    .into_iter()
                    .map(|entity| SpatialQueryResult {
                        entity_id: entity.id().to_string(),
                        entity_name: entity.name().to_string(),
                        entity_type: entity.entity_type().to_string(),
                        distance: 0.0,
                        relationship_type: SpatialRelationship::Adjacent,
                        intersection_points: vec![],
                    })
                    .collect()
            })
            .collect()
    } else {
        vec![]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_query_spatial_entities_no_index() {
        let bbox = BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 10.0, y: 10.0, z: 10.0 },
        };

        let results = query_spatial_entities(None, &bbox);
        assert_eq!(results.len(), 0);
    }

    #[test]
    fn test_query_entities_within_radius_no_index() {
        let center = Point3D { x: 5.0, y: 5.0, z: 5.0 };
        let radius = 10.0;

        let results = query_entities_within_radius(None, &center, radius);
        assert_eq!(results.len(), 0);
    }

    #[test]
    fn test_find_nearest_entity_no_index() {
        let point = Point3D { x: 5.0, y: 5.0, z: 5.0 };

        let result = find_nearest_entity(None, &point);
        assert!(result.is_none());
    }
}
