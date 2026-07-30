//! Adopt remote roots (authorization + completeness).

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::root::RootBody;

use super::{now_secs, AdoptOptions, BuildingRepository, CommitResult};

impl BuildingRepository {
    /// Adopt a remote root as this building's head (after objects are in the CAS).
    ///
    /// Fail closed by default if the root authors' signatures are missing or invalid.
    pub fn adopt_root(&mut self, root_cid: Cid) -> Result<CommitResult> {
        self.adopt_root_with_options(root_cid, &AdoptOptions::default())
    }

    /// Adopt a remote root with explicit control over signature validation.
    pub fn adopt_root_with_options(
        &mut self,
        root_cid: Cid,
        opts: &AdoptOptions,
    ) -> Result<CommitResult> {
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
                let preview: Vec<String> =
                    missing.iter().take(8).map(|c| c.to_string()).collect();
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

        if !opts.allow_untrusted {
            // Fail closed: valid signatures AND authors ∈ Building.controller_keys.
            root.verify_with_store(&self.store).map_err(|e| match e {
                Error::Authorization(msg) => Error::Authorization(format!(
                    "root author authorization failed: {msg}"
                )),
                Error::Signature(msg) => {
                    Error::Signature(format!("root author verification failed: {msg}"))
                }
                other => other,
            })?;
        } else {
            // Escape hatch: still attempt crypto verify for diagnostics, ignore failure.
            let _ = root.verify_authors();
        }

        let object_count = active_set.len() as u64;

        let previous = self.record.head_root;
        self.active_objects = active_set;
        self.record.head_root = Some(root_cid);
        self.record.pending.clear();
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
        })
    }

}
