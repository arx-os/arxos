//! Easing functions for smooth animations
//!
//! This module provides mathematical easing functions that create
//! smooth, natural-feeling animation transitions.

use super::types::EasingFunction;

/// Apply easing function to a progress value (0.0 to 1.0)
///
/// # Arguments
/// * `progress` - Animation progress from 0.0 to 1.0
/// * `easing` - The easing function to apply
///
/// # Returns
/// Eased progress value
pub fn apply_easing(progress: f64, easing: &EasingFunction) -> f64 {
    match easing {
        EasingFunction::Linear => progress,
        EasingFunction::EaseIn => progress * progress,
        EasingFunction::EaseOut => 1.0 - (1.0 - progress) * (1.0 - progress),
        EasingFunction::EaseInOut => {
            if progress < 0.5 {
                2.0 * progress * progress
            } else {
                1.0 - 2.0 * (1.0 - progress) * (1.0 - progress)
            }
        }
        EasingFunction::Bounce => bounce_easing(progress),
        EasingFunction::Elastic => elastic_easing(progress),
        EasingFunction::Back => back_easing(progress),
        EasingFunction::CubicBezier(x1, y1, x2, y2) => {
            cubic_bezier_easing(progress, *x1, *y1, *x2, *y2)
        }
    }
}

/// Bounce easing function - creates a bouncing effect
///
/// # Arguments
/// * `t` - Time value from 0.0 to 1.0
///
/// # Returns
/// Eased value with bounce effect
pub fn bounce_easing(t: f64) -> f64 {
    if t < 1.0 / 2.75 {
        7.5625 * t * t
    } else if t < 2.0 / 2.75 {
        let t = t - 1.5 / 2.75;
        7.5625 * t * t + 0.75
    } else if t < 2.5 / 2.75 {
        let t = t - 2.25 / 2.75;
        7.5625 * t * t + 0.9375
    } else {
        let t = t - 2.625 / 2.75;
        7.5625 * t * t + 0.984375
    }
}

/// Elastic easing function - creates an elastic/spring effect
///
/// # Arguments
/// * `t` - Time value from 0.0 to 1.0
///
/// # Returns
/// Eased value with elastic effect
pub fn elastic_easing(t: f64) -> f64 {
    if t == 0.0 || t == 1.0 {
        t
    } else {
        let c4 = (2.0 * std::f64::consts::PI) / 3.0;
        -(2.0_f64.powf(10.0 * t - 10.0)) * ((t * 10.0 - 10.75) * c4).sin()
    }
}

/// Back easing function - overshoots then comes back
///
/// # Arguments
/// * `t` - Time value from 0.0 to 1.0
///
/// # Returns
/// Eased value with back/overshoot effect
pub fn back_easing(t: f64) -> f64 {
    const C1: f64 = 1.70158;
    const C3: f64 = C1 + 1.0;
    C3 * t * t * t - C1 * t * t
}

/// Cubic bezier easing function - custom bezier curve interpolation
///
/// # Arguments
/// * `t` - Time value from 0.0 to 1.0
/// * `_x1` - First control point X (unused in simplified impl)
/// * `y1` - First control point Y
/// * `_x2` - Second control point X (unused in simplified impl)
/// * `y2` - Second control point Y
///
/// # Returns
/// Eased value following cubic bezier curve
pub fn cubic_bezier_easing(t: f64, _x1: f64, y1: f64, _x2: f64, y2: f64) -> f64 {
    // Simplified cubic bezier implementation
    let t2 = t * t;
    let t3 = t2 * t;
    let mt = 1.0 - t;
    let mt2 = mt * mt;
    let _mt3 = mt2 * mt;

    3.0 * mt2 * t * y1 + 3.0 * mt * t2 * y2 + t3
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_linear_easing() {
        let result = apply_easing(0.5, &EasingFunction::Linear);
        assert_eq!(result, 0.5);
    }

    #[test]
    fn test_ease_in() {
        let result = apply_easing(0.5, &EasingFunction::EaseIn);
        assert_eq!(result, 0.25);
    }

    #[test]
    fn test_ease_out() {
        let result = apply_easing(0.5, &EasingFunction::EaseOut);
        assert_eq!(result, 0.75);
    }

    #[test]
    fn test_bounce_easing() {
        let result = bounce_easing(0.5);
        assert!(result > 0.0 && result < 1.0);
    }

    #[test]
    fn test_elastic_easing() {
        assert_eq!(elastic_easing(0.0), 0.0);
        assert_eq!(elastic_easing(1.0), 1.0);
    }

    #[test]
    fn test_back_easing() {
        let result = back_easing(0.5);
        assert!(result.is_finite());
    }
}
