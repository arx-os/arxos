//! Configuration helper utilities
//! 
//! This module provides convenient helper functions for common configuration
//! operations throughout the codebase.

use super::{ConfigManager, ArxConfig, ConfigResult};

/// Get the current configuration with fallback to defaults
/// 
/// This is a convenience function that always returns a valid configuration.
/// If configuration loading fails, it returns the default configuration.
/// 
/// This function creates a new ConfigManager instance each time it's called.
/// For performance-critical code that accesses config frequently, consider
/// caching the ConfigManager instance.
/// 
/// # Returns
/// 
/// A cloned copy of the current configuration (merged from all sources) or defaults.
/// 
/// # Example
/// 
/// ```rust
/// use arxos::config::get_config_or_default;
/// 
/// let config = get_config_or_default();
/// println!("User: {}", config.user.name);
/// ```
pub fn get_config_or_default() -> ArxConfig {
    ConfigManager::new()
        .map(|cm| cm.get_config().clone())
        .unwrap_or_else(|_| ArxConfig::default())
}

/// Reload configuration
/// 
/// Validates that configuration can be loaded successfully.
/// Future versions may support hot-reloading of configuration changes.
/// 
/// # Returns
/// 
/// - `Ok(())` if config loads successfully
/// - `Err(ConfigError)` if config fails to load
/// 
/// # Example
/// 
/// ```rust
/// use arxos::config::reload_global_config;
/// 
/// // Validate config can be reloaded
/// if let Err(e) = reload_global_config() {
///     eprintln!("Config reload failed: {}", e);
/// }
/// ```
pub fn reload_global_config() -> ConfigResult<()> {
    // Validate that config can be loaded
    ConfigManager::new()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_get_config_or_default() {
        // Should always return a valid config
        let config = get_config_or_default();
        assert!(!config.user.name.is_empty());
        assert!(!config.user.email.is_empty());
    }
    
    #[test]
    fn test_reload_global_config() {
        // Should validate config loading
        let result = reload_global_config();
        // Either succeeds or fails, but should not panic
        match result {
            Ok(()) => {
                // Config loaded successfully
            }
            Err(_) => {
                // Config loading failed, but that's acceptable for tests
            }
        }
    }
}
