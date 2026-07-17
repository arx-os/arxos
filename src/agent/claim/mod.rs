//! Ownership Claim Flow manager for transition from provisional staging to verified main.
//!
//! Orchestrates the BuildingClaimed smart contract event listener, IPFS/Arweave
//! download/decryption pipeline, address promotions, and grace window escrow distributions.

pub mod listener;
pub mod reconstructor;
pub mod grace_window;
pub mod rewards;

pub use listener::{ClaimListener, ClaimEvent};
pub use reconstructor::GitReconstructor;
pub use grace_window::{GraceWindowManager, ClaimState};
pub use rewards::RewardReleaser;

/// Central coordinator managing transition states of claimed building twins.
pub struct ClaimManager {
    pub listener: ClaimListener,
    pub reconstructor: GitReconstructor,
    pub grace_manager: GraceWindowManager,
    pub reward_releaser: RewardReleaser,
}

impl Default for ClaimManager {
    fn default() -> Self {
        Self::new()
    }
}

impl ClaimManager {
    pub fn new() -> Self {
        Self {
            listener: ClaimListener::new(),
            reconstructor: GitReconstructor::new(),
            grace_manager: GraceWindowManager::new(),
            reward_releaser: RewardReleaser::new(false),
        }
    }

    /// Process incoming claims, promoting historical data and transitioning branches.
    pub fn handle_incoming_claim(
        &mut self,
        building_id: &str,
        owner_address: &str,
        root_hash: &[u8; 32],
        git_repo_path: &str,
    ) -> Result<(), String> {
        // 1. Download and reconstruct Git tree
        let decrypted_payload = self.reconstructor.fetch_and_verify_payload(building_id, root_hash)?;
        self.reconstructor.reconstruct_history(git_repo_path, &decrypted_payload)?;

        // 2. Lock & set active grace window timer
        self.grace_manager.register_active_claim(building_id.to_string(), 14); // 14 days default

        // 3. Payout first-phase rewards
        self.reward_releaser.release_escrowed_axd(building_id, owner_address, 70.0)?;

        Ok(())
    }
}
