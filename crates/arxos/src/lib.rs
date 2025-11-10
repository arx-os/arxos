#![cfg_attr(not(feature = "std"), no_std)]

#[cfg(not(feature = "std"))]
extern crate alloc;

// ArxOS Library - Public API for integration tests and external use

#[cfg(feature = "std")]
pub use arx::config;
pub use arx::error;

// Re-export protocol modules from the `arx` crate
pub use arx::{core, domain, git, ifc, spatial, utils, yaml};

// Integration modules (external systems)
#[cfg(feature = "std")]
pub mod ar_integration;
#[cfg(all(feature = "std", feature = "economy"))]
pub mod economy;
#[cfg(feature = "std")]
pub mod hardware;
#[cfg(feature = "std")]
pub mod mobile_ffi;

// Data modules (serialization/persistence)
#[cfg(feature = "std")]
pub mod export;
#[cfg(feature = "std")]
pub use arx::persistence;

// Application modules (utilities, features)
#[cfg(feature = "std")]
pub mod game;
#[cfg(feature = "std")]
pub mod query;
#[cfg(feature = "std")]
pub mod search;

// Service layer (business logic abstraction)
#[cfg(feature = "std")]
pub mod services;

// Identity module (user registry and attribution)
pub use arx::identity;

// Minimal runtime surface for embedded/no_std builds
#[cfg(not(feature = "std"))]
pub mod runtime;

// AR integration submodules
#[cfg(feature = "std")]
pub use ar_integration::pending::{
    DetectedEquipmentInfo, PendingEquipment, PendingEquipmentManager, PendingStatus,
};
#[cfg(feature = "std")]
pub use ar_integration::processing::{
    process_ar_scan_and_save_pending, process_ar_scan_to_pending, validate_ar_scan_data,
};

// Re-export commonly used types for easier access
pub use arx::core::{Building, Equipment};
pub use arx::ifc::{
    BoundingBox, EnhancedIFCParser, IFCError, IFCProcessor, IFCResult, ParseResult, ParseStats,
};
pub use arx::spatial::{BoundingBox3D, CoordinateSystem, Point3D, SpatialEngine, SpatialEntity};
// Re-export Git types
pub use arx::domain::{ArxAddress, RESERVED_SYSTEMS};
pub use arx::git::{BuildingGitManager, CommitMetadata, GitConfig, GitConfigManager, GitError};
#[allow(deprecated)]
pub use arx::yaml::{
    BuildingData, BuildingInfo, BuildingMetadata, BuildingYamlSerializer, EquipmentData, FloorData,
    RoomData, SensorMapping, ThresholdConfig,
};
#[cfg(feature = "std")]
pub use config::counters::CounterStorage;
#[cfg(feature = "std")]
pub use config::{ArxConfig, ConfigError, ConfigManager, ConfigResult};
#[cfg(all(feature = "std", feature = "economy"))]
pub use economy::{
    ArxoEconomyService, DatasetPublishRequest, EconomyConfig, EconomyError,
    RevenueDistributionRequest, StakingAction, VerificationRequest,
};
#[cfg(feature = "std")]
pub use export::ar::{ARExporter, ARFormat, GLTFExporter};
pub use identity::{
    PendingRegistryError, PendingRequestStatus, PendingUserRegistry, PendingUserRequest,
    RegistryError, User, UserRegistry, UserStatus,
};
#[cfg(feature = "std")]
pub use query::{query_addresses, QueryResult};
#[cfg(feature = "std")]
pub use services::{
    BuildingService, EquipmentService, FileRepository, InMemoryRepository, Repository, RoomService,
    SpatialService,
};
#[cfg(feature = "std")]
pub use utils::progress::utils as progress_utils;
#[cfg(feature = "std")]
pub use utils::progress::{ProgressContext, ProgressReporter};

// Re-export error types
pub use error::analytics::ErrorAnalyticsManager;
pub use error::display::{
    get_display_style, set_display_style, utils as error_utils, DisplayStyle, ErrorDisplay,
};
pub use error::{ArxError, ArxResult, ErrorAnalytics, ErrorContext};
