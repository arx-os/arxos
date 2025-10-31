//! JSON parsing helper functions for AR integration
//!
//! This module provides reusable helper functions to reduce code duplication
//! when parsing JSON data from mobile AR applications.

use crate::spatial::{Point3D, BoundingBox3D};
use crate::ar_integration::DetectionMethod;
use serde_json::Value;

/// Parse a Point3D from JSON object with x, y, z keys
///
/// # Arguments
///
/// * `json` - JSON Value containing position data
///
/// # Returns
///
/// Point3D with parsed coordinates, using 0.0 as default for missing values
pub fn parse_position(json: &Value) -> Point3D {
    Point3D {
        x: parse_optional_f64(json, "x", 0.0),
        y: parse_optional_f64(json, "y", 0.0),
        z: parse_optional_f64(json, "z", 0.0),
    }
}

/// Parse an optional f64 value from JSON with a default
///
/// # Arguments
///
/// * `json` - JSON Value to extract from
/// * `key` - Key to look up
/// * `default` - Default value if key is missing or invalid
///
/// # Returns
///
/// Parsed f64 value or default
pub fn parse_optional_f64(json: &Value, key: &str, default: f64) -> f64 {
    json.get(key)
        .and_then(|v| v.as_f64())
        .unwrap_or(default)
}

/// Parse an optional string value from JSON with a default
///
/// # Arguments
///
/// * `json` - JSON Value to extract from
/// * `key` - Key to look up
/// * `default` - Default string if key is missing or invalid
///
/// # Returns
///
/// Parsed string value or default
pub fn parse_optional_string(json: &Value, key: &str, default: &str) -> String {
    json.get(key)
        .and_then(|v| v.as_str())
        .unwrap_or(default)
        .to_string()
}

/// Parse DetectionMethod from JSON string
///
/// # Arguments
///
/// * `json` - JSON Value containing detectionMethod field
///
/// # Returns
///
/// DetectionMethod enum variant, defaults to Manual if invalid
pub fn parse_detection_method(json: &Value) -> DetectionMethod {
    match parse_optional_string(json, "detectionMethod", "unknown").as_str() {
        "ARKit" => DetectionMethod::ARKit,
        "ARCore" => DetectionMethod::ARCore,
        "LiDAR" => DetectionMethod::LiDAR,
        "Manual" => DetectionMethod::Manual,
        "AI" => DetectionMethod::AI,
        _ => DetectionMethod::Manual,
    }
}

/// Create a BoundingBox3D from a position with default size
///
/// # Arguments
///
/// * `position` - Center point for the bounding box
/// * `default_size` - Half-size in each direction (default: 0.5)
///
/// # Returns
///
/// BoundingBox3D centered on position
pub fn parse_bounding_box(position: &Point3D, default_size: f64) -> BoundingBox3D {
    BoundingBox3D {
        min: Point3D {
            x: position.x - default_size,
            y: position.y - default_size,
            z: position.z - default_size,
        },
        max: Point3D {
            x: position.x + default_size,
            y: position.y + default_size,
            z: position.z + default_size,
        },
    }
}

/// Parse a BoundingBox3D from JSON with min and max points
///
/// # Arguments
///
/// * `json` - JSON Value containing bounding box data
/// * `default_size` - Default size if min/max not present (uses position if available)
///
/// # Returns
///
/// BoundingBox3D parsed from JSON or default box if parsing fails
pub fn parse_bounding_box_from_json(json: &Value, default_size: f64) -> BoundingBox3D {
    if let (Some(min_json), Some(max_json)) = (json.get("min"), json.get("max")) {
        BoundingBox3D {
            min: parse_position(min_json),
            max: parse_position(max_json),
        }
    } else if let Some(pos_json) = json.get("position") {
        // Fallback: create box from position
        let position = parse_position(pos_json);
        parse_bounding_box(&position, default_size)
    } else {
        // Ultimate fallback: empty box at origin
        BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 0.0, y: 0.0, z: 0.0 },
        }
    }
}

