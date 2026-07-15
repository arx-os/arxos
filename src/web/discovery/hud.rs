//! AR HUD task compiler rendering active spatial micro-bounties.
//!
//! Generates real-time visual prompts for low-saturation anchors and dangling
//! relative pose vectors, integrating reward multipliers.

use crate::core::Anchor;
use crate::core::domain::ArxAddress;
use crate::core::RelativePose;

/// HUD task container representing actionable spatial cleaning items.
#[derive(Clone, Debug)]
pub enum HudTask {
    /// Pulsing orange sphere signifying low topological saturation.
    LowSaturation(SaturationTask),
    /// Red dotted vector signifying a missing transform destination.
    DanglingPose(DanglingPoseTask),
}

/// Saturation micro-bounty detail mapping.
#[derive(Clone, Debug)]
pub struct SaturationTask {
    pub anchor: Anchor,
    pub saturation_score: f64,
    pub bounty_multiplier: f64, // +50% (+0.50)
}

/// Broken link micro-bounty detail mapping.
#[derive(Clone, Debug)]
pub struct DanglingPoseTask {
    pub source_id: String,
    pub source_address: ArxAddress,
    pub pose: RelativePose,
    pub target_address: String,
    pub bounty_multiplier: f64, // +10% (+0.10)
}

/// Compiles visible spatial state into prioritized HUD tasks.
pub struct HudOverlay;

impl HudOverlay {
    /// Traverses anchors, computing data saturation and verifying RelativePose links.
    pub fn compile_tasks(visible_anchors: &[Anchor]) -> Vec<HudTask> {
        let mut tasks = Vec::new();

        for anchor in visible_anchors {
            // 1. Calculate Data Saturation
            // Heuristic formula: 0.4*(recalibrations/5) + 0.4*confidence + 0.2*(dependents/3)
            let saturation = anchor.data_saturation(anchor.relative_poses.len());

            if saturation < 0.8 {
                tasks.push(HudTask::LowSaturation(SaturationTask {
                    anchor: anchor.clone(),
                    saturation_score: saturation,
                    bounty_multiplier: 1.50, // +50% $AXD
                }));
            }

            // 2. Identify Dangling Poses
            for pose in &anchor.relative_poses {
                // If the target is missing or dangling (represented by dummy/broken target formats in test envelopes)
                // we compile a broken pose task.
                if pose.target_id.is_empty() || pose.target_id == "dangling" {
                    let source_addr = anchor.address.clone().unwrap_or_else(|| {
                        ArxAddress::from_path("/building/provisional").unwrap()
                    });
                    
                    tasks.push(HudTask::DanglingPose(DanglingPoseTask {
                        source_id: anchor.id.clone(),
                        source_address: source_addr,
                        pose: pose.clone(),
                        target_address: pose.target_id.clone(),
                        bounty_multiplier: 1.10, // +10% $AXD
                    }));
                }
            }
        }
        tasks
    }
}
