//! Content-addressed objects: header + typed body.

use std::collections::BTreeMap;
use std::fmt;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use ulid::Ulid;

use crate::canonical::{canonicalize_f64, from_cbor, is_finite_f64, to_canonical_cbor};
use crate::cid::Cid;
use crate::crypto::{AuthorSignature, Keypair, PublicKey};
use crate::entity::EntityId;
use crate::error::{Error, Result};
use crate::root::RootBody;

/// Stable building identifier (ULID string for Phase 0; DID later).
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct BuildingId(String);

impl BuildingId {
    /// Generate a new random building ID.
    pub fn new() -> Self {
        Self(Ulid::new().to_string())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl Default for BuildingId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for BuildingId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl FromStr for BuildingId {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        if s.is_empty() {
            return Err(Error::Validation("building id must not be empty".into()));
        }
        Ok(BuildingId(s.to_string()))
    }
}

impl From<String> for BuildingId {
    fn from(s: String) -> Self {
        BuildingId(s)
    }
}

/// Object type tag (schema discriminator).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ObjectType {
    Building,
    Floor,
    Space,
    Surface,
    Opening,
    Equipment,
    /// Pipe / conduit / cable run (polyline + optional diameter).
    Run,
    System,
    Circuit,
    Sensor,
    Fixture,
    Annotation,
    PointCloudChunk,
    Mesh,
    BoundingVolume,
    Relationship,
    SpatialIndexNode,
    Root,
    Provenance,
    /// Opaque / application-defined for early experiments.
    Blob,
}

impl ObjectType {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Building => "building",
            Self::Floor => "floor",
            Self::Space => "space",
            Self::Surface => "surface",
            Self::Opening => "opening",
            Self::Equipment => "equipment",
            Self::Run => "run",
            Self::System => "system",
            Self::Circuit => "circuit",
            Self::Sensor => "sensor",
            Self::Fixture => "fixture",
            Self::Annotation => "annotation",
            Self::PointCloudChunk => "point_cloud_chunk",
            Self::Mesh => "mesh",
            Self::BoundingVolume => "bounding_volume",
            Self::Relationship => "relationship",
            Self::SpatialIndexNode => "spatial_index_node",
            Self::Root => "root",
            Self::Provenance => "provenance",
            Self::Blob => "blob",
        }
    }
}

impl fmt::Display for ObjectType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

impl FromStr for ObjectType {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        match s {
            "building" => Ok(Self::Building),
            "floor" => Ok(Self::Floor),
            "space" => Ok(Self::Space),
            "surface" => Ok(Self::Surface),
            "opening" => Ok(Self::Opening),
            "equipment" => Ok(Self::Equipment),
            "run" => Ok(Self::Run),
            "system" => Ok(Self::System),
            "circuit" => Ok(Self::Circuit),
            "sensor" => Ok(Self::Sensor),
            "fixture" => Ok(Self::Fixture),
            "annotation" => Ok(Self::Annotation),
            "point_cloud_chunk" => Ok(Self::PointCloudChunk),
            "mesh" => Ok(Self::Mesh),
            "bounding_volume" => Ok(Self::BoundingVolume),
            "relationship" => Ok(Self::Relationship),
            "spatial_index_node" => Ok(Self::SpatialIndexNode),
            "root" => Ok(Self::Root),
            "provenance" => Ok(Self::Provenance),
            "blob" => Ok(Self::Blob),
            other => Err(Error::Schema(format!("unknown object type: {other}"))),
        }
    }
}

/// Object header: type, schema version, creation metadata, optional signature.
///
/// Signature covers the canonical CBOR of the *unsigned* object (header without
/// signature + body). Author is the signer's public key when present.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObjectHeader {
    pub object_type: ObjectType,
    pub schema_version: u32,
    /// Unix timestamp in seconds.
    pub created: u64,
    pub author: Option<PublicKey>,
    pub signature: Option<AuthorSignature>,
}

/// Typed object payload. All cross-object references are CIDs only.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "data", rename_all = "snake_case")]
pub enum ObjectBody {
    Building(BuildingBody),
    Floor(FloorBody),
    Space(SpaceBody),
    Surface(SurfaceBody),
    Opening(OpeningBody),
    Equipment(EquipmentBody),
    Run(RunBody),
    System(SystemBody),
    Circuit(CircuitBody),
    Sensor(SensorBody),
    Fixture(FixtureBody),
    Annotation(AnnotationBody),
    PointCloudChunk(PointCloudChunkBody),
    Mesh(MeshBody),
    BoundingVolume(BoundingVolumeBody),
    Relationship(RelationshipBody),
    SpatialIndexNode(SpatialIndexNodeBody),
    Root(RootBody),
    Provenance(ProvenanceBody),
    Blob(BlobBody),
}

impl ObjectBody {
    /// Fold geometry floats in place. Errors on NaN / ±Inf.
    pub fn canonicalize_geometry(&mut self) -> Result<()> {
        match self {
            Self::Floor(b) => {
                b.elevation_m = canonicalize_f64(b.elevation_m)?;
            }
            Self::Space(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
                if let Some(a) = &mut b.bounds {
                    a.canonicalize()?;
                }
            }
            Self::Surface(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
                if let Some(a) = &mut b.bounds {
                    a.canonicalize()?;
                }
                canonicalize_fact_fields(&mut b.extent, &mut b.sigma_mm)?;
            }
            Self::Opening(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
                canonicalize_fact_fields(&mut b.extent, &mut b.sigma_mm)?;
            }
            Self::Equipment(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
                canonicalize_fact_fields(&mut b.extent, &mut b.sigma_mm)?;
            }
            Self::Run(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
                for p in &mut b.points {
                    for v in p {
                        *v = canonicalize_f64(*v)?;
                    }
                }
                if let Some(d) = &mut b.diameter_m {
                    *d = canonicalize_f64(*d)?;
                    if *d < 0.0 {
                        return Err(Error::Validation(
                            "run.diameter_m must not be negative".into(),
                        ));
                    }
                }
                canonicalize_fact_fields(&mut b.extent, &mut b.sigma_mm)?;
            }
            Self::Sensor(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
            }
            Self::Fixture(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
            }
            Self::Annotation(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
            }
            Self::PointCloudChunk(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
                if let Some(a) = &mut b.bounds {
                    a.canonicalize()?;
                }
            }
            Self::Mesh(b) => {
                if let Some(p) = &mut b.pose {
                    p.canonicalize()?;
                }
                if let Some(a) = &mut b.bounds {
                    a.canonicalize()?;
                }
            }
            Self::BoundingVolume(b) => {
                b.bounds.canonicalize()?;
            }
            Self::SpatialIndexNode(b) => {
                b.bounds.canonicalize()?;
            }
            Self::Building(_)
            | Self::System(_)
            | Self::Circuit(_)
            | Self::Relationship(_)
            | Self::Root(_)
            | Self::Provenance(_)
            | Self::Blob(_) => {}
        }
        Ok(())
    }

    /// Reject non-finite geometry (does not mutate).
    pub fn validate_geometry(&self) -> Result<()> {
        match self {
            Self::Floor(b) => {
                if !is_finite_f64(b.elevation_m) {
                    return Err(Error::Validation(
                        "floor.elevation_m is not finite".into(),
                    ));
                }
            }
            Self::Space(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
                if let Some(a) = &b.bounds {
                    a.validate_finite()?;
                }
            }
            Self::Surface(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
                if let Some(a) = &b.bounds {
                    a.validate_finite()?;
                }
                validate_fact_fields(&b.extent, &b.sigma_mm)?;
            }
            Self::Opening(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
                validate_fact_fields(&b.extent, &b.sigma_mm)?;
            }
            Self::Equipment(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
                validate_fact_fields(&b.extent, &b.sigma_mm)?;
            }
            Self::Run(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
                for p in &b.points {
                    for (i, &v) in p.iter().enumerate() {
                        if !is_finite_f64(v) {
                            return Err(Error::Validation(format!(
                                "run.points component [{i}] is not finite"
                            )));
                        }
                    }
                }
                if let Some(d) = b.diameter_m {
                    if !is_finite_f64(d) {
                        return Err(Error::Validation(
                            "run.diameter_m is not finite".into(),
                        ));
                    }
                    if d < 0.0 {
                        return Err(Error::Validation(
                            "run.diameter_m must not be negative".into(),
                        ));
                    }
                }
                validate_fact_fields(&b.extent, &b.sigma_mm)?;
            }
            Self::Sensor(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
            }
            Self::Fixture(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
            }
            Self::Annotation(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
            }
            Self::PointCloudChunk(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
                if let Some(a) = &b.bounds {
                    a.validate_finite()?;
                }
            }
            Self::Mesh(b) => {
                if let Some(p) = &b.pose {
                    p.validate_finite()?;
                }
                if let Some(a) = &b.bounds {
                    a.validate_finite()?;
                }
            }
            Self::BoundingVolume(b) => {
                b.bounds.validate_finite()?;
            }
            Self::SpatialIndexNode(b) => {
                b.bounds.validate_finite()?;
            }
            Self::Building(_)
            | Self::System(_)
            | Self::Circuit(_)
            | Self::Relationship(_)
            | Self::Root(_)
            | Self::Provenance(_)
            | Self::Blob(_) => {}
        }
        Ok(())
    }

    pub fn object_type(&self) -> ObjectType {
        match self {
            Self::Building(_) => ObjectType::Building,
            Self::Floor(_) => ObjectType::Floor,
            Self::Space(_) => ObjectType::Space,
            Self::Surface(_) => ObjectType::Surface,
            Self::Opening(_) => ObjectType::Opening,
            Self::Equipment(_) => ObjectType::Equipment,
            Self::Run(_) => ObjectType::Run,
            Self::System(_) => ObjectType::System,
            Self::Circuit(_) => ObjectType::Circuit,
            Self::Sensor(_) => ObjectType::Sensor,
            Self::Fixture(_) => ObjectType::Fixture,
            Self::Annotation(_) => ObjectType::Annotation,
            Self::PointCloudChunk(_) => ObjectType::PointCloudChunk,
            Self::Mesh(_) => ObjectType::Mesh,
            Self::BoundingVolume(_) => ObjectType::BoundingVolume,
            Self::Relationship(_) => ObjectType::Relationship,
            Self::SpatialIndexNode(_) => ObjectType::SpatialIndexNode,
            Self::Root(_) => ObjectType::Root,
            Self::Provenance(_) => ObjectType::Provenance,
            Self::Blob(_) => ObjectType::Blob,
        }
    }
}

/// 3D pose in building-local coordinates (meters, right-handed Y-up for Phase 0).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Pose {
    pub position: [f64; 3],
    /// Unit quaternion (x, y, z, w).
    pub orientation: [f64; 4],
}

impl Default for Pose {
    fn default() -> Self {
        Self {
            position: [0.0, 0.0, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        }
    }
}

impl Pose {
    /// Fail if any component is NaN or ±Inf.
    pub fn validate_finite(&self) -> Result<()> {
        for (i, &v) in self.position.iter().enumerate() {
            if !is_finite_f64(v) {
                return Err(Error::Validation(format!(
                    "pose.position[{i}] is not finite"
                )));
            }
        }
        for (i, &v) in self.orientation.iter().enumerate() {
            if !is_finite_f64(v) {
                return Err(Error::Validation(format!(
                    "pose.orientation[{i}] is not finite"
                )));
            }
        }
        Ok(())
    }

    /// Apply the float CID policy in place: finite-only, `-0.0` → `+0.0`,
    /// quaternion hemisphere `(w, x, y, z)` first non-zero `>= 0`.
    pub fn canonicalize(&mut self) -> Result<()> {
        self.validate_finite()?;
        for v in &mut self.position {
            *v = canonicalize_f64(*v)?;
        }
        for v in &mut self.orientation {
            *v = canonicalize_f64(*v)?;
        }
        // Stored as (x, y, z, w). Hemisphere key is (w, x, y, z).
        let key = [
            self.orientation[3],
            self.orientation[0],
            self.orientation[1],
            self.orientation[2],
        ];
        let flip = key
            .iter()
            .copied()
            .find(|&c| c != 0.0)
            .map(|c| c < 0.0)
            .unwrap_or(false);
        if flip {
            for v in &mut self.orientation {
                *v = canonicalize_f64(-*v)?;
            }
        }
        Ok(())
    }

    /// Rotate a vector by this pose's quaternion (x, y, z, w).
    pub fn rotate_vector(&self, v: [f64; 3]) -> [f64; 3] {
        let [qx, qy, qz, qw] = self.orientation;
        // t = 2 * cross(q_xyz, v)
        let tx = 2.0 * (qy * v[2] - qz * v[1]);
        let ty = 2.0 * (qz * v[0] - qx * v[2]);
        let tz = 2.0 * (qx * v[1] - qy * v[0]);
        // v + qw * t + cross(q_xyz, t)
        [
            v[0] + qw * tx + (qy * tz - qz * ty),
            v[1] + qw * ty + (qz * tx - qx * tz),
            v[2] + qw * tz + (qx * ty - qy * tx),
        ]
    }

    /// Local +X axis in world coordinates.
    pub fn local_x(&self) -> [f64; 3] {
        self.rotate_vector([1.0, 0.0, 0.0])
    }

    /// Local +Y axis in world coordinates (building-up for identity / RoomPlan walls).
    pub fn local_y(&self) -> [f64; 3] {
        self.rotate_vector([0.0, 1.0, 0.0])
    }

    /// Local +Z axis in world coordinates (plane-rect surface normal).
    pub fn local_z(&self) -> [f64; 3] {
        self.rotate_vector([0.0, 0.0, 1.0])
    }
}

/// Axis-aligned bounding box.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Aabb {
    pub min: [f64; 3],
    pub max: [f64; 3],
}

impl Aabb {
    /// Fail if any corner component is NaN or ±Inf.
    pub fn validate_finite(&self) -> Result<()> {
        for (i, &v) in self.min.iter().enumerate() {
            if !is_finite_f64(v) {
                return Err(Error::Validation(format!("aabb.min[{i}] is not finite")));
            }
        }
        for (i, &v) in self.max.iter().enumerate() {
            if !is_finite_f64(v) {
                return Err(Error::Validation(format!("aabb.max[{i}] is not finite")));
            }
        }
        Ok(())
    }

    /// Apply the float CID policy: finite-only, `-0.0` → `+0.0`, then
    /// swap inverted axes (`min[i] <= max[i]`).
    pub fn canonicalize(&mut self) -> Result<()> {
        self.validate_finite()?;
        for v in &mut self.min {
            *v = canonicalize_f64(*v)?;
        }
        for v in &mut self.max {
            *v = canonicalize_f64(*v)?;
        }
        self.normalize();
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BuildingBody {
    pub building_id: BuildingId,
    pub name: Option<String>,
    pub controller_keys: Vec<PublicKey>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FloorBody {
    /// Stable identity across pose/property updates. `None` = legacy pure-CID.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub building_id: BuildingId,
    pub name: Option<String>,
    pub level_index: i32,
    pub elevation_m: f64,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpaceBody {
    /// Stable identity across pose/property updates. `None` = legacy pure-CID.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub floor: Option<Cid>,
    pub pose: Option<Pose>,
    pub bounds: Option<Aabb>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct SurfaceBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub space: Option<Cid>,
    pub pose: Option<Pose>,
    pub bounds: Option<Aabb>,
    pub surface_kind: Option<String>,
    /// Width, height, optional depth (meters). RoomPlan `dimensions` map here.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub extent: Option<[f64; 3]>,
    /// 1σ positional uncertainty in millimeters. Missing = unweighted (+inf).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sigma_mm: Option<f64>,
    /// Independent observations fused into this version. Missing decodes as 0;
    /// [`effective_support_count`] treats 0 as 1 when pose/extent are present.
    #[serde(default)]
    pub support_count: u32,
    /// Evidence blobs / keyframes. Never used by realization.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub evidence: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct OpeningBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub host_surface: Option<Cid>,
    /// Host wall identity that survives host version collapse.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub host_entity: Option<EntityId>,
    pub pose: Option<Pose>,
    pub opening_kind: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub extent: Option<[f64; 3]>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sigma_mm: Option<f64>,
    #[serde(default)]
    pub support_count: u32,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub evidence: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct EquipmentBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub equipment_kind: Option<String>,
    pub pose: Option<Pose>,
    pub system: Option<Cid>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub extent: Option<[f64; 3]>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sigma_mm: Option<f64>,
    #[serde(default)]
    pub support_count: u32,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub evidence: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

/// Pipe / conduit / cable: polyline + optional diameter.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct RunBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub run_kind: Option<String>,
    pub pose: Option<Pose>,
    /// Polyline in building-local meters.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub points: Vec<[f64; 3]>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub diameter_m: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub extent: Option<[f64; 3]>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sigma_mm: Option<f64>,
    #[serde(default)]
    pub support_count: u32,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub evidence: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SystemBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub system_kind: Option<String>,
    pub members: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CircuitBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub panel: Option<Cid>,
    pub members: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SensorBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub sensor_kind: Option<String>,
    pub pose: Option<Pose>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FixtureBody {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entity_id: Option<EntityId>,
    pub name: Option<String>,
    pub fixture_kind: Option<String>,
    pub pose: Option<Pose>,
    pub circuit: Option<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnnotationBody {
    pub text: Option<String>,
    pub transcript: Option<String>,
    pub media_ref: Option<Cid>,
    pub pose: Option<Pose>,
    pub space: Option<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PointCloudChunkBody {
    pub pose: Option<Pose>,
    pub bounds: Option<Aabb>,
    /// Legacy inline payload. Prefer [`Self::points_blob`] for new captures.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub points: Vec<u8>,
    /// Content-addressed blob holding packed point bytes (e.g. xyz f32 LE).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub points_blob: Option<Cid>,
    pub point_count: u64,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MeshBody {
    pub pose: Option<Pose>,
    pub bounds: Option<Aabb>,
    /// Legacy inline vertices. Prefer [`Self::vertices_blob`].
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub vertices: Vec<u8>,
    /// Legacy inline indices. Prefer [`Self::indices_blob`].
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub indices: Vec<u8>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub vertices_blob: Option<Cid>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub indices_blob: Option<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BoundingVolumeBody {
    pub bounds: Aabb,
    pub target: Option<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RelationshipBody {
    pub rel_type: String,
    pub from: Cid,
    pub to: Cid,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpatialIndexNodeBody {
    pub bounds: Aabb,
    pub children: Vec<Cid>,
    pub object_refs: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProvenanceBody {
    pub subject: Cid,
    pub statement: String,
    pub evidence: Vec<Cid>,
    pub properties: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BlobBody {
    pub content_type: Option<String>,
    pub data: Vec<u8>,
    pub properties: BTreeMap<String, String>,
}

/// Immutable content-addressed object.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Object {
    pub header: ObjectHeader,
    pub body: ObjectBody,
}

/// Current schema version for newly created objects.
///
/// Readers accept [`MIN_SCHEMA_VERSION`]..=[`SCHEMA_VERSION`]. v2 adds optional
/// Fact fields (`extent`, `sigma_mm`, `support_count`, `evidence`, `host_entity`)
/// and `ObjectType::Run`. v1 objects still decode (missing fields default).
pub const SCHEMA_VERSION: u32 = 2;

/// Oldest schema version this reader will load.
pub const MIN_SCHEMA_VERSION: u32 = 1;

/// True when `v` is a schema this reader accepts.
pub fn schema_version_supported(v: u32) -> bool {
    (MIN_SCHEMA_VERSION..=SCHEMA_VERSION).contains(&v)
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

impl Object {
    /// Create an unsigned object with the given body.
    ///
    /// Geometry floats are canonicalized when finite; non-finite values are
    /// left in place and rejected by [`validate`] / [`to_canonical_bytes`].
    pub fn new(body: ObjectBody) -> Self {
        let object_type = body.object_type();
        let mut obj = Self {
            header: ObjectHeader {
                object_type,
                schema_version: SCHEMA_VERSION,
                created: now_secs(),
                author: None,
                signature: None,
            },
            body,
        };
        let _ = obj.body.canonicalize_geometry();
        obj
    }

    /// Create with explicit timestamp (for tests / deterministic fixtures).
    pub fn new_with_created(body: ObjectBody, created: u64) -> Self {
        let mut obj = Self::new(body);
        obj.header.created = created;
        obj
    }

    /// Canonical CBOR of this object (as stored / hashed).
    ///
    /// Applies the geometry float policy to a clone, then encodes. The
    /// in-memory object is not mutated.
    pub fn to_canonical_bytes(&self) -> Result<Vec<u8>> {
        let mut obj = self.clone();
        obj.body.canonicalize_geometry()?;
        to_canonical_cbor(&obj)
    }

    /// CID of this object (BLAKE3 of canonical CBOR including signature fields).
    pub fn cid(&self) -> Result<Cid> {
        let bytes = self.to_canonical_bytes()?;
        Ok(Cid::from_canonical_bytes(&bytes))
    }

    /// Bytes that are signed: header without signature + body.
    ///
    /// Signature is excluded so the signed payload is stable before signing.
    /// Geometry is canonicalized so the signature covers the same bytes as the CID path.
    fn signing_payload(&self) -> Result<Vec<u8>> {
        let mut unsigned = Object {
            header: ObjectHeader {
                object_type: self.header.object_type,
                schema_version: self.header.schema_version,
                created: self.header.created,
                author: self.header.author,
                signature: None,
            },
            body: self.body.clone(),
        };
        unsigned.body.canonicalize_geometry()?;
        to_canonical_cbor(&unsigned)
    }

    /// Sign this object in place. Sets author + signature; CID changes after signing.
    ///
    /// Roots use [`crate::root::RootBody::sign`] / `into_object`. Signing a Root
    /// as a leaf is defined to fail.
    pub fn sign(&mut self, keypair: &Keypair) -> Result<()> {
        if self.header.object_type == ObjectType::Root
            || matches!(self.body, ObjectBody::Root(_))
        {
            return Err(Error::Signature(
                "Roots use RootBody::sign / into_object, not Object::sign".into(),
            ));
        }
        self.body.canonicalize_geometry()?;
        self.header.author = Some(keypair.public_key());
        self.header.signature = None;
        let payload = self.signing_payload()?;
        self.header.signature = Some(AuthorSignature::create(keypair, &payload));
        Ok(())
    }

    /// Verify object signature if present.
    ///
    /// Defined to fail for Root objects (authority is `RootBody.authors`).
    pub fn verify_signature(&self) -> Result<()> {
        if self.header.object_type == ObjectType::Root
            || matches!(self.body, ObjectBody::Root(_))
        {
            return Err(Error::Signature(
                "Object::verify_signature on a Root is defined to fail; use RootBody::verify_authors"
                    .into(),
            ));
        }
        let Some(sig) = &self.header.signature else {
            return Err(Error::Signature("object has no signature".into()));
        };
        let Some(author) = &self.header.author else {
            return Err(Error::Signature("object has signature but no author".into()));
        };
        if sig.public_key != *author {
            return Err(Error::Signature(
                "signature public key does not match author".into(),
            ));
        }
        let payload = self.signing_payload()?;
        sig.verify(&payload)
    }

    /// Validate type consistency and basic invariants.
    pub fn validate(&self) -> Result<()> {
        if self.header.object_type != self.body.object_type() {
            return Err(Error::Validation(format!(
                "header type {} does not match body type {}",
                self.header.object_type,
                self.body.object_type()
            )));
        }
        if !schema_version_supported(self.header.schema_version) {
            return Err(Error::Validation(format!(
                "schema_version {} is not supported (accepted {MIN_SCHEMA_VERSION}..={SCHEMA_VERSION})",
                self.header.schema_version
            )));
        }
        if let Some(sig) = &self.header.signature {
            if self.header.author.is_none() {
                return Err(Error::Validation(
                    "signed object must have author".into(),
                ));
            }
            // Full crypto verify is optional at validate time; callers may call verify_signature.
            let _ = sig;
        }
        self.body.validate_geometry()?;
        Ok(())
    }

    pub fn from_canonical_bytes(bytes: &[u8]) -> Result<Self> {
        let obj: Object = from_cbor(bytes)?;
        obj.validate()?;
        Ok(obj)
    }

    /// Pose of a domain object, if present.
    pub fn pose(&self) -> Option<&Pose> {
        match &self.body {
            ObjectBody::Space(b) => b.pose.as_ref(),
            ObjectBody::Surface(b) => b.pose.as_ref(),
            ObjectBody::Opening(b) => b.pose.as_ref(),
            ObjectBody::Equipment(b) => b.pose.as_ref(),
            ObjectBody::Run(b) => b.pose.as_ref(),
            ObjectBody::Sensor(b) => b.pose.as_ref(),
            ObjectBody::Fixture(b) => b.pose.as_ref(),
            ObjectBody::Annotation(b) => b.pose.as_ref(),
            ObjectBody::PointCloudChunk(b) => b.pose.as_ref(),
            ObjectBody::Mesh(b) => b.pose.as_ref(),
            _ => None,
        }
    }

    /// Mutable pose, if this body carries one.
    pub fn pose_mut(&mut self) -> Option<&mut Pose> {
        match &mut self.body {
            ObjectBody::Space(b) => b.pose.as_mut(),
            ObjectBody::Surface(b) => b.pose.as_mut(),
            ObjectBody::Opening(b) => b.pose.as_mut(),
            ObjectBody::Equipment(b) => b.pose.as_mut(),
            ObjectBody::Run(b) => b.pose.as_mut(),
            ObjectBody::Sensor(b) => b.pose.as_mut(),
            ObjectBody::Fixture(b) => b.pose.as_mut(),
            ObjectBody::Annotation(b) => b.pose.as_mut(),
            ObjectBody::PointCloudChunk(b) => b.pose.as_mut(),
            ObjectBody::Mesh(b) => b.pose.as_mut(),
            _ => None,
        }
    }

    /// Stored extent, or derived from `bounds` when missing.
    pub fn extent(&self) -> Option<[f64; 3]> {
        let stored = match &self.body {
            ObjectBody::Surface(b) => b.extent,
            ObjectBody::Opening(b) => b.extent,
            ObjectBody::Equipment(b) => b.extent,
            ObjectBody::Run(b) => b.extent,
            _ => None,
        };
        if stored.is_some() {
            return stored;
        }
        match &self.body {
            ObjectBody::Surface(b) => b.bounds.as_ref().map(|a| a.extents()),
            ObjectBody::Space(b) => b.bounds.as_ref().map(|a| a.extents()),
            _ => None,
        }
    }

    /// 1σ in millimeters, if present and finite.
    pub fn sigma_mm(&self) -> Option<f64> {
        match &self.body {
            ObjectBody::Surface(b) => b.sigma_mm,
            ObjectBody::Opening(b) => b.sigma_mm,
            ObjectBody::Equipment(b) => b.sigma_mm,
            ObjectBody::Run(b) => b.sigma_mm,
            _ => None,
        }
        .filter(|s| s.is_finite() && *s > 0.0)
    }

    /// Stored support count (0 if the field was missing on decode).
    pub fn stored_support_count(&self) -> u32 {
        match &self.body {
            ObjectBody::Surface(b) => b.support_count,
            ObjectBody::Opening(b) => b.support_count,
            ObjectBody::Equipment(b) => b.support_count,
            ObjectBody::Run(b) => b.support_count,
            _ => 0,
        }
    }

    /// Effective observation count for fuse.
    ///
    /// Missing/`0` → `1` if the object has pose or extent, else `0`.
    pub fn effective_support_count(&self) -> u32 {
        let stored = self.stored_support_count();
        if stored > 0 {
            stored
        } else if self.pose().is_some() || self.extent().is_some() {
            1
        } else {
            0
        }
    }

    /// Evidence CIDs (empty when the field is absent).
    pub fn evidence(&self) -> &[Cid] {
        match &self.body {
            ObjectBody::Surface(b) => &b.evidence,
            ObjectBody::Opening(b) => &b.evidence,
            ObjectBody::Equipment(b) => &b.evidence,
            ObjectBody::Run(b) => &b.evidence,
            _ => &[],
        }
    }

    /// Opening host entity, if this is an opening.
    pub fn host_entity(&self) -> Option<&EntityId> {
        match &self.body {
            ObjectBody::Opening(b) => b.host_entity.as_ref(),
            _ => None,
        }
    }

    /// Kind family used by fuse: (`object_type`, optional kind string).
    pub fn kind_family(&self) -> Option<(ObjectType, Option<&str>)> {
        match &self.body {
            ObjectBody::Surface(b) => Some((ObjectType::Surface, b.surface_kind.as_deref())),
            ObjectBody::Opening(b) => Some((ObjectType::Opening, b.opening_kind.as_deref())),
            ObjectBody::Equipment(b) => Some((ObjectType::Equipment, b.equipment_kind.as_deref())),
            ObjectBody::Run(b) => Some((ObjectType::Run, b.run_kind.as_deref())),
            ObjectBody::Space(b) => Some((ObjectType::Space, b.name.as_deref())),
            ObjectBody::Floor(_) => Some((ObjectType::Floor, None)),
            _ => None,
        }
    }
}

fn canonicalize_fact_fields(extent: &mut Option<[f64; 3]>, sigma_mm: &mut Option<f64>) -> Result<()> {
    if let Some(e) = extent {
        canonicalize_extent(e)?;
    }
    if let Some(s) = sigma_mm {
        *s = canonicalize_f64(*s)?;
        if *s <= 0.0 {
            return Err(Error::Validation(
                "sigma_mm must be > 0 when present".into(),
            ));
        }
    }
    Ok(())
}

fn validate_fact_fields(extent: &Option<[f64; 3]>, sigma_mm: &Option<f64>) -> Result<()> {
    if let Some(e) = extent {
        for (i, &v) in e.iter().enumerate() {
            if !is_finite_f64(v) {
                return Err(Error::Validation(format!(
                    "extent[{i}] is not finite"
                )));
            }
            if v < 0.0 {
                return Err(Error::Validation(format!(
                    "extent[{i}] must not be negative"
                )));
            }
        }
    }
    if let Some(s) = sigma_mm {
        if !is_finite_f64(*s) {
            return Err(Error::Validation("sigma_mm is not finite".into()));
        }
        if *s <= 0.0 {
            return Err(Error::Validation(
                "sigma_mm must be > 0 when present".into(),
            ));
        }
    }
    Ok(())
}

/// Fold extent components: finite-only, `-0.0` → `+0.0`, reject negatives.
pub fn canonicalize_extent(e: &mut [f64; 3]) -> Result<()> {
    for (i, v) in e.iter_mut().enumerate() {
        *v = canonicalize_f64(*v)?;
        if *v < 0.0 {
            return Err(Error::Validation(format!(
                "extent[{i}] must not be negative"
            )));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use std::collections::BTreeSet;

    #[test]
    fn object_cid_stable() {
        let body = ObjectBody::Blob(BlobBody {
            content_type: Some("text/plain".into()),
            data: b"hello".to_vec(),
            properties: BTreeMap::new(),
        });
        let obj = Object::new_with_created(body, 1_700_000_000);
        let c1 = obj.cid().unwrap();
        let c2 = obj.cid().unwrap();
        assert_eq!(c1, c2);

        let bytes = obj.to_canonical_bytes().unwrap();
        let obj2 = Object::from_canonical_bytes(&bytes).unwrap();
        assert_eq!(obj2.cid().unwrap(), c1);
    }

    #[test]
    fn sign_and_verify() {
        let kp = Keypair::generate();
        let body = ObjectBody::Annotation(AnnotationBody {
            text: Some("valve behind panel".into()),
            transcript: None,
            media_ref: None,
            pose: Some(Pose::default()),
            space: None,
            properties: BTreeMap::new(),
        });
        let mut obj = Object::new_with_created(body, 1_700_000_001);
        obj.sign(&kp).unwrap();
        obj.verify_signature().unwrap();
        obj.validate().unwrap();

        // Tamper
        if let ObjectBody::Annotation(ref mut a) = obj.body {
            a.text = Some("tampered".into());
        }
        assert!(obj.verify_signature().is_err());
    }

    #[test]
    fn building_id_roundtrip() {
        let id = BuildingId::new();
        let s = id.to_string();
        let id2 = BuildingId::from_str(&s).unwrap();
        assert_eq!(id, id2);
    }

    fn annotation_with_pose(pose: Pose) -> Object {
        Object::new_with_created(
            ObjectBody::Annotation(AnnotationBody {
                text: Some("float-policy".into()),
                transcript: None,
                media_ref: None,
                pose: Some(pose),
                space: None,
                properties: BTreeMap::new(),
            }),
            1_700_000_500,
        )
    }

    #[test]
    fn signed_zero_does_not_change_cid() {
        let pos = annotation_with_pose(Pose {
            position: [0.0, 1.0, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        });
        let neg = Object {
            header: pos.header.clone(),
            body: ObjectBody::Annotation(AnnotationBody {
                text: Some("float-policy".into()),
                transcript: None,
                media_ref: None,
                pose: Some(Pose {
                    position: [-0.0, 1.0, -0.0],
                    orientation: [-0.0, 0.0, 0.0, 1.0],
                }),
                space: None,
                properties: BTreeMap::new(),
            }),
        };
        assert_eq!(pos.cid().unwrap(), neg.cid().unwrap());
        assert_eq!(
            pos.to_canonical_bytes().unwrap(),
            neg.to_canonical_bytes().unwrap()
        );
    }

    #[test]
    fn opposite_quaternion_same_cid() {
        let q = annotation_with_pose(Pose {
            position: [1.0, 2.0, 3.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        });
        let nq = Object {
            header: q.header.clone(),
            body: ObjectBody::Annotation(AnnotationBody {
                text: Some("float-policy".into()),
                transcript: None,
                media_ref: None,
                pose: Some(Pose {
                    position: [1.0, 2.0, 3.0],
                    orientation: [0.0, 0.0, 0.0, -1.0],
                }),
                space: None,
                properties: BTreeMap::new(),
            }),
        };
        assert_eq!(q.cid().unwrap(), nq.cid().unwrap());
    }

    #[test]
    fn nan_pose_rejected_by_validate_and_cid() {
        let obj = Object {
            header: ObjectHeader {
                object_type: ObjectType::Annotation,
                schema_version: SCHEMA_VERSION,
                created: 1,
                author: None,
                signature: None,
            },
            body: ObjectBody::Annotation(AnnotationBody {
                text: Some("nan".into()),
                transcript: None,
                media_ref: None,
                pose: Some(Pose {
                    position: [f64::NAN, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                }),
                space: None,
                properties: BTreeMap::new(),
            }),
        };
        assert!(obj.validate().is_err());
        assert!(obj.cid().is_err());
        assert!(obj.to_canonical_bytes().is_err());
    }

    #[test]
    fn unknown_schema_version_rejected() {
        let obj = Object {
            header: ObjectHeader {
                object_type: ObjectType::Annotation,
                schema_version: 99,
                created: 1,
                author: None,
                signature: None,
            },
            body: ObjectBody::Annotation(AnnotationBody {
                text: Some("v99".into()),
                transcript: None,
                media_ref: None,
                pose: None,
                space: None,
                properties: BTreeMap::new(),
            }),
        };
        let err = obj.validate().unwrap_err();
        assert!(
            matches!(err, Error::Validation(ref m) if m.contains("schema_version")),
            "{err:?}"
        );
    }

    #[test]
    fn inf_aabb_rejected() {
        let obj = Object {
            header: ObjectHeader {
                object_type: ObjectType::BoundingVolume,
                schema_version: SCHEMA_VERSION,
                created: 1,
                author: None,
                signature: None,
            },
            body: ObjectBody::BoundingVolume(BoundingVolumeBody {
                bounds: Aabb {
                    min: [f64::NEG_INFINITY, 0.0, 0.0],
                    max: [1.0, 1.0, 1.0],
                },
                target: None,
                properties: BTreeMap::new(),
            }),
        };
        assert!(obj.validate().is_err());
        assert!(obj.cid().is_err());
    }

    #[test]
    fn sign_covers_canonical_geometry() {
        let kp = Keypair::generate();
        let mut obj = Object {
            header: ObjectHeader {
                object_type: ObjectType::Annotation,
                schema_version: SCHEMA_VERSION,
                created: 9,
                author: None,
                signature: None,
            },
            body: ObjectBody::Annotation(AnnotationBody {
                text: Some("signed-zero".into()),
                transcript: None,
                media_ref: None,
                pose: Some(Pose {
                    position: [-0.0, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, -1.0],
                }),
                space: None,
                properties: BTreeMap::new(),
            }),
        };
        obj.sign(&kp).unwrap();
        obj.verify_signature().unwrap();
        // In-memory pose is folded so it matches the signed payload.
        if let ObjectBody::Annotation(a) = &obj.body {
            let p = a.pose.as_ref().unwrap();
            assert_eq!(p.position[0].to_bits(), 0.0f64.to_bits());
            assert_eq!(p.orientation, [0.0, 0.0, 0.0, 1.0]);
        } else {
            panic!("expected annotation");
        }
    }

    #[test]
    fn schema_v1_still_validates() {
        let obj = Object {
            header: ObjectHeader {
                object_type: ObjectType::Annotation,
                schema_version: 1,
                created: 1,
                author: None,
                signature: None,
            },
            body: ObjectBody::Annotation(AnnotationBody {
                text: Some("v1".into()),
                transcript: None,
                media_ref: None,
                pose: None,
                space: None,
                properties: BTreeMap::new(),
            }),
        };
        obj.validate().unwrap();
    }

    #[test]
    fn extent_canonicalize_folds_neg_zero_rejects_negative() {
        let mut e = [-0.0, 1.0, 0.2];
        canonicalize_extent(&mut e).unwrap();
        assert_eq!(e[0].to_bits(), 0.0f64.to_bits());
        let mut bad = [1.0, -0.5, 0.1];
        assert!(canonicalize_extent(&mut bad).is_err());
    }

    #[test]
    fn legacy_surface_cbor_without_fact_fields_decodes() {
        #[derive(Serialize)]
        struct LegacySurface {
            entity_id: Option<EntityId>,
            space: Option<Cid>,
            pose: Option<Pose>,
            bounds: Option<Aabb>,
            surface_kind: Option<String>,
            properties: BTreeMap<String, String>,
        }
        #[derive(Serialize)]
        #[serde(tag = "kind", content = "data", rename_all = "snake_case")]
        enum LegacyBody {
            Surface(LegacySurface),
        }
        #[derive(Serialize)]
        struct LegacyObject {
            header: ObjectHeader,
            body: LegacyBody,
        }
        let legacy = LegacyObject {
            header: ObjectHeader {
                object_type: ObjectType::Surface,
                schema_version: 1,
                created: 42,
                author: None,
                signature: None,
            },
            body: LegacyBody::Surface(LegacySurface {
                entity_id: Some(EntityId::from("wall-legacy".to_string())),
                space: None,
                pose: Some(Pose::default()),
                bounds: Some(Aabb {
                    min: [0.0, 0.0, 0.0],
                    max: [4.0, 2.5, 0.15],
                }),
                surface_kind: Some("wall".into()),
                properties: BTreeMap::new(),
            }),
        };
        let bytes = to_canonical_cbor(&legacy).unwrap();
        let obj = Object::from_canonical_bytes(&bytes).unwrap();
        match &obj.body {
            ObjectBody::Surface(s) => {
                assert!(s.extent.is_none());
                assert!(s.sigma_mm.is_none());
                assert_eq!(s.support_count, 0);
                assert!(s.evidence.is_empty());
            }
            other => panic!("expected surface, got {other:?}"),
        }
        assert_eq!(obj.effective_support_count(), 1);
        let derived = obj.extent().unwrap();
        assert!((derived[0] - 4.0).abs() < 1e-12);
        assert!((derived[1] - 2.5).abs() < 1e-12);
    }

    #[test]
    fn object_sign_and_verify_fail_on_root() {
        let kp = Keypair::generate();
        let body = RootBody::new(BuildingId::new(), None, BTreeSet::new(), 1);
        let mut obj = Object::new(ObjectBody::Root(body));
        assert!(obj.sign(&kp).is_err());
        let (signed, _) = crate::root::RootBuilder::new(BuildingId::new(), 1)
            .objects(BTreeSet::new())
            .build_signed(&kp)
            .unwrap();
        assert!(signed.verify_signature().is_err());
    }
}
