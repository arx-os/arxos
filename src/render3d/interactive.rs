//! Interactive 3D Building Renderer
//!
//! This module provides an interactive wrapper around the existing Building3DRenderer,
//! adding real-time input handling, state management, and interactive controls.

use crate::yaml::BuildingData;
use crate::render3d::{Building3DRenderer, Render3DConfig, Scene3D, VisualEffectsEngine, InfoPanelState};
use crate::render3d::state::{InteractiveState, CameraState, ViewMode, Vector3D};
use crate::render3d::events::{EventHandler, InteractiveEvent, Action, CameraAction, ZoomAction, ViewModeAction};
use crossterm::event::KeyCode;
use crossterm::terminal::{enable_raw_mode, disable_raw_mode};
use std::io::{self, Write};
use std::time::{Duration, Instant};
use log::info;

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
    game_state: Option<crate::game::state::GameState>,
    /// Info panel state
    info_panel: InfoPanelState,
    /// Building data reference for info panel
    building_data: BuildingData,
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
}

impl InteractiveRenderer {
    /// Create a new interactive renderer
    pub fn new(building_data: BuildingData, config: Render3DConfig) -> Result<Self, Box<dyn std::error::Error>> {
        let building_data_clone = building_data.clone();
        let renderer = Building3DRenderer::new(building_data, config);
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
            building_data: building_data_clone,
        })
    }

    /// Create interactive renderer with custom configuration
    pub fn with_config(
        building_data: BuildingData, 
        render_config: Render3DConfig,
        interactive_config: InteractiveConfig
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let building_data_clone = building_data.clone();
        let renderer = Building3DRenderer::new(building_data, render_config);
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
            building_data: building_data_clone,
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
    fn handle_event(&mut self, event: InteractiveEvent) -> Result<bool, Box<dyn std::error::Error>> {
        match event {
            InteractiveEvent::Action(action) => {
                self.handle_action(action)?;
            }
            InteractiveEvent::KeyPress(KeyCode::Esc, _) | 
            InteractiveEvent::KeyPress(KeyCode::Char('q'), _) => {
                return Ok(true); // Quit
            }
            InteractiveEvent::KeyPress(KeyCode::Char('h'), _) => {
                self.toggle_help();
            }
            InteractiveEvent::KeyPress(KeyCode::Char('i'), _) | 
            InteractiveEvent::KeyPress(KeyCode::Char('I'), _) => {
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

    /// Handle specific actions
    fn handle_action(&mut self, action: Action) -> Result<(), Box<dyn std::error::Error>> {
        match action {
            Action::CameraMove(camera_action) => {
                self.handle_camera_action(camera_action)?;
            }
            Action::Zoom(zoom_action) => {
                self.handle_zoom_action(zoom_action)?;
            }
            Action::ViewModeChange(view_action) => {
                self.handle_view_mode_action(view_action)?;
            }
            Action::FloorChange(floor_delta) => {
                self.handle_floor_change(floor_delta)?;
            }
            Action::EquipmentSelect(equipment_id) => {
                self.state.select_equipment(equipment_id);
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
    fn handle_camera_action(&mut self, action: CameraAction) -> Result<(), Box<dyn std::error::Error>> {
        let move_speed = 1.0;
        let rotation_speed = 5.0;
        
        match action {
            CameraAction::MoveUp => {
                self.state.camera_state.translate(Vector3D::new(0.0, move_speed, 0.0));
            }
            CameraAction::MoveDown => {
                self.state.camera_state.translate(Vector3D::new(0.0, -move_speed, 0.0));
            }
            CameraAction::MoveLeft => {
                self.state.camera_state.translate(Vector3D::new(-move_speed, 0.0, 0.0));
            }
            CameraAction::MoveRight => {
                self.state.camera_state.translate(Vector3D::new(move_speed, 0.0, 0.0));
            }
            CameraAction::MoveForward => {
                self.state.camera_state.translate(Vector3D::new(0.0, 0.0, -move_speed));
            }
            CameraAction::MoveBackward => {
                self.state.camera_state.translate(Vector3D::new(0.0, 0.0, move_speed));
            }
            CameraAction::RotateLeft => {
                self.state.camera_state.rotate(0.0, -rotation_speed, 0.0);
            }
            CameraAction::RotateRight => {
                self.state.camera_state.rotate(0.0, rotation_speed, 0.0);
            }
            CameraAction::RotateUp => {
                self.state.camera_state.rotate(-rotation_speed, 0.0, 0.0);
            }
            CameraAction::RotateDown => {
                self.state.camera_state.rotate(rotation_speed, 0.0, 0.0);
            }
            CameraAction::Reset => {
                self.state.camera_state = CameraState::default();
            }
        }
        
        Ok(())
    }

    /// Handle zoom actions
    fn handle_zoom_action(&mut self, action: ZoomAction) -> Result<(), Box<dyn std::error::Error>> {
        match action {
            ZoomAction::In => {
                self.state.camera_state.zoom_in(1.2);
            }
            ZoomAction::Out => {
                self.state.camera_state.zoom_out(1.2);
            }
            ZoomAction::Reset => {
                self.state.camera_state.zoom = 1.0;
            }
        }
        
        Ok(())
    }

    /// Handle view mode changes
    fn handle_view_mode_action(&mut self, action: ViewModeAction) -> Result<(), Box<dyn std::error::Error>> {
        match action {
            ViewModeAction::Standard => {
                self.state.set_view_mode(ViewMode::Standard);
            }
            ViewModeAction::CrossSection => {
                self.state.set_view_mode(ViewMode::CrossSection);
            }
            ViewModeAction::Connections => {
                self.state.set_view_mode(ViewMode::Connections);
            }
            ViewModeAction::Maintenance => {
                self.state.set_view_mode(ViewMode::Maintenance);
            }
            ViewModeAction::ToggleRooms => {
                self.state.session_data.preferences.show_rooms = !self.state.session_data.preferences.show_rooms;
            }
            ViewModeAction::ToggleStatus => {
                self.state.session_data.preferences.show_status = !self.state.session_data.preferences.show_status;
            }
            ViewModeAction::ToggleConnections => {
                self.state.session_data.preferences.show_connections = !self.state.session_data.preferences.show_connections;
            }
        }
        
        Ok(())
    }

    /// Handle floor changes
    fn handle_floor_change(&mut self, floor_delta: i32) -> Result<(), Box<dyn std::error::Error>> {
        let current_floor = self.state.current_floor.unwrap_or(0);
        let new_floor = current_floor + floor_delta;
        
        // Validate floor exists in building data
        let max_floor = self.renderer.building_data.floors.iter()
            .map(|f| f.level)
            .max()
            .unwrap_or(0);
        
        let min_floor = self.renderer.building_data.floors.iter()
            .map(|f| f.level)
            .min()
            .unwrap_or(0);
        
        if new_floor >= min_floor && new_floor <= max_floor {
            self.state.set_current_floor(Some(new_floor));
        }
        
        Ok(())
    }

    /// Handle terminal resize
    fn handle_resize(&mut self, width: usize, height: usize) -> Result<(), Box<dyn std::error::Error>> {
        // Update renderer configuration
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
        // Clear screen
        print!("\x1B[2J\x1B[1;1H");
        
        // Update camera in renderer
        self.renderer.set_camera(
            self.state.camera_state.position,
            self.state.camera_state.target
        );
        
        // Update visual effects
        let delta_time = 1.0 / self.config.target_fps as f64;
        self.effects_engine.update(delta_time);
        
        // Render the 3D scene
        let scene = self.renderer.render_3d()?;
        
        // Convert to ASCII output
        let mut ascii_output = self.renderer.render_to_ascii(&scene)?;
        
        // Add particle effects to the output
        ascii_output = self.add_particle_effects_to_output(ascii_output);
        
        // Display the rendered scene
        print!("{}", ascii_output);
        
        // Display overlay information
        self.render_overlay(&scene)?;
        
        // Update statistics
        self.state.increment_render_count();
        self.frame_count += 1;
        
        // Calculate FPS
        let current_time = Instant::now();
        let elapsed = current_time.duration_since(self.last_render_time);
        if elapsed >= Duration::from_secs(1) {
            let fps = self.frame_count as f64 / elapsed.as_secs_f64();
            if self.config.show_fps {
                print!("FPS: {:.1}", fps);
            }
            self.frame_count = 0;
            self.last_render_time = current_time;
        }
        
        io::stdout().flush()?;
        Ok(())
    }

    /// Render overlay information
    fn render_overlay(&self, _scene: &Scene3D) -> Result<(), Box<dyn std::error::Error>> {
        let mut overlay = String::new();
        
        // Game overlay (if in game mode)
        if let Some(ref game_state) = self.game_state {
            overlay.push_str("\n");
            overlay.push_str("╔════════════════════════════════════════════════════════════╗\n");
            overlay.push_str("║                    GAME OVERLAY                           ║\n");
            overlay.push_str("╠════════════════════════════════════════════════════════════╣\n");
            
            // Objective
            if let Some(ref scenario) = game_state.scenario {
                overlay.push_str(&format!("║ Objective: {:<55} ║\n", 
                    scenario.objective.chars().take(55).collect::<String>()));
            }
            
            // Progress bar
            let progress_width: usize = 50;
            let filled = (game_state.progress * progress_width as f32) as usize;
            let bar = format!("[{}{}]", 
                "=".repeat(filled),
                " ".repeat(progress_width.saturating_sub(filled))
            );
            overlay.push_str(&format!("║ Progress: {:<55} ║\n", bar));
            overlay.push_str(&format!("║ Score: {:<57} ║\n", game_state.score));
            
            // Validation status
            let stats = game_state.get_stats();
            overlay.push_str(&format!("║ Valid: {} / {} | Violations: {:<42} ║\n", 
                stats.valid_placements, stats.total_placements, stats.violations));
            
            overlay.push_str("╚════════════════════════════════════════════════════════════╝\n");
            overlay.push_str("\n");
        }
        
        // Session information
        overlay.push_str(&format!("Session: {}s | ", self.state.session_duration().as_secs()));
        overlay.push_str(&format!("Floor: {} | ", 
            self.state.current_floor.map(|f| f.to_string()).unwrap_or("All".to_string())));
        overlay.push_str(&format!("Selected: {} | ", self.state.selected_equipment.len()));
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
                    for floor in &self.building_data.floors {
                        if let Some(equipment) = floor.equipment.iter().find(|e| e.id == *equipment_id) {
                            overlay.push_str(&format!("║   • {} ({:?})\n", equipment.name, equipment.status));
                        }
                    }
                }
            } else {
                overlay.push_str("║ Equipment: None selected\n");
            }
            
            // Camera info
            let camera = &self.state.camera_state;
            overlay.push_str(&format!("║ Camera: Pos({:.1},{:.1},{:.1}) Zoom:{:.2}x\n", 
                camera.position.x, camera.position.y, camera.position.z, camera.zoom));
            
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
            overlay.push_str(&format!("║ FPS: {:.1} | Frames: {}\n", fps, self.frame_count));
            
            overlay.push_str("╚════════════════════════════════════════════════════════════╝\n");
        }
        
        print!("{}", overlay);
        Ok(())
    }
    
    /// Start game mode with a scenario
    pub fn start_game_mode(&mut self, game_state: crate::game::state::GameState) {
        self.game_state = Some(game_state);
        info!("Game mode activated");
    }
    
    /// Stop game mode
    pub fn stop_game_mode(&mut self) {
        self.game_state = None;
        info!("Game mode deactivated");
    }
    
    /// Get game state (mutable)
    pub fn game_state_mut(&mut self) -> Option<&mut crate::game::state::GameState> {
        self.game_state.as_mut()
    }
    
    /// Get game state
    pub fn game_state(&self) -> Option<&crate::game::state::GameState> {
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
    pub fn create_equipment_status_effect(&mut self, equipment_id: String, status: crate::render3d::EquipmentStatus, position: crate::spatial::Point3D) -> Result<(), String> {
        self.effects_engine.create_equipment_status_effect(
            format!("status_{}", equipment_id),
            equipment_id,
            status,
            position
        )
    }

    /// Create maintenance alert effect
    pub fn create_maintenance_alert_effect(&mut self, equipment_id: String, alert_level: crate::render3d::AlertLevel, position: crate::spatial::Point3D) -> Result<(), String> {
        self.effects_engine.create_maintenance_alert_effect(
            format!("alert_{}", equipment_id),
            equipment_id,
            alert_level,
            position
        )
    }

    /// Create particle burst effect
    pub fn create_particle_burst_effect(&mut self, position: crate::spatial::Point3D, particle_type: crate::render3d::ParticleType, count: usize) -> Result<(), String> {
        self.effects_engine.create_particle_burst_effect(
            format!("burst_{}", self.frame_count),
            position,
            particle_type,
            count
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
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData};
    use crate::render3d::{ProjectionType, ViewAngle};
    use chrono::Utc;

    fn create_test_building_data() -> BuildingData {
        BuildingData {
            building: BuildingInfo {
                id: "test".to_string(),
                name: "Test Building".to_string(),
                description: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "1.0".to_string(),
                total_entities: 1,
                spatial_entities: 1,
                coordinate_system: "local".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![FloorData {
                id: "floor-1".to_string(),
                name: "Floor 1".to_string(),
                level: 0,
                elevation: 0.0,
                rooms: vec![],
                equipment: vec![],
                bounding_box: None,
            }],
            coordinate_systems: vec![],
        }
    }

    #[test]
    fn test_interactive_renderer_creation() {
        let building_data = create_test_building_data();
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
        
        let renderer = InteractiveRenderer::new(building_data, config);
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
        let building_data = create_test_building_data();
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
        
        let mut renderer = InteractiveRenderer::new(building_data, config).unwrap();
        
        // Test state access
        assert!(!renderer.state().is_active);
        
        // Test mutable state access
        renderer.state_mut().select_equipment("test-equipment".to_string());
        assert!(renderer.state().is_equipment_selected("test-equipment"));
    }
}
