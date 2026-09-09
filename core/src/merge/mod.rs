//! Merge concurrent building roots (three-way + entity collapse + annotation rules).
//!
//! Rules:
//! 1. **Three-way set merge** relative to the nearest common ancestor on the
//!    `previous_root ∪ merge_parents` DAG (not naive union). Concurrent
//!    removals are preserved; concurrent adds are unioned. If one tip is a
//!    DAG ancestor of the other, the descendant wins (fast-forward).
//! 2. **Entity collapse**: at most one version CID per [`crate::entity::EntityId`].
//! 3. **Building collapse**: at most one Building object per `building_id`
//!    (controller rotation produces successive Building CIDs).
//! 4. **Annotation proximity dedupe**: nearby identical text → keep newer.
//! 5. **Annotation conflict keep-both**: nearby different text → keep both.
//! 6. Spatial index is **rebuilt** after merge (not merged node-by-node).
//! 7. With [`MergeReplica`], a remote parent whose authors are not local
//!    controllers is rejected (Authorization). Untrusted objects cannot enter
//!    the merged set. `plan_merge` remains a dry-run without this gate.

use std::collections::{BTreeMap, BTreeSet, VecDeque};

use crate::capture::pose_distance;
use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::entity::collapse_active_set;
use crate::error::{Error, Result};
use crate::fuse::fuse_active_set;
use crate::object::{BuildingId, Object, ObjectBody, ObjectType, Pose};
use crate::root::{resolve_controller_keys, RootBody, RootBuilder};
use crate::spatial;
use crate::store::{ObjectRead, ObjectWrite};

/// Replica view for merge: local head is trusted; a remote parent whose
/// authors were never controllers on this replica cannot supply **objects**
/// (not only the winning Building).
///
/// Concurrent honest devices remain eligible, including a key Alice later
/// dropped (`controller_add_survives_sync_and_enforce`). Ancestry is not
/// required here — that is adopt's job. Winning Building collapse still uses
/// the *current* local controller set.
#[derive(Debug, Clone)]
pub struct MergeReplica {
    pub local_head: Cid,
    pub local_active: BTreeSet<Cid>,
}

/// Distance under which annotations with identical text are considered duplicates.
pub const ANNOTATION_DEDUP_M: f64 = 0.35;

/// Result of merging two roots.
#[derive(Debug, Clone)]
pub struct MergeResult {
    pub root_cid: Cid,
    pub object_count: u64,
    pub kept: u64,
    pub deduped_annotations: u64,
    pub spatial_index_root: Option<Cid>,
    pub parents: (Cid, Cid),
}

/// Load a root body by object CID.
pub fn load_root<R: ObjectRead + ?Sized>(store: &R, root_cid: &Cid) -> Result<(Object, RootBody)> {
    let obj = store.get(root_cid)?;
    let body = RootBody::from_object(&obj)?.clone();
    Ok((obj, body))
}

fn normalize_text(s: &str) -> String {
    s.split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .to_lowercase()
}

struct AnnMeta {
    cid: Cid,
    text: String,
    pose: Option<Pose>,
    created: u64,
}

fn collect_annotations<R: ObjectRead + ?Sized>(
    store: &R,
    cids: &BTreeSet<Cid>,
) -> Result<Vec<AnnMeta>> {
    let mut out = Vec::new();
    for cid in cids {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        };
        if obj.header.object_type != ObjectType::Annotation {
            continue;
        }
        if let ObjectBody::Annotation(a) = &obj.body {
            out.push(AnnMeta {
                cid: *cid,
                text: a.text.clone().unwrap_or_default(),
                pose: a.pose.clone(),
                created: obj.header.created,
            });
        }
    }
    Ok(out)
}

/// Apply annotation dedupe rules; returns CIDs to drop.
pub fn annotation_dedupe_drops<R: ObjectRead + ?Sized>(
    store: &R,
    objects: &BTreeSet<Cid>,
) -> Result<BTreeSet<Cid>> {
    let anns = collect_annotations(store, objects)?;
    let mut drop = BTreeSet::new();
    for i in 0..anns.len() {
        if drop.contains(&anns[i].cid) {
            continue;
        }
        for j in (i + 1)..anns.len() {
            if drop.contains(&anns[j].cid) {
                continue;
            }
            let (Some(pi), Some(pj)) = (&anns[i].pose, &anns[j].pose) else {
                // Pose-less annotations are not at the origin; skip distance dedupe.
                continue;
            };
            let d = pose_distance(pi, pj);
            if d > ANNOTATION_DEDUP_M {
                continue;
            }
            let ti = normalize_text(&anns[i].text);
            let tj = normalize_text(&anns[j].text);
            if ti.is_empty() || ti != tj {
                // Different text → keep both (conflict keep-both).
                continue;
            }
            // Same text nearby → keep newer (then higher CID).
            let (keep, lose) = if anns[i].created > anns[j].created
                || (anns[i].created == anns[j].created && anns[i].cid > anns[j].cid)
            {
                (anns[i].cid, anns[j].cid)
            } else {
                (anns[j].cid, anns[i].cid)
            };
            let _ = keep;
            drop.insert(lose);
        }
    }
    Ok(drop)
}

/// Ancestors of `tip` including `tip`, walking `previous_root ∪ merge_parents`.
///
/// Order is BFS from the tip so the first intersection with another tip's
/// ancestor set is a nearest common ancestor on the merge DAG.
fn ancestor_dag<R: ObjectRead + ?Sized>(store: &R, tip: Cid) -> Result<Vec<Cid>> {
    let mut order = Vec::new();
    let mut visited = BTreeSet::new();
    let mut queue = VecDeque::from([tip]);
    while let Some(cid) = queue.pop_front() {
        if !visited.insert(cid) {
            continue;
        }
        order.push(cid);
        let (_, body) = load_root(store, &cid)?;
        if let Some(prev) = body.previous_root {
            queue.push_back(prev);
        }
        for p in &body.merge_parents {
            queue.push_back(*p);
        }
    }
    Ok(order)
}

/// Nearest common ancestor of two root tips on the merge DAG.
///
/// Returns `None` only when histories are disjoint (no shared ancestor).
pub fn find_common_ancestor<R: ObjectRead + ?Sized>(
    store: &R,
    root_a: Cid,
    root_b: Cid,
) -> Result<Option<Cid>> {
    let set_a: BTreeSet<Cid> = ancestor_dag(store, root_a)?.into_iter().collect();
    for cid in ancestor_dag(store, root_b)? {
        if set_a.contains(&cid) {
            return Ok(Some(cid));
        }
    }
    Ok(None)
}

/// True if `ancestor` appears on the merge DAG of `desc` (inclusive).
fn is_ancestor_of<R: ObjectRead + ?Sized>(store: &R, ancestor: Cid, desc: Cid) -> Result<bool> {
    Ok(ancestor_dag(store, desc)?.contains(&ancestor))
}

/// Three-way object-set merge of two concurrent tips.
///
/// Given base B (LCA):
/// `result = (active_base ∪ (active_a − active_base) ∪ (active_b − active_base))
///           − (active_base − active_a) − (active_base − active_b)`
///
/// Equivalently: start from base, apply both sides' additions, then both sides'
/// removals. Concurrent remove+add of different CIDs composes correctly;
/// concurrent remove of the same CID is idempotent.
pub fn three_way_object_set(
    active_base: &BTreeSet<Cid>,
    active_a: &BTreeSet<Cid>,
    active_b: &BTreeSet<Cid>,
) -> BTreeSet<Cid> {
    let adds_a: BTreeSet<Cid> = active_a.difference(active_base).copied().collect();
    let adds_b: BTreeSet<Cid> = active_b.difference(active_base).copied().collect();
    let rems_a: BTreeSet<Cid> = active_base.difference(active_a).copied().collect();
    let rems_b: BTreeSet<Cid> = active_base.difference(active_b).copied().collect();

    let mut result = active_base.clone();
    result.extend(adds_a);
    result.extend(adds_b);
    for r in rems_a.iter().chain(rems_b.iter()) {
        result.remove(r);
    }
    result
}

/// Building CIDs present in `cids`. Missing objects are skipped.
fn building_cids_in<R: ObjectRead + ?Sized>(
    store: &R,
    cids: &BTreeSet<Cid>,
) -> Result<BTreeSet<Cid>> {
    let mut out = BTreeSet::new();
    for cid in cids {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => continue,
            Err(e) => return Err(e),
        };
        if matches!(obj.body, ObjectBody::Building(_)) {
            out.insert(*cid);
        }
    }
    Ok(out)
}

fn authors_are_local_controllers(root: &RootBody, local_keys: &[crate::crypto::PublicKey]) -> bool {
    !root.authors.is_empty()
        && root
            .authors
            .iter()
            .all(|a| local_keys.iter().any(|k| k == &a.public_key))
}

/// Controller keys this replica has ever trusted: current Building, plus every
/// Building on the local `previous_root` chain. A concurrent tip signed by a
/// key Alice later dropped is still mergeable; Mallory never appears here.
fn replica_authorized_keys<R: ObjectRead + ?Sized>(
    store: &R,
    building_id: &BuildingId,
    replica: &MergeReplica,
) -> Result<Vec<crate::crypto::PublicKey>> {
    let mut keys = resolve_controller_keys(store, &replica.local_active, building_id)?;
    for cid in ancestor_dag(store, replica.local_head)? {
        let (_, body) = load_root(store, &cid)?;
        let active = match body.materialize_active_objects(store) {
            Ok(s) => s,
            Err(_) => continue,
        };
        match resolve_controller_keys(store, &active, building_id) {
            Ok(more) => {
                for k in more {
                    if !keys.iter().any(|e| e == &k) {
                        keys.push(k);
                    }
                }
            }
            Err(_) => continue,
        }
    }
    Ok(keys)
}

/// Buildings allowed to win collapse: local replica set, plus Buildings from
/// a remote parent only when every remote author is a local controller.
#[allow(clippy::too_many_arguments)]
fn eligible_building_winners<R: ObjectRead + ?Sized>(
    store: &R,
    building_id: &BuildingId,
    cid_a: Cid,
    a: &RootBody,
    active_a: &BTreeSet<Cid>,
    cid_b: Cid,
    b: &RootBody,
    active_b: &BTreeSet<Cid>,
    replica: &MergeReplica,
) -> Result<BTreeSet<Cid>> {
    let local_keys = resolve_controller_keys(store, &replica.local_active, building_id)?;
    let mut eligible = building_cids_in(store, &replica.local_active)?;
    for (cid, body, active) in [(cid_a, a, active_a), (cid_b, b, active_b)] {
        if cid == replica.local_head || authors_are_local_controllers(body, &local_keys) {
            eligible.extend(building_cids_in(store, active)?);
        }
    }
    Ok(eligible)
}

/// Keep at most one Building object per [`BuildingId`] (newest `created`, then CID).
///
/// When `eligible_winners` is `Some`, only those CIDs may be selected. An
/// ingested-only untrusted Building with a newer `created` cannot win
/// (Mallory fork). Fail closed if Buildings exist but none are eligible.
fn collapse_buildings<R: ObjectRead + ?Sized>(
    store: &R,
    objects: &BTreeSet<Cid>,
    eligible_winners: Option<&BTreeSet<Cid>>,
) -> Result<(BTreeSet<Cid>, u64)> {
    let mut best: BTreeMap<BuildingId, (Cid, u64)> = BTreeMap::new();
    let mut building_cids: BTreeSet<Cid> = BTreeSet::new();
    let mut non_building: BTreeSet<Cid> = BTreeSet::new();

    for cid in objects {
        let obj = match store.get(cid) {
            Ok(o) => o,
            Err(Error::NotFound(_)) => {
                non_building.insert(*cid);
                continue;
            }
            Err(e) => return Err(e),
        };
        if let ObjectBody::Building(b) = &obj.body {
            building_cids.insert(*cid);
            if let Some(ok) = eligible_winners {
                if !ok.contains(cid) {
                    continue;
                }
            }
            let created = obj.header.created;
            match best.get(&b.building_id) {
                None => {
                    best.insert(b.building_id.clone(), (*cid, created));
                }
                Some((prev_cid, prev_created)) => {
                    if created > *prev_created || (created == *prev_created && *cid > *prev_cid) {
                        best.insert(b.building_id.clone(), (*cid, created));
                    }
                }
            }
        } else {
            non_building.insert(*cid);
        }
    }

    if eligible_winners.is_some() && !building_cids.is_empty() && best.is_empty() {
        return Err(Error::Authorization(
            "untrusted Building cannot win merge collapse".into(),
        ));
    }

    let mut kept = non_building;
    let mut superseded = 0u64;
    let winners: BTreeSet<Cid> = best.values().map(|(c, _)| *c).collect();
    for cid in building_cids {
        if winners.contains(&cid) {
            kept.insert(cid);
        } else {
            superseded += 1;
        }
    }
    Ok((kept, superseded))
}

/// Merge two root objects already present in `store`.
///
/// The merged root is signed by `keypair` and written to the store.
/// Parents must pass [`RootBody::verify_with_store`]. Without a
/// [`MergeReplica`], Building collapse is newest-`created` among both
/// parents (store-level helper / tests).
pub fn merge_roots<W: ObjectWrite + ?Sized>(
    store: &W,
    root_a: Cid,
    root_b: Cid,
    keypair: &Keypair,
    message: Option<String>,
    rebuild_spatial: bool,
) -> Result<MergeResult> {
    merge_roots_with_replica(
        store,
        root_a,
        root_b,
        keypair,
        message,
        rebuild_spatial,
        None,
    )
}

/// Merge with replica trust: a remote parent that is not signed by local
/// controllers is rejected; untrusted objects never enter the merged set.
pub fn merge_roots_with_replica<W: ObjectWrite + ?Sized>(
    store: &W,
    root_a: Cid,
    root_b: Cid,
    keypair: &Keypair,
    message: Option<String>,
    rebuild_spatial: bool,
    replica: Option<&MergeReplica>,
) -> Result<MergeResult> {
    if root_a == root_b {
        return Err(Error::Validation("cannot merge a root with itself".into()));
    }
    let (_, a) = load_root(store, &root_a)?;
    let (_, b) = load_root(store, &root_b)?;
    if a.building_id != b.building_id {
        return Err(Error::Validation(format!(
            "building_id mismatch: {} vs {}",
            a.building_id, b.building_id
        )));
    }

    // Self-consistency of each parent. Replica continuity (which Building may
    // win) is applied below when `replica` is set; ancestry is adopt's job.
    a.verify_with_store(store)?;
    b.verify_with_store(store)?;

    if let Some(rep) = replica {
        let authorized = replica_authorized_keys(store, &a.building_id, rep)?;
        for (cid, body) in [(root_a, &a), (root_b, &b)] {
            if cid == rep.local_head {
                continue;
            }
            if !authors_are_local_controllers(body, &authorized) {
                return Err(Error::Authorization(
                    "remote parent authors are not local controllers; refusing to merge untrusted objects"
                        .into(),
                ));
            }
        }
    }

    let active_a = a.materialize_active_objects(store)?;
    let active_b = b.materialize_active_objects(store)?;

    // Fast-forward when one tip is a linear descendant of the other.
    let mut objects = if is_ancestor_of(store, root_a, root_b)? {
        active_b.clone()
    } else if is_ancestor_of(store, root_b, root_a)? {
        active_a.clone()
    } else if let Some(lca) = find_common_ancestor(store, root_a, root_b)? {
        let active_base = if lca == root_a {
            active_a.clone()
        } else if lca == root_b {
            active_b.clone()
        } else {
            let (_, base_body) = load_root(store, &lca)?;
            base_body.materialize_active_objects(store)?
        };
        three_way_object_set(&active_base, &active_a, &active_b)
    } else {
        // Disjoint histories (should be rare for same building_id): fall back to union.
        active_a.iter().chain(active_b.iter()).copied().collect()
    };

    // Do not include the parent root objects themselves in the object set.
    objects.remove(&root_a);
    objects.remove(&root_b);

    let before = objects.len() as u64;

    // Geometric fuse when both tips carry the same EntityId, then collapse.
    objects = fuse_active_set(store, &objects, Some(keypair))?;
    let collapsed = collapse_active_set(store, &objects)?;
    objects = collapsed.kept;

    // Building collapse (controller rotation → one Building per building_id).
    let eligible = match replica {
        Some(rep) => Some(eligible_building_winners(
            store,
            &a.building_id,
            root_a,
            &a,
            &active_a,
            root_b,
            &b,
            &active_b,
            rep,
        )?),
        None => None,
    };
    let (after_bldg, bldg_superseded) = collapse_buildings(store, &objects, eligible.as_ref())?;
    objects = after_bldg;

    let drops = annotation_dedupe_drops(store, &objects)?;
    let deduped = drops.len() as u64 + collapsed.superseded.len() as u64 + bldg_superseded;
    for d in drops {
        objects.remove(&d);
    }

    let spatial_index_root = if rebuild_spatial {
        let entries = spatial::collect_entries(store, objects.iter().copied())?;
        spatial::build_index(store, entries)?
    } else {
        None
    };

    let timestamp = a.timestamp.max(b.timestamp).saturating_add(1);
    // Linear primary parent: prefer the newer tip for delta materialization.
    let previous = if a.timestamp >= b.timestamp {
        root_a
    } else {
        root_b
    };
    // Honest multi-parent history: record both concurrent tips.
    let mut merge_parents = BTreeSet::new();
    merge_parents.insert(root_a);
    merge_parents.insert(root_b);

    let is_checkpoint = crate::root::should_checkpoint_at(store, Some(previous))?;

    let mut builder = RootBuilder::new(a.building_id.clone(), timestamp)
        .previous_root(previous)
        .merge_parents(merge_parents);
    if is_checkpoint {
        builder = builder.objects(objects.clone());
    } else {
        let prev_obj = store.get(&previous)?;
        let prev_root = RootBody::from_object(&prev_obj)?;
        let prev_active = prev_root.materialize_active_objects(store)?;
        let added: BTreeSet<Cid> = objects.difference(&prev_active).copied().collect();
        let removed: BTreeSet<Cid> = prev_active.difference(&objects).copied().collect();
        builder = builder.added(added).removed(removed);
    }

    if let Some(si) = spatial_index_root {
        builder = builder.spatial_index(si);
        let _ = si;
    }
    if let Some(msg) = message {
        builder = builder.message(msg);
    } else {
        builder = builder.message(format!("merge {} + {}", root_a, root_b));
    }

    let (root_obj, root_cid) = builder.build_signed(keypair)?;
    // Fail closed: merge author must be a building controller.
    {
        let root = RootBody::from_object(&root_obj)?;
        root.verify_with_store(store)?;
    }
    store.put(&root_obj)?;

    Ok(MergeResult {
        root_cid,
        object_count: objects.len() as u64,
        kept: before - deduped,
        deduped_annotations: deduped,
        spatial_index_root,
        parents: (root_a, root_b),
    })
}

/// Stats helper for tests / CLI.
#[derive(Debug, Clone, Default)]
pub struct MergePlan {
    pub union_size: usize,
    pub would_dedupe: usize,
    pub building_id: String,
}

/// Dry-run merge planning without writing.
pub fn plan_merge<R: ObjectRead + ?Sized>(
    store: &R,
    root_a: Cid,
    root_b: Cid,
) -> Result<MergePlan> {
    let (_, a) = load_root(store, &root_a)?;
    let (_, b) = load_root(store, &root_b)?;
    if a.building_id != b.building_id {
        return Err(Error::Validation("building_id mismatch".into()));
    }
    let active_a = a.materialize_active_objects(store)?;
    let active_b = b.materialize_active_objects(store)?;
    let mut objects = if is_ancestor_of(store, root_a, root_b)? {
        active_b
    } else if is_ancestor_of(store, root_b, root_a)? {
        active_a
    } else if let Some(lca) = find_common_ancestor(store, root_a, root_b)? {
        let active_base = if lca == root_a {
            active_a.clone()
        } else if lca == root_b {
            active_b.clone()
        } else {
            let (_, base_body) = load_root(store, &lca)?;
            base_body.materialize_active_objects(store)?
        };
        three_way_object_set(&active_base, &active_a, &active_b)
    } else {
        active_a.iter().chain(active_b.iter()).copied().collect()
    };
    objects.remove(&root_a);
    objects.remove(&root_b);
    let collapsed = collapse_active_set(store, &objects)?;
    let (after_bldg, bldg_super) = collapse_buildings(store, &collapsed.kept, None)?;
    let drops = annotation_dedupe_drops(store, &after_bldg)?;
    Ok(MergePlan {
        union_size: after_bldg.len(),
        would_dedupe: drops.len() + collapsed.superseded.len() + bldg_super as usize,
        building_id: a.building_id.to_string(),
    })
}

#[cfg(test)]
mod tests;
