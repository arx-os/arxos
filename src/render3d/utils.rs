//! Utility functions for 3D rendering

use super::types::Scene3D;

/// Convert 3D scene to different output formats
pub fn format_scene_output(scene: &Scene3D, format: &str) -> Result<String, Box<dyn std::error::Error>> {
    match format.to_lowercase().as_str() {
        "json" => {
            Ok(serde_json::to_string_pretty(scene)?)
        }
        "yaml" => {
            Ok(serde_yaml::to_string(scene)?)
        }
        "ascii" => {
            // This would be handled by the renderer
            Ok("ASCII rendering handled by renderer".to_string())
        }
        _ => {
            Err(format!("Unsupported output format: {}", format).into())
        }
    }
}

