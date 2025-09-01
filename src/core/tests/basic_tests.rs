// Basic integration tests for core functionality
use arxos_core::arxobject::{ArxObject, object_types};
use arxos_core::detail_store::DetailLevel;

#[test]
fn test_arxobject_size() {
    // Critical: ArxObject must be exactly 13 bytes
    assert_eq!(std::mem::size_of::<ArxObject>(), 13);
}

#[test]
fn test_arxobject_round_trip() {
    let obj = ArxObject::new(
        0x1234,
        object_types::OUTLET,
        1000,
        2000,
        1500
    );
    
    let bytes = obj.to_bytes();
    assert_eq!(bytes.len(), 13);
    
    let restored = ArxObject::from_bytes(&bytes);
    assert_eq!(obj, restored);
    
    // Copy values from packed struct to avoid alignment issues
    let building_id = restored.building_id;
    let obj_type = restored.object_type;
    let x = restored.x;
    let y = restored.y;
    let z = restored.z;
    
    assert_eq!(building_id, 0x1234);
    assert_eq!(obj_type, object_types::OUTLET);
    assert_eq!(x, 1000);
    assert_eq!(y, 2000);
    assert_eq!(z, 1500);
}

#[test]
fn test_coordinate_limits() {
    // Test maximum coordinates (u16 max = 65535mm = 65.535m)
    let obj = ArxObject::new(
        0xFFFF,
        object_types::WALL,
        65535,
        65535,
        65535
    );
    
    let x = obj.x;
    let y = obj.y;
    let z = obj.z;
    
    assert_eq!(x, 65535);
    assert_eq!(y, 65535);
    assert_eq!(z, 65535);
}

#[test]
fn test_object_types() {
    // Test various object types
    let types = vec![
        object_types::OUTLET,
        object_types::LIGHT,
        object_types::LIGHT_SWITCH,
        object_types::AIR_VENT,
        object_types::THERMOSTAT,
        object_types::FLOOR,
        object_types::CEILING,
        object_types::WALL,
        object_types::DOOR,
        object_types::WINDOW,
    ];
    
    for obj_type in types {
        let obj = ArxObject::new(0x0001, obj_type, 1000, 1000, 1000);
        let stored_type = obj.object_type;
        assert_eq!(stored_type, obj_type);
    }
}

#[test]
fn test_detail_level() {
    let level = DetailLevel::default();
    // DetailLevel has boolean fields for different detail types
    assert!(!level.basic); // All default to false
}

#[test] 
fn test_property_array() {
    let mut obj = ArxObject::new(0x0001, object_types::AIR_VENT, 1000, 1000, 1000);
    
    // Set some properties
    obj.properties[0] = 100; // CFM
    obj.properties[1] = 1;   // Supply
    obj.properties[2] = 24;  // Temp
    obj.properties[3] = 0;   // Reserved
    
    // Verify they're stored
    assert_eq!(obj.properties[0], 100);
    assert_eq!(obj.properties[1], 1);
    assert_eq!(obj.properties[2], 24);
    assert_eq!(obj.properties[3], 0);
}