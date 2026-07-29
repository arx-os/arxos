//! # arxos-networking
//!
//! Multi-device object sync for Arxos buildings.
//!
//! ## Design
//!
//! - **Source of truth remains CIDs** in the local CAS — networking only moves bytes.
//! - **Protocol**: length-prefixed CBOR over bi-directional streams ([`protocol`]).
//! - **Transports**:
//!   - [`memory::MemoryMesh`] — in-process, for unit/integration tests
//!   - [`iroh_node::IrohNode`] — Iroh QUIC (feature `iroh`, default)
//! - **Discovery**: mDNS on the LAN (feature `mdns`) advertising building heads
//! - **Sync**: [`sync::pull_root`] materializes a root closure and can adopt head
//!
//! ## Phase 2 scope
//!
//! Publish Root + objects, second device pull by CID, basic nearby query (via core),
//! mDNS local discovery.

#![allow(missing_docs)]

pub mod discovery;
pub mod error;
pub mod memory;
pub mod protocol;
pub mod sync;
pub mod transport;

#[cfg(feature = "iroh")]
pub mod iroh_node;

pub use discovery::{DiscoveredPeer, MdnsDiscovery, SERVICE_TYPE};
pub use error::{NetError, Result};
pub use memory::{MemoryMesh, MemoryNode};
pub use protocol::{BuildingHeadAd, Message, ObjectBlob, ARXOS_ALPN, PROTOCOL_VERSION};
pub use sync::{building_ads_from_store, pull_root, pull_root_with_options, pull_building_head, pull_building_head_with_options, PullResult};
pub use transport::{ObjectTransport, PeerId};

#[cfg(feature = "iroh")]
pub use iroh_node::IrohNode;

/// Crate status string for smoke checks.
pub fn status() -> String {
    let mut parts = vec!["arxos-networking".to_string()];
    #[cfg(feature = "iroh")]
    parts.push("iroh".into());
    #[cfg(feature = "mdns")]
    parts.push("mdns".into());
    parts.push(format!("alpn={}", String::from_utf8_lossy(ARXOS_ALPN)));
    parts.join(" ")
}

#[cfg(test)]
mod tests {
    #[test]
    fn status_smoke() {
        let s = super::status();
        assert!(s.contains("arxos-networking"));
        assert!(s.contains("arxos/sync/1"));
    }
}
