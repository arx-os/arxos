//! Command trait for CLI command pattern
//!
//! Provides a common interface for all CLI commands, enabling
//! consistent execution and error handling.

use std::error::Error;

/// Command execution trait
///
/// Implement this trait for all CLI commands to provide consistent
/// execution semantics and error handling.
///
/// # Example
///
/// ```ignore
/// use crate::cli::commands::Command;
///
/// pub struct BuildCommand {
///     pub name: String,
/// }
///
/// impl Command for BuildCommand {
///     fn execute(&self) -> Result<(), Box<dyn Error>> {
///         println!("Building: {}", self.name);
///         Ok(())
///     }
/// }
/// ```
pub trait Command {
    /// Execute the command
    ///
    /// # Returns
    ///
    /// Ok(()) on success, or an error describing what went wrong
    fn execute(&self) -> Result<(), Box<dyn Error>>;

    /// Get command name (optional, for logging/debugging)
    fn name(&self) -> &'static str {
        "unknown"
    }

    /// Validate command arguments before execution (optional)
    fn validate(&self) -> Result<(), Box<dyn Error>> {
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestCommand {
        should_fail: bool,
    }

    impl Command for TestCommand {
        fn execute(&self) -> Result<(), Box<dyn Error>> {
            if self.should_fail {
                Err("Test failure".into())
            } else {
                Ok(())
            }
        }

        fn name(&self) -> &'static str {
            "test"
        }
    }

    #[test]
    fn test_command_success() {
        let cmd = TestCommand { should_fail: false };
        assert!(cmd.execute().is_ok());
        assert_eq!(cmd.name(), "test");
    }

    #[test]
    fn test_command_failure() {
        let cmd = TestCommand { should_fail: true };
        assert!(cmd.execute().is_err());
    }
}
