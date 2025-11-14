//! 3D projection mathematics for rendering
//!
//! This module contains projection functions for transforming 3D coordinates
//! to 2D screen coordinates using various projection methods.

use crate::render3d::types::{Camera3D, Projection3D, ViewAngle};
use crate::spatial::Point3D;

/// Apply isometric projection to a 3D point
///
/// # Arguments
///
/// * `point` - 3D point to project
/// * `scale` - Scale factor for projection
///
/// # Returns
///
/// Projected Point3D (z preserved for depth sorting)
pub fn isometric_projection(point: &Point3D, scale: f64) -> Point3D {
    // Isometric projection matrix
    let x = (point.x - point.z) * scale;
    let y = (point.x + point.z) * 0.5 * scale + point.y * scale;
    let z = point.z; // Keep original Z for depth sorting

    Point3D { x, y, z }
}

/// Apply orthographic projection to a 3D point
///
/// # Arguments
///
/// * `point` - 3D point to project
/// * `projection` - Projection configuration containing view angle and scale
///
/// # Returns
///
/// Projected Point3D based on view angle
pub fn orthographic_projection(point: &Point3D, projection: &Projection3D) -> Point3D {
    match projection.view_angle {
        ViewAngle::TopDown => Point3D {
            x: point.x * projection.scale,
            y: point.y * projection.scale,
            z: point.z,
        },
        ViewAngle::Front => Point3D {
            x: point.x * projection.scale,
            y: point.z * projection.scale,
            z: point.y,
        },
        ViewAngle::Side => Point3D {
            x: point.y * projection.scale,
            y: point.z * projection.scale,
            z: point.x,
        },
        ViewAngle::Isometric => isometric_projection(point, projection.scale),
    }
}

/// Apply perspective projection to a 3D point
///
/// # Arguments
///
/// * `point` - 3D point to project
/// * `camera` - Camera configuration containing position and FOV
///
/// # Returns
///
/// Projected Point3D (z contains distance for depth sorting)
pub fn perspective_projection(point: &Point3D, camera: &Camera3D) -> Point3D {
    // Simple perspective projection
    let distance = camera.position.z - point.z;
    if distance <= 0.0 {
        return *point; // Behind camera
    }

    let x = (point.x - camera.position.x) * camera.fov / distance;
    let y = (point.y - camera.position.y) * camera.fov / distance;
    let z = distance; // Use distance for depth sorting

    Point3D { x, y, z }
}

/// Apply the appropriate projection based on projection type
///
/// # Arguments
///
/// * `point` - 3D point to project
/// * `projection` - Projection configuration
/// * `camera` - Camera configuration (used for perspective)
///
/// # Returns
///
/// Projected Point3D
#[allow(dead_code)]
pub fn apply_projection(point: &Point3D, projection: &Projection3D, camera: &Camera3D) -> Point3D {
    match projection.projection_type {
        crate::render3d::types::ProjectionType::Isometric => {
            isometric_projection(point, projection.scale)
        }
        crate::render3d::types::ProjectionType::Orthographic => {
            orthographic_projection(point, projection)
        }
        crate::render3d::types::ProjectionType::Perspective => {
            perspective_projection(point, camera)
        }
    }
}
