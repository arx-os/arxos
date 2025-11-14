//! ASCII renderer for 3D building visualization
//!
//! Provides high-level ASCII rendering methods that combine canvas operations
//! with headers, legends, and formatting.

use super::canvas::{render_equipment, render_floors, render_rooms, AsciiCanvas, DepthBuffer};
use super::characters::LEGEND;
use crate::render3d::types::{ProjectionType, Scene3D};
use crate::spatial::Point3D;

/// ASCII renderer for 3D scenes
pub struct AsciiRenderer;

impl AsciiRenderer {
    /// Create a new ASCII renderer
    pub fn new() -> Self {
        Self
    }

    /// Render advanced ASCII output with projection info
    ///
    /// Includes header with camera info, projection details, and metadata.
    ///
    /// # Arguments
    ///
    /// * `scene` - 3D scene to render
    /// * `camera_info` - Camera position and target information
    /// * `projection_info` - Projection type, view angle, and scale
    ///
    /// # Returns
    ///
    /// Formatted ASCII string with headers and scene visualization
    pub fn render_advanced(
        &self,
        scene: &Scene3D,
        camera_info: CameraInfo,
        projection_info: ProjectionInfo,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut output = String::new();

        // Header with camera info
        output.push_str(&format!(
            "🏢 {} - Advanced 3D Building Visualization\n",
            scene.building_name.as_str()
        ));
        output.push_str(&format!(
            "📊 {} floors, {} rooms, {} equipment\n",
            scene.metadata.total_floors, scene.metadata.total_rooms, scene.metadata.total_equipment
        ));
        output.push_str(&format!(
            "🎯 Projection: {} | View: {} | Scale: {:.2}\n",
            projection_info.projection_type, projection_info.view_angle, projection_info.scale
        ));
        output.push_str(&format!(
            "📷 Camera: ({:.1}, {:.1}, {:.1}) → ({:.1}, {:.1}, {:.1})\n",
            camera_info.position.x,
            camera_info.position.y,
            camera_info.position.z,
            camera_info.target.x,
            camera_info.target.y,
            camera_info.target.z
        ));
        output.push_str("═".repeat(80).as_str());
        output.push('\n');

        Ok(output)
    }

    /// Render 3D building as ASCII art with depth and perspective
    ///
    /// Creates a bordered ASCII art visualization with legend.
    ///
    /// # Arguments
    ///
    /// * `scene` - 3D scene to render
    /// * `canvas_width` - Width of ASCII canvas
    /// * `canvas_height` - Height of ASCII canvas
    /// * `project_fn` - Function to project 3D points to screen coordinates
    ///
    /// # Returns
    ///
    /// Formatted ASCII art with borders and legend
    pub fn render_ascii_art<F>(
        &self,
        scene: &Scene3D,
        canvas_width: usize,
        canvas_height: usize,
        project_fn: F,
    ) -> Result<String, Box<dyn std::error::Error>>
    where
        F: Fn(&Point3D) -> Point3D + Copy,
    {
        let mut output = String::new();

        // Create canvas and depth buffer
        let mut canvas = AsciiCanvas::new(canvas_width, canvas_height);
        let mut depth_buffer = DepthBuffer::new(canvas_width, canvas_height);

        // Render scene elements
        render_floors(&scene.floors, &mut canvas, &mut depth_buffer, project_fn);
        render_equipment(
            &scene.equipment,
            &mut canvas,
            &mut depth_buffer,
            project_fn,
        );
        render_rooms(&scene.rooms, &mut canvas, &mut depth_buffer, project_fn);

        // Add header
        output.push_str("┌─────────────────────────────────────────────────────────────┐\n");
        output.push_str(&format!(
            "│ 🏢 {} - 3D ASCII Building Visualization │\n",
            scene.building_name.as_str()
        ));
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");

        // Add canvas content with borders
        for row in canvas.buffer() {
            let line: String = row.iter().collect();
            output.push_str(&format!("│{}│\n", line));
        }

        // Add legend
        output.push_str("└─────────────────────────────────────────────────────────────┘\n");
        output.push_str(LEGEND);
        output.push('\n');

        Ok(output)
    }

    /// Render simple ASCII output
    ///
    /// Basic ASCII rendering without borders or advanced formatting.
    ///
    /// # Arguments
    ///
    /// * `scene` - 3D scene to render
    /// * `canvas_width` - Width of ASCII canvas
    /// * `canvas_height` - Height of ASCII canvas
    /// * `project_fn` - Function to project 3D points to screen coordinates
    ///
    /// # Returns
    ///
    /// Simple ASCII visualization
    pub fn render_simple<F>(
        &self,
        scene: &Scene3D,
        canvas_width: usize,
        canvas_height: usize,
        project_fn: F,
    ) -> Result<String, Box<dyn std::error::Error>>
    where
        F: Fn(&Point3D) -> Point3D + Copy,
    {
        // Create canvas and depth buffer
        let mut canvas = AsciiCanvas::new(canvas_width, canvas_height);
        let mut depth_buffer = DepthBuffer::new(canvas_width, canvas_height);

        // Render scene elements
        render_floors(&scene.floors, &mut canvas, &mut depth_buffer, project_fn);
        render_equipment(
            &scene.equipment,
            &mut canvas,
            &mut depth_buffer,
            project_fn,
        );
        render_rooms(&scene.rooms, &mut canvas, &mut depth_buffer, project_fn);

        Ok(canvas.to_string())
    }

    /// Render to existing canvas and depth buffer
    ///
    /// Low-level rendering for custom canvas management.
    ///
    /// # Arguments
    ///
    /// * `scene` - 3D scene to render
    /// * `canvas` - Mutable ASCII canvas
    /// * `depth_buffer` - Mutable depth buffer
    /// * `project_fn` - Function to project 3D points to screen coordinates
    pub fn render_to_canvas<F>(
        &self,
        scene: &Scene3D,
        canvas: &mut AsciiCanvas,
        depth_buffer: &mut DepthBuffer,
        project_fn: F,
    ) where
        F: Fn(&Point3D) -> Point3D + Copy,
    {
        render_floors(&scene.floors, canvas, depth_buffer, project_fn);
        render_equipment(&scene.equipment, canvas, depth_buffer, project_fn);
        render_rooms(&scene.rooms, canvas, depth_buffer, project_fn);
    }
}

impl Default for AsciiRenderer {
    fn default() -> Self {
        Self::new()
    }
}

/// Camera information for rendering
#[derive(Debug, Clone)]
pub struct CameraInfo {
    pub position: Point3D,
    pub target: Point3D,
}

/// Projection information for rendering
#[derive(Debug, Clone)]
pub struct ProjectionInfo {
    pub projection_type: String,
    pub view_angle: String,
    pub scale: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::render3d::types::{Floor3D, SceneMetadata};
    use crate::spatial::BoundingBox3D;
    use std::sync::Arc;

    fn create_test_scene() -> Scene3D {
        Scene3D {
            building_name: Arc::new("Test Building".to_string()),
            floors: vec![],
            equipment: vec![],
            rooms: vec![],
            bounding_box: BoundingBox3D {
                min: Point3D {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                },
                max: Point3D {
                    x: 100.0,
                    y: 100.0,
                    z: 10.0,
                },
            },
            metadata: SceneMetadata {
                total_floors: 1,
                total_rooms: 0,
                total_equipment: 0,
                render_time_ms: 0,
                projection_type: "Isometric".to_string(),
                view_angle: "45deg".to_string(),
            },
        }
    }

    #[test]
    fn test_ascii_renderer_creation() {
        let renderer = AsciiRenderer::new();
        // Should not panic
        drop(renderer);
    }

    #[test]
    fn test_render_simple() {
        let renderer = AsciiRenderer::new();
        let scene = create_test_scene();
        let project_fn = |p: &Point3D| Point3D {
            x: p.x,
            y: p.y,
            z: p.z,
        };

        let result = renderer.render_simple(&scene, 80, 24, project_fn);
        assert!(result.is_ok());
    }

    #[test]
    fn test_render_ascii_art() {
        let renderer = AsciiRenderer::new();
        let scene = create_test_scene();
        let project_fn = |p: &Point3D| Point3D {
            x: p.x,
            y: p.y,
            z: p.z,
        };

        let result = renderer.render_ascii_art(&scene, 80, 24, project_fn);
        assert!(result.is_ok());
        let output = result.unwrap();
        assert!(output.contains("Test Building"));
        assert!(output.contains("Legend"));
    }

    #[test]
    fn test_render_advanced() {
        let renderer = AsciiRenderer::new();
        let scene = create_test_scene();
        let camera_info = CameraInfo {
            position: Point3D {
                x: 50.0,
                y: 50.0,
                z: 100.0,
            },
            target: Point3D {
                x: 0.0,
                y: 0.0,
                z: 0.0,
            },
        };
        let projection_info = ProjectionInfo {
            projection_type: "Isometric".to_string(),
            view_angle: "45deg".to_string(),
            scale: 1.0,
        };

        let result = renderer.render_advanced(&scene, camera_info, projection_info);
        assert!(result.is_ok());
        let output = result.unwrap();
        assert!(output.contains("Camera"));
        assert!(output.contains("Projection"));
    }
}
