//! Game engine for ASCII building exploration
//! 
//! This module provides the game-like interface for navigating buildings
//! via terminal, built on top of the ArxObject protocol.

pub mod world;
pub mod commands;
pub mod renderer;
pub mod player;

pub use world::{World, Room, Direction};
pub use commands::{Command, CommandParser};
pub use renderer::GameRenderer;
pub use player::{Player, PlayerState};