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

use std::collections::BTreeSet;
use std::fs;
use std::path::Path;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::canonical::from_cbor;
use crate::cid::Cid;
use crate::crypto::{Keypair, PublicKey};
use crate::error::{Error, Result};
use crate::object::{BuildingBody, BuildingId, Object, ObjectType};
use crate::root::RootBody;
use crate::store::{ObjectRead, ObjectStore, ObjectWrite};
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
    /// Adopt-only: [`crate::root::ContinuityOutcome`] from
    /// [`crate::root::verify_continuous_with_local`].
    ///
    /// - [`crate::root::ContinuityOutcome::FirstTrust`] — replica had no head (TOFU)
    /// - [`crate::root::ContinuityOutcome::FastForward`] — authors ∩ local keys and ancestry
    /// - `None` — local [`BuildingRepository::commit`], or `allow_untrusted` (continuity not claimed)
    pub continuity: Option<crate::root::ContinuityOutcome>,
}

/// Options for adopting a remote root.
///
/// Default is production pull: fail-closed self-consistency **and** replica
/// continuity. [`Self::allow_untrusted`] is an explicit disaster-recovery hatch
/// (not import, not the network default). [`Self::allow_partial`] cannot install
/// a head — adopt refuses it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct AdoptOptions {
    /// Skip Root-law and replica-continuity checks.
    ///
    /// If false (default), adopt requires [`crate::root::verify_continuous_with_local`].
    /// If true, unsigned / unauthorized / forked roots may still become head.
    /// This is not a warning: the head moves.
    pub allow_untrusted: bool,
    /// Historical flag. Adopt **rejects** `allow_partial = true`: an incomplete
    /// closure cannot become head. Metadata-only ingest must use `set_head = false`.
    pub allow_partial: bool,
    /// Exact `Building.controller_keys` required on first-contact TOFU.
    /// Empty (default) is classic TOFU. Ignored once this replica has a head.
    pub expected_controllers: Vec<crate::crypto::PublicKey>,
}

/// Building-scoped ingest of already-canonical objects (sync / import).
///
/// Does **not** stage into pending captures. The caller adopts or commits
/// afterwards. Presence checks use [`ObjectRead::has`].
pub trait ObjectIngest: ObjectRead {
    /// Store exact wire bytes (fail closed if non-canonical).
    fn ingest_canonical_bytes(&self, bytes: &[u8]) -> Result<Cid>;
}

/// Building repository handle: CAS + head metadata + session working set.
///
/// Write opens ([`Self::init`], [`Self::open`], [`Self::open_or_follow`]) hold
/// an exclusive [`crate::store::WriteGuard`] for the handle lifetime
/// (single-writer policy). [`Self::open_read`] takes no flock so score,
/// verify, and export can run while a writer is not (or even is) holding
/// the lock — see rustdoc on [`Self::open_read`] for consistency caveats.
pub struct BuildingRepository {
    store: ObjectStore,
    /// Exclusive store lock when this handle may write. `None` for
    /// [`Self::open_read`].
    _write_lock: Option<crate::store::WriteGuard>,
    /// Parent process already holds `store.lock` (serve-owned apply).
    assume_exclusive: bool,
    record: BuildingRecord,
    working_set: WorkingSet,
    keypair: Option<Keypair>,
    active_objects: BTreeSet<Cid>,
}

mod adopt;
mod capture;
mod commit;
mod inbox;
mod meta;
mod open;
mod query;

pub use inbox::{referenced_cids, reject_inbox_object, InboxApplyResult};

impl BuildingRepository {
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

    /// Load a typed object by CID (CID integrity check).
    pub fn get_object(&self, cid: &Cid) -> Result<Object> {
        self.store.get(cid)
    }

    /// True when opened with [`Self::open_read`] (no exclusive store lock).
    pub fn is_read_only(&self) -> bool {
        self._write_lock.is_none() && !self.assume_exclusive
    }

    fn require_write(&self) -> Result<()> {
        if self._write_lock.is_none() && !self.assume_exclusive {
            return Err(Error::Store(
                "read-only BuildingRepository (opened with open_read); use BuildingRepository::open for writes"
                    .into(),
            ));
        }
        Ok(())
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

    /// Replace the session signing key without writing `keys/device.seed`.
    pub fn set_keypair(&mut self, keypair: Keypair) {
        self.keypair = Some(keypair);
    }

    /// Rebuild spatial index for current head object set (does not create a new root).
    pub fn rebuild_spatial_index(&mut self) -> Result<Option<Cid>> {
        self.require_write()?;
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

    /// Ingest a typed object into the CAS (does not stage for commit).
    ///
    /// Use [`Self::stage_captured_object`] or capture methods for pending
    /// domain objects. Sync and import use this to place objects that a
    /// subsequent [`Self::adopt_root`] will reference.
    pub fn put_object(&self, obj: &Object) -> Result<Cid> {
        self.require_write()?;
        self.store.put(obj)
    }

    /// Ingest already-canonical object bytes (network sync / import).
    ///
    /// Does not stage. See [`ObjectIngest`].
    pub fn put_object_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        self.require_write()?;
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
}

impl ObjectRead for BuildingRepository {
    fn has(&self, cid: &Cid) -> bool {
        self.store.contains(cid)
    }

    fn get(&self, cid: &Cid) -> Result<Object> {
        ObjectStore::get(&self.store, cid)
    }

    fn get_bytes(&self, cid: &Cid) -> Result<Vec<u8>> {
        ObjectStore::get_bytes(&self.store, cid)
    }
}

impl ObjectWrite for BuildingRepository {
    fn put(&self, object: &Object) -> Result<Cid> {
        self.put_object(object)
    }

    fn put_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        self.put_object_bytes(bytes)
    }
}

impl ObjectIngest for BuildingRepository {
    fn ingest_canonical_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        self.put_object_bytes(bytes)
    }
}

#[cfg(test)]
mod tests;
