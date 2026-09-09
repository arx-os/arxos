//! Open / init / follow for [`super::BuildingRepository`].

use super::*;
use crate::object::{BuildingBody, Object, ObjectBody};
use crate::root::{RootBody, RootBuilder};
use crate::store::ObjectStore;
use crate::working_set::WorkingSet;
use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

impl BuildingRepository {
    /// Initialize a new building repository in `store_path`.
    ///
    /// Writes `keys/device.seed`. For in-memory / Keychain identity, use
    /// [`Self::init_ephemeral`].
    pub fn init(
        store_path: impl AsRef<Path>,
        name: Option<String>,
        keypair: Option<Keypair>,
    ) -> Result<Self> {
        Self::init_inner(store_path, name, keypair, true)
    }

    /// Initialize a building using `keypair` without writing `keys/device.seed`.
    pub fn init_ephemeral(
        store_path: impl AsRef<Path>,
        name: Option<String>,
        keypair: Keypair,
    ) -> Result<Self> {
        Self::init_inner(store_path, name, Some(keypair), false)
    }

    fn init_inner(
        store_path: impl AsRef<Path>,
        name: Option<String>,
        keypair: Option<Keypair>,
        persist_seed: bool,
    ) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
        let write_lock = store.try_lock_exclusive()?;
        fs::create_dir_all(store.root().join("meta").join("buildings"))?;
        fs::create_dir_all(store.root().join("keys"))?;

        let building_id = BuildingId::new();
        let kp = keypair.unwrap_or_else(Keypair::generate);
        if persist_seed {
            Self::write_seed(store.root(), &kp)?;
        }

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
            _write_lock: Some(write_lock),
            assume_exclusive: false,
            record,
            working_set,
            keypair: Some(kp),
            active_objects,
        })
    }

    /// Open an existing building by ID for mutation (exclusive store lock).
    ///
    /// Fails immediately if another process holds [`crate::store::WriteGuard`].
    /// For score / verify / export, use [`Self::open_read`].
    pub fn open(store_path: impl AsRef<Path>, building_id: &BuildingId) -> Result<Self> {
        Self::open_with_lock(store_path, building_id, true, false)
    }

    /// Open for writes **without** taking `store.lock`.
    ///
    /// The caller must already hold the exclusive flock (serve process). A
    /// second [`Self::open`] from another process still fails closed.
    pub fn open_assuming_exclusive(
        store_path: impl AsRef<Path>,
        building_id: &BuildingId,
    ) -> Result<Self> {
        Self::open_with_lock(store_path, building_id, false, true)
    }

    /// Open an existing building for read-only use (no flock).
    ///
    /// Concurrent [`Self::open_read`] handles are allowed. An exclusive writer
    /// ([`Self::open`]) is **not** blocked by readers, and readers are **not**
    /// blocked by a writer. Object files and head metadata are written
    /// atomically (temp + rename), so a reader sees a consistent object or
    /// a consistent `BuildingRecord`, but the pair can be slightly stale if
    /// a commit races the read (TOCTOU on the head pointer).
    ///
    /// Mutating methods return [`Error::Store`] on this handle.
    pub fn open_read(store_path: impl AsRef<Path>, building_id: &BuildingId) -> Result<Self> {
        Self::open_with_lock(store_path, building_id, false, false)
    }

    fn open_with_lock(
        store_path: impl AsRef<Path>,
        building_id: &BuildingId,
        exclusive: bool,
        assume_exclusive: bool,
    ) -> Result<Self> {
        let store = ObjectStore::open(store_path.as_ref())?;
        let write_lock = if exclusive {
            Some(store.try_lock_exclusive()?)
        } else {
            None
        };
        let record = Self::read_record(store.root(), building_id)?;
        let keypair = Self::read_seed(store.root()).ok();
        let mut working_set = WorkingSet::new();
        let mut active_objects = BTreeSet::new();

        // Partial by default — pin head root + building only.
        // Domain objects load via load_region / annotations_near / explicit get.
        // Fail closed if head exists but materialization fails (e.g. missing checkpoint).
        if let Some(head) = record.head_root {
            let root_obj = store.get(&head)?;
            working_set.pin(head);
            working_set.cache_only(head, root_obj.clone());
            let root = RootBody::from_object(&root_obj)?;
            active_objects = root.materialize_active_objects(&store)?;
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
            assume_exclusive,
            record,
            working_set,
            keypair,
            active_objects,
        })
    }
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
                    _write_lock: Some(write_lock),
                    assume_exclusive: false,
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
