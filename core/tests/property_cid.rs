//! Property tests: random object graphs → root → re-materialize → identical root.

use std::collections::BTreeMap;
use std::collections::BTreeSet;

use arxos_core::object::{
    AnnotationBody, BlobBody, BuildingBody, BuildingId, Object, ObjectBody, Pose,
};
use arxos_core::root::{RootBody, RootBuilder};
use arxos_core::store::ObjectStore;
use arxos_core::Keypair;
use proptest::prelude::*;
use tempfile::tempdir;

fn arb_bytes() -> impl Strategy<Value = Vec<u8>> {
    prop::collection::vec(any::<u8>(), 0..64)
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(32))]

    #[test]
    fn blob_cid_deterministic(data in arb_bytes(), created in 1u64..2_000_000_000u64) {
        let body = ObjectBody::Blob(BlobBody {
            content_type: Some("application/octet-stream".into()),
            data: data.clone(),
            properties: BTreeMap::new(),
        });
        let obj = Object::new_with_created(body, created);
        let c1 = obj.cid().unwrap();
        let bytes = obj.to_canonical_bytes().unwrap();
        let obj2 = Object::from_canonical_bytes(&bytes).unwrap();
        assert_eq!(obj2.cid().unwrap(), c1);
        assert_eq!(obj2.to_canonical_bytes().unwrap(), bytes);
    }

    #[test]
    fn store_roundtrip_preserves_cid(
        data in arb_bytes(),
        created in 1u64..2_000_000_000u64
    ) {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let obj = Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: None,
                data,
                properties: BTreeMap::new(),
            }),
            created,
        );
        let cid = store.put(&obj).unwrap();
        let loaded = store.get(&cid).unwrap();
        assert_eq!(loaded.cid().unwrap(), cid);
    }
}

#[test]
fn graph_root_rematerialize_identical() {
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let building_id = BuildingId::new();

    let mut cids = BTreeSet::new();

    let building = Object::new_with_created(
        ObjectBody::Building(BuildingBody {
            building_id: building_id.clone(),
            name: Some("PropTest Hall".into()),
            controller_keys: vec![kp.public_key()],
            properties: BTreeMap::new(),
        }),
        1_700_000_300,
    );
    cids.insert(store.put(&building).unwrap());

    for i in 0..5u64 {
        let mut ann = Object::new_with_created(
            ObjectBody::Annotation(AnnotationBody {
                text: Some(format!("note-{i}")),
                transcript: None,
                media_ref: None,
                pose: Some(Pose {
                    position: [i as f64, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                }),
                space: None,
                properties: BTreeMap::new(),
            }),
            1_700_000_301 + i,
        );
        ann.sign(&kp).unwrap();
        cids.insert(store.put(&ann).unwrap());
    }

    let (root_obj, root_cid) = RootBuilder::new(building_id.clone(), 1_700_000_400)
        .objects(cids.clone())
        .message("property graph")
        .build_signed(&kp)
        .unwrap();
    assert_eq!(store.put(&root_obj).unwrap(), root_cid);

    // Re-materialize every object and recompute root from the same set.
    let mut rematerialized = BTreeSet::new();
    for cid in &cids {
        let obj = store.get(cid).unwrap();
        assert_eq!(obj.cid().unwrap(), *cid);
        rematerialized.insert(obj.cid().unwrap());
    }
    assert_eq!(rematerialized, cids);

    let loaded_root = store.get(&root_cid).unwrap();
    let root = RootBody::from_object(&loaded_root).unwrap();
    root.verify_authors().unwrap();
    assert_eq!(root.objects.as_ref().unwrap(), &cids);
    assert_eq!(loaded_root.cid().unwrap(), root_cid);

    // Rebuild signed root with same inputs + same key → same CID only if
    // timestamp and author signatures match; signature includes random-free
    // deterministic ed25519, so same seed + same payload → same signature.
    let kp2 = Keypair::from_seed(kp.seed());
    let (root2, cid2) = RootBuilder::new(building_id, 1_700_000_400)
        .objects(cids)
        .message("property graph")
        .build_signed(&kp2)
        .unwrap();
    assert_eq!(cid2, root_cid);
    assert_eq!(root2.cid().unwrap(), root_cid);
}
