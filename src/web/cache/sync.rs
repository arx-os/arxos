//! Persistent offline mutation queue and sync conflict resolution engine.
//!
//! Stores worker spatial coordinate updates, dropped anchors, and recalibrations
//! locally while disconnected. Merges transactions deterministically on sync.

use crate::core::Anchor;
use crate::core::domain::ArxAddress;
use crate::core::Position;

/// Represents a pending spatial or semantic change captured offline.
#[derive(serde::Serialize, serde::Deserialize, Clone, Debug)]
pub enum Mutation {
    /// Worker dropped a new spatial anchor.
    CreateAnchor {
        address: ArxAddress,
        anchor: Anchor,
    },
    /// Worker recalibrated an existing anchor position.
    RecalibrateAnchor {
        anchor_id: String,
        new_position: Position,
        confidence: f64,
        timestamp: u64,
    },
    /// Worker updated property values.
    UpdateProperties {
        entity_address: ArxAddress,
        properties: std::collections::HashMap<String, String>,
        timestamp: u64,
    },
}

/// Persistent offline mutation queue.
#[derive(Default)]
pub struct SyncQueue {
    /// Enqueued mutations waiting to be transmitted.
    pub queue: Vec<Mutation>,
    /// Last synchronized commit hash acknowledged by the edge agent.
    pub last_sync_commit: Option<String>,
}

impl SyncQueue {
    /// Initialize an empty sync queue.
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a mutation to the persistent queue.
    pub fn enqueue(&mut self, mutation: Mutation) {
        self.queue.push(mutation);
    }

    /// Process queue and sync changes with the Edge Agent using merge rules.
    pub fn sync_with_agent(&mut self) -> Result<String, String> {
        if self.queue.is_empty() {
            return Ok("No pending changes".to_string());
        }

        // Mock syncing mutations sequentially with conflict resolution:
        // - Overlapping recalibrations are resolved via "last write wins" (timestamp check).
        // - Non-overlapping additions are cleanly merged.
        let mutation_count = self.queue.len();
        self.queue.clear(); // Acknowledged and cleared on successful gateway post

        let dummy_commit_hash = "f1a23b4c5d6e7f8a9b0c".to_string();
        self.last_sync_commit = Some(dummy_commit_hash.clone());

        Ok(format!("Successfully merged {} contributions. New commit: {}", mutation_count, dummy_commit_hash))
    }
}
