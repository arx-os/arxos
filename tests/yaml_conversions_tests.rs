//! Tests for YAML conversion functions
//!
//! These tests verify that conversion between core types and YAML types
//! works correctly, especially with the new health_status field.

#![allow(deprecated)]

use arxos::core::{Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType, Position};
use arxos::yaml::conversions::{equipment_data_to_equipment, equipment_to_equipment_data};
use arxos::yaml::{EquipmentData, EquipmentStatus as YamlEquipmentStatus};
use std::collections::HashMap;

/// Create a test equipment with specified status and health_status
fn create_test_equipment(
    status: EquipmentStatus,
    health_status: Option<EquipmentHealthStatus>,
) -> Equipment {
    Equipment {
        id: "test-equipment-001".to_string(),
        name: "Test Equipment".to_string(),
        path: "/equipment/test-equipment-001".to_string(),
        address: None,
        equipment_type: EquipmentType::HVAC,
        position: Position {
            x: 10.0,
            y: 20.0,
            z: 3.0,
            coordinate_system: "building_local".to_string(),
        },
        properties: HashMap::new(),
        status,
        health_status,
        room_id: None,
        sensor_mappings: None,
    }
}

#[test]
fn test_equipment_to_equipment_data_with_health_status() {
    // Test that health_status is used when present
    let equipment = create_test_equipment(
        EquipmentStatus::Active,
        Some(EquipmentHealthStatus::Warning),
    );

    let equipment_data = equipment_to_equipment_data(&equipment);

    // Should use health_status (Warning) instead of mapping from status
    assert_eq!(equipment_data.status, YamlEquipmentStatus::Warning);
    assert_eq!(equipment_data.id, "test-equipment-001");
    assert_eq!(equipment_data.name, "Test Equipment");
}

#[test]
fn test_equipment_to_equipment_data_without_health_status() {
    // Test backward compatibility: when health_status is None, should map from status
    let equipment = create_test_equipment(EquipmentStatus::Maintenance, None);

    let equipment_data = equipment_to_equipment_data(&equipment);

    // Should map Maintenance -> Warning
    assert_eq!(equipment_data.status, YamlEquipmentStatus::Warning);
}

#[test]
fn test_equipment_to_equipment_data_all_health_status_variants() {
    // Test all health_status variants are correctly serialized
    let test_cases = vec![
        (EquipmentHealthStatus::Healthy, YamlEquipmentStatus::Healthy),
        (EquipmentHealthStatus::Warning, YamlEquipmentStatus::Warning),
        (
            EquipmentHealthStatus::Critical,
            YamlEquipmentStatus::Critical,
        ),
        (EquipmentHealthStatus::Unknown, YamlEquipmentStatus::Unknown),
    ];

    for (health_status, expected_yaml_status) in test_cases {
        let equipment = create_test_equipment(EquipmentStatus::Active, Some(health_status));

        let equipment_data = equipment_to_equipment_data(&equipment);
        assert_eq!(
            equipment_data.status, expected_yaml_status,
            "Failed for health_status: {:?}",
            health_status
        );
    }
}

#[test]
fn test_equipment_to_equipment_data_all_operational_status_fallbacks() {
    // Test all operational status variants fallback correctly when health_status is None
    let test_cases = vec![
        (EquipmentStatus::Active, YamlEquipmentStatus::Healthy),
        (EquipmentStatus::Maintenance, YamlEquipmentStatus::Warning),
        (EquipmentStatus::Inactive, YamlEquipmentStatus::Critical),
        (EquipmentStatus::OutOfOrder, YamlEquipmentStatus::Critical),
        (EquipmentStatus::Unknown, YamlEquipmentStatus::Unknown),
    ];

    for (operational_status, expected_yaml_status) in test_cases {
        let equipment = create_test_equipment(operational_status, None);

        let equipment_data = equipment_to_equipment_data(&equipment);
        assert_eq!(
            equipment_data.status, expected_yaml_status,
            "Failed for operational status: {:?}",
            operational_status
        );
    }
}

#[test]
fn test_equipment_data_to_equipment_maps_to_both_statuses() {
    // Test that YAML status is mapped to both operational status and health_status
    let test_cases = vec![
        (
            YamlEquipmentStatus::Healthy,
            EquipmentStatus::Active,
            EquipmentHealthStatus::Healthy,
        ),
        (
            YamlEquipmentStatus::Warning,
            EquipmentStatus::Maintenance,
            EquipmentHealthStatus::Warning,
        ),
        (
            YamlEquipmentStatus::Critical,
            EquipmentStatus::Inactive,
            EquipmentHealthStatus::Critical,
        ),
        (
            YamlEquipmentStatus::Unknown,
            EquipmentStatus::Unknown,
            EquipmentHealthStatus::Unknown,
        ),
    ];

    for (yaml_status, expected_operational, expected_health) in test_cases {
        let equipment_data = EquipmentData {
            id: "test-001".to_string(),
            name: "Test".to_string(),
            equipment_type: "HVAC".to_string(),
            system_type: "HVAC".to_string(),
            position: arxos::spatial::Point3D {
                x: 0.0,
                y: 0.0,
                z: 0.0,
            },
            bounding_box: arxos::spatial::BoundingBox3D {
                min: arxos::spatial::Point3D {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                },
                max: arxos::spatial::Point3D {
                    x: 1.0,
                    y: 1.0,
                    z: 1.0,
                },
            },
            status: yaml_status,
            properties: HashMap::new(),
            universal_path: "/equipment/test-001".to_string(),
            address: None,
            sensor_mappings: None,
        };

        let equipment = equipment_data_to_equipment(&equipment_data);

        assert_eq!(
            equipment.status, expected_operational,
            "Operational status mismatch for YAML status: {:?}",
            yaml_status
        );

        assert_eq!(
            equipment.health_status,
            Some(expected_health),
            "Health status mismatch for YAML status: {:?}",
            yaml_status
        );
    }
}

#[test]
fn test_round_trip_conversion_with_health_status() {
    // Test round-trip: Equipment -> EquipmentData -> Equipment
    let original = create_test_equipment(
        EquipmentStatus::Active,
        Some(EquipmentHealthStatus::Warning),
    );

    let equipment_data = equipment_to_equipment_data(&original);
    let round_tripped = equipment_data_to_equipment(&equipment_data);

    // Verify health_status is preserved
    assert_eq!(round_tripped.health_status, original.health_status);
    // Note: operational status may differ due to mapping, but health_status should match
    assert_eq!(
        round_tripped.health_status,
        Some(EquipmentHealthStatus::Warning)
    );
}

#[test]
fn test_round_trip_conversion_without_health_status() {
    // Test round-trip when health_status is None (backward compatibility)
    let original = create_test_equipment(EquipmentStatus::Maintenance, None);

    let equipment_data = equipment_to_equipment_data(&original);
    let round_tripped = equipment_data_to_equipment(&equipment_data);

    // After round-trip, health_status should be set (from YAML status)
    assert_eq!(
        round_tripped.health_status,
        Some(EquipmentHealthStatus::Warning) // Maintenance -> Warning
    );
}

#[test]
fn test_health_status_priority_over_operational_status() {
    // Test that health_status takes priority when both are present
    // Equipment can be Active (operational) but Warning (health)
    let equipment = create_test_equipment(
        EquipmentStatus::Active,
        Some(EquipmentHealthStatus::Warning),
    );

    let equipment_data = equipment_to_equipment_data(&equipment);

    // Should use Warning (from health_status), not Healthy (from Active status)
    assert_eq!(equipment_data.status, YamlEquipmentStatus::Warning);
}

#[test]
fn test_independent_status_scenarios() {
    // Test that operational and health status can be independent
    let scenarios = vec![
        // Active but Warning (running but needs maintenance)
        (
            EquipmentStatus::Active,
            Some(EquipmentHealthStatus::Warning),
            YamlEquipmentStatus::Warning,
        ),
        // Inactive but Healthy (turned off, working fine)
        (
            EquipmentStatus::Inactive,
            Some(EquipmentHealthStatus::Healthy),
            YamlEquipmentStatus::Healthy,
        ),
        // Maintenance but Critical (in maintenance, critical issue)
        (
            EquipmentStatus::Maintenance,
            Some(EquipmentHealthStatus::Critical),
            YamlEquipmentStatus::Critical,
        ),
    ];

    for (operational, health, expected_yaml) in scenarios {
        let equipment = create_test_equipment(operational, health);
        let equipment_data = equipment_to_equipment_data(&equipment);

        assert_eq!(
            equipment_data.status, expected_yaml,
            "Failed for scenario: operational={:?}, health={:?}",
            operational, health
        );
    }
}

#[test]
fn test_conversion_preserves_other_fields() {
    // Test that conversion preserves all other equipment fields
    let mut properties = HashMap::new();
    properties.insert("test_key".to_string(), "test_value".to_string());

    let equipment = Equipment {
        sensor_mappings: None,
        id: "preserve-test-001".to_string(),
        name: "Preserve Test".to_string(),
        path: "/equipment/preserve-test".to_string(),
        address: None,
        equipment_type: EquipmentType::Electrical,
        position: Position {
            x: 5.5,
            y: 10.5,
            z: 2.5,
            coordinate_system: "building_local".to_string(),
        },
        properties: properties.clone(),
        status: EquipmentStatus::Active,
        health_status: Some(EquipmentHealthStatus::Healthy),
        room_id: Some("room-001".to_string()),
    };

    let equipment_data = equipment_to_equipment_data(&equipment);
    let round_tripped = equipment_data_to_equipment(&equipment_data);

    // Verify all fields are preserved
    assert_eq!(round_tripped.id, equipment.id);
    assert_eq!(round_tripped.name, equipment.name);
    assert_eq!(round_tripped.path, equipment.path);
    assert_eq!(round_tripped.equipment_type, equipment.equipment_type);
    assert_eq!(round_tripped.position.x, equipment.position.x);
    assert_eq!(round_tripped.position.y, equipment.position.y);
    assert_eq!(round_tripped.position.z, equipment.position.z);
    assert_eq!(round_tripped.properties, equipment.properties);
    // Note: room_id is not preserved in conversion (set to None in equipment_data_to_equipment)
}
