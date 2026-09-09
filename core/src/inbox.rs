//! Contributor inbox: pending Fact CIDs that are not yet official history.
//!
//! Path: `$STORE/meta/inbox/<building_id>.json`
//!
//! Push **ingests bytes into the CAS** and appends leaf CIDs here. It never
//! moves `head_root`. A controller [`BuildingRepository::inbox_apply`] stages
//! those CIDs and [`commit`]s; existing fuse runs. Meta keeps the CAS pure —
//! the pending list is not a CAS object and not a new Root type.
//!
//! Serve may read/write this file while holding `store.lock`. `inbox apply`
//! needs the exclusive repository lock, so it cannot run against the same
//! path while serve is up (TOCTOU if a reader races a writer).

use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::BuildingId;
use crate::store::atomic_write;

/// One pending Fact in the inbox.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InboxEntry {
    pub cid: String,
    #[serde(default)]
    pub author_hex: String,
    #[serde(default)]
    pub received_unix: u64,
}

/// On-disk inbox file (JSON).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InboxFile {
    pub building_id: String,
    #[serde(default)]
    pub pending: Vec<InboxEntry>,
}

impl InboxFile {
    pub fn new(building_id: &BuildingId) -> Self {
        Self {
            building_id: building_id.to_string(),
            pending: Vec::new(),
        }
    }

    pub fn cids(&self) -> Result<Vec<Cid>> {
        let mut out = Vec::new();
        for e in &self.pending {
            out.push(Cid::from_str_checked(&e.cid)?);
        }
        Ok(out)
    }
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// `$STORE/meta/inbox/<building_id>.json`
pub fn inbox_path(store_root: impl AsRef<Path>, building_id: &BuildingId) -> PathBuf {
    store_root
        .as_ref()
        .join("meta")
        .join("inbox")
        .join(format!("{building_id}.json"))
}

/// Load inbox; missing file is an empty inbox.
pub fn load_inbox(store_root: impl AsRef<Path>, building_id: &BuildingId) -> Result<InboxFile> {
    let path = inbox_path(store_root, building_id);
    if !path.exists() {
        return Ok(InboxFile::new(building_id));
    }
    let bytes = fs::read(&path)?;
    let file: InboxFile = serde_json::from_slice(&bytes)
        .map_err(|e| Error::Deserialization(format!("inbox json: {e}")))?;
    Ok(file)
}

/// Write inbox via temp + rename.
pub fn save_inbox(store_root: impl AsRef<Path>, file: &InboxFile) -> Result<()> {
    let bid = BuildingId::from(file.building_id.clone());
    let path = inbox_path(store_root, &bid);
    let bytes = serde_json::to_vec_pretty(file)
        .map_err(|e| Error::Serialization(format!("inbox json: {e}")))?;
    atomic_write(&path, &bytes)
}

/// Outcome of [`inbox_add`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InboxAdd {
    /// CID was not in the pending set; appended.
    Added,
    /// CID already listed; no change.
    Duplicate,
}

/// Append `cid` to the inbox (idempotent set keyed by CID).
pub fn inbox_add(
    store_root: impl AsRef<Path>,
    building_id: &BuildingId,
    cid: &Cid,
    author_hex: &str,
) -> Result<InboxAdd> {
    let root = store_root.as_ref();
    let mut file = load_inbox(root, building_id)?;
    let key = cid.to_string();
    if file.pending.iter().any(|e| e.cid == key) {
        return Ok(InboxAdd::Duplicate);
    }
    file.pending.push(InboxEntry {
        cid: key,
        author_hex: author_hex.to_string(),
        received_unix: now_secs(),
    });
    save_inbox(root, &file)?;
    Ok(InboxAdd::Added)
}

/// Remove CIDs from the inbox. Bytes in the CAS are left in place.
pub fn inbox_remove(
    store_root: impl AsRef<Path>,
    building_id: &BuildingId,
    cids: &BTreeSet<Cid>,
) -> Result<u64> {
    let root = store_root.as_ref();
    let mut file = load_inbox(root, building_id)?;
    let before = file.pending.len();
    let drop: BTreeSet<String> = cids.iter().map(|c| c.to_string()).collect();
    file.pending.retain(|e| !drop.contains(&e.cid));
    let n = (before - file.pending.len()) as u64;
    save_inbox(root, &file)?;
    Ok(n)
}

trait CidFromStr {
    fn from_str_checked(s: &str) -> Result<Cid>;
}

impl CidFromStr for Cid {
    fn from_str_checked(s: &str) -> Result<Cid> {
        use std::str::FromStr;
        Cid::from_str(s)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn add_is_idempotent() {
        let dir = tempdir().unwrap();
        let bid = BuildingId::new();
        let cid = Cid::from_canonical_bytes(b"hello-inbox");
        assert_eq!(
            inbox_add(dir.path(), &bid, &cid, "ed25519:ab").unwrap(),
            InboxAdd::Added
        );
        assert_eq!(
            inbox_add(dir.path(), &bid, &cid, "ed25519:cd").unwrap(),
            InboxAdd::Duplicate
        );
        let file = load_inbox(dir.path(), &bid).unwrap();
        assert_eq!(file.pending.len(), 1);
        assert_eq!(file.pending[0].author_hex, "ed25519:ab");
    }
}
