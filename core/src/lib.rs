//! # arxos-core
//!
//! Content-addressed object model, Merkle roots, local CAS store, and crypto
//! for the Arxos lived-experience architecture.
//!
//! ## Phase 0 surface
//! - Canonical CBOR serialization + BLAKE3 CIDs
//! - Object header/body model and typed payloads
//! - Root (repository state) with ed25519 multi-author signatures
//! - Local content-addressed file store
//! - Optional UniFFI bindings for Swift

// Module-level docs are required; per-field docs are encouraged but not denied in Phase 0.
#![allow(missing_docs)]

pub mod capture;
pub mod canonical;
pub mod cid;
pub mod crypto;
pub mod error;
pub mod merge;
pub mod object;
pub mod repository;
pub mod root;
pub mod schema;
pub mod spatial;
pub mod store;
pub mod working_set;

/// UniFFI foreign-language API (feature `uniffi`).
///
/// UDL scaffolding requires exported items at the crate root; we re-export
/// UniFFI-only helpers here. `hello` / `version` are defined on the crate root
/// so both native Rust and UniFFI share one implementation.
#[cfg(feature = "uniffi")]
#[allow(missing_docs)]
mod uniffi_api;

#[cfg(feature = "uniffi")]
#[allow(missing_docs, unused_imports)]
pub use uniffi_api::{
    annotations_near, capture_annotation, capture_point_cloud, capture_space, commit_building,
    create_root, generate_building_id, generate_keypair, init_building, list_buildings,
    open_building, public_key_hex, put_blob, show_root, AnnotationOverlay, BuildingSummary,
    CapturePutResult, CommitSummary, KeypairData, ObjectPutResult, RootCreateResult,
};

#[cfg(feature = "uniffi")]
uniffi::include_scaffolding!("arxos");

pub use capture::{
    annotation_object, point_cloud_object, space_object, AnnotationCapture, PointCloudCapture,
    SpaceCapture,
};
pub use cid::Cid;
pub use crypto::{AuthorSignature, Keypair, PublicKey, Signature};
pub use error::{Error, Result};
pub use object::{
    AnnotationBody, BlobBody, BuildingBody, BuildingId, FloorBody, Object, ObjectBody,
    ObjectHeader, ObjectType, Pose, SCHEMA_VERSION,
};
pub use merge::{merge_roots, plan_merge, MergePlan, MergeResult, ANNOTATION_DEDUP_M};
pub use object::Aabb;
pub use repository::{BuildingRecord, BuildingRepository, CaptureResult, CommitResult};
pub use root::{RootBody, RootBuilder};
pub use spatial::{QueryVolume, SpatialEntry, SpatialHit};
pub use store::ObjectStore;
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
        assert_eq!(root.objects.len(), 2);
    }
}
