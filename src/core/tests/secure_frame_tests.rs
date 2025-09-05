use arxos_core::radio::frame::{FrameConfig, RadioProfile, RadioFrame, pack_objects_into_frames, unpack_objects_from_frames};
use arxos_core::radio_secure::secure_frame::{SecurityHeader, seal_frame, open_frame};
use arxos_core::{ArxObject, arxobject::object_types};
use arxos_core::crypto::PacketAuthenticator;
use arxos_core::security::replay::ReplayWindow;

#[test]
fn test_seal_and_open_frame_success() {
    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    let mac = PacketAuthenticator::new([0x11; 32]);
    let mut replay = ReplayWindow::new(32);

    let objs = vec![
        ArxObject::new(0x1111, object_types::OUTLET, 100, 200, 300),
        ArxObject::new(0x1111, object_types::LIGHT, 150, 250, 350),
    ];

    let frames = pack_objects_into_frames(cfg, &objs, |idx, total| {
        let mut h = Vec::with_capacity(4);
        h.extend_from_slice(&(idx as u16).to_le_bytes());
        h.extend_from_slice(&(total as u16).to_le_bytes());
        h
    });
    assert_eq!(frames.len(), 1);

    let sec = SecurityHeader { sender_id: 0x77, key_version: 1, reserved: 0, nonce: 0xAABBCCDD };
    let sealed = seal_frame(cfg, frames[0].clone(), sec, &mac);
    assert!(sealed.payload.len() >= 16); // includes tag

    let opened = open_frame(cfg, &sealed, &mac, &mut replay).expect("should open");

    // After open, payload should be original payload (no tag)
    let restored = unpack_objects_from_frames(&[opened]);
    assert_eq!(restored, objs);
}

#[test]
fn test_open_frame_mac_failure() {
    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    let mac = PacketAuthenticator::new([0x22; 32]);
    let mut replay = ReplayWindow::new(32);

    let objs = vec![ArxObject::new(0x2222, object_types::OUTLET, 1, 2, 3)];
    let frames = pack_objects_into_frames(cfg, &objs, |i,t| { let mut h=Vec::new(); h.extend_from_slice(&(i as u16).to_le_bytes()); h.extend_from_slice(&(t as u16).to_le_bytes()); h });
    let sec = SecurityHeader { sender_id: 1, key_version: 0, reserved: 0, nonce: 1234 };
    let mut sealed = seal_frame(cfg, frames[0].clone(), sec, &mac);

    // Corrupt one byte in the tag
    let len = sealed.payload.len();
    sealed.payload[len - 1] ^= 0xFF;

    let opened = open_frame(cfg, &sealed, &mac, &mut replay);
    assert!(opened.is_none());
}

#[test]
fn test_open_frame_replay_protection() {
    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    let mac = PacketAuthenticator::new([0x33; 32]);
    let mut replay = ReplayWindow::new(4);

    let objs = vec![ArxObject::new(0x3333, object_types::OUTLET, 10, 20, 30)];
    let frames = pack_objects_into_frames(cfg, &objs, |i,t| { let mut h=Vec::new(); h.extend_from_slice(&(i as u16).to_le_bytes()); h.extend_from_slice(&(t as u16).to_le_bytes()); h });

    let sec = SecurityHeader { sender_id: 42, key_version: 1, reserved: 0, nonce: 0x01020304 };
    let sealed = seal_frame(cfg, frames[0].clone(), sec, &mac);

    // First open succeeds
    let opened1 = open_frame(cfg, &sealed, &mac, &mut replay);
    assert!(opened1.is_some());

    // Second open with identical frame should fail due to replay
    let opened2 = open_frame(cfg, &sealed, &mac, &mut replay);
    assert!(opened2.is_none());
}


