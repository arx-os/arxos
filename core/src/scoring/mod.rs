//! Contributor scoring (DePIN oracle input on the data plane).
//!
//! # Economic role
//!
//! Scoring attributes contributions under a root and produces **points** /
//! reputation-style aggregates. Settlement is **fiat** (not tokens): ops may
//! use scores later to pay contributors in fiat. This module never embeds
//! money in the CAS. See
//! [`ADR-001`](../../../docs/architecture/ADR-001-fiat-settled-depin.md).
//!
//! # Determinism
//!
//! Given the same `(store contents, root_cid, policy_version, weights)`,
//! [`score_root`] / [`score_contributions`] produce equal reports (stable
//! contributor ordering). There are no network, clock, or chain side effects.
//!
//! # Safety
//!
//! **Diagnostic only** (type-count weights). Do not use as a payment basis
//! until multi-signal quality scoring is intentional product work.
//!
//! # Future scoring extensions (data plane only)
//!
//! - Richer versioned [`ScoringPolicy`] tables
//! - Multi-dimension fields on [`ScoreReport`] (depth, coverage, review, …)

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use crate::cid::Cid;
use crate::crypto::PublicKey;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectBody, ObjectType};
use crate::root::RootBody;
use crate::store::ObjectStore;

/// Policy version embedded in every report for offline replay.
///
/// Bump when weight tables or aggregation rules change in a breaking way.
pub const DEFAULT_POLICY_VERSION: u32 = 1;

/// One attributed contribution unit (usually a signed object or root).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Contribution {
    pub cid: Cid,
    pub object_type: ObjectType,
    pub author: Option<PublicKey>,
    pub created: u64,
    /// True when the object signature verifies.
    pub signature_valid: bool,
    /// Optional device id from provenance linkage.
    pub device_id: Option<String>,
}

/// Aggregate score for a contributor (public key or anonymous bucket).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ContributorScore {
    pub author: Option<String>,
    pub objects: u64,
    pub roots: u64,
    pub annotations: u64,
    pub point_cloud_chunks: u64,
    pub spaces: u64,
    pub signed_valid: u64,
    pub signed_invalid: u64,
    /// Weighted score (see [`score_contributions`]).
    ///
    /// Treated as **points** for diagnostics; not a fiat amount.
    pub score: f64,
}

/// Full scoring report for a root (or explicit object set).
///
/// Future multi-dimension signals may extend this under a new `policy_version`
/// without embedding money fields.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScoreReport {
    /// Scoring policy version used to produce this report.
    pub policy_version: u32,
    pub building_id: String,
    pub root_cid: Option<String>,
    pub total_objects: u64,
    /// Aggregate points (diagnostic; not fiat).
    pub total_score: f64,
    pub contributors: Vec<ContributorScore>,
    /// Per-object contributions (for attribution dumps).
    pub contributions: Vec<Contribution>,
}

/// Weight table for scoring (tunable; versioned via [`ScoreReport::policy_version`]).
///
/// Current defaults are type-count heuristics only — **not** payment-grade.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScoreWeights {
    pub annotation: f64,
    pub space: f64,
    pub point_cloud_chunk: f64,
    pub floor: f64,
    pub building: f64,
    pub root: f64,
    pub other: f64,
    /// Multiplier applied when signature verifies.
    pub signed_bonus: f64,
}

impl Default for ScoreWeights {
    fn default() -> Self {
        Self {
            annotation: 1.0,
            space: 3.0,
            point_cloud_chunk: 5.0,
            floor: 2.0,
            building: 1.0,
            root: 0.5,
            other: 0.25,
            signed_bonus: 1.25,
        }
    }
}

/// Versioned scoring policy (weights + metadata).
///
/// Expand with additional signal coefficients without changing the pure
/// function shape: `score_*(…, &ScoringPolicy)`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScoringPolicy {
    pub version: u32,
    pub weights: ScoreWeights,
}

impl Default for ScoringPolicy {
    fn default() -> Self {
        Self {
            version: DEFAULT_POLICY_VERSION,
            weights: ScoreWeights::default(),
        }
    }
}

impl ScoringPolicy {
    pub fn with_weights(version: u32, weights: ScoreWeights) -> Self {
        Self { version, weights }
    }
}

fn weight_for(ty: ObjectType, w: &ScoreWeights) -> f64 {
    match ty {
        ObjectType::Annotation => w.annotation,
        ObjectType::Space => w.space,
        ObjectType::PointCloudChunk => w.point_cloud_chunk,
        ObjectType::Floor => w.floor,
        ObjectType::Building => w.building,
        ObjectType::Root => w.root,
        _ => w.other,
    }
}

/// Attribute a single object.
pub fn attribute_object(cid: Cid, obj: &Object) -> Contribution {
    let signature_valid = obj.header.signature.is_some() && obj.verify_signature().is_ok();
    let device_id = if let ObjectBody::Provenance(p) = &obj.body {
        p.properties.get("device_id").cloned()
    } else {
        None
    };
    Contribution {
        cid,
        object_type: obj.header.object_type,
        author: obj.header.author,
        created: obj.header.created,
        signature_valid,
        device_id,
    }
}

/// Score contributions under a root (includes root object set members present in store).
///
/// Uses [`ScoringPolicy::default`] (`policy_version` = [`DEFAULT_POLICY_VERSION`]).
pub fn score_root(
    store: &ObjectStore,
    root_cid: &Cid,
    weights: &ScoreWeights,
) -> Result<ScoreReport> {
    score_root_with_policy(
        store,
        root_cid,
        &ScoringPolicy {
            version: DEFAULT_POLICY_VERSION,
            weights: weights.clone(),
        },
    )
}

/// Score a root with an explicit versioned policy.
pub fn score_root_with_policy(
    store: &ObjectStore,
    root_cid: &Cid,
    policy: &ScoringPolicy,
) -> Result<ScoreReport> {
    let root_obj = store.get(root_cid)?;
    let root = RootBody::from_object(&root_obj)?;
    let mut cids: BTreeSet<Cid> = root.materialize_active_objects(store)?;
    cids.insert(*root_cid);
    score_cids_with_policy(
        store,
        cids,
        Some(root_cid.to_string()),
        root.building_id.to_string(),
        policy,
    )
}

/// Score an arbitrary set of CIDs with default policy version and given weights.
pub fn score_cids(
    store: &ObjectStore,
    cids: impl IntoIterator<Item = Cid>,
    root_cid: Option<String>,
    building_id: String,
    weights: &ScoreWeights,
) -> Result<ScoreReport> {
    score_cids_with_policy(
        store,
        cids,
        root_cid,
        building_id,
        &ScoringPolicy {
            version: DEFAULT_POLICY_VERSION,
            weights: weights.clone(),
        },
    )
}

/// Score an arbitrary set of CIDs with an explicit policy.
pub fn score_cids_with_policy(
    store: &ObjectStore,
    cids: impl IntoIterator<Item = Cid>,
    root_cid: Option<String>,
    building_id: String,
    policy: &ScoringPolicy,
) -> Result<ScoreReport> {
    let mut contributions = Vec::new();
    for cid in cids {
        match store.get(&cid) {
            Ok(obj) => contributions.push(attribute_object(cid, &obj)),
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        }
    }
    Ok(score_contributions_with_policy(
        contributions,
        root_cid,
        building_id,
        policy,
    ))
}

/// Pure scoring over already-attributed contributions (default policy version).
pub fn score_contributions(
    contributions: Vec<Contribution>,
    root_cid: Option<String>,
    building_id: String,
    weights: &ScoreWeights,
) -> ScoreReport {
    score_contributions_with_policy(
        contributions,
        root_cid,
        building_id,
        &ScoringPolicy {
            version: DEFAULT_POLICY_VERSION,
            weights: weights.clone(),
        },
    )
}

/// Pure scoring over already-attributed contributions with versioned policy.
///
/// Deterministic: stable sort of contributors by score desc, then author id.
pub fn score_contributions_with_policy(
    contributions: Vec<Contribution>,
    root_cid: Option<String>,
    building_id: String,
    policy: &ScoringPolicy,
) -> ScoreReport {
    let weights = &policy.weights;
    let mut by_author: BTreeMap<String, ContributorScore> = BTreeMap::new();
    let mut total_score = 0.0;

    for c in &contributions {
        let key = c
            .author
            .map(|a| a.to_string())
            .unwrap_or_else(|| "anonymous".into());
        let entry = by_author.entry(key.clone()).or_insert_with(|| ContributorScore {
            author: if key == "anonymous" {
                None
            } else {
                Some(key.clone())
            },
            objects: 0,
            roots: 0,
            annotations: 0,
            point_cloud_chunks: 0,
            spaces: 0,
            signed_valid: 0,
            signed_invalid: 0,
            score: 0.0,
        });
        entry.objects += 1;
        match c.object_type {
            ObjectType::Root => entry.roots += 1,
            ObjectType::Annotation => entry.annotations += 1,
            ObjectType::PointCloudChunk => entry.point_cloud_chunks += 1,
            ObjectType::Space => entry.spaces += 1,
            _ => {}
        }
        if c.author.is_some() {
            if c.signature_valid {
                entry.signed_valid += 1;
            } else {
                entry.signed_invalid += 1;
            }
        }
        let mut s = weight_for(c.object_type, weights);
        if c.signature_valid {
            s *= weights.signed_bonus;
        }
        entry.score += s;
        total_score += s;
    }

    let mut contributors: Vec<_> = by_author.into_values().collect();
    contributors.sort_by(|a, b| {
        b.score
            .partial_cmp(&a.score)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| {
                a.author
                    .as_deref()
                    .unwrap_or("")
                    .cmp(b.author.as_deref().unwrap_or(""))
            })
    });

    ScoreReport {
        policy_version: policy.version,
        building_id,
        root_cid,
        total_objects: contributions.len() as u64,
        total_score,
        contributors,
        contributions,
    }
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
    fn score_prefers_signed_annotations() {
        let dir = tempdir().unwrap();
        let kp = Keypair::generate();
        let mut repo = BuildingRepository::init(
            dir.path(),
            Some("Scoring".into()),
            Some(kp.clone()),
        )
        .unwrap();
        repo.capture_annotation(&AnnotationCapture::new(
            "note",
            Pose {
                position: [1.0, 1.0, 1.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
        let commit = repo.commit(Some("c".into())).unwrap();
        let report = score_root(repo.store(), &commit.root_cid, &ScoreWeights::default()).unwrap();
        assert_eq!(report.policy_version, DEFAULT_POLICY_VERSION);
        assert!(report.total_score > 0.0);
        assert!(!report.contributors.is_empty());
        assert!(report.contributors[0].signed_valid >= 1);
    }

    #[test]
    fn score_contributions_is_deterministic() {
        let kp = Keypair::generate();
        let author = kp.public_key();
        let cids: Vec<Cid> = (0..3)
            .map(|i| {
                let mut bytes = [0u8; 32];
                bytes[0] = i;
                Cid::from_bytes(bytes)
            })
            .collect();

        let make = || {
            vec![
                Contribution {
                    cid: cids[0],
                    object_type: ObjectType::Annotation,
                    author: Some(author),
                    created: 100,
                    signature_valid: true,
                    device_id: None,
                },
                Contribution {
                    cid: cids[1],
                    object_type: ObjectType::Space,
                    author: Some(author),
                    created: 101,
                    signature_valid: false,
                    device_id: None,
                },
                Contribution {
                    cid: cids[2],
                    object_type: ObjectType::Annotation,
                    author: None,
                    created: 102,
                    signature_valid: false,
                    device_id: None,
                },
            ]
        };

        let policy = ScoringPolicy::default();
        let a = score_contributions_with_policy(
            make(),
            Some("root".into()),
            "b1".into(),
            &policy,
        );
        let b = score_contributions_with_policy(
            make(),
            Some("root".into()),
            "b1".into(),
            &policy,
        );
        assert_eq!(a, b);
        assert_eq!(a.policy_version, DEFAULT_POLICY_VERSION);
        assert_eq!(a.contributors.len(), 2); // author + anonymous
        // Higher score first
        assert!(a.contributors[0].score >= a.contributors[1].score);
    }

    #[test]
    fn score_root_twice_matches() {
        let dir = tempdir().unwrap();
        let kp = Keypair::generate();
        let mut repo =
            BuildingRepository::init(dir.path(), Some("Det".into()), Some(kp.clone())).unwrap();
        repo.capture_annotation(&AnnotationCapture::new(
            "a",
            Pose {
                position: [0.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ))
        .unwrap();
        let commit = repo.commit(Some("c".into())).unwrap();
        let policy = ScoringPolicy::default();
        let r1 = score_root_with_policy(repo.store(), &commit.root_cid, &policy).unwrap();
        let r2 = score_root_with_policy(repo.store(), &commit.root_cid, &policy).unwrap();
        assert_eq!(r1, r2);
    }

    #[test]
    fn custom_policy_version_is_recorded() {
        let report = score_contributions_with_policy(
            vec![],
            None,
            "b".into(),
            &ScoringPolicy::with_weights(42, ScoreWeights::default()),
        );
        assert_eq!(report.policy_version, 42);
    }
}
