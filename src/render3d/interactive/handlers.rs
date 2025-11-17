//! Event handler implementations for interactive rendering
//!
//! This module contains all event handling logic including camera movement,
//! zoom controls, view mode changes, and floor navigation.

use crate::render3d::events::{Action, CameraAction, ViewModeAction, ZoomAction};
use crate::render3d::state::{CameraState, InteractiveState, Vector3D, ViewMode};
use crate::yaml::BuildingData;

/// Handle a specific action on the interactive state
///
/// # Arguments
/// * `state` - Mutable reference to the interactive state
/// * `action` - The action to handle
/// * `building_data` - Reference to building data for validation
///
/// # Returns
/// Result indicating success or error
pub fn handle_action(
    state: &mut InteractiveState,
    action: Action,
    building_data: &BuildingData,
) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        Action::CameraMove(camera_action) => {
            handle_camera_action(state, camera_action)?;
        }
        Action::Zoom(zoom_action) => {
            handle_zoom_action(state, zoom_action)?;
        }
        Action::ViewModeChange(view_action) => {
            handle_view_mode_action(state, view_action)?;
        }
        Action::FloorChange(floor_delta) => {
            handle_floor_change(state, floor_delta, building_data)?;
        }
        Action::EquipmentSelect(equipment_id) => {
            state.select_equipment(equipment_id);
        }
        Action::GameAction(game_action) => {
            // Game actions are handled by game overlay system
            // Game overlay processes these actions for game mode functionality
            log::debug!("Game action received: {:?}", game_action);
        }
    }

    Ok(())
}

/// Handle camera movement actions
///
/// # Arguments
/// * `state` - Mutable reference to interactive state
/// * `action` - Camera action to perform
///
/// # Returns
/// Result indicating success or error
pub fn handle_camera_action(
    state: &mut InteractiveState,
    action: CameraAction,
) -> Result<(), Box<dyn std::error::Error>> {
    let move_speed = 1.0;
    let rotation_speed = 5.0;

    match action {
        CameraAction::MoveUp => {
            state
                .camera_state
                .translate(Vector3D::new(0.0, move_speed, 0.0));
        }
        CameraAction::MoveDown => {
            state
                .camera_state
                .translate(Vector3D::new(0.0, -move_speed, 0.0));
        }
        CameraAction::MoveLeft => {
            state
                .camera_state
                .translate(Vector3D::new(-move_speed, 0.0, 0.0));
        }
        CameraAction::MoveRight => {
            state
                .camera_state
                .translate(Vector3D::new(move_speed, 0.0, 0.0));
        }
        CameraAction::MoveForward => {
            state
                .camera_state
                .translate(Vector3D::new(0.0, 0.0, -move_speed));
        }
        CameraAction::MoveBackward => {
            state
                .camera_state
                .translate(Vector3D::new(0.0, 0.0, move_speed));
        }
        CameraAction::RotateLeft => {
            state.camera_state.rotate(0.0, -rotation_speed, 0.0);
        }
        CameraAction::RotateRight => {
            state.camera_state.rotate(0.0, rotation_speed, 0.0);
        }
        CameraAction::RotateUp => {
            state.camera_state.rotate(-rotation_speed, 0.0, 0.0);
        }
        CameraAction::RotateDown => {
            state.camera_state.rotate(rotation_speed, 0.0, 0.0);
        }
        CameraAction::Reset => {
            state.camera_state = CameraState::default();
        }
    }

    Ok(())
}

/// Handle zoom actions
///
/// # Arguments
/// * `state` - Mutable reference to interactive state
/// * `action` - Zoom action to perform
///
/// # Returns
/// Result indicating success or error
pub fn handle_zoom_action(
    state: &mut InteractiveState,
    action: ZoomAction,
) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        ZoomAction::In => {
            state.camera_state.zoom_in(1.2);
        }
        ZoomAction::Out => {
            state.camera_state.zoom_out(1.2);
        }
        ZoomAction::Reset => {
            state.camera_state.zoom = 1.0;
        }
    }

    Ok(())
}

/// Handle view mode changes
///
/// # Arguments
/// * `state` - Mutable reference to interactive state
/// * `action` - View mode action to perform
///
/// # Returns
/// Result indicating success or error
pub fn handle_view_mode_action(
    state: &mut InteractiveState,
    action: ViewModeAction,
) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        ViewModeAction::Standard => {
            state.set_view_mode(ViewMode::Standard);
        }
        ViewModeAction::CrossSection => {
            state.set_view_mode(ViewMode::CrossSection);
        }
        ViewModeAction::Connections => {
            state.set_view_mode(ViewMode::Connections);
        }
        ViewModeAction::Maintenance => {
            state.set_view_mode(ViewMode::Maintenance);
        }
        ViewModeAction::ToggleRooms => {
            state.session_data.preferences.show_rooms =
                !state.session_data.preferences.show_rooms;
        }
        ViewModeAction::ToggleStatus => {
            state.session_data.preferences.show_status =
                !state.session_data.preferences.show_status;
        }
        ViewModeAction::ToggleConnections => {
            state.session_data.preferences.show_connections =
                !state.session_data.preferences.show_connections;
        }
    }

    Ok(())
}

/// Handle floor changes (navigate between floors)
///
/// # Arguments
/// * `state` - Mutable reference to interactive state
/// * `floor_delta` - Change in floor number (positive or negative)
/// * `building_data` - Reference to building data for validation
///
/// # Returns
/// Result indicating success or error
pub fn handle_floor_change(
    state: &mut InteractiveState,
    floor_delta: i32,
    building_data: &BuildingData,
) -> Result<(), Box<dyn std::error::Error>> {
    let current_floor = state.current_floor.unwrap_or(0);
    let new_floor = current_floor + floor_delta;

    // Validate floor exists in building data
    let max_floor = building_data
        .building
        .floors
        .iter()
        .map(|f| f.level)
        .max()
        .unwrap_or(0);
    let min_floor = building_data
        .building
        .floors
        .iter()
        .map(|f| f.level)
        .min()
        .unwrap_or(0);

    if new_floor >= min_floor && new_floor <= max_floor {
        state.current_floor = Some(new_floor);
        log::info!("Changed to floor {}", new_floor);
    } else {
        log::warn!(
            "Floor {} out of range ({} to {})",
            new_floor,
            min_floor,
            max_floor
        );
    }

    Ok(())
}

/// Handle window resize events
///
/// # Arguments
/// * `state` - Mutable reference to interactive state
/// * `width` - New window width
/// * `height` - New window height
///
/// # Returns
/// Result indicating success or error
pub fn handle_resize(
    state: &mut InteractiveState,
    width: u16,
    height: u16,
) -> Result<(), Box<dyn std::error::Error>> {
    state.session_data.viewport_width = width as usize;
    state.session_data.viewport_height = height as usize;
    log::info!("Window resized to {}x{}", width, height);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::yaml::Building;

    fn create_test_building_data() -> BuildingData {
        BuildingData {
            building: Building {
                name: "Test Building".to_string(),
                floors: vec![],
            },
        }
    }

    #[test]
    fn test_handle_zoom_action() {
        let mut state = InteractiveState::new();
        let initial_zoom = state.camera_state.zoom;

        handle_zoom_action(&mut state, ZoomAction::In).unwrap();
        assert!(state.camera_state.zoom > initial_zoom);

        handle_zoom_action(&mut state, ZoomAction::Reset).unwrap();
        assert_eq!(state.camera_state.zoom, 1.0);
    }

    #[test]
    fn test_handle_view_mode_action() {
        let mut state = InteractiveState::new();

        handle_view_mode_action(&mut state, ViewModeAction::CrossSection).unwrap();
        assert_eq!(state.view_mode, ViewMode::CrossSection);

        handle_view_mode_action(&mut state, ViewModeAction::Standard).unwrap();
        assert_eq!(state.view_mode, ViewMode::Standard);
    }
}
