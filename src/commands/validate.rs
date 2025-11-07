//! Validation command handlers
//!
//! Handles validation of building data files (YAML) and IFC files.

use crate::ifc;
use crate::utils::loading;

/// Handle the validate command
///
/// Validates building data files or IFC files for correctness and structure.
///
/// # Arguments
///
/// * `path` - Optional path to file or directory to validate
///   - If `None`: Validates all YAML files in current directory
///   - If path ends with `.ifc`: Validates as IFC file
///   - Otherwise: Validates as YAML file
///
/// # Returns
///
/// Returns `Ok(())` if validation succeeds, or an error if validation fails.
///
/// # Examples
///
/// ```no_run
/// // Validate all YAML files in current directory
/// handle_validate(None)?;
///
/// // Validate specific IFC file
/// handle_validate(Some("building.ifc".to_string()))?;
///
/// // Validate specific YAML file
/// handle_validate(Some("building.yaml".to_string()))?;
/// ```
pub fn handle_validate(path: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(data_path) = path {
        println!("Validating data at: {}", data_path);

        // Check if it's an IFC file
        if data_path.to_lowercase().ends_with(".ifc") {
            let processor = ifc::IFCProcessor::new();
            match processor.validate_ifc_file(&data_path) {
                Ok(_) => {
                    println!("✅ IFC file validation passed");
                }
                Err(e) => {
                    println!("❌ IFC file validation failed: {}", e);
                }
            }
        } else {
            println!("❌ Unsupported file type. Please provide an .ifc file for validation.");
        }
    } else {
        println!("Validating current directory");

        // Look for YAML files to validate
        let yaml_files = loading::find_yaml_files()?;

        if yaml_files.is_empty() {
            println!("❌ No YAML files found in current directory");
        } else {
            println!("📄 Found {} YAML file(s) to validate", yaml_files.len());

            for yaml_file in yaml_files {
                match loading::validate_yaml_file(&yaml_file) {
                    Ok(_) => {
                        println!("✅ {} - validation passed", yaml_file);
                    }
                    Err(e) => {
                        println!("❌ {} - validation failed: {}", yaml_file, e);
                    }
                }
            }
        }
    }

    Ok(())
}
