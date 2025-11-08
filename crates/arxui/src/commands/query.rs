//! Query command handler for ArxAddress glob patterns
//!
//! Handles the `arx query` command for querying equipment by ArxAddress path patterns.

use crate::query::query_addresses;
use crate::utils::loading;

/// Handle the query command
///
/// Queries equipment matching an ArxAddress glob pattern.
///
/// # Arguments
///
/// * `pattern` - Glob pattern for address paths (e.g., "/usa/ny/*/floor-*/mech/boiler-*")
/// * `format` - Output format (table, json, yaml)
/// * `verbose` - Whether to show detailed results
///
/// # Returns
///
/// Returns `Ok(())` if query completes successfully, or an error if query fails.
///
/// # Examples
///
/// ```ignore
/// handle_query_command("/usa/ny/*/floor-*/mech/boiler-*", "table", false)?;
/// ```
pub fn handle_query_command(
    pattern: String,
    format: String,
    verbose: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Querying equipment with pattern: '{}'", pattern);

    // Load building data
    let building_data = loading::load_building_data("")?;

    // Query addresses
    let results = query_addresses(&building_data, &pattern)?;

    if results.is_empty() {
        println!("No equipment found matching pattern: {}", pattern);
        return Ok(());
    }

    println!("Found {} equipment item(s):\n", results.len());

    // Format output based on requested format
    match format.to_lowercase().as_str() {
        "json" => {
            let json = serde_json::to_string_pretty(&results)?;
            println!("{}", json);
        }
        "yaml" => {
            let yaml = serde_yaml::to_string(&results)?;
            println!("{}", yaml);
        }
        _ => {
            // Print table format
            print_table(&results, verbose);
        }
    }

    println!("\n✅ Query completed");
    Ok(())
}

/// Print query results in table format
fn print_table(results: &[crate::query::QueryResult], verbose: bool) {
    if verbose {
        // Detailed table with all fields
        println!("{:-<100}", "");
        println!(
            "{:<20} {:<50} {:<15} {:<10} {:<10}",
            "Name", "Address", "Type", "Floor", "Room"
        );
        println!("{:-<100}", "");

        for result in results {
            let floor_str = result
                .floor
                .map(|f| f.to_string())
                .unwrap_or_else(|| "-".to_string());
            let room_str = result
                .room
                .as_ref()
                .cloned()
                .unwrap_or_else(|| "-".to_string());
            println!(
                "{:<20} {:<50} {:<15} {:<10} {:<10}",
                result.name, result.address, result.equipment_type, floor_str, room_str
            );
        }
        println!("{:-<100}", "");
    } else {
        // Compact table
        println!("{:-<90}", "");
        println!("{:<20} {:<50} {:<15}", "Name", "Address", "Type");
        println!("{:-<90}", "");

        for result in results {
            println!(
                "{:<20} {:<50} {:<15}",
                result.name, result.address, result.equipment_type
            );
        }
        println!("{:-<90}", "");
    }
}
