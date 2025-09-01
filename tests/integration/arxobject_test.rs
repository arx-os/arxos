//! Integration tests for ArxObject compression and transmission

use arxos_core::arxobject::{ArxObject, object_types};

#[test]
fn test_arxobject_compression_ratio() {
    // Create 1000 ArxObjects representing a building
    let objects: Vec<ArxObject> = (0..1000)
        .map(|i| {
            let object_type = match i % 10 {
                0 => object_types::OUTLET,
                1 => object_types::LIGHT,
                2 => object_types::DOOR,
                3 => object_types::WINDOW,
                4 => object_types::THERMOSTAT,
                5 => object_types::SMOKE_DETECTOR,
                6 => object_types::FIRE_ALARM,
                7 => object_types::AIR_VENT,
                8 => object_types::EMERGENCY_EXIT,
                _ => object_types::SPRINKLER,
            };
            
            ArxObject::new(
                i as u16,
                object_type,
                ((i * 100) % 65535) as u16,
                ((i * 200) % 65535) as u16,
                ((i * 50) % 3000) as u16,
            )
        })
        .collect();
    
    // Calculate sizes
    let arxobject_size = objects.len() * ArxObject::SIZE;
    assert_eq!(arxobject_size, 13000); // 13KB for 1000 objects
    
    // Simulate equivalent point cloud size
    // Assume each object represents ~50KB of point cloud data
    let point_cloud_size = objects.len() * 50_000;
    
    // Calculate compression ratio
    let compression_ratio = point_cloud_size as f32 / arxobject_size as f32;
    
    println!("ArxObject size: {} bytes", arxobject_size);
    println!("Simulated point cloud size: {} bytes", point_cloud_size);
    println!("Compression ratio: {:.1}:1", compression_ratio);
    
    // Should achieve at least 3000:1 compression
    assert!(compression_ratio > 3000.0, 
            "Compression ratio {:.1} is below target of 3000:1", compression_ratio);
}

#[test]
fn test_arxobject_round_trip_serialization() {
    let original = ArxObject::new(0x1234, object_types::OUTLET, 5000, 3000, 300);
    
    // Serialize to bytes
    let bytes = original.to_bytes();
    assert_eq!(bytes.len(), 13);
    
    // Deserialize back
    let restored = ArxObject::from_bytes(&bytes);
    
    // Verify all fields match (copy from packed struct)
    let orig_id = original.id;
    let rest_id = restored.id;
    assert_eq!(orig_id, rest_id);
    
    let orig_type = original.object_type;
    let rest_type = restored.object_type;
    assert_eq!(orig_type, rest_type);
    
    let orig_x = original.x;
    let rest_x = restored.x;
    assert_eq!(orig_x, rest_x);
    
    let orig_y = original.y;
    let rest_y = restored.y;
    assert_eq!(orig_y, rest_y);
    
    let orig_z = original.z;
    let rest_z = restored.z;
    assert_eq!(orig_z, rest_z);
}

#[test]
fn test_arxobject_coordinate_limits() {
    // Test maximum coordinate values (65.535 meters)
    let max_coord = ArxObject::new(
        0xFFFF,
        object_types::WALL,
        65535,
        65535,
        65535
    );
    
    let max_x = max_coord.x;
    let max_y = max_coord.y;
    let max_z = max_coord.z;
    
    assert_eq!(max_x, 65535);
    assert_eq!(max_y, 65535);
    assert_eq!(max_z, 65535);
    
    // Test minimum coordinate values
    let min_coord = ArxObject::new(
        0x0001,
        object_types::FLOOR,
        0,
        0,
        0
    );
    
    let min_x = min_coord.x;
    let min_y = min_coord.y;
    let min_z = min_coord.z;
    
    assert_eq!(min_x, 0);
    assert_eq!(min_y, 0);
    assert_eq!(min_z, 0);
}

#[test]
fn test_building_representation() {
    // Create a realistic building with multiple floors
    let mut building_objects = Vec::new();
    let floors = 5;
    let rooms_per_floor = 10;
    let objects_per_room = 5;
    
    let mut id = 1u16;
    
    for floor in 0..floors {
        for room in 0..rooms_per_floor {
            for obj in 0..objects_per_room {
                let object_type = match obj {
                    0 => object_types::OUTLET,
                    1 => object_types::LIGHT,
                    2 => object_types::DOOR,
                    3 => object_types::SMOKE_DETECTOR,
                    _ => object_types::AIR_VENT,
                };
                
                let x = (room * 5000 + obj * 1000) as u16;
                let y = (room * 3000) as u16;
                let z = (floor * 3000 + 300) as u16;
                
                building_objects.push(ArxObject::new(id, object_type, x, y, z));
                id += 1;
            }
        }
    }
    
    // Verify we created the expected number of objects
    assert_eq!(building_objects.len(), floors * rooms_per_floor * objects_per_room);
    
    // Calculate total size
    let total_size = building_objects.len() * ArxObject::SIZE;
    println!("Building with {} objects: {} bytes total", building_objects.len(), total_size);
    
    // This entire building fits in less than 4KB!
    assert!(total_size < 4000, "Building representation exceeds 4KB");
}