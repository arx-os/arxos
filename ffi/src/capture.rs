//! Capture, commit, RoomPlan ingest, and annotation overlay FFI.

use std::collections::BTreeMap;
use std::str::FromStr;

use arxos_core::capture::{AnnotationCapture, PointCloudCapture, SpaceCapture};
use arxos_core::object::{BuildingId, Pose};
use arxos_core::repository::BuildingRepository;

use crate::{open_write, ArxosError};

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
/// Capture a space at a world pose.
///
/// `entity_id`: pass an existing id to create a replacement version of the
/// same room (commit/merge will collapse). `None` mints a new [`arxos_core::EntityId`]
/// and will **not** collapse with prior rooms.
pub fn capture_space(
    store_path: String,
    building_id: String,
    name: Option<String>,
    x: f64,
    y: f64,
    z: f64,
    entity_id: Option<String>,
) -> Result<FfiCapturePutResult, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let entity_id = match entity_id {
        Some(s) if !s.is_empty() => {
            Some(
                arxos_core::EntityId::from_str(&s).map_err(|e| ArxosError::InvalidInput {
                    message: e.to_string(),
                })?,
            )
        }
        _ => None,
    };
    let mut repo = open_write(&store_path, &bid)?;
    let res = repo.capture_space(&SpaceCapture {
        entity_id,
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
    let mut repo = open_write(&store_path, &bid)?;
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
    let mut repo = open_write(&store_path, &bid)?;
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
    let mut repo = open_write(&store_path, &bid)?;
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
    let mut repo = BuildingRepository::open_read(&store_path, &bid)?;
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

/// Ingest RoomPlan structured surfaces and objects as Facts, and stage.
///
/// Mapping lives in `arxos_core::capture::roomplan`. Doors/windows become
/// Openings hosted on the nearest wall. Apple UUIDs become stable EntityIds.
pub fn ingest_room_plan(
    store_path: String,
    building_id: String,
    geometry: RoomPlanGeometry,
) -> Result<IngestResult, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let mut repo = open_write(&store_path, &bid)?;
    let core_geom = arxos_core::capture::roomplan::RoomPlanGeometry {
        surfaces: geometry
            .surfaces
            .into_iter()
            .map(|s| arxos_core::capture::roomplan::RoomPlanSurface {
                id: s.id,
                category: s.category,
                transform: s.transform,
                dimensions: s.dimensions,
            })
            .collect(),
        objects: geometry
            .objects
            .into_iter()
            .map(|o| arxos_core::capture::roomplan::RoomPlanObject {
                id: o.id,
                category: o.category,
                transform: o.transform,
                dimensions: o.dimensions,
            })
            .collect(),
    };
    let staged = repo.ingest_room_plan(&core_geom)?;
    let mut surface_cids: Vec<String> = staged.surfaces.iter().map(|c| c.to_string()).collect();
    surface_cids.extend(staged.openings.iter().map(|c| c.to_string()));
    let object_cids: Vec<String> = staged.equipment.iter().map(|c| c.to_string()).collect();
    Ok(IngestResult {
        space_cid: staged.space.to_string(),
        surface_cids,
        object_cids,
    })
}
