// Configuration management command handlers

use crate::config::{ArxConfig, ConfigError, ConfigManager};

/// Handle configuration command
pub fn handle_config(
    show: bool,
    set: Option<String>,
    reset: bool,
    edit: bool,
    interactive: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if interactive {
        return crate::commands::config_wizard::handle_config_wizard();
    }

    println!("⚙️ ArxOS Configuration");
    println!("{}", "=".repeat(50));

    // Initialize configuration manager
    let mut config_manager = ConfigManager::new().unwrap_or_else(|e| {
        println!("⚠️ Warning: Could not load configuration: {}", e);
        println!("Using default configuration");
        ConfigManager::default()
    });

    if show {
        display_configuration(config_manager.get_config())?;
    } else if let Some(set_value) = set {
        set_configuration_value(&mut config_manager, &set_value)?;
    } else if reset {
        reset_configuration(&mut config_manager)?;
    } else if edit {
        edit_configuration(&mut config_manager)?;
    } else {
        // Default: show configuration
        display_configuration(config_manager.get_config())?;
    }

    Ok(())
}

/// Display current configuration
fn display_configuration(config: &ArxConfig) -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Current Configuration:");
    println!("{}", "-".repeat(30));

    // User configuration
    println!("👤 User:");
    println!("   Name: {}", config.user.name);
    println!("   Email: {}", config.user.email);
    if let Some(ref org) = config.user.organization {
        println!("   Organization: {}", org);
    }
    println!("   Commit Template: {}", config.user.commit_template);

    // Path configuration
    println!("\n📁 Paths:");
    println!(
        "   Import Path: {}",
        config.paths.default_import_path.display()
    );
    println!("   Backup Path: {}", config.paths.backup_path.display());
    println!("   Template Path: {}", config.paths.template_path.display());
    println!("   Temp Path: {}", config.paths.temp_path.display());

    // Building configuration
    println!("\n🏗️ Building:");
    println!(
        "   Coordinate System: {}",
        config.building.default_coordinate_system
    );
    println!("   Auto Commit: {}", config.building.auto_commit);
    println!("   Naming Pattern: {}", config.building.naming_pattern);
    println!(
        "   Validate on Import: {}",
        config.building.validate_on_import
    );

    // Performance configuration
    println!("\n⚡ Performance:");
    println!(
        "   Max Threads: {}",
        config.performance.max_parallel_threads
    );
    println!("   Memory Limit: {} MB", config.performance.memory_limit_mb);
    println!("   Cache Enabled: {}", config.performance.cache_enabled);
    println!("   Show Progress: {}", config.performance.show_progress);

    // UI configuration
    println!("\n🎨 UI:");
    println!("   Use Emoji: {}", config.ui.use_emoji);
    println!("   Verbosity: {:?}", config.ui.verbosity);
    println!("   Color Scheme: {:?}", config.ui.color_scheme);
    println!("   Detailed Help: {}", config.ui.detailed_help);

    Ok(())
}

/// Set a configuration value
fn set_configuration_value(
    config_manager: &mut ConfigManager,
    set_value: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let parts: Vec<&str> = set_value.splitn(2, '=').collect();
    if parts.len() != 2 {
        return Err("Invalid format. Use: section.key=value".into());
    }

    let (key_path, value) = (parts[0], parts[1]);
    let key_parts: Vec<&str> = key_path.split('.').collect();

    if key_parts.len() != 2 {
        return Err("Invalid key format. Use: section.key".into());
    }

    let (section, key) = (key_parts[0], key_parts[1]);

    config_manager.update_config(|config| {
        match section {
            "user" => match key {
                "name" => config.user.name = value.to_string(),
                "email" => config.user.email = value.to_string(),
                "organization" => config.user.organization = Some(value.to_string()),
                "commit_template" => config.user.commit_template = value.to_string(),
                _ => {
                    return Err(ConfigError::ValidationFailed {
                        field: format!("user.{}", key),
                        message: "Unknown user configuration key".to_string(),
                    })
                }
            },
            "building" => match key {
                "auto_commit" => {
                    config.building.auto_commit =
                        value.parse().map_err(|e| ConfigError::ValidationFailed {
                            field: "building.auto_commit".to_string(),
                            message: format!("Invalid boolean value: {}", e),
                        })?;
                }
                "default_coordinate_system" => {
                    config.building.default_coordinate_system = value.to_string()
                }
                "naming_pattern" => config.building.naming_pattern = value.to_string(),
                "validate_on_import" => {
                    config.building.validate_on_import =
                        value.parse().map_err(|e| ConfigError::ValidationFailed {
                            field: "building.validate_on_import".to_string(),
                            message: format!("Invalid boolean value: {}", e),
                        })?;
                }
                _ => {
                    return Err(ConfigError::ValidationFailed {
                        field: format!("building.{}", key),
                        message: "Unknown building configuration key".to_string(),
                    })
                }
            },
            "performance" => match key {
                "max_parallel_threads" => {
                    config.performance.max_parallel_threads =
                        value.parse().map_err(|e| ConfigError::ValidationFailed {
                            field: "performance.max_parallel_threads".to_string(),
                            message: format!("Invalid number: {}", e),
                        })?;
                }
                "memory_limit_mb" => {
                    config.performance.memory_limit_mb =
                        value.parse().map_err(|e| ConfigError::ValidationFailed {
                            field: "performance.memory_limit_mb".to_string(),
                            message: format!("Invalid number: {}", e),
                        })?;
                }
                "cache_enabled" => {
                    config.performance.cache_enabled =
                        value.parse().map_err(|e| ConfigError::ValidationFailed {
                            field: "performance.cache_enabled".to_string(),
                            message: format!("Invalid boolean value: {}", e),
                        })?;
                }
                "show_progress" => {
                    config.performance.show_progress =
                        value.parse().map_err(|e| ConfigError::ValidationFailed {
                            field: "performance.show_progress".to_string(),
                            message: format!("Invalid boolean value: {}", e),
                        })?;
                }
                _ => {
                    return Err(ConfigError::ValidationFailed {
                        field: format!("performance.{}", key),
                        message: "Unknown performance configuration key".to_string(),
                    })
                }
            },
            _ => {
                return Err(ConfigError::ValidationFailed {
                    field: section.to_string(),
                    message: "Unknown configuration section".to_string(),
                })
            }
        }
        Ok(())
    })?;

    println!("✅ Configuration updated: {} = {}", key_path, value);
    Ok(())
}

/// Reset configuration to defaults
fn reset_configuration(
    config_manager: &mut ConfigManager,
) -> Result<(), Box<dyn std::error::Error>> {
    config_manager.update_config(|config| {
        *config = ArxConfig::default();
        Ok(())
    })?;

    println!("✅ Configuration reset to defaults");
    Ok(())
}

/// Edit configuration file
fn edit_configuration(
    config_manager: &mut ConfigManager,
) -> Result<(), Box<dyn std::error::Error>> {
    let config_path = std::env::current_dir()?.join("arx.toml");

    // Create default config file if it doesn't exist
    if !config_path.exists() {
        config_manager.save_to_file(&config_path)?;
        println!("📄 Created configuration file: {}", config_path.display());
    }

    // Try to open with default editor
    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "nano".to_string());
    let status = std::process::Command::new(&editor)
        .arg(&config_path)
        .status()?;

    if status.success() {
        println!("✅ Configuration file edited successfully");
        println!("💡 Run 'arx config --show' to view current configuration");
    } else {
        println!("❌ Failed to edit configuration file");
    }

    Ok(())
}
