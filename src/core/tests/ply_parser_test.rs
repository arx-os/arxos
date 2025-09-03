//! Test the PLY parser with our clean implementation

use arxos_core::ply_parser_simple::{SimplePlyParser, PlyStats};
use arxos_core::arxobject_simple::object_types;

#[test]
fn test_parse_test_ply_file() {
    let parser = SimplePlyParser::new();
    
    // Parse the test PLY file we created earlier
    let result = parser.parse_ply_file("test_data/simple_room.ply");
    
    assert!(result.is_ok(), "Should parse test PLY file");
    
    let points = result.unwrap();
    assert_eq!(points.len(), 1000, "Should have 1000 points");
    
    // Verify bounds are reasonable
    let first = points.first().unwrap();
    assert!(first.x >= 0.0 && first.x <= 10.0);
    assert!(first.y >= 0.0 && first.y <= 10.0);
}

#[test]
fn test_ply_to_arxobjects() {
    let parser = SimplePlyParser::new();
    
    // Convert PLY to ArxObjects
    let result = parser.parse_to_arxobjects("test_data/simple_room.ply", 0x4A7B);
    
    assert!(result.is_ok(), "Should convert to ArxObjects");
    
    let objects = result.unwrap();
    assert!(!objects.is_empty(), "Should generate ArxObjects");
    
    // Verify all objects have correct building ID
    for obj in &objects {
        assert_eq!(obj.building_id, 0x4A7B);
    }
    
    // Check for floor objects (z near 0)
    let has_floor = objects.iter().any(|o| o.object_type == object_types::FLOOR);
    assert!(has_floor, "Should detect floor from low Z points");
}

#[test]
fn test_compression_ratio() {
    let parser = SimplePlyParser::new();
    
    // Get file stats
    let stats = parser.get_file_stats("test_data/simple_room.ply").unwrap();
    assert_eq!(stats.point_count, 1000);
    
    // Parse to ArxObjects
    let objects = parser.parse_to_arxobjects("test_data/simple_room.ply", 0x4A7B).unwrap();
    
    // Calculate compression ratio
    let ratio = stats.compression_ratio(objects.len());
    
    println!("PLY Compression Results:");
    println!("  Input: {} points ({} bytes)", stats.point_count, stats.size_bytes);
    println!("  Output: {} ArxObjects ({} bytes)", objects.len(), objects.len() * 13);
    println!("  Compression ratio: {:.1}:1", ratio);
    
    // We should achieve significant compression
    assert!(ratio > 10.0, "Should achieve at least 10:1 compression");
}

#[test]
fn test_invalid_ply_file() {
    let parser = SimplePlyParser::new();
    
    // Try to parse non-existent file
    let result = parser.parse_ply_file("nonexistent.ply");
    assert!(result.is_err());
    
    // Try to parse invalid file (if we had one)
    // This would test error handling
}

#[test]
fn test_ply_stats() {
    let parser = SimplePlyParser::new();
    
    let stats = parser.get_file_stats("test_data/simple_room.ply");
    assert!(stats.is_ok());
    
    let stats = stats.unwrap();
    
    // Verify bounds
    let ((min_x, min_y, min_z), (max_x, max_y, max_z)) = stats.bounds;
    
    assert!(min_x >= 0.0 && min_x <= 1.0);
    assert!(max_x >= 9.0 && max_x <= 10.0);
    assert!(min_z >= 0.0 && min_z <= 1.0);
    assert!(max_z >= 0.0 && max_z <= 3.0);
    
    // Size should be reasonable
    assert!(stats.size_bytes > 0);
    assert_eq!(stats.size_bytes, 1000 * 12); // 1000 points * 3 floats * 4 bytes
}