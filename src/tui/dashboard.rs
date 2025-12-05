use crate::agent::dispatcher::AgentState;
use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Span, Line},
    widgets::{Block, Borders, Gauge, List, ListItem, Paragraph},
    Frame, Terminal,
};
use std::sync::Arc;
use std::time::Duration;

/// TUI Dashboard App State
pub struct App {
    pub title: String,
    pub should_quit: bool,
    pub sensors: Vec<SensorData>,
}

#[derive(Clone, Debug)]
pub struct SensorData {
    pub name: String,
    pub value: f64,
    pub unit: String,
}

impl App {
    pub fn new(title: &str, sensor_names: Vec<String>) -> App {
        let sensors = sensor_names.into_iter().map(|name| {
             SensorData { name, value: 0.0, unit: "-".to_string() }
        }).collect();

        App {
            title: title.to_string(),
            should_quit: false,
            sensors,
        }
    }

    pub fn on_tick(&mut self) {
        // Updates are now handled via hardware polling in the main loop
    }
}

pub async fn run_dashboard(state: Arc<AgentState>) -> Result<()> {
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = std::io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app state
    // Fetch available sensors from hardware
    let sensor_names = match state.hardware.list_sensors().await {
        Ok(names) => names,
        Err(e) => {
             // Fallback if Hardware list fails (e.g. not connected)
             vec![format!("Error listing sensors: {}", e)]
        }
    };
    
    // Sort for stability
    let mut sensor_names = sensor_names;
    sensor_names.sort();

    let mut app = App::new("ArxOS Dashboard", sensor_names);

    // Run app loop with state access
    let res = run_app(&mut terminal, &mut app, &state).await;

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        println!("{:?}", err)
    }

    Ok(())
}

async fn run_app<B: Backend>(terminal: &mut Terminal<B>, app: &mut App, state: &Arc<AgentState>) -> Result<()> {
    let tick_rate = Duration::from_millis(250);
    let mut last_tick = std::time::Instant::now();

    loop {
        terminal.draw(|f| ui(f, app))?;

        let timeout = tick_rate
            .checked_sub(last_tick.elapsed())
            .unwrap_or_else(|| Duration::from_secs(0));
            
        // Poll input events
        if crossterm::event::poll(timeout)? {
             if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => app.should_quit = true,
                    _ => {}
                }
            }
        }

        if last_tick.elapsed() >= tick_rate {
            // Update sensors
            for sensor in &mut app.sensors {
                // Skip error messages or non-sensor items if any
                if sensor.name.starts_with("Error") { continue; }
                
                // Read from hardware
                if let Ok(reading) = state.hardware.read_sensor(&sensor.name, "").await {
                    sensor.value = reading.value;
                    sensor.unit = reading.unit;
                }
            }
            
            app.on_tick();
            last_tick = std::time::Instant::now();
        }

        if app.should_quit {
            return Ok(());
        }
    }
}

fn ui(f: &mut Frame, app: &mut App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints(
            [
                Constraint::Percentage(10),
                Constraint::Percentage(40),
                Constraint::Percentage(50),
            ]
            .as_ref(),
        )
        .split(f.size());

    let title = Paragraph::new(app.title.as_str())
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::ALL).title("Info"));
    f.render_widget(title, chunks[0]);

    // Sensors List
    let sensors: Vec<ListItem> = app
        .sensors
        .iter()
        .map(|s| {
            let content = vec![Line::from(Span::raw(format!("{}: {:.2} {}", s.name, s.value, s.unit)))];
            ListItem::new(content)
        })
        .collect();
    let sensors_list = List::new(sensors)
        .block(Block::default().borders(Borders::ALL).title("Sensors"));
    f.render_widget(sensors_list, chunks[1]);
    
    // Gauge example
    let gauge = Gauge::default()
        .block(Block::default().borders(Borders::ALL).title("System Load"))
        .gauge_style(Style::default().fg(Color::Yellow))
        .percent(65);
    f.render_widget(gauge, chunks[2]);
}
