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
    /// The number of additional labels clustered/collapsed into this one.
    pub cluster_count: usize,
}

pub struct LabelProjector;

impl LabelProjector {
    /// Map spatial anchor positions to 2D viewport percentages based on heading and coordinates.
    pub fn project_labels(
        visible_anchors: &[Anchor],
        worker_pos: &Position,
        heading_deg: f64,
        fov_degrees: Option<f64>,
        cluster_threshold: Option<f64>,
        max_labels: Option<usize>,
    ) -> Vec<ScreenLabel> {
        let mut labels = Vec::new();
        let heading_rad = heading_deg.to_radians();

        // Horizontal Field of View approximation (e.g. 60 degrees default or override)
        let fov_deg = fov_degrees.unwrap_or(60.0);
        let fov_rad = fov_deg.to_radians();

        let threshold = cluster_threshold.unwrap_or(15.0);
        let limit = max_labels.unwrap_or(20);

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
                    cluster_count: 0,
                });
            }
        }

        // 1. Dynamic Priority Sorting: prioritize closer labels first
        labels.sort_by(|a, b| a.distance_m.partial_cmp(&b.distance_m).unwrap_or(std::cmp::Ordering::Equal));
        if labels.len() > limit {
            labels.truncate(limit);
        }

        // 2. Greedy vertical stacking and collision resolution (O(N log N))
        // Sort by horizontal position x_percent first
        labels.sort_by(|a, b| a.x_percent.partial_cmp(&b.x_percent).unwrap_or(std::cmp::Ordering::Equal));

        let mut placed: Vec<ScreenLabel> = Vec::new();

        for mut label in labels {
            let mut stack_y = label.y_percent;

            // Find previously placed labels that overlap horizontally within the cluster_threshold
            let mut overlapping_indices: Vec<usize> = Vec::new();
            for (idx, p) in placed.iter().enumerate() {
                if (p.x_percent - label.x_percent).abs() < threshold {
                    overlapping_indices.push(idx);
                }
            }

            if !overlapping_indices.is_empty() {
                // Sort overlapping labels by y_percent ascending (top to bottom)
                overlapping_indices.sort_by(|&a, &b| placed[a].y_percent.partial_cmp(&placed[b].y_percent).unwrap_or(std::cmp::Ordering::Equal));

                let label_height = 12.0; // visual percentage height offset in viewport
                for idx in overlapping_indices {
                    let p = &placed[idx];
                    if (p.y_percent - stack_y).abs() < label_height {
                        stack_y = p.y_percent + label_height;
                    }
                }
            }

            // Exceeds viewport limit check (clamp/collapse)
            if stack_y > 90.0 {
                // Find closest horizontal overlapping label to collapse into
                let mut best_match: Option<usize> = None;
                let mut min_dx = f64::MAX;
                for (idx, p) in placed.iter().enumerate() {
                    let dx = (p.x_percent - label.x_percent).abs();
                    if dx < threshold && dx < min_dx {
                        min_dx = dx;
                        best_match = Some(idx);
                    }
                }
                if let Some(idx) = best_match {
                    placed[idx].cluster_count += 1;
                } else {
                    label.y_percent = 90.0;
                    placed.push(label);
                }
            } else {
                label.y_percent = stack_y;
                placed.push(label);
            }
        }

        placed
    }
}
