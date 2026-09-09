use super::*;
use crate::capture::{annotation_object, space_object, AnnotationCapture, SpaceCapture};
use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::entity::{entity_id_of, EntityId};
use crate::object::{BuildingBody, BuildingId, Object, ObjectBody, Pose};
use crate::repository::BuildingRepository;
use crate::root::RootBuilder;
use crate::store::ObjectStore;
use crate::Error;
use std::collections::{BTreeMap, BTreeSet};
use tempfile::tempdir;

fn put_building(store: &ObjectStore, bid: &BuildingId, kp: &Keypair) -> Cid {
    let mut obj = Object::new_with_created(
        ObjectBody::Building(BuildingBody {
            building_id: bid.clone(),
            name: Some("M".into()),
            controller_keys: vec![kp.public_key()],
            properties: BTreeMap::new(),
        }),
        1,
    );
    obj.sign(kp).unwrap();
    store.put(&obj).unwrap()
}

#[test]
fn merge_union_and_dedupe() {
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let bid = BuildingId::new();
    let building = put_building(&store, &bid, &kp);

    let ann_a = {
        let mut o = annotation_object(&AnnotationCapture::new(
            "same note",
            Pose {
                position: [1.0, 1.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ));
        o.header.created = 100;
        o.sign(&kp).unwrap();
        store.put(&o).unwrap()
    };
    let ann_b_dup = {
        let mut o = annotation_object(&AnnotationCapture::new(
            "same note",
            Pose {
                position: [1.05, 1.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ));
        o.header.created = 50; // older → drop
        o.sign(&kp).unwrap();
        store.put(&o).unwrap()
    };
    let ann_c_conflict = {
        let mut o = annotation_object(&AnnotationCapture::new(
            "different note",
            Pose {
                position: [1.02, 1.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ));
        o.header.created = 80;
        o.sign(&kp).unwrap();
        store.put(&o).unwrap()
    };

    let set_a: BTreeSet<Cid> = [building, ann_a].into_iter().collect();
    let set_b: BTreeSet<Cid> = [building, ann_b_dup, ann_c_conflict].into_iter().collect();

    let (ra, ca) = RootBuilder::new(bid.clone(), 1000)
        .objects(set_a)
        .message("a")
        .build_signed(&kp)
        .unwrap();
    store.put(&ra).unwrap();
    let (rb, cb) = RootBuilder::new(bid.clone(), 1001)
        .objects(set_b)
        .message("b")
        .build_signed(&kp)
        .unwrap();
    store.put(&rb).unwrap();

    let merged = merge_roots(&store, ca, cb, &kp, Some("merge test".into()), true).unwrap();
    assert_eq!(merged.deduped_annotations, 1);
    // building + ann_a + ann_c (ann_b dropped)
    assert_eq!(merged.object_count, 3);

    let root = store.get(&merged.root_cid).unwrap();
    let body = RootBody::from_object(&root).unwrap();
    let active = body.materialize_active_objects(&store).unwrap();
    assert!(active.contains(&ann_a));
    assert!(active.contains(&ann_c_conflict));
    assert!(!active.contains(&ann_b_dup));
    assert!(body.spatial_index_root.is_some());

    // Multi-parent history: both concurrent tips recorded.
    assert_eq!(body.merge_parents.len(), 2);
    assert!(body.merge_parents.contains(&ca));
    assert!(body.merge_parents.contains(&cb));
    assert!(body.previous_root == Some(ca) || body.previous_root == Some(cb));
    assert_eq!(merged.parents, (ca, cb));
}

#[test]
fn three_way_preserves_concurrent_removal() {
    // base has space S; tip A keeps S; tip B removes S → merge must drop S.
    let base: BTreeSet<Cid> = [
        Cid::from_canonical_bytes(b"building"),
        Cid::from_canonical_bytes(b"space-v1"),
    ]
    .into_iter()
    .collect();
    let a = base.clone();
    let mut b = base.clone();
    b.remove(&Cid::from_canonical_bytes(b"space-v1"));
    let merged = three_way_object_set(&base, &a, &b);
    assert!(!merged.contains(&Cid::from_canonical_bytes(b"space-v1")));
    assert!(merged.contains(&Cid::from_canonical_bytes(b"building")));
}

#[test]
fn three_way_unions_concurrent_adds() {
    let base: BTreeSet<Cid> = [Cid::from_canonical_bytes(b"building")]
        .into_iter()
        .collect();
    let mut a = base.clone();
    a.insert(Cid::from_canonical_bytes(b"ann-a"));
    let mut b = base.clone();
    b.insert(Cid::from_canonical_bytes(b"ann-b"));
    let merged = three_way_object_set(&base, &a, &b);
    assert!(merged.contains(&Cid::from_canonical_bytes(b"ann-a")));
    assert!(merged.contains(&Cid::from_canonical_bytes(b"ann-b")));
}

#[test]
fn merge_concurrent_entity_remove_vs_keep() {
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let bid = BuildingId::new();
    let building = put_building(&store, &bid, &kp);
    let eid = EntityId::from("01ENTITYRMCONCURRENT000000".to_string());

    let mut space = space_object(&SpaceCapture {
        entity_id: Some(eid.clone()),
        name: Some("room".into()),
        pose: Pose::default(),
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    });
    space.header.created = 10;
    space.sign(&kp).unwrap();
    let space_cid = store.put(&space).unwrap();

    let base_set: BTreeSet<Cid> = [building, space_cid].into_iter().collect();
    let (rb, base_cid) = RootBuilder::new(bid.clone(), 1000)
        .objects(base_set)
        .build_signed(&kp)
        .unwrap();
    store.put(&rb).unwrap();

    // Tip A: keep space, add annotation
    let mut ann = annotation_object(&AnnotationCapture::new("note", Pose::default()));
    ann.header.created = 20;
    ann.sign(&kp).unwrap();
    let ann_cid = store.put(&ann).unwrap();
    let set_a: BTreeSet<Cid> = [building, space_cid, ann_cid].into_iter().collect();
    let (ra, tip_a) = RootBuilder::new(bid.clone(), 1001)
        .previous_root(base_cid)
        .objects(set_a)
        .build_signed(&kp)
        .unwrap();
    store.put(&ra).unwrap();

    // Tip B: remove space (only building)
    let set_b: BTreeSet<Cid> = [building].into_iter().collect();
    let (rbb, tip_b) = RootBuilder::new(bid, 1002)
        .previous_root(base_cid)
        .objects(set_b)
        .build_signed(&kp)
        .unwrap();
    store.put(&rbb).unwrap();

    let merged = merge_roots(&store, tip_a, tip_b, &kp, None, false).unwrap();
    let root = store.get(&merged.root_cid).unwrap();
    let body = RootBody::from_object(&root).unwrap();
    let active = body.materialize_active_objects(&store).unwrap();
    assert!(
        !active.contains(&space_cid),
        "concurrent removal must win over keep"
    );
    assert!(active.contains(&ann_cid), "concurrent add must be kept");
    assert!(active.contains(&building));
}

#[test]
fn merge_collapses_same_entity_to_newer_version() {
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let bid = BuildingId::new();
    let building = put_building(&store, &bid, &kp);
    let eid = EntityId::from("01ENTITYMERGE000000000000".to_string());

    let mut older = space_object(&SpaceCapture {
        entity_id: Some(eid.clone()),
        name: Some("older".into()),
        pose: Pose {
            position: [0.0, 0.0, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    });
    older.header.created = 10;
    older.sign(&kp).unwrap();
    let c_old = store.put(&older).unwrap();

    let mut newer = space_object(&SpaceCapture {
        entity_id: Some(eid.clone()),
        name: Some("newer".into()),
        pose: Pose {
            position: [5.0, 0.0, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    });
    newer.header.created = 20;
    newer.sign(&kp).unwrap();
    let c_new = store.put(&newer).unwrap();

    let set_a: BTreeSet<Cid> = [building, c_old].into_iter().collect();
    let set_b: BTreeSet<Cid> = [building, c_new].into_iter().collect();
    let (ra, ca) = RootBuilder::new(bid.clone(), 2000)
        .objects(set_a)
        .build_signed(&kp)
        .unwrap();
    store.put(&ra).unwrap();
    let (rb, cb) = RootBuilder::new(bid, 2001)
        .objects(set_b)
        .build_signed(&kp)
        .unwrap();
    store.put(&rb).unwrap();

    let merged = merge_roots(&store, ca, cb, &kp, None, false).unwrap();
    let root = store.get(&merged.root_cid).unwrap();
    let body = RootBody::from_object(&root).unwrap();
    let active = body.materialize_active_objects(&store).unwrap();
    assert!(active.contains(&c_new));
    assert!(!active.contains(&c_old));
    assert_eq!(entity_id_of(&store.get(&c_new).unwrap()).unwrap(), &eid);
    // building + one space version
    assert_eq!(active.len(), 2);
}

#[test]
fn merge_untrusted_newer_building_cannot_win() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("Alice".into()), None).unwrap();
    let alice_pk = repo.keypair().unwrap().public_key();
    let bid = repo.building_id().clone();
    let mallory = Keypair::generate();

    let b_m = Object::new_with_created(
        ObjectBody::Building(BuildingBody {
            building_id: bid.clone(),
            name: Some("Mallory".into()),
            controller_keys: vec![mallory.public_key()],
            properties: BTreeMap::new(),
        }),
        u64::MAX / 2,
    );
    let b_m_cid = repo.put_object(&b_m).unwrap();
    let mut objects = BTreeSet::new();
    objects.insert(b_m_cid);
    let (fork, fork_cid) = RootBuilder::new(bid, 50)
        .objects(objects)
        .message("mallory")
        .build_signed(&mallory)
        .unwrap();
    repo.put_object(&fork).unwrap();

    let err = repo
        .merge_root(fork_cid, Some("merge mallory".into()))
        .unwrap_err();
    assert!(
        matches!(err, Error::Authorization(_)),
        "expected Authorization, got {err:?}"
    );
    let keys = repo.controller_keys().unwrap();
    assert_eq!(keys.len(), 1, "{keys:?}");
    assert!(keys.contains(&alice_pk));
    assert!(!keys.contains(&mallory.public_key()));
}

#[test]
fn merge_untrusted_parent_cannot_add_objects() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("Alice".into()), None).unwrap();
    let alice_pk = repo.keypair().unwrap().public_key();
    let bid = repo.building_id().clone();
    let alice_head = repo.head_root().unwrap();
    let alice_objects: BTreeSet<Cid> = repo.head_object_cids().unwrap().into_iter().collect();
    let mallory = Keypair::generate();

    let b_m = Object::new_with_created(
        ObjectBody::Building(BuildingBody {
            building_id: bid.clone(),
            name: Some("Mallory".into()),
            controller_keys: vec![mallory.public_key()],
            properties: BTreeMap::new(),
        }),
        u64::MAX / 2,
    );
    let b_m_cid = repo.put_object(&b_m).unwrap();
    let mut space = space_object(&SpaceCapture {
        entity_id: Some(EntityId::new()),
        name: Some("mallory space".into()),
        pose: Pose::default(),
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    });
    space.sign(&mallory).unwrap();
    let space_cid = repo.put_object(&space).unwrap();
    let mut objects = BTreeSet::new();
    objects.insert(b_m_cid);
    objects.insert(space_cid);
    let (fork, fork_cid) = RootBuilder::new(bid, 50)
        .objects(objects)
        .message("mallory")
        .build_signed(&mallory)
        .unwrap();
    repo.put_object(&fork).unwrap();

    let err = repo
        .merge_root(fork_cid, Some("merge mallory space".into()))
        .unwrap_err();
    assert!(
        matches!(err, Error::Authorization(_)),
        "expected Authorization, got {err:?}"
    );
    assert_eq!(repo.head_root(), Some(alice_head));
    let active: BTreeSet<Cid> = repo.head_object_cids().unwrap().into_iter().collect();
    assert_eq!(active, alice_objects);
    assert!(!active.contains(&space_cid));
    let keys = repo.controller_keys().unwrap();
    assert!(keys.contains(&alice_pk));
    assert!(!keys.contains(&mallory.public_key()));
}

#[test]
fn merge_parents_are_dag_ancestors() {
    // M = merge(A,B) with previous_root=A. A must be an ancestor of M via
    // merge_parents, so merging A with M fast-forwards instead of unioning.
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let bid = BuildingId::new();
    let building = put_building(&store, &bid, &kp);

    let mut space = space_object(&SpaceCapture {
        entity_id: Some(EntityId::new()),
        name: Some("x".into()),
        pose: Pose::default(),
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    });
    space.sign(&kp).unwrap();
    let space_cid = store.put(&space).unwrap();

    let g_set: BTreeSet<Cid> = [building, space_cid].into_iter().collect();
    let (rg, g) = RootBuilder::new(bid.clone(), 1000)
        .objects(g_set)
        .build_signed(&kp)
        .unwrap();
    store.put(&rg).unwrap();

    let a_set: BTreeSet<Cid> = [building].into_iter().collect();
    let (ra, a) = RootBuilder::new(bid.clone(), 1001)
        .previous_root(g)
        .objects(a_set)
        .build_signed(&kp)
        .unwrap();
    store.put(&ra).unwrap();

    let b_set: BTreeSet<Cid> = [building, space_cid].into_iter().collect();
    let (rb, b) = RootBuilder::new(bid.clone(), 2000)
        .previous_root(g)
        .objects(b_set)
        .build_signed(&kp)
        .unwrap();
    store.put(&rb).unwrap();

    let m = merge_roots(&store, a, b, &kp, None, false).unwrap();
    assert!(
        is_ancestor_of(&store, a, m.root_cid).unwrap(),
        "merge parent A must be a DAG ancestor of the merge commit"
    );
    let lca = find_common_ancestor(&store, a, m.root_cid).unwrap();
    assert_eq!(lca, Some(a), "LCA(A, merge(A,B)) must be A, not genesis");

    let merged_again = merge_roots(&store, a, m.root_cid, &kp, None, false).unwrap();
    let active = {
        let root = store.get(&merged_again.root_cid).unwrap();
        RootBody::from_object(&root)
            .unwrap()
            .materialize_active_objects(&store)
            .unwrap()
    };
    assert!(
        !active.contains(&space_cid),
        "deleted space must not resurrect when re-merging a merge parent"
    );
}

#[test]
fn pose_less_annotations_are_not_deduped_at_origin() {
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let bid = BuildingId::new();
    let building = put_building(&store, &bid, &kp);

    let mut a1 = Object::new_with_created(
        ObjectBody::Annotation(crate::object::AnnotationBody {
            text: Some("same".into()),
            transcript: None,
            media_ref: None,
            pose: None,
            space: None,
            properties: BTreeMap::new(),
        }),
        10,
    );
    a1.sign(&kp).unwrap();
    let c1 = store.put(&a1).unwrap();

    let mut a2 = Object::new_with_created(
        ObjectBody::Annotation(crate::object::AnnotationBody {
            text: Some("same".into()),
            transcript: None,
            media_ref: None,
            pose: None,
            space: None,
            properties: BTreeMap::new(),
        }),
        20,
    );
    a2.sign(&kp).unwrap();
    let c2 = store.put(&a2).unwrap();

    let set_a: BTreeSet<Cid> = [building, c1].into_iter().collect();
    let set_b: BTreeSet<Cid> = [building, c2].into_iter().collect();
    let (ra, ca) = RootBuilder::new(bid.clone(), 1000)
        .objects(set_a)
        .build_signed(&kp)
        .unwrap();
    store.put(&ra).unwrap();
    let (rb, cb) = RootBuilder::new(bid, 1001)
        .objects(set_b)
        .build_signed(&kp)
        .unwrap();
    store.put(&rb).unwrap();

    let merged = merge_roots(&store, ca, cb, &kp, None, false).unwrap();
    let root = store.get(&merged.root_cid).unwrap();
    let active = RootBody::from_object(&root)
        .unwrap()
        .materialize_active_objects(&store)
        .unwrap();
    assert!(active.contains(&c1) && active.contains(&c2));
}
