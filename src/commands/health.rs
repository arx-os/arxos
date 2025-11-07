//! Health check command for ArxOS diagnostics

#[path = "health_dashboard.rs"]
mod health_dashboard;

use std::time::Instant;
use chrono::Utc;

/// Handle health diagnostics for the ArxOS system
pub fn handle_health(component: Option<String>, verbose: bool, interactive: bool, diagnostic: bool) -> Result<(), Box<dyn std::error::Error>> {
    if diagnostic {
        return generate_diagnostic_report(component, verbose);
    }
    if interactive {
        return health_dashboard::handle_health_dashboard();
    }
    println!("🏥 ArxOS Health Check");
    println!("====================");
    
    let start_time = Instant::now();
    let mut all_checks_passed = true;
    
    let component_to_check = component.unwrap_or_else(|| "all".to_string());
    
    match component_to_check.as_str() {
        "git" => {
            if !check_git(verbose) {
                all_checks_passed = false;
            }
        }
        "config" => {
            if !check_config(verbose) {
                all_checks_passed = false;
            }
        }
        "persistence" => {
            if !check_persistence(verbose) {
                all_checks_passed = false;
            }
        }
        "yaml" => {
            if !check_yaml(verbose) {
                all_checks_passed = false;
            }
        }
        _ => {
            if !check_git(verbose) {
                all_checks_passed = false;
            }
            if !check_config(verbose) {
                all_checks_passed = false;
            }
            if !check_persistence(verbose) {
                all_checks_passed = false;
            }
            if !check_yaml(verbose) {
                all_checks_passed = false;
            }
        }
    }
    
    let duration = start_time.elapsed();
    
    println!("\n====================");
    if all_checks_passed {
        println!("✅ All health checks passed in {:?}", duration);
    } else {
        println!("⚠️  Some health checks failed in {:?}", duration);
    }
    
    Ok(())
}

fn check_git(verbose: bool) -> bool {
    println!("\n📦 Git Integration");
    let mut passed = true;
    
    // Check Git availability
    match std::process::Command::new("git").arg("--version").output() {
        Ok(output) => {
            if output.status.success() {
                let version = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if verbose {
                    println!("  ✓ Git available: {}", version);
                } else {
                    println!("  ✓ Git available");
                }
            } else {
                println!("  ✗ Git not available");
                passed = false;
            }
        }
        Err(_) => {
            println!("  ✗ Git not found in PATH");
            passed = false;
        }
    }
    
    // Check git2 crate integration
    match crate::git::BuildingGitManager::new(".", "test", crate::git::GitConfig {
        author_name: "test".to_string(),
        author_email: "test@test.com".to_string(),
        branch: "main".to_string(),
        remote_url: None,
    }) {
        Ok(_) => {
            if verbose {
                println!("  ✓ Git2 crate integration working");
            }
        }
        Err(e) => {
            // Not in a git repo is OK, but other errors are not
            if !e.to_string().contains("not a git repository") {
                println!("  ⚠️  Git2 integration warning: {}", e);
            } else if verbose {
                println!("  ℹ️  Not currently in a git repository");
            }
        }
    }
    
    passed
}

fn check_config(verbose: bool) -> bool {
    println!("\n⚙️  Configuration");
    let passed = true;
    
    // Check config manager
    match crate::config::ConfigManager::new() {
        Ok(config_manager) => {
            let config = config_manager.get_config();
            if verbose {
                println!("  ✓ Configuration loaded");
                println!("     Auto-commit: {:?}", config.building.auto_commit);
            } else {
                println!("  ✓ Configuration loaded");
            }
        }
        Err(e) => {
            println!("  ⚠️  Configuration warning: {}", e);
            if verbose {
                println!("     Using default configuration");
            }
        }
    }
    
    // Check environment variables
    let git_user = std::env::var("GIT_AUTHOR_NAME").ok();
    let git_email = std::env::var("GIT_AUTHOR_EMAIL").ok();
    
    if verbose {
        if let Some(ref name) = git_user {
            println!("  ✓ GIT_AUTHOR_NAME set: {}", name);
        }
        if let Some(ref email) = git_email {
            println!("  ✓ GIT_AUTHOR_EMAIL set: {}", email);
        }
    }
    
    passed
}

fn check_persistence(verbose: bool) -> bool {
    println!("\n💾 Persistence");
    let mut passed = true;
    
    // Check current directory write permissions
    match std::fs::create_dir_all("test_write_check") {
        Ok(_) => {
            if let Err(e) = std::fs::remove_dir("test_write_check") {
                if verbose {
                    println!("  ⚠️  Warning: could not clean up test directory: {}", e);
                }
            }
            if verbose {
                println!("  ✓ Write permissions OK");
            }
        }
        Err(e) => {
            println!("  ✗ Write permissions: {}", e);
            passed = false;
        }
    }
    
    // Check YAML serialization
    use crate::yaml::{BuildingYamlSerializer, BuildingData, BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    
    let test_data = BuildingData {
        building: BuildingInfo {
            id: "test".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "test".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![],
    };
    
    let serializer = BuildingYamlSerializer::new();
    match serializer.to_yaml(&test_data) {
        Ok(_) => {
            if verbose {
                println!("  ✓ YAML serialization working");
            }
        }
        Err(e) => {
            println!("  ✗ YAML serialization failed: {}", e);
            passed = false;
        }
    }
    
    passed
}

fn check_yaml(verbose: bool) -> bool {
    println!("\n📄 YAML Processing");
    let mut passed = true;
    
    // Check YAML parsing with minimal valid structure
    use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata, BuildingYamlSerializer};
    use chrono::Utc;
    
    let test_data = BuildingData {
        building: BuildingInfo {
            id: "test".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "test".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![],
    };
    
    let serializer = BuildingYamlSerializer::new();
    match serializer.to_yaml(&test_data) {
        Ok(yaml_str) => {
            // Now try parsing it back
            match serde_yaml::from_str::<BuildingData>(&yaml_str) {
                Ok(_) => {
                    if verbose {
                        println!("  ✓ YAML round-trip parsing working");
                    } else {
                        println!("  ✓ YAML parsing OK");
                    }
                }
                Err(e) => {
                    println!("  ✗ YAML round-trip parsing failed: {}", e);
                    passed = false;
                }
            }
        }
        Err(e) => {
            println!("  ✗ YAML serialization failed: {}", e);
            passed = false;
        }
    }
    
    passed
}

/// Generate comprehensive diagnostic report
fn generate_diagnostic_report(component: Option<String>, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    let mut report = String::new();
    
    report.push_str("ArxOS Diagnostic Report\n");
    report.push_str(&format!("Generated: {}\n", Utc::now().to_rfc3339()));
    report.push_str(&format!("Version: {}\n", env!("CARGO_PKG_VERSION")));
    report.push_str(&format!("{}\n\n", "=".repeat(60)));
    
    report.push_str("System Information\n");
    report.push_str(&format!("{}\n", "-".repeat(60)));
    report.push_str(&format!("OS: {}\n", std::env::consts::OS));
    report.push_str(&format!("Architecture: {}\n", std::env::consts::ARCH));
    
    if let Ok(output) = std::process::Command::new("rustc").arg("--version").output() {
        if let Ok(version) = String::from_utf8(output.stdout) {
            report.push_str(&format!("Rust Version: {}\n", version.trim()));
        }
    }
    
    if let Ok(output) = std::process::Command::new("git").arg("--version").output() {
        if let Ok(version) = String::from_utf8(output.stdout) {
            report.push_str(&format!("Git Version: {}\n", version.trim()));
        }
    }
    
    report.push('\n');
    
    let component_to_check = component.unwrap_or_else(|| "all".to_string());
    
    match component_to_check.as_str() {
        "git" => {
            report.push_str("Git Integration Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("Git Available: {}\n", check_git_status()));
            report.push_str(&format!("Git Repository: {}\n", check_git_repo_status()));
        }
        "config" => {
            report.push_str("Configuration Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("Configuration Status: {}\n", check_config_status()));
            report.push_str(&format!("Environment Variables: {}\n", check_env_vars()));
        }
        "persistence" => {
            report.push_str("Persistence Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("Write Permissions: {}\n", check_write_permissions()));
            report.push_str(&format!("YAML Serialization: {}\n", check_yaml_serialization()));
        }
        "yaml" => {
            report.push_str("YAML Processing Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("YAML Parsing: {}\n", check_yaml_parsing()));
        }
        _ => {
            report.push_str("Git Integration Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("Git Available: {}\n", check_git_status()));
            report.push_str(&format!("Git Repository: {}\n", check_git_repo_status()));
            report.push('\n');
            
            report.push_str("Configuration Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("Configuration Status: {}\n", check_config_status()));
            report.push_str(&format!("Environment Variables: {}\n", check_env_vars()));
            report.push('\n');
            
            report.push_str("Persistence Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("Write Permissions: {}\n", check_write_permissions()));
            report.push_str(&format!("YAML Serialization: {}\n", check_yaml_serialization()));
            report.push('\n');
            
            report.push_str("YAML Processing Diagnostics\n");
            report.push_str(&format!("{}\n", "-".repeat(60)));
            report.push_str(&format!("YAML Parsing: {}\n", check_yaml_parsing()));
        }
    }
    
    report.push('\n');
    report.push_str("File System Information\n");
    report.push_str(&format!("{}\n", "-".repeat(60)));
    report.push_str(&format!("Current Directory: {}\n", std::env::current_dir()?.display()));
    
    if let Ok(entries) = std::fs::read_dir(".") {
        let yaml_files: Vec<String> = entries
            .filter_map(|e| e.ok())
            .filter(|e| {
                if let Some(name) = e.file_name().to_str() {
                    name.ends_with(".yaml") || name.ends_with(".yml")
                } else {
                    false
                }
            })
            .filter_map(|e| e.file_name().to_str().map(|s| s.to_string()))
            .collect();
        
        if !yaml_files.is_empty() {
            report.push_str(&format!("YAML Files Found: {}\n", yaml_files.join(", ")));
        } else {
            report.push_str("YAML Files Found: None\n");
        }
    }
    
    report.push('\n');
    report.push_str("Configuration File Locations\n");
    report.push_str(&format!("{}\n", "-".repeat(60)));
    
    let home_dir = std::env::var("HOME").unwrap_or_else(|_| "~".to_string());
    let project_config_path = "./.arxos/config.toml";
    let user_config_path = format!("{}/.arxos/config.toml", home_dir);
    
    if std::path::Path::new(project_config_path).exists() {
        report.push_str(&format!("Project Config: ✓ Found ({})\n", project_config_path));
    } else {
        report.push_str(&format!("Project Config: ✗ Not Found ({})\n", project_config_path));
    }
    
    if std::path::Path::new(&user_config_path).exists() {
        report.push_str(&format!("User Config: ✓ Found ({})\n", user_config_path));
    } else {
        report.push_str(&format!("User Config: ✗ Not Found ({})\n", user_config_path));
    }
    
    println!("{}", report);
    
    if verbose {
        let timestamp = Utc::now().format("%Y%m%d-%H%M%S").to_string();
        let report_file = format!("arxos-diagnostic-{}.txt", timestamp);
        std::fs::write(&report_file, &report)?;
        println!("\n📄 Diagnostic report saved to: {}", report_file);
    }
    
    Ok(())
}

fn check_git_status() -> String {
    match std::process::Command::new("git").arg("--version").output() {
        Ok(output) => {
            if output.status.success() {
                String::from_utf8_lossy(&output.stdout).trim().to_string()
            } else {
                "Not Available".to_string()
            }
        }
        Err(_) => "Not Found in PATH".to_string()
    }
}

fn check_git_repo_status() -> String {
    match std::process::Command::new("git").arg("rev-parse").arg("--git-dir").output() {
        Ok(output) => {
            if output.status.success() {
                "Initialized".to_string()
            } else {
                "Not Initialized".to_string()
            }
        }
        Err(_) => "Not Available".to_string()
    }
}

fn check_config_status() -> String {
    match crate::config::ConfigManager::new() {
        Ok(_) => "Loaded Successfully".to_string(),
        Err(e) => format!("Error: {}", e)
    }
}

fn check_env_vars() -> String {
    let mut vars = Vec::new();
    if std::env::var("ARX_USER_NAME").is_ok() {
        vars.push("ARX_USER_NAME");
    }
    if std::env::var("ARX_USER_EMAIL").is_ok() {
        vars.push("ARX_USER_EMAIL");
    }
    if std::env::var("ARX_AUTO_COMMIT").is_ok() {
        vars.push("ARX_AUTO_COMMIT");
    }
    if vars.is_empty() {
        "None Set".to_string()
    } else {
        vars.join(", ")
    }
}

fn check_write_permissions() -> String {
    match std::fs::create_dir_all("test_write_check") {
        Ok(_) => {
            let result = if std::fs::remove_dir("test_write_check").is_ok() {
                "OK"
            } else {
                "Warning: Could not clean up test directory"
            };
            result.to_string()
        }
        Err(e) => format!("Error: {}", e)
    }
}

fn check_yaml_serialization() -> String {
    use crate::yaml::{BuildingYamlSerializer, BuildingData, BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    
    let test_data = BuildingData {
        building: BuildingInfo {
            id: "test".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "test".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![],
    };
    
    let serializer = BuildingYamlSerializer::new();
    match serializer.to_yaml(&test_data) {
        Ok(_) => "Working".to_string(),
        Err(e) => format!("Error: {}", e)
    }
}

fn check_yaml_parsing() -> String {
    use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata, BuildingYamlSerializer};
    use chrono::Utc;
    
    let test_data = BuildingData {
        building: BuildingInfo {
            id: "test".to_string(),
            name: "Test Building".to_string(),
            description: None,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: "1.0".to_string(),
            global_bounding_box: None,
        },
        metadata: BuildingMetadata {
            source_file: None,
            parser_version: "test".to_string(),
            total_entities: 0,
            spatial_entities: 0,
            coordinate_system: "test".to_string(),
            units: "meters".to_string(),
            tags: vec![],
        },
        floors: vec![],
        coordinate_systems: vec![],
    };
    
    let serializer = BuildingYamlSerializer::new();
    match serializer.to_yaml(&test_data) {
        Ok(yaml_str) => {
            match serde_yaml::from_str::<BuildingData>(&yaml_str) {
                Ok(_) => "Working".to_string(),
                Err(e) => format!("Error: {}", e)
            }
        }
        Err(e) => format!("Serialization Error: {}", e)
    }
}
