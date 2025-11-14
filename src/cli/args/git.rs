//! Git command arguments
//!
//! Argument structures for Git-related CLI commands including
//! staging, committing, diffing, and history.

use clap::Args;

/// Arguments for the Stage command
///
/// Stage changes in the working directory.
#[derive(Debug, Clone, Args)]
pub struct StageArgs {
    /// Stage all modified files (default behavior)
    #[arg(long)]
    pub all: bool,

    /// Specific file to stage
    pub file: Option<String>,
}

/// Arguments for the Commit command
///
/// Commit staged changes.
#[derive(Debug, Clone, Args)]
pub struct CommitArgs {
    /// Commit message
    pub message: String,
}

/// Arguments for the Unstage command
///
/// Unstage changes.
#[derive(Debug, Clone, Args)]
pub struct UnstageArgs {
    /// Unstage all files
    #[arg(long)]
    pub all: bool,

    /// Specific file to unstage
    pub file: Option<String>,
}

/// Arguments for the Diff command
///
/// Show differences between commits.
#[derive(Debug, Clone, Args)]
pub struct DiffArgs {
    /// Compare with specific commit hash
    #[arg(long)]
    pub commit: Option<String>,

    /// Show diff for specific file
    #[arg(long)]
    pub file: Option<String>,

    /// Show file statistics only
    #[arg(long)]
    pub stat: bool,

    /// Open interactive viewer
    #[arg(long)]
    pub interactive: bool,
}

/// Arguments for the History command
///
/// Show commit history.
#[derive(Debug, Clone, Args)]
pub struct HistoryArgs {
    /// Number of commits to show (1-1000)
    #[arg(long, default_value = "10", value_parser = validate_history_limit)]
    pub limit: usize,

    /// Show detailed commit information
    #[arg(long)]
    pub verbose: bool,

    /// Show history for specific file
    #[arg(long)]
    pub file: Option<String>,
}

/// Arguments for the Status command
///
/// Show repository status and changes.
#[derive(Debug, Clone, Args)]
pub struct StatusArgs {
    /// Show detailed status information
    #[arg(long)]
    pub verbose: bool,

    /// Open interactive dashboard
    #[arg(long)]
    pub interactive: bool,
}

/// Validate history limit is between 1 and 1000
fn validate_history_limit(s: &str) -> Result<usize, String> {
    let val: usize = s
        .parse()
        .map_err(|_| "must be a number between 1 and 1000".to_string())?;
    if val < 1 || val > 1000 {
        Err(format!("Limit must be between 1 and 1000, got {}", val))
    } else {
        Ok(val)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_history_limit() {
        assert!(validate_history_limit("10").is_ok());
        assert!(validate_history_limit("1").is_ok());
        assert!(validate_history_limit("1000").is_ok());
        assert!(validate_history_limit("0").is_err());
        assert!(validate_history_limit("1001").is_err());
        assert!(validate_history_limit("invalid").is_err());
    }
}
