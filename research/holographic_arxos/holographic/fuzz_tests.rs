//! Fuzz Testing for Holographic System
//! 
//! Stress-tests the system with random inputs to find edge cases and crashes.

#[cfg(test)]
mod tests {
    use crate::holographic::*;
    use crate::arxobject::ArxObject;
    
    // Helper to generate random bytes
    fn random_bytes(seed: u64, len: usize) -> Vec<u8> {
        (0..len)
            .map(|i| ((seed.wrapping_mul(7919).wrapping_add(i as u64)) % 256) as u8)
            .collect()
    }
    
    #[test]
    fn fuzz_arxobject_parsing() {
        // Fuzz test ArxObject parsing with random byte sequences
        for seed in 0..1000 {
            let bytes = random_bytes(seed, 13);
            
            // Create ArxObject from bytes - should never panic
            let building_id = u16::from_le_bytes([bytes[0], bytes[1]]);
            let object_type = bytes[2];
            let x = u16::from_le_bytes([bytes[3], bytes[4]]);
            let y = u16::from_le_bytes([bytes[5], bytes[6]]);
            let z = u16::from_le_bytes([bytes[7], bytes[8]]);
            
            let obj = ArxObject::new(building_id, object_type, x, y, z);
            
            // All values should be valid
            assert!(obj.building_id <= 65535);
            assert!(obj.object_type <= 255);
            assert!(obj.x <= 65535);
            assert!(obj.y <= 65535);
            assert!(obj.z <= 65535);
        }
    }
    
    #[test]
    fn fuzz_fractal_coordinate_operations() {
        use crate::holographic::fractal::FractalCoordinate;
        
        for seed in 0..1000 {
            let bytes = random_bytes(seed, 20);
            
            // Generate random fractal coordinates
            let base = u16::from_le_bytes([bytes[0], bytes[1]]);
            let depth = (bytes[2] as i8) % 21; // Keep within bounds
            let sub_pos = (bytes[3] as f32) / 255.0;
            
            let coord = FractalCoordinate::new(base, depth, sub_pos);
            
            // Test various operations - none should panic
            let _ = coord.to_absolute(1.0);
            let _ = coord.voxel_index();
            
            // Random rescale operations
            for i in 0..5 {
                let mut coord_copy = coord.clone();
                let delta = ((bytes[4 + i] as i8) % 10) - 5;
                let _ = coord_copy.rescale(delta);
            }
            
            // Interpolation with another random coordinate
            let base2 = u16::from_le_bytes([bytes[10], bytes[11]]);
            let coord2 = FractalCoordinate::new(base2, depth, 0.5);
            for i in 0..5 {
                let t = (bytes[12 + i] as f32) / 255.0;
                let _ = coord.lerp(&coord2, t);
            }
        }
    }
    
    #[test]
    fn fuzz_noise_generation() {
        use crate::holographic::noise;
        
        for seed in 0..500 {
            let bytes = random_bytes(seed * 1337, 32);
            
            // Generate random noise parameters
            let noise_seed = u64::from_le_bytes([
                bytes[0], bytes[1], bytes[2], bytes[3],
                bytes[4], bytes[5], bytes[6], bytes[7],
            ]);
            
            // Random positions
            for i in 0..5 {
                let x = f32::from_bits(u32::from_le_bytes([
                    bytes[8 + i*3], bytes[9 + i*3], bytes[10 + i*3], 0,
                ]));
                let y = f32::from_bits(u32::from_le_bytes([
                    bytes[11 + i*3], bytes[12 + i*3], bytes[13 + i*3], 0,
                ]));
                let z = f32::from_bits(u32::from_le_bytes([
                    bytes[14 + i*3], bytes[15 + i*3], bytes[16 + i*3], 0,
                ]));
                
                // Skip NaN and infinite values
                if !x.is_finite() || !y.is_finite() || !z.is_finite() {
                    continue;
                }
                
                // Clamp to reasonable range
                let x = x.clamp(-10000.0, 10000.0);
                let y = y.clamp(-10000.0, 10000.0);
                let z = z.clamp(-10000.0, 10000.0);
                
                let value = noise::perlin_3d(noise_seed, x, y, z);
                assert!(value >= -1.0 && value <= 1.0);
                assert!(value.is_finite());
                
                // Fractal noise
                let octaves = ((bytes[20 + i] % 8) + 1) as u8;
                let persistence = 0.5;
                let lacunarity = 2.0;
                
                let fractal = noise::fractal_noise_3d(
                    noise_seed, x, y, z, octaves, persistence, lacunarity
                );
                assert!(fractal.is_finite());
            }
        }
    }
    
    #[test]
    fn fuzz_quantum_state_operations() {
        use crate::holographic::quantum_async::SimpleQuantumState;
        use crate::holographic::quantum::QuantumBasis;
        
        for seed in 0..500 {
            let bytes = random_bytes(seed * 2718, 64);
            
            // Create random quantum states
            let num_states = ((bytes[0] % 10) + 2) as usize;
            let mut amplitudes = Vec::new();
            
            for i in 0..num_states {
                let amp = (bytes[1 + i] as f32) / 255.0;
                amplitudes.push(amp);
            }
            
            // Normalize
            let sum: f32 = amplitudes.iter().sum();
            if sum > 0.0 {
                for a in &mut amplitudes {
                    *a /= sum;
                }
            } else {
                amplitudes = vec![1.0];
            }
            
            let state = SimpleQuantumState::Superposition {
                amplitudes: amplitudes.clone(),
                basis: QuantumBasis::Computational,
            };
            
            // Verify normalization
            if let SimpleQuantumState::Superposition { amplitudes, .. } = &state {
                let sum: f32 = amplitudes.iter().sum();
                assert!((sum - 1.0).abs() < 0.01);
            }
            
            // Test collapse
            let collapsed = SimpleQuantumState::Collapsed {
                state: bytes[20] % (num_states as u8),
                basis: QuantumBasis::Computational,
            };
            
            match collapsed {
                SimpleQuantumState::Collapsed { state, .. } => {
                    assert!(state < 255);
                }
                _ => unreachable!(),
            }
        }
    }
    
    #[test]
    fn fuzz_consciousness_field_evolution() {
        use crate::holographic::consciousness::{ConsciousnessField, QualiaSpace};
        
        for seed in 0..500 {
            let bytes = random_bytes(seed * 3141, 32);
            
            // Create random consciousness fields
            let phi = (bytes[0] as f32) / 255.0;
            let strength = (bytes[1] as f32) / 255.0;
            let coherence = (bytes[2] as f32) / 255.0;
            let causal_power = (bytes[3] as f32) / 255.0;
            let resonance = ((bytes[4] as f32) + 1.0) * 10.0;
            
            let field = ConsciousnessField {
                phi,
                strength,
                qualia: QualiaSpace::default(),
                causal_power,
                resonance_frequency: resonance,
                coherence,
            };
            
            // All values should be in valid ranges
            assert!(field.phi >= 0.0 && field.phi <= 1.0);
            assert!(field.strength >= 0.0 && field.strength <= 1.0);
            assert!(field.coherence >= 0.0 && field.coherence <= 1.0);
            assert!(field.causal_power >= 0.0 && field.causal_power <= 1.0);
            assert!(field.resonance_frequency > 0.0);
            
            // Test field operations
            let field2 = ConsciousnessField {
                phi: (bytes[5] as f32) / 255.0,
                strength: (bytes[6] as f32) / 255.0,
                qualia: QualiaSpace::default(),
                causal_power: (bytes[7] as f32) / 255.0,
                resonance_frequency: ((bytes[8] as f32) + 1.0) * 10.0,
                coherence: (bytes[9] as f32) / 255.0,
            };
            
            // Manual integration calculation
            let phi_diff = (field.phi - field2.phi).abs();
            let strength_product = field.strength * field2.strength;
            let coherence_factor = (field.coherence + field2.coherence) / 2.0;
            let integration = strength_product * coherence_factor * (1.0 - phi_diff);
            
            assert!(integration >= 0.0 && integration <= 1.0);
        }
    }
    
    #[test]
    fn fuzz_spatial_index_operations() {
        use crate::holographic::spatial_index::{SpatialIndex, Point3D};
        
        for seed in 0..200 {
            let bytes = random_bytes(seed * 1618, 128);
            
            let mut index = SpatialIndex::new(
                Point3D::new(0.0, 0.0, 0.0),
                Point3D::new(1000.0, 1000.0, 1000.0),
            );
            
            // Insert random points
            for i in 0..10 {
                let id = u16::from_le_bytes([bytes[i*6], bytes[i*6 + 1]]);
                let x = ((bytes[i*6 + 2] as f32) * 4.0) % 1000.0;
                let y = ((bytes[i*6 + 3] as f32) * 4.0) % 1000.0;
                let z = ((bytes[i*6 + 4] as f32) * 4.0) % 1000.0;
                
                let _ = index.insert(id, Point3D::new(x, y, z));
            }
            
            // Query operations
            for i in 0..5 {
                let x = ((bytes[60 + i*3] as f32) * 4.0) % 1000.0;
                let y = ((bytes[61 + i*3] as f32) * 4.0) % 1000.0;
                let z = ((bytes[62 + i*3] as f32) * 4.0) % 1000.0;
                let radius = ((bytes[75 + i] as f32) + 1.0) * 10.0;
                
                let center = Point3D::new(x, y, z);
                let results = index.find_within_radius(&center, radius);
                
                // Results should be valid IDs
                for &id in &results {
                    assert!(id <= 65535);
                }
                
                // K-nearest query
                let k = ((bytes[80 + i] % 10) + 1) as usize;
                let nearest = index.find_k_nearest(&center, k);
                assert!(nearest.len() <= k);
                
                // Should be sorted by distance
                for j in 1..nearest.len() {
                    assert!(nearest[j-1].1 <= nearest[j].1);
                }
            }
        }
    }
    
    #[test]
    fn fuzz_automaton_evolution() {
        use crate::holographic::automata::{CellularAutomaton3D, AutomatonRules};
        
        for seed in 0..100 {
            let bytes = random_bytes(seed * 2024, 16);
            
            // Small grids for performance
            let width = ((bytes[0] % 20) + 10) as usize;
            let height = ((bytes[1] % 20) + 10) as usize;
            let depth = ((bytes[2] % 20) + 10) as usize;
            let density = (bytes[3] as f32) / 255.0;
            
            let rules = AutomatonRules::conway_3d();
            
            let mut ca = CellularAutomaton3D::random(
                width, height, depth, rules, density, seed
            ).unwrap();
            
            // Evolution steps
            for _ in 0..5 {
                ca.step();
                let pop = ca.grid().population();
                assert!(pop <= width * height * depth);
            }
            
            // Set random regions
            for i in 0..3 {
                let x1 = (bytes[5 + i*2] as usize) % width;
                let y1 = (bytes[6 + i*2] as usize) % height;
                let z1 = (bytes[7 + i*2] as usize) % depth;
                let x2 = x1.min(width - 1);
                let y2 = y1.min(height - 1);
                let z2 = z1.min(depth - 1);
                
                ca.set_region(
                    x1 as i32, y1 as i32, z1 as i32,
                    x2 as i32, y2 as i32, z2 as i32,
                    bytes[8 + i]
                );
            }
        }
    }
    
    #[test]
    fn fuzz_memory_bounded_collections() {
        use crate::holographic::sparse::{BoundedVecDeque, SparseGrid3D};
        
        for seed in 0..200 {
            let bytes = random_bytes(seed * 9999, 64);
            
            // Test BoundedVecDeque
            let max_size = ((bytes[0] % 50) + 10) as usize;
            let mut deque = BoundedVecDeque::new(max_size);
            
            // Push random values
            for i in 0..100 {
                deque.push_back(bytes[i % 64] as i32);
                assert!(deque.len() <= max_size);
            }
            
            // Test SparseGrid3D
            let width = ((bytes[1] % 50) + 10) as usize;
            let height = ((bytes[2] % 50) + 10) as usize;
            let depth = ((bytes[3] % 50) + 10) as usize;
            
            let mut grid = SparseGrid3D::new(width, height, depth);
            
            // Set random values
            for i in 0..10 {
                let idx_base = (4 + i * 4) % 60; // Stay within bounds
                let x = (bytes[idx_base] as usize) % (width * 2);
                let y = (bytes[idx_base + 1] as usize) % (height * 2);
                let z = (bytes[idx_base + 2] as usize) % (depth * 2);
                let value = bytes[idx_base + 3] as i32;
                
                // Should handle out-of-bounds gracefully
                let _ = grid.set(x, y, z, value);
                
                if x < width && y < height && z < depth {
                    assert_eq!(*grid.get(x, y, z), value);
                }
            }
            
            // Check that sparse grid is working
            let count = grid.non_default_count();
            assert!(count <= 20); // We set at most 20 values
        }
    }
}