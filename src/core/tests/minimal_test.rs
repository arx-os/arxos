// Minimal test to verify core ArxObject functionality

#[test]
fn test_arxobject_size() {
    use arxos_core::ArxObject;
    
    // Critical: ArxObject must be exactly 13 bytes for protocol compatibility
    assert_eq!(std::mem::size_of::<ArxObject>(), 13);
}

#[test]
fn test_arxobject_creation() {
    use arxos_core::{ArxObject, object_types};
    
    let obj = ArxObject::new(
        0x1234,
        object_types::OUTLET,
        1000,
        2000,
        1500
    );
    
    // Copy fields to avoid packed struct alignment issues
    let building_id = obj.building_id;
    let object_type = obj.object_type;
    let x = obj.x;
    let y = obj.y;
    let z = obj.z;
    
    assert_eq!(building_id, 0x1234);
    assert_eq!(object_type, object_types::OUTLET);
    assert_eq!(x, 1000);
    assert_eq!(y, 2000);
    assert_eq!(z, 1500);
}

#[test]
fn test_arxobject_serialization() {
    use arxos_core::{ArxObject, object_types};
    
    let obj = ArxObject::new(
        0x5678,
        object_types::LIGHT_SWITCH,
        3000,
        4000,
        1200
    );
    
    let bytes = obj.to_bytes();
    assert_eq!(bytes.len(), 13);
    
    let restored = ArxObject::from_bytes(&bytes);
    
    // Copy fields to avoid alignment issues
    let building_id = restored.building_id;
    let object_type = restored.object_type;
    let x = restored.x;
    let y = restored.y;
    let z = restored.z;
    
    assert_eq!(building_id, 0x5678);
    assert_eq!(object_type, object_types::LIGHT_SWITCH);
    assert_eq!(x, 3000);
    assert_eq!(y, 4000);
    assert_eq!(z, 1200);
}

#[test]
fn test_detail_level() {
    use arxos_core::DetailLevel;
    
    let basic = DetailLevel::Basic;
    let enhanced = DetailLevel::Enhanced;
    let full = DetailLevel::Full;
    
    // Just verify enum variants exist
    match basic {
        DetailLevel::Basic => assert!(true),
        _ => assert!(false),
    }
}

#[test]
fn test_object_types() {
    use arxos_core::object_types;
    
    // Test that common object types are defined
    assert_eq!(object_types::OUTLET, 0x10);
    assert_eq!(object_types::LIGHT_SWITCH, 0x11);
    assert_eq!(object_types::THERMOSTAT, 0x20);
    assert_eq!(object_types::LIGHT, 0x30);
    assert_eq!(object_types::DOOR, 0x40);
    assert_eq!(object_types::WALL, 0x54);
    assert_eq!(object_types::FLOOR, 0x51);
    assert_eq!(object_types::CEILING, 0x55);
    assert_eq!(object_types::LEAK, 0x68);
}