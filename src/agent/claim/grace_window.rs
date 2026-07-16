//! Configuration manager for staging grace window timing.
//!
//! Controls ingestion, directory queuing, and automatic promotion of staging
//! updates reviewed and approved by the building owner.

use std::collections::HashMap;
use std::fs;
use std::path::Path;
use crate::yaml::BuildingYamlSerializer;
use super::rewards::RewardReleaser;

/// Active States of a Claim transaction or contribution.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ClaimState {
    WaitingForOwnerReview,
    Approved,
    Rejected,
    RewardsReleased,
    Failed(String),
}

pub struct GraceWindowManager {
    /// Active claims mapped to expiration timestamps (Unix epoch seconds).
    pub active_claims: HashMap<String, u64>,
}

impl GraceWindowManager {
    pub fn new() -> Self {
        Self {
            active_claims: HashMap::new(),
        }
    }

    /// Register a newly claimed building, setting the grace window duration threshold.
    pub fn register_active_claim(&mut self, building_id: String, duration_days: u32) {
        let now = chrono::Utc::now().timestamp() as u64;
        let expiration = now + (duration_days as u64 * 24 * 60 * 60);
        self.active_claims.insert(building_id, expiration);
    }

    /// Return true if the building's grace window has not expired.
    pub fn is_in_grace_window(&self, building_id: &str) -> bool {
        if let Some(&expiration) = self.active_claims.get(building_id) {
            let now = chrono::Utc::now().timestamp() as u64;
            now < expiration
        } else {
            false
        }
    }

    /// Add a contribution scan payload to the pending review folder.
    pub fn add_pending_contribution(&self, repo_path: &str, provisional_yaml: &str) -> Result<usize, String> {
        let building_id = if let Ok(data) = crate::yaml::BuildingYamlSerializer::deserialize(provisional_yaml) {
            data.building.id.clone()
        } else {
            "unknown".to_string()
        };
        let span = tracing::info_span!("add_pending_contribution", building_id = %building_id);
        let _enter = span.enter();

        let pending_dir = Path::new(repo_path).join(".arx").join("claims").join("pending");
        fs::create_dir_all(&pending_dir).map_err(|e| e.to_string())?;

        // Determine next sequence index
        let mut index = 0;
        while pending_dir.join(format!("{}.yaml", index)).exists() {
            index += 1;
        }

        let filepath = pending_dir.join(format!("{}.yaml", index));
        fs::write(&filepath, provisional_yaml).map_err(|e| e.to_string())?;
        
        tracing::info!(index = index, path = ?filepath, "Stored pending contribution");
        Ok(index)
    }

    /// Retrieve all pending contributions under `.arx/claims/pending/`.
    pub fn list_pending_contributions(&self, repo_path: &str) -> Result<Vec<(usize, String)>, String> {
        let pending_dir = Path::new(repo_path).join(".arx").join("claims").join("pending");
        if !pending_dir.exists() {
            return Ok(Vec::new());
        }

        let mut list = Vec::new();
        for entry in fs::read_dir(pending_dir).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("yaml") {
                if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                    if let Ok(idx) = stem.parse::<usize>() {
                        let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;
                        list.push((idx, content));
                    }
                }
            }
        }
        // Sort by index
        list.sort_by_key(|item| item.0);
        Ok(list)
    }

    /// Review a contribution, applying it on approval or archiving it on rejection.
    pub fn review_pending_contribution(
        &self,
        repo_path: &str,
        building_id: &str,
        index: usize,
        approve: bool,
        owner_address: &str,
        live_mode: bool,
    ) -> Result<(ClaimState, String), String> {
        let span = tracing::info_span!("review_pending_contribution", building_id = %building_id, index = index, approve = approve);
        let _enter = span.enter();

        let pending_path = Path::new(repo_path).join(".arx").join("claims").join("pending").join(format!("{}.yaml", index));
        if !pending_path.exists() {
            return Err(format!("Pending contribution index {} does not exist", index));
        }

        let provisional_yaml = fs::read_to_string(&pending_path).map_err(|e| e.to_string())?;

        if approve {
            tracing::info!("Approving contribution");
            
            // Promote provisional references to main
            let promoted_yaml = self.process_in_flight_contribution(building_id, &provisional_yaml)?;

            // Overwrite authoritative building.yaml
            let filepath = Path::new(repo_path).join("building.yaml");
            fs::write(&filepath, &promoted_yaml).map_err(|e| e.to_string())?;

            // Move to approved folder
            let approved_dir = Path::new(repo_path).join(".arx").join("claims").join("approved");
            fs::create_dir_all(&approved_dir).map_err(|e| e.to_string())?;
            fs::rename(&pending_path, approved_dir.join(format!("{}.yaml", index))).map_err(|e| e.to_string())?;

            // Release AXD rewards
            let releaser = RewardReleaser::new(live_mode);
            let payout_amount = 500.0; // default claim completeness bounty pool
            let payout_receipt = releaser.release_escrowed_axd(building_id, owner_address, payout_amount)?;

            Ok((ClaimState::RewardsReleased, payout_receipt))
        } else {
            tracing::warn!("Rejecting contribution");

            // Move to rejected folder
            let rejected_dir = Path::new(repo_path).join(".arx").join("claims").join("rejected");
            fs::create_dir_all(&rejected_dir).map_err(|e| e.to_string())?;
            fs::rename(&pending_path, rejected_dir.join(format!("{}.yaml", index))).map_err(|e| e.to_string())?;

            Ok((ClaimState::Rejected, "Contribution rejected and archived".to_string()))
        }
    }

    /// Process in-flight contributions, promoting provisional addresses to main.
    pub fn process_in_flight_contribution(&self, building_id: &str, provisional_yaml: &str) -> Result<String, String> {
        if !self.is_in_grace_window(building_id) {
            return Err("Grace Window has expired or claim is unverified".to_string());
        }

        // Deserialize contribution
        let data = BuildingYamlSerializer::deserialize(provisional_yaml)
            .map_err(|e| format!("YAML parse error: {:?}", e))?;
        let mut building = data.into_building();

        // Promote provisional references to active owner twin structure
        building.promote_addresses("building", "main");

        // Reserialize
        let promoted_yaml = BuildingYamlSerializer::serialize_building(&building)
            .map_err(|e| format!("YAML format error: {:?}", e))?;

        Ok(promoted_yaml)
    }
}
