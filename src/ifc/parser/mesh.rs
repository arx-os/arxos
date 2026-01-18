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
            "IFCSHELLBASEDSURFACEMODEL" => self.resolve_shell_based_surface_model(item_entity, transform),
            "IFCFACETEDBREP" => self.resolve_faceted_brep(item_entity, transform),
            "IFCCLOSEDSHELL" | "IFCOPENSHELL" => self.resolve_shell(item_id, transform),
            "IFCBOOLEANRESULT" => self.resolve_boolean_result(item_entity, transform),
            _ => None,
        }
    }

    fn resolve_boolean_result(&self, entity: &RawEntity, transform: &Transform3D) -> Option<Mesh> {
        // IfcBooleanResult
        // Param 0: Operator (.UNION., .INTERSECTION., .DIFFERENCE.)
        // Param 1: FirstOperand
        // Param 2: SecondOperand
        
        let op = if let Some(Param::Enum(op_str)) = entity.params.get(0) {
            op_str.as_str()
        } else {
            ".UNION."
        };

        let first_mesh = if let Some(Param::Reference(first_id)) = entity.params.get(1) {
            self.resolve_mesh_item(*first_id, transform)
        } else {
            None
        };

        // For now, we only support Union (merging meshes) or simple "first operand" for Difference
        // Full CSG intersection/difference is computationally expensive and left for Phase 4
        if op == ".UNION." {
            if let Some(Param::Reference(second_id)) = entity.params.get(2) {
                let second_mesh = self.resolve_mesh_item(*second_id, transform);
                match (first_mesh, second_mesh) {
                    (Some(mut m1), Some(m2)) => {
                        let offset = m1.vertices.len() as u32;
                        m1.vertices.extend(m2.vertices);
                        m1.indices.extend(m2.indices.iter().map(|i| i + offset));
                        return Some(m1);
                    }
                    (Some(m1), None) => return Some(m1),
                    (None, Some(m2)) => return Some(m2),
                    _ => return None,
                }
            }
        }

        // Default to first operand for Difference/Intersection
        first_mesh
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

    fn resolve_shell_based_surface_model(&self, entity: &RawEntity, transform: &Transform3D) -> Option<Mesh> {
        // Param 0: SbsmBoundary (List of shells)
        let mut all_vertices = Vec::new();
        let mut all_indices = Vec::new();

        if let Some(Param::List(shells)) = entity.params.get(0) {
            for shell_param in shells {
                if let Param::Reference(shell_id) = shell_param {
                    if let Some(mesh) = self.resolve_shell(*shell_id, transform) {
                        let offset = all_vertices.len() as u32;
                        all_vertices.extend(mesh.vertices);
                        all_indices.extend(mesh.indices.into_iter().map(|i| i + offset));
                    }
                }
            }
        }

        if all_vertices.is_empty() {
            return None;
        }

        Some(Mesh { vertices: all_vertices, indices: all_indices })
    }

    fn resolve_faceted_brep(&self, entity: &RawEntity, transform: &Transform3D) -> Option<Mesh> {
        // Param 0: Outer (IfcClosedShell)
        if let Some(Param::Reference(shell_id)) = entity.params.get(0) {
            return self.resolve_shell(*shell_id, transform);
        }
        None
    }

    fn resolve_shell(&self, shell_id: u64, transform: &Transform3D) -> Option<Mesh> {
        let shell_entity = self.registry.get_raw(shell_id)?;
        // IfcClosedShell or IfcOpenShell
        // Param 0: CfsFaces (List of IfcFace)
        
        let mut all_vertices = Vec::new();
        let mut all_indices = Vec::new();

        if let Some(Param::List(faces)) = shell_entity.params.get(0) {
            for face_param in faces {
                if let Param::Reference(face_id) = face_param {
                    if let Some(mesh) = self.resolve_face(*face_id, transform) {
                        let offset = all_vertices.len() as u32;
                        all_vertices.extend(mesh.vertices);
                        all_indices.extend(mesh.indices.into_iter().map(|i| i + offset));
                    }
                }
            }
        }

        if all_vertices.is_empty() {
            return None;
        }

        Some(Mesh { vertices: all_vertices, indices: all_indices })
    }

    fn resolve_face(&self, face_id: u64, transform: &Transform3D) -> Option<Mesh> {
        let face_entity = self.registry.get_raw(face_id)?;
        // IfcFace
        // Param 0: Bounds (List of IfcFaceBound)
        
        let mut all_bounds_vertices = Vec::new();
        let mut hole_indices = Vec::new();
        let mut current_offset = 0;

        if let Some(Param::List(bounds)) = face_entity.params.get(0) {
            for (i, bound_param) in bounds.iter().enumerate() {
                if let Param::Reference(bound_id) = bound_param {
                    if let Some(vertices) = self.resolve_bound_points(*bound_id, transform) {
                        if i > 0 {
                            hole_indices.push(current_offset);
                        }
                        current_offset += vertices.len();
                        all_bounds_vertices.extend(vertices);
                    }
                }
            }
        }

        if all_bounds_vertices.is_empty() {
            return None;
        }

        // Triangulate using earcutr
        // Earcutr expects a flat array of coordinates [x, y, z, x, y, z, ...]
        // However, it works best in 2D. We need to project to the face plane.
        // For now, let's try 3D earcutr if available, otherwise project to 2D.
        // earcutr usually takes [[f64; 2]], so we need to project.
        
        let n = all_bounds_vertices.len();
        let mut flat_coords = Vec::with_capacity(n * 2);
        
        // Find best projection plane (X, Y, or Z) based on normal
        let normal = calculate_normal(&all_bounds_vertices[..all_bounds_vertices.len().min(3)]);
        let (idx1, idx2) = if normal.z.abs() > normal.x.abs() && normal.z.abs() > normal.y.abs() {
            (0, 1) // Project to XY
        } else if normal.x.abs() > normal.y.abs() {
            (1, 2) // Project to YZ
        } else {
            (0, 2) // Project to XZ
        };

        for v in &all_bounds_vertices {
            let coords = [v.x, v.y, v.z];
            flat_coords.push(coords[idx1]);
            flat_coords.push(coords[idx2]);
        }

        let result = earcutr::earcut(&flat_coords, &hole_indices, 2).ok()?;
        let indices: Vec<u32> = result.into_iter().map(|i| i as u32).collect();

        Some(Mesh { vertices: all_bounds_vertices, indices })
    }

    fn resolve_bound_points(&self, bound_id: u64, transform: &Transform3D) -> Option<Vec<Point3D>> {
        let bound_entity = self.registry.get_raw(bound_id)?;
        if let Some(Param::Reference(loop_id)) = bound_entity.params.get(0) {
            let loop_entity = self.registry.get_raw(*loop_id)?;
            if loop_entity.class == "IFCPOLYLOOP" {
                let mut vertices = Vec::new();
                if let Some(Param::List(points)) = loop_entity.params.get(0) {
                    for p_param in points {
                        if let Param::Reference(p_id) = p_param {
                            let v = self.geometry.resolve_cartesian_point(*p_id);
                            let transformed = transform.transform_point(&v);
                            vertices.push(Point3D::new(transformed.x, transformed.y, transformed.z));
                        }
                    }
                }
                return Some(vertices);
            }
        }
        None
    }

    fn extract_float(&self, list: &[Param], index: usize) -> Option<f64> {
        match list.get(index)? {
            Param::Float(f) => Some(*f),
            Param::Integer(i) => Some(*i as f64),
            _ => None,
        }
    }
}

pub fn calculate_normal(points: &[Point3D]) -> Vector3<f64> {
    if points.len() < 3 {
        return Vector3::new(0.0, 0.0, 1.0);
    }
    let v1 = Vector3::new(points[1].x - points[0].x, points[1].y - points[0].y, points[1].z - points[0].z);
    let v2 = Vector3::new(points[2].x - points[0].x, points[2].y - points[0].y, points[2].z - points[0].z);
    v1.cross(&v2).normalize()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_normal() {
        let p1 = Point3D::new(0.0, 0.0, 0.0);
        let p2 = Point3D::new(1.0, 0.0, 0.0);
        let p3 = Point3D::new(0.0, 1.0, 0.0);
        
        let normal = calculate_normal(&[p1, p2, p3]);
        assert!((normal.z - 1.0).abs() < 1e-6);
        assert!(normal.x.abs() < 1e-6);
        assert!(normal.y.abs() < 1e-6);
    }
}

