//! IFC geometry utilities for resolving placements and transforms.
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use nalgebra::{Matrix3, Vector3};

use crate::core::spatial::Point3D;

use super::fallback::IFCEntity;

pub(crate) fn parameters_from_definition(definition: &str) -> Vec<String> {
    let mut params = Vec::new();
    let start = match definition.find('(') {
        Some(idx) => idx + 1,
        None => return params,
    };

    let mut depth = 0i32;
    let mut current = String::new();
    let chars: Vec<char> = definition[start..].chars().collect();

    for ch in chars {
        match ch {
            '(' => {
                depth += 1;
                current.push(ch);
            }
            ')' => {
                if depth == 0 {
                    if !current.trim().is_empty() {
                        params.push(current.trim().to_string());
                    }
                    break;
                } else {
                    depth -= 1;
                    current.push(ch);
                }
            }
            ',' => {
                if depth == 0 {
                    params.push(current.trim().to_string());
                    current.clear();
                } else {
                    current.push(ch);
                }
            }
            _ => current.push(ch),
        }
    }

    params
}

pub(crate) fn extract_reference_id(param: &str) -> Option<String> {
    let trimmed = param.trim();
    if trimmed.starts_with('#') {
        Some(trimmed.trim_start_matches('#').to_string())
    } else {
        None
    }
}

#[derive(Clone, Debug)]
pub struct Transform3D {
    pub translation: Vector3<f64>,
    pub rotation: Matrix3<f64>,
}

impl Transform3D {
    pub fn identity() -> Self {
        Self {
            translation: Vector3::new(0.0, 0.0, 0.0),
            rotation: Matrix3::identity(),
        }
    }

    fn compose(&self, other: &Transform3D) -> Transform3D {
        let translation = self.translation + self.rotation * other.translation;
        let rotation = self.rotation * other.rotation;
        Transform3D {
            translation,
            rotation,
        }
    }

    pub fn transform_point(&self, point: &Vector3<f64>) -> Vector3<f64> {
        self.translation + self.rotation * point
    }

    pub fn rotate_vector(&self, vector: &Vector3<f64>) -> Vector3<f64> {
        self.rotation * vector
    }

    pub fn to_point(&self) -> Point3D {
        Point3D::new(self.translation.x, self.translation.y, self.translation.z)
    }
}

#[derive(Clone)]
pub struct PlacementResolver {
    entities: Arc<HashMap<String, IFCEntity>>,
    transform_cache: Arc<Mutex<HashMap<String, Transform3D>>>,
}

impl PlacementResolver {
    pub fn new(entities: &[IFCEntity]) -> Self {
        let mut map = HashMap::with_capacity(entities.len());
        for entity in entities {
            map.insert(entity.id.clone(), entity.clone());
        }
        Self {
            entities: Arc::new(map),
            transform_cache: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn from_map(map: HashMap<String, IFCEntity>) -> Self {
        Self {
            entities: Arc::new(map),
            transform_cache: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn resolve_entity_transform(&self, entity: &IFCEntity) -> Option<Transform3D> {
        let params = parameters_from_definition(&entity.definition);
        for param in params {
            if let Some(reference) = extract_reference_id(&param) {
                if let Some(target) = self.entities.get(&reference) {
                    if target.entity_type == "IFCLOCALPLACEMENT" {
                        return self.resolve_local_placement(&reference);
                    }
                }
            }
        }
        None
    }

    pub fn resolve_local_placement(&self, reference: &str) -> Option<Transform3D> {
        let id = reference.trim_start_matches('#').to_string();

        {
            let cache = self.transform_cache.lock().unwrap();
            if let Some(existing) = cache.get(&id) {
                return Some(existing.clone());
            }
        }

        let entity = self.entities.get(&id)?;
        if entity.entity_type != "IFCLOCALPLACEMENT" {
            return None;
        }

        let params = parameters_from_definition(&entity.definition);
        let parent_ref = params.first().map(|s| s.as_str()).unwrap_or("$");
        let relative_ref = params.get(1).map(|s| s.as_str()).unwrap_or("$");

        let parent_transform = if parent_ref != "$" {
            self.resolve_local_placement(parent_ref)?
        } else {
            Transform3D::identity()
        };

        let relative_transform = if relative_ref != "$" {
            self.resolve_axis_placement(relative_ref)?
        } else {
            Transform3D::identity()
        };

        let composed = parent_transform.compose(&relative_transform);

        let mut cache = self.transform_cache.lock().unwrap();
        cache.insert(id, composed.clone());

        Some(composed)
    }

    pub fn resolve_axis_transform(&self, reference: &str) -> Option<Transform3D> {
        self.resolve_axis_placement(reference)
    }

    pub fn compute_entity_bounding_box(
        &self,
        entity: &IFCEntity,
    ) -> Option<(Vector3<f64>, Vector3<f64>)> {
        let representation_ids = self.collect_shape_references(entity);
        if representation_ids.is_empty() {
            return None;
        }

        let entity_transform = self.resolve_entity_transform(entity);
        let mut all_points: Vec<Vector3<f64>> = Vec::new();

        for shape_id in representation_ids {
            let points = self.collect_points_from_shape(&shape_id);
            if points.is_empty() {
                continue;
            }
            if let Some(ref transform) = entity_transform {
                for point in points {
                    all_points.push(transform.transform_point(&point));
                }
            } else {
                all_points.extend(points);
            }
        }

        if all_points.is_empty() {
            None
        } else {
            Some(compute_bounds(&all_points))
        }
    }

    fn resolve_axis_placement(&self, reference: &str) -> Option<Transform3D> {
        let id = reference.trim_start_matches('#');
        let entity = self.entities.get(id)?;

        match entity.entity_type.as_str() {
            "IFCAXIS2PLACEMENT3D" => self.resolve_axis2placement3d(entity),
            "IFCAXIS2PLACEMENT2D" => self.resolve_axis2placement2d(entity),
            _ => None,
        }
    }

    fn resolve_axis2placement3d(&self, entity: &IFCEntity) -> Option<Transform3D> {
        let params = parameters_from_definition(&entity.definition);
        let location_ref = params.first()?.as_str();
        let axis_ref = params.get(1).map(|s| s.as_str()).filter(|s| *s != "$");
        let ref_dir_ref = params.get(2).map(|s| s.as_str()).filter(|s| *s != "$");

        let location = self.resolve_cartesian_point(location_ref)?;
        let axis_dir = axis_ref
            .and_then(|r| self.resolve_direction(r))
            .unwrap_or(Vector3::new(0.0, 0.0, 1.0));
        let ref_dir = ref_dir_ref
            .and_then(|r| self.resolve_direction(r))
            .unwrap_or(Vector3::new(1.0, 0.0, 0.0));

        let rotation = build_rotation_matrix(&axis_dir, &ref_dir);

        Some(Transform3D {
            translation: location,
            rotation,
        })
    }

    fn resolve_axis2placement2d(&self, entity: &IFCEntity) -> Option<Transform3D> {
        let params = parameters_from_definition(&entity.definition);
        let location_ref = params.first()?.as_str();
        let ref_dir_ref = params.get(1).map(|s| s.as_str()).filter(|s| *s != "$");

        let location = self.resolve_cartesian_point(location_ref)?;
        let ref_dir = ref_dir_ref
            .and_then(|r| self.resolve_direction(r))
            .unwrap_or(Vector3::new(1.0, 0.0, 0.0));

        let rotation = build_rotation_matrix(&Vector3::new(0.0, 0.0, 1.0), &ref_dir);

        Some(Transform3D {
            translation: location,
            rotation,
        })
    }

    fn resolve_cartesian_point(&self, reference: &str) -> Option<Vector3<f64>> {
        let id = reference.trim_start_matches('#');
        let entity = self.entities.get(id)?;
        if entity.entity_type != "IFCCARTESIANPOINT" {
            return None;
        }

        let coords = extract_numeric_values(&entity.definition);
        let x = coords.first().copied().unwrap_or(0.0);
        let y = coords.get(1).copied().unwrap_or(0.0);
        let z = coords.get(2).copied().unwrap_or(0.0);

        Some(Vector3::new(x, y, z))
    }

    fn resolve_direction(&self, reference: &str) -> Option<Vector3<f64>> {
        let id = reference.trim_start_matches('#');
        let entity = self.entities.get(id)?;
        if entity.entity_type != "IFCDIRECTION" {
            return None;
        }

        let coords = extract_numeric_values(&entity.definition);
        let x = coords.first().copied().unwrap_or(1.0);
        let y = coords.get(1).copied().unwrap_or(0.0);
        let z = coords.get(2).copied().unwrap_or(0.0);

        let vector = Vector3::new(x, y, z);
        let magnitude = vector.norm();
        if magnitude == 0.0 {
            None
        } else {
            Some(vector / magnitude)
        }
    }



    fn collect_shape_references(&self, entity: &IFCEntity) -> Vec<String> {
        let mut references = Vec::new();
        for param in parameters_from_definition(&entity.definition) {
            if let Some(reference) = extract_reference_id(&param) {
                if let Some(shape) = self.entities.get(&reference) {
                    if shape.entity_type == "IFCPRODUCTDEFINITIONSHAPE" {
                        let reps = extract_all_references(&shape.definition);
                        for rep in reps {
                            if let Some(rep_entity) = self.entities.get(&rep) {
                                if rep_entity.entity_type == "IFCSHAPEREPRESENTATION" {
                                    references.push(rep);
                                }
                            }
                        }
                    }
                }
            }
        }
        references
    }

    fn collect_points_from_shape(&self, shape_id: &str) -> Vec<Vector3<f64>> {
        let mut points = Vec::new();
        let shape = match self.entities.get(shape_id) {
            Some(entity) => entity,
            None => return points,
        };

        let item_refs = extract_all_references(&shape.definition);
        for item_ref in item_refs {
            if let Some(item_entity) = self.entities.get(&item_ref) {
                if item_entity.entity_type.as_str() == "IFCEXTRUDEDAREASOLID" {
                    points.extend(self.collect_points_from_extruded_area_solid(item_entity))
                }
            }
        }

        points
    }

    fn collect_points_from_extruded_area_solid(
        &self,
        solid: &IFCEntity,
    ) -> Vec<Vector3<f64>> {
        let params = parameters_from_definition(&solid.definition);
        if params.len() < 4 {
            return Vec::new();
        }

        let profile_ref = params[0].as_str();
        let placement_ref = params[1].as_str();
        let direction_ref = params[2].as_str();
        let depth_value = parse_float(params[3].as_str());

        let depth = match depth_value {
            Some(value) if value != 0.0 => value,
            _ => return Vec::new(),
        };

        let mut profile_points = self.collect_profile_points(profile_ref);
        if profile_points.is_empty() {
            return Vec::new();
        }

        let profile_transform = if placement_ref != "$" {
            self.resolve_axis_transform(placement_ref)
                .unwrap_or_else(Transform3D::identity)
        } else {
            Transform3D::identity()
        };

        let direction = if direction_ref != "$" {
            self.resolve_direction(direction_ref)
                .unwrap_or(Vector3::new(0.0, 0.0, 1.0))
        } else {
            Vector3::new(0.0, 0.0, 1.0)
        };

        let extrude_direction = profile_transform.rotate_vector(&direction);
        let extrusion = extrude_direction * depth;

        let mut result = Vec::new();
        for point in profile_points.drain(..) {
            let base = profile_transform.transform_point(&point);
            result.push(base);
            result.push(base + extrusion);
        }

        result
    }

    fn collect_profile_points(&self, reference: &str) -> Vec<Vector3<f64>> {
        let id = reference.trim_start_matches('#');
        let profile = match self.entities.get(id) {
            Some(entity) => entity,
            None => return Vec::new(),
        };

        match profile.entity_type.as_str() {
            "IFCARBITRARYCLOSEDPROFILEDEF" => self.collect_points_from_arbitrary_profile(profile),
            "IFCRECTANGLEPROFILEDEF" => self.collect_points_from_rectangle_profile(profile),
            _ => Vec::new(),
        }
    }

    fn collect_points_from_arbitrary_profile(&self, profile: &IFCEntity) -> Vec<Vector3<f64>> {
        let params = parameters_from_definition(&profile.definition);
        if params.len() < 2 {
            return Vec::new();
        }

        let polyline_ref = params[1].as_str();
        let id = polyline_ref.trim_start_matches('#');
        let polyline = match self.entities.get(id) {
            Some(entity) if entity.entity_type == "IFCPOLYLINE" => entity,
            _ => return Vec::new(),
        };

        let point_refs = extract_all_references(&polyline.definition);
        let mut points = Vec::new();
        for point_ref in point_refs {
            if let Some(point) = self.resolve_cartesian_point(&format!("#{}", point_ref)) {
                points.push(point);
            }
        }
        points
    }

    fn collect_points_from_rectangle_profile(&self, profile: &IFCEntity) -> Vec<Vector3<f64>> {
        let params = parameters_from_definition(&profile.definition);
        if params.len() < 5 {
            return Vec::new();
        }

        let position_ref = params[2].as_str();
        let width = match parse_float(params[3].as_str()) {
            Some(v) => v,
            None => return Vec::new(),
        };
        let height = match parse_float(params[4].as_str()) {
            Some(v) => v,
            None => return Vec::new(),
        };

        let half_w = width / 2.0;
        let half_h = height / 2.0;

        let mut points = vec![
            Vector3::new(half_w, half_h, 0.0),
            Vector3::new(-half_w, half_h, 0.0),
            Vector3::new(-half_w, -half_h, 0.0),
            Vector3::new(half_w, -half_h, 0.0),
        ];

        if position_ref != "$" {
            if let Some(transform) = self.resolve_axis_transform(position_ref) {
                points = points
                    .into_iter()
                    .map(|point| transform.transform_point(&point))
                    .collect();
            }
        }

        points
    }
}

fn extract_numeric_values(definition: &str) -> Vec<f64> {
    let mut values = Vec::new();
    let mut buf = String::new();
    let mut inside_number = false;

    for ch in definition.chars() {
        match ch {
            '-' | '+' | '.' | '0'..='9' | 'E' | 'e' => {
                buf.push(ch);
                inside_number = true;
            }
            _ => {
                if inside_number {
                    if let Ok(value) = buf.parse::<f64>() {
                        values.push(value);
                    }
                    buf.clear();
                    inside_number = false;
                }
            }
        }
    }

    if inside_number {
        if let Ok(value) = buf.parse::<f64>() {
            values.push(value);
        }
    }

    values
}

fn build_rotation_matrix(axis_dir: &Vector3<f64>, ref_dir: &Vector3<f64>) -> Matrix3<f64> {
    let z_axis = normalize_or_default(axis_dir, Vector3::new(0.0, 0.0, 1.0));
    let mut x_axis = normalize_or_default(ref_dir, Vector3::new(1.0, 0.0, 0.0));

    // Ensure x axis is orthogonal to z axis.
    x_axis = (x_axis - (z_axis.dot(&x_axis) * z_axis)).normalize();

    let y_axis = z_axis.cross(&x_axis);

    Matrix3::from_columns(&[x_axis, y_axis, z_axis])
}

fn normalize_or_default(vector: &Vector3<f64>, default: Vector3<f64>) -> Vector3<f64> {
    let norm = vector.norm();
    if norm == 0.0 {
        default
    } else {
        vector / norm
    }
}

fn parse_float(value: &str) -> Option<f64> {
    let trimmed = value.trim().trim_matches('\'');
    trimmed.parse::<f64>().ok()
}

pub(crate) fn extract_all_references(definition: &str) -> Vec<String> {
    let mut refs = Vec::new();
    let mut chars = definition.chars().peekable();
    while let Some(ch) = chars.next() {
        if ch == '#' {
            let mut id = String::new();
            while let Some(peek) = chars.peek() {
                if peek.is_ascii_digit() {
                    id.push(*peek);
                    chars.next();
                } else {
                    break;
                }
            }
            if !id.is_empty() {
                refs.push(id);
            }
        }
    }
    refs
}

fn compute_bounds(points: &[Vector3<f64>]) -> (Vector3<f64>, Vector3<f64>) {
    let mut min = points[0];
    let mut max = points[0];

    for point in points.iter().skip(1) {
        min.x = min.x.min(point.x);
        min.y = min.y.min(point.y);
        min.z = min.z.min(point.z);

        max.x = max.x.max(point.x);
        max.y = max.y.max(point.y);
        max.z = max.z.max(point.z);
    }

    (min, max)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn entity(id: &str, entity_type: &str, definition: &str) -> IFCEntity {
        IFCEntity {
            id: id.to_string(),
            entity_type: entity_type.to_string(),
            name: "".to_string(),
            definition: definition.to_string(),
        }
    }

    #[test]
    fn resolves_simple_local_placement() {
        let entities = vec![
            entity("10", "IFCCARTESIANPOINT", "IFCCARTESIANPOINT((0.,0.,0.))"),
            entity("11", "IFCAXIS2PLACEMENT3D", "IFCAXIS2PLACEMENT3D(#10,$,$)"),
            entity("12", "IFCLOCALPLACEMENT", "IFCLOCALPLACEMENT($,#11)"),
            entity(
                "20",
                "IFCSPACE",
                "IFCSPACE('Room',$,#12,$,#25,$,$,.ELEMENT.,0.)",
            ),
        ];

        let resolver = PlacementResolver::new(&entities);
        let room = entities.iter().find(|e| e.id == "20").unwrap();
        let transform = resolver.resolve_entity_transform(room).unwrap();
        assert_eq!(transform.translation, Vector3::new(0.0, 0.0, 0.0));
        assert_eq!(transform.rotation, Matrix3::identity());
    }

    #[test]
    fn resolves_nested_local_placement_with_translation() {
        let entities = vec![
            entity("1", "IFCCARTESIANPOINT", "IFCCARTESIANPOINT((10.,0.,0.))"),
            entity("2", "IFCAXIS2PLACEMENT3D", "IFCAXIS2PLACEMENT3D(#1,$,$)"),
            entity("3", "IFCLOCALPLACEMENT", "IFCLOCALPLACEMENT($,#2)"),
            entity("4", "IFCCARTESIANPOINT", "IFCCARTESIANPOINT((0.,5.,0.))"),
            entity("5", "IFCAXIS2PLACEMENT3D", "IFCAXIS2PLACEMENT3D(#4,$,$)"),
            entity("6", "IFCLOCALPLACEMENT", "IFCLOCALPLACEMENT(#3,#5)"),
            entity(
                "7",
                "IFCFLOWTERMINAL",
                "IFCFLOWTERMINAL('Eq',$,#6,$,#40,$,$,.ELEMENT.,$)",
            ),
        ];

        let resolver = PlacementResolver::new(&entities);
        let equipment = entities.iter().find(|e| e.id == "7").unwrap();
        let transform = resolver.resolve_entity_transform(equipment).unwrap();
        assert_eq!(
            transform.translation,
            Vector3::new(10.0, 5.0, 0.0)
        );
    }

    #[test]
    fn computes_bounding_box_for_extruded_solid() {
        let entities = vec![
            entity("1", "IFCCARTESIANPOINT", "IFCCARTESIANPOINT((0.,0.,0.))"),
            entity("2", "IFCCARTESIANPOINT", "IFCCARTESIANPOINT((4.,0.,0.))"),
            entity("3", "IFCCARTESIANPOINT", "IFCCARTESIANPOINT((4.,3.,0.))"),
            entity("4", "IFCCARTESIANPOINT", "IFCCARTESIANPOINT((0.,3.,0.))"),
            entity("5", "IFCPOLYLINE", "IFCPOLYLINE((#1,#2,#3,#4,#1))"),
            entity(
                "6",
                "IFCARBITRARYCLOSEDPROFILEDEF",
                "IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$, #5)",
            ),
            entity("7", "IFCAXIS2PLACEMENT3D", "IFCAXIS2PLACEMENT3D(#1,$,$)"),
            entity("8", "IFCDIRECTION", "IFCDIRECTION((0.,0.,1.))"),
            entity(
                "9",
                "IFCEXTRUDEDAREASOLID",
                "IFCEXTRUDEDAREASOLID(#6,#7,#8,3.)",
            ),
            entity(
                "10",
                "IFCSHAPEREPRESENTATION",
                "IFCSHAPEREPRESENTATION($,$,(#9))",
            ),
            entity(
                "11",
                "IFCPRODUCTDEFINITIONSHAPE",
                "IFCPRODUCTDEFINITIONSHAPE($,$,(#10))",
            ),
            entity(
                "12",
                "IFCSPACE",
                "IFCSPACE('Room',$,$,$,#11,$,$,.ELEMENT.,0.)",
            ),
        ];

        let resolver = PlacementResolver::new(&entities);
        let room = entities.iter().find(|e| e.id == "12").unwrap();
        let bbox = resolver.compute_entity_bounding_box(room).unwrap();
        assert!((bbox.0.x - 0.0).abs() < 1e-6);
        assert!((bbox.0.y - 0.0).abs() < 1e-6);
        assert!((bbox.0.z - 0.0).abs() < 1e-6);
        assert!((bbox.1.x - 4.0).abs() < 1e-6);
        assert!((bbox.1.y - 3.0).abs() < 1e-6);
        assert!((bbox.1.z - 3.0).abs() < 1e-6);
    }
}

