//! Capture helpers: turn device/sensor payloads into content-addressed objects.
//!
//! Phase 1 focuses on Space, PointCloudChunk, and Annotation. ARKit / RoomPlan
//! run on-device; this module is the pure, testable conversion boundary.

use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::crypto::Keypair;
use crate::entity::EntityId;
use crate::error::Result;
use crate::object::{
    Aabb, AnnotationBody, BlobBody, Object, ObjectBody, PointCloudChunkBody, Pose, SpaceBody,
};
use crate::store::ObjectStore;

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Input for creating a Space object from RoomPlan / manual capture.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct SpaceCapture {
    /// Stable entity id. When `None`, a new [`EntityId`] is assigned on convert.
    /// Pass an existing id to create a **replacement version** of the same space.
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub pose: Pose,
    pub bounds: Option<Aabb>,
    pub floor: Option<crate::cid::Cid>,
    pub properties: BTreeMap<String, String>,
}

/// Packed XYZ point cloud from LiDAR / RoomPlan mesh sampling.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PointCloudCapture {
    pub pose: Pose,
    pub bounds: Option<Aabb>,
    /// Little-endian f32 triples: x0,y0,z0,x1,y1,z1,...
    pub points_xyz_f32_le: Vec<u8>,
    pub properties: BTreeMap<String, String>,
}

impl PointCloudCapture {
    /// Build from f32 coordinates (x,y,z interleaved).
    pub fn from_xyz(points: &[[f32; 3]], pose: Pose, bounds: Option<Aabb>) -> Self {
        let mut bytes = Vec::with_capacity(points.len() * 12);
        for p in points {
            bytes.extend_from_slice(&p[0].to_le_bytes());
            bytes.extend_from_slice(&p[1].to_le_bytes());
            bytes.extend_from_slice(&p[2].to_le_bytes());
        }
        let mut properties = BTreeMap::new();
        properties.insert("format".into(), "xyz_f32_le".into());
        properties.insert("source".into(), "capture".into());
        Self {
            pose,
            bounds,
            points_xyz_f32_le: bytes,
            properties,
        }
    }

    pub fn point_count(&self) -> u64 {
        (self.points_xyz_f32_le.len() / 12) as u64
    }
}

/// Text (or transcript) annotation with optional world pose.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnnotationCapture {
    pub text: String,
    pub transcript: Option<String>,
    pub pose: Pose,
    pub space: Option<crate::cid::Cid>,
    pub properties: BTreeMap<String, String>,
}

impl AnnotationCapture {
    pub fn new(text: impl Into<String>, pose: Pose) -> Self {
        Self {
            text: text.into(),
            transcript: None,
            pose,
            space: None,
            properties: BTreeMap::new(),
        }
    }
}

/// Convert a space capture into an unsigned Object.
///
/// Always stamps an [`EntityId`] (generated when the capture omits one) so
/// subsequent pose/property updates can supersede this version on commit/merge.
pub fn space_object(capture: &SpaceCapture) -> Object {
    let entity_id = capture
        .entity_id
        .clone()
        .unwrap_or_else(EntityId::new);
    Object::new_with_created(
        ObjectBody::Space(SpaceBody {
            entity_id: Some(entity_id),
            name: capture.name.clone(),
            floor: capture.floor,
            pose: Some(capture.pose.clone()),
            bounds: capture.bounds.clone(),
            properties: capture.properties.clone(),
        }),
        now_secs(),
    )
}

/// Convert a point-cloud capture into an unsigned Object with **inline** points.
///
/// Prefer [`put_point_cloud_chunk`] for production paths so payloads are tiered
/// into a separate Blob (skinny domain object + content-addressed bytes).
pub fn point_cloud_object(capture: &PointCloudCapture) -> Object {
    let mut props = capture.properties.clone();
    props
        .entry("format".into())
        .or_insert_with(|| "xyz_f32_le".into());
    Object::new_with_created(
        ObjectBody::PointCloudChunk(PointCloudChunkBody {
            pose: Some(capture.pose.clone()),
            bounds: capture.bounds.clone(),
            points: capture.points_xyz_f32_le.clone(),
            points_blob: None,
            point_count: capture.point_count(),
            properties: props,
        }),
        now_secs(),
    )
}

/// Put point payload as a Blob, return a skinny PointCloudChunk object (unsigned).
///
/// The blob is stored first; the returned object references it via `points_blob`
/// and keeps `points` empty.
pub fn put_point_cloud_chunk(
    store: &ObjectStore,
    capture: &PointCloudCapture,
) -> Result<Object> {
    let mut blob_props = BTreeMap::new();
    blob_props.insert("format".into(), "xyz_f32_le".into());
    blob_props.insert("role".into(), "point_cloud".into());
    let blob = Object::new_with_created(
        ObjectBody::Blob(BlobBody {
            content_type: Some("application/x-arxos-xyz-f32-le".into()),
            data: capture.points_xyz_f32_le.clone(),
            properties: blob_props,
        }),
        0, // stable timestamp for pure data blobs
    );
    let blob_cid = store.put(&blob)?;

    let mut props = capture.properties.clone();
    props
        .entry("format".into())
        .or_insert_with(|| "xyz_f32_le".into());
    props.insert("points_blob".into(), blob_cid.to_string());

    Ok(Object::new_with_created(
        ObjectBody::PointCloudChunk(PointCloudChunkBody {
            pose: Some(capture.pose.clone()),
            bounds: capture.bounds.clone(),
            points: Vec::new(),
            points_blob: Some(blob_cid),
            point_count: capture.point_count(),
            properties: props,
        }),
        now_secs(),
    ))
}

/// Resolve point bytes from a chunk (blob ref preferred, else legacy inline).
pub fn resolve_point_bytes(
    store: &ObjectStore,
    body: &PointCloudChunkBody,
) -> Result<Vec<u8>> {
    if let Some(cid) = &body.points_blob {
        let obj = store.get(cid)?;
        match obj.body {
            ObjectBody::Blob(b) => Ok(b.data),
            _ => Err(crate::error::Error::Validation(format!(
                "points_blob {cid} is not a Blob object"
            ))),
        }
    } else {
        Ok(body.points.clone())
    }
}

/// Convert an annotation capture into an unsigned Object.
pub fn annotation_object(capture: &AnnotationCapture) -> Object {
    Object::new_with_created(
        ObjectBody::Annotation(AnnotationBody {
            text: Some(capture.text.clone()),
            transcript: capture.transcript.clone(),
            media_ref: None,
            pose: Some(capture.pose.clone()),
            space: capture.space,
            properties: capture.properties.clone(),
        }),
        now_secs(),
    )
}

/// Sign an object if a keypair is provided.
pub fn maybe_sign(mut object: Object, keypair: Option<&Keypair>) -> Result<Object> {
    if let Some(kp) = keypair {
        object.sign(kp)?;
    }
    Ok(object)
}

/// Axis-aligned bounds from a list of XYZ points.
pub fn aabb_from_xyz(points: &[[f32; 3]]) -> Option<Aabb> {
    if points.is_empty() {
        return None;
    }
    let mut min = [f64::INFINITY; 3];
    let mut max = [f64::NEG_INFINITY; 3];
    for p in points {
        for i in 0..3 {
            let v = p[i] as f64;
            min[i] = min[i].min(v);
            max[i] = max[i].max(v);
        }
    }
    Some(Aabb { min, max })
}

/// Euclidean distance between two poses (position only).
pub fn pose_distance(a: &Pose, b: &Pose) -> f64 {
    let dx = a.position[0] - b.position[0];
    let dy = a.position[1] - b.position[1];
    let dz = a.position[2] - b.position[2];
    (dx * dx + dy * dy + dz * dz).sqrt()
}

/// Decompose a 4×4 column-major transform into a [`Pose`] (RoomPlan / ARKit).
///
/// `transform` must be 16 elements. Translation is column 3; rotation is the
/// upper-left 3×3 converted to a unit quaternion `(x,y,z,w)`.
pub fn pose_from_column_major_matrix(transform: &[f64]) -> crate::error::Result<Pose> {
    if transform.len() != 16 {
        return Err(crate::error::Error::Validation(format!(
            "transform matrix must have 16 elements, got {}",
            transform.len()
        )));
    }

    let tx = transform[12];
    let ty = transform[13];
    let tz = transform[14];

    let m00 = transform[0];
    let m10 = transform[4];
    let m20 = transform[8];
    let m01 = transform[1];
    let m11 = transform[5];
    let m21 = transform[9];
    let m02 = transform[2];
    let m12 = transform[6];
    let m22 = transform[10];

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

    let len = (qx * qx + qy * qy + qz * qz + qw * qw).sqrt();
    let orientation = if len > 0.0 {
        [qx / len, qy / len, qz / len, qw / len]
    } else {
        [0.0, 0.0, 0.0, 1.0]
    };

    Ok(Pose {
        position: [tx, ty, tz],
        orientation,
    })
}

/// Tight world-space AABB from a 4×4 column-major transform and local dimensions
/// `(width, height, depth)` (RoomPlan surface/object extents).
pub fn world_aabb_from_transform_and_dimensions(
    transform: &[f64],
    dimensions: &[f64],
) -> crate::error::Result<Aabb> {
    if transform.len() != 16 {
        return Err(crate::error::Error::Validation(format!(
            "transform must be 4x4 matrix (16 elements), got {}",
            transform.len()
        )));
    }
    if dimensions.len() != 3 {
        return Err(crate::error::Error::Validation(format!(
            "dimensions must have 3 elements, got {}",
            dimensions.len()
        )));
    }
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

        min_x = min_x.min(px);
        min_y = min_y.min(py);
        min_z = min_z.min(pz);
        max_x = max_x.max(px);
        max_y = max_y.max(py);
        max_z = max_z.max(pz);
    }

    Ok(Aabb {
        min: [min_x, min_y, min_z],
        max: [max_x, max_y, max_z],
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn point_cloud_pack_count() {
        let pts = [[0.0f32, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]];
        let cap = PointCloudCapture::from_xyz(&pts, Pose::default(), aabb_from_xyz(&pts));
        assert_eq!(cap.point_count(), 3);
        let obj = point_cloud_object(&cap);
        assert_eq!(obj.header.object_type.as_str(), "point_cloud_chunk");
        let cid = obj.cid().unwrap();
        assert!(!cid.to_string().is_empty());
    }

    #[test]
    fn point_cloud_tiered_blob_roundtrip() {
        use crate::store::ObjectStore;
        use tempfile::tempdir;

        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let pts = [[0.0f32, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]];
        let cap = PointCloudCapture::from_xyz(&pts, Pose::default(), aabb_from_xyz(&pts));
        let obj = put_point_cloud_chunk(&store, &cap).unwrap();
        if let ObjectBody::PointCloudChunk(ref b) = obj.body {
            assert!(b.points.is_empty());
            assert!(b.points_blob.is_some());
            assert_eq!(b.point_count, 3);
            let resolved = resolve_point_bytes(&store, b).unwrap();
            assert_eq!(resolved, cap.points_xyz_f32_le);
            // Skinny domain object is much smaller than inline payload + header.
            let domain_bytes = obj.to_canonical_bytes().unwrap();
            assert!(domain_bytes.len() < 512);
        } else {
            panic!("expected point cloud chunk");
        }
    }

    #[test]
    fn annotation_and_space_objects() {
        let space = space_object(&SpaceCapture {
                    entity_id: None,
            name: Some("Electrical".into()),
            pose: Pose {
                position: [1.0, 0.0, 2.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        });
        assert_eq!(space.header.object_type.as_str(), "space");

        let ann = annotation_object(&AnnotationCapture::new(
            "panel A",
            Pose {
                position: [1.1, 1.5, 2.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ));
        assert_eq!(ann.header.object_type.as_str(), "annotation");
    }
}
