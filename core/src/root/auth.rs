//! Root authorization: authors must be building controllers.

use std::collections::BTreeSet;

use crate::cid::Cid;
use crate::crypto::PublicKey;
use crate::error::{Error, Result};
use crate::object::{BuildingId, ObjectBody};
use crate::store::ObjectStore;

use super::RootBody;

/// Find `Building.controller_keys` for `building_id` among an active object set.
///
/// Fail closed if no matching Building object is present, or if `controller_keys`
/// is empty.
pub fn resolve_controller_keys(
    store: &ObjectStore,
    active: &BTreeSet<Cid>,
    building_id: &BuildingId,
) -> Result<Vec<PublicKey>> {
    let mut found: Option<Vec<PublicKey>> = None;
    for cid in active {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        };
        if let ObjectBody::Building(b) = &obj.body {
            if &b.building_id == building_id {
                if found.is_some() {
                    return Err(Error::Authorization(format!(
                        "multiple Building objects for {building_id} in active set"
                    )));
                }
                found = Some(b.controller_keys.clone());
            }
        }
    }
    match found {
        Some(keys) if !keys.is_empty() => Ok(keys),
        Some(_) => Err(Error::Authorization(format!(
            "building {building_id} has empty controller_keys"
        ))),
        None => Err(Error::Authorization(format!(
            "no Building object for {building_id} in active set"
        ))),
    }
}

impl RootBody {
    /// Verify all author signatures (cryptographic validity only).
    ///
    /// Prefer [`Self::verify_authorized`] or [`Self::verify_with_store`] for
    /// fail-closed policy that also checks building controller membership.
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

    /// Verify signatures and require every author to be in `controller_keys`.
    ///
    /// Fail closed: empty controller set or any unauthorized author is an error.
    pub fn verify_authorized(&self, controller_keys: &[PublicKey]) -> Result<()> {
        self.verify_authors()?;
        if controller_keys.is_empty() {
            return Err(Error::Authorization(
                "building has empty controller_keys; no author is authorized".into(),
            ));
        }
        for author in &self.authors {
            if !controller_keys.iter().any(|k| k == &author.public_key) {
                return Err(Error::Authorization(format!(
                    "author {} is not in building controller_keys",
                    author.public_key
                )));
            }
        }
        Ok(())
    }

    /// Materialize this root's active set, resolve Building.controller_keys, and
    /// verify that every author is an authorized controller with valid signatures.
    ///
    /// This is the single verification entry point for adopt/commit/CLI/network.
    pub fn verify_with_store(&self, store: &ObjectStore) -> Result<()> {
        let active = self.materialize_active_objects(store)?;
        let controllers = resolve_controller_keys(store, &active, &self.building_id)?;
        self.verify_authorized(&controllers)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::{BuildingBody, Object};
    use crate::root::RootBuilder;
    use std::collections::BTreeMap;
    use tempfile::tempdir;

    #[test]
    fn authorized_author_accepted() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: Some("Auth".into()),
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(bc);

        let (obj, _) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&obj).unwrap();
        let root = RootBody::from_object(&obj).unwrap();
        root.verify_with_store(&store).unwrap();
    }

    #[test]
    fn unauthorized_valid_signature_rejected() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let controller = Keypair::generate();
        let outsider = Keypair::generate();
        let bid = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![controller.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(bc);

        let (obj, _) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&outsider)
            .unwrap();
        store.put(&obj).unwrap();
        let root = RootBody::from_object(&obj).unwrap();
        root.verify_authors().unwrap();
        let err = root.verify_with_store(&store).unwrap_err();
        assert!(matches!(err, Error::Authorization(_)), "{err:?}");
    }

    #[test]
    fn missing_building_rejects_authorization() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();
        let mut objects = BTreeSet::new();
        objects.insert(Cid::from_canonical_bytes(b"not-a-building"));

        let (obj, _) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&obj).unwrap();
        let root = RootBody::from_object(&obj).unwrap();
        let err = root.verify_with_store(&store).unwrap_err();
        assert!(matches!(err, Error::Authorization(_)), "{err:?}");
    }

    #[test]
    fn empty_controller_keys_rejected() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(bc);

        let (obj, _) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&obj).unwrap();
        let root = RootBody::from_object(&obj).unwrap();
        let err = root.verify_with_store(&store).unwrap_err();
        assert!(matches!(err, Error::Authorization(_)), "{err:?}");
    }
}
