//! Pull a root closure from a peer into a local building repository.

use std::str::FromStr;

use arxos_core::object::BuildingId;
use arxos_core::repository::{AdoptOptions, BuildingRepository, CommitResult, ObjectIngest};
use arxos_core::{Cid, PublicKey};

use crate::error::{NetError, Result};
use crate::transport::{ObjectTransport, PeerId};

/// Result of pulling a root from a peer.
#[derive(Debug, Clone)]
pub struct PullResult {
    pub root_cid: Cid,
    pub objects_stored: u64,
    pub objects_skipped_existing: u64,
    pub adopted: Option<CommitResult>,
}

/// Pull a root closure from `peer` into `store_path`, optionally adopting as head.
///
/// Fail closed by default if signature verification fails.
/// Full closure (including blobs) by default.
pub async fn pull_root<T: ObjectTransport + ?Sized>(
    transport: &T,
    peer: &PeerId,
    store_path: &std::path::Path,
    root_cid: &str,
    building_id: Option<&str>,
    set_head: bool,
) -> Result<PullResult> {
    pull_root_with_options(
        transport,
        peer,
        store_path,
        root_cid,
        building_id,
        set_head,
        false,
        false,
        Vec::new(),
    )
    .await
}

/// Pull a root closure with options controlling signature verification and
/// whether large blob payloads are included.
///
/// When `metadata_only` is true, the peer is asked for a closure that omits
/// `Blob` objects (skinny domain objects only). A metadata-only pull **cannot**
/// become head (`set_head` must be false); ingest stores what arrived and
/// leaves `head_root` unchanged.
pub async fn pull_root_with_options<T: ObjectTransport + ?Sized>(
    transport: &T,
    peer: &PeerId,
    store_path: &std::path::Path,
    root_cid: &str,
    building_id: Option<&str>,
    set_head: bool,
    allow_untrusted: bool,
    metadata_only: bool,
    expected_controllers: Vec<PublicKey>,
) -> Result<PullResult> {
    let blobs = if metadata_only {
        transport
            .fetch_root_closure_with_options(peer, root_cid, false)
            .await?
    } else {
        transport.fetch_root_closure(peer, root_cid).await?
    };
    if blobs.is_empty() {
        return Err(NetError::ObjectMissing(root_cid.to_string()));
    }

    // Validate CIDs and learn building_id in memory — no store writes yet.
    let mut resolved_building: Option<BuildingId> = building_id
        .map(BuildingId::from_str)
        .transpose()
        .map_err(|e| NetError::Core(e.to_string()))?;

    for blob in &blobs {
        let cid = Cid::from_str(&blob.cid).map_err(|e| NetError::Protocol(e.to_string()))?;
        let actual = Cid::from_canonical_bytes(&blob.bytes);
        if actual != cid {
            return Err(NetError::Protocol(format!(
                "CID mismatch for {}: wire={} actual={}",
                blob.cid, cid, actual
            )));
        }
        if resolved_building.is_none() {
            if let Ok(obj) = arxos_core::Object::from_canonical_bytes(&blob.bytes) {
                if let Ok(root) = arxos_core::root::RootBody::from_object(&obj) {
                    resolved_building = Some(root.building_id.clone());
                }
            }
        }
    }

    let root = Cid::from_str(root_cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    let (stored, skipped, adopted) = ingest_pulled_blobs(
        store_path,
        &blobs,
        resolved_building,
        root,
        set_head,
        allow_untrusted,
        metadata_only,
        expected_controllers,
    )?;

    Ok(PullResult {
        root_cid: root,
        objects_stored: stored,
        objects_skipped_existing: skipped,
        adopted,
    })
}

/// Write a fetched closure under the repository's exclusive store lock.
///
/// A building id is required (passed in, or parsed from a Root in the payload).
/// Anonymous CAS puts without a repository are not allowed.
pub(crate) fn ingest_pulled_blobs(
    store_path: &std::path::Path,
    blobs: &[crate::protocol::ObjectBlob],
    building_id: Option<BuildingId>,
    root: Cid,
    set_head: bool,
    allow_untrusted: bool,
    metadata_only: bool,
    expected_controllers: Vec<PublicKey>,
) -> Result<(u64, u64, Option<CommitResult>)> {
    let bid = building_id.ok_or_else(|| {
        NetError::Protocol(
            "could not determine building_id for ingest (pass building_id or include a Root in the closure)".into(),
        )
    })?;
    if set_head && metadata_only {
        return Err(NetError::Protocol(
            "refusing to adopt a metadata-only pull as head; pass --no-set-head".into(),
        ));
    }
    let mut repo = BuildingRepository::open_or_follow(store_path, &bid, None)?;
    let (stored, skipped) = put_blobs_into_repo(&repo, blobs)?;
    let adopted = if set_head {
        let opts = AdoptOptions {
            allow_untrusted,
            allow_partial: false,
            expected_controllers,
        };
        Some(repo.adopt_root_with_options(root, &opts)?)
    } else {
        None
    };
    Ok((stored, skipped, adopted))
}

fn put_blobs_into_repo<I: ObjectIngest + ?Sized>(
    repo: &I,
    blobs: &[crate::protocol::ObjectBlob],
) -> Result<(u64, u64)> {
    let mut stored = 0u64;
    let mut skipped = 0u64;
    for blob in blobs {
        let cid = Cid::from_str(&blob.cid).map_err(|e| NetError::Protocol(e.to_string()))?;
        if repo.has(&cid) {
            skipped += 1;
            continue;
        }
        repo.ingest_canonical_bytes(&blob.bytes)?;
        stored += 1;
    }
    Ok((stored, skipped))
}

/// Pull whatever head a peer advertises for `building_id`.
///
/// Fail closed by default if signature verification fails.
pub async fn pull_building_head<T: ObjectTransport + ?Sized>(
    transport: &T,
    peer: &PeerId,
    store_path: &std::path::Path,
    building_id: &str,
    set_head: bool,
) -> Result<PullResult> {
    pull_building_head_with_options(transport, peer, store_path, building_id, set_head, false).await
}

/// Pull whatever head a peer advertises with options controlling signature verification.
pub async fn pull_building_head_with_options<T: ObjectTransport + ?Sized>(
    transport: &T,
    peer: &PeerId,
    store_path: &std::path::Path,
    building_id: &str,
    set_head: bool,
    allow_untrusted: bool,
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
    pull_root_with_options(
        transport,
        peer,
        store_path,
        &ad.root_cid,
        Some(building_id),
        set_head,
        allow_untrusted,
        false,
        Vec::new(),
    )
    .await
}
