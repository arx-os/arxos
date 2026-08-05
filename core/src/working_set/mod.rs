//! In-memory working set for partial materialization on device.
//!
//! Devices only keep what they need: staged captures + nearby annotations.
//! The full building graph remains in the CAS; this is a thin session cache.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use crate::capture::pose_distance;
use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectBody, ObjectType, Pose};
use crate::store::ObjectStore;

/// Summary of an annotation for AR overlay without full object bytes.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AnnotationHit {
    pub cid: Cid,
    pub text: String,
    pub pose: Pose,
    pub distance_m: f64,
}

/// Session working set: staged CIDs + optionally materialized objects.
#[derive(Debug, Clone, Default)]
pub struct WorkingSet {
    /// Objects created this session and not yet committed (or just committed).
    staged: BTreeSet<Cid>,
    /// Materialized object cache (partial by design).
    cache: BTreeMap<Cid, Object>,
    /// Explicit pin set (always keep).
    pinned: BTreeSet<Cid>,
    /// Soft cap on cache size (object count). 0 = unlimited.
    max_cached: usize,
}

impl WorkingSet {
    pub fn new() -> Self {
        Self {
            staged: BTreeSet::new(),
            cache: BTreeMap::new(),
            pinned: BTreeSet::new(),
            max_cached: 512,
        }
    }

    pub fn with_max_cached(mut self, max: usize) -> Self {
        self.max_cached = max;
        self
    }

    pub fn staged(&self) -> &BTreeSet<Cid> {
        &self.staged
    }

    pub fn staged_len(&self) -> usize {
        self.staged.len()
    }

    pub fn cache_len(&self) -> usize {
        self.cache.len()
    }

    /// Record a newly put object as staged and cache it.
    pub fn stage(&mut self, cid: Cid, object: Object) {
        self.staged.insert(cid);
        self.insert_cache(cid, object);
    }

    /// Drop a CID from the staged set (e.g. when staging a removal).
    pub fn unstaged(&mut self, cid: &Cid) {
        self.staged.remove(cid);
    }

    /// Cache an object without marking it staged (used on open/reload).
    pub fn cache_only(&mut self, cid: Cid, object: Object) {
        self.insert_cache(cid, object);
    }

    /// Pin a CID so eviction prefers others.
    pub fn pin(&mut self, cid: Cid) {
        self.pinned.insert(cid);
    }

    /// Materialize an object from the store into the cache.
    pub fn materialize(&mut self, store: &ObjectStore, cid: &Cid) -> Result<&Object> {
        if !self.cache.contains_key(cid) {
            let obj = store.get(cid)?;
            self.insert_cache(*cid, obj);
        }
        self.cache
            .get(cid)
            .ok_or_else(|| Error::NotFound(cid.to_string()))
    }

    /// Get from cache only (no store I/O).
    pub fn get_cached(&self, cid: &Cid) -> Option<&Object> {
        self.cache.get(cid)
    }

    /// Clear staged set after a successful root commit (objects remain in cache).
    pub fn clear_staged(&mut self) {
        self.staged.clear();
    }

    /// Drop unpinned, unstaged cache entries (partial materialization hygiene).
    pub fn evict_unneeded(&mut self) {
        if self.max_cached == 0 || self.cache.len() <= self.max_cached {
            return;
        }
        let victims: Vec<Cid> = self
            .cache
            .keys()
            .filter(|c| !self.pinned.contains(c) && !self.staged.contains(c))
            .copied()
            .collect();
        for cid in victims {
            if self.cache.len() <= self.max_cached {
                break;
            }
            self.cache.remove(&cid);
        }
    }

    fn insert_cache(&mut self, cid: Cid, object: Object) {
        self.cache.insert(cid, object);
        self.evict_unneeded();
    }

    /// Find annotations near a pose within `radius_m` among cached + optional store CIDs.
    pub fn annotations_near(
        &mut self,
        store: &ObjectStore,
        origin: &Pose,
        radius_m: f64,
        candidate_cids: impl IntoIterator<Item = Cid>,
    ) -> Result<Vec<AnnotationHit>> {
        let mut hits = Vec::new();
        for cid in candidate_cids {
            let obj = match self.cache.get(&cid) {
                Some(o) => o.clone(),
                None => {
                    let o = store.get(&cid)?;
                    self.insert_cache(cid, o.clone());
                    o
                }
            };
            if obj.header.object_type != ObjectType::Annotation {
                continue;
            }
            if let ObjectBody::Annotation(body) = &obj.body {
                let pose = body.pose.clone().unwrap_or_default();
                let d = pose_distance(origin, &pose);
                if d <= radius_m {
                    hits.push(AnnotationHit {
                        cid,
                        text: body.text.clone().unwrap_or_default(),
                        pose,
                        distance_m: d,
                    });
                }
            }
        }
        hits.sort_by(|a, b| {
            a.distance_m
                .partial_cmp(&b.distance_m)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        Ok(hits)
    }

    /// Collect annotation CIDs currently in cache.
    pub fn cached_annotation_cids(&self) -> Vec<Cid> {
        self.cache
            .iter()
            .filter(|(_, o)| o.header.object_type == ObjectType::Annotation)
            .map(|(c, _)| *c)
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capture::{annotation_object, AnnotationCapture};
    use crate::object::Pose;
    use tempfile::tempdir;

    #[test]
    fn stage_and_near_query() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let mut ws = WorkingSet::new();

        let near = annotation_object(&AnnotationCapture::new(
            "near",
            Pose {
                position: [0.5, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ));
        let far = annotation_object(&AnnotationCapture::new(
            "far",
            Pose {
                position: [50.0, 0.0, 0.0],
                orientation: [0.0, 0.0, 0.0, 1.0],
            },
        ));
        let c1 = store.put(&near).unwrap();
        let c2 = store.put(&far).unwrap();
        ws.stage(c1, near);
        ws.stage(c2, far);

        let origin = Pose::default();
        let hits = ws
            .annotations_near(&store, &origin, 5.0, [c1, c2])
            .unwrap();
        assert_eq!(hits.len(), 1);
        assert_eq!(hits[0].text, "near");
    }
}
