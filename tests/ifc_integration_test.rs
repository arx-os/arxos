// Integration test: Verify IFC files parse with the native path into core::Building
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

        let processor = arxos::ifc::IFCProcessor::new();
        match processor.parse_native(file_path, false) {
            Ok(result) => {
                let building = result.building;
                println!("  ✅ Parsed successfully");
                println!("  📊 Building: {}", building.name);
                println!("  🏢 Floors: {}", building.floors.len());

                // Validate room bounding boxes on the canonical Building graph
                for floor in &building.floors {
                    for wing in &floor.wings {
                        for room in &wing.rooms {
                            let bbox = &room.spatial_properties.bounding_box;
                            assert!(
                                bbox.max.x >= bbox.min.x,
                                "Invalid bbox X for room {}",
                                room.id
                            );
                            assert!(
                                bbox.max.y >= bbox.min.y,
                                "Invalid bbox Y for room {}",
                                room.id
                            );
                            assert!(
                                bbox.max.z >= bbox.min.z,
                                "Invalid bbox Z for room {}",
                                room.id
                            );
                        }
                    }
                }
                println!("  ✅ Room bounding boxes valid");
            }
            Err(e) => {
                panic!("❌ Failed to parse {}: {:?}", file_path, e);
            }
        }
        println!();
    }
}
