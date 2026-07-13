use crate::core::spatial::Point3D;
use crate::core::{Building, Wing};
use anyhow::Result;
use std::path::Path;

pub mod detector;
pub mod downsampler;
pub mod parser;

pub struct LidarPipeline {
    pub voxel_size: f64,
    pub light_mode: bool,
}

impl LidarPipeline {
    pub fn new(voxel_size: f64, light_mode: bool) -> Self {
        Self {
            voxel_size,
            light_mode,
        }
    }

    pub fn process<P: AsRef<Path>>(&self, path: P) -> Result<Building> {
        let path = path.as_ref();
        println!("🚀 Reading points from {}...", path.display());
        let points = parser::stream_points(path)?;

        println!("🧹 Filtering point cloud via voxel downsampler...");
        let downsampler = downsampler::VoxelGridFilter::new(self.voxel_size, self.light_mode);
        let (downsampled_points, stats) = downsampler.filter(points)?;

        println!("🏢 Reconstructing building structure...");
        let building = self.reconstruct_building(path, downsampled_points, stats)?;

        Ok(building)
    }

    fn reconstruct_building(
        &self,
        path: &Path,
        points: Vec<Point3D>,
        stats: downsampler::IngestionStats,
    ) -> Result<Building> {
        let name = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("LiDAR_Import")
            .replace("_", " ")
            .replace("-", " ");

        let mut building = Building::new(name, "".to_string());

        // Compute Bounding Box
        let mut min_x = f64::MAX;
        let mut min_y = f64::MAX;
        let mut min_z = f64::MAX;
        let mut max_x = f64::MIN;
        let mut max_y = f64::MIN;
        let mut max_z = f64::MIN;

        for p in &points {
            if p.x < min_x {
                min_x = p.x;
            }
            if p.y < min_y {
                min_y = p.y;
            }
            if p.z < min_z {
                min_z = p.z;
            }
            if p.x > max_x {
                max_x = p.x;
            }
            if p.y > max_y {
                max_y = p.y;
            }
            if p.z > max_z {
                max_z = p.z;
            }
        }

        // 1. Detect Floor levels
        let floor_detector = detector::FloorDetector::new(0.10, 2.5, 1.5);
        let floor_elevations = floor_detector.detect(&points);

        println!(
            "📶 Detected {} floor level(s): {:?}",
            floor_elevations.len(),
            floor_elevations
        );

        // 2. Detect Rooms and Equipment per Floor slice
        let room_detector = detector::RoomDetector::new(0.20, 2, 16);
        let eq_detector = detector::EquipmentDetector::new(0.40, 4);

        let mut total_rooms = 0;
        let mut total_equipment = 0;

        for (idx, &elev) in floor_elevations.iter().enumerate() {
            let ceil_elev = if idx + 1 < floor_elevations.len() {
                floor_elevations[idx + 1]
            } else {
                max_z
            };

            let mut floor = crate::core::Floor::new(format!("Floor {}", idx + 1), idx as i32);
            floor.level = idx as i32;

            let rooms = room_detector.detect_rooms(&points, elev, ceil_elev);
            println!("🚪 Segmented {} room(s) on Floor {}", rooms.len(), idx + 1);
            total_rooms += rooms.len();

            let mut wing = Wing::new("Main".to_string());
            for mut r in rooms {
                let room_path = format!(
                    "/building/{}/{}",
                    floor.name.to_lowercase().replace(" ", "-"),
                    r.name.to_lowercase().replace(" ", "-")
                );
                let equipment = eq_detector.detect_equipment(
                    &points,
                    &r.spatial_properties.bounding_box,
                    &room_path,
                );

                println!(
                    "   Plugged in {} equipment item(s) in {}",
                    equipment.len(),
                    r.name
                );
                total_equipment += equipment.len();

                for mut eq in equipment {
                    eq.room_id = Some(r.id.clone());
                    r.add_equipment(eq);
                }
                wing.add_room(r);
            }
            floor.add_wing(wing);
            building.add_floor(floor);
        }

        println!(
            "✨ Ingestion complete: Detected {} floor(s), {} room(s), {} equipment item(s)",
            floor_elevations.len(),
            total_rooms,
            total_equipment
        );

        let mut properties = std::collections::HashMap::new();
        properties.insert("total_points".to_string(), stats.total_points.to_string());
        properties.insert(
            "downsampled_points".to_string(),
            stats.downsampled_points.to_string(),
        );

        if !points.is_empty() {
            properties.insert("bbox_min_x".to_string(), min_x.to_string());
            properties.insert("bbox_min_y".to_string(), min_y.to_string());
            properties.insert("bbox_min_z".to_string(), min_z.to_string());
            properties.insert("bbox_max_x".to_string(), max_x.to_string());
            properties.insert("bbox_max_y".to_string(), max_y.to_string());
            properties.insert("bbox_max_z".to_string(), max_z.to_string());
        }

        building.metadata = Some(crate::core::BuildingMetadata {
            source_file: Some(path.to_string_lossy().into_owned()),
            parser_version: env!("CARGO_PKG_VERSION").to_string(),
            total_entities: stats.total_points,
            spatial_entities: stats.downsampled_points,
            coordinate_system: "building_local".to_string(),
            units: "meters".to_string(),
            tags: vec!["lidar".to_string(), "point_cloud".to_string()],
            properties,
        });

        Ok(building)
    }
}
