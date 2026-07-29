//! Merge concurrent building roots (union + simple conflict rules).
//!
//! Phase 3 rules:
//! 1. **Union** of object CID sets (and carry the newer previous_root chain tip).
//! 2. **Annotation proximity dedupe**: if two annotations are within
//!    [`ANNOTATION_DEDUP_M`] and share the same normalized text, keep the one
//!    with the later `created` timestamp (tie-break by CID).
//! 3. **Annotation conflict keep-both**: same pose proximity but different text
//!    → keep both (field truth is multi-author).
//! 4. Spatial index is **rebuilt** after merge (not merged node-by-node).

use std::collections::BTreeSet;

use crate::capture::pose_distance;
use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectBody, ObjectType, Pose};
use crate::root::{RootBody, RootBuilder};
use crate::spatial;
use crate::store::ObjectStore;

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
pub fn load_root(store: &ObjectStore, root_cid: &Cid) -> Result<(Object, RootBody)> {
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

fn collect_annotations(store: &ObjectStore, cids: &BTreeSet<Cid>) -> Result<Vec<AnnMeta>> {
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
pub fn annotation_dedupe_drops(store: &ObjectStore, objects: &BTreeSet<Cid>) -> Result<BTreeSet<Cid>> {
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

/// Merge two root objects already present in `store`.
///
/// The merged root is signed by `keypair` and written to the store.
pub fn merge_roots(
    store: &ObjectStore,
    root_a: Cid,
    root_b: Cid,
    keypair: &Keypair,
    message: Option<String>,
    rebuild_spatial: bool,
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

    let active_a = a.materialize_active_objects(store)?;
    let active_b = b.materialize_active_objects(store)?;
    let mut objects: BTreeSet<Cid> = active_a.iter().chain(active_b.iter()).copied().collect();
    // Do not include the parent root objects themselves in the object set.
    objects.remove(&root_a);
    objects.remove(&root_b);

    let before = objects.len() as u64;
    let drops = annotation_dedupe_drops(store, &objects)?;
    let deduped = drops.len() as u64;
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
    // previous_root: prefer the newer parent tip.
    let previous = if a.timestamp >= b.timestamp {
        root_a
    } else {
        root_b
    };

    // Calculate checkpoint distance along the previous root line
    let mut checkpoint_dist = 0;
    let mut current = Some(previous);
    let mut visited = BTreeSet::new();
    while let Some(cid) = current {
        if !visited.insert(cid) {
            break;
        }
        if let Ok(obj) = store.get(&cid) {
            if let Ok(root) = RootBody::from_object(&obj) {
                if root.objects.is_some() {
                    break;
                }
                checkpoint_dist += 1;
                current = root.previous_root;
            } else {
                break;
            }
        } else {
            break;
        }
    }
    let is_checkpoint = checkpoint_dist >= 50;

    let mut builder = RootBuilder::new(a.building_id.clone(), timestamp)
        .previous_root(previous);
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
pub fn plan_merge(store: &ObjectStore, root_a: Cid, root_b: Cid) -> Result<MergePlan> {
    let (_, a) = load_root(store, &root_a)?;
    let (_, b) = load_root(store, &root_b)?;
    if a.building_id != b.building_id {
        return Err(Error::Validation("building_id mismatch".into()));
    }
    let active_a = a.materialize_active_objects(store)?;
    let active_b = b.materialize_active_objects(store)?;
    let mut objects: BTreeSet<Cid> = active_a.iter().chain(active_b.iter()).copied().collect();
    objects.remove(&root_a);
    objects.remove(&root_b);
    let drops = annotation_dedupe_drops(store, &objects)?;
    Ok(MergePlan {
        union_size: objects.len(),
        would_dedupe: drops.len(),
        building_id: a.building_id.to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::{annotation_object, AnnotationCapture};
    use crate::object::{BuildingBody, BuildingId, ObjectBody};
    use crate::crypto::Keypair;
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
    }
}
