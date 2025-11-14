//! Interactive 3D Rendering State Management
//!
//! This module provides state management for interactive 3D rendering sessions,
//! including camera state, selection state, and session data.

use crate::render3d::{ProjectionType, ViewAngle};
use crate::spatial::Point3D;
use std::collections::HashSet;

/// Interactive session state for 3D rendering
#[derive(Debug, Clone)]
pub struct InteractiveState {
    /// Currently selected equipment IDs
    pub selected_equipment: HashSet<String>,
    /// Camera state for 3D navigation
    pub camera_state: CameraState,
    /// Current view mode
    pub view_mode: ViewMode,
    /// Session data and preferences
    pub session_data: SessionData,
    /// Current floor being viewed
    pub current_floor: Option<i32>,
    /// Whether the session is active
    pub is_active: bool,
}

/// Camera state for 3D navigation
#[derive(Debug, Clone)]
pub struct CameraState {
    /// Camera position in 3D space
    pub position: Point3D,
    /// Camera target/look-at point
    pub target: Point3D,
    /// Camera up vector
    pub up: Vector3D,
    /// Field of view angle
    pub fov: f64,
    /// Zoom level
    pub zoom: f64,
    /// Rotation angles (pitch, yaw, roll)
    pub rotation: Rotation3D,
}

/// 3D rotation representation
#[derive(Debug, Clone)]
pub struct Rotation3D {
    pub pitch: f64, // X-axis rotation
    pub yaw: f64,   // Y-axis rotation
    pub roll: f64,  // Z-axis rotation
}

/// 3D vector for camera operations
#[derive(Debug, Clone)]
pub struct Vector3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// View mode for interactive rendering
#[derive(Debug, Clone, PartialEq)]
pub enum ViewMode {
    /// Standard 3D view
    Standard,
    /// Cross-section view
    CrossSection,
    /// Equipment connections view
    Connections,
    /// Maintenance overlay view
    Maintenance,
}

/// Session data and user preferences
#[derive(Debug, Clone)]
pub struct SessionData {
    /// User preferences for rendering
    pub preferences: RenderPreferences,
    /// Session statistics
    pub stats: SessionStats,
    /// Last interaction timestamp
    pub last_interaction: std::time::Instant,
}

/// User rendering preferences
#[derive(Debug, Clone)]
pub struct RenderPreferences {
    /// Show equipment status indicators
    pub show_status: bool,
    /// Show room boundaries
    pub show_rooms: bool,
    /// Show equipment connections
    pub show_connections: bool,
    /// Show maintenance overlays
    pub show_maintenance: bool,
    /// Preferred projection type
    pub projection_type: ProjectionType,
    /// Preferred view angle
    pub view_angle: ViewAngle,
    /// Rendering quality level
    pub quality_level: QualityLevel,
}

/// Rendering quality levels
#[derive(Debug, Clone, PartialEq)]
pub enum QualityLevel {
    /// Low quality for performance
    Low,
    /// Medium quality balance
    Medium,
    /// High quality for detail
    High,
}

/// Session statistics
#[derive(Debug, Clone)]
pub struct SessionStats {
    /// Number of renders performed
    pub render_count: u32,
    /// Total session time
    pub session_time: std::time::Duration,
    /// Number of equipment selections
    pub selection_count: u32,
    /// Number of view changes
    pub view_change_count: u32,
}

impl Default for InteractiveState {
    fn default() -> Self {
        Self::new()
    }
}

impl InteractiveState {
    /// Create a new interactive state with default values
    pub fn new() -> Self {
        Self {
            selected_equipment: HashSet::new(),
            camera_state: CameraState::default(),
            view_mode: ViewMode::Standard,
            session_data: SessionData::new(),
            current_floor: None,
            is_active: false,
        }
    }

    /// Create interactive state with custom camera position
    pub fn with_camera(position: Point3D, target: Point3D) -> Self {
        let mut state = Self::new();
        state.camera_state.position = position;
        state.camera_state.target = target;
        state
    }

    /// Select equipment by ID
    pub fn select_equipment(&mut self, equipment_id: String) {
        self.selected_equipment.insert(equipment_id);
        self.session_data.stats.selection_count += 1;
        self.session_data.last_interaction = std::time::Instant::now();
    }

    /// Deselect equipment by ID
    pub fn deselect_equipment(&mut self, equipment_id: &str) {
        self.selected_equipment.remove(equipment_id);
        self.session_data.last_interaction = std::time::Instant::now();
    }

    /// Clear all equipment selections
    pub fn clear_selections(&mut self) {
        self.selected_equipment.clear();
        self.session_data.last_interaction = std::time::Instant::now();
    }

    /// Check if equipment is selected
    pub fn is_equipment_selected(&self, equipment_id: &str) -> bool {
        self.selected_equipment.contains(equipment_id)
    }

    /// Change view mode
    pub fn set_view_mode(&mut self, mode: ViewMode) {
        if self.view_mode != mode {
            self.view_mode = mode;
            self.session_data.stats.view_change_count += 1;
            self.session_data.last_interaction = std::time::Instant::now();
        }
    }

    /// Update camera position
    pub fn update_camera(&mut self, position: Point3D, target: Point3D) {
        self.camera_state.position = position;
        self.camera_state.target = target;
        self.session_data.last_interaction = std::time::Instant::now();
    }

    /// Set current floor
    pub fn set_current_floor(&mut self, floor: Option<i32>) {
        self.current_floor = floor;
        self.session_data.last_interaction = std::time::Instant::now();
    }

    /// Activate the session
    pub fn activate(&mut self) {
        self.is_active = true;
        self.session_data.stats.session_time = std::time::Duration::from_secs(0);
    }

    /// Deactivate the session
    pub fn deactivate(&mut self) {
        self.is_active = false;
    }

    /// Increment render count
    pub fn increment_render_count(&mut self) {
        self.session_data.stats.render_count += 1;
    }

    /// Get session duration
    pub fn session_duration(&self) -> std::time::Duration {
        if self.is_active {
            self.session_data.stats.session_time + self.session_data.last_interaction.elapsed()
        } else {
            self.session_data.stats.session_time
        }
    }
}

impl CameraState {
    /// Create a new camera state with default values
    pub fn new() -> Self {
        Self {
            position: Point3D::new(0.0, 0.0, 10.0),
            target: Point3D::new(0.0, 0.0, 0.0),
            up: Vector3D::new(0.0, 1.0, 0.0),
            fov: 60.0,
            zoom: 1.0,
            rotation: Rotation3D::new(0.0, 0.0, 0.0),
        }
    }

    /// Create camera state with specific position and target
    pub fn with_position_target(position: Point3D, target: Point3D) -> Self {
        Self {
            position,
            target,
            up: Vector3D::new(0.0, 1.0, 0.0),
            fov: 60.0,
            zoom: 1.0,
            rotation: Rotation3D::new(0.0, 0.0, 0.0),
        }
    }

    /// Zoom in by the specified factor
    pub fn zoom_in(&mut self, factor: f64) {
        self.zoom *= factor;
        if self.zoom > 10.0 {
            self.zoom = 10.0;
        }
    }

    /// Zoom out by the specified factor
    pub fn zoom_out(&mut self, factor: f64) {
        self.zoom /= factor;
        if self.zoom < 0.1 {
            self.zoom = 0.1;
        }
    }

    /// Rotate camera by the specified angles
    pub fn rotate(&mut self, pitch: f64, yaw: f64, roll: f64) {
        self.rotation.pitch += pitch;
        self.rotation.yaw += yaw;
        self.rotation.roll += roll;

        // Normalize angles to [-180, 180]
        self.rotation.pitch = self.normalize_angle(self.rotation.pitch);
        self.rotation.yaw = self.normalize_angle(self.rotation.yaw);
        self.rotation.roll = self.normalize_angle(self.rotation.roll);
    }

    /// Normalize angle to [-180, 180] range
    fn normalize_angle(&self, angle: f64) -> f64 {
        let mut normalized = angle;
        while normalized > 180.0 {
            normalized -= 360.0;
        }
        while normalized < -180.0 {
            normalized += 360.0;
        }
        normalized
    }

    /// Move camera by the specified offset
    pub fn translate(&mut self, offset: Vector3D) {
        self.position.x += offset.x;
        self.position.y += offset.y;
        self.position.z += offset.z;
    }

    /// Set camera to look at a specific target
    pub fn look_at(&mut self, target: Point3D) {
        self.target = target;
    }
}

impl Default for CameraState {
    fn default() -> Self {
        Self::new()
    }
}

impl Rotation3D {
    /// Create a new rotation with specified angles
    pub fn new(pitch: f64, yaw: f64, roll: f64) -> Self {
        Self { pitch, yaw, roll }
    }

    /// Create zero rotation
    pub fn zero() -> Self {
        Self::new(0.0, 0.0, 0.0)
    }
}

impl Vector3D {
    /// Create a new 3D vector
    pub fn new(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z }
    }

    /// Create zero vector
    pub fn zero() -> Self {
        Self::new(0.0, 0.0, 0.0)
    }

    /// Calculate vector length
    pub fn length(&self) -> f64 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    /// Normalize vector to unit length
    pub fn normalize(&self) -> Self {
        let len = self.length();
        if len > 0.0 {
            Self::new(self.x / len, self.y / len, self.z / len)
        } else {
            Self::zero()
        }
    }
}

impl SessionData {
    /// Create new session data with default values
    pub fn new() -> Self {
        Self {
            preferences: RenderPreferences::default(),
            stats: SessionStats::new(),
            last_interaction: std::time::Instant::now(),
        }
    }
}

impl Default for SessionData {
    fn default() -> Self {
        Self::new()
    }
}

impl RenderPreferences {
    /// Create default render preferences
    pub fn new() -> Self {
        Self {
            show_status: true,
            show_rooms: true,
            show_connections: false,
            show_maintenance: false,
            projection_type: ProjectionType::Isometric,
            view_angle: ViewAngle::Isometric,
            quality_level: QualityLevel::Medium,
        }
    }
}

impl Default for RenderPreferences {
    fn default() -> Self {
        Self::new()
    }
}

impl SessionStats {
    /// Create new session statistics
    pub fn new() -> Self {
        Self {
            render_count: 0,
            session_time: std::time::Duration::from_secs(0),
            selection_count: 0,
            view_change_count: 0,
        }
    }
}

impl Default for SessionStats {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_interactive_state_creation() {
        let state = InteractiveState::new();
        assert!(!state.is_active);
        assert!(state.selected_equipment.is_empty());
        assert_eq!(state.view_mode, ViewMode::Standard);
        assert_eq!(state.current_floor, None);
    }

    #[test]
    fn test_equipment_selection() {
        let mut state = InteractiveState::new();

        // Test selection
        state.select_equipment("equipment-1".to_string());
        assert!(state.is_equipment_selected("equipment-1"));
        assert_eq!(state.session_data.stats.selection_count, 1);

        // Test deselection
        state.deselect_equipment("equipment-1");
        assert!(!state.is_equipment_selected("equipment-1"));

        // Test clear selections
        state.select_equipment("equipment-1".to_string());
        state.select_equipment("equipment-2".to_string());
        state.clear_selections();
        assert!(state.selected_equipment.is_empty());
    }

    #[test]
    fn test_camera_operations() {
        let mut camera = CameraState::new();

        // Test zoom
        camera.zoom_in(2.0);
        assert_eq!(camera.zoom, 2.0);

        camera.zoom_out(2.0);
        assert_eq!(camera.zoom, 1.0);

        // Test rotation
        camera.rotate(45.0, 30.0, 15.0);
        assert_eq!(camera.rotation.pitch, 45.0);
        assert_eq!(camera.rotation.yaw, 30.0);
        assert_eq!(camera.rotation.roll, 15.0);

        // Test translation
        camera.translate(Vector3D::new(1.0, 2.0, 3.0));
        assert_eq!(camera.position.x, 1.0);
        assert_eq!(camera.position.y, 2.0);
        assert_eq!(camera.position.z, 13.0);
    }

    #[test]
    fn test_vector_operations() {
        let vector = Vector3D::new(3.0, 4.0, 0.0);
        assert_eq!(vector.length(), 5.0);

        let normalized = vector.normalize();
        assert!((normalized.length() - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_view_mode_changes() {
        let mut state = InteractiveState::new();

        state.set_view_mode(ViewMode::CrossSection);
        assert_eq!(state.view_mode, ViewMode::CrossSection);
        assert_eq!(state.session_data.stats.view_change_count, 1);

        // Same mode should not increment counter
        state.set_view_mode(ViewMode::CrossSection);
        assert_eq!(state.session_data.stats.view_change_count, 1);
    }
}
