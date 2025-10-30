//! # Performance Benchmarks for ArxOS Critical Operations
//!
//! This module contains performance benchmarks for critical operations:
//! - IFC parsing performance
//! - Spatial query performance
//! - Git operations
//! - 3D rendering performance

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use arxos::{
    ifc::IFCProcessor,
    spatial::{Point3D, BoundingBox3D},
    git::BuildingGitManager,
    yaml::{BuildingData, BuildingYamlSerializer},
};
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

/// Helper function to create test building data
fn create_test_building_data(entity_count: usize) -> BuildingData {
    use chrono::Utc;
    use std::collections::HashMap;
    
    use arxos::yaml::{
        BuildingInfo, BuildingMetadata, FloorData, RoomData, EquipmentData, 
        EquipmentStatus
    };
    
    let mut rooms = Vec::new();
    let mut equipment = Vec::new();
    
    // Create rooms and equipment based on entity count
    for i in 0..entity_count {
        if i % 2 == 0 {
            // Create room
            rooms.push(RoomData {
                id: format!("room-{}", i),
                name: format!("Room {}", i),
                room_type: "Office".to_string(),
                area: Some(100.0 + i as f64),
                volume: Some(400.0 + (i as f64 * 10.0)),
                position: Point3D::new(i as f64, i as f64, (i % 3) as f64),
                bounding_box: BoundingBox3D {
                    min: Point3D::new(i as f64, i as f64, 0.0),
                    max: Point3D::new((i + 10) as f64, (i + 10) as f64, 4.0),
                },
                equipment: vec![],
                properties: HashMap::new(),
            });
        } else {
            // Create equipment
            equipment.push(EquipmentData {
                id: format!("equipment-{}", i),
                name: format!("Equipment {}", i),
                equipment_type: "HVAC".to_string(),
                system_type: "VAV".to_string(),
                position: Point3D::new(i as f64, i as f64, 2.0),
                bounding_box: BoundingBox3D {
                    min: Point3D::new((i - 1) as f64, (i - 1) as f64, 1.5),
                    max: Point3D::new((i + 1) as f64, (i + 1) as f64, 2.5),
                },
                status: EquipmentStatus::Healthy,
                properties: HashMap::new(),
                universal_path: format!("/building/floor1/equipment-{}", i),
                sensor_mappings: None,
            });
        }
    }
    
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
        floors: vec![FloorData {
            id: "floor-1".to_string(),
            name: "Floor 1".to_string(),
            level: 1,
            elevation: 0.0,
            rooms,
            equipment,
            bounding_box: None,
        }],
        coordinate_systems: vec![],
    }
}

/// Configure and run all benchmarks
criterion_group!(
    benches,
    benchmark_ifc_processor_init,
    benchmark_yaml_serialization,
    benchmark_yaml_deserialization,
    benchmark_spatial_point_ops,
    benchmark_spatial_bbox_ops,
    benchmark_git_manager_init
);

criterion_main!(benches);

