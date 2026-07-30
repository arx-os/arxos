//! Spatial query and partial materialization.

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{ObjectBody, Pose};
use crate::root::RootBody;
use crate::working_set::AnnotationHit;

use super::BuildingRepository;

impl BuildingRepository {
    /// Query objects intersecting a volume using the head's spatial index when present.
    pub fn query_volume(
        &self,
        volume: &crate::spatial::QueryVolume,
    ) -> Result<Vec<crate::spatial::SpatialHit>> {
        let Some(head) = self.record.head_root else {
            return Ok(Vec::new());
        };
        let root_obj = self.store.get(&head)?;
        let root = RootBody::from_object(&root_obj)?;
        if let Some(si) = root.spatial_index_root {
            return crate::spatial::query_index_refined(&self.store, &si, volume);
        }
        // Fallback: linear scan of head objects.
        let mut hits = Vec::new();
        for cid in &self.active_objects {
            let obj = match self.store.get(cid) {
                Ok(o) => o,
                Err(Error::NotFound(_)) => continue,
                Err(e) => return Err(e),
            };
            if let Some(entry) = crate::spatial::entry_from_object(*cid, &obj) {
                if entry.bounds.intersects(&volume.bounds) {
                    hits.push(crate::spatial::SpatialHit {
                        object: *cid,
                        bounds: Some(entry.bounds),
                    });
                }
            }
        }
        Ok(hits)
    }

    /// Partial materialization: load objects in `volume` into the working set.
    ///
    /// Returns number of newly materialized objects. Respects `limit` (0 = unlimited).
    pub fn load_region(
        &mut self,
        volume: &crate::spatial::QueryVolume,
        limit: usize,
    ) -> Result<usize> {
        let hits = self.query_volume(volume)?;
        let mut loaded = 0usize;
        for hit in hits {
            if limit > 0 && loaded >= limit {
                break;
            }
            if self.working_set.get_cached(&hit.object).is_some() {
                continue;
            }
            self.working_set.materialize(&self.store, &hit.object)?;
            loaded += 1;
        }
        Ok(loaded)
    }

    /// Load objects associated with a floor (by floor object CID or elevation slab).
    pub fn load_floor(&mut self, floor_cid: &Cid, limit: usize) -> Result<usize> {
        // Prefer explicit floor links; also slab from Floor body.
        let floor_obj = self.store.get(floor_cid)?;
        let volume = if let ObjectBody::Floor(f) = &floor_obj.body {
            crate::spatial::QueryVolume {
                bounds: crate::object::Aabb {
                    min: [-1.0e6, f.elevation_m - 1.5, -1.0e6],
                    max: [1.0e6, f.elevation_m + 1.5, 1.0e6],
                },
            }
        } else {
            crate::spatial::QueryVolume {
                bounds: crate::object::Aabb::from_min_max(
                    [-1.0e6, -1.0e6, -1.0e6],
                    [1.0e6, 1.0e6, 1.0e6],
                ),
            }
        };
        let hits = self.query_volume(&volume)?;
        let mut loaded = 0usize;
        // Always pin the floor object.
        self.working_set.materialize(&self.store, floor_cid)?;
        for hit in hits {
            if limit > 0 && loaded >= limit {
                break;
            }
            // Prefer objects that reference this floor when available.
            if let Ok(obj) = self.store.get(&hit.object) {
                if let Some(entry) = crate::spatial::entry_from_object(hit.object, &obj) {
                    if (entry.floor.as_ref() == Some(floor_cid)
                        || entry.bounds.intersects(&volume.bounds))
                        && self.working_set.get_cached(&hit.object).is_none()
                    {
                        self.working_set.materialize(&self.store, &hit.object)?;
                        loaded += 1;
                    }
                }
            }
        }
        Ok(loaded)
    }

    /// Merge another root into this repository (same building_id), adopt result as head.
    pub fn merge_root(
        &mut self,
        other_root: Cid,
        message: Option<String>,
    ) -> Result<crate::merge::MergeResult> {
        let kp = self
            .keypair
            .as_ref()
            .ok_or_else(|| Error::Crypto("no device keypair for merge signing".into()))?
            .clone();
        let head = self
            .record
            .head_root
            .ok_or_else(|| Error::Validation("no local head to merge into".into()))?;
        let result =
            crate::merge::merge_roots(&self.store, head, other_root, &kp, message, true)?;
        self.adopt_root(result.root_cid)?;
        Ok(result)
    }

    /// Annotations within radius of a pose.
    ///
    /// Uses the spatial index when present (partial candidate set); otherwise
    /// falls back to the full head object list.
    pub fn annotations_near(&mut self, origin: &Pose, radius_m: f64) -> Result<Vec<AnnotationHit>> {
        let volume = crate::spatial::volume_around_pose(origin, radius_m);
        let candidates: Vec<Cid> = match self.query_volume(&volume) {
            Ok(hits) if !hits.is_empty() => hits.into_iter().map(|h| h.object).collect(),
            _ => self.head_object_cids()?,
        };
        self.working_set
            .annotations_near(&self.store, origin, radius_m, candidates)
    }

}
