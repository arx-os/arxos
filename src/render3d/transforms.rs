//! 3D transformation operations for rendering
//!
//! This module contains functions for transforming 3D scene elements
//! (floors, equipment, rooms) using camera and projection systems.

use super::projections;
use super::types::*;
use crate::core::spatial::{BoundingBox3D, Point3D};

/// Transform floors for rendering with camera and projection
///
/// # Arguments
/// * `floors` - The floors to transform
/// * `projection` - The projection settings to apply
///
/// # Returns
/// Vector of transformed floors with updated bounding boxes
pub fn transform_floors(floors: &[Floor3D], projection: &Projection3D, camera: &Camera3D) -> Vec<Floor3D> {
    floors
        .iter()
        .map(|floor| {
            let transformed_bbox = transform_bounding_box(&floor.bounding_box, projection, camera);
            Floor3D {
                id: floor.id.clone(),
                name: floor.name.clone(),
                level: floor.level,
                elevation: floor.elevation,
                bounding_box: transformed_bbox,
                rooms: floor.rooms.clone(),
                equipment: floor.equipment.clone(),
            }
        })
        .collect()
}

/// Transform equipment for rendering with camera and projection
///
/// # Arguments
/// * `equipment` - The equipment to transform
/// * `projection` - The projection settings to apply
/// * `camera` - The camera settings to apply
///
/// # Returns
/// Vector of transformed equipment with updated positions and bounding boxes
pub fn transform_equipment(equipment: &[Equipment3D], projection: &Projection3D, camera: &Camera3D) -> Vec<Equipment3D> {
    equipment
        .iter()
        .map(|eq| {
            let transformed_position = transform_point(&eq.position, projection, camera);
            let transformed_bbox = transform_bounding_box(&eq.bounding_box, projection, camera);
            Equipment3D {
                id: eq.id.clone(),
                name: eq.name.clone(),
                equipment_type: eq.equipment_type.clone(),
                status: eq.status.clone(),
                position: transformed_position,
                bounding_box: transformed_bbox,
                floor_level: eq.floor_level,
                room_id: eq.room_id.clone(),
                connections: eq.connections.clone(),
                spatial_relationships: eq.spatial_relationships,
                nearest_entity_distance: eq.nearest_entity_distance,
            }
        })
        .collect()
}

/// Transform rooms for rendering with camera and projection
///
/// # Arguments
/// * `rooms` - The rooms to transform
/// * `projection` - The projection settings to apply
/// * `camera` - The camera settings to apply
///
/// # Returns
/// Vector of transformed rooms with updated positions and bounding boxes
pub fn transform_rooms(rooms: &[Room3D], projection: &Projection3D, camera: &Camera3D) -> Vec<Room3D> {
    rooms
        .iter()
        .map(|room| {
            let transformed_position = transform_point(&room.position, projection, camera);
            let transformed_bbox = transform_bounding_box(&room.bounding_box, projection, camera);
            Room3D {
                id: room.id.clone(),
                name: room.name.clone(),
                room_type: room.room_type.clone(),
                position: transformed_position,
                bounding_box: transformed_bbox,
                floor_level: room.floor_level,
                equipment: room.equipment.clone(),
            }
        })
        .collect()
}

/// Transform a 3D point using camera and projection
///
/// # Arguments
/// * `point` - The point to transform
/// * `projection` - The projection settings to apply
/// * `camera` - The camera settings to apply
///
/// # Returns
/// Transformed point in screen space
pub fn transform_point(point: &Point3D, projection: &Projection3D, camera: &Camera3D) -> Point3D {
    match projection.projection_type {
        ProjectionType::Isometric => projections::isometric_projection(point, projection.scale),
        ProjectionType::Orthographic => projections::orthographic_projection(point, projection),
        ProjectionType::Perspective => projections::perspective_projection(point, camera),
    }
}

/// Transform a 3D bounding box using camera and projection
///
/// # Arguments
/// * `bbox` - The bounding box to transform
/// * `projection` - The projection settings to apply
/// * `camera` - The camera settings to apply
///
/// # Returns
/// Transformed bounding box in screen space
pub fn transform_bounding_box(bbox: &BoundingBox3D, projection: &Projection3D, camera: &Camera3D) -> BoundingBox3D {
    let transformed_min = transform_point(&bbox.min, projection, camera);
    let transformed_max = transform_point(&bbox.max, projection, camera);

    BoundingBox3D {
        min: transformed_min,
        max: transformed_max,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    #[test]
    fn test_transform_point_isometric() {
        let point = Point3D { x: 10.0, y: 10.0, z: 5.0 };
        let projection = Projection3D::new(ProjectionType::Isometric, ViewAngle::Isometric, 1.0);
        let camera = Camera3D::default();

        let transformed = transform_point(&point, &projection, &camera);

        // Isometric transformation should modify x and y based on the projection
        assert!(transformed.x != point.x || transformed.y != point.y);
    }

    #[test]
    fn test_transform_bounding_box() {
        let bbox = BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 10.0, y: 10.0, z: 5.0 },
        };
        let projection = Projection3D::new(ProjectionType::Isometric, ViewAngle::Isometric, 1.0);
        let camera = Camera3D::default();

        let transformed = transform_bounding_box(&bbox, &projection, &camera);

        // Both min and max should be transformed
        assert!(transformed.min.x != bbox.min.x || transformed.min.y != bbox.min.y);
        assert!(transformed.max.x != bbox.max.x || transformed.max.y != bbox.max.y);
    }

    #[test]
    fn test_transform_floors_preserves_count() {
        let floors = vec![
            Floor3D {
                id: Arc::new("F1".to_string()),
                name: Arc::new("Floor 1".to_string()),
                level: 1,
                elevation: 0.0,
                bounding_box: BoundingBox3D {
                    min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                    max: Point3D { x: 100.0, y: 100.0, z: 3.0 },
                },
                rooms: vec![],
                equipment: vec![],
            },
        ];
        let projection = Projection3D::new(ProjectionType::Isometric, ViewAngle::Isometric, 1.0);
        let camera = Camera3D::default();

        let transformed = transform_floors(&floors, &projection, &camera);

        assert_eq!(transformed.len(), floors.len());
        assert_eq!(transformed[0].level, floors[0].level);
        assert_eq!(transformed[0].elevation, floors[0].elevation);
    }
}
