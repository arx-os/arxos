// Render command handlers
// Handles 2D and 3D building visualization

use crate::render3d::{
    format_scene_output, Building3DRenderer, ProjectionType, Render3DConfig, ViewAngle,
};
use crate::utils::loading::load_building_data;
use log::{info, warn};

/// Configuration for the render command
///
/// Controls both 2D floor plan and 3D building visualization rendering.
#[derive(Debug, Clone)]
pub struct RenderCommandConfig {
    /// Building name to render
    pub building: String,
    /// Specific floor to render (None for all floors)
    pub floor: Option<i32>,
    /// Enable 3D rendering mode
    pub three_d: bool,
    /// Show equipment status indicators
    pub show_status: bool,
    /// Show room boundaries and labels
    pub show_rooms: bool,
    /// Output format (ascii, advanced, json, yaml)
    pub format: String,
    /// Projection type for 3D (isometric, orthographic, perspective)
    pub projection: String,
    /// View angle for 3D (topdown, front, side, isometric)
    pub view_angle: String,
    /// Scale factor for rendering
    pub scale: f64,
    /// Build spatial index for enhanced queries
    pub spatial_index: bool,
}

/// Handle the render command for both 2D and 3D building visualization
pub fn handle_render(config: RenderCommandConfig) -> Result<(), Box<dyn std::error::Error>> {
    info!("🎨 Rendering building: {}", config.building);
    println!("🎨 Rendering building: {}", config.building);

    // Load building data
    let building_data = load_building_data(&config.building)?;

    if config.three_d {
        // 3D rendering
        info!("3D Multi-Floor Visualization");
        println!("🏷️  3D Multi-Floor Visualization");

        // Parse projection type
        let projection_type = match config.projection.to_lowercase().as_str() {
            "isometric" => ProjectionType::Isometric,
            "orthographic" => ProjectionType::Orthographic,
            "perspective" => ProjectionType::Perspective,
            _ => {
                warn!(
                    "⚠️ Unknown projection type '{}', using isometric",
                    config.projection
                );
                println!(
                    "⚠️ Unknown projection type '{}', using isometric",
                    config.projection
                );
                ProjectionType::Isometric
            }
        };

        // Parse view angle
        let view_angle_type = match config.view_angle.to_lowercase().as_str() {
            "topdown" => ViewAngle::TopDown,
            "front" => ViewAngle::Front,
            "side" => ViewAngle::Side,
            "isometric" => ViewAngle::Isometric,
            _ => {
                warn!(
                    "⚠️ Unknown view angle '{}', using isometric",
                    config.view_angle
                );
                println!(
                    "⚠️ Unknown view angle '{}', using isometric",
                    config.view_angle
                );
                ViewAngle::Isometric
            }
        };

        let render_config = Render3DConfig {
            show_status: config.show_status,
            show_rooms: config.show_rooms,
            show_equipment: true,
            show_connections: false,
            projection_type,
            view_angle: view_angle_type,
            scale_factor: config.scale,
            max_width: 120,
            max_height: 40,
        };

        let renderer = Building3DRenderer::new(building_data, render_config);

        // Apply spatial index if requested
        if config.spatial_index {
            info!("Building spatial index for enhanced queries...");
            println!("🔍 Building spatial index for enhanced queries...");
            println!("💡 Spatial index integration will be available when IFC data is loaded");
        }

        let scene = renderer.render_3d_advanced()?;

        match config.format.to_lowercase().as_str() {
            "json" => {
                let json_output = format_scene_output(&scene, "json")?;
                println!("{}", json_output);
            }
            "yaml" => {
                let yaml_output = format_scene_output(&scene, "yaml")?;
                println!("{}", yaml_output);
            }
            "ascii" => {
                // Use the new advanced ASCII art rendering
                let ascii_output = renderer.render_3d_ascii_art(&scene)?;
                println!("{}", ascii_output);
            }
            "advanced" => {
                // Use the advanced projection-based rendering
                let advanced_output = renderer.render_to_ascii_advanced(&scene)?;
                println!("{}", advanced_output);
            }
            _ => {
                return Err(format!(
                    "Unsupported format: {}. Supported formats: ascii, advanced, json, yaml",
                    config.format
                )
                .into());
            }
        }
    } else {
        // Traditional 2D rendering
        info!("2D Floor Plan Rendering");
        println!("🏢 2D Floor Plan Rendering");

        let renderer = crate::render::BuildingRenderer::new(building_data);

        if let Some(floor_num) = config.floor {
            println!("Floor: {}", floor_num);
            renderer.render_floor(floor_num)?;
        } else {
            // Render all floors
            for floor_data in renderer.floors() {
                renderer.render_floor(floor_data.level)?;
                println!(); // Add spacing between floors
            }
        }
    }

    println!("✅ Rendering completed");
    Ok(())
}
