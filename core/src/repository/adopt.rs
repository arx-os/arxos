//! Adopt remote roots (authorization + completeness + replica continuity).

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::root::{verify_continuous_with_local, RootBody};

use super::{now_secs, AdoptOptions, BuildingRepository, CommitResult};

impl BuildingRepository {
    /// Adopt a remote root as this building's head (after objects are in the CAS).
    ///
    /// Default (`allow_untrusted = false`): remote must be self-consistent
    /// ([`RootBody::verify_with_store`]) **and** continuous with this replica
    /// ([`verify_continuous_with_local`]). First contact (`head_root == None`)
    /// is TOFU.
    pub fn adopt_root(&mut self, root_cid: Cid) -> Result<CommitResult> {
        self.adopt_root_with_options(root_cid, &AdoptOptions::default())
    }

    /// Adopt a remote root with explicit control over signature validation.
    ///
    /// Continuity is checked against [`BuildingRecord::head_root`] *before*
    /// mutation. [`CommitResult::previous_root`] is observational.
    pub fn adopt_root_with_options(
        &mut self,
        root_cid: Cid,
        opts: &AdoptOptions,
    ) -> Result<CommitResult> {
        self.require_write()?;
        let obj = self.store.get(&root_cid)?;
        let root = RootBody::from_object(&obj)?.clone();
        if root.building_id != self.record.building_id {
            return Err(Error::Validation(format!(
                "root building_id {} does not match repository {}",
                root.building_id, self.record.building_id
            )));
        }

        // Always materialize first so we can resolve controllers from the root's active set.
        let active_set = root.materialize_active_objects(&self.store)?;

        if !opts.allow_partial {
            let missing = crate::root::missing_active_objects(&self.store, &active_set)?;
            if !missing.is_empty() {
                let preview: Vec<String> = missing.iter().take(8).map(|c| c.to_string()).collect();
                return Err(Error::NotFound(format!(
                    "incomplete root for adopt: missing {} active object(s), e.g. {}",
                    missing.len(),
                    preview.join(", ")
                )));
            }
            if let Some(si) = root.spatial_index_root {
                if !self.store.contains(&si) {
                    return Err(Error::NotFound(format!(
                        "incomplete root for adopt: spatial_index_root {si} missing"
                    )));
                }
            }
        }

        let continuity = if !opts.allow_untrusted {
            // Self-consistency + replica continuity. `allow_untrusted` skips both.
            Some(verify_continuous_with_local(
                &root,
                &root_cid,
                &self.store,
                self.record.head_root.as_ref(),
                &self.active_objects,
            )?)
        } else {
            // Escape hatch: still attempt crypto verify for diagnostics, ignore failure.
            // Continuity is not claimed.
            let _ = root.verify_authors();
            None
        };

        let object_count = active_set.len() as u64;

        let previous = self.record.head_root;
        self.active_objects = active_set;
        self.record.head_root = Some(root_cid);
        self.record.pending.clear();
        self.record.pending_removes.clear();
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;

        self.working_set.clear_staged();
        self.working_set.pin(root_cid);
        self.working_set.cache_only(root_cid, obj);
        // Do not eagerly materialize the full object set (partial by default).

        Ok(CommitResult {
            root_cid,
            building_id: self.record.building_id.clone(),
            object_count,
            previous_root: previous,
            continuity,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::{BuildingBody, Object, ObjectBody};
    use crate::root::RootBuilder;
    use crate::Error;
    use std::collections::{BTreeMap, BTreeSet};
    use tempfile::tempdir;

    fn mallory_fork(repo: &BuildingRepository, mallory: &Keypair) -> (Cid, Cid) {
        let bid = repo.building_id().clone();
        let b_m = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: Some("Mallory".into()),
                controller_keys: vec![mallory.public_key()],
                properties: BTreeMap::new(),
            }),
            99,
        );
        let b_m_cid = repo.put_object(&b_m).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(b_m_cid);
        let (fork_obj, fork_cid) = RootBuilder::new(bid, 10_000)
            .objects(objects)
            .message("mallory genesis")
            .build_signed(mallory)
            .unwrap();
        repo.put_object(&fork_obj).unwrap();
        (b_m_cid, fork_cid)
    }

    #[test]
    fn adopt_rejects_replaced_building_full_set_fork() {
        let dir = tempdir().unwrap();
        let mut repo = BuildingRepository::init(dir.path(), Some("Alice".into()), None).unwrap();
        let alice_head = repo.head_root().unwrap();
        let mallory = Keypair::generate();
        let (_, fork_cid) = mallory_fork(&repo, &mallory);

        let err = repo.adopt_root(fork_cid).unwrap_err();
        assert!(
            matches!(err, Error::Authorization(_)),
            "expected Authorization, got {err:?}"
        );
        assert_eq!(repo.head_root(), Some(alice_head));
    }

    #[test]
    fn adopt_rejects_full_set_checkpoint_not_descending_local_head() {
        // Alice-signed sibling history: same keys, not a descendant of current head.
        let dir = tempdir().unwrap();
        let mut repo = BuildingRepository::init(dir.path(), Some("Alice".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let alice = Keypair::from_seed(*repo.keypair().unwrap().seed());
        let building = repo.record().building_object.unwrap();
        let h0 = repo.head_root().unwrap();

        repo.capture_annotation(&crate::capture::AnnotationCapture::new(
            "advance",
            crate::object::Pose::default(),
        ))
        .unwrap();
        let h1 = repo.commit(Some("advance".into())).unwrap().root_cid;
        assert_ne!(h1, h0);

        let mut objects = BTreeSet::new();
        objects.insert(building);
        let (sib, sib_cid) = RootBuilder::new(bid, 50)
            .objects(objects)
            .previous_root(h0)
            .message("equivocation from h0")
            .build_signed(&alice)
            .unwrap();
        repo.put_object(&sib).unwrap();

        let err = repo.adopt_root(sib_cid).unwrap_err();
        assert!(
            matches!(err, Error::Authorization(ref m) if m.contains("not a descendant")),
            "expected descendant rejection, got {err:?}"
        );
        assert_eq!(repo.head_root(), Some(h1));
    }

    #[test]
    fn adopt_accepts_fast_forward_signed_by_local_controller() {
        let dir = tempdir().unwrap();
        let mut repo = BuildingRepository::init(dir.path(), Some("Alice".into()), None).unwrap();
        let bid = repo.building_id().clone();
        let alice = Keypair::from_seed(*repo.keypair().unwrap().seed());
        let building = repo.record().building_object.unwrap();
        let local_head = repo.head_root().unwrap();

        let mut objects = BTreeSet::new();
        objects.insert(building);
        let (ff, ff_cid) = RootBuilder::new(bid, 50)
            .objects(objects)
            .previous_root(local_head)
            .message("fast-forward")
            .build_signed(&alice)
            .unwrap();
        repo.put_object(&ff).unwrap();

        let res = repo.adopt_root(ff_cid).unwrap();
        assert_eq!(res.root_cid, ff_cid);
        assert_eq!(res.previous_root, Some(local_head));
        assert_eq!(
            res.continuity,
            Some(crate::root::ContinuityOutcome::FastForward)
        );
        assert_eq!(repo.head_root(), Some(ff_cid));
    }

    #[test]
    fn adopt_first_contact_tofu_succeeds() {
        let dir_a = tempdir().unwrap();
        let dir_b = tempdir().unwrap();
        let repo_a = BuildingRepository::init(dir_a.path(), Some("Site".into()), None).unwrap();
        let bid = repo_a.building_id().clone();
        let head = repo_a.head_root().unwrap();
        let closure = repo_a.root_closure_bytes(&head).unwrap();
        drop(repo_a);

        let mut repo_b =
            BuildingRepository::open_or_follow(dir_b.path(), &bid, Some("Site".into())).unwrap();
        assert!(repo_b.head_root().is_none());
        for (_cid, bytes) in &closure {
            repo_b.put_object_bytes(bytes).unwrap();
        }
        let res = repo_b.adopt_root(head).unwrap();
        assert_eq!(res.root_cid, head);
        assert_eq!(
            res.continuity,
            Some(crate::root::ContinuityOutcome::FirstTrust)
        );
        assert_eq!(repo_b.head_root(), Some(head));
    }

    #[test]
    fn adopt_rejects_fork_claiming_local_head_in_merge_parents() {
        // Mallory names local_head in merge_parents / previous_root so a naive
        // DAG walk would treat the fork as a descendant. Author intersection
        // still rejects: ingested-only Mallory is not a local controller.
        let dir = tempdir().unwrap();
        let mut repo = BuildingRepository::init(dir.path(), Some("Alice".into()), None).unwrap();
        let alice_head = repo.head_root().unwrap();
        let bid = repo.building_id().clone();
        let mallory = Keypair::generate();
        let b_m = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: Some("Mallory".into()),
                controller_keys: vec![mallory.public_key()],
                properties: BTreeMap::new(),
            }),
            99,
        );
        let b_m_cid = repo.put_object(&b_m).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(b_m_cid);
        let mut merge_parents = BTreeSet::new();
        merge_parents.insert(alice_head);
        let (fork_obj, fork_cid) = RootBuilder::new(bid, 10_000)
            .objects(objects)
            .previous_root(alice_head)
            .merge_parents(merge_parents)
            .message("mallory claims merge")
            .build_signed(&mallory)
            .unwrap();
        repo.put_object(&fork_obj).unwrap();

        let err = repo.adopt_root(fork_cid).unwrap_err();
        assert!(
            matches!(err, Error::Authorization(ref m) if m.contains("not a local controller")),
            "expected local-controller rejection, got {err:?}"
        );
        assert_eq!(repo.head_root(), Some(alice_head));
    }
}
