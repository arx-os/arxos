//! Transport abstraction for object sync.
//!
//! Production: Iroh QUIC. Tests: in-process [`crate::memory::MemoryMesh`].

use std::future::Future;
use std::pin::Pin;

use crate::error::Result;
use crate::protocol::{BuildingHeadAd, ObjectBlob};

/// Opaque peer handle (endpoint id hex, memory node id, etc.).
pub type PeerId = String;

/// Async trait object style for dyn-friendly transports.
pub type BoxFuture<'a, T> = Pin<Box<dyn Future<Output = T> + Send + 'a>>;

/// Capability to talk Arxos sync protocol to peers.
pub trait ObjectTransport: Send + Sync {
    /// Local peer id.
    fn local_peer_id(&self) -> PeerId;

    /// Buildings this node currently advertises.
    fn advertise_buildings(&self) -> BoxFuture<'_, Result<Vec<BuildingHeadAd>>>;

    /// Fetch a single object by CID string from a peer.
    fn fetch_object<'a>(
        &'a self,
        peer: &'a PeerId,
        cid: &'a str,
    ) -> BoxFuture<'a, Result<Option<Vec<u8>>>>;

    /// Fetch a root and all members the peer holds.
    fn fetch_root_closure<'a>(
        &'a self,
        peer: &'a PeerId,
        root_cid: &'a str,
    ) -> BoxFuture<'a, Result<Vec<ObjectBlob>>>;

    /// Optional: notify peer of a new root (best-effort).
    fn announce_root<'a>(
        &'a self,
        peer: &'a PeerId,
        building_id: &'a str,
        root_cid: &'a str,
        object_count: u64,
        message: Option<String>,
    ) -> BoxFuture<'a, Result<()>>;
}
