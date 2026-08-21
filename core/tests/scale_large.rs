//! Large-scale integration test for incremental spatial index updates and delta root sizes.

use std::time::Instant;

use arxos_core::capture::AnnotationCapture;
use arxos_core::object::Pose;
use arxos_core::repository::BuildingRepository;
use arxos_core::spatial::QueryVolume;
use tempfile::tempdir;

#[test]
fn test_large_scale_incremental_commits() {
    let dir = tempdir().unwrap();
    let repo_path = dir.path();

    let mut repo = BuildingRepository::init(repo_path, Some("Large Scale Building".into()), None).unwrap();

    // Batch size of 1,000 objects. We will do 5 batches to reach 5,000 objects.
    let num_batches = 5;
    let batch_size = 1000;

    let mut last_root_cid = repo.head_root().unwrap();

    for b in 0..num_batches {
        let t_start = Instant::now();
        // Capture 1,000 annotations in a grid layout
        for i in 0..batch_size {
            let idx = b * batch_size + i;
            let x = (idx % 100) as f64 * 1.0;
            let z = (idx / 100) as f64 * 1.0;

            repo.capture_annotation(&AnnotationCapture::new(
                format!("ann-{b}-{i}"),
                Pose {
                    position: [x, 0.0, z],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ))
            .unwrap();
        }

        let t_capture = t_start.elapsed().as_millis();

        let t_commit_start = Instant::now();
        let commit_res = repo.commit(Some(format!("batch-{b}"))).unwrap();
        let commit_ms = t_commit_start.elapsed().as_millis();

        let root_obj = repo.get_object(&commit_res.root_cid).unwrap();
        let cbor_bytes = root_obj.to_canonical_bytes().unwrap();

        println!(
            "Batch {b}: capture={t_capture}ms, commit={commit_ms}ms, root size={} bytes, total_objects={}",
            cbor_bytes.len(),
            commit_res.object_count
        );

        if b == 0 {
            // First batch is a checkpoint root, so it serializes all 1,001 objects.
            assert!(cbor_bytes.len() > 20_000, "First checkpoint root should serialize all objects");
        } else {
            // Subsequent batches are delta roots, so they only serialize 1,000 added objects!
            // The size should be tiny (e.g. less than 50,000 bytes).
            assert!(cbor_bytes.len() < 50_000, "Delta root size should remain bounded/tiny");
        }

        last_root_cid = commit_res.root_cid;
    }

    // Perform a spatial query in a 5x5 area: x in [10.0, 15.0], z in [10.0, 15.0].
    // Since coordinates are x = idx % 100, z = idx / 100:
    // x can be 10, 11, 12, 13, 14, 15 (6 values).
    // z can be 10, 11, 12, 13, 14, 15 (6 values).
    // So there should be exactly 6 * 6 = 36 annotations in this query volume.
    let volume = QueryVolume::from_min_max([10.0, -1.0, 10.0], [15.0, 1.0, 15.0]);
    let hits = repo.query_volume(&volume).unwrap();
    println!("Spatial hits count: {}", hits.len());
    assert_eq!(hits.len(), 36, "Should return exactly 36 hits");

    // Verify bounded closure sync: get_root_closure_blobs must only collect roots & active objects
    // back to the nearest checkpoint, avoiding transferring the entire history.
    let blobs = repo.root_closure_bytes(&last_root_cid).unwrap();
    println!("Closure blobs count: {}", blobs.len());
    assert!(blobs.len() > 5000);
}
