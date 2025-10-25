//! # Display Utilities
//!
//! This module provides utilities for formatting and displaying output
//! in the CLI application, including status displays, progress indicators,
//! and formatted output.

use crate::error::CliError;

/// Display a success message with emoji
pub fn display_success(message: &str) {
    println!("✅ {}", message);
}

/// Display an error message with emoji
pub fn display_error(message: &str) {
    eprintln!("❌ {}", message);
}

/// Display a warning message with emoji
pub fn display_warning(message: &str) {
    println!("⚠️  {}", message);
}

/// Display an info message with emoji
pub fn display_info(message: &str) {
    println!("ℹ️  {}", message);
}

/// Display a progress indicator
pub fn display_progress(current: usize, total: usize, operation: &str) {
    let percentage = (current as f64 / total as f64 * 100.0) as usize;
    let bar_length = 20;
    let filled_length = (current as f64 / total as f64 * bar_length as f64) as usize;
    
    let bar = "█".repeat(filled_length) + &"░".repeat(bar_length - filled_length);
    print!("\r🔄 {} [{}] {}% ({}/{})", operation, bar, percentage, current, total);
    
    if current == total {
        println!();
    }
}
