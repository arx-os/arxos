//! Serde helper functions for custom serialization/deserialization
//!
//! This module provides custom serialization logic for core types to maintain
//! backward compatibility with YAML format while supporting new features.

use crate::core::{BoundingBox, Equipment, EquipmentHealthStatus, EquipmentStatus, Position};
use crate::core::spatial::{BoundingBox3D, Point3D};
use crate::yaml::EquipmentStatus as YamlEquipmentStatus;
use serde::{Deserialize, Deserializer, Serialize, Serializer};

/// Serialize Equipment's status for YAML format
///
/// This function serializes the health_status field (if present) as "status" in YAML
/// for backward compatibility. If health_status is None, it falls back to mapping
/// operational status to health status.
#[allow(dead_code)]
pub fn serialize_equipment_status_for_yaml<S>(
    status: &EquipmentStatus,
    health_status: &Option<EquipmentHealthStatus>,
    serializer: S,
) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    // If health_status is set, use it directly
    if let Some(health) = health_status {
        let yaml_status = match health {
            EquipmentHealthStatus::Healthy => YamlEquipmentStatus::Healthy,
            EquipmentHealthStatus::Warning => YamlEquipmentStatus::Warning,
            EquipmentHealthStatus::Critical => YamlEquipmentStatus::Critical,
            EquipmentHealthStatus::Unknown => YamlEquipmentStatus::Unknown,
        };
        return yaml_status.serialize(serializer);
    }

    // Fallback: map operational status to health status (backward compatibility)
    let yaml_status = match status {
        EquipmentStatus::Active => YamlEquipmentStatus::Healthy,
        EquipmentStatus::Maintenance => YamlEquipmentStatus::Warning,
        EquipmentStatus::Inactive => YamlEquipmentStatus::Critical,
        EquipmentStatus::OutOfOrder => YamlEquipmentStatus::Critical,
        EquipmentStatus::Unknown => YamlEquipmentStatus::Unknown,
    };

    yaml_status.serialize(serializer)
}

/// Deserialize Equipment's status from YAML format
///
/// This function deserializes the "status" field from YAML and maps it to health_status.
/// The operational status is inferred from health status for backward compatibility.
#[allow(dead_code)]
pub fn deserialize_equipment_status_from_yaml<'de, D>(
    deserializer: D,
) -> Result<(EquipmentStatus, Option<EquipmentHealthStatus>), D::Error>
where
    D: Deserializer<'de>,
{
    let yaml_status = YamlEquipmentStatus::deserialize(deserializer)?;

    // Map YAML health status to both operational and health status
    let (operational_status, health_status) = match yaml_status {
        YamlEquipmentStatus::Healthy => (
            EquipmentStatus::Active,
            Some(EquipmentHealthStatus::Healthy),
        ),
        YamlEquipmentStatus::Warning => (
            EquipmentStatus::Maintenance,
            Some(EquipmentHealthStatus::Warning),
        ),
        YamlEquipmentStatus::Critical => (
            EquipmentStatus::Inactive,
            Some(EquipmentHealthStatus::Critical),
        ),
        YamlEquipmentStatus::Unknown => (
            EquipmentStatus::Unknown,
            Some(EquipmentHealthStatus::Unknown),
        ),
    };

    Ok((operational_status, health_status))
}

// ============================================================================
// Position ↔ Point3D Serialization
// ============================================================================

/// Serialize Position as Point3D (omitting coordinate_system)
///
/// This allows Position to serialize to the same format as Point3D in YAML,
/// while keeping the coordinate_system information in the core type.
pub fn serialize_position_as_point3d<S>(
    position: &Position,
    serializer: S,
) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    // Create Point3D from Position fields (Position has x,y,z fields directly)
    let point = Point3D::new(position.x, position.y, position.z);
    point.serialize(serializer)
}

/// Deserialize Point3D as Position (with default coordinate system)
///
/// When deserializing from YAML, we get Point3D (no coordinate system).
/// We convert it to Position with a default coordinate system.
pub fn deserialize_point3d_as_position<'de, D>(deserializer: D) -> Result<Position, D::Error>
where
    D: Deserializer<'de>,
{
    let point: Point3D = Point3D::deserialize(deserializer)?;
    Ok(Position {
        x: point.x,
        y: point.y,
        z: point.z,
        coordinate_system: "building_local".to_string(), // Default coordinate system
    })
}

// ============================================================================
// BoundingBox ↔ BoundingBox3D Serialization
// ============================================================================

/// Serialize BoundingBox as BoundingBox3D (omitting coordinate systems)
///
/// This allows BoundingBox to serialize to the same format as BoundingBox3D in YAML,
/// while keeping the coordinate system information in the core type.
pub fn serialize_bounding_box_as_bbox3d<S>(
    bbox: &BoundingBox,
    serializer: S,
) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    // bbox.min and bbox.max are Position types with x,y,z fields
    // Convert to Point3D (nalgebra Point3<f64>) for BoundingBox3D
    let bbox3d = BoundingBox3D {
        min: Point3D::new(bbox.min.x, bbox.min.y, bbox.min.z),
        max: Point3D::new(bbox.max.x, bbox.max.y, bbox.max.z),
    };
    bbox3d.serialize(serializer)
}

/// Deserialize BoundingBox3D as BoundingBox (with default coordinate system)
///
/// When deserializing from YAML, we get BoundingBox3D (no coordinate systems).
/// We convert it to BoundingBox with default coordinate systems.
pub fn deserialize_bbox3d_as_bounding_box<'de, D>(deserializer: D) -> Result<BoundingBox, D::Error>
where
    D: Deserializer<'de>,
{
    let bbox3d: BoundingBox3D = BoundingBox3D::deserialize(deserializer)?;
    let default_coord_system = "building_local".to_string();
    Ok(BoundingBox {
        min: Position {
            x: bbox3d.min.x,
            y: bbox3d.min.y,
            z: bbox3d.min.z,
            coordinate_system: default_coord_system.clone(),
        },
        max: Position {
            x: bbox3d.max.x,
            y: bbox3d.max.y,
            z: bbox3d.max.z,
            coordinate_system: default_coord_system,
        },
    })
}

// ============================================================================
// Room Equipment Serialization (Vec<Equipment> ↔ Vec<String>)
// ============================================================================

/// Serialize Room's equipment as IDs only
///
/// This allows Room's equipment field to serialize as Vec<String> (IDs) in YAML,
/// while keeping full Equipment objects in the core type.
#[allow(dead_code)]
pub fn serialize_equipment_as_ids<S>(
    equipment: &[Equipment],
    serializer: S,
) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let ids: Vec<String> = equipment.iter().map(|e| e.id.clone()).collect();
    ids.serialize(serializer)
}

/// Deserialize Room's equipment from IDs
///
/// **Note:** This function cannot fully resolve Equipment objects from IDs without
/// building context. It returns an empty Vec and equipment should be populated
/// separately using building data. This is a limitation of the current architecture
/// where equipment is stored at floor level in YAML but in rooms in core.
#[allow(dead_code)]
pub fn deserialize_equipment_from_ids<'de, D>(deserializer: D) -> Result<Vec<Equipment>, D::Error>
where
    D: Deserializer<'de>,
{
    // Deserialize as IDs
    let _ids: Vec<String> = Vec::<String>::deserialize(deserializer)?;

    // Return empty Vec - equipment will be populated separately from building data
    // This is because equipment is stored at floor level in YAML, not in rooms
    Ok(Vec::new())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json;

    #[test]
    fn test_serialize_health_status_priority() {
        // When health_status is set, it should be used
        let status = EquipmentStatus::Active;
        let health_status = Some(EquipmentHealthStatus::Warning);

        let serialized =
            serde_json::to_string(&yaml_status_from_core(&status, &health_status)).unwrap();
        assert!(serialized.contains("Warning"));
    }

    #[test]
    fn test_serialize_fallback_to_operational() {
        // When health_status is None, fall back to operational status mapping
        let status = EquipmentStatus::Maintenance;
        let health_status = None;

        let serialized =
            serde_json::to_string(&yaml_status_from_core(&status, &health_status)).unwrap();
        assert!(serialized.contains("Warning")); // Maintenance -> Warning
    }

    // Helper function for testing
    fn yaml_status_from_core(
        status: &EquipmentStatus,
        health_status: &Option<EquipmentHealthStatus>,
    ) -> YamlEquipmentStatus {
        if let Some(health) = health_status {
            match health {
                EquipmentHealthStatus::Healthy => YamlEquipmentStatus::Healthy,
                EquipmentHealthStatus::Warning => YamlEquipmentStatus::Warning,
                EquipmentHealthStatus::Critical => YamlEquipmentStatus::Critical,
                EquipmentHealthStatus::Unknown => YamlEquipmentStatus::Unknown,
            }
        } else {
            match status {
                EquipmentStatus::Active => YamlEquipmentStatus::Healthy,
                EquipmentStatus::Maintenance => YamlEquipmentStatus::Warning,
                EquipmentStatus::Inactive => YamlEquipmentStatus::Critical,
                EquipmentStatus::OutOfOrder => YamlEquipmentStatus::Critical,
                EquipmentStatus::Unknown => YamlEquipmentStatus::Unknown,
            }
        }
    }

    // ============================================================================
    // Position Serialization Tests
    // ============================================================================

    #[test]
    fn test_serialize_position_as_point3d() {
        let position = Position {
            x: 10.5,
            y: 20.5,
            z: 30.5,
            coordinate_system: "world".to_string(),
        };

        let json = serde_json::to_string(&position).unwrap();

        // Should serialize as Point3D (x, y, z only, no coordinate_system)
        assert!(json.contains("10.5"));
        assert!(json.contains("20.5"));
        assert!(json.contains("30.5"));
        assert!(!json.contains("coordinate_system")); // Should not include coordinate_system
        assert!(!json.contains("world")); // Should not include coordinate system value
    }

    #[test]
    fn test_deserialize_point3d_as_position() {
        // Point3D JSON (no coordinate_system)
        let json = r#"{"x":10.5,"y":20.5,"z":30.5}"#;

        let position: Position = serde_json::from_str(json).unwrap();

        assert_eq!(position.x, 10.5);
        assert_eq!(position.y, 20.5);
        assert_eq!(position.z, 30.5);
        assert_eq!(position.coordinate_system, "building_local"); // Default coordinate system
    }

    #[test]
    fn test_position_round_trip() {
        let original = Position {
            x: 15.0,
            y: 25.0,
            z: 35.0,
            coordinate_system: "custom_system".to_string(),
        };

        // Serialize to JSON
        let json = serde_json::to_string(&original).unwrap();

        // Deserialize back
        let round_tripped: Position = serde_json::from_str(&json).unwrap();

        // Coordinates should match
        assert_eq!(round_tripped.x, original.x);
        assert_eq!(round_tripped.y, original.y);
        assert_eq!(round_tripped.z, original.z);

        // Coordinate system will be default (building_local) after round-trip
        // This is expected behavior - coordinate_system is not serialized
        assert_eq!(round_tripped.coordinate_system, "building_local");
    }

    // ============================================================================
    // BoundingBox Serialization Tests
    // ============================================================================

    #[test]
    fn test_serialize_bounding_box_as_bbox3d() {
        let bbox = BoundingBox {
            min: Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "world".to_string(),
            },
            max: Position {
                x: 10.0,
                y: 20.0,
                z: 30.0,
                coordinate_system: "world".to_string(),
            },
        };

        let json = serde_json::to_string(&bbox).unwrap();

        // Should serialize as BoundingBox3D (min/max with x, y, z only)
        assert!(json.contains("min"));
        assert!(json.contains("max"));
        assert!(json.contains("0.0"));
        assert!(json.contains("10.0"));
        assert!(json.contains("20.0"));
        assert!(json.contains("30.0"));
        assert!(!json.contains("coordinate_system")); // Should not include coordinate_system
    }

    #[test]
    fn test_deserialize_bbox3d_as_bounding_box() {
        // BoundingBox3D JSON (no coordinate systems)
        let json = r#"{"min":{"x":0.0,"y":0.0,"z":0.0},"max":{"x":10.0,"y":20.0,"z":30.0}}"#;

        let bbox: BoundingBox = serde_json::from_str(json).unwrap();

        assert_eq!(bbox.min.x, 0.0);
        assert_eq!(bbox.min.y, 0.0);
        assert_eq!(bbox.min.z, 0.0);
        assert_eq!(bbox.max.x, 10.0);
        assert_eq!(bbox.max.y, 20.0);
        assert_eq!(bbox.max.z, 30.0);

        // Coordinate systems should default to "building_local"
        assert_eq!(bbox.min.coordinate_system, "building_local");
        assert_eq!(bbox.max.coordinate_system, "building_local");
    }

    #[test]
    fn test_bounding_box_round_trip() {
        let original = BoundingBox {
            min: Position {
                x: 5.0,
                y: 10.0,
                z: 15.0,
                coordinate_system: "custom_system".to_string(),
            },
            max: Position {
                x: 15.0,
                y: 20.0,
                z: 25.0,
                coordinate_system: "custom_system".to_string(),
            },
        };

        // Serialize to JSON
        let json = serde_json::to_string(&original).unwrap();

        // Deserialize back
        let round_tripped: BoundingBox = serde_json::from_str(&json).unwrap();

        // Coordinates should match
        assert_eq!(round_tripped.min.x, original.min.x);
        assert_eq!(round_tripped.min.y, original.min.y);
        assert_eq!(round_tripped.min.z, original.min.z);
        assert_eq!(round_tripped.max.x, original.max.x);
        assert_eq!(round_tripped.max.y, original.max.y);
        assert_eq!(round_tripped.max.z, original.max.z);

        // Coordinate systems will be default (building_local) after round-trip
        // This is expected behavior - coordinate_system is not serialized
        assert_eq!(round_tripped.min.coordinate_system, "building_local");
        assert_eq!(round_tripped.max.coordinate_system, "building_local");
    }
}
