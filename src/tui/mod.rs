//! ArxOS Terminal User Interface Module
//!
//! Provides reusable Ratatui components and patterns for interactive terminal experiences.
//! Designed for non-technical building management professionals.

pub mod command_palette;
pub mod dashboard;
pub mod diff_view;
pub mod error_integration;
pub mod error_modal;
pub mod export;
pub mod help;
pub mod layouts;
pub mod merge_tool;
pub mod mouse;
pub mod spreadsheet;
pub mod terminal;
pub mod theme;
pub mod theme_manager;
pub mod users;
pub mod widgets;
pub mod workspace_manager;

pub use error_modal::{
    handle_error_modal_event, render_error_modal, ErrorAction, ErrorModal,
};
pub use help::{
    handle_help_event, render_help_overlay, HelpContext, HelpSystem,
};
pub use terminal::TerminalManager;
pub use theme::{StatusColor, Theme};

/// Simple building renderer for ASCII output
pub fn render_building(building_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("🏠 Rendering building: {}", building_name);
    
    // Load building data from current directory
    let building_data = crate::persistence::load_building_data_from_dir()?;
    let building = &building_data.building;
    
    if building.name != building_name && building.id != building_name {
        println!("⚠️  Warning: Loaded building '{}' does not match requested '{}'", building.name, building_name);
    }
    
    println!("🏢 {}", building.name);
    println!("   ID: {}", building.id);
    
    for floor in &building.floors {
        println!("   ├──  Floor {} (Level: {})", floor.name, floor.level);
        for wing in &floor.wings {
            println!("   │   ├── 🪽 Wing: {}", wing.name);
            for room in &wing.rooms {
                println!("   │   │   ├── 🚪 {}", room.name);
                // Limit equipment output to avoid spamming
                let eq_count = room.equipment.len();
                if eq_count > 0 {
                    if eq_count <= 3 {
                        for equipment in &room.equipment {
                            println!("   │   │   │   └── 📦 {}", equipment.name);
                        }
                    } else {
                        println!("   │   │   │   └── 📦 {} items...", eq_count);
                    }
                }
            }
        }
    }
    
    Ok(())
}
