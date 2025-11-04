//! Init command handler for creating new buildings from scratch

use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata, BuildingYamlSerializer, CoordinateSystemInfo};
use crate::spatial::Point3D;
use uuid::Uuid;
use chrono::Utc;

/// Configuration for init command
#[derive(Debug, Clone)]
pub struct InitConfig {
    pub name: String,
    pub description: Option<String>,
    pub location: Option<String>,
    pub git_init: bool,
    pub commit: bool,
    pub coordinate_system: String,
    pub units: String,
}

/// Handle the init command
pub fn handle_init(config: InitConfig) -> Result<(), Box<dyn std::error::Error>> {
    println!("🏗️  Initializing new building: {}", config.name);
    
    // Validate building name
    validate_building_name(&config.name)?;
    
    // Create minimal building data
    let building_data = create_minimal_building(&config)?;
    
    // Generate output filename
    let output_file = generate_output_filename(&config.name);
    
    // Write to file
    let serializer = BuildingYamlSerializer::new();
    serializer.write_to_file(&building_data, &output_file)?;
    
    println!("✅ Created building file: {}", output_file);
    println!("   Building ID: {}", building_data.building.id);
    println!("   Created: {}", building_data.building.created_at.format("%Y-%m-%d %H:%M:%S"));
    
    // Initialize Git if requested
    if config.git_init || config.commit {
        initialize_git_for_building(&output_file, &building_data, &config)?;
    }
    
    // Provide next steps
    print_next_steps(&config.name, &output_file);
    
    Ok(())
}

/// Validate building name
pub fn validate_building_name(name: &str) -> Result<(), Box<dyn std::error::Error>> {
    if name.trim().is_empty() {
        return Err("Building name cannot be empty".into());
    }
    
    if name.len() > 100 {
        return Err("Building name too long (max 100 characters)".into());
    }
    
    if name.contains('\0') || name.contains('/') {
        return Err("Building name contains invalid characters".into());
    }
    
    Ok(())
}

/// Create minimal building data structure
fn create_minimal_building(config: &InitConfig) -> Result<BuildingData, Box<dyn std::error::Error>> {
    let now = Utc::now();
    let building_id = Uuid::new_v4().to_string();
    
    // Build description from available metadata
    let description = if let Some(ref desc) = config.description {
        Some(desc.clone())
    } else if let Some(ref loc) = config.location {
        Some(format!("Building at {}", loc))
    } else {
        Some("Building created via arxos init".to_string())
    };
    
    let building_info = BuildingInfo {
        id: building_id.clone(),
        name: config.name.clone(),
        description,
        created_at: now,
        updated_at: now,
        version: "1.0.0".to_string(),
        global_bounding_box: None,
    };
    
    let metadata = BuildingMetadata {
        source_file: None,
        parser_version: "ArxOS v2.0".to_string(),
        total_entities: 0,
        spatial_entities: 0,
        coordinate_system: config.coordinate_system.clone(),
        units: config.units.clone(),
        tags: vec!["manual-creation".to_string(), "init-command".to_string()],
    };
    
    let coordinate_systems = vec![CoordinateSystemInfo {
        name: config.coordinate_system.clone(),
        origin: Point3D::origin(),
        x_axis: Point3D::new(1.0, 0.0, 0.0),
        y_axis: Point3D::new(0.0, 1.0, 0.0),
        z_axis: Point3D::new(0.0, 0.0, 1.0),
        description: Some("Default coordinate system".to_string()),
    }];
    
    Ok(BuildingData {
        building: building_info,
        metadata,
        floors: vec![],
        coordinate_systems,
    })
}

/// Generate output filename from building name
pub fn generate_output_filename(name: &str) -> String {
    format!("{}.yaml",
        name.to_lowercase()
            .replace(" ", "_")
            .replace("/", "-")
            .replace("\\", "-")
    )
}

/// Initialize Git repository for the building
fn initialize_git_for_building(
    _output_file: &str,
    _building_data: &BuildingData,
    _config: &InitConfig,
) -> Result<(), Box<dyn std::error::Error>> {
    // Git integration for init command
    // Uses BuildingGitManager similar to import command when Git repository is initialized
    println!("🔧 Git integration for init command will be available when repository is initialized");
    Ok(())
}

/// Print next steps guidance
fn print_next_steps(building_name: &str, _output_file: &str) {
    println!("\n📚 Next Steps:");
    println!("   1. Add a room:    arxos room create --building \"{}\" --floor 1 --wing A --name \"Main Hall\" --room-type hallway", building_name);
    println!("   2. View building: arxos render --building \"{}\"", building_name);
    println!("   3. Commit:        arxos stage --all && arxos commit \"Initial setup\"");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_building_name_valid() {
        // Test valid names pass
        assert!(validate_building_name("High School Main").is_ok());
        assert!(validate_building_name("Office Building 1").is_ok());
        assert!(validate_building_name("A").is_ok());
    }

    #[test]
    fn test_validate_building_name_empty() {
        // Test empty names are rejected
        let result = validate_building_name("");
        assert!(result.is_err());
        
        let error_msg = result.unwrap_err().to_string();
        assert!(error_msg.contains("cannot be empty"));
    }

    #[test]
    fn test_validate_building_name_whitespace() {
        // Test whitespace-only names are rejected
        let result = validate_building_name("   ");
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_building_name_too_long() {
        // Test names >100 characters are rejected
        let long_name = "a".repeat(101);
        let result = validate_building_name(&long_name);
        assert!(result.is_err());
        
        let error_msg = result.unwrap_err().to_string();
        assert!(error_msg.contains("too long"));
    }

    #[test]
    fn test_validate_building_name_invalid_chars_null() {
        // Test null character is rejected
        let result = validate_building_name("Building\0Name");
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_building_name_invalid_chars_slash() {
        // Test slash character is rejected
        let result = validate_building_name("Building/Name");
        assert!(result.is_err());
    }

    #[test]
    fn test_generate_output_filename() {
        // Test filename generation from building name
        let result = generate_output_filename("High School Main");
        assert_eq!(result, "high_school_main.yaml");
    }

    #[test]
    fn test_generate_output_filename_with_special_chars() {
        // Test filename generation with special characters
        let result = generate_output_filename("Office/Building");
        assert_eq!(result, "office-building.yaml");
    }

    #[test]
    fn test_generate_output_filename_with_backslash() {
        // Test filename generation with backslash
        let result = generate_output_filename("Building\\Main");
        assert_eq!(result, "building-main.yaml");
    }

    #[test]
    fn test_create_minimal_building() {
        // Test creating minimal building data structure
        let config = InitConfig {
            name: "Test Building".to_string(),
            description: None,
            location: None,
            git_init: false,
            commit: false,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
        };
        
        let building_data = create_minimal_building(&config).unwrap();
        
        assert_eq!(building_data.building.name, "Test Building");
        assert_eq!(building_data.floors.len(), 0);
        assert_eq!(building_data.coordinate_systems.len(), 1);
        assert_eq!(building_data.metadata.tags.len(), 2);
        assert!(building_data.metadata.tags.contains(&"manual-creation".to_string()));
        assert!(building_data.metadata.tags.contains(&"init-command".to_string()));
    }

    #[test]
    fn test_create_minimal_building_with_description() {
        // Test with description provided
        let config = InitConfig {
            name: "Test Building".to_string(),
            description: Some("A test building".to_string()),
            location: None,
            git_init: false,
            commit: false,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
        };
        
        let building_data = create_minimal_building(&config).unwrap();
        assert_eq!(building_data.building.description, Some("A test building".to_string()));
    }

    #[test]
    fn test_create_minimal_building_with_location() {
        // Test with location provided but no description
        let config = InitConfig {
            name: "Test Building".to_string(),
            description: None,
            location: Some("123 Main St".to_string()),
            git_init: false,
            commit: false,
            coordinate_system: "World".to_string(),
            units: "meters".to_string(),
        };
        
        let building_data = create_minimal_building(&config).unwrap();
        assert_eq!(building_data.building.description, Some("Building at 123 Main St".to_string()));
    }
}

