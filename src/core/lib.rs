//! Arxos Core Library
//! 
//! The heart of the Arxos mesh network - 13-byte ArxObject protocol
//! with slow-bleed progressive enhancement for CAD-level detail

#![forbid(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used)]
#![cfg_attr(test, allow(clippy::unwrap_used, clippy::expect_used))]
#![cfg_attr(not(feature = "std"), no_std)]
// Enforce rf_only at compile time for default builds
#[cfg(all(feature = "std", feature = "rf_only"))]
const _RF_ONLY_BUILD: bool = true;

pub mod arxobject;
#[cfg(feature = "std")]
pub mod paths;
pub mod packet;
pub mod detail_store;
pub mod broadcast_scheduler;
pub mod progressive_renderer;
pub mod slow_bleed_node;
pub mod meshtastic_protocol;
pub mod mesh_network;


#[cfg(feature = "std")]
pub mod error;

// Semantic compression for point cloud processing
#[cfg(feature = "std")]
pub mod compression;

#[cfg(feature = "std")]
pub mod data_consumer_api;

#[cfg(feature = "std")]
pub mod crypto;


// Feature-gated modules (only with std)
#[cfg(feature = "std")]
pub mod document_parser;

#[cfg(feature = "std")]
pub mod point_cloud_parser;

#[cfg(feature = "std")]
pub mod ply_parser;

#[cfg(feature = "std")]
pub mod point_cloud_processor;

#[cfg(feature = "std")]
pub mod point_cloud_parser_enhanced;

// Simplified implementations for testing
// [removed] arxobject_simple export to enforce canonical arxobject

#[cfg(feature = "std")]
pub mod point_cloud_simple;

// Progressive Detail Architecture
#[cfg(feature = "std")]
pub mod progressive_detail;

#[cfg(feature = "std")]
pub mod inference_engine;

#[cfg(feature = "std")]
pub mod transmission_protocol;

// Game and rendering modules
#[cfg(feature = "std")]
pub mod game;

#[cfg(feature = "std")]
pub mod ascii_renderer_2d;

#[cfg(feature = "std")]
pub mod ply_parser_simple;


// REST API removed to enforce RF-only operation

#[cfg(feature = "std")]
pub mod mesh_network_simple;

// Point cloud processing is integrated for compression and routing

// Transport layer for remote access
#[cfg(feature = "std")]
pub mod transport;

// Holographic system moved to research/holographic_arxos/
// Complex quantum processing violates 'stay light' principle


// Note: Heavy persistence operations moved to external services
// ArxOS only stores routing tables and basic state

// ASCII Bridge - Interface between field operations and mesh network
#[cfg(feature = "std")]
pub mod ascii_bridge;

// AR compression and streaming for field technician collaboration
#[cfg(feature = "std")]
pub mod ar_compression;
#[cfg(feature = "std")]
pub mod ar_streaming;

// Pixelated aesthetic rendering pipeline
#[cfg(feature = "std")]
pub mod pixelated_renderer;
#[cfg(feature = "std")]
pub mod aesthetic_pipeline;

// File storage integration
#[cfg(feature = "std")]
pub mod file_storage;

// Mesh Router - Lightweight packet routing for building networks
#[cfg(feature = "std")]
pub mod mesh_router;

// Terminal Interface - Command line for building intelligence
#[cfg(feature = "std")]
pub mod terminal_interface;

// Hypori-inspired concepts adapted for ArxOS
#[cfg(feature = "std")]
pub mod virtual_building_space;
#[cfg(feature = "std")]
pub mod arxos_pixel_stream;
#[cfg(feature = "std")]
pub mod zero_trust_mesh;
#[cfg(feature = "std")]
pub mod offline_workspace_cache;

// Practical field-ready IAM
#[cfg(feature = "std")]
pub mod field_identity_access;
#[cfg(feature = "std")]
pub mod simple_access_control;
#[cfg(feature = "std")]
pub mod access_in_practice;
#[cfg(all(feature = "std", feature = "internet_touchpoints"))]
pub mod sms_access_token;

// Git-like building version control
#[cfg(feature = "std")]
pub mod building_repository;
#[cfg(feature = "std")]
pub mod branch_mesh_protocol;
#[cfg(feature = "std")]
pub mod merge_review_system;

// Terminal-based CMMS
#[cfg(feature = "std")]
pub mod terminal_cmms;
#[cfg(feature = "std")]
pub mod work_order_tabs;
#[cfg(feature = "std")]
pub mod cmms_lifecycle;

// BILT Token and Gamification
#[cfg(feature = "std")]
pub mod bilt_contribution_tracker;
#[cfg(feature = "std")]
pub mod minecraft_terminal;

// Data Broker Feed System (Database-free)
#[cfg(feature = "std")]
pub mod data_broker_feed;
#[cfg(feature = "std")]
pub mod data_aggregator;
#[cfg(feature = "std")]
pub mod report_generator;

// Data Model and Business Logic
#[cfg(feature = "std")]
pub mod data_model_engine;

// SDR Platform and Multi-Service Infrastructure
#[cfg(feature = "std")]
pub mod sdr_platform;

// Radio frame/MTU module
#[cfg(feature = "std")]
pub mod radio { pub mod frame; }
#[cfg(feature = "std")]
pub mod security { pub mod replay; }
#[cfg(feature = "std")]
pub mod invites { pub mod invite; }
#[cfg(feature = "std")]
pub mod radio_secure { pub mod secure_frame; }
#[cfg(feature = "std")]
pub mod radio_adapter { pub mod adapter; }

// Mobile offline binder & transports
#[cfg(all(feature = "std", feature = "mobile_offline"))]
pub mod mobile_offline { pub mod transport; pub mod binder; }

// Re-export the main types
pub use arxobject::{ArxObject, ObjectCategory, ValidationError, object_types, properties};
pub use packet::{MeshPacket, ChunkType, DetailChunk};
pub use detail_store::{DetailStore, DetailLevel};
pub use broadcast_scheduler::{BroadcastScheduler, ChunkPriority};
pub use progressive_renderer::{ProgressiveRenderer, render_progress_bar};
pub use slow_bleed_node::{SlowBleedNode, NodeStats, NodeState};
pub use meshtastic_protocol::{MeshtasticPacket, MeshtasticPacketType, BuildingQuery, MeshtasticProtocolHandler, MockMeshtasticHandler};

#[cfg(feature = "std")]
pub use file_storage::{FileStorage, MemoryDatabase, Database, FileStorageConfig, StorageStats};

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