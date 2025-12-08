//! CLI commands module

pub mod building;
pub mod catalog;
pub mod command_trait;
pub mod data;
pub mod git;
pub mod maintenance;
pub mod merge;
pub mod query;
pub mod rendering;
pub mod import;
pub mod export;
pub mod init;
pub mod sync;
#[cfg(feature = "tui")]
pub mod search;

pub use catalog::*;
pub use command_trait::Command;
pub use merge::MergeCommand;
pub use import::ImportCommand;
pub use export::ExportCommand;
pub use init::InitCommand;
pub use sync::SyncCommand;
#[cfg(feature = "tui")]
pub use search::SearchCommand;
#[cfg(feature = "agent")]
pub mod remote;
#[cfg(feature = "agent")]
pub use remote::RemoteCommand;
