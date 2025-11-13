use std::collections::HashSet;

use anyhow::{anyhow, Result};
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct TokenState {
    value: String,
    capabilities: Vec<String>,
    last_rotated: DateTime<Utc>,
}

impl TokenState {
    pub fn new(value: String, capabilities: Vec<String>) -> Self {
        Self {
            value,
            capabilities,
            last_rotated: Utc::now(),
        }
    }

    pub fn value(&self) -> &str {
        &self.value
    }

    pub fn capabilities(&self) -> &[String] {
        &self.capabilities
    }

    pub fn last_rotated(&self) -> DateTime<Utc> {
        self.last_rotated
    }

    pub fn rotate(&mut self, new_value: String, capabilities: Vec<String>) {
        self.value = new_value;
        self.capabilities = capabilities;
        self.last_rotated = Utc::now();
    }

    pub fn update_capabilities(&mut self, capabilities: Vec<String>) {
        self.capabilities = capabilities;
    }
}

pub fn generate_did_key() -> String {
    format!("did:key:z{}", Uuid::new_v4().to_string().replace('-', ""))
}

pub fn filter_capabilities(default: &[String], requested: &[String]) -> (Vec<String>, Vec<String>) {
    let available: HashSet<&String> = default.iter().collect();
    let mut granted = Vec::new();
    let mut denied = Vec::new();

    for cap in requested {
        if available.contains(cap) {
            granted.push(cap.clone());
        } else {
            denied.push(cap.clone());
        }
    }

    (granted, denied)
}

pub fn ensure_capability(action: &str, capabilities: &[String]) -> Result<()> {
    if let Some(required) = action_required_capability(action) {
        if capabilities.iter().any(|cap| cap == required) {
            Ok(())
        } else {
            Err(anyhow!(
                "Capability '{}' required for action '{}'",
                required,
                action
            ))
        }
    } else {
        Ok(())
    }
}

fn action_required_capability(action: &str) -> Option<&'static str> {
    match action {
        "git.status" => Some("git.status"),
        "git.diff" => Some("git.diff"),
        "git.commit" => Some("git.commit"),
        "files.read" => Some("files.read"),
        "ifc.import" => Some("ifc.import"),
        "ifc.export" => Some("ifc.export"),
        "auth.rotate" | "auth.negotiate" => Some("auth.manage"),
        "collab.sync" => Some("collab.sync"),
        "collab.config.get" | "collab.config.set" => Some("collab.config"),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rotate_updates_token_and_timestamp() {
        let mut state = TokenState::new("did:key:ztoken".into(), vec!["git.status".into()]);
        let previous_timestamp = state.last_rotated();
        state.rotate("did:key:znew".into(), vec!["git.diff".into()]);

        assert_eq!(state.value(), "did:key:znew");
        assert_eq!(state.capabilities(), &[String::from("git.diff")]);
        assert!(state.last_rotated() > previous_timestamp);
    }

    #[test]
    fn ensure_capability_allows_permitted_actions() {
        let capabilities = vec!["git.status".into(), "ifc.export".into()];
        assert!(ensure_capability("git.status", &capabilities).is_ok());
        assert!(ensure_capability("ifc.export", &capabilities).is_ok());
        assert!(ensure_capability("ping", &capabilities).is_ok());
        assert!(ensure_capability("git.commit", &capabilities).is_err());
    }

    #[test]
    fn filter_capabilities_partitions_requested() {
        let default = vec!["git.status".into(), "git.diff".into()];
        let requested = vec!["git.status".into(), "files.read".into()];
        let (granted, denied) = filter_capabilities(&default, &requested);

        assert_eq!(granted, vec!["git.status"]);
        assert_eq!(denied, vec!["files.read"]);
    }
}
