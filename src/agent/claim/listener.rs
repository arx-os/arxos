//! Blockchain client listening for BuildingClaimed smart contract events.

/// Emitted payload when an initial zero-knowledge or TLSNotary claim finishes on-chain.
#[derive(Debug, Clone)]
pub struct ClaimEvent {
    pub building_uuid: String,
    pub owner_address: String,
    pub merkle_root: [u8; 32],
    pub git_repo_url: String,
}

#[derive(Default)]
pub struct ClaimListener {
    pub polled_events: Vec<ClaimEvent>,
}

impl ClaimListener {
    pub fn new() -> Self {
        Self::default()
    }

    /// Simulate or poll RPC endpoints for newly emitted BuildingClaimed events.
    pub fn poll_events(&mut self) -> Vec<ClaimEvent> {
        // Swap out accumulated mock events (representing Phase RPC queries)
        std::mem::take(&mut self.polled_events)
    }

    /// Push a simulated event (used for local capture testing and CI).
    pub fn inject_simulated_event(&mut self, event: ClaimEvent) {
        self.polled_events.push(event);
    }
}
