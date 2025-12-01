use crate::git::manager::{BuildingGitManager, GitConfigManager};
use crate::tui::terminal::TerminalManager;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Wrap},
};
use std::error::Error;
use std::time::Duration;

pub struct DiffView {
    git_manager: BuildingGitManager,
}

impl DiffView {
    pub fn new() -> Result<Self, Box<dyn Error>> {
        let config = GitConfigManager::load_from_arx_config_or_env();
        let git_manager = BuildingGitManager::new(".", "current", config)?;
        
        Ok(Self {
            git_manager,
        })
    }

    pub fn run(&self) -> Result<(), Box<dyn Error>> {
        let mut terminal_manager = TerminalManager::new()?;

        loop {
            terminal_manager.terminal().draw(|f| {
                let size = f.size();
                
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

                let title = Paragraph::new("ArxOS Diff Viewer")
                    .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
                    .alignment(Alignment::Center)
                    .block(Block::default().borders(Borders::ALL));
                f.render_widget(title, chunks[0]);

                // Real diff content
                let diff_text = self.get_diff_text();

                let content = Paragraph::new(diff_text)
                    .block(Block::default().title("Changes").borders(Borders::ALL))
                    .wrap(Wrap { trim: true });
                f.render_widget(content, chunks[1]);

                let footer = Paragraph::new("Press 'q' to quit")
                    .style(Style::default().fg(Color::Gray))
                    .alignment(Alignment::Center)
                    .block(Block::default().borders(Borders::ALL));
                f.render_widget(footer, chunks[2]);
            })?;

            if let Some(Event::Key(key)) = terminal_manager.poll_event(Duration::from_millis(100))? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => break,
                    _ => {}
                }
            }
        }

        Ok(())
    }

    fn get_diff_text(&self) -> Vec<Line> {
        let mut lines = Vec::new();

        match self.git_manager.get_diff(None, None) {
            Ok(diff_result) => {
                if diff_result.file_diffs.is_empty() {
                    lines.push(Line::from("No changes detected."));
                } else {
                    let mut current_file = String::new();
                    
                    for file_diff in diff_result.file_diffs {
                        // Add file header if file changes
                        if file_diff.file_path != current_file {
                            if !current_file.is_empty() {
                                lines.push(Line::from(""));
                            }
                            current_file = file_diff.file_path.clone();
                            lines.push(Line::from(vec![
                                Span::styled(format!("File: {}", current_file), Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
                            ]));
                        }
                        
                        let (prefix, color) = match file_diff.line_type {
                            crate::git::diff::DiffLineType::Addition => ("+ ", Color::Green),
                            crate::git::diff::DiffLineType::Deletion => ("- ", Color::Red),
                            crate::git::diff::DiffLineType::Context => ("  ", Color::White),
                        };
                        
                        lines.push(Line::from(vec![
                            Span::styled(format!("{}{}", prefix, file_diff.content), Style::default().fg(color)),
                        ]));
                    }
                }
            },
            Err(e) => {
                lines.push(Line::from(vec![
                    Span::styled("Error getting diff: ", Style::default().fg(Color::Red)),
                    Span::raw(e.to_string()),
                ]));
            }
        }
        
        lines
    }
}
