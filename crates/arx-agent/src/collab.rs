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
    pub owner: String,
    pub repo: String,
    pub target: CollabTarget,
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

pub fn github_token() -> Result<String> {
    env::var(GITHUB_TOKEN_ENV)
        .map_err(|_| anyhow!("{GITHUB_TOKEN_ENV} must be set for collaboration sync"))
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

    let client = Octocrab::builder()
        .personal_token(token.to_owned())
        .build()
        .context("Failed to initialise GitHub client")?;

    let mut successes = Vec::with_capacity(messages.len());
    let mut errors = Vec::new();

    for message in messages {
        match post_comment(&client, config, message).await {
            Ok(success) => successes.push(success),
            Err(error) => errors.push(SyncError {
                id: message.id.clone(),
                error: error.to_string(),
            }),
        }
    }

    Ok(SyncOutcome { successes, errors })
}

async fn post_comment(
    client: &Octocrab,
    config: &CollabConfig,
    message: &CollabMessage,
) -> Result<SyncSuccess> {
    let number = match config.target {
        CollabTarget::Issue { number } | CollabTarget::PullRequest { number } => number,
    };

    let body = format_comment(message);
    let comment = client
        .issues(&config.owner, &config.repo)
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
    ensure!(
        !config.owner.trim().is_empty(),
        "GitHub owner cannot be empty"
    );
    ensure!(
        !config.repo.trim().is_empty(),
        "GitHub repo cannot be empty"
    );
    match config.target {
        CollabTarget::Issue { number } | CollabTarget::PullRequest { number } => {
            ensure!(number > 0, "Target number must be greater than zero");
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
        let tmp = tempdir().unwrap();
        env::set_var(CONFIG_ENV, tmp.path());

        let config = CollabConfig {
            owner: "arx-os".into(),
            repo: "arxos".into(),
            target: CollabTarget::Issue { number: 42 },
        };

        let stored = save_config(&config).unwrap();
        assert_eq!(stored.owner, "arx-os");

        let loaded = load_config().unwrap().unwrap();
        assert_eq!(loaded.owner, "arx-os");
        assert_eq!(loaded.repo, "arxos");

        env::remove_var(CONFIG_ENV);
    }

    #[test]
    fn config_validation_rejects_empty_values() {
        let config = CollabConfig {
            owner: "".into(),
            repo: "repo".into(),
            target: CollabTarget::Issue { number: 1 },
        };
        assert!(validate_config(&config).is_err());
    }
}
