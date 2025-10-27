// Interactive 3D rendering command handler

use crate::render3d::{ProjectionType, ViewAngle, Render3DConfig, InteractiveConfig, InteractiveRenderer};
use crate::utils::loading::load_building_data;
use log::{info, warn};

/// Handle the interactive 3D building visualization command
pub fn handle_interactive(
    building: String,
    projection: String,
    view_angle: String,
    scale: f64,
    width: usize,
    height: usize,
    spatial_index: bool,
    show_status: bool,
    show_rooms: bool,
    show_connections: bool,
    fps: u32,
    show_fps: bool,
    show_help: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("🔮 Interactive 3D Building Visualization: {}", building);
    println!("🔮 Interactive 3D Building Visualization: {}", building);

    // Load building data
    let building_data = load_building_data(&building)?;

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

    // Create render configuration
    let render_config = Render3DConfig {
        show_status,
        show_rooms,
        show_equipment: true,
        show_connections,
        projection_type: projection_type.clone(),
        view_angle: view_angle_type.clone(),
        scale_factor: scale,
        max_width: width,
        max_height: height,
    };

    // Create interactive configuration
    let interactive_config = InteractiveConfig {
        target_fps: fps,
        real_time_updates: true,
        show_fps,
        show_help,
        auto_hide_help: true,
        help_duration: std::time::Duration::from_secs(5),
    };

    // Create interactive renderer
    let mut interactive_renderer = InteractiveRenderer::with_config(
        building_data,
        render_config,
        interactive_config
    )?;

    // Apply spatial index if requested
    if spatial_index {
        info!("Enabling spatial index integration...");
        println!("🔍 Enabling spatial index integration...");
        // Note: Spatial index integration would be added here
    }

    // Start interactive session
    info!("Starting interactive session");
    interactive_renderer.start_interactive_session()?;

    println!("✅ Interactive session completed");
    Ok(())
}

