use crate::git::manager::{BuildingGitManager, GitConfigManager};
use crate::tui::terminal::TerminalManager;
use crate::tui::theme::Theme;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Wrap},
};
use std::error::Error;
use std::time::Duration;

pub struct Dashboard {
    git_manager: BuildingGitManager,
    theme: Theme,
}

impl Dashboard {
    pub fn new() -> Result<Self, Box<dyn Error>> {
        let config = GitConfigManager::load_from_arx_config_or_env();
        let git_manager = BuildingGitManager::new(".", "current", config)?;
        
        Ok(Self {
            git_manager,
            theme: Theme::default(),
        })
    }

    pub fn run(&self) -> Result<(), Box<dyn Error>> {
        let mut terminal_manager = TerminalManager::new()?;

        loop {
            terminal_manager.terminal().draw(|f| {
                let size = f.size();
                
                // Layout
                let chunks = Layout::default()
                    .direction(Direction::Vertical)
                    .margin(1)
                    .constraints(
                        [
                            Constraint::Length(3), // Title
                            Constraint::Min(10),   // Content
                            Constraint::Length(3), // Footer
                        ]
                        .as_ref(),
                    )
                    .split(size);

                // Title
                let title = Paragraph::new("ArxOS Dashboard")
                    .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
                    .alignment(Alignment::Center)
                    .block(Block::default().borders(Borders::ALL));
                f.render_widget(title, chunks[0]);

                // Content
                let status_text = self.get_status_text();
                let content = Paragraph::new(status_text)
                    .style(Style::default().fg(Color::White))
                    .block(Block::default().title("Repository Status").borders(Borders::ALL))
                    .wrap(Wrap { trim: true });
                f.render_widget(content, chunks[1]);

                // Footer
                let footer = Paragraph::new("Press 'q' to quit")
                    .style(Style::default().fg(Color::Gray))
                    .alignment(Alignment::Center)
                    .block(Block::default().borders(Borders::ALL));
                f.render_widget(footer, chunks[2]);
            })?;

            // Event handling
            if let Some(Event::Key(key)) = terminal_manager.poll_event(Duration::from_millis(100))? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => break,
                    _ => {}
                }
            }
        }

        Ok(())
    }

    fn get_status_text(&self) -> Vec<Line> {
        let mut lines = Vec::new();

        // Mock data for now since git_manager might need a repo path or context
        // In a real implementation, we'd call self.git_manager methods
        
        lines.push(Line::from(vec![
            Span::styled("Current Branch: ", Style::default().fg(Color::Yellow)),
            Span::raw("main"),
        ]));
        
        lines.push(Line::from(""));

        lines.push(Line::from(vec![
            Span::styled("Last Commit: ", Style::default().fg(Color::Yellow)),
            Span::raw("a1b2c3d - Initial commit"),
        ]));

        lines.push(Line::from(""));

        lines.push(Line::from(vec![
            Span::styled("Status: ", Style::default().fg(Color::Green)),
            Span::raw("Clean"),
        ]));

        lines
    }
}
