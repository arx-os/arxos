//! CLI sub-command definitions
//!
//! This module contains all sub-command enums for the ArxOS CLI,
//! organized by domain.

pub mod ar;
pub mod economy;
pub mod equipment;
pub mod game;
pub mod ifc;
pub mod room;
pub mod spatial;
pub mod spreadsheet;
pub mod users;

// Re-export all sub-command enums
pub use ar::ArCommands;
pub use economy::EconomyCommands;
pub use equipment::EquipmentCommands;
pub use game::GameCommands;
pub use ifc::IfcCommands;
pub use room::RoomCommands;
pub use spatial::SpatialCommands;
pub use spreadsheet::SpreadsheetCommands;
pub use users::UsersCommands;
