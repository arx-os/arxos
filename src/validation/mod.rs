//! Validation rules and constraints engine

pub mod building;
pub mod rules;

pub use building::{validate_building, BuildingValidationReport};
pub use rules::{ValidationResult, ValidationRule, ValidationRuleType, ValidationSeverity};

