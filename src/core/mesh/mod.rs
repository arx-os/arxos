//! Mesh Networking Module
//! 
//! Pure RF mesh routing through Meshtastic/LoRa networks.
//! No internet required - all communication through radio.

pub mod mesh_network;
pub mod mesh_network_simple;
pub mod meshtastic_protocol;
pub mod mesh_router;
pub mod branch_mesh_protocol;

pub use meshtastic_protocol::{MeshtasticPacket, MeshtasticPacketType, BuildingQuery};
pub use mesh_network::{MeshNode, MeshConfig};
pub use mesh_router::{MeshRouter, Route};