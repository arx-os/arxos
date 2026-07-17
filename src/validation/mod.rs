//! Validation rules and constraints engine

pub mod building;
pub mod rules;

pub use building::{validate_building, BuildingValidationReport, STRICT_ADDRESSES};
pub use rules::{ValidationResult, ValidationRule, ValidationRuleType, ValidationSeverity};
