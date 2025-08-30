//! Arxos Core Library
//! 
//! The heart of the Arxos mesh network - 13-byte ArxObject protocol
//! with slow-bleed progressive enhancement for CAD-level detail

#![cfg_attr(not(feature = "std"), no_std)]

pub mod arxobject;
pub mod packet;
pub mod detail_store;
pub mod broadcast_scheduler;
pub mod progressive_renderer;
pub mod slow_bleed_node;

// Re-export the main types
pub use arxobject::{ArxObject, ObjectCategory, ValidationError, object_types, properties};
pub use packet::{MeshPacket, ChunkType, DetailChunk};
pub use detail_store::{DetailStore, DetailLevel};
pub use broadcast_scheduler::{BroadcastScheduler, ChunkPriority};
pub use progressive_renderer::{ProgressiveRenderer, render_progress_bar};
pub use slow_bleed_node::{SlowBleedNode, NodeStats, NodeState};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arxobject_size() {
        assert_eq!(core::mem::size_of::<ArxObject>(), 13);
    }

    #[test]
    fn test_round_trip() {
        let obj = ArxObject::new(0x4A7B, object_types::OUTLET, 1000, 2000, 1500);
        let bytes = obj.to_bytes();
        let restored = ArxObject::from_bytes(&bytes);
        assert_eq!(obj, restored);
    }
}