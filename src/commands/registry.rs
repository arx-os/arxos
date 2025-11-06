//! Command registry for trait-based command routing

use super::traits::CommandHandler;
use super::handlers::*;
use crate::cli::Commands;

/// Registry that maps command names to handlers
pub struct CommandRegistry {
    handlers: Vec<Box<dyn CommandHandler>>,
}

impl CommandRegistry {
    /// Create a new command registry with all default handlers registered
    pub fn new() -> Self {
        let mut registry = Self {
            handlers: Vec::new(),
        };
        registry.register_default_handlers();
        registry
    }
    
    /// Register the default set of command handlers
    fn register_default_handlers(&mut self) {
        self.register(InitHandler);
        self.register(ImportHandler);
        self.register(ExportHandler);
        self.register(SyncHandler);
        self.register(ValidateHandler);
        self.register(QueryHandler);
        self.register(MigrateHandler);
        self.register(DocHandler);
        self.register(VerifyHandler);
    }
    
    /// Register a command handler
    pub fn register<H: CommandHandler + 'static>(&mut self, handler: H) {
        self.handlers.push(Box::new(handler));
    }
    
    /// Find a handler for the given command
    pub fn find_handler(&self, command: &Commands) -> Option<&dyn CommandHandler> {
        self.handlers.iter()
            .find(|h| h.can_handle(command))
            .map(|h| h.as_ref())
    }
    
    /// Execute a command using the registry
    pub fn execute(&self, command: Commands) -> Result<(), Box<dyn std::error::Error>> {
        if let Some(handler) = self.find_handler(&command) {
            handler.execute(command)
        } else {
            Err(format!("No handler found for command").into())
        }
    }
}

impl Default for CommandRegistry {
    fn default() -> Self {
        Self::new()
    }
}

