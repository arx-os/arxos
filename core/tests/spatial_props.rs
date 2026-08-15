//! Property tests for spatial index construction and query membership.

use std::collections::BTreeSet;

use arxos_core::object::{AnnotationBody, Object, ObjectBody, Pose};
use arxos_core::spatial::{self, QueryVolume, LEAF_CAPACITY};
use arxos_core::store::ObjectStore;
use arxos_core::Cid;
use proptest::prelude::*;
use tempfile::tempdir;

fn put_annotations(store: &ObjectStore, poses: &[[f64; 3]]) -> Vec<Cid> {
    let mut cids = Vec::with_capacity(poses.len());
    for (i, pos) in poses.iter().enumerate() {
        let obj = Object::new_with_created(
            ObjectBody::Annotation(AnnotationBody {
                text: Some(format!("sp-{i}")),
                transcript: None,
                media_ref: None,
                pose: Some(Pose {
                    position: *pos,
                    orientation: [0.0, 0.0, 0.0, 1.0],
                }),
                space: None,
                properties: Default::default(),
            }),
            1_800_000_000 + i as u64,
        );
        cids.push(store.put(&obj).unwrap());
    }
    cids
}

fn refined_cids(store: &ObjectStore, root: &Cid, volume: &QueryVolume) -> Vec<Cid> {
    let mut hits: Vec<Cid> = spatial::query_index_refined(store, root, volume)
        .unwrap()
        .into_iter()
        .map(|h| h.object)
        .collect();
    hits.sort();
    hits.dedup();
    hits
}

fn arb_pose_coord() -> impl Strategy<Value = f64> {
    -50.0f64..50.0
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(24))]

    #[test]
    fn rebuild_and_incremental_same_query_set(
        coords in prop::collection::vec(
            (arb_pose_coord(), arb_pose_coord(), arb_pose_coord()),
            1..=40
        )
    ) {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let poses: Vec<[f64; 3]> = coords.iter().map(|(x, y, z)| [*x, *y, *z]).collect();
        let cids = put_annotations(&store, &poses);
        let mut entries = spatial::collect_entries(&store, cids.iter().copied()).unwrap();
        entries.sort_by_key(|e| e.cid);
        prop_assume!(!entries.is_empty());

        let rebuilt = spatial::build_index(&store, entries.clone()).unwrap().unwrap();
        let mut incremental = None;
        for entry in &entries {
            incremental = spatial::insert_incremental(&store, incremental, vec![entry.clone()])
                .unwrap();
        }
        let incremental = incremental.unwrap();

        let volume = QueryVolume::from_min_max([-60.0, -60.0, -60.0], [60.0, 60.0, 60.0]);
        let h1 = refined_cids(&store, &rebuilt, &volume);
        let h2 = refined_cids(&store, &incremental, &volume);
        prop_assert_eq!(&h1, &h2);
        prop_assert_eq!(h1.len(), entries.len());

        // Membership: refined hits are exactly the entries whose bounds intersect.
        let expected: Vec<Cid> = entries
            .iter()
            .filter(|e| e.bounds.intersects(&volume.bounds))
            .map(|e| e.cid)
            .collect();
        prop_assert_eq!(h1, expected);
    }

    #[test]
    fn full_rebuild_after_delete_excludes_removed(
        coords in prop::collection::vec(
            (arb_pose_coord(), arb_pose_coord(), arb_pose_coord()),
            3..=32
        ),
        drop_seed in 0usize..1000
    ) {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let poses: Vec<[f64; 3]> = coords.iter().map(|(x, y, z)| [*x, *y, *z]).collect();
        let cids = put_annotations(&store, &poses);
        let mut entries = spatial::collect_entries(&store, cids.iter().copied()).unwrap();
        entries.sort_by_key(|e| e.cid);
        prop_assume!(entries.len() >= 2);

        let n_drop = 1 + (drop_seed % (entries.len() - 1));
        let removed: BTreeSet<Cid> = entries.iter().take(n_drop).map(|e| e.cid).collect();
        let kept: Vec<_> = entries.iter().filter(|e| !removed.contains(&e.cid)).cloned().collect();
        prop_assume!(!kept.is_empty());

        // Safety path: full rebuild on the remaining set (no remove_incremental).
        let rebuilt = spatial::build_index(&store, kept.clone()).unwrap().unwrap();
        let volume = QueryVolume::from_min_max([-60.0, -60.0, -60.0], [60.0, 60.0, 60.0]);
        let hits = refined_cids(&store, &rebuilt, &volume);
        for r in &removed {
            prop_assert!(!hits.contains(r), "removed cid {r} still in query hits");
        }
        let expected: Vec<Cid> = kept.iter().map(|e| e.cid).collect();
        prop_assert_eq!(hits, expected);
    }
}

#[test]
fn leaf_and_child_caps_are_published() {
    assert_eq!(LEAF_CAPACITY, 16);
    assert_eq!(arxos_core::spatial::MAX_CHILDREN, 16);
}
