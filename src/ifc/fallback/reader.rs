//! IFC file reader and validation
//!
//! Handles file reading, path validation, and size checking for IFC files.

use crate::ifc::IFCError;
use crate::utils::path_safety::PathSafety;
use std::path::Path;

/// IFC file reader with validation
pub struct IFCReader;

impl IFCReader {
    pub fn new() -> Self {
        Self
    }

    /// Read and validate IFC file
    pub fn read_file(&self, file_path: &str) -> Result<String, Box<dyn std::error::Error>> {
        // Validate file path with path safety
        let current_dir = std::env::current_dir()?;
        let file_path_buf = Path::new(file_path);
        let validated_path = if file_path_buf.is_absolute() {
            PathSafety::canonicalize_and_validate(file_path_buf, &current_dir)?
        } else {
            let joined = current_dir.join(file_path_buf);
            PathSafety::canonicalize_and_validate(&joined, &current_dir)?
        };

        // Check file size before reading
        let validated_path_str = validated_path
            .to_str()
            .ok_or_else(|| format!("Invalid file path encoding: {}", validated_path.display()))?;
        self.validate_file_size(validated_path_str)?;

        // Use path-safe file reading
        let content = PathSafety::read_file_safely(&validated_path, &current_dir)?;
        Ok(content)
    }

    /// Validate IFC file size before processing
    pub fn validate_file_size(&self, file_path: &str) -> Result<(), Box<dyn std::error::Error>> {
        use log::info;
        use std::fs::metadata;

        let metadata = metadata(file_path)?;
        let file_size_bytes = metadata.len();
        let file_size_mb = file_size_bytes / (1024 * 1024);

        const MAX_FILE_SIZE_MB: u64 = 500;
        const WARNING_THRESHOLD_MB: u64 = 100;

        if file_size_mb > MAX_FILE_SIZE_MB {
            return Err(Box::new(IFCError::FileTooLarge {
                size: file_size_mb,
                max: MAX_FILE_SIZE_MB,
            }));
        }

        if file_size_mb > WARNING_THRESHOLD_MB {
            info!(
                "Warning: Large IFC file detected ({}MB). Processing may take longer.",
                file_size_mb
            );
        }

        Ok(())
    }
}

impl Default for IFCReader {
    fn default() -> Self {
        Self::new()
    }
}
