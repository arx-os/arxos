// ArxOS Library - Public API for integration tests and external use

// Core modules (foundational)
pub mod cli;
pub mod config;
pub mod core;
pub mod error;

// Domain modules (business logic)
pub mod domain;
pub mod git;
pub mod ifc;
pub mod render;
pub mod render3d;
pub mod spatial;

// Integration modules (external systems)
pub mod ar_integration;
pub mod hardware;
pub mod mobile_ffi;

// Data modules (serialization/persistence)
pub mod export;
pub mod persistence;
pub mod yaml;

// Application modules (commands, utilities, features)
pub mod commands;
pub mod docs;
pub mod game;
pub mod query;
pub mod search;
pub mod utils;

// Service layer (business logic abstraction)
pub mod services;

// Identity module (user registry and attribution)
pub mod identity;

// UI module (terminal user interface)
pub mod ui;

// Re-export docs for external use
pub use docs::generate_building_docs;

// AR integration submodules
pub use ar_integration::pending::{
    DetectedEquipmentInfo, PendingEquipment, PendingEquipmentManager, PendingStatus,
};
pub use ar_integration::processing::{
    process_ar_scan_and_save_pending, process_ar_scan_to_pending, validate_ar_scan_data,
};

// Re-export commonly used types for easier access
pub use core::{Building, Equipment};
pub use ifc::{
    BoundingBox, EnhancedIFCParser, IFCError, IFCProcessor, IFCResult, ParseResult, ParseStats,
};
pub use spatial::{BoundingBox3D, CoordinateSystem, Point3D, SpatialEngine, SpatialEntity};
// Re-export Git types
pub use config::counters::CounterStorage;
pub use config::{ArxConfig, ConfigError, ConfigManager, ConfigResult};
pub use domain::{ArxAddress, RESERVED_SYSTEMS};
pub use export::ar::{ARExporter, ARFormat, GLTFExporter};
pub use git::{BuildingGitManager, CommitMetadata, GitConfig, GitConfigManager, GitError};
pub use identity::{
    PendingRegistryError, PendingRequestStatus, PendingUserRegistry, PendingUserRequest,
    RegistryError, User, UserRegistry, UserStatus,
};
pub use query::{query_addresses, QueryResult};
pub use render::BuildingRenderer;
pub use services::{
    BuildingService, EquipmentService, FileRepository, InMemoryRepository, Repository, RoomService,
    SpatialService,
};
pub use utils::progress::utils as progress_utils;
pub use utils::progress::{ProgressContext, ProgressReporter};
#[allow(deprecated)]
pub use yaml::{
    BuildingData, BuildingInfo, BuildingMetadata, BuildingYamlSerializer, EquipmentData, FloorData,
    RoomData, SensorMapping, ThresholdConfig,
};

// Re-export error types
pub use error::analytics::ErrorAnalyticsManager;
pub use error::display::{
    get_display_style, set_display_style, utils as error_utils, DisplayStyle, ErrorDisplay,
};
pub use error::{ArxError, ArxResult, ErrorAnalytics, ErrorContext};
