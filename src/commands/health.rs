//! Health check command for ArxOS diagnostics

#[path = "health_dashboard.rs"]
mod health_dashboard;

use std::time::Instant;

/// Handle health diagnostics for the ArxOS system
pub fn handle_health(component: Option<String>, verbose: bool, interactive: bool) -> Result<(), Box<dyn std::error::Error>> {
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
        "all" | _ => {
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
