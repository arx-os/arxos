//! Simple PLY File Parser for ArxOS
//! 
//! Minimal dependency PLY parser that converts 3D point cloud data
//! directly to ArxObjects

use std::io::{BufRead, BufReader};
use std::fs::File;
use crate::arxobject::ArxObject;
use crate::point_cloud_simple::SimplePointCloudProcessor;

/// Simple PLY point
#[derive(Debug, Clone, Copy)]
pub struct PlyPoint {
    pub x: f32,
    pub y: f32,
    pub z: f32,
}

/// PLY file header info
#[derive(Debug)]
struct PlyHeader {
    vertex_count: usize,
    has_colors: bool,
    has_normals: bool,
}

/// Simple PLY parser
pub struct SimplePlyParser {
    processor: SimplePointCloudProcessor,
}

impl SimplePlyParser {
    /// Create new PLY parser
    pub fn new() -> Self {
        Self {
            processor: SimplePointCloudProcessor::new(),
        }
    }
    
    /// Parse PLY file and convert to ArxObjects
    pub fn parse_to_arxobjects(&self, file_path: &str, building_id: u16) -> Result<Vec<ArxObject>, String> {
        let points = self.parse_ply_file(file_path)?;
        
        // Convert to our PointCloud format
        let cloud = self.points_to_cloud(points);
        
        // Process into ArxObjects
        Ok(self.processor.process(&cloud, building_id))
    }
    
    /// Parse PLY file into points
    pub fn parse_ply_file(&self, file_path: &str) -> Result<Vec<PlyPoint>, String> {
        let file = File::open(file_path)
            .map_err(|e| format!("Failed to open PLY file: {}", e))?;
        
        let mut reader = BufReader::new(file);
        
        // Parse header
        let header = self.parse_header(&mut reader)?;
        
        // Parse vertices
        self.parse_vertices(&mut reader, header.vertex_count)
    }
    
    /// Parse PLY header
    fn parse_header<R: BufRead>(&self, reader: &mut R) -> Result<PlyHeader, String> {
        let mut line = String::new();
        let mut vertex_count = 0;
        let mut has_colors = false;
        let mut has_normals = false;
        
        // Read magic number
        reader.read_line(&mut line)
            .map_err(|e| format!("Failed to read PLY header: {}", e))?;
        
        if !line.trim().eq_ignore_ascii_case("ply") {
            return Err("Not a PLY file".to_string());
        }
        
        line.clear();
        
        // Parse header lines
        loop {
            reader.read_line(&mut line)
                .map_err(|e| format!("Failed to read header line: {}", e))?;
            
            let trimmed = line.trim();
            
            if trimmed == "end_header" {
                break;
            }
            
            // Parse vertex count
            if trimmed.starts_with("element vertex") {
                let parts: Vec<&str> = trimmed.split_whitespace().collect();
                if parts.len() >= 3 {
                    vertex_count = parts[2].parse()
                        .map_err(|_| "Invalid vertex count".to_string())?;
                }
            }
            
            // Check for colors
            if trimmed.contains("property uchar red") || trimmed.contains("property float red") {
                has_colors = true;
            }
            
            // Check for normals
            if trimmed.contains("property float nx") {
                has_normals = true;
            }
            
            line.clear();
        }
        
        if vertex_count == 0 {
            return Err("No vertices found in PLY file".to_string());
        }
        
        Ok(PlyHeader {
            vertex_count,
            has_colors,
            has_normals,
        })
    }
    
    /// Parse vertices from PLY file
    fn parse_vertices<R: BufRead>(&self, reader: &mut R, count: usize) -> Result<Vec<PlyPoint>, String> {
        let mut points = Vec::with_capacity(count);
        let mut line = String::new();
        
        for i in 0..count {
            line.clear();
            reader.read_line(&mut line)
                .map_err(|e| format!("Failed to read vertex {}: {}", i, e))?;
            
            let parts: Vec<&str> = line.trim().split_whitespace().collect();
            
            if parts.len() < 3 {
                return Err(format!("Invalid vertex data at line {}", i));
            }
            
            let x = parts[0].parse::<f32>()
                .map_err(|_| format!("Invalid X coordinate at vertex {}", i))?;
            let y = parts[1].parse::<f32>()
                .map_err(|_| format!("Invalid Y coordinate at vertex {}", i))?;
            let z = parts[2].parse::<f32>()
                .map_err(|_| format!("Invalid Z coordinate at vertex {}", i))?;
            
            points.push(PlyPoint { x, y, z });
        }
        
        Ok(points)
    }
    
    /// Convert PLY points to our PointCloud format
    fn points_to_cloud(&self, ply_points: Vec<PlyPoint>) -> crate::point_cloud_parser::PointCloud {
        use crate::document_parser::{Point3D, BoundingBox};
        use crate::point_cloud_parser::PointCloud;
        
        if ply_points.is_empty() {
            return PointCloud {
                points: vec![],
                colors: vec![],
                normals: vec![],
                bounds: BoundingBox {
                    min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                    max: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                },
            };
        }
        
        // Calculate bounds
        let mut min_x = ply_points[0].x;
        let mut min_y = ply_points[0].y;
        let mut min_z = ply_points[0].z;
        let mut max_x = ply_points[0].x;
        let mut max_y = ply_points[0].y;
        let mut max_z = ply_points[0].z;
        
        let points: Vec<Point3D> = ply_points.iter().map(|p| {
            min_x = min_x.min(p.x);
            min_y = min_y.min(p.y);
            min_z = min_z.min(p.z);
            max_x = max_x.max(p.x);
            max_y = max_y.max(p.y);
            max_z = max_z.max(p.z);
            
            Point3D { x: p.x, y: p.y, z: p.z }
        }).collect();
        
        PointCloud {
            points,
            colors: vec![],
            normals: vec![],
            bounds: BoundingBox {
                min: Point3D { x: min_x, y: min_y, z: min_z },
                max: Point3D { x: max_x, y: max_y, z: max_z },
            },
        }
    }
    
    /// Get statistics about a PLY file
    pub fn get_file_stats(&self, file_path: &str) -> Result<PlyStats, String> {
        let points = self.parse_ply_file(file_path)?;
        
        if points.is_empty() {
            return Ok(PlyStats::default());
        }
        
        let mut min_x = points[0].x;
        let mut min_y = points[0].y;
        let mut min_z = points[0].z;
        let mut max_x = points[0].x;
        let mut max_y = points[0].y;
        let mut max_z = points[0].z;
        
        for p in &points {
            min_x = min_x.min(p.x);
            min_y = min_y.min(p.y);
            min_z = min_z.min(p.z);
            max_x = max_x.max(p.x);
            max_y = max_y.max(p.y);
            max_z = max_z.max(p.z);
        }
        
        Ok(PlyStats {
            point_count: points.len(),
            bounds: (
                (min_x, min_y, min_z),
                (max_x, max_y, max_z),
            ),
            size_bytes: points.len() * std::mem::size_of::<PlyPoint>(),
        })
    }
}

/// PLY file statistics
#[derive(Debug, Default)]
pub struct PlyStats {
    pub point_count: usize,
    pub bounds: ((f32, f32, f32), (f32, f32, f32)),
    pub size_bytes: usize,
}

impl PlyStats {
    /// Get compression ratio when converted to ArxObjects
    pub fn compression_ratio(&self, arxobject_count: usize) -> f32 {
        if arxobject_count == 0 {
            return 0.0;
        }
        
        let arxobject_size = arxobject_count * 13; // 13 bytes per ArxObject
        self.size_bytes as f32 / arxobject_size as f32
    }
}