//! DePIN (decentralized physical infrastructure) primitives.
//!
//! This module provides shared sensor data structures and validation routines
//! that can be reused by runtimes, services, and embedded targets.

mod sensor;
mod validator;

pub use sensor::{
    ArxosMetadata, EquipmentSensorMapping, SensorAlert, SensorData, SensorDataValues,
    SensorMetadata, SensorType, ThresholdCheck,
};
pub use validator::{SensorReadingValidator, ValidationOutcome};
