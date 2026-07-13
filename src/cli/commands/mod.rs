//! CLI command implementations for the Building compiler surface.

pub mod command_trait;
pub mod data;
pub mod edit;
pub mod export;
pub mod git;
pub mod import;
pub mod import_lidar;
pub mod init;
pub mod merge;
pub mod migrate;
pub mod query;

#[cfg(feature = "tui")]
pub mod search;

pub use command_trait::Command;
pub use export::ExportCommand;
pub use import::ImportCommand;
pub use init::InitCommand;
pub use merge::MergeCommand;
pub use migrate::MigrateCommand;

#[cfg(feature = "tui")]
pub use search::SearchCommand;

#[cfg(feature = "agent")]
pub mod remote;
#[cfg(feature = "agent")]
pub use remote::RemoteCommand;
