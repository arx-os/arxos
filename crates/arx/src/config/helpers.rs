//! Configuration helper utilities
//!
//! This module provides convenient helper functions for common configuration
//! operations throughout the codebase.

use super::{ArxConfig, ConfigManager, ConfigResult};
use std::sync::{Mutex, OnceLock};

/// Global cached configuration manager
///
/// This uses `OnceLock` for thread-safe lazy initialization.
/// The config is loaded once on first access and cached for subsequent calls.
static CACHED_CONFIG: OnceLock<Mutex<ConfigManager>> = OnceLock::new();

/// Initialize the cached configuration manager
fn init_cached_config() -> ConfigManager {
    ConfigManager::new().unwrap_or_else(|_| ConfigManager::default())
}

/// Get the cached configuration manager
fn get_cached_manager() -> &'static Mutex<ConfigManager> {
    CACHED_CONFIG.get_or_init(|| Mutex::new(init_cached_config()))
}

/// Get the current configuration with fallback to defaults
///
/// This is a convenience function that always returns a valid configuration.
/// If configuration loading fails, it returns the default configuration.
///
/// **Performance:** This function uses a cached `ConfigManager` instance to avoid
/// repeated file I/O and parsing. The config is loaded once on first access and
/// cached for subsequent calls, providing significant performance improvements
/// when called multiple times.
///
/// To reload the configuration (e.g., after a config file change), use `reload_global_config()`.
///
/// # Returns
///
/// A cloned copy of the current configuration (merged from all sources) or defaults.
///
/// # Example
///
/// ```rust
/// use arx::config::get_config_or_default;
///
/// let config = get_config_or_default();
/// println!("User: {}", config.user.name);
/// ```
pub fn get_config_or_default() -> ArxConfig {
    get_cached_manager()
        .lock()
        .expect("ConfigManager mutex poisoned")
        .get_config()
        .clone()
}

/// Reload configuration from disk and update the cache
///
/// This function reloads the configuration from all configured sources (project,
/// user, global config files and environment variables) and updates the cached
/// configuration manager. This is useful after modifying configuration files
/// or environment variables.
///
/// **Note:** This reloads the entire configuration. If you need to update specific
/// values, use `ConfigManager::update_config()` instead.
///
/// # Returns
///
/// - `Ok(())` if config loads successfully and cache is updated
/// - `Err(ConfigError)` if config fails to load (cache remains unchanged)
///
/// # Example
///
/// ```rust
/// use arx::config::reload_global_config;
///
/// // Reload config after external changes
/// if let Err(e) = reload_global_config() {
///     eprintln!("Config reload failed: {}", e);
/// }
/// ```
pub fn reload_global_config() -> ConfigResult<()> {
    // Load new configuration
    let new_manager = ConfigManager::new()?;

    // Update the cached manager
    let mut cached = get_cached_manager()
        .lock()
        .expect("ConfigManager mutex poisoned");
    *cached = new_manager;

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
