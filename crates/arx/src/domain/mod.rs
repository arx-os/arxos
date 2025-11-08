//! Domain layer for ArxOS business logic
//!
//! This module contains core domain concepts like addresses, fixtures, and other
//! building-related entities.

pub mod address;

pub use address::{ArxAddress, RESERVED_SYSTEMS};
