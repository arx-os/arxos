//! End-to-end workflow integration tests
//!
//! These tests verify complete workflows spanning multiple ArxOS subsystems:
//! - IFC → YAML → AR Export (glTF/USDZ)
//! - Hardware sensor ingestion → Equipment status updates → Alerts
//! - Full round-trip workflows

use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata, CoordinateSystemInfo};
use arxos::core::{Floor, Wing, Room, Equipment, RoomType, EquipmentType, EquipmentStatus, EquipmentHealthStatus, Position, SpatialProperties, Dimensions, BoundingBox};
use arxos::export::ifc::{IFCExporter, IFCSyncState};
use arxos::export::ar::{ARExporter, ARFormat};
use arxos::hardware::{EquipmentStatusUpdater, SensorData, SensorMetadata, SensorDataValues};
use arxos::spatial::{Point3D, BoundingBox3D};
use serial_test::serial;
use std::fs;
use std::collections::HashMap;
use tempfile::TempDir;
use chrono::Utc;

/// Create comprehensive test building data
fn create_comprehensive_test_building() -> BuildingData {
    BuildingData {
        building: BuildingInfo {
            id: "e2e-test-building".to_string(),
            name: "E2E Test Building".to_string(),
            description: Some("Comprehensive building for end-to-end workflow testing".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0.0".to_string(),
            global_bounding_box: Some(BoundingBox3D::new(
                Point3D::new(0.0, 0.0, 0.0),
                Point3D::new(50.0, 50.0, 10.0),
            )),
        },
        metadata: BuildingMetadata {
            source_file: Some("test_building.ifc".to_string()),
            parser_version: "ArxOS E2E Test".to_string(),
            total_entities: 5,
            spatial_entities: 5,
            coordinate_system: "LOCAL".to_string(),
            units: "meters".to_string(),
            tags: vec!["e2e".to_string(), "test".to_string()],
        },
        floors: vec![
            Floor {
                id: "floor-1".to_string(),
                name: "Ground Floor".to_string(),
                level: 0,
                elevation: Some(0.0),
                bounding_box: Some(BoundingBox3D::new(
                    Point3D::new(0.0, 0.0, 0.0),
                    Point3D::new(50.0, 50.0, 10.0),
                )),
                wings: vec![
                    Wing {
                        id: "wing-1".to_string(),
                        name: "Main Wing".to_string(),
                        rooms: vec![
                            Room {
                                id: "room-101".to_string(),
                                name: "Office 101".to_string(),
                                room_type: RoomType::Office,
                                equipment: vec![],
                                spatial_properties: SpatialProperties {
                                    position: Position { x: 5.0, y: 5.0, z: 2.0, coordinate_system: "LOCAL".to_string() },
                                    dimensions: Dimensions { width: 10.0, height: 3.0, depth: 6.0 },
                                    bounding_box: BoundingBox {
                                        min: Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "LOCAL".to_string() },
                                        max: Position { x: 10.0, y: 6.0, z: 3.0, coordinate_system: "LOCAL".to_string() },
                                    },
                                    coordinate_system: "LOCAL".to_string(),
                                },
                                properties: HashMap::new(),
                                created_at: None,
                                updated_at: None,
                            },
                        ],
                        equipment: vec![],
                        properties: HashMap::new(),
                    },
                ],
                equipment: vec![
                    Equipment {
                        id: "hvac-unit-1".to_string(),
                        name: "HVAC Unit 1".to_string(),
                        path: "building/floor-1/room-101/equipment-hvac-1".to_string(),
                        address: None,
                        equipment_type: EquipmentType::HVAC,
                        position: Position { x: 2.0, y: 3.0, z: 2.0, coordinate_system: "LOCAL".to_string() },
                        properties: {
                            let mut props = HashMap::new();
                            props.insert("temperature_setpoint".to_string(), "72".to_string());
                            props.insert("sensor_id".to_string(), "sensor-hvac-001".to_string());
                            props
                        },
                        status: EquipmentStatus::Active,
                        health_status: Some(EquipmentHealthStatus::Healthy),
                        room_id: Some("room-101".to_string()),
                        sensor_mappings: None,
                    },
                    Equipment {
                        id: "electrical-fixture-1".to_string(),
                        name: "Light Fixture 1".to_string(),
                        path: "building/floor-1/room-101/equipment-electrical-1".to_string(),
                        address: None,
                        equipment_type: EquipmentType::Electrical,
                        position: Position { x: 7.0, y: 3.0, z: 2.5, coordinate_system: "LOCAL".to_string() },
                        properties: HashMap::new(),
                        status: EquipmentStatus::Active,
                        health_status: Some(EquipmentHealthStatus::Healthy),
                        room_id: Some("room-101".to_string()),
                        sensor_mappings: None,
                    },
                ],
                properties: HashMap::new(),
            },
        ],
        coordinate_systems: vec![CoordinateSystemInfo {
            name: "World".to_string(),
            origin: Point3D::origin(),
            x_axis: Point3D::new(1.0, 0.0, 0.0),
            y_axis: Point3D::new(0.0, 1.0, 0.0),
            z_axis: Point3D::new(0.0, 0.0, 1.0),
            description: Some("Default world coordinate system".to_string()),
        }],
    }
}

#[test]
fn test_yaml_to_ar_export_workflow() {
    // Test: YAML → glTF export workflow
    let temp_dir = TempDir::new().unwrap();
    let gltf_path = temp_dir.path().join("test_export.gltf");
    
    let building_data = create_comprehensive_test_building();
    let ar_exporter = ARExporter::new(building_data);
    
    // Export to glTF
    ar_exporter.export(ARFormat::GLTF, &gltf_path).expect("glTF export should succeed");
    
    // Verify glTF file was created
    assert!(gltf_path.exists(), "glTF file should be created");
    
    // Verify glTF file is valid JSON
    let content = fs::read_to_string(&gltf_path).unwrap();
    let json: serde_json::Value = serde_json::from_str(&content).expect("glTF should be valid JSON");
    
    // Verify glTF structure
    assert!(json.get("asset").is_some(), "glTF should have asset");
    assert!(json.get("scenes").is_some(), "glTF should have scenes");
    
    // Verify equipment is represented in glTF
    let nodes = json.get("nodes").and_then(|n| n.as_array());
    assert!(nodes.is_some(), "glTF should have nodes");
    let node_count = nodes.as_ref().map(|n| n.len()).unwrap_or(0);
    assert!(node_count > 0, "glTF should have at least one node for equipment");
}

#[test]
fn test_yaml_to_ifc_export_workflow() {
    // Test: YAML → IFC export workflow
    let temp_dir = TempDir::new().unwrap();
    let ifc_path = temp_dir.path().join("test_export.ifc");
    
    let building_data = create_comprehensive_test_building();
    let ifc_exporter = IFCExporter::new(building_data.clone());
    
    // Export to IFC
    ifc_exporter.export(&ifc_path).expect("IFC export should succeed");
    
    // Verify IFC file was created
    assert!(ifc_path.exists(), "IFC file should be created");
    
    // Verify IFC file content
    let content = fs::read_to_string(&ifc_path).unwrap();
    assert!(content.contains("ISO-10303-21"), "Should contain IFC header");
    assert!(content.contains("IFCROOM") || content.contains("IFCSPACE"), "Should contain room entities");
    assert!(content.contains("IFCAIRTERMINAL") || content.contains("IFCDISTRIBUTIONELEMENT"), "Should contain HVAC equipment");
}

#[serial]
#[test]
fn test_sensor_ingestion_to_equipment_update_workflow() {
    // Test: Sensor data ingestion → Equipment status update → Alerts
    let temp_dir = TempDir::new().unwrap();
    
    // Create temporary building YAML file with unique name
    let mut building_data = create_comprehensive_test_building();
    use std::time::{SystemTime, UNIX_EPOCH};
    let unique_id = format!("{}-{}", SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos(), std::process::id());
    building_data.building.id = format!("e2e-sensor-test-{}", unique_id);
    building_data.building.name = format!("E2E Sensor Test Building {}", unique_id);
    let building_name = format!("e2e-sensor-test-{}", unique_id);
    let building_yaml_path = temp_dir.path().join(format!("{}.yaml", building_name));
    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).unwrap();
    fs::write(&building_yaml_path, yaml_content).unwrap();
    
    // Change to temp directory to simulate working directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Create equipment status updater
    let mut status_updater = EquipmentStatusUpdater::new(&building_name)
        .expect("Should create status updater");
    
    // Create sensor data for HVAC equipment
    // Note: sensor_id should match equipment_id for find_equipment_for_sensor fallback logic
    let sensor_data = SensorData {
        api_version: "arxos.io/v1".to_string(),
        kind: "SensorData".to_string(),
        metadata: SensorMetadata {
            sensor_id: "hvac-unit-1".to_string(), // Match equipment_id for lookup
            sensor_type: "temperature".to_string(),
            room_path: Some("/building/floor-1/room-101".to_string()),
            timestamp: Utc::now().to_rfc3339(),
            source: "test-sensor".to_string(),
            building_id: Some("e2e-test-building".to_string()),
            equipment_id: Some("hvac-unit-1".to_string()),
            extra: HashMap::new(),
        },
        data: SensorDataValues {
            values: {
                let mut map = HashMap::new();
                map.insert("temperature".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(95)));
                map.insert("unit".to_string(), serde_yaml::Value::String("fahrenheit".to_string()));
                map
            },
        },
        alerts: vec![],
        arxos: None,
    };
    
    // Process sensor data
    let update_result = status_updater.process_sensor_data(&sensor_data)
        .expect("Sensor data processing should succeed");
    
    // Verify equipment was updated
    assert_eq!(update_result.equipment_id, "hvac-unit-1");
    assert_ne!(update_result.old_status, update_result.new_status, "Status should change");
    
    // Verify alerts were generated (temperature 95°F is out of normal range)
    assert!(!update_result.alerts.is_empty(), "Should generate alerts for out-of-range temperature");
    assert!(update_result.alerts.iter().any(|a| a.level == "warning" || a.level == "critical"),
            "Should have warning or critical alert");
    
    // Restore original directory
    std::env::set_current_dir(original_dir).unwrap();
}

#[serial]
#[test]
fn test_complete_workflow_yaml_ifc_ar_hardware() {
    // Test: Complete workflow combining all subsystems
    let temp_dir = TempDir::new().unwrap();
    
    // Step 1: Create building data (simulating IFC import)
    let building_data = create_comprehensive_test_building();
    
    // Step 2: Export to IFC
    let ifc_path = temp_dir.path().join("exported_building.ifc");
    let ifc_exporter = IFCExporter::new(building_data.clone());
    ifc_exporter.export(&ifc_path).expect("IFC export should succeed");
    assert!(ifc_path.exists(), "IFC file should be created");
    
    // Step 3: Export to AR (glTF)
    let gltf_path = temp_dir.path().join("building_ar.gltf");
    let ar_exporter = ARExporter::new(building_data.clone());
    ar_exporter.export(ARFormat::GLTF, &gltf_path).expect("glTF export should succeed");
    assert!(gltf_path.exists(), "glTF file should be created");
    
    // Step 4: Simulate hardware sensor ingestion
    use std::time::{SystemTime, UNIX_EPOCH};
    let unique_id = format!("{}-{}", SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos(), std::process::id());
    let building_name = format!("e2e-complete-workflow-{}", unique_id);
    let mut workflow_building = building_data.clone();
    workflow_building.building.id = building_name.clone();
    workflow_building.building.name = format!("E2E Complete Workflow {}", unique_id);
    let building_yaml_path = temp_dir.path().join(format!("{}.yaml", building_name));
    fs::write(&building_yaml_path, serde_yaml::to_string(&workflow_building).unwrap()).unwrap();
    
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    let mut status_updater = EquipmentStatusUpdater::new(&building_name)
        .expect("Should create status updater");
    
    // Simulate critical sensor reading
    let critical_sensor_data = SensorData {
        api_version: "arxos.io/v1".to_string(),
        kind: "SensorData".to_string(),
        metadata: SensorMetadata {
            sensor_id: "hvac-unit-1".to_string(), // Match equipment_id for lookup
            sensor_type: "temperature".to_string(),
            room_path: Some("/building/floor-1/room-101".to_string()),
            timestamp: Utc::now().to_rfc3339(),
            source: "test-sensor".to_string(),
            building_id: Some("e2e-test-building".to_string()),
            equipment_id: Some("hvac-unit-1".to_string()),
            extra: HashMap::new(),
        },
        data: SensorDataValues {
            values: {
                let mut map = HashMap::new();
                map.insert("temperature".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(110)));
                map
            },
        },
        alerts: vec![],
        arxos: None,
    };
    
    let update_result = status_updater.process_sensor_data(&critical_sensor_data)
        .expect("Sensor processing should succeed");
    
    // Verify complete workflow results
    assert!(update_result.alerts.len() > 0, "Should generate alerts for critical temperature");
    assert_eq!(update_result.equipment_id, "hvac-unit-1");
    
    // Verify all export files exist
    assert!(ifc_path.exists(), "IFC export should exist");
    assert!(gltf_path.exists(), "glTF export should exist");
    
    // Restore original directory
    std::env::set_current_dir(original_dir).unwrap();
}

#[test]
fn test_delta_export_with_sensor_updates() {
    // Test: Delta IFC export after sensor-driven equipment status changes
    let temp_dir = TempDir::new().unwrap();
    
    // Create temporary building YAML file with unique name
    use std::time::{SystemTime, UNIX_EPOCH};
    let unique_id = format!("{}-{}", SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos(), std::process::id());
    let building_name = format!("e2e-delta-export-{}", unique_id);
    let mut building_data = create_comprehensive_test_building();
    building_data.building.id = building_name.clone();
    building_data.building.name = format!("E2E Delta Export {}", unique_id);
    let building_yaml_path = temp_dir.path().join(format!("{}.yaml", building_name));
    let serializer = arxos::yaml::BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).unwrap();
    fs::write(&building_yaml_path, yaml_content).unwrap();
    
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    // Initial full export
    let ifc_path = temp_dir.path().join("initial.ifc");
    let ifc_exporter = IFCExporter::new(building_data.clone());
    ifc_exporter.export(&ifc_path).expect("Initial export should succeed");
    
    // Create sync state
    let sync_state_path = temp_dir.path().join(".arxos").join("ifc-sync-state.json");
    fs::create_dir_all(sync_state_path.parent().unwrap()).unwrap();
    let mut sync_state = IFCSyncState::new(ifc_path.clone());
    let (eq_paths, room_paths) = ifc_exporter.collect_universal_paths();
    sync_state.update_after_export(eq_paths, room_paths);
    sync_state.save(&sync_state_path).unwrap();
    
    // Simulate sensor update that changes equipment status
    let mut status_updater = EquipmentStatusUpdater::new(&building_name).unwrap();
    let sensor_data = SensorData {
        api_version: "arxos.io/v1".to_string(),
        kind: "SensorData".to_string(),
        metadata: SensorMetadata {
            sensor_id: "hvac-unit-1".to_string(), // Match equipment_id for lookup
            sensor_type: "temperature".to_string(),
            room_path: None,
            timestamp: Utc::now().to_rfc3339(),
            source: "test".to_string(),
            building_id: None,
            equipment_id: Some("hvac-unit-1".to_string()),
            extra: HashMap::new(),
        },
        data: SensorDataValues {
            values: {
                let mut map = HashMap::new();
                map.insert("temperature".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(100)));
                map
            },
        },
        alerts: vec![],
        arxos: None,
    };
    
    status_updater.process_sensor_data(&sensor_data).unwrap();
    
    // Reload building data and create delta export
    let updated_building = arxos::persistence::PersistenceManager::new(&building_name)
        .unwrap()
        .load_building_data()
        .unwrap();
    
    let delta_exporter = IFCExporter::new(updated_building);
    let delta_ifc_path = temp_dir.path().join("delta.ifc");
    let loaded_sync_state = IFCSyncState::load(&sync_state_path).unwrap();
    delta_exporter.export_delta(Some(&loaded_sync_state), &delta_ifc_path)
        .expect("Delta export should succeed");
    
    // Verify delta export was created
    assert!(delta_ifc_path.exists(), "Delta IFC file should be created");
    
    std::env::set_current_dir(original_dir).unwrap();
}

