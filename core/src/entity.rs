//! Stable mutable identity for physical entities.
//!
//! [`EntityId`] names a physical thing (room, floor, equipment, …) across
//! successive content-addressed **versions**. Each version is still a normal
//! object with its own CID; roots hold version CIDs in the active set.
//!
//! At commit and merge, [`collapse_active_set`] ensures at most one version
//! per `EntityId` remains. Objects without an `entity_id` (legacy) never
//! collapse with peers — they are identified solely by CID.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::str::FromStr;

use serde::{Deserialize, Serialize};
use ulid::Ulid;

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectBody};
use crate::store::ObjectStore;

/// Stable identifier for a physical entity within a building graph.
///
/// Globally unique ULID strings; uniqueness within a building is enforced by
/// collapse (one active version per id).
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct EntityId(String);

impl EntityId {
    /// Generate a new random entity ID.
    pub fn new() -> Self {
        Self(Ulid::new().to_string())
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl Default for EntityId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for EntityId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl FromStr for EntityId {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        if s.is_empty() {
            return Err(Error::Validation("entity id must not be empty".into()));
        }
        Ok(EntityId(s.to_string()))
    }
}

impl From<String> for EntityId {
    fn from(s: String) -> Self {
        EntityId(s)
    }
}

/// Extract the stable entity id from a domain object, if present.
pub fn entity_id_of(obj: &Object) -> Option<&EntityId> {
    match &obj.body {
        ObjectBody::Floor(b) => b.entity_id.as_ref(),
        ObjectBody::Space(b) => b.entity_id.as_ref(),
        ObjectBody::Surface(b) => b.entity_id.as_ref(),
        ObjectBody::Opening(b) => b.entity_id.as_ref(),
        ObjectBody::Equipment(b) => b.entity_id.as_ref(),
        ObjectBody::System(b) => b.entity_id.as_ref(),
        ObjectBody::Circuit(b) => b.entity_id.as_ref(),
        ObjectBody::Sensor(b) => b.entity_id.as_ref(),
        ObjectBody::Fixture(b) => b.entity_id.as_ref(),
        _ => None,
    }
}

/// True when this object type participates in entity identity.
pub fn is_entity_typed(obj: &Object) -> bool {
    matches!(
        obj.body,
        ObjectBody::Floor(_)
            | ObjectBody::Space(_)
            | ObjectBody::Surface(_)
            | ObjectBody::Opening(_)
            | ObjectBody::Equipment(_)
            | ObjectBody::System(_)
            | ObjectBody::Circuit(_)
            | ObjectBody::Sensor(_)
            | ObjectBody::Fixture(_)
    )
}

/// Result of collapsing an active set by [`EntityId`].
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CollapseResult {
    /// Active CIDs after collapse (at most one version per entity id).
    pub kept: BTreeSet<Cid>,
    /// Version CIDs dropped in favor of a newer version of the same entity.
    pub superseded: BTreeSet<Cid>,
}

#[derive(Clone)]
struct Candidate {
    cid: Cid,
    created: u64,
}

/// Collapse `cids` so that for every present [`EntityId`], only the winning
/// version remains.
///
/// Winner rules (deterministic):
/// 1. Highest `header.created`
/// 2. On equal `created`, prefer a CID present in `prefer` (e.g. staged updates)
/// 3. Else highest `Cid`
///
/// Objects without `entity_id` or missing from the store are kept as-is.
pub fn collapse_active_set(
    store: &ObjectStore,
    cids: &BTreeSet<Cid>,
) -> Result<CollapseResult> {
    collapse_active_set_preferring(store, cids, &BTreeSet::new())
}

/// Like [`collapse_active_set`], but on equal `created` prefers CIDs in `prefer`
/// (typically the staged set on commit).
pub fn collapse_active_set_preferring(
    store: &ObjectStore,
    cids: &BTreeSet<Cid>,
    prefer: &BTreeSet<Cid>,
) -> Result<CollapseResult> {
    // entity_id → best candidate
    let mut best: BTreeMap<EntityId, Candidate> = BTreeMap::new();
    // All CIDs that carry an entity_id (for superseded calculation).
    let mut entity_versions: BTreeMap<EntityId, Vec<Cid>> = BTreeMap::new();
    let mut non_entity: BTreeSet<Cid> = BTreeSet::new();

    for cid in cids {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => {
                // Preserve the reference; completeness is enforced elsewhere.
                non_entity.insert(*cid);
                continue;
            }
            Err(e) => return Err(e),
        };
        match entity_id_of(&obj).cloned() {
            Some(eid) => {
                entity_versions.entry(eid.clone()).or_default().push(*cid);
                let cand = Candidate {
                    cid: *cid,
                    created: obj.header.created,
                };
                match best.get(&eid) {
                    None => {
                        best.insert(eid, cand);
                    }
                    Some(prev) => {
                        if beats(prev, &cand, prefer) {
                            // keep prev
                        } else {
                            best.insert(eid, cand);
                        }
                    }
                }
            }
            None => {
                non_entity.insert(*cid);
            }
        }
    }

    let mut kept = non_entity;
    let mut superseded = BTreeSet::new();
    for (eid, versions) in entity_versions {
        let winner = best
            .get(&eid)
            .map(|c| c.cid)
            .expect("best must contain every entity with versions");
        kept.insert(winner);
        for v in versions {
            if v != winner {
                superseded.insert(v);
            }
        }
    }

    Ok(CollapseResult { kept, superseded })
}

/// True when `prev` should remain preferred over `cand`.
fn beats(prev: &Candidate, cand: &Candidate, prefer: &BTreeSet<Cid>) -> bool {
    if prev.created != cand.created {
        return prev.created > cand.created;
    }
    let prev_pref = prefer.contains(&prev.cid);
    let cand_pref = prefer.contains(&cand.cid);
    if prev_pref != cand_pref {
        return prev_pref;
    }
    prev.cid > cand.cid
}

/// Find active CIDs that carry `entity_id`.
pub fn find_entity_versions(
    store: &ObjectStore,
    cids: &BTreeSet<Cid>,
    entity_id: &EntityId,
) -> Result<BTreeSet<Cid>> {
    let mut out = BTreeSet::new();
    for cid in cids {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        };
        if entity_id_of(&obj) == Some(entity_id) {
            out.insert(*cid);
        }
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::object::{ObjectBody, Pose, SpaceBody, SCHEMA_VERSION};
    use crate::object::{Object, ObjectHeader, ObjectType};
    use std::collections::BTreeMap;
    use tempfile::tempdir;

    fn space(eid: Option<EntityId>, created: u64, name: &str) -> Object {
        Object {
            header: ObjectHeader {
                object_type: ObjectType::Space,
                schema_version: SCHEMA_VERSION,
                created,
                author: None,
                signature: None,
            },
            body: ObjectBody::Space(SpaceBody {
                entity_id: eid,
                name: Some(name.into()),
                floor: None,
                pose: Some(Pose::default()),
                bounds: None,
                properties: BTreeMap::new(),
            }),
        }
    }

    #[test]
    fn collapse_keeps_newer_version() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let eid = EntityId::from("01ENTITYTEST00000000000000".to_string());
        let old = space(Some(eid.clone()), 100, "v1");
        let new = space(Some(eid.clone()), 200, "v2");
        let c_old = store.put(&old).unwrap();
        let c_new = store.put(&new).unwrap();
        let mut set = BTreeSet::new();
        set.insert(c_old);
        set.insert(c_new);
        let r = collapse_active_set(&store, &set).unwrap();
        assert_eq!(r.kept, BTreeSet::from([c_new]));
        assert_eq!(r.superseded, BTreeSet::from([c_old]));
    }

    #[test]
    fn legacy_without_entity_id_never_collapses() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let a = space(None, 100, "a");
        let b = space(None, 200, "b");
        let ca = store.put(&a).unwrap();
        let cb = store.put(&b).unwrap();
        let mut set = BTreeSet::new();
        set.insert(ca);
        set.insert(cb);
        let r = collapse_active_set(&store, &set).unwrap();
        assert_eq!(r.kept.len(), 2);
        assert!(r.superseded.is_empty());
    }

    #[test]
    fn tie_break_by_cid() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let eid = EntityId::from("01ENTITYTIE000000000000000".to_string());
        // Same created; different names → different CIDs; higher CID wins.
        let a = space(Some(eid.clone()), 50, "aaa");
        let b = space(Some(eid.clone()), 50, "zzz");
        let ca = store.put(&a).unwrap();
        let cb = store.put(&b).unwrap();
        let winner = ca.max(cb);
        let loser = ca.min(cb);
        let mut set = BTreeSet::new();
        set.insert(ca);
        set.insert(cb);
        let r = collapse_active_set(&store, &set).unwrap();
        assert_eq!(r.kept, BTreeSet::from([winner]));
        assert_eq!(r.superseded, BTreeSet::from([loser]));
    }
}
