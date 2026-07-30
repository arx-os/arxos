//! Bounded root object closures for sync (checkpoint-limited history).

use std::collections::BTreeSet;

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectBody};
use crate::store::ObjectStore;

use super::RootBody;

/// Options for collecting a root object closure.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct ClosureOptions {
    /// When true, missing domain/index objects are listed in
    /// [`ClosureResult::missing`] instead of failing the call.
    /// Default is false (fail closed).
    pub allow_partial: bool,
}

/// Result of collecting the objects required to materialize and query a root.
#[derive(Debug, Clone)]
pub struct ClosureResult {
    /// Present objects as `(cid, canonical bytes)`.
    pub blobs: Vec<(Cid, Vec<u8>)>,
    /// CIDs that were required but not found in the store (empty when complete).
    pub missing: Vec<Cid>,
}

/// Computes the complete deterministic closure of objects belonging to a Root
/// up to the nearest checkpoint root in history.
///
/// Fail closed: any missing active object or spatial-index node is an error.
pub fn get_root_closure_blobs(store: &ObjectStore, root_cid: &Cid) -> Result<Vec<(Cid, Vec<u8>)>> {
    let result = get_root_closure_blobs_with_options(store, root_cid, &ClosureOptions::default())?;
    Ok(result.blobs)
}

/// Like [`get_root_closure_blobs`], with control over partial closures.
pub fn get_root_closure_blobs_with_options(
    store: &ObjectStore,
    root_cid: &Cid,
    opts: &ClosureOptions,
) -> Result<ClosureResult> {
    let mut visited = BTreeSet::new();
    let mut out = Vec::new();
    let mut missing = BTreeSet::new();

    // 1. Walk root chain backwards to collect Root CIDs and active domain objects
    //    up to the nearest checkpoint.
    let mut active_objects = BTreeSet::new();
    let mut removed_set = BTreeSet::new();
    let mut current_prev = Some(*root_cid);

    while let Some(cid) = current_prev {
        if !visited.insert(cid) {
            break;
        }
        let bytes = store.get_bytes(&cid)?;
        out.push((cid, bytes.clone()));

        let obj = Object::from_canonical_bytes(&bytes)?;
        let root = RootBody::from_object(&obj)?;

        if let Some(ref legacy_set) = root.objects {
            for item in legacy_set {
                if !removed_set.contains(item) {
                    active_objects.insert(*item);
                }
            }
            break;
        }

        for item in &root.added {
            if !removed_set.contains(item) {
                active_objects.insert(*item);
            }
        }
        for item in &root.removed {
            removed_set.insert(*item);
        }

        current_prev = root.previous_root;
    }

    // 2. Domain objects (fail closed unless allow_partial).
    for cid in &active_objects {
        if !visited.insert(*cid) {
            continue;
        }
        match store.get_bytes(cid) {
            Ok(bytes) => out.push((*cid, bytes)),
            Err(Error::NotFound(_)) => {
                missing.insert(*cid);
            }
            Err(e) => return Err(e),
        }
    }

    // 3. Spatial index nodes from the tip root.
    let root_bytes = store.get_bytes(root_cid)?;
    let root_obj = Object::from_canonical_bytes(&root_bytes)?;
    let root_body = RootBody::from_object(&root_obj)?;
    if let Some(si_root) = root_body.spatial_index_root {
        let mut stack = vec![si_root];
        while let Some(node_cid) = stack.pop() {
            if !visited.insert(node_cid) {
                continue;
            }
            match store.get_bytes(&node_cid) {
                Ok(bytes) => {
                    out.push((node_cid, bytes.clone()));
                    if let Ok(obj) = Object::from_canonical_bytes(&bytes) {
                        if let ObjectBody::SpatialIndexNode(node) = obj.body {
                            stack.extend(node.children);
                        }
                    }
                }
                Err(Error::NotFound(_)) => {
                    missing.insert(node_cid);
                }
                Err(e) => return Err(e),
            }
        }
    }

    let missing: Vec<Cid> = missing.into_iter().collect();
    if !missing.is_empty() && !opts.allow_partial {
        let preview: Vec<String> = missing.iter().take(8).map(|c| c.to_string()).collect();
        return Err(Error::NotFound(format!(
            "incomplete root closure for {root_cid}: missing {} object(s), e.g. {}",
            missing.len(),
            preview.join(", ")
        )));
    }

    Ok(ClosureResult {
        blobs: out,
        missing,
    })
}

/// Ensure every CID in `active` is present in `store`.
///
/// Returns the list of missing CIDs (empty when complete).
pub fn missing_active_objects(store: &ObjectStore, active: &BTreeSet<Cid>) -> Result<Vec<Cid>> {
    let mut missing = Vec::new();
    for cid in active {
        if !store.contains(cid) {
            missing.push(*cid);
        }
    }
    Ok(missing)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::{BuildingBody, BuildingId, Object};
    use crate::root::RootBuilder;
    use std::collections::BTreeMap;
    use tempfile::tempdir;

    #[test]
    fn closure_fails_closed_on_missing_object() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();
        let ghost = Cid::from_canonical_bytes(b"missing-from-store");
        let mut objects = BTreeSet::new();
        objects.insert(bc);
        objects.insert(ghost);

        let (root_obj, root_cid) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&root_obj).unwrap();

        let err = get_root_closure_blobs(&store, &root_cid).unwrap_err();
        assert!(matches!(err, Error::NotFound(_)), "{err:?}");

        let partial = get_root_closure_blobs_with_options(
            &store,
            &root_cid,
            &ClosureOptions {
                allow_partial: true,
            },
        )
        .unwrap();
        assert!(partial.missing.contains(&ghost));
        assert!(!partial.blobs.is_empty());
    }
}
