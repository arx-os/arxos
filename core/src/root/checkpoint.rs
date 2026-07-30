//! Checkpoint policy for delta roots.

use std::collections::BTreeSet;

use crate::cid::Cid;
use crate::error::Result;
use crate::store::ObjectStore;

use super::RootBody;

/// Number of consecutive delta commits after which a full-set checkpoint is required.
pub const CHECKPOINT_INTERVAL: u32 = 50;

/// True when this root serializes the full active object set (checkpoint / genesis).
pub fn is_checkpoint_body(root: &RootBody) -> bool {
    root.objects.is_some()
}

/// Walk from `start` (a previous root tip) toward history and count consecutive
/// non-checkpoint roots until a checkpoint (or chain end / cycle) is hit.
///
/// Does not count the checkpoint itself. Broken / missing links stop the walk.
pub fn distance_from_checkpoint(store: &ObjectStore, start: Option<Cid>) -> Result<u32> {
    let Some(mut current) = start else {
        return Ok(0);
    };
    let mut dist = 0u32;
    let mut visited = BTreeSet::new();
    loop {
        if !visited.insert(current) {
            break;
        }
        let obj = match store.get(&current) {
            Ok(o) => o,
            Err(_) => break,
        };
        let root = match RootBody::from_object(&obj) {
            Ok(r) => r,
            Err(_) => break,
        };
        if is_checkpoint_body(root) {
            break;
        }
        dist = dist.saturating_add(1);
        match root.previous_root {
            Some(prev) => current = prev,
            None => break,
        }
    }
    Ok(dist)
}

/// Whether the next commit should emit a full-set checkpoint root.
///
/// - Genesis (`previous` is `None`) always checkpoints.
/// - Otherwise checkpoint when distance from the last checkpoint is
///   ≥ [`CHECKPOINT_INTERVAL`].
pub fn should_emit_checkpoint(previous: Option<Cid>, distance: u32) -> bool {
    previous.is_none() || distance >= CHECKPOINT_INTERVAL
}

/// Convenience: compute distance and decide whether to checkpoint.
pub fn should_checkpoint_at(store: &ObjectStore, previous: Option<Cid>) -> Result<bool> {
    let dist = distance_from_checkpoint(store, previous)?;
    Ok(should_emit_checkpoint(previous, dist))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::BuildingId;
    use crate::root::RootBuilder;
    use crate::store::ObjectStore;
    use tempfile::tempdir;

    #[test]
    fn genesis_should_checkpoint() {
        assert!(should_emit_checkpoint(None, 0));
        assert!(should_emit_checkpoint(None, 99));
    }

    #[test]
    fn interval_boundary() {
        let tip = Cid::from_canonical_bytes(b"tip");
        assert!(!should_emit_checkpoint(Some(tip), CHECKPOINT_INTERVAL - 1));
        assert!(should_emit_checkpoint(Some(tip), CHECKPOINT_INTERVAL));
    }

    #[test]
    fn distance_stops_at_checkpoint() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();
        let mut objects = BTreeSet::new();
        objects.insert(Cid::from_canonical_bytes(b"only"));

        let (cp, cp_cid) = RootBuilder::new(bid.clone(), 1)
            .objects(objects.clone())
            .build_signed(&kp)
            .unwrap();
        store.put(&cp).unwrap();

        let (d1, d1_cid) = RootBuilder::new(bid.clone(), 2)
            .previous_root(cp_cid)
            .added(BTreeSet::from([Cid::from_canonical_bytes(b"a")]))
            .build_signed(&kp)
            .unwrap();
        store.put(&d1).unwrap();

        let (d2, d2_cid) = RootBuilder::new(bid, 3)
            .previous_root(d1_cid)
            .added(BTreeSet::from([Cid::from_canonical_bytes(b"b")]))
            .build_signed(&kp)
            .unwrap();
        store.put(&d2).unwrap();

        assert_eq!(distance_from_checkpoint(&store, Some(cp_cid)).unwrap(), 0);
        assert_eq!(distance_from_checkpoint(&store, Some(d1_cid)).unwrap(), 1);
        assert_eq!(distance_from_checkpoint(&store, Some(d2_cid)).unwrap(), 2);
    }
}
