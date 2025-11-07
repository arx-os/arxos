//! Camera implementation for 3D rendering

use super::types::{Camera3D, Vector3D};
use crate::spatial::Point3D;

impl Default for Camera3D {
    fn default() -> Self {
        Self {
            position: Point3D {
                x: 50.0,
                y: 50.0,
                z: 100.0,
            },
            target: Point3D {
                x: 50.0,
                y: 50.0,
                z: 0.0,
            },
            up: Vector3D {
                x: 0.0,
                y: 1.0,
                z: 0.0,
            },
            fov: 45.0,
            near_clip: 0.1,
            far_clip: 1000.0,
        }
    }
}
