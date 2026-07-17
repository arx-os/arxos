//! Observability and operational instrumentation helper for the ArxOS agent.

use std::fmt;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;
use std::time::Instant;
use std::path::PathBuf;
use std::sync::OnceLock;
use regex::Regex;
use tracing_subscriber::{reload, EnvFilter, Registry};

/// Thread-safe accumulator for agent operational metrics.
pub struct AgentMetrics {
    pub start_time: Instant,
    pub claims_processed: AtomicUsize,
    pub claims_approved: AtomicUsize,
    pub claims_rejected: AtomicUsize,
    pub rewards_distributed_axd: Mutex<f64>,
    pub errors_encountered: AtomicUsize,
    pub active_ws_clients: AtomicUsize,
}

impl Default for AgentMetrics {
    fn default() -> Self {
        Self::new()
    }
}

impl AgentMetrics {
    pub fn new() -> Self {
        Self {
            start_time: Instant::now(),
            claims_processed: AtomicUsize::new(0),
            claims_approved: AtomicUsize::new(0),
            claims_rejected: AtomicUsize::new(0),
            rewards_distributed_axd: Mutex::new(0.0),
            errors_encountered: AtomicUsize::new(0),
            active_ws_clients: AtomicUsize::new(0),
        }
    }

    pub fn record_claim_processed(&self, approved: bool, reward: f64) {
        self.claims_processed.fetch_add(1, Ordering::SeqCst);
        if approved {
            self.claims_approved.fetch_add(1, Ordering::SeqCst);
            if let Ok(mut val) = self.rewards_distributed_axd.lock() {
                *val += reward;
            }
        } else {
            self.claims_rejected.fetch_add(1, Ordering::SeqCst);
        }
    }

    pub fn record_error(&self) {
        self.errors_encountered.fetch_add(1, Ordering::SeqCst);
    }
}

/// A wrapper that hides sensitive values (such as private keys or signatures) from formatting outputs.
pub struct Sensitive<T>(pub T);

impl<T: fmt::Display> fmt::Display for Sensitive<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[REDACTED]")
    }
}

impl<T: fmt::Debug> fmt::Debug for Sensitive<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[REDACTED]")
    }
}

/// Redacts 64-character hex strings and common test key patterns in generic text messages.
pub fn redact_secrets(input: &str) -> String {
    static RE_HEX64: OnceLock<Regex> = OnceLock::new();
    let re = RE_HEX64.get_or_init(|| {
        Regex::new(r"\b[0-9a-fA-F]{64}\b").unwrap()
    });
    let redacted = re.replace_all(input, "[REDACTED]");
    redacted
        .replace("MOCK_SECRET_KEY", "[REDACTED]")
        .replace("ENV_SECRET", "[REDACTED]")
        .replace("FILE_SECRET", "[REDACTED]")
        .replace("ENV_PRIORITY", "[REDACTED]")
}

/// Dynamic log level watcher that runs in a background thread to check environment updates or file changes.
pub fn spawn_log_level_watcher(
    repo_root: PathBuf,
    reload_handle: reload::Handle<EnvFilter, Registry>,
) {
    tokio::spawn(async move {
        let interval_sec = std::env::var("LOG_RELOAD_INTERVAL_SEC")
            .ok()
            .and_then(|v| v.parse::<u64>().ok())
            .unwrap_or(5);

        let config_file = repo_root.join(".arx").join("config").join("log_level.txt");
        let mut last_level = String::new();

        loop {
            tokio::time::sleep(std::time::Duration::from_secs(interval_sec)).await;

            let mut current_level = String::new();
            if config_file.exists() {
                if let Ok(content) = std::fs::read_to_string(&config_file) {
                    current_level = content.trim().to_lowercase();
                }
            }
            if current_level.is_empty() {
                if let Ok(env_val) = std::env::var("LOG_LEVEL") {
                    current_level = env_val.trim().to_lowercase();
                }
            }

            if !current_level.is_empty() && current_level != last_level {
                tracing::info!("🔄 Log level config changed to '{}'. Reloading...", current_level);
                match EnvFilter::try_new(&current_level) {
                    Ok(filter) => {
                        if let Err(e) = reload_handle.modify(|f| *f = filter) {
                            tracing::error!("❌ Failed to apply log filter reload: {:?}", e);
                        } else {
                            tracing::info!("✅ Log filter successfully reloaded to '{}'", current_level);
                            last_level = current_level;
                        }
                    }
                    Err(e) => {
                        tracing::error!("❌ Invalid log level filter '{}': {:?}", current_level, e);
                    }
                }
            }
        }
    });
}
