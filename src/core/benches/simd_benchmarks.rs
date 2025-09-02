//! SIMD Performance Benchmarks
//! 
//! Comprehensive benchmarks comparing SIMD vs scalar implementations
//! for noise generation, quantum calculations, and consciousness fields.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use arxos_core::holographic::{
    noise::{perlin_3d, fractal_noise_3d},
    noise_simd::{perlin_3d_simd_x4, fractal_noise_simd, generate_noise_field},
    quantum_simd::{
        calculate_amplitudes_simd, calculate_entanglement_simd,
        quantum_interference_simd, tunneling_probability_simd,
    },
    consciousness::{ConsciousnessField, QualiaSpace},
    consciousness_simd::{
        calculate_phi_batch_simd, integrate_information_simd,
        calculate_resonance_simd,
    },
};
use rand::prelude::*;

/// Benchmark Perlin noise: SIMD vs scalar
fn bench_perlin_noise(c: &mut Criterion) {
    let mut group = c.benchmark_group("perlin_noise");
    let seed = 12345u64;
    
    // Test different batch sizes
    for size in [4, 16, 64, 256, 1024].iter() {
        let points: Vec<(f32, f32, f32)> = (0..*size)
            .map(|i| {
                let f = i as f32 * 0.1;
                (f, f * 1.1, f * 1.2)
            })
            .collect();
        
        // Scalar version
        group.bench_with_input(
            BenchmarkId::new("scalar", size),
            size,
            |b, _| {
                b.iter(|| {
                    for &(x, y, z) in &points {
                        black_box(perlin_3d(seed, x, y, z));
                    }
                });
            },
        );
        
        // SIMD version (process in batches of 4)
        #[cfg(target_arch = "x86_64")]
        group.bench_with_input(
            BenchmarkId::new("simd", size),
            size,
            |b, _| {
                b.iter(|| {
                    for chunk in points.chunks(4) {
                        let mut x_batch = [0.0f32; 4];
                        let mut y_batch = [0.0f32; 4];
                        let mut z_batch = [0.0f32; 4];
                        
                        for (i, &(x, y, z)) in chunk.iter().enumerate() {
                            x_batch[i] = x;
                            y_batch[i] = y;
                            z_batch[i] = z;
                        }
                        
                        black_box(perlin_3d_simd_x4(seed, x_batch, y_batch, z_batch));
                    }
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark fractal noise generation
fn bench_fractal_noise(c: &mut Criterion) {
    let mut group = c.benchmark_group("fractal_noise");
    let seed = 42u64;
    let octaves = 4;
    let persistence = 0.5;
    let lacunarity = 2.0;
    
    for size in [100, 500, 1000, 5000].iter() {
        let points: Vec<(f32, f32, f32)> = (0..*size)
            .map(|i| {
                let f = i as f32 * 0.01;
                (f, f * 1.1, f * 1.2)
            })
            .collect();
        
        // Scalar version
        group.bench_with_input(
            BenchmarkId::new("scalar", size),
            size,
            |b, _| {
                b.iter(|| {
                    for &(x, y, z) in &points {
                        black_box(fractal_noise_3d(
                            seed, x, y, z, octaves, persistence, lacunarity
                        ));
                    }
                });
            },
        );
        
        // SIMD batch version
        group.bench_with_input(
            BenchmarkId::new("simd_batch", size),
            size,
            |b, _| {
                b.iter(|| {
                    black_box(fractal_noise_simd(
                        seed, &points, octaves, persistence, lacunarity
                    ));
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark noise field generation
fn bench_noise_field(c: &mut Criterion) {
    let mut group = c.benchmark_group("noise_field_3d");
    
    for dimension in [16, 32, 64].iter() {
        let size = dimension * dimension * dimension;
        
        group.bench_with_input(
            BenchmarkId::new("simd_field", size),
            dimension,
            |b, &dim| {
                b.iter(|| {
                    black_box(generate_noise_field(
                        42, dim, dim, dim, 0.1, 4, 0.5, 2.0
                    ));
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark quantum amplitude calculations
fn bench_quantum_amplitudes(c: &mut Criterion) {
    let mut group = c.benchmark_group("quantum_amplitudes");
    let mut rng = thread_rng();
    
    for size in [16, 64, 256, 1024].iter() {
        let states: Vec<f32> = (0..*size).map(|_| rng.gen_range(0.0..1.0)).collect();
        let phases: Vec<f32> = (0..*size).map(|_| rng.gen_range(0.0..6.28)).collect();
        let time = 1.0;
        
        // SIMD version
        #[cfg(target_arch = "x86_64")]
        group.bench_with_input(
            BenchmarkId::new("simd", size),
            size,
            |b, _| {
                b.iter(|| {
                    black_box(unsafe {
                        calculate_amplitudes_simd(&states, &phases, time)
                    });
                });
            },
        );
        
        // Scalar version for comparison
        group.bench_with_input(
            BenchmarkId::new("scalar", size),
            size,
            |b, _| {
                b.iter(|| {
                    let result: Vec<f32> = states.iter()
                        .zip(phases.iter())
                        .map(|(&s, &p)| s * (p * time).cos())
                        .collect();
                    black_box(result);
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark quantum interference patterns
fn bench_quantum_interference(c: &mut Criterion) {
    let mut group = c.benchmark_group("quantum_interference");
    
    for num_points in [10, 50, 100, 500].iter() {
        let positions: Vec<(f32, f32, f32)> = (0..*num_points)
            .map(|i| (i as f32, 0.0, 0.0))
            .collect();
        
        // Double slit sources
        let sources = vec![
            (-1.0, 0.0, 0.0, 1.0),
            (1.0, 0.0, 0.0, 1.0),
        ];
        
        group.bench_with_input(
            BenchmarkId::new("simd", num_points),
            num_points,
            |b, _| {
                b.iter(|| {
                    black_box(quantum_interference_simd(&positions, &sources, 0.5));
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark consciousness phi calculations
fn bench_consciousness_phi(c: &mut Criterion) {
    let mut group = c.benchmark_group("consciousness_phi");
    let mut rng = thread_rng();
    
    for size in [8, 32, 128, 512].iter() {
        let fields: Vec<ConsciousnessField> = (0..*size)
            .map(|_| ConsciousnessField {
                phi: rng.gen_range(0.0..1.0),
                strength: rng.gen_range(0.5..1.0),
                coherence: rng.gen_range(0.3..0.9),
                causal_power: rng.gen_range(0.4..0.8),
                resonance_frequency: rng.gen_range(5.0..15.0),
                qualia: QualiaSpace::default(),
            })
            .collect();
        
        // SIMD version
        #[cfg(target_arch = "x86_64")]
        group.bench_with_input(
            BenchmarkId::new("simd", size),
            size,
            |b, _| {
                b.iter(|| {
                    black_box(unsafe {
                        calculate_phi_batch_simd(&fields)
                    });
                });
            },
        );
        
        // Scalar version
        group.bench_with_input(
            BenchmarkId::new("scalar", size),
            size,
            |b, _| {
                b.iter(|| {
                    let result: Vec<f32> = fields.iter()
                        .map(|f| f.phi * f.strength * f.coherence * f.causal_power)
                        .collect();
                    black_box(result);
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark information integration
fn bench_information_integration(c: &mut Criterion) {
    let mut group = c.benchmark_group("information_integration");
    let mut rng = thread_rng();
    
    for size in [64, 256, 1024].iter() {
        let field1: Vec<f32> = (0..*size).map(|_| rng.gen_range(0.0..1.0)).collect();
        let field2: Vec<f32> = (0..*size).map(|_| rng.gen_range(0.0..1.0)).collect();
        let coupling = 0.5;
        
        // SIMD version
        #[cfg(target_arch = "x86_64")]
        group.bench_with_input(
            BenchmarkId::new("simd", size),
            size,
            |b, _| {
                b.iter(|| {
                    black_box(unsafe {
                        integrate_information_simd(&field1, &field2, coupling)
                    });
                });
            },
        );
        
        // Scalar version
        group.bench_with_input(
            BenchmarkId::new("scalar", size),
            size,
            |b, _| {
                b.iter(|| {
                    let result: Vec<f32> = field1.iter()
                        .zip(field2.iter())
                        .map(|(&p1, &p2)| {
                            let sum = p1 + p2;
                            let diff = (p1 - p2).abs();
                            sum * coupling / (1.0 + diff)
                        })
                        .collect();
                    black_box(result);
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark quantum tunneling probability
fn bench_quantum_tunneling(c: &mut Criterion) {
    let mut group = c.benchmark_group("quantum_tunneling");
    let mut rng = thread_rng();
    
    for size in [100, 500, 2000].iter() {
        let energies: Vec<f32> = (0..*size)
            .map(|_| rng.gen_range(0.0..3.0))
            .collect();
        
        let barrier_height = 2.0;
        let barrier_width = 1.0;
        let mass = 1.0;
        
        #[cfg(target_arch = "x86_64")]
        group.bench_with_input(
            BenchmarkId::new("simd", size),
            size,
            |b, _| {
                b.iter(|| {
                    black_box(tunneling_probability_simd(
                        &energies, barrier_height, barrier_width, mass
                    ));
                });
            },
        );
    }
    
    group.finish();
}

criterion_group!(
    benches,
    bench_perlin_noise,
    bench_fractal_noise,
    bench_noise_field,
    bench_quantum_amplitudes,
    bench_quantum_interference,
    bench_consciousness_phi,
    bench_information_integration,
    bench_quantum_tunneling,
);

criterion_main!(benches);