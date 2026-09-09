//! `arx://bldg/<BuildingId>?controllers=<pk,pk>&inbox=<ticket>`
//!
//! Name is discovery. Trust is pinned controller keys. The ticket is an Iroh
//! peer capability, not an IP-as-authority.

use arxos_core::object::BuildingId;
use arxos_core::PublicKey;

use crate::error::{NetError, Result};

/// Parsed building locator.
#[derive(Debug, Clone)]
pub struct BuildingLocator {
    pub building_id: BuildingId,
    pub controllers: Vec<PublicKey>,
    /// Iroh dial ticket (JSON EndpointAddr) when present.
    pub inbox: Option<String>,
}

/// Parse `arx://bldg/<id>?controllers=...&inbox=...`
pub fn parse_arx_uri(s: &str) -> Result<BuildingLocator> {
    let s = s.trim();
    let rest = s.strip_prefix("arx://").ok_or_else(|| {
        NetError::Protocol("locator must start with arx://".into())
    })?;
    let (path, query) = match rest.split_once('?') {
        Some((p, q)) => (p, Some(q)),
        None => (rest, None),
    };
    let id_str = path
        .strip_prefix("bldg/")
        .ok_or_else(|| NetError::Protocol("locator path must be bldg/<BuildingId>".into()))?;
    if id_str.is_empty() {
        return Err(NetError::Protocol("empty building id".into()));
    }
    let building_id = BuildingId::from(id_str.to_string());
    let mut controllers = Vec::new();
    let mut inbox = None;
    if let Some(q) = query {
        for pair in q.split('&') {
            if pair.is_empty() {
                continue;
            }
            let (k, v) = match pair.split_once('=') {
                Some(kv) => kv,
                None => continue,
            };
            let v = urlencoding_decode(v);
            match k {
                "controllers" => {
                    for pk in v.split(',') {
                        let pk = pk.trim();
                        if pk.is_empty() {
                            continue;
                        }
                        let key = PublicKey::from_str_flexible(pk).map_err(|e| {
                            NetError::Protocol(format!("controller key: {e}"))
                        })?;
                        controllers.push(key);
                    }
                }
                "inbox" => {
                    if !v.is_empty() {
                        inbox = Some(v);
                    }
                }
                _ => {}
            }
        }
    }
    Ok(BuildingLocator {
        building_id,
        controllers,
        inbox,
    })
}

fn urlencoding_decode(s: &str) -> String {
    // Minimal percent-decode for tickets that contain `{` `}` `"` as %7B etc.
    let mut out = String::with_capacity(s.len());
    let b = s.as_bytes();
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'%' && i + 2 < b.len() {
            if let Ok(v) = u8::from_str_radix(std::str::from_utf8(&b[i + 1..i + 3]).unwrap_or(""), 16)
            {
                out.push(v as char);
                i += 3;
                continue;
            }
        }
        out.push(b[i] as char);
        i += 1;
    }
    out
}

trait PkParse {
    fn from_str_flexible(s: &str) -> arxos_core::Result<PublicKey>;
}

impl PkParse for PublicKey {
    fn from_str_flexible(s: &str) -> arxos_core::Result<PublicKey> {
        use std::str::FromStr;
        PublicKey::from_str(s)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_bldg_and_query() {
        let loc = parse_arx_uri("arx://bldg/01ABCDEF?inbox=ticket123").unwrap();
        assert_eq!(loc.building_id.to_string(), "01ABCDEF");
        assert_eq!(loc.inbox.as_deref(), Some("ticket123"));
        assert!(loc.controllers.is_empty());
    }
}
