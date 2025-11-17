//! Animation builder functions
//!
//! This module provides convenient builder functions for creating
//! common animation types with sensible defaults.

use super::types::*;
use std::time::{Duration, Instant};

/// Create a linear animation
///
/// # Arguments
/// * `id` - Unique identifier for the animation
/// * `start_value` - Starting value
/// * `end_value` - Ending value
/// * `duration` - Animation duration
///
/// # Returns
/// Configured Animation ready to be started
pub fn create_linear_animation(
    id: String,
    start_value: f64,
    end_value: f64,
    duration: Duration,
) -> Animation {
    Animation {
        id,
        animation_type: AnimationType::Linear,
        progress: 0.0,
        duration,
        start_time: Instant::now(),
        easing: EasingFunction::EaseInOut,
        state: AnimationState::Pending,
        data: AnimationData::Linear {
            start_value,
            end_value,
            current_value: start_value,
        },
    }
}

/// Create a camera movement animation
///
/// # Arguments
/// * `id` - Unique identifier for the animation
/// * `start_pos` - Starting camera position
/// * `end_pos` - Ending camera position
/// * `duration` - Animation duration
///
/// # Returns
/// Configured Animation ready to be started
pub fn create_camera_move_animation(
    id: String,
    start_pos: CameraPosition,
    end_pos: CameraPosition,
    duration: Duration,
) -> Animation {
    Animation {
        id,
        animation_type: AnimationType::CameraMove,
        progress: 0.0,
        duration,
        start_time: Instant::now(),
        easing: EasingFunction::EaseInOut,
        state: AnimationState::Pending,
        data: AnimationData::CameraMove {
            start_position: start_pos.clone(),
            end_position: end_pos.clone(),
            current_position: start_pos,
        },
    }
}

/// Create a status transition animation
///
/// # Arguments
/// * `id` - Unique identifier for the animation
/// * `from_status` - Initial equipment status
/// * `to_status` - Target equipment status
/// * `duration` - Animation duration
///
/// # Returns
/// Configured Animation ready to be started
pub fn create_status_transition_animation(
    id: String,
    from_status: EquipmentStatus,
    to_status: EquipmentStatus,
    duration: Duration,
) -> Animation {
    Animation {
        id,
        animation_type: AnimationType::StatusTransition,
        progress: 0.0,
        duration,
        start_time: Instant::now(),
        easing: EasingFunction::EaseInOut,
        state: AnimationState::Pending,
        data: AnimationData::StatusTransition {
            from_status: from_status.clone(),
            to_status: to_status.clone(),
            current_status: from_status,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_linear_animation() {
        let anim = create_linear_animation(
            "test".to_string(),
            0.0,
            100.0,
            Duration::from_millis(500),
        );

        assert_eq!(anim.id, "test");
        assert_eq!(anim.animation_type, AnimationType::Linear);
        assert_eq!(anim.state, AnimationState::Pending);

        if let AnimationData::Linear {
            start_value,
            end_value,
            ..
        } = anim.data
        {
            assert_eq!(start_value, 0.0);
            assert_eq!(end_value, 100.0);
        } else {
            panic!("Expected Linear animation data");
        }
    }

    #[test]
    fn test_create_camera_move_animation() {
        let start = CameraPosition {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            target_x: 0.0,
            target_y: 0.0,
            target_z: 0.0,
        };
        let end = CameraPosition {
            x: 10.0,
            y: 10.0,
            z: 10.0,
            target_x: 5.0,
            target_y: 5.0,
            target_z: 5.0,
        };

        let anim = create_camera_move_animation(
            "camera".to_string(),
            start,
            end,
            Duration::from_secs(1),
        );

        assert_eq!(anim.animation_type, AnimationType::CameraMove);
    }

    #[test]
    fn test_create_status_transition_animation() {
        let anim = create_status_transition_animation(
            "status".to_string(),
            EquipmentStatus::Healthy,
            EquipmentStatus::Warning,
            Duration::from_millis(300),
        );

        assert_eq!(anim.animation_type, AnimationType::StatusTransition);

        if let AnimationData::StatusTransition {
            from_status,
            to_status,
            ..
        } = anim.data
        {
            assert_eq!(from_status, EquipmentStatus::Healthy);
            assert_eq!(to_status, EquipmentStatus::Warning);
        } else {
            panic!("Expected StatusTransition animation data");
        }
    }
}
