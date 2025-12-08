// Integration test: Verify IFC files parse with correct bounding boxes
use std::path::Path;

#[test]
fn test_ifc_files_parse_with_bounding_boxes() {
    let test_files = vec![
        "test_data/sample_building.ifc",
        "test_data/Building-Hvac.ifc",
        "test_data/Building-Architecture.ifc",
    ];

    for file_path in test_files {
        if !Path::new(file_path).exists() {
            eprintln!("⚠️  Skipping {}: file not found", file_path);
            continue;
        }

        println!("📄 Testing IFC file: {}", file_path);
        
        // Use ArxOS IFC processor to parse
        let processor = arxos::ifc::IFCProcessor::new();
        match processor.process_file(file_path) {
            Ok((building, spatial_entities)) => {
                println!("  ✅ Parsed successfully");
                println!("  📊 Building: {}", building.name);
                println!("  🏢 Floors: {}", building.floors.len());
                println!("  📦 Spatial entities: {}", spatial_entities.len());
                
                // Verify spatial entities have valid bounding boxes where applicable
                for entity in &spatial_entities {
                    if let Some(bbox) = &entity.bounding_box {
                        // Basic sanity check: max >= min for all dimensions
                        assert!(bbox.max.x >= bbox.min.x, "Invalid bbox X for entity");
                        assert!(bbox.max.y >= bbox.min.y, "Invalid bbox Y for entity");
                        assert!(bbox.max.z >= bbox.min.z, "Invalid bbox Z for entity");
                    }
                }
                println!("  ✅ All bounding boxes valid");
            }
            Err(e) => {
                panic!("❌ Failed to parse {}: {:?}", file_path, e);
            }
        }
        println!();
    }
}
