//! Orthographic view rendering

use crate::render3d::types::{Projection3D, Scene3D, ViewAngle};

/// Render scene in orthographic view
pub fn render_orthographic_view(
    scene: &Scene3D,
    projection: &Projection3D,
    render_top_down: impl Fn(&Scene3D) -> String,
    render_front: impl Fn(&Scene3D) -> String,
    render_side: impl Fn(&Scene3D) -> String,
) -> Result<String, Box<dyn std::error::Error>> {
    let mut output = String::new();

    output.push_str(&format!(
        "📐 Orthographic View ({:?}):\n",
        projection.view_angle
    ));
    output.push_str("┌─────────────────────────────────────────────────────────────┐\n");

    // Render based on view angle
    match projection.view_angle {
        ViewAngle::TopDown => {
            output.push_str("│ Top-Down View (X-Y Plane) │\n");
            output.push_str(&render_top_down(scene));
        }
        ViewAngle::Front => {
            output.push_str("│ Front View (X-Z Plane) │\n");
            output.push_str(&render_front(scene));
        }
        ViewAngle::Side => {
            output.push_str("│ Side View (Y-Z Plane) │\n");
            output.push_str(&render_side(scene));
        }
        _ => {
            output.push_str("│ Orthographic View │\n");
        }
    }

    output.push_str("└─────────────────────────────────────────────────────────────┘\n");

    Ok(output)
}
