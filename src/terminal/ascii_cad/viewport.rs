//! Viewport management for CAD display

use crate::cad::data_model::{Point2D, BoundingBox};

/// Viewport state for panning and zooming
#[derive(Debug, Clone)]
pub struct Viewport {
    /// Center of viewport in world coordinates
    pub center: Point2D,
    
    /// Zoom level (pixels per world unit)
    pub scale: f64,
    
    /// Terminal dimensions
    pub width: usize,
    pub height: usize,
    
    /// Aspect ratio correction for terminal characters
    pub aspect_ratio: f64,
    
    /// Visible bounds in world coordinates
    pub bounds: BoundingBox,
}

/// Viewport state for undo/redo
#[derive(Debug, Clone)]
pub struct ViewportState {
    pub center: Point2D,
    pub scale: f64,
}

impl Viewport {
    pub fn new(width: usize, height: usize) -> Self {
        let center = Point2D { x: 0.0, y: 0.0 };
        let scale = 1.0;
        let aspect_ratio = 2.0;  // Terminal chars are ~2x taller than wide
        
        let mut viewport = Self {
            center,
            scale,
            width,
            height,
            aspect_ratio,
            bounds: BoundingBox {
                min: Point2D { x: 0.0, y: 0.0 },
                max: Point2D { x: 0.0, y: 0.0 },
            },
        };
        
        viewport.update_bounds();
        viewport
    }
    
    /// Update visible bounds based on current viewport settings
    pub fn update_bounds(&mut self) {
        let half_width = (self.width as f64) / (2.0 * self.scale);
        let half_height = (self.height as f64) / (2.0 * self.scale * self.aspect_ratio);
        
        self.bounds = BoundingBox {
            min: Point2D {
                x: self.center.x - half_width,
                y: self.center.y - half_height,
            },
            max: Point2D {
                x: self.center.x + half_width,
                y: self.center.y + half_height,
            },
        };
    }
    
    /// Convert world coordinates to screen coordinates
    pub fn world_to_screen(&self, point: Point2D) -> (i32, i32) {
        let x = ((point.x - self.center.x) * self.scale + (self.width as f64 / 2.0)) as i32;
        let y = ((point.y - self.center.y) * self.scale * self.aspect_ratio + (self.height as f64 / 2.0)) as i32;
        (x, y)
    }
    
    /// Convert screen coordinates to world coordinates
    pub fn screen_to_world(&self, x: i32, y: i32) -> Point2D {
        Point2D {
            x: (x as f64 - self.width as f64 / 2.0) / self.scale + self.center.x,
            y: (y as f64 - self.height as f64 / 2.0) / (self.scale * self.aspect_ratio) + self.center.y,
        }
    }
    
    /// Zoom in/out by a factor
    pub fn zoom(&mut self, factor: f64) {
        self.scale *= factor;
        self.scale = self.scale.clamp(0.01, 100.0);  // Prevent extreme zoom
        self.update_bounds();
    }
    
    /// Zoom to specific scale
    pub fn set_zoom(&mut self, scale: f64) {
        self.scale = scale.clamp(0.01, 100.0);
        self.update_bounds();
    }
    
    /// Pan the viewport
    pub fn pan(&mut self, delta_x: f64, delta_y: f64) {
        self.center.x += delta_x / self.scale;
        self.center.y += delta_y / (self.scale * self.aspect_ratio);
        self.update_bounds();
    }
    
    /// Pan to specific point
    pub fn pan_to(&mut self, point: Point2D) {
        self.center = point;
        self.update_bounds();
    }
    
    /// Fit viewport to bounding box
    pub fn fit_to_bounds(&mut self, bounds: BoundingBox) {
        // Calculate center
        self.center = Point2D {
            x: (bounds.min.x + bounds.max.x) / 2.0,
            y: (bounds.min.y + bounds.max.y) / 2.0,
        };
        
        // Calculate scale to fit
        let width = bounds.max.x - bounds.min.x;
        let height = bounds.max.y - bounds.min.y;
        
        if width > 0.0 && height > 0.0 {
            let scale_x = self.width as f64 / width;
            let scale_y = self.height as f64 / (height * self.aspect_ratio);
            
            // Use smaller scale to ensure everything fits
            self.scale = scale_x.min(scale_y) * 0.9;  // 90% to add margin
            self.scale = self.scale.clamp(0.01, 100.0);
        }
        
        self.update_bounds();
    }
    
    /// Check if a point is visible in the viewport
    pub fn is_visible(&self, point: Point2D) -> bool {
        point.x >= self.bounds.min.x &&
        point.x <= self.bounds.max.x &&
        point.y >= self.bounds.min.y &&
        point.y <= self.bounds.max.y
    }
    
    /// Check if a bounding box overlaps the viewport
    pub fn overlaps(&self, bounds: BoundingBox) -> bool {
        !(bounds.max.x < self.bounds.min.x ||
          bounds.min.x > self.bounds.max.x ||
          bounds.max.y < self.bounds.min.y ||
          bounds.min.y > self.bounds.max.y)
    }
    
    /// Get current state for undo/redo
    pub fn get_state(&self) -> ViewportState {
        ViewportState {
            center: self.center,
            scale: self.scale,
        }
    }
    
    /// Restore state from undo/redo
    pub fn set_state(&mut self, state: ViewportState) {
        self.center = state.center;
        self.scale = state.scale;
        self.update_bounds();
    }
    
    /// Resize the viewport (when terminal is resized)
    pub fn resize(&mut self, width: usize, height: usize) {
        self.width = width;
        self.height = height;
        self.update_bounds();
    }
    
    /// Get viewport info as string
    pub fn info(&self) -> String {
        format!(
            "Center: ({:.2}, {:.2}) | Scale: {:.2}x | View: {:.2} x {:.2} units",
            self.center.x,
            self.center.y,
            self.scale,
            self.bounds.max.x - self.bounds.min.x,
            self.bounds.max.y - self.bounds.min.y
        )
    }
}

/// Snap modes for precise drawing
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum SnapMode {
    None,
    Grid(f64),      // Snap to grid with spacing
    Endpoint,       // Snap to line endpoints
    Midpoint,       // Snap to line midpoints
    Center,         // Snap to circle/arc centers
    Intersection,   // Snap to intersections
    Perpendicular,  // Snap perpendicular to lines
    Tangent,        // Snap tangent to circles/arcs
}

/// Snap settings
pub struct SnapSettings {
    pub mode: SnapMode,
    pub enabled: bool,
    pub snap_distance: f64,  // In screen pixels
}

impl SnapSettings {
    pub fn new() -> Self {
        Self {
            mode: SnapMode::Grid(10.0),
            enabled: true,
            snap_distance: 5.0,
        }
    }
    
    /// Snap a point based on current settings
    pub fn snap_point(&self, point: Point2D, viewport: &Viewport) -> Point2D {
        if !self.enabled {
            return point;
        }
        
        match self.mode {
            SnapMode::None => point,
            SnapMode::Grid(spacing) => {
                Point2D {
                    x: (point.x / spacing).round() * spacing,
                    y: (point.y / spacing).round() * spacing,
                }
            }
            // Other snap modes would require entity data
            _ => point,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_viewport_coordinates() {
        let viewport = Viewport::new(80, 24);
        
        // Test world to screen
        let world_point = Point2D { x: 10.0, y: 10.0 };
        let (screen_x, screen_y) = viewport.world_to_screen(world_point);
        
        // Test screen to world (should round-trip)
        let world_point2 = viewport.screen_to_world(screen_x, screen_y);
        assert!((world_point.x - world_point2.x).abs() < 0.1);
        assert!((world_point.y - world_point2.y).abs() < 0.1);
    }
    
    #[test]
    fn test_viewport_zoom() {
        let mut viewport = Viewport::new(80, 24);
        let initial_scale = viewport.scale;
        
        viewport.zoom(2.0);
        assert_eq!(viewport.scale, initial_scale * 2.0);
        
        viewport.zoom(0.5);
        assert_eq!(viewport.scale, initial_scale);
    }
    
    #[test]
    fn test_snap_to_grid() {
        let snap = SnapSettings::new();
        let point = Point2D { x: 12.3, y: 47.8 };
        let viewport = Viewport::new(80, 24);
        
        let snapped = snap.snap_point(point, &viewport);
        assert_eq!(snapped.x, 10.0);  // Snapped to nearest 10
        assert_eq!(snapped.y, 50.0);  // Snapped to nearest 10
    }
}