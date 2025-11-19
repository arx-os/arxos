//! Query and search command arguments
//!
//! Argument structures for query-related CLI commands including
//! text search and ArxAddress pattern matching.

use clap::Args;

/// Arguments for the Search command
///
/// Search building data with various filters.
#[derive(Debug, Clone, Args)]
pub struct SearchArgs {
    /// Search query
    pub query: String,

    /// Search in equipment names
    #[arg(long)]
    pub equipment: bool,

    /// Search in room names
    #[arg(long)]
    pub rooms: bool,

    /// Search in building names
    #[arg(long)]
    pub buildings: bool,

    /// Case-sensitive search
    #[arg(long)]
    pub case_sensitive: bool,

    /// Use regex pattern matching
    #[arg(long)]
    pub regex: bool,

    /// Maximum number of results (1-10000)
    #[arg(long, default_value = "50", value_parser = validate_search_limit)]
    pub limit: usize,

    /// Show detailed results
    #[arg(long)]
    pub verbose: bool,

    /// Open interactive browser
    #[arg(long)]
    pub interactive: bool,
}

/// Arguments for the Query command
///
/// Query equipment by ArxAddress glob pattern.
/// Supports hierarchical path queries: /country/state/city/building/floor/room/fixture
///
/// # Examples
///
/// ```bash
/// # Find all boilers in mech rooms on any floor
/// arx query "/usa/ny/*/floor-*/mech/boiler-*"
///
/// # Find all equipment in kitchen on floor 02
/// arx query "/usa/ny/brooklyn/ps-118/floor-02/kitchen/*"
///
/// # Find all HVAC equipment in any city
/// arx query "/usa/ny/*/ps-118/floor-*/hvac/*"
/// ```
#[derive(Debug, Clone, Args)]
pub struct QueryArgs {
    /// ArxAddress glob pattern with wildcards (e.g., "/usa/ny/*/floor-*/mech/boiler-*")
    pub pattern: String,

    /// Output format (table, json, yaml)
    #[arg(long, default_value = "table")]
    pub format: String,

    /// Show detailed results
    #[arg(long)]
    pub verbose: bool,
}

/// Validate search limit is between 1 and 10000
fn validate_search_limit(s: &str) -> Result<usize, String> {
    let val: usize = s
        .parse()
        .map_err(|_| "must be a number between 1 and 10000".to_string())?;
    if !(1..=10000).contains(&val) {
        Err(format!("Limit must be between 1 and 10000, got {}", val))
    } else {
        Ok(val)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_search_limit() {
        assert!(validate_search_limit("50").is_ok());
        assert!(validate_search_limit("1").is_ok());
        assert!(validate_search_limit("10000").is_ok());
        assert!(validate_search_limit("0").is_err());
        assert!(validate_search_limit("10001").is_err());
        assert!(validate_search_limit("invalid").is_err());
    }

    #[test]
    fn test_search_args_defaults() {
        // Verify that the Args derive works correctly
        // Actual parsing would need clap's testing utilities
    }

    #[test]
    fn test_query_args_defaults() {
        // Verify that the Args derive works correctly
    }
}
