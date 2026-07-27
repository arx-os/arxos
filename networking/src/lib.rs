//! Arxos networking (Iroh) — scaffold for Phase 2.
//!
//! Phase 0 intentionally ships a stub so the workspace builds cleanly.
//! Phase 2 will add: announce roots via gossip, fetch objects by CID,
//! direct connections + relays, and mDNS local discovery.

#![allow(missing_docs)]

/// Placeholder until Iroh integration lands in Phase 2.
pub fn status() -> &'static str {
    "arxos-networking: stub (Phase 2)"
}

#[cfg(test)]
mod tests {
    #[test]
    fn stub() {
        assert!(super::status().contains("Phase 2"));
    }
}
