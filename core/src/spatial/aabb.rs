//! Axis-aligned bounding box geometry helpers.

use crate::object::{Aabb, Pose};

/// Epsilon for point-like objects (annotations, etc.) when only a pose is known.
pub const POINT_HALF_EXTENT_M: f64 = 0.25;

impl Aabb {
    /// Create an AABB from min/max corners (auto-corrects inverted axes).
    pub fn from_min_max(min: [f64; 3], max: [f64; 3]) -> Self {
        let mut out = Self { min, max };
        out.normalize();
        out
    }

    /// AABB centered on a pose with half-extents.
    pub fn from_pose(pose: &Pose, half: f64) -> Self {
        let h = half.abs().max(1e-6);
        Self {
            min: [
                pose.position[0] - h,
                pose.position[1] - h,
                pose.position[2] - h,
            ],
            max: [
                pose.position[0] + h,
                pose.position[1] + h,
                pose.position[2] + h,
            ],
        }
    }

    /// Ensure min[i] <= max[i] for all axes.
    pub fn normalize(&mut self) {
        for i in 0..3 {
            if self.min[i] > self.max[i] {
                std::mem::swap(&mut self.min[i], &mut self.max[i]);
            }
        }
    }

    pub fn centroid(&self) -> [f64; 3] {
        [
            0.5 * (self.min[0] + self.max[0]),
            0.5 * (self.min[1] + self.max[1]),
            0.5 * (self.min[2] + self.max[2]),
        ]
    }

    pub fn extents(&self) -> [f64; 3] {
        [
            self.max[0] - self.min[0],
            self.max[1] - self.min[1],
            self.max[2] - self.min[2],
        ]
    }

    pub fn volume(&self) -> f64 {
        let e = self.extents();
        e[0].max(0.0) * e[1].max(0.0) * e[2].max(0.0)
    }

    /// Longest axis index (0=x, 1=y, 2=z).
    pub fn longest_axis(&self) -> usize {
        let e = self.extents();
        if e[0] >= e[1] && e[0] >= e[2] {
            0
        } else if e[1] >= e[2] {
            1
        } else {
            2
        }
    }

    pub fn intersects(&self, other: &Aabb) -> bool {
        for i in 0..3 {
            if self.max[i] < other.min[i] || self.min[i] > other.max[i] {
                return false;
            }
        }
        true
    }

    pub fn contains_point(&self, p: [f64; 3]) -> bool {
        for i in 0..3 {
            if p[i] < self.min[i] || p[i] > self.max[i] {
                return false;
            }
        }
        true
    }

    pub fn union(&self, other: &Aabb) -> Aabb {
        Aabb {
            min: [
                self.min[0].min(other.min[0]),
                self.min[1].min(other.min[1]),
                self.min[2].min(other.min[2]),
            ],
            max: [
                self.max[0].max(other.max[0]),
                self.max[1].max(other.max[1]),
                self.max[2].max(other.max[2]),
            ],
        }
    }

    /// Expand by margin on all sides.
    pub fn expand(&self, margin: f64) -> Aabb {
        let m = margin.abs();
        Aabb {
            min: [self.min[0] - m, self.min[1] - m, self.min[2] - m],
            max: [self.max[0] + m, self.max[1] + m, self.max[2] + m],
        }
    }

    /// Infinite slab for a floor level (Y-up): elevation ± half_height.
    pub fn floor_slab(elevation_m: f64, half_height_m: f64) -> Aabb {
        let h = half_height_m.abs().max(0.5);
        Aabb {
            min: [f64::NEG_INFINITY, elevation_m - h, f64::NEG_INFINITY],
            max: [f64::INFINITY, elevation_m + h, f64::INFINITY],
        }
    }
}

/// Union of many AABBs; None if empty.
pub fn union_all(boxes: impl IntoIterator<Item = Aabb>) -> Option<Aabb> {
    let mut iter = boxes.into_iter();
    let first = iter.next()?;
    Some(iter.fold(first, |a, b| a.union(&b)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn intersect_and_union() {
        let a = Aabb::from_min_max([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]);
        let b = Aabb::from_min_max([0.5, 0.5, 0.5], [2.0, 2.0, 2.0]);
        let c = Aabb::from_min_max([3.0, 3.0, 3.0], [4.0, 4.0, 4.0]);
        assert!(a.intersects(&b));
        assert!(!a.intersects(&c));
        let u = a.union(&b);
        assert_eq!(u.min, [0.0, 0.0, 0.0]);
        assert_eq!(u.max, [2.0, 2.0, 2.0]);
    }
}
