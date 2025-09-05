//! Meshtastic adapter using unified radio frames and secure sealing.
//! Bridges `ArxObject` batches into `MeshtasticPacket`s and back.

use crate::arxobject::ArxObject;
use crate::meshtastic_protocol::{MeshtasticPacket, MeshtasticPacketType};
use crate::radio::frame::{FrameConfig, RadioFrame, pack_objects_into_frames, unpack_objects_from_frames};
use crate::radio_secure::secure_frame::{SecurityHeader, seal_frame, open_frame};
use crate::crypto::PacketAuthenticator;
use crate::security::replay::ReplayWindow;

/// Create Meshtastic broadcast packets from a batch of objects using secure frames.
pub fn create_broadcast_packets(
    source_id: u32,
    dest_id: u32,
    seq_start: u16,
    cfg: FrameConfig,
    objects: &[ArxObject],
    mac: &PacketAuthenticator,
    sender_id: u16,
    key_version: u8,
    nonce_seed: u32,
) -> Vec<MeshtasticPacket> {
    // Pack objects into frames under MTU; header encodes (frame_index, total_frames)
    let frames = pack_objects_into_frames(cfg, objects, |idx, total| {
        let mut h = vec![0u8; cfg.header_len];
        // Little-endian frame index/total (2 bytes each) if header_len >= 4
        if cfg.header_len >= 2 {
            let ib = (idx as u16).to_le_bytes(); h[0] = ib[0]; if cfg.header_len > 1 { h[1] = ib[1]; }
        }
        if cfg.header_len >= 4 {
            let tb = (total as u16).to_le_bytes(); h[2] = tb[0]; h[3] = tb[1];
        }
        h
    });

    // Seal each frame and wrap in Meshtastic packets
    let mut packets = Vec::with_capacity(frames.len());
    for (i, f) in frames.into_iter().enumerate() {
        let sec = SecurityHeader { sender_id, key_version, reserved: 0, nonce: nonce_seed.wrapping_add(i as u32) };
        let sealed = seal_frame(cfg, f, sec, mac);

        // Serialize frame as header || payload
        let mut payload = Vec::with_capacity(sealed.header.len() + sealed.payload.len());
        payload.extend_from_slice(&sealed.header);
        payload.extend_from_slice(&sealed.payload);

        packets.push(MeshtasticPacket::new(
            source_id,
            dest_id,
            MeshtasticPacketType::ArxObjectBroadcast,
            seq_start.wrapping_add(i as u16),
            payload,
        ));
    }

    packets
}

/// Decode one Meshtastic payload (one frame) into objects after MAC verification.
pub fn decode_broadcast_payload(
    cfg: FrameConfig,
    payload: &[u8],
    mac: &PacketAuthenticator,
    replay: &mut ReplayWindow,
) -> Option<Vec<ArxObject>> {
    if payload.len() < 8 + 16 { return None; } // security header + mac at minimum

    // Split into RadioFrame layout: header || payload
    if payload.len() < cfg.header_len + 8 + 16 { return None; }
    // We don't know exact header len on the wire, but we enforce cfg.header_len + SecurityHeader::LEN
    let header_len = 8 + cfg.header_len;
    if payload.len() < header_len { return None; }

    let header = payload[..header_len].to_vec();
    let body = payload[header_len..].to_vec();
    let rf = RadioFrame { header, payload: body };

    // Verify and open
    let opened = open_frame(cfg, &rf, mac, replay)?;
    let objs = unpack_objects_from_frames(&[opened]);
    Some(objs)
}


