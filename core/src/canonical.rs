//! Canonical CBOR serialization for content addressing.
//!
//! Encoding rules for Arxos Phase 0:
//! - Serde structs use field declaration order (stable).
//! - Maps use `BTreeMap` so keys are ordered.
//! - Sets use `BTreeSet` so members are ordered.
//! - ciborium definite-length CBOR encoding.
//! - Geometry floats (`Pose`, `Aabb`, `elevation_m`) follow the float policy
//!   in [`canonicalize_f64`] before CID encoding.
//!
//! The CID of a value is BLAKE3-256 over these exact bytes.
//!
//! # Float policy (CID stability)
//!
//! Stored geometry must be finite. At encode/sign/validate:
//! 1. **Reject** NaN and ±Inf (`Object::validate`, encode-time canonicalize).
//! 2. **Fold** `-0.0` → `+0.0` (IEEE signed zero is a distinct CBOR bit pattern).
//! 3. **Quaternion hemisphere**: first non-zero of `(w, x, y, z)` must be `>= 0`
//!    so `q` and `-q` share a CID.
//!
//! `to_canonical_cbor` itself is still raw serde+ciborium. Object CIDs go
//! through [`Object::to_canonical_bytes`], which applies this policy first.

use std::cmp::Ordering;

use serde::{de::DeserializeOwned, Serialize};

use crate::cid::Cid;
use crate::error::{Error, Result};

/// Fold a geometry scalar to its CID-stable form.
///
/// Rejects non-finite values. Maps `-0.0` to `+0.0`.
pub fn canonicalize_f64(v: f64) -> Result<f64> {
    if !v.is_finite() {
        return Err(Error::Validation(format!(
            "non-finite float is not allowed in content-addressed geometry ({v})"
        )));
    }
    if v == 0.0 {
        Ok(0.0)
    } else {
        Ok(v)
    }
}

/// True if `v` is finite (not NaN / ±Inf).
pub fn is_finite_f64(v: f64) -> bool {
    v.is_finite()
}

/// Total order for spatial splits: IEEE order, with NaNs sorting last and
/// equal to each other. `-0.0` compares equal to `+0.0` (IEEE).
pub fn cmp_f64(a: f64, b: f64) -> Ordering {
    match a.partial_cmp(&b) {
        Some(o) => o,
        None => match (a.is_nan(), b.is_nan()) {
            (true, true) => Ordering::Equal,
            (true, false) => Ordering::Greater,
            (false, true) => Ordering::Less,
            (false, false) => Ordering::Equal,
        },
    }
}

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

    #[test]
    fn canonicalize_f64_folds_signed_zero() {
        assert_eq!(canonicalize_f64(-0.0).unwrap().to_bits(), 0.0f64.to_bits());
        assert_eq!(canonicalize_f64(0.0).unwrap().to_bits(), 0.0f64.to_bits());
        assert_eq!(canonicalize_f64(1.5).unwrap(), 1.5);
        assert!(canonicalize_f64(f64::NAN).is_err());
        assert!(canonicalize_f64(f64::INFINITY).is_err());
        assert!(canonicalize_f64(f64::NEG_INFINITY).is_err());
    }

    #[test]
    fn cmp_f64_total_order() {
        assert_eq!(cmp_f64(-0.0, 0.0), Ordering::Equal);
        assert_eq!(cmp_f64(1.0, 2.0), Ordering::Less);
        assert_eq!(cmp_f64(f64::NAN, 1.0), Ordering::Greater);
        assert_eq!(cmp_f64(1.0, f64::NAN), Ordering::Less);
        assert_eq!(cmp_f64(f64::NAN, f64::NAN), Ordering::Equal);
    }
}
