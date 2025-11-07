//! Configuration schema documentation and JSON schema generation
//!
//! This module provides configuration schema documentation and validation
//! schemas for ArxOS configuration.

/// Configuration schema documentation
pub struct ConfigSchema;

impl ConfigSchema {
    /// Get the JSON schema for ArxOS configuration
    ///
    /// Returns a JSON schema string that can be used for validation,
    /// IDE autocomplete, and documentation generation.
    pub fn json_schema() -> &'static str {
        include_str!("../../schemas/config.schema.json")
    }

    /// Get detailed documentation for all configuration options
    pub fn documentation() -> &'static str {
        precedence_documentation()
    }

    /// List all available configuration fields with descriptions
    pub fn field_documentation() -> Vec<ConfigField> {
        vec![
            // User configuration
            ConfigField {
                path: "user.name".to_string(),
                description: "User's full name for commits".to_string(),
                default: "ArxOS User".to_string(),
                example: "John Doe".to_string(),
                env_var: "ARX_USER_NAME".to_string(),
            },
            ConfigField {
                path: "user.email".to_string(),
                description: "User's email address for commits".to_string(),
                default: "user@arxos.com".to_string(),
                example: "john.doe@example.com".to_string(),
                env_var: "ARX_USER_EMAIL".to_string(),
            },
            ConfigField {
                path: "user.organization".to_string(),
                description: "User's organization (optional)".to_string(),
                default: "None".to_string(),
                example: "Acme Corp".to_string(),
                env_var: "ARX_USER_ORGANIZATION".to_string(),
            },
            ConfigField {
                path: "user.commit_template".to_string(),
                description: "Default commit message template".to_string(),
                default: "feat: {operation} {building_name}".to_string(),
                example: "feat: {operation} {building_name}".to_string(),
                env_var: "".to_string(),
            },
            // Path configuration
            ConfigField {
                path: "paths.default_import_path".to_string(),
                description: "Default directory for importing IFC files".to_string(),
                default: "./buildings".to_string(),
                example: "./buildings".to_string(),
                env_var: "ARX_DEFAULT_IMPORT_PATH".to_string(),
            },
            ConfigField {
                path: "paths.backup_path".to_string(),
                description: "Directory for backup files".to_string(),
                default: "./backups".to_string(),
                example: "./backups".to_string(),
                env_var: "ARX_BACKUP_PATH".to_string(),
            },
            ConfigField {
                path: "paths.template_path".to_string(),
                description: "Directory for template files".to_string(),
                default: "./templates".to_string(),
                example: "./templates".to_string(),
                env_var: "".to_string(),
            },
            ConfigField {
                path: "paths.temp_path".to_string(),
                description: "Directory for temporary files".to_string(),
                default: "./temp".to_string(),
                example: "./temp".to_string(),
                env_var: "".to_string(),
            },
            // Building configuration
            ConfigField {
                path: "building.default_coordinate_system".to_string(),
                description: "Default coordinate system for new buildings (WGS84, UTM, LOCAL)"
                    .to_string(),
                default: "WGS84".to_string(),
                example: "LOCAL".to_string(),
                env_var: "".to_string(),
            },
            ConfigField {
                path: "building.auto_commit".to_string(),
                description: "Automatically commit changes to Git".to_string(),
                default: "true".to_string(),
                example: "false".to_string(),
                env_var: "ARX_AUTO_COMMIT".to_string(),
            },
            ConfigField {
                path: "building.naming_pattern".to_string(),
                description: "Default building naming pattern (must include {building_name})"
                    .to_string(),
                default: "{building_name}-{timestamp}".to_string(),
                example: "{building_name}-{timestamp}".to_string(),
                env_var: "".to_string(),
            },
            ConfigField {
                path: "building.validate_on_import".to_string(),
                description: "Validate IFC files on import".to_string(),
                default: "true".to_string(),
                example: "false".to_string(),
                env_var: "".to_string(),
            },
            // Performance configuration
            ConfigField {
                path: "performance.max_parallel_threads".to_string(),
                description: "Maximum number of parallel threads (1-64)".to_string(),
                default: format!("{}", num_cpus::get()),
                example: "4".to_string(),
                env_var: "ARX_MAX_THREADS".to_string(),
            },
            ConfigField {
                path: "performance.memory_limit_mb".to_string(),
                description: "Memory limit in MB (1-16384)".to_string(),
                default: "1024".to_string(),
                example: "2048".to_string(),
                env_var: "ARX_MEMORY_LIMIT_MB".to_string(),
            },
            ConfigField {
                path: "performance.cache_enabled".to_string(),
                description: "Enable caching".to_string(),
                default: "true".to_string(),
                example: "false".to_string(),
                env_var: "".to_string(),
            },
            ConfigField {
                path: "performance.cache_path".to_string(),
                description: "Cache directory path".to_string(),
                default: "./cache".to_string(),
                example: "./cache".to_string(),
                env_var: "".to_string(),
            },
            ConfigField {
                path: "performance.show_progress".to_string(),
                description: "Show progress bars".to_string(),
                default: "true".to_string(),
                example: "false".to_string(),
                env_var: "".to_string(),
            },
            // UI configuration
            ConfigField {
                path: "ui.use_emoji".to_string(),
                description: "Use emoji in output".to_string(),
                default: "true".to_string(),
                example: "false".to_string(),
                env_var: "".to_string(),
            },
            ConfigField {
                path: "ui.verbosity".to_string(),
                description: "Output verbosity level (Silent, Normal, Verbose, Debug)".to_string(),
                default: "Normal".to_string(),
                example: "Verbose".to_string(),
                env_var: "ARX_VERBOSITY".to_string(),
            },
            ConfigField {
                path: "ui.color_scheme".to_string(),
                description: "Color scheme preference (Auto, Always, Never)".to_string(),
                default: "Auto".to_string(),
                example: "Always".to_string(),
                env_var: "".to_string(),
            },
            ConfigField {
                path: "ui.detailed_help".to_string(),
                description: "Show detailed help by default".to_string(),
                default: "false".to_string(),
                example: "true".to_string(),
                env_var: "".to_string(),
            },
        ]
    }
}

/// Documentation for a single configuration field
#[derive(Debug, Clone)]
pub struct ConfigField {
    /// Field path (e.g., "user.name")
    pub path: String,
    /// Field description
    pub description: String,
    /// Default value
    pub default: String,
    /// Example value
    pub example: String,
    /// Environment variable override (if any)
    pub env_var: String,
}

/// Generate configuration precedence documentation
pub fn precedence_documentation() -> &'static str {
    r#"Configuration Precedence (highest to lowest priority):

1. Environment Variables (highest priority)
   - ARX_USER_NAME
   - ARX_USER_EMAIL
   - ARX_USER_ORGANIZATION
   - ARX_AUTO_COMMIT
   - ARX_MAX_THREADS
   - ARX_MEMORY_LIMIT_MB
   - ARX_VERBOSITY

2. Project Config (`.arxos/config.toml` in current directory)
   - Highest file priority
   - Used for project-specific settings

3. User Config (`~/.arxos/config.toml` on Unix, `%APPDATA%\arxos\config.toml` on Windows)
   - User-specific settings
   - Persistent across projects

4. Global Config (`/etc/arxos/config.toml` on Unix, `C:\ProgramData\arxos\config.toml` on Windows)
   - System-wide defaults
   - Lowest file priority

5. Built-in Defaults (lowest priority)
   - Used when no configuration is found
"#
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_field_documentation() {
        let fields = ConfigSchema::field_documentation();
        assert!(!fields.is_empty());
        assert!(fields.len() >= 20); // Should have all fields
    }

    #[test]
    fn test_precedence_documentation() {
        let doc = precedence_documentation();
        assert!(doc.contains("Environment Variables"));
        assert!(doc.contains("Precedence"));
    }
}
