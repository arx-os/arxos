//! Push object bytes then bind leaf CIDs to a peer inbox. Never sets head.

use std::str::FromStr;

use arxos_core::repository::BuildingRepository;
use arxos_core::Cid;

use crate::error::{NetError, Result};
use crate::transport::{ObjectTransport, PeerId};

/// Ingest canonical bytes into the CAS. **Never** adopts or stages onto head.
///
/// CID on the wire must match BLAKE3 of the payload. Non-canonical objects
/// are rejected by [`arxos_core::store::ObjectStore::put_bytes`].
pub fn serve_put_object(
    store_path: &std::path::Path,
    cid: &str,
    bytes: &[u8],
) -> Result<crate::protocol::Message> {
    use arxos_core::object::Object;
    let want = Cid::from_str(cid).map_err(|e| NetError::Protocol(e.to_string()))?;
    let computed = Cid::from_canonical_bytes(bytes);
    if computed != want {
        return Ok(crate::protocol::Message::PutObjectReject {
            cid: cid.to_string(),
            message: format!("cid mismatch: wire {want} hashed {computed}"),
        });
    }
    // Decode as Object so we fail closed before CAS write on garbage.
    if let Err(e) = Object::from_canonical_bytes(bytes) {
        return Ok(crate::protocol::Message::PutObjectReject {
            cid: cid.to_string(),
            message: e.to_string(),
        });
    }
    let store = arxos_core::store::ObjectStore::open(store_path)?;
    match store.put_bytes(bytes) {
        Ok(stored) => {
            if stored != want {
                return Ok(crate::protocol::Message::PutObjectReject {
                    cid: cid.to_string(),
                    message: "store cid mismatch".into(),
                });
            }
            Ok(crate::protocol::Message::PutObjectOk {
                cid: cid.to_string(),
            })
        }
        Err(e) => Ok(crate::protocol::Message::PutObjectReject {
            cid: cid.to_string(),
            message: e.to_string(),
        }),
    }
}

/// Bind leaf CIDs already in the CAS to a building inbox. **Never** adopts.
pub fn serve_push_facts(
    store_path: &std::path::Path,
    building_id: &str,
    leaf_cids: &[String],
    author_hex: &str,
) -> Result<crate::protocol::Message> {
    use arxos_core::inbox::{inbox_add, InboxAdd};
    use arxos_core::repository::reject_inbox_object;
    use arxos_core::BuildingId;

    let bid = BuildingId::from_str(building_id).map_err(|e| NetError::Protocol(e.to_string()))?;
    let buildings = BuildingRepository::list_buildings(store_path)?;
    if !buildings.iter().any(|r| r.building_id == bid) {
        return Ok(crate::protocol::Message::Error {
            message: format!("unknown building {building_id}"),
        });
    }
    let store = arxos_core::store::ObjectStore::open(store_path)?;
    let mut accepted = Vec::new();
    let mut duplicate = Vec::new();
    let mut rejected = Vec::new();
    for cid_s in leaf_cids {
        let cid = match Cid::from_str(cid_s) {
            Ok(c) => c,
            Err(e) => {
                rejected.push(crate::protocol::CidReject {
                    cid: cid_s.clone(),
                    reason: e.to_string(),
                });
                continue;
            }
        };
        let obj = match store.get(&cid) {
            Ok(o) => o,
            Err(arxos_core::Error::NotFound(_)) => {
                rejected.push(crate::protocol::CidReject {
                    cid: cid_s.clone(),
                    reason: "not in CAS (PutObject first)".into(),
                });
                continue;
            }
            Err(e) => {
                rejected.push(crate::protocol::CidReject {
                    cid: cid_s.clone(),
                    reason: e.to_string(),
                });
                continue;
            }
        };
        if let Err(e) = reject_inbox_object(&obj, &bid) {
            rejected.push(crate::protocol::CidReject {
                cid: cid_s.clone(),
                reason: e.to_string(),
            });
            continue;
        }
        match inbox_add(store_path, &bid, &cid, author_hex) {
            Ok(InboxAdd::Added) => accepted.push(cid_s.clone()),
            Ok(InboxAdd::Duplicate) => duplicate.push(cid_s.clone()),
            Err(e) => rejected.push(crate::protocol::CidReject {
                cid: cid_s.clone(),
                reason: e.to_string(),
            }),
        }
    }
    Ok(crate::protocol::Message::PushFactsOk {
        building_id: building_id.to_string(),
        accepted,
        duplicate,
        rejected,
    })
}

/// Result of [`push_facts`].
#[derive(Debug, Clone)]
pub struct PushResult {
    pub building_id: String,
    pub accepted: Vec<String>,
    pub duplicate: Vec<String>,
    pub rejected: Vec<crate::protocol::CidReject>,
    pub put_ok: u64,
    pub put_rejected: u64,
}

/// Push object bytes then bind leaf CIDs to the peer's inbox. Never sets head.
pub async fn push_facts<T: ObjectTransport + ?Sized>(
    transport: &T,
    peer: &PeerId,
    building_id: &str,
    objects: &[(String, Vec<u8>)],
    leaf_cids: &[String],
    author_hex: &str,
) -> Result<PushResult> {
    let mut put_ok = 0u64;
    let mut put_rejected = 0u64;
    for (cid, bytes) in objects {
        match transport.put_object(peer, cid, bytes).await? {
            crate::protocol::Message::PutObjectOk { .. } => put_ok += 1,
            crate::protocol::Message::PutObjectReject { .. } => put_rejected += 1,
            crate::protocol::Message::Error { message } => {
                return Err(NetError::Protocol(message));
            }
            other => {
                return Err(NetError::Protocol(format!(
                    "unexpected PutObject response: {other:?}"
                )));
            }
        }
    }
    match transport
        .push_facts(peer, building_id, leaf_cids, author_hex)
        .await?
    {
        crate::protocol::Message::PushFactsOk {
            building_id,
            accepted,
            duplicate,
            rejected,
        } => Ok(PushResult {
            building_id,
            accepted,
            duplicate,
            rejected,
            put_ok,
            put_rejected,
        }),
        crate::protocol::Message::Error { message } => Err(NetError::Protocol(message)),
        other => Err(NetError::Protocol(format!(
            "unexpected PushFacts response: {other:?}"
        ))),
    }
}
