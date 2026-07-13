//! Interactive 3D Building Renderer
//!
//! This module provides an interactive wrapper around the existing Building3DRenderer,
//! adding real-time input handling, state management, and interactive controls.

// Submodules
pub mod effects;
pub mod game;
pub mod handlers;
pub mod rendering;

// Re-export types from submodules
pub use effects::{
    add_particle_effects_to_output, create_equipment_status_effect,
    create_maintenance_alert_effect, create_particle_burst_effect,
};
pub use game::{GameScenario, GameState, GameStats};
pub use handlers::{
    handle_action, handle_camera_action, handle_floor_change, handle_resize,
    handle_view_mode_action, handle_zoom_action,
};
pub use rendering::{render_frame, render_overlay};

// Imports
use crate::core::spatial::Point3D;
use crate::core::Building;
use crate::render3d::events::{EventHandler, InteractiveEvent};
use crate::render3d::state::{CameraState, InteractiveState};
use crate::render3d::{
    Building3DRenderer, InfoPanelState, Render3DConfig, Scene3D, ViewMode, VisualEffectsEngine,
};
use crossterm::event::KeyCode;
use crossterm::terminal::{disable_raw_mode, enable_raw_mode};
use log::info;
use std::io::{self, Write};
use std::time::{Duration, Instant};

/// Interactive 3D building renderer with real-time controls
pub struct InteractiveRenderer {
    /// Core 3D renderer (existing functionality)
    renderer: Building3DRenderer,
    /// Interactive state management
    state: InteractiveState,
    /// Event handling system
    event_handler: EventHandler,
    /// Visual effects engine
    effects_engine: VisualEffectsEngine,
    /// Rendering configuration
    config: InteractiveConfig,
    /// Last render time for FPS calculation
    last_render_time: Instant,
    /// Frame count for statistics
    frame_count: u32,
    /// Optional game state for game overlay
    game_state: Option<GameState>,
    /// Info panel state
    info_panel: InfoPanelState,

    // Caching state fields for dirty frame optimization
    last_rendered_camera: Option<CameraState>,
    last_rendered_floor: Option<i32>,
    last_rendered_view_mode: Option<ViewMode>,
    last_selected_equipment: std::collections::HashSet<String>,
    last_viewport_width: usize,
    last_viewport_height: usize,
    last_info_panel_show: bool,
    last_help_show: bool,
    last_game_score: Option<u32>,
    last_game_progress: Option<f32>,
    last_game_violations: Option<u32>,
    last_rendered_duration_secs: u64,
    cached_scene: Option<crate::render3d::Scene3D>,
    cached_ascii_output: Option<String>,
    start_time: Instant,
}

/// Configuration for interactive rendering
#[derive(Debug, Clone)]
pub struct InteractiveConfig {
    /// Target FPS for rendering
    pub target_fps: u32,
    /// Enable real-time updates
    pub real_time_updates: bool,
    /// Show FPS counter
    pub show_fps: bool,
    /// Show help overlay
    pub show_help: bool,
    /// Auto-hide help after inactivity
    pub auto_hide_help: bool,
    /// Help display duration
    pub help_duration: Duration,
    /// Enable dirty frame checking to skip rendering when idle
    pub enable_dirty_rendering: bool,
}

impl InteractiveRenderer {
    /// Create a new interactive renderer
    pub fn new(
        building: Building,
        config: Render3DConfig,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let renderer = Building3DRenderer::new(building, config);
        let state = InteractiveState::new();
        let event_handler = EventHandler::new();
        let effects_engine = VisualEffectsEngine::new();
        let interactive_config = InteractiveConfig::default();
        let info_panel = InfoPanelState::new();

        Ok(Self {
            renderer,
            state,
            event_handler,
            effects_engine,
            config: interactive_config,
            last_render_time: Instant::now(),
            frame_count: 0,
            game_state: None,
            info_panel,
            last_rendered_camera: None,
            last_rendered_floor: None,
            last_rendered_view_mode: None,
            last_selected_equipment: std::collections::HashSet::new(),
            last_viewport_width: 0,
            last_viewport_height: 0,
            last_info_panel_show: false,
            last_help_show: false,
            last_game_score: None,
            last_game_progress: None,
            last_game_violations: None,
            last_rendered_duration_secs: 0,
            cached_scene: None,
            cached_ascii_output: None,
            start_time: Instant::now(),
        })
    }

    /// Create interactive renderer with custom configuration
    pub fn with_config(
        building: Building,
        render_config: Render3DConfig,
        interactive_config: InteractiveConfig,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let renderer = Building3DRenderer::new(building, render_config);
        let state = InteractiveState::new();
        let event_handler = EventHandler::new();
        let effects_engine = VisualEffectsEngine::new();
        let info_panel = InfoPanelState::new();

        Ok(Self {
            renderer,
            state,
            event_handler,
            effects_engine,
            config: interactive_config,
            last_render_time: Instant::now(),
            frame_count: 0,
            game_state: None,
            info_panel,
            last_rendered_camera: None,
            last_rendered_floor: None,
            last_rendered_view_mode: None,
            last_selected_equipment: std::collections::HashSet::new(),
            last_viewport_width: 0,
            last_viewport_height: 0,
            last_info_panel_show: false,
            last_help_show: false,
            last_game_score: None,
            last_game_progress: None,
            last_game_violations: None,
            last_rendered_duration_secs: 0,
            cached_scene: None,
            cached_ascii_output: None,
            start_time: Instant::now(),
        })
    }

    /// Start interactive rendering session
    pub fn start_interactive_session(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        println!("🎮 Starting Interactive 3D Rendering Session");
        println!("{}", self.event_handler.get_help_text());
        println!("Press any key to start...");

        // Enable raw mode for real-time input
        enable_raw_mode()?;

        // Activate session
        self.state.activate();

        // Main event loop
        self.run_event_loop()?;

        // Cleanup
        disable_raw_mode()?;
        self.state.deactivate();

        println!("✅ Interactive session ended");
        Ok(())
    }

    /// Run the main event loop
    fn run_event_loop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let mut last_frame_time = Instant::now();
        let frame_duration = Duration::from_secs_f64(1.0 / self.config.target_fps as f64);

        loop {
            let current_time = Instant::now();

            // Process events
            if let Some(event) = self.poll_event()? {
                if self.handle_event(event)? {
                    break; // Quit requested
                }
            }

            // Render if enough time has passed
            if current_time.duration_since(last_frame_time) >= frame_duration {
                self.render_frame()?;
                last_frame_time = current_time;
            }

            // Small sleep to prevent 100% CPU usage
            std::thread::sleep(Duration::from_millis(1));
        }

        Ok(())
    }

    /// Poll for events from crossterm
    fn poll_event(&self) -> Result<Option<InteractiveEvent>, Box<dyn std::error::Error>> {
        use crossterm::event::{poll, read};

        if poll(self.event_handler.config().poll_interval)? {
            if let Some(event) = self.event_handler.process_event(read()?) {
                return Ok(Some(event));
            }
        }

        Ok(None)
    }

    /// Handle interactive events
    fn handle_event(
        &mut self,
        event: InteractiveEvent,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        match event {
            InteractiveEvent::Action(action) => {
                self.handle_action(action)?;
            }
            InteractiveEvent::KeyPress(KeyCode::Esc, _)
            | InteractiveEvent::KeyPress(KeyCode::Char('q'), _) => {
                return Ok(true); // Quit
            }
            InteractiveEvent::KeyPress(KeyCode::Char('h'), _) => {
                self.toggle_help();
            }
            InteractiveEvent::KeyPress(KeyCode::Char('i'), _)
            | InteractiveEvent::KeyPress(KeyCode::Char('I'), _) => {
                self.info_panel.toggle();
            }
            InteractiveEvent::Resize(width, height) => {
                self.handle_resize(width, height)?;
            }
            _ => {
                // Handle other events as needed
            }
        }

        Ok(false) // Continue
    }

    /// Handle specific actions (delegates to handlers module)
    fn handle_action(
        &mut self,
        action: crate::render3d::events::Action,
    ) -> Result<(), Box<dyn std::error::Error>> {
        handlers::handle_action(&mut self.state, action, &self.renderer.building)
    }

    /// Handle terminal resize (delegates to handlers module)
    fn handle_resize(
        &mut self,
        width: usize,
        height: usize,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Convert usize to u16 and delegate to handlers module
        handlers::handle_resize(&mut self.state, width as u16, height as u16)?;

        // Also update renderer configuration
        self.renderer.config.max_width = width;
        self.renderer.config.max_height = height;

        Ok(())
    }

    /// Toggle help display
    fn toggle_help(&mut self) {
        self.config.show_help = !self.config.show_help;
    }

    /// Render a single frame
    fn render_frame(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        let current_time = Instant::now();
        let session_duration_secs = current_time.duration_since(self.start_time).as_secs();

        // 1. Check if the 3D scene needs to be re-rendered (projection & geometry pass)
        let mut is_3d_scene_dirty = false;

        if !self.config.enable_dirty_rendering {
            is_3d_scene_dirty = true;
        } else {
            // Check camera changes
            if self.last_rendered_camera.as_ref() != Some(&self.state.camera_state) {
                is_3d_scene_dirty = true;
            }
            // Check current floor change
            if self.last_rendered_floor != self.state.current_floor {
                is_3d_scene_dirty = true;
            }
            // Check view mode change
            if self.last_rendered_view_mode.as_ref() != Some(&self.state.view_mode) {
                is_3d_scene_dirty = true;
            }
            // Check viewport dimension changes
            if self.last_viewport_width != self.state.session_data.viewport_width
                || self.last_viewport_height != self.state.session_data.viewport_height
            {
                is_3d_scene_dirty = true;
            }
            // Check selections changes
            if self.last_selected_equipment != self.state.selected_equipment {
                is_3d_scene_dirty = true;
            }
            // If cached components are missing
            if self.cached_scene.is_none() || self.cached_ascii_output.is_none() {
                is_3d_scene_dirty = true;
            }
        }

        // 2. Fetch or compute the 3D scene & basic ASCII output
        let (scene, ascii_output) = if is_3d_scene_dirty {
            // Update camera in renderer
            self.renderer.set_camera(
                self.state.camera_state.position,
                self.state.camera_state.target,
            );

            // Render the 3D scene (expensive!)
            let new_scene = self.renderer.render_3d()?;

            // Convert to ASCII output (expensive!)
            let new_ascii = self.renderer.render_to_ascii(&new_scene)?;

            // Cache them
            self.cached_scene = Some(new_scene.clone());
            self.cached_ascii_output = Some(new_ascii.clone());

            // Update cached states
            self.last_rendered_camera = Some(self.state.camera_state.clone());
            self.last_rendered_floor = self.state.current_floor;
            self.last_rendered_view_mode = Some(self.state.view_mode.clone());
            self.last_viewport_width = self.state.session_data.viewport_width;
            self.last_viewport_height = self.state.session_data.viewport_height;
            self.last_selected_equipment = self.state.selected_equipment.clone();

            (new_scene, new_ascii)
        } else {
            // Reuse cached outputs
            (
                self.cached_scene.clone().unwrap(),
                self.cached_ascii_output.clone().unwrap(),
            )
        };

        // 3. Update visual effects
        let delta_time = 1.0 / self.config.target_fps as f64;
        self.effects_engine.update(delta_time);

        // 4. Check if the terminal display actually needs to be updated.
        // Even if the 3D scene didn't change, we might need to redraw if:
        // - Active visual effects/particles/animations are running
        // - Info panel toggle changed
        // - Help screen toggle changed
        // - Game state changes (progress/score/violations)
        // - Session duration seconds changed (updating the overlay counter)
        let mut is_display_dirty = is_3d_scene_dirty;

        if !is_display_dirty && self.config.enable_dirty_rendering {
            // Check active effects
            if self.effects_engine.effect_count() > 0
                || self.effects_engine.animation_system().animation_count() > 0
                || self.effects_engine.particle_system().particle_count() > 0
            {
                is_display_dirty = true;
            }
            // Check overlays toggle changes
            if self.last_info_panel_show != self.info_panel.show_panel {
                is_display_dirty = true;
            }
            if self.last_help_show != self.config.show_help {
                is_display_dirty = true;
            }
            // Check game state changes
            if let Some(ref gs) = self.game_state {
                let stats = gs.get_stats();
                if self.last_game_score != Some(gs.score)
                    || self.last_game_progress != Some(gs.progress)
                    || self.last_game_violations != Some(stats.violations)
                {
                    is_display_dirty = true;
                }
            }
            // Check session clock seconds
            if self.last_rendered_duration_secs != session_duration_secs {
                is_display_dirty = true;
            }
        }

        // 5. If dirty, execute clear, print, and overlay output
        if is_display_dirty {
            // Clear screen
            print!("\x1B[2J\x1B[1;1H");

            // Add particle effects to the output
            let final_ascii = self.add_particle_effects_to_output(ascii_output);

            // Display the rendered scene
            print!("{}", final_ascii);

            // Display overlay information
            self.render_overlay(&scene)?;

            // Update stats
            self.last_info_panel_show = self.info_panel.show_panel;
            self.last_help_show = self.config.show_help;
            if let Some(ref gs) = self.game_state {
                let stats = gs.get_stats();
                self.last_game_score = Some(gs.score);
                self.last_game_progress = Some(gs.progress);
                self.last_game_violations = Some(stats.violations);
            }
            self.last_rendered_duration_secs = session_duration_secs;

            self.state.increment_render_count();
            self.frame_count += 1;
        }

        // Calculate FPS (we do this regardless of print to keep the frame rate calculations running)
        let elapsed = current_time.duration_since(self.last_render_time);
        if elapsed >= Duration::from_secs(1) {
            let fps = self.frame_count as f64 / elapsed.as_secs_f64();
            if self.config.show_fps && is_display_dirty {
                print!("FPS: {:.1}", fps);
            }
            self.frame_count = 0;
            self.last_render_time = current_time;
        }

        if is_display_dirty {
            io::stdout().flush()?;
        }

        Ok(())
    }

    /// Render overlay information
    fn render_overlay(&self, _scene: &Scene3D) -> Result<(), Box<dyn std::error::Error>> {
        let mut overlay = String::new();

        // Game overlay (if in game mode)
        if let Some(ref game_state) = self.game_state {
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

        // Session information
        overlay.push_str(&format!(
            "Session: {}s | ",
            self.state.session_duration().as_secs()
        ));
        overlay.push_str(&format!(
            "Floor: {} | ",
            self.state
                .current_floor
                .map(|f| f.to_string())
                .unwrap_or("All".to_string())
        ));
        overlay.push_str(&format!(
            "Selected: {} | ",
            self.state.selected_equipment.len()
        ));
        overlay.push_str(&format!("Mode: {:?}", self.state.view_mode));
        if self.info_panel.show_panel {
            overlay.push_str(" | Info Panel: ON");
        }

        // Help overlay
        if self.config.show_help {
            overlay.push_str("\n\n");
            overlay.push_str(&self.event_handler.get_help_text());
        }

        // Info panel overlay (if enabled)
        if self.info_panel.show_panel {
            overlay.push_str("\n\n");
            overlay.push_str("╔════════════════════════════════════════════════════════════╗\n");
            overlay.push_str("║                    INFO PANEL                             ║\n");
            overlay.push_str("╠════════════════════════════════════════════════════════════╣\n");

            // Equipment info
            if !self.state.selected_equipment.is_empty() {
                overlay.push_str("║ Equipment:\n");
                for equipment_id in &self.state.selected_equipment {
                    if let Some(equipment) = self.renderer.building.find_equipment(equipment_id) {
                        overlay.push_str(&format!(
                            "║   • {} ({:?})\n",
                            equipment.name, equipment.status
                        ));
                    }
                }
            } else {
                overlay.push_str("║ Equipment: None selected\n");
            }

            // Camera info
            let camera = &self.state.camera_state;
            overlay.push_str(&format!(
                "║ Camera: Pos({:.1},{:.1},{:.1}) Zoom:{:.2}x\n",
                camera.position.x, camera.position.y, camera.position.z, camera.zoom
            ));

            // View mode
            let mode_text = match self.state.view_mode {
                ViewMode::Standard => "Standard",
                ViewMode::CrossSection => "Cross-Section",
                ViewMode::Connections => "Connections",
                ViewMode::Maintenance => "Maintenance",
            };
            overlay.push_str(&format!("║ View: {}\n", mode_text));

            // Stats
            let current_time = Instant::now();
            let elapsed = current_time.duration_since(self.last_render_time);
            let fps = if elapsed.as_secs() > 0 {
                self.frame_count as f64 / elapsed.as_secs_f64()
            } else {
                0.0
            };
            overlay.push_str(&format!(
                "║ FPS: {:.1} | Frames: {}\n",
                fps, self.frame_count
            ));

            overlay.push_str("╚════════════════════════════════════════════════════════════╝\n");
        }

        print!("{}", overlay);
        Ok(())
    }

    /// Start game mode with a scenario
    pub fn start_game_mode(&mut self, game_state: GameState) {
        self.game_state = Some(game_state);
        info!("Game mode activated");
    }

    /// Stop game mode
    pub fn stop_game_mode(&mut self) {
        self.game_state = None;
        info!("Game mode deactivated");
    }

    /// Get game state (mutable)
    pub fn game_state_mut(&mut self) -> Option<&mut GameState> {
        self.game_state.as_mut()
    }

    /// Get game state
    pub fn game_state(&self) -> Option<&GameState> {
        self.game_state.as_ref()
    }

    /// Add particle effects to ASCII output
    fn add_particle_effects_to_output(&self, mut output: String) -> String {
        // Get all active particles
        let particles = self.effects_engine.particle_system().particles();

        // Convert particles to ASCII characters and add to output
        for particle in particles {
            // Simple particle rendering - in a real implementation, this would be more sophisticated
            let particle_char = particle.character;
            let intensity = particle.lifetime;

            // Add particle to output (simplified - would need proper 3D to 2D projection)
            if intensity > 0.1 {
                // This is a simplified approach - in reality, we'd need proper 3D projection
                output.push_str(&format!("{}", particle_char));
            }
        }

        output
    }

    /// Create equipment status effect
    pub fn create_equipment_status_effect(
        &mut self,
        equipment_id: String,
        status: crate::render3d::EquipmentStatus,
        position: Point3D,
    ) -> Result<(), String> {
        self.effects_engine.create_equipment_status_effect(
            format!("status_{}", equipment_id),
            equipment_id,
            status,
            position,
        )
    }

    /// Create maintenance alert effect
    pub fn create_maintenance_alert_effect(
        &mut self,
        equipment_id: String,
        alert_level: crate::render3d::AlertLevel,
        position: Point3D,
    ) -> Result<(), String> {
        self.effects_engine.create_maintenance_alert_effect(
            format!("alert_{}", equipment_id),
            equipment_id,
            alert_level,
            position,
        )
    }

    /// Create particle burst effect
    pub fn create_particle_burst_effect(
        &mut self,
        position: Point3D,
        particle_type: crate::render3d::ParticleType,
        count: usize,
    ) -> Result<(), String> {
        self.effects_engine.create_particle_burst_effect(
            format!("burst_{}", self.frame_count),
            position,
            particle_type,
            count,
        )
    }

    /// Get current interactive state
    pub fn state(&self) -> &InteractiveState {
        &self.state
    }

    /// Get mutable reference to state
    pub fn state_mut(&mut self) -> &mut InteractiveState {
        &mut self.state
    }

    /// Get event handler
    pub fn event_handler(&self) -> &EventHandler {
        &self.event_handler
    }

    /// Get mutable reference to event handler
    pub fn event_handler_mut(&mut self) -> &mut EventHandler {
        &mut self.event_handler
    }

    /// Get configuration
    pub fn config(&self) -> &InteractiveConfig {
        &self.config
    }

    /// Update configuration
    pub fn update_config(&mut self, config: InteractiveConfig) {
        self.config = config;
    }

    /// Get effects engine
    pub fn effects_engine(&self) -> &VisualEffectsEngine {
        &self.effects_engine
    }

    /// Get mutable effects engine
    pub fn effects_engine_mut(&mut self) -> &mut VisualEffectsEngine {
        &mut self.effects_engine
    }
}

impl Default for InteractiveConfig {
    fn default() -> Self {
        Self {
            target_fps: 30,
            real_time_updates: true,
            show_fps: true,
            show_help: false,
            auto_hide_help: true,
            help_duration: Duration::from_secs(5),
            enable_dirty_rendering: true,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor, Room, RoomType, Wing};
    use crate::render3d::{ProjectionType, ViewAngle};
    use crate::yaml::BuildingData;
    use chrono::Utc;

    fn create_test_building() -> Building {
        let mut building = Building::default();
        building.name = "Test Building".to_string();

        let mut floor = Floor::new("Floor 1".to_string(), 0);
        floor.elevation = Some(0.0);

        let mut wing = Wing::new("Wing A".to_string());

        let mut room = Room::new("Room 101".to_string(), RoomType::Office);
        room.spatial_properties = crate::core::SpatialProperties {
            position: crate::core::Position {
                x: 10.0,
                y: 10.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            },
            dimensions: crate::core::Dimensions {
                width: 10.0,
                height: 3.0,
                depth: 10.0,
            },
            bounding_box: crate::core::BoundingBox {
                min: crate::core::Position {
                    x: 5.0,
                    y: 5.0,
                    z: 0.0,
                    coordinate_system: "building_local".to_string(),
                },
                max: crate::core::Position {
                    x: 15.0,
                    y: 15.0,
                    z: 3.0,
                    coordinate_system: "building_local".to_string(),
                },
            },
            mesh: None,
            coordinate_system: "building_local".to_string(),
        };

        let mut equipment = crate::core::Equipment::new(
            "AC-1".to_string(),
            "US/HQ/Main/test_facility/Floor 1/Wing A/Room 101/AC-1".to_string(),
            crate::core::EquipmentType::HVAC,
        );
        equipment.position = crate::core::Position {
            x: 12.0,
            y: 12.0,
            z: 2.0,
            coordinate_system: "building_local".to_string(),
        };
        equipment.status = crate::core::EquipmentStatus::Active;
        equipment.health_status = Some(crate::core::EquipmentHealthStatus::Healthy);

        room.equipment.push(equipment);
        wing.rooms.push(room);
        floor.wings.push(wing);
        building.add_floor(floor);

        building
    }

    #[test]
    fn test_interactive_renderer_creation() {
        let building = create_test_building();
        let config = Render3DConfig {
            show_status: true,
            show_rooms: true,
            show_equipment: true,
            show_connections: false,
            projection_type: ProjectionType::Isometric,
            view_angle: ViewAngle::Isometric,
            scale_factor: 1.0,
            max_width: 120,
            max_height: 40,
        };

        let renderer = InteractiveRenderer::new(building, config);
        assert!(renderer.is_ok());
    }

    #[test]
    fn test_interactive_config_defaults() {
        let config = InteractiveConfig::default();
        assert_eq!(config.target_fps, 30);
        assert!(config.real_time_updates);
        assert!(config.show_fps);
        assert!(!config.show_help);
        assert!(config.auto_hide_help);
    }

    #[test]
    fn test_state_access() {
        let building = create_test_building();
        let config = Render3DConfig {
            show_status: true,
            show_rooms: true,
            show_equipment: true,
            show_connections: false,
            projection_type: ProjectionType::Isometric,
            view_angle: ViewAngle::Isometric,
            scale_factor: 1.0,
            max_width: 120,
            max_height: 40,
        };

        let mut renderer = InteractiveRenderer::new(building, config).unwrap();

        // Test state access
        assert!(!renderer.state().is_active);

        // Test mutable state access
        renderer
            .state_mut()
            .select_equipment("test-equipment".to_string());
        assert!(renderer.state().is_equipment_selected("test-equipment"));
    }
}
