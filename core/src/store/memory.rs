//! In-memory content-addressed store (`ObjectRead` + `ObjectWrite`).
//!
//! Same CAS contract as [`super::ObjectStore`] for get/put, without paths,
//! locks, or the optional thin index.

use std::collections::BTreeMap;
use std::sync::RwLock;

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::Object;

use super::{ObjectRead, ObjectWrite, MAX_OBJECT_BYTES};

/// Pure in-memory CAS. Suitable for unit tests and as a second backend for
/// anything bounded on [`ObjectRead`] / [`ObjectWrite`].
#[derive(Debug)]
pub struct MemObjectStore {
    objects: RwLock<BTreeMap<Cid, Vec<u8>>>,
}

impl Default for MemObjectStore {
    fn default() -> Self {
        Self::new()
    }
}

impl MemObjectStore {
    pub fn new() -> Self {
        Self {
            objects: RwLock::new(BTreeMap::new()),
        }
    }

    fn write_map(&self) -> std::sync::RwLockWriteGuard<'_, BTreeMap<Cid, Vec<u8>>> {
        self.objects.write().unwrap_or_else(|e| e.into_inner())
    }

    fn read_map(&self) -> std::sync::RwLockReadGuard<'_, BTreeMap<Cid, Vec<u8>>> {
        self.objects.read().unwrap_or_else(|e| e.into_inner())
    }

    fn put_canonical_bytes(&self, bytes: &[u8]) -> Result<Cid> {
        if bytes.len() as u64 > MAX_OBJECT_BYTES {
            return Err(Error::Validation(format!(
                "object exceeds max size {MAX_OBJECT_BYTES} bytes (got {})",
                bytes.len()
            )));
        }
        let cid = Cid::from_canonical_bytes(bytes);
        let mut map = self.write_map();
        map.entry(cid).or_insert_with(|| bytes.to_vec());
        Ok(cid)
    }
}

impl ObjectRead for MemObjectStore {
    fn has(&self, cid: &Cid) -> bool {
        self.read_map().contains_key(cid)
    }

    fn get(&self, cid: &Cid) -> Result<Object> {
        let bytes = self.get_bytes(cid)?;
        let object = Object::from_canonical_bytes(&bytes)?;
        let actual = object.cid()?;
        if actual != *cid {
            return Err(Error::Store(format!(
                "CID mismatch: expected {cid}, got {actual}"
            )));
        }
        Ok(object)
    }

    fn get_bytes(&self, cid: &Cid) -> Result<Vec<u8>> {
        self.read_map()
            .get(cid)
            .cloned()
            .ok_or_else(|| Error::NotFound(cid.to_string()))
    }
}

impl ObjectWrite for MemObjectStore {
    fn put(&self, object: &Object) -> Result<Cid> {
        object.validate()?;
        let bytes = object.to_canonical_bytes()?;
        self.put_canonical_bytes(&bytes)
    }

    fn put_bytes(&self, bytes: &[u8]) -> Result<Cid> {
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
        self.put_canonical_bytes(bytes)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::object::{BlobBody, ObjectBody, ObjectType};
    use crate::store::ObjectRead;
    use std::collections::BTreeMap;

    fn blob(data: Vec<u8>, created: u64) -> Object {
        Object::new_with_created(
            ObjectBody::Blob(BlobBody {
                content_type: Some("application/octet-stream".into()),
                data,
                properties: BTreeMap::new(),
            }),
            created,
        )
    }

    fn accepts_read<R: ObjectRead + ?Sized>(store: &R, cid: &Cid) -> bool {
        store.has(cid)
    }

    fn accepts_write<W: ObjectWrite + ?Sized>(store: &W, object: &Object) -> Cid {
        store.put(object).unwrap()
    }

    #[test]
    fn object_read_bound_accepts_mem_store() {
        let store = MemObjectStore::new();
        let obj = blob(vec![9, 8, 7], 1);
        let cid = accepts_write(&store, &obj);
        assert!(accepts_read(&store, &cid));
        let via_read: &dyn ObjectRead = &store;
        assert_eq!(via_read.get(&cid).unwrap(), obj);
        assert_eq!(
            via_read.get_bytes(&cid).unwrap(),
            obj.to_canonical_bytes().unwrap()
        );
        let via_write: &dyn ObjectWrite = &store;
        assert_eq!(via_write.put(&obj).unwrap(), cid);
    }

    #[test]
    fn put_get_roundtrip_idempotent() {
        let store = MemObjectStore::new();
        let obj = blob(vec![1, 2, 3, 4], 42);
        let cid = store.put(&obj).unwrap();
        assert!(store.has(&cid));
        let loaded = store.get(&cid).unwrap();
        assert_eq!(loaded.cid().unwrap(), cid);
        assert_eq!(loaded, obj);
        let cid2 = store.put(&obj).unwrap();
        assert_eq!(cid, cid2);
    }

    #[test]
    fn put_bytes_stores_exact_wire_and_is_idempotent() {
        let store = MemObjectStore::new();
        let obj = blob(b"wire-exact".to_vec(), 99);
        let wire = obj.to_canonical_bytes().unwrap();
        let cid = store.put_bytes(&wire).unwrap();
        assert_eq!(cid, Cid::from_canonical_bytes(&wire));
        assert_eq!(store.get_bytes(&cid).unwrap(), wire);
        assert_eq!(store.put_bytes(&wire).unwrap(), cid);
    }

    #[test]
    fn missing_cid_is_not_found() {
        let store = MemObjectStore::new();
        let cid = Cid::from_canonical_bytes(b"nope");
        assert!(!store.has(&cid));
        assert!(matches!(store.get(&cid), Err(Error::NotFound(_))));
        assert!(matches!(store.get_bytes(&cid), Err(Error::NotFound(_))));
    }

    #[test]
    fn put_rejects_oversized_object() {
        let store = MemObjectStore::new();
        let data = vec![0u8; (MAX_OBJECT_BYTES as usize) + 1024];
        let obj = blob(data, 1);
        let err = store.put(&obj).unwrap_err();
        assert!(
            matches!(err, Error::Validation(ref m) if m.contains("max size")),
            "{err:?}"
        );
    }

    #[test]
    fn put_bytes_rejects_non_canonical_wire() {
        let store = MemObjectStore::new();
        let obj = blob(b"x".to_vec(), 1);
        let mut wire = obj.to_canonical_bytes().unwrap();
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

    #[test]
    fn put_bytes_rejects_non_canonical_signed_zero() {
        let store = MemObjectStore::new();
        let obj = Object {
            header: crate::object::ObjectHeader {
                object_type: ObjectType::Annotation,
                schema_version: crate::object::SCHEMA_VERSION,
                created: 1,
                author: None,
                signature: None,
            },
            body: ObjectBody::Annotation(crate::object::AnnotationBody {
                text: Some("neg-zero".into()),
                transcript: None,
                media_ref: None,
                pose: Some(crate::object::Pose {
                    position: [-0.0, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                }),
                space: None,
                properties: BTreeMap::new(),
            }),
        };
        let mut wire = Vec::new();
        ciborium::into_writer(&obj, &mut wire).unwrap();
        let err = store.put_bytes(&wire).unwrap_err();
        assert!(
            matches!(err, Error::Validation(ref m) if m.contains("not canonical")),
            "{err:?}"
        );
    }

    #[test]
    fn get_reports_cid_mismatch_on_corrupt_slot() {
        let store = MemObjectStore::new();
        let obj = blob(vec![1], 1);
        let good_cid = store.put(&obj).unwrap();
        let other = blob(vec![2], 2);
        let other_bytes = other.to_canonical_bytes().unwrap();
        store.write_map().insert(good_cid, other_bytes);
        let err = store.get(&good_cid).unwrap_err();
        assert!(
            matches!(err, Error::Store(ref m) if m.contains("CID mismatch")),
            "{err:?}"
        );
    }

    #[test]
    fn default_is_empty() {
        let store = MemObjectStore::default();
        assert!(!store.has(&Cid::from_canonical_bytes(b"x")));
    }
}
