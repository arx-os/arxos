//! Root authorization: authors must be building controllers.
//!
//! Two checks, two jobs:
//! - [`RootBody::verify_with_store`] — **self-consistency** of a Root versus
//!   the Building in *that Root's* active set. Used by local commit.
//! - [`verify_continuous_with_local`] — **replica continuity**: the remote
//!   Root is self-consistent *and* its authors are controllers of *this*
//!   replica's current Building, and the remote descends from the local head.
//!   Used by default adopt / production pull. Do not fold the two together.

use std::collections::BTreeSet;

use crate::cid::Cid;
use crate::crypto::PublicKey;
use crate::error::{Error, Result};
use crate::object::{BuildingId, ObjectBody};
use crate::store::ObjectRead;

use super::checkpoint::is_checkpoint_body;
use super::RootBody;

/// Max Root hops when proving replica descent.
///
/// Generous versus [`super::CHECKPOINT_INTERVAL`] so honest pulls across
/// several checkpoints still work. Exceeding the bound is fail-closed
/// (never “self-consistent is enough”).
pub const MAX_CONTINUITY_ANCESTOR_HOPS: u32 = 4096;

/// Outcome of [`verify_continuous_with_local`] after self-consistency holds.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContinuityOutcome {
    /// Replica has no head. Remote passed [`RootBody::verify_with_store`].
    /// This is first-trust (`open_or_follow`); not a fast-forward.
    FirstTrust,
    /// Remote authors are local controllers and the remote Root descends
    /// from the local head (including idempotent re-adopt of that head).
    FastForward,
}

/// Find `Building.controller_keys` for `building_id` among an active object set.
///
/// Fail closed if no matching Building object is present, or if `controller_keys`
/// is empty.
pub fn resolve_controller_keys<R: ObjectRead + ?Sized>(
    store: &R,
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
    /// Self-consistency only: controllers come from **this Root's** active set,
    /// not from a replica's current head. Local [`crate::repository::BuildingRepository::commit`]
    /// uses this. Adopt / production pull must also call
    /// [`verify_continuous_with_local`].
    pub fn verify_with_store<R: ObjectRead + ?Sized>(&self, store: &R) -> Result<()> {
        let active = self.materialize_active_objects(store)?;
        let controllers = resolve_controller_keys(store, &active, &self.building_id)?;
        self.verify_authorized(&controllers)
    }
}

/// Replica-relative continuity for a remote Root already in `store`.
///
/// 1. Always [`RootBody::verify_with_store`] (self-consistency).
/// 2. `local_head == None` → [`ContinuityOutcome::FirstTrust`] (TOFU).
/// 3. Otherwise every remote author must be in the **local** Building's
///    `controller_keys`, and `remote` must be a descendant of `local_head`.
///
/// `remote_cid` is the CAS id of the Root object (not [`super::root_body_cid`]).
/// A full-set checkpoint with `previous_root == None` against an existing
/// head is a second genesis and is rejected.
///
/// Ancestry walks `previous_root` and `merge_parents` (multi-parent merge
/// commits name both tips). Missing parents and walk-bound exceeded fail
/// closed. `created` timestamps are not consulted (I3 / I8: no newest-wins).
pub fn verify_continuous_with_local<R: ObjectRead + ?Sized>(
    remote: &RootBody,
    remote_cid: &Cid,
    store: &R,
    local_head: Option<&Cid>,
    local_active: &BTreeSet<Cid>,
) -> Result<ContinuityOutcome> {
    remote.verify_with_store(store).map_err(|e| match e {
        Error::Authorization(msg) => {
            Error::Authorization(format!("root author authorization failed: {msg}"))
        }
        Error::Signature(msg) => {
            Error::Signature(format!("root author verification failed: {msg}"))
        }
        other => other,
    })?;

    let Some(local_head) = local_head else {
        return Ok(ContinuityOutcome::FirstTrust);
    };

    let local_keys = resolve_controller_keys(store, local_active, &remote.building_id)?;
    for author in &remote.authors {
        if !local_keys.iter().any(|k| k == &author.public_key) {
            return Err(Error::Authorization(format!(
                "remote author is not a local controller: {}",
                author.public_key
            )));
        }
    }

    if remote_cid == local_head {
        return Ok(ContinuityOutcome::FastForward);
    }

    if is_checkpoint_body(remote) && remote.previous_root.is_none() {
        return Err(Error::Authorization(
            "refusing second genesis for building with existing head".into(),
        ));
    }

    if descendant_of_local_head(store, remote, local_head)? {
        Ok(ContinuityOutcome::FastForward)
    } else {
        Err(Error::Authorization(
            "remote root is not a descendant of local head".into(),
        ))
    }
}

/// True when `local_head` appears on `remote`'s `previous_root` / `merge_parents`
/// DAG. `merge_parents` are searched for `local_head` only — an ingested-only
/// Mallory CID in that set is not a trusted head and does not make Mallory's
/// own Root a descendant. Fail closed on missing parent objects, non-Root
/// ancestors; cycles skipped via `visited`; bound exceeded is an error.
fn descendant_of_local_head<R: ObjectRead + ?Sized>(
    store: &R,
    remote: &RootBody,
    local_head: &Cid,
) -> Result<bool> {
    let mut stack: Vec<Cid> = Vec::new();
    if let Some(prev) = remote.previous_root {
        stack.push(prev);
    }
    stack.extend(remote.merge_parents.iter().copied());

    let mut visited: BTreeSet<Cid> = BTreeSet::new();
    let mut hops: u32 = 0;
    while let Some(cid) = stack.pop() {
        hops = hops.saturating_add(1);
        if hops > MAX_CONTINUITY_ANCESTOR_HOPS {
            return Err(Error::Authorization(format!(
                "remote root ancestor walk exceeded bound ({MAX_CONTINUITY_ANCESTOR_HOPS})"
            )));
        }
        if cid == *local_head {
            return Ok(true);
        }
        if !visited.insert(cid) {
            continue;
        }
        let obj = store.get(&cid).map_err(|e| match e {
            Error::NotFound(msg) => Error::NotFound(format!(
                "missing parent {cid} while proving descent from remote root: {msg}"
            )),
            other => other,
        })?;
        let body = RootBody::from_object(&obj).map_err(|_| {
            Error::Authorization(format!(
                "ancestor {cid} is not a Root while proving descent from remote root"
            ))
        })?;
        if let Some(prev) = body.previous_root {
            stack.push(prev);
        }
        stack.extend(body.merge_parents.iter().copied());
    }
    Ok(false)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::{BuildingBody, Object};
    use crate::root::RootBuilder;
    use crate::store::ObjectStore;
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

    #[test]
    fn continuity_first_trust_when_no_local_head() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();
        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(bc);
        let (obj, cid) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&obj).unwrap();
        let root = RootBody::from_object(&obj).unwrap();
        let outcome =
            verify_continuous_with_local(root, &cid, &store, None, &BTreeSet::new()).unwrap();
        assert_eq!(outcome, ContinuityOutcome::FirstTrust);
    }

    #[test]
    fn continuity_rejects_second_genesis_against_existing_head() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();
        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(bc);
        let (h0, h0_cid) = RootBuilder::new(bid.clone(), 10)
            .objects(objects.clone())
            .build_signed(&kp)
            .unwrap();
        store.put(&h0).unwrap();
        let (fork, fork_cid) = RootBuilder::new(bid, 11)
            .objects(objects)
            .message("equivocation")
            .build_signed(&kp)
            .unwrap();
        store.put(&fork).unwrap();
        let remote = RootBody::from_object(&fork).unwrap();
        let err = verify_continuous_with_local(
            remote,
            &fork_cid,
            &store,
            Some(&h0_cid),
            &BTreeSet::from([bc]),
        )
        .unwrap_err();
        assert!(
            matches!(err, Error::Authorization(ref m) if m.contains("second genesis")),
            "{err:?}"
        );
    }
}
