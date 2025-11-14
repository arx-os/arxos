//! Rendering command arguments
//!
//! Argument structures for rendering-related CLI commands including
//! visualization and interactive 3D rendering.

use clap::Args;

/// Arguments for the Render command
///
/// Render building visualization with various options.
#[derive(Debug, Clone, Args)]
pub struct RenderArgs {
    /// Building identifier
    #[arg(long)]
    pub building: String,

    /// Floor number
    #[arg(long)]
    pub floor: Option<i32>,

    /// Enable 3D multi-floor visualization
    #[arg(long)]
    pub three_d: bool,

    /// Show equipment status indicators
    #[arg(long)]
    pub show_status: bool,

    /// Show room boundaries
    #[arg(long)]
    pub show_rooms: bool,

    /// Output format (ascii, advanced, json, yaml)
    #[arg(long, default_value = "ascii")]
    pub format: String,

    /// Projection type for 3D rendering (isometric, orthographic, perspective)
    #[arg(long, default_value = "isometric")]
    pub projection: String,

    /// View angle (45deg, 30deg, top, front, side)
    #[arg(long, default_value = "45deg")]
    pub view_angle: String,

    /// Launch interactive 3D renderer with controls
    #[arg(long)]
    pub interactive: bool,
}

/// Arguments for the Interactive command
///
/// Launch interactive 3D visualization with full controls.
#[derive(Debug, Clone, Args)]
pub struct InteractiveArgs {
    /// Building to visualize
    #[arg(long)]
    pub building: String,

    /// Initial floor to show
    #[arg(long)]
    pub floor: Option<i32>,

    /// Initial projection type
    #[arg(long, default_value = "isometric")]
    pub projection: String,

    /// Show equipment status
    #[arg(long)]
    pub show_status: bool,

    /// Enable spatial queries
    #[arg(long)]
    pub spatial_queries: bool,

    /// Enable animations
    #[arg(long)]
    pub animations: bool,

    /// Animation speed (1-100)
    #[arg(long, default_value = "50", value_parser = validate_animation_speed)]
    pub animation_speed: u32,

    /// Target FPS (1-240)
    #[arg(long, default_value = "30", value_parser = validate_fps)]
    pub fps: u32,

    /// Show FPS counter
    #[arg(long)]
    pub show_fps: bool,

    /// Show help overlay by default
    #[arg(long)]
    pub show_help: bool,
}

/// Validate animation speed is between 1 and 100
fn validate_animation_speed(s: &str) -> Result<u32, String> {
    let val: u32 = s
        .parse()
        .map_err(|_| "must be a number between 1 and 100".to_string())?;
    if val < 1 || val > 100 {
        Err(format!(
            "Animation speed must be between 1 and 100, got {}",
            val
        ))
    } else {
        Ok(val)
    }
}

/// Validate FPS is between 1 and 240
fn validate_fps(s: &str) -> Result<u32, String> {
    let val: u32 = s
        .parse()
        .map_err(|_| "must be a number between 1 and 240".to_string())?;
    if val < 1 || val > 240 {
        Err(format!("FPS must be between 1 and 240, got {}", val))
    } else {
        Ok(val)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_animation_speed() {
        assert!(validate_animation_speed("50").is_ok());
        assert!(validate_animation_speed("1").is_ok());
        assert!(validate_animation_speed("100").is_ok());
        assert!(validate_animation_speed("0").is_err());
        assert!(validate_animation_speed("101").is_err());
    }

    #[test]
    fn test_validate_fps() {
        assert!(validate_fps("30").is_ok());
        assert!(validate_fps("1").is_ok());
        assert!(validate_fps("240").is_ok());
        assert!(validate_fps("0").is_err());
        assert!(validate_fps("241").is_err());
    }
}
