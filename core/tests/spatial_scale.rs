//! Scale test: floor-sized synthetic graph with partial loading measurements.
//!
//! Target class: tens of thousands of objects (architecture: ~250k sq ft class).
//! Phase 3 uses a 50×50 m floor with a dense annotation grid (~10k objects) to
//! stay fast in CI while still exercising index build + partial query.

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::time::Instant;

use arxos_core::capture::{annotation_object, space_object, AnnotationCapture, SpaceCapture};
use arxos_core::object::{Aabb, BuildingBody, BuildingId, FloorBody, Object, ObjectBody, Pose};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::RootBuilder;
use arxos_core::spatial::{self, QueryVolume};
use arxos_core::store::ObjectStore;
use arxos_core::{Cid, Keypair};
use tempfile::tempdir;

#[test]
fn floor_scale_index_and_partial_load() {
    let dir = tempdir().unwrap();
    let store = ObjectStore::open(dir.path()).unwrap();
    let kp = Keypair::generate();
    let bid = BuildingId::new();

    let mut building = Object::new_with_created(
        ObjectBody::Building(BuildingBody {
            building_id: bid.clone(),
            name: Some("Scale Hall".into()),
            controller_keys: vec![kp.public_key()],
            properties: BTreeMap::new(),
        }),
        1,
    );
    building.sign(&kp).unwrap();
    let building_cid = store.put(&building).unwrap();

    let floor = Object::new_with_created(
        ObjectBody::Floor(FloorBody {
            entity_id: Some(arxos_core::EntityId::new()),
            building_id: bid.clone(),
            name: Some("L1".into()),
            level_index: 0,
            elevation_m: 0.0,
            properties: BTreeMap::new(),
        }),
        2,
    );
    let floor_cid = store.put(&floor).unwrap();

    let space = space_object(&SpaceCapture {
                    entity_id: None,
        name: Some("Open office".into()),
        pose: Pose {
            position: [25.0, 0.0, 25.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        },
        bounds: Some(Aabb::from_min_max([0.0, 0.0, 0.0], [50.0, 3.0, 50.0])),
        floor: Some(floor_cid),
        properties: BTreeMap::new(),
    });
    let space_cid = store.put(&space).unwrap();

    // 40×40 grid = 1_600 annotations across 20×20 m (0.5 m spacing).
    // Enough to exercise hierarchy + partial load without multi-minute CI runs.
    let grid = 40usize;
    let mut objects: BTreeSet<Cid> = [building_cid, floor_cid, space_cid].into_iter().collect();
    let t_put = Instant::now();
    for ix in 0..grid {
        for iz in 0..grid {
            let x = ix as f64 * 0.5;
            let z = iz as f64 * 0.5;
            let mut ann = annotation_object(&AnnotationCapture::new(
                format!("cell-{ix}-{iz}"),
                Pose {
                    position: [x, 1.2, z],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            ann.header.created = 10 + (ix * grid + iz) as u64;
            let cid = store.put(&ann).unwrap();
            objects.insert(cid);
        }
    }
    let put_ms = t_put.elapsed().as_millis();
    assert_eq!(objects.len(), 3 + grid * grid);

    let entries = spatial::collect_entries(&store, objects.iter().copied()).unwrap();
    assert!(entries.len() > 1_500);

    let t_build = Instant::now();
    let index_root = spatial::build_index(&store, entries).unwrap().unwrap();
    let build_ms = t_build.elapsed().as_millis();

    let (root_obj, root_cid) = RootBuilder::new(bid.clone(), 99)
        .objects(objects)
        .spatial_index(index_root)
        .message("scale floor")
        .build_signed(&kp)
        .unwrap();
    store.put(&root_obj).unwrap();

    // 5×5 m region should hit ~100 annotations (0.5 m grid → 11×11 ≈ 121).
    let volume = QueryVolume::from_min_max([10.0, 0.0, 10.0], [15.0, 3.0, 15.0]);
    let t_query = Instant::now();
    let hits = spatial::query_index_refined(&store, &index_root, &volume).unwrap();
    let query_ms = t_query.elapsed().as_millis();
    assert!(
        hits.len() >= 80 && hits.len() <= 150,
        "expected ~100 hits, got {}",
        hits.len()
    );

    // Partial load via repository.
    let mut repo = BuildingRepository::open_or_follow(dir.path(), &bid, Some("Scale".into())).unwrap();
    // Manually set head by writing record through adopt.
    // Seed device key so later ops work.
    repo.adopt_root(root_cid).unwrap();
    let before = repo.working_set().cache_len();
    let loaded = repo.load_region(&volume, 0).unwrap();
    let after = repo.working_set().cache_len();
    assert!(loaded >= 80, "loaded={loaded}");
    assert!(after >= before + loaded);

    eprintln!(
        "spatial_scale: put={put_ms}ms build={build_ms}ms query={query_ms}ms hits={} loaded={loaded} root={root_cid}",
        hits.len()
    );

    // CI budgets (generous; local debug is fine).
    assert!(build_ms < 30_000, "index build too slow: {build_ms}ms");
    assert!(query_ms < 5_000, "query too slow: {query_ms}ms");
}
