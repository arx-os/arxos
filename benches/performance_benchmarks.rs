//! # Performance Benchmarks for ArxOS Critical Operations
//!
//! This module contains performance benchmarks for critical operations:
//! - IFC parsing performance
//! - Spatial query performance
//! - Git operations
//! - 3D rendering performance
//! - AR export performance
//! - Sensor processing performance

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use arxos::{
    ifc::IFCProcessor,
    spatial::{Point3D, BoundingBox3D, SpatialEntity},
    git::BuildingGitManager,
    yaml::{BuildingData, BuildingYamlSerializer},
    persistence::PersistenceManager,
};
#[cfg(feature = "async-sensors")]
use arxos::export::ar::{GLTFExporter, ARFormat, ARExporter};
#[cfg(feature = "async-sensors")]
use arxos::hardware::{SensorData, SensorMetadata, SensorDataValues};
use tempfile::TempDir;

/// Benchmark IFC parser initialization
fn benchmark_ifc_processor_init(c: &mut Criterion) {
    c.bench_function("ifc_processor_init", |b| {
        b.iter(|| {
            let _processor = black_box(IFCProcessor::new());
        });
    });
}

/// Benchmark YAML serialization performance with varying data sizes
fn benchmark_yaml_serialization(c: &mut Criterion) {
    let mut group = c.benchmark_group("yaml_serialization");
    
    for entity_count in [10, 100, 1000].iter() {
        let building_data = create_test_building_data(*entity_count);
        
        group.bench_with_input(
            BenchmarkId::new("serialize", entity_count),
            &building_data,
            |b, data| {
                let serializer = BuildingYamlSerializer::new();
                b.iter(|| {
                    black_box(serializer.to_yaml(data).unwrap());
                });
            }
        );
    }
    
    group.finish();
}

/// Benchmark YAML deserialization performance
fn benchmark_yaml_deserialization(c: &mut Criterion) {
    let mut group = c.benchmark_group("yaml_deserialization");
    
    for entity_count in [10, 100, 1000].iter() {
        let building_data = create_test_building_data(*entity_count);
        let serializer = BuildingYamlSerializer::new();
        let yaml_content = serializer.to_yaml(&building_data).unwrap();
        
        group.bench_with_input(
            BenchmarkId::new("deserialize", entity_count),
            &yaml_content,
            |b, content| {
                b.iter(|| {
                    black_box(serde_yaml::from_str::<BuildingData>(content).unwrap());
                });
            }
        );
    }
    
    group.finish();
}

/// Benchmark spatial point operations
fn benchmark_spatial_point_ops(c: &mut Criterion) {
    let mut group = c.benchmark_group("spatial_point_ops");
    
    let p1 = Point3D::new(0.0, 0.0, 0.0);
    let p2 = Point3D::new(1.0, 1.0, 1.0);
    let p3 = Point3D::new(5.0, 5.0, 5.0);
    
    group.bench_function("distance", |b| {
        b.iter(|| {
            black_box(p1.distance_to(&p2));
        });
    });
    
    group.bench_function("center", |b| {
        let bbox = BoundingBox3D::new(p1, p3);
        b.iter(|| {
            black_box(bbox.center());
        });
    });
    
    group.finish();
}

/// Benchmark spatial bounding box operations
fn benchmark_spatial_bbox_ops(c: &mut Criterion) {
    let mut group = c.benchmark_group("spatial_bbox_ops");
    
    let bbox1 = BoundingBox3D {
        min: Point3D::new(0.0, 0.0, 0.0),
        max: Point3D::new(10.0, 10.0, 4.0),
    };
    
    group.bench_function("volume", |b| {
        b.iter(|| {
            black_box(bbox1.volume());
        });
    });
    
    group.bench_function("center", |b| {
        b.iter(|| {
            black_box(bbox1.center());
        });
    });
    
    group.bench_function("from_points", |b| {
        let points = vec![
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(1.0, 1.0, 1.0),
            Point3D::new(2.0, 2.0, 2.0),
            Point3D::new(-1.0, -1.0, -1.0),
        ];
        b.iter(|| {
            black_box(BoundingBox3D::from_points(&points));
        });
    });
    
    group.finish();
}

/// Benchmark Git manager initialization
fn benchmark_git_manager_init(c: &mut Criterion) {
    let temp_dir = TempDir::new().unwrap();
    let repo_path = temp_dir.path();
    
    c.bench_function("git_manager_init", |b| {
        b.iter(|| {
            let config = arxos::git::GitConfig {
                author_name: "Test User".to_string(),
                author_email: "test@example.com".to_string(),
                branch: "main".to_string(),
                remote_url: None,
            };
            let _manager = black_box(BuildingGitManager::new(
                &repo_path.to_string_lossy(),
                "test_building",
                config,
            ));
        });
    });
}

/// Benchmark glTF export performance with varying data sizes
#[cfg(feature = "async-sensors")]
fn benchmark_gltf_export(c: &mut Criterion) {
    let mut group = c.benchmark_group("gltf_export");
    
    let temp_dir = TempDir::new().unwrap();
    
    for entity_count in [10, 100, 500].iter() {
        let building_data = create_test_building_data(*entity_count);
        
        group.bench_with_input(
            BenchmarkId::new("export", entity_count),
            entity_count,
            |b, _count| {
                let output_path = temp_dir.path().join(format!("output_{}.gltf", entity_count));
                b.iter(|| {
                    let exporter = GLTFExporter::new(&building_data);
                    black_box(exporter.export(&output_path)).ok();
                });
            }
        );
    }
    
    group.finish();
}

/// Benchmark AR export performance
#[cfg(feature = "async-sensors")]
fn benchmark_ar_export(c: &mut Criterion) {
    let mut group = c.benchmark_group("ar_export");
    
    let temp_dir = TempDir::new().unwrap();
    
    group.bench_function("export_gltf", |b| {
        let building_data = create_test_building_data(100);
        let output_path = temp_dir.path().join("output.gltf");
        b.iter(|| {
            let exporter = ARExporter::new(building_data.clone());
            black_box(exporter.export(ARFormat::GLTF, &output_path)).ok();
        });
    });
    
    group.finish();
}

/// Benchmark sensor data JSON serialization
#[cfg(feature = "async-sensors")]
fn benchmark_sensor_json_serialization(c: &mut Criterion) {
    let mut group = c.benchmark_group("sensor_json_serialization");
    
    let sensor_data = create_test_sensor_data();
    
    group.bench_function("serialize", |b| {
        b.iter(|| {
            black_box(serde_json::to_string(&sensor_data).unwrap());
        });
    });
    
    group.bench_function("deserialize", |b| {
        let json = serde_json::to_string(&sensor_data).unwrap();
        b.iter(|| {
            black_box(serde_json::from_str::<SensorData>(&json).unwrap());
        });
    });
    
    group.finish();
}

/// Benchmark sensor data validation
#[cfg(feature = "async-sensors")]
fn benchmark_sensor_validation(c: &mut Criterion) {
    let mut group = c.benchmark_group("sensor_validation");
    
    let sensor_data = create_test_sensor_data();
    
    group.bench_function("validate_valid", |b| {
        b.iter(|| {
            black_box(validate_sensor_data(&sensor_data));
        });
    });
    
    group.finish();
}

/// Helper function to create test sensor data
#[cfg(feature = "async-sensors")]
fn create_test_sensor_data() -> SensorData {
    use std::collections::HashMap;
    use arxos::hardware::{SensorAlert, ArxosMetadata};
    
    SensorData {
        api_version: "arxos.io/v1".to_string(),
        kind: "SensorData".to_string(),
        metadata: SensorMetadata {
            sensor_id: "sensor_001".to_string(),
            sensor_type: "Temperature".to_string(),
            room_path: Some("/B1/3/301".to_string()),
            timestamp: "2024-01-01T12:00:00Z".to_string(),
            source: "HTTP".to_string(),
            building_id: Some("B1".to_string()),
            equipment_id: Some("HVAC-301".to_string()),
            extra: HashMap::new(),
        },
        data: SensorDataValues {
            values: {
                let mut map = HashMap::new();
                map.insert("temperature".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(72)));
                map.insert("humidity".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(45)));
                map
            },
        },
        alerts: vec![SensorAlert {
            level: "info".to_string(),
            message: "All readings normal".to_string(),
            timestamp: "2024-01-01T12:00:00Z".to_string(),
        }],
        arxos: Some(ArxosMetadata {
            processed: false,
            validated: false,
            device_id: "esp32_001".to_string(),
        }),
    }
}

/// Helper function to validate sensor data
#[cfg(feature = "async-sensors")]
fn validate_sensor_data(data: &SensorData) -> bool {
    !data.api_version.is_empty() 
        && !data.kind.is_empty()
        && !data.metadata.sensor_id.is_empty()
        && !data.metadata.sensor_type.is_empty()
        && !data.data.values.is_empty()
}


/// Helper function to create test building data
fn create_test_building_data(entity_count: usize) -> BuildingData {
    use chrono::Utc;
    use std::collections::HashMap;
    
    use arxos::yaml::{BuildingInfo, BuildingMetadata};
    use arxos::core::{Floor, Wing, Room, Equipment, RoomType, EquipmentType, EquipmentStatus, Position, Dimensions, SpatialProperties, BoundingBox};
    use arxos::spatial::{Point3D, BoundingBox3D};
    
    let mut rooms = Vec::new();
    let mut equipment = Vec::new();
    
    // Create rooms and equipment based on entity count
    for i in 0..entity_count {
        if i % 2 == 0 {
            // Create room using core types
            let position = Position {
                x: i as f64,
                y: i as f64,
                z: (i % 3) as f64,
                coordinate_system: "building_local".to_string(),
            };
            let dimensions = Dimensions {
                width: 10.0,
                height: 4.0,
                depth: 10.0,
            };
            let bounding_box = BoundingBox {
                min: Position {
                    x: i as f64,
                    y: i as f64,
                    z: 0.0,
                    coordinate_system: "building_local".to_string(),
                },
                max: Position {
                    x: (i + 10) as f64,
                    y: (i + 10) as f64,
                    z: 4.0,
                    coordinate_system: "building_local".to_string(),
                },
            };
            let spatial_properties = SpatialProperties {
                position,
                dimensions,
                bounding_box,
                coordinate_system: "building_local".to_string(),
            };
            rooms.push(Room {
                id: format!("room-{}", i),
                name: format!("Room {}", i),
                room_type: RoomType::Office,
                equipment: vec![],
                spatial_properties,
                properties: HashMap::new(),
                created_at: None,
                updated_at: None,
            });
        } else {
            // Create equipment using core types
            equipment.push(Equipment {
                id: format!("equipment-{}", i),
                name: format!("Equipment {}", i),
                path: format!("/building/floor1/equipment-{}", i),
                address: None,
                equipment_type: EquipmentType::HVAC,
                position: Position {
                    x: i as f64,
                    y: i as f64,
                    z: 2.0,
                    coordinate_system: "building_local".to_string(),
                },
                properties: HashMap::new(),
                status: EquipmentStatus::Active,
                health_status: None,
                room_id: None,
                sensor_mappings: None,
            });
        }
    }
    
    // Create a wing with rooms
    let mut wing = Wing::new("Default".to_string());
    wing.rooms = rooms;
    
    BuildingData {
        building: BuildingInfo {
            id: "benchmark-building".to_string(),
            name: "Benchmark Building".to_string(),
            description: Some("Test building for benchmarks".to_string()),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "1.0".to_string(),
            total_entities: entity_count,
            spatial_entities: entity_count,
            coordinate_system: "local".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![Floor {
            id: "floor-1".to_string(),
            name: "Floor 1".to_string(),
            level: 1,
            elevation: Some(0.0),
            bounding_box: None,
            wings: vec![wing],
            equipment,
            properties: HashMap::new(),
        }],
        coordinate_systems: vec![],
    }
}

// Conditionally include async-sensors benchmarks
#[cfg(feature = "async-sensors")]
criterion_group!(
    benches,
    benchmark_ifc_processor_init,
    benchmark_yaml_serialization,
    benchmark_yaml_deserialization,
    benchmark_spatial_point_ops,
    benchmark_spatial_bbox_ops,
    benchmark_git_manager_init,
    benchmark_gltf_export,
    benchmark_ar_export,
    benchmark_sensor_json_serialization,
    benchmark_sensor_validation
);

#[cfg(not(feature = "async-sensors"))]
// Benchmark group consolidated below with #[cfg(not(feature = "async-sensors"))]

/// Benchmark building data loading with caching
fn benchmark_building_data_caching(c: &mut Criterion) {
    let temp_dir = TempDir::new().unwrap();
    let test_file = temp_dir.path().join("test_building.yaml");
    
    // Create test building data
    let building_data = create_test_building_data(100);
    let serializer = BuildingYamlSerializer::new();
    let yaml_content = serializer.to_yaml(&building_data).unwrap();
    std::fs::write(&test_file, yaml_content).unwrap();
    
    // Change to temp directory
    let original_dir = std::env::current_dir().unwrap();
    std::env::set_current_dir(temp_dir.path()).unwrap();
    
    let mut group = c.benchmark_group("building_data_caching");
    
    group.bench_function("cache_miss", |b| {
        // Clear cache before each iteration
        arxos::persistence::invalidate_building_data_cache();
        b.iter(|| {
            let persistence = PersistenceManager::new("test_building").unwrap();
            black_box(persistence.load_building_data().unwrap());
        });
    });
    
    group.bench_function("cache_hit", |b| {
        // Load once to populate cache
        let persistence = PersistenceManager::new("test_building").unwrap();
        let _ = persistence.load_building_data().unwrap();
        
        b.iter(|| {
            let persistence = PersistenceManager::new("test_building").unwrap();
            black_box(persistence.load_building_data().unwrap());
        });
    });
    
    group.finish();
    
    std::env::set_current_dir(original_dir).unwrap();
}

/// Benchmark collection indexing performance
fn benchmark_collection_indexing(c: &mut Criterion) {
    let mut building_data = create_test_building_data(1000);
    
    let mut group = c.benchmark_group("collection_indexing");
    
    group.bench_function("indexed_lookup", |b| {
        let index = building_data.build_index();
        b.iter(|| {
            // O(1) lookup using index
            let _ = building_data.get_floor_mut(1, &index);
            black_box(());
        });
    });
    
    group.bench_function("linear_search", |b| {
        b.iter(|| {
            // O(n) linear search
            let _ = building_data.floors.iter().find(|f| f.level == 1);
            black_box(());
        });
    });
    
    group.finish();
}

/// Benchmark spatial index building performance
fn benchmark_spatial_index_building(c: &mut Criterion) {
    let processor = IFCProcessor::new();
    
    // Create test spatial entities
    let mut entities = Vec::new();
    for i in 0..1000 {
        entities.push(SpatialEntity {
            id: format!("entity-{}", i),
            name: format!("Room {}", i),
            entity_type: "Room".to_string(),
            position: Point3D::new(i as f64 * 10.0, i as f64 * 10.0, (i % 10) as f64 * 3.0),
            bounding_box: BoundingBox3D {
                min: Point3D::new(i as f64 * 10.0, i as f64 * 10.0, (i % 10) as f64 * 3.0),
                max: Point3D::new((i + 1) as f64 * 10.0, (i + 1) as f64 * 10.0, (i % 10) as f64 * 3.0 + 3.0),
            },
            coordinate_system: None,
        });
    }
    
    c.bench_function("spatial_index_building", |b| {
        b.iter(|| {
            // build_spatial_index removed - spatial indexing now internal
            black_box(&entities);
        });
    });
}

// Conditionally include async-sensors benchmarks
#[cfg(feature = "async-sensors")]
criterion_group!(
    benches,
    benchmark_ifc_processor_init,
    benchmark_yaml_serialization,
    benchmark_yaml_deserialization,
    benchmark_spatial_point_ops,
    benchmark_spatial_bbox_ops,
    benchmark_git_manager_init,
    benchmark_gltf_export,
    benchmark_ar_export,
    benchmark_sensor_json_serialization,
    benchmark_sensor_validation,
    benchmark_building_data_caching,
    benchmark_collection_indexing,
    benchmark_spatial_index_building
);

#[cfg(not(feature = "async-sensors"))]
criterion_group!(
    benches,
    benchmark_ifc_processor_init,
    benchmark_yaml_serialization,
    benchmark_yaml_deserialization,
    benchmark_spatial_point_ops,
    benchmark_spatial_bbox_ops,
    benchmark_git_manager_init,
    benchmark_building_data_caching,
    benchmark_collection_indexing,
    benchmark_spatial_index_building
);

criterion_main!(benches);

