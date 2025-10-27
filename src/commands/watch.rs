// Live monitoring dashboard command handler

use crossterm::{
    event::{self, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    widgets::{Block, Borders, Paragraph},
    Terminal,
};
use std::io::stdout;
use std::time::Duration;

/// Handle the watch command
pub fn handle_watch_command(
    building: Option<String>,
    floor: Option<i32>,
    room: Option<String>,
    refresh_interval: u64,
    sensors_only: bool,
    alerts_only: bool,
    _log_level: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Starting Live Monitoring Dashboard...");
    println!("   Building: {}", building.as_deref().unwrap_or("All"));
    println!("   Floor: {}", floor.map(|f| f.to_string()).unwrap_or("All".to_string()));
    println!("   Room: {}", room.as_deref().unwrap_or("All"));
    println!("   Refresh Interval: {}s", refresh_interval);
    println!("   Sensors Only: {}", sensors_only);
    println!("   Alerts Only: {}", alerts_only);
    
    // Initialize terminal
    enable_raw_mode()?;
    let mut stdout = stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    
    // Simple monitoring loop
    let mut should_quit = false;
    let start_time = std::time::Instant::now();
    
    while !should_quit {
        // Draw the monitoring UI
        terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3),
                    Constraint::Min(0),
                    Constraint::Length(3),
                ])
                .split(f.size());
            
            // Header
            let header = Paragraph::new(format!(
                "ArxOS Live Monitor - {} | Refresh: {}s | Runtime: {}s",
                building.as_deref().unwrap_or("All Buildings"),
                refresh_interval,
                start_time.elapsed().as_secs()
            ))
            .style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::ALL).title("Live Monitoring"));
            
            f.render_widget(header, chunks[0]);
            
            // Content
            let content = Paragraph::new(
                "Live monitoring dashboard is active.\n\n\
                 Sensor data will be displayed here.\n\
                 Alerts and logs will be shown in real-time.\n\n\
                 Press 'q' to quit."
            )
            .style(Style::default().fg(Color::Green))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::ALL).title("Status"));
            
            f.render_widget(content, chunks[1]);
            
            // Footer
            let footer = Paragraph::new("Press 'q' to quit | 'r' to refresh | 'h' for help")
                .style(Style::default().fg(Color::Gray))
                .alignment(Alignment::Center)
                .block(Block::default().borders(Borders::ALL).title("Controls"));
            
            f.render_widget(footer, chunks[2]);
        })?;
        
        // Handle events
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key_event) = event::read()? {
                match key_event.code {
                    KeyCode::Char('q') | KeyCode::Esc => {
                        should_quit = true;
                    }
                    _ => {}
                }
            }
        }
        
        // Small delay to prevent excessive CPU usage
        std::thread::sleep(Duration::from_millis(50));
    }
    
    // Cleanup terminal
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    
    println!("✅ Live monitoring stopped");
    Ok(())
}
