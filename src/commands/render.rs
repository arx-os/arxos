// Render command handlers
// Handles 2D and 3D building visualization

use crate::render3d::{ProjectionType, ViewAngle, Render3DConfig, Building3DRenderer, format_scene_output};
use crate::utils::loading::load_building_data;
use log::{info, warn};

/// Handle the render command for both 2D and 3D building visualization
pub fn handle_render(
    building: String,
    floor: Option<i32>,
    three_d: bool,
    show_status: bool,
    show_rooms: bool,
    format: String,
    projection: String,
    view_angle: String,
    scale: f64,
    spatial_index: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("🎨 Rendering building: {}", building);
    println!("🎨 Rendering building: {}", building);

    // Load building data
    let building_data = load_building_data(&building)?;

    if three_d {
        // 3D rendering
        info!("3D Multi-Floor Visualization");
        println!("🏷️  3D Multi-Floor Visualization");

        // Parse projection type
        let projection_type = match projection.to_lowercase().as_str() {
            "isometric" => ProjectionType::Isometric,
            "orthographic" => ProjectionType::Orthographic,
            "perspective" => ProjectionType::Perspective,
            _ => {
                warn!("⚠️ Unknown projection type '{}', using isometric", projection);
                println!("⚠️ Unknown projection type '{}', using isometric", projection);
                ProjectionType::Isometric
            }
        };

        // Parse view angle
        let view_angle_type = match view_angle.to_lowercase().as_str() {
            "topdown" => ViewAngle::TopDown,
            "front" => ViewAngle::Front,
            "side" => ViewAngle::Side,
            "isometric" => ViewAngle::Isometric,
            _ => {
                warn!("⚠️ Unknown view angle '{}', using isometric", view_angle);
                println!("⚠️ Unknown view angle '{}', using isometric", view_angle);
                ViewAngle::Isometric
            }
        };

        let config = Render3DConfig {
            show_status,
            show_rooms,
            show_equipment: true,
            show_connections: false,
            projection_type,
            view_angle: view_angle_type,
            scale_factor: scale,
            max_width: 120,
            max_height: 40,
        };

        let renderer = Building3DRenderer::new(building_data, config);

        // Apply spatial index if requested
        if spatial_index {
            info!("Building spatial index for enhanced queries...");
            println!("🔍 Building spatial index for enhanced queries...");
            println!("💡 Spatial index integration will be available when IFC data is loaded");
        }

        let scene = renderer.render_3d_advanced()?;

        match format.to_lowercase().as_str() {
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
                return Err(format!("Unsupported format: {}. Supported formats: ascii, advanced, json, yaml", format).into());
            }
        }
    } else {
        // Traditional 2D rendering
        info!("2D Floor Plan Rendering");
        println!("🏢 2D Floor Plan Rendering");

        let renderer = crate::render::BuildingRenderer::new(building_data);

        if let Some(floor_num) = floor {
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

