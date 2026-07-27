//! Property tests: random objects/roots → canonicalize → verify transition.

use std::collections::BTreeMap;
use std::collections::BTreeSet;

use arxos_core::object::{BlobBody, BuildingBody, BuildingId, Object, ObjectBody};
use arxos_core::root::RootBuilder;
use arxos_core::store::ObjectStore;
use arxos_core::verify::{verify_object_canonicalization, verify_root_transition};
use arxos_core::Keypair;
use proptest::prelude::*;
use tempfile::tempdir;

proptest! {
    #![proptest_config(ProptestConfig::with_cases(24))]

    #[test]
    fn object_canon_stable(data in prop::collection::vec(any::<u8>(), 0..48), created in 1u64..2_000_000_000) {
        let obj = Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: Some("application/octet-stream".into()),
                data,
                properties: BTreeMap::new(),
            }),
            created,
        );
        let report = verify_object_canonicalization(&obj).unwrap();
        prop_assert!(report.ok, "{:?}", report.findings);
    }
}

#[test]
fn signed_root_chain_verifies() {
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let bid = BuildingId::new();
    let mut building = Object::new_with_created(
        ObjectBody::Building(BuildingBody {
            building_id: bid.clone(),
            name: Some("P".into()),
            controller_keys: vec![kp.public_key()],
            properties: BTreeMap::new(),
        }),
        1,
    );
    building.sign(&kp).unwrap();
    let bc = store.put(&building).unwrap();

    let mut set = BTreeSet::new();
    set.insert(bc);
    let (r1, c1) = RootBuilder::new(bid.clone(), 10)
        .objects(set.clone())
        .message("g")
        .build_signed(&kp)
        .unwrap();
    store.put(&r1).unwrap();

    let blob = Object::new_with_created(
        ObjectBody::Blob(BlobBody {
            content_type: None,
            data: vec![9, 9, 9],
            properties: BTreeMap::new(),
        }),
        11,
    );
    let blob_c = store.put(&blob).unwrap();
    set.insert(blob_c);
    let (r2, c2) = RootBuilder::new(bid, 20)
        .objects(set)
        .previous_root(c1)
        .message("n")
        .build_signed(&kp)
        .unwrap();
    store.put(&r2).unwrap();

    let rep = verify_root_transition(&store, &c2).unwrap();
    assert!(rep.ok, "{:?}", rep.findings);
}
