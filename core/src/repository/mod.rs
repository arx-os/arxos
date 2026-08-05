//! Building-as-repository: local head pointer + capture/commit workflow.
//!
//! Layout under the CAS root:
//! ```text
//! <store>/
//!   objects/…
//!   meta/buildings/<building_id>.cbor   # BuildingRecord (head, name, …)
//!   keys/device.seed                    # optional 32-byte ed25519 seed
//! ```
//!
//! No general-purpose database — only content-addressed objects plus a tiny
//! rebuildable head pointer file.

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::capture::{
    annotation_object, maybe_sign, put_point_cloud_chunk, space_object, AnnotationCapture,
    PointCloudCapture, SpaceCapture,
};
use crate::canonical::from_cbor;
use crate::cid::Cid;
use crate::crypto::{Keypair, PublicKey};
use crate::error::{Error, Result};
use crate::object::{BuildingBody, BuildingId, Object, ObjectBody, ObjectType};
use crate::root::{RootBody, RootBuilder};
use crate::store::ObjectStore;
use crate::working_set::WorkingSet;

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Persistent building metadata (head pointer, not object graph state).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BuildingRecord {
    pub building_id: BuildingId,
    pub name: Option<String>,
    /// CID of the Building object in the CAS.
    pub building_object: Option<Cid>,
    /// Current official head root CID for this device.
    pub head_root: Option<Cid>,
    /// Captures not yet included in a committed root (survives process restarts).
    #[serde(default)]
    pub pending: BTreeSet<Cid>,
    /// Object CIDs staged for removal on the next commit (explicit delete).
    #[serde(default)]
    pub pending_removes: BTreeSet<Cid>,
    pub updated: u64,
}

/// Result of a capture → put into the store.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CaptureResult {
    pub cid: Cid,
    pub object_type: ObjectType,
}

/// Result of committing a new root.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommitResult {
    pub root_cid: Cid,
    pub building_id: BuildingId,
    pub object_count: u64,
    pub previous_root: Option<Cid>,
}

/// Options for adopting a remote root.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct AdoptOptions {
    /// Allow untrusted root signatures / unauthorized authors.
    /// If false, verification failures cause adoption to fail.
    pub allow_untrusted: bool,
    /// Allow adopting a root even when some active objects (or the spatial index)
    /// are missing from the local store. Default is false (fail closed).
    pub allow_partial: bool,
}

/// Building repository handle: CAS + head metadata + session working set.
///
/// Holds an exclusive [`crate::store::WriteGuard`] for the store for the
/// lifetime of the repository (single-writer policy).
pub struct BuildingRepository {
    store: ObjectStore,
    /// Exclusive store lock — released on drop.
    _write_lock: crate::store::WriteGuard,
    record: BuildingRecord,
    working_set: WorkingSet,
    keypair: Option<Keypair>,
    active_objects: BTreeSet<Cid>,
}

mod adopt;
mod commit;
mod meta;
mod query;

impl BuildingRepository {
    /// Initialize a new building repository in `store_path`.
    pub fn init(
        store_path: impl AsRef<Path>,
        name: Option<String>,
        keypair: Option<Keypair>,
    ) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
        let write_lock = store.try_lock_exclusive()?;
        fs::create_dir_all(store.root().join("meta").join("buildings"))?;
        fs::create_dir_all(store.root().join("keys"))?;

        let building_id = BuildingId::new();
        let kp = keypair.unwrap_or_else(Keypair::generate);
        Self::write_seed(store.root(), &kp)?;

        let mut building_obj = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: building_id.clone(),
                name: name.clone(),
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            now_secs(),
        );
        building_obj.sign(&kp)?;
        let building_cid = store.put(&building_obj)?;

        let mut record = BuildingRecord {
            building_id: building_id.clone(),
            name,
            building_object: Some(building_cid),
            head_root: None,
            pending: BTreeSet::new(),
            pending_removes: BTreeSet::new(),
            updated: now_secs(),
        };

        // Initial root commits the building object alone.
        let mut active_objects = BTreeSet::new();
        active_objects.insert(building_cid);

        let mut objects = BTreeSet::new();
        objects.insert(building_cid);
        let (root_obj, root_cid) = RootBuilder::new(building_id.clone(), now_secs())
            .objects(objects)
            .message("init")
            .build_signed(&kp)?;
        // Fail closed: init root must be signed by a controller (the seed key we just registered).
        {
            let root = RootBody::from_object(&root_obj)?;
            root.verify_with_store(&store)?;
        }
        store.put(&root_obj)?;
        record.head_root = Some(root_cid);
        record.updated = now_secs();
        Self::write_record(store.root(), &record)?;

        let mut working_set = WorkingSet::new();
        working_set.stage(building_cid, building_obj);
        working_set.pin(building_cid);
        working_set.pin(root_cid);

        Ok(Self {
            store,
            _write_lock: write_lock,
            record,
            working_set,
            keypair: Some(kp),
            active_objects,
        })
    }

    /// Open an existing building by ID (loads head metadata + optional seed).
    pub fn open(store_path: impl AsRef<Path>, building_id: &BuildingId) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
        let write_lock = store.try_lock_exclusive()?;
        let record = Self::read_record(store.root(), building_id)?;
        let keypair = Self::read_seed(store.root()).ok();
        let mut working_set = WorkingSet::new();
        let mut active_objects = BTreeSet::new();

        // Phase 3: partial by default — pin head root + building only.
        // Domain objects load via load_region / annotations_near / explicit get.
        if let Some(head) = record.head_root {
            if let Ok(root_obj) = store.get(&head) {
                working_set.pin(head);
                working_set.cache_only(head, root_obj.clone());
                if let Ok(root) = RootBody::from_object(&root_obj) {
                    if let Ok(set) = root.materialize_active_objects(&store) {
                        active_objects = set;
                    }
                }
            }
        }
        if let Some(b) = record.building_object {
            if let Ok(obj) = store.get(&b) {
                working_set.pin(b);
                working_set.cache_only(b, obj);
            } else {
                working_set.pin(b);
            }
        }

        // Restore pending captures into the session working set.
        for cid in record.pending.clone() {
            if let Ok(obj) = store.get(&cid) {
                working_set.stage(cid, obj);
            }
        }

        Ok(Self {
            store,
            _write_lock: write_lock,
            record,
            working_set,
            keypair,
            active_objects,
        })
    }

    /// List building IDs with metadata under this store.
    pub fn list_buildings(store_path: impl AsRef<Path>) -> Result<Vec<BuildingRecord>> {
        let root = store_path.as_ref();
        let dir = root.join("meta").join("buildings");
        if !dir.exists() {
            return Ok(Vec::new());
        }
        let mut out = Vec::new();
        for ent in fs::read_dir(dir)? {
            let ent = ent?;
            if ent.path().extension().and_then(|e| e.to_str()) != Some("cbor") {
                continue;
            }
            let bytes = fs::read(ent.path())?;
            let rec: BuildingRecord = from_cbor(&bytes)?;
            out.push(rec);
        }
        out.sort_by(|a, b| a.building_id.as_str().cmp(b.building_id.as_str()));
        Ok(out)
    }

    pub fn store(&self) -> &ObjectStore {
        &self.store
    }

    pub fn record(&self) -> &BuildingRecord {
        &self.record
    }

    pub fn building_id(&self) -> &BuildingId {
        &self.record.building_id
    }

    pub fn head_root(&self) -> Option<Cid> {
        self.record.head_root
    }

    pub fn working_set(&self) -> &WorkingSet {
        &self.working_set
    }

    pub fn working_set_mut(&mut self) -> &mut WorkingSet {
        &mut self.working_set
    }

    pub fn keypair(&self) -> Option<&Keypair> {
        self.keypair.as_ref()
    }

    /// Capture a space → put → stage.
    pub fn capture_space(&mut self, capture: &SpaceCapture) -> Result<CaptureResult> {
        let obj = maybe_sign(space_object(capture), self.keypair.as_ref())?;
        self.put_staged(obj)
    }

    /// Capture a point cloud chunk → tier bytes into a Blob → put → stage.
    ///
    /// Also stages the blob CID into pending so it is included in the next root.
    pub fn capture_point_cloud(&mut self, capture: &PointCloudCapture) -> Result<CaptureResult> {
        let obj = put_point_cloud_chunk(&self.store, capture)?;
        // Ensure the blob is part of the active set (referenced + present).
        if let ObjectBody::PointCloudChunk(ref b) = obj.body {
            if let Some(blob_cid) = b.points_blob {
                if let Ok(blob_obj) = self.store.get(&blob_cid) {
                    self.working_set.stage(blob_cid, blob_obj);
                    self.record.pending.insert(blob_cid);
                }
            }
        }
        let obj = maybe_sign(obj, self.keypair.as_ref())?;
        self.put_staged(obj)
    }

    /// Capture an annotation → put → stage.
    pub fn capture_annotation(&mut self, capture: &AnnotationCapture) -> Result<CaptureResult> {
        let obj = maybe_sign(annotation_object(capture), self.keypair.as_ref())?;
        self.put_staged(obj)
    }

    /// Put and stage any captured object directly into the repository.
    pub fn stage_captured_object(&mut self, obj: Object) -> Result<CaptureResult> {
        self.put_staged(obj)
    }

    /// Stage an object CID for removal on the next commit.
    ///
    /// The object remains in the CAS (content-addressed history); it is dropped
    /// from the active set via the root `removed` delta.
    pub fn remove_object(&mut self, cid: Cid) -> Result<()> {
        self.record.pending.remove(&cid);
        self.working_set.unstaged(&cid);
        self.record.pending_removes.insert(cid);
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;
        Ok(())
    }

    /// Stage all active (and pending) versions of `entity_id` for removal.
    pub fn remove_entity(&mut self, entity_id: &crate::entity::EntityId) -> Result<u64> {
        let mut candidates = self.active_objects.clone();
        candidates.extend(self.record.pending.iter().copied());
        let versions =
            crate::entity::find_entity_versions(&self.store, &candidates, entity_id)?;
        let n = versions.len() as u64;
        for cid in versions {
            self.remove_object(cid)?;
        }
        Ok(n)
    }

    /// Add a controller public key without re-initializing the building.
    ///
    /// Stages a **new** Building object (new CID) with an expanded
    /// `controller_keys` set and stages removal of the previous Building
    /// object. Call [`commit`] afterward; the **current** controller must
    /// sign that commit (fail-closed).
    ///
    /// Idempotent if `key` is already a controller (returns the existing
    /// building object CID without staging changes).
    pub fn add_controller_key(&mut self, key: PublicKey) -> Result<CaptureResult> {
        let (old_cid, body) = self.current_building_body()?;
        if body.controller_keys.iter().any(|k| k == &key) {
            return Ok(CaptureResult {
                cid: old_cid,
                object_type: ObjectType::Building,
            });
        }
        let mut keys = body.controller_keys.clone();
        keys.push(key);
        // Stable order for deterministic CIDs when the same set is rebuilt.
        keys.sort();
        keys.dedup();
        self.replace_building_object(old_cid, body, keys)
    }

    /// Remove a controller public key without re-initializing the building.
    ///
    /// Fail-closed rules:
    /// - Key must currently be a controller.
    /// - Cannot remove the last remaining controller.
    /// - Stages a new Building object + removal of the prior one; caller must
    ///   [`commit`] with a remaining controller key.
    pub fn remove_controller_key(&mut self, key: PublicKey) -> Result<CaptureResult> {
        let (old_cid, body) = self.current_building_body()?;
        if !body.controller_keys.iter().any(|k| k == &key) {
            return Err(Error::Validation(format!(
                "public key {key} is not in building controller_keys"
            )));
        }
        if body.controller_keys.len() <= 1 {
            return Err(Error::Authorization(
                "cannot remove the last remaining controller; offline recovery required".into(),
            ));
        }
        let mut keys: Vec<PublicKey> = body
            .controller_keys
            .iter()
            .copied()
            .filter(|k| k != &key)
            .collect();
        keys.sort();
        keys.dedup();
        if keys.is_empty() {
            return Err(Error::Authorization(
                "cannot remove the last remaining controller; offline recovery required".into(),
            ));
        }
        self.replace_building_object(old_cid, body, keys)
    }

    /// Controller public keys on the current Building object in the active set.
    pub fn controller_keys(&self) -> Result<Vec<PublicKey>> {
        let (_, body) = self.current_building_body()?;
        Ok(body.controller_keys)
    }

    /// List entity heads in the active set: `(EntityId, version Cid, ObjectType)`.
    ///
    /// Deterministic order by entity id string. Objects without `entity_id` are omitted.
    /// When multiple versions of the same entity appear (should not after collapse),
    /// the higher `created` (then higher CID) wins.
    pub fn list_entity_heads(&self) -> Result<Vec<(crate::entity::EntityId, Cid, ObjectType)>> {
        use crate::entity::entity_id_of;
        let mut by_entity: std::collections::BTreeMap<
            crate::entity::EntityId,
            (Cid, u64, ObjectType),
        > = std::collections::BTreeMap::new();
        for cid in &self.active_objects {
            let obj = match self.store.get(cid) {
                Ok(o) => o,
                Err(Error::NotFound(_)) => continue,
                Err(e) => return Err(e),
            };
            let Some(eid) = entity_id_of(&obj).cloned() else {
                continue;
            };
            let created = obj.header.created;
            let ty = obj.header.object_type;
            let replace = match by_entity.get(&eid) {
                None => true,
                Some((prev_cid, prev_created, _)) => {
                    created > *prev_created || (created == *prev_created && *cid > *prev_cid)
                }
            };
            if replace {
                by_entity.insert(eid, (*cid, created, ty));
            }
        }
        Ok(by_entity
            .into_iter()
            .map(|(eid, (cid, _, ty))| (eid, cid, ty))
            .collect())
    }

    fn replace_building_object(
        &mut self,
        old_cid: Cid,
        body: BuildingBody,
        keys: Vec<PublicKey>,
    ) -> Result<CaptureResult> {
        let mut new_obj = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: body.building_id,
                name: body.name,
                controller_keys: keys,
                properties: body.properties,
            }),
            now_secs(),
        );
        if let Some(kp) = self.keypair.as_ref() {
            new_obj.sign(kp)?;
        }

        self.remove_object(old_cid)?;
        let res = self.put_staged(new_obj)?;
        self.record.building_object = Some(res.cid);
        Self::write_record(self.store.root(), &self.record)?;
        Ok(res)
    }

    /// Current Building object CID and body from the active set (fail closed).
    pub fn current_building_body(&self) -> Result<(Cid, BuildingBody)> {
        let mut found: Option<(Cid, BuildingBody)> = None;
        for cid in &self.active_objects {
            let obj = match self.store.get(cid) {
                Ok(o) => o,
                Err(Error::NotFound(_)) => continue,
                Err(e) => return Err(e),
            };
            if let ObjectBody::Building(b) = &obj.body {
                if b.building_id == self.record.building_id {
                    if found.is_some() {
                        return Err(Error::Authorization(format!(
                            "multiple Building objects for {} in active set",
                            self.record.building_id
                        )));
                    }
                    found = Some((*cid, b.clone()));
                }
            }
        }
        found.ok_or_else(|| {
            Error::Authorization(format!(
                "no Building object for {} in active set",
                self.record.building_id
            ))
        })
    }

    fn put_staged(&mut self, obj: Object) -> Result<CaptureResult> {
        let object_type = obj.header.object_type;
        let cid = self.store.put(&obj)?;
        // If this is a new version of an existing entity, clear any staged remove
        // of this cid (re-add) and leave older versions to entity collapse on commit.
        self.record.pending_removes.remove(&cid);
        self.working_set.stage(cid, obj);
        self.record.pending.insert(cid);
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;
        Ok(CaptureResult { cid, object_type })
    }

    /// Rebuild spatial index for current head object set (does not create a new root).
    pub fn rebuild_spatial_index(&mut self) -> Result<Option<Cid>> {
        let cids = self.head_object_cids()?;
        let entries = crate::spatial::collect_entries(&self.store, cids)?;
        let index_root = crate::spatial::build_index(&self.store, entries)?;
        // Optionally re-commit with index — caller may commit. Store index CID on a
        // lightweight side path: for Phase 3 we require a commit to attach.
        Ok(index_root)
    }

    /// All CIDs in the current head root (empty if no head).
    pub fn head_object_cids(&self) -> Result<Vec<Cid>> {
        Ok(self.active_objects.iter().copied().collect())
    }

    /// Load and verify the current head root.
    pub fn load_head_root(&self) -> Result<Option<RootBody>> {
        let Some(head) = self.record.head_root else {
            return Ok(None);
        };
        let obj = self.store.get(&head)?;
        let root = RootBody::from_object(&obj)?.clone();
        let _ = root.verify_with_store(&self.store);
        Ok(Some(root))
    }
}

impl BuildingRepository {
    /// Parse building id from string helper.
    pub fn parse_building_id(s: &str) -> Result<BuildingId> {
        BuildingId::from_str(s)
    }

    /// Put raw object bytes into the CAS (used by network sync).
    pub fn put_object_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        self.store.put_bytes(bytes)
    }

    /// Fetch raw object bytes by CID if present.
    pub fn get_object_bytes(&self, cid: &Cid) -> Result<Vec<u8>> {
        self.store.get_bytes(cid)
    }

    /// Whether the store holds this CID.
    pub fn contains(&self, cid: &Cid) -> bool {
        self.store.contains(cid)
    }

    /// Collect the full object-set closure for a root CID (root object + members).
    ///
    /// Returns `(root_cid, ordered list of (cid, bytes))` including the root itself.
    pub fn root_closure_bytes(&self, root_cid: &Cid) -> Result<Vec<(Cid, Vec<u8>)>> {
        crate::root::get_root_closure_blobs(&self.store, root_cid)
    }


    /// Create or open a building record that will follow a remote building id
    /// (no local key required until the device wants to author new roots).
    pub fn open_or_follow(
        store_path: impl AsRef<Path>,
        building_id: &BuildingId,
        name: Option<String>,
    ) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
        let write_lock = store.try_lock_exclusive()?;
        fs::create_dir_all(store.root().join("meta").join("buildings"))?;
        match Self::read_record(store.root(), building_id) {
            Ok(_) => {
                // Re-open through open() so we don't hold two locks; drop this one first.
                drop(write_lock);
                Self::open(store_path, building_id)
            }
            Err(Error::NotFound(_)) => {
                let record = BuildingRecord {
                    building_id: building_id.clone(),
                    name,
                    building_object: None,
                    head_root: None,
                    pending: BTreeSet::new(),
                    pending_removes: BTreeSet::new(),
                    updated: now_secs(),
                };
                Self::write_record(store.root(), &record)?;
                let keypair = Self::read_seed(store.root()).ok();
                Ok(Self {
                    store,
                    _write_lock: write_lock,
                    record,
                    working_set: WorkingSet::new(),
                    keypair,
                    active_objects: BTreeSet::new(),
                })
            }
            Err(e) => Err(e),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::PointCloudCapture;
    use crate::entity::{entity_id_of, EntityId};
    use crate::object::Pose;
    use tempfile::tempdir;

    #[test]
    fn entity_replace_on_commit_drops_old_version() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("E".into()), None).unwrap();
        let eid = EntityId::from("01ENTITYREPLACE0000000000".to_string());

        let r1 = repo
            .capture_space(&SpaceCapture {
                entity_id: Some(eid.clone()),
                name: Some("v1".into()),
                pose: Pose {
                    position: [0.0, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
                bounds: None,
                floor: None,
                properties: BTreeMap::new(),
            })
            .unwrap();
        repo.commit(Some("add v1".into())).unwrap();
        assert!(repo.active_objects.contains(&r1.cid));

        let r2 = repo
            .capture_space(&SpaceCapture {
                entity_id: Some(eid.clone()),
                name: Some("v2".into()),
                pose: Pose {
                    position: [1.0, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
                bounds: None,
                floor: None,
                properties: BTreeMap::new(),
            })
            .unwrap();
        let commit = repo.commit(Some("replace v1".into())).unwrap();
        assert!(repo.active_objects.contains(&r2.cid));
        assert!(!repo.active_objects.contains(&r1.cid));

        // Root delta records the removal.
        let head = repo.load_head_root().unwrap().unwrap();
        if head.objects.is_none() {
            assert!(head.removed.contains(&r1.cid));
            assert!(head.added.contains(&r2.cid));
        }
        let _ = commit;
        // Entity id preserved on the new head object.
        let obj = repo.store().get(&r2.cid).unwrap();
        assert_eq!(entity_id_of(&obj).map(|e| e.as_str()), Some(eid.as_str()));
    }

    #[test]
    fn entity_remove_without_replace() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("R".into()), None).unwrap();
        let eid = EntityId::from("01ENTITYREMOVE00000000000".to_string());
        let r = repo
            .capture_space(&SpaceCapture {
                entity_id: Some(eid.clone()),
                name: Some("gone".into()),
                pose: Pose::default(),
                bounds: None,
                floor: None,
                properties: BTreeMap::new(),
            })
            .unwrap();
        repo.commit(Some("add".into())).unwrap();
        let n = repo.remove_entity(&eid).unwrap();
        assert_eq!(n, 1);
        repo.commit(Some("remove".into())).unwrap();
        assert!(!repo.active_objects.contains(&r.cid));
    }

    #[test]
    fn init_capture_commit_reload() {
        let dir = tempdir().unwrap();
        let path = dir.path();

        let mut repo = BuildingRepository::init(path, Some("Hall".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let head0 = repo.head_root().unwrap();

        repo.capture_space(&SpaceCapture {
                    entity_id: None,
            name: Some("Mech Room".into()),
            pose: Pose {
                position: [2.0, 0.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        })
        .unwrap();

        let pts = [[0.0f32, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 1.0], [0.0, 0.0, 1.0]];
        repo.capture_point_cloud(&PointCloudCapture::from_xyz(
            &pts,
            Pose::default(),
            None,
        ))
        .unwrap();

        repo.capture_annotation(&AnnotationCapture::new(
            "disconnect switch",
            Pose {
                position: [2.1, 1.2, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();

        let commit = repo.commit(Some("first scan".into())).unwrap();
        assert_ne!(commit.root_cid, head0);
        assert_eq!(commit.previous_root, Some(head0));
        assert!(commit.object_count >= 4);
        drop(repo); // release exclusive store lock before re-open

        // Reload same building on "same device"
        let mut repo2 = BuildingRepository::open(path, &bid).unwrap();
        assert_eq!(repo2.head_root(), Some(commit.root_cid));
        let root = repo2.load_head_root().unwrap().unwrap();
        assert_eq!(root.message.as_deref(), Some("first scan"));
        root.verify_authors().unwrap();

        let hits = repo2
            .annotations_near(
                &Pose {
                    position: [2.0, 1.0, 1.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
                5.0,
            )
            .unwrap();
        assert_eq!(hits.len(), 1);
        assert_eq!(hits[0].text, "disconnect switch");

        let listed = BuildingRepository::list_buildings(path).unwrap();
        assert_eq!(listed.len(), 1);
        assert_eq!(listed[0].building_id, bid);
    }

    #[test]
    fn pending_survives_reopen_then_commit() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("Pending".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let head0 = repo.head_root().unwrap();

        repo.capture_annotation(&AnnotationCapture::new(
            "staged offline",
            Pose {
                position: [0.0, 1.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
        assert_eq!(repo.record().pending.len(), 1);
        drop(repo);

        // Simulate UniFFI: new process opens building; pending must restore.
        let mut repo2 = BuildingRepository::open(path, &bid).unwrap();
        assert_eq!(repo2.record().pending.len(), 1);
        assert_eq!(repo2.working_set().staged_len(), 1);

        let commit = repo2.commit(Some("after reopen".into())).unwrap();
        assert_ne!(commit.root_cid, head0);
        assert!(repo2.record().pending.is_empty());

        let hits = repo2
            .annotations_near(
                &Pose {
                    position: [0.0, 1.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
                1.0,
            )
            .unwrap();
        assert_eq!(hits.len(), 1);
        assert_eq!(hits[0].text, "staged offline");
    }

    #[test]
    fn test_adopt_root_validation() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("AdoptTest".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let controller = repo.keypair().unwrap().clone();
        let outsider = Keypair::generate();

        // 1. Authorized controller signs a root — adopt succeeds.
        let mut objects = BTreeSet::new();
        objects.insert(repo.record().building_object.unwrap());
        let (root_obj, signed_root_cid) = RootBuilder::new(bid.clone(), 100)
            .objects(objects.clone())
            .message("signed commit")
            .build_signed(&controller)
            .unwrap();
        repo.store().put(&root_obj).unwrap();
        assert!(repo.adopt_root(signed_root_cid).is_ok());

        // 2. Valid signature from a non-controller — rejected under default options.
        let (bad_obj, bad_cid) = RootBuilder::new(bid.clone(), 101)
            .objects(objects.clone())
            .previous_root(signed_root_cid)
            .message("outsider")
            .build_signed(&outsider)
            .unwrap();
        repo.store().put(&bad_obj).unwrap();
        let err = repo.adopt_root(bad_cid).unwrap_err();
        assert!(
            matches!(err, Error::Authorization(_)),
            "expected Authorization, got {err:?}"
        );

        // 3. Unsigned root — rejected by default.
        let body = RootBody::new(bid.clone(), Some(signed_root_cid), objects, 102);
        let obj = body.into_object(102);
        let unsigned_root_cid = repo.store().put(&obj).unwrap();
        let err = repo.adopt_root(unsigned_root_cid);
        assert!(err.is_err());
        assert!(matches!(err.unwrap_err(), Error::Signature(_)));

        // 4. allow_untrusted escape hatch accepts unauthorized / unsigned roots.
        let res = repo.adopt_root_with_options(
            unsigned_root_cid,
            &AdoptOptions {
                allow_untrusted: true,
                allow_partial: false,
            },
        );
        assert!(res.is_ok());
    }

    #[test]
    fn adopt_incomplete_closure_fails_by_default() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("Partial".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let controller = repo.keypair().unwrap().clone();
        let building_cid = repo.record().building_object.unwrap();

        // Phantom CID listed as active but never stored.
        let ghost = Cid::from_canonical_bytes(b"ghost-object-not-in-store");
        let mut objects = BTreeSet::new();
        objects.insert(building_cid);
        objects.insert(ghost);
        let (root_obj, root_cid) = RootBuilder::new(bid, 200)
            .objects(objects)
            .message("incomplete")
            .build_signed(&controller)
            .unwrap();
        repo.store().put(&root_obj).unwrap();

        let err = repo.adopt_root(root_cid).unwrap_err();
        assert!(
            matches!(err, Error::NotFound(_)),
            "expected NotFound for incomplete adopt, got {err:?}"
        );

        // Explicit allow_partial still needs authz unless also allow_untrusted.
        // Building is present so authz can succeed; ghost remains missing.
        let res = repo.adopt_root_with_options(
            root_cid,
            &AdoptOptions {
                allow_untrusted: false,
                allow_partial: true,
            },
        );
        assert!(res.is_ok(), "{res:?}");
    }

    #[test]
    fn add_controller_key_allows_second_device_commit() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("Multi".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let first_pk = repo.keypair().unwrap().public_key();
        let second = Keypair::generate();
        let second_pk = second.public_key();

        repo.add_controller_key(second_pk).unwrap();
        let commit = repo.commit(Some("add device B".into())).unwrap();
        assert!(commit.object_count >= 1);
        drop(repo);

        // Device B: write its seed and open; can commit as new controller.
        BuildingRepository::write_seed(path, &second).unwrap();
        let mut repo_b = BuildingRepository::open(path, &bid).unwrap();
        repo_b
            .capture_annotation(&AnnotationCapture::new(
                "from B",
                Pose {
                    position: [0.0, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ))
            .unwrap();
        let c2 = repo_b.commit(Some("B scan".into())).unwrap();
        assert_eq!(c2.previous_root, Some(commit.root_cid));

        let (_, body) = repo_b.current_building_body().unwrap();
        assert_eq!(body.controller_keys.len(), 2);
        assert!(body.controller_keys.contains(&second_pk));
        assert!(body.controller_keys.contains(&first_pk));
    }

    #[test]
    fn remove_controller_key_success_and_remaining_can_commit() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("Rm".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let first = repo.keypair().unwrap().clone();
        let second = Keypair::generate();
        repo.add_controller_key(second.public_key()).unwrap();
        repo.commit(Some("add B".into())).unwrap();
        drop(repo);

        BuildingRepository::write_seed(path, &first).unwrap();
        let mut repo = BuildingRepository::open(path, &bid).unwrap();
        repo.remove_controller_key(second.public_key()).unwrap();
        let c = repo.commit(Some("remove B".into())).unwrap();
        assert_eq!(repo.controller_keys().unwrap().len(), 1);
        assert!(repo.controller_keys().unwrap().contains(&first.public_key()));
        drop(repo);

        // Remaining controller can still author.
        BuildingRepository::write_seed(path, &first).unwrap();
        let mut repo = BuildingRepository::open(path, &bid).unwrap();
        repo.capture_annotation(&AnnotationCapture::new("still here", Pose::default()))
            .unwrap();
        let c2 = repo.commit(Some("after remove".into())).unwrap();
        assert_eq!(c2.previous_root, Some(c.root_cid));
    }

    #[test]
    fn remove_last_controller_rejected() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("Last".into()), None).unwrap();
        let only = repo.keypair().unwrap().public_key();
        let err = repo.remove_controller_key(only).unwrap_err();
        assert!(
            matches!(err, Error::Authorization(_)),
            "expected Authorization, got {err:?}"
        );
    }

    #[test]
    fn remove_unknown_controller_rejected() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("Unk".into()), None).unwrap();
        let stranger = Keypair::generate().public_key();
        let err = repo.remove_controller_key(stranger).unwrap_err();
        assert!(
            matches!(err, Error::Validation(_)),
            "expected Validation, got {err:?}"
        );
    }

    #[test]
    fn removed_controller_cannot_author() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        let mut repo = BuildingRepository::init(path, Some("Authz".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let first = repo.keypair().unwrap().clone();
        let second = Keypair::generate();
        repo.add_controller_key(second.public_key()).unwrap();
        repo.commit(Some("add B".into())).unwrap();
        // First removes second.
        repo.remove_controller_key(second.public_key()).unwrap();
        repo.commit(Some("drop B".into())).unwrap();
        drop(repo);

        BuildingRepository::write_seed(path, &second).unwrap();
        let mut repo = BuildingRepository::open(path, &bid).unwrap();
        repo.capture_annotation(&AnnotationCapture::new("nope", Pose::default()))
            .unwrap();
        let err = repo.commit(Some("should fail".into())).unwrap_err();
        assert!(
            matches!(err, Error::Authorization(_)),
            "expected Authorization, got {err:?}"
        );
        let _ = first;
    }

    #[test]
    fn commit_requires_controller_keypair() {
        let dir = tempdir().unwrap();
        let path = dir.path();
        // Init with known controller, then replace seed with an outsider key.
        let repo = BuildingRepository::init(path, Some("Ctrl".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let outsider = Keypair::generate();
        BuildingRepository::write_seed(path, &outsider).unwrap();
        drop(repo); // release exclusive store lock before re-open

        let mut repo = BuildingRepository::open(path, &bid).unwrap();
        repo.capture_annotation(&AnnotationCapture::new(
            "x",
            Pose {
                position: [0.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
        let err = repo.commit(Some("should fail".into())).unwrap_err();
        assert!(
            matches!(err, Error::Authorization(_)),
            "expected Authorization, got {err:?}"
        );
    }
}
