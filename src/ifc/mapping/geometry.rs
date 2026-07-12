//! Geometry / placement contract for IFC ↔ core model (Phase 4 / L2).
//!
//! ## Coordinate convention
//!
//! - **System:** `building_local` (meters).
//! - **Product placement:** absolute in building coordinates (no parent
//!   `IfcLocalPlacement` chain on Arx export). Floor elevation is stored on
//!   `IfcBuildingStorey` and on `Floor.elevation`; room/equipment Z is absolute.
//! - **Room position:** center of the floor footprint in X/Y; bottom of the
//!   volume in Z (matches `SpatialProperties::new`).
//! - **Body geometry:** expressed in the product's local frame (relative to
//!   placement). Extruded rectangle boxes use X = width, Y = depth, Z = height.
//! - **Equipment without mesh:** position only (no synthetic body on export).

use crate::core::spatial::mesh::Mesh;
use crate::core::spatial::types::Point3D;
use crate::core::{BoundingBox, Dimensions, Position, SpatialProperties};

/// Canonical coordinate system name written on import/export.
pub const COORD_BUILDING_LOCAL: &str = "building_local";

/// Absolute tolerance for coordinate / dimension comparisons (meters).
pub const GEOMETRY_EPSILON: f64 = 1e-3;

/// True if `|a - b| <= GEOMETRY_EPSILON`.
pub fn approx_eq(a: f64, b: f64) -> bool {
    (a - b).abs() <= GEOMETRY_EPSILON
}

/// True if two positions match within epsilon (coordinate system ignored).
pub fn positions_approx_eq(a: &Position, b: &Position) -> bool {
    approx_eq(a.x, b.x) && approx_eq(a.y, b.y) && approx_eq(a.z, b.z)
}

/// True if dimensions match within epsilon.
pub fn dimensions_approx_eq(a: &Dimensions, b: &Dimensions) -> bool {
    approx_eq(a.width, b.width)
        && approx_eq(a.height, b.height)
        && approx_eq(a.depth, b.depth)
}

/// Build `SpatialProperties` from position + dimensions in `building_local`.
pub fn spatial_from_position_dims(position: Position, dimensions: Dimensions) -> SpatialProperties {
    let mut pos = position;
    if pos.coordinate_system.is_empty() {
        pos.coordinate_system = COORD_BUILDING_LOCAL.to_string();
    }
    SpatialProperties::new(pos, dimensions, COORD_BUILDING_LOCAL.to_string())
}

/// Rebuild bounding box from position + dimensions (center XY, bottom Z).
pub fn bounding_box_from_position_dims(
    position: &Position,
    dimensions: &Dimensions,
) -> BoundingBox {
    BoundingBox {
        min: Position {
            x: position.x - dimensions.width / 2.0,
            y: position.y - dimensions.depth / 2.0,
            z: position.z,
            coordinate_system: position.coordinate_system.clone(),
        },
        max: Position {
            x: position.x + dimensions.width / 2.0,
            y: position.y + dimensions.depth / 2.0,
            z: position.z + dimensions.height,
            coordinate_system: position.coordinate_system.clone(),
        },
    }
}

/// Position from a placement origin in building_local.
pub fn position_from_origin(x: f64, y: f64, z: f64) -> Position {
    Position {
        x,
        y,
        z,
        coordinate_system: COORD_BUILDING_LOCAL.to_string(),
    }
}

/// Translate mesh vertices by `(-ox, -oy, -oz)` so they sit in the product
/// local frame given a world-space mesh and placement origin.
pub fn mesh_to_local(mesh: &Mesh, origin_x: f64, origin_y: f64, origin_z: f64) -> Mesh {
    let vertices = mesh
        .vertices
        .iter()
        .map(|v| Point3D::new(v.x - origin_x, v.y - origin_y, v.z - origin_z))
        .collect();
    Mesh {
        vertices,
        indices: mesh.indices.clone(),
    }
}

/// Axis-aligned dimensions from a mesh in local (or world) coordinates.
///
/// Returns `(width=X extent, depth=Y extent, height=Z extent)`.
pub fn dimensions_from_mesh_aabb(mesh: &Mesh) -> Option<Dimensions> {
    if mesh.vertices.is_empty() {
        return None;
    }
    let mut min_x = f64::INFINITY;
    let mut min_y = f64::INFINITY;
    let mut min_z = f64::INFINITY;
    let mut max_x = f64::NEG_INFINITY;
    let mut max_y = f64::NEG_INFINITY;
    let mut max_z = f64::NEG_INFINITY;

    for v in &mesh.vertices {
        min_x = min_x.min(v.x);
        min_y = min_y.min(v.y);
        min_z = min_z.min(v.z);
        max_x = max_x.max(v.x);
        max_y = max_y.max(v.y);
        max_z = max_z.max(v.z);
    }

    let width = (max_x - min_x).abs();
    let depth = (max_y - min_y).abs();
    let height = (max_z - min_z).abs();
    if width <= 0.0 && depth <= 0.0 && height <= 0.0 {
        return None;
    }
    Some(Dimensions {
        width: if width > 0.0 { width } else { 0.0 },
        depth: if depth > 0.0 { depth } else { 0.0 },
        height: if height > 0.0 { height } else { 0.0 },
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spatial_center_bottom_convention() {
        let pos = position_from_origin(10.0, 20.0, 1.0);
        let dims = Dimensions {
            width: 4.0,
            depth: 6.0,
            height: 3.0,
        };
        let sp = spatial_from_position_dims(pos, dims);
        assert!(approx_eq(sp.bounding_box.min.x, 8.0));
        assert!(approx_eq(sp.bounding_box.max.x, 12.0));
        assert!(approx_eq(sp.bounding_box.min.y, 17.0));
        assert!(approx_eq(sp.bounding_box.max.y, 23.0));
        assert!(approx_eq(sp.bounding_box.min.z, 1.0));
        assert!(approx_eq(sp.bounding_box.max.z, 4.0));
    }

    #[test]
    fn mesh_to_local_subtracts_origin() {
        let mesh = Mesh {
            vertices: vec![Point3D::new(5.0, 7.0, 2.0), Point3D::new(6.0, 7.0, 2.0)],
            indices: vec![0, 1, 0],
        };
        let local = mesh_to_local(&mesh, 5.0, 7.0, 2.0);
        assert!(approx_eq(local.vertices[0].x, 0.0));
        assert!(approx_eq(local.vertices[0].y, 0.0));
        assert!(approx_eq(local.vertices[1].x, 1.0));
    }

    #[test]
    fn dimensions_from_aabb() {
        let mesh = Mesh {
            vertices: vec![
                Point3D::new(-2.0, -1.0, 0.0),
                Point3D::new(2.0, 1.0, 3.0),
            ],
            indices: vec![],
        };
        let d = dimensions_from_mesh_aabb(&mesh).unwrap();
        assert!(approx_eq(d.width, 4.0));
        assert!(approx_eq(d.depth, 2.0));
        assert!(approx_eq(d.height, 3.0));
    }
}
