//! Building-head advertisements and serve-side CAS filtering.

use std::str::FromStr;

use arxos_core::repository::BuildingRepository;
use arxos_core::Cid;

use crate::error::{NetError, Result};
use crate::protocol::BuildingHeadAd;

/// Build mDNS / Hello advertisements from a local store path.
///
/// Read-only: does not acquire the exclusive store write lock.
pub fn building_ads_from_store(store_path: &std::path::Path) -> Result<Vec<BuildingHeadAd>> {
    let list = BuildingRepository::list_buildings(store_path)?;
    let store = arxos_core::store::ObjectStore::open(store_path)?;
    let mut ads = Vec::new();
    for rec in list {
        let Some(root) = rec.head_root else {
            continue;
        };
        let object_count = store
            .get(&root)
            .ok()
            .and_then(|obj| arxos_core::root::RootBody::from_object(&obj).ok().cloned())
            .and_then(|body| body.materialize_active_objects(&store).ok())
            .map(|set| set.len() as u64)
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

/// True if `cid` is an advertised head or a member of an advertised head's closure.
pub fn cid_in_advertised_closures(
    store_path: &std::path::Path,
    cid: &str,
    ads: &[BuildingHeadAd],
) -> Result<bool> {
    if ads.iter().any(|a| a.root_cid == cid) {
        return Ok(true);
    }
    let store = arxos_core::store::ObjectStore::open(store_path)?;
    let want = Cid::from_str(cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    for ad in ads {
        let root = Cid::from_str(&ad.root_cid).map_err(|e| NetError::Protocol(e.to_string()))?;
        let result = arxos_core::root::get_root_closure_blobs_with_options(
            &store,
            &root,
            &arxos_core::root::ClosureOptions {
                allow_partial: true,
                include_blobs: true,
            },
        )
        .map_err(|e| NetError::Core(e.to_string()))?;
        if result.blobs.iter().any(|(c, _)| *c == want) {
            return Ok(true);
        }
    }
    Ok(false)
}

/// Serve helper: load object bytes for protocol handlers.
///
/// Only CIDs in the closure of a currently advertised building head are
/// returned. Other CAS slots look missing (do not leak existence).
pub fn serve_get_object(store_path: &std::path::Path, cid: &str) -> Result<Option<Vec<u8>>> {
    let ads = building_ads_from_store(store_path)?;
    if !cid_in_advertised_closures(store_path, cid, &ads)? {
        return Ok(None);
    }
    let store = arxos_core::store::ObjectStore::open(store_path)?;
    let cid = Cid::from_str(cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    match store.get_bytes(&cid) {
        Ok(b) => Ok(Some(b)),
        Err(arxos_core::Error::NotFound(_)) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// Serve helper: full root closure for protocol handlers.
pub fn serve_root_closure(
    store_path: &std::path::Path,
    root_cid: &str,
) -> Result<Vec<crate::protocol::ObjectBlob>> {
    serve_root_closure_with_options(store_path, root_cid, true)
}

/// Serve helper: root closure with optional blob exclusion (metadata-first).
pub fn serve_root_closure_with_options(
    store_path: &std::path::Path,
    root_cid: &str,
    include_blobs: bool,
) -> Result<Vec<crate::protocol::ObjectBlob>> {
    use arxos_core::root::{get_root_closure_blobs_with_options, ClosureOptions};

    let ads = building_ads_from_store(store_path)?;
    if !ads.iter().any(|a| a.root_cid == root_cid) {
        return Err(NetError::Protocol("root is not an advertised head".into()));
    }

    let store = arxos_core::store::ObjectStore::open(store_path)?;
    let root = Cid::from_str(root_cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    let result = get_root_closure_blobs_with_options(
        &store,
        &root,
        &ClosureOptions {
            allow_partial: false,
            include_blobs,
        },
    )
    .map_err(|e| NetError::Core(e.to_string()))?;
    let mut total = 0usize;
    let out: Vec<crate::protocol::ObjectBlob> = result
        .blobs
        .into_iter()
        .map(|(cid, bytes)| {
            total = total.saturating_add(bytes.len());
            crate::protocol::ObjectBlob {
                cid: cid.to_string(),
                bytes,
            }
        })
        .collect();
    if total > crate::protocol::MAX_MESSAGE_BYTES as usize {
        return Err(NetError::Protocol(format!(
            "root closure {} bytes exceeds max frame {}",
            total,
            crate::protocol::MAX_MESSAGE_BYTES
        )));
    }
    Ok(out)
}
