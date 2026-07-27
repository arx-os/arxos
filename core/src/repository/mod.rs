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

/// Building repository handle: CAS + head metadata + session working set.
pub struct BuildingRepository {
    store: ObjectStore,
    record: BuildingRecord,
    working_set: WorkingSet,
    keypair: Option<Keypair>,
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
        })
    }

    /// Open an existing building by ID (loads head metadata + optional seed).
    pub fn open(store_path: impl AsRef<Path>, building_id: &BuildingId) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
        let record = Self::read_record(store.root(), building_id)?;
        let keypair = Self::read_seed(store.root()).ok();
        let mut working_set = WorkingSet::new();

        // Materialize head root + its object set (partial: only annotations get
        // distance queries later; we load all root members for Phase 1 reload).
        if let Some(head) = record.head_root {
            let root_obj = store.get(&head)?;
            working_set.pin(head);
            working_set.cache_only(head, root_obj.clone());
            if let ObjectBody::Root(root) = &root_obj.body {
                for cid in &root.objects {
                    if let Ok(obj) = store.get(cid) {
                        working_set.pin(*cid);
                        working_set.cache_only(*cid, obj);
                    }
                }
            }
        }
        if let Some(b) = record.building_object {
            working_set.pin(b);
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
    pub fn commit(&mut self, message: Option<String>) -> Result<CommitResult> {
        let kp = self
            .keypair
            .as_ref()
            .ok_or_else(|| Error::Crypto("no device keypair loaded for signing".into()))?;

        let mut objects = BTreeSet::new();

        // Carry forward previous root object set if present.
        if let Some(prev) = self.record.head_root {
            let prev_obj = self.store.get(&prev)?;
            if let ObjectBody::Root(root) = prev_obj.body {
                objects.extend(root.objects);
            }
        }
        // Add staged + durable pending captures.
        objects.extend(self.working_set.staged().iter().copied());
        objects.extend(self.record.pending.iter().copied());

        if objects.is_empty() {
            return Err(Error::Validation(
                "cannot commit empty object set".into(),
            ));
        }

        let previous = self.record.head_root;
        let mut builder =
            RootBuilder::new(self.record.building_id.clone(), now_secs()).objects(objects.clone());
        if let Some(prev) = previous {
            builder = builder.previous_root(prev);
        }
        if let Some(msg) = message {
            builder = builder.message(msg);
        }
        let (root_obj, root_cid) = builder.build_signed(kp)?;
        self.store.put(&root_obj)?;

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
            object_count: objects.len() as u64,
            previous_root: previous,
        })
    }

    /// Annotations within radius of a pose (from current head object set).
    pub fn annotations_near(&mut self, origin: &Pose, radius_m: f64) -> Result<Vec<AnnotationHit>> {
        let candidates = self.head_object_cids()?;
        self.working_set
            .annotations_near(&self.store, origin, radius_m, candidates)
    }

    /// All CIDs in the current head root (empty if no head).
    pub fn head_object_cids(&self) -> Result<Vec<Cid>> {
        let Some(head) = self.record.head_root else {
            return Ok(Vec::new());
        };
        let obj = self.store.get(&head)?;
        match obj.body {
            ObjectBody::Root(root) => Ok(root.objects.into_iter().collect()),
            _ => Err(Error::Validation("head is not a root object".into())),
        }
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
}
