// ArxOS Library - Public API for integration tests and external use
pub mod core;
pub mod cli;
pub mod config;
pub mod error;
pub mod spatial;
pub mod git;
pub mod ifc;
pub mod progress;
pub mod render;
pub mod render3d;
pub mod ar_integration;
pub mod docs;
pub mod export;

// Re-export docs for external use
pub use docs::generate_building_docs;

// AR integration submodules
pub use ar_integration::pending::{PendingEquipment, PendingStatus, PendingEquipmentManager, DetectedEquipmentInfo};
pub use ar_integration::processing::{process_ar_scan_to_pending, validate_ar_scan_data, process_ar_scan_and_save_pending};
pub mod yaml;
pub mod path;
pub mod search;
pub mod hardware;
pub mod persistence;
pub mod mobile_ffi;
pub mod commands;
pub mod utils;
pub mod game;

// Re-export commonly used types for easier access
pub use core::{Building, Equipment};
pub use ifc::{IFCProcessor, BoundingBox, IFCError, IFCResult, EnhancedIFCParser, ParseResult, ParseStats};
pub use spatial::{SpatialEngine, Point3D, BoundingBox3D, CoordinateSystem, SpatialEntity};
pub use git::{GitClient, BuildingGitManager, GitConfig, GitConfigManager, GitError};
pub use render::BuildingRenderer;
pub use yaml::{BuildingYamlSerializer, BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData, EquipmentData, SensorMapping, ThresholdConfig};
pub use path::{PathGenerator, UniversalPath, PathComponents, PathError, PathValidator};
pub use progress::{ProgressReporter, ProgressContext};
pub use progress::utils as progress_utils;
pub use config::{ArxConfig, ConfigManager, ConfigError, ConfigResult};
pub use export::ar::{ARExporter, ARFormat, GLTFExporter};

// Re-export error types
pub use error::{ArxError, ArxResult, ErrorContext, ErrorAnalytics};
pub use error::analytics::ErrorAnalyticsManager;
pub use error::display::{ErrorDisplay, utils as error_utils};
