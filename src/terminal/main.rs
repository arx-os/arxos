//! Arxos Terminal Client - Minecraft for Buildings
//! 
//! This is the main entry point for the Arxos terminal interface.
//! It provides CAD-level building visualization with progressive
//! detail enhancement from the mesh network.

use arxos_core::{
    ArxObject, SlowBleedNode, ProgressiveRenderer, 
    MeshPacket, object_types
};
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style, Stylize},
    text::{Line, Span, Text},
    widgets::{Block, BorderType, Borders, Paragraph, List, ListItem, Gauge},
    Frame, Terminal,
};
use std::{
    error::Error,
    io,
    time::{Duration, Instant},
};
use clap::Parser;

/// Arxos command-line arguments
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Building ID to connect to
    #[arg(short, long, default_value_t = 0xA001)]
    building: u16,
    
    /// Floor level to display
    #[arg(short, long, default_value_t = 1)]
    floor: i8,
    
    /// Start in simulation mode (no real mesh connection)
    #[arg(short, long, default_value_t = true)]
    simulate: bool,
    
    /// Node ID for this terminal
    #[arg(short, long, default_value_t = 0x0001)]
    node_id: u16,
}

/// Application state
struct App {
    // Core components
    node: SlowBleedNode,
    renderer: ProgressiveRenderer,
    
    // UI state
    current_tab: Tab,
    command_buffer: String,
    messages: Vec<String>,
    selected_object: Option<u16>,
    
    // Statistics
    packets_received: u64,
    start_time: Instant,
    
    // Simulation
    simulate_mode: bool,
    sim_timer: u32,
}

#[derive(Debug, Clone, Copy, PartialEq)]
enum Tab {
    FloorPlan,
    ObjectDetail,
    MeshStatus,
    Terminal,
}

impl App {
    fn new(args: Args) -> Self {
        let node = SlowBleedNode::new(args.node_id, args.building);
        let renderer = ProgressiveRenderer::new();
        
        Self {
            node,
            renderer,
            current_tab: Tab::FloorPlan,
            command_buffer: String::new(),
            messages: vec![
                "Welcome to Arxos Terminal v0.1.0".to_string(),
                "Minecraft for Buildings + Pokémon GO for Infrastructure".to_string(),
                format!("Node {:04X} | Building {:04X}", args.node_id, args.building),
                String::new(),
            ],
            selected_object: None,
            packets_received: 0,
            start_time: Instant::now(),
            simulate_mode: args.simulate,
            sim_timer: 0,
        }
    }
    
    /// Process a tick (called ~10 times per second)
    fn tick(&mut self) {
        self.node.tick();
        
        // Simulate mesh traffic if in simulation mode
        if self.simulate_mode {
            self.simulate_mesh_traffic();
        }
        
        // Broadcast if we have data to share
        if let Some(packet) = self.node.next_broadcast() {
            // In real implementation, would send to mesh
            if self.simulate_mode {
                // Loop back for testing
                self.node.process_packet(packet);
            }
        }
    }
    
    /// Simulate incoming mesh packets for testing
    fn simulate_mesh_traffic(&mut self) {
        self.sim_timer += 1;
        
        // Generate different objects over time
        match self.sim_timer {
            10 => self.create_simulated_object(0x1234, object_types::OUTLET, 2000, 3000),
            20 => self.create_simulated_object(0x2345, object_types::THERMOSTAT, 5000, 3000),
            30 => self.create_simulated_object(0x3456, object_types::LIGHT_SWITCH, 2000, 6000),
            40 => self.create_simulated_object(0x4567, object_types::ELECTRICAL_PANEL, 8000, 1000),
            50..=200 if self.sim_timer % 5 == 0 => {
                // Send detail chunks for existing objects
                self.send_simulated_detail_chunk();
            }
            _ => {}
        }
    }
    
    fn create_simulated_object(&mut self, id: u16, obj_type: u8, x: u16, y: u16) {
        let mut object = ArxObject::new(id, obj_type, x, y, 1500);
        
        // Add some properties based on type
        match obj_type {
            object_types::OUTLET => {
                object.properties[0] = 12;  // Circuit 12
                object.properties[1] = 120; // 120V
            }
            object_types::THERMOSTAT => {
                object.properties[0] = 72;  // Current temp
                object.properties[1] = 70;  // Setpoint
            }
            _ => {}
        }
        
        let packet = MeshPacket::live_update(&object);
        self.node.process_packet(packet);
        self.packets_received += 1;
        
        self.messages.push(format!(
            "📡 Discovered: {} {:04X} at ({}, {})",
            Self::get_object_name(obj_type),
            id,
            x / 1000,
            y / 1000
        ));
    }
    
    fn send_simulated_detail_chunk(&mut self) {
        // Pick a random object to enhance
        let objects: Vec<u16> = self.node.live_objects.keys().copied().collect();
        if objects.is_empty() {
            return;
        }
        
        let object_id = objects[self.sim_timer as usize % objects.len()];
        let chunk_types = [
            arxos_core::ChunkType::MaterialDensity,
            arxos_core::ChunkType::ElectricalConnections,
            arxos_core::ChunkType::MaintenanceHistory,
        ];
        let chunk_type = chunk_types[self.sim_timer as usize % chunk_types.len()];
        
        let packet = MeshPacket::detail_chunk(
            object_id,
            self.sim_timer as u16,
            chunk_type,
            &[1, 2, 3, 4, 5, 6, 7, 8],
        );
        
        self.node.process_packet(packet);
        self.packets_received += 1;
    }
    
    fn get_object_name(obj_type: u8) -> &'static str {
        match obj_type {
            object_types::OUTLET => "Outlet",
            object_types::LIGHT_SWITCH => "Switch",
            object_types::THERMOSTAT => "Thermostat",
            object_types::ELECTRICAL_PANEL => "Panel",
            object_types::DOOR => "Door",
            object_types::WINDOW => "Window",
            object_types::CAMERA => "Camera",
            object_types::WIFI_AP => "WiFi AP",
            _ => "Unknown",
        }
    }
    
    fn handle_command(&mut self, cmd: &str) {
        let parts: Vec<&str> = cmd.split_whitespace().collect();
        if parts.is_empty() {
            return;
        }
        
        match parts[0] {
            "help" | "?" => {
                self.messages.push("Commands:".to_string());
                self.messages.push("  select <id>  - Select object by ID".to_string());
                self.messages.push("  list         - List all objects".to_string());
                self.messages.push("  stats        - Show statistics".to_string());
                self.messages.push("  clear        - Clear messages".to_string());
                self.messages.push("  quit         - Exit program".to_string());
            }
            "select" if parts.len() > 1 => {
                if let Ok(id) = u16::from_str_radix(parts[1], 16) {
                    self.selected_object = Some(id);
                    self.messages.push(format!("Selected object {:04X}", id));
                    self.current_tab = Tab::ObjectDetail;
                }
            }
            "list" => {
                self.messages.push(format!("Objects: {} tracked", self.node.live_objects.len()));
                for (id, obj) in &self.node.live_objects {
                    let detail = self.node.detail_store.get_completeness(*id);
                    self.messages.push(format!(
                        "  {:04X}: {} @ ({}, {}) - {:.0}% complete",
                        id,
                        Self::get_object_name(obj.object_type),
                        obj.x / 1000,
                        obj.y / 1000,
                        detail.completeness() * 100.0
                    ));
                }
            }
            "stats" => {
                let elapsed = self.start_time.elapsed().as_secs();
                self.messages.push(format!("Runtime: {}s", elapsed));
                self.messages.push(format!("Packets: {}", self.packets_received));
                self.messages.push(format!("BILT earned: {}", self.node.stats.bilt_earned));
            }
            "clear" => {
                self.messages.clear();
                self.messages.push("Terminal cleared".to_string());
            }
            _ => {
                self.messages.push(format!("Unknown command: {}", parts[0]));
            }
        }
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    // Parse command-line arguments
    let args = Args::parse();
    
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    
    // Create app state
    let mut app = App::new(args);
    
    // Run the app
    let res = run_app(&mut terminal, app);
    
    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;
    
    if let Err(err) = res {
        eprintln!("Error: {}", err);
    }
    
    Ok(())
}

fn run_app<B: Backend>(terminal: &mut Terminal<B>, mut app: App) -> io::Result<()> {
    let tick_rate = Duration::from_millis(100);  // 10 FPS
    let mut last_tick = Instant::now();
    
    loop {
        terminal.draw(|f| ui(f, &mut app))?;
        
        let timeout = tick_rate
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_secs(0));
            
        if crossterm::event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match key.code {
                        KeyCode::Char('q') if app.current_tab != Tab::Terminal => {
                            return Ok(());
                        }
                        KeyCode::Tab => {
                            app.current_tab = match app.current_tab {
                                Tab::FloorPlan => Tab::ObjectDetail,
                                Tab::ObjectDetail => Tab::MeshStatus,
                                Tab::MeshStatus => Tab::Terminal,
                                Tab::Terminal => Tab::FloorPlan,
                            };
                        }
                        KeyCode::Char('1') => app.current_tab = Tab::FloorPlan,
                        KeyCode::Char('2') => app.current_tab = Tab::ObjectDetail,
                        KeyCode::Char('3') => app.current_tab = Tab::MeshStatus,
                        KeyCode::Char('4') => app.current_tab = Tab::Terminal,
                        KeyCode::Char(c) if app.current_tab == Tab::Terminal => {
                            app.command_buffer.push(c);
                        }
                        KeyCode::Backspace if app.current_tab == Tab::Terminal => {
                            app.command_buffer.pop();
                        }
                        KeyCode::Enter if app.current_tab == Tab::Terminal => {
                            let cmd = app.command_buffer.clone();
                            app.command_buffer.clear();
                            app.messages.push(format!("> {}", cmd));
                            
                            if cmd == "quit" || cmd == "q" {
                                return Ok(());
                            }
                            
                            app.handle_command(&cmd);
                        }
                        _ => {}
                    }
                }
            }
        }
        
        if last_tick.elapsed() >= tick_rate {
            app.tick();
            last_tick = Instant::now();
        }
    }
}

fn ui(f: &mut Frame, app: &mut App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Header
            Constraint::Min(0),     // Main content
            Constraint::Length(3),  // Footer
        ])
        .split(f.size());
    
    render_header(f, app, chunks[0]);
    render_main_content(f, app, chunks[1]);
    render_footer(f, app, chunks[2]);
}

fn render_header(f: &mut Frame, app: &App, area: Rect) {
    let header_text = format!(
        " ARXOS │ Node {:04X} │ Building {:04X} │ {} Mode │ BILT: {} ",
        app.node.node_id,
        app.node.building_id,
        if app.simulate_mode { "SIMULATION" } else { "LIVE" },
        app.node.stats.bilt_earned
    );
    
    let header = Paragraph::new(header_text)
        .style(Style::default().bg(Color::Blue).fg(Color::White))
        .block(Block::default().borders(Borders::NONE));
    
    f.render_widget(header, area);
}

fn render_main_content(f: &mut Frame, app: &mut App, area: Rect) {
    let tabs = [" [1] Floor Plan ", " [2] Object Detail ", " [3] Mesh Status ", " [4] Terminal "];
    let mut tab_line = String::new();
    
    for (i, tab) in tabs.iter().enumerate() {
        let tab_enum = match i {
            0 => Tab::FloorPlan,
            1 => Tab::ObjectDetail,
            2 => Tab::MeshStatus,
            _ => Tab::Terminal,
        };
        
        if tab_enum == app.current_tab {
            tab_line.push_str(&format!("{}", tab.on_cyan().black()));
        } else {
            tab_line.push_str(tab);
        }
    }
    
    let content_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),  // Tab bar
            Constraint::Min(0),     // Content
        ])
        .split(area);
    
    // Render tab bar
    let tab_bar = Paragraph::new(tab_line)
        .style(Style::default().fg(Color::White));
    f.render_widget(tab_bar, content_chunks[0]);
    
    // Render content based on selected tab
    match app.current_tab {
        Tab::FloorPlan => render_floor_plan(f, app, content_chunks[1]),
        Tab::ObjectDetail => render_object_detail(f, app, content_chunks[1]),
        Tab::MeshStatus => render_mesh_status(f, app, content_chunks[1]),
        Tab::Terminal => render_terminal(f, app, content_chunks[1]),
    }
}

fn render_floor_plan(f: &mut Frame, app: &mut App, area: Rect) {
    let mut lines = vec![];
    
    // Create a simple ASCII floor plan
    lines.push(Line::from("╔════════════════════════════════════════╗"));
    lines.push(Line::from("║          FLOOR PLAN - LEVEL 1          ║"));
    lines.push(Line::from("╠════════════════════════════════════════╣"));
    
    // Add a grid
    for y in 0..15 {
        let mut line = String::from("║ ");
        for x in 0..40 {
            let mut found = false;
            
            // Check if any object is at this position
            for (id, obj) in &app.node.live_objects {
                let obj_x = (obj.x / 500) as usize;  // Scale to grid
                let obj_y = (obj.y / 500) as usize;
                
                if obj_x == x && obj_y == y {
                    let symbol = match obj.object_type {
                        object_types::OUTLET => 'o',
                        object_types::LIGHT_SWITCH => 's',
                        object_types::THERMOSTAT => 't',
                        object_types::ELECTRICAL_PANEL => '⚡',
                        object_types::DOOR => 'D',
                        object_types::CAMERA => 'C',
                        object_types::WIFI_AP => '@',
                        _ => '?',
                    };
                    line.push(symbol);
                    found = true;
                    break;
                }
            }
            
            if !found {
                line.push(if (x + y) % 10 == 0 { '·' } else { ' ' });
            }
        }
        line.push_str(" ║");
        lines.push(Line::from(line));
    }
    
    lines.push(Line::from("╚════════════════════════════════════════╝"));
    lines.push(Line::from(""));
    lines.push(Line::from("Legend: o=Outlet s=Switch t=Thermostat ⚡=Panel"));
    lines.push(Line::from(format!("Objects tracked: {}", app.node.live_objects.len())));
    
    let paragraph = Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title(" Floor Plan "))
        .style(Style::default().fg(Color::White));
    
    f.render_widget(paragraph, area);
}

fn render_object_detail(f: &mut Frame, app: &mut App, area: Rect) {
    let content = if let Some(object_id) = app.selected_object {
        if let Some(object) = app.node.live_objects.get(&object_id) {
            let detail_level = app.node.detail_store.get_completeness(object_id);
            let rendered = app.renderer.render_object(object, &detail_level);
            
            let mut lines = vec![];
            for line in rendered.lines() {
                lines.push(Line::from(line.to_string()));
            }
            
            // Add progress bar
            lines.push(Line::from(""));
            lines.push(Line::from(format!(
                "Detail Level: {:.1}%",
                detail_level.completeness() * 100.0
            )));
            
            let progress = arxos_core::render_progress_bar(detail_level.completeness(), 40);
            lines.push(Line::from(progress.as_str()));
            
            lines
        } else {
            vec![Line::from("Object not found")]
        }
    } else {
        vec![Line::from("No object selected. Use 'select <id>' command in Terminal.")]
    };
    
    let paragraph = Paragraph::new(content)
        .block(Block::default().borders(Borders::ALL).title(" Object Detail "))
        .style(Style::default().fg(Color::White));
    
    f.render_widget(paragraph, area);
}

fn render_mesh_status(f: &mut Frame, app: &App, area: Rect) {
    let status = app.node.status_report();
    let mut lines = vec![];
    
    for line in status.lines() {
        lines.push(Line::from(line.to_string()));
    }
    
    lines.push(Line::from(""));
    lines.push(Line::from("═══ Packet Statistics ═══"));
    lines.push(Line::from(format!("Total received: {}", app.packets_received)));
    lines.push(Line::from(format!("Sent: {}", app.node.stats.packets_sent)));
    lines.push(Line::from(format!("Live updates: {}", app.node.stats.live_updates)));
    lines.push(Line::from(format!("Detail chunks: {}", app.node.stats.detail_chunks)));
    
    let paragraph = Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title(" Mesh Network Status "))
        .style(Style::default().fg(Color::White));
    
    f.render_widget(paragraph, area);
}

fn render_terminal(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(0),     // Messages
            Constraint::Length(3),  // Input
        ])
        .split(area);
    
    // Render messages
    let messages: Vec<ListItem> = app.messages
        .iter()
        .rev()
        .take(chunks[0].height as usize - 2)
        .rev()
        .map(|msg| ListItem::new(msg.as_str()))
        .collect();
    
    let messages_list = List::new(messages)
        .block(Block::default().borders(Borders::TOP | Borders::LEFT | Borders::RIGHT).title(" Terminal "));
    
    f.render_widget(messages_list, chunks[0]);
    
    // Render input
    let input = Paragraph::new(format!("> {}", app.command_buffer))
        .style(Style::default().fg(Color::Yellow))
        .block(Block::default().borders(Borders::BOTTOM | Borders::LEFT | Borders::RIGHT));
    
    f.render_widget(input, chunks[1]);
}

fn render_footer(f: &mut Frame, app: &App, area: Rect) {
    let elapsed = app.start_time.elapsed().as_secs();
    let footer_text = format!(
        " [Tab] Switch View │ [q] Quit │ Runtime: {}s │ {} ",
        elapsed,
        if app.simulate_mode { "SIMULATION" } else { "LIVE MESH" }
    );
    
    let footer = Paragraph::new(footer_text)
        .style(Style::default().bg(Color::DarkGray).fg(Color::White))
        .alignment(Alignment::Center);
    
    f.render_widget(footer, area);
}