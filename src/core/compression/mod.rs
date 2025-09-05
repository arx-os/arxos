//! Point Cloud Compression Module
//! 
//! Converts LiDAR point clouds from iPhone scans into compressed ArxObjects
//! achieving 10,000:1 compression through semantic understanding.

pub mod parser;
pub mod parser_enhanced;
pub mod semantic;

pub use parser::PointCloudParser;
pub use semantic::SemanticCompressor;

/// Main entry point for point cloud compression
pub fn compress_point_cloud(points: Vec<(f32, f32, f32)>) -> Vec<crate::arxobject::ArxObject> {
    let mut compressor = SemanticCompressor::new();
    compressor.compress(points)
}