//! Building locator: `arx://bldg/<BuildingId>?controllers=<pk>&inbox=<ticket>`
//!
//! Name is discovery. Trust is pinned controller keys (the query string), not
//! DNS and not an IP. The `inbox` value is an opaque dial ticket; this module
//! does not parse Iroh internals.

use std::fmt;
use std::str::FromStr;

use crate::crypto::PublicKey;
use crate::error::{Error, Result};
use crate::object::BuildingId;

/// Parsed `arx://` building locator.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BuildingLocator {
    pub building_id: BuildingId,
    /// Client-side expect set for later fetch/adopt. Empty = unspecified (TOFU).
    pub controllers: Vec<PublicKey>,
    /// Opaque inbox / Iroh ticket. Not interpreted here.
    pub inbox: Option<String>,
}

impl BuildingLocator {
    /// Parse `arx://bldg/<id>?…` or `arx:bldg/<id>?…`.
    ///
    /// Unknown query keys and URL fragments are ignored. Empty `controllers`
    /// tokens and unparsable keys fail closed.
    pub fn parse(s: &str) -> Result<Self> {
        let s = s.trim();
        let s = s.split_once('#').map(|(a, _)| a).unwrap_or(s);
        let rest = if let Some(r) = s.strip_prefix("arx://") {
            r
        } else if let Some(r) = s.strip_prefix("arx:") {
            r.trim_start_matches("//")
        } else {
            return Err(Error::Validation(
                "locator must start with arx:// or arx:".into(),
            ));
        };
        let (path, query) = match rest.split_once('?') {
            Some((p, q)) => (p, Some(q)),
            None => (rest, None),
        };
        let path = path.trim_start_matches('/');
        let id_str = path
            .strip_prefix("bldg/")
            .ok_or_else(|| {
                Error::Validation("locator path must be bldg/<BuildingId>".into())
            })?
            .trim_start_matches('/');
        if id_str.is_empty() {
            return Err(Error::Validation("locator building id must not be empty".into()));
        }
        let building_id = BuildingId::from_str(id_str)?;
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
                match k {
                    "controllers" => {
                        if v.is_empty() {
                            return Err(Error::Validation(
                                "controllers query must not be empty".into(),
                            ));
                        }
                        for pk in v.split(',') {
                            let pk = pk.trim();
                            if pk.is_empty() {
                                return Err(Error::Validation(
                                    "controllers contains an empty token".into(),
                                ));
                            }
                            let decoded = percent_decode(pk);
                            controllers.push(PublicKey::from_str(&decoded)?);
                        }
                    }
                    "inbox" => {
                        let decoded = percent_decode(v);
                        if !decoded.is_empty() {
                            inbox = Some(decoded);
                        }
                    }
                    _ => {}
                }
            }
        }
        Ok(Self {
            building_id,
            controllers,
            inbox,
        })
    }

    /// Canonical URI. Tickets are percent-encoded; controller keys use the
    /// `ed25519:<hex>` form already printed by `arx`.
    pub fn to_uri(&self) -> String {
        let mut out = format!("arx://bldg/{}", self.building_id);
        let mut q = Vec::new();
        if !self.controllers.is_empty() {
            let keys: Vec<String> = self.controllers.iter().map(|k| k.to_string()).collect();
            q.push(format!("controllers={}", keys.join(",")));
        }
        if let Some(t) = &self.inbox {
            q.push(format!("inbox={}", percent_encode(t)));
        }
        if !q.is_empty() {
            out.push('?');
            out.push_str(&q.join("&"));
        }
        out
    }
}

impl FromStr for BuildingLocator {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        Self::parse(s)
    }
}

impl fmt::Display for BuildingLocator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.to_uri())
    }
}

fn percent_encode(s: &str) -> String {
    let mut out = String::new();
    for b in s.bytes() {
        match b {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'.' | b'_' | b'~' => {
                out.push(b as char);
            }
            _ => out.push_str(&format!("%{b:02X}")),
        }
    }
    out
}

fn percent_decode(s: &str) -> String {
    let mut out = Vec::new();
    let b = s.as_bytes();
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'+' {
            out.push(b' ');
            i += 1;
            continue;
        }
        if b[i] == b'%' && i + 2 < b.len() {
            if let Ok(v) = u8::from_str_radix(std::str::from_utf8(&b[i + 1..i + 3]).unwrap_or(""), 16)
            {
                out.push(v);
                i += 3;
                continue;
            }
        }
        out.push(b[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::Keypair;

    #[test]
    fn parse_id_only() {
        let loc = BuildingLocator::parse("arx://bldg/01ABCDEF").unwrap();
        assert_eq!(loc.building_id.to_string(), "01ABCDEF");
        assert!(loc.controllers.is_empty());
        assert!(loc.inbox.is_none());
    }

    #[test]
    fn parse_arx_colon_form() {
        let loc = BuildingLocator::parse("arx:bldg/01ABCDEF").unwrap();
        assert_eq!(loc.building_id.to_string(), "01ABCDEF");
    }

    #[test]
    fn roundtrip_with_ticket_encoding() {
        let kp = Keypair::generate();
        let loc = BuildingLocator {
            building_id: BuildingId::from("01TICKETTEST00000000000000".to_string()),
            controllers: vec![kp.public_key()],
            inbox: Some(r#"{"x":"a+b"}"#.into()),
        };
        let uri = loc.to_uri();
        assert!(uri.contains("%7B") || uri.contains("%22"), "{uri}");
        assert!(uri.contains("%2B"), "plus must be encoded: {uri}");
        let back = BuildingLocator::parse(&uri).unwrap();
        assert_eq!(back.building_id, loc.building_id);
        assert_eq!(back.controllers, loc.controllers);
        assert_eq!(back.inbox, loc.inbox);
    }

    #[test]
    fn plus_in_query_is_space_percent_2b_is_plus() {
        let loc = BuildingLocator::parse("arx://bldg/01X?inbox=hello+world").unwrap();
        assert_eq!(loc.inbox.as_deref(), Some("hello world"));
        let loc = BuildingLocator::parse("arx://bldg/01X?inbox=hello%2Bworld").unwrap();
        assert_eq!(loc.inbox.as_deref(), Some("hello+world"));
    }

    #[test]
    fn ignore_unknown_query_and_fragment() {
        let loc =
            BuildingLocator::parse("arx://bldg/01X?foo=bar&inbox=tix#frag").unwrap();
        assert_eq!(loc.inbox.as_deref(), Some("tix"));
        assert_eq!(loc.building_id.to_string(), "01X");
    }

    #[test]
    fn reject_missing_id() {
        assert!(BuildingLocator::parse("arx://bldg/").is_err());
        assert!(BuildingLocator::parse("arx://nope/01X").is_err());
        assert!(BuildingLocator::parse("https://bldg/01X").is_err());
    }

    #[test]
    fn reject_bad_and_empty_controller() {
        assert!(BuildingLocator::parse("arx://bldg/01X?controllers=").is_err());
        assert!(BuildingLocator::parse("arx://bldg/01X?controllers=ed25519:aa,").is_err());
        assert!(BuildingLocator::parse("arx://bldg/01X?controllers=not-a-key").is_err());
    }
}
