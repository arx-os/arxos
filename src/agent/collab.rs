use std::{env, fs, path::PathBuf};

use anyhow::{anyhow, ensure, Context, Result};
use chrono::{DateTime, Utc};
use dirs;
use octocrab::Octocrab;
use serde::{Deserialize, Serialize};

const CONFIG_ENV: &str = "ARXOS_AGENT_CONFIG_DIR";
pub const GITHUB_TOKEN_ENV: &str = "ARXOS_GITHUB_TOKEN";
const CONFIG_FILENAME: &str = "collab.toml";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CollabConfig {
    #[serde(default)]
    pub owner: Option<String>,
    #[serde(default)]
    pub repo: Option<String>,
    #[serde(default)]
    pub target: Option<CollabTarget>,
    #[serde(default)]
    pub peers: Option<Vec<String>>,
    #[serde(default)]
    pub enable_discovery: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum CollabTarget {
    Issue { number: u64 },
    PullRequest { number: u64 },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CollabMessage {
    pub id: String,
    pub building_id: String,
    pub author: String,
    pub content: String,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SyncRequest {
    pub messages: Vec<CollabMessage>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SyncSuccess {
    pub id: String,
    pub remote_id: u64,
    pub remote_url: Option<String>,
    pub synced_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SyncError {
    pub id: String,
    pub error: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SyncOutcome {
    pub successes: Vec<SyncSuccess>,
    pub errors: Vec<SyncError>,
}

pub fn config_path() -> Result<PathBuf> {
    let root = if let Ok(custom) = env::var(CONFIG_ENV) {
        PathBuf::from(custom)
    } else {
        dirs::config_dir()
            .map(|mut path| {
                path.push("arxos");
                path
            })
            .ok_or_else(|| anyhow!("Unable to determine config directory"))?
    };

    if !root.exists() {
        fs::create_dir_all(&root)
            .with_context(|| format!("Failed to create config dir at {root:?}"))?;
    }

    Ok(root.join(CONFIG_FILENAME))
}

pub fn load_config() -> Result<Option<CollabConfig>> {
    let path = config_path()?;
    if !path.exists() {
        return Ok(None);
    }

    let contents = fs::read_to_string(&path)
        .with_context(|| format!("Failed to read collaboration config at {}", path.display()))?;
    let config: CollabConfig = toml::from_str(&contents)
        .with_context(|| format!("Invalid collaboration config at {}", path.display()))?;
    validate_config(&config)?;
    Ok(Some(config))
}

pub fn save_config(config: &CollabConfig) -> Result<CollabConfig> {
    validate_config(config)?;
    let path = config_path()?;
    let encoded = toml::to_string_pretty(config)?;
    fs::write(&path, encoded)
        .with_context(|| format!("Failed to write collaboration config at {}", path.display()))?;
    Ok(config.clone())
}

pub fn github_token() -> Result<Option<String>> {
    match env::var(GITHUB_TOKEN_ENV) {
        Ok(t) => Ok(Some(t)),
        Err(_) => Ok(None),
    }
}

pub async fn sync_messages(
    messages: &[CollabMessage],
    config: &CollabConfig,
    token: &str,
) -> Result<SyncOutcome> {
    if messages.is_empty() {
        return Ok(SyncOutcome {
            successes: Vec::new(),
            errors: Vec::new(),
        });
    }

    let mut successes = Vec::new();
    let mut errors = Vec::new();
    let mut sync_success = false;

    // 1. Collect peer endpoints
    let mut peer_endpoints = Vec::new();
    if let Some(ref configured_peers) = config.peers {
        peer_endpoints.extend(configured_peers.clone());
    }
    if config.enable_discovery.unwrap_or(false) {
        let discovered = crate::agent::discovery::get_peers();
        let guard = discovered.lock().unwrap();
        for peer in guard.iter() {
            peer_endpoints.push(peer.endpoint.clone());
        }
    }

    // 2. Attempt sync with local network peers
    let client = reqwest::Client::new();
    for endpoint in &peer_endpoints {
        let mut peer_url = endpoint.clone();
        let mut peer_token = String::new();
        if let Ok(parsed) = url::Url::parse(endpoint) {
            if let Some(tok_val) = parsed
                .query_pairs()
                .find(|(k, _)| k == "token")
                .map(|(_, v)| v.into_owned())
            {
                peer_token = tok_val;
                if let Some(pos) = peer_url.find('?') {
                    peer_url.truncate(pos);
                }
            }
        }

        let url = format!("{}/rpc", peer_url.trim_end_matches('/'));
        let mut req = client.post(&url);
        if !peer_token.is_empty() {
            req = req.query(&[("token", &peer_token)]);
        }

        let body = serde_json::json!({
            "jsonrpc": "2.0",
            "method": "collab.sync",
            "params": {
                "messages": messages
            },
            "id": "p2p-sync"
        });

        match req.json(&body).send().await {
            Ok(resp) => {
                if let Ok(rpc_resp) = resp.json::<serde_json::Value>().await {
                    if let Some(result_val) = rpc_resp.get("result") {
                        if let Ok(outcome) =
                            serde_json::from_value::<SyncOutcome>(result_val.clone())
                        {
                            successes.extend(outcome.successes);
                            errors.extend(outcome.errors);
                            sync_success = true;
                        }
                    }
                }
            }
            Err(e) => {
                log::warn!("Failed to sync with local peer {}: {}", endpoint, e);
            }
        }
    }

    // 3. Fallback to centralized GitHub comment sync if local peers didn't succeed and config is present
    if !sync_success {
        let has_github_config =
            config.owner.is_some() && config.repo.is_some() && config.target.is_some();
        if has_github_config && !token.is_empty() {
            let client = Octocrab::builder()
                .personal_token(token.to_owned())
                .build()
                .context("Failed to initialise GitHub client")?;

            for message in messages {
                match post_comment(&client, config, message).await {
                    Ok(success) => successes.push(success),
                    Err(error) => errors.push(SyncError {
                        id: message.id.clone(),
                        error: error.to_string(),
                    }),
                }
            }
        } else {
            // Neither peer nor GitHub succeeded, return errors for all messages
            for message in messages {
                errors.push(SyncError {
                    id: message.id.clone(),
                    error: "No local peers reached and GitHub collaboration is not configured."
                        .to_string(),
                });
            }
        }
    }

    Ok(SyncOutcome { successes, errors })
}

async fn post_comment(
    client: &Octocrab,
    config: &CollabConfig,
    message: &CollabMessage,
) -> Result<SyncSuccess> {
    let owner = config
        .owner
        .as_ref()
        .ok_or_else(|| anyhow!("Missing owner"))?;
    let repo = config
        .repo
        .as_ref()
        .ok_or_else(|| anyhow!("Missing repo"))?;
    let target = config
        .target
        .as_ref()
        .ok_or_else(|| anyhow!("Missing target"))?;

    let number = match target {
        CollabTarget::Issue { number } | CollabTarget::PullRequest { number } => *number,
    };

    let body = format_comment(message);
    let comment = client
        .issues(owner, repo)
        .create_comment(number, body)
        .await
        .context("Failed to create comment via GitHub API")?;

    let synced_at = comment.created_at;

    Ok(SyncSuccess {
        id: message.id.clone(),
        remote_id: comment.id.0,
        remote_url: Some(comment.html_url.to_string()),
        synced_at,
    })
}

fn format_comment(message: &CollabMessage) -> String {
    let submitted_at =
        DateTime::<Utc>::from_timestamp_millis(message.timestamp).unwrap_or_else(|| Utc::now());

    format!(
        "### ArxOS Update for `{}`\n\n{}\n\n— _{}_ @ {} UTC_",
        message.building_id,
        message.content.trim(),
        message.author,
        submitted_at.format("%Y-%m-%d %H:%M:%S")
    )
}

fn validate_config(config: &CollabConfig) -> Result<()> {
    if let Some(ref owner) = config.owner {
        ensure!(!owner.trim().is_empty(), "GitHub owner cannot be empty");
    }
    if let Some(ref repo) = config.repo {
        ensure!(!repo.trim().is_empty(), "GitHub repo cannot be empty");
    }
    if let Some(ref target) = config.target {
        match target {
            CollabTarget::Issue { number } | CollabTarget::PullRequest { number } => {
                ensure!(*number > 0, "Target number must be greater than zero");
            }
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn save_and_load_roundtrip() {
        let tmp = tempdir().expect("Failed to create temp directory");
        env::set_var(CONFIG_ENV, tmp.path());

        let config = CollabConfig {
            owner: Some("arx-os".into()),
            repo: Some("arxos".into()),
            target: Some(CollabTarget::Issue { number: 42 }),
            peers: None,
            enable_discovery: Some(true),
        };

        let stored = save_config(&config).expect("Failed to save config");
        assert_eq!(stored.owner.unwrap(), "arx-os");

        let loaded = load_config()
            .expect("Failed to load config")
            .expect("Config should exist after saving");
        assert_eq!(loaded.owner.unwrap(), "arx-os");
        assert_eq!(loaded.repo.unwrap(), "arxos");

        env::remove_var(CONFIG_ENV);
    }

    #[test]
    fn config_validation_rejects_empty_values() {
        let config = CollabConfig {
            owner: Some("".into()),
            repo: Some("repo".into()),
            target: Some(CollabTarget::Issue { number: 1 }),
            peers: None,
            enable_discovery: None,
        };
        assert!(validate_config(&config).is_err());
    }
}
