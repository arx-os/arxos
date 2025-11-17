//! Error conversion implementations
//!
//! This module provides From trait implementations for converting
//! standard library and third-party errors into ArxError.

use super::types::{ArxError, ErrorContext};

// From trait implementations for common error types

impl From<std::io::Error> for ArxError {
    fn from(err: std::io::Error) -> Self {
        let path = err
            .raw_os_error()
            .map(|_| "System error occurred".to_string())
            .or_else(|| {
                // Try to extract path from error message if available
                let msg = err.to_string();
                if msg.contains("No such file") {
                    msg.split("No such file")
                        .nth(1)
                        .map(|s| {
                            s.trim()
                                .trim_matches(|c| c == '"' || c == '\'' || c == '(' || c == ')')
                        })
                        .map(|s| s.to_string())
                } else {
                    None
                }
            });

        Self::IoError {
            message: err.to_string(),
            context: Box::new(ErrorContext::default()),
            path,
        }
    }
}

impl From<serde_yaml::Error> for ArxError {
    fn from(err: serde_yaml::Error) -> Self {
        // Extract file path if available from location
        let file_path = err.location().map(|_| "YAML file".to_string());

        Self::YamlProcessing {
            message: err.to_string(),
            context: Box::new(ErrorContext::default()),
            file_path,
        }
    }
}

impl From<serde_json::Error> for ArxError {
    fn from(err: serde_json::Error) -> Self {
        Self::YamlProcessing {
            message: format!("JSON parsing error: {}", err),
            context: Box::new(ErrorContext::default()),
            file_path: None,
        }
    }
}

impl From<git2::Error> for ArxError {
    fn from(err: git2::Error) -> Self {
        Self::GitOperation {
            message: err.message().to_string(),
            context: Box::new(ErrorContext::default()),
            operation: "Git operation".to_string(),
        }
    }
}

impl From<crate::git::GitError> for ArxError {
    fn from(err: crate::git::GitError) -> Self {
        match err {
            crate::git::GitError::GitError(git_err_msg) => Self::GitOperation {
                message: git_err_msg,
                context: Box::new(ErrorContext {
                    suggestions: vec![
                        "Check Git repository status".to_string(),
                        "Verify Git is properly configured".to_string(),
                        "Ensure you have appropriate permissions".to_string(),
                    ],
                    recovery_steps: vec![
                        "Run: git status".to_string(),
                        "Check: git config --list".to_string(),
                        "Verify repository permissions".to_string(),
                    ],
                    help_url: Some(
                        "https://github.com/arx-os/arxos/docs/core/ARCHITECTURE.md#git-operations"
                            .to_string(),
                    ),
                    ..Default::default()
                }),
                operation: "Git operation".to_string(),
            },
            crate::git::GitError::IoError(io_err) => Self::IoError {
                message: format!("Git IO error: {}", io_err),
                context: Box::new(ErrorContext {
                    suggestions: vec![
                        "Check file system permissions".to_string(),
                        "Verify disk space is available".to_string(),
                        "Ensure the repository path is accessible".to_string(),
                    ],
                    recovery_steps: vec![
                        "Check file permissions: ls -l".to_string(),
                        "Verify disk space: df -h".to_string(),
                        "Check repository path exists".to_string(),
                    ],
                    ..Default::default()
                }),
                path: None,
            },
            crate::git::GitError::SerializationError(serde_err) => Self::YamlProcessing {
                message: format!("Git serialization error: {}", serde_err),
                context: Box::new(ErrorContext {
                    suggestions: vec![
                        "Check YAML file format".to_string(),
                        "Verify file encoding (UTF-8)".to_string(),
                        "Review YAML syntax".to_string(),
                    ],
                    recovery_steps: vec![
                        "Validate YAML syntax".to_string(),
                        "Check file encoding".to_string(),
                        "Review documentation for YAML format".to_string(),
                    ],
                    ..Default::default()
                }),
                file_path: None,
            },
            crate::git::GitError::Generic(err) => Self::GitOperation {
                message: format!("Git error: {}", err),
                context: Box::new(ErrorContext::default()),
                operation: "Git operation".to_string(),
            },
            crate::git::GitError::RepositoryNotFound { path } => Self::GitOperation {
                message: format!("Git repository not found: {}", path),
                context: Box::new(ErrorContext {
                    suggestions: vec![
                        "Verify the repository path is correct".to_string(),
                        "Check if the repository exists".to_string(),
                        "Initialize a new repository if needed".to_string(),
                    ],
                    recovery_steps: vec![
                        format!("Check path exists: ls -la {}", path),
                        "Initialize repository: git init".to_string(),
                        "Verify repository path in configuration".to_string(),
                    ],
                    file_path: Some(path),
                    ..Default::default()
                }),
                operation: "repository initialization".to_string(),
            },
            crate::git::GitError::InvalidConfig { reason } => Self::Configuration {
                message: format!("Invalid Git configuration: {}", reason),
                context: Box::new(ErrorContext {
                    suggestions: vec![
                        "Review Git configuration settings".to_string(),
                        "Check environment variables".to_string(),
                        "Verify ArxConfig settings".to_string(),
                    ],
                    recovery_steps: vec![
                        "Check: git config --list".to_string(),
                        "Review environment variables (GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL)"
                            .to_string(),
                        "Verify ArxConfig user settings".to_string(),
                    ],
                    ..Default::default()
                }),
                field: Some("git_config".to_string()),
            },
            crate::git::GitError::OperationFailed { operation, reason } => Self::GitOperation {
                message: format!("Git operation failed: {}", reason),
                context: Box::new(ErrorContext {
                    suggestions: vec![
                        "Check Git repository status".to_string(),
                        "Review error details for specific issue".to_string(),
                        "Verify repository permissions".to_string(),
                    ],
                    recovery_steps: vec![
                        format!("Review operation: {}", operation),
                        "Check repository status: git status".to_string(),
                        "Verify permissions and configuration".to_string(),
                    ],
                    debug_info: Some(format!("Operation: {}, Reason: {}", operation, reason)),
                    ..Default::default()
                }),
                operation,
            },
        }
    }
}
