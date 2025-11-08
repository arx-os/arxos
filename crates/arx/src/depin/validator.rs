use super::{EquipmentSensorMapping, ThresholdCheck};

/// Result of validating an observed sensor value.
#[derive(Debug, Clone, PartialEq)]
pub enum ValidationOutcome {
    Normal,
    OutOfRange {
        value: f64,
        threshold_min: Option<f64>,
        threshold_max: Option<f64>,
    },
}

/// Helper used to evaluate sensor readings against configured thresholds.
pub struct SensorReadingValidator<'a> {
    mapping: &'a EquipmentSensorMapping,
}

impl<'a> SensorReadingValidator<'a> {
    pub fn new(mapping: &'a EquipmentSensorMapping) -> Self {
        Self { mapping }
    }

    /// Evaluate a reading and return whether it is inside the expected range.
    pub fn evaluate(&self, value: f64) -> ValidationOutcome {
        let out_of_range = match (self.mapping.threshold_min, self.mapping.threshold_max) {
            (Some(min), Some(max)) => value < min || value > max,
            (Some(min), None) => value < min,
            (None, Some(max)) => value > max,
            (None, None) => false,
        };

        if out_of_range {
            ValidationOutcome::OutOfRange {
                value,
                threshold_min: self.mapping.threshold_min,
                threshold_max: self.mapping.threshold_max,
            }
        } else {
            ValidationOutcome::Normal
        }
    }

    /// Whether an alert should be emitted when the value is outside the range.
    pub fn should_alert(&self, outcome: &ValidationOutcome) -> bool {
        matches!(outcome, ValidationOutcome::OutOfRange { .. })
            && self.mapping.alert_on_out_of_range
    }
}

impl From<ValidationOutcome> for ThresholdCheck {
    fn from(value: ValidationOutcome) -> Self {
        match value {
            ValidationOutcome::Normal => ThresholdCheck::Normal,
            ValidationOutcome::OutOfRange { .. } => ThresholdCheck::OutOfRange,
        }
    }
}
