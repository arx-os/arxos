//! Local content-addressed object store (Git-style fan-out).

use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::path::{Path, PathBuf};

use fs2::FileExt;
use serde::{Deserialize, Serialize};

use crate::canonical::{from_cbor, to_canonical_cbor};
use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectType};

/// Hard cap on a single object's canonical CBOR size (4 MiB).
///
/// Dense point clouds must be chunked into multiple Blob objects rather than
/// packing unbounded bytes into one domain object.
pub const MAX_OBJECT_BYTES: u64 = 4 * 1024 * 1024;

/// Filename for the exclusive single-writer advisory lock.
pub const STORE_LOCK_FILE: &str = "store.lock";

/// Optional rebuildable thin index entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexEntry {
    pub object_type: ObjectType,
    pub schema_version: u32,
    pub size: u64,
}

/// RAII exclusive write lock on a store (`store.lock` via flock).
///
/// Dropping the guard releases the lock. Concurrent writers on the same path
/// fail with a clear store error.
#[derive(Debug)]
pub struct WriteGuard {
    _file: File,
}

/// Local CAS: objects stored as files named by CID under a fan-out directory.
///
/// Layout:
/// ```text
/// <root>/
///   objects/
///     ab/
///       cdef...   # remaining hex of CID
///   store.lock    # exclusive writer flock (see [`WriteGuard`])
///   index.cbor    # optional thin index (rebuildable; not updated on put)
/// ```
///
/// The thin `index.cbor` is **not** maintained on the put hot path. Call
/// [`ObjectStore::rebuild_index`] when an offline type/size catalog is needed.
///
/// Read-only opens (`open`) do not take the lock. Writers should call
/// [`try_lock_exclusive`] and hold the guard for the write session.
#[derive(Debug, Clone)]
pub struct ObjectStore {
    root: PathBuf,
}

impl ObjectStore {
    /// Open or create a store at `root` (no lock acquired).
    pub fn open(root: impl AsRef<Path>) -> Result<Self> {
        let root = root.as_ref().to_path_buf();
        fs::create_dir_all(root.join("objects"))?;
        Ok(Self { root })
    }

    /// Acquire an exclusive advisory lock on this store (non-blocking).
    ///
    /// Returns an error immediately if another process holds the lock.
    pub fn try_lock_exclusive(&self) -> Result<WriteGuard> {
        let path = self.root.join(STORE_LOCK_FILE);
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(&path)
            .map_err(|e| Error::Store(format!("open store lock: {e}")))?;
        file.try_lock_exclusive().map_err(|e| {
            Error::Store(format!(
                "store is locked by another process ({}): {e}",
                path.display()
            ))
        })?;
        Ok(WriteGuard { _file: file })
    }

    /// Acquire an exclusive advisory lock, blocking until available.
    pub fn lock_exclusive(&self) -> Result<WriteGuard> {
        let path = self.root.join(STORE_LOCK_FILE);
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(&path)
            .map_err(|e| Error::Store(format!("open store lock: {e}")))?;
        file.lock_exclusive()
            .map_err(|e| Error::Store(format!("store lock: {e}")))?;
        Ok(WriteGuard { _file: file })
    }

    pub fn root(&self) -> &Path {
        &self.root
    }

    fn object_path(&self, cid: &Cid) -> PathBuf {
        let hex = cid.to_hex();
        // Fan-out: first 2 hex chars → directory, rest → file.
        let (dir, file) = hex.split_at(2);
        self.root.join("objects").join(dir).join(file)
    }

    /// Put an object; returns its CID. Idempotent if content already present.
    ///
    /// Crash-safe on the same filesystem (temp file + rename). Does not update
    /// the optional thin index — use [`rebuild_index`] when needed.
    pub fn put(&self, object: &Object) -> Result<Cid> {
        object.validate()?;
        let bytes = object.to_canonical_bytes()?;
        self.put_canonical_bytes(&bytes)
    }

    /// Put already-canonical object bytes (network / import path).
    ///
    /// Fail closed for untrusted wire data:
    /// 1. Size limit
    /// 2. Decode + validate as an [`Object`]
    /// 3. Re-encode and require **exact** byte equality with the wire payload
    /// 4. Store the **wire** bytes under `BLAKE3(wire)` (no silent re-encode drift)
    ///
    /// Typed construction should use [`put`] instead.
    pub fn put_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        if bytes.len() as u64 > MAX_OBJECT_BYTES {
            return Err(Error::Validation(format!(
                "object exceeds max size {MAX_OBJECT_BYTES} bytes (got {})",
                bytes.len()
            )));
        }
        let object = Object::from_canonical_bytes(bytes)?;
        let reencoded = object.to_canonical_bytes()?;
        if reencoded.as_slice() != bytes {
            return Err(Error::Validation(
                "wire object bytes are not canonical (re-encode differs from input); refusing put"
                    .into(),
            ));
        }
        // Store exact wire bytes so CID on the wire matches the CAS path.
        self.put_canonical_bytes(bytes)
    }

    fn put_canonical_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        if bytes.len() as u64 > MAX_OBJECT_BYTES {
            return Err(Error::Validation(format!(
                "object exceeds max size {MAX_OBJECT_BYTES} bytes (got {})",
                bytes.len()
            )));
        }
        let cid = Cid::from_canonical_bytes(bytes);
        let path = self.object_path(&cid);
        if path.exists() {
            return Ok(cid);
        }
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        // Write temp then rename for atomicity on same filesystem.
        let tmp = path.with_extension("tmp");
        fs::write(&tmp, bytes)?;
        fs::rename(&tmp, &path)?;
        Ok(cid)
    }

    /// Get an object by CID.
    pub fn get(&self, cid: &Cid) -> Result<Object> {
        let path = self.object_path(cid);
        if !path.exists() {
            return Err(Error::NotFound(cid.to_string()));
        }
        let bytes = fs::read(&path)?;
        let object = Object::from_canonical_bytes(&bytes)?;
        // Integrity check: recompute CID.
        let actual = object.cid()?;
        if actual != *cid {
            return Err(Error::Store(format!(
                "CID mismatch: expected {cid}, got {actual}"
            )));
        }
        Ok(object)
    }

    /// True if the store contains this CID.
    pub fn contains(&self, cid: &Cid) -> bool {
        self.object_path(cid).exists()
    }

    /// Raw bytes for a CID.
    pub fn get_bytes(&self, cid: &Cid) -> Result<Vec<u8>> {
        let path = self.object_path(cid);
        if !path.exists() {
            return Err(Error::NotFound(cid.to_string()));
        }
        Ok(fs::read(path)?)
    }

    /// List all CIDs present in the store.
    pub fn list_cids(&self) -> Result<Vec<Cid>> {
        let mut out = Vec::new();
        let objects = self.root.join("objects");
        if !objects.exists() {
            return Ok(out);
        }
        for dir_ent in fs::read_dir(&objects)? {
            let dir_ent = dir_ent?;
            if !dir_ent.file_type()?.is_dir() {
                continue;
            }
            let prefix = dir_ent.file_name().to_string_lossy().to_string();
            if prefix.len() != 2 {
                continue;
            }
            for file_ent in fs::read_dir(dir_ent.path())? {
                let file_ent = file_ent?;
                if !file_ent.file_type()?.is_file() {
                    continue;
                }
                let name = file_ent.file_name().to_string_lossy().to_string();
                if name.ends_with(".tmp") {
                    continue;
                }
                let hex = format!("{prefix}{name}");
                if let Ok(cid) = hex.parse::<Cid>() {
                    out.push(cid);
                }
            }
        }
        out.sort();
        Ok(out)
    }

    fn index_path(&self) -> PathBuf {
        self.root.join("index.cbor")
    }

    fn load_index(&self) -> Result<BTreeMap<String, IndexEntry>> {
        let path = self.index_path();
        if !path.exists() {
            return Ok(BTreeMap::new());
        }
        let bytes = fs::read(path)?;
        from_cbor(&bytes)
    }

    fn save_index(&self, index: &BTreeMap<String, IndexEntry>) -> Result<()> {
        let bytes = to_canonical_cbor(index)?;
        let path = self.index_path();
        let tmp = path.with_extension("tmp");
        fs::write(&tmp, &bytes)?;
        fs::rename(tmp, path)?;
        Ok(())
    }

    /// Rebuild the optional thin index by scanning all objects.
    ///
    /// The index is not required for CAS correctness; it is a rebuildable
    /// catalog for tooling. Written atomically via temp + rename.
    pub fn rebuild_index(&self) -> Result<usize> {
        let mut index = BTreeMap::new();
        for cid in self.list_cids()? {
            let obj = self.get(&cid)?;
            let size = self.get_bytes(&cid)?.len() as u64;
            index.insert(
                cid.to_string(),
                IndexEntry {
                    object_type: obj.header.object_type,
                    schema_version: obj.header.schema_version,
                    size,
                },
            );
        }
        let n = index.len();
        self.save_index(&index)?;
        Ok(n)
    }

    /// Look up thin index entry if present (after [`rebuild_index`]).
    pub fn index_get(&self, cid: &Cid) -> Result<Option<IndexEntry>> {
        let index = self.load_index()?;
        Ok(index.get(&cid.to_string()).cloned())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::object::{BlobBody, ObjectBody};
    use std::collections::BTreeMap;
    use tempfile::tempdir;

    #[test]
    fn put_get_roundtrip() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();

        let obj = Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: Some("application/octet-stream".into()),
                data: vec![1, 2, 3, 4],
                properties: BTreeMap::new(),
            }),
            42,
        );
        let cid = store.put(&obj).unwrap();
        assert!(store.contains(&cid));

        let loaded = store.get(&cid).unwrap();
        assert_eq!(loaded.cid().unwrap(), cid);
        assert_eq!(loaded, obj);

        // Idempotent put
        let cid2 = store.put(&obj).unwrap();
        assert_eq!(cid, cid2);
    }

    #[test]
    fn missing_object() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let cid = Cid::from_canonical_bytes(b"nope");
        assert!(store.get(&cid).is_err());
    }

    #[test]
    fn put_rejects_oversized_object() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        // Slightly over the cap (header overhead means we need data near the limit).
        let data = vec![0u8; (MAX_OBJECT_BYTES as usize) + 1024];
        let obj = Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: None,
                data,
                properties: BTreeMap::new(),
            }),
            1,
        );
        let err = store.put(&obj).unwrap_err();
        assert!(
            matches!(err, Error::Validation(ref m) if m.contains("max size")),
            "{err:?}"
        );
    }

    #[test]
    fn put_does_not_write_index_file() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        for i in 0..20u8 {
            let obj = Object::new_with_created(
                ObjectBody::Blob(BlobBody {
                    content_type: None,
                    data: vec![i],
                    properties: BTreeMap::new(),
                }),
                i as u64,
            );
            store.put(&obj).unwrap();
        }
        assert!(
            !store.index_path().exists(),
            "put must not maintain index.cbor on the hot path"
        );
        let n = store.rebuild_index().unwrap();
        assert_eq!(n, 20);
        assert!(store.index_path().exists());
    }

    #[test]
    fn put_bytes_stores_exact_wire_bytes() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let obj = Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: Some("text/plain".into()),
                data: b"wire-exact".to_vec(),
                properties: BTreeMap::new(),
            }),
            99,
        );
        let wire = obj.to_canonical_bytes().unwrap();
        let cid = store.put_bytes(&wire).unwrap();
        assert_eq!(cid, Cid::from_canonical_bytes(&wire));
        assert_eq!(store.get_bytes(&cid).unwrap(), wire);
    }

    #[test]
    fn put_bytes_rejects_non_canonical_wire() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let obj = Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: None,
                data: b"x".to_vec(),
                properties: BTreeMap::new(),
            }),
            1,
        );
        let mut wire = obj.to_canonical_bytes().unwrap();
        // Corrupt trailing bytes while keeping a parseable prefix is hard for CBOR;
        // append garbage so decode fails OR if still decodes, re-encode differs.
        wire.push(0xff);
        let err = store.put_bytes(&wire).unwrap_err();
        assert!(
            matches!(
                err,
                Error::Deserialization(_) | Error::Validation(_) | Error::Schema(_)
            ),
            "{err:?}"
        );
    }
}
