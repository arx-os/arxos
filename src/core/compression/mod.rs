//! Point Cloud Compression Module
//! 
//! Converts LiDAR point clouds from iPhone scans into compressed ArxObjects
//! achieving 10,000:1 compression through semantic understanding.

// Unified compression module (preferred)
pub mod unified;

// Legacy modules (to be deprecated)
pub mod parser;
pub mod parser_enhanced;
pub mod semantic;

// Re-export main types
pub use unified::{PointCloudProcessor, VoxelData, MaterialDetector};
pub use parser::PointCloudParser;
pub use semantic::SemanticCompressor;

/// Main entry point for point cloud compression
pub fn compress_point_cloud(points: Vec<(f32, f32, f32)>) -> Vec<crate::arxobject::ArxObject> {
    use semantic::{PointCloud, Point3D};
    
    // Convert tuples to PointCloud structure
    let point_cloud = PointCloud {
        points: points.into_iter()
            .map(|(x, y, z)| Point3D { x, y, z })
            .collect(),
        normals: None,
        colors: None,
    };
    
    let compressor = SemanticCompressor::new();
    let components = compressor.compress(&point_cloud);
    
    // Convert semantic components to ArxObjects
    // Using origin at (0, 0, 0) for simplicity
    let origin = Point3D { x: 0.0, y: 0.0, z: 0.0 };
    compressor.to_arxobjects(&components, origin)
}