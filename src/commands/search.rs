//! Search and filter command handlers
//!
//! Handles search and filtering operations on building data.

use crate::search::{
    format_search_results, FilterConfig, OutputFormat, SearchConfig, SearchEngine,
};
use crate::utils::loading;

/// Handle the search command
///
/// Searches building data for entities matching the query.
///
/// # Arguments
///
/// * `config` - Search configuration specifying query, filters, and options
/// * `interactive` - If `true`, opens interactive search browser; otherwise prints results
///
/// # Returns
///
/// Returns `Ok(())` if search completes successfully, or an error if search fails.
///
/// # Examples
///
/// ```no_run
/// let config = SearchConfig {
///     query: "HVAC".to_string(),
///     search_equipment: true,
///     search_rooms: false,
///     search_buildings: false,
///     case_sensitive: false,
///     use_regex: false,
///     limit: 50,
///     verbose: false,
/// };
/// handle_search_command(config, false)?;
/// ```
pub fn handle_search_command(
    config: SearchConfig,
    interactive: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if interactive {
        return crate::commands::search_browser::handle_search_browser(Some(config.query.clone()));
    }

    println!("🔍 Searching building data for: '{}'", config.query);

    // Load building data
    let building_data = loading::load_building_data("")?;

    // Use the provided search configuration

    // Create search engine and perform search
    let search_engine = SearchEngine::new(&building_data);
    let results = search_engine.search(&config)?;

    // Format and display results
    let output_format = OutputFormat::Table;
    let formatted_results = format_search_results(&results, &output_format, config.verbose);
    println!("{}", formatted_results);

    println!("✅ Search completed");
    Ok(())
}

/// Handle the filter command
///
/// Filters building data based on specified criteria (equipment type, status, floor, room, etc.).
///
/// # Arguments
///
/// * `config` - Filter configuration specifying criteria and output format
/// * `verbose` - If `true`, shows detailed information for each result
///
/// # Returns
///
/// Returns `Ok(())` if filtering completes successfully, or an error if filtering fails.
///
/// # Examples
///
/// ```no_run
/// let config = FilterConfig {
///     equipment_type: Some("HVAC".to_string()),
///     status: Some("Critical".to_string()),
///     floor: Some(2),
///     room: None,
///     building: None,
///     critical_only: false,
///     healthy_only: false,
///     alerts_only: false,
///     format: OutputFormat::Table,
///     limit: 100,
/// };
/// handle_filter_command(config, false)?;
/// ```
pub fn handle_filter_command(
    config: FilterConfig,
    verbose: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Filtering building data...");

    // Load building data
    let building_data = loading::load_building_data("")?;

    // Create search engine and perform filtering
    let search_engine = SearchEngine::new(&building_data);
    let results = search_engine.filter(&config)?;

    // Format and display results
    let formatted_results = format_search_results(&results, &config.format, verbose);
    println!("{}", formatted_results);

    println!("✅ Filter completed");
    Ok(())
}
