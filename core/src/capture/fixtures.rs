//! Deterministic RoomPlan geometry for CLI simulate and golden tests.

use super::roomplan::{RoomPlanGeometry, RoomPlanSurface};

/// Identity 4×4 column-major with translation `(tx, ty, tz)`.
pub fn identity_transform(tx: f64, ty: f64, tz: f64) -> Vec<f64> {
    vec![
        1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, tx, ty, tz, 1.0,
    ]
}

/// 90° about +Y (wall facing +X): local X along −Z, local Y up, local Z along +X.
pub fn rot_y_90_transform(tx: f64, ty: f64, tz: f64) -> Vec<f64> {
    vec![
        0.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, tx, ty, tz, 1.0,
    ]
}

/// Stable Apple UUID for the simulated hall door (south wall).
pub const HALL_DOOR_UUID: &str = "00000000-0000-0000-0000-000000000010";

/// Four walls of a 4×4 m room (centers at height 1.25 m, thickness 0.15 m).
///
/// Stable Apple-style UUIDs so a second call with a translation fuses rather
/// than stacking walls. Used by CLI simulate and slice golden tests.
pub fn hall_four_walls(translation: [f64; 3], sigma_ignored_here: f64) -> RoomPlanGeometry {
    let _ = sigma_ignored_here;
    let [dx, dy, dz] = translation;
    let h = 1.25 + dy;
    RoomPlanGeometry {
        surfaces: vec![
            RoomPlanSurface {
                id: "00000000-0000-0000-0000-000000000001".into(),
                category: "wall".into(),
                transform: identity_transform(2.0 + dx, h, 0.0 + dz),
                dimensions: vec![4.0, 2.5, 0.15],
            },
            RoomPlanSurface {
                id: "00000000-0000-0000-0000-000000000002".into(),
                category: "wall".into(),
                transform: identity_transform(2.0 + dx, h, 4.0 + dz),
                dimensions: vec![4.0, 2.5, 0.15],
            },
            RoomPlanSurface {
                id: "00000000-0000-0000-0000-000000000003".into(),
                category: "wall".into(),
                transform: rot_y_90_transform(0.0 + dx, h, 2.0 + dz),
                dimensions: vec![4.0, 2.5, 0.15],
            },
            RoomPlanSurface {
                id: "00000000-0000-0000-0000-000000000004".into(),
                category: "wall".into(),
                transform: rot_y_90_transform(4.0 + dx, h, 2.0 + dz),
                dimensions: vec![4.0, 2.5, 0.15],
            },
        ],
        objects: Vec::new(),
    }
}

/// [`hall_four_walls`] plus a 0.9×2.1 m door on the south wall (z = 0).
///
/// Same Apple UUIDs as the walls helper so `--dx` / `--sigma-mm` simulate
/// walks fuse. The door origin sits 50 mm in front of the wall plane so
/// [`super::host::resolve_opening_host`] accepts it.
pub fn hall_four_walls_with_door(translation: [f64; 3], sigma_mm: f64) -> RoomPlanGeometry {
    let mut g = hall_four_walls(translation, sigma_mm);
    let [dx, dy, dz] = translation;
    g.surfaces.push(RoomPlanSurface {
        id: HALL_DOOR_UUID.into(),
        category: "door".into(),
        transform: identity_transform(2.0 + dx, 1.05 + dy, 0.05 + dz),
        dimensions: vec![0.9, 2.1, 0.1],
    });
    g
}
