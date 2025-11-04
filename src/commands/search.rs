// Search and filter command handlers

use crate::utils::loading;
use crate::search::{SearchEngine, SearchConfig, FilterConfig, OutputFormat, format_search_results};

/// Handle the search command
pub fn handle_search_command(config: SearchConfig, interactive: bool) -> Result<(), Box<dyn std::error::Error>> {
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
pub fn handle_filter_command(config: FilterConfig, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
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
