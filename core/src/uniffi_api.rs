//! UniFFI scaffolding API for Swift (and other languages).
//!
//! Functions and types here are re-exported at the crate root when the
//! `uniffi` feature is enabled (required by UniFFI's UDL scaffolding).

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::cid::Cid;
use crate::crypto::Keypair;
use crate::object::{BlobBody, BuildingId, Object, ObjectBody};
use crate::root::{RootBody, RootBuilder};
use crate::store::ObjectStore;

// `hello` and `version` live on the crate root (shared with native Rust API).

/// Generate a new BuildingId string (ULID).
pub fn generate_building_id() -> String {
    BuildingId::new().to_string()
}

/// Keypair data exposed to foreign languages.
#[derive(Debug, Clone)]
pub struct KeypairData {
    pub seed: Vec<u8>,
    pub public_key_hex: String,
}

/// Generate a random ed25519 keypair.
pub fn generate_keypair() -> KeypairData {
    let kp = Keypair::generate();
    KeypairData {
        seed: kp.seed().to_vec(),
        public_key_hex: kp.public_key().to_hex(),
    }
}

/// Public key hex from keypair data.
pub fn public_key_hex(keypair: KeypairData) -> String {
    keypair.public_key_hex
}

/// Result of putting a blob object.
#[derive(Debug, Clone)]
pub struct ObjectPutResult {
    pub cid: String,
    pub object_type: String,
}

/// Put a blob into the local store at `store_path`.
pub fn put_blob(
    store_path: String,
    data: Vec<u8>,
    content_type: Option<String>,
) -> ObjectPutResult {
    let store = ObjectStore::open(&store_path).expect("open store");
    let obj = Object::new(ObjectBody::Blob(BlobBody {
        content_type,
        data,
        properties: BTreeMap::new(),
    }));
    let cid = store.put(&obj).expect("put object");
    ObjectPutResult {
        cid: cid.to_string(),
        object_type: "blob".into(),
    }
}

/// Result of creating a signed root.
#[derive(Debug, Clone)]
pub struct RootCreateResult {
    pub root_cid: String,
    pub building_id: String,
    pub object_count: u64,
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// Create and store a signed root from existing object CID strings.
pub fn create_root(
    store_path: String,
    building_id: String,
    object_cids: Vec<String>,
    seed_hex: String,
    message: Option<String>,
) -> RootCreateResult {
    let store = ObjectStore::open(&store_path).expect("open store");
    let seed_bytes = hex::decode(&seed_hex).expect("seed hex");
    assert_eq!(seed_bytes.len(), 32, "seed must be 32 bytes");
    let mut seed = [0u8; 32];
    seed.copy_from_slice(&seed_bytes);
    let kp = Keypair::from_seed(seed);

    let mut set = BTreeSet::new();
    for s in &object_cids {
        set.insert(Cid::from_str(s).expect("cid"));
    }
    let count = set.len() as u64;
    let bid = BuildingId::from_str(&building_id).expect("building id");

    let mut builder = RootBuilder::new(bid.clone(), now_secs()).objects(set);
    if let Some(msg) = message {
        builder = builder.message(msg);
    }
    let (obj, root_cid) = builder.build_signed(&kp).expect("sign root");
    store.put(&obj).expect("store root");

    RootCreateResult {
        root_cid: root_cid.to_string(),
        building_id: bid.to_string(),
        object_count: count,
    }
}

/// Show a root as a summary string, or None if missing.
pub fn show_root(store_path: String, root_cid: String) -> Option<String> {
    let store = ObjectStore::open(&store_path).ok()?;
    let cid = Cid::from_str(&root_cid).ok()?;
    let obj = store.get(&cid).ok()?;
    let root = RootBody::from_object(&obj).ok()?;
    Some(format!(
        "building_id={} previous={:?} objects={} authors={} message={:?} timestamp={}",
        root.building_id,
        root.previous_root.map(|c| c.to_string()),
        root.objects.len(),
        root.authors.len(),
        root.message,
        root.timestamp
    ))
}
