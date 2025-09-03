//! PLY File Parser for ArxOS
//! 
//! Production-ready PLY (Polygon File Format) parser for processing
//! LiDAR scans into ArxOS's internal representation.

use std::fs::File;
use std::io::{BufRead, BufReader, Read};
use std::path::Path;
use crate::error::{ArxError, Result};

/// 3D Point from PLY file
#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct Point3D {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub r: Option<u8>,
    pub g: Option<u8>,
    pub b: Option<u8>,
    pub nx: Option<f32>,
    pub ny: Option<f32>,
    pub nz: Option<f32>,
}

impl Point3D {
    /// Create a point with just coordinates
    pub fn new(x: f32, y: f32, z: f32) -> Self {
        Self {
            x, y, z,
            r: None, g: None, b: None,
            nx: None, ny: None, nz: None,
        }
    }
    
    /// Create with color
    pub fn with_color(x: f32, y: f32, z: f32, r: u8, g: u8, b: u8) -> Self {
        Self {
            x, y, z,
            r: Some(r), g: Some(g), b: Some(b),
            nx: None, ny: None, nz: None,
        }
    }
    
    /// Distance from origin
    pub fn magnitude(&self) -> f32 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }
    
    /// Distance to another point
    pub fn distance_to(&self, other: &Point3D) -> f32 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        let dz = self.z - other.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
}

/// PLY file format specification
#[derive(Debug, Clone, PartialEq)]
pub enum PlyFormat {
    Ascii,
    BinaryLittleEndian,
    BinaryBigEndian,
}

/// PLY property type
#[derive(Debug, Clone, PartialEq)]
pub enum PropertyType {
    Char,
    UChar,
    Short,
    UShort,
    Int,
    UInt,
    Float,
    Double,
}

impl PropertyType {
    fn from_str(s: &str) -> Option<Self> {
        match s {
            "char" | "int8" => Some(PropertyType::Char),
            "uchar" | "uint8" => Some(PropertyType::UChar),
            "short" | "int16" => Some(PropertyType::Short),
            "ushort" | "uint16" => Some(PropertyType::UShort),
            "int" | "int32" => Some(PropertyType::Int),
            "uint" | "uint32" => Some(PropertyType::UInt),
            "float" | "float32" => Some(PropertyType::Float),
            "double" | "float64" => Some(PropertyType::Double),
            _ => None,
        }
    }
}

/// PLY element property
#[derive(Debug, Clone)]
pub struct Property {
    pub name: String,
    pub data_type: PropertyType,
}

/// PLY element (vertex, face, etc.)
#[derive(Debug, Clone)]
pub struct Element {
    pub name: String,
    pub count: usize,
    pub properties: Vec<Property>,
}

/// PLY file header
#[derive(Debug)]
pub struct PlyHeader {
    pub format: PlyFormat,
    pub elements: Vec<Element>,
    pub comments: Vec<String>,
}

/// PLY file parser
pub struct PlyParser {
    header: Option<PlyHeader>,
    points: Vec<Point3D>,
}

impl PlyParser {
    /// Create a new PLY parser
    pub fn new() -> Self {
        Self {
            header: None,
            points: Vec::new(),
        }
    }
    
    /// Parse a PLY file from path
    pub fn parse_file<P: AsRef<Path>>(&mut self, path: P) -> Result<()> {
        let file = File::open(path.as_ref())?;
        
        let mut reader = BufReader::new(file);
        
        // Parse header
        self.header = Some(self.parse_header(&mut reader)?);
        
        // Parse data based on format
        match &self.header.as_ref().unwrap().format {
            PlyFormat::Ascii => self.parse_ascii_data(&mut reader)?,
            PlyFormat::BinaryLittleEndian => self.parse_binary_data(&mut reader, true)?,
            PlyFormat::BinaryBigEndian => self.parse_binary_data(&mut reader, false)?,
        }
        
        Ok(())
    }
    
    /// Parse PLY header
    fn parse_header<R: BufRead>(&self, reader: &mut R) -> Result<PlyHeader> {
        let mut format = None;
        let mut elements = Vec::new();
        let mut comments = Vec::new();
        let mut current_element = None;
        
        for line in reader.lines() {
            let line = line.map_err(|e| ArxError::Internal(e.to_string()))?;
            let line = line.trim();
            
            if line == "end_header" {
                break;
            }
            
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.is_empty() {
                continue;
            }
            
            match parts[0] {
                "ply" => {
                    if line != "ply" {
                        return Err(ArxError::ParseError("Invalid PLY file header".into()));
                    }
                }
                "format" => {
                    if parts.len() != 3 {
                        return Err(ArxError::ParseError("Invalid format specification".into()));
                    }
                    format = Some(match parts[1] {
                        "ascii" => PlyFormat::Ascii,
                        "binary_little_endian" => PlyFormat::BinaryLittleEndian,
                        "binary_big_endian" => PlyFormat::BinaryBigEndian,
                        _ => return Err(ArxError::ParseError(format!("Unknown format: {}", parts[1]))),
                    });
                }
                "comment" => {
                    comments.push(line[7..].trim().to_string());
                }
                "element" => {
                    if parts.len() != 3 {
                        return Err(ArxError::ParseError("Invalid element specification".into()));
                    }
                    
                    // Save previous element if exists
                    if let Some(elem) = current_element.take() {
                        elements.push(elem);
                    }
                    
                    let count = parts[2].parse::<usize>()
                        .map_err(|_| ArxError::ParseError(format!("Invalid element count: {}", parts[2])))?;
                    
                    current_element = Some(Element {
                        name: parts[1].to_string(),
                        count,
                        properties: Vec::new(),
                    });
                }
                "property" => {
                    if parts.len() < 3 {
                        return Err(ArxError::ParseError("Invalid property specification".into()));
                    }
                    
                    let data_type = PropertyType::from_str(parts[1])
                        .ok_or_else(|| ArxError::ParseError(format!("Unknown property type: {}", parts[1])))?;
                    
                    let name = parts[2].to_string();
                    
                    if let Some(ref mut elem) = current_element {
                        elem.properties.push(Property { name, data_type });
                    } else {
                        return Err(ArxError::ParseError("Property without element".into()));
                    }
                }
                _ => {
                    // Ignore unknown header lines
                }
            }
        }
        
        // Save last element
        if let Some(elem) = current_element {
            elements.push(elem);
        }
        
        let format = format.ok_or_else(|| ArxError::ParseError("No format specified".into()))?;
        
        Ok(PlyHeader {
            format,
            elements,
            comments,
        })
    }
    
    /// Parse ASCII format data
    fn parse_ascii_data<R: BufRead>(&mut self, reader: &mut R) -> Result<()> {
        let header = self.header.as_ref().unwrap();
        
        // Find vertex element
        let vertex_elem = header.elements.iter()
            .find(|e| e.name == "vertex")
            .ok_or_else(|| ArxError::ParseError("No vertex element found".into()))?;
        
        // Find property indices
        let x_idx = vertex_elem.properties.iter().position(|p| p.name == "x");
        let y_idx = vertex_elem.properties.iter().position(|p| p.name == "y");
        let z_idx = vertex_elem.properties.iter().position(|p| p.name == "z");
        
        if x_idx.is_none() || y_idx.is_none() || z_idx.is_none() {
            return Err(ArxError::ParseError("Missing x, y, or z coordinates".into()));
        }
        
        let x_idx = x_idx.unwrap();
        let y_idx = y_idx.unwrap();
        let z_idx = z_idx.unwrap();
        
        // Optional properties
        let r_idx = vertex_elem.properties.iter().position(|p| p.name == "red");
        let g_idx = vertex_elem.properties.iter().position(|p| p.name == "green");
        let b_idx = vertex_elem.properties.iter().position(|p| p.name == "blue");
        
        // Reserve capacity
        self.points.reserve(vertex_elem.count);
        
        // Parse vertices
        for _ in 0..vertex_elem.count {
            let line = reader.lines().next()
                .ok_or_else(|| ArxError::ParseError("Unexpected end of file".into()))?
                .map_err(|e| ArxError::Internal(e.to_string()))?;
            
            let parts: Vec<&str> = line.trim().split_whitespace().collect();
            
            if parts.len() < vertex_elem.properties.len() {
                return Err(ArxError::ParseError(format!(
                    "Expected {} properties, got {}", 
                    vertex_elem.properties.len(), 
                    parts.len()
                )));
            }
            
            let x = parts[x_idx].parse::<f32>()
                .map_err(|_| ArxError::ParseError("Invalid x coordinate".into()))?;
            let y = parts[y_idx].parse::<f32>()
                .map_err(|_| ArxError::ParseError("Invalid y coordinate".into()))?;
            let z = parts[z_idx].parse::<f32>()
                .map_err(|_| ArxError::ParseError("Invalid z coordinate".into()))?;
            
            let mut point = Point3D::new(x, y, z);
            
            // Parse color if present
            if let (Some(r_idx), Some(g_idx), Some(b_idx)) = (r_idx, g_idx, b_idx) {
                point.r = parts[r_idx].parse::<u8>().ok();
                point.g = parts[g_idx].parse::<u8>().ok();
                point.b = parts[b_idx].parse::<u8>().ok();
            }
            
            self.points.push(point);
        }
        
        Ok(())
    }
    
    /// Parse binary format data
    fn parse_binary_data<R: Read>(&mut self, _reader: &mut R, _little_endian: bool) -> Result<()> {
        // Binary parsing would be implemented here
        // For now, return error as we focus on ASCII PLY files
        Err(ArxError::NotImplemented("Binary PLY parsing not yet implemented".into()))
    }
    
    /// Get parsed points
    pub fn points(&self) -> &[Point3D] {
        &self.points
    }
    
    /// Take ownership of points
    pub fn take_points(self) -> Vec<Point3D> {
        self.points
    }
    
    /// Get point cloud statistics
    pub fn statistics(&self) -> PointCloudStatistics {
        if self.points.is_empty() {
            return PointCloudStatistics::default();
        }
        
        let mut min = Point3D::new(f32::MAX, f32::MAX, f32::MAX);
        let mut max = Point3D::new(f32::MIN, f32::MIN, f32::MIN);
        
        for point in &self.points {
            min.x = min.x.min(point.x);
            min.y = min.y.min(point.y);
            min.z = min.z.min(point.z);
            max.x = max.x.max(point.x);
            max.y = max.y.max(point.y);
            max.z = max.z.max(point.z);
        }
        
        let center = Point3D::new(
            (min.x + max.x) / 2.0,
            (min.y + max.y) / 2.0,
            (min.z + max.z) / 2.0,
        );
        
        PointCloudStatistics {
            point_count: self.points.len(),
            min_bounds: min,
            max_bounds: max,
            center,
            has_colors: self.points.iter().any(|p| p.r.is_some()),
            has_normals: self.points.iter().any(|p| p.nx.is_some()),
        }
    }
}

/// Statistics about parsed point cloud
#[derive(Debug, Default)]
pub struct PointCloudStatistics {
    pub point_count: usize,
    pub min_bounds: Point3D,
    pub max_bounds: Point3D,
    pub center: Point3D,
    pub has_colors: bool,
    pub has_normals: bool,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_point_creation() {
        let p1 = Point3D::new(1.0, 2.0, 3.0);
        assert_eq!(p1.x, 1.0);
        assert_eq!(p1.y, 2.0);
        assert_eq!(p1.z, 3.0);
        assert!(p1.r.is_none());
        
        let p2 = Point3D::with_color(1.0, 2.0, 3.0, 255, 128, 0);
        assert_eq!(p2.r, Some(255));
        assert_eq!(p2.g, Some(128));
        assert_eq!(p2.b, Some(0));
    }
    
    #[test]
    fn test_point_distance() {
        let p1 = Point3D::new(0.0, 0.0, 0.0);
        let p2 = Point3D::new(3.0, 4.0, 0.0);
        assert_eq!(p1.distance_to(&p2), 5.0);
    }
}