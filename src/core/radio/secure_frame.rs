//! Secure radio frames: appends a 16-byte MAC and includes sender, nonce.
//! Uses PacketAuthenticator (SHA-256 based MAC) for lightweight per-frame auth.

#![deny(clippy::pedantic, clippy::nursery)]
#![allow(clippy::module_name_repetitions, clippy::missing_errors_doc, clippy::missing_panics_doc)]
use crate::crypto::PacketAuthenticator;
use crate::radio::frame::{FrameConfig, RadioFrame};
use crate::security::replay::ReplayWindow;

/// Metadata that precedes/augments RadioFrame.header for auth
#[derive(Debug, Clone, Copy)]
pub struct SecurityHeader {
    pub sender_id: u16,
    pub key_version: u8,
    pub reserved: u8,
    pub nonce: u32, // per-frame nonce (timestamp or counter)
}

impl SecurityHeader {
    pub const LEN: usize = 8; // 2 + 1 + 1 + 4
    pub fn to_bytes(&self) -> [u8; Self::LEN] {
        let mut out = [0u8; Self::LEN];
        let sid = self.sender_id.to_le_bytes(); out[0] = sid[0]; out[1] = sid[1];
        out[2] = self.key_version; out[3] = self.reserved;
        let n = self.nonce.to_le_bytes(); out[4] = n[0]; out[5] = n[1]; out[6] = n[2]; out[7] = n[3];
        out
    }
}

/// Securely pack: prepend SecurityHeader to header, append 16B MAC
pub fn seal_frame(
    cfg: FrameConfig,
    mut frame: RadioFrame,
    sec: SecurityHeader,
    mac: &PacketAuthenticator,
) -> RadioFrame {
    // Build authenticated bytes: security header || original header || payload
    let sh = sec.to_bytes();
    let mut auth_data = Vec::with_capacity(SecurityHeader::LEN + frame.header.len() + frame.payload.len());
    auth_data.extend_from_slice(&sh);
    auth_data.extend_from_slice(&frame.header);
    auth_data.extend_from_slice(&frame.payload);

    let tag = mac.generate_mac(&auth_data); // 16 bytes

    // New header becomes: security header || original header
    let mut new_header = Vec::with_capacity(SecurityHeader::LEN + frame.header.len());
    new_header.extend_from_slice(&sh);
    new_header.extend_from_slice(&frame.header);

    // New payload becomes: payload || tag
    let mut new_payload = frame.payload;
    new_payload.extend_from_slice(&tag);

    RadioFrame { header: new_header, payload: new_payload }
}

/// Verify and strip MAC; enforce replay protection by (sender_id, nonce)
pub fn open_frame(
    cfg: FrameConfig,
    frame: &RadioFrame,
    mac: &PacketAuthenticator,
    replay: &mut ReplayWindow,
) -> Option<RadioFrame> {
    if frame.header.len() < SecurityHeader::LEN { return None; }
    if frame.payload.len() < 16 { return None; }

    // Split components
    let sh_bytes: [u8; SecurityHeader::LEN] = frame.header[0..SecurityHeader::LEN].try_into().ok()?;
    let orig_header = frame.header[SecurityHeader::LEN..].to_vec();
    let (payload_wo_tag, tag) = frame.payload.split_at(frame.payload.len() - 16);

    let sender_id = u16::from_le_bytes([sh_bytes[0], sh_bytes[1]]);
    let key_version = sh_bytes[2];
    let nonce = u32::from_le_bytes([sh_bytes[4], sh_bytes[5], sh_bytes[6], sh_bytes[7]]);

    // Re-compose authenticated data
    let mut auth_data = Vec::with_capacity(SecurityHeader::LEN + orig_header.len() + payload_wo_tag.len());
    auth_data.extend_from_slice(&sh_bytes);
    auth_data.extend_from_slice(&orig_header);
    auth_data.extend_from_slice(payload_wo_tag);

    // Verify MAC
    let mut tag_arr = [0u8; 16];
    tag_arr.copy_from_slice(tag);
    if !mac.verify_mac(&auth_data, &tag_arr) { return None; }

    // Replay protection
    let token = ((nonce as u64) << 16) | sender_id as u64;
    if !replay.accept(sender_id, token) { return None; }

    Some(RadioFrame { header: orig_header, payload: payload_wo_tag.to_vec() })
}


