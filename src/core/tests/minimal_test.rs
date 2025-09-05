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

use arxos_core::{ArxObject, arxobject::object_types};
use arxos_core::radio::frame::{FrameConfig, RadioProfile, pack_objects_into_frames, unpack_objects_from_frames};
use arxos_core::radio_secure::secure_frame::{SecurityHeader, seal_frame, open_frame};
use arxos_core::crypto::PacketAuthenticator;
use arxos_core::security::replay::ReplayWindow;

#[test]
fn test_radio_frame_and_secure_roundtrip() {
    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    let objs = vec![
        ArxObject::new(0x1111, object_types::OUTLET, 10, 20, 30),
        ArxObject::new(0x1111, object_types::LIGHT, 11, 21, 31),
        ArxObject::new(0x1111, object_types::THERMOSTAT, 12, 22, 32),
    ];
    let frames = pack_objects_into_frames(cfg, &objs, |i,t| { let mut h=Vec::new(); h.extend_from_slice(&(i as u16).to_le_bytes()); h.extend_from_slice(&(t as u16).to_le_bytes()); h });
    let mac = PacketAuthenticator::new([0x42; 32]);
    let sec = SecurityHeader { sender_id: 7, key_version: 1, reserved: 0, nonce: 0x01020304 };
    let sealed = seal_frame(cfg, frames[0].clone(), sec, &mac);
    let mut replay = ReplayWindow::new(8);
    let opened = open_frame(cfg, &sealed, &mac, &mut replay).expect("open ok");
    let restored = unpack_objects_from_frames(&[opened]);
    assert_eq!(restored, objs);
}

#[test]
fn test_fragmentation_edges() {
    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    let per = cfg.objects_per_frame().max(1);
    // 0 objects
    let frames0 = pack_objects_into_frames(cfg, &[], |i,t| { let mut h=Vec::new(); h.extend_from_slice(&(i as u16).to_le_bytes()); h.extend_from_slice(&(t as u16).to_le_bytes()); h });
    assert_eq!(frames0.len(), 1);
    // 1 object
    let one = vec![ArxObject::new(1, object_types::OUTLET, 0,0,0)];
    let frames1 = pack_objects_into_frames(cfg, &one, |i,t| { let mut h=Vec::new(); h.extend_from_slice(&(i as u16).to_le_bytes()); h.extend_from_slice(&(t as u16).to_le_bytes()); h });
    assert_eq!(frames1.len(), 1);
    // MAX objects in one frame
    let max_objs: Vec<_> = (0..per).map(|i| ArxObject::new(1, object_types::OUTLET, i as i16,0,0)).collect();
    let frames_max = pack_objects_into_frames(cfg, &max_objs, |i,t| { let mut h=Vec::new(); h.extend_from_slice(&(i as u16).to_le_bytes()); h.extend_from_slice(&(t as u16).to_le_bytes()); h });
    assert_eq!(frames_max.len(), 1);
    // MAX+1 objects spills to 2 frames
    let maxp1: Vec<_> = (0..(per+1)).map(|i| ArxObject::new(1, object_types::OUTLET, i as i16,0,0)).collect();
    let frames_maxp1 = pack_objects_into_frames(cfg, &maxp1, |i,t| { let mut h=Vec::new(); h.extend_from_slice(&(i as u16).to_le_bytes()); h.extend_from_slice(&(t as u16).to_le_bytes()); h });
    assert_eq!(frames_maxp1.len(), 2);
}

#[test]
fn test_seeded_fuzz_arxobject_roundtrip() {
    let mut seed: u64 = 0xDEADBEEFCAFEBABE;
    for _ in 0..200 {
        // Simple LCG for determinism without external deps
        seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
        let bid = (seed >> 48) as u16 | 1; // non-null
        let typ = (((seed >> 40) as u8) & 0x1F) | 0x10; // keep in electrical+ range
        let x = (seed >> 24) as i16;
        let y = (seed >> 8) as i16;
        let z = seed as i16;
        let props = [seed as u8, (seed>>8) as u8, (seed>>16) as u8, (seed>>24) as u8];
        let obj = ArxObject::with_properties(bid, typ, x, y, z, props);
        let bytes = obj.to_bytes();
        let restored = ArxObject::from_bytes(&bytes);
        assert_eq!(obj, restored);
    }
}