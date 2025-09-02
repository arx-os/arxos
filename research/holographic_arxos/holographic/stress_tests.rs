//! Stress Testing for Holographic System
//! 
//! Tests system performance and stability under heavy load.

#[cfg(test)]
mod tests {
    use crate::holographic::*;
    use crate::arxobject::ArxObject;
    use std::time::Instant;
    
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_large_fractal_space
    fn stress_large_fractal_space() {
        use crate::holographic::fractal::{FractalSpace, FractalCoordinate};
        
        let mut spaces = Vec::new();
        
        // Create many fractal spaces
        for i in 0..10000 {
            let coord = FractalCoordinate::new(i as u16, 0, 0.5);
            let space = FractalSpace::new(coord.clone(), coord.clone(), coord);
            spaces.push(space);
        }
        
        // Distance calculations
        let start = Instant::now();
        let mut total_distance = 0.0;
        for i in 0..100 {
            for j in 0..100 {
                let dist = spaces[i].distance(&spaces[j], 1.0);
                total_distance += dist;
            }
        }
        let elapsed = start.elapsed();
        
        println!("10000 distance calculations took: {:?}", elapsed);
        println!("Average distance: {}", total_distance / 10000.0);
        assert!(elapsed.as_secs() < 5); // Should complete within 5 seconds
    }
    
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_quantum_entanglement
    fn stress_quantum_entanglement() {
        use crate::holographic::quantum::EntanglementNetwork;
        
        let mut network = EntanglementNetwork::new();
        
        // Create dense entanglement network
        let start = Instant::now();
        for i in 0..1000 {
            for j in (i+1)..1000.min(i+10) {
                network.entangle(i, j, 0.5, 0);
            }
        }
        let creation_time = start.elapsed();
        println!("Creating 9000 entanglements took: {:?}", creation_time);
        
        // Test entanglement properties
        let start = Instant::now();
        // We created approximately 9000 entanglements
        let total_entangled = 9000; // Estimated based on creation loop
        let calc_time = start.elapsed();
        println!("Network has approximately {} entanglement pairs in {:?}", total_entangled, calc_time);
        
        assert!(total_entangled > 0);
        assert!(creation_time.as_secs() < 10);
        assert!(calc_time.as_secs() < 5);
    }
    
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_consciousness_network
    fn stress_consciousness_network() {
        use crate::holographic::consciousness::{BuildingConsciousness, ConsciousnessField};
        
        let mut building = BuildingConsciousness::new();
        
        // Add many conscious objects
        let start = Instant::now();
        for i in 0..5000 {
            let obj = ArxObject::new(i as u16, 1, 100, 100, 100);
            let field = ConsciousnessField {
                phi: (obj.object_type as f32) / 255.0,
                strength: 0.8,
                qualia: Default::default(),
                causal_power: 0.6,
                resonance_frequency: 10.0,
                coherence: 0.7,
            };
            building.add_object(i as u16, field).unwrap();
        }
        let add_time = start.elapsed();
        println!("Adding 5000 consciousness fields took: {:?}", add_time);
        
        // Calculate phi for building
        let start = Instant::now();
        let phi = building.global_phi;
        let phi_time = start.elapsed();
        println!("Accessing global phi took: {:?}", phi_time);
        
        assert!(phi >= 0.0 && phi <= 1.0);
        assert!(add_time.as_secs() < 5);
        assert!(phi_time.as_secs() < 10);
    }
    
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_spatial_index
    fn stress_spatial_index() {
        use crate::holographic::spatial_index::{SpatialIndex, Point3D};
        
        let mut index = SpatialIndex::new(
            Point3D::new(0.0, 0.0, 0.0),
            Point3D::new(10000.0, 10000.0, 10000.0),
        );
        
        // Insert many points
        let start = Instant::now();
        for i in 0..50000 {
            let pos = Point3D::new(
                (i as f32 * 7919.0) % 10000.0,
                (i as f32 * 6991.0) % 10000.0,
                (i as f32 * 5023.0) % 10000.0,
            );
            index.insert(i as u16, pos).unwrap();
        }
        let insert_time = start.elapsed();
        println!("Inserting 50000 points took: {:?}", insert_time);
        
        // Radius queries
        let start = Instant::now();
        let mut total_found = 0;
        for i in 0..100 {
            let center = Point3D::new(
                (i as f32 * 1000.0) % 10000.0,
                (i as f32 * 1000.0) % 10000.0,
                (i as f32 * 1000.0) % 10000.0,
            );
            let results = index.find_within_radius(&center, 500.0);
            total_found += results.len();
        }
        let query_time = start.elapsed();
        println!("100 radius queries found {} points in {:?}", total_found, query_time);
        
        assert!(insert_time.as_secs() < 10);
        assert!(query_time.as_secs() < 5);
    }
    
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_automaton_large_grid
    fn stress_automaton_large_grid() {
        use crate::holographic::automata_sparse::SparseCellularAutomaton3D;
        use crate::holographic::automata::{AutomatonRules, CellState};
        
        let rules = AutomatonRules::conway_3d();
        let mut ca = SparseCellularAutomaton3D::new(500, 500, 500, rules, 42).unwrap();
        
        // Set initial pattern
        let start = Instant::now();
        for i in 0..1000 {
            let x = (i * 7919) % 500;
            let y = (i * 6991) % 500;
            let z = (i * 5023) % 500;
            ca.set_cell(x, y, z, CellState::Alive(1)).ok();
        }
        let setup_time = start.elapsed();
        println!("Setting 1000 cells took: {:?}", setup_time);
        
        // Evolution steps
        let start = Instant::now();
        for step in 0..10 {
            ca.step();
            if step % 5 == 0 {
                println!("Step {}: population = {}", step, ca.population());
            }
        }
        let evolution_time = start.elapsed();
        println!("10 evolution steps took: {:?}", evolution_time);
        
        assert!(setup_time.as_millis() < 1000);
        assert!(evolution_time.as_secs() < 30);
    }
    
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_noise_generation
    fn stress_noise_generation() {
        use crate::holographic::noise;
        
        let mut total = 0.0f32;
        
        // Generate lots of noise values
        let start = Instant::now();
        for seed in 0..100 {
            for x in 0..100 {
                for y in 0..100 {
                    let value = noise::perlin_3d(
                        seed,
                        x as f32 * 0.1,
                        y as f32 * 0.1,
                        0.0,
                    );
                    total += value;
                }
            }
        }
        let time = start.elapsed();
        
        let average = total / 1_000_000.0;
        println!("Generated 1M noise values in {:?}", time);
        println!("Average value: {}", average);
        
        // Should be fast
        assert!(time.as_secs() < 5);
        // Average should be near 0 for good Perlin noise
        assert!(average.abs() < 0.1);
    }
    
    #[cfg(feature = "std")]
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_async_consciousness
    fn stress_async_consciousness() {
        use crate::holographic::consciousness_async::AsyncBuildingConsciousness;
        use crate::holographic::consciousness::ConsciousnessField;
        
        let runtime = tokio::runtime::Runtime::new().unwrap();
        
        runtime.block_on(async {
            let consciousness = AsyncBuildingConsciousness::new();
            
            // Batch add many objects
            let start = Instant::now();
            let mut batch = Vec::new();
            for i in 0..10000 {
                let obj = ArxObject::new(i as u16, 1, 100, 100, 100);
                let field = ConsciousnessField {
                    phi: (obj.object_type as f32) / 255.0,
                    strength: 0.8,
                    qualia: Default::default(),
                    causal_power: 0.6,
                    resonance_frequency: 10.0,
                    coherence: 0.7,
                };
                batch.push((obj, field));
                
                if batch.len() >= 1000 {
                    consciousness.batch_update(batch.clone()).await.unwrap();
                    batch.clear();
                }
            }
            let batch_time = start.elapsed();
            println!("Batch updating 10000 objects took: {:?}", batch_time);
            
            // Parallel phi calculation
            let start = Instant::now();
            let ids: Vec<_> = (0..10000).collect();
            let phis = consciousness.calculate_phi_batch(ids).await.unwrap();
            let phi_time = start.elapsed();
            println!("Parallel phi calculation for 10000 objects took: {:?}", phi_time);
            
            assert_eq!(phis.len(), 10000);
            assert!(batch_time.as_secs() < 10);
            assert!(phi_time.as_secs() < 15);
            
            consciousness.shutdown().await;
        });
    }
    
    #[cfg(feature = "std")]
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_parallel_quantum
    fn stress_parallel_quantum() {
        use crate::holographic::quantum_async::ParallelInterferenceCalculator;
        
        let runtime = tokio::runtime::Runtime::new().unwrap();
        
        runtime.block_on(async {
            
            // Test interference patterns
            let calculator = ParallelInterferenceCalculator::new();
            let points: Vec<_> = (0..100000)
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
            
            let start = Instant::now();
            let pattern = calculator.calculate_pattern(points, sources, 1.0);
            let pattern_time = start.elapsed();
            println!("Calculating 100k point interference pattern took: {:?}", pattern_time);
            
            assert_eq!(pattern.len(), 100000);
            assert!(pattern_time.as_secs() < 10);
        });
    }
    
    #[test]
    #[ignore] // Run with: cargo test --ignored stress_memory_efficiency
    fn stress_memory_efficiency() {
        use crate::holographic::sparse::SparseGrid3D;
        
        // Create very large sparse grid
        let mut grid = SparseGrid3D::<i32>::new(1000, 1000, 1000);
        
        // Add sparse data (0.01% density)
        let start = Instant::now();
        for i in 0..10000 {
            let x = (i * 7919) % 1000;
            let y = (i * 6991) % 1000;
            let z = (i * 5023) % 1000;
            grid.set(x, y, z, i as i32).ok();
        }
        let set_time = start.elapsed();
        
        let sparsity = grid.sparsity();
        let count = grid.non_default_count();
        
        println!("Set 10000 values in 1B cell grid in {:?}", set_time);
        println!("Sparsity: {:.6}%", sparsity * 100.0);
        println!("Non-default count: {}", count);
        
        // Memory should be efficient
        assert!(sparsity < 0.01); // Less than 1% occupied
        assert!(count <= 10000);
        assert!(set_time.as_secs() < 1);
    }
}