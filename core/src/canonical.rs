//! Canonical CBOR serialization for content addressing.
//!
//! Encoding rules for Arxos Phase 0:
//! - Serde structs use field declaration order (stable).
//! - Maps use `BTreeMap` so keys are ordered.
//! - Sets use `BTreeSet` so members are ordered.
//! - ciborium definite-length CBOR encoding.
//!
//! The CID of a value is BLAKE3-256 over these exact bytes.

use serde::{de::DeserializeOwned, Serialize};

use crate::cid::Cid;
use crate::error::{Error, Result};

/// Serialize a value to canonical CBOR bytes.
pub fn to_canonical_cbor<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    let mut buf = Vec::new();
    ciborium::into_writer(value, &mut buf)
        .map_err(|e| Error::Serialization(e.to_string()))?;
    Ok(buf)
}

/// Deserialize a value from CBOR bytes.
pub fn from_cbor<T: DeserializeOwned>(bytes: &[u8]) -> Result<T> {
    ciborium::from_reader(bytes).map_err(|e| Error::Deserialization(e.to_string()))
}

/// Compute the CID of a value from its canonical CBOR encoding.
pub fn cid_of<T: Serialize>(value: &T) -> Result<Cid> {
    let bytes = to_canonical_cbor(value)?;
    Ok(Cid::from_canonical_bytes(&bytes))
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde::{Deserialize, Serialize};
    use std::collections::BTreeMap;

    #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
    struct Sample {
        a: u32,
        b: String,
        m: BTreeMap<String, u64>,
    }

    #[test]
    fn canonical_bytes_stable() {
        let mut m = BTreeMap::new();
        m.insert("z".into(), 1);
        m.insert("a".into(), 2);
        let s = Sample {
            a: 42,
            b: "hello".into(),
            m,
        };
        let b1 = to_canonical_cbor(&s).unwrap();
        let b2 = to_canonical_cbor(&s).unwrap();
        assert_eq!(b1, b2);

        let decoded: Sample = from_cbor(&b1).unwrap();
        assert_eq!(decoded, s);

        let c1 = cid_of(&s).unwrap();
        let c2 = cid_of(&s).unwrap();
        assert_eq!(c1, c2);
    }

    #[test]
    fn map_key_order_does_not_affect_cid() {
        let mut m1 = BTreeMap::new();
        m1.insert("b".into(), 1u64);
        m1.insert("a".into(), 2u64);
        let mut m2 = BTreeMap::new();
        m2.insert("a".into(), 2u64);
        m2.insert("b".into(), 1u64);
        let s1 = Sample {
            a: 1,
            b: "x".into(),
            m: m1,
        };
        let s2 = Sample {
            a: 1,
            b: "x".into(),
            m: m2,
        };
        assert_eq!(cid_of(&s1).unwrap(), cid_of(&s2).unwrap());
    }
}
