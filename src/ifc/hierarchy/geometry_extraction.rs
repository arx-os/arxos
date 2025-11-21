//! Geometry and coordinate extraction from IFC entities
//!
//! Utilities for extracting coordinates, placements, and geometry from IFC entity chains.

use super::types::IFCEntity;
use std::collections::HashMap;

/// Extract coordinates from IFC placement chain
/// Follows IFCLOCALPLACEMENT -> IFCAXIS2PLACEMENT3D -> IFCCARTESIANPOINT
pub fn extract_coordinates_from_placement(
    placement_ref: &str,
    entity_map: &HashMap<String, IFCEntity>,
) -> Option<(f64, f64, f64)> {
    // Remove # prefix if present
    let ref_id = placement_ref.trim_start_matches('#').to_string();

    // Find the placement entity
    let placement_entity = entity_map.get(&ref_id)?;

    // Parse IFCLOCALPLACEMENT(#parent,#relative_placement)
    // We need the relative_placement (#21 in example)
    if placement_entity.entity_type == "IFCLOCALPLACEMENT" {
        // Extract relative placement reference from definition
        // Format: IFCLOCALPLACEMENT(#16,#21)
        if let Some(relative_ref) = extract_second_reference(&placement_entity.definition) {
            return extract_coordinates_from_axis_placement(&relative_ref, entity_map);
        }
    }

    None
}

/// Extract coordinates from IFCAXIS2PLACEMENT3D
/// Format: IFCAXIS2PLACEMENT3D(#location,#axis,#ref_dir)
pub fn extract_coordinates_from_axis_placement(
    axis_ref: &str,
    entity_map: &HashMap<String, IFCEntity>,
) -> Option<(f64, f64, f64)> {
    let ref_id = axis_ref.trim_start_matches('#').to_string();
    let axis_entity = entity_map.get(&ref_id)?;

    if axis_entity.entity_type == "IFCAXIS2PLACEMENT3D" {
        // Extract location reference (first parameter)
        // Format: IFCAXIS2PLACEMENT3D(#22,#6,#7)
        if let Some(location_ref) = extract_first_reference(&axis_entity.definition) {
            return extract_coordinates_from_point(&location_ref, entity_map);
        }
    }

    None
}

/// Extract coordinates from IFCCARTESIANPOINT
/// Format: IFCCARTESIANPOINT((x,y,z))
pub fn extract_coordinates_from_point(
    point_ref: &str,
    entity_map: &HashMap<String, IFCEntity>,
) -> Option<(f64, f64, f64)> {
    let ref_id = point_ref.trim_start_matches('#').to_string();
    let point_entity = entity_map.get(&ref_id)?;

    if point_entity.entity_type == "IFCCARTESIANPOINT" {
        // Parse coordinates from definition
        // Format: IFCCARTESIANPOINT((5.,5.,0.))
        if let Some(coords) = parse_cartesian_point(&point_entity.definition) {
            return Some(coords);
        }
    }

    None
}

/// Extract first reference from entity definition
/// Format: IFCAXIS2PLACEMENT3D(#22,#6,#7) -> #22
pub fn extract_first_reference(definition: &str) -> Option<String> {
    if let Some(start) = definition.find("(#") {
        if let Some(end) = definition[start + 2..].find(',') {
            let ref_str = &definition[start + 1..start + 2 + end];
            return Some(ref_str.to_string());
        } else if let Some(end) = definition[start + 2..].find(')') {
            let ref_str = &definition[start + 1..start + 2 + end];
            return Some(ref_str.to_string());
        }
    }
    None
}

/// Extract second reference from entity definition
/// Format: IFCLOCALPLACEMENT(#16,#21) -> #21
pub fn extract_second_reference(definition: &str) -> Option<String> {
    if let Some(first_comma) = definition.find(',') {
        if let Some(start) = definition[first_comma..].find("#") {
            let ref_start = first_comma + start;
            if let Some(end) = definition[ref_start + 1..].find(|c| [',', ')'].contains(&c)) {
                let ref_str = &definition[ref_start..ref_start + 1 + end];
                return Some(ref_str.to_string());
            }
        }
    }
    None
}

/// Extract nested reference from entity definition with nested parentheses
/// Format: IFCPRODUCTDEFINITIONSHAPE($,$,(#172)) -> #172
pub fn extract_nested_reference(definition: &str) -> Option<String> {
    // Find the nested parentheses group (need to look inside outermost parens)
    // Format: IFCPRODUCTDEFINITIONSHAPE($,$,(#172))
    // Need to find the innermost (#ref) group

    // First find the outermost opening paren
    if let Some(out_start) = definition.find('(') {
        // From there, find matching closing parens
        let mut depth = 1;
        let mut pos = out_start + 1;
        let mut inner_start = None;

        while pos < definition.len() && depth > 0 {
            match definition.chars().nth(pos) {
                Some('(') => {
                    if inner_start.is_none() {
                        inner_start = Some(pos + 1);
                    }
                    depth += 1;
                }
                Some(')') => {
                    depth -= 1;
                    if depth == 0 {
                        if let Some(start) = inner_start {
                            let nested_content = &definition[start..pos];
                            // Look for #reference in nested content
                            if let Some(ref_start) = nested_content.find('#') {
                                // Find the end of the reference
                                for i in (ref_start + 1)..nested_content.len() {
                                    if nested_content
                                        .chars()
                                        .nth(i)
                                        .is_some_and(|c| c == ',' || c == ')')
                                    {
                                        let ref_str = &nested_content[ref_start..i];
                                        return Some(ref_str.to_string());
                                    }
                                }
                            }
                        }
                    }
                }
                _ => {}
            }
            pos += 1;
        }
    }
    None
}

/// Parse coordinates from IFCCARTESIANPOINT definition
/// Format: IFCCARTESIANPOINT((5.,5.,0.)) -> (5.0, 5.0, 0.0)
pub fn parse_cartesian_point(definition: &str) -> Option<(f64, f64, f64)> {
    // Look for double parentheses: ((x,y,z))
    if let Some(start) = definition.find("((") {
        if let Some(end) = definition[start + 2..].find("))") {
            let coords_str = &definition[start + 2..start + 2 + end];
            let coords: Vec<&str> = coords_str.split(',').collect();
            if coords.len() >= 3 {
                let x = coords[0].trim().parse::<f64>().ok()?;
                let y = coords[1].trim().parse::<f64>().ok()?;
                let z = coords[2].trim().parse::<f64>().ok()?;
                return Some((x, y, z));
            }
        }
    }
    None
}

/// Parse 2D cartesian point (returns z=0.0)
/// Format: IFCCARTESIANPOINT((x,y)) -> (x, y, 0.0)
pub fn parse_cartesian_point_2d(definition: &str) -> Option<(f64, f64, f64)> {
    // Look for double parentheses: ((x,y))
    if let Some(start) = definition.find("((") {
        if let Some(end) = definition[start + 2..].find("))") {
            let coords_str = &definition[start + 2..start + 2 + end];
            let coords: Vec<&str> = coords_str.split(',').collect();
            if coords.len() >= 2 {
                let x = coords[0].trim().parse::<f64>().ok()?;
                let y = coords[1].trim().parse::<f64>().ok()?;
                return Some((x, y, 0.0));
            }
        }
    }
    None
}

/// Extract list of references from definition
/// Format: (#1,#2,#3) -> vec!["#1", "#2", "#3"]
pub fn extract_reference_list(definition: &str) -> Option<Vec<String>> {
    // Find opening parenthesis for list
    let start = definition.find('(')?;
    let end = definition.rfind(')')?;

    let list_content = &definition[start + 1..end];
    let mut references = Vec::new();

    for part in list_content.split(',') {
        let trimmed = part.trim();
        if trimmed.starts_with('#') {
            references.push(trimmed.to_string());
        }
    }

    if references.is_empty() {
        None
    } else {
        Some(references)
    }
}
