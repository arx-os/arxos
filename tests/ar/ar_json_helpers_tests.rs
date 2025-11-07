//! Tests for JSON parsing helper functions in AR integration

use arxos::ar_integration::json_helpers;
use arxos::spatial::Point3D;
use serde_json::json;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_position_valid() {
        let json = json!({
            "x": 10.5,
            "y": 20.3,
            "z": 5.7
        });

        let position = json_helpers::parse_position(&json);
        assert_eq!(position.x, 10.5);
        assert_eq!(position.y, 20.3);
        assert_eq!(position.z, 5.7);
    }

    #[test]
    fn test_parse_position_missing_keys() {
        let json = json!({
            "x": 10.0
            // y and z missing
        });

        let position = json_helpers::parse_position(&json);
        assert_eq!(position.x, 10.0);
        assert_eq!(position.y, 0.0); // Default
        assert_eq!(position.z, 0.0); // Default
    }

    #[test]
    fn test_parse_position_wrong_types() {
        let json = json!({
            "x": "not_a_number",
            "y": null,
            "z": []
        });

        let position = json_helpers::parse_position(&json);
        // Should default to 0.0 for invalid types
        assert_eq!(position.x, 0.0);
        assert_eq!(position.y, 0.0);
        assert_eq!(position.z, 0.0);
    }

    #[test]
    fn test_parse_position_empty_object() {
        let json = json!({});

        let position = json_helpers::parse_position(&json);
        assert_eq!(position.x, 0.0);
        assert_eq!(position.y, 0.0);
        assert_eq!(position.z, 0.0);
    }

    #[test]
    fn test_parse_optional_f64_present() {
        let json = json!({
            "value": 42.5
        });

        let result = json_helpers::parse_optional_f64(&json, "value", 0.0);
        assert_eq!(result, 42.5);
    }

    #[test]
    fn test_parse_optional_f64_missing() {
        let json = json!({});

        let result = json_helpers::parse_optional_f64(&json, "value", 99.9);
        assert_eq!(result, 99.9); // Should use default
    }

    #[test]
    fn test_parse_optional_f64_invalid_type() {
        let json = json!({
            "value": "not_a_number"
        });

        let result = json_helpers::parse_optional_f64(&json, "value", 99.9);
        assert_eq!(result, 99.9); // Should use default
    }

    #[test]
    fn test_parse_optional_string_present() {
        let json = json!({
            "name": "Test Equipment"
        });

        let result = json_helpers::parse_optional_string(&json, "name", "Default");
        assert_eq!(result, "Test Equipment");
    }

    #[test]
    fn test_parse_optional_string_missing() {
        let json = json!({});

        let result = json_helpers::parse_optional_string(&json, "name", "Default");
        assert_eq!(result, "Default");
    }

    #[test]
    fn test_parse_optional_string_wrong_type() {
        let json = json!({
            "name": 12345
        });

        let result = json_helpers::parse_optional_string(&json, "name", "Default");
        assert_eq!(result, "Default");
    }

    #[test]
    fn test_parse_detection_method_arkit() {
        let json = json!({
            "detectionMethod": "ARKit"
        });

        let method = json_helpers::parse_detection_method(&json);
        assert!(matches!(
            method,
            arxos::ar_integration::DetectionMethod::ARKit
        ));
    }

    #[test]
    fn test_parse_detection_method_arcore() {
        let json = json!({
            "detectionMethod": "ARCore"
        });

        let method = json_helpers::parse_detection_method(&json);
        assert!(matches!(
            method,
            arxos::ar_integration::DetectionMethod::ARCore
        ));
    }

    #[test]
    fn test_parse_detection_method_lidar() {
        let json = json!({
            "detectionMethod": "LiDAR"
        });

        let method = json_helpers::parse_detection_method(&json);
        assert!(matches!(
            method,
            arxos::ar_integration::DetectionMethod::LiDAR
        ));
    }

    #[test]
    fn test_parse_detection_method_default() {
        let json = json!({
            "detectionMethod": "unknown"
        });

        let method = json_helpers::parse_detection_method(&json);
        assert!(matches!(
            method,
            arxos::ar_integration::DetectionMethod::Manual
        ));
    }

    #[test]
    fn test_parse_detection_method_missing() {
        let json = json!({});

        let method = json_helpers::parse_detection_method(&json);
        assert!(matches!(
            method,
            arxos::ar_integration::DetectionMethod::Manual
        ));
    }

    #[test]
    fn test_parse_bounding_box() {
        let position = Point3D {
            x: 10.0,
            y: 20.0,
            z: 5.0,
        };
        let bbox = json_helpers::parse_bounding_box(&position, 0.5);

        assert_eq!(bbox.min.x, 9.5);
        assert_eq!(bbox.min.y, 19.5);
        assert_eq!(bbox.min.z, 4.5);
        assert_eq!(bbox.max.x, 10.5);
        assert_eq!(bbox.max.y, 20.5);
        assert_eq!(bbox.max.z, 5.5);
    }

    #[test]
    fn test_parse_bounding_box_custom_size() {
        let position = Point3D {
            x: 0.0,
            y: 0.0,
            z: 0.0,
        };
        let bbox = json_helpers::parse_bounding_box(&position, 2.0);

        assert_eq!(bbox.min.x, -2.0);
        assert_eq!(bbox.min.y, -2.0);
        assert_eq!(bbox.min.z, -2.0);
        assert_eq!(bbox.max.x, 2.0);
        assert_eq!(bbox.max.y, 2.0);
        assert_eq!(bbox.max.z, 2.0);
    }

    #[test]
    fn test_parse_bounding_box_from_json_with_min_max() {
        let json = json!({
            "min": { "x": 0.0, "y": 0.0, "z": 0.0 },
            "max": { "x": 10.0, "y": 20.0, "z": 5.0 }
        });

        let bbox = json_helpers::parse_bounding_box_from_json(&json, 0.5);
        assert_eq!(bbox.min.x, 0.0);
        assert_eq!(bbox.max.x, 10.0);
        assert_eq!(bbox.max.y, 20.0);
    }

    #[test]
    fn test_parse_bounding_box_from_json_with_position() {
        let json = json!({
            "position": { "x": 5.0, "y": 10.0, "z": 2.5 }
        });

        let bbox = json_helpers::parse_bounding_box_from_json(&json, 1.0);
        // Should create box around position
        assert_eq!(bbox.min.x, 4.0);
        assert_eq!(bbox.max.x, 6.0);
        assert_eq!(bbox.min.z, 1.5);
        assert_eq!(bbox.max.z, 3.5);
    }

    #[test]
    fn test_parse_bounding_box_from_json_empty() {
        let json = json!({});

        let bbox = json_helpers::parse_bounding_box_from_json(&json, 0.5);
        // Should return empty box at origin
        assert_eq!(bbox.min.x, 0.0);
        assert_eq!(bbox.max.x, 0.0);
    }
}
