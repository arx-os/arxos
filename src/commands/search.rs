// Search and filter command handlers

use crate::utils::loading;
use crate::search::{SearchEngine, SearchConfig, FilterConfig, OutputFormat, format_search_results};

/// Handle the search command
pub fn handle_search_command(
    query: String,
    equipment: bool,
    rooms: bool,
    buildings: bool,
    case_sensitive: bool,
    regex: bool,
    limit: usize,
    verbose: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Searching building data for: '{}'", query);
    
    // Load building data
    let building_data = loading::load_building_data("")?;
    
    // Create search configuration
    let search_config = SearchConfig {
        query,
        search_equipment: equipment || (!equipment && !rooms && !buildings), // Default to equipment if none specified
        search_rooms: rooms,
        search_buildings: buildings,
        case_sensitive,
        use_regex: regex,
        limit,
        verbose,
    };
    
    // Create search engine and perform search
    let search_engine = SearchEngine::new(&building_data);
    let results = search_engine.search(&search_config)?;
    
    // Format and display results
    let output_format = OutputFormat::Table;
    let formatted_results = format_search_results(&results, &output_format, verbose);
    println!("{}", formatted_results);
    
    println!("✅ Search completed");
    Ok(())
}

/// Handle the filter command
pub fn handle_filter_command(
    equipment_type: Option<String>,
    status: Option<String>,
    floor: Option<i32>,
    room: Option<String>,
    building: Option<String>,
    critical_only: bool,
    healthy_only: bool,
    alerts_only: bool,
    format: String,
    limit: usize,
    verbose: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Filtering building data...");
    
    // Load building data
    let building_data = loading::load_building_data("")?;
    
    // Create filter configuration
    let filter_config = FilterConfig {
        equipment_type,
        status,
        floor,
        room,
        building,
        critical_only,
        healthy_only,
        alerts_only,
        format: OutputFormat::from(format),
        limit,
    };
    
    // Create search engine and perform filtering
    let search_engine = SearchEngine::new(&building_data);
    let results = search_engine.filter(&filter_config)?;
    
    // Format and display results
    let formatted_results = format_search_results(&results, &filter_config.format, verbose);
    println!("{}", formatted_results);
    
    println!("✅ Filter completed");
    Ok(())
}
