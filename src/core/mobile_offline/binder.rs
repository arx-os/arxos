//! Mobile Offline binder: bridges ArxObjects to/from a mobile device
//! using unified radio framing and secure MAC, over an offline link.

use crate::{ArxObject};
use crate::radio::frame::{FrameConfig, RadioProfile, pack_objects_into_frames, unpack_objects_from_frames, RadioFrame};
use crate::radio_secure::secure_frame::{SecurityHeader, seal_frame, open_frame};
use crate::crypto::PacketAuthenticator;
use crate::security::replay::ReplayWindow;
use super::transport::MobileTransport;

pub struct MobileBinder<T: MobileTransport> {
    cfg: FrameConfig,
    mac: PacketAuthenticator,
    sender_id: u16,
    key_version: u8,
    nonce_counter: u32,
    replay: ReplayWindow,
    transport: T,
}

impl<T: MobileTransport> MobileBinder<T> {
    pub fn new(transport: T, shared_key: [u8; 32], sender_id: u16, key_version: u8) -> Self {
        Self {
            cfg: FrameConfig::for_profile(RadioProfile::MeshtasticLoRa),
            mac: PacketAuthenticator::new(shared_key),
            sender_id,
            key_version,
            nonce_counter: 1,
            replay: ReplayWindow::new(64),
            transport,
        }
    }

    /// Send objects to mobile device as sealed frames
    pub fn send_objects(&mut self, objects: &[ArxObject]) -> Result<usize, ()> {
        let frames = pack_objects_into_frames(self.cfg, objects, |idx, total| {
            let mut h = Vec::with_capacity(4);
            h.extend_from_slice(&(idx as u16).to_le_bytes());
            h.extend_from_slice(&(total as u16).to_le_bytes());
            h
        });
        let mut count = 0usize;
        for f in frames {
            let sec = SecurityHeader { sender_id: self.sender_id, key_version: self.key_version, reserved: 0, nonce: self.nonce_counter };
            self.nonce_counter = self.nonce_counter.wrapping_add(1);
            let sealed = seal_frame(self.cfg, f, sec, &self.mac);
            // serialize wire: header || payload
            let mut wire = Vec::with_capacity(sealed.header.len() + sealed.payload.len());
            wire.extend_from_slice(&sealed.header);
            wire.extend_from_slice(&sealed.payload);
            self.transport.send(&wire).map_err(|_| ())?;
            count += 1;
        }
        Ok(count)
    }

    /// Poll transport and return any received objects after verification
    pub fn poll_objects(&mut self) -> Vec<ArxObject> {
        let mut out = Vec::new();
        while let Some(frame_bytes) = self.transport.try_receive() {
            if frame_bytes.len() < self.cfg.header_len + 8 + 16 { continue; }
            // Split into RadioFrame (we cannot infer header len on wire beyond minimum)
            let header_min = 8 + self.cfg.header_len; // sec header + declared header
            if frame_bytes.len() < header_min { continue; }
            let header = frame_bytes[..header_min].to_vec();
            let payload = frame_bytes[header_min..].to_vec();
            let rf = RadioFrame { header, payload };
            if let Some(opened) = open_frame(self.cfg, &rf, &self.mac, &mut self.replay) {
                let mut objs = unpack_objects_from_frames(&[opened]);
                out.append(&mut objs);
            }
        }
        out
    }
}

impl MobileBinder<super::transport::QueueTransport> {
    /// Testing helper: drain all frames sent by `self` into `other`'s incoming queue
    pub fn drain_sent_into(&mut self, other: &mut MobileBinder<super::transport::QueueTransport>) {
        let frames = std::mem::take(&mut self.transport.sent_frames);
        for f in frames { other.transport.push_incoming(f); }
    }
}


