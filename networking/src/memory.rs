//! In-process multi-node mesh for deterministic tests (no sockets).

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

use arxos_core::store::ObjectStore;
use arxos_core::Cid;

use crate::error::{NetError, Result};
use crate::protocol::{BuildingHeadAd, ObjectBlob};
use crate::transport::{BoxFuture, ObjectTransport, PeerId};

static NODE_SEQ: AtomicU64 = AtomicU64::new(1);

/// Shared mesh registry of memory nodes.
#[derive(Clone, Default)]
pub struct MemoryMesh {
    inner: Arc<Mutex<HashMap<PeerId, MemoryNodeInner>>>,
}

struct MemoryNodeInner {
    store: ObjectStore,
    buildings: Vec<BuildingHeadAd>,
}

/// A single node attached to a [`MemoryMesh`].
#[derive(Clone)]
pub struct MemoryNode {
    peer_id: PeerId,
    mesh: MemoryMesh,
    store: ObjectStore,
}

impl MemoryMesh {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Register a node serving `store` with optional building ads.
    pub fn attach(
        &self,
        store: ObjectStore,
        buildings: Vec<BuildingHeadAd>,
    ) -> Result<MemoryNode> {
        let peer_id = format!("mem-{:04}", NODE_SEQ.fetch_add(1, Ordering::Relaxed));
        let mut guard = self.inner.lock().map_err(|e| NetError::Transport(e.to_string()))?;
        guard.insert(
            peer_id.clone(),
            MemoryNodeInner {
                store: store.clone(),
                buildings,
            },
        );
        Ok(MemoryNode {
            peer_id,
            mesh: self.clone(),
            store,
        })
    }

    pub fn update_buildings(&self, peer_id: &PeerId, buildings: Vec<BuildingHeadAd>) -> Result<()> {
        let mut guard = self.inner.lock().map_err(|e| NetError::Transport(e.to_string()))?;
        let node = guard
            .get_mut(peer_id)
            .ok_or_else(|| NetError::PeerNotFound(peer_id.clone()))?;
        node.buildings = buildings;
        Ok(())
    }

    pub fn peer_ids(&self) -> Result<Vec<PeerId>> {
        let guard = self.inner.lock().map_err(|e| NetError::Transport(e.to_string()))?;
        Ok(guard.keys().cloned().collect())
    }
}

impl MemoryNode {
    pub fn peer_id(&self) -> &PeerId {
        &self.peer_id
    }

    pub fn store(&self) -> &ObjectStore {
        &self.store
    }

    pub fn set_buildings(&self, buildings: Vec<BuildingHeadAd>) -> Result<()> {
        self.mesh.update_buildings(&self.peer_id, buildings)
    }

    fn with_peer<R>(&self, peer: &PeerId, f: impl FnOnce(&MemoryNodeInner) -> R) -> Result<R> {
        let guard = self
            .mesh
            .inner
            .lock()
            .map_err(|e| NetError::Transport(e.to_string()))?;
        let node = guard
            .get(peer)
            .ok_or_else(|| NetError::PeerNotFound(peer.clone()))?;
        Ok(f(node))
    }
}

impl ObjectTransport for MemoryNode {
    fn local_peer_id(&self) -> PeerId {
        self.peer_id.clone()
    }

    fn advertise_buildings(&self) -> BoxFuture<'_, Result<Vec<BuildingHeadAd>>> {
        Box::pin(async move {
            self.with_peer(&self.peer_id, |n| n.buildings.clone())
        })
    }

    fn fetch_object<'a>(
        &'a self,
        peer: &'a PeerId,
        cid: &'a str,
    ) -> BoxFuture<'a, Result<Option<Vec<u8>>>> {
        Box::pin(async move {
            let cid = Cid::parse_str(cid).map_err(|e| NetError::Protocol(e.to_string()))?;
            self.with_peer(peer, |n| match n.store.get_bytes(&cid) {
                Ok(b) => Ok(Some(b)),
                Err(arxos_core::Error::NotFound(_)) => Ok(None),
                Err(e) => Err(NetError::from(e)),
            })?
        })
    }

    fn fetch_root_closure<'a>(
        &'a self,
        peer: &'a PeerId,
        root_cid: &'a str,
    ) -> BoxFuture<'a, Result<Vec<ObjectBlob>>> {
        Box::pin(async move {
            let root = Cid::parse_str(root_cid).map_err(|e| NetError::Protocol(e.to_string()))?;
            self.with_peer(peer, |n| {
                let closure = arxos_core::root::get_root_closure_blobs(&n.store, &root)
                    .map_err(NetError::from)?;
                let out = closure
                    .into_iter()
                    .map(|(cid, bytes)| ObjectBlob {
                        cid: cid.to_string(),
                        bytes,
                    })
                    .collect();
                Ok(out)
            })?
        })
    }

    fn announce_root<'a>(
        &'a self,
        peer: &'a PeerId,
        building_id: &'a str,
        root_cid: &'a str,
        object_count: u64,
        _message: Option<String>,
    ) -> BoxFuture<'a, Result<()>> {
        Box::pin(async move {
            // Memory mesh: update the peer's advertised buildings in place.
            let mut guard = self
                .mesh
                .inner
                .lock()
                .map_err(|e| NetError::Transport(e.to_string()))?;
            let node = guard
                .get_mut(peer)
                .ok_or_else(|| NetError::PeerNotFound(peer.clone()))?;
            if let Some(ad) = node
                .buildings
                .iter_mut()
                .find(|b| b.building_id == building_id)
            {
                ad.root_cid = root_cid.to_string();
                ad.object_count = object_count;
            } else {
                node.buildings.push(BuildingHeadAd {
                    building_id: building_id.to_string(),
                    root_cid: root_cid.to_string(),
                    name: None,
                    object_count,
                });
            }
            Ok(())
        })
    }
}

/// Helper: Cid parse that maps to core Error.
trait CidParse {
    fn parse_str(s: &str) -> arxos_core::Result<Cid>;
}

impl CidParse for Cid {
    fn parse_str(s: &str) -> arxos_core::Result<Cid> {
        use std::str::FromStr;
        Cid::from_str(s)
    }
}
