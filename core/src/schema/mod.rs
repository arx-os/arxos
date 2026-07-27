//! Schema helpers and documentation constants.

use crate::object::{ObjectType, SCHEMA_VERSION};

/// Human-readable list of Phase 0 object types.
pub fn initial_object_types() -> &'static [ObjectType] {
    &[
        ObjectType::Building,
        ObjectType::Floor,
        ObjectType::Space,
        ObjectType::Surface,
        ObjectType::Opening,
        ObjectType::Equipment,
        ObjectType::System,
        ObjectType::Circuit,
        ObjectType::Sensor,
        ObjectType::Fixture,
        ObjectType::Annotation,
        ObjectType::PointCloudChunk,
        ObjectType::Mesh,
        ObjectType::BoundingVolume,
        ObjectType::Relationship,
        ObjectType::SpatialIndexNode,
        ObjectType::Root,
        ObjectType::Provenance,
        ObjectType::Blob,
    ]
}

/// Current schema version for new objects.
pub fn current_schema_version() -> u32 {
    SCHEMA_VERSION
}
