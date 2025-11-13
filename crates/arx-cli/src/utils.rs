//! Utility functions for the CLI

use arx::error::ArxResult;

pub fn print_success(message: &str) {
    println!("✅ {}", message);
}

pub fn print_error(message: &str) {
    eprintln!("❌ {}", message);
}

pub fn print_info(message: &str) {
    println!("ℹ️  {}", message);
}