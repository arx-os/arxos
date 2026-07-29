//! UniFFI FFI static library implementation for Arxos iOS production path.

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use arxos_core::capture::{AnnotationCapture, PointCloudCapture, SpaceCapture, maybe_sign};
use arxos_core::cid::Cid;
use arxos_core::crypto::Keypair;
use arxos_core::object::{
    Aabb, BlobBody, BuildingId, EquipmentBody, Object, ObjectBody, Pose, SpaceBody, SurfaceBody,
};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::{RootBody, RootBuilder};
use arxos_core::store::ObjectStore;

uniffi::include_scaffolding!("arxos");

/// Return static hello message.
pub fn hello(name: String) -> String {
    format!("Hello, {name}!")
}

/// Return library version.
pub fn version() -> String {
    "0.1.0".to_string()
}

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
    let active_count = root.materialize_active_objects(&store).ok()?.len();
    Some(format!(
        "building_id={} previous={:?} objects={} authors={} message={:?} timestamp={}",
        root.building_id,
        root.previous_root.map(|c| c.to_string()),
        active_count,
        root.authors.len(),
        root.message,
        root.timestamp
    ))
}

// ─── Phase 1 ───

/// Building summary for mobile UI.
#[derive(Debug, Clone)]
pub struct FfiBuildingSummary {
    pub building_id: String,
    pub name: Option<String>,
    pub head_root: Option<String>,
    pub building_object: Option<String>,
    pub staged_count: u64,
}

fn summary_from_repo(repo: &BuildingRepository) -> FfiBuildingSummary {
    let r = repo.record();
    FfiBuildingSummary {
        building_id: r.building_id.to_string(),
        name: r.name.clone(),
        head_root: r.head_root.map(|c| c.to_string()),
        building_object: r.building_object.map(|c| c.to_string()),
        staged_count: repo.working_set().staged_len() as u64,
    }
}

/// Initialize a new building repository.
pub fn init_building(store_path: String, name: Option<String>) -> FfiBuildingSummary {
    let repo = BuildingRepository::init(&store_path, name, None).expect("init building");
    summary_from_repo(&repo)
}

/// Open an existing building and materialize its head working set.
pub fn open_building(store_path: String, building_id: String) -> FfiBuildingSummary {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let repo = BuildingRepository::open(&store_path, &bid).expect("open building");
    summary_from_repo(&repo)
}

/// List buildings in a store.
pub fn list_buildings(store_path: String) -> Vec<FfiBuildingSummary> {
    BuildingRepository::list_buildings(&store_path)
        .expect("list buildings")
        .into_iter()
        .map(|r| FfiBuildingSummary {
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
pub struct FfiCapturePutResult {
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
) -> FfiCapturePutResult {
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
    FfiCapturePutResult {
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
) -> FfiCapturePutResult {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let res = repo
        .capture_annotation(&AnnotationCapture::new(text, pose(x, y, z)))
        .expect("capture annotation");
    FfiCapturePutResult {
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
) -> FfiCapturePutResult {
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
    FfiCapturePutResult {
        cid: res.cid.to_string(),
        object_type: res.object_type.to_string(),
    }
}

/// Commit staged captures to a new root.
#[derive(Debug, Clone)]
pub struct FfiCommitSummary {
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
) -> FfiCommitSummary {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let res = repo.commit(message).expect("commit");
    FfiCommitSummary {
        root_cid: res.root_cid.to_string(),
        building_id: res.building_id.to_string(),
        object_count: res.object_count,
        previous_root: res.previous_root.map(|c| c.to_string()),
    }
}

/// Annotation overlay data for AR.
#[derive(Debug, Clone)]
pub struct FfiAnnotationOverlay {
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
) -> Vec<FfiAnnotationOverlay> {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    repo.annotations_near(&pose(x, y, z), radius_m)
        .expect("annotations near")
        .into_iter()
        .map(|h| FfiAnnotationOverlay {
            cid: h.cid.to_string(),
            text: h.text,
            x: h.pose.position[0],
            y: h.pose.position[1],
            z: h.pose.position[2],
            distance_m: h.distance_m,
        })
        .collect()
}

// ─── Phase 1 Mobile Production Surface Expansion ───

#[derive(Debug, Clone)]
pub struct FfiRoomPlanSurface {
    pub id: String,
    pub category: String,
    pub transform: Vec<f64>,
    pub dimensions: Vec<f64>,
}

#[derive(Debug, Clone)]
pub struct FfiRoomPlanObject {
    pub id: String,
    pub category: String,
    pub transform: Vec<f64>,
    pub dimensions: Vec<f64>,
}

#[derive(Debug, Clone)]
pub struct RoomPlanGeometry {
    pub surfaces: Vec<FfiRoomPlanSurface>,
    pub objects: Vec<FfiRoomPlanObject>,
}

#[derive(Debug, Clone)]
pub struct IngestResult {
    pub space_cid: String,
    pub surface_cids: Vec<String>,
    pub object_cids: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct StringKeyValuePair {
    pub key: String,
    pub value: String,
}

#[derive(Debug, Clone)]
pub struct SpatialQueryResult {
    pub cid: String,
    pub object_type: String,
    pub name: Option<String>,
    pub pose_x: f64,
    pub pose_y: f64,
    pub pose_z: f64,
    pub properties: Vec<StringKeyValuePair>,
}

#[derive(Debug, Clone)]
pub struct MergeSummary {
    pub root_cid: String,
    pub object_count: u64,
    pub kept: u64,
    pub deduped_annotations: u64,
    pub spatial_index_root: Option<String>,
    pub parent_a: String,
    pub parent_b: String,
}

#[derive(Debug, Clone)]
pub struct PullResultSummary {
    pub root_cid: String,
    pub objects_stored: u64,
    pub objects_skipped: u64,
    pub adopted_root: Option<String>,
}

fn pose_from_transform(transform: &[f64]) -> Pose {
    assert_eq!(transform.len(), 16, "transform matrix must have 16 elements");
    
    let tx = transform[12];
    let ty = transform[13];
    let tz = transform[14];

    let m00 = transform[0]; let m10 = transform[4]; let m20 = transform[8];
    let m01 = transform[1]; let m11 = transform[5]; let m21 = transform[9];
    let m02 = transform[2]; let m12 = transform[6]; let m22 = transform[10];

    let tr = m00 + m11 + m22;

    let (qx, qy, qz, qw) = if tr > 0.0 {
        let s = (tr + 1.0).sqrt() * 2.0;
        let qw = 0.25 * s;
        let qx = (m21 - m12) / s;
        let qy = (m02 - m20) / s;
        let qz = (m10 - m01) / s;
        (qx, qy, qz, qw)
    } else if (m00 > m11) && (m00 > m22) {
        let s = (1.0 + m00 - m11 - m22).sqrt() * 2.0;
        let qw = (m21 - m12) / s;
        let qx = 0.25 * s;
        let qy = (m01 + m10) / s;
        let qz = (m02 + m20) / s;
        (qx, qy, qz, qw)
    } else if m11 > m22 {
        let s = (1.0 + m11 - m00 - m22).sqrt() * 2.0;
        let qw = (m02 - m20) / s;
        let qx = (m01 + m10) / s;
        let qy = 0.25 * s;
        let qz = (m12 + m21) / s;
        (qx, qy, qz, qw)
    } else {
        let s = (1.0 + m22 - m00 - m11).sqrt() * 2.0;
        let qw = (m10 - m01) / s;
        let qx = (m02 + m20) / s;
        let qy = (m12 + m21) / s;
        let qz = 0.25 * s;
        (qx, qy, qz, qw)
    };

    let len = (qx*qx + qy*qy + qz*qz + qw*qw).sqrt();
    let orientation = if len > 0.0 {
        [qx / len, qy / len, qz / len, qw / len]
    } else {
        [0.0, 0.0, 0.0, 1.0]
    };

    Pose {
        position: [tx, ty, tz],
        orientation,
    }
}

fn world_aabb_from_transform_and_dimensions(transform: &[f64], dimensions: &[f64]) -> Aabb {
    assert_eq!(transform.len(), 16, "transform must be 4x4 matrix (16 elements)");
    assert_eq!(dimensions.len(), 3, "dimensions must have 3 elements");
    let w = dimensions[0] / 2.0;
    let h = dimensions[1] / 2.0;
    let d = dimensions[2] / 2.0;

    let corners = [
        [-w, -h, -d],
        [w, -h, -d],
        [-w, h, -d],
        [w, h, -d],
        [-w, -h, d],
        [w, -h, d],
        [-w, h, d],
        [w, h, d],
    ];

    let mut min_x = f64::MAX;
    let mut min_y = f64::MAX;
    let mut min_z = f64::MAX;
    let mut max_x = f64::MIN;
    let mut max_y = f64::MIN;
    let mut max_z = f64::MIN;

    for [cx, cy, cz] in corners {
        let px = transform[0] * cx + transform[4] * cy + transform[8] * cz + transform[12];
        let py = transform[1] * cx + transform[5] * cy + transform[9] * cz + transform[13];
        let pz = transform[2] * cx + transform[6] * cy + transform[10] * cz + transform[14];

        if px < min_x { min_x = px; }
        if py < min_y { min_y = py; }
        if pz < min_z { min_z = pz; }
        if px > max_x { max_x = px; }
        if py > max_y { max_y = py; }
        if pz > max_z { max_z = pz; }
    }

    Aabb {
        min: [min_x, min_y, min_z],
        max: [max_x, max_y, max_z],
    }
}

/// Ingest RoomPlan structured surfaces and objects, group into a Space, and stage.
pub fn ingest_room_plan(
    store_path: String,
    building_id: String,
    geometry: RoomPlanGeometry,
) -> IngestResult {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let kp = repo.keypair().cloned();

    let mut surface_objs = Vec::new();
    let mut object_objs = Vec::new();
    let mut room_bounds: Option<Aabb> = None;

    for s in &geometry.surfaces {
        let pose = pose_from_transform(&s.transform);
        let bounds = world_aabb_from_transform_and_dimensions(&s.transform, &s.dimensions);

        if let Some(ref mut rb) = room_bounds {
            rb.min[0] = rb.min[0].min(bounds.min[0]);
            rb.min[1] = rb.min[1].min(bounds.min[1]);
            rb.min[2] = rb.min[2].min(bounds.min[2]);
            rb.max[0] = rb.max[0].max(bounds.max[0]);
            rb.max[1] = rb.max[1].max(bounds.max[1]);
            rb.max[2] = rb.max[2].max(bounds.max[2]);
        } else {
            room_bounds = Some(bounds.clone());
        }

        let mut properties = BTreeMap::new();
        properties.insert("identifier".into(), s.id.clone());
        properties.insert("source".into(), "roomplan".into());
        properties.insert("width".into(), s.dimensions.first().cloned().unwrap_or(0.0).to_string());
        properties.insert("height".into(), s.dimensions.get(1).cloned().unwrap_or(0.0).to_string());
        properties.insert("depth".into(), s.dimensions.get(2).cloned().unwrap_or(0.0).to_string());

        surface_objs.push((s.category.clone(), pose, bounds, properties));
    }

    for o in &geometry.objects {
        let pose = pose_from_transform(&o.transform);
        let bounds = world_aabb_from_transform_and_dimensions(&o.transform, &o.dimensions);

        if let Some(ref mut rb) = room_bounds {
            rb.min[0] = rb.min[0].min(bounds.min[0]);
            rb.min[1] = rb.min[1].min(bounds.min[1]);
            rb.min[2] = rb.min[2].min(bounds.min[2]);
            rb.max[0] = rb.max[0].max(bounds.max[0]);
            rb.max[1] = rb.max[1].max(bounds.max[1]);
            rb.max[2] = rb.max[2].max(bounds.max[2]);
        } else {
            room_bounds = Some(bounds.clone());
        }

        let mut properties = BTreeMap::new();
        properties.insert("identifier".into(), o.id.clone());
        properties.insert("source".into(), "roomplan".into());

        object_objs.push((o.category.clone(), pose, properties));
    }

    // 2. Create the Space object
    let space_pose = if let Some(ref rb) = room_bounds {
        Pose {
            position: [
                (rb.min[0] + rb.max[0]) / 2.0,
                (rb.min[1] + rb.max[1]) / 2.0,
                (rb.min[2] + rb.max[2]) / 2.0,
            ],
            orientation: [0.0, 0.0, 0.0, 1.0],
        }
    } else {
        Pose::default()
    };

    let mut space_props = BTreeMap::new();
    space_props.insert("source".into(), "roomplan".into());
    let space_body = SpaceBody {
        name: Some("RoomPlan Room".into()),
        floor: None,
        pose: Some(space_pose),
        bounds: room_bounds,
        properties: space_props,
    };
    let space_object = Object::new_with_created(ObjectBody::Space(space_body), 0);
    let signed_space = maybe_sign(space_object, kp.as_ref()).expect("sign space");
    let space_cid = repo.stage_captured_object(signed_space).expect("stage space").cid;

    // 3. Create and stage all surfaces referencing space_cid
    let mut surface_cids = Vec::new();
    for (category, pose, bounds, properties) in surface_objs {
        let surface_body = SurfaceBody {
            space: Some(space_cid),
            pose: Some(pose),
            bounds: Some(bounds),
            surface_kind: Some(category),
            properties,
        };
        let surface_object = Object::new_with_created(ObjectBody::Surface(surface_body), 0);
        let signed_surface = maybe_sign(surface_object, kp.as_ref()).expect("sign surface");
        let cid = repo.stage_captured_object(signed_surface).expect("stage surface").cid;
        surface_cids.push(cid.to_string());
    }

    // 4. Create and stage all objects referencing space_cid
    let mut object_cids = Vec::new();
    for (category, pose, mut properties) in object_objs {
        properties.insert("space".into(), space_cid.to_string());
        let equipment_body = EquipmentBody {
            name: Some(category.clone()),
            equipment_kind: Some(category),
            pose: Some(pose),
            system: None,
            properties,
        };
        let equipment_object = Object::new_with_created(ObjectBody::Equipment(equipment_body), 0);
        let signed_equipment = maybe_sign(equipment_object, kp.as_ref()).expect("sign equipment");
        let cid = repo.stage_captured_object(signed_equipment).expect("stage equipment").cid;
        object_cids.push(cid.to_string());
    }

    IngestResult {
        space_cid: space_cid.to_string(),
        surface_cids,
        object_cids,
    }
}

/// Query spatial volume for indexed objects.
pub fn query_spatial_volume(
    store_path: String,
    building_id: String,
    min_x: f64,
    min_y: f64,
    min_z: f64,
    max_x: f64,
    max_y: f64,
    max_z: f64,
) -> Vec<SpatialQueryResult> {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let volume = arxos_core::QueryVolume::from_min_max(
        [min_x, min_y, min_z],
        [max_x, max_y, max_z],
    );

    let hits = repo.query_volume(&volume).unwrap_or_default();
    let mut out = Vec::new();
    for hit in hits {
        if let Ok(obj) = repo.store().get(&hit.object) {
            let object_type = obj.header.object_type.as_str().to_string();
            let (name, pose_pos, properties) = match &obj.body {
                ObjectBody::Space(s) => {
                    let pos = s.pose.as_ref().map(|p| p.position).unwrap_or([0.0, 0.0, 0.0]);
                    (s.name.clone(), pos, s.properties.clone())
                }
                ObjectBody::Surface(s) => {
                    let pos = s.pose.as_ref().map(|p| p.position).unwrap_or([0.0, 0.0, 0.0]);
                    (None, pos, s.properties.clone())
                }
                ObjectBody::Equipment(e) => {
                    let pos = e.pose.as_ref().map(|p| p.position).unwrap_or([0.0, 0.0, 0.0]);
                    (e.name.clone(), pos, e.properties.clone())
                }
                ObjectBody::Annotation(a) => {
                    let pos = a.pose.as_ref().map(|p| p.position).unwrap_or([0.0, 0.0, 0.0]);
                    (a.text.clone(), pos, a.properties.clone())
                }
                _ => (None, [0.0, 0.0, 0.0], BTreeMap::new()),
            };

            let properties_list = properties
                .into_iter()
                .map(|(key, value)| StringKeyValuePair { key, value })
                .collect();

            out.push(SpatialQueryResult {
                cid: hit.object.to_string(),
                object_type,
                name,
                pose_x: pose_pos[0],
                pose_y: pose_pos[1],
                pose_z: pose_pos[2],
                properties: properties_list,
            });
        }
    }
    out
}

/// Merge remote head root.
pub fn merge_building_root(
    store_path: String,
    building_id: String,
    other_root_cid: String,
    message: Option<String>,
) -> MergeSummary {
    let bid = BuildingId::from_str(&building_id).expect("building id");
    let mut repo = BuildingRepository::open(&store_path, &bid).expect("open");
    let other = Cid::from_str(&other_root_cid).expect("other root");
    let res = repo.merge_root(other, message).expect("merge");
    MergeSummary {
        root_cid: res.root_cid.to_string(),
        object_count: res.object_count,
        kept: res.kept,
        deduped_annotations: res.deduped_annotations,
        spatial_index_root: res.spatial_index_root.map(|c| c.to_string()),
        parent_a: res.parents.0.to_string(),
        parent_b: res.parents.1.to_string(),
    }
}

/// Pull a remote root closure using a temporary local Tokio executor runtime.
pub fn pull_remote_root(
    store_path: String,
    peer_ticket: String,
    root_cid: String,
    building_id: Option<String>,
    set_head: bool,
    allow_untrusted: bool,
) -> PullResultSummary {
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("tokio runtime");
    
    rt.block_on(async move {
        let node = arxos_networking::IrohNode::bind(std::path::Path::new(&store_path))
            .await
            .expect("bind client endpoint");
        
        let result = arxos_networking::sync::pull_root_with_options(
            &node,
            &peer_ticket,
            std::path::Path::new(&store_path),
            &root_cid,
            building_id.as_deref(),
            set_head,
            allow_untrusted,
        )
        .await
        .expect("pull remote root");

        node.close().await;

        PullResultSummary {
            root_cid: result.root_cid.to_string(),
            objects_stored: result.objects_stored,
            objects_skipped: result.objects_skipped_existing,
            adopted_root: result.adopted.as_ref().map(|a| a.root_cid.to_string()),
        }
    })
}

/// Export to USD file.
pub fn export_usd(store_path: String, building_id: String, output_path: String) -> bool {
    let bid = BuildingId::from_str(&building_id).ok();
    if let Some(bid) = bid {
        let opts = arxos_usd::ExportOptions::default();
        if let Ok(content) = arxos_usd::export_building_usda(
            std::path::Path::new(&store_path),
            &bid,
            &opts,
        ) {
            if std::fs::write(&output_path, content).is_ok() {
                return true;
            }
        }
    }
    false
}

/// Export to IFC file.
pub fn export_ifc(store_path: String, building_id: String, output_path: String) -> bool {
    let bid = BuildingId::from_str(&building_id).ok();
    if let Some(bid) = bid {
        let opts = arxos_ifc::ExportOptions::default();
        if let Ok(content) = arxos_ifc::export_building_ifc(
            std::path::Path::new(&store_path),
            &bid,
            &opts,
        ) {
            if std::fs::write(&output_path, content).is_ok() {
                return true;
            }
        }
    }
    false
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_matrix_to_pose_conversion() {
        // Identity matrix
        let identity = vec![
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            1.5, -2.0, 3.5, 1.0, // translation col 3
        ];
        let p = pose_from_transform(&identity);
        assert_eq!(p.position, [1.5, -2.0, 3.5]);
        // orientation should be identity [0, 0, 0, 1]
        assert!((p.orientation[0] - 0.0).abs() < 1e-5);
        assert!((p.orientation[1] - 0.0).abs() < 1e-5);
        assert!((p.orientation[2] - 0.0).abs() < 1e-5);
        assert!((p.orientation[3] - 1.0).abs() < 1e-5);

        // Simple dimensions world-AABB check
        let dims = vec![2.0, 4.0, 6.0];
        let bounds = world_aabb_from_transform_and_dimensions(&identity, &dims);
        assert_eq!(bounds.min, [0.5, -4.0, 0.5]);
        assert_eq!(bounds.max, [2.5, 0.0, 6.5]);
    }

    #[test]
    fn test_ingest_room_plan_spatial_query() {
        let dir = tempdir().unwrap();
        let path = dir.path().to_str().unwrap().to_string();

        let summary = init_building(path.clone(), Some("RoomPlan Site".into()));
        let bid = summary.building_id;

        // Generate geometry: 1 wall, 1 chair
        let wall = FfiRoomPlanSurface {
            id: "wall-1".into(),
            category: "wall".into(),
            transform: vec![
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                2.0, 0.0, 0.0, 1.0,
            ],
            dimensions: vec![0.1, 2.5, 4.0],
        };

        let chair = FfiRoomPlanObject {
            id: "chair-1".into(),
            category: "chair".into(),
            transform: vec![
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
            dimensions: vec![0.6, 0.8, 0.6],
        };

        let geom1 = RoomPlanGeometry {
            surfaces: vec![wall.clone()],
            objects: vec![chair.clone()],
        };

        // Ingest first time
        let res1 = ingest_room_plan(path.clone(), bid.clone(), geom1.clone());
        assert!(!res1.space_cid.is_empty());
        assert_eq!(res1.surface_cids.len(), 1);
        assert_eq!(res1.object_cids.len(), 1);

        // Commit to update spatial index
        let commit = commit_building(path.clone(), bid.clone(), Some("RP commit".into()));
        assert!(!commit.root_cid.is_empty());

        // Perform query
        let query_res = query_spatial_volume(path.clone(), bid.clone(), -5.0, -5.0, -5.0, 5.0, 5.0, 5.0);
        assert_eq!(query_res.len(), 3); // space, surface, and equipment

        // Verify CIDs are stable for identical inputs
        let res2 = ingest_room_plan(path.clone(), bid.clone(), geom1);
        assert_eq!(res1.space_cid, res2.space_cid);
        assert_eq!(res1.surface_cids[0], res2.surface_cids[0]);
        assert_eq!(res1.object_cids[0], res2.object_cids[0]);
    }
}
