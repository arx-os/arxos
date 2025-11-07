//! Formatting functions for search results

use super::types::{OutputFormat, SearchResult};

/// Format search results for display with highlighting
pub fn format_search_results(
    results: &[SearchResult],
    format: &OutputFormat,
    verbose: bool,
) -> String {
    match format {
        OutputFormat::Table => format_table_results(results, verbose),
        OutputFormat::Json => {
            serde_json::to_string_pretty(results).unwrap_or_else(|_| "[]".to_string())
        }
        OutputFormat::Yaml => serde_yaml::to_string(results).unwrap_or_else(|_| "[]".to_string()),
    }
}

/// Format search results with query highlighting
pub fn format_search_results_with_highlight(
    results: &[SearchResult],
    query: &str,
    format: &OutputFormat,
    verbose: bool,
) -> String {
    match format {
        OutputFormat::Table => format_table_results_with_highlight(results, query, verbose),
        OutputFormat::Json => {
            serde_json::to_string_pretty(results).unwrap_or_else(|_| "[]".to_string())
        }
        OutputFormat::Yaml => serde_yaml::to_string(results).unwrap_or_else(|_| "[]".to_string()),
    }
}

/// Format results as a table
fn format_table_results(results: &[SearchResult], verbose: bool) -> String {
    if results.is_empty() {
        return "No results found.".to_string();
    }

    let mut output = String::new();

    if verbose {
        // Detailed table format
        output.push_str(&format!(
            "{:<12} {:<20} {:<30} {:<15} {:<10} {:<15} {:<10}\n",
            "Type", "Name", "Path", "Building", "Floor", "Room", "Status"
        ));
        output.push_str(&format!(
            "{:-<12} {:-<20} {:-<30} {:-<15} {:-<10} {:-<15} {:-<10}\n",
            "", "", "", "", "", "", ""
        ));

        for result in results {
            output.push_str(&format!(
                "{:<12} {:<20} {:<30} {:<15} {:<10} {:<15} {:<10}\n",
                result.item_type,
                result.name,
                result.path,
                result.building.as_deref().unwrap_or("-"),
                result
                    .floor
                    .map(|f| f.to_string())
                    .unwrap_or("-".to_string()),
                result.room.as_deref().unwrap_or("-"),
                result.status.as_deref().unwrap_or("-")
            ));
        }
    } else {
        // Simple table format
        output.push_str(&format!("{:<12} {:<20} {:<30}\n", "Type", "Name", "Path"));
        output.push_str(&format!("{:-<12} {:-<20} {:-<30}\n", "", "", ""));

        for result in results {
            output.push_str(&format!(
                "{:<12} {:<20} {:<30}\n",
                result.item_type, result.name, result.path
            ));
        }
    }

    output.push_str(&format!("\nFound {} results.\n", results.len()));
    output
}

/// Format results as a table with highlighting
fn format_table_results_with_highlight(
    results: &[SearchResult],
    query: &str,
    verbose: bool,
) -> String {
    if results.is_empty() {
        return "No results found.".to_string();
    }

    let mut output = String::new();

    if verbose {
        // Detailed table format with highlighting
        output.push_str(&format!(
            "{:<12} {:<20} {:<30} {:<15} {:<10} {:<15} {:<10}\n",
            "Type", "Name", "Path", "Building", "Floor", "Room", "Status"
        ));
        output.push_str(&format!(
            "{:-<12} {:-<20} {:-<30} {:-<15} {:-<10} {:-<15} {:-<10}\n",
            "", "", "", "", "", "", ""
        ));

        for result in results {
            let highlighted_name = highlight_text(&result.name, query);
            let highlighted_path = highlight_text(&result.path, query);

            output.push_str(&format!(
                "{:<12} {:<20} {:<30} {:<15} {:<10} {:<15} {:<10}\n",
                result.item_type,
                highlighted_name,
                highlighted_path,
                result.building.as_deref().unwrap_or("-"),
                result
                    .floor
                    .map(|f| f.to_string())
                    .unwrap_or("-".to_string()),
                result.room.as_deref().unwrap_or("-"),
                result.status.as_deref().unwrap_or("-")
            ));
        }
    } else {
        // Simple table format with highlighting
        output.push_str(&format!("{:<12} {:<20} {:<30}\n", "Type", "Name", "Path"));
        output.push_str(&format!("{:-<12} {:-<20} {:-<30}\n", "", "", ""));

        for result in results {
            let highlighted_name = highlight_text(&result.name, query);
            let highlighted_path = highlight_text(&result.path, query);

            output.push_str(&format!(
                "{:<12} {:<20} {:<30}\n",
                result.item_type, highlighted_name, highlighted_path
            ));
        }
    }

    output.push_str(&format!("\nFound {} results.\n", results.len()));
    output
}

/// Highlight matching text in a string
fn highlight_text(text: &str, query: &str) -> String {
    if query.is_empty() {
        return text.to_string();
    }

    let query_lower = query.to_lowercase();
    let text_lower = text.to_lowercase();

    if let Some(start) = text_lower.find(&query_lower) {
        let end = start + query.len();
        format!("{}{}{}", &text[..start], &text[start..end], &text[end..])
    } else {
        text.to_string()
    }
}
