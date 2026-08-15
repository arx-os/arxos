//! Shared CLI helpers.

use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{bail, Context, Result};
use arxos_core::object::{Object, ObjectBody};
use arxos_core::root::RootBody;
use arxos_core::{Cid, Keypair};
use zeroize::Zeroize;

pub fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

pub fn keypair_from_seed_hex(seed_hex: &str) -> Result<Keypair> {
    let mut bytes = hex::decode(seed_hex).context("decode seed hex")?;
    if bytes.len() != 32 {
        bytes.zeroize();
        bail!("seed must be 32 bytes (64 hex chars), got {}", bytes.len());
    }
    let mut seed = [0u8; 32];
    seed.copy_from_slice(&bytes);
    bytes.zeroize();
    Ok(Keypair::from_seed(seed))
}

pub fn load_device_keypair(store: &Path) -> Option<Keypair> {
    let path = store.join("keys").join("device.seed");
    let seed = arxos_core::read_secret_32(&path).ok()?;
    Some(Keypair::from_seed(*seed))
}

pub fn print_object(obj: &Object, cid: &Cid) {
    println!("cid={cid}");
    println!("type={}", obj.header.object_type);
    println!("schema_version={}", obj.header.schema_version);
    println!("created={}", obj.header.created);
    if let Some(author) = &obj.header.author {
        println!("author={author}");
    }
    println!("signed={}", obj.header.signature.is_some());
    match &obj.body {
        ObjectBody::Blob(b) => {
            println!("content_type={:?}", b.content_type);
            println!("data_len={}", b.data.len());
        }
        ObjectBody::Annotation(a) => {
            println!("text={:?}", a.text);
            println!("pose={:?}", a.pose);
        }
        ObjectBody::Building(b) => {
            println!("building_id={}", b.building_id);
            println!("name={:?}", b.name);
            println!("controllers={}", b.controller_keys.len());
        }
        ObjectBody::Root(r) => {
            println!("building_id={}", r.building_id);
            if let Some(ref objs) = r.objects {
                println!("objects={}", objs.len());
            } else {
                println!("added={}", r.added.len());
                println!("removed={}", r.removed.len());
            }
        }
        other => {
            println!("body_type={}", other.object_type());
        }
    }
}

pub fn object_summary(obj: &Object, cid: &Cid) -> serde_json::Value {
    serde_json::json!({
        "cid": cid.to_string(),
        "type": obj.header.object_type.to_string(),
        "schema_version": obj.header.schema_version,
        "created": obj.header.created,
        "author": obj.header.author.map(|a| a.to_string()),
        "signed": obj.header.signature.is_some(),
    })
}

pub fn root_summary(root: &RootBody, cid: &Cid) -> serde_json::Value {
    let mut summary = serde_json::json!({
        "root_cid": cid.to_string(),
        "building_id": root.building_id.to_string(),
        "previous_root": root.previous_root.map(|c| c.to_string()),
        "timestamp": root.timestamp,
        "message": root.message,
        "spatial_index_root": root.spatial_index_root.map(|c| c.to_string()),
        "authors": root.authors.iter().map(|a| a.public_key.to_string()).collect::<Vec<_>>(),
    });
    if let Some(ref objs) = root.objects {
        summary["objects"] = serde_json::json!(objs.iter().map(|c| c.to_string()).collect::<Vec<_>>());
        summary["object_count"] = serde_json::json!(objs.len());
    } else {
        summary["added"] = serde_json::json!(root.added.iter().map(|c| c.to_string()).collect::<Vec<_>>());
        summary["removed"] = serde_json::json!(root.removed.iter().map(|c| c.to_string()).collect::<Vec<_>>());
        summary["added_count"] = serde_json::json!(root.added.len());
        summary["removed_count"] = serde_json::json!(root.removed.len());
    }
    summary
}
