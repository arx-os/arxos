//! Sensor data ingestion for hardware integration

use super::{HardwareError, HardwareResult, SensorData};
use log::{info, warn};
use std::path::{Path, PathBuf};

/// Sensor data ingestion service
///
/// This service reads sensor data files and prepares them for processing.
/// It supports reading from local file systems (simulating HTTP/MQTT input in Phase 1).
pub struct SensorIngestionService {
    pub config: SensorIngestionConfig,
}

#[derive(Debug, Clone)]
pub struct SensorIngestionConfig {
    pub data_directory: PathBuf,
    pub supported_formats: Vec<String>,
    pub auto_process: bool,
}

impl Default for SensorIngestionConfig {
    fn default() -> Self {
        Self {
            data_directory: PathBuf::from("./sensor-data"),
            supported_formats: vec!["yaml".to_string(), "yml".to_string(), "json".to_string()],
            auto_process: true,
        }
    }
}

impl SensorIngestionService {
    /// Create a new sensor ingestion service
    pub fn new(config: SensorIngestionConfig) -> Self {
        Self { config }
    }

    /// Read and parse sensor data from a file
    pub fn read_sensor_data_file<P: AsRef<Path>>(
        &self,
        file_path: P,
    ) -> HardwareResult<SensorData> {
        use crate::utils::path_safety::PathSafety;

        let path = file_path.as_ref();
        info!("Reading sensor data from: {}", path.display());

        // Use path-safe file reading - restrict to configured data directory
        let base_dir = &self.config.data_directory;

        let content = PathSafety::read_file_safely(path, base_dir).map_err(|e| {
            HardwareError::FileNotFound {
                path: format!("{} (path safety check failed: {})", path.display(), e),
            }
        })?;

        // Determine format from extension
        let ext = path
            .extension()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .to_lowercase();

        match ext.as_str() {
            "yaml" | "yml" => {
                let sensor_data: SensorData = serde_yaml::from_str(&content)?;
                Ok(sensor_data)
            }
            "json" => {
                let sensor_data: SensorData = serde_json::from_str(&content)?;
                Ok(sensor_data)
            }
            _ => Err(HardwareError::InvalidFormat {
                reason: format!("Unsupported file format: {}", ext),
            }),
        }
    }

    /// Scan directory for sensor data files
    pub fn scan_directory<P: AsRef<Path>>(&self, dir_path: P) -> HardwareResult<Vec<PathBuf>> {
        use crate::utils::path_safety::PathSafety;

        let dir_path = dir_path.as_ref();
        info!("Scanning directory for sensor data: {}", dir_path.display());

        // Use path-safe directory reading - restrict to configured data directory
        let base_dir = &self.config.data_directory;

        // If directory doesn't exist, return empty (not an error)
        if !dir_path.exists() {
            return Ok(Vec::new());
        }

        // Validate directory is within base
        let canonical_dir =
            PathSafety::canonicalize_and_validate(dir_path, base_dir).map_err(|e| {
                HardwareError::InvalidFormat {
                    reason: format!("Directory path validation failed: {}", e),
                }
            })?;

        // Use path-safe directory reading
        let paths = PathSafety::read_dir_safely(&canonical_dir, base_dir).map_err(|e| {
            HardwareError::InvalidFormat {
                reason: format!("Cannot read directory: {}", e),
            }
        })?;

        // Filter for supported file formats
        let mut sensor_files = Vec::new();
        for path in paths {
            if let Some(ext) = path.extension().and_then(|s| s.to_str()) {
                if self.config.supported_formats.contains(&ext.to_lowercase()) {
                    sensor_files.push(path);
                }
            }
        }

        info!("Found {} sensor data files", sensor_files.len());
        Ok(sensor_files)
    }

    /// Process all sensor files in configured directory
    pub fn process_all_sensor_files(&self) -> HardwareResult<Vec<SensorData>> {
        let files = self.scan_directory(&self.config.data_directory)?;
        let mut sensor_data = Vec::new();

        for file in files {
            match self.read_sensor_data_file(&file) {
                Ok(data) => {
                    info!("Successfully processed: {}", file.display());
                    sensor_data.push(data);
                }
                Err(e) => {
                    warn!("Failed to process {}: {}", file.display(), e);
                    // Continue processing other files
                }
            }
        }

        Ok(sensor_data)
    }

    /// Validate sensor data structure
    pub fn validate_sensor_data(&self, data: &SensorData) -> bool {
        // Check required fields
        if data.api_version.is_empty() || data.kind.is_empty() {
            return false;
        }

        // Check metadata
        if data.metadata.sensor_id.is_empty() || data.metadata.sensor_type.is_empty() {
            return false;
        }

        // Check data values
        if data.data.values.is_empty() {
            return false;
        }

        true
    }

    /// Get the configured sensor data directory
    pub fn sensor_data_dir(&self) -> &std::path::Path {
        &self.config.data_directory
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    #[test]
    fn test_scan_directory() {
        let temp_dir = TempDir::new().unwrap();
        let config = SensorIngestionConfig {
            data_directory: temp_dir.path().to_path_buf(),
            ..Default::default()
        };

        let service = SensorIngestionService::new(config);

        // Create some test files
        fs::write(temp_dir.path().join("test1.yaml"), "").unwrap();
        fs::write(temp_dir.path().join("test2.json"), "").unwrap();
        fs::write(temp_dir.path().join("test3.txt"), "").unwrap();

        let files = service.scan_directory(temp_dir.path()).unwrap();
        assert_eq!(files.len(), 2); // Only yaml and json
    }
}
