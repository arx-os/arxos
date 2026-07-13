//! CLI sub-command definitions for the Building compiler surface.

pub mod equipment;
pub mod room;
pub mod spatial;

pub use equipment::EquipmentCommands;
pub use room::RoomCommands;
pub use spatial::SpatialCommands;
