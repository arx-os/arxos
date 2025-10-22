// ArxOS Library - Public API for integration tests and external use
pub mod core;
pub mod cli;
pub mod spatial;
pub mod git;
pub mod ifc;
pub mod render;
pub mod yaml;
pub mod path;

// Re-export commonly used types for easier access
pub use core::{Building, Equipment};
pub use ifc::{IFCProcessor, BoundingBox, IFCError, IFCResult};
pub use spatial::{SpatialEngine, Point3D, BoundingBox3D, CoordinateSystem, SpatialEntity};
pub use git::{GitClient, BuildingGitManager, GitConfig, GitConfigManager, GitError};
pub use render::BuildingRenderer;
pub use yaml::{BuildingYamlSerializer, BuildingData, BuildingInfo, BuildingMetadata, FloorData, RoomData, EquipmentData};
pub use path::{PathGenerator, UniversalPath, PathComponents, PathError, PathValidator};
