//! DePIN contribution attribution and off-chain scoring hooks.
//!
//! Economic signals can stay off-chain initially and later feed an on-chain
//! registry / rewards path. Scoring is **deterministic** given a store + root.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use crate::cid::Cid;
use crate::crypto::PublicKey;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectBody, ObjectType};
use crate::root::RootBody;
use crate::store::ObjectStore;

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
    pub score: f64,
}

/// Full scoring report for a root (or explicit object set).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScoreReport {
    pub building_id: String,
    pub root_cid: Option<String>,
    pub total_objects: u64,
    pub total_score: f64,
    pub contributors: Vec<ContributorScore>,
    /// Per-object contributions (for attribution dumps).
    pub contributions: Vec<Contribution>,
}

/// Weight table for off-chain scoring (tunable; not consensus-critical yet).
#[derive(Debug, Clone)]
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
pub fn score_root(
    store: &ObjectStore,
    root_cid: &Cid,
    weights: &ScoreWeights,
) -> Result<ScoreReport> {
    let root_obj = store.get(root_cid)?;
    let root = RootBody::from_object(&root_obj)?;
    let mut cids: BTreeSet<Cid> = root.objects.iter().copied().collect();
    cids.insert(*root_cid);
    score_cids(
        store,
        cids,
        Some(root_cid.to_string()),
        root.building_id.to_string(),
        weights,
    )
}

/// Score an arbitrary set of CIDs.
pub fn score_cids(
    store: &ObjectStore,
    cids: impl IntoIterator<Item = Cid>,
    root_cid: Option<String>,
    building_id: String,
    weights: &ScoreWeights,
) -> Result<ScoreReport> {
    let mut contributions = Vec::new();
    for cid in cids {
        match store.get(&cid) {
            Ok(obj) => contributions.push(attribute_object(cid, &obj)),
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        }
    }
    Ok(score_contributions(contributions, root_cid, building_id, weights))
}

/// Pure scoring over already-attributed contributions.
pub fn score_contributions(
    contributions: Vec<Contribution>,
    root_cid: Option<String>,
    building_id: String,
    weights: &ScoreWeights,
) -> ScoreReport {
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
        building_id,
        root_cid,
        total_objects: contributions.len() as u64,
        total_score,
        contributors,
        contributions,
    }
}

/// Build a registry-facing snapshot (BuildingId → official root + controllers).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RegistrySnapshot {
    pub building_id: String,
    pub official_root_cid: String,
    /// Controller public keys (hex with ed25519: prefix as Display).
    pub controllers: Vec<String>,
    pub object_count: u64,
    pub updated: u64,
}

/// Extract registry snapshot from a building root in the store.
pub fn registry_snapshot(store: &ObjectStore, root_cid: &Cid) -> Result<RegistrySnapshot> {
    let root_obj = store.get(root_cid)?;
    let root = RootBody::from_object(&root_obj)?;
    let mut controllers = Vec::new();
    for cid in &root.objects {
        if let Ok(obj) = store.get(cid) {
            if let ObjectBody::Building(b) = &obj.body {
                for k in &b.controller_keys {
                    controllers.push(k.to_string());
                }
            }
        }
    }
    for a in &root.authors {
        let s = a.public_key.to_string();
        if !controllers.contains(&s) {
            controllers.push(s);
        }
    }
    controllers.sort();
    controllers.dedup();
    Ok(RegistrySnapshot {
        building_id: root.building_id.to_string(),
        official_root_cid: root_cid.to_string(),
        controllers,
        object_count: root.objects.len() as u64,
        updated: root.timestamp,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::AnnotationCapture;
    use crate::object::{BuildingBody, BuildingId, Pose};
    use crate::repository::BuildingRepository;
    use crate::Keypair;
    use tempfile::tempdir;

    #[test]
    fn score_prefers_signed_annotations() {
        let dir = tempdir().unwrap();
        let kp = Keypair::generate();
        let mut repo =
            BuildingRepository::init(dir.path(), Some("Depin".into()), Some(kp.clone())).unwrap();
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
        assert!(report.total_score > 0.0);
        assert!(!report.contributors.is_empty());
        assert!(report.contributors[0].signed_valid >= 1);
        let snap = registry_snapshot(repo.store(), &commit.root_cid).unwrap();
        assert_eq!(snap.building_id, repo.building_id().to_string());
        assert!(!snap.controllers.is_empty());
        let _ = BuildingBody {
            building_id: BuildingId::new(),
            name: None,
            controller_keys: vec![],
            properties: Default::default(),
        };
    }
}
