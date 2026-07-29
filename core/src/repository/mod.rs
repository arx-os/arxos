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
use std::path::{Path, PathBuf};
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::capture::{
    annotation_object, maybe_sign, point_cloud_object, space_object, AnnotationCapture,
    PointCloudCapture, SpaceCapture,
};
use crate::canonical::{from_cbor, to_canonical_cbor};
use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::error::{Error, Result};
use crate::object::{BuildingBody, BuildingId, Object, ObjectBody, ObjectType, Pose};
use crate::root::{RootBody, RootBuilder};
use crate::store::ObjectStore;
use crate::working_set::{AnnotationHit, WorkingSet};

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
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct AdoptOptions {
    /// Allow untrusted root signatures (invalid or missing author signatures).
    /// If false, verification failures cause adoption to fail with a signature error.
    pub allow_untrusted: bool,
}

impl Default for AdoptOptions {
    fn default() -> Self {
        Self {
            allow_untrusted: false,
        }
    }
}

/// Building repository handle: CAS + head metadata + session working set.
pub struct BuildingRepository {
    store: ObjectStore,
    record: BuildingRecord,
    working_set: WorkingSet,
    keypair: Option<Keypair>,
    active_objects: BTreeSet<Cid>,
}

impl BuildingRepository {
    fn meta_path(store_root: &Path, building_id: &BuildingId) -> PathBuf {
        store_root
            .join("meta")
            .join("buildings")
            .join(format!("{building_id}.cbor"))
    }

    fn keys_path(store_root: &Path) -> PathBuf {
        store_root.join("keys").join("device.seed")
    }

    /// Initialize a new building repository in `store_path`.
    pub fn init(
        store_path: impl AsRef<Path>,
        name: Option<String>,
        keypair: Option<Keypair>,
    ) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
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
            record,
            working_set,
            keypair: Some(kp),
            active_objects,
        })
    }

    /// Open an existing building by ID (loads head metadata + optional seed).
    pub fn open(store_path: impl AsRef<Path>, building_id: &BuildingId) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
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

    /// Capture a point cloud chunk → put → stage.
    pub fn capture_point_cloud(&mut self, capture: &PointCloudCapture) -> Result<CaptureResult> {
        let obj = maybe_sign(point_cloud_object(capture), self.keypair.as_ref())?;
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

    fn put_staged(&mut self, obj: Object) -> Result<CaptureResult> {
        let object_type = obj.header.object_type;
        let cid = self.store.put(&obj)?;
        self.working_set.stage(cid, obj);
        self.record.pending.insert(cid);
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;
        Ok(CaptureResult { cid, object_type })
    }

    /// Commit staged (+ existing head set) to a new signed Root and advance head.
    ///
    /// Rebuilds the versioned spatial index and attaches it to the root.
    pub fn commit(&mut self, message: Option<String>) -> Result<CommitResult> {
        self.commit_with_options(message, true)
    }

    /// Commit with control over spatial index rebuild.
    pub fn commit_with_options(
        &mut self,
        message: Option<String>,
        rebuild_spatial: bool,
    ) -> Result<CommitResult> {
        let kp = self
            .keypair
            .as_ref()
            .ok_or_else(|| Error::Crypto("no device keypair loaded for signing".into()))?
            .clone();

        // 1. Calculate new active set in memory
        let mut new_active = self.active_objects.clone();
        let staged_and_pending: BTreeSet<Cid> = self.working_set.staged().iter().copied()
            .chain(self.record.pending.iter().copied())
            .collect();
        new_active.extend(staged_and_pending.clone());

        if new_active.is_empty() {
            return Err(Error::Validation(
                "cannot commit empty object set".into(),
            ));
        }

        let added: BTreeSet<Cid> = staged_and_pending.difference(&self.active_objects).copied().collect();
        let removed = BTreeSet::new(); // Currently no deletion API exists

        // 2. Walk backwards to calculate checkpoint distance
        let previous = self.record.head_root;
        let mut checkpoint_dist = 0;
        if let Some(prev) = previous {
            let mut current = Some(prev);
            let mut visited = BTreeSet::new();
            while let Some(cid) = current {
                if !visited.insert(cid) {
                    break;
                }
                if let Ok(obj) = self.store.get(&cid) {
                    if let Ok(root) = RootBody::from_object(&obj) {
                        if root.objects.is_some() {
                            break; // hit a checkpoint!
                        }
                        checkpoint_dist += 1;
                        current = root.previous_root;
                    } else {
                        break;
                    }
                } else {
                    break;
                }
            }
        }

        let is_checkpoint = previous.is_none() || checkpoint_dist >= 50;

        // 3. Spatial index update (incremental or full build)
        let spatial_index_root = if rebuild_spatial {
            let mut prev_si = None;
            if let Some(prev_cid) = previous {
                if let Ok(prev_obj) = self.store.get(&prev_cid) {
                    if let Ok(prev_root) = RootBody::from_object(&prev_obj) {
                        prev_si = prev_root.spatial_index_root;
                    }
                }
            }
            if let Some(si) = prev_si {
                let new_entries = crate::spatial::collect_entries(&self.store, added.iter().copied())?;
                crate::spatial::insert_incremental(&self.store, Some(si), new_entries)?
            } else {
                let entries = crate::spatial::collect_entries(&self.store, new_active.iter().copied())?;
                crate::spatial::build_index(&self.store, entries)?
            }
        } else {
            None
        };

        // 4. Construct Root using Builder
        let mut builder = RootBuilder::new(self.record.building_id.clone(), now_secs());
        if is_checkpoint {
            builder = builder.objects(new_active.clone());
        } else {
            builder = builder.added(added).removed(removed);
        }

        if let Some(prev) = previous {
            builder = builder.previous_root(prev);
        }
        if let Some(si) = spatial_index_root {
            builder = builder.spatial_index(si);
        }
        if let Some(msg) = message {
            builder = builder.message(msg);
        }

        let (root_obj, root_cid) = builder.build_signed(&kp)?;
        self.store.put(&root_obj)?;

        // Update state
        self.active_objects = new_active;
        self.record.head_root = Some(root_cid);
        self.record.pending.clear();
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;

        self.working_set.clear_staged();
        self.working_set.pin(root_cid);
        self.working_set.cache_only(root_cid, root_obj);

        Ok(CommitResult {
            root_cid,
            building_id: self.record.building_id.clone(),
            object_count: self.active_objects.len() as u64,
            previous_root: previous,
        })
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

    /// Query objects intersecting a volume using the head's spatial index when present.
    pub fn query_volume(
        &self,
        volume: &crate::spatial::QueryVolume,
    ) -> Result<Vec<crate::spatial::SpatialHit>> {
        let Some(head) = self.record.head_root else {
            return Ok(Vec::new());
        };
        let root_obj = self.store.get(&head)?;
        let root = RootBody::from_object(&root_obj)?;
        if let Some(si) = root.spatial_index_root {
            return crate::spatial::query_index_refined(&self.store, &si, volume);
        }
        // Fallback: linear scan of head objects.
        let mut hits = Vec::new();
        for cid in &self.active_objects {
            let obj = match self.store.get(cid) {
                Ok(o) => o,
                Err(Error::NotFound(_)) => continue,
                Err(e) => return Err(e),
            };
            if let Some(entry) = crate::spatial::entry_from_object(*cid, &obj) {
                if entry.bounds.intersects(&volume.bounds) {
                    hits.push(crate::spatial::SpatialHit {
                        object: *cid,
                        bounds: Some(entry.bounds),
                    });
                }
            }
        }
        Ok(hits)
    }

    /// Partial materialization: load objects in `volume` into the working set.
    ///
    /// Returns number of newly materialized objects. Respects `limit` (0 = unlimited).
    pub fn load_region(
        &mut self,
        volume: &crate::spatial::QueryVolume,
        limit: usize,
    ) -> Result<usize> {
        let hits = self.query_volume(volume)?;
        let mut loaded = 0usize;
        for hit in hits {
            if limit > 0 && loaded >= limit {
                break;
            }
            if self.working_set.get_cached(&hit.object).is_some() {
                continue;
            }
            self.working_set.materialize(&self.store, &hit.object)?;
            loaded += 1;
        }
        Ok(loaded)
    }

    /// Load objects associated with a floor (by floor object CID or elevation slab).
    pub fn load_floor(&mut self, floor_cid: &Cid, limit: usize) -> Result<usize> {
        // Prefer explicit floor links; also slab from Floor body.
        let floor_obj = self.store.get(floor_cid)?;
        let volume = if let ObjectBody::Floor(f) = &floor_obj.body {
            crate::spatial::QueryVolume {
                bounds: crate::object::Aabb {
                    min: [-1.0e6, f.elevation_m - 1.5, -1.0e6],
                    max: [1.0e6, f.elevation_m + 1.5, 1.0e6],
                },
            }
        } else {
            crate::spatial::QueryVolume {
                bounds: crate::object::Aabb::from_min_max(
                    [-1.0e6, -1.0e6, -1.0e6],
                    [1.0e6, 1.0e6, 1.0e6],
                ),
            }
        };
        let hits = self.query_volume(&volume)?;
        let mut loaded = 0usize;
        // Always pin the floor object.
        self.working_set.materialize(&self.store, floor_cid)?;
        for hit in hits {
            if limit > 0 && loaded >= limit {
                break;
            }
            // Prefer objects that reference this floor when available.
            if let Ok(obj) = self.store.get(&hit.object) {
                if let Some(entry) = crate::spatial::entry_from_object(hit.object, &obj) {
                    if entry.floor.as_ref() == Some(floor_cid)
                        || entry.bounds.intersects(&volume.bounds)
                    {
                        if self.working_set.get_cached(&hit.object).is_none() {
                            self.working_set.materialize(&self.store, &hit.object)?;
                            loaded += 1;
                        }
                    }
                }
            }
        }
        Ok(loaded)
    }

    /// Merge another root into this repository (same building_id), adopt result as head.
    pub fn merge_root(
        &mut self,
        other_root: Cid,
        message: Option<String>,
    ) -> Result<crate::merge::MergeResult> {
        let kp = self
            .keypair
            .as_ref()
            .ok_or_else(|| Error::Crypto("no device keypair for merge signing".into()))?
            .clone();
        let head = self
            .record
            .head_root
            .ok_or_else(|| Error::Validation("no local head to merge into".into()))?;
        let result =
            crate::merge::merge_roots(&self.store, head, other_root, &kp, message, true)?;
        self.adopt_root(result.root_cid)?;
        Ok(result)
    }

    /// Annotations within radius of a pose.
    ///
    /// Uses the spatial index when present (partial candidate set); otherwise
    /// falls back to the full head object list.
    pub fn annotations_near(&mut self, origin: &Pose, radius_m: f64) -> Result<Vec<AnnotationHit>> {
        let volume = crate::spatial::volume_around_pose(origin, radius_m);
        let candidates: Vec<Cid> = match self.query_volume(&volume) {
            Ok(hits) if !hits.is_empty() => hits.into_iter().map(|h| h.object).collect(),
            _ => self.head_object_cids()?,
        };
        self.working_set
            .annotations_near(&self.store, origin, radius_m, candidates)
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
        let _ = root.verify_authors();
        Ok(Some(root))
    }

    fn write_record(store_root: &Path, record: &BuildingRecord) -> Result<()> {
        let path = Self::meta_path(store_root, &record.building_id);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        let bytes = to_canonical_cbor(record)?;
        let tmp = path.with_extension("tmp");
        fs::write(&tmp, &bytes)?;
        fs::rename(tmp, path)?;
        Ok(())
    }

    fn read_record(store_root: &Path, building_id: &BuildingId) -> Result<BuildingRecord> {
        let path = Self::meta_path(store_root, building_id);
        if !path.exists() {
            return Err(Error::NotFound(format!(
                "building record {building_id}"
            )));
        }
        let bytes = fs::read(path)?;
        from_cbor(&bytes)
    }

    fn write_seed(store_root: &Path, kp: &Keypair) -> Result<()> {
        let path = Self::keys_path(store_root);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        // Restrictive permissions where supported.
        fs::write(&path, kp.seed())?;
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let _ = fs::set_permissions(&path, fs::Permissions::from_mode(0o600));
        }
        Ok(())
    }

    fn read_seed(store_root: &Path) -> Result<Keypair> {
        let path = Self::keys_path(store_root);
        let bytes = fs::read(path).map_err(|e| Error::Crypto(format!("read seed: {e}")))?;
        if bytes.len() != 32 {
            return Err(Error::Crypto(format!(
                "seed must be 32 bytes, got {}",
                bytes.len()
            )));
        }
        let mut seed = [0u8; 32];
        seed.copy_from_slice(&bytes);
        Ok(Keypair::from_seed(seed))
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


    /// Adopt a remote root as this building's head (after objects are in the CAS).
    ///
    /// Fail closed by default if the root authors' signatures are missing or invalid.
    pub fn adopt_root(&mut self, root_cid: Cid) -> Result<CommitResult> {
        self.adopt_root_with_options(root_cid, &AdoptOptions::default())
    }

    /// Adopt a remote root with explicit control over signature validation.
    pub fn adopt_root_with_options(
        &mut self,
        root_cid: Cid,
        opts: &AdoptOptions,
    ) -> Result<CommitResult> {
        let obj = self.store.get(&root_cid)?;
        let root = RootBody::from_object(&obj)?.clone();
        if root.building_id != self.record.building_id {
            return Err(Error::Validation(format!(
                "root building_id {} does not match repository {}",
                root.building_id, self.record.building_id
            )));
        }

        if !opts.allow_untrusted {
            root.verify_authors().map_err(|e| {
                Error::Signature(format!("root author verification failed: {e}"))
            })?;
        } else {
            let _ = root.verify_authors();
        }

        let active_set = root.materialize_active_objects(&self.store)?;
        let object_count = active_set.len() as u64;

        let previous = self.record.head_root;
        self.active_objects = active_set;
        self.record.head_root = Some(root_cid);
        self.record.pending.clear();
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;

        self.working_set.clear_staged();
        self.working_set.pin(root_cid);
        self.working_set.cache_only(root_cid, obj);
        // Do not eagerly materialize the full object set (partial by default).

        Ok(CommitResult {
            root_cid,
            building_id: self.record.building_id.clone(),
            object_count,
            previous_root: previous,
        })
    }

    /// Create or open a building record that will follow a remote building id
    /// (no local key required until the device wants to author new roots).
    pub fn open_or_follow(
        store_path: impl AsRef<Path>,
        building_id: &BuildingId,
        name: Option<String>,
    ) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
        fs::create_dir_all(store.root().join("meta").join("buildings"))?;
        match Self::read_record(store.root(), building_id) {
            Ok(_) => Self::open(store_path, building_id),
            Err(Error::NotFound(_)) => {
                let record = BuildingRecord {
                    building_id: building_id.clone(),
                    name,
                    building_object: None,
                    head_root: None,
                    pending: BTreeSet::new(),
                    updated: now_secs(),
                };
                Self::write_record(store.root(), &record)?;
                let keypair = Self::read_seed(store.root()).ok();
                Ok(Self {
                    store,
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
    use crate::object::Pose;
    use tempfile::tempdir;

    #[test]
    fn init_capture_commit_reload() {
        let dir = tempdir().unwrap();
        let path = dir.path();

        let mut repo = BuildingRepository::init(path, Some("Hall".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let head0 = repo.head_root().unwrap();

        repo.capture_space(&SpaceCapture {
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
        let kp = Keypair::generate();

        // 1. Create a correctly signed root for this building
        let mut objects = BTreeSet::new();
        objects.insert(repo.record().building_object.unwrap());
        let (root_obj, signed_root_cid) = RootBuilder::new(bid.clone(), 100)
            .objects(objects.clone())
            .message("signed commit")
            .build_signed(&kp)
            .unwrap();
        repo.store().put(&root_obj).unwrap();

        // Adopting correctly signed root must succeed
        assert!(repo.adopt_root(signed_root_cid).is_ok());

        // 2. Create an unsigned root for this building
        let body = RootBody::new(bid.clone(), Some(signed_root_cid), objects, 101);
        let obj = body.into_object(101);
        let unsigned_root_cid = repo.store().put(&obj).unwrap();

        // Adopting unsigned root must fail by default
        let err = repo.adopt_root(unsigned_root_cid);
        assert!(err.is_err());
        assert!(matches!(err.unwrap_err(), Error::Signature(_)));

        // 3. Adopting unsigned root with allow_untrusted = true must succeed
        let res = repo.adopt_root_with_options(unsigned_root_cid, &AdoptOptions { allow_untrusted: true });
        assert!(res.is_ok());
    }
}
