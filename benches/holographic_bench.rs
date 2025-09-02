use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use arxos_core::holographic::{
    consciousness::{BuildingConsciousness, ConsciousnessField},
    consciousness_async::{AsyncBuildingConsciousness, ParallelPhiCalculator},
    quantum_async::{ParallelQuantumSystem, ParallelInterferenceCalculator, SimpleQuantumState},
    spatial_index::{SpatialIndex, Point3D},
    sparse::SparseGrid3D,
    automata::{CellularAutomaton3D, AutomatonRules},
    automata_sparse::SparseCellularAutomaton3D,
    quantum::QuantumBasis,
};
use arxos_core::arxobject::ArxObject;
use std::time::Duration;

fn bench_consciousness_phi(c: &mut Criterion) {
    let mut group = c.benchmark_group("consciousness_phi");
    
    for size in [100, 500, 1000, 5000].iter() {
        // Sequential version
        group.bench_with_input(
            BenchmarkId::new("sequential", size),
            size,
            |b, &size| {
                let mut consciousness = BuildingConsciousness::new();
                let objects: Vec<_> = (0..size)
                    .map(|i| ArxObject::new(i as u16, 1, 100, 100, 100))
                    .collect();
                
                b.iter(|| {
                    for obj in &objects {
                        let field = ConsciousnessField::from_arxobject(black_box(obj));
                        consciousness.add_object(obj.building_id, field).ok();
                    }
                    consciousness.calculate_global_phi()
                });
            },
        );
        
        // Parallel version
        group.bench_with_input(
            BenchmarkId::new("parallel", size),
            size,
            |b, &size| {
                let calculator = ParallelPhiCalculator::new(None);
                let objects: Vec<_> = (0..size)
                    .map(|i| ArxObject::new(i as u16, 1, 100, 100, 100))
                    .collect();
                
                b.iter(|| {
                    calculator.calculate_all(black_box(&objects))
                });
            },
        );
    }
    
    group.finish();
}

fn bench_spatial_index(c: &mut Criterion) {
    let mut group = c.benchmark_group("spatial_index");
    
    for size in [1000, 5000, 10000].iter() {
        group.bench_with_input(
            BenchmarkId::new("insert", size),
            size,
            |b, &size| {
                let mut index = SpatialIndex::new(
                    Point3D::new(0.0, 0.0, 0.0),
                    Point3D::new(10000.0, 10000.0, 10000.0),
                );
                
                b.iter(|| {
                    for i in 0..size {
                        let pos = Point3D::new(
                            (i as f32 * 7919.0) % 10000.0,
                            (i as f32 * 6991.0) % 10000.0,
                            (i as f32 * 5023.0) % 10000.0,
                        );
                        index.insert(i as u16, pos).ok();
                    }
                });
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("query_radius", size),
            size,
            |b, &size| {
                let mut index = SpatialIndex::new(
                    Point3D::new(0.0, 0.0, 0.0),
                    Point3D::new(10000.0, 10000.0, 10000.0),
                );
                
                // Populate index
                for i in 0..size {
                    let pos = Point3D::new(
                        (i as f32 * 7919.0) % 10000.0,
                        (i as f32 * 6991.0) % 10000.0,
                        (i as f32 * 5023.0) % 10000.0,
                    );
                    index.insert(i as u16, pos).ok();
                }
                
                b.iter(|| {
                    let center = Point3D::new(5000.0, 5000.0, 5000.0);
                    index.find_within_radius(black_box(&center), black_box(500.0))
                });
            },
        );
    }
    
    group.finish();
}

fn bench_sparse_vs_dense(c: &mut Criterion) {
    let mut group = c.benchmark_group("sparse_vs_dense");
    
    // Dense automaton
    group.bench_function("dense_automaton_1000", |b| {
        let rules = AutomatonRules::conway_3d();
        let mut ca = CellularAutomaton3D::new(100, 100, 100, rules, 42).unwrap();
        
        // Set some initial cells
        ca.set_region(45, 45, 45, 55, 55, 55, 1);
        
        b.iter(|| {
            ca.step();
        });
    });
    
    // Sparse automaton
    group.bench_function("sparse_automaton_1000", |b| {
        let rules = AutomatonRules::conway_3d();
        let mut ca = SparseCellularAutomaton3D::new(100, 100, 100, rules, 42).unwrap();
        
        // Set some initial cells
        for x in 45..55 {
            for y in 45..55 {
                for z in 45..55 {
                    ca.set_cell(x, y, z, arxos_core::holographic::automata::CellState::Alive(1)).ok();
                }
            }
        }
        
        b.iter(|| {
            ca.step();
        });
    });
    
    group.finish();
}

fn bench_quantum_parallel(c: &mut Criterion) {
    let mut group = c.benchmark_group("quantum_parallel");
    
    // Interference pattern calculation
    group.bench_function("interference_pattern_10000", |b| {
        let calculator = ParallelInterferenceCalculator::new();
        
        let points: Vec<_> = (0..10000)
            .map(|i| {
                let x = (i % 100) as f32;
                let y = ((i / 100) % 100) as f32;
                let z = (i / 10000) as f32;
                (x, y, z)
            })
            .collect();
        
        let sources = vec![
            (0.0, 0.0, 0.0, 1.0),
            (100.0, 0.0, 0.0, 1.0),
            (50.0, 50.0, 0.0, 0.5),
        ];
        
        b.iter(|| {
            calculator.calculate_pattern(
                black_box(points.clone()),
                black_box(sources.clone()),
                black_box(1.0),
            )
        });
    });
    
    group.finish();
}

fn bench_memory_efficiency(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_efficiency");
    
    // Sparse grid memory usage
    group.bench_function("sparse_grid_set_get", |b| {
        let mut grid: SparseGrid3D<i32> = SparseGrid3D::new(1000, 1000, 1000);
        
        b.iter(|| {
            // Set sparse values
            for i in 0..100 {
                grid.set(i * 10, i * 10, i * 10, i as i32).ok();
            }
            
            // Get values
            for i in 0..100 {
                black_box(grid.get(i * 10, i * 10, i * 10));
            }
        });
    });
    
    group.finish();
}

// Async benchmarks need special handling
fn bench_async_consciousness(c: &mut Criterion) {
    let runtime = tokio::runtime::Runtime::new().unwrap();
    
    let mut group = c.benchmark_group("async_consciousness");
    group.measurement_time(Duration::from_secs(10));
    
    group.bench_function("async_batch_update_1000", |b| {
        b.to_async(&runtime).iter(|| async {
            let consciousness = AsyncBuildingConsciousness::new();
            
            let objects: Vec<_> = (0..1000)
                .map(|i| {
                    let obj = ArxObject::new(i as u16, 1, 100, 100, 100);
                    let field = ConsciousnessField::from_arxobject(&obj);
                    (obj, field)
                })
                .collect();
            
            consciousness.batch_update(black_box(objects)).await.ok();
            consciousness.evolve_consciousness(0.1).await.ok();
            
            consciousness.shutdown().await;
        });
    });
    
    group.finish();
}

criterion_group!(
    benches,
    bench_consciousness_phi,
    bench_spatial_index,
    bench_sparse_vs_dense,
    bench_quantum_parallel,
    bench_memory_efficiency,
    bench_async_consciousness
);
criterion_main!(benches);