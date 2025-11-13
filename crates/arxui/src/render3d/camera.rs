//! WebGL-style camera implementation for 3D rendering
//! Exactly matches three.js OrbitControls behavior

use super::types::Vector3D;
use arx::spatial::Point3D;
use std::f64::consts::{PI, FRAC_PI_2};

/// WebGL-style camera with yaw/pitch/distance controls
/// Behaves exactly like three.js OrbitControls
#[derive(Debug, Clone)]
pub struct Camera {
    pub pos: Vec3,
    pub yaw: f32,
    pub pitch: f32,
    pub target: Vec3,
    pub distance: f32,
    pub fov_scale: f32,
}

/// 3D vector for WebGL-style math
#[derive(Debug, Clone, Copy)]
pub struct Vec3 {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

impl Vec3 {
    pub fn new(x: f32, y: f32, z: f32) -> Self {
        Self { x, y, z }
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

    pub fn length(&self) -> f32 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    pub fn dot(&self, other: &Self) -> f32 {
        self.x * other.x + self.y * other.y + self.z * other.z
    }

    pub fn cross(&self, other: &Self) -> Self {
        Self {
            x: self.y * other.z - self.z * other.y,
            y: self.z * other.x - self.x * other.z,
            z: self.x * other.y - self.y * other.x,
        }
    }

    pub fn sub(&self, other: &Self) -> Self {
        Self {
            x: self.x - other.x,
            y: self.y - other.y,
            z: self.z - other.z,
        }
    }

    pub fn add(&self, other: &Self) -> Self {
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
            z: self.z + other.z,
        }
    }

    pub fn mul(&self, scalar: f32) -> Self {
        Self {
            x: self.x * scalar,
            y: self.y * scalar,
            z: self.z * scalar,
        }
    }
}

impl std::ops::Sub for Vec3 {
    type Output = Vec3;
    fn sub(self, other: Vec3) -> Vec3 {
        self.sub(other)
    }
}

impl std::ops::Add for Vec3 {
    type Output = Vec3;
    fn add(self, other: Vec3) -> Vec3 {
        self.add(other)
    }
}

impl std::ops::Mul<f32> for Vec3 {
    type Output = Vec3;
    fn mul(self, scalar: f32) -> Vec3 {
        self.mul(scalar)
    }
}

pub fn vec3(x: f32, y: f32, z: f32) -> Vec3 {
    Vec3::new(x, y, z)
}

impl Camera {
    pub fn new() -> Self {
        Self {
            pos: vec3(0.0, 0.0, 100.0),
            yaw: 0.0,
            pitch: 0.0,
            target: vec3(0.0, 0.0, 0.0),
            distance: 100.0,
            fov_scale: 100.0, // Matches perspective projection scale
        }
    }

    /// Get forward direction vector (exactly like WebGL)
    pub fn forward(&self) -> Vec3 {
        let cos_pitch = self.pitch.cos();
        vec3(
            self.yaw.cos() * cos_pitch,
            self.pitch.sin(),
            self.yaw.sin() * cos_pitch,
        ).normalize()
    }

    /// Get right direction vector (exactly like WebGL)
    pub fn right(&self) -> Vec3 {
        let up = vec3(0.0, 1.0, 0.0);
        self.forward().cross(&up).normalize()
    }

    /// Get up direction vector (exactly like WebGL)
    pub fn up(&self) -> Vec3 {
        self.right().cross(&self.forward()).normalize()
    }

    /// Update camera position based on yaw/pitch/distance (OrbitControls style)
    pub fn update_position(&mut self) {
        let forward = self.forward();
        self.pos = self.target.add(&forward.mul(-self.distance));
    }

    /// Handle mouse drag for orbiting (exactly like OrbitControls)
    pub fn orbit(&mut self, delta_x: f32, delta_y: f32, sensitivity: f32) {
        self.yaw += delta_x * sensitivity;
        self.pitch -= delta_y * sensitivity;

        // Clamp pitch to avoid gimbal lock (just like OrbitControls)
        self.pitch = self.pitch.clamp(-FRAC_PI_2 as f32 + 0.01, FRAC_PI_2 as f32 - 0.01);

        self.update_position();
    }

    /// Handle WASD movement (exactly like three.js FlyControls)
    pub fn move_camera(&mut self, forward: f32, right: f32, up: f32, speed: f32) {
        let forward_vec = self.forward().mul(forward * speed);
        let right_vec = self.right().mul(right * speed);
        let up_vec = vec3(0.0, 1.0, 0.0).mul(up * speed);

        let movement = forward_vec.add(&right_vec).add(&up_vec);
        self.target = self.target.add(&movement);
        self.update_position();
    }

    /// Handle zoom (mouse wheel)
    pub fn zoom(&mut self, delta: f32, zoom_speed: f32) {
        self.distance *= (1.0 + delta * zoom_speed).max(0.1);
        self.distance = self.distance.clamp(1.0, 1000.0);
        self.update_position();
    }

    /// Set target and recalculate position (for focusing on objects)
    pub fn look_at(&mut self, target: Vec3) {
        self.target = target;
        self.update_position();
    }
}

impl Default for Camera {
    fn default() -> Self {
        Self::new()
    }
}

/// Project 3D point to screen coordinates (exactly like WebGL)
/// Returns Option<(x, y, depth)> where depth is for z-buffering
pub fn project(p: Vec3, cam: &Camera, width: u16, height: u16) -> Option<(usize, usize, f32)> {
    let dir = (p - cam.pos).normalize();
    let forward = cam.forward();
    let up = vec3(0.0, 1.0, 0.0);

    let dot = dir.dot(&forward);
    if dot < 0.01 { 
        return None; // behind camera
    }

    let right = forward.cross(&up).normalize();
    let u = dir.dot(&right) / dot * cam.fov_scale + width as f32 / 2.0;
    let v = dir.dot(&up) / dot * cam.fov_scale + height as f32 / 2.0;

    if u < 0.0 || u >= width as f32 || v < 0.0 || v >= height as f32 { 
        return None; 
    }

    Some((u as usize, v as usize, dot)) // dot = rough depth
}

// Legacy compatibility with existing Camera3D type
impl From<Camera> for super::types::Camera3D {
    fn from(cam: Camera) -> Self {
        Self {
            position: Point3D {
                x: cam.pos.x as f64,
                y: cam.pos.y as f64,
                z: cam.pos.z as f64,
            },
            target: Point3D {
                x: cam.target.x as f64,
                y: cam.target.y as f64,
                z: cam.target.z as f64,
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
