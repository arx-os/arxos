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

pub use super::fixtures::{
    hall_four_walls, hall_four_walls_with_door, identity_transform, rot_y_90_transform,
    HALL_DOOR_UUID,
};
pub use super::host::{
    plane_distance, resolve_opening_host, wall_local_xy, WallHostCandidate, HOST_EXTENT_PAD_M,
    HOST_PLANE_MAX_M, HOST_PROP, HOST_UNRESOLVED,
};

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

fn source_props(id: &str) -> BTreeMap<String, String> {
    let mut p = BTreeMap::new();
    p.insert("identifier".into(), id.to_string());
    p.insert("source".into(), "roomplan".into());
    p
}

/// Map RoomPlan geometry to unsigned Fact objects.
///
/// Walls / floors / slabs / ceilings become [`Surface`] Facts. Doors / windows /
/// openings become [`Opening`] Facts hosted on a wall via
/// [`resolve_opening_host`]. Furniture becomes [`Equipment`].
///
/// `created` is stamped on every object so a second ingest of the same Apple
/// UUIDs yields the same [`EntityId`] (`rp:` + lowercase uuid) and a new CID
/// (unless the timestamp collides and the body is identical).
pub fn map_roomplan(geometry: &RoomPlanGeometry, created: u64) -> Result<MappedRoomPlan> {
    let space_entity =
        space_entity_id_from_surface_ids(geometry.surfaces.iter().map(|s| s.id.as_str()));

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

    struct OpeningInput {
        entity_id: EntityId,
        pose: Pose,
        extent: [f64; 3],
        kind: String,
        properties: BTreeMap<String, String>,
    }

    let mut surfaces = Vec::new();
    let mut opening_inputs: Vec<OpeningInput> = Vec::new();
    for (s, pose, bounds, extent, kind) in parsed_surfaces {
        let entity_id = entity_id_from_roomplan_uuid(&s.id)?;
        let mut properties = source_props(&s.id);
        properties.insert(
            "width".into(),
            s.dimensions.first().copied().unwrap_or(0.0).to_string(),
        );
        properties.insert(
            "height".into(),
            s.dimensions.get(1).copied().unwrap_or(0.0).to_string(),
        );
        properties.insert(
            "depth".into(),
            s.dimensions.get(2).copied().unwrap_or(0.0).to_string(),
        );

        if is_opening_kind(&kind) {
            opening_inputs.push(OpeningInput {
                entity_id,
                pose,
                extent,
                kind,
                properties,
            });
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

    let mut walls: Vec<WallHostCandidate> = Vec::new();
    for obj in &surfaces {
        let ObjectBody::Surface(b) = &obj.body else {
            continue;
        };
        if !b.surface_kind.as_deref().is_some_and(is_wall_kind) {
            continue;
        }
        let (Some(eid), Some(pose), Some(extent)) = (&b.entity_id, &b.pose, b.extent) else {
            continue;
        };
        walls.push(WallHostCandidate {
            entity_id: eid.clone(),
            pose: pose.clone(),
            extent,
            cid: obj.cid()?,
        });
    }

    let mut openings = Vec::new();
    for mut input in opening_inputs {
        let host_entity = resolve_opening_host(&walls, &input.pose);
        if host_entity.is_none() {
            input
                .properties
                .insert(HOST_PROP.into(), HOST_UNRESOLVED.into());
        }
        openings.push(Object::new_with_created(
            ObjectBody::Opening(OpeningBody {
                entity_id: Some(input.entity_id),
                host_surface: None,
                host_entity,
                pose: Some(input.pose),
                opening_kind: Some(input.kind),
                extent: Some(input.extent),
                sigma_mm: Some(ROOMPLAN_OPENING_SIGMA_MM),
                support_count: 1,
                evidence: Vec::new(),
                properties: input.properties,
            }),
            created,
        ));
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

    fn parallel_walls_and_door(door_tz: f64, door_tx: f64) -> RoomPlanGeometry {
        RoomPlanGeometry {
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
                    transform: identity_transform(door_tx, 1.0, door_tz),
                    dimensions: vec![0.9, 2.1, 0.1],
                },
            ],
            objects: vec![],
        }
    }

    fn opening_host(mapped: &MappedRoomPlan) -> (Option<String>, Option<String>) {
        match &mapped.openings[0].body {
            ObjectBody::Opening(o) => (
                o.host_entity.as_ref().map(|e| e.as_str().to_string()),
                o.properties.get(HOST_PROP).cloned(),
            ),
            _ => panic!("expected opening"),
        }
    }

    #[test]
    fn door_in_middle_of_wall_a_hosts_on_a() {
        // Two parallel walls 4 m apart; door on wall A's face.
        let mapped = map_roomplan(&parallel_walls_and_door(0.05, 0.0), 1).unwrap();
        assert_eq!(mapped.surfaces.len(), 2);
        assert_eq!(mapped.openings.len(), 1);
        let (host, host_prop) = opening_host(&mapped);
        assert_eq!(host.as_deref(), Some("rp:wall-a"));
        assert_eq!(host_prop, None);
    }

    #[test]
    fn door_two_metres_from_both_walls_is_unresolved() {
        let mapped = map_roomplan(&parallel_walls_and_door(2.0, 0.0), 1).unwrap();
        let (host, host_prop) = opening_host(&mapped);
        assert_eq!(host, None, "must not glue to a random wall");
        assert_eq!(host_prop.as_deref(), Some(HOST_UNRESOLVED));
    }

    #[test]
    fn door_outside_padded_extent_is_unresolved() {
        // Wall A width 4 m → half-width + pad = 2.15 m. Door at x=3.0 is off-wall.
        let mapped = map_roomplan(&parallel_walls_and_door(0.05, 3.0), 1).unwrap();
        let (host, host_prop) = opening_host(&mapped);
        assert_eq!(host, None);
        assert_eq!(host_prop.as_deref(), Some(HOST_UNRESOLVED));
    }

    #[test]
    fn floor_is_not_a_host_even_when_closer() {
        let g = RoomPlanGeometry {
            surfaces: vec![
                RoomPlanSurface {
                    id: "floor-1".into(),
                    category: "floor".into(),
                    transform: identity_transform(0.0, 1.25, 0.0),
                    dimensions: vec![4.0, 2.5, 0.15],
                },
                RoomPlanSurface {
                    id: "wall-far".into(),
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
        let (host, host_prop) = opening_host(&mapped);
        assert_eq!(host, None);
        assert_eq!(host_prop.as_deref(), Some(HOST_UNRESOLVED));
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
    fn hall_door_hosts_on_south_wall() {
        let mapped = map_roomplan(&hall_four_walls_with_door([0.0, 0.0, 0.0], 40.0), 1).unwrap();
        assert_eq!(mapped.surfaces.len(), 4);
        assert_eq!(mapped.openings.len(), 1);
        match &mapped.openings[0].body {
            ObjectBody::Opening(o) => {
                assert_eq!(o.opening_kind.as_deref(), Some("door"));
                assert_eq!(
                    o.host_entity.as_ref().map(|e| e.as_str()),
                    Some("rp:00000000-0000-0000-0000-000000000001")
                );
                assert_eq!(o.properties.get(HOST_PROP), None);
            }
            _ => panic!("expected opening"),
        }
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
