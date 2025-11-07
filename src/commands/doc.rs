//! Documentation generation command handler
//!
//! Handles the `arx doc` command for generating HTML documentation from building data.

use crate::docs::generate_building_docs;
use log::info;

/// Handle the doc command
///
/// Generates HTML documentation for a building and writes it to a file.
///
/// # Parameters
///
/// * `building` - Name of the building to document
/// * `output` - Optional output file path (default: `./docs/{building}.html`)
///
/// # Returns
///
/// Returns a `Result` indicating success or failure.
///
/// # Errors
///
/// This function can return errors for:
/// * Building data not found
/// * Invalid building data
/// * File system errors
pub fn handle_doc(
    building: String,
    output: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("📚 Generating documentation for building: {}", building);
    println!("📚 Generating documentation for building: {}", building);

    let output_path = output.as_deref();
    let generated_path = generate_building_docs(&building, output_path)?;

    println!("✅ Documentation generated successfully");
    println!("   Location: {}", generated_path);
    println!("   Open in browser to view");

    Ok(())
}
