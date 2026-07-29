//! Capture helpers: turn device/sensor payloads into content-addressed objects.
//!
//! Phase 1 focuses on Space, PointCloudChunk, and Annotation. ARKit / RoomPlan
//! run on-device; this module is the pure, testable conversion boundary.

use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::crypto::Keypair;
use crate::error::Result;
use crate::object::{
    Aabb, AnnotationBody, Object, ObjectBody, PointCloudChunkBody, Pose, SpaceBody,
};

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Input for creating a Space object from RoomPlan / manual capture.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct SpaceCapture {
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
pub fn space_object(capture: &SpaceCapture) -> Object {
    Object::new_with_created(
        ObjectBody::Space(SpaceBody {
            name: capture.name.clone(),
            floor: capture.floor,
            pose: Some(capture.pose.clone()),
            bounds: capture.bounds.clone(),
            properties: capture.properties.clone(),
        }),
        now_secs(),
    )
}

/// Convert a point-cloud capture into an unsigned Object.
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
            point_count: capture.point_count(),
            properties: props,
        }),
        now_secs(),
    )
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
    fn annotation_and_space_objects() {
        let space = space_object(&SpaceCapture {
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
