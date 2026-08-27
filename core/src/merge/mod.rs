//! Merge concurrent building roots (three-way + entity collapse + annotation rules).
//!
//! Rules:
//! 1. **Three-way set merge** relative to the nearest common ancestor on the
//!    `previous_root` chain (not naive union). Concurrent removals are preserved;
//!    concurrent adds are unioned. If one tip is an ancestor of the other, the
//!    descendant wins (fast-forward).
//! 2. **Entity collapse**: at most one version CID per [`crate::entity::EntityId`].
//! 3. **Building collapse**: at most one Building object per `building_id`
//!    (controller rotation produces successive Building CIDs).
//! 4. **Annotation proximity dedupe**: nearby identical text → keep newer.
//! 5. **Annotation conflict keep-both**: nearby different text → keep both.
//! 6. Spatial index is **rebuilt** after merge (not merged node-by-node).

use std::collections::{BTreeMap, BTreeSet};

use crate::capture::pose_distance;
use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::entity::collapse_active_set;
use crate::error::{Error, Result};
use crate::object::{BuildingId, Object, ObjectBody, ObjectType, Pose};
use crate::root::{resolve_controller_keys, RootBody, RootBuilder};
use crate::spatial;
use crate::store::{ObjectRead, ObjectWrite};

/// Replica view for merge: local head is trusted; a remote parent whose
/// authors are not local controllers cannot supply the winning Building.
///
/// Concurrent honest devices that are still on `controller_keys` remain
/// eligible (`controller_add_survives_sync_and_enforce`). Ancestry is not
/// required here — that is adopt's job.
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
    pose: Pose,
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
                pose: a.pose.clone().unwrap_or_default(),
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
            let d = pose_distance(&anns[i].pose, &anns[j].pose);
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

/// Walk `previous_root` from `tip` collecting ancestor CIDs (including tip).
fn ancestor_chain<R: ObjectRead + ?Sized>(store: &R, tip: Cid) -> Result<Vec<Cid>> {
    let mut chain = Vec::new();
    let mut visited = BTreeSet::new();
    let mut cur = Some(tip);
    while let Some(cid) = cur {
        if !visited.insert(cid) {
            return Err(Error::Validation(
                "cyclic root chain during merge LCA".into(),
            ));
        }
        chain.push(cid);
        let (_, body) = load_root(store, &cid)?;
        cur = body.previous_root;
    }
    Ok(chain)
}

/// Nearest common ancestor of two root tips on the linear `previous_root` chain.
///
/// Returns `None` only when histories are disjoint (no shared ancestor).
pub fn find_common_ancestor<R: ObjectRead + ?Sized>(
    store: &R,
    root_a: Cid,
    root_b: Cid,
) -> Result<Option<Cid>> {
    let chain_a = ancestor_chain(store, root_a)?;
    let set_a: BTreeSet<Cid> = chain_a.into_iter().collect();
    for cid in ancestor_chain(store, root_b)? {
        if set_a.contains(&cid) {
            return Ok(Some(cid));
        }
    }
    Ok(None)
}

/// True if `ancestor` appears on the `previous_root` chain of `desc` (inclusive).
fn is_ancestor_of<R: ObjectRead + ?Sized>(store: &R, ancestor: Cid, desc: Cid) -> Result<bool> {
    Ok(ancestor_chain(store, desc)?.contains(&ancestor))
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

/// Buildings allowed to win collapse: local replica set, plus Buildings from
/// a remote parent only when every remote author is a local controller.
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

/// Merge with replica trust: untrusted remote Buildings cannot win collapse.
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

    // Entity collapse (same physical entity → one version).
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
mod tests {
    use super::*;
    use crate::capture::{annotation_object, space_object, AnnotationCapture, SpaceCapture};
    use crate::crypto::Keypair;
    use crate::entity::{entity_id_of, EntityId};
    use crate::object::{BuildingBody, BuildingId, ObjectBody, Pose};
    use crate::repository::BuildingRepository;
    use crate::store::ObjectStore;
    use std::collections::BTreeMap;
    use tempfile::tempdir;

    fn put_building(store: &ObjectStore, bid: &BuildingId, kp: &Keypair) -> Cid {
        let mut obj = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: Some("M".into()),
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        obj.sign(kp).unwrap();
        store.put(&obj).unwrap()
    }

    #[test]
    fn merge_union_and_dedupe() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();
        let building = put_building(&store, &bid, &kp);

        let ann_a = {
            let mut o = annotation_object(&AnnotationCapture::new(
                "same note",
                Pose {
                    position: [1.0, 1.0, 1.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            o.header.created = 100;
            o.sign(&kp).unwrap();
            store.put(&o).unwrap()
        };
        let ann_b_dup = {
            let mut o = annotation_object(&AnnotationCapture::new(
                "same note",
                Pose {
                    position: [1.05, 1.0, 1.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            o.header.created = 50; // older → drop
            o.sign(&kp).unwrap();
            store.put(&o).unwrap()
        };
        let ann_c_conflict = {
            let mut o = annotation_object(&AnnotationCapture::new(
                "different note",
                Pose {
                    position: [1.02, 1.0, 1.0],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ));
            o.header.created = 80;
            o.sign(&kp).unwrap();
            store.put(&o).unwrap()
        };

        let set_a: BTreeSet<Cid> = [building, ann_a].into_iter().collect();
        let set_b: BTreeSet<Cid> = [building, ann_b_dup, ann_c_conflict].into_iter().collect();

        let (ra, ca) = RootBuilder::new(bid.clone(), 1000)
            .objects(set_a)
            .message("a")
            .build_signed(&kp)
            .unwrap();
        store.put(&ra).unwrap();
        let (rb, cb) = RootBuilder::new(bid.clone(), 1001)
            .objects(set_b)
            .message("b")
            .build_signed(&kp)
            .unwrap();
        store.put(&rb).unwrap();

        let merged = merge_roots(&store, ca, cb, &kp, Some("merge test".into()), true).unwrap();
        assert_eq!(merged.deduped_annotations, 1);
        // building + ann_a + ann_c (ann_b dropped)
        assert_eq!(merged.object_count, 3);

        let root = store.get(&merged.root_cid).unwrap();
        let body = RootBody::from_object(&root).unwrap();
        let active = body.materialize_active_objects(&store).unwrap();
        assert!(active.contains(&ann_a));
        assert!(active.contains(&ann_c_conflict));
        assert!(!active.contains(&ann_b_dup));
        assert!(body.spatial_index_root.is_some());

        // Multi-parent history: both concurrent tips recorded.
        assert_eq!(body.merge_parents.len(), 2);
        assert!(body.merge_parents.contains(&ca));
        assert!(body.merge_parents.contains(&cb));
        assert!(body.previous_root == Some(ca) || body.previous_root == Some(cb));
        assert_eq!(merged.parents, (ca, cb));
    }

    #[test]
    fn three_way_preserves_concurrent_removal() {
        // base has space S; tip A keeps S; tip B removes S → merge must drop S.
        let base: BTreeSet<Cid> = [
            Cid::from_canonical_bytes(b"building"),
            Cid::from_canonical_bytes(b"space-v1"),
        ]
        .into_iter()
        .collect();
        let a = base.clone();
        let mut b = base.clone();
        b.remove(&Cid::from_canonical_bytes(b"space-v1"));
        let merged = three_way_object_set(&base, &a, &b);
        assert!(!merged.contains(&Cid::from_canonical_bytes(b"space-v1")));
        assert!(merged.contains(&Cid::from_canonical_bytes(b"building")));
    }

    #[test]
    fn three_way_unions_concurrent_adds() {
        let base: BTreeSet<Cid> = [Cid::from_canonical_bytes(b"building")]
            .into_iter()
            .collect();
        let mut a = base.clone();
        a.insert(Cid::from_canonical_bytes(b"ann-a"));
        let mut b = base.clone();
        b.insert(Cid::from_canonical_bytes(b"ann-b"));
        let merged = three_way_object_set(&base, &a, &b);
        assert!(merged.contains(&Cid::from_canonical_bytes(b"ann-a")));
        assert!(merged.contains(&Cid::from_canonical_bytes(b"ann-b")));
    }

    #[test]
    fn merge_concurrent_entity_remove_vs_keep() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();
        let building = put_building(&store, &bid, &kp);
        let eid = EntityId::from("01ENTITYRMCONCURRENT000000".to_string());

        let mut space = space_object(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("room".into()),
            pose: Pose::default(),
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        });
        space.header.created = 10;
        space.sign(&kp).unwrap();
        let space_cid = store.put(&space).unwrap();

        let base_set: BTreeSet<Cid> = [building, space_cid].into_iter().collect();
        let (rb, base_cid) = RootBuilder::new(bid.clone(), 1000)
            .objects(base_set)
            .build_signed(&kp)
            .unwrap();
        store.put(&rb).unwrap();

        // Tip A: keep space, add annotation
        let mut ann = annotation_object(&AnnotationCapture::new("note", Pose::default()));
        ann.header.created = 20;
        ann.sign(&kp).unwrap();
        let ann_cid = store.put(&ann).unwrap();
        let set_a: BTreeSet<Cid> = [building, space_cid, ann_cid].into_iter().collect();
        let (ra, tip_a) = RootBuilder::new(bid.clone(), 1001)
            .previous_root(base_cid)
            .objects(set_a)
            .build_signed(&kp)
            .unwrap();
        store.put(&ra).unwrap();

        // Tip B: remove space (only building)
        let set_b: BTreeSet<Cid> = [building].into_iter().collect();
        let (rbb, tip_b) = RootBuilder::new(bid, 1002)
            .previous_root(base_cid)
            .objects(set_b)
            .build_signed(&kp)
            .unwrap();
        store.put(&rbb).unwrap();

        let merged = merge_roots(&store, tip_a, tip_b, &kp, None, false).unwrap();
        let root = store.get(&merged.root_cid).unwrap();
        let body = RootBody::from_object(&root).unwrap();
        let active = body.materialize_active_objects(&store).unwrap();
        assert!(
            !active.contains(&space_cid),
            "concurrent removal must win over keep"
        );
        assert!(active.contains(&ann_cid), "concurrent add must be kept");
        assert!(active.contains(&building));
    }

    #[test]
    fn merge_collapses_same_entity_to_newer_version() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();
        let building = put_building(&store, &bid, &kp);
        let eid = EntityId::from("01ENTITYMERGE000000000000".to_string());

        let mut older = space_object(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("older".into()),
            pose: Pose {
                position: [0.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        });
        older.header.created = 10;
        older.sign(&kp).unwrap();
        let c_old = store.put(&older).unwrap();

        let mut newer = space_object(&SpaceCapture {
            entity_id: Some(eid.clone()),
            name: Some("newer".into()),
            pose: Pose {
                position: [5.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
            bounds: None,
            floor: None,
            properties: BTreeMap::new(),
        });
        newer.header.created = 20;
        newer.sign(&kp).unwrap();
        let c_new = store.put(&newer).unwrap();

        let set_a: BTreeSet<Cid> = [building, c_old].into_iter().collect();
        let set_b: BTreeSet<Cid> = [building, c_new].into_iter().collect();
        let (ra, ca) = RootBuilder::new(bid.clone(), 2000)
            .objects(set_a)
            .build_signed(&kp)
            .unwrap();
        store.put(&ra).unwrap();
        let (rb, cb) = RootBuilder::new(bid, 2001)
            .objects(set_b)
            .build_signed(&kp)
            .unwrap();
        store.put(&rb).unwrap();

        let merged = merge_roots(&store, ca, cb, &kp, None, false).unwrap();
        let root = store.get(&merged.root_cid).unwrap();
        let body = RootBody::from_object(&root).unwrap();
        let active = body.materialize_active_objects(&store).unwrap();
        assert!(active.contains(&c_new));
        assert!(!active.contains(&c_old));
        assert_eq!(entity_id_of(&store.get(&c_new).unwrap()).unwrap(), &eid);
        // building + one space version
        assert_eq!(active.len(), 2);
    }

    #[test]
    fn merge_untrusted_newer_building_cannot_win() {
        let dir = tempdir().unwrap();
        let mut repo = BuildingRepository::init(dir.path(), Some("Alice".into()), None).unwrap();
        let alice_pk = repo.keypair().unwrap().public_key();
        let bid = repo.building_id().clone();
        let mallory = Keypair::generate();

        let b_m = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: Some("Mallory".into()),
                controller_keys: vec![mallory.public_key()],
                properties: BTreeMap::new(),
            }),
            u64::MAX / 2,
        );
        let b_m_cid = repo.put_object(&b_m).unwrap();
        let mut objects = BTreeSet::new();
        objects.insert(b_m_cid);
        let (fork, fork_cid) = RootBuilder::new(bid, 50)
            .objects(objects)
            .message("mallory")
            .build_signed(&mallory)
            .unwrap();
        repo.put_object(&fork).unwrap();

        repo.merge_root(fork_cid, Some("merge mallory".into()))
            .unwrap();
        let keys = repo.controller_keys().unwrap();
        assert_eq!(keys.len(), 1, "{keys:?}");
        assert!(keys.contains(&alice_pk));
        assert!(!keys.contains(&mallory.public_key()));
    }
}
