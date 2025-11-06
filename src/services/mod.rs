//! Service layer for ArxOS
//!
//! This module provides service abstractions that decouple business logic
//! from persistence and improve testability through dependency injection.
//!
//! ## Architecture
//!
//! The service layer follows the Repository pattern:
//! - **Services**: Business logic operations (create, update, query)
//! - **Repositories**: Data access abstraction (load, save)
//! - **Entities**: Domain models (Building, Room, Equipment)
//!
//! ## Benefits
//!
//! - **Testability**: Services can be tested with mock repositories
//! - **Flexibility**: Easy to swap persistence implementations
//! - **Separation of Concerns**: Business logic separated from I/O
//! - **Dependency Injection**: Services accept repositories as dependencies

pub mod repository;
pub mod building_service;
pub mod room_service;
pub mod equipment_service;
pub mod spatial_service;

pub use repository::{Repository, InMemoryRepository, FileRepository};
pub use building_service::BuildingService;
pub use room_service::RoomService;
pub use equipment_service::EquipmentService;
pub use spatial_service::SpatialService;

