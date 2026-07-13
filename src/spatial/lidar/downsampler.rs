use crate::core::spatial::Point3D;
use crate::resource_limits::max_lidar_input_points;
use anyhow::{bail, Result};
use std::collections::HashMap;

pub struct IngestionStats {
    pub total_points: usize,
    pub downsampled_points: usize,
}

pub struct VoxelGridFilter {
    voxel_size: f64,
    light_mode: bool,
}

struct VoxelAccumulator {
    sum_x: f64,
    sum_y: f64,
    sum_z: f64,
    count: usize,
}

impl VoxelGridFilter {
    pub fn new(voxel_size: f64, light_mode: bool) -> Self {
        Self {
            voxel_size,
            light_mode,
        }
    }

    pub fn filter(
        &self,
        points: impl Iterator<Item = Result<Point3D>>,
    ) -> Result<(Vec<Point3D>, IngestionStats)> {
        // Enforce light mode constraints
        let voxel_size = if self.light_mode {
            self.voxel_size.max(0.20)
        } else {
            self.voxel_size.max(0.01) // Prevent division-by-zero or extremely tiny voxels
        };

        let max_capacity = if self.light_mode { 100_000 } else { 500_000 };

        let mut voxel_map: HashMap<(i64, i64, i64), VoxelAccumulator> =
            HashMap::with_capacity(max_capacity);
        let mut filtered_points = Vec::new();
        let mut total_points = 0;

        let max_input = max_lidar_input_points();

        for point_result in points {
            let p = point_result?;
            total_points += 1;
            if total_points > max_input {
                bail!(
                    "LiDAR input exceeded pilot point limit ({} points). \
                     Use --light, increase --voxel-size, decimate the scan offline, \
                     or set ARX_MAX_LIDAR_INPUT_POINTS. See docs/resource-limits.md.",
                    max_input
                );
            }

            let key = (
                (p.x / voxel_size).floor() as i64,
                (p.y / voxel_size).floor() as i64,
                (p.z / voxel_size).floor() as i64,
            );

            let entry = voxel_map.entry(key).or_insert(VoxelAccumulator {
                sum_x: 0.0,
                sum_y: 0.0,
                sum_z: 0.0,
                count: 0,
            });

            entry.sum_x += p.x;
            entry.sum_y += p.y;
            entry.sum_z += p.z;
            entry.count += 1;

            // Bounded memory protection: flush if capacity reached
            if voxel_map.len() >= max_capacity {
                self.flush_voxels(&mut voxel_map, &mut filtered_points);
            }
        }

        // Final flush
        self.flush_voxels(&mut voxel_map, &mut filtered_points);

        let stats = IngestionStats {
            total_points,
            downsampled_points: filtered_points.len(),
        };

        Ok((filtered_points, stats))
    }

    fn flush_voxels(
        &self,
        voxel_map: &mut HashMap<(i64, i64, i64), VoxelAccumulator>,
        filtered_points: &mut Vec<Point3D>,
    ) {
        for accum in voxel_map.values() {
            if accum.count > 0 {
                let count_f = accum.count as f64;
                filtered_points.push(Point3D::new(
                    accum.sum_x / count_f,
                    accum.sum_y / count_f,
                    accum.sum_z / count_f,
                ));
            }
        }
        voxel_map.clear();
    }
}
