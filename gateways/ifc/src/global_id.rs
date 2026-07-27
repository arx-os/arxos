//! IFC GlobalId (22-char compressed GUID) derived from Arxos CIDs.

use arxos_core::Cid;

/// Base64-like IFC compression alphabet (IFC2x3/IFC4).
const IFC_CHARS: &[u8] =
    b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";

/// Produce a stable 22-character IFC GlobalId from a CID.
///
/// This is not a standard UUID compression of a random GUID; it is a
/// deterministic encoding of the CID digest so re-exports stay stable.
pub fn global_id_from_cid(cid: &Cid) -> String {
    let bytes = cid.as_bytes();
    // Take 16 bytes for 128-bit worth of material.
    let mut n = [0u8; 16];
    n.copy_from_slice(&bytes[..16]);
    compress_guid(&n)
}

fn compress_guid(guid: &[u8; 16]) -> String {
    // Pack 128 bits into 22 IFC chars (6 bits each, 22*6=132 >= 128).
    let mut bits: u128 = 0;
    for (i, b) in guid.iter().enumerate() {
        bits |= (*b as u128) << (8 * (15 - i));
    }
    let mut out = String::with_capacity(22);
    for i in (0..22).rev() {
        let shift = i * 6;
        let idx = ((bits >> shift) & 0x3f) as usize;
        out.push(IFC_CHARS[idx.min(63)] as char);
    }
    out
}

/// Best-effort reverse: not bijective to original UUID; used only as opaque tag.
#[allow(dead_code)]
pub fn cid_hint_from_global_id(gid: &str) -> Option<String> {
    if gid.len() != 22 {
        return None;
    }
    Some(format!("ifc:{gid}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stable_global_id() {
        let c = Cid::from_canonical_bytes(b"test-cid-material");
        let a = global_id_from_cid(&c);
        let b = global_id_from_cid(&c);
        assert_eq!(a, b);
        assert_eq!(a.len(), 22);
    }
}
