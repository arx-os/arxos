//! Import IFC subset (with Pset_ArxosIdentity) into Arxos store.

use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use arxos_core::object::{
    AnnotationBody, BuildingBody, BuildingId, FloorBody, Object, ObjectBody, Pose, SpaceBody,
};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::RootBuilder;
use arxos_core::store::ObjectStore;
use arxos_core::{AdoptOptions, Cid, Keypair};

use crate::error::{IfcError, Result};
use crate::parse::{
    parse_ifc, parse_ref, parse_typed_text, split_args, unquote, IfcEntity, IfcFile,
};

#[derive(Debug, Clone)]
pub struct ImportResult {
    pub building_id: BuildingId,
    pub object_cids: Vec<Cid>,
    pub root_cid: Option<Cid>,
    pub source_root_cid: Option<String>,
}

/// Import IFC STEP text into the store and commit a root.
pub fn import_ifc(
    store_path: impl AsRef<Path>,
    ifc_text: &str,
    sign: Option<&Keypair>,
) -> Result<ImportResult> {
    let file = parse_ifc(ifc_text).map_err(IfcError::Format)?;
    import_file(store_path, &file, sign)
}

fn import_file(
    store_path: impl AsRef<Path>,
    file: &IfcFile,
    sign: Option<&Keypair>,
) -> Result<ImportResult> {
    let store = ObjectStore::open(store_path.as_ref())?;
    let source_root = file.comments.iter().find_map(|c| {
        c.split_whitespace()
            .find(|t| t.starts_with("arxos_root="))
            .map(|t| t.trim_start_matches("arxos_root=").to_string())
    });
    let building_from_comment = file.comments.iter().find_map(|c| {
        c.split_whitespace()
            .find(|t| t.starts_with("arxos_building="))
            .map(|t| t.trim_start_matches("arxos_building=").to_string())
    });

    // Build identity map: entity_id → (cid?, type, building_id?, name?, text?)
    let identities = collect_identities(file);

    let mut building_id = building_from_comment
        .as_ref()
        .and_then(|s| BuildingId::from_str(s).ok())
        .or_else(|| {
            identities
                .values()
                .find_map(|i| i.building_id.clone())
                .and_then(|s| BuildingId::from_str(&s).ok())
        })
        .unwrap_or_else(BuildingId::new);

    let mut object_cids = Vec::new();
    let mut building_seen = false;

    // Floors: IfcBuildingStorey
    let mut floor_elev: BTreeMap<u64, f64> = BTreeMap::new();
    for (id, ent) in &file.entities {
        if ent.type_name == "IFCBUILDINGSTOREY" {
            let args = split_args(&ent.args_raw);
            // elevation often last numeric
            if let Some(elev) = args.last().and_then(|a| a.trim_end_matches('.').parse().ok()) {
                floor_elev.insert(*id, elev);
            }
        }
    }

    for (id, ent) in &file.entities {
        let ident = identities.get(id);
        let ty = ident
            .and_then(|i| i.object_type.clone())
            .or_else(|| match ent.type_name.as_str() {
                "IFCBUILDING" => Some("building".into()),
                "IFCBUILDINGSTOREY" => Some("floor".into()),
                "IFCSPACE" => Some("space".into()),
                "IFCANNOTATION" => Some("annotation".into()),
                _ => None,
            });
        let Some(ty) = ty else {
            continue;
        };

        let mut props = BTreeMap::new();
        props.insert("ifc_entity_id".into(), id.to_string());
        props.insert("ifc_type".into(), ent.type_name.clone());
        if let Some(i) = ident {
            if let Some(c) = &i.source_cid {
                props.insert("arxos_source_cid".into(), c.clone());
            }
            if let Some(g) = entity_global_id(ent) {
                props.insert("ifc_global_id".into(), g);
            }
        } else if let Some(g) = entity_global_id(ent) {
            props.insert("ifc_global_id".into(), g);
        }

        let name = entity_name(ent);
        let pose = None; // placement reverse-parse is best-effort; Phase 4 keeps identity + labels

        let body = match ty.as_str() {
            "building" => {
                building_seen = true;
                if let Some(bid) = ident.and_then(|i| i.building_id.as_ref()) {
                    if let Ok(b) = BuildingId::from_str(bid) {
                        building_id = b;
                    }
                }
                ObjectBody::Building(BuildingBody {
                    building_id: building_id.clone(),
                    name,
                    // Importer key becomes the controller so signed import roots authorize.
                    controller_keys: sign.map(|k| vec![k.public_key()]).unwrap_or_default(),
                    properties: props,
                })
            }
            "floor" => ObjectBody::Floor(FloorBody {
                entity_id: Some(arxos_core::EntityId::new()),
                building_id: building_id.clone(),
                name,
                level_index: 0,
                elevation_m: floor_elev.get(id).copied().unwrap_or(0.0),
                properties: props,
            }),
            "space" => ObjectBody::Space(SpaceBody {
                entity_id: Some(arxos_core::EntityId::new()),
                name,
                floor: None,
                pose,
                bounds: None,
                properties: props,
            }),
            "annotation" => {
                let text = ident
                    .and_then(|i| i.text.clone())
                    .or_else(|| annotation_text(file, *id));
                ObjectBody::Annotation(AnnotationBody {
                    text,
                    transcript: None,
                    media_ref: None,
                    pose: pose.or(Some(Pose::default())),
                    space: None,
                    properties: props,
                })
            }
            _ => continue,
        };

        let mut obj = Object::new(body);
        if let Some(kp) = sign {
            obj.sign(kp)?;
        }
        object_cids.push(store.put(&obj)?);
    }

    if !building_seen {
        let mut obj = Object::new(ObjectBody::Building(BuildingBody {
            building_id: building_id.clone(),
            name: None,
            controller_keys: sign.map(|k| vec![k.public_key()]).unwrap_or_default(),
            properties: BTreeMap::new(),
        }));
        if let Some(kp) = sign {
            obj.sign(kp)?;
        }
        object_cids.push(store.put(&obj)?);
    }

    let mut repo = BuildingRepository::open_or_follow(store_path.as_ref(), &building_id, None)?;
    let mut set: BTreeSet<Cid> = object_cids.iter().copied().collect();
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
            .message("ifc import")
            .build_signed(kp)?;
        store.put(&root_obj)?;
        repo.adopt_root(root_cid)?;
        Some(root_cid)
    } else {
        let mut body =
            arxos_core::root::RootBody::new(building_id.clone(), repo.head_root(), set, ts);
        body.message = Some("ifc import".into());
        let obj = body.into_object(ts);
        let root_cid = store.put(&obj)?;
        repo.adopt_root_with_options(
            root_cid,
            &AdoptOptions {
                allow_untrusted: true,
                allow_partial: false,
            },
        )?;
        Some(root_cid)
    };

    Ok(ImportResult {
        building_id,
        object_cids,
        root_cid,
        source_root_cid: source_root,
    })
}

#[derive(Default, Clone)]
struct Identity {
    source_cid: Option<String>,
    building_id: Option<String>,
    object_type: Option<String>,
    text: Option<String>,
}

fn collect_identities(file: &IfcFile) -> BTreeMap<u64, Identity> {
    let mut map: BTreeMap<u64, Identity> = BTreeMap::new();

    // Find property sets named Pset_ArxosIdentity / Pset_ArxosAnnotation
    let mut pset_props: BTreeMap<u64, BTreeMap<String, String>> = BTreeMap::new();
    for (id, ent) in &file.entities {
        if ent.type_name == "IFCPROPERTYSET" {
            let args = split_args(&ent.args_raw);
            let name = args.get(2).and_then(|a| unquote(a)).unwrap_or_default();
            if name != "Pset_ArxosIdentity" && name != "Pset_ArxosAnnotation" {
                continue;
            }
            // last arg is list of property refs
            if let Some(list) = args.last() {
                let mut props = BTreeMap::new();
                for part in list.trim_start_matches('(').trim_end_matches(')').split(',') {
                    if let Some(pid) = parse_ref(part.trim()) {
                        if let Some(pent) = file.entities.get(&pid) {
                            if pent.type_name == "IFCPROPERTYSINGLEVALUE" {
                                let pargs = split_args(&pent.args_raw);
                                let pname = pargs.first().and_then(|a| unquote(a)).unwrap_or_default();
                                let pval = pargs
                                    .get(2)
                                    .and_then(|a| parse_typed_text(a))
                                    .unwrap_or_default();
                                props.insert(pname, pval);
                            }
                        }
                    }
                }
                pset_props.insert(*id, props);
            }
        }
    }

    // IFCRELDEFINESBYPROPERTIES links objects to psets
    for ent in file.entities.values() {
        if ent.type_name != "IFCRELDEFINESBYPROPERTIES" {
            continue;
        }
        let args = split_args(&ent.args_raw);
        // related objects list, then pset ref
        if args.len() < 6 {
            continue;
        }
        let objs = args.get(4).cloned().unwrap_or_default();
        let pset_ref = args.get(5).and_then(|a| parse_ref(a));
        let Some(pset_id) = pset_ref else { continue };
        let Some(props) = pset_props.get(&pset_id) else {
            continue;
        };
        for part in objs.trim_start_matches('(').trim_end_matches(')').split(',') {
            if let Some(oid) = parse_ref(part.trim()) {
                let entry = map.entry(oid).or_default();
                if let Some(v) = props.get("Cid") {
                    entry.source_cid = Some(v.clone());
                }
                if let Some(v) = props.get("BuildingId") {
                    entry.building_id = Some(v.clone());
                }
                if let Some(v) = props.get("ObjectType") {
                    entry.object_type = Some(v.clone());
                }
                if let Some(v) = props.get("Text") {
                    entry.text = Some(v.clone());
                }
            }
        }
    }
    map
}

fn entity_global_id(ent: &IfcEntity) -> Option<String> {
    let args = split_args(&ent.args_raw);
    args.first().and_then(|a| unquote(a))
}

fn entity_name(ent: &IfcEntity) -> Option<String> {
    // Name is typically 3rd argument for root products
    let args = split_args(&ent.args_raw);
    args.get(2).and_then(|a| unquote(a))
}

fn annotation_text(file: &IfcFile, _ann_id: u64) -> Option<String> {
    // Prefer Pset text; fallback None
    let _ = file;
    None
}
