// Re-export main types and functions for testing
pub use crate::ProjectData;
pub use crate::ArxideError;
pub use crate::ArxideState;

// Re-export commands for testing
pub mod commands {
    pub use super::super::commands::*;
}

// Test utilities
#[cfg(test)]
pub mod test_utils {
    use super::*;
    use tempfile::TempDir;
    use std::path::PathBuf;

    pub fn create_test_project() -> ProjectData {
        ProjectData::new(
            "Test Project".to_string(),
            "A test project for unit testing".to_string(),
        )
    }

    pub fn create_temp_dir() -> TempDir {
        tempfile::tempdir().expect("Failed to create temp directory")
    }

    pub fn create_test_file_path(temp_dir: &TempDir, filename: &str) -> PathBuf {
        temp_dir.path().join(filename)
    }
}
