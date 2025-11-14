//! Data extractors for converting building data to 3D representations
//!
//! This module provides specialized extractors for converting building domain
//! data into optimized 3D representations suitable for rendering.

mod floor_extractor;
mod equipment_extractor;
mod room_extractor;

pub use floor_extractor::extract_floors_3d;
pub use equipment_extractor::extract_equipment_3d;
pub use room_extractor::extract_rooms_3d;
