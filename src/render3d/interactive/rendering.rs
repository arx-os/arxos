//! Rendering functions for interactive mode
//!
//! This module handles frame rendering and overlay display for the
//! interactive 3D building renderer.

use crate::render3d::events::EventHandler;
use crate::render3d::state::{InteractiveState, ViewMode};
use crate::render3d::{Building3DRenderer, InfoPanelState, Scene3D, VisualEffectsEngine};
use crate::yaml::BuildingData;
use std::io::{self, Write};
use std::time::Instant;

use super::game::GameState;

/// Render a complete frame including scene and overlays
///
/// # Arguments
/// * `renderer` - Mutable reference to the 3D renderer
/// * `effects_engine` - Mutable reference to the effects engine
/// * `state` - Mutable reference to the interactive state
/// * `game_state` - Optional game state for game overlay
/// * `info_panel` - Reference to info panel state
/// * `event_handler` - Reference to event handler for help text
/// * `show_help` - Whether to show the help overlay
/// * `show_fps` - Whether to show the FPS counter
/// * `target_fps` - Target frames per second
/// * `last_render_time` - Mutable reference to last render timestamp
/// * `frame_count` - Mutable reference to frame counter
/// * `add_particle_effects` - Function to add particle effects to output
///
/// # Returns
/// Result indicating success or error
#[allow(clippy::too_many_arguments)]
pub fn render_frame<F>(
    renderer: &mut Building3DRenderer,
    effects_engine: &mut VisualEffectsEngine,
    state: &mut InteractiveState,
    game_state: Option<&GameState>,
    info_panel: &InfoPanelState,
    event_handler: &EventHandler,
    show_help: bool,
    show_fps: bool,
    target_fps: u32,
    last_render_time: &mut Instant,
    frame_count: &mut u32,
    add_particle_effects: F,
) -> Result<(), Box<dyn std::error::Error>>
where
    F: Fn(&VisualEffectsEngine, String) -> String,
{
    // Clear screen
    print!("\x1B[2J\x1B[1;1H");

    // Update camera in renderer
    renderer.set_camera(state.camera_state.position, state.camera_state.target);

    // Update visual effects
    let delta_time = 1.0 / target_fps as f64;
    effects_engine.update(delta_time);

    // Render the 3D scene
    let scene = renderer.render_3d()?;

    // Convert to ASCII output
    let mut ascii_output = renderer.render_to_ascii(&scene)?;

    // Add particle effects to the output
    ascii_output = add_particle_effects(effects_engine, ascii_output);

    // Display the rendered scene
    print!("{}", ascii_output);

    // Display overlay information
    render_overlay(
        &scene,
        state,
        game_state,
        info_panel,
        event_handler,
        show_help,
        &renderer.building_data,
        *last_render_time,
        *frame_count,
    )?;

    // Update statistics
    state.increment_render_count();
    *frame_count += 1;

    // Calculate and display FPS
    let current_time = Instant::now();
    let elapsed = current_time.duration_since(*last_render_time);
    if elapsed >= std::time::Duration::from_secs(1) {
        let fps = *frame_count as f64 / elapsed.as_secs_f64();
        if show_fps {
            print!("FPS: {:.1}", fps);
        }
        *frame_count = 0;
        *last_render_time = current_time;
    }

    io::stdout().flush()?;
    Ok(())
}

/// Render overlay information on top of the scene
///
/// # Arguments
/// * `_scene` - Reference to the rendered scene
/// * `state` - Reference to interactive state
/// * `game_state` - Optional game state for game overlay
/// * `info_panel` - Reference to info panel state
/// * `event_handler` - Reference to event handler for help text
/// * `show_help` - Whether to show the help overlay
/// * `building_data` - Reference to building data for equipment lookup
/// * `last_render_time` - Last render timestamp for FPS calculation
/// * `frame_count` - Current frame count for FPS calculation
///
/// # Returns
/// Result indicating success or error
#[allow(clippy::too_many_arguments)]
pub fn render_overlay(
    _scene: &Scene3D,
    state: &InteractiveState,
    game_state: Option<&GameState>,
    info_panel: &InfoPanelState,
    event_handler: &EventHandler,
    show_help: bool,
    building_data: &BuildingData,
    last_render_time: Instant,
    frame_count: u32,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut overlay = String::new();

    // Game overlay (if in game mode)
    if let Some(game_state) = game_state {
        render_game_overlay(&mut overlay, game_state);
    }

    // Session information
    render_session_info(&mut overlay, state, info_panel);

    // Help overlay
    if show_help {
        overlay.push_str("\n\n");
        overlay.push_str(&event_handler.get_help_text());
    }

    // Info panel overlay (if enabled)
    if info_panel.show_panel {
        render_info_panel(&mut overlay, state, building_data, last_render_time, frame_count)?;
    }

    print!("{}", overlay);
    Ok(())
}

/// Render the game overlay section
fn render_game_overlay(overlay: &mut String, game_state: &GameState) {
    overlay.push('\n');
    overlay.push_str("╔════════════════════════════════════════════════════════════╗\n");
    overlay.push_str("║                    GAME OVERLAY                           ║\n");
    overlay.push_str("╠════════════════════════════════════════════════════════════╣\n");

    // Objective
    if let Some(ref scenario) = game_state.scenario {
        overlay.push_str(&format!(
            "║ Objective: {:<55} ║\n",
            scenario.objective.chars().take(55).collect::<String>()
        ));
    }

    // Progress bar
    let progress_width: usize = 50;
    let filled = (game_state.progress * progress_width as f32) as usize;
    let bar = format!(
        "[{}{}]",
        "=".repeat(filled),
        " ".repeat(progress_width.saturating_sub(filled))
    );
    overlay.push_str(&format!("║ Progress: {:<55} ║\n", bar));
    overlay.push_str(&format!("║ Score: {:<57} ║\n", game_state.score));

    // Validation status
    let stats = game_state.get_stats();
    overlay.push_str(&format!(
        "║ Valid: {} / {} | Violations: {:<42} ║\n",
        stats.valid_placements, stats.total_placements, stats.violations
    ));

    overlay.push_str("╚════════════════════════════════════════════════════════════╝\n");
    overlay.push('\n');
}

/// Render session information
fn render_session_info(overlay: &mut String, state: &InteractiveState, info_panel: &InfoPanelState) {
    overlay.push_str(&format!(
        "Session: {}s | ",
        state.session_duration().as_secs()
    ));
    overlay.push_str(&format!(
        "Floor: {} | ",
        state
            .current_floor
            .map(|f| f.to_string())
            .unwrap_or("All".to_string())
    ));
    overlay.push_str(&format!(
        "Selected: {} | ",
        state.selected_equipment.len()
    ));
    overlay.push_str(&format!("Mode: {:?}", state.view_mode));
    if info_panel.show_panel {
        overlay.push_str(" | Info Panel: ON");
    }
}

/// Render the info panel
fn render_info_panel(
    overlay: &mut String,
    state: &InteractiveState,
    building_data: &BuildingData,
    last_render_time: Instant,
    frame_count: u32,
) -> Result<(), Box<dyn std::error::Error>> {
    overlay.push_str("\n\n");
    overlay.push_str("╔════════════════════════════════════════════════════════════╗\n");
    overlay.push_str("║                    INFO PANEL                             ║\n");
    overlay.push_str("╠════════════════════════════════════════════════════════════╣\n");

    // Equipment info
    if !state.selected_equipment.is_empty() {
        overlay.push_str("║ Equipment:\n");
        for equipment_id in &state.selected_equipment {
            for floor in &building_data.building.floors {
                if let Some(equipment) = floor.equipment.iter().find(|e| e.id == *equipment_id) {
                    overlay.push_str(&format!(
                        "║   • {} ({:?})\n",
                        equipment.name, equipment.status
                    ));
                }
            }
        }
    } else {
        overlay.push_str("║ Equipment: None selected\n");
    }

    // Camera info
    let camera = &state.camera_state;
    overlay.push_str(&format!(
        "║ Camera: Pos({:.1},{:.1},{:.1}) Zoom:{:.2}x\n",
        camera.position.x, camera.position.y, camera.position.z, camera.zoom
    ));

    // View mode
    let mode_text = match state.view_mode {
        ViewMode::Standard => "Standard",
        ViewMode::CrossSection => "Cross-Section",
        ViewMode::Connections => "Connections",
        ViewMode::Maintenance => "Maintenance",
    };
    overlay.push_str(&format!("║ View: {}\n", mode_text));

    // Stats
    let current_time = Instant::now();
    let elapsed = current_time.duration_since(last_render_time);
    let fps = if elapsed.as_secs() > 0 {
        frame_count as f64 / elapsed.as_secs_f64()
    } else {
        0.0
    };
    overlay.push_str(&format!(
        "║ FPS: {:.1} | Frames: {}\n",
        fps, frame_count
    ));

    overlay.push_str("╚════════════════════════════════════════════════════════════╝\n");

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_render_session_info() {
        let state = InteractiveState::new();
        let info_panel = InfoPanelState { show_panel: false };
        let mut overlay = String::new();

        render_session_info(&mut overlay, &state, &info_panel);

        assert!(overlay.contains("Session:"));
        assert!(overlay.contains("Floor:"));
        assert!(overlay.contains("Mode:"));
    }
}
