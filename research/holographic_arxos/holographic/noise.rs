//! Deterministic Noise Functions
//! 
//! Implements Perlin noise and fractal Brownian motion for organic
//! procedural generation with deterministic reproducibility.

use core::f32::consts::PI;

/// Hash function for deterministic randomness
#[inline]
fn hash(seed: u64, x: i32, y: i32, z: i32) -> f32 {
    let mut h = seed;
    h ^= (x as u64).wrapping_mul(0x1f1f1f1f1f1f1f1f);
    h ^= (y as u64).wrapping_mul(0x2e2e2e2e2e2e2e2e);
    h ^= (z as u64).wrapping_mul(0x3d3d3d3d3d3d3d3d);
    h = h.wrapping_mul(0x94d049bb133111eb);
    h ^= h >> 30;
    h = h.wrapping_mul(0xbf58476d1ce4e5b9);
    h ^= h >> 27;
    
    // Convert to float in range [0, 1]
    ((h & 0xFFFFFF) as f32) / 16777216.0
}

/// Smooth interpolation curve (Ken Perlin's improved version)
#[inline]
fn fade(t: f32) -> f32 {
    // 6t^5 - 15t^4 + 10t^3
    t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
}

/// Linear interpolation
#[inline]
fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + t * (b - a)
}

/// Trilinear interpolation for 3D
#[inline]
fn trilinear_interp(
    c000: f32, c001: f32, c010: f32, c011: f32,
    c100: f32, c101: f32, c110: f32, c111: f32,
    u: f32, v: f32, w: f32,
) -> f32 {
    let c00 = lerp(c000, c100, u);
    let c01 = lerp(c001, c101, u);
    let c10 = lerp(c010, c110, u);
    let c11 = lerp(c011, c111, u);
    
    let c0 = lerp(c00, c10, v);
    let c1 = lerp(c01, c11, v);
    
    lerp(c0, c1, w)
}

/// 3D gradient for Perlin noise
#[inline]
fn gradient_3d(hash: f32, x: f32, y: f32, z: f32) -> f32 {
    // Convert hash to gradient index (12 possible gradients)
    let h = (hash * 12.0) as u32;
    
    // Gradient vectors for 3D Perlin noise
    let (gx, gy, gz) = match h {
        0 => (1.0, 1.0, 0.0),
        1 => (-1.0, 1.0, 0.0),
        2 => (1.0, -1.0, 0.0),
        3 => (-1.0, -1.0, 0.0),
        4 => (1.0, 0.0, 1.0),
        5 => (-1.0, 0.0, 1.0),
        6 => (1.0, 0.0, -1.0),
        7 => (-1.0, 0.0, -1.0),
        8 => (0.0, 1.0, 1.0),
        9 => (0.0, -1.0, 1.0),
        10 => (0.0, 1.0, -1.0),
        11 => (0.0, -1.0, -1.0),
        _ => (1.0, 1.0, 0.0),
    };
    
    // Dot product with distance vector
    gx * x + gy * y + gz * z
}

/// Generate smooth 3D Perlin noise
pub fn perlin_3d(seed: u64, x: f32, y: f32, z: f32) -> f32 {
    // Integer coordinates of containing cube
    let x0 = x.floor() as i32;
    let y0 = y.floor() as i32;
    let z0 = z.floor() as i32;
    
    // Fractional coordinates within cube
    let fx = x - x0 as f32;
    let fy = y - y0 as f32;
    let fz = z - z0 as f32;
    
    // Smooth interpolation curves
    let u = fade(fx);
    let v = fade(fy);
    let w = fade(fz);
    
    // Hash and gradient at each corner of the cube
    let mut corners = [0.0; 8];
    let positions = [
        (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0),
        (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1),
    ];
    
    for (i, &(dx, dy, dz)) in positions.iter().enumerate() {
        let h = hash(seed, x0 + dx, y0 + dy, z0 + dz);
        let gx = fx - dx as f32;
        let gy = fy - dy as f32;
        let gz = fz - dz as f32;
        corners[i] = gradient_3d(h, gx, gy, gz);
    }
    
    // Trilinear interpolation
    let result = trilinear_interp(
        corners[0], corners[4], corners[2], corners[6],
        corners[1], corners[5], corners[3], corners[7],
        u, v, w,
    );
    
    // Normalize to approximately [-1, 1]
    result.clamp(-1.0, 1.0)
}

/// 3D fractal noise with multiple octaves (fractal Brownian motion)
pub fn fractal_noise_3d(
    seed: u64,
    x: f32,
    y: f32,
    z: f32,
    octaves: u8,
    persistence: f32,
    lacunarity: f32,
) -> f32 {
    let mut value = 0.0;
    let mut amplitude = 1.0;
    let mut frequency = 1.0;
    let mut max_value = 0.0;
    
    for octave in 0..octaves {
        // Add noise at this octave
        let noise = perlin_3d(
            seed ^ (octave as u64),
            x * frequency,
            y * frequency,
            z * frequency,
        );
        value += noise * amplitude;
        
        // Track maximum for normalization
        max_value += amplitude;
        
        // Update for next octave
        amplitude *= persistence;
        frequency *= lacunarity;
    }
    
    // Normalize to [-1, 1]
    value / max_value
}

/// Turbulence function (absolute value of noise)
pub fn turbulence_3d(
    seed: u64,
    x: f32,
    y: f32,
    z: f32,
    octaves: u8,
) -> f32 {
    let mut value = 0.0;
    let mut amplitude = 1.0;
    let mut frequency = 1.0;
    
    for octave in 0..octaves {
        let noise = perlin_3d(
            seed ^ (octave as u64),
            x * frequency,
            y * frequency,
            z * frequency,
        );
        value += noise.abs() * amplitude;
        amplitude *= 0.5;
        frequency *= 2.0;
    }
    
    value
}

/// Ridged noise (inverted absolute value)
pub fn ridged_noise_3d(
    seed: u64,
    x: f32,
    y: f32,
    z: f32,
    octaves: u8,
    ridge_offset: f32,
) -> f32 {
    let mut value = 0.0;
    let mut amplitude = 1.0;
    let mut frequency = 1.0;
    let mut weight = 1.0;
    
    for octave in 0..octaves {
        let noise = perlin_3d(
            seed ^ (octave as u64),
            x * frequency,
            y * frequency,
            z * frequency,
        );
        
        // Ridge calculation
        let ridge = (ridge_offset - noise.abs()).max(0.0);
        value += ridge * ridge * weight;
        
        // Update weight based on current value
        weight = value.clamp(0.0, 1.0);
        
        amplitude *= 0.5;
        frequency *= 2.0;
    }
    
    value
}

/// Voronoi/Worley noise for cellular patterns
pub fn voronoi_3d(seed: u64, x: f32, y: f32, z: f32) -> (f32, f32) {
    let x0 = x.floor() as i32;
    let y0 = y.floor() as i32;
    let z0 = z.floor() as i32;
    
    let mut min_dist = f32::MAX;
    let mut second_min = f32::MAX;
    
    // Check neighboring cells
    for dx in -1..=1 {
        for dy in -1..=1 {
            for dz in -1..=1 {
                let cell_x = x0 + dx;
                let cell_y = y0 + dy;
                let cell_z = z0 + dz;
                
                // Generate random point in this cell
                let px = cell_x as f32 + hash(seed, cell_x, cell_y, cell_z);
                let py = cell_y as f32 + hash(seed ^ 1, cell_x, cell_y, cell_z);
                let pz = cell_z as f32 + hash(seed ^ 2, cell_x, cell_y, cell_z);
                
                // Calculate distance
                let dist = ((x - px).powi(2) + (y - py).powi(2) + (z - pz).powi(2)).sqrt();
                
                if dist < min_dist {
                    second_min = min_dist;
                    min_dist = dist;
                } else if dist < second_min {
                    second_min = dist;
                }
            }
        }
    }
    
    (min_dist, second_min)
}

/// Domain warping for more organic patterns
pub fn domain_warp_3d(
    seed: u64,
    x: f32,
    y: f32,
    z: f32,
    warp_amount: f32,
    octaves: u8,
) -> f32 {
    // First warp
    let wx = fractal_noise_3d(seed, x, y, z, octaves, 0.5, 2.0) * warp_amount;
    let wy = fractal_noise_3d(seed ^ 1, x, y, z, octaves, 0.5, 2.0) * warp_amount;
    let wz = fractal_noise_3d(seed ^ 2, x, y, z, octaves, 0.5, 2.0) * warp_amount;
    
    // Second warp
    let wx2 = fractal_noise_3d(seed ^ 3, x + wx, y + wy, z + wz, octaves, 0.5, 2.0) * warp_amount;
    let wy2 = fractal_noise_3d(seed ^ 4, x + wx, y + wy, z + wz, octaves, 0.5, 2.0) * warp_amount;
    let wz2 = fractal_noise_3d(seed ^ 5, x + wx, y + wy, z + wz, octaves, 0.5, 2.0) * warp_amount;
    
    // Final noise with warped coordinates
    fractal_noise_3d(seed ^ 6, x + wx + wx2, y + wy + wy2, z + wz + wz2, octaves, 0.5, 2.0)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_hash_deterministic() {
        let seed = 42;
        let h1 = hash(seed, 10, 20, 30);
        let h2 = hash(seed, 10, 20, 30);
        assert_eq!(h1, h2);
        
        let h3 = hash(seed, 10, 20, 31);
        assert_ne!(h1, h3);
    }
    
    #[test]
    fn test_perlin_range() {
        let seed = 12345;
        for x in 0..10 {
            for y in 0..10 {
                for z in 0..10 {
                    let noise = perlin_3d(seed, x as f32 * 0.1, y as f32 * 0.1, z as f32 * 0.1);
                    assert!(noise >= -1.0 && noise <= 1.0);
                }
            }
        }
    }
    
    #[test]
    fn test_fractal_noise_octaves() {
        let seed = 999;
        let pos = (1.5, 2.5, 3.5);
        
        let noise1 = fractal_noise_3d(seed, pos.0, pos.1, pos.2, 1, 0.5, 2.0);
        let noise4 = fractal_noise_3d(seed, pos.0, pos.1, pos.2, 4, 0.5, 2.0);
        
        // More octaves should produce different (more detailed) result
        assert_ne!(noise1, noise4);
    }
    
    #[test]
    fn test_voronoi_distances() {
        let seed = 777;
        let (min_dist, second_min) = voronoi_3d(seed, 1.5, 2.5, 3.5);
        
        assert!(min_dist >= 0.0);
        assert!(second_min >= min_dist);
    }
}