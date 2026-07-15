//! Task Resolver executing AR HUD micro-bounty completion workflows.
//!
//! Exposes mutation handlers that update spatial poses, drop new anchor entities,
//! and enqueue local-first transactions into the persistent Sync Queue.

use crate::core::Anchor;
use crate::core::domain::ArxAddress;
use crate::core::Position;
use crate::web::cache::SyncQueue;
use crate::web::cache::sync::Mutation;

/// Resolves active spatial tasks, transforming them into persistent mutators.
pub struct TaskResolver;

impl TaskResolver {
    /// Handler: Recalibrate an existing anchor's position, increasing confidence.
    pub fn recalibrate_anchor(
        anchor_id: &str,
        new_coords: Position,
        new_confidence: f64,
        sync_queue: &mut SyncQueue,
    ) {
        let mutation = Mutation::RecalibrateAnchor {
            anchor_id: anchor_id.to_string(),
            new_position: new_coords,
            confidence: new_confidence,
            timestamp: chrono::Utc::now().timestamp() as u64,
        };
        sync_queue.enqueue(mutation);
    }

    /// Handler Option A: Resolve dangling RelativePose by linking to an adjacent equipment ID.
    pub fn resolve_pose_link_to_equipment(
        source_address: ArxAddress,
        mut anchor: Anchor,
        pose_index: usize,
        target_equipment_address: ArxAddress,
        sync_queue: &mut SyncQueue,
    ) {
        if pose_index < anchor.relative_poses.len() {
            // Update the target ID/address of the RelativePose
            anchor.relative_poses[pose_index].target_id = target_equipment_address.path.clone();
            
            // Queue properties update containing modified pose vector
            let mut props = std::collections::HashMap::new();
            props.insert("resolved_transform".to_string(), target_equipment_address.path);

            let mutation = Mutation::UpdateProperties {
                entity_address: source_address,
                properties: props,
                timestamp: chrono::Utc::now().timestamp() as u64,
            };
            sync_queue.enqueue(mutation);
        }
    }

    /// Handler Option B: Resolve dangling RelativePose by creating a new spatial Anchor.
    pub fn resolve_pose_create_new_anchor(
        source_address: ArxAddress,
        mut anchor: Anchor,
        pose_index: usize,
        new_anchor_id: &str,
        new_anchor_coords: Position,
        sync_queue: &mut SyncQueue,
    ) {
        // Create new target Anchor
        let new_anchor = Anchor::new(
            new_anchor_id.to_string(),
            new_anchor_coords,
            1.0, // Initial confidence
        );

        let new_addr = source_address.path.split('/')
            .take(4)
            .collect::<Vec<&str>>()
            .join("/");
        let new_anchor_address = ArxAddress::from_path(&format!("{}/{}", new_addr, new_anchor_id)).unwrap();

        // 1. Enqueue new Anchor creation mutation
        sync_queue.enqueue(Mutation::CreateAnchor {
            address: new_anchor_address.clone(),
            anchor: new_anchor,
        });

        // 2. Link existing RelativePose to this new Anchor
        if pose_index < anchor.relative_poses.len() {
            anchor.relative_poses[pose_index].target_id = new_anchor_address.path.clone();
            
            let mut props = std::collections::HashMap::new();
            props.insert("resolved_anchor_link".to_string(), new_anchor_address.path);

            sync_queue.enqueue(Mutation::UpdateProperties {
                entity_address: source_address,
                properties: props,
                timestamp: chrono::Utc::now().timestamp() as u64,
            });
        }
    }
}
