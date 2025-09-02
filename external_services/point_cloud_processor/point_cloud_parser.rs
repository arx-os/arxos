//! Point Cloud Parser for LiDAR Data
//! 
//! Converts PLY/OBJ point clouds to ArxObjects and ASCII

use crate::arxobject::ArxObject;
use crate::document_parser::{BuildingPlan, FloorPlan, Room, Equipment, Point3D, BoundingBox};
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum PointCloudError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Parse error: {0}")]
    Parse(String),
    
    #[error("Unsupported format: {0}")]
    UnsupportedFormat(String),
}

/// Point cloud data structure
#[derive(Debug, Clone)]
pub struct PointCloud {
    pub points: Vec<Point3D>,
    pub colors: Vec<(u8, u8, u8)>,
    pub normals: Vec<Point3D>,
    pub bounds: BoundingBox,
}

/// Detected plane in point cloud
#[derive(Debug, Clone)]
pub struct Plane {
    pub normal: Point3D,
    pub distance: f32,
    pub points: Vec<usize>,
    pub plane_type: PlaneType,
}

#[derive(Debug, Clone, PartialEq)]
pub enum PlaneType {
    Floor,
    Ceiling,
    Wall,
    Unknown,
}

/// Point cloud parser and analyzer
pub struct PointCloudParser {
    /// Voxel size for spatial hashing (meters)
    voxel_size: f32,
    
    /// Minimum points to consider a plane
    min_plane_points: usize,
    
    /// Distance threshold for plane fitting
    plane_threshold: f32,
}

impl PointCloudParser {
    pub fn new() -> Self {
        Self {
            voxel_size: 0.05,  // 5cm voxels
            min_plane_points: 100,
            plane_threshold: 0.02,  // 2cm tolerance
        }
    }
    
    /// Parse PLY file format
    pub fn parse_ply(&self, file_path: &str) -> Result<PointCloud, PointCloudError> {
        let file = File::open(file_path)?;
        let reader = BufReader::new(file);
        let mut lines = reader.lines();
        
        // Parse PLY header
        let mut vertex_count = 0;
        let mut has_color = false;
        let mut has_normal = false;
        
        while let Some(line) = lines.next() {
            let line = line?;
            
            if line == "end_header" {
                break;
            }
            
            if line.starts_with("element vertex") {
                vertex_count = line.split_whitespace()
                    .nth(2)
                    .and_then(|s| s.parse().ok())
                    .ok_or_else(|| PointCloudError::Parse("Invalid vertex count".to_string()))?;
            }
            
            if line.contains("property uchar red") {
                has_color = true;
            }
            
            if line.contains("property float nx") || line.contains("property double nx") {
                has_normal = true;
            }
        }
        
        // Parse vertices
        let mut points = Vec::with_capacity(vertex_count);
        let mut colors = Vec::with_capacity(vertex_count);
        let mut normals = Vec::with_capacity(vertex_count);
        
        let mut min = Point3D { x: f32::MAX, y: f32::MAX, z: f32::MAX };
        let mut max = Point3D { x: f32::MIN, y: f32::MIN, z: f32::MIN };
        
        for _ in 0..vertex_count {
            if let Some(line) = lines.next() {
                let line = line?;
                let parts: Vec<&str> = line.split_whitespace().collect();
                
                if parts.len() < 3 {
                    continue;
                }
                
                // Parse point - iPhone uses Y-up coordinate system
                let x_coord: f32 = parts[0].parse().map_err(|_| PointCloudError::Parse("Invalid X".to_string()))?;
                let y_coord: f32 = parts[1].parse().map_err(|_| PointCloudError::Parse("Invalid Y".to_string()))?;
                let z_coord: f32 = parts[2].parse().map_err(|_| PointCloudError::Parse("Invalid Z".to_string()))?;
                
                // Transform from Y-up (iPhone/ARKit) to Z-up (building standard)
                let point = Point3D {
                    x: x_coord,      // X stays the same
                    y: -z_coord,     // iPhone Z becomes negative Y (flip for correct orientation)
                    z: y_coord,      // iPhone Y becomes Z (up)
                };
                
                // Update bounds
                min.x = min.x.min(point.x);
                min.y = min.y.min(point.y);
                min.z = min.z.min(point.z);
                max.x = max.x.max(point.x);
                max.y = max.y.max(point.y);
                max.z = max.z.max(point.z);
                
                points.push(point);
                
                // Parse color if present
                if has_color && parts.len() >= 6 {
                    colors.push((
                        parts[3].parse().unwrap_or(255),
                        parts[4].parse().unwrap_or(255),
                        parts[5].parse().unwrap_or(255),
                    ));
                } else {
                    colors.push((255, 255, 255));
                }
                
                // Parse normal if present (may have curvature after)
                let normal_offset = if has_color { 6 } else { 3 };
                if has_normal && parts.len() > normal_offset + 2 {
                    normals.push(Point3D {
                        x: parts[normal_offset].parse().unwrap_or(0.0),
                        y: parts[normal_offset + 1].parse().unwrap_or(0.0),
                        z: parts[normal_offset + 2].parse().unwrap_or(1.0),
                    });
                } else {
                    normals.push(Point3D { x: 0.0, y: 0.0, z: 1.0 });
                }
            }
        }
        
        Ok(PointCloud {
            points,
            colors,
            normals,
            bounds: BoundingBox { min, max },
        })
    }
    
    /// Detect planes using RANSAC
    pub fn detect_planes(&self, cloud: &PointCloud) -> Vec<Plane> {
        let mut planes = Vec::new();
        let mut remaining_points: Vec<usize> = (0..cloud.points.len()).collect();
        
        // Detect floor (lowest horizontal plane)
        if let Some(floor) = self.detect_horizontal_plane(&cloud, &remaining_points, true) {
            remaining_points.retain(|i| !floor.points.contains(i));
            planes.push(floor);
        }
        
        // Detect ceiling (highest horizontal plane)
        if let Some(ceiling) = self.detect_horizontal_plane(&cloud, &remaining_points, false) {
            remaining_points.retain(|i| !ceiling.points.contains(i));
            planes.push(ceiling);
        }
        
        // Detect walls (vertical planes)
        for _ in 0..10 {  // Try to find up to 10 walls
            if let Some(wall) = self.detect_vertical_plane(&cloud, &remaining_points) {
                remaining_points.retain(|i| !wall.points.contains(i));
                planes.push(wall);
            } else {
                break;
            }
        }
        
        planes
    }
    
    /// Detect horizontal plane (floor or ceiling)
    fn detect_horizontal_plane(&self, cloud: &PointCloud, indices: &[usize], is_floor: bool) -> Option<Plane> {
        if indices.len() < self.min_plane_points {
            return None;
        }
        
        // Find points near the expected height
        let mut z_values: Vec<f32> = indices.iter()
            .map(|&i| cloud.points[i].z)
            .collect();
        z_values.sort_by(|a, b| a.partial_cmp(b).unwrap());
        
        let target_z = if is_floor {
            z_values[z_values.len() / 10]  // 10th percentile for floor
        } else {
            z_values[z_values.len() * 9 / 10]  // 90th percentile for ceiling
        };
        
        // Collect points near target height
        let plane_points: Vec<usize> = indices.iter()
            .filter(|&&i| (cloud.points[i].z - target_z).abs() < self.plane_threshold)
            .copied()
            .collect();
        
        if plane_points.len() < self.min_plane_points {
            return None;
        }
        
        Some(Plane {
            normal: Point3D { x: 0.0, y: 0.0, z: 1.0 },
            distance: target_z,
            points: plane_points,
            plane_type: if is_floor { PlaneType::Floor } else { PlaneType::Ceiling },
        })
    }
    
    /// Detect vertical plane (wall)
    fn detect_vertical_plane(&self, cloud: &PointCloud, indices: &[usize]) -> Option<Plane> {
        if indices.len() < self.min_plane_points {
            return None;
        }
        
        // RANSAC for vertical plane detection
        let mut best_plane = None;
        let mut best_inliers = 0;
        
        // Simple deterministic sampling instead of random for now
        let step = indices.len().max(1) / 100;
        for i in 0..100.min(indices.len() / 2) {  // RANSAC iterations
            // Sample points deterministically
            let idx1 = indices[(i * step) % indices.len()];
            let idx2 = indices[((i * step) + step/2) % indices.len()];
            
            let p1 = &cloud.points[idx1];
            let p2 = &cloud.points[idx2];
            
            // Skip if points are too close
            let dx = p2.x - p1.x;
            let dy = p2.y - p1.y;
            if (dx * dx + dy * dy).sqrt() < 0.5 {
                continue;
            }
            
            // Calculate plane normal (vertical, so z component is 0)
            let normal = Point3D {
                x: -dy,
                y: dx,
                z: 0.0,
            };
            let norm = (normal.x * normal.x + normal.y * normal.y).sqrt();
            let normal = Point3D {
                x: normal.x / norm,
                y: normal.y / norm,
                z: 0.0,
            };
            
            // Calculate distance
            let distance = normal.x * p1.x + normal.y * p1.y;
            
            // Count inliers
            let inliers: Vec<usize> = indices.iter()
                .filter(|&&i| {
                    let p = &cloud.points[i];
                    let dist = (normal.x * p.x + normal.y * p.y - distance).abs();
                    dist < self.plane_threshold
                })
                .copied()
                .collect();
            
            if inliers.len() > best_inliers {
                best_inliers = inliers.len();
                best_plane = Some(Plane {
                    normal,
                    distance,
                    points: inliers,
                    plane_type: PlaneType::Wall,
                });
            }
        }
        
        best_plane.filter(|p| p.points.len() >= self.min_plane_points)
    }
    
    /// Convert point cloud to building plan
    pub fn to_building_plan(&self, cloud: &PointCloud, building_name: &str) -> BuildingPlan {
        let planes = self.detect_planes(cloud);
        
        // Group planes by floor
        let floor_planes: Vec<&Plane> = planes.iter()
            .filter(|p| p.plane_type == PlaneType::Floor)
            .collect();
        
        let mut floors = Vec::new();
        
        for (i, floor_plane) in floor_planes.iter().enumerate() {
            let floor_z = floor_plane.distance;
            
            // Find walls for this floor
            let floor_walls: Vec<&Plane> = planes.iter()
                .filter(|p| p.plane_type == PlaneType::Wall)
                .filter(|p| {
                    // Check if wall intersects with floor height
                    p.points.iter().any(|&idx| {
                        (cloud.points[idx].z - floor_z).abs() < 1.0
                    })
                })
                .collect();
            
            // Create room from walls
            let room = self.create_room_from_walls(cloud, floor_walls, i);
            
            // Detect equipment (simplified - look for clusters)
            let equipment = self.detect_equipment(cloud, floor_z);
            
            floors.push(FloorPlan {
                floor_number: i as i8,
                rooms: vec![room],
                ascii_layout: String::new(),  // Will be generated by renderer
                equipment,
            });
        }
        
        BuildingPlan {
            name: building_name.to_string(),
            floors,
            arxobjects: Vec::new(),
            metadata: super::document_parser::BuildingMetadata {
                address: None,
                total_sqft: self.calculate_area(&cloud.bounds),
                year_built: None,
                building_type: Some("Scanned".to_string()),
                occupancy_class: None,
            },
        }
    }
    
    /// Create room from detected walls
    fn create_room_from_walls(&self, cloud: &PointCloud, walls: Vec<&Plane>, floor_num: usize) -> Room {
        // Calculate room bounds from wall intersections
        let mut min_x = f32::MAX;
        let mut max_x = f32::MIN;
        let mut min_y = f32::MAX;
        let mut max_y = f32::MIN;
        
        for wall in &walls {
            for &idx in &wall.points {
                let p = &cloud.points[idx];
                min_x = min_x.min(p.x);
                max_x = max_x.max(p.x);
                min_y = min_y.min(p.y);
                max_y = max_y.max(p.y);
            }
        }
        
        Room {
            number: format!("S{:03}", floor_num * 100 + 1),  // S for Scanned
            name: "Scanned Room".to_string(),
            area_sqft: ((max_x - min_x) * (max_y - min_y) * 10.764).abs(),  // m² to sq ft
            bounds: BoundingBox {
                min: Point3D { x: min_x, y: min_y, z: 0.0 },
                max: Point3D { x: max_x, y: max_y, z: 3.0 },
            },
            equipment_count: 0,
        }
    }
    
    /// Detect equipment using clustering
    fn detect_equipment(&self, cloud: &PointCloud, floor_z: f32) -> Vec<Equipment> {
        use super::document_parser::EquipmentType;
        let mut equipment = Vec::new();
        
        // Find points at outlet height (0.3m above floor)
        let outlet_points: Vec<usize> = (0..cloud.points.len())
            .filter(|&i| {
                let z_diff = cloud.points[i].z - floor_z;
                z_diff > 0.2 && z_diff < 0.5
            })
            .collect();
        
        // Cluster nearby points as outlets
        let clusters = self.cluster_points(cloud, &outlet_points, 0.2);
        
        for cluster in clusters {
            if cluster.len() > 10 {  // Minimum points for equipment
                let center = self.cluster_center(cloud, &cluster);
                equipment.push(Equipment {
                    equipment_type: EquipmentType::ElectricalOutlet,
                    location: center,
                    room_number: None,
                    properties: HashMap::new(),
                });
            }
        }
        
        // Find points at ceiling height (lights)
        let ceiling_points: Vec<usize> = (0..cloud.points.len())
            .filter(|&i| {
                let z_diff = cloud.points[i].z - floor_z;
                z_diff > 2.5 && z_diff < 3.5
            })
            .collect();
        
        let clusters = self.cluster_points(cloud, &ceiling_points, 0.3);
        
        for cluster in clusters {
            if cluster.len() > 20 {
                let center = self.cluster_center(cloud, &cluster);
                equipment.push(Equipment {
                    equipment_type: EquipmentType::LightFixture,
                    location: center,
                    room_number: None,
                    properties: HashMap::new(),
                });
            }
        }
        
        equipment
    }
    
    /// Cluster nearby points
    fn cluster_points(&self, cloud: &PointCloud, indices: &[usize], radius: f32) -> Vec<Vec<usize>> {
        let mut clusters = Vec::new();
        let mut visited = vec![false; indices.len()];
        
        for (i, &idx) in indices.iter().enumerate() {
            if visited[i] {
                continue;
            }
            
            let mut cluster = vec![idx];
            visited[i] = true;
            
            let p1 = &cloud.points[idx];
            
            for (j, &jdx) in indices.iter().enumerate() {
                if visited[j] {
                    continue;
                }
                
                let p2 = &cloud.points[jdx];
                let dist = ((p2.x - p1.x).powi(2) + (p2.y - p1.y).powi(2) + (p2.z - p1.z).powi(2)).sqrt();
                
                if dist < radius {
                    cluster.push(jdx);
                    visited[j] = true;
                }
            }
            
            clusters.push(cluster);
        }
        
        clusters
    }
    
    /// Calculate cluster center
    fn cluster_center(&self, cloud: &PointCloud, cluster: &[usize]) -> Point3D {
        let mut sum = Point3D { x: 0.0, y: 0.0, z: 0.0 };
        
        for &idx in cluster {
            let p = &cloud.points[idx];
            sum.x += p.x;
            sum.y += p.y;
            sum.z += p.z;
        }
        
        let count = cluster.len() as f32;
        Point3D {
            x: sum.x / count,
            y: sum.y / count,
            z: sum.z / count,
        }
    }
    
    /// Calculate area from bounding box
    fn calculate_area(&self, bounds: &BoundingBox) -> f32 {
        let width = (bounds.max.x - bounds.min.x).abs();
        let depth = (bounds.max.y - bounds.min.y).abs();
        width * depth * 10.764  // m² to sq ft
    }
    
    /// Compress point cloud to ArxObjects
    pub fn to_arxobjects(&self, cloud: &PointCloud, building_id: u16) -> Vec<ArxObject> {
        let mut objects = Vec::new();
        
        // Voxelize the point cloud
        let voxels = self.voxelize(cloud);
        
        // Each voxel becomes an ArxObject
        for (_key, indices) in voxels {
            if indices.len() < 5 {
                continue;  // Skip sparse voxels
            }
            
            // Calculate voxel center
            let center = self.cluster_center(cloud, &indices);
            
            // Determine object type based on height and density
            let object_type = if center.z < 0.5 {
                0x30  // Floor (using FLOOR constant)
            } else if center.z > 2.5 {
                0x31  // Ceiling (using CEILING constant)
            } else if indices.len() > 50 {
                0x32  // Wall (using WALL constant)
            } else {
                0x33  // Furniture/Equipment
            };
            
            objects.push(ArxObject::new(
                building_id,
                object_type,
                (center.x * 1000.0).max(0.0).min(65535.0) as u16,
                (center.y * 1000.0).max(0.0).min(65535.0) as u16,
                (center.z * 1000.0).max(0.0).min(65535.0) as u16,
            ));
        }
        
        objects
    }
    
    /// Voxelize point cloud for compression
    fn voxelize(&self, cloud: &PointCloud) -> HashMap<(i32, i32, i32), Vec<usize>> {
        let mut voxels = HashMap::new();
        
        for (i, point) in cloud.points.iter().enumerate() {
            let voxel_x = (point.x / self.voxel_size) as i32;
            let voxel_y = (point.y / self.voxel_size) as i32;
            let voxel_z = (point.z / self.voxel_size) as i32;
            
            voxels.entry((voxel_x, voxel_y, voxel_z))
                .or_insert_with(Vec::new)
                .push(i);
        }
        
        voxels
    }
}