//! WebSocket agent daemon (feature-gated)
//! 
//! Provides a local WebSocket server for PWA integration when agent feature is enabled.

#[cfg(feature = "agent")]
pub mod server;

#[cfg(feature = "agent")]
pub use server::*;

#[cfg(not(feature = "agent"))]
pub fn start_agent() -> Result<(), Box<dyn std::error::Error>> {
    eprintln!("❌ Agent feature not enabled. Rebuild with --features agent");
    Err("Agent feature not enabled".into())
}