//! High-level sync: pull root closures into a local building repository.

use std::str::FromStr;

use arxos_core::object::BuildingId;
use arxos_core::repository::{BuildingRepository, CommitResult};
use arxos_core::Cid;

use crate::error::{NetError, Result};
use crate::protocol::BuildingHeadAd;
use crate::transport::{ObjectTransport, PeerId};

/// Result of pulling a root from a peer.
#[derive(Debug, Clone)]
pub struct PullResult {
    pub root_cid: Cid,
    pub objects_stored: u64,
    pub objects_skipped_existing: u64,
    pub adopted: Option<CommitResult>,
}

/// Build mDNS / Hello advertisements from a local store path.
pub fn building_ads_from_store(store_path: &std::path::Path) -> Result<Vec<BuildingHeadAd>> {
    let list = BuildingRepository::list_buildings(store_path)?;
    let mut ads = Vec::new();
    for rec in list {
        let Some(root) = rec.head_root else {
            continue;
        };
        let object_count = BuildingRepository::open(store_path, &rec.building_id)
            .ok()
            .and_then(|r| r.load_head_root().ok().flatten())
            .map(|b| b.objects.len() as u64)
            .unwrap_or(0);
        ads.push(BuildingHeadAd {
            building_id: rec.building_id.to_string(),
            root_cid: root.to_string(),
            name: rec.name,
            object_count,
        });
    }
    Ok(ads)
}

/// Pull a root closure from `peer` into `store_path`, optionally adopting as head.
pub async fn pull_root<T: ObjectTransport + ?Sized>(
    transport: &T,
    peer: &PeerId,
    store_path: &std::path::Path,
    root_cid: &str,
    building_id: Option<&str>,
    set_head: bool,
) -> Result<PullResult> {
    let blobs = transport.fetch_root_closure(peer, root_cid).await?;
    if blobs.is_empty() {
        return Err(NetError::ObjectMissing(root_cid.to_string()));
    }

    // Ensure store exists.
    let _ = arxos_core::store::ObjectStore::open(store_path)?;

    let mut stored = 0u64;
    let mut skipped = 0u64;
    let mut resolved_building: Option<BuildingId> = building_id
        .map(BuildingId::from_str)
        .transpose()
        .map_err(|e| NetError::Core(e.to_string()))?;

    for blob in &blobs {
        let cid = Cid::from_str(&blob.cid).map_err(|e| NetError::Protocol(e.to_string()))?;
        // Integrity: recompute CID from bytes.
        let actual = Cid::from_canonical_bytes(&blob.bytes);
        if actual != cid {
            return Err(NetError::Protocol(format!(
                "CID mismatch for {}: wire={} actual={}",
                blob.cid, cid, actual
            )));
        }
        let store = arxos_core::store::ObjectStore::open(store_path)?;
        if store.contains(&cid) {
            skipped += 1;
            continue;
        }
        store.put_bytes(&blob.bytes)?;
        stored += 1;

        // Learn building_id from root object if not provided.
        if resolved_building.is_none() {
            if let Ok(obj) = arxos_core::Object::from_canonical_bytes(&blob.bytes) {
                if let Ok(root) = arxos_core::root::RootBody::from_object(&obj) {
                    resolved_building = Some(root.building_id.clone());
                }
            }
        }
    }

    let root = Cid::from_str(root_cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    let adopted = if set_head {
        let bid = resolved_building.ok_or_else(|| {
            NetError::Protocol("could not determine building_id for adopt".into())
        })?;
        let mut repo = BuildingRepository::open_or_follow(store_path, &bid, None)?;
        Some(repo.adopt_root(root)?)
    } else {
        None
    };

    Ok(PullResult {
        root_cid: root,
        objects_stored: stored,
        objects_skipped_existing: skipped,
        adopted,
    })
}

/// Pull whatever head a peer advertises for `building_id`.
pub async fn pull_building_head<T: ObjectTransport + ?Sized>(
    transport: &T,
    peer: &PeerId,
    store_path: &std::path::Path,
    building_id: &str,
    set_head: bool,
) -> Result<PullResult> {
    // Prefer Hello ads — fetch via a lightweight GetRoot if we know the cid.
    // Memory/Iroh peers expose buildings through advertise on local side; for remote,
    // fetch Hello by doing a root pull when root_cid is known by caller.
    // Here we scan local knowledge: caller should pass peer that announced via mDNS.
    // For transport-level: try announce list from peer by fetching a known root only.
    //
    // Convention: peer id may be paired with BuildingHeadAd from discovery.
    // This function requires the peer's advertise_buildings if peer == local mirror;
    // for remote Iroh we use discovery service separately.
    let ads = transport.advertise_buildings().await?;
    // When asking a remote, advertise_buildings is local. So this helper is for
    // discovery-provided root_cid. Prefer pull_root when root known.
    let ad = ads
        .into_iter()
        .find(|a| a.building_id == building_id)
        .ok_or_else(|| {
            NetError::PeerNotFound(format!(
                "no advertised head for building {building_id} on local ads; pass root_cid"
            ))
        })?;
    pull_root(
        transport,
        peer,
        store_path,
        &ad.root_cid,
        Some(building_id),
        set_head,
    )
    .await
}

/// Serve helper: load object bytes for protocol handlers.
pub fn serve_get_object(store_path: &std::path::Path, cid: &str) -> Result<Option<Vec<u8>>> {
    let store = arxos_core::store::ObjectStore::open(store_path)?;
    let cid = Cid::from_str(cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    match store.get_bytes(&cid) {
        Ok(b) => Ok(Some(b)),
        Err(arxos_core::Error::NotFound(_)) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// Serve helper: root closure for protocol handlers.
pub fn serve_root_closure(
    store_path: &std::path::Path,
    root_cid: &str,
) -> Result<Vec<crate::protocol::ObjectBlob>> {
    let store = arxos_core::store::ObjectStore::open(store_path)?;
    let root = Cid::from_str(root_cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    // Temporary repo handle isn't required — use store + root parse.
    let root_bytes = match store.get_bytes(&root) {
        Ok(b) => b,
        Err(arxos_core::Error::NotFound(_)) => {
            return Err(NetError::ObjectMissing(root_cid.to_string()));
        }
        Err(e) => return Err(e.into()),
    };
    let obj = arxos_core::Object::from_canonical_bytes(&root_bytes)?;
    let body = arxos_core::root::RootBody::from_object(&obj)?;
    let mut out = vec![crate::protocol::ObjectBlob {
        cid: root.to_string(),
        bytes: root_bytes,
    }];
    for cid in &body.objects {
        if cid == &root {
            continue;
        }
        if let Ok(bytes) = store.get_bytes(cid) {
            out.push(crate::protocol::ObjectBlob {
                cid: cid.to_string(),
                bytes,
            });
        }
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory::MemoryMesh;
    use crate::protocol::BuildingHeadAd;
    use arxos_core::capture::AnnotationCapture;
    use arxos_core::object::Pose;
    use arxos_core::repository::BuildingRepository;
    use tempfile::tempdir;

    #[tokio::test]
    async fn two_device_pull_root() {
        let mesh = MemoryMesh::new();
        let dir_a = tempdir().unwrap();
        let dir_b = tempdir().unwrap();

        // Device A: capture and commit
        let mut repo_a =
            BuildingRepository::init(dir_a.path(), Some("Site A".into()), None).unwrap();
        let bid = repo_a.building_id().clone();
        repo_a
            .capture_annotation(&AnnotationCapture::new(
                "from device A",
                Pose {
                    position: [1.0, 1.0, 1.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ))
            .unwrap();
        let commit = repo_a.commit(Some("scan a".into())).unwrap();
        let root = commit.root_cid.to_string();

        let node_a = mesh
            .attach(
                repo_a.store().clone(),
                vec![BuildingHeadAd {
                    building_id: bid.to_string(),
                    root_cid: root.clone(),
                    name: Some("Site A".into()),
                    object_count: commit.object_count,
                }],
            )
            .unwrap();

        // Device B: empty follow
        let _repo_b =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Site A".into())).unwrap();
        let node_b = mesh
            .attach(arxos_core::store::ObjectStore::open(dir_b.path()).unwrap(), vec![])
            .unwrap();

        let pull = pull_root(
            &node_b,
            node_a.peer_id(),
            dir_b.path(),
            &root,
            Some(bid.as_str()),
            true,
        )
        .await
        .unwrap();

        assert!(pull.objects_stored >= 2);
        assert!(pull.adopted.is_some());
        assert_eq!(pull.adopted.unwrap().root_cid, commit.root_cid);

        let mut repo_b2 = BuildingRepository::open(dir_b.path(), &bid).unwrap();
        assert_eq!(repo_b2.head_root(), Some(commit.root_cid));
        let hits = repo_b2
            .annotations_near(
                &Pose {
                    position: [1.0, 1.0, 1.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
                2.0,
            )
            .unwrap();
        assert_eq!(hits.len(), 1);
        assert_eq!(hits[0].text, "from device A");
    }
}
