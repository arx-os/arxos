//! Search command for interactive fuzzy search browser

use crate::cli::commands::Command;
use crate::persistence;
use crate::tui::search::{SearchAction, SearchBrowser};
use crate::tui::TerminalManager;
use clap::Args;
use crossterm::event::{self, Event};
use std::time::Duration;

#[derive(Args, Debug)]
pub struct SearchCommand {
    /// Initial search query
    #[arg(short, long)]
    query: Option<String>,

    /// Maximum number of results
    #[arg(short = 'n', long, default_value = "50")]
    max_results: usize,
    
    /// Filter by result type (room, equipment, floor, building)
    #[arg(short = 't', long)]
    result_type: Option<String>,
    
    /// Filter by floor level
    #[arg(short = 'f', long)]
    floor: Option<i32>,
}

impl Command for SearchCommand {
    fn execute(&self) -> Result<(), Box<dyn std::error::Error>> {
        // Load building data from current directory
        let building_data = persistence::load_building_data_from_dir()?;

        // Initialize terminal
        let mut terminal_manager = TerminalManager::new()?;

        // Create search browser
        let mut browser = SearchBrowser::new(building_data);
        
        // Apply CLI filters
        if let Some(ref type_str) = self.result_type {
            use crate::tui::search::SearchResultType;
            let filter_type = match type_str.to_lowercase().as_str() {
                "room" => Some(SearchResultType::Room),
                "equipment" => Some(SearchResultType::Equipment),
                "floor" => Some(SearchResultType::Floor),
                "building" => Some(SearchResultType::Building),
                _ => {
                    eprintln!("Invalid result type: {}. Use: room, equipment, floor, building", type_str);
                    None
                }
            };
            browser.set_type_filter(filter_type);
        }
        
        if let Some(floor_level) = self.floor {
            browser.set_floor_filter(Some(floor_level));
        }
        
        if let Some(ref query) = self.query {
            // Set initial query if provided
            for c in query.chars() {
                browser.handle_key(event::KeyEvent::from(crossterm::event::KeyCode::Char(c)));
            }
        }

        // Main event loop
        let result = loop {
            terminal_manager.terminal().draw(|frame| {
                browser.render(frame, frame.size());
            })?;

            if event::poll(Duration::from_millis(100))? {
                if let Event::Key(key) = event::read()? {
                    match browser.handle_key(key) {
                        SearchAction::Continue => {}
                        SearchAction::Select(result) => {
                            break Ok(result);
                        }
                        SearchAction::Exit => {
                            // TerminalManager cleanup handled by Drop
                            return Ok(());
                        }
                    }
                }
            }
        };

        // TerminalManager cleanup handled by Drop trait

        // Display selected result
        match result {
            Ok(result) => {
                println!("Selected: {} {} - {}", result.icon(), result.title, result.subtitle);
                println!("ID: {}", result.id);
                Ok(())
            }
            Err(e) => Err(e),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_search_command_creation() {
        let cmd = SearchCommand {
            query: Some("test".to_string()),
            max_results: 10,
            result_type: None,
            floor: None,
        };
        assert_eq!(cmd.query, Some("test".to_string()));
        assert_eq!(cmd.max_results, 10);
    }
}
