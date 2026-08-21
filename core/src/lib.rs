//! # arxos-core
//!
//! Content-addressed object model, Merkle roots, local CAS store, ed25519
//! integrity signatures, and contributor scoring for the Arxos DePIN data plane.
//!
//! Economic settlement is **fiat** (not tokens / chain mint). Scoring produces
//! points for contribution attribution; the core never embeds money in CIDs.
//!
//! ## Surface
//! - Canonical CBOR serialization + BLAKE3 CIDs
//! - Object header/body model and typed payloads
//! - Root (repository state) with ed25519 multi-author signatures
//! - Local content-addressed file store
//! - Deterministic contributor scoring (`scoring`)
//! - Optional UniFFI bindings for Swift

// Module-level docs are required; per-field docs are encouraged but not denied in Phase 0.
#![allow(missing_docs)]

pub mod attest;
pub mod capture;
pub mod canonical;
pub mod cid;
pub mod crypto;
pub mod entity;
pub mod error;
pub mod merge;
pub mod object;
pub mod repository;
pub mod root;
pub mod schema;
pub mod scoring;
pub mod spatial;
pub mod store;
pub mod verify;
pub mod working_set;



pub use attest::{
    AppAttestVerifier, AttestationKind, AttestationStatement, AttestationVerdict,
    AttestationVerifier, DefaultAttestationVerifier, MockAttestationVerifier,
};
pub use capture::{
    annotation_object, mesh_object, point_cloud_object, pose_from_column_major_matrix, put_mesh,
    put_point_cloud_chunk, resolve_mesh_indices, resolve_mesh_vertices, resolve_point_bytes,
    space_object, world_aabb_from_transform_and_dimensions, AnnotationCapture, MeshCapture,
    PointCloudCapture, SpaceCapture,
};
pub use cid::Cid;
pub use crypto::{
    read_secret_32, write_secret_bytes, AuthorSignature, Keypair, PublicKey, Signature,
};
pub use entity::{
    collapse_active_set, collapse_active_set_preferring, entity_id_of, find_entity_versions,
    CollapseResult, EntityId,
};
pub use scoring::{
    attribute_object, score_cids, score_cids_with_policy, score_contributions,
    score_contributions_with_policy, score_root, score_root_with_policy, Contribution,
    ContributorScore, ScoreReport, ScoreWeights, ScoringPolicy, DEFAULT_POLICY_VERSION,
};
pub use error::{Error, Result};
pub use merge::{
    find_common_ancestor, merge_roots, plan_merge, three_way_object_set, MergePlan, MergeResult,
    ANNOTATION_DEDUP_M,
};
pub use object::{
    AnnotationBody, BlobBody, BuildingBody, BuildingId, FloorBody, Object, ObjectBody,
    ObjectHeader, ObjectType, Pose, SCHEMA_VERSION,
};
pub use object::Aabb;
pub use repository::{
    AdoptOptions, BuildingRecord, BuildingRepository, CaptureResult, CommitResult, ObjectIngest,
};
pub use root::{
    distance_from_checkpoint, get_root_closure_blobs, get_root_closure_blobs_with_options,
    missing_active_objects, resolve_controller_keys, should_checkpoint_at, should_emit_checkpoint,
    ClosureOptions, ClosureResult, ClosureView, RootBody, RootBuilder, RootClosure,
    CHECKPOINT_INTERVAL,
};
pub use spatial::{QueryVolume, SpatialEntry, SpatialHit};
pub use store::{
    atomic_write, is_tmp_name, unique_tmp_path, MemObjectStore, ObjectRead, ObjectStore,
    ObjectWrite, WriteGuard, MAX_OBJECT_BYTES, STORE_LOCK_FILE,
};
pub use verify::{
    verify_object_canonicalization, verify_root_body_determinism, verify_root_transition, Finding,
    Severity, VerificationReport,
};
pub use working_set::{AnnotationHit, WorkingSet};

/// Library version string.
///
/// Returns owned `String` so the signature matches the UniFFI surface.
pub fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// Phase 0 hello for UniFFI / smoke tests.
pub fn hello(name: String) -> String {
    format!("Hello, {name} — Arxos core {}", version())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;
    use std::collections::BTreeSet;
    use tempfile::tempdir;

    #[test]
    fn hello_smoke() {
        let s = hello("Phase0".into());
        assert!(s.contains("Phase0"));
        assert!(s.contains("0.1.0"));
    }

    #[test]
    fn end_to_end_object_root_store() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let building_id = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: building_id.clone(),
                name: Some("Demo Hall".into()),
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1_700_000_200,
        );
        let building_cid = store.put(&building).unwrap();

        let mut annotation = Object::new_with_created(
            ObjectBody::Annotation(AnnotationBody {
                text: Some("Main electrical room".into()),
                transcript: None,
                media_ref: None,
                pose: Some(Pose::default()),
                space: None,
                properties: BTreeMap::new(),
            }),
            1_700_000_201,
        );
        annotation.sign(&kp).unwrap();
        let ann_cid = store.put(&annotation).unwrap();

        let mut objects = BTreeSet::new();
        objects.insert(building_cid);
        objects.insert(ann_cid);

        let (root_obj, root_cid) = RootBuilder::new(building_id, 1_700_000_202)
            .objects(objects)
            .message("phase0 e2e")
            .build_signed(&kp)
            .unwrap();

        let stored_root = store.put(&root_obj).unwrap();
        assert_eq!(stored_root, root_cid);

        let loaded = store.get(&root_cid).unwrap();
        let root = RootBody::from_object(&loaded).unwrap();
        root.verify_authors().unwrap();
        assert_eq!(root.materialize_active_objects(&store).unwrap().len(), 2);
    }
}
