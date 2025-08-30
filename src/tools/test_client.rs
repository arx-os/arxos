//! Test client for verifying SSH connectivity
//! 
//! Simple tool to test connection to mesh nodes

use russh::client::{self, Handle};
use russh_keys::key::PublicKey;
use std::sync::Arc;
use anyhow::Result;
use clap::Parser;

/// Test client arguments
#[derive(Parser, Debug)]
#[command(author, version, about = "Test SSH connection to mesh nodes")]
struct Args {
    /// Host to connect to
    #[arg(short = 'H', long, default_value = "localhost")]
    host: String,
    
    /// Port to connect to
    #[arg(short, long, default_value_t = 2222)]
    port: u16,
    
    /// Username
    #[arg(short, long, default_value = "arxos")]
    username: String,
    
    /// Command to execute
    #[arg(short, long)]
    command: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();
    let args = Args::parse();
    
    println!("Testing connection to {}:{}", args.host, args.port);
    
    // Create SSH config
    let config = Arc::new(client::Config::default());
    
    // Connect
    let addr = format!("{}:{}", args.host, args.port);
    let mut session = client::connect(config, &addr, TestHandler).await?;
    
    // Try to authenticate (no auth for testing)
    let auth_result = session.authenticate_none(&args.username).await?;
    
    if !auth_result {
        println!("Authentication failed, trying password 'test'");
        let auth_result = session.authenticate_password(&args.username, "test").await?;
        if !auth_result {
            eprintln!("Authentication failed!");
            return Ok(());
        }
    }
    
    println!("Connected and authenticated!");
    
    // Open channel
    let mut channel = session.channel_open_session().await?;
    
    if let Some(cmd) = args.command {
        // Execute command
        channel.exec(true, cmd).await?;
        
        // Read output
        let mut output = Vec::new();
        let mut code = None;
        
        loop {
            match channel.wait().await {
                Some(russh::ChannelMsg::Data { data }) => {
                    output.extend_from_slice(&data);
                }
                Some(russh::ChannelMsg::ExitStatus { exit_status }) => {
                    code = Some(exit_status);
                }
                Some(russh::ChannelMsg::Eof) => break,
                _ => {}
            }
        }
        
        println!("Output: {}", String::from_utf8_lossy(&output));
        if let Some(code) = code {
            println!("Exit code: {}", code);
        }
    } else {
        // Interactive shell
        channel.request_shell(true).await?;
        
        // Send test command
        channel.data(&b"arxos status\n"[..]).await?;
        
        // Read response
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        
        while let Some(msg) = channel.wait().await {
            match msg {
                russh::ChannelMsg::Data { data } => {
                    print!("{}", String::from_utf8_lossy(&data));
                }
                russh::ChannelMsg::Eof => break,
                _ => {}
            }
        }
    }
    
    // Disconnect
    session.disconnect(russh::Disconnect::ByApplication, "Test complete", "en").await?;
    
    println!("\nTest complete!");
    Ok(())
}

struct TestHandler;

#[async_trait::async_trait]
impl client::Handler for TestHandler {
    type Error = anyhow::Error;
    
    async fn check_server_key(
        &mut self,
        _server_public_key: &PublicKey,
    ) -> Result<bool, Self::Error> {
        // Accept all keys for testing
        Ok(true)
    }
}