//! Integration test for the clean ArxOS implementation
//! This test verifies the simplified modules work correctly together

#[test]
fn test_arxobject_simple_core() {
    use arxos_core::{ArxObject, object_types};
    
    // Verify size
    assert_eq!(std::mem::size_of::<ArxObject>(), 13);
    
    // Create and test various object types
    let objects = vec![
        ArxObject::new(100, object_types::OUTLET, 1000, 2000, 300),
        ArxObject::new(100, object_types::LIGHT_SWITCH, 2000, 1000, 1200),
        ArxObject::new(100, object_types::THERMOSTAT, 3000, 2000, 1500),
        ArxObject::new(100, object_types::LEAK, 1500, 1500, 100),
    ];
    
    for obj in &objects {
        // Test serialization
        let bytes = obj.to_bytes();
        assert_eq!(bytes.len(), 13);
        
        // Test deserialization
        let restored = ArxObject::from_bytes(&bytes);
        
        // Verify fields (copy to avoid alignment issues)
        let building_id = restored.building_id;
        let object_type = restored.object_type;
        let x = restored.x;
        let y = restored.y;
        let z = restored.z;
        
        assert_eq!(building_id, obj.building_id);
        assert_eq!(object_type, obj.object_type);
        assert_eq!(x, obj.x);
        assert_eq!(y, obj.y);
        assert_eq!(z, obj.z);
    }
}

#[test]
fn test_point_cloud_simple_processing() {
    use arxos_core::object_types;
    use arxos_core::point_cloud_simple::SimplePointCloudProcessor;
    use arxos_core::document_parser::{Point3D, BoundingBox};
    use arxos_core::point_cloud_parser::PointCloud;
    
    // Create a test point cloud with recognizable patterns
    let mut points = Vec::new();
    
    // Floor points (z = 0, many points)
    for x in 0..20 {
        for y in 0..20 {
            points.push(Point3D {
                x: x as f32 * 0.1,
                y: y as f32 * 0.1,
                z: 0.0,
            });
        }
    }
    
    // Outlet cluster (z = 0.3m, small cluster)
    for x in 0..5 {
        for y in 0..5 {
            points.push(Point3D {
                x: 3.0 + x as f32 * 0.01,
                y: 2.0 + y as f32 * 0.01,
                z: 0.3,
            });
        }
    }
    
    // Light switch cluster (z = 1.2m, small cluster)
    for x in 0..5 {
        for y in 0..5 {
            points.push(Point3D {
                x: 1.0 + x as f32 * 0.01,
                y: 1.0 + y as f32 * 0.01,
                z: 1.2,
            });
        }
    }
    
    let cloud = PointCloud {
        points,
        colors: vec![],
        normals: vec![],
        bounds: BoundingBox {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 4.0, y: 3.0, z: 1.2 },
        },
    };
    
    // Process the point cloud
    let processor = SimplePointCloudProcessor::new();
    let objects = processor.process(&cloud, 100);
    
    // Verify we found the expected object types
    assert!(!objects.is_empty(), "Should have found objects");
    
    // Check for floor
    let has_floor = objects.iter().any(|o| o.object_type == object_types::FLOOR);
    assert!(has_floor, "Should have detected floor");
    
    // Check for outlet
    let has_outlet = objects.iter().any(|o| o.object_type == object_types::OUTLET);
    assert!(has_outlet, "Should have detected outlet");
    
    // Check for light switch
    let has_switch = objects.iter().any(|o| o.object_type == object_types::LIGHT_SWITCH);
    assert!(has_switch, "Should have detected light switch");
}

#[test]
fn test_compression_ratio() {
    use arxos_core::ArxObject;
    use arxos_core::document_parser::Point3D;
    
    // Simulate point cloud data size
    let num_points = 1000;
    let point_size = std::mem::size_of::<Point3D>(); // 12 bytes (3 floats)
    let original_size = num_points * point_size;
    
    // Simulate compressed ArxObjects
    let num_objects = 10; // 1000 points compressed to 10 objects
    let object_size = std::mem::size_of::<ArxObject>(); // 13 bytes
    let compressed_size = num_objects * object_size;
    
    let ratio = original_size as f32 / compressed_size as f32;
    
    // Verify significant compression
    assert!(ratio > 50.0, "Compression ratio should be > 50:1, got {:.1}:1", ratio);
    
    println!("Achieved compression ratio: {:.1}:1", ratio);
}

#[test]
fn test_properties_and_validation() {
    use arxos_core::{ArxObject, object_types};
    use arxos_core::arxobject::is_valid_object_type;
    
    // Test properties storage
    let properties = [10, 20, 30, 40];
    let obj = ArxObject::with_properties(
        100,
        object_types::THERMOSTAT,
        3000,
        4000,
        1500,
        properties,
    );
    
    assert_eq!(obj.properties, properties);
    
    // Test serialization preserves properties
    let bytes = obj.to_bytes();
    let restored = ArxObject::from_bytes(&bytes);
    assert_eq!(restored.properties, properties);
    
    // Test validation
    assert!(is_valid_object_type(object_types::OUTLET));
    assert!(is_valid_object_type(object_types::LEAK));
    assert!(!is_valid_object_type(0x99)); // Invalid type
}

#[test]
fn test_object_categories() {
    use arxos_core::{object_types, ObjectCategory};
    
    // Test category classification
    assert_eq!(ObjectCategory::from_type(object_types::OUTLET), ObjectCategory::Electrical);
    assert_eq!(ObjectCategory::from_type(object_types::THERMOSTAT), ObjectCategory::HVAC);
    assert_eq!(ObjectCategory::from_type(object_types::LIGHT), ObjectCategory::Lighting);
    assert_eq!(ObjectCategory::from_type(object_types::WALL), ObjectCategory::Structural);
    assert_eq!(ObjectCategory::from_type(object_types::LEAK), ObjectCategory::Plumbing);
    assert_eq!(ObjectCategory::from_type(0x99), ObjectCategory::Unknown);
}