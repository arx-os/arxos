//! Binary Asset Cache tier for storing heavy SLAM maps, mesh fragments, and point clouds.
//!
//! Enforces its own dedicated 200MB storage limit, remaining separate from the
//! metadata Warm Cache budget. Integrates with the Anchor's type-safe MapRef enum.

use crate::core::MapRef;
use std::collections::HashMap;

/// Manages loading and caching of heavy binary spatial descriptors (.map).
pub struct BinaryAssetCache {
    /// In-memory or OPFS binary cache maps, keyed by serialized MapRef string.
    pub assets: HashMap<String, Vec<u8>>,
    /// Access tracking (LRU) for asset eviction.
    pub lru_keys: Vec<String>,
    /// Limit for binary assets (200MB).
    pub max_budget_bytes: usize,
    /// Current calculated footprint in bytes.
    pub current_footprint_bytes: usize,
    /// Hit counter.
    pub hits: usize,
    /// Miss counter.
    pub misses: usize,
    /// Eviction counter.
    pub evictions: usize,
    /// Last load latency in milliseconds.
    pub last_latency_ms: u64,
}

impl Default for BinaryAssetCache {
    fn default() -> Self {
        Self::new()
    }
}

impl BinaryAssetCache {
    /// Initialize the Binary Asset Cache with a 200MB budget.
    pub fn new() -> Self {
        Self {
            assets: HashMap::new(),
            lru_keys: Vec::new(),
            max_budget_bytes: 200 * 1024 * 1024, // 200MB
            current_footprint_bytes: 0,
            hits: 0,
            misses: 0,
            evictions: 0,
            last_latency_ms: 0,
        }
    }

    /// Hydrate a binary SLAM/feature map on-demand based on its MapRef source.
    pub fn load_asset(&mut self, map_ref: &MapRef) -> Result<Vec<u8>, String> {
        let key = map_ref.to_string();

        if let Some(data) = self.assets.get(&key) {
            self.hits += 1;
            // Update LRU queue
            if let Some(pos) = self.lru_keys.iter().position(|x| x == &key) {
                self.lru_keys.remove(pos);
            }
            self.lru_keys.push(key);
            return Ok(data.clone());
        }

        self.misses += 1;
        let start_time = chrono::Utc::now().timestamp_millis();

        // Implement simple retry loop for transient failures (e.g. gateway timeouts)
        let mut attempts = 0;
        let max_attempts = 3;
        let mut fetched_data = None;

        while attempts < max_attempts {
            attempts += 1;
            // Simulated transient failure (e.g. succeeds on second attempt, or mock success)
            let result = match map_ref {
                MapRef::GitLfs { path } => {
                    Ok(format!("Mock Git LFS binary map data from: {}", path).into_bytes())
                }
                MapRef::Ipfs { cid } => {
                    if attempts == 1 {
                        Err("Gateway timeout".to_string())
                    } else {
                        Ok(format!("Mock IPFS binary map data for CID: {}", cid).into_bytes())
                    }
                }
                MapRef::Arweave { tx_id } => {
                    Ok(format!("Mock Arweave binary map data for Tx: {}", tx_id).into_bytes())
                }
                MapRef::Local { path } => {
                    Ok(format!("Mock Local file binary map data at: {}", path).into_bytes())
                }
            };

            match result {
                Ok(data) => {
                    fetched_data = Some(data);
                    break;
                }
                Err(e) if attempts == max_attempts => {
                    return Err(format!("Failed loading after {} attempts: {}", max_attempts, e));
                }
                Err(_) => {
                    // Backoff / retry
                    continue;
                }
            }
        }

        let data = fetched_data.ok_or_else(|| "Unknown load error".to_string())?;
        let end_time = chrono::Utc::now().timestamp_millis();
        self.last_latency_ms = (end_time - start_time).max(0) as u64;

        // Cache the newly fetched binary asset
        self.insert_asset(key, data.clone());
        Ok(data)
    }

    /// Cache a binary map, evicting the least recently used binary maps if we exceed 200MB.
    pub fn insert_asset(&mut self, key: String, data: Vec<u8>) {
        let size = key.len() + data.len();

        while self.current_footprint_bytes + size > self.max_budget_bytes && !self.lru_keys.is_empty() {
            let victim = self.lru_keys.remove(0);
            if let Some(removed) = self.assets.remove(&victim) {
                self.evictions += 1;
                self.current_footprint_bytes = self.current_footprint_bytes.saturating_sub(victim.len() + removed.len());
            }
        }

        if let Some(pos) = self.lru_keys.iter().position(|x| x == &key) {
            self.lru_keys.remove(pos);
        }
        self.lru_keys.push(key.clone());

        self.current_footprint_bytes += size;
        self.assets.insert(key, data);
    }
}
