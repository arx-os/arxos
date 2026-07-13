use crate::core::spatial::Point3D;
use crate::core::{
    BoundingBox, Dimensions, Equipment, EquipmentType, LidarEnrichment, Position, Room, RoomType,
    SpatialProperties,
};
use std::collections::{HashMap, VecDeque};

pub struct DetectedFloor {
    pub elevation: f64,
    pub floor_index: i32,
    pub rooms: Vec<Room>,
}

pub struct FloorDetector {
    bin_size: f64,
    min_floor_height: f64,
    density_factor: f64,
}

impl FloorDetector {
    pub fn new(bin_size: f64, min_floor_height: f64, density_factor: f64) -> Self {
        Self {
            bin_size,
            min_floor_height,
            density_factor,
        }
    }

    /// Detect floor elevations from the downsampled points
    pub fn detect(&self, points: &[Point3D]) -> Vec<f64> {
        if points.is_empty() {
            return Vec::new();
        }

        let mut min_z = f64::MAX;
        let mut max_z = f64::MIN;
        for p in points {
            if p.z < min_z {
                min_z = p.z;
            }
            if p.z > max_z {
                max_z = p.z;
            }
        }

        // If the vertical spread is too small, assume a single floor
        if max_z - min_z < self.min_floor_height {
            return vec![min_z];
        }

        let bin_count = ((max_z - min_z) / self.bin_size).ceil() as usize + 1;
        let mut bins = vec![0; bin_count];

        for p in points {
            let idx = ((p.z - min_z) / self.bin_size).floor() as usize;
            if idx < bin_count {
                bins[idx] += 1;
            }
        }

        let total_points = points.len();
        let avg_bin_count = total_points as f64 / bin_count as f64;
        let min_density = avg_bin_count * self.density_factor;

        // Window size for local maxima search (e.g. ±0.3 meters)
        let window = (0.3 / self.bin_size).ceil() as usize;
        let mut candidates = Vec::new();

        for i in 0..bin_count {
            let count = bins[i];
            if (count as f64) < min_density {
                continue;
            }

            // Check local maximum
            let start = i.saturating_sub(window);
            let end = (i + window).min(bin_count - 1);
            let is_max = bins
                .iter()
                .enumerate()
                .take(end + 1)
                .skip(start)
                .all(|(j, &c)| i == j || c <= count);

            if is_max {
                let elevation = min_z + (i as f64 * self.bin_size);
                candidates.push((elevation, count));
            }
        }

        // Sort candidates by density (descending)
        candidates.sort_by_key(|b| std::cmp::Reverse(b.1));

        // Enforce story separation (Non-maximum suppression vertically)
        let mut selected_elevations: Vec<f64> = Vec::new();
        for &(elev, _) in &candidates {
            let mut too_close = false;
            for &existing in &selected_elevations {
                if (elev - existing).abs() < self.min_floor_height {
                    too_close = true;
                    break;
                }
            }
            if !too_close {
                selected_elevations.push(elev);
            }
        }

        selected_elevations.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        // Ensure we always return at least one floor level if candidates were empty
        if selected_elevations.is_empty() {
            selected_elevations.push(min_z);
        }

        selected_elevations
    }
}

pub struct RoomDetector {
    grid_resolution: f64,
    wall_threshold: usize,
    min_room_cells: usize,
}

impl RoomDetector {
    pub fn new(grid_resolution: f64, wall_threshold: usize, min_room_cells: usize) -> Self {
        Self {
            grid_resolution,
            wall_threshold,
            min_room_cells,
        }
    }

    /// Detect rooms for a given floor slice
    pub fn detect_rooms(&self, points: &[Point3D], floor_elev: f64, ceil_elev: f64) -> Vec<Room> {
        let slice_points: Vec<&Point3D> = points
            .iter()
            .filter(|p| p.z >= (floor_elev + 0.5) && p.z < (ceil_elev - 0.5))
            .collect();

        if slice_points.is_empty() {
            return Vec::new();
        }

        // 1. Compute 2D Bounds
        let mut min_x = f64::MAX;
        let mut max_x = f64::MIN;
        let mut min_y = f64::MAX;
        let mut max_y = f64::MIN;

        for p in &slice_points {
            if p.x < min_x {
                min_x = p.x;
            }
            if p.x > max_x {
                max_x = p.x;
            }
            if p.y < min_y {
                min_y = p.y;
            }
            if p.y > max_y {
                max_y = p.y;
            }
        }

        let cols = ((max_x - min_x) / self.grid_resolution).ceil() as usize + 1;
        let rows = ((max_y - min_y) / self.grid_resolution).ceil() as usize + 1;

        // 2. Populate 2D occupancy grid
        let mut grid = vec![vec![0; cols]; rows];
        for p in &slice_points {
            let c = ((p.x - min_x) / self.grid_resolution) as usize;
            let r = ((p.y - min_y) / self.grid_resolution) as usize;
            if r < rows && c < cols {
                grid[r][c] += 1;
            }
        }

        // 3. Flood-fill segment connected components of Empty cells
        let mut visited = vec![vec![false; cols]; rows];
        let mut rooms = Vec::new();
        let mut room_counter = 1;

        let floor_height = ceil_elev - floor_elev;

        for r in 0..rows {
            for c in 0..cols {
                if grid[r][c] < self.wall_threshold && !visited[r][c] {
                    // Start flood fill
                    let mut component = Vec::new();
                    let mut queue = VecDeque::new();
                    let mut touches_boundary = false;

                    queue.push_back((r, c));
                    visited[r][c] = true;

                    while let Some((curr_r, curr_c)) = queue.pop_front() {
                        component.push((curr_r, curr_c));

                        if curr_r == 0 || curr_r == rows - 1 || curr_c == 0 || curr_c == cols - 1 {
                            touches_boundary = true;
                        }

                        // Check 4-way neighbors
                        let neighbors = [
                            (curr_r.wrapping_sub(1), curr_c),
                            (curr_r + 1, curr_c),
                            (curr_r, curr_c.wrapping_sub(1)),
                            (curr_r, curr_c + 1),
                        ];

                        for &(nr, nc) in &neighbors {
                            if nr < rows
                                && nc < cols
                                && !visited[nr][nc]
                                && grid[nr][nc] < self.wall_threshold
                            {
                                visited[nr][nc] = true;
                                queue.push_back((nr, nc));
                            }
                        }
                    }

                    // If it is not the external background and meets the minimum size, save as a Room
                    if !touches_boundary && component.len() >= self.min_room_cells {
                        let mut r_min_c = usize::MAX;
                        let mut r_max_c = usize::MIN;
                        let mut r_min_r = usize::MAX;
                        let mut r_max_r = usize::MIN;

                        for &(cr, cc) in &component {
                            if cc < r_min_c {
                                r_min_c = cc;
                            }
                            if cc > r_max_c {
                                r_max_c = cc;
                            }
                            if cr < r_min_r {
                                r_min_r = cr;
                            }
                            if cr > r_max_r {
                                r_max_r = cr;
                            }
                        }

                        let room_min_x = min_x + (r_min_c as f64 * self.grid_resolution);
                        let room_max_x = min_x + (r_max_c as f64 * self.grid_resolution);
                        let room_min_y = min_y + (r_min_r as f64 * self.grid_resolution);
                        let room_max_y = min_y + (r_max_r as f64 * self.grid_resolution);

                        let center_x = (room_min_x + room_max_x) / 2.0;
                        let center_y = (room_min_y + room_max_y) / 2.0;
                        let width = room_max_x - room_min_x;
                        let depth = room_max_y - room_min_y;

                        let mut room =
                            Room::new(format!("Room {}", room_counter), RoomType::Office);

                        room.spatial_properties = SpatialProperties {
                            position: Position {
                                x: center_x,
                                y: center_y,
                                z: floor_elev,
                                coordinate_system: "building_local".to_string(),
                            },
                            dimensions: Dimensions {
                                width,
                                height: floor_height,
                                depth,
                            },
                            bounding_box: BoundingBox {
                                min: Position {
                                    x: room_min_x,
                                    y: room_min_y,
                                    z: floor_elev,
                                    coordinate_system: "building_local".to_string(),
                                },
                                max: Position {
                                    x: room_max_x,
                                    y: room_max_y,
                                    z: ceil_elev,
                                    coordinate_system: "building_local".to_string(),
                                },
                            },
                            mesh: None,
                            coordinate_system: "building_local".to_string(),
                        };

                        let room_points_count = slice_points
                            .iter()
                            .filter(|p| {
                                p.x >= room_min_x
                                    && p.x <= room_max_x
                                    && p.y >= room_min_y
                                    && p.y <= room_max_y
                            })
                            .count();

                        room.lidar_enrichment = Some(LidarEnrichment {
                            point_count: room_points_count,
                            confidence_score: 0.90,
                            last_scan_timestamp: Some(chrono::Utc::now()),
                            classification_heuristic: Some(
                                "2D Occupancy Grid Connected Components".to_string(),
                            ),
                        });

                        rooms.push(room);
                        room_counter += 1;
                    }
                }
            }
        }

        rooms
    }
}

pub struct EquipmentDetector {
    voxel_size: f64,
    min_points: usize,
}

impl EquipmentDetector {
    pub fn new(voxel_size: f64, min_points: usize) -> Self {
        Self {
            voxel_size,
            min_points,
        }
    }

    /// Detect equipment clusters inside a given room boundary
    pub fn detect_equipment(
        &self,
        points: &[Point3D],
        room_bbox: &BoundingBox,
        room_path: &str,
    ) -> Vec<Equipment> {
        // 1. Filter points strictly inside the room volume, inset by 0.15m from walls
        let inset = 0.15;
        let r_min_x = room_bbox.min.x + inset;
        let r_max_x = room_bbox.max.x - inset;
        let r_min_y = room_bbox.min.y + inset;
        let r_max_y = room_bbox.max.y - inset;
        let r_min_z = room_bbox.min.z;
        let r_max_z = room_bbox.max.z;

        let room_points: Vec<&Point3D> = points
            .iter()
            .filter(|p| {
                p.x >= r_min_x
                    && p.x <= r_max_x
                    && p.y >= r_min_y
                    && p.y <= r_max_y
                    && p.z >= r_min_z
                    && p.z <= r_max_z
            })
            .collect();

        if room_points.is_empty() {
            return Vec::new();
        }

        // 2. Voxel Binning
        let mut voxel_map: HashMap<(i32, i32, i32), Vec<Point3D>> = HashMap::new();
        for p in &room_points {
            let gx = (p.x / self.voxel_size).floor() as i32;
            let gy = (p.y / self.voxel_size).floor() as i32;
            let gz = (p.z / self.voxel_size).floor() as i32;
            voxel_map.entry((gx, gy, gz)).or_default().push(**p);
        }

        // 3. Flood-fill Connected Components on occupied voxels (Chebyshev 26-connectivity)
        let mut visited = std::collections::HashSet::new();
        let mut clusters = Vec::new();

        let voxels: Vec<(i32, i32, i32)> = voxel_map.keys().cloned().collect();

        for voxel in &voxels {
            if visited.contains(voxel) {
                continue;
            }

            // Start BFS
            let mut component_points = Vec::new();
            let mut queue = VecDeque::new();
            queue.push_back(*voxel);
            visited.insert(*voxel);

            while let Some(curr) = queue.pop_front() {
                if let Some(pts) = voxel_map.get(&curr) {
                    component_points.extend(pts.clone());
                }

                // Check 26 neighbors
                for dx in -1..=1 {
                    for dy in -1..=1 {
                        for dz in -1..=1 {
                            if dx == 0 && dy == 0 && dz == 0 {
                                continue;
                            }
                            let neighbor = (curr.0 + dx, curr.1 + dy, curr.2 + dz);
                            if voxel_map.contains_key(&neighbor) && !visited.contains(&neighbor) {
                                visited.insert(neighbor);
                                queue.push_back(neighbor);
                            }
                        }
                    }
                }
            }

            if component_points.len() >= self.min_points {
                clusters.push(component_points);
            }
        }

        // 4. Classify each cluster and instantiate Equipment
        let mut equipment_list = Vec::new();

        for (eq_counter, cluster) in (1..).zip(clusters) {
            let mut min_x = f64::MAX;
            let mut max_x = f64::MIN;
            let mut min_y = f64::MAX;
            let mut max_y = f64::MIN;
            let mut min_z = f64::MAX;
            let mut max_z = f64::MIN;

            for p in &cluster {
                if p.x < min_x {
                    min_x = p.x;
                }
                if p.x > max_x {
                    max_x = p.x;
                }
                if p.y < min_y {
                    min_y = p.y;
                }
                if p.y > max_y {
                    max_y = p.y;
                }
                if p.z < min_z {
                    min_z = p.z;
                }
                if p.z > max_z {
                    max_z = p.z;
                }
            }

            let width = max_x - min_x;
            let depth = max_y - min_y;
            let height = max_z - min_z;
            let volume = width * depth * height;
            let center_x = (min_x + max_x) / 2.0;
            let center_y = (min_y + max_y) / 2.0;
            let center_z = (min_z + max_z) / 2.0;

            // Classify equipment type using rules
            let eq_type = if height > 1.4 && volume < 0.8 {
                EquipmentType::Electrical
            } else if volume > 0.4 && (0.6..=1.8).contains(&height) {
                EquipmentType::HVAC
            } else if height < 0.5 && volume < 0.2 {
                EquipmentType::Plumbing
            } else {
                EquipmentType::Furniture
            };

            let type_str = match &eq_type {
                EquipmentType::Electrical => "Electrical",
                EquipmentType::HVAC => "HVAC",
                EquipmentType::Plumbing => "Plumbing",
                _ => "Furniture",
            };

            let name = format!("{} Item {}", type_str, eq_counter);
            let path = format!("{}/{}", room_path, name.to_lowercase().replace(" ", "-"));

            let mut equipment = Equipment::new(name, path, eq_type);
            equipment.position = Position {
                x: center_x,
                y: center_y,
                z: center_z,
                coordinate_system: "building_local".to_string(),
            };

            // Save estimated dimensions as properties
            equipment
                .properties
                .insert("width".to_string(), width.to_string());
            equipment
                .properties
                .insert("depth".to_string(), depth.to_string());
            equipment
                .properties
                .insert("height".to_string(), height.to_string());
            equipment
                .properties
                .insert("volume".to_string(), volume.to_string());
            equipment
                .properties
                .insert("point_count".to_string(), cluster.len().to_string());

            let confidence_score = match &equipment.equipment_type {
                EquipmentType::Furniture => 0.75, // Default fallback
                _ => 0.90,                        // Rule-based match
            };

            equipment.lidar_enrichment = Some(LidarEnrichment {
                point_count: cluster.len(),
                confidence_score,
                last_scan_timestamp: Some(chrono::Utc::now()),
                classification_heuristic: Some(format!(
                    "Rule-based geometric filter (height: {:.2}, vol: {:.3})",
                    height, volume
                )),
            });

            equipment_list.push(equipment);
        }

        equipment_list
    }
}
