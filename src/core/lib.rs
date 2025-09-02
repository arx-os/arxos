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
pub mod meshtastic_protocol;
pub mod mesh_network;

#[cfg(feature = "std")]
pub mod database;

// Semantic compression moved to external_services/point_cloud_processor/
// ArxOS routes, doesn't process

#[cfg(feature = "std")]
pub mod mesh_network;

#[cfg(feature = "std")]
pub mod data_consumer_api;

#[cfg(feature = "std")]
pub mod crypto;

#[cfg(feature = "std")]
pub mod database_impl;

// Feature-gated modules (only with std)
#[cfg(feature = "std")]
pub mod document_parser;

// Point cloud processing moved to external_services/point_cloud_processor/
// ArxOS receives ASCII descriptions, doesn't process point clouds

// Transport layer for remote access
#[cfg(feature = "std")]
pub mod transport;

// Holographic system moved to research/holographic_arxos/
// Complex quantum processing violates 'stay light' principle

// Persistence layer for SQLite storage
#[cfg(feature = "std")]
pub mod persistence;

// Note: Heavy persistence operations moved to external services
// ArxOS only stores routing tables and basic state

// ASCII Bridge - Interface between field operations and mesh network
#[cfg(feature = "std")]
pub mod ascii_bridge;

// Mesh Router - Lightweight packet routing for building networks
#[cfg(feature = "std")]
pub mod mesh_router;

// Terminal Interface - Command line for building intelligence
#[cfg(feature = "std")]
pub mod terminal_interface;

// Re-export the main types
pub use arxobject::{ArxObject, ObjectCategory, ValidationError, object_types, properties};
pub use packet::{MeshPacket, ChunkType, DetailChunk};
pub use detail_store::{DetailStore, DetailLevel};
pub use broadcast_scheduler::{BroadcastScheduler, ChunkPriority};
pub use progressive_renderer::{ProgressiveRenderer, render_progress_bar};
pub use slow_bleed_node::{SlowBleedNode, NodeStats, NodeState};
pub use meshtastic_protocol::{MeshtasticPacket, MeshtasticPacketType, BuildingQuery, MeshtasticProtocolHandler, MockMeshtasticHandler};

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

#[cfg(all(test, feature = "std"))]
mod integration_test;