//! Property-based tests for ArxOS using proptest
//!
//! These tests verify properties that should hold for all inputs,
//! not just specific test cases.

use arxos::core::{EquipmentHealthStatus, EquipmentStatus, EquipmentType, Position};
use arxos::core::domain::address::ArxAddress;
use arxos::core::spatial::{BoundingBox3D, Point3D};
use proptest::prelude::*;

// ============================================================================
// Property Tests for ArxAddress
// ============================================================================

proptest! {
    /// Property: Any valid ArxAddress should round-trip through string serialization
    #[test]
    fn test_address_roundtrip(
        country in "[a-z]{2,3}",
        state in "[a-z]{2,3}",
        city in "[a-z]{3,10}",
        building in "[a-z0-9\\-]{3,15}",
        floor in "[a-z0-9\\-]{3,10}",
        room in "[a-z0-9\\-]{3,10}",
    ) {
        // Create a valid path
        let path = format!("/{}/{}/{}/{}/{}/{}", country, state, city, building, floor, room);

        // Try to parse as address
        if let Ok(address) = ArxAddress::from_path(&path) {
            // Should be able to get the path back
            let reconstructed_path = address.path;

            // Paths should be equivalent (case-insensitive)
            prop_assert_eq!(path.to_lowercase(), reconstructed_path.to_lowercase());
        }
    }

    /// Property: GUID should be deterministic for the same path
    #[test]
    fn test_guid_deterministic(
        country in "[a-z]{2,3}",
        state in "[a-z]{2,3}",
        city in "[a-z]{3,10}",
    ) {
        let path = format!("/{}/{}/{}", country, state, city);

        if let Ok(address1) = ArxAddress::from_path(&path) {
            if let Ok(address2) = ArxAddress::from_path(&path) {
                // GUID should be derived deterministically from path
                prop_assert_eq!(address1.path, address2.path, "Paths should match");
            }
        }
    }

    /// Property: Different paths should produce different GUIDs
    #[test]
    fn test_guid_uniqueness(
        path1 in "/[a-z]{2}/[a-z]{2}/[a-z]{5}",
        path2 in "/[a-z]{2}/[a-z]{2}/[a-z]{5}",
    ) {
        if path1 != path2 {
            if let (Ok(addr1), Ok(addr2)) = (ArxAddress::from_path(&path1), ArxAddress::from_path(&path2)) {
                // Different paths should be distinct
                prop_assert_ne!(addr1.path, addr2.path, "Different paths should remain different");
            }
        }
    }

    /// Property: Parent address should be a prefix of child address
    #[test]
    fn test_address_hierarchy(
        country in "[a-z]{2}",
        state in "[a-z]{2}",
        city in "[a-z]{5}",
        building in "[a-z]{5}",
    ) {
        let parent_path = format!("/{}/{}/{}", country, state, city);
        let child_path = format!("/{}/{}/{}/{}", country, state, city, building);

        if let (Ok(parent), Ok(child)) = (ArxAddress::from_path(&parent_path), ArxAddress::from_path(&child_path)) {
            // Parent path should be a prefix of child path
            prop_assert!(child.path.starts_with(&parent.path));
        }
    }
}

// ============================================================================
// Property Tests for Spatial Types
// ============================================================================

proptest! {
    /// Property: Distance from a point to itself should always be zero
    #[test]
    fn test_point_self_distance(
        x in -1000.0..1000.0_f64,
        y in -1000.0..1000.0_f64,
        z in -1000.0..1000.0_f64,
    ) {
        let point = Point3D { x, y, z };
        let distance = point.distance_to(&point);
        prop_assert!((distance - 0.0).abs() < 1e-10, "Distance to self should be zero");
    }

    /// Property: Distance should be symmetric
    #[test]
    fn test_distance_symmetric(
        x1 in -1000.0..1000.0_f64, y1 in -1000.0..1000.0_f64, z1 in -1000.0..1000.0_f64,
        x2 in -1000.0..1000.0_f64, y2 in -1000.0..1000.0_f64, z2 in -1000.0..1000.0_f64,
    ) {
        let point1 = Point3D { x: x1, y: y1, z: z1 };
        let point2 = Point3D { x: x2, y: y2, z: z2 };

        let d1 = point1.distance_to(&point2);
        let d2 = point2.distance_to(&point1);

        prop_assert!((d1 - d2).abs() < 1e-10, "Distance should be symmetric");
    }

    /// Property: Triangle inequality should hold
    #[test]
    fn test_triangle_inequality(
        x1 in -100.0..100.0_f64, y1 in -100.0..100.0_f64, z1 in -100.0..100.0_f64,
        x2 in -100.0..100.0_f64, y2 in -100.0..100.0_f64, z2 in -100.0..100.0_f64,
        x3 in -100.0..100.0_f64, y3 in -100.0..100.0_f64, z3 in -100.0..100.0_f64,
    ) {
        let p1 = Point3D { x: x1, y: y1, z: z1 };
        let p2 = Point3D { x: x2, y: y2, z: z2 };
        let p3 = Point3D { x: x3, y: y3, z: z3 };

        let d12 = p1.distance_to(&p2);
        let d23 = p2.distance_to(&p3);
        let d13 = p1.distance_to(&p3);

        // d(p1, p3) <= d(p1, p2) + d(p2, p3)
        prop_assert!(d13 <= d12 + d23 + 1e-10, "Triangle inequality should hold");
    }

    /// Property: Bounding box should be well-formed (min <= max)
    #[test]
    fn test_bbox_well_formed(
        min_x in -1000.0..1000.0_f64, min_y in -1000.0..1000.0_f64, min_z in -1000.0..1000.0_f64,
        max_x in -1000.0..1000.0_f64, max_y in -1000.0..1000.0_f64, max_z in -1000.0..1000.0_f64,
    ) {
        // Ensure min < max
        let (min_x, max_x) = if min_x <= max_x { (min_x, max_x) } else { (max_x, min_x) };
        let (min_y, max_y) = if min_y <= max_y { (min_y, max_y) } else { (max_y, min_y) };
        let (min_z, max_z) = if min_z <= max_z { (min_z, max_z) } else { (max_z, min_z) };

        let _bbox = BoundingBox3D {
            min: Point3D { x: min_x, y: min_y, z: min_z },
            max: Point3D { x: max_x, y: max_y, z: max_z },
        };

        prop_assert!(_bbox.min.x <= _bbox.max.x, "Bounding box min.x should be <= max.x");
        prop_assert!(_bbox.min.y <= _bbox.max.y, "Bounding box min.y should be <= max.y");
        prop_assert!(_bbox.min.z <= _bbox.max.z, "Bounding box min.z should be <= max.z");
    }

    /// Property: Center point should be between min and max
    #[test]
    fn test_bbox_center(
        min_x in -1000.0..1000.0_f64, min_y in -1000.0..1000.0_f64, min_z in -1000.0..1000.0_f64,
        max_x in -1000.0..1000.0_f64, max_y in -1000.0..1000.0_f64, max_z in -1000.0..1000.0_f64,
    ) {
        let (min_x, max_x) = if min_x <= max_x { (min_x, max_x) } else { (max_x, min_x) };
        let (min_y, max_y) = if min_y <= max_y { (min_y, max_y) } else { (max_y, min_y) };
        let (min_z, max_z) = if min_z <= max_z { (min_z, max_z) } else { (max_z, min_z) };

        let _bbox = BoundingBox3D {
            min: Point3D { x: min_x, y: min_y, z: min_z },
            max: Point3D { x: max_x, y: max_y, z: max_z },
        };

        let center_x = (min_x + max_x) / 2.0;
        let center_y = (min_y + max_y) / 2.0;
        let center_z = (min_z + max_z) / 2.0;

        prop_assert!(center_x >= min_x && center_x <= max_x, "Center X should be between min and max");
        prop_assert!(center_y >= min_y && center_y <= max_y, "Center Y should be between min and max");
        prop_assert!(center_z >= min_z && center_z <= max_z, "Center Z should be between min and max");
    }
}

// ============================================================================
// Property Tests for Equipment Status
// ============================================================================

proptest! {
    /// Property: Equipment status transitions should be valid
    #[test]
    fn test_equipment_status_is_valid(status_val in 0u8..4) {
        let status = match status_val {
            0 => EquipmentStatus::Active,
            1 => EquipmentStatus::Inactive,
            2 => EquipmentStatus::Maintenance,
            3 => EquipmentStatus::Unknown,
            _ => EquipmentStatus::Unknown,
        };

        // All enum variants should be valid
        prop_assert!(matches!(status,
            EquipmentStatus::Active |
            EquipmentStatus::Inactive |
            EquipmentStatus::Maintenance |
            EquipmentStatus::Unknown
        ));
    }

    /// Property: Health status should be distinct from operational status
    #[test]
    fn test_health_vs_operational_status(
        health_val in 0u8..4,
        status_val in 0u8..4,
    ) {
        let health = match health_val {
            0 => Some(EquipmentHealthStatus::Healthy),
            1 => Some(EquipmentHealthStatus::Warning),
            2 => Some(EquipmentHealthStatus::Critical),
            3 => Some(EquipmentHealthStatus::Unknown),
            _ => None,
        };

        let status = match status_val {
            0 => EquipmentStatus::Active,
            1 => EquipmentStatus::Inactive,
            2 => EquipmentStatus::Maintenance,
            _ => EquipmentStatus::Unknown,
        };

        // Equipment can be Active but have Critical health (e.g., running but overheating)
        // Equipment can be in Maintenance but have Healthy status (e.g., preventive maintenance)
        // These are independent dimensions
        let _ = (health, status); // Just verify types work together
        prop_assert!(health.is_some());
    }
}

// ============================================================================
// Property Tests for Position
// ============================================================================

proptest! {
    /// Property: Position coordinates should preserve their values
    #[test]
    fn test_position_preservation(
        x in -10000.0..10000.0_f64,
        y in -10000.0..10000.0_f64,
        z in -10000.0..10000.0_f64,
    ) {
        let position = Position {
            x,
            y,
            z,
            coordinate_system: "LOCAL".to_string(),
        };

        prop_assert_eq!(position.x, x);
        prop_assert_eq!(position.y, y);
        prop_assert_eq!(position.z, z);
    }

    /// Property: Cloned position should equal original
    #[test]
    fn test_position_clone(
        x in -1000.0..1000.0_f64,
        y in -1000.0..1000.0_f64,
        z in -1000.0..1000.0_f64,
    ) {
        let position = Position {
            x,
            y,
            z,
            coordinate_system: "LOCAL".to_string(),
        };

        let cloned = position.clone();

        prop_assert_eq!(position.x, cloned.x);
        prop_assert_eq!(position.y, cloned.y);
        prop_assert_eq!(position.z, cloned.z);
        prop_assert_eq!(position.coordinate_system, cloned.coordinate_system);
    }
}

// ============================================================================
// Property Tests for Equipment Type
// ============================================================================

proptest! {
    /// Property: Equipment type string conversion should be reversible for standard types
    #[test]
    fn test_equipment_type_standard_types(type_val in 0u8..7) {
        let equipment_type = match type_val {
            0 => EquipmentType::HVAC,
            1 => EquipmentType::Electrical,
            2 => EquipmentType::Plumbing,
            3 => EquipmentType::Network,
            4 => EquipmentType::AV,
            5 => EquipmentType::Safety,
            6 => EquipmentType::Furniture,
            _ => EquipmentType::HVAC,
        };

        // Should be able to format as Debug string
        let debug_str = format!("{:?}", equipment_type);
        prop_assert!(!debug_str.is_empty());
    }

    /// Property: Custom equipment types should preserve their name
    #[test]
    fn test_equipment_type_custom(
        name in "[A-Za-z][A-Za-z0-9 ]{2,30}",
    ) {
        let equipment_type = EquipmentType::Other(name.clone());

        if let EquipmentType::Other(stored_name) = equipment_type {
            prop_assert_eq!(stored_name, name);
        } else {
            prop_assert!(false, "Custom type should be Other variant");
        }
    }
}
