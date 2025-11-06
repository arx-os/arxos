//! Command handler traits for extensible command routing

use crate::cli::Commands;

/// Trait for command handlers that can process CLI commands
pub trait CommandHandler {
    /// Execute the command and return a result
    fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>>;
    
    /// Get the command name this handler processes
    fn command_name(&self) -> &'static str;
    
    /// Check if this handler can process the given command
    fn can_handle(&self, command: &Commands) -> bool;
}

