//! Geometric utilities for the custom IFC parser.
//! 
//! This module provides high-precision (f64) transformation logic 
//! using nalgebra, tailored for STEP-21 entity resolution.

use nalgebra::{Matrix3, Vector3, Matrix4};
use super::lexer::{RawEntity, Param};
use super::registry::EntityRegistry;

#[derive(Debug, Clone)]
pub struct Transform3D {
    pub matrix: Matrix4<f64>,
}

impl Transform3D {
    pub fn identity() -> Self {
        Self { matrix: Matrix4::identity() }
    }

    pub fn from_translation_rotation(translation: Vector3<f64>, rotation: Matrix3<f64>) -> Self {
        let mut matrix = Matrix4::identity();
        matrix.fixed_view_mut::<3, 3>(0, 0).copy_from(&rotation);
        matrix.fixed_view_mut::<3, 1>(0, 3).copy_from(&translation);
        Self { matrix }
    }

    pub fn compose(&self, other: &Transform3D) -> Self {
        Self { matrix: self.matrix * other.matrix }
    }

    pub fn transform_point(&self, point: &Vector3<f64>) -> Vector3<f64> {
        let p = self.matrix * point.insert_row(3, 1.0);
        p.fixed_view::<3, 1>(0, 0).into_owned()
    }
}

/// Resolves geometric placements for IFC entities.
pub struct GeometryResolver<'a> {
    registry: &'a EntityRegistry,
}

impl<'a> GeometryResolver<'a> {
    pub fn new(registry: &'a EntityRegistry) -> Self {
        Self { registry }
    }

    /// Resolve the global transform for a given entity's placement.
    pub fn resolve_placement(&self, placement_id: u64) -> Transform3D {
        if let Some(entity) = self.registry.get_raw(placement_id) {
            match entity.class.as_str() {
                "IFCLOCALPLACEMENT" => self.resolve_local_placement(entity),
                "IFCAXIS2PLACEMENT3D" => self.resolve_axis2placement3d(entity),
                _ => Transform3D::identity(),
            }
        } else {
            Transform3D::identity()
        }
    }

    fn resolve_local_placement(&self, entity: &RawEntity) -> Transform3D {
        // Param 0: Parent Placement (Optional)
        // Param 1: Relative Placement
        let parent_transform = if let Some(Param::Reference(parent_id)) = entity.params.get(0) {
            self.resolve_placement(*parent_id)
        } else {
            Transform3D::identity()
        };

        let relative_transform = if let Some(Param::Reference(rel_id)) = entity.params.get(1) {
            self.resolve_placement(*rel_id)
        } else {
            Transform3D::identity()
        };

        parent_transform.compose(&relative_transform)
    }

    fn resolve_axis2placement3d(&self, entity: &RawEntity) -> Transform3D {
        // Param 0: Location (IfcCartesianPoint)
        // Param 1: Axis (IfcDirection) - Z direction
        // Param 2: RefDirection (IfcDirection) - X direction
        
        let location = if let Some(Param::Reference(loc_id)) = entity.params.get(0) {
            self.resolve_cartesian_point(*loc_id)
        } else {
            Vector3::new(0.0, 0.0, 0.0)
        };

        let z_axis = if let Some(Param::Reference(axis_id)) = entity.params.get(1) {
            self.resolve_direction(*axis_id).unwrap_or(Vector3::new(0.0, 0.0, 1.0))
        } else {
            Vector3::new(0.0, 0.0, 1.0)
        };

        let x_axis_raw = if let Some(Param::Reference(ref_id)) = entity.params.get(2) {
            self.resolve_direction(*ref_id).unwrap_or(Vector3::new(1.0, 0.0, 0.0))
        } else {
            Vector3::new(1.0, 0.0, 0.0)
        };

        // Orthonormalize
        let z = z_axis.normalize();
        let x = (x_axis_raw - x_axis_raw.dot(&z) * z).normalize();
        let y = z.cross(&x);

        let rotation = Matrix3::from_columns(&[x, y, z]);
        Transform3D::from_translation_rotation(location, rotation)
    }

    pub fn resolve_cartesian_point(&self, point_id: u64) -> Vector3<f64> {
        if let Some(entity) = self.registry.get_raw(point_id) {
            if entity.class == "IFCCARTESIANPOINT" {
                if let Some(Param::List(coords)) = entity.params.get(0) {
                    let x = self.extract_float(&coords, 0).unwrap_or(0.0);
                    let y = self.extract_float(&coords, 1).unwrap_or(0.0);
                    let z = self.extract_float(&coords, 2).unwrap_or(0.0);
                    return Vector3::new(x, y, z);
                }
            }
        }
        Vector3::new(0.0, 0.0, 0.0)
    }

    pub fn resolve_direction(&self, dir_id: u64) -> Option<Vector3<f64>> {
        if let Some(entity) = self.registry.get_raw(dir_id) {
            if entity.class == "IFCDIRECTION" {
                if let Some(Param::List(ratios)) = entity.params.get(0) {
                    let x = self.extract_float(&ratios, 0).unwrap_or(0.0);
                    let y = self.extract_float(&ratios, 1).unwrap_or(0.0);
                    let z = self.extract_float(&ratios, 2).unwrap_or(0.0);
                    let vec = Vector3::new(x, y, z);
                    if vec.norm() > 0.0 {
                        return Some(vec.normalize());
                    }
                }
            }
        }
        None
    }

    /// Resolve points from a polyline (IfcPolyline)
    pub fn resolve_polyline(&self, polyline_id: u64) -> Vec<Vector3<f64>> {
        let mut points = Vec::new();
        if let Some(entity) = self.registry.get_raw(polyline_id) {
            if entity.class == "IFCPOLYLINE" {
                if let Some(Param::List(point_refs)) = entity.params.get(0) {
                    for p_ref in point_refs {
                        if let Param::Reference(p_id) = p_ref {
                            points.push(self.resolve_cartesian_point(*p_id));
                        }
                    }
                }
            }
        }
        points
    }

    /// Resolve a list of points representing a 2D profile
    pub fn resolve_profile_points(&self, profile_id: u64) -> Vec<Vector3<f64>> {
        let mut points = Vec::new();
        if let Some(entity) = self.registry.get_raw(profile_id) {
            match entity.class.as_str() {
                "IFCRECTANGLEPROFILEDEF" => {
                    // Param 3: XDim, Param 4: YDim
                    let dx = self.extract_float(&entity.params, 3).unwrap_or(1.0) / 2.0;
                    let dy = self.extract_float(&entity.params, 4).unwrap_or(1.0) / 2.0;
                    points.push(Vector3::new(-dx, -dy, 0.0));
                    points.push(Vector3::new(dx, -dy, 0.0));
                    points.push(Vector3::new(dx, dy, 0.0));
                    points.push(Vector3::new(-dx, dy, 0.0));
                }
                "IFCARBITRARYCLOSEDPROFILEDEF" => {
                    // Param 2: OuterCurve (IfcPolyline etc)
                    if let Some(Param::Reference(curve_id)) = entity.params.get(2) {
                        points = self.resolve_polyline(*curve_id);
                    }
                }
                _ => {}
            }
        }
        points
    }

    fn extract_float(&self, list: &[Param], index: usize) -> Option<f64> {
        match list.get(index)? {
            Param::Float(f) => Some(*f),
            Param::Integer(i) => Some(*i as f64),
            _ => None,
        }
    }
}
