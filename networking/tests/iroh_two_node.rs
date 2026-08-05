//! Integration: two Iroh endpoints exchange a building root closure.

#![cfg(feature = "iroh")]

use std::time::Duration;

use arxos_core::capture::AnnotationCapture;
use arxos_core::object::Pose;
use arxos_core::repository::BuildingRepository;
use arxos_networking::sync::pull_root;
use arxos_networking::IrohNode;
use tempfile::tempdir;

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn iroh_publish_and_pull() {
    let dir_a = tempdir().unwrap();
    let dir_b = tempdir().unwrap();

    let mut repo_a = BuildingRepository::init(dir_a.path(), Some("Iroh Site".into()), None).unwrap();
    let bid = repo_a.building_id().clone();
    repo_a
        .capture_annotation(&AnnotationCapture::new(
            "peer note",
            Pose {
                position: [3.0, 1.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
    let commit = repo_a.commit(Some("from A".into())).unwrap();
    let root = commit.root_cid.to_string();

    let node_a = std::sync::Arc::new(IrohNode::bind(dir_a.path()).await.expect("bind A"));
    let ticket = node_a.ticket().await.expect("ticket");
    let accept = {
        let n = std::sync::Arc::clone(&node_a);
        tokio::spawn(async move {
            let _ = n.accept_loop().await;
        })
    };

    // Give accept loop a moment.
    tokio::time::sleep(Duration::from_millis(200)).await;

    let node_b = IrohNode::bind(dir_b.path()).await.expect("bind B");
    {
        let _follow =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Iroh Site".into()))
                .unwrap();
    } // drop lock before pull adopt

    let pull = pull_root(
        &node_b,
        &ticket,
        dir_b.path(),
        &root,
        Some(bid.as_str()),
        true,
    )
    .await
    .expect("pull");

    assert!(pull.objects_stored >= 2);
    assert_eq!(pull.root_cid, commit.root_cid);

    let mut repo_b = BuildingRepository::open(dir_b.path(), &bid).unwrap();
    assert_eq!(repo_b.head_root(), Some(commit.root_cid));
    let hits = repo_b
        .annotations_near(
            &Pose {
                position: [3.0, 1.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            2.0,
        )
        .unwrap();
    assert_eq!(hits.len(), 1);
    assert_eq!(hits[0].text, "peer note");

    accept.abort();
    node_b.close().await;
}
