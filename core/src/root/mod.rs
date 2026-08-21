//! Repository root: commits a set of object CIDs for a building.
//!
//! Submodules:
//! - [`auth`] — controller authorization
//! - [`checkpoint`] — delta/checkpoint emission policy
//! - [`closure`] — bounded sync closures

mod auth;
mod checkpoint;
mod closure;

pub use auth::resolve_controller_keys;
pub use checkpoint::{
    distance_from_checkpoint, is_checkpoint_body, should_checkpoint_at, should_emit_checkpoint,
    CHECKPOINT_INTERVAL,
};
pub use closure::{
    get_root_closure_blobs, get_root_closure_blobs_with_options, missing_active_objects,
    ClosureOptions, ClosureResult, ClosureView, RootClosure,
};

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::canonical::{cid_of, to_canonical_cbor};
use crate::cid::Cid;
use crate::crypto::{AuthorSignature, Keypair};
use crate::error::{Error, Result};
use crate::object::{BuildingId, Object, ObjectBody, ObjectHeader, SCHEMA_VERSION};
use crate::store::ObjectRead;

/// Root body: the committed state of a building repository.
///
/// The CID of a Root object is the current state of the building repository.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RootBody {
    pub building_id: BuildingId,
    pub previous_root: Option<Cid>,

    /// When this root is a merge of concurrent tips, the full parent set
    /// (typically both tips). Materialization still walks `previous_root` as
    /// the linear primary parent; `merge_parents` is recorded for history and
    /// attribution. Empty for non-merge commits.
    #[serde(default, skip_serializing_if = "BTreeSet::is_empty")]
    pub merge_parents: BTreeSet<Cid>,
    
    /// Incremental added object CIDs.
    #[serde(default)]
    pub added: BTreeSet<Cid>,
    
    /// Incremental removed object CIDs.
    #[serde(default)]
    pub removed: BTreeSet<Cid>,
    
    /// Content-addressed object set for legacy full-set roots.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub objects: Option<BTreeSet<Cid>>,
    
    pub spatial_index_root: Option<Cid>,
    /// Unix timestamp in seconds.
    pub timestamp: u64,
    /// Author signatures over the unsigned root payload.
    pub authors: Vec<AuthorSignature>,
    /// Optional commit message.
    pub message: Option<String>,
}

impl RootBody {
    /// Create a new legacy-style full-set root.
    pub fn new(
        building_id: BuildingId,
        previous_root: Option<Cid>,
        objects: BTreeSet<Cid>,
        timestamp: u64,
    ) -> Self {
        Self {
            building_id,
            previous_root,
            merge_parents: BTreeSet::new(),
            added: BTreeSet::new(),
            removed: BTreeSet::new(),
            objects: Some(objects),
            spatial_index_root: None,
            timestamp,
            authors: Vec::new(),
            message: None,
        }
    }

    /// Create a new delta-style root.
    pub fn new_delta(
        building_id: BuildingId,
        previous_root: Option<Cid>,
        added: BTreeSet<Cid>,
        removed: BTreeSet<Cid>,
        timestamp: u64,
    ) -> Self {
        Self {
            building_id,
            previous_root,
            merge_parents: BTreeSet::new(),
            added,
            removed,
            objects: None,
            spatial_index_root: None,
            timestamp,
            authors: Vec::new(),
            message: None,
        }
    }

    /// Materialize the full set of active object CIDs by walking the root chain
    /// backwards (if this is a delta root) until hitting a checkpoint (legacy/checkpoint full-set root).
    ///
    /// Fail closed: a pure delta chain that never reaches a checkpoint (full-set
    /// root with `objects: Some(_)`) is rejected. Repository genesis always
    /// checkpoints; this guards hand-built or corrupted history.
    pub fn materialize_active_objects<R: ObjectRead + ?Sized>(
        &self,
        store: &R,
    ) -> Result<BTreeSet<Cid>> {
        if let Some(ref legacy_set) = self.objects {
            return Ok(legacy_set.clone());
        }

        let mut active = BTreeSet::new();
        let mut removed = BTreeSet::new();
        let mut visited = BTreeSet::new();
        let mut hit_checkpoint = false;

        // Start with this root's deltas
        for item in &self.added {
            active.insert(*item);
        }
        for item in &self.removed {
            removed.insert(*item);
        }

        let mut current_prev = self.previous_root;
        while let Some(prev_cid) = current_prev {
            if !visited.insert(prev_cid) {
                return Err(Error::Validation("cyclic root chain detected".into()));
            }
            let obj = store.get(&prev_cid)?;
            let root = RootBody::from_object(&obj)?;

            if let Some(ref legacy_set) = root.objects {
                // Checkpoint hit! Accumulate all active and stop walking.
                for item in legacy_set {
                    if !removed.contains(item) {
                        active.insert(*item);
                    }
                }
                hit_checkpoint = true;
                break;
            }

            for item in &root.added {
                if !removed.contains(item) {
                    active.insert(*item);
                }
            }
            for item in &root.removed {
                removed.insert(*item);
            }

            current_prev = root.previous_root;
        }

        if !hit_checkpoint {
            return Err(Error::Validation(
                "incomplete root chain: delta materialization requires a checkpoint ancestor \
                 (objects: Some(...)); refuse incomplete active set"
                    .into(),
            ));
        }

        Ok(active)
    }

    pub fn with_message(mut self, message: impl Into<String>) -> Self {
        self.message = Some(message.into());
        self
    }

    pub fn with_spatial_index(mut self, spatial_index_root: Cid) -> Self {
        self.spatial_index_root = Some(spatial_index_root);
        self
    }

    pub fn with_merge_parents(mut self, parents: BTreeSet<Cid>) -> Self {
        self.merge_parents = parents;
        self
    }

    /// Canonical bytes signed by authors (authors field cleared).
    pub fn signing_payload(&self) -> Result<Vec<u8>> {
        let unsigned = RootBody {
            building_id: self.building_id.clone(),
            previous_root: self.previous_root,
            merge_parents: self.merge_parents.clone(),
            added: self.added.clone(),
            removed: self.removed.clone(),
            objects: self.objects.clone(),
            spatial_index_root: self.spatial_index_root,
            timestamp: self.timestamp,
            authors: Vec::new(),
            message: self.message.clone(),
        };
        to_canonical_cbor(&unsigned)
    }

    /// Append an author signature.
    pub fn sign(&mut self, keypair: &Keypair) -> Result<()> {
        let payload = self.signing_payload()?;
        self.authors.push(AuthorSignature::create(keypair, &payload));
        Ok(())
    }


    /// Wrap as a full Object (for CAS storage).
    pub fn into_object(self, created: u64) -> Object {
        Object {
            header: ObjectHeader {
                object_type: crate::object::ObjectType::Root,
                schema_version: SCHEMA_VERSION,
                created,
                author: self.authors.first().map(|a| a.public_key),
                signature: None,
            },
            body: ObjectBody::Root(self),
        }
    }

    /// Extract RootBody from an object if it is a Root.
    pub fn from_object(obj: &Object) -> Result<&RootBody> {
        match &obj.body {
            ObjectBody::Root(r) => Ok(r),
            _ => Err(Error::Validation(format!(
                "expected root object, got {}",
                obj.header.object_type
            ))),
        }
    }
}

/// Convenience builder for creating and signing roots.
pub struct RootBuilder {
    building_id: BuildingId,
    previous_root: Option<Cid>,
    merge_parents: BTreeSet<Cid>,
    added: BTreeSet<Cid>,
    removed: BTreeSet<Cid>,
    objects: Option<BTreeSet<Cid>>,
    spatial_index_root: Option<Cid>,
    timestamp: u64,
    message: Option<String>,
}

impl RootBuilder {
    pub fn new(building_id: BuildingId, timestamp: u64) -> Self {
        Self {
            building_id,
            previous_root: None,
            merge_parents: BTreeSet::new(),
            added: BTreeSet::new(),
            removed: BTreeSet::new(),
            objects: None,
            spatial_index_root: None,
            timestamp,
            message: None,
        }
    }

    pub fn previous_root(mut self, cid: Cid) -> Self {
        self.previous_root = Some(cid);
        self
    }

    /// Record concurrent parent roots for a merge commit (in addition to `previous_root`).
    pub fn merge_parents(mut self, parents: BTreeSet<Cid>) -> Self {
        self.merge_parents = parents;
        self
    }

    pub fn objects(mut self, objects: BTreeSet<Cid>) -> Self {
        self.objects = Some(objects);
        self
    }

    pub fn added(mut self, added: BTreeSet<Cid>) -> Self {
        self.added = added;
        self
    }

    pub fn removed(mut self, removed: BTreeSet<Cid>) -> Self {
        self.removed = removed;
        self
    }

    pub fn insert(mut self, cid: Cid) -> Self {
        self.added.insert(cid);
        self
    }

    pub fn spatial_index(mut self, cid: Cid) -> Self {
        self.spatial_index_root = Some(cid);
        self
    }

    pub fn message(mut self, msg: impl Into<String>) -> Self {
        self.message = Some(msg.into());
        self
    }

    /// Build unsigned root body.
    pub fn build(self) -> RootBody {
        RootBody {
            building_id: self.building_id,
            previous_root: self.previous_root,
            merge_parents: self.merge_parents,
            added: self.added,
            removed: self.removed,
            objects: self.objects,
            spatial_index_root: self.spatial_index_root,
            timestamp: self.timestamp,
            authors: Vec::new(),
            message: self.message,
        }
    }

    /// Build, sign with keypair, and wrap as Object. Returns (object, root_cid).
    pub fn build_signed(self, keypair: &Keypair) -> Result<(Object, Cid)> {
        let created = self.timestamp;
        let mut body = self.build();
        body.sign(keypair)?;
        let obj = body.into_object(created);
        let cid = obj.cid()?;
        Ok((obj, cid))
    }
}

/// CID of a root body alone (without object envelope). Prefer object CID in store.
pub fn root_body_cid(root: &RootBody) -> Result<Cid> {
    cid_of(root)
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::BuildingId;

    #[test]
    fn root_sign_verify() {
        let kp = Keypair::generate();
        let building = BuildingId::new();
        let mut objects = BTreeSet::new();
        objects.insert(Cid::from_canonical_bytes(b"obj-a"));
        objects.insert(Cid::from_canonical_bytes(b"obj-b"));

        let (obj, cid) = RootBuilder::new(building, 1_700_000_100)
            .objects(objects)
            .message("initial scan")
            .build_signed(&kp)
            .unwrap();

        let root = RootBody::from_object(&obj).unwrap();
        root.verify_authors().unwrap();
        assert_eq!(obj.cid().unwrap(), cid);
        assert_eq!(root.objects.as_ref().unwrap().len(), 2);
    }

    #[test]
    fn root_object_set_order_independent() {
        let building = BuildingId::from("01TESTBUILDING000000000000".to_string());
        let a = Cid::from_canonical_bytes(b"aaa");
        let b = Cid::from_canonical_bytes(b"bbb");

        let mut s1 = BTreeSet::new();
        s1.insert(b);
        s1.insert(a);
        let mut s2 = BTreeSet::new();
        s2.insert(a);
        s2.insert(b);

        let r1 = RootBody::new(building.clone(), None, s1, 1);
        let r2 = RootBody::new(building, None, s2, 1);
        assert_eq!(root_body_cid(&r1).unwrap(), root_body_cid(&r2).unwrap());
    }

    #[test]
    fn materialize_delta_without_checkpoint_fails() {
        use crate::store::ObjectStore;
        use tempfile::tempdir;

        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let building = BuildingId::new();

        // Pure delta root with no previous and no objects set — incomplete chain.
        let (obj, _) = RootBuilder::new(building, 1)
            .added(BTreeSet::from([Cid::from_canonical_bytes(b"ghost")]))
            .build_signed(&kp)
            .unwrap();
        store.put(&obj).unwrap();
        let root = RootBody::from_object(&obj).unwrap();
        let err = root.materialize_active_objects(&store).unwrap_err();
        assert!(
            matches!(err, crate::error::Error::Validation(ref m) if m.contains("checkpoint")),
            "{err:?}"
        );
    }
}
