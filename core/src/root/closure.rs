//! Bounded root object closures for sync (checkpoint-limited history).

use std::collections::BTreeSet;

use crate::cid::Cid;
use crate::error::{Error, Result};
use crate::object::{Object, ObjectBody};
use crate::store::ObjectStore;

use super::RootBody;

/// Options for collecting a root object closure.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ClosureOptions {
    /// When true, missing domain/index objects are listed in
    /// [`ClosureResult::missing`] instead of failing the call.
    /// Default is false (fail closed).
    pub allow_partial: bool,
    /// When false, skip `Blob` objects and do not follow `points_blob` /
    /// mesh blob references (metadata-first sync). Default is true.
    pub include_blobs: bool,
}

impl Default for ClosureOptions {
    fn default() -> Self {
        Self {
            allow_partial: false,
            include_blobs: true,
        }
    }
}

/// Result of collecting the objects required to materialize and query a root.
#[derive(Debug, Clone)]
pub struct ClosureResult {
    /// Present objects as `(cid, canonical bytes)`.
    pub blobs: Vec<(Cid, Vec<u8>)>,
    /// CIDs that were required but not found in the store (empty when complete).
    pub missing: Vec<Cid>,
}

/// Computes the complete deterministic closure of objects belonging to a Root
/// up to the nearest checkpoint root in history.
///
/// Fail closed: any missing active object or spatial-index node is an error.
pub fn get_root_closure_blobs(store: &ObjectStore, root_cid: &Cid) -> Result<Vec<(Cid, Vec<u8>)>> {
    let result = get_root_closure_blobs_with_options(store, root_cid, &ClosureOptions::default())?;
    Ok(result.blobs)
}

/// Like [`get_root_closure_blobs`], with control over partial closures.
pub fn get_root_closure_blobs_with_options(
    store: &ObjectStore,
    root_cid: &Cid,
    opts: &ClosureOptions,
) -> Result<ClosureResult> {
    let mut visited = BTreeSet::new();
    let mut out = Vec::new();
    let mut missing = BTreeSet::new();

    // 1. Walk root chain backwards to collect Root CIDs and active domain objects
    //    up to the nearest checkpoint. Fail closed if no checkpoint is reached
    //    (same rule as RootBody::materialize_active_objects).
    let mut active_objects = BTreeSet::new();
    let mut removed_set = BTreeSet::new();
    let mut current_prev = Some(*root_cid);
    let mut hit_checkpoint = false;

    while let Some(cid) = current_prev {
        if !visited.insert(cid) {
            break;
        }
        let bytes = store.get_bytes(&cid)?;
        out.push((cid, bytes.clone()));

        let obj = Object::from_canonical_bytes(&bytes)?;
        let root = RootBody::from_object(&obj)?;

        if let Some(ref legacy_set) = root.objects {
            for item in legacy_set {
                if !removed_set.contains(item) {
                    active_objects.insert(*item);
                }
            }
            hit_checkpoint = true;
            break;
        }

        for item in &root.added {
            if !removed_set.contains(item) {
                active_objects.insert(*item);
            }
        }
        for item in &root.removed {
            removed_set.insert(*item);
        }

        current_prev = root.previous_root;
    }

    if !hit_checkpoint {
        return Err(Error::Validation(
            "incomplete root chain for closure: delta walk requires a checkpoint ancestor"
                .into(),
        ));
    }

    // 2. Domain objects (fail closed unless allow_partial).
    //    Optionally skip Blob payloads for metadata-first sync; still collect
    //    skinny domain objects and follow blob refs only when include_blobs.
    let mut blob_refs: BTreeSet<Cid> = BTreeSet::new();
    for cid in &active_objects {
        if !visited.insert(*cid) {
            continue;
        }
        match store.get_bytes(cid) {
            Ok(bytes) => {
                if let Ok(obj) = Object::from_canonical_bytes(&bytes) {
                    if !opts.include_blobs && obj.header.object_type == crate::object::ObjectType::Blob
                    {
                        // Metadata-first: omit blob payloads from the wire set.
                        continue;
                    }
                    if opts.include_blobs {
                        for b in referenced_blob_cids(&obj) {
                            blob_refs.insert(b);
                        }
                    }
                }
                out.push((*cid, bytes));
            }
            Err(Error::NotFound(_)) => {
                missing.insert(*cid);
            }
            Err(e) => return Err(e),
        }
    }

    // 2b. Blob objects referenced by skinny domain objects but not in the
    //     active set (defensive; capture normally stages them into the set).
    if opts.include_blobs {
        for cid in blob_refs {
            if !visited.insert(cid) {
                continue;
            }
            match store.get_bytes(&cid) {
                Ok(bytes) => out.push((cid, bytes)),
                Err(Error::NotFound(_)) => {
                    missing.insert(cid);
                }
                Err(e) => return Err(e),
            }
        }
    }

    // 3. Spatial index nodes from the tip root.
    let root_bytes = store.get_bytes(root_cid)?;
    let root_obj = Object::from_canonical_bytes(&root_bytes)?;
    let root_body = RootBody::from_object(&root_obj)?;
    if let Some(si_root) = root_body.spatial_index_root {
        let mut stack = vec![si_root];
        while let Some(node_cid) = stack.pop() {
            if !visited.insert(node_cid) {
                continue;
            }
            match store.get_bytes(&node_cid) {
                Ok(bytes) => {
                    out.push((node_cid, bytes.clone()));
                    if let Ok(obj) = Object::from_canonical_bytes(&bytes) {
                        if let ObjectBody::SpatialIndexNode(node) = obj.body {
                            stack.extend(node.children);
                        }
                    }
                }
                Err(Error::NotFound(_)) => {
                    missing.insert(node_cid);
                }
                Err(e) => return Err(e),
            }
        }
    }

    let missing: Vec<Cid> = missing.into_iter().collect();
    if !missing.is_empty() && !opts.allow_partial {
        let preview: Vec<String> = missing.iter().take(8).map(|c| c.to_string()).collect();
        return Err(Error::NotFound(format!(
            "incomplete root closure for {root_cid}: missing {} object(s), e.g. {}",
            missing.len(),
            preview.join(", ")
        )));
    }

    Ok(ClosureResult {
        blobs: out,
        missing,
    })
}

/// CIDs of blob payloads referenced by a domain object.
fn referenced_blob_cids(obj: &Object) -> Vec<Cid> {
    match &obj.body {
        ObjectBody::PointCloudChunk(b) => b.points_blob.into_iter().collect(),
        ObjectBody::Mesh(b) => [b.vertices_blob, b.indices_blob]
            .into_iter()
            .flatten()
            .collect(),
        ObjectBody::Annotation(b) => b.media_ref.into_iter().collect(),
        _ => Vec::new(),
    }
}

/// Ensure every CID in `active` is present in `store`.
///
/// Returns the list of missing CIDs (empty when complete).
pub fn missing_active_objects(store: &ObjectStore, active: &BTreeSet<Cid>) -> Result<Vec<Cid>> {
    let mut missing = Vec::new();
    for cid in active {
        if !store.contains(cid) {
            missing.push(*cid);
        }
    }
    Ok(missing)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;
    use crate::object::{BuildingBody, BuildingId, Object};
    use crate::root::RootBuilder;
    use std::collections::BTreeMap;
    use tempfile::tempdir;

    #[test]
    fn closure_fails_closed_on_missing_object() {
        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();
        let ghost = Cid::from_canonical_bytes(b"missing-from-store");
        let mut objects = BTreeSet::new();
        objects.insert(bc);
        objects.insert(ghost);

        let (root_obj, root_cid) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&root_obj).unwrap();

        let err = get_root_closure_blobs(&store, &root_cid).unwrap_err();
        assert!(matches!(err, Error::NotFound(_)), "{err:?}");

        let partial = get_root_closure_blobs_with_options(
            &store,
            &root_cid,
            &ClosureOptions {
                allow_partial: true,
                include_blobs: true,
            },
        )
        .unwrap();
        assert!(partial.missing.contains(&ghost));
        assert!(!partial.blobs.is_empty());
    }

    #[test]
    fn metadata_first_skips_blob_payloads() {
        use crate::capture::{put_point_cloud_chunk, PointCloudCapture};
        use crate::object::Pose;

        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();

        let pts = [[0.0f32, 0.0, 0.0], [1.0, 0.0, 0.0]];
        let cap = PointCloudCapture::from_xyz(&pts, Pose::default(), None);
        let chunk = put_point_cloud_chunk(&store, &cap).unwrap();
        let blob_cid = match &chunk.body {
            ObjectBody::PointCloudChunk(b) => b.points_blob.unwrap(),
            _ => panic!("chunk"),
        };
        let chunk_cid = store.put(&chunk).unwrap();

        let mut objects = BTreeSet::new();
        objects.insert(bc);
        objects.insert(chunk_cid);
        objects.insert(blob_cid);

        let (root_obj, root_cid) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&root_obj).unwrap();

        let full = get_root_closure_blobs(&store, &root_cid).unwrap();
        assert!(full.iter().any(|(c, _)| *c == blob_cid));

        let meta = get_root_closure_blobs_with_options(
            &store,
            &root_cid,
            &ClosureOptions {
                allow_partial: false,
                include_blobs: false,
            },
        )
        .unwrap();
        assert!(!meta.blobs.iter().any(|(c, _)| *c == blob_cid));
        assert!(meta.blobs.iter().any(|(c, _)| *c == chunk_cid));
    }

    #[test]
    fn metadata_first_skips_mesh_blobs() {
        use crate::capture::{put_mesh, MeshCapture};
        use crate::object::Pose;

        let dir = tempdir().unwrap();
        let store = ObjectStore::open(dir.path()).unwrap();
        let kp = Keypair::generate();
        let bid = BuildingId::new();

        let building = Object::new_with_created(
            ObjectBody::Building(BuildingBody {
                building_id: bid.clone(),
                name: None,
                controller_keys: vec![kp.public_key()],
                properties: BTreeMap::new(),
            }),
            1,
        );
        let bc = store.put(&building).unwrap();

        let mesh = put_mesh(
            &store,
            &MeshCapture {
                pose: Pose::default(),
                bounds: None,
                vertices: vec![9, 8, 7, 6],
                indices: vec![0, 1, 2],
                properties: BTreeMap::new(),
            },
        )
        .unwrap();
        let (v_blob, i_blob) = match &mesh.body {
            ObjectBody::Mesh(b) => (b.vertices_blob.unwrap(), b.indices_blob.unwrap()),
            _ => panic!("mesh"),
        };
        let mesh_cid = store.put(&mesh).unwrap();

        let mut objects = BTreeSet::new();
        objects.insert(bc);
        objects.insert(mesh_cid);
        objects.insert(v_blob);
        objects.insert(i_blob);

        let (root_obj, root_cid) = RootBuilder::new(bid, 10)
            .objects(objects)
            .build_signed(&kp)
            .unwrap();
        store.put(&root_obj).unwrap();

        let meta = get_root_closure_blobs_with_options(
            &store,
            &root_cid,
            &ClosureOptions {
                allow_partial: false,
                include_blobs: false,
            },
        )
        .unwrap();
        assert!(meta.blobs.iter().any(|(c, _)| *c == mesh_cid));
        assert!(!meta.blobs.iter().any(|(c, _)| *c == v_blob));
        assert!(!meta.blobs.iter().any(|(c, _)| *c == i_blob));
    }
}
