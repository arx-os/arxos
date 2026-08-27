//! Commit staged captures into a signed root.

use std::collections::BTreeSet;

use crate::entity::collapse_active_set_preferring;
use crate::error::{Error, Result};
use crate::root::{RootBody, RootBuilder};

use super::{now_secs, BuildingRepository, CommitResult};

impl BuildingRepository {
    /// Commit staged (+ existing head set) to a new signed Root and advance head.
    ///
    /// Rebuilds the versioned spatial index and attaches it to the root.
    /// Applies `pending_removes`, then collapses the active set so at most one
    /// version CID per [`crate::entity::EntityId`] remains (staged updates win
    /// ties on equal `created`).
    pub fn commit(&mut self, message: Option<String>) -> Result<CommitResult> {
        self.commit_with_options(message, true)
    }

    /// Commit with control over spatial index rebuild.
    pub fn commit_with_options(
        &mut self,
        message: Option<String>,
        rebuild_spatial: bool,
    ) -> Result<CommitResult> {
        self.require_write()?;
        let kp = self
            .keypair
            .as_ref()
            .ok_or_else(|| Error::Crypto("no device keypair loaded for signing".into()))?;

        // 1. Proposed active set: previous + staged − explicit removes.
        let mut proposed = self.active_objects.clone();
        let staged: BTreeSet<_> = self
            .working_set
            .staged()
            .iter()
            .copied()
            .chain(self.record.pending.iter().copied())
            .collect();
        proposed.extend(staged.iter().copied());
        for r in &self.record.pending_removes {
            proposed.remove(r);
        }

        // 2. Entity collapse: one version per EntityId (prefer staged on ties).
        let collapsed = collapse_active_set_preferring(&self.store, &proposed, &staged)?;
        let new_active = collapsed.kept;

        if new_active.is_empty() {
            return Err(Error::Validation("cannot commit empty object set".into()));
        }

        let added: BTreeSet<_> = new_active
            .difference(&self.active_objects)
            .copied()
            .collect();
        let removed: BTreeSet<_> = self
            .active_objects
            .difference(&new_active)
            .copied()
            .collect();

        // 3. Checkpoint policy (single source of truth in root::checkpoint).
        let previous = self.record.head_root;
        let is_checkpoint = crate::root::should_checkpoint_at(&self.store, previous)?;

        // 4. Spatial index update (incremental for pure adds; full rebuild when
        //    anything was removed/superseded so the index drops dead refs).
        let spatial_index_root = if rebuild_spatial {
            let need_full = !removed.is_empty();
            let mut prev_si = None;
            if let Some(prev_cid) = previous {
                if let Ok(prev_obj) = self.store.get(&prev_cid) {
                    if let Ok(prev_root) = RootBody::from_object(&prev_obj) {
                        prev_si = prev_root.spatial_index_root;
                    }
                }
            }
            if !need_full {
                if let Some(si) = prev_si {
                    let new_entries =
                        crate::spatial::collect_entries(&self.store, added.iter().copied())?;
                    crate::spatial::insert_incremental(&self.store, Some(si), new_entries)?
                } else {
                    let entries =
                        crate::spatial::collect_entries(&self.store, new_active.iter().copied())?;
                    crate::spatial::build_index(&self.store, entries)?
                }
            } else {
                let entries =
                    crate::spatial::collect_entries(&self.store, new_active.iter().copied())?;
                crate::spatial::build_index(&self.store, entries)?
            }
        } else {
            None
        };

        // 5. Construct Root using Builder
        let mut builder = RootBuilder::new(self.record.building_id.clone(), now_secs());
        if is_checkpoint {
            builder = builder.objects(new_active.clone());
        } else {
            builder = builder.added(added).removed(removed);
        }

        if let Some(prev) = previous {
            builder = builder.previous_root(prev);
        }
        if let Some(si) = spatial_index_root {
            builder = builder.spatial_index(si);
        }
        if let Some(msg) = message {
            builder = builder.message(msg);
        }

        let (root_obj, root_cid) = builder.build_signed(&kp)?;
        // Fail closed: author must be in Building.controller_keys of the new active set.
        {
            let root = RootBody::from_object(&root_obj)?;
            root.verify_with_store(&self.store)?;
        }
        self.store.put(&root_obj)?;

        // Update state
        self.active_objects = new_active;
        self.record.head_root = Some(root_cid);
        self.record.pending.clear();
        self.record.pending_removes.clear();
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;

        self.working_set.clear_staged();
        self.working_set.pin(root_cid);
        self.working_set.cache_only(root_cid, root_obj);

        Ok(CommitResult {
            root_cid,
            building_id: self.record.building_id.clone(),
            object_count: self.active_objects.len() as u64,
            previous_root: previous,
            continuity: None,
        })
    }
}
