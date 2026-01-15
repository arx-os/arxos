//! Mesh extraction for the native IFC parser.
//! 
//! This module resolves geometric entities into ArxOS Mesh structures
//! (vertices and indices), ensuring 1:1 fidelity with the source STEP data.

use crate::core::spatial::mesh::Mesh;
use crate::core::spatial::types::Point3D;
use super::lexer::{RawEntity, Param};
use super::registry::EntityRegistry;
use super::geometry::{GeometryResolver, Transform3D};
use nalgebra::Vector3;

pub struct MeshResolver<'a> {
    registry: &'a EntityRegistry,
    geometry: &'a GeometryResolver<'a>,
}

impl<'a> MeshResolver<'a> {
    pub fn new(registry: &'a EntityRegistry, geometry: &'a GeometryResolver<'a>) -> Self {
        Self { registry, geometry }
    }

    /// Extract a Mesh from a product definition shape.
    pub fn extract_mesh_from_shape(&self, shape_id: u64, transform: &Transform3D) -> Option<Mesh> {
        let shape_entity = self.registry.get_raw(shape_id)?;
        if shape_entity.class != "IFCPRODUCTDEFINITIONSHAPE" {
            return None;
        }

        // Param 2: Representations (List of IfcShapeRepresentation)
        if let Some(Param::List(reps)) = shape_entity.params.get(2) {
            for rep_id_param in reps {
                if let Param::Reference(rep_id) = rep_id_param {
                    if let Some(mesh) = self.extract_mesh_from_representation(*rep_id, transform) {
                        return Some(mesh); // Return first valid mesh for now
                    }
                }
            }
        }

        None
    }

    fn extract_mesh_from_representation(&self, rep_id: u64, transform: &Transform3D) -> Option<Mesh> {
        let rep_entity = self.registry.get_raw(rep_id)?;
        if rep_entity.class != "IFCSHAPEREPRESENTATION" {
            return None;
        }

        // Param 3: Items (List of geometric items)
        if let Some(Param::List(items)) = rep_entity.params.get(3) {
            for item_id_param in items {
                if let Param::Reference(item_id) = item_id_param {
                    if let Some(mesh) = self.resolve_mesh_item(*item_id, transform) {
                        return Some(mesh);
                    }
                }
            }
        }

        None
    }

    pub fn resolve_mesh_item(&self, item_id: u64, transform: &Transform3D) -> Option<Mesh> {
        let item_entity = self.registry.get_raw(item_id)?;
        match item_entity.class.as_str() {
            "IFCTRIANGULATEDFACESET" => self.resolve_triangulated_face_set(item_entity, transform),
            "IFCEXTRUDEDAREASOLID" => self.resolve_extruded_area_solid(item_entity, transform),
            _ => None,
        }
    }

    fn resolve_triangulated_face_set(&self, entity: &RawEntity, transform: &Transform3D) -> Option<Mesh> {
        // Param 0: Coordinates (Reference to IfcCartesianPointList3D)
        let coords_id = match entity.params.get(0)? {
            Param::Reference(id) => *id,
            _ => return None,
        };

        let vertices = self.resolve_point_list_3d(coords_id, transform)?;

        // Param 3: CoordIndex (List of Triangles)
        let mut indices = Vec::new();
        if let Some(Param::List(triangles)) = entity.params.get(3) {
            for triangle_param in triangles {
                if let Param::List(tri) = triangle_param {
                    for index_param in tri {
                        if let Param::Integer(idx) = index_param {
                            // IFC indices are 1-based
                            indices.push((*idx - 1) as u32);
                        }
                    }
                }
            }
        }

        if vertices.is_empty() || indices.is_empty() {
            return None;
        }

        Some(Mesh { vertices, indices })
    }

    fn resolve_extruded_area_solid(&self, entity: &RawEntity, transform: &Transform3D) -> Option<Mesh> {
        // Param 0: SweptArea (IfcProfileDef)
        // Param 1: Position (IfcAxis2Placement3D) - Local origin of extrusion
        // Param 2: ExtrudedDirection (IfcDirection)
        // Param 3: Depth (Real)

        let profile_id = match entity.params.get(0)? {
            Param::Reference(id) => *id,
            _ => return None,
        };
        
        let local_pos_id = match entity.params.get(1)? {
            Param::Reference(id) => *id,
            _ => return None,
        };

        let depth = match entity.params.get(3)? {
            Param::Float(f) => *f,
            Param::Integer(i) => *i as f64,
            _ => 1.0,
        };

        let profile_points = self.geometry.resolve_profile_points(profile_id);
        if profile_points.len() < 3 {
            return None;
        }

        let local_transform = self.geometry.resolve_placement(local_pos_id);
        let final_transform = transform.compose(&local_transform);

        let mut vertices = Vec::new();
        let mut indices = Vec::new();

        // 1. Generate bottom vertices
        for p in &profile_points {
            let v = final_transform.transform_point(p);
            vertices.push(Point3D::new(v.x, v.y, v.z));
        }

        // 2. Generate top vertices (offset by depth along local Z)
        let z_offset = Vector3::new(0.0, 0.0, depth);
        for p in &profile_points {
            let p_top = p + z_offset;
            let v = final_transform.transform_point(&p_top);
            vertices.push(Point3D::new(v.x, v.y, v.z));
        }

        let n = profile_points.len() as u32;

        // 3. Side walls triangles
        for i in 0..n {
            let next = (i + 1) % n;
            let b1 = i;
            let b2 = next;
            let t1 = i + n;
            let t2 = next + n;

            // Two triangles per side face
            indices.push(b1); indices.push(b2); indices.push(t1);
            indices.push(b2); indices.push(t2); indices.push(t1);
        }

        // 4. Bottom and Top caps (Simple fan for convexity)
        for i in 1..(n - 1) {
            // Bottom cap
            indices.push(0); indices.push(i + 1); indices.push(i);
            // Top cap
            indices.push(n); indices.push(n + i); indices.push(n + i + 1);
        }

        Some(Mesh { vertices, indices })
    }

    fn resolve_point_list_3d(&self, list_id: u64, transform: &Transform3D) -> Option<Vec<Point3D>> {
        let list_entity = self.registry.get_raw(list_id)?;
        if list_entity.class != "IFCCARTESIANPOINTLIST3D" {
            return None;
        }

        // Param 0: CoordList
        let mut vertices = Vec::new();
        if let Some(Param::List(coord_list)) = list_entity.params.get(0) {
            for point_param in coord_list {
                if let Param::List(coords) = point_param {
                    let x = self.extract_float(&coords, 0).unwrap_or(0.0);
                    let y = self.extract_float(&coords, 1).unwrap_or(0.0);
                    let z = self.extract_float(&coords, 2).unwrap_or(0.0);
                    
                    let v = Vector3::new(x, y, z);
                    let transformed = transform.transform_point(&v);
                    
                    vertices.push(Point3D::new(transformed.x, transformed.y, transformed.z));
                }
            }
        }

        Some(vertices)
    }

    fn extract_float(&self, list: &[Param], index: usize) -> Option<f64> {
        match list.get(index)? {
            Param::Float(f) => Some(*f),
            Param::Integer(i) => Some(*i as f64),
            _ => None,
        }
    }
}
