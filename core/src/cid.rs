//! Content identifiers (CIDs) based on BLAKE3-256 of canonical CBOR.

use std::fmt;
use std::str::FromStr;

use serde::{Deserialize, Deserializer, Serialize, Serializer};

use crate::error::{Error, Result};

/// Size of a BLAKE3-256 digest in bytes.
pub const CID_LEN: usize = 32;

/// String prefix for human-readable CIDs.
pub const CID_PREFIX: &str = "b3:";

/// Content identifier: BLAKE3-256 hash of canonical CBOR bytes.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Cid([u8; CID_LEN]);

impl Cid {
    /// Create a CID from a raw 32-byte BLAKE3 digest.
    pub fn from_bytes(bytes: [u8; CID_LEN]) -> Self {
        Self(bytes)
    }

    /// Compute a CID from already-canonicalized CBOR bytes.
    pub fn from_canonical_bytes(bytes: &[u8]) -> Self {
        let hash = blake3::hash(bytes);
        Self(*hash.as_bytes())
    }

    /// Raw digest bytes.
    pub fn as_bytes(&self) -> &[u8; CID_LEN] {
        &self.0
    }

    /// Hex encoding of the digest (without prefix).
    pub fn to_hex(&self) -> String {
        hex::encode(self.0)
    }

    /// First byte of the digest (for store fan-out).
    pub fn fanout_byte(&self) -> u8 {
        self.0[0]
    }
}

impl fmt::Display for Cid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}{}", CID_PREFIX, self.to_hex())
    }
}

impl fmt::Debug for Cid {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Cid({})", self)
    }
}

impl FromStr for Cid {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        let hex_part = s
            .strip_prefix(CID_PREFIX)
            .or_else(|| s.strip_prefix("b3"))
            .unwrap_or(s)
            .trim_start_matches(':');

        let bytes = hex::decode(hex_part)
            .map_err(|e| Error::InvalidCid(format!("invalid hex: {e}")))?;
        if bytes.len() != CID_LEN {
            return Err(Error::InvalidCid(format!(
                "expected {CID_LEN} bytes, got {}",
                bytes.len()
            )));
        }
        let mut arr = [0u8; CID_LEN];
        arr.copy_from_slice(&bytes);
        Ok(Cid(arr))
    }
}

impl Serialize for Cid {
    fn serialize<S: Serializer>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error> {
        // CBOR: tagged as byte string for compact binary; JSON: string form.
        if serializer.is_human_readable() {
            serializer.serialize_str(&self.to_string())
        } else {
            serializer.serialize_bytes(&self.0)
        }
    }
}

impl<'de> Deserialize<'de> for Cid {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> std::result::Result<Self, D::Error> {
        use serde::de::{self, Visitor};

        struct CidVisitor;

        impl<'de> Visitor<'de> for CidVisitor {
            type Value = Cid;

            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("a CID as 32 bytes or b3:hex string")
            }

            fn visit_bytes<E: de::Error>(self, v: &[u8]) -> std::result::Result<Cid, E> {
                if v.len() != CID_LEN {
                    return Err(E::custom(format!(
                        "CID must be {CID_LEN} bytes, got {}",
                        v.len()
                    )));
                }
                let mut arr = [0u8; CID_LEN];
                arr.copy_from_slice(v);
                Ok(Cid(arr))
            }

            fn visit_byte_buf<E: de::Error>(self, v: Vec<u8>) -> std::result::Result<Cid, E> {
                self.visit_bytes(&v)
            }

            fn visit_str<E: de::Error>(self, v: &str) -> std::result::Result<Cid, E> {
                Cid::from_str(v).map_err(E::custom)
            }

            fn visit_string<E: de::Error>(self, v: String) -> std::result::Result<Cid, E> {
                self.visit_str(&v)
            }

            fn visit_seq<A>(self, mut seq: A) -> std::result::Result<Cid, A::Error>
            where
                A: de::SeqAccess<'de>,
            {
                let mut arr = [0u8; CID_LEN];
                for (i, slot) in arr.iter_mut().enumerate() {
                    *slot = seq
                        .next_element()?
                        .ok_or_else(|| de::Error::invalid_length(i, &self))?;
                }
                if seq.next_element::<u8>()?.is_some() {
                    return Err(de::Error::invalid_length(CID_LEN + 1, &self));
                }
                Ok(Cid(arr))
            }
        }

        if deserializer.is_human_readable() {
            deserializer.deserialize_str(CidVisitor)
        } else {
            deserializer.deserialize_bytes(CidVisitor)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cid_from_bytes_roundtrip_display() {
        let c = Cid::from_canonical_bytes(b"hello arxos");
        let s = c.to_string();
        assert!(s.starts_with("b3:"));
        let parsed = Cid::from_str(&s).unwrap();
        assert_eq!(c, parsed);
    }

    #[test]
    fn cid_determinism() {
        let a = Cid::from_canonical_bytes(b"same");
        let b = Cid::from_canonical_bytes(b"same");
        assert_eq!(a, b);
        let c = Cid::from_canonical_bytes(b"different");
        assert_ne!(a, c);
    }
}
