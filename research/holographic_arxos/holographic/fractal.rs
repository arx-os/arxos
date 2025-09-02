//! Fractal Coordinate System
//! 
//! Implements infinite-precision coordinates using fractal mathematics
//! allowing seamless zoom from atomic to cosmic scales.

use crate::holographic::error::{FractalError, Result, validation};
use core::ops::{Add, Sub, Mul};

/// Helper trait for checked float operations
trait CheckedFloat {
    fn checked_powi(self, n: i32) -> Option<Self> where Self: Sized;
}

impl CheckedFloat for f32 {
    fn checked_powi(self, n: i32) -> Option<Self> {
        // Check for potential overflow
        if n.abs() > 20 {  // 3^20 is already very large
            return None;
        }
        let result = self.powi(n);
        if result.is_finite() {
            Some(result)
        } else {
            None
        }
    }
}

/// Fractal coordinate with infinite precision across scales
#[derive(Clone, Debug, PartialEq)]
pub struct FractalCoordinate {
    /// Base coordinate in millimeters (0-65535)
    pub base: u16,
    
    /// Fractal depth (negative = zoom out, positive = zoom in)
    /// Each level represents a factor of 3 in scale
    pub depth: i8,
    
    /// Sub-position within current voxel (0.0-1.0)
    /// Provides smooth interpolation between discrete levels
    pub sub_position: f32,
}

impl FractalCoordinate {
    /// Create a new fractal coordinate
    pub fn new(base: u16, depth: i8, sub_position: f32) -> Self {
        Self {
            base,
            depth,
            sub_position: sub_position.clamp(0.0, 1.0),
        }
    }
    
    /// Create from millimeter position
    pub fn from_mm(mm: u16) -> Self {
        Self {
            base: mm,
            depth: 0,
            sub_position: 0.0,
        }
    }
    
    /// Convert to absolute position at given scale
    pub fn to_absolute(&self, scale: f32) -> f64 {
        let base_meters = self.base as f64 / 1000.0;
        let scale_factor = (3.0_f64).powi(self.depth as i32);
        let scaled_position = base_meters * scale_factor;
        let sub_contribution = (self.sub_position as f64 * scale_factor / 3.0);
        
        (scaled_position + sub_contribution) * scale as f64
    }
    
    /// Zoom in/out while maintaining position continuity
    pub fn rescale(&mut self, delta_depth: i8) -> Result<()> {
        let new_depth = self.depth.saturating_add(delta_depth);
        validation::validate_depth(new_depth)?;
        self.depth = new_depth;
        
        if delta_depth > 0 {
            // Zooming in - increase precision
            let scale_factor = 3.0_f32.checked_powi(delta_depth as i32)
                .ok_or(FractalError::ScaleOverflow)?;
            self.sub_position *= scale_factor;
            while self.sub_position > 1.0 {
                self.sub_position /= 3.0;
                self.base = self.base.saturating_add(1);
            }
        } else if delta_depth < 0 {
            // Zooming out - reduce precision
            let scale_factor = 3.0_f32.checked_powi((-delta_depth) as i32)
                .ok_or(FractalError::ScaleOverflow)?;
            self.sub_position /= scale_factor;
        }
        Ok(())
    }
    
    /// Get the voxel index at current depth
    pub fn voxel_index(&self) -> Result<(i32, i32, i32)> {
        validation::validate_depth(self.depth)?;
        
        let depth_abs = self.depth.abs() as u32;
        let scale = 3_i32.checked_pow(depth_abs)
            .ok_or(FractalError::ScaleOverflow)?;
        
        if scale == 0 {
            return Err(FractalError::DivisionByZero.into());
        }
        
        let index = (self.base as i32).checked_div(scale)
            .ok_or(FractalError::DivisionByZero)?;
        
        Ok((index, index, index)) // Simplified for now, should be 3D
    }
    
    /// Interpolate between two fractal coordinates
    pub fn lerp(&self, other: &Self, t: f32) -> Self {
        let t = t.clamp(0.0, 1.0);
        
        // Align depths for interpolation
        let (aligned_self, aligned_other) = if self.depth != other.depth {
            let target_depth = self.depth.max(other.depth);
            let mut s = self.clone();
            let mut o = other.clone();
            // If rescale fails, just use original coordinates
            let _ = s.rescale(target_depth - self.depth);
            let _ = o.rescale(target_depth - other.depth);
            (s, o)
        } else {
            (self.clone(), other.clone())
        };
        
        Self {
            base: ((aligned_self.base as f32 * (1.0 - t)) + 
                   (aligned_other.base as f32 * t)) as u16,
            depth: aligned_self.depth,
            sub_position: aligned_self.sub_position * (1.0 - t) + 
                         aligned_other.sub_position * t,
        }
    }
    
    /// Calculate fractal dimension at this coordinate
    pub fn fractal_dimension(&self) -> f32 {
        // Hausdorff dimension calculation
        // For building structures: typically between 1.0 and 3.0
        let scale_ratio: f32 = 3.0;
        let pieces: f32 = 27.0; // 3x3x3 subdivision
        
        (pieces.ln() / scale_ratio.ln())
    }
}

/// 3D fractal space for coordinate transformations
#[derive(Clone, Debug)]
pub struct FractalSpace {
    pub x: FractalCoordinate,
    pub y: FractalCoordinate,
    pub z: FractalCoordinate,
}

impl FractalSpace {
    /// Create new fractal space position
    pub fn new(x: FractalCoordinate, y: FractalCoordinate, z: FractalCoordinate) -> Self {
        Self { x, y, z }
    }
    
    /// Create from millimeter coordinates
    pub fn from_mm(x: u16, y: u16, z: u16) -> Self {
        Self {
            x: FractalCoordinate::from_mm(x),
            y: FractalCoordinate::from_mm(y),
            z: FractalCoordinate::from_mm(z),
        }
    }
    
    /// Convert to absolute 3D position
    pub fn to_absolute(&self, scale: f32) -> (f64, f64, f64) {
        (
            self.x.to_absolute(scale),
            self.y.to_absolute(scale),
            self.z.to_absolute(scale),
        )
    }
    
    /// Calculate distance to another point in fractal space
    pub fn distance(&self, other: &Self, scale: f32) -> f64 {
        let (x1, y1, z1) = self.to_absolute(scale);
        let (x2, y2, z2) = other.to_absolute(scale);
        
        let dx = x2 - x1;
        let dy = y2 - y1;
        let dz = z2 - z1;
        
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
    
    /// Rescale all coordinates uniformly
    pub fn rescale(&mut self, delta_depth: i8) -> Result<()> {
        self.x.rescale(delta_depth)?;
        self.y.rescale(delta_depth)?;
        self.z.rescale(delta_depth)?;
        Ok(())
    }
    
    /// Get the fractal box containing this position
    pub fn containing_box(&self, level: u8) -> FractalBox {
        let scale = 3_u32.pow(level as u32);
        let x_min = (self.x.base as u32 / scale) * scale;
        let y_min = (self.y.base as u32 / scale) * scale;
        let z_min = (self.z.base as u32 / scale) * scale;
        
        FractalBox {
            min: FractalSpace::from_mm(x_min as u16, y_min as u16, z_min as u16),
            max: FractalSpace::from_mm(
                (x_min + scale) as u16,
                (y_min + scale) as u16,
                (z_min + scale) as u16,
            ),
            level,
        }
    }
}

/// Fractal bounding box for spatial queries
pub struct FractalBox {
    pub min: FractalSpace,
    pub max: FractalSpace,
    pub level: u8,
}

impl FractalBox {
    /// Check if a point is inside this box
    pub fn contains(&self, point: &FractalSpace) -> bool {
        point.x.base >= self.min.x.base && point.x.base <= self.max.x.base &&
        point.y.base >= self.min.y.base && point.y.base <= self.max.y.base &&
        point.z.base >= self.min.z.base && point.z.base <= self.max.z.base
    }
    
    /// Subdivide into 27 child boxes (3x3x3)
    pub fn subdivide(&self) -> Vec<FractalBox> {
        let mut children = Vec::with_capacity(27);
        // Calculate the size of each subdivision
        let width = self.max.x.base - self.min.x.base;
        let height = self.max.y.base - self.min.y.base;
        let depth = self.max.z.base - self.min.z.base;
        
        let child_width = width / 3;
        let child_height = height / 3;
        let child_depth = depth / 3;
        
        for x in 0..3 {
            for y in 0..3 {
                for z in 0..3 {
                    let x_min = self.min.x.base + (x as u16 * child_width);
                    let y_min = self.min.y.base + (y as u16 * child_height);
                    let z_min = self.min.z.base + (z as u16 * child_depth);
                    
                    children.push(FractalBox {
                        min: FractalSpace::from_mm(x_min, y_min, z_min),
                        max: FractalSpace::from_mm(
                            x_min + child_width,
                            y_min + child_height,
                            z_min + child_depth,
                        ),
                        level: self.level + 1,
                    });
                }
            }
        }
        
        children
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_fractal_coordinate_scaling() {
        let coord = FractalCoordinate::new(1000, 0, 0.5);
        let initial_pos = coord.to_absolute(1.0);
        
        // Zoom in by 2 levels - creates new coordinate
        let mut zoomed = coord.clone();
        assert!(zoomed.rescale(2).is_ok());
        assert_eq!(zoomed.depth, 2);
        
        // When we zoom in, the absolute position at scale 1.0 will change
        // because we're looking at a smaller region in more detail
        let zoomed_pos = zoomed.to_absolute(1.0);
        
        // The positions will be different due to scale change
        // But the ratio should follow the power of 3 scaling
        let expected_ratio = 9.0; // 3^2
        let actual_ratio = zoomed_pos / initial_pos;
        assert!((actual_ratio - expected_ratio).abs() < 1.0);
    }
    
    #[test]
    fn test_fractal_interpolation() {
        let coord1 = FractalCoordinate::new(1000, 0, 0.0);
        let coord2 = FractalCoordinate::new(2000, 0, 1.0);
        
        let mid = coord1.lerp(&coord2, 0.5);
        assert_eq!(mid.base, 1500);
        assert!((mid.sub_position - 0.5).abs() < 0.001);
    }
    
    #[test]
    fn test_fractal_dimension() {
        let coord = FractalCoordinate::new(1000, 3, 0.5);
        let dim = coord.fractal_dimension();
        
        // Hausdorff dimension for 3D space subdivision
        // log(27)/log(3) = 3.0 for perfect 3D filling
        assert!((dim - 3.0).abs() < 0.01);
    }
    
    #[test]
    fn test_fractal_box_subdivision() {
        let bbox = FractalBox {
            min: FractalSpace::from_mm(0, 0, 0),
            max: FractalSpace::from_mm(27, 27, 27),  // Use smaller values for level 0
            level: 0,
        };
        
        let children = bbox.subdivide();
        assert_eq!(children.len(), 27);
        
        // Check first child - at level 0, scale is 1
        // 27 / 3 = 9
        assert_eq!(children[0].min.x.base, 0);
        assert_eq!(children[0].max.x.base, 9);
    }
}