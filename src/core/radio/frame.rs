//! Unified radio frame handling for RF backends (Meshtastic LoRa, SDR, etc.)
//!
//! Provides a single source of truth for MTU configuration, frame headers,
//! fragmentation/defragmentation, and packing 13-byte `ArxObject`s into frames.

#![deny(clippy::pedantic, clippy::nursery)]
#![allow(clippy::module_name_repetitions, clippy::missing_errors_doc, clippy::missing_panics_doc)]
use crate::ArxObject;

/// Radio profiles with predefined MTUs and header sizes
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RadioProfile {
    /// Meshtastic/LoRa typical payload budget
    MeshtasticLoRa,
    /// SDR backhaul with larger frames
    SDR,
    /// Custom profile (set via `FrameConfig`)
    Custom,
}

/// Frame configuration used by packers/unpackers
#[derive(Debug, Clone, Copy)]
pub struct FrameConfig {
    /// Maximum payload bytes available per frame (including header)
    pub mtu_bytes: usize,
    /// Header length in bytes reserved in each frame
    pub header_len: usize,
}

impl FrameConfig {
    pub fn for_profile(profile: RadioProfile) -> Self {
        match profile {
            RadioProfile::MeshtasticLoRa => Self { mtu_bytes: 255, header_len: 4 },
            RadioProfile::SDR => Self { mtu_bytes: 1024, header_len: 8 },
            RadioProfile::Custom => Self { mtu_bytes: 255, header_len: 4 },
        }
    }

    /// Compute maximum number of 13-byte objects that fit in one frame
    pub fn objects_per_frame(&self) -> usize {
        if self.mtu_bytes <= self.header_len { return 0; }
        (self.mtu_bytes - self.header_len) / ArxObject::SIZE
    }
}

/// A serialized radio frame containing a small header and variable payload
#[derive(Debug, Clone)]
pub struct RadioFrame {
    /// Backend-independent header bytes (caller populates)
    pub header: Vec<u8>,
    /// Frame payload bytes (packed objects or fragment)
    pub payload: Vec<u8>,
}

impl RadioFrame {
    pub fn total_len(&self) -> usize { self.header.len() + self.payload.len() }
}

/// Pack a slice of `ArxObject` into as many frames as needed under the MTU
pub fn pack_objects_into_frames(
    cfg: FrameConfig,
    objects: &[ArxObject],
    mk_header: impl Fn(usize, usize) -> Vec<u8>, // (frame_index, total_frames) -> header
) -> Vec<RadioFrame> {
    let per = cfg.objects_per_frame().max(1);
    let total_frames = (objects.len() + per - 1) / per;
    let mut frames = Vec::with_capacity(total_frames.max(1));

    if objects.is_empty() {
        // Produce an empty payload frame for signaling if desired
        frames.push(RadioFrame { header: mk_header(0, 1), payload: Vec::new() });
        return frames;
    }

    for (i, chunk) in objects.chunks(per).enumerate() {
        let mut payload = Vec::with_capacity(chunk.len() * ArxObject::SIZE);
        for obj in chunk {
            payload.extend_from_slice(&obj.to_bytes());
        }
        let header = mk_header(i, total_frames);
        frames.push(RadioFrame { header, payload });
    }

    frames
}

/// Unpack `ArxObject`s from a sequence of frames (no reordering). Returns
/// all objects concatenated in arrival order. Caller handles integrity/auth.
pub fn unpack_objects_from_frames(frames: &[RadioFrame]) -> Vec<ArxObject> {
    let mut objects = Vec::new();
    for frame in frames {
        let mut offset = 0usize;
        while offset + ArxObject::SIZE <= frame.payload.len() {
            let mut buf = [0u8; ArxObject::SIZE];
            buf.copy_from_slice(&frame.payload[offset..offset + ArxObject::SIZE]);
            let obj = ArxObject::from_bytes(&buf);
            objects.push(obj);
            offset += ArxObject::SIZE;
        }
    }
    objects
}


