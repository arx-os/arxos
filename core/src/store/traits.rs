//! Narrow CAS traits over [`super::ObjectStore`].
//!
//! These traits freeze the content-addressed get/put surface so later PRs can
//! retarget callers without changing the filesystem implementation. Inherent
//! methods on [`super::ObjectStore`] remain the source of behavior.

use crate::cid::Cid;
use crate::error::Result;
use crate::object::Object;

use super::ObjectStore;

/// Read-only content-addressed access.
///
/// No locks, paths, or catalog operations. Implementors must be usable from
/// `&self` across threads (`Send + Sync`).
pub trait ObjectRead: Send + Sync {
    /// True if this CID is present.
    ///
    /// Preferred name for presence checks; the filesystem store forwards this
    /// to [`ObjectStore::contains`].
    fn has(&self, cid: &Cid) -> bool;

    /// Load an object by CID, decoding it and checking CID integrity.
    ///
    /// Returns [`crate::error::Error::NotFound`] if the CID is absent.
    fn get(&self, cid: &Cid) -> Result<Object>;

    /// Exact stored bytes for a CID (sync / closure paths).
    ///
    /// Unlike [`ObjectRead::get`], this does not decode or re-verify the CID.
    /// Returns [`crate::error::Error::NotFound`] if the CID is absent.
    fn get_bytes(&self, cid: &Cid) -> Result<Vec<u8>>;
}

/// Write side of the CAS. Still `&self`: durability is the backend's job.
pub trait ObjectWrite: ObjectRead {
    /// Validate, canonicalize, and store `object`. Idempotent if the CID is
    /// already present. Returns the object's CID.
    fn put(&self, object: &Object) -> Result<Cid>;

    /// Store **already-canonical** wire bytes.
    ///
    /// Fail closed if the payload is oversize or if a re-encode differs from
    /// the input (no silent canonicalization drift). Idempotent if present.
    fn put_bytes(&self, bytes: &[u8]) -> Result<Cid>;
}

impl ObjectRead for ObjectStore {
    fn has(&self, cid: &Cid) -> bool {
        self.contains(cid)
    }

    fn get(&self, cid: &Cid) -> Result<Object> {
        ObjectStore::get(self, cid)
    }

    fn get_bytes(&self, cid: &Cid) -> Result<Vec<u8>> {
        ObjectStore::get_bytes(self, cid)
    }
}

impl ObjectWrite for ObjectStore {
    fn put(&self, object: &Object) -> Result<Cid> {
        ObjectStore::put(self, object)
    }

    fn put_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        ObjectStore::put_bytes(self, bytes)
    }
}
