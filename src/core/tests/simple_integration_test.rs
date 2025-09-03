//! Simple integration test using the clean implementations

use arxos_core::arxobject_simple::{ArxObject, object_types};
use arxos_core::point_cloud_simple::{SimplePointCloudProcessor};
use arxos_core::document_parser::{Point3D, BoundingBox};
use arxos_core::point_cloud_parser::PointCloud;

#[test]
fn test_arxobject_core_functionality() {
    // Test 1: ArxObject size is exactly 13 bytes
    assert_eq!(std::mem::size_of::<ArxObject>(), 13);
    
    // Test 2: Create and serialize ArxObject
    let obj = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 300);
    let bytes = obj.to_bytes();
    assert_eq!(bytes.len(), 13);
    
    // Test 3: Deserialize and verify
    let restored = ArxObject::from_bytes(&bytes);
    
    // Copy fields to avoid packed struct alignment issues
    let building_id = restored.building_id;
    let object_type = restored.object_type;
    let x = restored.x;
    let y = restored.y;
    let z = restored.z;
    
    assert_eq!(building_id, 0x1234);
    assert_eq!(object_type, object_types::OUTLET);
    assert_eq!(x, 1000);
    assert_eq!(y, 2000);
    assert_eq!(z, 300);
}

#[test]
fn test_point_cloud_to_arxobject() {
    // Create a simple point cloud
    let mut points = Vec::new();
    
    // Add a cluster of points representing an outlet at 30cm height
    for dx in 0..10 {
        for dy in 0..10 {
            points.push(Point3D {
                x: 1.0 + dx as f32 * 0.01,
                y: 2.0 + dy as f32 * 0.01,
                z: 0.3, // 30cm height (outlet height)
            });
        }
    }
    
    // Add a cluster representing a light switch at 1.2m height
    for dx in 0..10 {
        for dy in 0..10 {
            points.push(Point3D {
                x: 2.0 + dx as f32 * 0.01,
                y: 1.0 + dy as f32 * 0.01,
                z: 1.2, // 1.2m height (switch height)
            });
        }
    }
    
    let cloud = PointCloud {
        points,
        colors: vec![],
        normals: vec![],
        bounds: BoundingBox {
            min: Point3D { x: 1.0, y: 1.0, z: 0.3 },
            max: Point3D { x: 2.1, y: 2.1, z: 1.2 },
        },
    };
    
    // Process with the simple processor
    let processor = SimplePointCloudProcessor::new();
    let objects = processor.process(&cloud, 0x0001);
    
    // Should have detected at least 2 objects
    assert!(objects.len() >= 2);
    
    // Verify we found an outlet
    let outlets: Vec<_> = objects.iter()
        .filter(|o| o.object_type == object_types::OUTLET)
        .collect();
    assert!(!outlets.is_empty(), "Should have found at least one outlet");
    
    // Verify we found a light switch
    let switches: Vec<_> = objects.iter()
        .filter(|o| o.object_type == object_types::LIGHT_SWITCH)
        .collect();
    assert!(!switches.is_empty(), "Should have found at least one light switch");
}

#[test]
fn test_object_validation() {
    // Valid object
    let valid = ArxObject::new(0x1234, object_types::OUTLET, 1000, 2000, 300);
    assert!(valid.validate().is_ok());
    
    // Invalid building ID (0)
    let invalid_building = ArxObject::new(0, object_types::OUTLET, 1000, 2000, 300);
    assert!(invalid_building.validate().is_err());
    
    // Invalid object type
    let invalid_type = ArxObject::new(0x1234, 0xAA, 1000, 2000, 300);
    assert!(invalid_type.validate().is_err());
}

#[test]
fn test_position_conversion() {
    let obj = ArxObject::new(0x1234, object_types::OUTLET, 1500, 2500, 300);
    let (x_m, y_m, z_m) = obj.position_meters();
    
    assert_eq!(x_m, 1.5);  // 1500mm = 1.5m
    assert_eq!(y_m, 2.5);  // 2500mm = 2.5m
    assert_eq!(z_m, 0.3);  // 300mm = 0.3m
}

#[test]
fn test_properties_storage() {
    let properties = [10, 20, 30, 40];
    let obj = ArxObject::with_properties(
        0x1234,
        object_types::THERMOSTAT,
        3000,
        4000,
        1500,
        properties,
    );
    
    // Verify properties are stored correctly
    assert_eq!(obj.properties[0], 10);
    assert_eq!(obj.properties[1], 20);
    assert_eq!(obj.properties[2], 30);
    assert_eq!(obj.properties[3], 40);
    
    // Verify serialization preserves properties
    let bytes = obj.to_bytes();
    let restored = ArxObject::from_bytes(&bytes);
    assert_eq!(restored.properties, properties);
}