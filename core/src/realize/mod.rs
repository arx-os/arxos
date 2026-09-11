//! Realization \( B = R(S) \): Facts → solids (still not pixels).
//!
//! Read-only. v1 extrudes pose + extent into oriented boxes. v2 clips wall
//! rectangles by neighboring non-parallel planes and lists hosted openings
//! as `voids`. If clip/subtract fails, the v1 box is kept — a wall is never
//! dropped because CSG was sad. ASCII occupancy may use boxes.
//!
//! # Coordinate frame
//!
//! Building-local **meters**, right-handed, **Y-up** (Phase-0 pose policy).
//!
//! | Concept | Convention |
//! |---|---|
//! | World up | \(+Y\) |
//! | `plane_rect` surface | local **XY** of `pose` |
//! | Surface normal | \(R(\mathrm{pose})\cdot(0,0,1)\) = local \(+Z\) |
//! | `extent[0]` | width along local \(X\) |
//! | `extent[1]` | height along local \(Y\) |
//! | `extent[2]` | thickness along local \(Z\) (default wall 0.15 m / slab 0.30 m) |
//!
//! RoomPlan / ARKit wall frames already match this: local X = width, local Y =
//! height (world-up), local Z = thickness / wall normal. Identity pose ⇒ normal
//! is world \(+Z\). A 90° about \(+Y\) ⇒ normal is world \(+X\).
//!
//! Facts with `sigma_mm > SIGMA_EXCLUDE_MM` (500 mm) stay in \(S\) but are
//! omitted from solids.

use crate::entity::EntityId;
use crate::error::Result;
use crate::object::{ObjectBody, ObjectType, Pose};
use crate::state::BuildingState;

mod clip;
pub use clip::{world_outline, CLIP_MIN_VERTS, NEIGHBOR_VERTICAL_MAX_M, PARALLEL_DOT};
pub use crate::measure::SIGMA_EXCLUDE_MM;

/// Default wall thickness when `extent[2]` is missing (meters).
pub const WALL_THICKNESS_M: f64 = 0.15;
/// Default slab / floor / ceiling thickness (meters).
pub const SLAB_THICKNESS_M: f64 = 0.30;
/// Default run radius when diameter is missing (meters).
pub const RUN_RADIUS_M: f64 = 0.02;

/// Kind of realized solid.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SolidKind {
    Wall,
    Slab,
    Opening,
    Equipment,
    Run,
}

impl SolidKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Wall => "wall",
            Self::Slab => "slab",
            Self::Opening => "opening",
            Self::Equipment => "equipment",
            Self::Run => "run",
        }
    }
}

/// Oriented box (or run polyline) produced by \(R(S)\).
#[derive(Debug, Clone, PartialEq)]
pub struct Solid {
    pub entity_id: EntityId,
    pub cid: crate::cid::Cid,
    pub kind: SolidKind,
    pub pose: Pose,
    /// v1 box extents `[width, height, thickness]` (meters). Always present.
    pub extent: [f64; 3],
    /// Local-XY polygon when v2 clipping succeeded (≥ 3 vertices).
    pub outline_xy: Option<Vec<[f64; 2]>>,
    pub host: Option<EntityId>,
    /// Openings hosted on this solid (realize v2). Empty for non-walls.
    pub voids: Vec<EntityId>,
    /// Run polyline (building-local meters). Empty for boxes.
    pub points: Vec<[f64; 3]>,
    pub radius_m: f64,
}

/// \( B = R(S) \).
#[derive(Debug, Clone, Default)]
pub struct Realization {
    pub solids: Vec<Solid>,
    pub spaces: Vec<(EntityId, crate::cid::Cid)>,
    pub notes: Vec<(crate::cid::Cid, String, Pose)>,
}

/// Count Facts that \(R(S)\) skips because \(\sigma\) exceeds [`SIGMA_EXCLUDE_MM`].
pub fn high_sigma_skip_count(state: &BuildingState) -> u64 {
    state
        .facts()
        .filter(|(_, obj)| {
            matches!(
                obj.header.object_type,
                ObjectType::Surface | ObjectType::Opening | ObjectType::Equipment | ObjectType::Run
            ) && obj
                .sigma_mm()
                .map(|s| s > SIGMA_EXCLUDE_MM)
                .unwrap_or(false)
        })
        .count() as u64
}

/// Realize solids from official state. Read-only.
pub fn realize(state: &BuildingState) -> Result<Realization> {
    let mut out = Realization::default();
    for (eid, cid, obj) in state.facts_with_cids() {
        if let Some(s) = obj.sigma_mm() {
            if s > SIGMA_EXCLUDE_MM
                && matches!(
                    obj.header.object_type,
                    ObjectType::Surface
                        | ObjectType::Opening
                        | ObjectType::Equipment
                        | ObjectType::Run
                )
            {
                continue;
            }
        }
        match &obj.body {
            ObjectBody::Surface(b) => {
                let Some(pose) = b.pose.clone() else {
                    continue;
                };
                let kind_str = b.surface_kind.as_deref().unwrap_or("wall");
                let solid_kind = match kind_str {
                    "floor" | "slab" | "ceiling" => SolidKind::Slab,
                    _ => SolidKind::Wall,
                };
                let mut extent = obj
                    .extent()
                    .unwrap_or([1.0, 1.0, default_thickness(solid_kind)]);
                if extent[2] == 0.0 {
                    extent[2] = default_thickness(solid_kind);
                }
                out.solids.push(Solid {
                    entity_id: eid.clone(),
                    cid,
                    kind: solid_kind,
                    pose,
                    extent,
                    outline_xy: None,
                    host: None,
                    voids: Vec::new(),
                    points: Vec::new(),
                    radius_m: 0.0,
                });
            }
            ObjectBody::Opening(b) => {
                let Some(pose) = b.pose.clone() else {
                    continue;
                };
                let extent = obj.extent().unwrap_or([0.9, 2.1, 0.1]);
                out.solids.push(Solid {
                    entity_id: eid.clone(),
                    cid,
                    kind: SolidKind::Opening,
                    pose,
                    extent,
                    outline_xy: None,
                    host: b.host_entity.clone(),
                    voids: Vec::new(),
                    points: Vec::new(),
                    radius_m: 0.0,
                });
            }
            ObjectBody::Equipment(b) => {
                let Some(pose) = b.pose.clone() else {
                    continue;
                };
                let extent = obj.extent().unwrap_or([0.5, 0.5, 0.5]);
                out.solids.push(Solid {
                    entity_id: eid.clone(),
                    cid,
                    kind: SolidKind::Equipment,
                    pose,
                    extent,
                    outline_xy: None,
                    host: None,
                    voids: Vec::new(),
                    points: Vec::new(),
                    radius_m: 0.0,
                });
            }
            ObjectBody::Run(b) => {
                let pose = b.pose.clone().unwrap_or_default();
                let radius = b
                    .diameter_m
                    .map(|d| d / 2.0)
                    .filter(|r| *r > 0.0)
                    .unwrap_or(RUN_RADIUS_M);
                out.solids.push(Solid {
                    entity_id: eid.clone(),
                    cid,
                    kind: SolidKind::Run,
                    pose,
                    extent: obj.extent().unwrap_or([0.0, 0.0, 0.0]),
                    outline_xy: None,
                    host: None,
                    voids: Vec::new(),
                    points: b.points.clone(),
                    radius_m: radius,
                });
            }
            ObjectBody::Space(_) => {
                out.spaces.push((eid.clone(), cid));
            }
            ObjectBody::Floor(_) => {
                out.spaces.push((eid.clone(), cid));
            }
            ObjectBody::Annotation(a) => {
                if let (Some(text), Some(pose)) = (a.text.clone(), a.pose.clone()) {
                    out.notes.push((cid, text, pose));
                }
            }
            _ => {}
        }
    }
    out.solids.sort_by(|a, b| a.entity_id.cmp(&b.entity_id));
    clip::apply_v2(&mut out);
    out.solids.sort_by(|a, b| a.entity_id.cmp(&b.entity_id));
    out.spaces.sort_by(|a, b| a.0.cmp(&b.0));
    out.notes.sort_by(|a, b| a.0.cmp(&b.0));
    Ok(out)
}

fn default_thickness(kind: SolidKind) -> f64 {
    match kind {
        SolidKind::Slab => SLAB_THICKNESS_M,
        _ => WALL_THICKNESS_M,
    }
}

/// True if world point `p` lies inside the oriented box of `solid`.
pub fn point_in_solid(solid: &Solid, p: [f64; 3]) -> bool {
    if solid.kind == SolidKind::Run {
        return point_near_run(solid, p);
    }
    let d = [
        p[0] - solid.pose.position[0],
        p[1] - solid.pose.position[1],
        p[2] - solid.pose.position[2],
    ];
    let lx = solid.pose.local_x();
    let ly = solid.pose.local_y();
    let lz = solid.pose.local_z();
    let local = [
        d[0] * lx[0] + d[1] * lx[1] + d[2] * lx[2],
        d[0] * ly[0] + d[1] * ly[1] + d[2] * ly[2],
        d[0] * lz[0] + d[1] * lz[1] + d[2] * lz[2],
    ];
    let hx = solid.extent[0] / 2.0;
    let hy = solid.extent[1] / 2.0;
    let hz = solid.extent[2] / 2.0;
    local[0].abs() <= hx + 1e-9 && local[1].abs() <= hy + 1e-9 && local[2].abs() <= hz + 1e-9
}

fn point_near_run(solid: &Solid, p: [f64; 3]) -> bool {
    let r = solid.radius_m.max(0.0);
    let pts = if solid.points.len() >= 2 {
        &solid.points[..]
    } else {
        return dist2(p, solid.pose.position).sqrt() <= r + 1e-9;
    };
    for w in pts.windows(2) {
        if dist_point_segment(p, w[0], w[1]) <= r + 1e-9 {
            return true;
        }
    }
    false
}

fn dist2(a: [f64; 3], b: [f64; 3]) -> f64 {
    let dx = a[0] - b[0];
    let dy = a[1] - b[1];
    let dz = a[2] - b[2];
    dx * dx + dy * dy + dz * dz
}

fn dist_point_segment(p: [f64; 3], a: [f64; 3], b: [f64; 3]) -> f64 {
    let ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    let ap = [p[0] - a[0], p[1] - a[1], p[2] - a[2]];
    let ab2 = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2];
    let t = if ab2 <= 1e-18 {
        0.0
    } else {
        ((ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / ab2).clamp(0.0, 1.0)
    };
    let q = [a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2]];
    dist2(p, q).sqrt()
}

/// Occupancy glyph at a world point: `+` opening, `o` equipment, `#` wall/slab, `.` empty.
pub fn occupancy_glyph(realization: &Realization, p: [f64; 3]) -> char {
    let mut wall = false;
    let mut opening = false;
    let mut equipment = false;
    for s in &realization.solids {
        if !point_in_solid(s, p) {
            continue;
        }
        match s.kind {
            SolidKind::Opening => opening = true,
            SolidKind::Equipment => equipment = true,
            SolidKind::Wall | SolidKind::Slab => wall = true,
            SolidKind::Run => equipment = true,
        }
    }
    if opening {
        '+'
    } else if equipment {
        'o'
    } else if wall {
        '#'
    } else {
        '.'
    }
}

/// ASCII slice of occupancy on the plane \(Y = z\) (Y-up floor plan), grid in XZ.
///
/// Rows run from max Z (top) to min Z. `--width` caps the number of columns.
pub fn ascii_slice(realization: &Realization, z: f64, cell: f64, width: usize) -> String {
    let cell = if cell > 1e-6 { cell } else { 0.25 };
    let width = width.max(8);
    let boxes: Vec<&Solid> = realization
        .solids
        .iter()
        .filter(|s| s.kind != SolidKind::Run)
        .collect();
    if boxes.is_empty() {
        return "(no solids)\n".into();
    }
    let mut min_x = f64::INFINITY;
    let mut max_x = f64::NEG_INFINITY;
    let mut min_z = f64::INFINITY;
    let mut max_z = f64::NEG_INFINITY;
    for s in &boxes {
        let hx = s.extent[0] / 2.0 + s.extent[2] / 2.0;
        min_x = min_x.min(s.pose.position[0] - hx);
        max_x = max_x.max(s.pose.position[0] + hx);
        min_z = min_z.min(s.pose.position[2] - hx);
        max_z = max_z.max(s.pose.position[2] + hx);
    }
    min_x -= cell;
    max_x += cell;
    min_z -= cell;
    max_z += cell;
    let nx = (((max_x - min_x) / cell).ceil() as usize).clamp(1, width);
    let nz = (((max_z - min_z) / cell).ceil() as usize).clamp(1, width * 2);
    let mut lines = Vec::with_capacity(nz);
    for iz in 0..nz {
        // Top of the map = max Z.
        let z_world = max_z - (iz as f64 + 0.5) * (max_z - min_z) / nz as f64;
        let mut row = String::with_capacity(nx);
        for ix in 0..nx {
            let x_world = min_x + (ix as f64 + 0.5) * (max_x - min_x) / nx as f64;
            row.push(occupancy_glyph(realization, [x_world, z, z_world]));
        }
        lines.push(row);
    }
    lines.join("\n") + "\n"
}

/// Normalize a slice for golden tests: strip trailing spaces, keep `#`/`+`/`o`/`.`.
pub fn normalize_slice(s: &str) -> String {
    s.lines()
        .map(|l| l.trim_end())
        .filter(|l| !l.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::entity::EntityId;
    use crate::object::{Object, ObjectBody, OpeningBody, SurfaceBody};
    use crate::Cid;
    use std::collections::BTreeSet;

    fn wall_at(eid: &str, pos: [f64; 3], extent: [f64; 3], orient: [f64; 4]) -> Object {
        Object::new_with_created(
            ObjectBody::Surface(SurfaceBody {
                entity_id: Some(EntityId::from(eid.to_string())),
                pose: Some(Pose {
                    position: pos,
                    orientation: orient,
                }),
                surface_kind: Some("wall".into()),
                extent: Some(extent),
                sigma_mm: Some(40.0),
                support_count: 1,
                ..Default::default()
            }),
            1,
        )
    }

    fn state_from(objs: Vec<Object>) -> BuildingState {
        use crate::store::ObjectStore;
        let dir = tempfile::tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let mut cids = BTreeSet::new();
        for o in objs {
            cids.insert(store.put(&o).unwrap());
        }
        BuildingState::from_cids(&store, &cids, None).unwrap()
    }

    #[test]
    fn identity_pose_wall_normal_is_plus_z() {
        let w = wall_at(
            "w",
            [0.0, 1.25, 0.0],
            [4.0, 2.5, 0.15],
            [0.0, 0.0, 0.0, 1.0],
        );
        let n = w.pose().unwrap().local_z();
        assert!((n[0]).abs() < 1e-9);
        assert!((n[1]).abs() < 1e-9);
        assert!((n[2] - 1.0).abs() < 1e-9);
        let state = state_from(vec![w]);
        let r = realize(&state).unwrap();
        assert_eq!(r.solids.len(), 1);
        assert_eq!(r.solids[0].kind, SolidKind::Wall);
        // A point on the wall plane at the center is inside.
        assert!(point_in_solid(&r.solids[0], [0.0, 1.25, 0.0]));
        // 1 m along +Z (normal) is outside a 0.15 m thick wall.
        assert!(!point_in_solid(&r.solids[0], [0.0, 1.25, 1.0]));
    }

    #[test]
    fn rot_y_90_wall_normal_is_plus_x() {
        // q = (0, sin(π/4), 0, cos(π/4))
        let s = std::f64::consts::FRAC_1_SQRT_2;
        let w = wall_at("w", [0.0, 1.25, 2.0], [4.0, 2.5, 0.15], [0.0, s, 0.0, s]);
        let n = w.pose().unwrap().local_z();
        assert!((n[0] - 1.0).abs() < 1e-6, "normal {n:?}");
        assert!(n[1].abs() < 1e-6);
        assert!(n[2].abs() < 1e-6);
        let state = state_from(vec![w]);
        let r = realize(&state).unwrap();
        assert!(point_in_solid(&r.solids[0], [0.0, 1.25, 2.0]));
        assert!(!point_in_solid(&r.solids[0], [1.0, 1.25, 2.0]));
    }

    #[test]
    fn high_sigma_excluded_from_solids() {
        let mut w = wall_at("w", [0.0, 1.0, 0.0], [1.0, 2.0, 0.15], [0.0, 0.0, 0.0, 1.0]);
        if let ObjectBody::Surface(ref mut b) = w.body {
            b.sigma_mm = Some(800.0);
        }
        let state = state_from(vec![w]);
        let r = realize(&state).unwrap();
        assert!(r.solids.is_empty());
        assert!(state.get(&EntityId::from("w".to_string())).is_some());
    }

    #[test]
    fn opening_records_host() {
        let host = EntityId::from("wall-a".to_string());
        let door = Object::new_with_created(
            ObjectBody::Opening(OpeningBody {
                entity_id: Some(EntityId::from("door-1".to_string())),
                host_entity: Some(host.clone()),
                pose: Some(Pose::default()),
                opening_kind: Some("door".into()),
                extent: Some([0.9, 2.1, 0.1]),
                sigma_mm: Some(40.0),
                support_count: 1,
                ..Default::default()
            }),
            1,
        );
        let state = state_from(vec![door]);
        let r = realize(&state).unwrap();
        assert_eq!(r.solids[0].kind, SolidKind::Opening);
        assert_eq!(r.solids[0].host.as_ref(), Some(&host));
        let _ = Cid::from_canonical_bytes(b"x");
    }

    #[test]
    fn hall_slice_is_hollow_rectangle() {
        use crate::capture::roomplan::{hall_four_walls, map_roomplan};
        let g = hall_four_walls([0.0, 0.0, 0.0], 40.0);
        let mapped = map_roomplan(&g, 1).unwrap();
        let state = state_from(mapped.surfaces);
        let r = realize(&state).unwrap();
        assert_eq!(r.solids.len(), 4);
        let grid = ascii_slice(&r, 1.2, 0.25, 80);
        let norm = normalize_slice(&grid);
        assert!(norm.contains('#'), "{norm}");
        // Hollow: some interior row is mostly '.' with '#' at the sides.
        let rows: Vec<&str> = norm.lines().collect();
        assert!(rows.len() >= 4, "{norm}");
        let mid = rows[rows.len() / 2];
        assert!(
            mid.contains('.'),
            "mid row should have empty interior: {mid}"
        );
        assert!(mid.contains('#'), "mid row should still hit walls: {mid}");
    }
}
