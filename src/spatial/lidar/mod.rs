use crate::core::spatial::Point3D;
use crate::core::{Building, Wing};
use anyhow::{bail, Result};
use std::path::Path;

pub mod detector;
pub mod downsampler;
pub mod parser;

pub struct LidarPipeline {
    pub voxel_size: f64,
    pub light_mode: bool,
}

/// Outcome of file LiDAR structure assist (Decision 10: geometry disposable; entities proposed).
#[derive(Debug)]
pub struct LidarProcessResult {
    pub building: Building,
    /// Honesty lines for LossReport / CLI (code, message).
    pub warnings: Vec<(String, String)>,
    pub floors_detected: usize,
    pub rooms_segmented: usize,
    pub rooms_fallback: usize,
    pub equipment: usize,
    pub total_points: usize,
    pub downsampled_points: usize,
}

impl LidarPipeline {
    pub fn new(voxel_size: f64, light_mode: bool) -> Self {
        Self {
            voxel_size,
            light_mode,
        }
    }

    pub fn process<P: AsRef<Path>>(&self, path: P) -> Result<LidarProcessResult> {
        let path = path.as_ref();
        println!("🚀 Reading points from {}...", path.display());
        let points = parser::stream_points(path)?;

        println!("🧹 Filtering point cloud via voxel downsampler...");
        let downsampler = downsampler::VoxelGridFilter::new(self.voxel_size, self.light_mode);
        let (downsampled_points, stats) = downsampler.filter(points)?;

        if downsampled_points.is_empty() {
            bail!(
                "LiDAR file produced zero points after read/downsample ({}). \
                 Check format (PLY/LAS/XYZ), units, and that the file is not empty. \
                 See docs/reference/resource-limits.md and docs/reference/lidar-confidence.md.",
                path.display()
            );
        }

        println!("🏢 Reconstructing building structure...");
        self.reconstruct_building(path, downsampled_points, stats)
    }

    fn reconstruct_building(
        &self,
        path: &Path,
        points: Vec<Point3D>,
        stats: downsampler::IngestionStats,
    ) -> Result<LidarProcessResult> {
        let mut warnings: Vec<(String, String)> = Vec::new();

        let name = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("LiDAR_Import")
            .replace(['_', '-'], " ");

        let mut building = Building::new(name, "".to_string());

        let mut min_x = f64::MAX;
        let mut min_y = f64::MAX;
        let mut min_z = f64::MAX;
        let mut max_x = f64::MIN;
        let mut max_y = f64::MIN;
        let mut max_z = f64::MIN;

        for p in &points {
            min_x = min_x.min(p.x);
            min_y = min_y.min(p.y);
            min_z = min_z.min(p.z);
            max_x = max_x.max(p.x);
            max_y = max_y.max(p.y);
            max_z = max_z.max(p.z);
        }

        let effective_voxel = if self.light_mode {
            self.voxel_size.max(0.20)
        } else {
            self.voxel_size.max(0.01)
        };

        // 1. Detect Floor levels
        let floor_detector = detector::FloorDetector::new(0.10, 2.5, 1.5);
        let floor_elevations = floor_detector.detect(&points);

        println!(
            "📶 Detected {} floor level(s): {:?}",
            floor_elevations.len(),
            floor_elevations
        );

        if floor_elevations.len() == 1 && (max_z - min_z) < 1.5 {
            warnings.push((
                "lidar_single_level".into(),
                format!(
                    "Vertical span {:.2} m — treated as one level (not multi-story). \
                     Confirm units are meters.",
                    max_z - min_z
                ),
            ));
        }

        // 2. Detect Rooms and Equipment per Floor slice
        let room_detector = detector::RoomDetector::new(0.20, 2, 16);
        let eq_detector = detector::EquipmentDetector::new(0.40, 4);

        let mut total_rooms_seg = 0;
        let mut total_rooms_fb = 0;
        let mut total_equipment = 0;

        for (idx, &elev) in floor_elevations.iter().enumerate() {
            let ceil_elev = if idx + 1 < floor_elevations.len() {
                floor_elevations[idx + 1]
            } else {
                // Include top slab points; ensure non-zero band for thin clouds
                (max_z + 0.1).max(elev + 2.4)
            };

            let mut floor = crate::core::Floor::new(format!("Floor {}", idx + 1), idx as i32);
            floor.level = idx as i32;

            // Points in this story band (generous) for fallback bbox
            let band_points: Vec<Point3D> = points
                .iter()
                .filter(|p| p.z >= elev - 0.15 && p.z <= ceil_elev + 0.15)
                .cloned()
                .collect();

            let mut rooms = room_detector.detect_rooms(&points, elev, ceil_elev);
            let segmented = rooms.len();
            total_rooms_seg += segmented;

            if rooms.is_empty() {
                // Real field scans often lack closed free-space components.
                let fb_name = if floor_elevations.len() == 1 {
                    "Room 1".to_string()
                } else {
                    format!("Room Floor-{}-1", idx + 1)
                };
                let source_pts = if band_points.is_empty() {
                    &points
                } else {
                    &band_points
                };
                if let Some(room) = detector::proposed_room_from_point_bbox(
                    fb_name,
                    source_pts,
                    elev,
                    ceil_elev.max(elev + 2.0),
                ) {
                    warnings.push((
                        "lidar_room_fallback".into(),
                        format!(
                            "Floor {}: occupancy-grid found 0 enclosed rooms; \
                             created proposed bbox footprint from point extent \
                             (heuristic=bbox_fallback). Human review required.",
                            idx + 1
                        ),
                    ));
                    rooms.push(room);
                    total_rooms_fb += 1;
                }
            }

            println!("🚪 Segmented {} room(s) on Floor {}", rooms.len(), idx + 1);

            let mut wing = Wing::new("Main".to_string());
            for mut r in rooms {
                // Ensure provenance even if detector path already stamped
                if !r.properties.contains_key("capture_source") {
                    detector::stamp_lidar_room_provenance(
                        &mut r,
                        "occupancy_grid",
                        "LiDAR auto room",
                    );
                }

                let room_path = format!(
                    "/building/{}/{}",
                    floor.name.to_lowercase().replace(' ', "-"),
                    r.name.to_lowercase().replace(' ', "-")
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
                    eq.properties
                        .insert("capture_source".into(), "lidar_file".into());
                    r.add_equipment(eq);
                }
                wing.add_room(r);
            }
            floor.add_wing(wing);
            building.add_floor(floor);
        }

        // Last resort: detector produced floors but still no rooms somehow
        if building.get_all_rooms().is_empty() && !points.is_empty() {
            warnings.push((
                "lidar_global_fallback".into(),
                "No per-floor rooms; created single proposed room from full cloud extent."
                    .into(),
            ));
            let elev = floor_elevations.first().copied().unwrap_or(min_z);
            let ceil = (max_z + 0.1).max(elev + 2.4);
            if let Some(room) =
                detector::proposed_room_from_point_bbox("Room 1".into(), &points, elev, ceil)
            {
                if building.floors.is_empty() {
                    let mut floor = crate::core::Floor::new("Floor 1".into(), 0);
                    let mut wing = Wing::new("Main".into());
                    wing.add_room(room);
                    floor.add_wing(wing);
                    building.add_floor(floor);
                } else if let Some(w) = building.floors[0].wings.first_mut() {
                    w.add_room(room);
                }
                total_rooms_fb += 1;
            }
        }

        println!(
            "✨ Ingestion complete: Detected {} floor(s), {} room(s) ({} segmented + {} fallback), {} equipment item(s)",
            floor_elevations.len(),
            total_rooms_seg + total_rooms_fb,
            total_rooms_seg,
            total_rooms_fb,
            total_equipment
        );

        if total_equipment == 0 {
            warnings.push((
                "lidar_no_equipment".into(),
                "No equipment clusters auto-detected (common on sparse or wall-only scans). \
                 Add fixtures via `arx edit` or accept structure-only model."
                    .into(),
            ));
        }

        if self.light_mode {
            warnings.push((
                "lidar_light_mode".into(),
                format!(
                    "Light mode on (voxel ≥ {:.2} m, lower capacity). Prefer for laptops; \
                     re-run without --light on a stronger node if structure looks too coarse.",
                    effective_voxel
                ),
            ));
        }

        let reduction = if stats.total_points > 0 {
            100.0 * (1.0 - (stats.downsampled_points as f64 / stats.total_points as f64))
        } else {
            0.0
        };
        if reduction > 90.0 {
            warnings.push((
                "lidar_heavy_downsample".into(),
                format!(
                    "Downsampled {:.0}% of points ({} → {}). Increase voxel carefully or use \
                     denser regions if rooms look wrong.",
                    reduction, stats.total_points, stats.downsampled_points
                ),
            ));
        }

        warnings.push((
            "lidar_proposed_only".into(),
            "All LiDAR structure is review_status=proposed (Decision 10). \
             Do not treat as official until human accept; prefer --approved-only on export."
                .into(),
        ));

        let mut properties = std::collections::HashMap::new();
        properties.insert("total_points".to_string(), stats.total_points.to_string());
        properties.insert(
            "downsampled_points".to_string(),
            stats.downsampled_points.to_string(),
        );
        properties.insert("capture_source".to_string(), "lidar_file".to_string());
        properties.insert("voxel_size_m".to_string(), effective_voxel.to_string());
        properties.insert("light_mode".to_string(), self.light_mode.to_string());
        properties.insert(
            "rooms_segmented".to_string(),
            total_rooms_seg.to_string(),
        );
        properties.insert("rooms_fallback".to_string(), total_rooms_fb.to_string());
        properties.insert(
            "capture_note".to_string(),
            "Structure assist only; dense cloud not stored as product (Decision 10)".to_string(),
        );

        properties.insert("bbox_min_x".to_string(), min_x.to_string());
        properties.insert("bbox_min_y".to_string(), min_y.to_string());
        properties.insert("bbox_min_z".to_string(), min_z.to_string());
        properties.insert("bbox_max_x".to_string(), max_x.to_string());
        properties.insert("bbox_max_y".to_string(), max_y.to_string());
        properties.insert("bbox_max_z".to_string(), max_z.to_string());

        building.metadata = Some(crate::core::BuildingMetadata {
            source_file: Some(path.to_string_lossy().into_owned()),
            parser_version: env!("CARGO_PKG_VERSION").to_string(),
            total_entities: stats.total_points,
            spatial_entities: stats.downsampled_points,
            coordinate_system: "building_local".to_string(),
            units: "meters".to_string(),
            tags: vec![
                "lidar".to_string(),
                "point_cloud".to_string(),
                "proposed_structure".to_string(),
            ],
            properties,
        });

        Ok(LidarProcessResult {
            building,
            warnings,
            floors_detected: floor_elevations.len(),
            rooms_segmented: total_rooms_seg,
            rooms_fallback: total_rooms_fb,
            equipment: total_equipment,
            total_points: stats.total_points,
            downsampled_points: stats.downsampled_points,
        })
    }
}
