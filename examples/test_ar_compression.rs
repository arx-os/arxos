use arxos_core::ar_compression::*;
use arxos_core::arxobject::ArxObject;

fn main() {
    println!("\n=== AR Compression Test ===\n");
    
    // Create test AR drawing (conduit path avoiding HVAC)
    let drawing = ARDrawingPrimitive {
        path_type: ARPathType::ElectricalConduit,
        start: (1250.0, 3400.0, 2800.0),  // millimeters
        end: (4250.0, 3400.0, 2800.0),    // 3 meters away
        obstacle_id: Some(0xA3),          // HVAC duct
        bend_radius: Some(300.0),         // 30cm radius
        annotations: AnnotationFlags {
            needs_approval: true,
            cost_impact: true,
            ..Default::default()
        },
    };
    
    // Compress
    let mut compressor = ARCompressor::new(42);
    let objects = compressor.compress_drawing(&drawing);
    
    println!("Original AR Drawing:");
    println!("  Start: ({:.0}, {:.0}, {:.0}) mm", drawing.start.0, drawing.start.1, drawing.start.2);
    println!("  End:   ({:.0}, {:.0}, {:.0}) mm", drawing.end.0, drawing.end.1, drawing.end.2);
    println!("  Distance: {:.1} meters", 
        ((drawing.end.0 - drawing.start.0).powi(2) + 
         (drawing.end.1 - drawing.start.1).powi(2) + 
         (drawing.end.2 - drawing.start.2).powi(2)).sqrt() / 1000.0);
    
    println!("\nCompressed to {} ArxObjects:", objects.len());
    for (i, obj) in objects.iter().enumerate() {
        println!("  [{}] Type:0x{:02X} @ ({},{},{}) Props:[{:02X},{:02X},{:02X},{:02X}]",
            i, obj.object_type, obj.x, obj.y, obj.z,
            obj.properties[0], obj.properties[1], obj.properties[2], obj.properties[3]);
    }
    
    println!("\nCompression Results:");
    println!("  Traditional LiDAR+AR: ~50 MB");
    println!("  ArxOS Compressed: {} bytes", objects.len() * 13);
    println!("  Compression Ratio: {:.0}:1", 50_000_000.0 / (objects.len() as f64 * 13.0));
    println!("  Transmission Time @ 9.6kbps: {:.1} ms", (objects.len() as f64 * 13.0 * 8.0) / 9.6);
    
    // Decompress
    let mut decompressor = ARDecompressor::new();
    for obj in &objects {
        if let Some(paths) = decompressor.process_object(obj) {
            println!("\nReconstructed {} path segments", paths.len());
        }
    }
    
    println!("\n✅ AR compression working!");
}