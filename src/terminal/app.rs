//! Terminal Application State and Logic
//!
//! Manages the terminal UI and meshtastic connection to mesh nodes

use crate::meshtastic_client::{MeshtasticClient, MeshtasticConfig, MeshtasticClientError};
use crate::commands::CommandProcessor;
use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style, Stylize},
    text::Line,
    widgets::{Block, BorderType, Borders, List, ListItem, Paragraph, Tabs},
    Frame,
};

/// Application state
pub struct App {
    /// Current mode
    pub mode: AppMode,
    
    /// Meshtastic client
    meshtastic_client: Option<MeshtasticClient>,
    
    /// Meshtastic configuration
    meshtastic_config: MeshtasticConfig,
    
    /// Command processor
    command_processor: CommandProcessor,
    
    /// Terminal output buffer
    pub output: Vec<String>,
    
    /// Current input line
    pub input: String,
    
    /// Command history
    pub history: Vec<String>,
    
    /// History index
    history_index: usize,
    
    /// Connection status
    pub connection_status: ConnectionStatus,
    
    /// Current building data
    pub building_id: u16,
    
    /// Mesh statistics
    pub mesh_stats: MeshStats,
    
    /// Last error message
    pub error_message: Option<String>,
    
    /// Should quit
    pub should_quit: bool,
    
    /// Selected tab
    pub selected_tab: usize,
}

/// Application modes
#[derive(Debug, Clone, PartialEq)]
pub enum AppMode {
    Normal,
    Insert,
    Command,
    Connecting,
}

/// Connection status
#[derive(Debug, Clone)]
pub enum ConnectionStatus {
    Disconnected,
    Connecting,
    Connected { node_id: u16, rssi: i16 },
    Error(String),
}

/// Mesh network statistics
#[derive(Debug, Clone, Default)]
pub struct MeshStats {
    pub packets_sent: u32,
    pub packets_received: u32,
    pub neighbors: u8,
    pub uptime_hours: u32,
}

impl App {
    /// Create new application
    pub fn new(meshtastic_config: MeshtasticConfig) -> Self {
        Self {
            mode: AppMode::Normal,
            meshtastic_client: None,
            meshtastic_config,
            command_processor: CommandProcessor::new(),
            output: Vec::new(),
            input: String::new(),
            history: Vec::new(),
            history_index: 0,
            connection_status: ConnectionStatus::Disconnected,
            building_id: 0x0001,
            mesh_stats: MeshStats::default(),
            error_message: None,
            should_quit: false,
            selected_tab: 0,
        }
    }
    
    /// Connect to meshtastic network
    pub async fn connect(&mut self) -> Result<(), MeshtasticClientError> {
        self.connection_status = ConnectionStatus::Connecting;
        self.add_output("Connecting to meshtastic network...".to_string());
        
        let mut client = MeshtasticClient::new(self.meshtastic_config.clone());
        
        match client.connect().await {
            Ok(_) => {
                self.connection_status = ConnectionStatus::Connected {
                    node_id: self.meshtastic_config.node_id as u16,
                    rssi: -72,        // TODO: Get actual RSSI from radio
                };
                self.add_output("Connected to meshtastic network!".to_string());
                self.add_output("Type 'help' for available commands".to_string());
                
                // Get initial status
                if let Ok(status) = client.get_status().await {
                    self.add_output(status);
                }
                
                self.meshtastic_client = Some(client);
                Ok(())
            }
            Err(e) => {
                self.connection_status = ConnectionStatus::Error(e.to_string());
                self.error_message = Some(format!("Connection failed: {}", e));
                self.add_output(format!("Error: {}", e));
                Err(e)
            }
        }
    }
    
    /// Disconnect from meshtastic network
    pub async fn disconnect(&mut self) {
        if let Some(mut client) = self.meshtastic_client.take() {
            let _ = client.disconnect().await;
        }
        self.connection_status = ConnectionStatus::Disconnected;
        self.add_output("Disconnected from meshtastic network".to_string());
    }
    
    /// Process terminal input
    pub async fn process_input(&mut self) {
        if self.input.is_empty() {
            return;
        }
        
        let command = self.input.clone();
        self.history.push(command.clone());
        self.history_index = self.history.len();
        
        // Display command in output
        self.add_output(format!("> {}", command));
        self.input.clear();
        
        // Process local commands first
        if self.process_local_command(&command).await {
            return;
        }
        
        // Send to remote if connected
        if let Some(client) = &mut self.meshtastic_client {
            match client.send_command(&command).await {
                Ok(response) => {
                    self.add_output(response);
                }
                Err(e) => {
                    self.add_output(format!("Error: {}", e));
                }
            }
        } else {
            self.add_output("Not connected. Use 'connect' to connect to a mesh node.".to_string());
        }
    }
    
    /// Process local commands
    async fn process_local_command(&mut self, command: &str) -> bool {
        let parts: Vec<&str> = command.split_whitespace().collect();
        if parts.is_empty() {
            return true;
        }
        
        match parts[0] {
            "connect" => {
                let _ = self.connect().await;
                true
            }
            "disconnect" => {
                self.disconnect().await;
                true
            }
            "clear" => {
                self.output.clear();
                true
            }
            "quit" | "exit" => {
                self.should_quit = true;
                true
            }
            "config" => {
                self.show_config();
                true
            }
            "help" | "?" => {
                self.show_help();
                true
            }
            "load-plan" | "view-floor" | "list-floors" | "show-equipment" | "export-arxobjects" => {
                // Process document commands
                let result = self.command_processor.process(command).await;
                for line in result.output {
                    self.add_output(line);
                }
                true
            }
            _ => false,  // Not a local command
        }
    }
    
    /// Show configuration
    fn show_config(&mut self) {
        self.add_output("Current Configuration:".to_string());
        self.add_output(format!("  Host: {}", self.ssh_config.host));
        self.add_output(format!("  Port: {}", self.ssh_config.port));
        self.add_output(format!("  Username: {}", self.ssh_config.username));
        self.add_output(format!("  Timeout: {}s", self.ssh_config.timeout_seconds));
    }
    
    /// Show help
    fn show_help(&mut self) {
        self.add_output("Local Commands:".to_string());
        self.add_output("  connect              - Connect to mesh node".to_string());
        self.add_output("  disconnect           - Disconnect from node".to_string());
        self.add_output("  config               - Show configuration".to_string());
        self.add_output("  clear                - Clear terminal".to_string());
        self.add_output("  quit/exit            - Exit application".to_string());
        self.add_output("".to_string());
        self.add_output("Document Commands:".to_string());
        self.add_output("  load-plan <file>     - Load PDF/IFC building plan".to_string());
        self.add_output("  view-floor [n]       - View floor n (or current)".to_string());
        self.add_output("  list-floors          - List all floors".to_string());
        self.add_output("  show-equipment [n]   - Show equipment on floor".to_string());
        self.add_output("  export-arxobjects    - Export as ArxObjects".to_string());
        self.add_output("".to_string());
        self.add_output("Remote Commands (when connected):".to_string());
        self.add_output("  arxos query <search> - Query objects".to_string());
        self.add_output("  arxos scan [location]- Trigger scan".to_string());
        self.add_output("  arxos status         - Show status".to_string());
        self.add_output("  arxos mesh           - Mesh info".to_string());
        self.add_output("  arxos bilt           - BILT balance".to_string());
    }
    
    /// Add output line
    pub fn add_output(&mut self, line: String) {
        // Split by newlines and add each line
        for l in line.lines() {
            self.output.push(l.to_string());
        }
        
        // Limit output buffer size
        if self.output.len() > 1000 {
            self.output.drain(0..100);
        }
    }
    
    /// Handle key event
    pub async fn handle_key(&mut self, key: KeyEvent) -> bool {
        match self.mode {
            AppMode::Normal => self.handle_normal_key(key).await,
            AppMode::Insert => self.handle_insert_key(key).await,
            _ => false,
        }
    }
    
    /// Handle key in normal mode
    async fn handle_normal_key(&mut self, key: KeyEvent) -> bool {
        match key.code {
            KeyCode::Char('q') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.should_quit = true;
                true
            }
            KeyCode::Char('i') | KeyCode::Char(':') => {
                self.mode = AppMode::Insert;
                true
            }
            KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.output.clear();
                true
            }
            KeyCode::Tab => {
                self.selected_tab = (self.selected_tab + 1) % 3;
                true
            }
            _ => false,
        }
    }
    
    /// Handle key in insert mode
    async fn handle_insert_key(&mut self, key: KeyEvent) -> bool {
        match key.code {
            KeyCode::Esc => {
                self.mode = AppMode::Normal;
                true
            }
            KeyCode::Enter => {
                self.process_input().await;
                true
            }
            KeyCode::Char(c) => {
                self.input.push(c);
                true
            }
            KeyCode::Backspace => {
                self.input.pop();
                true
            }
            KeyCode::Up => {
                if self.history_index > 0 {
                    self.history_index -= 1;
                    self.input = self.history[self.history_index].clone();
                }
                true
            }
            KeyCode::Down => {
                if self.history_index < self.history.len() - 1 {
                    self.history_index += 1;
                    self.input = self.history[self.history_index].clone();
                } else if self.history_index == self.history.len() - 1 {
                    self.history_index = self.history.len();
                    self.input.clear();
                }
                true
            }
            _ => false,
        }
    }
    
    /// Render the UI
    pub fn render(&self, frame: &mut Frame) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(3),  // Header
                Constraint::Min(10),    // Main content
                Constraint::Length(3),  // Status bar
            ])
            .split(frame.size());
        
        self.render_header(frame, chunks[0]);
        self.render_main(frame, chunks[1]);
        self.render_status(frame, chunks[2]);
    }
    
    /// Render header
    fn render_header(&self, frame: &mut Frame, area: Rect) {
        let header = Block::default()
            .title(" Arxos Terminal - RF Mesh Network ")
            .title_alignment(Alignment::Center)
            .borders(Borders::ALL)
            .border_type(BorderType::Double)
            .style(Style::default().fg(Color::Cyan));
        
        frame.render_widget(header, area);
    }
    
    /// Render main content area
    fn render_main(&self, frame: &mut Frame, area: Rect) {
        let tabs = vec!["Terminal", "Objects", "Mesh"];
        let tabs = Tabs::new(tabs)
            .block(Block::default().borders(Borders::ALL))
            .select(self.selected_tab)
            .style(Style::default().fg(Color::White))
            .highlight_style(Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD));
        
        frame.render_widget(tabs, area);
        
        let inner = area.inner(&ratatui::layout::Margin {
            vertical: 2,
            horizontal: 1,
        });
        
        match self.selected_tab {
            0 => self.render_terminal(frame, inner),
            1 => self.render_objects(frame, inner),
            2 => self.render_mesh(frame, inner),
            _ => {}
        }
    }
    
    /// Render terminal tab
    fn render_terminal(&self, frame: &mut Frame, area: Rect) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Min(5),     // Output
                Constraint::Length(3),  // Input
            ])
            .split(area);
        
        // Output area
        let output_text: Vec<Line> = self.output
            .iter()
            .rev()
            .take(chunks[0].height as usize - 2)
            .rev()
            .map(|line| Line::from(line.as_str()))
            .collect();
        
        let output = Paragraph::new(output_text)
            .block(Block::default()
                .borders(Borders::ALL)
                .title(" Output "))
            .wrap(ratatui::widgets::Wrap { trim: false });
        
        frame.render_widget(output, chunks[0]);
        
        // Input area
        let input_text = if self.mode == AppMode::Insert {
            format!("{}█", self.input)
        } else {
            self.input.clone()
        };
        
        let input = Paragraph::new(input_text)
            .block(Block::default()
                .borders(Borders::ALL)
                .title(" Input (i to edit, ESC to exit) ")
                .border_style(if self.mode == AppMode::Insert {
                    Style::default().fg(Color::Yellow)
                } else {
                    Style::default()
                }));
        
        frame.render_widget(input, chunks[1]);
    }
    
    /// Render objects tab
    fn render_objects(&self, frame: &mut Frame, area: Rect) {
        let objects = vec![
            ListItem::new("Outlet @ (1000, 2000, 300) - Circuit 12"),
            ListItem::new("Light @ (2000, 2000, 2500) - Zone 3"),
            ListItem::new("Thermostat @ (3000, 1000, 1500) - 72°F"),
            ListItem::new("Smoke Detector @ (2000, 2000, 2800)"),
            ListItem::new("Emergency Exit @ (0, 3000, 0)"),
        ];
        
        let list = List::new(objects)
            .block(Block::default()
                .borders(Borders::ALL)
                .title(" Building Objects "))
            .highlight_style(Style::default().add_modifier(Modifier::BOLD))
            .highlight_symbol(">> ");
        
        frame.render_widget(list, area);
    }
    
    /// Render mesh tab
    fn render_mesh(&self, frame: &mut Frame, area: Rect) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(8),   // Stats
                Constraint::Min(5),      // Neighbors
            ])
            .split(area);
        
        // Mesh statistics
        let stats_text = vec![
            Line::from(format!("Packets Sent: {}", self.mesh_stats.packets_sent)),
            Line::from(format!("Packets Received: {}", self.mesh_stats.packets_received)),
            Line::from(format!("Active Neighbors: {}", self.mesh_stats.neighbors)),
            Line::from(format!("Uptime: {} hours", self.mesh_stats.uptime_hours)),
            Line::from(""),
            Line::from("RF Signal: -72 dBm (Good)"),
        ];
        
        let stats = Paragraph::new(stats_text)
            .block(Block::default()
                .borders(Borders::ALL)
                .title(" Mesh Statistics "));
        
        frame.render_widget(stats, chunks[0]);
        
        // Neighbor list
        let neighbors = vec![
            ListItem::new("Node 0x0002 - RSSI: -65 dBm - 12 hops"),
            ListItem::new("Node 0x0003 - RSSI: -78 dBm - 3 hops"),
            ListItem::new("Node 0x0004 - RSSI: -82 dBm - 7 hops"),
        ];
        
        let neighbor_list = List::new(neighbors)
            .block(Block::default()
                .borders(Borders::ALL)
                .title(" Neighbor Nodes "));
        
        frame.render_widget(neighbor_list, chunks[1]);
    }
    
    /// Render status bar
    fn render_status(&self, frame: &mut Frame, area: Rect) {
        let chunks = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Percentage(33),
                Constraint::Percentage(34),
                Constraint::Percentage(33),
            ])
            .split(area);
        
        // Connection status
        let (conn_text, conn_style) = match &self.connection_status {
            ConnectionStatus::Connected { node_id, rssi } => {
                (format!(" Connected: 0x{:04X} ({} dBm) ", node_id, rssi), 
                 Style::default().fg(Color::Green))
            }
            ConnectionStatus::Connecting => {
                (" Connecting... ".to_string(), Style::default().fg(Color::Yellow))
            }
            ConnectionStatus::Disconnected => {
                (" Disconnected ".to_string(), Style::default().fg(Color::Red))
            }
            ConnectionStatus::Error(e) => {
                (format!(" Error: {} ", e), Style::default().fg(Color::Red))
            }
        };
        
        let connection = Paragraph::new(conn_text)
            .block(Block::default().borders(Borders::ALL))
            .style(conn_style)
            .alignment(Alignment::Center);
        
        frame.render_widget(connection, chunks[0]);
        
        // Mode indicator
        let mode_text = match self.mode {
            AppMode::Normal => " NORMAL ",
            AppMode::Insert => " INSERT ",
            AppMode::Command => " COMMAND ",
            AppMode::Connecting => " CONNECTING ",
        };
        
        let mode = Paragraph::new(mode_text)
            .block(Block::default().borders(Borders::ALL))
            .style(Style::default().fg(Color::Cyan))
            .alignment(Alignment::Center);
        
        frame.render_widget(mode, chunks[1]);
        
        // Help text
        let help = Paragraph::new(" Ctrl+Q: Quit | Tab: Switch | i: Insert ")
            .block(Block::default().borders(Borders::ALL))
            .alignment(Alignment::Center);
        
        frame.render_widget(help, chunks[2]);
    }
}