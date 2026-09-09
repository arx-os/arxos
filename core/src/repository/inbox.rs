//! Inbox apply / reject on [`BuildingRepository`].

use std::collections::BTreeSet;

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::inbox::{self, InboxAdd, InboxFile};
use crate::object::{Object, ObjectBody, ObjectType};

use super::{now_secs, BuildingRepository, CaptureResult, CommitResult};

/// Result of applying the inbox into official history.
#[derive(Debug, Clone)]
pub struct InboxApplyResult {
    pub commit: CommitResult,
    pub applied: Vec<Cid>,
}

impl BuildingRepository {
    /// Stage an object already in the CAS (no byte copy).
    ///
    /// Used by inbox apply so fuse-on-commit stays the one implementation.
    pub fn stage_object(&mut self, cid: Cid) -> Result<CaptureResult> {
        self.require_write()?;
        if !self.store.contains(&cid) {
            return Err(Error::NotFound(format!("stage_object: {cid} not in CAS")));
        }
        let obj = self.store.get(&cid)?;
        if obj.header.object_type == ObjectType::Root || matches!(obj.body, ObjectBody::Root(_)) {
            return Err(Error::Validation(
                "cannot stage a Root; contributors do not push official history".into(),
            ));
        }
        self.record.pending_removes.remove(&cid);
        self.working_set.stage(cid, obj.clone());
        self.record.pending.insert(cid);
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;
        Ok(CaptureResult {
            cid,
            object_type: obj.header.object_type,
        })
    }

    /// Append a CAS object to this building's inbox (idempotent). Does not stage
    /// onto the working set and does not move `head_root`.
    pub fn inbox_add(&self, cid: Cid, author_hex: &str) -> Result<InboxAdd> {
        self.require_write()?;
        if !self.store.contains(&cid) {
            return Err(Error::NotFound(format!(
                "inbox_add: {cid} not in CAS (PutObject first)"
            )));
        }
        let obj = self.store.get(&cid)?;
        reject_inbox_object(&obj, &self.record.building_id)?;
        inbox::inbox_add(self.store.root(), &self.record.building_id, &cid, author_hex)
    }

    /// List pending inbox entries (no flock required; TOCTOU vs serve).
    pub fn inbox_list(&self) -> Result<InboxFile> {
        inbox::load_inbox(self.store.root(), &self.record.building_id)
    }

    /// Stage pending Facts and commit (controller only). Fuse-on-commit runs.
    ///
    /// `only` restricts to a CID subset; `None` applies the whole inbox.
    pub fn inbox_apply(&mut self, only: Option<&BTreeSet<Cid>>) -> Result<InboxApplyResult> {
        self.require_write()?;
        if self.keypair.is_none() {
            return Err(Error::Crypto(
                "no device keypair loaded for inbox apply (controller commit)".into(),
            ));
        }
        let file = inbox::load_inbox(self.store.root(), &self.record.building_id)?;
        let mut applied = Vec::new();
        for entry in &file.pending {
            let cid = parse_cid(&entry.cid)?;
            if let Some(want) = only {
                if !want.contains(&cid) {
                    continue;
                }
            }
            let obj = self.store.get(&cid)?;
            reject_inbox_object(&obj, &self.record.building_id)?;
            self.stage_object(cid)?;
            applied.push(cid);
        }
        if applied.is_empty() {
            return Err(Error::Validation("inbox apply: nothing to apply".into()));
        }
        let commit = self.commit(Some("inbox apply".into()))?;
        let drop: BTreeSet<Cid> = applied.iter().copied().collect();
        inbox::inbox_remove(self.store.root(), &self.record.building_id, &drop)?;
        Ok(InboxApplyResult { commit, applied })
    }

    /// Drop CIDs from the inbox only. CAS bytes remain.
    pub fn inbox_reject(&self, cids: &BTreeSet<Cid>) -> Result<u64> {
        self.require_write()?;
        inbox::inbox_remove(self.store.root(), &self.record.building_id, cids)
    }
}

fn parse_cid(s: &str) -> Result<Cid> {
    use std::str::FromStr;
    Cid::from_str(s)
}

/// Roots cannot enter the inbox. Building/Floor `building_id` must match.
pub fn reject_inbox_object(obj: &Object, building_id: &crate::object::BuildingId) -> Result<()> {
    if obj.header.object_type == ObjectType::Root || matches!(obj.body, ObjectBody::Root(_)) {
        return Err(Error::Validation(
            "inbox rejects Root objects (contributors do not push official history)".into(),
        ));
    }
    if let Some(bid) = object_building_id(obj) {
        if bid != building_id {
            return Err(Error::Validation(format!(
                "object building_id {bid} does not match inbox building {building_id}"
            )));
        }
    }
    Ok(())
}

fn object_building_id(obj: &Object) -> Option<&crate::object::BuildingId> {
    match &obj.body {
        ObjectBody::Building(b) => Some(&b.building_id),
        ObjectBody::Floor(b) => Some(&b.building_id),
        _ => None,
    }
}

/// CIDs referenced from a domain object (blobs, hosts, evidence).
pub fn referenced_cids(obj: &Object) -> Vec<Cid> {
    match &obj.body {
        ObjectBody::Surface(b) => {
            let mut v = b.evidence.clone();
            if let Some(s) = b.space {
                v.push(s);
            }
            v
        }
        ObjectBody::Opening(b) => {
            let mut v = b.evidence.clone();
            if let Some(s) = b.host_surface {
                v.push(s);
            }
            v
        }
        ObjectBody::Equipment(b) => {
            let mut v = b.evidence.clone();
            if let Some(s) = b.system {
                v.push(s);
            }
            v
        }
        ObjectBody::Run(b) => b.evidence.clone(),
        ObjectBody::Annotation(b) => {
            let mut v = Vec::new();
            if let Some(s) = b.media_ref {
                v.push(s);
            }
            if let Some(s) = b.space {
                v.push(s);
            }
            v
        }
        ObjectBody::PointCloudChunk(b) => b.points_blob.into_iter().collect(),
        ObjectBody::Mesh(b) => {
            let mut v = Vec::new();
            if let Some(s) = b.vertices_blob {
                v.push(s);
            }
            if let Some(s) = b.indices_blob {
                v.push(s);
            }
            v
        }
        ObjectBody::Provenance(b) => {
            let mut v = b.evidence.clone();
            v.push(b.subject);
            v
        }
        _ => Vec::new(),
    }
}


