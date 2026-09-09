//! RoomPlan → Fact mapping.
//!
//! Apple RoomPlan surfaces/objects become named Facts (`Surface`, `Opening`,
//! `Equipment`) with stable [`EntityId`]s derived from Apple UUIDs. The phone
//! is a camera that mints Facts; it is not the official building replica.

use std::collections::BTreeMap;

use crate::entity::EntityId;
use crate::error::{Error, Result};
use crate::object::{
    Aabb, EquipmentBody, Object, ObjectBody, OpeningBody, Pose, SpaceBody, SurfaceBody,
};

use super::{pose_from_column_major_matrix, world_aabb_from_transform_and_dimensions};

/// Default 1σ for RoomPlan wall/slab/ceiling surfaces (millimeters).
pub const ROOMPLAN_SURFACE_SIGMA_MM: f64 = 40.0;
/// Default 1σ for RoomPlan furniture / equipment proxies (millimeters).
pub const ROOMPLAN_EQUIPMENT_SIGMA_MM: f64 = 50.0;
/// Default 1σ for RoomPlan openings (millimeters).
pub const ROOMPLAN_OPENING_SIGMA_MM: f64 = 40.0;

/// Default wall thickness when RoomPlan omits depth (meters).
pub const DEFAULT_WALL_THICKNESS_M: f64 = 0.15;
/// Default slab / floor / ceiling thickness when omitted (meters).
pub const DEFAULT_SLAB_THICKNESS_M: f64 = 0.30;

/// One RoomPlan captured surface (wall, floor, door, window, …).
#[derive(Debug, Clone, PartialEq)]
pub struct RoomPlanSurface {
    /// Apple UUID (or any stable identifier from the capture session).
    pub id: String,
    /// RoomPlan category (`wall`, `door`, `window`, `floor`, `opening`, …).
    pub category: String,
    /// 4×4 column-major transform (ARKit Y-up).
    pub transform: Vec<f64>,
    /// Local dimensions `(width, height, depth)` in meters.
    pub dimensions: Vec<f64>,
}

/// One RoomPlan captured object (furniture / equipment proxy).
#[derive(Debug, Clone, PartialEq)]
pub struct RoomPlanObject {
    pub id: String,
    pub category: String,
    pub transform: Vec<f64>,
    pub dimensions: Vec<f64>,
}

/// Batch of RoomPlan geometry from one capture stop.
#[derive(Debug, Clone, PartialEq, Default)]
pub struct RoomPlanGeometry {
    pub surfaces: Vec<RoomPlanSurface>,
    pub objects: Vec<RoomPlanObject>,
}

/// Unsigned Fact objects produced by [`map_roomplan`].
#[derive(Debug, Clone)]
pub struct MappedRoomPlan {
    pub space: Object,
    pub surfaces: Vec<Object>,
    pub openings: Vec<Object>,
    pub equipment: Vec<Object>,
}

impl MappedRoomPlan {
    /// Overwrite surface/opening σ (CLI simulate / tests).
    pub fn set_sigma_mm(&mut self, sigma_mm: f64) {
        for o in &mut self.surfaces {
            if let ObjectBody::Surface(b) = &mut o.body {
                b.sigma_mm = Some(sigma_mm);
            }
        }
        for o in &mut self.openings {
            if let ObjectBody::Opening(b) = &mut o.body {
                b.sigma_mm = Some(sigma_mm);
            }
        }
    }
}

/// CIDs returned after staging a mapped RoomPlan batch.
#[derive(Debug, Clone)]
pub struct MappedRoomPlanCids {
    pub space: crate::cid::Cid,
    pub surfaces: Vec<crate::cid::Cid>,
    pub openings: Vec<crate::cid::Cid>,
    pub equipment: Vec<crate::cid::Cid>,
}

/// Stable entity id from an Apple RoomPlan UUID.
///
/// `entity_id = "rp:" + lowercase(uuid)`. Empty ids are rejected (fail closed).
pub fn entity_id_from_roomplan_uuid(uuid: &str) -> Result<EntityId> {
    let trimmed = uuid.trim();
    if trimmed.is_empty() {
        return Err(Error::Validation(
            "RoomPlan surface/object id must not be empty".into(),
        ));
    }
    Ok(EntityId::from(format!("rp:{}", trimmed.to_lowercase())))
}

/// Stable space id for one ingest batch: `rp-space:` + hash of sorted surface ids.
pub fn space_entity_id_from_surface_ids<'a, I>(surface_ids: I) -> EntityId
where
    I: IntoIterator<Item = &'a str>,
{
    let mut ids: Vec<String> = surface_ids
        .into_iter()
        .map(|s| s.trim().to_lowercase())
        .filter(|s| !s.is_empty())
        .collect();
    ids.sort();
    ids.dedup();
    let material = ids.join("|");
    let digest = blake3::hash(material.as_bytes());
    let hex = hex::encode(&digest.as_bytes()[..16]);
    EntityId::from(format!("rp-space:{hex}"))
}

fn normalize_kind(s: &str) -> String {
    s.trim().to_lowercase()
}

fn is_opening_kind(kind: &str) -> bool {
    matches!(kind, "door" | "window" | "opening")
}

fn is_wall_kind(kind: &str) -> bool {
    kind == "wall"
}

fn default_thickness(kind: &str) -> f64 {
    match kind {
        "floor" | "slab" | "ceiling" => DEFAULT_SLAB_THICKNESS_M,
        _ => DEFAULT_WALL_THICKNESS_M,
    }
}

fn extent_from_dimensions(dimensions: &[f64], kind: &str) -> Result<[f64; 3]> {
    if dimensions.len() != 3 {
        return Err(Error::Validation(format!(
            "RoomPlan dimensions must have 3 elements, got {}",
            dimensions.len()
        )));
    }
    let mut e = [dimensions[0], dimensions[1], dimensions[2]];
    if e[2] == 0.0 {
        e[2] = default_thickness(kind);
    }
    crate::object::canonicalize_extent(&mut e)?;
    Ok(e)
}

/// Distance from `point` to the wall plane (local XY of `wall_pose`; normal = local +Z).
pub fn plane_distance(wall_pose: &Pose, point: [f64; 3]) -> f64 {
    let n = wall_pose.local_z();
    let dx = point[0] - wall_pose.position[0];
    let dy = point[1] - wall_pose.position[1];
    let dz = point[2] - wall_pose.position[2];
    (n[0] * dx + n[1] * dy + n[2] * dz).abs()
}

/// Choose the nearest wall entity in XY/plane distance for an opening pose.
pub fn nearest_wall_entity(walls: &[(EntityId, Pose)], opening: &Pose) -> Option<EntityId> {
    let mut best: Option<(EntityId, f64, f64)> = None;
    for (eid, pose) in walls {
        let plane = plane_distance(pose, opening.position);
        let dx = pose.position[0] - opening.position[0];
        let dz = pose.position[2] - opening.position[2];
        let xy = (dx * dx + dz * dz).sqrt();
        let better = match &best {
            None => true,
            Some((_, bp, bxy)) => plane < *bp - 1e-9 || ((plane - *bp).abs() < 1e-9 && xy < *bxy),
        };
        if better {
            best = Some((eid.clone(), plane, xy));
        }
    }
    best.map(|(e, _, _)| e)
}

fn source_props(id: &str) -> BTreeMap<String, String> {
    let mut p = BTreeMap::new();
    p.insert("identifier".into(), id.to_string());
    p.insert("source".into(), "roomplan".into());
    p
}

/// Map RoomPlan geometry to unsigned Fact objects.
///
/// Walls / floors / slabs / ceilings become [`Surface`] Facts. Doors / windows /
/// openings become [`Opening`] Facts hosted on the nearest wall (XY plane
/// heuristic). Furniture becomes [`Equipment`].
///
/// `created` is stamped on every object so a second ingest of the same Apple
/// UUIDs yields the same [`EntityId`] and a new CID (unless the timestamp
/// collides and the body is identical).
pub fn map_roomplan(geometry: &RoomPlanGeometry, created: u64) -> Result<MappedRoomPlan> {
    let space_entity = space_entity_id_from_surface_ids(geometry.surfaces.iter().map(|s| s.id.as_str()));

    let mut room_bounds: Option<Aabb> = None;
    let mut parsed_surfaces: Vec<(RoomPlanSurface, Pose, Aabb, [f64; 3], String)> = Vec::new();

    for s in &geometry.surfaces {
        let pose = pose_from_column_major_matrix(&s.transform)?;
        let bounds = world_aabb_from_transform_and_dimensions(&s.transform, &s.dimensions)?;
        let kind = normalize_kind(&s.category);
        let extent = extent_from_dimensions(&s.dimensions, &kind)?;
        expand_bounds(&mut room_bounds, &bounds);
        parsed_surfaces.push((s.clone(), pose, bounds, extent, kind));
    }

    let mut parsed_objects: Vec<(RoomPlanObject, Pose, Aabb, [f64; 3])> = Vec::new();
    for o in &geometry.objects {
        let pose = pose_from_column_major_matrix(&o.transform)?;
        let bounds = world_aabb_from_transform_and_dimensions(&o.transform, &o.dimensions)?;
        let kind = normalize_kind(&o.category);
        let extent = extent_from_dimensions(&o.dimensions, &kind)?;
        expand_bounds(&mut room_bounds, &bounds);
        parsed_objects.push((o.clone(), pose, bounds, extent));
    }

    let space_pose = if let Some(ref rb) = room_bounds {
        Pose {
            position: [
                (rb.min[0] + rb.max[0]) / 2.0,
                (rb.min[1] + rb.max[1]) / 2.0,
                (rb.min[2] + rb.max[2]) / 2.0,
            ],
            orientation: [0.0, 0.0, 0.0, 1.0],
        }
    } else {
        Pose::default()
    };

    let mut space_props = BTreeMap::new();
    space_props.insert("source".into(), "roomplan".into());
    let space = Object::new_with_created(
        ObjectBody::Space(SpaceBody {
            entity_id: Some(space_entity),
            name: Some("RoomPlan Room".into()),
            floor: None,
            pose: Some(space_pose),
            bounds: room_bounds,
            properties: space_props,
        }),
        created,
    );

    let mut walls: Vec<(EntityId, Pose)> = Vec::new();
    for (s, pose, _, _, kind) in &parsed_surfaces {
        if is_wall_kind(kind) {
            walls.push((entity_id_from_roomplan_uuid(&s.id)?, pose.clone()));
        }
    }

    let mut surfaces = Vec::new();
    let mut openings = Vec::new();
    for (s, pose, bounds, extent, kind) in parsed_surfaces {
        let entity_id = entity_id_from_roomplan_uuid(&s.id)?;
        let mut properties = source_props(&s.id);
        properties.insert("width".into(), s.dimensions.first().copied().unwrap_or(0.0).to_string());
        properties.insert("height".into(), s.dimensions.get(1).copied().unwrap_or(0.0).to_string());
        properties.insert("depth".into(), s.dimensions.get(2).copied().unwrap_or(0.0).to_string());

        if is_opening_kind(&kind) {
            let host_entity = nearest_wall_entity(&walls, &pose);
            openings.push(Object::new_with_created(
                ObjectBody::Opening(OpeningBody {
                    entity_id: Some(entity_id),
                    host_surface: None,
                    host_entity,
                    pose: Some(pose),
                    opening_kind: Some(kind),
                    extent: Some(extent),
                    sigma_mm: Some(ROOMPLAN_OPENING_SIGMA_MM),
                    support_count: 1,
                    evidence: Vec::new(),
                    properties,
                }),
                created,
            ));
        } else {
            surfaces.push(Object::new_with_created(
                ObjectBody::Surface(SurfaceBody {
                    entity_id: Some(entity_id),
                    space: None,
                    pose: Some(pose),
                    bounds: Some(bounds),
                    surface_kind: Some(kind),
                    extent: Some(extent),
                    sigma_mm: Some(ROOMPLAN_SURFACE_SIGMA_MM),
                    support_count: 1,
                    evidence: Vec::new(),
                    properties,
                }),
                created,
            ));
        }
    }

    let mut equipment = Vec::new();
    for (o, pose, _bounds, extent) in parsed_objects {
        let entity_id = entity_id_from_roomplan_uuid(&o.id)?;
        let kind = normalize_kind(&o.category);
        equipment.push(Object::new_with_created(
            ObjectBody::Equipment(EquipmentBody {
                entity_id: Some(entity_id),
                name: Some(o.category.clone()),
                equipment_kind: Some(kind),
                pose: Some(pose),
                system: None,
                extent: Some(extent),
                sigma_mm: Some(ROOMPLAN_EQUIPMENT_SIGMA_MM),
                support_count: 1,
                evidence: Vec::new(),
                properties: source_props(&o.id),
            }),
            created,
        ));
    }

    Ok(MappedRoomPlan {
        space,
        surfaces,
        openings,
        equipment,
    })
}

fn expand_bounds(acc: &mut Option<Aabb>, bounds: &Aabb) {
    if let Some(ref mut rb) = acc {
        rb.min[0] = rb.min[0].min(bounds.min[0]);
        rb.min[1] = rb.min[1].min(bounds.min[1]);
        rb.min[2] = rb.min[2].min(bounds.min[2]);
        rb.max[0] = rb.max[0].max(bounds.max[0]);
        rb.max[1] = rb.max[1].max(bounds.max[1]);
        rb.max[2] = rb.max[2].max(bounds.max[2]);
    } else {
        *acc = Some(bounds.clone());
    }
}

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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::entity::entity_id_of;

    #[test]
    fn same_uuid_same_entity_id() {
        let g = RoomPlanGeometry {
            surfaces: vec![RoomPlanSurface {
                id: "AABBCCDD-EEFF-0011-2233-445566778899".into(),
                category: "wall".into(),
                transform: identity_transform(0.0, 1.25, 0.0),
                dimensions: vec![4.0, 2.5, 0.15],
            }],
            objects: vec![],
        };
        let a = map_roomplan(&g, 100).unwrap();
        let b = map_roomplan(&g, 200).unwrap();
        let ea = entity_id_of(&a.surfaces[0]).unwrap();
        let eb = entity_id_of(&b.surfaces[0]).unwrap();
        assert_eq!(ea, eb);
        assert_eq!(ea.as_str(), "rp:aabbccdd-eeff-0011-2233-445566778899");
        assert_ne!(a.surfaces[0].cid().unwrap(), b.surfaces[0].cid().unwrap());
        match &a.surfaces[0].body {
            ObjectBody::Surface(s) => {
                assert_eq!(s.sigma_mm, Some(ROOMPLAN_SURFACE_SIGMA_MM));
                assert_eq!(s.extent, Some([4.0, 2.5, 0.15]));
                assert_eq!(s.support_count, 1);
            }
            _ => panic!("expected surface"),
        }
    }

    #[test]
    fn door_hosts_on_nearest_wall() {
        let g = RoomPlanGeometry {
            surfaces: vec![
                RoomPlanSurface {
                    id: "wall-a".into(),
                    category: "wall".into(),
                    transform: identity_transform(0.0, 1.25, 0.0),
                    dimensions: vec![4.0, 2.5, 0.15],
                },
                RoomPlanSurface {
                    id: "wall-b".into(),
                    category: "wall".into(),
                    transform: identity_transform(0.0, 1.25, 4.0),
                    dimensions: vec![4.0, 2.5, 0.15],
                },
                RoomPlanSurface {
                    id: "door-1".into(),
                    category: "door".into(),
                    transform: identity_transform(0.0, 1.0, 0.05),
                    dimensions: vec![0.9, 2.1, 0.1],
                },
            ],
            objects: vec![],
        };
        let mapped = map_roomplan(&g, 1).unwrap();
        assert_eq!(mapped.surfaces.len(), 2);
        assert_eq!(mapped.openings.len(), 1);
        match &mapped.openings[0].body {
            ObjectBody::Opening(o) => {
                assert_eq!(o.opening_kind.as_deref(), Some("door"));
                assert_eq!(
                    o.host_entity.as_ref().map(|e| e.as_str()),
                    Some("rp:wall-a")
                );
            }
            _ => panic!("expected opening"),
        }
    }

    #[test]
    fn space_id_stable_across_ingest() {
        let g = hall_four_walls([0.0, 0.0, 0.0], 40.0);
        let a = map_roomplan(&g, 1).unwrap();
        let b = map_roomplan(&g, 2).unwrap();
        assert_eq!(entity_id_of(&a.space), entity_id_of(&b.space));
        assert!(entity_id_of(&a.space)
            .unwrap()
            .as_str()
            .starts_with("rp-space:"));
    }

    #[test]
    fn empty_uuid_rejected() {
        let g = RoomPlanGeometry {
            surfaces: vec![RoomPlanSurface {
                id: "  ".into(),
                category: "wall".into(),
                transform: identity_transform(0.0, 0.0, 0.0),
                dimensions: vec![1.0, 1.0, 0.1],
            }],
            objects: vec![],
        };
        assert!(map_roomplan(&g, 1).is_err());
    }
}
