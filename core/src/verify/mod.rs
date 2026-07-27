//! Formal-ish verification of canonicalization and root transitions.
//!
//! Phase 5: deterministic checks that any node can re-run. These are not a
//! full proof assistant, but they encode the critical safety properties of
//! the lived-experience architecture.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::canonical::{cid_of, to_canonical_cbor};
use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::Object;
use crate::root::RootBody;
use crate::store::ObjectStore;

/// Severity of a verification finding.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Severity {
    Error,
    Warning,
    Info,
}

/// One verification finding.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Finding {
    pub severity: Severity,
    pub code: String,
    pub message: String,
}

/// Result of verifying a root transition or object.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerificationReport {
    pub ok: bool,
    pub findings: Vec<Finding>,
}

impl VerificationReport {
    pub fn pass() -> Self {
        Self {
            ok: true,
            findings: Vec::new(),
        }
    }

    pub fn push(&mut self, severity: Severity, code: impl Into<String>, message: impl Into<String>) {
        if severity == Severity::Error {
            self.ok = false;
        }
        self.findings.push(Finding {
            severity,
            code: code.into(),
            message: message.into(),
        });
    }
}

/// Property: canonical CBOR is stable and CID is BLAKE3 of those bytes.
pub fn verify_object_canonicalization(obj: &Object) -> Result<VerificationReport> {
    let mut report = VerificationReport::pass();
    let b1 = obj.to_canonical_bytes()?;
    let b2 = to_canonical_cbor(obj)?;
    if b1 != b2 {
        report.push(
            Severity::Error,
            "CANON_MISMATCH",
            "to_canonical_bytes != to_canonical_cbor",
        );
    }
    let c1 = obj.cid()?;
    let c2 = Cid::from_canonical_bytes(&b1);
    if c1 != c2 {
        report.push(
            Severity::Error,
            "CID_MISMATCH",
            "object.cid() != BLAKE3(canonical bytes)",
        );
    }
    // Round-trip
    let decoded = Object::from_canonical_bytes(&b1)?;
    let c3 = decoded.cid()?;
    if c3 != c1 {
        report.push(
            Severity::Error,
            "ROUNDTRIP_CID",
            "decode → cid changed",
        );
    }
    if obj.header.signature.is_some() {
        match obj.verify_signature() {
            Ok(()) => report.push(
                Severity::Info,
                "SIG_OK",
                "object signature verifies",
            ),
            Err(e) => report.push(
                Severity::Error,
                "SIG_FAIL",
                format!("object signature invalid: {e}"),
            ),
        }
    }
    Ok(report)
}

/// Verify a root object and optional transition from `previous`.
pub fn verify_root_transition(
    store: &ObjectStore,
    root_cid: &Cid,
) -> Result<VerificationReport> {
    let mut report = VerificationReport::pass();
    let root_obj = store.get(root_cid)?;
    let canon = verify_object_canonicalization(&root_obj)?;
    report.findings.extend(canon.findings);
    report.ok &= canon.ok;

    let root = match RootBody::from_object(&root_obj) {
        Ok(r) => r.clone(),
        Err(e) => {
            report.push(Severity::Error, "NOT_ROOT", e.to_string());
            return Ok(report);
        }
    };

    match root.verify_authors() {
        Ok(()) => report.push(Severity::Info, "ROOT_SIG_OK", "all root authors verify"),
        Err(e) => report.push(
            Severity::Error,
            "ROOT_SIG_FAIL",
            format!("root author verification failed: {e}"),
        ),
    }

    // Every listed object should exist (or warn if partial).
    let mut missing = 0u64;
    for cid in &root.objects {
        if !store.contains(cid) {
            missing += 1;
        }
    }
    if missing > 0 {
        report.push(
            Severity::Warning,
            "PARTIAL_OBJECTS",
            format!("{missing} root objects not present in local store"),
        );
    }

    if let Some(prev_cid) = root.previous_root {
        if prev_cid == *root_cid {
            report.push(
                Severity::Error,
                "PREV_SELF",
                "previous_root equals current root",
            );
        }
        match store.get(&prev_cid) {
            Ok(prev_obj) => {
                let prev = RootBody::from_object(&prev_obj)?;
                if prev.building_id != root.building_id {
                    report.push(
                        Severity::Error,
                        "BUILDING_MISMATCH",
                        format!(
                            "previous building_id {} != current {}",
                            prev.building_id, root.building_id
                        ),
                    );
                }
                if root.timestamp < prev.timestamp {
                    report.push(
                        Severity::Warning,
                        "TIME_REGRESSION",
                        format!(
                            "root timestamp {} < previous {}",
                            root.timestamp, prev.timestamp
                        ),
                    );
                }
                // Transition property: objects may grow (union) or change via merge;
                // we only require both sets are well-formed BTreeSets (always true).
                let prev_set: BTreeSet<Cid> = prev.objects.clone();
                let cur_set: BTreeSet<Cid> = root.objects.clone();
                let added = cur_set.difference(&prev_set).count();
                let removed = prev_set.difference(&cur_set).count();
                report.push(
                    Severity::Info,
                    "DELTA",
                    format!("objects +{added} -{removed}"),
                );
                // Cycle detection: walk previous chain with depth limit
                if let Err(e) = detect_root_cycle(store, root_cid, 256) {
                    report.push(Severity::Error, "ROOT_CYCLE", e.to_string());
                }
            }
            Err(Error::NotFound(_)) => report.push(
                Severity::Warning,
                "PREV_MISSING",
                format!("previous root {prev_cid} not in store"),
            ),
            Err(e) => return Err(e),
        }
    } else {
        report.push(Severity::Info, "GENESIS", "root has no previous_root");
    }

    if let Some(si) = root.spatial_index_root {
        if !store.contains(&si) {
            report.push(
                Severity::Warning,
                "SPATIAL_MISSING",
                format!("spatial_index_root {si} not in store"),
            );
        }
    }

    Ok(report)
}

fn detect_root_cycle(store: &ObjectStore, start: &Cid, max_depth: usize) -> Result<()> {
    let mut seen = BTreeSet::new();
    let mut cur = Some(*start);
    let mut depth = 0;
    while let Some(cid) = cur {
        if !seen.insert(cid) {
            return Err(Error::Validation(format!(
                "cycle detected at {cid} in root chain"
            )));
        }
        if depth >= max_depth {
            return Err(Error::Validation(
                "root chain exceeds max depth (possible cycle)".into(),
            ));
        }
        let obj = match store.get(&cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => break,
            Err(e) => return Err(e),
        };
        let root = RootBody::from_object(&obj)?;
        cur = root.previous_root;
        depth += 1;
    }
    Ok(())
}

/// Verify that two serializations of the same logical root body yield the same CID.
pub fn verify_root_body_determinism(root: &RootBody) -> Result<VerificationReport> {
    let mut report = VerificationReport::pass();
    let c1 = cid_of(root)?;
    let c2 = cid_of(root)?;
    if c1 != c2 {
        report.push(
            Severity::Error,
            "ROOT_BODY_NONDET",
            "cid_of(root) unstable",
        );
    }
    Ok(report)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::AnnotationCapture;
    use crate::object::Pose;
    use crate::repository::BuildingRepository;
    use crate::Keypair;
    use tempfile::tempdir;

    #[test]
    fn root_transition_ok() {
        let dir = tempdir().unwrap();
        let kp = Keypair::generate();
        let mut repo =
            BuildingRepository::init(dir.path(), Some("V".into()), Some(kp)).unwrap();
        repo.capture_annotation(&AnnotationCapture::new(
            "a",
            Pose {
                position: [0.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
        let c1 = repo.commit(Some("1".into())).unwrap();
        repo.capture_annotation(&AnnotationCapture::new(
            "b",
            Pose {
                position: [1.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
        let c2 = repo.commit(Some("2".into())).unwrap();
        let report = verify_root_transition(repo.store(), &c2.root_cid).unwrap();
        assert!(report.ok, "{:?}", report.findings);
        assert_eq!(c2.previous_root, Some(c1.root_cid));
    }
}
