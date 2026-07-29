//! Project Arxos store objects into a USDA stage.

use std::collections::BTreeMap;
use std::path::Path;

use arxos_core::object::{Object, ObjectBody, ObjectType, Pose};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::RootBody;
use arxos_core::store::ObjectStore;
use arxos_core::{BuildingId, Cid};

use crate::error::{Result, UsdError};
use crate::model::{sanitize_name, UsdPrim, UsdStage, UsdValue};

/// Export options.
#[derive(Debug, Clone)]
pub struct ExportOptions {
    /// Include point-cloud points (can be large).
    pub include_point_clouds: bool,
    /// Max points per cloud (0 = unlimited).
    pub max_points_per_cloud: usize,
}

impl Default for ExportOptions {
    fn default() -> Self {
        Self {
            include_point_clouds: true,
            max_points_per_cloud: 50_000,
        }
    }
}

/// Export a building head (or explicit root) to USDA text.
pub fn export_building_usda(
    store_path: impl AsRef<Path>,
    building_id: &BuildingId,
    opts: &ExportOptions,
) -> Result<String> {
    let repo = BuildingRepository::open(store_path.as_ref(), building_id)?;
    let head = repo
        .head_root()
        .ok_or_else(|| UsdError::NotFound("building has no head root".into()))?;
    export_root_usda(store_path, &head, opts)
}

/// Export a specific root CID to USDA.
pub fn export_root_usda(
    store_path: impl AsRef<Path>,
    root_cid: &Cid,
    opts: &ExportOptions,
) -> Result<String> {
    let store = ObjectStore::open(store_path.as_ref())?;
    let root_obj = store.get(root_cid)?;
    let root = RootBody::from_object(&root_obj)?;
    let stage = project_root(&store, root_cid, &root, opts)?;
    Ok(stage.to_usda())
}

fn project_root(
    store: &ObjectStore,
    root_cid: &Cid,
    root: &RootBody,
    opts: &ExportOptions,
) -> Result<UsdStage> {
    let mut stage = UsdStage::new();
    stage.custom_layer_data.insert(
        "arxosRootCid".into(),
        root_cid.to_string(),
    );
    stage.custom_layer_data.insert(
        "arxosBuildingId".into(),
        root.building_id.to_string(),
    );
    stage.custom_layer_data.insert(
        "arxosExporter".into(),
        format!("arxos-usd/{}", env!("CARGO_PKG_VERSION")),
    );

    let building_path = format!("/Building_{}", sanitize_name(root.building_id.as_str()));
    stage.default_prim = Some(building_path.clone());

    // Root building prim
    let mut building_prim = UsdPrim {
        path: building_path.clone(),
        type_name: "Xform".into(),
        specifier: "def".into(),
        attrs: BTreeMap::new(),
        metadata: BTreeMap::new(),
    };
    building_prim.attrs.insert(
        "arxos:type".into(),
        UsdValue::String("building".into()),
    );
    building_prim.attrs.insert(
        "arxos:buildingId".into(),
        UsdValue::String(root.building_id.to_string()),
    );
    building_prim.attrs.insert(
        "arxos:rootCid".into(),
        UsdValue::String(root_cid.to_string()),
    );
    stage.prims.push(building_prim);

    // Index objects by type for hierarchy hints
    let mut floors: Vec<(Cid, Object)> = Vec::new();
    let mut spaces: Vec<(Cid, Object)> = Vec::new();
    let mut other: Vec<(Cid, Object)> = Vec::new();

    let active = root.materialize_active_objects(store)?;
    for cid in &active {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(_) => continue,
        };
        match obj.header.object_type {
            ObjectType::Building => {
                // attach name to building prim
                if let ObjectBody::Building(b) = &obj.body {
                    if let Some(last) = stage.prims.first_mut() {
                        last.attrs.insert(
                            "arxos:cid".into(),
                            UsdValue::String(cid.to_string()),
                        );
                        if let Some(n) = &b.name {
                            last.attrs
                                .insert("arxos:name".into(), UsdValue::String(n.clone()));
                        }
                    }
                }
            }
            ObjectType::Floor => floors.push((*cid, obj)),
            ObjectType::Space => spaces.push((*cid, obj)),
            ObjectType::Root | ObjectType::SpatialIndexNode => {}
            _ => other.push((*cid, obj)),
        }
    }

    floors.sort_by_key(|(c, _)| c.to_string());
    spaces.sort_by_key(|(c, _)| c.to_string());
    other.sort_by_key(|(c, _)| c.to_string());

    for (cid, obj) in &floors {
        let path = format!("{building_path}/{}", prim_name(obj, cid));
        stage.prims.push(object_to_prim(&path, cid, obj, opts)?);
    }
    for (cid, obj) in &spaces {
        let parent = space_parent_path(&building_path, obj, &floors);
        let path = format!("{parent}/{}", prim_name(obj, cid));
        stage.prims.push(object_to_prim(&path, cid, obj, opts)?);
    }
    for (cid, obj) in &other {
        let parent = match obj.header.object_type {
            ObjectType::Annotation
            | ObjectType::PointCloudChunk
            | ObjectType::Equipment
            | ObjectType::Sensor
            | ObjectType::Fixture => {
                // Prefer space path if space ref present
                other_parent_path(&building_path, obj, &spaces)
            }
            _ => building_path.clone(),
        };
        let path = format!("{parent}/{}", prim_name(obj, cid));
        stage.prims.push(object_to_prim(&path, cid, obj, opts)?);
    }

    Ok(stage)
}

fn prim_name(obj: &Object, cid: &Cid) -> String {
    let short = &cid.to_hex()[..8.min(cid.to_hex().len())];
    let kind = obj.header.object_type.as_str();
    let label = match &obj.body {
        ObjectBody::Floor(b) => b.name.clone().unwrap_or_else(|| format!("Floor_{}", b.level_index)),
        ObjectBody::Space(b) => b.name.clone().unwrap_or_else(|| format!("Space_{short}")),
        ObjectBody::Annotation(b) => b
            .text
            .clone()
            .map(|t| t.chars().take(24).collect())
            .unwrap_or_else(|| format!("Ann_{short}")),
        ObjectBody::Equipment(b) => b.name.clone().unwrap_or_else(|| format!("Eq_{short}")),
        _ => format!("{kind}_{short}"),
    };
    format!("{}_{}", sanitize_name(&label), short)
}

fn space_parent_path(
    building_path: &str,
    space: &Object,
    floors: &[(Cid, Object)],
) -> String {
    if let ObjectBody::Space(s) = &space.body {
        if let Some(floor_cid) = s.floor {
            if let Some((_, fobj)) = floors.iter().find(|(c, _)| *c == floor_cid) {
                return format!("{building_path}/{}", prim_name(fobj, &floor_cid));
            }
        }
    }
    building_path.to_string()
}

fn other_parent_path(
    building_path: &str,
    obj: &Object,
    spaces: &[(Cid, Object)],
) -> String {
    let space_ref = match &obj.body {
        ObjectBody::Annotation(a) => a.space,
        _ => None,
    };
    if let Some(sc) = space_ref {
        if let Some((_, sobj)) = spaces.iter().find(|(c, _)| *c == sc) {
            return format!("{building_path}/{}", prim_name(sobj, &sc));
        }
    }
    building_path.to_string()
}

fn object_to_prim(
    path: &str,
    cid: &Cid,
    obj: &Object,
    opts: &ExportOptions,
) -> Result<UsdPrim> {
    let type_name = match obj.header.object_type {
        ObjectType::PointCloudChunk => "Points",
        ObjectType::Mesh => "Mesh",
        ObjectType::Annotation => "Xform",
        ObjectType::Space | ObjectType::Floor | ObjectType::Building => "Xform",
        ObjectType::Equipment | ObjectType::Sensor | ObjectType::Fixture => "Xform",
        _ => "Xform",
    };
    let mut prim = UsdPrim {
        path: path.to_string(),
        type_name: type_name.into(),
        specifier: "def".into(),
        attrs: BTreeMap::new(),
        metadata: BTreeMap::new(),
    };
    prim.attrs.insert(
        "arxos:cid".into(),
        UsdValue::String(cid.to_string()),
    );
    prim.attrs.insert(
        "arxos:type".into(),
        UsdValue::String(obj.header.object_type.to_string()),
    );
    prim.attrs.insert(
        "arxos:schemaVersion".into(),
        UsdValue::String(obj.header.schema_version.to_string()),
    );
    prim.attrs.insert(
        "arxos:created".into(),
        UsdValue::String(obj.header.created.to_string()),
    );

    if let Some(pose) = extract_pose(obj) {
        prim.attrs.insert(
            "xformOp:translate".into(),
            UsdValue::Float3(pose.position),
        );
        // Quaternion as custom float4 for fidelity (USD xformOp:orient later).
        prim.attrs.insert(
            "arxos:orientation".into(),
            UsdValue::String(format!(
                "{},{},{},{}",
                pose.orientation[0],
                pose.orientation[1],
                pose.orientation[2],
                pose.orientation[3]
            )),
        );
    }

    match &obj.body {
        ObjectBody::Annotation(a) => {
            if let Some(t) = &a.text {
                prim.attrs
                    .insert("arxos:text".into(), UsdValue::String(t.clone()));
            }
            if let Some(t) = &a.transcript {
                prim.attrs
                    .insert("arxos:transcript".into(), UsdValue::String(t.clone()));
            }
        }
        ObjectBody::Space(s) => {
            if let Some(n) = &s.name {
                prim.attrs
                    .insert("arxos:name".into(), UsdValue::String(n.clone()));
            }
            if let Some(b) = &s.bounds {
                prim.attrs.insert(
                    "extent".into(),
                    UsdValue::Float3Array(vec![b.min, b.max]),
                );
            }
        }
        ObjectBody::Floor(f) => {
            if let Some(n) = &f.name {
                prim.attrs
                    .insert("arxos:name".into(), UsdValue::String(n.clone()));
            }
            prim.attrs.insert(
                "arxos:levelIndex".into(),
                UsdValue::String(f.level_index.to_string()),
            );
            prim.attrs.insert(
                "arxos:elevationM".into(),
                UsdValue::Float(f.elevation_m),
            );
        }
        ObjectBody::PointCloudChunk(pc) if opts.include_point_clouds => {
            let mut pts = decode_xyz_f32_le(&pc.points);
            if opts.max_points_per_cloud > 0 && pts.len() > opts.max_points_per_cloud {
                pts.truncate(opts.max_points_per_cloud);
            }
            if !pts.is_empty() {
                prim.attrs
                    .insert("points".into(), UsdValue::Float3Array(pts));
            }
            prim.attrs.insert(
                "arxos:pointCount".into(),
                UsdValue::String(pc.point_count.to_string()),
            );
        }
        ObjectBody::Equipment(e) => {
            if let Some(n) = &e.name {
                prim.attrs
                    .insert("arxos:name".into(), UsdValue::String(n.clone()));
            }
            if let Some(k) = &e.equipment_kind {
                prim.attrs
                    .insert("arxos:kind".into(), UsdValue::String(k.clone()));
            }
        }
        _ => {}
    }

    // Preserve free-form properties as custom strings (prefix arxos:prop:)
    for (k, v) in extract_properties(obj) {
        prim.attrs.insert(
            format!("arxos:prop:{}", sanitize_name(&k)),
            UsdValue::String(v),
        );
    }

    Ok(prim)
}

fn extract_pose(obj: &Object) -> Option<Pose> {
    match &obj.body {
        ObjectBody::Space(b) => b.pose.clone(),
        ObjectBody::Surface(b) => b.pose.clone(),
        ObjectBody::Opening(b) => b.pose.clone(),
        ObjectBody::Equipment(b) => b.pose.clone(),
        ObjectBody::Sensor(b) => b.pose.clone(),
        ObjectBody::Fixture(b) => b.pose.clone(),
        ObjectBody::Annotation(b) => b.pose.clone(),
        ObjectBody::PointCloudChunk(b) => b.pose.clone(),
        ObjectBody::Mesh(b) => b.pose.clone(),
        _ => None,
    }
}

fn extract_properties(obj: &Object) -> BTreeMap<String, String> {
    match &obj.body {
        ObjectBody::Building(b) => b.properties.clone(),
        ObjectBody::Floor(b) => b.properties.clone(),
        ObjectBody::Space(b) => b.properties.clone(),
        ObjectBody::Annotation(b) => b.properties.clone(),
        ObjectBody::PointCloudChunk(b) => b.properties.clone(),
        ObjectBody::Equipment(b) => b.properties.clone(),
        ObjectBody::Sensor(b) => b.properties.clone(),
        ObjectBody::Fixture(b) => b.properties.clone(),
        ObjectBody::Surface(b) => b.properties.clone(),
        _ => BTreeMap::new(),
    }
}

fn decode_xyz_f32_le(bytes: &[u8]) -> Vec<[f64; 3]> {
    let mut out = Vec::with_capacity(bytes.len() / 12);
    let mut i = 0;
    while i + 12 <= bytes.len() {
        let x = f32::from_le_bytes([bytes[i], bytes[i + 1], bytes[i + 2], bytes[i + 3]]);
        let y = f32::from_le_bytes([bytes[i + 4], bytes[i + 5], bytes[i + 6], bytes[i + 7]]);
        let z = f32::from_le_bytes([bytes[i + 8], bytes[i + 9], bytes[i + 10], bytes[i + 11]]);
        out.push([x as f64, y as f64, z as f64]);
        i += 12;
    }
    out
}
