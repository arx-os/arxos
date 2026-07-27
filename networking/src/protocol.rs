//! Arxos object-sync protocol messages and framing.
//!
//! Wire format: `u32` big-endian length + CBOR body of [`Message`].
//! ALPN for Iroh QUIC: [`ARXOS_ALPN`].

use serde::{Deserialize, Serialize};

/// QUIC ALPN identifier for the Arxos sync protocol.
pub const ARXOS_ALPN: &[u8] = b"arxos/sync/1";

/// Protocol version carried in Hello.
pub const PROTOCOL_VERSION: u32 = 1;

/// Maximum message body size (64 MiB) — guards against unbounded allocations.
pub const MAX_MESSAGE_BYTES: u32 = 64 * 1024 * 1024;

/// Peer-facing building head advertisement.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BuildingHeadAd {
    pub building_id: String,
    pub root_cid: String,
    pub name: Option<String>,
    pub object_count: u64,
}

/// Application messages (request/response over bi-directional streams).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Message {
    Hello {
        protocol_version: u32,
        /// Opaque peer identity string (endpoint id hex / memory node id).
        peer_id: String,
        buildings: Vec<BuildingHeadAd>,
    },
    /// Request a single object by CID string (`b3:…`).
    GetObject {
        cid: String,
    },
    GetObjectOk {
        cid: String,
        /// Canonical CBOR object bytes.
        bytes: Vec<u8>,
    },
    GetObjectMissing {
        cid: String,
    },
    /// Request root object + all members present on the server.
    GetRootClosure {
        root_cid: String,
    },
    RootClosure {
        root_cid: String,
        /// `(cid, bytes)` pairs; root included first when present.
        objects: Vec<ObjectBlob>,
    },
    /// Advertise a new root (optional; mDNS also advertises).
    AnnounceRoot {
        building_id: String,
        root_cid: String,
        object_count: u64,
        message: Option<String>,
    },
    /// Acknowledge announce.
    Ok {
        detail: Option<String>,
    },
    Error {
        message: String,
    },
}

/// One content-addressed object payload.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObjectBlob {
    pub cid: String,
    pub bytes: Vec<u8>,
}

/// Encode a message to length-prefixed CBOR.
pub fn encode_message(msg: &Message) -> Result<Vec<u8>, String> {
    let mut body = Vec::new();
    ciborium::into_writer(msg, &mut body).map_err(|e| e.to_string())?;
    if body.len() > MAX_MESSAGE_BYTES as usize {
        return Err(format!(
            "message too large: {} > {}",
            body.len(),
            MAX_MESSAGE_BYTES
        ));
    }
    let mut out = Vec::with_capacity(4 + body.len());
    out.extend_from_slice(&(body.len() as u32).to_be_bytes());
    out.extend_from_slice(&body);
    Ok(out)
}

/// Decode one length-prefixed message from a buffer; returns message + bytes consumed.
pub fn decode_message(buf: &[u8]) -> Result<Option<(Message, usize)>, String> {
    if buf.len() < 4 {
        return Ok(None);
    }
    let len = u32::from_be_bytes([buf[0], buf[1], buf[2], buf[3]]);
    if len > MAX_MESSAGE_BYTES {
        return Err(format!("message length {len} exceeds max"));
    }
    let total = 4 + len as usize;
    if buf.len() < total {
        return Ok(None);
    }
    let msg: Message =
        ciborium::from_reader(&buf[4..total]).map_err(|e| format!("cbor decode: {e}"))?;
    Ok(Some((msg, total)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_get_object() {
        let msg = Message::GetObject {
            cid: "b3:abc".into(),
        };
        let enc = encode_message(&msg).unwrap();
        let (dec, n) = decode_message(&enc).unwrap().unwrap();
        assert_eq!(n, enc.len());
        assert_eq!(dec, msg);
    }

    #[test]
    fn incomplete_buffer() {
        let msg = Message::Ok {
            detail: Some("hi".into()),
        };
        let enc = encode_message(&msg).unwrap();
        assert!(decode_message(&enc[..3]).unwrap().is_none());
        assert!(decode_message(&enc[..enc.len() - 1]).unwrap().is_none());
    }
}
