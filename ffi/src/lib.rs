//! UniFFI FFI static library implementation for Arxos iOS production path.
//!
//! All fallible public entry points return [`Result`] with [`ArxosError`] —
//! ordinary failures must never panic across the FFI boundary.

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use arxos_core::capture::{maybe_sign, AnnotationCapture, PointCloudCapture, SpaceCapture};
use arxos_core::cid::Cid;
use arxos_core::crypto::Keypair;
use arxos_core::object::{
    Aabb, BlobBody, BuildingId, EquipmentBody, Object, ObjectBody, Pose, SpaceBody, SurfaceBody,
};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::{RootBody, RootBuilder};
use arxos_core::store::ObjectStore;
use arxos_core::Error as CoreError;

/// UniFFI-facing error. Maps core and networking failures without panicking.
#[derive(Debug, thiserror::Error)]
pub enum ArxosError {
    #[error("not found: {message}")]
    NotFound { message: String },
    #[error("signature: {message}")]
    Signature { message: String },
    #[error("authorization: {message}")]
    Authorization { message: String },
    #[error("validation: {message}")]
    Validation { message: String },
    #[error("store: {message}")]
    Store { message: String },
    #[error("crypto: {message}")]
    Crypto { message: String },
    #[error("network: {message}")]
    Network { message: String },
    #[error("invalid input: {message}")]
    InvalidInput { message: String },
    #[error("internal: {message}")]
    Internal { message: String },
}

impl From<CoreError> for ArxosError {
    fn from(e: CoreError) -> Self {
        match e {
            CoreError::NotFound(message) => ArxosError::NotFound { message },
            CoreError::Signature(message) => ArxosError::Signature { message },
            CoreError::Authorization(message) => ArxosError::Authorization { message },
            CoreError::Validation(message) => ArxosError::Validation { message },
            CoreError::Store(message) => ArxosError::Store { message },
            CoreError::Crypto(message) => ArxosError::Crypto { message },
            CoreError::InvalidCid(message) => ArxosError::InvalidInput { message },
            CoreError::Serialization(message) | CoreError::Deserialization(message) => {
                ArxosError::Store { message }
            }
            CoreError::Schema(message) => ArxosError::Validation { message },
            CoreError::Io(err) => ArxosError::Store {
                message: err.to_string(),
            },
        }
    }
}

impl From<arxos_networking::NetError> for ArxosError {
    fn from(e: arxos_networking::NetError) -> Self {
        ArxosError::Network {
            message: e.to_string(),
        }
    }
}

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
) -> Result<ObjectPutResult, ArxosError> {
    let store = ObjectStore::open(&store_path)?;
    let obj = Object::new(ObjectBody::Blob(BlobBody {
        content_type,
        data,
        properties: BTreeMap::new(),
    }));
    let cid = store.put(&obj)?;
    Ok(ObjectPutResult {
        cid: cid.to_string(),
        object_type: "blob".into(),
    })
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

fn keypair_from_seed_hex(seed_hex: &str) -> Result<Keypair, ArxosError> {
    let seed_bytes = hex::decode(seed_hex).map_err(|e| ArxosError::InvalidInput {
        message: format!("invalid seed hex: {e}"),
    })?;
    if seed_bytes.len() != 32 {
        return Err(ArxosError::InvalidInput {
            message: format!("seed must be 32 bytes, got {}", seed_bytes.len()),
        });
    }
    let mut seed = [0u8; 32];
    seed.copy_from_slice(&seed_bytes);
    Ok(Keypair::from_seed(seed))
}

/// Create and store a signed root from existing object CID strings.
pub fn create_root(
    store_path: String,
    building_id: String,
    object_cids: Vec<String>,
    seed_hex: String,
    message: Option<String>,
) -> Result<RootCreateResult, ArxosError> {
    let store = ObjectStore::open(&store_path)?;
    let kp = keypair_from_seed_hex(&seed_hex)?;

    let mut set = BTreeSet::new();
    for s in &object_cids {
        set.insert(Cid::from_str(s).map_err(|e| ArxosError::InvalidInput {
            message: format!("invalid object cid '{s}': {e}"),
        })?);
    }
    let count = set.len() as u64;
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: format!("invalid building id: {e}"),
    })?;

    let mut builder = RootBuilder::new(bid.clone(), now_secs()).objects(set);
    if let Some(msg) = message {
        builder = builder.message(msg);
    }
    let (obj, root_cid) = builder.build_signed(&kp)?;
    {
        let root = RootBody::from_object(&obj)?;
        root.verify_with_store(&store)?;
    }
    store.put(&obj)?;

    Ok(RootCreateResult {
        root_cid: root_cid.to_string(),
        building_id: bid.to_string(),
        object_count: count,
    })
}

/// Show a root as a summary string, or None if the CID is absent from the store.
pub fn show_root(store_path: String, root_cid: String) -> Result<Option<String>, ArxosError> {
    let store = ObjectStore::open(&store_path)?;
    let cid = Cid::from_str(&root_cid).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    match store.get(&cid) {
        Err(CoreError::NotFound(_)) => return Ok(None),
        Err(e) => return Err(e.into()),
        Ok(obj) => {
            let root = RootBody::from_object(&obj)?;
            let active_count = root.materialize_active_objects(&store)?.len();
            Ok(Some(format!(
                "building_id={} previous={:?} objects={} authors={} message={:?} timestamp={}",
                root.building_id,
                root.previous_root.map(|c| c.to_string()),
                active_count,
                root.authors.len(),
                root.message,
                root.timestamp
            )))
        }
    }
}

// ─── Building repository + capture ───

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
pub fn init_building(
    store_path: String,
    name: Option<String>,
) -> Result<FfiBuildingSummary, ArxosError> {
    let repo = BuildingRepository::init(&store_path, name, None)?;
    Ok(summary_from_repo(&repo))
}

/// Open an existing building and materialize its head working set.
pub fn open_building(
    store_path: String,
    building_id: String,
) -> Result<FfiBuildingSummary, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let repo = BuildingRepository::open(&store_path, &bid)?;
    Ok(summary_from_repo(&repo))
}

/// List buildings in a store.
pub fn list_buildings(store_path: String) -> Result<Vec<FfiBuildingSummary>, ArxosError> {
    let list = BuildingRepository::list_buildings(&store_path)?;
    Ok(list
        .into_iter()
        .map(|r| FfiBuildingSummary {
            building_id: r.building_id.to_string(),
            name: r.name,
            head_root: r.head_root.map(|c| c.to_string()),
            building_object: r.building_object.map(|c| c.to_string()),
            staged_count: 0,
        })
        .collect())
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
) -> Result<FfiCapturePutResult, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = BuildingRepository::open(&store_path, &bid)?;
    let res = repo.capture_space(&SpaceCapture {
                    entity_id: None,
        name,
        pose: pose(x, y, z),
        bounds: None,
        floor: None,
        properties: BTreeMap::new(),
    })?;
    Ok(FfiCapturePutResult {
        cid: res.cid.to_string(),
        object_type: res.object_type.to_string(),
    })
}

/// Capture a text annotation at a world pose.
pub fn capture_annotation(
    store_path: String,
    building_id: String,
    text: String,
    x: f64,
    y: f64,
    z: f64,
) -> Result<FfiCapturePutResult, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = BuildingRepository::open(&store_path, &bid)?;
    let res = repo.capture_annotation(&AnnotationCapture::new(text, pose(x, y, z)))?;
    Ok(FfiCapturePutResult {
        cid: res.cid.to_string(),
        object_type: res.object_type.to_string(),
    })
}

/// Capture a packed XYZ f32 little-endian point cloud.
pub fn capture_point_cloud(
    store_path: String,
    building_id: String,
    points_xyz_f32_le: Vec<u8>,
    x: f64,
    y: f64,
    z: f64,
) -> Result<FfiCapturePutResult, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = BuildingRepository::open(&store_path, &bid)?;
    let mut properties = BTreeMap::new();
    properties.insert("format".into(), "xyz_f32_le".into());
    properties.insert("source".into(), "device".into());
    let res = repo.capture_point_cloud(&PointCloudCapture {
        pose: pose(x, y, z),
        bounds: None,
        points_xyz_f32_le,
        properties,
    })?;
    Ok(FfiCapturePutResult {
        cid: res.cid.to_string(),
        object_type: res.object_type.to_string(),
    })
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
) -> Result<FfiCommitSummary, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = BuildingRepository::open(&store_path, &bid)?;
    let res = repo.commit(message)?;
    Ok(FfiCommitSummary {
        root_cid: res.root_cid.to_string(),
        building_id: res.building_id.to_string(),
        object_count: res.object_count,
        previous_root: res.previous_root.map(|c| c.to_string()),
    })
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
) -> Result<Vec<FfiAnnotationOverlay>, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = BuildingRepository::open(&store_path, &bid)?;
    let hits = repo.annotations_near(&pose(x, y, z), radius_m)?;
    Ok(hits
        .into_iter()
        .map(|h| FfiAnnotationOverlay {
            cid: h.cid.to_string(),
            text: h.text,
            x: h.pose.position[0],
            y: h.pose.position[1],
            z: h.pose.position[2],
            distance_m: h.distance_m,
        })
        .collect())
}

// ─── Mobile production surface ───

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

fn pose_from_transform(transform: &[f64]) -> Result<Pose, ArxosError> {
    arxos_core::capture::pose_from_column_major_matrix(transform).map_err(Into::into)
}

fn world_aabb_from_transform_and_dimensions(
    transform: &[f64],
    dimensions: &[f64],
) -> Result<Aabb, ArxosError> {
    arxos_core::capture::world_aabb_from_transform_and_dimensions(transform, dimensions)
        .map_err(Into::into)
}

/// Stable entity id from a RoomPlan surface/object identifier.
fn roomplan_entity_id(kind: &str, rp_id: &str) -> arxos_core::EntityId {
    if rp_id.is_empty() {
        arxos_core::EntityId::new()
    } else {
        arxos_core::EntityId::from(format!("rp:{kind}:{rp_id}"))
    }
}

/// Deterministic space entity id from the set of RoomPlan identifiers.
fn roomplan_space_entity_id(geometry: &RoomPlanGeometry) -> arxos_core::EntityId {
    let mut parts: Vec<&str> = geometry
        .surfaces
        .iter()
        .map(|s| s.id.as_str())
        .chain(geometry.objects.iter().map(|o| o.id.as_str()))
        .collect();
    parts.sort_unstable();
    let material = parts.join("|");
    let digest = blake3::hash(material.as_bytes());
    let hex = hex::encode(&digest.as_bytes()[..16]);
    arxos_core::EntityId::from(format!("rp:space:{hex}"))
}

/// Ingest RoomPlan structured surfaces and objects, group into a Space, and stage.
pub fn ingest_room_plan(
    store_path: String,
    building_id: String,
    geometry: RoomPlanGeometry,
) -> Result<IngestResult, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = BuildingRepository::open(&store_path, &bid)?;
    let kp = repo.keypair().cloned();

    let mut surface_objs = Vec::new();
    let mut object_objs = Vec::new();
    let mut room_bounds: Option<Aabb> = None;

    for s in &geometry.surfaces {
        let pose = pose_from_transform(&s.transform)?;
        let bounds = world_aabb_from_transform_and_dimensions(&s.transform, &s.dimensions)?;

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
        properties.insert(
            "width".into(),
            s.dimensions.first().cloned().unwrap_or(0.0).to_string(),
        );
        properties.insert(
            "height".into(),
            s.dimensions.get(1).cloned().unwrap_or(0.0).to_string(),
        );
        properties.insert(
            "depth".into(),
            s.dimensions.get(2).cloned().unwrap_or(0.0).to_string(),
        );

        surface_objs.push((s.id.clone(), s.category.clone(), pose, bounds, properties));
    }

    for o in &geometry.objects {
        let pose = pose_from_transform(&o.transform)?;
        let bounds = world_aabb_from_transform_and_dimensions(&o.transform, &o.dimensions)?;

        if let Some(ref mut rb) = room_bounds {
            rb.min[0] = rb.min[0].min(bounds.min[0]);
            rb.min[1] = rb.min[1].min(bounds.min[1]);
            rb.min[2] = rb.min[2].min(bounds.min[2]);
            rb.max[0] = rb.max[0].max(bounds.max[0]);
            rb.max[1] = rb.max[1].max(bounds.max[1]);
            rb.max[2] = rb.max[2].max(bounds.max[2]);
        } else {
            room_bounds = Some(bounds);
        }

        let mut properties = BTreeMap::new();
        properties.insert("identifier".into(), o.id.clone());
        properties.insert("source".into(), "roomplan".into());

        object_objs.push((o.id.clone(), o.category.clone(), pose, properties));
    }

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

    // Stable entity ids from RoomPlan identifiers so rescans of the same
    // geometry produce the same CIDs when created timestamps are fixed.
    let space_entity = roomplan_space_entity_id(&geometry);

    let mut space_props = BTreeMap::new();
    space_props.insert("source".into(), "roomplan".into());
    let space_body = SpaceBody {
        entity_id: Some(space_entity),
        name: Some("RoomPlan Room".into()),
        floor: None,
        pose: Some(space_pose),
        bounds: room_bounds,
        properties: space_props,
    };
    let space_object = Object::new_with_created(ObjectBody::Space(space_body), 0);
    let signed_space = maybe_sign(space_object, kp.as_ref())?;
    let space_cid = repo.stage_captured_object(signed_space)?.cid;

    let mut surface_cids = Vec::new();
    for (rp_id, category, pose, bounds, properties) in surface_objs {
        let surface_body = SurfaceBody {
            entity_id: Some(roomplan_entity_id("surface", &rp_id)),
            space: Some(space_cid),
            pose: Some(pose),
            bounds: Some(bounds),
            surface_kind: Some(category),
            properties,
        };
        let surface_object = Object::new_with_created(ObjectBody::Surface(surface_body), 0);
        let signed_surface = maybe_sign(surface_object, kp.as_ref())?;
        let cid = repo.stage_captured_object(signed_surface)?.cid;
        surface_cids.push(cid.to_string());
    }

    let mut object_cids = Vec::new();
    for (rp_id, category, pose, mut properties) in object_objs {
        properties.insert("space".into(), space_cid.to_string());
        let equipment_body = EquipmentBody {
            entity_id: Some(roomplan_entity_id("equipment", &rp_id)),
            name: Some(category.clone()),
            equipment_kind: Some(category),
            pose: Some(pose),
            system: None,
            properties,
        };
        let equipment_object = Object::new_with_created(ObjectBody::Equipment(equipment_body), 0);
        let signed_equipment = maybe_sign(equipment_object, kp.as_ref())?;
        let cid = repo.stage_captured_object(signed_equipment)?.cid;
        object_cids.push(cid.to_string());
    }

    Ok(IngestResult {
        space_cid: space_cid.to_string(),
        surface_cids,
        object_cids,
    })
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
) -> Result<Vec<SpatialQueryResult>, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let repo = BuildingRepository::open(&store_path, &bid)?;
    let volume =
        arxos_core::QueryVolume::from_min_max([min_x, min_y, min_z], [max_x, max_y, max_z]);

    let hits = repo.query_volume(&volume)?;
    let mut out = Vec::new();
    for hit in hits {
        if let Ok(obj) = repo.store().get(&hit.object) {
            let object_type = obj.header.object_type.as_str().to_string();
            let (name, pose_pos, properties) = match &obj.body {
                ObjectBody::Space(s) => {
                    let pos = s
                        .pose
                        .as_ref()
                        .map(|p| p.position)
                        .unwrap_or([0.0, 0.0, 0.0]);
                    (s.name.clone(), pos, s.properties.clone())
                }
                ObjectBody::Surface(s) => {
                    let pos = s
                        .pose
                        .as_ref()
                        .map(|p| p.position)
                        .unwrap_or([0.0, 0.0, 0.0]);
                    (None, pos, s.properties.clone())
                }
                ObjectBody::Equipment(e) => {
                    let pos = e
                        .pose
                        .as_ref()
                        .map(|p| p.position)
                        .unwrap_or([0.0, 0.0, 0.0]);
                    (e.name.clone(), pos, e.properties.clone())
                }
                ObjectBody::Annotation(a) => {
                    let pos = a
                        .pose
                        .as_ref()
                        .map(|p| p.position)
                        .unwrap_or([0.0, 0.0, 0.0]);
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
    Ok(out)
}

/// Merge remote head root.
pub fn merge_building_root(
    store_path: String,
    building_id: String,
    other_root_cid: String,
    message: Option<String>,
) -> Result<MergeSummary, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = BuildingRepository::open(&store_path, &bid)?;
    let other = Cid::from_str(&other_root_cid).map_err(|e| ArxosError::InvalidInput {
        message: format!("invalid other root cid: {e}"),
    })?;
    let res = repo.merge_root(other, message)?;
    Ok(MergeSummary {
        root_cid: res.root_cid.to_string(),
        object_count: res.object_count,
        kept: res.kept,
        deduped_annotations: res.deduped_annotations,
        spatial_index_root: res.spatial_index_root.map(|c| c.to_string()),
        parent_a: res.parents.0.to_string(),
        parent_b: res.parents.1.to_string(),
    })
}

/// Pull a remote root closure using a temporary local Tokio executor runtime.
pub fn pull_remote_root(
    store_path: String,
    peer_ticket: String,
    root_cid: String,
    building_id: Option<String>,
    set_head: bool,
    allow_untrusted: bool,
) -> Result<PullResultSummary, ArxosError> {
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .map_err(|e| ArxosError::Internal {
            message: format!("tokio runtime: {e}"),
        })?;

    rt.block_on(async move {
        let node = arxos_networking::IrohNode::bind(std::path::Path::new(&store_path)).await?;

        let result = arxos_networking::sync::pull_root_with_options(
            &node,
            &peer_ticket,
            std::path::Path::new(&store_path),
            &root_cid,
            building_id.as_deref(),
            set_head,
            allow_untrusted,
        )
        .await?;

        node.close().await;

        Ok(PullResultSummary {
            root_cid: result.root_cid.to_string(),
            objects_stored: result.objects_stored,
            objects_skipped: result.objects_skipped_existing,
            adopted_root: result.adopted.as_ref().map(|a| a.root_cid.to_string()),
        })
    })
}

/// Export to USD file.
pub fn export_usd(
    store_path: String,
    building_id: String,
    output_path: String,
) -> Result<(), ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let opts = arxos_usd::ExportOptions::default();
    let content = arxos_usd::export_building_usda(std::path::Path::new(&store_path), &bid, &opts)
        .map_err(|e| ArxosError::Store {
            message: e.to_string(),
        })?;
    std::fs::write(&output_path, content).map_err(|e| ArxosError::Store {
        message: format!("write {}: {e}", output_path),
    })?;
    Ok(())
}

/// Export to IFC file.
pub fn export_ifc(
    store_path: String,
    building_id: String,
    output_path: String,
) -> Result<(), ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let opts = arxos_ifc::ExportOptions::default();
    let content = arxos_ifc::export_building_ifc(std::path::Path::new(&store_path), &bid, &opts)
        .map_err(|e| ArxosError::Store {
            message: e.to_string(),
        })?;
    std::fs::write(&output_path, content).map_err(|e| ArxosError::Store {
        message: format!("write {}: {e}", output_path),
    })?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_matrix_to_pose_conversion() {
        let identity = vec![
            1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.5, -2.0, 3.5, 1.0,
        ];
        let p = pose_from_transform(&identity).unwrap();
        assert_eq!(p.position, [1.5, -2.0, 3.5]);
        assert!((p.orientation[0] - 0.0).abs() < 1e-5);
        assert!((p.orientation[1] - 0.0).abs() < 1e-5);
        assert!((p.orientation[2] - 0.0).abs() < 1e-5);
        assert!((p.orientation[3] - 1.0).abs() < 1e-5);

        let dims = vec![2.0, 4.0, 6.0];
        let bounds = world_aabb_from_transform_and_dimensions(&identity, &dims).unwrap();
        assert_eq!(bounds.min, [0.5, -4.0, 0.5]);
        assert_eq!(bounds.max, [2.5, 0.0, 6.5]);
    }

    #[test]
    fn bad_transform_returns_error_not_panic() {
        let err = pose_from_transform(&[1.0, 2.0]).unwrap_err();
        assert!(
            matches!(err, ArxosError::Validation { .. }),
            "expected Validation, got {err:?}"
        );
    }

    #[test]
    fn open_missing_building_returns_error() {
        let dir = tempdir().unwrap();
        let path = dir.path().to_str().unwrap().to_string();
        let err = open_building(path, "01NOTAREALBUILDINGID00000000".into()).unwrap_err();
        assert!(matches!(err, ArxosError::NotFound { .. }));
    }

    #[test]
    fn unauthorized_commit_surfaces_as_authorization_error() {
        let dir = tempdir().unwrap();
        let path = dir.path().to_str().unwrap().to_string();
        let summary = init_building(path.clone(), Some("Auth".into())).unwrap();
        let bid = summary.building_id;
        // Overwrite device seed with an outsider key (not a controller).
        let outsider = Keypair::generate();
        let seed_path = std::path::Path::new(&path).join("keys").join("device.seed");
        std::fs::write(&seed_path, outsider.seed()).unwrap();

        capture_annotation(
            path.clone(),
            bid.clone(),
            "note".into(),
            0.0,
            0.0,
            0.0,
        )
        .unwrap();
        let err = commit_building(path, bid, Some("should fail".into())).unwrap_err();
        assert!(
            matches!(err, ArxosError::Authorization { .. }),
            "expected Authorization, got {err:?}"
        );
    }

    #[test]
    fn test_ingest_room_plan_spatial_query() {
        let dir = tempdir().unwrap();
        let path = dir.path().to_str().unwrap().to_string();

        let summary = init_building(path.clone(), Some("RoomPlan Site".into())).unwrap();
        let bid = summary.building_id;

        let wall = FfiRoomPlanSurface {
            id: "wall-1".into(),
            category: "wall".into(),
            transform: vec![
                1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 2.0, 0.0, 0.0, 1.0,
            ],
            dimensions: vec![0.1, 2.5, 4.0],
        };

        let chair = FfiRoomPlanObject {
            id: "chair-1".into(),
            category: "chair".into(),
            transform: vec![
                1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0,
            ],
            dimensions: vec![0.6, 0.8, 0.6],
        };

        let geom1 = RoomPlanGeometry {
            surfaces: vec![wall.clone()],
            objects: vec![chair.clone()],
        };

        let res1 = ingest_room_plan(path.clone(), bid.clone(), geom1.clone()).unwrap();
        assert!(!res1.space_cid.is_empty());
        assert_eq!(res1.surface_cids.len(), 1);
        assert_eq!(res1.object_cids.len(), 1);

        let commit = commit_building(path.clone(), bid.clone(), Some("RP commit".into())).unwrap();
        assert!(!commit.root_cid.is_empty());

        let query_res =
            query_spatial_volume(path.clone(), bid.clone(), -5.0, -5.0, -5.0, 5.0, 5.0, 5.0)
                .unwrap();
        assert_eq!(query_res.len(), 3);

        let res2 = ingest_room_plan(path.clone(), bid.clone(), geom1).unwrap();
        assert_eq!(res1.space_cid, res2.space_cid);
        assert_eq!(res1.surface_cids[0], res2.surface_cids[0]);
        assert_eq!(res1.object_cids[0], res2.object_cids[0]);
    }
}
