//! Commit staged captures into a signed root.

use std::collections::BTreeSet;

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::root::{RootBody, RootBuilder};

use super::{now_secs, BuildingRepository, CommitResult};

impl BuildingRepository {
    /// Commit staged (+ existing head set) to a new signed Root and advance head.
    ///
    /// Rebuilds the versioned spatial index and attaches it to the root.
    pub fn commit(&mut self, message: Option<String>) -> Result<CommitResult> {
        self.commit_with_options(message, true)
    }

    /// Commit with control over spatial index rebuild.
    pub fn commit_with_options(
        &mut self,
        message: Option<String>,
        rebuild_spatial: bool,
    ) -> Result<CommitResult> {
        let kp = self
            .keypair
            .as_ref()
            .ok_or_else(|| Error::Crypto("no device keypair loaded for signing".into()))?
            .clone();

        // 1. Calculate new active set in memory
        let mut new_active = self.active_objects.clone();
        let staged_and_pending: BTreeSet<Cid> = self.working_set.staged().iter().copied()
            .chain(self.record.pending.iter().copied())
            .collect();
        new_active.extend(staged_and_pending.clone());

        if new_active.is_empty() {
            return Err(Error::Validation(
                "cannot commit empty object set".into(),
            ));
        }

        let added: BTreeSet<Cid> = staged_and_pending.difference(&self.active_objects).copied().collect();
        let removed = BTreeSet::new(); // Currently no deletion API exists

        // 2. Checkpoint policy (single source of truth in root::checkpoint).
        let previous = self.record.head_root;
        let is_checkpoint = crate::root::should_checkpoint_at(&self.store, previous)?;

        // 3. Spatial index update (incremental or full build)
        let spatial_index_root = if rebuild_spatial {
            let mut prev_si = None;
            if let Some(prev_cid) = previous {
                if let Ok(prev_obj) = self.store.get(&prev_cid) {
                    if let Ok(prev_root) = RootBody::from_object(&prev_obj) {
                        prev_si = prev_root.spatial_index_root;
                    }
                }
            }
            if let Some(si) = prev_si {
                let new_entries = crate::spatial::collect_entries(&self.store, added.iter().copied())?;
                crate::spatial::insert_incremental(&self.store, Some(si), new_entries)?
            } else {
                let entries = crate::spatial::collect_entries(&self.store, new_active.iter().copied())?;
                crate::spatial::build_index(&self.store, entries)?
            }
        } else {
            None
        };

        // 4. Construct Root using Builder
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
            // Building may only be resolvable after domain objects are in the store;
            // new_active is already staged into the CAS via capture.
            root.verify_with_store(&self.store)?;
        }
        self.store.put(&root_obj)?;

        // Update state
        self.active_objects = new_active;
        self.record.head_root = Some(root_cid);
        self.record.pending.clear();
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
        })
    }

}
