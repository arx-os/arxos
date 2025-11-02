// Interactive 3D rendering command handler

use crate::render3d::{ProjectionType, ViewAngle, Render3DConfig, InteractiveConfig, InteractiveRenderer};
use crate::utils::loading::load_building_data;
use log::{info, warn};

/// Configuration for the interactive 3D rendering command
///
/// Enables real-time interactive manipulation of 3D building visualization.
#[derive(Debug, Clone)]
pub struct InteractiveCommandConfig {
    /// Building name to visualize
    pub building: String,
    /// Projection type for 3D (isometric, orthographic, perspective)
    pub projection: String,
    /// View angle for 3D (topdown, front, side, isometric)
    pub view_angle: String,
    /// Scale factor for rendering
    pub scale: f64,
    /// Terminal width in characters
    pub width: usize,
    /// Terminal height in characters
    pub height: usize,
    /// Build spatial index for enhanced queries
    pub spatial_index: bool,
    /// Show equipment status indicators
    pub show_status: bool,
    /// Show room boundaries and labels
    pub show_rooms: bool,
    /// Show equipment connections
    pub show_connections: bool,
    /// Target frames per second
    pub fps: u32,
    /// Display FPS counter
    pub show_fps: bool,
    /// Display help overlay
    pub show_help: bool,
}

/// Handle the interactive 3D building visualization command
pub fn handle_interactive(config: InteractiveCommandConfig) -> Result<(), Box<dyn std::error::Error>> {
    info!("🔮 Interactive 3D Building Visualization: {}", config.building);
    println!("🔮 Interactive 3D Building Visualization: {}", config.building);

    // Load building data
    let building_data = load_building_data(&config.building)?;

    // Parse projection type
    let projection_type = match config.projection.to_lowercase().as_str() {
        "isometric" => ProjectionType::Isometric,
        "orthographic" => ProjectionType::Orthographic,
        "perspective" => ProjectionType::Perspective,
        _ => {
            warn!("⚠️ Unknown projection type '{}', using isometric", config.projection);
            println!("⚠️ Unknown projection type '{}', using isometric", config.projection);
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
            warn!("⚠️ Unknown view angle '{}', using isometric", config.view_angle);
            println!("⚠️ Unknown view angle '{}', using isometric", config.view_angle);
            ViewAngle::Isometric
        }
    };

    // Create render configuration
    let render_config = Render3DConfig {
        show_status: config.show_status,
        show_rooms: config.show_rooms,
        show_equipment: true,
        show_connections: config.show_connections,
        projection_type: projection_type.clone(),
        view_angle: view_angle_type.clone(),
        scale_factor: config.scale,
        max_width: config.width,
        max_height: config.height,
    };

    // Create interactive configuration
    let interactive_config = InteractiveConfig {
        target_fps: config.fps,
        real_time_updates: true,
        show_fps: config.show_fps,
        show_help: config.show_help,
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
    if config.spatial_index {
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

