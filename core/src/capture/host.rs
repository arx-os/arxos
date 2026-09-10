//! Opening → wall host heuristic.
//!
//! Used by RoomPlan mapping. Do not change `HOST_PLANE_MAX_M` /
//! `HOST_EXTENT_PAD_M` / CID tie-break without a field reason.

use crate::cid::Cid;
use crate::entity::EntityId;
use crate::object::Pose;

/// Max plane distance (meters) for an Opening to attach to a wall.
///
/// Farther than this, the opening is emitted with `host_entity = None` and
/// property `host=unresolved`. Realize / IFC skip the void relationship
/// until a later ingest resolves the host.
pub const HOST_PLANE_MAX_M: f64 = 0.35;
/// In-plane pad (meters) added to wall `extent` when testing the projected
/// opening origin. Projection outside the padded rectangle is not a host.
pub const HOST_EXTENT_PAD_M: f64 = 0.15;
/// Opening property value when no wall host survives the heuristic.
pub const HOST_UNRESOLVED: &str = "unresolved";
/// Opening property key for host resolution status.
pub const HOST_PROP: &str = "host";

/// One wall that may host an Opening. Built from mapped `Surface` Facts
/// with `surface_kind = wall` (slabs / ceilings are not candidates).
#[derive(Debug, Clone)]
pub struct WallHostCandidate {
    pub entity_id: EntityId,
    pub pose: Pose,
    /// Local extent: `[width, height, thickness]` (meters).
    pub extent: [f64; 3],
    /// Unsigned CID of the wall Fact in this ingest batch (tie-break only).
    pub cid: Cid,
}

/// Distance from `point` to the wall plane (local XY of `wall_pose`; normal = local +Z).
pub fn plane_distance(wall_pose: &Pose, point: [f64; 3]) -> f64 {
    let n = wall_pose.local_z();
    let dx = point[0] - wall_pose.position[0];
    let dy = point[1] - wall_pose.position[1];
    let dz = point[2] - wall_pose.position[2];
    (n[0] * dx + n[1] * dy + n[2] * dz).abs()
}

/// Wall face coordinates of `point` in the wall pose's local XY (meters).
///
/// Equivalent to projecting onto the plane, then reading local X/Y: the
/// normal component does not contribute to those axes.
pub fn wall_local_xy(wall_pose: &Pose, point: [f64; 3]) -> [f64; 2] {
    let dx = point[0] - wall_pose.position[0];
    let dy = point[1] - wall_pose.position[1];
    let dz = point[2] - wall_pose.position[2];
    let x = wall_pose.local_x();
    let y = wall_pose.local_y();
    [
        x[0] * dx + x[1] * dy + x[2] * dz,
        y[0] * dx + y[1] * dy + y[2] * dz,
    ]
}

/// Assign an Opening to a wall host.
///
/// 1. Candidates: walls only.
/// 2. Project the opening origin onto each wall plane.
/// 3. Reject if plane distance `> HOST_PLANE_MAX_M` or the projection falls
///    outside wall `extent` expanded by `HOST_EXTENT_PAD_M`.
/// 4. Winner: smallest plane distance; tie → larger face area
///    (`extent[0] * extent[1]`); tie → higher CID.
///
/// `None` means leave `host_entity` unset and stamp `host=unresolved`.
/// Do not glue the opening to a random nearby wall.
pub fn resolve_opening_host(walls: &[WallHostCandidate], opening: &Pose) -> Option<EntityId> {
    let mut best: Option<(EntityId, f64, f64, Cid)> = None;
    for w in walls {
        let dist = plane_distance(&w.pose, opening.position);
        if dist > HOST_PLANE_MAX_M {
            continue;
        }
        let [lx, ly] = wall_local_xy(&w.pose, opening.position);
        if lx.abs() > w.extent[0] / 2.0 + HOST_EXTENT_PAD_M
            || ly.abs() > w.extent[1] / 2.0 + HOST_EXTENT_PAD_M
        {
            continue;
        }
        let area = w.extent[0] * w.extent[1];
        let better = match &best {
            None => true,
            Some((_, bd, ba, bc)) => {
                if dist < *bd - 1e-9 {
                    true
                } else if (dist - *bd).abs() < 1e-9 {
                    if area > *ba + 1e-9 {
                        true
                    } else if (area - *ba).abs() < 1e-9 {
                        w.cid > *bc
                    } else {
                        false
                    }
                } else {
                    false
                }
            }
        };
        if better {
            best = Some((w.entity_id.clone(), dist, area, w.cid));
        }
    }
    best.map(|(e, _, _, _)| e)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::object::Pose;

    #[test]
    fn equal_distance_prefers_larger_area_then_higher_cid() {
        let pose = Pose {
            position: [0.0, 1.25, 0.0],
            orientation: [0.0, 0.0, 0.0, 1.0],
        };
        let opening = Pose {
            position: [0.0, 1.0, 0.05],
            orientation: [0.0, 0.0, 0.0, 1.0],
        };
        let small = WallHostCandidate {
            entity_id: EntityId::from("rp:small".to_string()),
            pose: pose.clone(),
            extent: [2.0, 2.5, 0.15],
            cid: Cid::from_bytes([1; 32]),
        };
        let large = WallHostCandidate {
            entity_id: EntityId::from("rp:large".to_string()),
            pose: pose.clone(),
            extent: [4.0, 2.5, 0.15],
            cid: Cid::from_bytes([0; 32]),
        };
        assert_eq!(
            resolve_opening_host(&[small.clone(), large.clone()], &opening)
                .map(|e| e.as_str().to_string()),
            Some("rp:large".into())
        );

        let a = WallHostCandidate {
            entity_id: EntityId::from("rp:a".to_string()),
            pose: pose.clone(),
            extent: [4.0, 2.5, 0.15],
            cid: Cid::from_bytes([1; 32]),
        };
        let b = WallHostCandidate {
            entity_id: EntityId::from("rp:b".to_string()),
            pose,
            extent: [4.0, 2.5, 0.15],
            cid: Cid::from_bytes([2; 32]),
        };
        assert_eq!(
            resolve_opening_host(&[a, b], &opening).map(|e| e.as_str().to_string()),
            Some("rp:b".into()),
            "tie on distance and area → higher CID"
        );
    }
}
