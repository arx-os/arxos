//! # Performance Benchmarks for ArxOS Core
//!
//! This module contains comprehensive performance benchmarks for core operations
//! using the Criterion benchmarking framework.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use arxos_core::{ArxOSCore, RoomType, EquipmentType, Point3D};
use std::fs;
use std::path::Path;
use tempfile::TempDir;

/// Benchmark helper to create a temporary test environment
fn setup_benchmark_environment() -> TempDir {
    let temp_dir = tempfile::tempdir().expect("Failed to create temp directory");
    fs::create_dir_all("./data").expect("Failed to create data directory");
    temp_dir
}

/// Benchmark helper to clean up test environment
fn cleanup_benchmark_environment(temp_dir: TempDir) {
    temp_dir.close().expect("Failed to close temp directory");
}

/// Benchmark room creation performance
fn benchmark_room_creation(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    c.bench_function("room_creation", |b| {
        b.iter(|| {
            let mut core = ArxOSCore::new().expect("Failed to create core");
            let _room = core.create_room(
                black_box("Benchmark Building"),
                black_box(1),
                black_box("A"),
                black_box("Benchmark Room"),
                black_box(RoomType::Classroom),
            ).expect("Failed to create room");
        });
    });
    
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark room listing performance with varying numbers of rooms
fn benchmark_room_listing(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    let mut group = c.benchmark_group("room_listing");
    
    for room_count in [1, 10, 50, 100].iter() {
        // Create test rooms
        let mut core = ArxOSCore::new().expect("Failed to create core");
        for i in 0..*room_count {
            let _room = core.create_room(
                "Benchmark Building",
                1,
                "A",
                &format!("Room_{}", i),
                RoomType::Classroom,
            ).expect("Failed to create room");
        }
        
        group.bench_with_input(BenchmarkId::new("list_rooms", room_count), room_count, |b, _| {
            b.iter(|| {
                let core = ArxOSCore::new().expect("Failed to create core");
                let _rooms = core.list_rooms(
                    black_box("Benchmark Building"),
                    black_box(1),
                    Some(black_box("A")),
                ).expect("Failed to list rooms");
            });
        });
    }
    
    group.finish();
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark equipment management performance
fn benchmark_equipment_management(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    // Create a room first
    let mut core = ArxOSCore::new().expect("Failed to create core");
    let _room = core.create_room(
        "Benchmark Building",
        1,
        "A",
        "Benchmark Room",
        RoomType::Classroom,
    ).expect("Failed to create room");
    
    c.bench_function("equipment_creation", |b| {
        b.iter(|| {
            let mut core = ArxOSCore::new().expect("Failed to create core");
            let _equipment = core.add_equipment(
                black_box("Benchmark Building"),
                black_box(1),
                black_box("A"),
                black_box("Benchmark Room"),
                black_box("Benchmark Equipment"),
                black_box(EquipmentType::HVAC),
                black_box(Some(Point3D { x: 10.0, y: 5.0, z: 1.0 })),
            ).expect("Failed to add equipment");
        });
    });
    
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark spatial operations performance
fn benchmark_spatial_operations(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    // Create test data structure
    fs::create_dir_all("./data/Benchmark Building/1/A").expect("Failed to create test structure");
    fs::create_dir_all("./data/Benchmark Building/1/A/Room1").expect("Failed to create room1");
    fs::create_dir_all("./data/Benchmark Building/1/A/Room2").expect("Failed to create room2");
    fs::write("./data/Benchmark Building/1/A/Room1/room.yaml", "id: room1\nname: Room1\n").expect("Failed to write room1");
    fs::write("./data/Benchmark Building/1/A/Room2/room.yaml", "id: room2\nname: Room2\n").expect("Failed to write room2");
    
    let mut group = c.benchmark_group("spatial_operations");
    
    group.bench_function("spatial_query", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _results = core.spatial_query(
                black_box("Benchmark Building"),
                black_box("rooms_in_floor"),
                black_box(&["1".to_string()]),
            ).expect("Failed to perform spatial query");
        });
    });
    
    group.bench_function("spatial_relationship", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _relationship = core.get_spatial_relationship(
                black_box("Benchmark Building"),
                black_box("room1"),
                black_box("room2"),
            ).expect("Failed to get spatial relationship");
        });
    });
    
    group.bench_function("spatial_transformation", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _transform = core.apply_spatial_transformation(
                black_box("Benchmark Building"),
                black_box("room1"),
                black_box("translate_x_10"),
            ).expect("Failed to apply spatial transformation");
        });
    });
    
    group.bench_function("spatial_validation", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _validation = core.validate_spatial_data(black_box("Benchmark Building"))
                .expect("Failed to validate spatial data");
        });
    });
    
    group.finish();
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark configuration management performance
fn benchmark_configuration_management(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    let mut group = c.benchmark_group("configuration_management");
    
    group.bench_function("get_configuration", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _config = core.get_configuration().expect("Failed to get configuration");
        });
    });
    
    group.bench_function("set_configuration_value", |b| {
        b.iter(|| {
            let mut core = ArxOSCore::new().expect("Failed to create core");
            let _result = core.set_configuration_value(
                black_box("user_name"),
                black_box("Benchmark User"),
            ).expect("Failed to set configuration value");
        });
    });
    
    group.finish();
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark IFC processing performance
fn benchmark_ifc_processing(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    // Create a mock IFC file with varying sizes
    let mut group = c.benchmark_group("ifc_processing");
    
    for entity_count in [10, 100, 1000, 5000].iter() {
        let ifc_content = (0..*entity_count)
            .map(|i| format!("#{} = IFCPROJECT('{}', $, $, $, $, $, $, $, $);", i, i))
            .collect::<Vec<_>>()
            .join("\n");
        
        let ifc_file = format!("benchmark_{}.ifc", entity_count);
        fs::write(&ifc_file, ifc_content).expect("Failed to write IFC file");
        
        group.bench_with_input(BenchmarkId::new("process_ifc", entity_count), entity_count, |b, _| {
            b.iter(|| {
                let core = ArxOSCore::new().expect("Failed to create core");
                let _result = core.process_ifc_file(black_box(&ifc_file))
                    .expect("Failed to process IFC file");
            });
        });
    }
    
    group.finish();
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark Git export performance
fn benchmark_git_export(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    c.bench_function("git_export", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _result = core.export_to_repository(black_box("https://github.com/benchmark/repo"))
                .expect("Failed to export to repository");
        });
    });
    
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark 3D rendering performance
fn benchmark_3d_rendering(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    fs::create_dir_all("./output").expect("Failed to create output directory");
    
    // Create test building data
    let building = arxos_core::Building {
        id: "benchmark-building".to_string(),
        name: "Benchmark Building".to_string(),
        path: "/benchmark".to_string(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
        floors: vec![],
        equipment: vec![],
    };
    
    let building_data = arxos_core::BuildingData::new(building);
    
    c.bench_function("3d_rendering", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _result = core.render_building_3d(black_box(&building_data))
                .expect("Failed to render building 3D");
        });
    });
    
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark interactive rendering performance
fn benchmark_interactive_rendering(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    // Create test building data
    let building = arxos_core::Building {
        id: "benchmark-building".to_string(),
        name: "Benchmark Building".to_string(),
        path: "/benchmark".to_string(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
        floors: vec![],
        equipment: vec![],
    };
    
    let building_data = arxos_core::BuildingData::new(building);
    
    c.bench_function("interactive_rendering", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _result = core.start_interactive_renderer(black_box(&building_data))
                .expect("Failed to start interactive renderer");
        });
    });
    
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark live monitoring performance
fn benchmark_live_monitoring(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    // Create test data structure
    fs::create_dir_all("./data/Benchmark Building/1/A/Room1").expect("Failed to create test structure");
    fs::write("./data/Benchmark Building/1/A/Room1/room.yaml", "id: room1\nname: Room1\n").expect("Failed to write room");
    
    c.bench_function("live_monitoring", |b| {
        b.iter(|| {
            let core = ArxOSCore::new().expect("Failed to create core");
            let _result = core.start_live_monitoring(
                black_box("Benchmark Building"),
                Some(black_box(1)),
                Some(black_box("Room1")),
                black_box(1000),
            ).expect("Failed to start live monitoring");
        });
    });
    
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark memory usage for large datasets
fn benchmark_memory_usage(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    let mut group = c.benchmark_group("memory_usage");
    
    for room_count in [100, 500, 1000].iter() {
        group.bench_with_input(BenchmarkId::new("large_dataset", room_count), room_count, |b, _| {
            b.iter(|| {
                let mut core = ArxOSCore::new().expect("Failed to create core");
                
                // Create many rooms
                for i in 0..*room_count {
                    let _room = core.create_room(
                        "Memory Building",
                        1,
                        "A",
                        &format!("Room_{}", i),
                        RoomType::Classroom,
                    ).expect("Failed to create room");
                }
                
                // Perform operations on large dataset
                let _rooms = core.list_rooms("Memory Building", 1, Some("A"))
                    .expect("Failed to list rooms");
                
                // Clean up for next iteration
                for i in 0..*room_count {
                    let _ = core.delete_room("Memory Building", 1, "A", &format!("Room_{}", i));
                }
            });
        });
    }
    
    group.finish();
    cleanup_benchmark_environment(temp_dir);
}

/// Benchmark concurrent operations performance
fn benchmark_concurrent_operations(c: &mut Criterion) {
    let temp_dir = setup_benchmark_environment();
    
    c.bench_function("concurrent_operations", |b| {
        b.iter(|| {
            use std::thread;
            use std::sync::Arc;
            
            let handles: Vec<_> = (0..4).map(|i| {
                thread::spawn(move || {
                    let mut core = ArxOSCore::new().expect("Failed to create core");
                    
                    // Each thread creates rooms in different buildings
                    for j in 0..10 {
                        let _room = core.create_room(
                            &format!("Concurrent Building {}", i),
                            1,
                            "A",
                            &format!("Room_{}", j),
                            RoomType::Classroom,
                        ).expect("Failed to create room");
                    }
                    
                    // List rooms
                    let _rooms = core.list_rooms(&format!("Concurrent Building {}", i), 1, Some("A"))
                        .expect("Failed to list rooms");
                })
            }).collect();
            
            // Wait for all threads to complete
            for handle in handles {
                handle.join().expect("Thread panicked");
            }
        });
    });
    
    cleanup_benchmark_environment(temp_dir);
}

// Define benchmark groups
criterion_group!(
    benches,
    benchmark_room_creation,
    benchmark_room_listing,
    benchmark_equipment_management,
    benchmark_spatial_operations,
    benchmark_configuration_management,
    benchmark_ifc_processing,
    benchmark_git_export,
    benchmark_3d_rendering,
    benchmark_interactive_rendering,
    benchmark_live_monitoring,
    benchmark_memory_usage,
    benchmark_concurrent_operations
);

criterion_main!(benches);
