//! Screen coordinate label projector translating spatial offsets to 2D percentages.

use crate::core::Anchor;
use crate::core::Position;

/// Representation of an HTML text-label absolute overlay positioning and payload.
#[derive(Debug, Clone)]
pub struct ScreenLabel {
    /// Associated Anchor.
    pub anchor: Anchor,
    /// Absolute horizontal CSS layout percentage (0% to 100%).
    pub x_percent: f64,
    /// Absolute vertical CSS layout percentage (0% to 100%).
    pub y_percent: f64,
    /// Display title/name of the anchor/equipment.
    pub title: String,
    /// Details (e.g. circuit ID, metadata).
    pub subtitle: String,
    /// True if the parent building/anchor is provisional (/building).
    pub is_provisional: bool,
    /// Distance in meters to the worker.
    pub distance_m: f64,
}

pub struct LabelProjector;

impl LabelProjector {
    /// Map spatial anchor positions to 2D viewport percentages based on heading and coordinates.
    pub fn project_labels(
        visible_anchors: &[Anchor],
        worker_pos: &Position,
        heading_deg: f64,
        fov_degrees: Option<f64>,
    ) -> Vec<ScreenLabel> {
        let mut labels = Vec::new();
        let heading_rad = heading_deg.to_radians();

        // Horizontal Field of View approximation (e.g. 60 degrees default or override)
        let fov_deg = fov_degrees.unwrap_or(60.0);
        let fov_rad = fov_deg.to_radians();

        for anchor in visible_anchors {
            let dx = anchor.position.x - worker_pos.x;
            let dy = anchor.position.y - worker_pos.y;
            let dz = anchor.position.z - worker_pos.z;
            let distance = (dx*dx + dy*dy + dz*dz).sqrt();

            if distance < 0.1 {
                continue; // Avoid division by zero
            }

            // Calculate angle offset relative to worker's horizontal heading vector
            let angle_to_anchor = dy.atan2(dx);
            let angle_diff = angle_to_anchor - heading_rad;

            // Normalize angle diff to (-PI, PI]
            let angle_diff = (angle_diff + std::f64::consts::PI).rem_euclid(2.0 * std::f64::consts::PI) - std::f64::consts::PI;

            // If anchor is within the camera's FOV (front view)
            if angle_diff.abs() <= fov_rad / 2.0 {
                // Map horizontal position: -FOV/2 is left (10%), +FOV/2 is right (90%)
                let x_norm = (angle_diff / (fov_rad / 2.0) + 1.0) / 2.0; // 0.0 to 1.0
                let x_percent = 10.0 + x_norm * 80.0; // Fit between 10% and 90%

                // Map vertical position using relative Z height:
                // If anchor is higher than worker, position higher up.
                let z_scale = (dz / distance).clamp(-1.0, 1.0);
                let y_norm = (z_scale + 1.0) / 2.0; // 0.0 to 1.0
                let y_percent = 90.0 - y_norm * 80.0; // Invert for screen space (0% is top)

                // Subtitle composition containing properties or circuit details
                let circuit_id = anchor.properties.get("circuit_id").cloned()
                    .unwrap_or_else(|| "No Circuit ID".to_string());
                let subtitle = format!("Circuit: {} | Saturation: {:.2}", circuit_id, anchor.data_saturation(anchor.relative_poses.len()));

                let is_provisional = if let Some(addr) = &anchor.address {
                    addr.path.starts_with("/building")
                } else {
                    true
                };

                labels.push(ScreenLabel {
                    anchor: anchor.clone(),
                    x_percent,
                    y_percent,
                    title: anchor.name.clone(),
                    subtitle,
                    is_provisional,
                    distance_m: distance,
                });
            }
        }

        // Post-process to resolve label overlap in viewport via vertical clustering
        labels.sort_by(|a, b| a.x_percent.partial_cmp(&b.x_percent).unwrap_or(std::cmp::Ordering::Equal));
        for i in 0..labels.len() {
            for j in (i + 1)..labels.len() {
                let dx = (labels[i].x_percent - labels[j].x_percent).abs();
                let dy = (labels[i].y_percent - labels[j].y_percent).abs();
                // If close horizontally and vertically, offset the second label vertically
                if dx < 12.0 && dy < 10.0 {
                    labels[j].y_percent = (labels[i].y_percent + 12.0).min(95.0);
                }
            }
        }

        labels
    }
}
