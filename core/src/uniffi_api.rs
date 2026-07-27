//! UniFFI scaffolding API for Swift (and other languages).
//!
//! Functions and types here are re-exported at the crate root when the
//! `uniffi` feature is enabled (required by UniFFI's UDL scaffolding).

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::capture::{AnnotationCapture, PointCloudCapture, SpaceCapture};
use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::object::{BlobBody, BuildingId, Object, ObjectBody, Pose};
use crate::repository::BuildingRepository;
use crate::root::{RootBody, RootBuilder};
use crate::store::ObjectStore;

// `hello` and `version` live on the crate root (shared with native Rust API).

/// Generate a new BuildingId string (ULID).
pub fn generate_building_id() -> String {
    BuildingId::new().to_string()
}

/// Keypair data exposed to foreign languages.
#[derive(Debug, Clone)]
pub struct KeypairData {
    pub seed: Vec<u8>,
    pub public_key_hex: String,
}

/// Generate a random ed25519 keypair.
pub fn generate_keypair() -> KeypairData {
    let kp = Keypair::generate();
    KeypairData {
        seed: kp.seed().to_vec(),
        public_key_hex: kp.public_key().to_hex(),
    }
}

/// Public key hex from keypair data.
pub fn public_key_hex(keypair: KeypairData) -> String {
    keypair.public_key_hex
}

/// Result of putting a blob object.
#[derive(Debug, Clone)]
pub struct ObjectPutResult {
    pub cid: String,
    pub object_type: String,
}

/// Put a blob into the local store at `store_path`.
pub fn put_blob(
    store_path: String,
    data: Vec<u8>,
    content_type: Option<String>,
) -> ObjectPutResult {
    let store = ObjectStore::open(&store_path).expect("open store");
    let obj = Object::new(ObjectBody::Blob(BlobBody {
        content_type,
        data,
        properties: BTreeMap::new(),
    }));
    let cid = store.put(&obj).expect("put object");
    ObjectPutResult {
        cid: cid.to_string(),
        object_type: "blob".into(),
    }
}

/// Result of creating a signed root.
#[derive(Debug, Clone)]
pub struct RootCreateResult {
    pub root_cid: String,
    pub building_id: String,
    pub object_count: u64,
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Create and store a signed root from existing object CID strings.
pub fn create_root(
    store_path: String,
    building_id: String,
    object_cids: Vec<String>,
    seed_hex: String,
    message: Option<String>,
) -> RootCreateResult {
    let store = ObjectStore::open(&store_path).expect("open store");
    let seed_bytes = hex::decode(&seed_hex).expect("seed hex");
    assert_eq!(seed_bytes.len(), 32, "seed must be 32 bytes");
    let mut seed = [0u8; 32];
    seed.copy_from_slice(&seed_bytes);
    let kp = Keypair::from_seed(seed);

    let mut set = BTreeSet::new();
    for s in &object_cids {
        set.insert(Cid::from_str(s).expect("cid"));
    }
    let count = set.len() as u64;
    let bid = BuildingId::from_str(&building_id).expect("building id");

    let mut builder = RootBuilder::new(bid.clone(), now_secs()).objects(set);
    if let Some(msg) = message {
        builder = builder.message(msg);
    }
    let (obj, root_cid) = builder.build_signed(&kp).expect("sign root");
    store.put(&obj).expect("store root");

    RootCreateResult {
        root_cid: root_cid.to_string(),
        building_id: bid.to_string(),
        object_count: count,
    }
}

/// Show a root as a summary string, or None if missing.
pub fn show_root(store_path: String, root_cid: String) -> Option<String> {
    let store = ObjectStore::open(&store_path).ok()?;
    let cid = Cid::from_str(&root_cid).ok()?;
    let obj = store.get(&cid).ok()?;
    let root = RootBody::from_object(&obj).ok()?;
    Some(format!(
        "building_id={} previous={:?} objects={} authors={} message={:?} timestamp={}",
        root.building_id,
        root.previous_root.map(|c| c.to_string()),
        root.objects.len(),
        root.authors.len(),
        root.message,
        root.timestamp
    ))
}

// ─── Phase 1 ───────────────────────────────────────────────────────────────

/// Building summary for mobile UI.
#[derive(Debug, Clone)]
pub struct BuildingSummary {
    pub building_id: String,
    pub name: Option<String>,
    pub head_root: Option<String>,
    pub building_object: Option<String>,
    pub staged_count: u64,
}

fn summary_from_repo(repo: &BuildingRepository) -> BuildingSummary {
    let r = repo.record();
    BuildingSummary {
        building_id: r.building_id.to_string(),
        name: r.name.clone(),
        head_root: r.head_root.map(|c| c.to_string()),
        building_object: r.building_object.map(|c| c.to_string()),
        staged_count: repo.working_set().staged_len() as u64,
    }
}

/// Initialize a new building repository.
pub fn init_building(store_path: String, name: Option<String>) -> BuildingSummary {
    let repo = BuildingRepository::init(&store_path, name, None).expect("init building");
    summary_from_repo(&repo)
}

/// Open an existing building and materialize its head working set.
pub fn open_building(store_path: String, building_id: String) -> BuildingSummary {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let repo = BuildingRepository::open(&store_path, &bid).expect("open building");
    summary_from_repo(&repo)
}

/// List buildings in a store.
pub fn list_buildings(store_path: String) -> Vec<BuildingSummary> {
    BuildingRepository::list_buildings(&store_path)
        .expect("list buildings")
        .into_iter()
        .map(|r| BuildingSummary {
            building_id: r.building_id.to_string(),
            name: r.name,
            head_root: r.head_root.map(|c| c.to_string()),
            building_object: r.building_object.map(|c| c.to_string()),
            staged_count: 0,
        })
        .collect()
}

/// Capture put result.
#[derive(Debug, Clone)]
pub struct CapturePutResult {
    pub cid: String,
    pub object_type: String,
}

fn pose(x: f64, y: f64, z: f64) -> Pose {
    Pose {
        position: [x, y, z],
        orientation: [0.0, 0.0, 0.0, 1.0],
    }
}

/// Capture a space at a world pose.
pub fn capture_space(
    store_path: String,
    building_id: String,
    name: Option<String>,
    x: f64,
    y: f64,
    z: f64,
) -> CapturePutResult {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let res = repo
        .capture_space(&SpaceCapture {
            name,
            pose: pose(x, y, z),
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .expect("capture space");
    CapturePutResult {
        cid: res.cid.to_string(),
        object_type: res.object_type.to_string(),
    }
}

/// Capture a text annotation at a world pose.
pub fn capture_annotation(
    store_path: String,
    building_id: String,
    text: String,
    x: f64,
    y: f64,
    z: f64,
) -> CapturePutResult {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let res = repo
        .capture_annotation(&AnnotationCapture::new(text, pose(x, y, z)))
        .expect("capture annotation");
    CapturePutResult {
        cid: res.cid.to_string(),
        object_type: res.object_type.to_string(),
    }
}

/// Capture a packed XYZ f32 little-endian point cloud.
pub fn capture_point_cloud(
    store_path: String,
    building_id: String,
    points_xyz_f32_le: Vec<u8>,
    x: f64,
    y: f64,
    z: f64,
) -> CapturePutResult {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let mut properties = BTreeMap::new();
    properties.insert("format".into(), "xyz_f32_le".into());
    properties.insert("source".into(), "device".into());
    let res = repo
        .capture_point_cloud(&PointCloudCapture {
            pose: pose(x, y, z),
            bounds: None,
            points_xyz_f32_le,
            properties,
        })
        .expect("capture point cloud");
    CapturePutResult {
        cid: res.cid.to_string(),
        object_type: res.object_type.to_string(),
    }
}

/// Commit staged captures to a new root.
#[derive(Debug, Clone)]
pub struct CommitSummary {
    pub root_cid: String,
    pub building_id: String,
    pub object_count: u64,
    pub previous_root: Option<String>,
}

/// Commit building working set to a new signed root.
pub fn commit_building(
    store_path: String,
    building_id: String,
    message: Option<String>,
) -> CommitSummary {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    // Note: open() does not restore staged set across process boundaries.
    // Mobile clients should capture and commit in one process session, or
    // re-stage by listing uncommitted objects. For UniFFI single-call capture
    // then commit: captures write objects but staged is lost on reopen.
    //
    // Fix: track "pending" CIDs in BuildingRecord for cross-call sessions.
    let res = repo.commit(message).expect("commit");
    CommitSummary {
        root_cid: res.root_cid.to_string(),
        building_id: res.building_id.to_string(),
        object_count: res.object_count,
        previous_root: res.previous_root.map(|c| c.to_string()),
    }
}

/// Annotation overlay data for AR.
#[derive(Debug, Clone)]
pub struct AnnotationOverlay {
    pub cid: String,
    pub text: String,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub distance_m: f64,
}

/// Query annotations near a pose.
pub fn annotations_near(
    store_path: String,
    building_id: String,
    x: f64,
    y: f64,
    z: f64,
    radius_m: f64,
) -> Vec<AnnotationOverlay> {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    repo.annotations_near(&pose(x, y, z), radius_m)
        .expect("annotations near")
        .into_iter()
        .map(|h| AnnotationOverlay {
            cid: h.cid.to_string(),
            text: h.text,
            x: h.pose.position[0],
            y: h.pose.position[1],
            z: h.pose.position[2],
            distance_m: h.distance_m,
        })
        .collect()
}
