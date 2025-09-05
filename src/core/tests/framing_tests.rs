use arxos_core::{ArxObject, arxobject::object_types};
use arxos_core::radio::frame::{FrameConfig, RadioProfile, pack_objects_into_frames, unpack_objects_from_frames};

#[test]
fn test_objects_per_frame_meshtastic() {
    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    // 255 MTU - 4 header = 251; 251 / 13 = 19 objects per frame
    assert_eq!(cfg.objects_per_frame(), 19);
}

#[test]
fn test_pack_unpack_roundtrip() {
    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    let mut objs = Vec::new();
    for i in 0..50 {
        let o = ArxObject::with_properties(0x1234, object_types::OUTLET, i * 10, i * 20, i * 5, [i as u8, 1, 2, 3]);
        objs.push(o);
    }

    // Simple header: [frame_index, total_frames] as 2 bytes each LE
    let frames = pack_objects_into_frames(cfg, &objs, |idx, total| {
        let mut h = Vec::with_capacity(4);
        h.extend_from_slice(&(idx as u16).to_le_bytes());
        h.extend_from_slice(&(total as u16).to_le_bytes());
        h
    });

    assert!(frames.len() >= 3); // 50 objects with 19 per frame => 3 frames
    for f in &frames {
        // Header must be 4 bytes as constructed
        assert_eq!(f.header.len(), 4);
        // Payload should be multiple of 13
        assert_eq!(f.payload.len() % ArxObject::SIZE, 0);
    }

    let restored = unpack_objects_from_frames(&frames);
    assert_eq!(restored.len(), objs.len());
    assert_eq!(restored[0], objs[0]);
    assert_eq!(restored[49], objs[49]);
}


