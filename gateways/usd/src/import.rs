//! Import a USDA subset back into an Arxos object store.

use std::collections::BTreeMap;
use std::path::Path;
use std::str::FromStr;

use arxos_core::object::{
    AnnotationBody, BuildingBody, BuildingId, FloorBody, Object, ObjectBody, PointCloudChunkBody,
    Pose, SpaceBody,
};
use arxos_core::repository::BuildingRepository;
use arxos_core::store::ObjectStore;
use arxos_core::{Cid, Keypair};

use crate::error::{Result, UsdError};
use crate::model::{parse_usda, UsdPrim, UsdStage, UsdValue};

/// Result of importing a USDA file/string.
#[derive(Debug, Clone)]
pub struct ImportResult {
    pub building_id: BuildingId,
    pub object_cids: Vec<Cid>,
    pub root_cid: Option<Cid>,
    pub source_root_cid: Option<String>,
}

/// Import USDA text into `store_path`, creating/following a building and committing a root.
pub fn import_usda(
    store_path: impl AsRef<Path>,
    usda: &str,
    sign: Option<&Keypair>,
) -> Result<ImportResult> {
    let stage = parse_usda(usda).map_err(UsdError::Format)?;
    import_stage(store_path, &stage, sign)
}

fn import_stage(
    store_path: impl AsRef<Path>,
    stage: &UsdStage,
    sign: Option<&Keypair>,
) -> Result<ImportResult> {
    let store = ObjectStore::open(store_path.as_ref())?;
    let source_root = stage
        .custom_layer_data
        .get("arxosRootCid")
        .cloned()
        .or_else(|| {
            stage
                .prims
                .iter()
                .find_map(|p| attr_string(p, "arxos:rootCid"))
        });
    let building_id = stage
        .custom_layer_data
        .get("arxosBuildingId")
        .and_then(|s| BuildingId::from_str(s).ok())
        .or_else(|| {
            stage
                .prims
                .iter()
                .find_map(|p| attr_string(p, "arxos:buildingId"))
                .and_then(|s| BuildingId::from_str(&s).ok())
        })
        .unwrap_or_else(BuildingId::new);

    // Ensure building record exists.
    let repo = BuildingRepository::open_or_follow(
        store_path.as_ref(),
        &building_id,
        stage
            .prims
            .iter()
            .find_map(|p| attr_string(p, "arxos:name")),
    )?;

    let mut object_cids = Vec::new();
    let mut building_seen = false;

    for prim in &stage.prims {
        let ty = attr_string(prim, "arxos:type").unwrap_or_else(|| infer_type(prim));
        let source_cid = attr_string(prim, "arxos:cid");
        let pose = pose_from_prim(prim);
        let mut props = BTreeMap::new();
        if let Some(c) = &source_cid {
            props.insert("arxos_source_cid".into(), c.clone());
        }
        // Restore prop:* attributes
        for (k, v) in &prim.attrs {
            if let Some(rest) = k.strip_prefix("arxos:prop:") {
                if let UsdValue::String(s) = v {
                    props.insert(rest.to_string(), s.clone());
                }
            }
        }

        let body = match ty.as_str() {
            "building" => {
                building_seen = true;
                ObjectBody::Building(BuildingBody {
                    building_id: building_id.clone(),
                    name: attr_string(prim, "arxos:name"),
                    controller_keys: Vec::new(),
                    properties: props,
                })
            }
            "floor" => ObjectBody::Floor(FloorBody {
                building_id: building_id.clone(),
                name: attr_string(prim, "arxos:name"),
                level_index: attr_string(prim, "arxos:levelIndex")
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0),
                elevation_m: attr_float(prim, "arxos:elevationM").unwrap_or(0.0),
                properties: props,
            }),
            "space" => ObjectBody::Space(SpaceBody {
                name: attr_string(prim, "arxos:name"),
                floor: None,
                pose,
                bounds: extent_to_aabb(prim),
                properties: props,
            }),
            "annotation" => ObjectBody::Annotation(AnnotationBody {
                text: attr_string(prim, "arxos:text"),
                transcript: attr_string(prim, "arxos:transcript"),
                media_ref: None,
                pose,
                space: None,
                properties: props,
            }),
            "point_cloud_chunk" => {
                let pts = attr_points(prim).unwrap_or_default();
                let bytes = encode_xyz_f32_le(&pts);
                props
                    .entry("format".into())
                    .or_insert_with(|| "xyz_f32_le".into());
                props.insert("source".into(), "usd_import".into());
                ObjectBody::PointCloudChunk(PointCloudChunkBody {
                    pose,
                    bounds: extent_to_aabb(prim),
                    point_count: pts.len() as u64,
                    points: bytes,
                    properties: props,
                })
            }
            "equipment" => ObjectBody::Equipment(arxos_core::object::EquipmentBody {
                name: attr_string(prim, "arxos:name"),
                equipment_kind: attr_string(prim, "arxos:kind"),
                pose,
                system: None,
                properties: props,
            }),
            _ => continue,
        };

        let mut obj = Object::new(body);
        if let Some(created) = attr_string(prim, "arxos:created").and_then(|s| s.parse().ok()) {
            obj.header.created = created;
        }
        if let Some(kp) = sign {
            obj.sign(kp)?;
        }
        let cid = store.put(&obj)?;
        object_cids.push(cid);
        // Stage via pending for commit
        // Use capture path: put already done; add pending by staging through a dummy reopen
        let _ = cid;
    }

    if !building_seen {
        let mut obj = Object::new(ObjectBody::Building(BuildingBody {
            building_id: building_id.clone(),
            name: None,
            controller_keys: Vec::new(),
            properties: BTreeMap::new(),
        }));
        if let Some(kp) = sign {
            obj.sign(kp)?;
        }
        object_cids.push(store.put(&obj)?);
    }

    // Manually stage pending into record by putting through capture APIs is heavy;
    // instead write objects then commit via root builder on the repository.
    // Rebuild pending set:
    for cid in &object_cids {
        // Open mutably — re-fetch repo
        let _ = cid;
    }
    drop(repo);

    // Commit: open repo, inject pending by re-putting isn't needed; use RootBuilder via store.
    let mut repo = BuildingRepository::open_or_follow(store_path.as_ref(), &building_id, None)?;
    // Stage each object into pending by reading and re-staging through internal path:
    // BuildingRepository doesn't expose stage_cid; use commit after putting via capture no-ops.
    // Workaround: use merge-style — put objects already in store, then create root with open_or_follow
    // and adopt after manual root creation.
    use arxos_core::root::RootBuilder;
    use std::collections::BTreeSet;
    use std::time::{SystemTime, UNIX_EPOCH};

    let mut set: BTreeSet<Cid> = object_cids.iter().copied().collect();
    // Include previous head objects if any.
    if let Ok(cids) = repo.head_object_cids() {
        set.extend(cids);
    }
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let kp_owned = sign.cloned().or_else(|| repo.keypair().cloned());
    let root_cid = if let Some(kp) = kp_owned.as_ref() {
        let (root_obj, root_cid) = RootBuilder::new(building_id.clone(), ts)
            .objects(set)
            .message("usd import")
            .build_signed(kp)?;
        store.put(&root_obj)?;
        repo.adopt_root(root_cid)?;
        Some(root_cid)
    } else {
        // Unsigned root
        let mut body =
            arxos_core::root::RootBody::new(building_id.clone(), repo.head_root(), set, ts);
        body.message = Some("usd import".into());
        let obj = body.into_object(ts);
        let root_cid = store.put(&obj)?;
        repo.adopt_root(root_cid)?;
        Some(root_cid)
    };

    Ok(ImportResult {
        building_id,
        object_cids,
        root_cid,
        source_root_cid: source_root,
    })
}

fn infer_type(prim: &UsdPrim) -> String {
    if prim.type_name == "Points" {
        return "point_cloud_chunk".into();
    }
    if prim.attrs.contains_key("arxos:text") {
        return "annotation".into();
    }
    if prim.attrs.contains_key("arxos:levelIndex") {
        return "floor".into();
    }
    if prim.path.to_lowercase().contains("space") {
        return "space".into();
    }
    if prim.attrs.contains_key("arxos:buildingId") {
        return "building".into();
    }
    "space".into()
}

fn attr_string(prim: &UsdPrim, key: &str) -> Option<String> {
    match prim.attrs.get(key)? {
        UsdValue::String(s) | UsdValue::Token(s) => Some(s.clone()),
        _ => None,
    }
}

fn attr_float(prim: &UsdPrim, key: &str) -> Option<f64> {
    match prim.attrs.get(key)? {
        UsdValue::Float(f) => Some(*f),
        UsdValue::String(s) => s.parse().ok(),
        _ => None,
    }
}

fn attr_points(prim: &UsdPrim) -> Option<Vec<[f64; 3]>> {
    match prim.attrs.get("points")? {
        UsdValue::Float3Array(a) => Some(a.clone()),
        _ => None,
    }
}

fn pose_from_prim(prim: &UsdPrim) -> Option<Pose> {
    let position = match prim.attrs.get("xformOp:translate")? {
        UsdValue::Float3(p) => *p,
        _ => return None,
    };
    let orientation = attr_string(prim, "arxos:orientation")
        .and_then(|s| {
            let p: Vec<f64> = s.split(',').filter_map(|x| x.trim().parse().ok()).collect();
            if p.len() == 4 {
                Some([p[0], p[1], p[2], p[3]])
            } else {
                None
            }
        })
        .unwrap_or([0.0, 0.0, 0.0, 1.0]);
    Some(Pose {
        position,
        orientation,
    })
}

fn extent_to_aabb(prim: &UsdPrim) -> Option<arxos_core::object::Aabb> {
    match prim.attrs.get("extent")? {
        UsdValue::Float3Array(a) if a.len() >= 2 => Some(arxos_core::object::Aabb {
            min: a[0],
            max: a[1],
        }),
        _ => None,
    }
}

fn encode_xyz_f32_le(pts: &[[f64; 3]]) -> Vec<u8> {
    let mut out = Vec::with_capacity(pts.len() * 12);
    for p in pts {
        out.extend_from_slice(&(p[0] as f32).to_le_bytes());
        out.extend_from_slice(&(p[1] as f32).to_le_bytes());
        out.extend_from_slice(&(p[2] as f32).to_le_bytes());
    }
    out
}
