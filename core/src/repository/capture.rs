//! Capture / stage helpers for [`super::BuildingRepository`].

use super::*;
use crate::capture::{
    annotation_object, maybe_sign, put_mesh, put_point_cloud_chunk, space_object,
    AnnotationCapture, MeshCapture, PointCloudCapture, SpaceCapture,
};
use crate::object::ObjectBody;

impl BuildingRepository {
    /// Capture a space → put → stage.
    pub fn capture_space(&mut self, capture: &SpaceCapture) -> Result<CaptureResult> {
        let obj = maybe_sign(space_object(capture), self.keypair.as_ref())?;
        self.put_staged(obj)
    }

    /// Capture a point cloud chunk → tier bytes into a Blob → put → stage.
    ///
    /// Also stages the blob CID into pending so it is included in the next root.
    pub fn capture_point_cloud(&mut self, capture: &PointCloudCapture) -> Result<CaptureResult> {
        let obj = put_point_cloud_chunk(&*self, capture)?;
        // Ensure the blob is part of the active set (referenced + present).
        if let ObjectBody::PointCloudChunk(ref b) = obj.body {
            if let Some(blob_cid) = b.points_blob {
                if let Ok(blob_obj) = self.store.get(&blob_cid) {
                    self.working_set.stage(blob_cid, blob_obj);
                    self.record.pending.insert(blob_cid);
                }
            }
        }
        let obj = maybe_sign(obj, self.keypair.as_ref())?;
        self.put_staged(obj)
    }

    /// Capture a mesh → tier vertex/index blobs → put → stage.
    ///
    /// Also stages blob CIDs into pending so they are included in the next root.
    pub fn capture_mesh(&mut self, capture: &MeshCapture) -> Result<CaptureResult> {
        let obj = put_mesh(&*self, capture)?;
        if let ObjectBody::Mesh(ref b) = obj.body {
            for blob_cid in [b.vertices_blob, b.indices_blob].into_iter().flatten() {
                if let Ok(blob_obj) = self.store.get(&blob_cid) {
                    self.working_set.stage(blob_cid, blob_obj);
                    self.record.pending.insert(blob_cid);
                }
            }
        }
        let obj = maybe_sign(obj, self.keypair.as_ref())?;
        self.put_staged(obj)
    }

    /// Capture an annotation → put → stage.
    pub fn capture_annotation(&mut self, capture: &AnnotationCapture) -> Result<CaptureResult> {
        let obj = maybe_sign(annotation_object(capture), self.keypair.as_ref())?;
        self.put_staged(obj)
    }

    /// Ingest RoomPlan geometry as Facts, stage them, and return CIDs.
    ///
    /// Surfaces that RoomPlan labels door/window/opening become [`Opening`]
    /// Facts hosted on the nearest wall. Apple UUIDs become stable
    /// [`crate::entity::EntityId`]s (`rp:` + lowercase uuid).
    pub fn ingest_room_plan(
        &mut self,
        geometry: &crate::capture::roomplan::RoomPlanGeometry,
    ) -> Result<crate::capture::roomplan::MappedRoomPlanCids> {
        let created = now_secs();
        let mapped = crate::capture::roomplan::map_roomplan(geometry, created)?;
        self.ingest_mapped_roomplan(mapped)
    }

    /// Stage an already-mapped RoomPlan batch (Facts, not scans).
    pub fn ingest_mapped_roomplan(
        &mut self,
        mapped: crate::capture::roomplan::MappedRoomPlan,
    ) -> Result<crate::capture::roomplan::MappedRoomPlanCids> {
        self.require_write()?;
        // Keypair is not Clone; copy seed so we can sign while mutably staging.
        let kp_owned = self.keypair.as_ref().map(|k| Keypair::from_seed(*k.seed()));
        let kp = kp_owned.as_ref();

        let space = maybe_sign(mapped.space, kp)?;
        let space_res = self.put_staged(space)?;

        let mut surfaces = Vec::new();
        for mut obj in mapped.surfaces {
            if let ObjectBody::Surface(ref mut b) = obj.body {
                b.space = Some(space_res.cid);
            }
            let signed = maybe_sign(obj, kp)?;
            surfaces.push(self.put_staged(signed)?.cid);
        }

        let mut openings = Vec::new();
        for obj in mapped.openings {
            let signed = maybe_sign(obj, kp)?;
            openings.push(self.put_staged(signed)?.cid);
        }

        let mut equipment = Vec::new();
        for mut obj in mapped.equipment {
            if let ObjectBody::Equipment(ref mut b) = obj.body {
                b.properties
                    .insert("space".into(), space_res.cid.to_string());
            }
            let signed = maybe_sign(obj, kp)?;
            equipment.push(self.put_staged(signed)?.cid);
        }

        Ok(crate::capture::roomplan::MappedRoomPlanCids {
            space: space_res.cid,
            surfaces,
            openings,
            equipment,
        })
    }

    /// Put and stage any captured object directly into the repository.
    pub fn stage_captured_object(&mut self, obj: Object) -> Result<CaptureResult> {
        self.put_staged(obj)
    }

    /// Stage an object CID for removal on the next commit.
    ///
    /// The object remains in the CAS (content-addressed history); it is dropped
    /// from the active set via the root `removed` delta.
    pub fn remove_object(&mut self, cid: Cid) -> Result<()> {
        self.require_write()?;
        self.record.pending.remove(&cid);
        self.working_set.unstaged(&cid);
        self.record.pending_removes.insert(cid);
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;
        Ok(())
    }

    /// Stage all active (and pending) versions of `entity_id` for removal.
    pub fn remove_entity(&mut self, entity_id: &crate::entity::EntityId) -> Result<u64> {
        let mut candidates = self.active_objects.clone();
        candidates.extend(self.record.pending.iter().copied());
        let versions = crate::entity::find_entity_versions(&self.store, &candidates, entity_id)?;
        let n = versions.len() as u64;
        for cid in versions {
            self.remove_object(cid)?;
        }
        Ok(n)
    }

    /// Add a controller public key without re-initializing the building.
    ///
    /// Stages a **new** Building object (new CID) with an expanded
    /// `controller_keys` set and stages removal of the previous Building
    /// object. Call [`commit`] afterward; the **current** controller must
    /// sign that commit (fail-closed).
    ///
    /// Idempotent if `key` is already a controller (returns the existing
    /// building object CID without staging changes).
    pub fn add_controller_key(&mut self, key: PublicKey) -> Result<CaptureResult> {
        let (old_cid, body) = self.current_building_body()?;
        if body.controller_keys.iter().any(|k| k == &key) {
            return Ok(CaptureResult {
                cid: old_cid,
                object_type: ObjectType::Building,
            });
        }
        let mut keys = body.controller_keys.clone();
        keys.push(key);
        // Stable order for deterministic CIDs when the same set is rebuilt.
        keys.sort();
        keys.dedup();
        self.replace_building_object(old_cid, body, keys)
    }

    /// Remove a controller public key without re-initializing the building.
    ///
    /// Fail-closed rules:
    /// - Key must currently be a controller.
    /// - Cannot remove the last remaining controller.
    /// - Stages a new Building object + removal of the prior one; caller must
    ///   [`commit`] with a remaining controller key.
    pub fn remove_controller_key(&mut self, key: PublicKey) -> Result<CaptureResult> {
        let (old_cid, body) = self.current_building_body()?;
        if !body.controller_keys.iter().any(|k| k == &key) {
            return Err(Error::Validation(format!(
                "public key {key} is not in building controller_keys"
            )));
        }
        if body.controller_keys.len() <= 1 {
            return Err(Error::Authorization(
                "cannot remove the last remaining controller; offline recovery required".into(),
            ));
        }
        let mut keys: Vec<PublicKey> = body
            .controller_keys
            .iter()
            .copied()
            .filter(|k| k != &key)
            .collect();
        keys.sort();
        keys.dedup();
        if keys.is_empty() {
            return Err(Error::Authorization(
                "cannot remove the last remaining controller; offline recovery required".into(),
            ));
        }
        self.replace_building_object(old_cid, body, keys)
    }

    /// Controller public keys on the current Building object in the active set.
    pub fn controller_keys(&self) -> Result<Vec<PublicKey>> {
        let (_, body) = self.current_building_body()?;
        Ok(body.controller_keys)
    }

    /// List entity heads in the active set: `(EntityId, version Cid, ObjectType)`.
    ///
    /// Deterministic order by entity id string. Objects without `entity_id` are omitted.
    /// When multiple versions of the same entity appear (should not after collapse),
    /// the higher `created` (then higher CID) wins.
    pub fn list_entity_heads(&self) -> Result<Vec<(crate::entity::EntityId, Cid, ObjectType)>> {
        use crate::entity::entity_id_of;
        let mut by_entity: std::collections::BTreeMap<
            crate::entity::EntityId,
            (Cid, u64, ObjectType),
        > = std::collections::BTreeMap::new();
        for cid in &self.active_objects {
            let obj = match self.store.get(cid) {
                Ok(o) => o,
                Err(Error::NotFound(_)) => continue,
                Err(e) => return Err(e),
            };
            let Some(eid) = entity_id_of(&obj).cloned() else {
                continue;
            };
            let created = obj.header.created;
            let ty = obj.header.object_type;
            let replace = match by_entity.get(&eid) {
                None => true,
                Some((prev_cid, prev_created, _)) => {
                    created > *prev_created || (created == *prev_created && *cid > *prev_cid)
                }
            };
            if replace {
                by_entity.insert(eid, (*cid, created, ty));
            }
        }
        Ok(by_entity
            .into_iter()
            .map(|(eid, (cid, _, ty))| (eid, cid, ty))
            .collect())
    }

    fn replace_building_object(
        &mut self,
        old_cid: Cid,
        body: BuildingBody,
        keys: Vec<PublicKey>,
    ) -> Result<CaptureResult> {
        let mut new_obj = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: body.building_id,
                name: body.name,
                controller_keys: keys,
                properties: body.properties,
            }),
            now_secs(),
        );
        if let Some(kp) = self.keypair.as_ref() {
            new_obj.sign(kp)?;
        }

        self.remove_object(old_cid)?;
        let res = self.put_staged(new_obj)?;
        self.record.building_object = Some(res.cid);
        Self::write_record(self.store.root(), &self.record)?;
        Ok(res)
    }

    /// Current Building object CID and body from the active set (fail closed).
    pub fn current_building_body(&self) -> Result<(Cid, BuildingBody)> {
        let mut found: Option<(Cid, BuildingBody)> = None;
        for cid in &self.active_objects {
            let obj = match self.store.get(cid) {
                Ok(o) => o,
                Err(Error::NotFound(_)) => continue,
                Err(e) => return Err(e),
            };
            if let ObjectBody::Building(b) = &obj.body {
                if b.building_id == self.record.building_id {
                    if found.is_some() {
                        return Err(Error::Authorization(format!(
                            "multiple Building objects for {} in active set",
                            self.record.building_id
                        )));
                    }
                    found = Some((*cid, b.clone()));
                }
            }
        }
        found.ok_or_else(|| {
            Error::Authorization(format!(
                "no Building object for {} in active set",
                self.record.building_id
            ))
        })
    }

    fn put_staged(&mut self, obj: Object) -> Result<CaptureResult> {
        self.require_write()?;
        let object_type = obj.header.object_type;
        let cid = self.store.put(&obj)?;
        // If this is a new version of an existing entity, clear any staged remove
        // of this cid (re-add) and leave older versions to entity collapse on commit.
        self.record.pending_removes.remove(&cid);
        self.working_set.stage(cid, obj);
        self.record.pending.insert(cid);
        self.record.updated = now_secs();
        Self::write_record(self.store.root(), &self.record)?;
        Ok(CaptureResult { cid, object_type })
    }
}
