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
pub mod yaml;
pub mod path;

// Re-export commonly used types for easier access
pub use core::{Building, Equipment};
pub use ifc::{IFCProcessor, BoundingBox, IFCError, IFCResult, EnhancedIFCParser, ParseResult, ParseStats};
pub use spatial::{SpatialEngine, Point3D, BoundingBox3D, CoordinateSystem, SpatialEntity};
pub use git::{GitClient, BuildingGitManager, GitConfig, GitConfigManager, GitError};
pub use render::BuildingRenderer;
pub use yaml::{BuildingYamlSerializer, BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData, EquipmentData};
pub use path::{PathGenerator, UniversalPath, PathComponents, PathError, PathValidator};
pub use progress::{ProgressReporter, ProgressContext, utils};
pub use config::{ArxConfig, ConfigManager, ConfigError, ConfigResult};

// Re-export error types
pub use error::{ArxError, ArxResult, ErrorContext, ErrorAnalytics};
pub use error::analytics::ErrorAnalyticsManager;
pub use error::display::{ErrorDisplay, utils as error_utils};
