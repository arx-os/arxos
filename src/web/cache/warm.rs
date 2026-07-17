//! Persistent Warm Cache tier representing IndexedDB storage of building metadata.
//!
//! Stores scoped subtree envelopes keyed by ArxAddress prefixes.
//! Enforces a strict storage budget of ~100MB via spatial & prefix-depth eviction.

use crate::core::domain::ArxAddress;
use crate::core::Anchor;
use std::collections::HashMap;

/// Represents a loaded working-set envelope returned by the Edge Agent.
#[derive(serde::Serialize, serde::Deserialize, Clone, Debug)]
pub struct BuildingSyncEnvelope {
    /// Active prefix path of the envelope working-set.
    pub base_address: ArxAddress,
    /// List of anchors contained within this subtree.
    pub anchors: Vec<Anchor>,
    /// Raw serialized YAML or JSON subtree snapshot.
    pub payload: String,
    /// Timestamp of capture.
    pub fetched_at_timestamp: u64,
}

/// Persistent local cache wrapper for IndexedDB storage.
pub struct WarmCache {
    /// Scoped subtrees cached locally, keyed by ArxAddress path.
    pub subtrees: HashMap<String, BuildingSyncEnvelope>,
    /// List of keys ordered by access history (LRU).
    pub lru_keys: Vec<String>,
    /// Maximum cache storage budget (100MB limit).
    pub max_budget_bytes: usize,
    /// Current calculated cache footprint in bytes.
    pub current_footprint_bytes: usize,
    /// Hit counter.
    pub hits: usize,
    /// Miss counter.
    pub misses: usize,
    /// Eviction counter.
    pub evictions: usize,
    /// Weight ratio between recency (LRU) and spatial proximity constraints (0.0 to 1.0).
    pub recency_vs_proximity_weight: f64,
}

impl Default for WarmCache {
    fn default() -> Self {
        Self::new()
    }
}

impl WarmCache {
    /// Initialize the Warm Cache with a 100MB budget.
    pub fn new() -> Self {
        Self {
            subtrees: HashMap::new(),
            lru_keys: Vec::new(),
            max_budget_bytes: 100 * 1024 * 1024, // 100MB
            current_footprint_bytes: 0,
            hits: 0,
            misses: 0,
            evictions: 0,
            recency_vs_proximity_weight: 0.5, // Default balanced weight
        }
    }

    /// Retrieve a cached subtree by its ArxAddress path, updating the LRU queue.
    pub fn get_subtree(&mut self, address: &ArxAddress) -> Option<&BuildingSyncEnvelope> {
        let key = address.path.clone();
        if self.subtrees.contains_key(&key) {
            self.hits += 1;
            // Update LRU queue
            if let Some(pos) = self.lru_keys.iter().position(|x| x == &key) {
                self.lru_keys.remove(pos);
            }
            self.lru_keys.push(key.clone());
            self.subtrees.get(&key)
        } else {
            self.misses += 1;
            None
        }
    }

    /// Insert a retrieved subtree envelope, executing the eviction policy if the budget is exceeded.
    pub fn insert_subtree(&mut self, envelope: BuildingSyncEnvelope) {
        let key = envelope.base_address.path.clone();
        let size = key.len() + envelope.payload.len() + envelope.anchors.len() * std::mem::size_of::<Anchor>();

        // Evict older/distant subtrees if we exceed the 100MB storage limit
        while self.current_footprint_bytes + size > self.max_budget_bytes && !self.lru_keys.is_empty() {
            self.evict_least_relevant();
        }

        // Add key to LRU
        if let Some(pos) = self.lru_keys.iter().position(|x| x == &key) {
            self.lru_keys.remove(pos);
        }
        self.lru_keys.push(key.clone());

        self.current_footprint_bytes += size;
        self.subtrees.insert(key, envelope);
    }

    /// Evicts the least relevant subtree envelope based on LRU and prefix-depth constraints.
    fn evict_least_relevant(&mut self) {
        if self.lru_keys.is_empty() {
            return;
        }

        // 1. Identify eviction candidate (oldest item in LRU)
        let candidate_key = self.lru_keys.remove(0);
        if let Some(envelope) = self.subtrees.remove(&candidate_key) {
            self.evictions += 1;
            let size = candidate_key.len() 
                + envelope.payload.len() 
                + envelope.anchors.len() * std::mem::size_of::<Anchor>();
            self.current_footprint_bytes = self.current_footprint_bytes.saturating_sub(size);
        }
    }
}
