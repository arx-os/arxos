//! Repository root: commits a set of object CIDs for a building.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::canonical::{cid_of, to_canonical_cbor};
use crate::cid::Cid;
use crate::crypto::{AuthorSignature, Keypair};
use crate::error::{Error, Result};
use crate::object::{BuildingId, Object, ObjectBody, ObjectHeader, SCHEMA_VERSION};

/// Root body: the committed state of a building repository.
///
/// The CID of a Root object is the current state of the building repository.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RootBody {
    pub building_id: BuildingId,
    pub previous_root: Option<Cid>,
    /// Content-addressed object set (ordered for determinism).
    pub objects: BTreeSet<Cid>,
    pub spatial_index_root: Option<Cid>,
    /// Unix timestamp in seconds.
    pub timestamp: u64,
    /// Author signatures over the unsigned root payload.
    pub authors: Vec<AuthorSignature>,
    /// Optional commit message.
    pub message: Option<String>,
}

impl RootBody {
    /// Create a new root without signatures.
    pub fn new(
        building_id: BuildingId,
        previous_root: Option<Cid>,
        objects: BTreeSet<Cid>,
        timestamp: u64,
    ) -> Self {
        Self {
            building_id,
            previous_root,
            objects,
            spatial_index_root: None,
            timestamp,
            authors: Vec::new(),
            message: None,
        }
    }

    pub fn with_message(mut self, message: impl Into<String>) -> Self {
        self.message = Some(message.into());
        self
    }

    pub fn with_spatial_index(mut self, spatial_index_root: Cid) -> Self {
        self.spatial_index_root = Some(spatial_index_root);
        self
    }

    /// Canonical bytes signed by authors (authors field cleared).
    pub fn signing_payload(&self) -> Result<Vec<u8>> {
        let unsigned = RootBody {
            building_id: self.building_id.clone(),
            previous_root: self.previous_root,
            objects: self.objects.clone(),
            spatial_index_root: self.spatial_index_root,
            timestamp: self.timestamp,
            authors: Vec::new(),
            message: self.message.clone(),
        };
        to_canonical_cbor(&unsigned)
    }

    /// Append an author signature.
    pub fn sign(&mut self, keypair: &Keypair) -> Result<()> {
        let payload = self.signing_payload()?;
        self.authors.push(AuthorSignature::create(keypair, &payload));
        Ok(())
    }

    /// Verify all author signatures.
    pub fn verify_authors(&self) -> Result<()> {
        if self.authors.is_empty() {
            return Err(Error::Signature("root has no author signatures".into()));
        }
        let payload = self.signing_payload()?;
        for author in &self.authors {
            author.verify(&payload)?;
        }
        Ok(())
    }

    /// Wrap as a full Object (for CAS storage).
    ///
    /// Author signatures live on [`RootBody::authors`] (they cover the root
    /// body payload, not the object envelope). The header only records the
    /// primary author public key for attribution — use `verify_authors`.
    pub fn into_object(self, created: u64) -> Object {
        Object {
            header: ObjectHeader {
                object_type: crate::object::ObjectType::Root,
                schema_version: SCHEMA_VERSION,
                created,
                author: self.authors.first().map(|a| a.public_key),
                signature: None,
            },
            body: ObjectBody::Root(self),
        }
    }

    /// Extract RootBody from an object if it is a Root.
    pub fn from_object(obj: &Object) -> Result<&RootBody> {
        match &obj.body {
            ObjectBody::Root(r) => Ok(r),
            _ => Err(Error::Validation(format!(
                "expected root object, got {}",
                obj.header.object_type
            ))),
        }
    }
}

/// Convenience builder for creating and signing roots.
pub struct RootBuilder {
    building_id: BuildingId,
    previous_root: Option<Cid>,
    objects: BTreeSet<Cid>,
    spatial_index_root: Option<Cid>,
    timestamp: u64,
    message: Option<String>,
}

impl RootBuilder {
    pub fn new(building_id: BuildingId, timestamp: u64) -> Self {
        Self {
            building_id,
            previous_root: None,
            objects: BTreeSet::new(),
            spatial_index_root: None,
            timestamp,
            message: None,
        }
    }

    pub fn previous_root(mut self, cid: Cid) -> Self {
        self.previous_root = Some(cid);
        self
    }

    pub fn objects(mut self, objects: BTreeSet<Cid>) -> Self {
        self.objects = objects;
        self
    }

    pub fn insert(mut self, cid: Cid) -> Self {
        self.objects.insert(cid);
        self
    }

    pub fn spatial_index(mut self, cid: Cid) -> Self {
        self.spatial_index_root = Some(cid);
        self
    }

    pub fn message(mut self, msg: impl Into<String>) -> Self {
        self.message = Some(msg.into());
        self
    }

    /// Build unsigned root body.
    pub fn build(self) -> RootBody {
        let mut root = RootBody::new(
            self.building_id,
            self.previous_root,
            self.objects,
            self.timestamp,
        );
        root.spatial_index_root = self.spatial_index_root;
        root.message = self.message;
        root
    }

    /// Build, sign with keypair, and wrap as Object. Returns (object, root_cid).
    pub fn build_signed(self, keypair: &Keypair) -> Result<(Object, Cid)> {
        let created = self.timestamp;
        let mut body = self.build();
        body.sign(keypair)?;
        let obj = body.into_object(created);
        let cid = obj.cid()?;
        Ok((obj, cid))
    }
}

/// CID of a root body alone (without object envelope). Prefer object CID in store.
pub fn root_body_cid(root: &RootBody) -> Result<Cid> {
    cid_of(root)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::BuildingId;

    #[test]
    fn root_sign_verify() {
        let kp = Keypair::generate();
        let building = BuildingId::new();
        let mut objects = BTreeSet::new();
        objects.insert(Cid::from_canonical_bytes(b"obj-a"));
        objects.insert(Cid::from_canonical_bytes(b"obj-b"));

        let (obj, cid) = RootBuilder::new(building, 1_700_000_100)
            .objects(objects)
            .message("initial scan")
            .build_signed(&kp)
            .unwrap();

        let root = RootBody::from_object(&obj).unwrap();
        root.verify_authors().unwrap();
        assert_eq!(obj.cid().unwrap(), cid);
        assert_eq!(root.objects.len(), 2);
    }

    #[test]
    fn root_object_set_order_independent() {
        let building = BuildingId::from("01TESTBUILDING000000000000".to_string());
        let a = Cid::from_canonical_bytes(b"aaa");
        let b = Cid::from_canonical_bytes(b"bbb");

        let mut s1 = BTreeSet::new();
        s1.insert(b);
        s1.insert(a);
        let mut s2 = BTreeSet::new();
        s2.insert(a);
        s2.insert(b);

        let r1 = RootBody::new(building.clone(), None, s1, 1);
        let r2 = RootBody::new(building, None, s2, 1);
        assert_eq!(root_body_cid(&r1).unwrap(), root_body_cid(&r2).unwrap());
    }
}
