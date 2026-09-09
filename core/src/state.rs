//! Official building state \(S\): the map from [`EntityId`] to live Fact.
//!
//! \[
//! S : \mathrm{EntityId} \rightarrow \mathrm{Fact}
//! \]
//!
//! Readers (realize, export, slice, score-by-entity) consume [`BuildingState`],
//! not a raw CID soup. Objects without `entity_id` are legacy isolates: kept,
//! never fused.

use std::collections::BTreeMap;

use crate::cid::Cid;
use crate::entity::{collapse_active_set, entity_id_of, EntityId};
use crate::error::Result;
use crate::object::Object;
use crate::root::RootBody;
use crate::store::ObjectRead;

/// Materialized official map \(S\) plus leftover objects that have no entity id.
#[derive(Debug, Clone)]
pub struct BuildingState {
    /// Live Fact per entity (one CID after collapse).
    facts: BTreeMap<EntityId, (Cid, Object)>,
    /// Legacy isolates and non-entity objects (Building, Root refs, blobs, …).
    leftovers: Vec<(Cid, Object)>,
    /// Root this state was materialized from, when known.
    pub root_cid: Option<Cid>,
}

impl BuildingState {
    /// Materialize \(S\) from a Root: active set → collapse → index by entity.
    pub fn from_root<R: ObjectRead + ?Sized>(store: &R, root: &RootBody) -> Result<Self> {
        let active = root.materialize_active_objects(store)?;
        Self::from_cids(store, &active, None)
    }

    /// Materialize from an explicit object set (already the intended active set).
    pub fn from_cids<R: ObjectRead + ?Sized>(
        store: &R,
        cids: &std::collections::BTreeSet<Cid>,
        root_cid: Option<Cid>,
    ) -> Result<Self> {
        let collapsed = collapse_active_set(store, cids)?;
        let mut facts = BTreeMap::new();
        let mut leftovers = Vec::new();
        for cid in &collapsed.kept {
            let obj = match store.get(cid) {
                Ok(o) => o,
                Err(crate::error::Error::NotFound(_)) => continue,
                Err(e) => return Err(e),
            };
            match entity_id_of(&obj).cloned() {
                Some(eid) => {
                    facts.insert(eid, (*cid, obj));
                }
                None => leftovers.push((*cid, obj)),
            }
        }
        leftovers.sort_by(|a, b| a.0.cmp(&b.0));
        Ok(Self {
            facts,
            leftovers,
            root_cid,
        })
    }

    /// Live Fact for `id`, if present.
    pub fn get(&self, id: &EntityId) -> Option<&Object> {
        self.facts.get(id).map(|(_, o)| o)
    }

    /// Live CID for `id`, if present.
    pub fn cid_of(&self, id: &EntityId) -> Option<Cid> {
        self.facts.get(id).map(|(c, _)| *c)
    }

    /// Iterator over named Facts.
    pub fn facts(&self) -> impl Iterator<Item = (&EntityId, &Object)> {
        self.facts.iter().map(|(id, (_, o))| (id, o))
    }

    /// Iterator over named Facts with their CIDs.
    pub fn facts_with_cids(&self) -> impl Iterator<Item = (&EntityId, Cid, &Object)> {
        self.facts.iter().map(|(id, (c, o))| (id, *c, o))
    }

    /// Number of named entities in \(S\).
    pub fn len(&self) -> usize {
        self.facts.len()
    }

    /// True when no named entities are present.
    pub fn is_empty(&self) -> bool {
        self.facts.is_empty()
    }

    /// Legacy isolates (no `entity_id`).
    pub fn leftovers(&self) -> &[(Cid, Object)] {
        &self.leftovers
    }

    /// Named Facts of a given object type.
    pub fn facts_of_type(&self, ty: crate::object::ObjectType) -> Vec<(&EntityId, Cid, &Object)> {
        self.facts
            .iter()
            .filter(|(_, (_, o))| o.header.object_type == ty)
            .map(|(id, (c, o))| (id, *c, o))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::object::{ObjectBody, Pose, SurfaceBody};
    use crate::repository::BuildingRepository;
    use crate::Keypair;
    use tempfile::tempdir;

    #[test]
    fn from_root_indexes_by_entity() {
        let dir = tempdir().unwrap();
        let kp = Keypair::generate();
        let mut repo = BuildingRepository::init(
            dir.path(),
            Some("S".into()),
            Some(Keypair::from_seed(*kp.seed())),
        )
        .unwrap();
        let wall = Object::new_with_created(
            ObjectBody::Surface(SurfaceBody {
                entity_id: Some(EntityId::from("wall-a".to_string())),
                pose: Some(Pose::default()),
                surface_kind: Some("wall".into()),
                extent: Some([1.0, 2.0, 0.15]),
                sigma_mm: Some(40.0),
                support_count: 1,
                ..Default::default()
            }),
            1,
        );
        repo.stage_captured_object(wall).unwrap();
        repo.commit(Some("one wall".into())).unwrap();
        let head = repo.head_root().unwrap();
        let root_obj = repo.get_object(&head).unwrap();
        let root = crate::root::RootBody::from_object(&root_obj).unwrap();
        let state = BuildingState::from_root(&repo, root).unwrap();
        assert!(state.get(&EntityId::from("wall-a".to_string())).is_some());
        assert_eq!(state.facts_of_type(crate::object::ObjectType::Surface).len(), 1);
    }
}
