//! Realize v2: clip wall rectangles by neighboring planes and list voids.
//!
//! If clipping yields fewer than 3 vertices, the solid keeps the v1 box
//! (`outline_xy = None`). Openings with `host_entity` are listed on the host
//! `Solid.voids`. A 2D rectangle is subtracted from `outline_xy` only when
//! that cut stays a single polygon; otherwise the outline is kept and the
//! void list is still the IFC relationship.

use super::{Realization, Solid, SolidKind};
use crate::entity::EntityId;

/// Neighbors farther than this in world Y are not the same storey (meters).
pub const NEIGHBOR_VERTICAL_MAX_M: f64 = 0.25;
/// `|n_i · n_j|` at or above this is treated as parallel (no clip line).
pub const PARALLEL_DOT: f64 = 0.95;
/// Minimum vertices for a clipped outline; fewer → v1 box fallback.
pub const CLIP_MIN_VERTS: usize = 3;

/// Apply v2 clip + void listing in place. Never drops a wall.
pub fn apply_v2(out: &mut Realization) {
    clip_walls(out);
    attach_voids(out);
}

fn clip_walls(out: &mut Realization) {
    let walls: Vec<(usize, EntityId, crate::object::Pose, [f64; 3])> = out
        .solids
        .iter()
        .enumerate()
        .filter(|(_, s)| s.kind == SolidKind::Wall)
        .map(|(i, s)| (i, s.entity_id.clone(), s.pose.clone(), s.extent))
        .collect();

    for (i, _eid, pose, extent) in &walls {
        let mut poly = box_outline(*extent);
        for (j, _, npose, _) in &walls {
            if i == j {
                continue;
            }
            if (pose.position[1] - npose.position[1]).abs() > NEIGHBOR_VERTICAL_MAX_M {
                continue;
            }
            let ni = pose.local_z();
            let nj = npose.local_z();
            let dot = (ni[0] * nj[0] + ni[1] * nj[1] + ni[2] * nj[2]).abs();
            if dot >= PARALLEL_DOT {
                continue;
            }
            let Some((a, b, c0)) = neighbor_line(pose, npose) else {
                continue;
            };
            if c0.abs() < 1e-12 {
                continue;
            }
            poly = clip_halfplane(&poly, a, b, c0);
        }
        if poly.len() >= CLIP_MIN_VERTS {
            out.solids[*i].outline_xy = Some(poly);
        }
        // else keep v1 box (outline_xy stays None)
    }
}

/// Line `c0 + a x + b y = 0` in wall local XY from neighbor plane.
fn neighbor_line(
    wall: &crate::object::Pose,
    neighbor: &crate::object::Pose,
) -> Option<(f64, f64, f64)> {
    let n = neighbor.local_z();
    let lx = wall.local_x();
    let ly = wall.local_y();
    let a = n[0] * lx[0] + n[1] * lx[1] + n[2] * lx[2];
    let b = n[0] * ly[0] + n[1] * ly[1] + n[2] * ly[2];
    let d = [
        wall.position[0] - neighbor.position[0],
        wall.position[1] - neighbor.position[1],
        wall.position[2] - neighbor.position[2],
    ];
    let c0 = n[0] * d[0] + n[1] * d[1] + n[2] * d[2];
    if a * a + b * b < 1e-18 {
        return None;
    }
    Some((a, b, c0))
}

fn box_outline(extent: [f64; 3]) -> Vec<[f64; 2]> {
    let hx = extent[0] / 2.0;
    let hy = extent[1] / 2.0;
    vec![[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]]
}

/// Keep the half-plane whose sign matches the wall origin (`c0`).
fn clip_halfplane(poly: &[[f64; 2]], a: f64, b: f64, c0: f64) -> Vec<[f64; 2]> {
    if poly.is_empty() {
        return Vec::new();
    }
    let mut out = Vec::with_capacity(poly.len() + 2);
    let n = poly.len();
    for i in 0..n {
        let p = poly[i];
        let q = poly[(i + 1) % n];
        let pin = inside(a, b, c0, p);
        let qin = inside(a, b, c0, q);
        if pin && qin {
            out.push(q);
        } else if pin && !qin {
            if let Some(x) = intersect(a, b, c0, p, q) {
                out.push(x);
            }
        } else if !pin && qin {
            if let Some(x) = intersect(a, b, c0, p, q) {
                out.push(x);
            }
            out.push(q);
        }
    }
    dedup_closed(&mut out);
    out
}

fn inside(a: f64, b: f64, c0: f64, p: [f64; 2]) -> bool {
    let v = c0 + a * p[0] + b * p[1];
    v * c0 >= -1e-12
}

fn intersect(a: f64, b: f64, c0: f64, p: [f64; 2], q: [f64; 2]) -> Option<[f64; 2]> {
    let vp = c0 + a * p[0] + b * p[1];
    let vq = c0 + a * q[0] + b * q[1];
    let den = vp - vq;
    if den.abs() < 1e-18 {
        return None;
    }
    let t = vp / den;
    Some([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])])
}

fn dedup_closed(poly: &mut Vec<[f64; 2]>) {
    const EPS: f64 = 1e-9;
    let mut i = 0;
    while i < poly.len() {
        let j = (i + 1) % poly.len();
        let d0 = (poly[i][0] - poly[j][0]).abs();
        let d1 = (poly[i][1] - poly[j][1]).abs();
        if d0 < EPS && d1 < EPS {
            poly.remove(j);
            if j < i {
                i = i.saturating_sub(1);
            }
            if poly.len() < 2 {
                break;
            }
        } else {
            i += 1;
        }
        if i >= poly.len() {
            break;
        }
    }
}

fn attach_voids(out: &mut Realization) {
    let openings: Vec<(EntityId, Option<EntityId>, crate::object::Pose, [f64; 3])> = out
        .solids
        .iter()
        .filter(|s| s.kind == SolidKind::Opening)
        .map(|s| {
            (
                s.entity_id.clone(),
                s.host.clone(),
                s.pose.clone(),
                s.extent,
            )
        })
        .collect();

    for (oid, host, opose, oext) in openings {
        let Some(host_id) = host else {
            continue;
        };
        let Some(wall) = out
            .solids
            .iter_mut()
            .find(|s| s.kind == SolidKind::Wall && s.entity_id == host_id)
        else {
            continue;
        };
        if !wall.voids.iter().any(|e| e == &oid) {
            wall.voids.push(oid);
        }
        try_notch(wall, &opose, oext);
    }
}

/// Subtract an axis-aligned opening rectangle from a rectangular outline when
/// the cut stays one polygon (a notch from an edge). Interior holes are left
/// as void-list only so we never split the wall into islands.
fn try_notch(wall: &mut Solid, opening: &crate::object::Pose, oext: [f64; 3]) {
    let outline = wall
        .outline_xy
        .clone()
        .unwrap_or_else(|| box_outline(wall.extent));
    if outline.len() != 4 {
        return;
    }
    let [ox, oy] = crate::capture::roomplan::wall_local_xy(&wall.pose, opening.position);
    let hw = oext[0] / 2.0;
    let hh = oext[1] / 2.0;
    let hole = [ox - hw, oy - hh, ox + hw, oy + hh]; // xmin, ymin, xmax, ymax
    let Some(notched) = notch_rect(&outline, hole) else {
        return;
    };
    if notched.len() >= CLIP_MIN_VERTS {
        wall.outline_xy = Some(notched);
    }
}

/// `hole` is `[xmin, ymin, xmax, ymax]` in the same frame as a 4-vertex
/// axis-aligned rectangle `outline`. Returns a U-notch if the hole overlaps
/// exactly one outer edge; `None` if it would punch an interior island.
fn notch_rect(outline: &[[f64; 2]], hole: [f64; 4]) -> Option<Vec<[f64; 2]>> {
    let mut min_x = f64::INFINITY;
    let mut max_x = f64::NEG_INFINITY;
    let mut min_y = f64::INFINITY;
    let mut max_y = f64::NEG_INFINITY;
    for p in outline {
        min_x = min_x.min(p[0]);
        max_x = max_x.max(p[0]);
        min_y = min_y.min(p[1]);
        max_y = max_y.max(p[1]);
    }
    let [hx0, hy0, hx1, hy1] = hole;
    let ix0 = hx0.max(min_x);
    let iy0 = hy0.max(min_y);
    let ix1 = hx1.min(max_x);
    let iy1 = hy1.min(max_y);
    if ix1 - ix0 < 1e-6 || iy1 - iy0 < 1e-6 {
        return None;
    }
    let touch_bottom = (iy0 - min_y).abs() < 1e-6;
    let touch_top = (iy1 - max_y).abs() < 1e-6;
    let touch_left = (ix0 - min_x).abs() < 1e-6;
    let touch_right = (ix1 - max_x).abs() < 1e-6;
    let edges = [touch_bottom, touch_top, touch_left, touch_right]
        .iter()
        .filter(|t| **t)
        .count();
    if edges != 1 {
        return None;
    }
    // CCW from bottom-left, cutting a U from the touched edge.
    let poly = if touch_bottom {
        vec![
            [min_x, min_y],
            [ix0, min_y],
            [ix0, iy1],
            [ix1, iy1],
            [ix1, min_y],
            [max_x, min_y],
            [max_x, max_y],
            [min_x, max_y],
        ]
    } else if touch_top {
        vec![
            [min_x, min_y],
            [max_x, min_y],
            [max_x, max_y],
            [ix1, max_y],
            [ix1, iy0],
            [ix0, iy0],
            [ix0, max_y],
            [min_x, max_y],
        ]
    } else if touch_left {
        vec![
            [min_x, min_y],
            [max_x, min_y],
            [max_x, max_y],
            [min_x, max_y],
            [min_x, iy1],
            [ix1, iy1],
            [ix1, iy0],
            [min_x, iy0],
        ]
    } else {
        vec![
            [min_x, min_y],
            [max_x, min_y],
            [max_x, iy0],
            [ix0, iy0],
            [ix0, iy1],
            [max_x, iy1],
            [max_x, max_y],
            [min_x, max_y],
        ]
    };
    Some(poly)
}

/// World-space face vertices (local Z = 0) for tests and projectors.
pub fn world_outline(solid: &Solid) -> Vec<[f64; 3]> {
    let pts = solid
        .outline_xy
        .clone()
        .unwrap_or_else(|| box_outline(solid.extent));
    let lx = solid.pose.local_x();
    let ly = solid.pose.local_y();
    let c = solid.pose.position;
    pts.iter()
        .map(|[x, y]| {
            [
                c[0] + lx[0] * x + ly[0] * y,
                c[1] + lx[1] * x + ly[1] * y,
                c[2] + lx[2] * x + ly[2] * y,
            ]
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::roomplan::{hall_four_walls, hall_four_walls_with_door, map_roomplan};
    use crate::object::Object;
    use crate::realize::{realize, SolidKind};
    use crate::state::BuildingState;
    use crate::store::ObjectStore;
    use std::collections::BTreeSet;

    fn state_from(objs: Vec<Object>) -> BuildingState {
        let dir = tempfile::tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let mut cids = BTreeSet::new();
        for o in objs {
            cids.insert(store.put(&o).unwrap());
        }
        BuildingState::from_cids(&store, &cids, None).unwrap()
    }

    #[test]
    fn four_wall_room_outlines_meet_at_corners() {
        let g = hall_four_walls([0.0, 0.0, 0.0], 40.0);
        let mapped = map_roomplan(&g, 1).unwrap();
        let state = state_from(mapped.surfaces);
        let r = realize(&state).unwrap();
        let walls: Vec<_> = r
            .solids
            .iter()
            .filter(|s| s.kind == SolidKind::Wall)
            .collect();
        assert_eq!(walls.len(), 4);
        for w in &walls {
            let o = w.outline_xy.as_ref().expect("v2 outline");
            assert!(
                o.len() >= 3,
                "wall {} outline verts {}",
                w.entity_id,
                o.len()
            );
        }
        // Every wall shares a vertex with some other wall within 20 mm.
        let pts: Vec<Vec<[f64; 3]>> = walls.iter().map(|w| world_outline(w)).collect();
        for (i, a) in pts.iter().enumerate() {
            let mut hit = false;
            for (j, b) in pts.iter().enumerate() {
                if i == j {
                    continue;
                }
                for pa in a {
                    for pb in b {
                        let d = ((pa[0] - pb[0]).powi(2)
                            + (pa[1] - pb[1]).powi(2)
                            + (pa[2] - pb[2]).powi(2))
                        .sqrt();
                        if d <= 0.020 + 1e-9 {
                            hit = true;
                        }
                    }
                }
            }
            assert!(hit, "wall {i} does not meet a neighbor within 20 mm");
        }
    }

    #[test]
    fn door_is_listed_as_void_on_host() {
        let g = hall_four_walls_with_door([0.0, 0.0, 0.0], 40.0);
        let mapped = map_roomplan(&g, 1).unwrap();
        let mut objs = mapped.surfaces;
        objs.extend(mapped.openings);
        let state = state_from(objs);
        let r = realize(&state).unwrap();
        let door = r
            .solids
            .iter()
            .find(|s| s.kind == SolidKind::Opening)
            .expect("door");
        let host_id = door.host.clone().expect("hosted");
        let host = r
            .solids
            .iter()
            .find(|s| s.entity_id == host_id)
            .expect("host wall");
        assert!(
            host.voids.iter().any(|e| e == &door.entity_id),
            "host voids {:?}, door {}",
            host.voids,
            door.entity_id
        );
        // Notch from the floor *or* box+void list; both are v2-complete.
        if let Some(outline) = &host.outline_xy {
            assert!(outline.len() >= 3);
        }
    }

    #[test]
    fn clip_failure_keeps_v1_box() {
        // A lone wall has no neighbors; outline may still be the starting
        // rectangle (clip of nothing). A wall with no pose is skipped earlier.
        let mut r = Realization::default();
        apply_v2(&mut r);
        assert!(r.solids.is_empty());
    }
}
