#![cfg(all(feature = "std", feature = "mobile_offline"))]

use arxos_core::{ArxObject, arxobject::object_types};
use arxos_core::mobile_offline::transport::QueueTransport;
use arxos_core::mobile_offline::binder::MobileBinder;

#[test]
fn test_mobile_binder_loopback() {
    let shared_key = [0x42; 32];
    let mut tx = QueueTransport::new();
    let mut rx = QueueTransport::new();

    // Simulate a wire by moving sent frames from sender to receiver incoming
    let mut sender = MobileBinder::new(tx, shared_key, 0x1111, 1);
    let mut receiver = MobileBinder::new(rx, shared_key, 0x2222, 1);

    // Prepare objects
    let objects = vec![
        ArxObject::new(0xAAAA, object_types::OUTLET, 100, 200, 300),
        ArxObject::new(0xAAAA, object_types::LIGHT, 150, 250, 350),
    ];

    // Send
    let sent_frames = sender.send_objects(&objects).expect("send ok");
    assert!(sent_frames >= 1);

    // Move frames onto receiver's incoming
    let mut sent = sender.transport.sent_frames.clone();
    for frame in sent.drain(..) {
        receiver.transport.push_incoming(frame);
    }

    // Receive
    let restored = receiver.poll_objects();
    assert_eq!(restored, objects);
}

#[test]
fn test_meshtastic_adapter_roundtrip() {
    use arxos_core::radio::frame::{FrameConfig, RadioProfile};
    use arxos_core::radio_adapter::adapter::{create_broadcast_packets, decode_broadcast_payload};
    use arxos_core::security::replay::ReplayWindow;
    use arxos_core::crypto::PacketAuthenticator;

    let cfg = FrameConfig::for_profile(RadioProfile::MeshtasticLoRa);
    let mac = PacketAuthenticator::new([0xAA; 32]);
    let mut replay = ReplayWindow::new(16);

    let objects = (0..25).map(|i| ArxObject::new(0xABCD, object_types::OUTLET, i, i*2, 5)).collect::<Vec<_>>();
    let packets = create_broadcast_packets(1, 0xFFFF, 1, cfg, &objects, &mac, 0x77, 1, 0);
    assert!(!packets.is_empty());

    // Decode first packet payload back to objects
    let restored = decode_broadcast_payload(cfg, &packets[0].payload, &mac, &mut replay).expect("decode ok");
    assert!(!restored.is_empty());
}


