//! Export Arxos roots to IFC4 STEP.

use std::collections::BTreeMap;
use std::path::Path;

use arxos_core::object::{Object, ObjectBody, ObjectType, Pose};
use arxos_core::realize::{realize, Solid, SolidKind};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::{ClosureOptions, RootBody, RootClosure};
use arxos_core::state::BuildingState;
use arxos_core::store::{ObjectRead, ObjectStore};
use arxos_core::{BuildingId, Cid, EntityId};

use crate::error::{IfcError, Result};
use crate::global_id::global_id_from_cid;

#[derive(Debug, Clone, Default)]
pub struct ExportOptions {
    pub project_name: Option<String>,
}

struct Writer {
    next_id: u64,
    lines: Vec<String>,
}

impl Writer {
    fn new() -> Self {
        Self {
            next_id: 1,
            lines: Vec::new(),
        }
    }

    fn emit(&mut self, entity: &str) -> u64 {
        let id = self.next_id;
        self.next_id += 1;
        self.lines.push(format!("#{id}={entity};"));
        id
    }

    fn finish(self, description: &str) -> String {
        let mut out = String::new();
        out.push_str("ISO-10303-21;\n");
        out.push_str("HEADER;\n");
        out.push_str("FILE_DESCRIPTION(('ViewDefinition [ArxosAsBuiltView]'),'2;1');\n");
        out.push_str(&format!(
            "FILE_NAME('arxos_export.ifc','{}',('Arxos'),('Arxos'),'arxos-ifc {}','arxos-ifc','');\n",
            iso_timestamp(),
            env!("CARGO_PKG_VERSION")
        ));
        out.push_str("FILE_SCHEMA(('IFC4'));\n");
        out.push_str("ENDSEC;\n");
        out.push_str("DATA;\n");
        for line in &self.lines {
            out.push_str(line);
            out.push('\n');
        }
        out.push_str(&format!("/* {description} */\n"));
        out.push_str("ENDSEC;\n");
        out.push_str("END-ISO-10303-21;\n");
        out
    }
}

fn iso_timestamp() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs().to_string())
        .unwrap_or_else(|_| "0".into())
}

fn ifc_str(s: &str) -> String {
    format!("'{}'", s.replace('\'', "''"))
}

fn ifc_opt_str(s: Option<&str>) -> String {
    match s {
        Some(v) => ifc_str(v),
        None => "$".into(),
    }
}

/// Export building head to IFC4 STEP text.
pub fn export_building_ifc(
    store_path: impl AsRef<Path>,
    building_id: &BuildingId,
    opts: &ExportOptions,
) -> Result<String> {
    let repo = BuildingRepository::open_read(store_path.as_ref(), building_id)?;
    let head = repo
        .head_root()
        .ok_or_else(|| IfcError::NotFound("no head root".into()))?;
    export_from_read(&repo, &head, opts)
}

/// Export a root CID to IFC4 STEP text.
pub fn export_root_ifc(
    store_path: impl AsRef<Path>,
    root_cid: &Cid,
    opts: &ExportOptions,
) -> Result<String> {
    let store = ObjectStore::open(store_path.as_ref())?;
    export_from_read(&store, root_cid, opts)
}

fn export_from_read<R: ObjectRead + ?Sized>(
    store: &R,
    root_cid: &Cid,
    opts: &ExportOptions,
) -> Result<String> {
    let closure = RootClosure::collect(store, root_cid, &ClosureOptions::default())?;
    let view = closure.as_read();
    let root_obj = view.get(root_cid)?;
    let root = RootBody::from_object(&root_obj)?;
    write_ifc(&view, root_cid, root, opts)
}

fn write_ifc<R: ObjectRead + ?Sized>(
    store: &R,
    root_cid: &Cid,
    root: &RootBody,
    opts: &ExportOptions,
) -> Result<String> {
    let mut w = Writer::new();

    let origin = w.emit("IFCCARTESIANPOINT((0.,0.,0.))");
    let axis_z = w.emit("IFCDIRECTION((0.,0.,1.))");
    let axis_x = w.emit("IFCDIRECTION((1.,0.,0.))");
    let world_place = w.emit(&format!(
        "IFCAXIS2PLACEMENT3D(#{origin},#{axis_z},#{axis_x})"
    ));
    let world = w.emit(&format!("IFCLOCALPLACEMENT($,#{world_place})"));

    let app = w.emit(&format!(
        "IFCAPPLICATION({},{},{},{})",
        ifc_str("Arxos"),
        ifc_str(env!("CARGO_PKG_VERSION")),
        ifc_str("arxos-ifc"),
        ifc_str("Arxos IFC Gateway")
    ));
    let person = w.emit("IFCPERSON($,$,$,$,$,$,$,$)");
    let org = w.emit(&format!("IFCORGANIZATION($,{},$,$,$)", ifc_str("Arxos")));
    let person_org = w.emit(&format!("IFCPERSONANDORGANIZATION(#{person},#{org},$)"));
    let owner = w.emit(&format!(
        "IFCOWNERHISTORY(#{person_org},#{app},$,.ADDED.,$,$,$,0)"
    ));

    let si_len = w.emit("IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)");
    let units = w.emit(&format!("IFCUNITASSIGNMENT((#{si_len}))"));
    let ctx = w.emit(&format!(
        "IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,#{world_place},$)"
    ));

    let project_gid = global_id_from_cid(root_cid);
    let project_name = opts
        .project_name
        .clone()
        .unwrap_or_else(|| format!("Arxos {}", root.building_id));
    let project = w.emit(&format!(
        "IFCPROJECT({},#{owner},{},$,$,$,$,(#{ctx}),#{units})",
        ifc_str(&project_gid),
        ifc_str(&project_name),
    ));

    let site_gid = global_id_from_cid(&Cid::from_canonical_bytes(
        format!("site:{}", root.building_id).as_bytes(),
    ));
    let site = w.emit(&format!(
        "IFCSITE({},#{owner},{},$,$,#{world},$,$,.ELEMENT.,$,$,$,$,$)",
        ifc_str(&site_gid),
        ifc_str("Site"),
    ));

    let mut floors: Vec<(Cid, Object)> = Vec::new();
    let mut spaces: Vec<(Cid, Object)> = Vec::new();
    let mut annotations: Vec<(Cid, Object)> = Vec::new();
    let mut building_obj: Option<(Cid, Object)> = None;

    let active = root.materialize_active_objects(store)?;
    for cid in &active {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(_) => continue,
        };
        match obj.header.object_type {
            ObjectType::Building => building_obj = Some((*cid, obj)),
            ObjectType::Floor => floors.push((*cid, obj)),
            ObjectType::Space => spaces.push((*cid, obj)),
            ObjectType::Annotation => annotations.push((*cid, obj)),
            _ => {}
        }
    }
    floors.sort_by_key(|(c, _)| c.to_string());
    spaces.sort_by_key(|(c, _)| c.to_string());

    let (b_cid, b_name) = match &building_obj {
        Some((c, o)) => {
            let name = if let ObjectBody::Building(b) = &o.body {
                b.name.clone()
            } else {
                None
            };
            (*c, name)
        }
        None => (*root_cid, Some(root.building_id.to_string())),
    };

    let building_gid = global_id_from_cid(&b_cid);
    let building = w.emit(&format!(
        "IFCBUILDING({},#{owner},{},$,$,#{world},$,$,.ELEMENT.,$,$,$)",
        ifc_str(&building_gid),
        ifc_opt_str(b_name.as_deref()),
    ));
    emit_identity_pset(
        &mut w,
        owner,
        building,
        &b_cid,
        "building",
        &root.building_id,
        None,
    );

    w.emit(&format!(
        "IFCRELAGGREGATES({},#{owner},$,$,#{project},(#{site}))",
        ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
            b"rel:project-site"
        )))
    ));
    w.emit(&format!(
        "IFCRELAGGREGATES({},#{owner},$,$,#{site},(#{building}))",
        ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
            b"rel:site-building"
        )))
    ));

    let mut storey_map: BTreeMap<Cid, u64> = BTreeMap::new();
    let mut storey_list = Vec::new();

    for (cid, obj) in &floors {
        let (name, elev) = if let ObjectBody::Floor(f) = &obj.body {
            (f.name.clone(), f.elevation_m)
        } else {
            (None, 0.0)
        };
        let elev_pt = w.emit(&format!("IFCCARTESIANPOINT((0.,{elev},0.))"));
        let elev_place = w.emit(&format!(
            "IFCAXIS2PLACEMENT3D(#{elev_pt},#{axis_z},#{axis_x})"
        ));
        let elev_loc = w.emit(&format!("IFCLOCALPLACEMENT(#{world},#{elev_place})"));
        let gid = global_id_from_cid(cid);
        let storey = w.emit(&format!(
            "IFCBUILDINGSTOREY({},#{owner},{},$,$,#{elev_loc},$,$,.ELEMENT.,{elev})",
            ifc_str(&gid),
            ifc_opt_str(name.as_deref()),
        ));
        let eid = arxos_core::entity::entity_id_of(obj).map(|e| e.as_str());
        emit_identity_pset(&mut w, owner, storey, cid, "floor", &root.building_id, eid);
        storey_map.insert(*cid, storey);
        storey_list.push(storey);
    }

    if storey_list.is_empty() {
        let gid = global_id_from_cid(&Cid::from_canonical_bytes(b"default-storey"));
        let storey = w.emit(&format!(
            "IFCBUILDINGSTOREY({},#{owner},{},$,$,#{world},$,$,.ELEMENT.,0.)",
            ifc_str(&gid),
            ifc_str("Level 0"),
        ));
        storey_list.push(storey);
    }

    let storey_refs = storey_list
        .iter()
        .map(|id| format!("#{id}"))
        .collect::<Vec<_>>()
        .join(",");
    w.emit(&format!(
        "IFCRELAGGREGATES({},#{owner},$,$,#{building},({storey_refs}))",
        ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
            b"rel:building-storeys"
        )))
    ));

    let default_storey = storey_list[0];

    for (cid, obj) in &spaces {
        let (name, pose, floor_ref) = if let ObjectBody::Space(s) = &obj.body {
            (s.name.clone(), s.pose.clone(), s.floor)
        } else {
            (None, None, None)
        };
        let parent_storey = floor_ref
            .and_then(|f| storey_map.get(&f).copied())
            .unwrap_or(default_storey);
        let loc = placement_for_pose(&mut w, world, &pose, axis_z, axis_x);
        let gid = global_id_from_cid(cid);
        let space = w.emit(&format!(
            "IFCSPACE({},#{owner},{},$,$,#{loc},$,$,.ELEMENT.,.SPACE.,$)",
            ifc_str(&gid),
            ifc_opt_str(name.as_deref()),
        ));
        let eid = arxos_core::entity::entity_id_of(obj).map(|e| e.as_str());
        emit_identity_pset(&mut w, owner, space, cid, "space", &root.building_id, eid);
        w.emit(&format!(
            "IFCRELCONTAINEDINSPATIALSTRUCTURE({},#{owner},$,$,(#{space}),#{parent_storey})",
            ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
                format!("rel:space:{cid}").as_bytes()
            )))
        ));
    }

    for (cid, obj) in &annotations {
        let (text, pose) = if let ObjectBody::Annotation(a) = &obj.body {
            (a.text.clone(), a.pose.clone())
        } else {
            (None, None)
        };
        let loc = placement_for_pose(&mut w, world, &pose, axis_z, axis_x);
        let gid = global_id_from_cid(cid);
        let ann = w.emit(&format!(
            "IFCANNOTATION({},#{owner},{},$,$,#{loc},$)",
            ifc_str(&gid),
            ifc_str("Annotation"),
        ));
        emit_identity_pset(
            &mut w,
            owner,
            ann,
            cid,
            "annotation",
            &root.building_id,
            None,
        );
        if let Some(t) = &text {
            let p = w.emit(&format!(
                "IFCPROPERTYSINGLEVALUE({},$,IFCTEXT({}),$)",
                ifc_str("Text"),
                ifc_str(t)
            ));
            let pset = w.emit(&format!(
                "IFCPROPERTYSET({},#{owner},{},$,(#{p}))",
                ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
                    format!("pset:text:{cid}").as_bytes()
                ))),
                ifc_str("Pset_ArxosAnnotation"),
            ));
            w.emit(&format!(
                "IFCRELDEFINESBYPROPERTIES({},#{owner},$,$,(#{ann}),#{pset})",
                ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
                    format!("rel:pset:text:{cid}").as_bytes()
                )))
            ));
        }
        w.emit(&format!(
            "IFCRELCONTAINEDINSPATIALSTRUCTURE({},#{owner},$,$,(#{ann}),#{default_storey})",
            ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
                format!("rel:ann:{cid}").as_bytes()
            )))
        ));
    }

    let state = BuildingState::from_root(store, root)?;
    let realization = realize(&state)?;
    emit_realized_solids(
        &mut w,
        owner,
        world,
        ctx,
        default_storey,
        &root.building_id,
        &realization.solids,
        &state,
    );

    let desc = format!(
        "arxos_root={} arxos_building={}",
        root_cid, root.building_id
    );
    Ok(w.finish(&desc))
}

fn placement_for_pose(
    w: &mut Writer,
    parent_place: u64,
    pose: &Option<Pose>,
    axis_z: u64,
    axis_x: u64,
) -> u64 {
    let (x, y, z) = match pose {
        Some(p) => (p.position[0], p.position[1], p.position[2]),
        None => (0.0, 0.0, 0.0),
    };
    let pt = w.emit(&format!("IFCCARTESIANPOINT(({x},{y},{z}))"));
    let axis = w.emit(&format!(
        "IFCAXIS2PLACEMENT3D(#{pt},#{axis_z},#{axis_x})"
    ));
    w.emit(&format!("IFCLOCALPLACEMENT(#{parent_place},#{axis})"))
}

#[allow(clippy::too_many_arguments)]
fn emit_realized_solids(
    w: &mut Writer,
    owner: u64,
    world: u64,
    ctx: u64,
    storey: u64,
    building_id: &BuildingId,
    solids: &[Solid],
    state: &BuildingState,
) {
    let mut wall_ids: BTreeMap<EntityId, u64> = BTreeMap::new();
    let mut element_ids: Vec<u64> = Vec::new();
    let mut openings: Vec<(&Solid, u64)> = Vec::new();

    for solid in solids {
        let (ifc_type, obj_ty) = match solid.kind {
            SolidKind::Wall => ("IFCWALL", "surface"),
            SolidKind::Slab => ("IFCSLAB", "surface"),
            SolidKind::Opening => match state
                .get(&solid.entity_id)
                .and_then(|o| match &o.body {
                    ObjectBody::Opening(b) => b.opening_kind.as_deref(),
                    _ => None,
                }) {
                Some("window") => ("IFCWINDOW", "opening"),
                Some("door") => ("IFCDOOR", "opening"),
                _ => ("IFCOPENINGELEMENT", "opening"),
            },
            SolidKind::Equipment => ("IFCBUILDINGELEMENTPROXY", "equipment"),
            SolidKind::Run => ("IFCFLOWSEGMENT", "run"),
        };
        let loc = placement_from_solid(w, world, solid);
        let body_shape = extruded_box_shape(w, ctx, solid);
        let gid = global_id_from_cid(&solid.cid);
        let name = ifc_str(solid.entity_id.as_str());
        let elem = w.emit(&format!(
            "{ifc_type}({},#{owner},{name},$,$,#{loc},#{body_shape},$)",
            ifc_str(&gid),
        ));
        emit_identity_pset(
            w,
            owner,
            elem,
            &solid.cid,
            obj_ty,
            building_id,
            Some(solid.entity_id.as_str()),
        );
        emit_measure_pset(w, owner, elem, &solid.cid, state.get(&solid.entity_id), solid);
        match solid.kind {
            SolidKind::Wall | SolidKind::Slab => {
                wall_ids.insert(solid.entity_id.clone(), elem);
                element_ids.push(elem);
            }
            SolidKind::Opening => {
                openings.push((solid, elem));
            }
            _ => element_ids.push(elem),
        }
    }

    for (solid, opening_id) in &openings {
        if let Some(host) = &solid.host {
            if let Some(host_id) = wall_ids.get(host) {
                w.emit(&format!(
                    "IFCRELVOIDSELEMENT({},#{owner},$,$,#{host_id},#{opening_id})",
                    ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
                        format!("rel:voids:{}", solid.cid).as_bytes()
                    )))
                ));
            }
        }
        element_ids.push(*opening_id);
    }

    if !element_ids.is_empty() {
        let refs = element_ids
            .iter()
            .map(|id| format!("#{id}"))
            .collect::<Vec<_>>()
            .join(",");
        w.emit(&format!(
            "IFCRELCONTAINEDINSPATIALSTRUCTURE({},#{owner},$,$,({refs}),#{storey})",
            ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
                b"rel:storey-solids"
            )))
        ));
    }
}

fn placement_from_solid(w: &mut Writer, parent: u64, solid: &Solid) -> u64 {
    let p = solid.pose.position;
    let x = solid.pose.local_x();
    let y = solid.pose.local_y();
    let pt = w.emit(&format!(
        "IFCCARTESIANPOINT(({},{},{}))",
        p[0], p[1], p[2]
    ));
    let axis = w.emit(&format!(
        "IFCDIRECTION(({},{},{}))",
        y[0], y[1], y[2]
    ));
    let refd = w.emit(&format!(
        "IFCDIRECTION(({},{},{}))",
        x[0], x[1], x[2]
    ));
    let place = w.emit(&format!(
        "IFCAXIS2PLACEMENT3D(#{pt},#{axis},#{refd})"
    ));
    w.emit(&format!("IFCLOCALPLACEMENT(#{parent},#{place})"))
}

fn extruded_box_shape(w: &mut Writer, ctx: u64, solid: &Solid) -> u64 {
    let [width, height, thick] = solid.extent;
    let origin2 = w.emit("IFCCARTESIANPOINT((0.,0.))");
    let dir2 = w.emit("IFCDIRECTION((1.,0.))");
    let p2 = w.emit(&format!("IFCAXIS2PLACEMENT2D(#{origin2},#{dir2})"));
    let profile = w.emit(&format!(
        "IFCRECTANGLEPROFILEDEF(.AREA.,$,#{p2},{width},{thick})"
    ));
    let origin3 = w.emit(&format!(
        "IFCCARTESIANPOINT((0.,{},0.))",
        -height / 2.0
    ));
    let zdir = w.emit("IFCDIRECTION((0.,0.,1.))");
    let xdir = w.emit("IFCDIRECTION((1.,0.,0.))");
    let p3 = w.emit(&format!(
        "IFCAXIS2PLACEMENT3D(#{origin3},#{zdir},#{xdir})"
    ));
    let extrude_dir = w.emit("IFCDIRECTION((0.,0.,1.))");
    let solid_id = w.emit(&format!(
        "IFCEXTRUDEDAREASOLID(#{profile},#{p3},#{extrude_dir},{height})"
    ));
    let rep = w.emit(&format!(
        "IFCSHAPEREPRESENTATION(#{ctx},'Body','SweptSolid',(#{solid_id}))"
    ));
    w.emit(&format!("IFCPRODUCTDEFINITIONSHAPE($,$,(#{rep}))"))
}

fn emit_measure_pset(
    w: &mut Writer,
    owner: u64,
    target: u64,
    cid: &Cid,
    obj: Option<&Object>,
    solid: &Solid,
) {
    let sigma = obj.and_then(|o| o.sigma_mm()).unwrap_or(0.0);
    let support = obj.map(|o| o.effective_support_count()).unwrap_or(1);
    let e = solid.extent;
    let p_s = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCREAL({}),$)",
        ifc_str("SigmaMm"),
        sigma
    ));
    let p_n = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCINTEGER({}),$)",
        ifc_str("SupportCount"),
        support
    ));
    let p_x = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCREAL({}),$)",
        ifc_str("ExtentX"),
        e[0]
    ));
    let p_y = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCREAL({}),$)",
        ifc_str("ExtentY"),
        e[1]
    ));
    let p_z = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCREAL({}),$)",
        ifc_str("ExtentZ"),
        e[2]
    ));
    let pset = w.emit(&format!(
        "IFCPROPERTYSET({},#{owner},{},$,(#{p_s},#{p_n},#{p_x},#{p_y},#{p_z}))",
        ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
            format!("pset:meas:{cid}").as_bytes()
        ))),
        ifc_str("Pset_ArxosMeasure"),
    ));
    w.emit(&format!(
        "IFCRELDEFINESBYPROPERTIES({},#{owner},$,$,(#{target}),#{pset})",
        ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
            format!("rel:meas:{cid}").as_bytes()
        )))
    ));
}

fn emit_identity_pset(
    w: &mut Writer,
    owner: u64,
    target: u64,
    cid: &Cid,
    object_type: &str,
    building_id: &BuildingId,
    entity_id: Option<&str>,
) {
    let p_cid = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCTEXT({}),$)",
        ifc_str("Cid"),
        ifc_str(&cid.to_string())
    ));
    let p_bid = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCTEXT({}),$)",
        ifc_str("BuildingId"),
        ifc_str(&building_id.to_string())
    ));
    let p_ty = w.emit(&format!(
        "IFCPROPERTYSINGLEVALUE({},$,IFCTEXT({}),$)",
        ifc_str("ObjectType"),
        ifc_str(object_type)
    ));
    let mut prop_refs = format!("#{p_cid},#{p_bid},#{p_ty}");
    if let Some(eid) = entity_id {
        let p_eid = w.emit(&format!(
            "IFCPROPERTYSINGLEVALUE({},$,IFCTEXT({}),$)",
            ifc_str("EntityId"),
            ifc_str(eid)
        ));
        prop_refs.push_str(&format!(",#{p_eid}"));
    }
    let pset = w.emit(&format!(
        "IFCPROPERTYSET({},#{owner},{},$,({prop_refs}))",
        ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
            format!("pset:id:{cid}").as_bytes()
        ))),
        ifc_str("Pset_ArxosIdentity"),
    ));
    w.emit(&format!(
        "IFCRELDEFINESBYPROPERTIES({},#{owner},$,$,(#{target}),#{pset})",
        ifc_str(&global_id_from_cid(&Cid::from_canonical_bytes(
            format!("rel:id:{cid}").as_bytes()
        )))
    ));
}
