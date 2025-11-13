//! Arx protocol core library.
//!
//! This crate provides the core data model, IFC processing pipeline, Git
//! integration, spatial reasoning engine, and DePIN primitives used across the
//! ArxOS ecosystem.

pub mod building;
pub mod config;
pub mod core;
pub mod depin;
pub mod domain;
pub mod error;
pub mod git;
pub mod identity;
pub mod ifc;
pub mod persistence;
pub mod sensor;
pub mod spatial;
pub mod utils;
pub mod validation;
pub mod yaml;

// Re-export foundational types for convenience.
pub use config::{ArxConfig, ConfigError, ConfigManager, ConfigResult};
pub use core::{
    add_equipment, create_room, delete_room, delete_room_impl, get_room, list_equipment,
    list_rooms, remove_equipment, remove_equipment_impl, set_spatial_relationship, spatial_query,
    transform_coordinates, update_equipment, update_equipment_impl, update_room, update_room_impl,
    validate_spatial, Building, BuildingMetadata, CoordinateSystemInfo, Dimensions, Equipment,
    EquipmentHealthStatus, EquipmentStatus, EquipmentType, Position, Room, RoomType, SensorMapping,
    SpatialProperties, SpatialQueryResult, SpatialValidationIssue, SpatialValidationResult,
    ThresholdConfig, Wing,
};
pub use depin::{
    SensorAlert, SensorData, SensorMetadata, SensorReadingValidator, SensorType, ThresholdCheck,
    ValidationOutcome,
};
pub use domain::{
    ArxAddress, BuildingValuation, ContributionRecord, EconomySnapshot, Money, RevenuePayout,
    RESERVED_SYSTEMS,
};
pub use error::{ArxError, ArxResult, ErrorAnalytics, ErrorContext};
pub use git::{BuildingGitManager, CommitMetadata, GitConfig, GitConfigManager, GitError};
pub use identity::{
    PendingRegistryError, PendingRequestStatus, PendingUserRegistry, PendingUserRequest,
    RegistryError, User, UserRegistry, UserStatus,
};
pub use ifc::{
    BoundingBox, EnhancedIFCParser, IFCError, IFCProcessor, IFCResult, ParseResult, ParseStats,
};
pub use persistence::{load_building_data_from_dir, PersistenceManager};
pub use spatial::{BoundingBox3D, CoordinateSystem, Point3D, SpatialEngine, SpatialEntity};
pub use utils::progress::{self, ProgressContext, ProgressReporter};
#[allow(deprecated)]
pub use yaml::{
    BuildingData, BuildingInfo, BuildingMetadata as YamlBuildingMetadata, BuildingYamlSerializer,
    EquipmentData as YamlEquipmentData, FloorData, RoomData,
};
