//! Building metadata and device seed I/O (effectful FS helpers).

use std::fs;
use std::path::{Path, PathBuf};

use crate::canonical::{from_cbor, to_canonical_cbor};
use crate::crypto::Keypair;
use crate::error::{Error, Result};
use crate::object::BuildingId;

use super::{BuildingRecord, BuildingRepository};

impl BuildingRepository {
    pub(super) fn meta_path(store_root: &Path, building_id: &BuildingId) -> PathBuf {
        store_root
            .join("meta")
            .join("buildings")
            .join(format!("{building_id}.cbor"))
    }

    pub(super) fn keys_path(store_root: &Path) -> PathBuf {
        store_root.join("keys").join("device.seed")
    }

    pub(super) fn write_record(store_root: &Path, record: &BuildingRecord) -> Result<()> {
        let path = Self::meta_path(store_root, &record.building_id);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }
        let bytes = to_canonical_cbor(record)?;
        crate::store::atomic_write(&path, &bytes)
    }

    pub(super) fn read_record(
        store_root: &Path,
        building_id: &BuildingId,
    ) -> Result<BuildingRecord> {
        let path = Self::meta_path(store_root, building_id);
        if !path.exists() {
            return Err(Error::NotFound(format!("building record {building_id}")));
        }
        let bytes = fs::read(path)?;
        from_cbor(&bytes)
    }

    pub(super) fn write_seed(store_root: &Path, kp: &Keypair) -> Result<()> {
        let seed = kp.seed();
        crate::crypto::write_secret_bytes(&Self::keys_path(store_root), seed.as_ref())
    }

    pub(super) fn read_seed(store_root: &Path) -> Result<Keypair> {
        let seed = crate::crypto::read_secret_32(&Self::keys_path(store_root))?;
        Ok(Keypair::from_seed(*seed))
    }
}
