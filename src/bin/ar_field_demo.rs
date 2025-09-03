//! AR Field Technician Demo
//! 
//! Demonstrates how a field tech using iPhone LiDAR can collaborate
//! with a supervisor in real-time over low-bandwidth radio

use arxos_core::ar_compression::*;
use arxos_core::ar_streaming::*;
use arxos_core::arxobject::ArxObject;

fn main() {
    println!("\n╔═══════════════════════════════════════════════════════════╗");
    println!("║    ArxOS AR Field Collaboration Demo                       ║");
    println!("║    Compressing Reality for Radio Transmission              ║");
    println!("╚═══════════════════════════════════════════════════════════╝\n");

    // Scenario: Field tech needs to reroute electrical conduit around HVAC duct
    demo_field_scenario();
    
    // Show compression metrics
    show_compression_analysis();
    
    // Demonstrate real-time streaming
    simulate_ar_scenario();
}

fn demo_field_scenario() {
    println!("📱 FIELD TECHNICIAN (iPhone with LiDAR)");
    println!("════════════════════════════════════════");
    println!("Location: School Building #42, Room 127");
    println!("Task: Install new electrical conduit");
    println!("Problem: HVAC duct blocking planned route\n");

    // Tech scans room with LiDAR (stays local, not transmitted)
    println!("1️⃣  LiDAR Scan:");
    println!("   • Raw point cloud: 2,847,293 points");
    println!("   • File size: ~45.5 MB");
    println!("   • ❌ Too large for radio transmission!\n");

    // Tech draws new route in AR
    println!("2️⃣  AR Drawing (new conduit path):");
    let mut compressor = ARCompressor::new(42); // Building #42
    
    // Create the path segments
    let segments = vec![
        // Segment 1: Start from electrical panel
        ARDrawingPrimitive {
            path_type: ARPathType::ElectricalConduit,
            start: (1250.0, 3400.0, 2800.0), // mm from room origin
            end: (2250.0, 3400.0, 2800.0),
            obstacle_id: None,
            bend_radius: None,
            annotations: AnnotationFlags::default(),
        },
        // Segment 2: Bend around HVAC duct
        ARDrawingPrimitive {
            path_type: ARPathType::ElectricalConduit,
            start: (2250.0, 3400.0, 2800.0),
            end: (2250.0, 4200.0, 2800.0),
            obstacle_id: Some(0xA3), // HVAC duct ID
            bend_radius: Some(300.0), // 30cm bend radius
            annotations: AnnotationFlags {
                code_violation: false,
                needs_approval: true, // Deviation from plan
                cost_impact: true,    // Extra materials
                ..Default::default()
            },
        },
        // Segment 3: Return to original path
        ARDrawingPrimitive {
            path_type: ARPathType::ElectricalConduit,
            start: (2250.0, 4200.0, 2800.0),
            end: (4250.0, 4200.0, 2800.0),
            obstacle_id: None,
            bend_radius: None,
            annotations: AnnotationFlags::default(),
        },
        // Segment 4: Connect to outlet location
        ARDrawingPrimitive {
            path_type: ARPathType::ElectricalConduit,
            start: (4250.0, 4200.0, 2800.0),
            end: (4250.0, 3400.0, 2600.0), // Drop down to outlet height
            obstacle_id: None,
            bend_radius: Some(150.0), // Smooth transition
            annotations: AnnotationFlags {
                safety_critical: true, // Near live wires
                ..Default::default()
            },
        },
    ];

    // Compress the path
    let compressed_objects = compressor.compress_path(&segments);
    
    println!("   • Path segments: {}", segments.len());
    println!("   • Compressed to: {} ArxObjects", compressed_objects.len());
    println!("   • Total size: {} bytes", compressed_objects.len() * 13);
    println!("   • ✅ Easily fits in radio bandwidth!\n");

    // Show the actual ArxObjects
    println!("3️⃣  Compressed ArxObjects (hex):");
    for (i, obj) in compressed_objects.iter().enumerate().take(3) {
        println!("   [{:2}] Type:0x{:02X} Pos:({},{},{}) Props:[{:02X},{:02X},{:02X},{:02X}]",
            i, obj.object_type, obj.x, obj.y, obj.z,
            obj.properties[0], obj.properties[1], obj.properties[2], obj.properties[3]);
    }
    if compressed_objects.len() > 3 {
        println!("   ... {} more objects", compressed_objects.len() - 3);
    }
    println!();

    // Simulate supervisor receiving and reconstructing
    println!("💻 SUPERVISOR (Operations Center)");
    println!("═══════════════════════════════════");
    println!("Receiving ArxObjects over radio...\n");

    let mut decompressor = ARDecompressor::new();
    let mut reconstructed_paths = Vec::new();

    for obj in &compressed_objects {
        if let Some(paths) = decompressor.process_object(obj) {
            reconstructed_paths = paths;
        }
    }

    println!("4️⃣  Reconstructed Path:");
    for (i, segment) in reconstructed_paths.iter().enumerate() {
        println!("   Segment {}: {:?} conduit", i + 1, segment.path_type);
        println!("      From: ({:.1}, {:.1}, {:.1}) mm", 
            segment.start.0, segment.start.1, segment.start.2);
        println!("      To:   ({:.1}, {:.1}, {:.1}) mm",
            segment.end.0, segment.end.1, segment.end.2);
        
        if let Some(obstacle_id) = segment.obstacle_id {
            println!("      ⚠️  Avoiding obstacle: 0x{:04X}", obstacle_id);
        }
        
        if segment.annotations.needs_approval {
            println!("      📋 Requires approval (cost impact)");
        }
        
        if segment.annotations.safety_critical {
            println!("      🚨 Safety critical section!");
        }
    }
    println!();

    // Generate interpolated path for visualization
    let points = decompressor.interpolate_path(&reconstructed_paths);
    println!("5️⃣  Procedural Path Interpolation:");
    println!("   • Generated {} smooth points from {} segments", 
        points.len(), reconstructed_paths.len());
    println!("   • Ready for 3D visualization");
    println!("   • No raw LiDAR data needed!\n");
}

fn show_compression_analysis() {
    println!("📊 COMPRESSION ANALYSIS");
    println!("════════════════════════");
    
    println!("Traditional Approach:");
    println!("  • LiDAR scan:        45,500,000 bytes");
    println!("  • AR annotations:     1,200,000 bytes");
    println!("  • Total:             46,700,000 bytes");
    println!("  • Time on 9.6kbps:   10.8 hours ❌\n");
    
    println!("ArxOS Approach:");
    println!("  • Semantic objects:         91 bytes (7 ArxObjects)");
    println!("  • Time on 9.6kbps:         76 milliseconds ✅");
    println!("  • Compression ratio:   513,186:1 🚀\n");
    
    println!("Why It Works:");
    println!("  1. LiDAR stays local (context, not data)");
    println!("  2. Transmit intent, not geometry");
    println!("  3. Shared building model (both sides have context)");
    println!("  4. Procedural reconstruction from seeds");
    println!("  5. 13-byte constraint forces semantic compression\n");
}

fn format_time(ms: f64) -> String {
    if ms < 1000.0 {
        format!("{:.1}ms", ms)
    } else if ms < 60000.0 {
        format!("{:.1}s", ms / 1000.0)
    } else if ms < 3600000.0 {
        format!("{:.1}min", ms / 60000.0)
    } else {
        format!("{:.1}hr", ms / 3600000.0)
    }
}