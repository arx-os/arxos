//! # Performance Benchmarks for ArxOS Core
//!
//! This module contains performance benchmarks for core operations
//! using the Criterion benchmarking framework.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use arxos::{core::{Room, Equipment, RoomType, EquipmentType}, spatial::Point3D};

/// Benchmark room creation performance
fn benchmark_room_creation(c: &mut Criterion) {
    c.bench_function("room_creation", |b| {
        b.iter(|| {
            let _room = Room::new(
                black_box("Benchmark Room".to_string()),
                black_box(RoomType::Classroom),
            );
        });
    });
}

/// Benchmark room listing performance with varying numbers of rooms
fn benchmark_room_listing(c: &mut Criterion) {
    let mut group = c.benchmark_group("room_listing");
    
    for room_count in [1, 10, 50, 100].iter() {
        // Create test rooms
        let mut rooms = Vec::new();
        for i in 0..*room_count {
            rooms.push(Room::new(
                format!("Room {}", i),
                RoomType::Classroom,
            ));
        }
        
        group.bench_with_input(
            BenchmarkId::new("list_rooms", room_count),
            &rooms,
            |b, rooms| {
                b.iter(|| {
                    // Actually iterate through and access room data (simulating listing operation)
                    let mut count = 0;
                    for room in rooms.iter() {
                        black_box(&room.name);
                        black_box(&room.room_type);
                        count += 1;
                    }
                    black_box(count);
                });
            }
        );
    }
    
    group.finish();
}

/// Benchmark equipment management operations
fn benchmark_equipment_management(c: &mut Criterion) {
    c.bench_function("equipment_creation", |b| {
        b.iter(|| {
            let _equipment = Equipment::new(
                black_box("Test Equipment".to_string()),
                black_box("/path/to".to_string()),
                black_box(EquipmentType::HVAC),
            );
        });
    });
}

/// Benchmark spatial operations
fn benchmark_spatial_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("spatial_operations");
    
    group.bench_function("point_distance", |b| {
        let p1 = Point3D::new(0.0, 0.0, 0.0);
        let p2 = Point3D::new(1.0, 1.0, 1.0);
        b.iter(|| {
            black_box(p1.distance_to(&p2));
        });
    });
    
    group.finish();
}

criterion_group!(
    benches,
    benchmark_room_creation,
    benchmark_room_listing,
    benchmark_equipment_management,
    benchmark_spatial_operations
);

criterion_main!(benches);
