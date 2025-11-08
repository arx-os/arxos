#![no_std]

//! Aggregated hardware abstraction layer for ArxOS.
//!
//! This crate re-exports board-specific HAL implementations under feature
//! flags. Enable the relevant feature (`esp32-c3`, `rp2040`, etc.) to pull in
//! the corresponding driver support.

#[cfg(feature = "esp32-c3")]
pub use arxos_hal_esp32_c3 as esp32_c3;

#[cfg(feature = "rp2040")]
pub use arxos_hal_rp2040 as rp2040;
