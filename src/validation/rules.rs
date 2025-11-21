//! Validation rules and constraints engine

use crate::error::ArxResult;
use serde::{Deserialize, Serialize};
use regex::Regex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ValidationRuleType {
    /// Field must not be empty
    Required,
    /// String must be at least this long
    MinLength(usize),
    /// String must be at most this long
    MaxLength(usize),
    /// String must match regex pattern
    Regex(String),
    /// Number must be within range (inclusive)
    Range { min: f64, max: f64 },
    /// Custom validation logic (name of the validator)
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationRule {
    pub id: String,
    pub name: String,
    pub description: String,
    pub severity: ValidationSeverity,
    pub rule_type: ValidationRuleType,
    pub target_field: Option<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum ValidationSeverity {
    Error,
    Warning,
    Info,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ValidationResult {
    pub rule_id: String,
    pub message: String,
    pub severity: ValidationSeverity,
    pub field: Option<String>,
}

pub struct ValidationEngine {
    rules: Vec<ValidationRule>,
}

impl ValidationEngine {
    pub fn new() -> Self {
        Self { rules: Vec::new() }
    }

    pub fn add_rule(&mut self, rule: ValidationRule) {
        self.rules.push(rule);
    }

    /// Validate a string value against applicable rules
    pub fn validate_field(&self, field_name: &str, value: &str) -> ArxResult<Vec<ValidationResult>> {
        let mut results = Vec::new();

        for rule in &self.rules {
            // Skip rules that target other fields
            if let Some(target) = &rule.target_field {
                if target != field_name {
                    continue;
                }
            }

            let valid = match &rule.rule_type {
                ValidationRuleType::Required => !value.trim().is_empty(),
                ValidationRuleType::MinLength(min) => value.len() >= *min,
                ValidationRuleType::MaxLength(max) => value.len() <= *max,
                ValidationRuleType::Regex(pattern) => {
                    if let Ok(re) = Regex::new(pattern) {
                        re.is_match(value)
                    } else {
                        // If regex is invalid, fail safe (or log error)
                        false
                    }
                }
                ValidationRuleType::Range { min, max } => {
                    if let Ok(num) = value.parse::<f64>() {
                        num >= *min && num <= *max
                    } else {
                        // Not a number, so range validation fails (unless optional, but we assume checked)
                        false
                    }
                }
                ValidationRuleType::Custom(_) => true, // Custom validators need external context
            };

            if !valid {
                results.push(ValidationResult {
                    rule_id: rule.id.clone(),
                    message: format!("Validation failed: {}", rule.description),
                    severity: rule.severity,
                    field: Some(field_name.to_string()),
                });
            }
        }

        Ok(results)
    }
}

impl Default for ValidationEngine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_required_rule() {
        let mut engine = ValidationEngine::new();
        engine.add_rule(ValidationRule {
            id: "R1".to_string(),
            name: "Required Name".to_string(),
            description: "Name is required".to_string(),
            severity: ValidationSeverity::Error,
            rule_type: ValidationRuleType::Required,
            target_field: Some("name".to_string()),
        });

        let results = engine.validate_field("name", "").unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].rule_id, "R1");

        let results_ok = engine.validate_field("name", "Test").unwrap();
        assert!(results_ok.is_empty());
    }

    #[test]
    fn test_length_rule() {
        let mut engine = ValidationEngine::new();
        engine.add_rule(ValidationRule {
            id: "R2".to_string(),
            name: "Min Length".to_string(),
            description: "Must be at least 3 chars".to_string(),
            severity: ValidationSeverity::Warning,
            rule_type: ValidationRuleType::MinLength(3),
            target_field: Some("code".to_string()),
        });

        let results = engine.validate_field("code", "AB").unwrap();
        assert_eq!(results.len(), 1);

        let results_ok = engine.validate_field("code", "ABC").unwrap();
        assert!(results_ok.is_empty());
    }
}