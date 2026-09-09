//! Geometric fuse of two versions of the same entity.
//!
//! ```text
//! fuse(old, new) -> Object
//! ```
//!
//! Never mutates `old` or `new`. The result is a new unsigned object (the
//! commit path re-signs when a controller keypair is present).
//!
//! ## Weights
//!
//! \( w = 1/\sigma^2 \) when \(\sigma\) is finite and \(> 0\); otherwise \(w = 0\).
//! Combined 1σ (millimetres):
//!
//! \[
//! \sigma' = \bigl(\sum w\bigr)^{-1/2}
//! \]
//!
//! Clamped to `(0, 1e9]`. If both weights are 0, the `new` pose is kept and
//! `support_count` still increases.
//!
//! ## Support
//!
//! `support_count = old.effective.max(1) + new.effective.max(1)` when blending.
//! Kind-mismatch does not blend: a deterministic winner is returned unchanged.
//!
//! Pairwise fold of three observations is associative for position and \(\sigma\)
//! because combined weight is \(w_a+w_b\). Sequential commits (A then A') vs one
//! commit that stages both therefore agree on pose when created-order matches.

use std::collections::{BTreeMap, BTreeSet};

use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::entity::entity_id_of;
use crate::error::{Error, Result};
use crate::object::{
    canonicalize_extent, Object, ObjectBody, ObjectType, Pose, SCHEMA_VERSION,
};
use crate::store::{ObjectRead, ObjectWrite};

/// Cap on fused evidence CIDs.
pub const EVIDENCE_CAP: usize = 16;
/// Upper clamp for combined \(\sigma\) (millimetres).
pub const SIGMA_MAX_MM: f64 = 1e9;

/// Fuse two versions of the same physical entity.
///
/// Callers must pass the objects that `old_cid` / `new_cid` name. CIDs are
/// used only for kind-mismatch tie-breaks.
pub fn fuse(old: &Object, old_cid: Cid, new: &Object, new_cid: Cid) -> Result<Object> {
    if !kinds_match(old, new) {
        return Ok(mismatch_winner(old, old_cid, new, new_cid).clone());
    }
    blend(old, new)
}

fn kinds_match(a: &Object, b: &Object) -> bool {
    match (a.kind_family(), b.kind_family()) {
        (Some((ta, ka)), Some((tb, kb))) => {
            if ta != tb {
                return false;
            }
            match (ka, kb) {
                (Some(x), Some(y)) => x.eq_ignore_ascii_case(y),
                _ => true,
            }
        }
        _ => a.header.object_type == b.header.object_type,
    }
}

fn mismatch_winner<'a>(old: &'a Object, old_cid: Cid, new: &'a Object, new_cid: Cid) -> &'a Object {
    let so = old.effective_support_count();
    let sn = new.effective_support_count();
    if so != sn {
        return if so > sn { old } else { new };
    }
    let sig_o = old.sigma_mm().unwrap_or(f64::INFINITY);
    let sig_n = new.sigma_mm().unwrap_or(f64::INFINITY);
    if (sig_o - sig_n).abs() > 1e-12 {
        return if sig_o < sig_n { old } else { new };
    }
    if old.header.created != new.header.created {
        return if old.header.created > new.header.created {
            old
        } else {
            new
        };
    }
    if old_cid >= new_cid {
        old
    } else {
        new
    }
}

fn fuse_weight(sigma_mm: Option<f64>) -> f64 {
    match sigma_mm {
        Some(s) if s.is_finite() && s > 0.0 => 1.0 / (s * s),
        _ => 0.0,
    }
}

fn combined_sigma_mm(w_sum: f64) -> Option<f64> {
    if w_sum <= 0.0 {
        return None;
    }
    let s = (1.0 / w_sum).sqrt();
    Some(s.clamp(f64::MIN_POSITIVE, SIGMA_MAX_MM))
}

fn weighted_mean_pose(old: &Pose, w_old: f64, new: &Pose, w_new: f64) -> Result<Pose> {
    if w_old == 0.0 && w_new == 0.0 {
        let mut p = new.clone();
        p.canonicalize()?;
        return Ok(p);
    }
    if w_old == 0.0 {
        let mut p = new.clone();
        p.canonicalize()?;
        return Ok(p);
    }
    if w_new == 0.0 {
        let mut p = old.clone();
        p.canonicalize()?;
        return Ok(p);
    }
    let w = w_old + w_new;
    let position = [
        (w_old * old.position[0] + w_new * new.position[0]) / w,
        (w_old * old.position[1] + w_new * new.position[1]) / w,
        (w_old * old.position[2] + w_new * new.position[2]) / w,
    ];
    let orientation = weighted_mean_quat(old.orientation, w_old, new.orientation, w_new);
    let mut pose = Pose {
        position,
        orientation,
    };
    pose.canonicalize()?;
    Ok(pose)
}

fn weighted_mean_quat(q_old: [f64; 4], w_old: f64, mut q_new: [f64; 4], w_new: f64) -> [f64; 4] {
    let dot = q_old[0] * q_new[0] + q_old[1] * q_new[1] + q_old[2] * q_new[2] + q_old[3] * q_new[3];
    if dot < 0.0 {
        for v in &mut q_new {
            *v = -*v;
        }
    }
    let mut acc = [
        w_old * q_old[0] + w_new * q_new[0],
        w_old * q_old[1] + w_new * q_new[1],
        w_old * q_old[2] + w_new * q_new[2],
        w_old * q_old[3] + w_new * q_new[3],
    ];
    let n = (acc[0] * acc[0] + acc[1] * acc[1] + acc[2] * acc[2] + acc[3] * acc[3]).sqrt();
    if n > 0.0 {
        for v in &mut acc {
            *v /= n;
        }
    } else {
        acc = q_new;
    }
    acc
}

fn fuse_extent(old: Option<[f64; 3]>, w_old: f64, new: Option<[f64; 3]>, w_new: f64) -> Result<Option<[f64; 3]>> {
    match (old, new) {
        (Some(a), Some(b)) => {
            if w_old == 0.0 && w_new == 0.0 {
                let mut e = b;
                canonicalize_extent(&mut e)?;
                return Ok(Some(e));
            }
            if w_old == 0.0 {
                let mut e = b;
                canonicalize_extent(&mut e)?;
                return Ok(Some(e));
            }
            if w_new == 0.0 {
                let mut e = a;
                canonicalize_extent(&mut e)?;
                return Ok(Some(e));
            }
            let w = w_old + w_new;
            let mut e = [
                (w_old * a[0] + w_new * b[0]) / w,
                (w_old * a[1] + w_new * b[1]) / w,
                (w_old * a[2] + w_new * b[2]) / w,
            ];
            canonicalize_extent(&mut e)?;
            Ok(Some(e))
        }
        (Some(a), None) => {
            let mut e = a;
            canonicalize_extent(&mut e)?;
            Ok(Some(e))
        }
        (None, Some(b)) => {
            let mut e = b;
            canonicalize_extent(&mut e)?;
            Ok(Some(e))
        }
        (None, None) => Ok(None),
    }
}

fn merge_evidence(old: &[Cid], new: &[Cid]) -> Vec<Cid> {
    let mut out = Vec::new();
    for c in new.iter().chain(old.iter()) {
        if !out.contains(c) {
            out.push(*c);
        }
        if out.len() == EVIDENCE_CAP {
            break;
        }
    }
    out.sort();
    out
}

fn blend(old: &Object, new: &Object) -> Result<Object> {
    let w_old = fuse_weight(old.sigma_mm());
    let w_new = fuse_weight(new.sigma_mm());
    let fused_pose = match (old.pose(), new.pose()) {
        (Some(po), Some(pn)) => Some(weighted_mean_pose(po, w_old, pn, w_new)?),
        (None, Some(pn)) => {
            let mut p = pn.clone();
            p.canonicalize()?;
            Some(p)
        }
        (Some(po), None) => {
            let mut p = po.clone();
            p.canonicalize()?;
            Some(p)
        }
        (None, None) => None,
    };
    let fused_extent = fuse_extent(old.extent(), w_old, new.extent(), w_new)?;
    let fused_sigma = match (old.sigma_mm(), new.sigma_mm()) {
        (None, None) => None,
        (Some(s), None) if w_new == 0.0 => Some(s),
        (None, Some(s)) if w_old == 0.0 => Some(s),
        _ => combined_sigma_mm(w_old + w_new).or(new.sigma_mm()).or(old.sigma_mm()),
    };
    let support = old.effective_support_count().max(1) + new.effective_support_count().max(1);
    let evidence = merge_evidence(old.evidence(), new.evidence());
    let created = old.header.created.max(new.header.created);

    let mut fused = new.clone();
    fused.header.author = None;
    fused.header.signature = None;
    fused.header.schema_version = SCHEMA_VERSION;
    fused.header.created = created;

    apply_fused_fields(
        &mut fused,
        fused_pose,
        fused_extent,
        fused_sigma,
        support,
        evidence,
        old,
    )?;
    fused.body.canonicalize_geometry()?;
    Ok(fused)
}

fn apply_fused_fields(
    fused: &mut Object,
    pose: Option<Pose>,
    extent: Option<[f64; 3]>,
    sigma_mm: Option<f64>,
    support: u32,
    evidence: Vec<Cid>,
    old: &Object,
) -> Result<()> {
    match &mut fused.body {
        ObjectBody::Surface(b) => {
            if pose.is_some() {
                b.pose = pose;
            }
            b.extent = extent;
            b.sigma_mm = sigma_mm;
            b.support_count = support;
            b.evidence = evidence;
        }
        ObjectBody::Opening(b) => {
            if pose.is_some() {
                b.pose = pose;
            }
            b.extent = extent;
            b.sigma_mm = sigma_mm;
            b.support_count = support;
            b.evidence = evidence;
            if b.host_entity.is_none() {
                b.host_entity = old.host_entity().cloned();
            }
            if b.host_surface.is_none() {
                if let ObjectBody::Opening(o) = &old.body {
                    b.host_surface = o.host_surface;
                }
            }
        }
        ObjectBody::Equipment(b) => {
            if pose.is_some() {
                b.pose = pose;
            }
            b.extent = extent;
            b.sigma_mm = sigma_mm;
            b.support_count = support;
            b.evidence = evidence;
        }
        ObjectBody::Run(b) => {
            if pose.is_some() {
                b.pose = pose;
            }
            b.extent = extent;
            b.sigma_mm = sigma_mm;
            b.support_count = support;
            b.evidence = evidence;
        }
        _ => {
            if let Some(p) = pose {
                if let Some(slot) = fused.pose_mut() {
                    *slot = p;
                }
            }
        }
    }
    Ok(())
}

/// Fuse every `EntityId` that has two or more versions in `cids`.
///
/// Versions of one id are folded in `(created, CID)` order. The fused object
/// is `put` (never mutating inputs). Objects without `entity_id` are kept.
///
/// When `sign` is `Some`, the fused leaf is signed with that controller key.
pub fn fuse_active_set<W: ObjectWrite + ?Sized>(
    store: &W,
    cids: &BTreeSet<Cid>,
    sign: Option<&Keypair>,
) -> Result<BTreeSet<Cid>> {
    let mut by_entity: BTreeMap<crate::entity::EntityId, Vec<(Cid, Object)>> = BTreeMap::new();
    let mut kept: BTreeSet<Cid> = BTreeSet::new();

    for cid in cids {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => {
                kept.insert(*cid);
                continue;
            }
            Err(e) => return Err(e),
        };
        match entity_id_of(&obj).cloned() {
            Some(eid) if is_fusable(obj.header.object_type) => {
                by_entity.entry(eid).or_default().push((*cid, obj));
            }
            Some(_) | None => {
                // Spaces / floors / etc. collapse by created; they are not fused.
                kept.insert(*cid);
            }
        }
    }

    for (_eid, mut versions) in by_entity {
        if versions.len() == 1 {
            kept.insert(versions[0].0);
            continue;
        }
        versions.sort_by(|a, b| {
            a.1.header
                .created
                .cmp(&b.1.header.created)
                .then_with(|| a.0.cmp(&b.0))
        });
        let orig: BTreeSet<Cid> = versions.iter().map(|(c, _)| *c).collect();
        let (mut acc_cid, mut acc) = versions.remove(0);
        for (cid, obj) in versions {
            acc = fuse(&acc, acc_cid, &obj, cid)?;
            acc_cid = acc.cid()?;
        }
        if orig.contains(&acc_cid) {
            // Kind-mismatch supersede: keep the winning CID, do not re-sign.
            kept.insert(acc_cid);
        } else {
            if let Some(kp) = sign {
                acc.sign(kp)?;
            }
            kept.insert(store.put(&acc)?);
        }
    }
    Ok(kept)
}

/// Convenience: fuse using [`ObjectRead`] only for tests that already `put`.
pub fn fuse_from_store<R: ObjectRead + ?Sized>(
    store: &R,
    old_cid: Cid,
    new_cid: Cid,
) -> Result<Object> {
    let old = store.get(&old_cid)?;
    let new = store.get(&new_cid)?;
    fuse(&old, old_cid, &new, new_cid)
}

/// Object types that participate in geometric fuse.
pub fn is_fusable(ty: ObjectType) -> bool {
    matches!(
        ty,
        ObjectType::Surface | ObjectType::Opening | ObjectType::Equipment | ObjectType::Run
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::entity::EntityId;
    use crate::object::{ObjectBody, SurfaceBody};
    use crate::store::ObjectStore;
    use tempfile::tempdir;

    fn wall(eid: &str, created: u64, pos: [f64; 3], sigma: Option<f64>, support: u32) -> Object {
        Object::new_with_created(
            ObjectBody::Surface(SurfaceBody {
                entity_id: Some(EntityId::from(eid.to_string())),
                space: None,
                pose: Some(Pose {
                    position: pos,
                    orientation: [0.0, 0.0, 0.0, 1.0],
                }),
                bounds: None,
                surface_kind: Some("wall".into()),
                extent: Some([4.0, 2.5, 0.15]),
                sigma_mm: sigma,
                support_count: support,
                evidence: Vec::new(),
                properties: Default::default(),
            }),
            created,
        )
    }

    #[test]
    fn tighter_sigma_pulls_pose() {
        let a = wall("e1", 1, [0.0, 0.0, 0.0], Some(40.0), 1);
        let b = wall("e1", 2, [0.10, 0.0, 0.0], Some(20.0), 1);
        let ca = a.cid().unwrap();
        let cb = b.cid().unwrap();
        let f = fuse(&a, ca, &b, cb).unwrap();
        let p = f.pose().unwrap().position[0];
        // Weights 1/1600 and 1/400 → mean = 0.08
        assert!((p - 0.08).abs() < 1e-9, "got {p}");
        assert_eq!(f.effective_support_count(), 2);
        assert!(f.header.signature.is_none());
    }

    #[test]
    fn legacy_unweighted_keeps_new_pose() {
        let old = wall("e1", 1, [0.0, 0.0, 0.0], None, 0);
        let new = wall("e1", 2, [0.05, 0.0, 0.0], Some(20.0), 1);
        let f = fuse(&old, old.cid().unwrap(), &new, new.cid().unwrap()).unwrap();
        assert!((f.pose().unwrap().position[0] - 0.05).abs() < 1e-12);
        assert!(f.effective_support_count() >= 2);
    }

    #[test]
    fn kind_mismatch_does_not_blend() {
        let wall_obj = wall("e1", 1, [0.0, 0.0, 0.0], Some(40.0), 1);
        let mut eq = Object::new_with_created(
            ObjectBody::Equipment(crate::object::EquipmentBody {
                entity_id: Some(EntityId::from("e1".to_string())),
                name: Some("box".into()),
                equipment_kind: Some("box".into()),
                pose: Some(Pose {
                    position: [9.0, 0.0, 0.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                }),
                system: None,
                extent: Some([1.0, 1.0, 1.0]),
                sigma_mm: Some(50.0),
                support_count: 1,
                evidence: Vec::new(),
                properties: Default::default(),
            }),
            2,
        );
        // Equipment has lower support? both 1. Lower sigma is wall (40 < 50) so wall wins
        // if compared on sigma after equal support. created is newer for equipment.
        // Rules: higher support, then lower sigma, then newer created, then CID.
        // support equal, wall sigma 40 < 50 → wall wins (no blend).
        let f = fuse(
            &wall_obj,
            wall_obj.cid().unwrap(),
            &eq,
            eq.cid().unwrap(),
        )
        .unwrap();
        assert_eq!(f.header.object_type, ObjectType::Surface);
        assert!((f.pose().unwrap().position[0] - 0.0).abs() < 1e-12);

        // Higher support on equipment wins even with worse sigma.
        if let ObjectBody::Equipment(ref mut b) = eq.body {
            b.support_count = 5;
        }
        let f2 = fuse(
            &wall_obj,
            wall_obj.cid().unwrap(),
            &eq,
            eq.cid().unwrap(),
        )
        .unwrap();
        assert_eq!(f2.header.object_type, ObjectType::Equipment);
        let _ = eq;
    }

    #[test]
    fn identical_facts_identity_pose_support_increases() {
        let a = wall("e1", 1, [1.0, 0.0, 0.0], Some(40.0), 1);
        let b = wall("e1", 2, [1.0, 0.0, 0.0], Some(40.0), 1);
        let f = fuse(&a, a.cid().unwrap(), &b, b.cid().unwrap()).unwrap();
        assert!((f.pose().unwrap().position[0] - 1.0).abs() < 1e-12);
        assert_eq!(f.effective_support_count(), 2);
    }

    #[test]
    fn fuse_active_set_puts_new_cid() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let a = wall("e1", 1, [0.0, 0.0, 0.0], Some(40.0), 1);
        let b = wall("e1", 2, [0.10, 0.0, 0.0], Some(20.0), 1);
        let ca = store.put(&a).unwrap();
        let cb = store.put(&b).unwrap();
        let mut set = BTreeSet::new();
        set.insert(ca);
        set.insert(cb);
        let out = fuse_active_set(&store, &set, None).unwrap();
        assert_eq!(out.len(), 1);
        let fused_cid = *out.iter().next().unwrap();
        assert_ne!(fused_cid, ca);
        assert_ne!(fused_cid, cb);
        let fused = store.get(&fused_cid).unwrap();
        assert_eq!(fused.effective_support_count(), 2);
    }
}
