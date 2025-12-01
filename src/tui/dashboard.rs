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

        match self.git_manager.get_status() {
            Ok(status) => {
                lines.push(Line::from(vec![
                    Span::styled("Current Branch: ", Style::default().fg(Color::Yellow)),
                    Span::raw(status.current_branch.clone()),
                ]));
                
                lines.push(Line::from(""));
                
                let status_color = if status.is_clean { Color::Green } else { Color::Red };
                lines.push(Line::from(vec![
                    Span::styled("Status: ", Style::default().fg(status_color)),
                    Span::raw(if status.is_clean { "Clean" } else { "Dirty" }),
                ]));
                
                // Clone to avoid borrow issues
                let modified_files = status.modified_files.clone();
                
                if !modified_files.is_empty() {
                    lines.push(Line::from(""));
                    lines.push(Line::from(Span::styled("Modified Files:", Style::default().fg(Color::Red))));
                    for file in modified_files.iter().take(5) {
                        lines.push(Line::from(vec![
                            Span::raw("  - "),
                            Span::raw(file.clone()),
                        ]));
                    }
                    if modified_files.len() > 5 {
                        lines.push(Line::from(vec![
                            Span::raw("  ... and "),
                            Span::raw((modified_files.len() - 5).to_string()),
                            Span::raw(" more"),
                        ]));
                    }
                }
            },
            Err(e) => {
                lines.push(Line::from(vec![
                    Span::styled("Error getting status: ", Style::default().fg(Color::Red)),
                    Span::raw(e.to_string()),
                ]));
            }
        }

        lines.push(Line::from(""));

        // Clone commits to avoid borrow issues
        let commits = self.git_manager.list_commits(1).unwrap_or_else(|_| Vec::new());
        if let Some(commit) = commits.first() {
            lines.push(Line::from(vec![
                Span::styled("Last Commit: ", Style::default().fg(Color::Yellow)),
                Span::raw(format!("{} - {}", &commit.id[..7], &commit.message)),
            ]));
            lines.push(Line::from(vec![
                Span::styled("Author: ", Style::default().fg(Color::Blue)),
                Span::raw(commit.author.clone()),
            ]));
            
            use chrono::{TimeZone, Utc};
            let dt = Utc.timestamp_opt(commit.time, 0).single().unwrap_or_default();
            lines.push(Line::from(vec![
                Span::styled("Date: ", Style::default().fg(Color::Blue)),
                Span::raw(dt.format("%Y-%m-%d %H:%M:%S").to_string()),
            ]));
        } else {
            lines.push(Line::from("No commits yet"));
        }

        lines
    }
}
