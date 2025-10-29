//! Projection, viewport, matrix, and vector implementations

use super::types::{Projection3D, Viewport3D, Matrix3D, Vector3D, ProjectionType, ViewAngle};

impl Projection3D {
    pub fn new(projection_type: ProjectionType, view_angle: ViewAngle, scale: f64) -> Self {
        Self {
            projection_type,
            view_angle,
            scale,
            aspect_ratio: 1.0,
        }
    }
}

impl Viewport3D {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            offset_x: 0,
            offset_y: 0,
            depth_buffer: vec![vec![f64::INFINITY; width]; height],
        }
    }
}

impl Matrix3D {
    pub fn identity() -> Self {
        Self {
            m: [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        }
    }
}

impl Vector3D {
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }
    
    pub fn length(&self) -> f64 {
        (self.x.powi(2) + self.y.powi(2) + self.z.powi(2)).sqrt()
    }
    
    pub fn normalize(&self) -> Self {
        let len = self.length();
        if len > 0.0 {
            Self {
                x: self.x / len,
                y: self.y / len,
                z: self.z / len,
            }
        } else {
            Self { x: 0.0, y: 0.0, z: 0.0 }
        }
    }
}

impl Default for super::types::Render3DConfig {
    fn default() -> Self {
        Self {
            show_status: true,
            show_rooms: true,
            show_equipment: true,
            show_connections: false,
            projection_type: ProjectionType::Isometric,
            view_angle: ViewAngle::Isometric,
            scale_factor: 1.0,
            max_width: 120,
            max_height: 40,
        }
    }
}

