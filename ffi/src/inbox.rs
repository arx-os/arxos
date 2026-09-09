//! Staged-facts push FFI (never sets remote head).

use std::collections::BTreeSet;
use std::str::FromStr;

use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;

use crate::ArxosError;

/// Push staged Facts to a peer inbox. Never sets remote head.
#[derive(Debug, Clone)]
pub struct FfiPushSummary {
    pub building_id: String,
    pub accepted: u64,
    pub duplicate: u64,
    pub rejected: u64,
}

pub fn push_staged(
    store_path: String,
    building_id: String,
    peer_ticket: String,
) -> Result<FfiPushSummary, ArxosError> {
    let bid = BuildingId::from_str(&building_id).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    let repo = BuildingRepository::open_read(&store_path, &bid)?;
    let pending: Vec<_> = repo.record().pending.iter().copied().collect();
    if pending.is_empty() {
        return Err(ArxosError::Validation {
            message: "no staged facts to push".into(),
        });
    }
    let mut objects = Vec::new();
    let mut seen = BTreeSet::new();
    let mut leaves = Vec::new();
    for cid in &pending {
        leaves.push(cid.to_string());
        if let Ok(obj) = repo.get_object(cid) {
            for dep in arxos_core::repository::referenced_cids(&obj) {
                if seen.insert(dep) {
                    if let Ok(b) = repo.get_object_bytes(&dep) {
                        objects.push((dep.to_string(), b));
                    }
                }
            }
        }
        if seen.insert(*cid) {
            objects.push((cid.to_string(), repo.get_object_bytes(cid)?));
        }
    }
    let author = repo
        .keypair()
        .map(|k| k.public_key().to_string())
        .unwrap_or_default();
    drop(repo);

    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .map_err(|e| ArxosError::Internal {
            message: format!("tokio runtime: {e}"),
        })?;
    rt.block_on(async move {
        let node = arxos_networking::IrohNode::bind(std::path::Path::new(&store_path)).await?;
        let result = arxos_networking::sync::push_facts(
            &node,
            &peer_ticket,
            &building_id,
            &objects,
            &leaves,
            &author,
        )
        .await?;
        node.close().await;
        Ok(FfiPushSummary {
            building_id: result.building_id,
            accepted: result.accepted.len() as u64,
            duplicate: result.duplicate.len() as u64,
            rejected: result.rejected.len() as u64,
        })
    })
}
