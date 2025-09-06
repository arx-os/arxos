//! ArxOS Core Library
//! 
//! Terminal-based building intelligence routing through RF mesh networks.
//! Core components: ArxObject protocol, mesh networking, compression, and ASCII visualization.

#![allow(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used)]
#![cfg_attr(test, allow(clippy::unwrap_used, clippy::expect_used))]
#![cfg_attr(not(feature = "std"), no_std)]

// ═══════════════════════════════════════════════════════════════════
// CORE ARXOBJECT - The 13-byte fractal building intelligence protocol
// ═══════════════════════════════════════════════════════════════════

pub mod arxobject;
pub use arxobject::{ArxObject, ObjectCategory, ValidationError, object_types};

// ═══════════════════════════════════════════════════════════════════
// MESH NETWORKING - RF-only routing through Meshtastic/LoRa
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod mesh {
    pub mod mesh_network;
    pub mod mesh_network_simple;
    pub mod meshtastic_protocol;
    pub mod mesh_router;
    pub mod branch_mesh_protocol;
}

#[cfg(feature = "std")]
pub use mesh::meshtastic_protocol;

// ═══════════════════════════════════════════════════════════════════
// COMPRESSION - PLY to ArxObject pipeline for massive compression
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod compression;

// ═══════════════════════════════════════════════════════════════════
// TERMINAL VISUALIZATION - ASCII art rendering for terminal UI
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod ascii_renderer_2d;

#[cfg(feature = "std")]
pub mod ascii_bridge;

#[cfg(feature = "std")]
pub mod progressive_renderer;

#[cfg(feature = "std")]
pub mod pixelated_renderer;

// ═══════════════════════════════════════════════════════════════════
// CORE INFRASTRUCTURE - Essential utilities and protocols
// ═══════════════════════════════════════════════════════════════════

pub mod packet;
pub mod detail_store;
pub mod broadcast_scheduler;
pub mod slow_bleed_node;

#[cfg(feature = "std")]
pub mod error;

#[cfg(feature = "std")]
pub mod paths;

#[cfg(feature = "std")]
pub mod crypto;

// ═══════════════════════════════════════════════════════════════════
// FILE STORAGE - No database, just files
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod file_storage;

// ═══════════════════════════════════════════════════════════════════
// ACCESS CONTROL - Simple role-based access for building data
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod simple_access_control;

#[cfg(feature = "std")]
pub mod access_in_practice;

#[cfg(feature = "std")]
pub mod sms_access_token;

// ═══════════════════════════════════════════════════════════════════
// BUILDING INTELLIGENCE - Core building data structures
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod building_repository;

#[cfg(feature = "std")]
pub mod virtual_building_space;

#[cfg(feature = "std")]
pub mod terminal_interface;

#[cfg(feature = "std")]
pub mod terminal_cmms;

// ═══════════════════════════════════════════════════════════════════
// TRANSPORT - Serial/BLE communication with devices
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod transport;

// ═══════════════════════════════════════════════════════════════════
// DOCUMENT PARSING - For importing building data
// ═══════════════════════════════════════════════════════════════════

#[cfg(feature = "std")]
pub mod document_parser;

// ═══════════════════════════════════════════════════════════════════
// EXTRAS MODULE - Optional features moved to separate crate
// ═══════════════════════════════════════════════════════════════════
// Commerce, blockchain, and other non-core features are in arxos-extras

// ═══════════════════════════════════════════════════════════════════
// PUBLIC EXPORTS - Main types for external use
// ═══════════════════════════════════════════════════════════════════

pub use packet::{MeshPacket, ChunkType, DetailChunk};
pub use detail_store::{DetailStore, DetailLevel};
pub use broadcast_scheduler::{BroadcastScheduler, ChunkPriority};
pub use progressive_renderer::{ProgressiveRenderer, render_progress_bar};
pub use slow_bleed_node::{SlowBleedNode, NodeStats, NodeState};

// ═══════════════════════════════════════════════════════════════════
// DEPRECATED/REMOVED
// ═══════════════════════════════════════════════════════════════════
// - SDR Platform: Removed - focus on Meshtastic/LoRa only
// - Education Service: Removed - not core to building intelligence
// - Gaming: Removed - terminal visualization is sufficient
// - Consciousness: Renamed to "fractal generation"
// - Blockchain/BILT: Moved to arxos-extras