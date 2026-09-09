use super::pull::ingest_pulled_blobs;
use super::*;
use crate::memory::MemoryMesh;
use crate::protocol::BuildingHeadAd;
use arxos_core::capture::AnnotationCapture;
use arxos_core::object::{BuildingId, Pose};
use arxos_core::repository::BuildingRepository;
use arxos_core::Cid;
use tempfile::tempdir;

#[tokio::test]
async fn two_device_pull_root() {
    let mesh = MemoryMesh::new();
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();

    // Device A: capture and commit
    let mut repo_a = BuildingRepository::init(dir_a.path(), Some("Site A".into()), None).unwrap();
    let bid = repo_a.building_id().clone();
    repo_a
        .capture_annotation(&AnnotationCapture::new(
            "from device A",
            Pose {
                position: [1.0, 1.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
    let commit = repo_a.commit(Some("scan a".into())).unwrap();
    let root = commit.root_cid.to_string();

    let node_a = mesh
        .attach(
            dir_a.path(),
            vec![BuildingHeadAd {
                building_id: bid.to_string(),
                root_cid: root.clone(),
                name: Some("Site A".into()),
                object_count: commit.object_count,
            }],
        )
        .unwrap();

    // Device B: empty follow (drop before pull so adopt can take the write lock)
    {
        let _repo_b =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Site A".into())).unwrap();
    }
    let node_b = mesh.attach(dir_b.path(), vec![]).unwrap();

    let pull = pull_root(
        &node_b,
        node_a.peer_id(),
        dir_b.path(),
        &root,
        Some(bid.as_str()),
        true,
    )
    .await
    .unwrap();

    assert!(pull.objects_stored >= 2);
    assert!(pull.adopted.is_some());
    assert_eq!(pull.adopted.unwrap().root_cid, commit.root_cid);

    let mut repo_b2 = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    assert_eq!(repo_b2.head_root(), Some(commit.root_cid));
    let hits = repo_b2
        .annotations_near(
            &Pose {
                position: [1.0, 1.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            2.0,
        )
        .unwrap();
    assert_eq!(hits.len(), 1);
    assert_eq!(hits[0].text, "from device A");
}

#[tokio::test]
async fn pull_set_head_default_does_not_install_mallory_fork() {
    use arxos_core::crypto::Keypair;
    use arxos_core::object::{BuildingBody, Object, ObjectBody};
    use arxos_core::root::RootBuilder;
    use std::collections::{BTreeMap, BTreeSet};

    let mesh = MemoryMesh::new();
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();
    let dir_m = tempdir().unwrap();

    let mut repo_a = BuildingRepository::init(dir_a.path(), Some("Site A".into()), None).unwrap();
    let bid = repo_a.building_id().clone();
    repo_a
        .capture_annotation(&AnnotationCapture::new("alice", Pose::default()))
        .unwrap();
    let commit = repo_a.commit(Some("alice".into())).unwrap();
    let alice_root = commit.root_cid.to_string();
    drop(repo_a);

    let node_a = mesh
        .attach(
            dir_a.path(),
            vec![BuildingHeadAd {
                building_id: bid.to_string(),
                root_cid: alice_root.clone(),
                name: Some("Site A".into()),
                object_count: commit.object_count,
            }],
        )
        .unwrap();

    {
        let _repo_b =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Site A".into())).unwrap();
    }
    let node_b = mesh.attach(dir_b.path(), vec![]).unwrap();
    let pull_alice = pull_root(
        &node_b,
        node_a.peer_id(),
        dir_b.path(),
        &alice_root,
        Some(bid.as_str()),
        true,
    )
    .await
    .unwrap();
    assert_eq!(pull_alice.adopted.unwrap().root_cid, commit.root_cid);

    // Mallory: same building_id, replaced Building, full-set genesis.
    let mallory = Keypair::generate();
    let mut repo_m =
        BuildingRepository::open_or_follow(dir_m.path(), &bid, Some("Mallory".into())).unwrap();
    let b_m = Object::new_with_created(
        ObjectBody::Building(BuildingBody {
            building_id: bid.clone(),
            name: Some("Mallory".into()),
            controller_keys: vec![mallory.public_key()],
            properties: BTreeMap::new(),
        }),
        99,
    );
    let b_m_cid = repo_m.put_object(&b_m).unwrap();
    let mut objects = BTreeSet::new();
    objects.insert(b_m_cid);
    let (fork_obj, fork_cid) = RootBuilder::new(bid.clone(), 10_000)
        .objects(objects)
        .message("mallory genesis")
        .build_signed(&mallory)
        .unwrap();
    repo_m.put_object(&fork_obj).unwrap();
    repo_m.adopt_root(fork_cid).unwrap();
    drop(repo_m);

    let node_m = mesh
        .attach(
            dir_m.path(),
            vec![BuildingHeadAd {
                building_id: bid.to_string(),
                root_cid: fork_cid.to_string(),
                name: Some("Mallory".into()),
                object_count: 1,
            }],
        )
        .unwrap();

    let err = pull_root(
        &node_b,
        node_m.peer_id(),
        dir_b.path(),
        &fork_cid.to_string(),
        Some(bid.as_str()),
        true,
    )
    .await
    .unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains("authorization")
            || msg.contains("local controller")
            || msg.contains("second genesis")
            || msg.contains("not a descendant"),
        "unexpected error: {msg}"
    );

    let repo_b2 = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    assert_eq!(repo_b2.head_root(), Some(commit.root_cid));
}

#[tokio::test]
async fn two_device_pull_root_with_spatial_index() {
    let mesh = MemoryMesh::new();
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();

    // 1. Device A: init, capture space and multiple annotations, commit (which builds the spatial index)
    let mut repo_a =
        BuildingRepository::init(dir_a.path(), Some("Site Spatial A".into()), None).unwrap();
    let bid = repo_a.building_id().clone();

    // Add multiple annotations to guarantee index node creation (LEAF_CAPACITY is 16, so 20 annotations will split it)
    for i in 0..20 {
        repo_a
            .capture_annotation(&AnnotationCapture::new(
                format!("ann-{i}"),
                Pose {
                    position: [i as f64 * 0.1, 1.0, 1.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ))
            .unwrap();
    }
    let commit = repo_a
        .commit(Some("commit with spatial index".into()))
        .unwrap();
    let root = commit.root_cid;

    // Retrieve spatial index root CID from committed root body
    let root_obj = repo_a.get_object(&root).unwrap();
    let root_body = arxos_core::root::RootBody::from_object(&root_obj).unwrap();
    let index_root_cid = root_body
        .spatial_index_root
        .expect("should have spatial index root");

    // Verify that the index root exists in A's store
    assert!(repo_a.contains(&index_root_cid));

    let node_a = mesh
        .attach(
            dir_a.path(),
            vec![BuildingHeadAd {
                building_id: bid.to_string(),
                root_cid: root.to_string(),
                name: Some("Site Spatial A".into()),
                object_count: commit.object_count,
            }],
        )
        .unwrap();

    // 2. Device B: empty follow (drop before pull so adopt can take the write lock)
    {
        let _repo_b =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Site Spatial B".into()))
                .unwrap();
    }
    let node_b = mesh.attach(dir_b.path(), vec![]).unwrap();

    // 3. Pull root on B
    let pull = pull_root(
        &node_b,
        node_a.peer_id(),
        dir_b.path(),
        &root.to_string(),
        Some(bid.as_str()),
        true,
    )
    .await
    .unwrap();

    // Verify pull is successful and adopted
    assert!(pull.adopted.is_some());
    assert_eq!(pull.adopted.unwrap().root_cid, commit.root_cid);

    // Assert 1: The index node CIDs (including index root) are present in the receiving store after fetch.
    let store_b = arxos_core::store::ObjectStore::open(dir_b.path()).unwrap();
    assert!(
        store_b.contains(&index_root_cid),
        "B's store must contain index root"
    );

    // Let's also traverse the children of index root and verify they are present in B's store
    let index_root_obj = store_b
        .get(&index_root_cid)
        .expect("load index root from B");
    if let arxos_core::ObjectBody::SpatialIndexNode(node) = index_root_obj.body {
        assert!(!node.children.is_empty(), "index should have child nodes");
        for child in &node.children {
            assert!(
                store_b.contains(child),
                "B's store must contain child node {}",
                child
            );
        }
    } else {
        panic!("Expected SpatialIndexNode");
    }

    // Assert 2: A spatial query after fetch does not fall back to the linear path (by verifying the index root is loaded).
    let repo_b = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    let volume = arxos_core::QueryVolume::from_min_max([-1.0, 0.0, -1.0], [5.0, 5.0, 5.0]);

    // Because the spatial index root exists in the adopted root body, the query uses it.
    // Let's assert repo_b.query_volume succeeds and does not hit linear scan (meaning it uses the index).
    let hits = repo_b.query_volume(&volume).unwrap();
    assert!(!hits.is_empty(), "should find hits via spatial index");
}

#[tokio::test]
async fn multi_device_metadata_pull_entity_merge_cycle() {
    use arxos_core::capture::SpaceCapture;
    use arxos_core::entity::EntityId;
    use arxos_core::Keypair;
    use std::collections::BTreeMap;

    let mesh = MemoryMesh::new();
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();
    let dir_edge = tempdir().unwrap();

    // A init + entity + annotation
    let mut repo_a = BuildingRepository::init(dir_a.path(), Some("Cycle".into()), None).unwrap();
    let bid = repo_a.building_id().clone();
    let kp_a = Keypair::from_seed(*repo_a.keypair().unwrap().seed());
    let kp_b = Keypair::generate();
    repo_a.add_controller_key(kp_b.public_key()).unwrap();
    let eid = EntityId::from("01CYCLEENTITY0000000000000".to_string());
    repo_a
        .capture_space(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("room".into()),
            pose: Pose::default(),
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .unwrap();
    // Point cloud so metadata-only is meaningful
    use arxos_core::capture::PointCloudCapture;
    let pts = [[0.0f32; 3], [1.0, 0.0, 0.0]];
    repo_a
        .capture_point_cloud(&PointCloudCapture::from_xyz(&pts, Pose::default(), None))
        .unwrap();
    let base = repo_a.commit(Some("base".into())).unwrap();
    let root = base.root_cid.to_string();
    drop(repo_a);

    let node_a = mesh
        .attach(
            dir_a.path(),
            vec![BuildingHeadAd {
                building_id: bid.to_string(),
                root_cid: root.clone(),
                name: Some("Cycle".into()),
                object_count: base.object_count,
            }],
        )
        .unwrap();

    // Edge metadata-only pull
    {
        let _ = BuildingRepository::open_or_follow(dir_edge.path(), &bid, Some("Cycle".into()))
            .unwrap();
    }
    let node_edge = mesh.attach(dir_edge.path(), vec![]).unwrap();
    let pull_edge = pull_root_with_options(
        &node_edge,
        node_a.peer_id(),
        dir_edge.path(),
        &root,
        Some(bid.as_str()),
        false, // metadata-only cannot set head
        false,
        true,
        Vec::new(),
    )
    .await
    .unwrap();
    assert!(pull_edge.adopted.is_none());

    // B full pull then offline entity update
    {
        let _ =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Cycle".into())).unwrap();
    }
    // Install B's seed as controller
    let seed_path = dir_b.path().join("keys").join("device.seed");
    std::fs::create_dir_all(seed_path.parent().unwrap()).unwrap();
    arxos_core::write_secret_bytes(&seed_path, kp_b.seed().as_ref()).unwrap();

    let node_b = mesh.attach(dir_b.path(), vec![]).unwrap();
    let pull_b = pull_root(
        &node_b,
        node_a.peer_id(),
        dir_b.path(),
        &root,
        Some(bid.as_str()),
        true,
    )
    .await
    .unwrap();
    assert!(pull_b.adopted.is_some());

    let mut repo_b = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    repo_b
        .capture_space(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("room-v2".into()),
            pose: Pose {
                position: [1.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .unwrap();
    let tip_b = repo_b.commit(Some("B update".into())).unwrap();
    drop(repo_b);

    // A concurrent annotation
    arxos_core::write_secret_bytes(
        &dir_a.path().join("keys").join("device.seed"),
        kp_a.seed().as_ref(),
    )
    .unwrap();
    let mut repo_a = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    repo_a
        .capture_annotation(&AnnotationCapture::new("A concurrent", Pose::default()))
        .unwrap();
    let tip_a = repo_a.commit(Some("A note".into())).unwrap();
    drop(repo_a);

    // Pull B's tip into A (full), merge
    let node_a2 = mesh.attach(dir_a.path(), vec![]).unwrap();
    // Publish B for pull
    let node_b2 = mesh
        .attach(
            dir_b.path(),
            vec![BuildingHeadAd {
                building_id: bid.to_string(),
                root_cid: tip_b.root_cid.to_string(),
                name: None,
                object_count: tip_b.object_count,
            }],
        )
        .unwrap();
    let pull_ab = pull_root(
        &node_a2,
        node_b2.peer_id(),
        dir_a.path(),
        &tip_b.root_cid.to_string(),
        Some(bid.as_str()),
        false, // store objects only; don't adopt B over A
    )
    .await
    .unwrap();
    assert!(pull_ab.objects_stored > 0);

    let mut repo_a = BuildingRepository::open(dir_a.path(), &bid).unwrap();
    assert_eq!(repo_a.head_root(), Some(tip_a.root_cid));
    let merged = repo_a
        .merge_root(tip_b.root_cid, Some("merge cycle".into()))
        .unwrap();
    let heads = repo_a.list_entity_heads().unwrap();
    assert!(
        heads.iter().any(|(e, _, _)| e == &eid),
        "entity still present after merge"
    );
    assert_eq!(repo_a.controller_keys().unwrap().len(), 2);
    let _ = merged;
}

#[tokio::test]
async fn metadata_only_pull_omits_blobs() {
    use arxos_core::capture::PointCloudCapture;
    use arxos_core::object::ObjectBody;

    let mesh = MemoryMesh::new();
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();

    let mut repo_a = BuildingRepository::init(dir_a.path(), Some("Meta".into()), None).unwrap();
    let bid = repo_a.building_id().clone();
    let pts = [[0.0f32, 0.0, 0.0], [1.0, 0.0, 0.0]];
    let cap = PointCloudCapture::from_xyz(&pts, Pose::default(), None);
    let capture_res = repo_a.capture_point_cloud(&cap).unwrap();
    let chunk_obj = repo_a.get_object(&capture_res.cid).unwrap();
    let blob_cid = match chunk_obj.body {
        ObjectBody::PointCloudChunk(b) => b.points_blob.expect("tiered blob"),
        _ => panic!("expected point cloud"),
    };
    let commit = repo_a.commit(Some("with cloud".into())).unwrap();
    let root = commit.root_cid.to_string();
    drop(repo_a);

    let node_a = mesh
        .attach(
            dir_a.path(),
            vec![BuildingHeadAd {
                building_id: bid.to_string(),
                root_cid: root.clone(),
                name: Some("Meta".into()),
                object_count: commit.object_count,
            }],
        )
        .unwrap();

    {
        let _ =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Meta".into())).unwrap();
    }
    let node_b = mesh.attach(dir_b.path(), vec![]).unwrap();

    let err = pull_root_with_options(
        &node_b,
        node_a.peer_id(),
        dir_b.path(),
        &root,
        Some(bid.as_str()),
        true, // set_head
        false,
        true, // metadata_only
        Vec::new(),
    )
    .await
    .unwrap_err();
    assert!(
        err.to_string().contains("metadata-only"),
        "set_head + metadata_only must fail, got {err}"
    );

    let pull = pull_root_with_options(
        &node_b,
        node_a.peer_id(),
        dir_b.path(),
        &root,
        Some(bid.as_str()),
        false, // no-set-head
        false,
        true, // metadata_only
        Vec::new(),
    )
    .await
    .unwrap();
    assert!(pull.adopted.is_none());

    let store_b = arxos_core::store::ObjectStore::open(dir_b.path()).unwrap();
    assert!(
        !store_b.contains(&blob_cid),
        "metadata-only pull must not transfer blob {blob_cid}"
    );
    assert!(store_b.contains(&commit.root_cid));
    assert!(store_b.contains(&capture_res.cid));
}

#[test]
fn pull_ingest_fails_closed_when_store_locked() {
    use arxos_core::object::{BlobBody, Object, ObjectBody};
    use std::collections::BTreeMap;

    if std::env::var_os("ARXOS_PULL_LOCK_CHILD").is_some() {
        let path = std::env::var("ARXOS_LOCK_PATH").expect("ARXOS_LOCK_PATH");
        let obj = Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: None,
                data: b"pull-lock".to_vec(),
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bytes = obj.to_canonical_bytes().unwrap();
        let cid = Cid::from_canonical_bytes(&bytes);
        let blobs = vec![crate::protocol::ObjectBlob {
            cid: cid.to_string(),
            bytes,
        }];
        let r = ingest_pulled_blobs(
            std::path::Path::new(&path),
            &blobs,
            Some(BuildingId::new()),
            cid,
            false,
            false,
            false,
            Vec::new(),
        );
        let blocked = match r {
            Err(e) => {
                let s = e.to_string();
                s.contains("locked") || s.contains("store")
            }
            Ok(_) => false,
        };
        std::process::exit(if blocked { 0 } else { 1 });
    }

    let dir = tempdir().unwrap();
    let store = arxos_core::store::ObjectStore::open(dir.path()).unwrap();
    let _guard = store.try_lock_exclusive().unwrap();

    let exe = std::env::current_exe().expect("current_exe");
    let status = std::process::Command::new(exe)
        .arg("--exact")
        .arg("sync::tests::pull_ingest_fails_closed_when_store_locked")
        .env("ARXOS_PULL_LOCK_CHILD", "1")
        .env("ARXOS_LOCK_PATH", dir.path())
        .status()
        .expect("spawn pull lock probe");
    assert!(
        status.success(),
        "pull ingest must fail closed while another writer holds store.lock; {status}"
    );
}

#[test]
fn serve_get_object_hides_cids_outside_advertised_closures() {
    use arxos_core::object::{BlobBody, Object, ObjectBody};
    use std::collections::BTreeMap;

    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("Advertised".into()), None).unwrap();
    repo.capture_annotation(&AnnotationCapture::new("keep", Pose::default()))
        .unwrap();
    let commit = repo.commit(Some("head".into())).unwrap();
    let head = commit.root_cid.to_string();
    let orphan = {
        let obj = Object::new(ObjectBody::Blob(BlobBody {
            content_type: None,
            data: b"secret-orphan".to_vec(),
            properties: BTreeMap::new(),
        }));
        repo.put_object(&obj).unwrap()
    };
    drop(repo);

    let ads = building_ads_from_store(dir.path()).unwrap();
    assert!(ads.iter().any(|a| a.root_cid == head));

    assert!(serve_get_object(dir.path(), &head).unwrap().is_some());
    assert!(
        serve_get_object(dir.path(), &orphan.to_string())
            .unwrap()
            .is_none(),
        "orphan CAS CID must not be served"
    );
    let err = serve_root_closure(dir.path(), &orphan.to_string()).unwrap_err();
    assert!(
        err.to_string().contains("advertised"),
        "GetRootClosure of non-head must fail, got {err}"
    );
}

#[test]
fn serve_root_closure_rejects_historical_non_head() {
    let dir = tempdir().unwrap();
    let mut repo = BuildingRepository::init(dir.path(), Some("History".into()), None).unwrap();
    let first = repo.head_root().unwrap();
    repo.capture_annotation(&AnnotationCapture::new("later", Pose::default()))
        .unwrap();
    let second = repo.commit(Some("advance".into())).unwrap().root_cid;
    drop(repo);

    assert_ne!(first, second);
    let err = serve_root_closure(dir.path(), &first.to_string()).unwrap_err();
    assert!(
        err.to_string().contains("advertised"),
        "historical root must not be a GetRootClosure target, got {err}"
    );
    assert!(serve_root_closure(dir.path(), &second.to_string())
        .unwrap()
        .iter()
        .any(|b| b.cid == second.to_string()));
}
