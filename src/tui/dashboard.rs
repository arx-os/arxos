//! Dashboard module - requires both tui and agent features.
//!
//! Shows agent repo context (no hardware/sensor polling — drivers deferred).

#![cfg(feature = "agent")]

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
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Frame, Terminal,
};
use std::sync::Arc;
use std::time::Duration;

/// TUI Dashboard App State
pub struct App {
    pub title: String,
    pub should_quit: bool,
    pub lines: Vec<String>,
}

impl App {
    pub fn new(title: &str, lines: Vec<String>) -> App {
        App {
            title: title.to_string(),
            should_quit: false,
            lines,
        }
    }
}

pub async fn run_dashboard(state: Arc<AgentState>) -> Result<()> {
    enable_raw_mode()?;
    let mut stdout = std::io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let lines = vec![
        format!("Repo: {}", state.repo_root.display()),
        "Mode: agent edge bridge (git + IFC)".to_string(),
        "Hardware sensors: not in this build".to_string(),
        "Keys: q / Esc quit".to_string(),
    ];
    let mut app = App::new("ArxOS Agent Dashboard", lines);

    let res = run_app(&mut terminal, &mut app).await;

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

async fn run_app<B: Backend>(terminal: &mut Terminal<B>, app: &mut App) -> Result<()> {
    let tick_rate = Duration::from_millis(250);

    loop {
        terminal.draw(|f| ui(f, app))?;

        if crossterm::event::poll(tick_rate)? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => app.should_quit = true,
                    _ => {}
                }
            }
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
        .constraints([Constraint::Length(3), Constraint::Min(5)].as_ref())
        .split(f.size());

    let title = Paragraph::new(Line::from(vec![Span::styled(
        app.title.as_str(),
        Style::default()
            .fg(Color::Cyan)
            .add_modifier(Modifier::BOLD),
    )]))
    .block(Block::default().borders(Borders::ALL).title("ArxOS"));
    f.render_widget(title, chunks[0]);

    let items: Vec<ListItem> = app
        .lines
        .iter()
        .map(|s| ListItem::new(s.as_str()))
        .collect();
    let list = List::new(items).block(
        Block::default()
            .borders(Borders::ALL)
            .title("Status (no hardware drivers)"),
    );
    f.render_widget(list, chunks[1]);
}
