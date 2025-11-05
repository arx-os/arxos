// ArxOS Library - Public API for integration tests and external use

// Core modules (foundational)
pub mod core;
pub mod cli;
pub mod config;
pub mod error;

// Domain modules (business logic)
pub mod spatial;
pub mod git;
pub mod ifc;
pub mod render;
pub mod render3d;

// Integration modules (external systems)
pub mod ar_integration;
pub mod mobile_ffi;
pub mod hardware;

// Data modules (serialization/persistence)
pub mod yaml;
pub mod path;
pub mod persistence;
pub mod export;

// Application modules (commands, utilities, features)
pub mod commands;
pub mod search;
pub mod utils;
pub mod docs;
pub mod game;

// Identity module (user registry and attribution)
pub mod identity;

// UI module (terminal user interface)
pub mod ui;

// Re-export docs for external use
pub use docs::generate_building_docs;

// AR integration submodules
pub use ar_integration::pending::{PendingEquipment, PendingStatus, PendingEquipmentManager, DetectedEquipmentInfo};
pub use ar_integration::processing::{process_ar_scan_to_pending, validate_ar_scan_data, process_ar_scan_and_save_pending};

// Re-export commonly used types for easier access
pub use core::{Building, Equipment};
pub use ifc::{IFCProcessor, BoundingBox, IFCError, IFCResult, EnhancedIFCParser, ParseResult, ParseStats};
pub use spatial::{SpatialEngine, Point3D, BoundingBox3D, CoordinateSystem, SpatialEntity};
pub use git::{GitClient, BuildingGitManager, GitConfig, GitConfigManager, GitError, CommitMetadata};
pub use render::BuildingRenderer;
pub use yaml::{BuildingYamlSerializer, BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData, EquipmentData, SensorMapping, ThresholdConfig};
pub use path::{PathGenerator, UniversalPath, PathComponents, PathError, PathValidator};
pub use utils::progress::{ProgressReporter, ProgressContext};
pub use utils::progress::utils as progress_utils;
pub use config::{ArxConfig, ConfigManager, ConfigError, ConfigResult};
pub use export::ar::{ARExporter, ARFormat, GLTFExporter};
pub use identity::{User, UserStatus, UserRegistry, RegistryError, PendingUserRequest, PendingUserRegistry, PendingRequestStatus, PendingRegistryError};

// Re-export error types
pub use error::{ArxError, ArxResult, ErrorContext, ErrorAnalytics};
pub use error::analytics::ErrorAnalyticsManager;
pub use error::display::{ErrorDisplay, DisplayStyle, set_display_style, get_display_style, utils as error_utils};
