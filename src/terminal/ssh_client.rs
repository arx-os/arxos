//! SSH Client for connecting to Arxos mesh nodes
//!
//! Provides secure terminal access to mesh nodes via SSH protocol

use async_trait::async_trait;
use russh::client::{self, Handle};
use russh::{Channel, ChannelMsg, Disconnect, Pty, ChannelId};
use russh_keys::key::{PublicKey, KeyPair};
use std::sync::Arc;
use tokio::sync::{mpsc, Mutex};
use thiserror::Error;
use anyhow::Result;
use log::{debug, error, info, warn};
use std::time::Duration;
use futures::StreamExt;

/// SSH client errors
#[derive(Error, Debug)]
pub enum SshClientError {
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),
    
    #[error("Authentication failed")]
    AuthenticationFailed,
    
    #[error("SSH error: {0}")]
    SshError(#[from] russh::Error),
    
    #[error("Key error: {0}")]
    KeyError(#[from] russh_keys::Error),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Channel closed")]
    ChannelClosed,
    
    #[error("Timeout")]
    Timeout,
}

/// SSH connection configuration
#[derive(Debug, Clone)]
pub struct SshConfig {
    pub host: String,
    pub port: u16,
    pub username: String,
    pub private_key_path: Option<String>,
    pub password: Option<String>,
    pub timeout_seconds: u64,
    pub keepalive_seconds: u32,
}

impl Default for SshConfig {
    fn default() -> Self {
        Self {
            host: "mesh-node.local".to_string(),
            port: 2222,  // Non-standard port for security
            username: "arxos".to_string(),
            private_key_path: None,
            password: None,
            timeout_seconds: 30,
            keepalive_seconds: 15,
        }
    }
}

/// SSH client for mesh node connection
pub struct MeshSshClient {
    config: SshConfig,
    session: Option<Handle<MeshClientHandler>>,
    channel: Option<Channel<ChannelMsg>>,
    output_rx: mpsc::UnboundedReceiver<Vec<u8>>,
    output_tx: mpsc::UnboundedSender<Vec<u8>>,
    input_tx: Option<mpsc::UnboundedSender<Vec<u8>>>,
}

impl MeshSshClient {
    /// Create new SSH client
    pub fn new(config: SshConfig) -> Self {
        let (output_tx, output_rx) = mpsc::unbounded_channel();
        
        Self {
            config,
            session: None,
            channel: None,
            output_rx,
            output_tx,
            input_tx: None,
        }
    }
    
    /// Connect to mesh node
    pub async fn connect(&mut self) -> Result<(), SshClientError> {
        info!("Connecting to {}:{}", self.config.host, self.config.port);
        
        // Create SSH client configuration
        let mut ssh_config = client::Config::default();
        ssh_config.connection_timeout = Some(Duration::from_secs(self.config.timeout_seconds));
        ssh_config.keepalive_interval = Some(Duration::from_secs(self.config.keepalive_seconds as u64));
        
        // Only use secure algorithms
        ssh_config.preferred.key.clear();
        ssh_config.preferred.key.push(russh::kex::ED25519);
        
        // Create client handler
        let (input_tx, input_rx) = mpsc::unbounded_channel();
        self.input_tx = Some(input_tx);
        
        let handler = MeshClientHandler {
            output_tx: self.output_tx.clone(),
            input_rx: Arc::new(Mutex::new(input_rx)),
            authenticated: false,
        };
        
        // Connect to server
        let addr = format!("{}:{}", self.config.host, self.config.port);
        let session = client::connect(Arc::new(ssh_config), &addr, handler)
            .await
            .map_err(|e| SshClientError::ConnectionFailed(e.to_string()))?;
        
        // Authenticate
        self.authenticate(&session).await?;
        
        // Request PTY and shell
        let channel = session.channel_open_session().await?;
        
        // Request pseudo-terminal
        channel.request_pty(
            false,  // want_reply
            "xterm-256color",  // term
            80,     // columns
            24,     // rows
            0,      // pixel width
            0,      // pixel height
            &[],    // terminal modes
        ).await?;
        
        // Request shell
        channel.request_shell(false).await?;
        
        self.session = Some(session);
        self.channel = Some(channel);
        
        info!("Successfully connected to mesh node");
        Ok(())
    }
    
    /// Authenticate with the server
    async fn authenticate(&self, session: &Handle<MeshClientHandler>) -> Result<(), SshClientError> {
        // Try key authentication first
        if let Some(key_path) = &self.config.private_key_path {
            debug!("Attempting key authentication with {}", key_path);
            
            let key_data = tokio::fs::read(key_path).await?;
            let keypair = russh_keys::decode_secret_key(&key_data, None)?;
            
            let auth_result = session
                .authenticate_publickey(&self.config.username, Arc::new(keypair))
                .await?;
            
            if auth_result {
                info!("Key authentication successful");
                return Ok(());
            }
        }
        
        // Try password authentication
        if let Some(password) = &self.config.password {
            debug!("Attempting password authentication");
            
            let auth_result = session
                .authenticate_password(&self.config.username, password)
                .await?;
            
            if auth_result {
                info!("Password authentication successful");
                return Ok(());
            }
        }
        
        Err(SshClientError::AuthenticationFailed)
    }
    
    /// Send data to the remote terminal
    pub async fn send(&mut self, data: &[u8]) -> Result<(), SshClientError> {
        if let Some(channel) = &self.channel {
            channel.data(data).await?;
            Ok(())
        } else {
            Err(SshClientError::ChannelClosed)
        }
    }
    
    /// Send a command and wait for response
    pub async fn send_command(&mut self, command: &str) -> Result<String, SshClientError> {
        // Send command with newline
        let cmd_bytes = format!("{}\n", command).into_bytes();
        self.send(&cmd_bytes).await?;
        
        // Wait for response (with timeout)
        let timeout = Duration::from_secs(5);
        let start = tokio::time::Instant::now();
        let mut response = Vec::new();
        
        while start.elapsed() < timeout {
            // Check for output
            if let Ok(data) = self.output_rx.try_recv() {
                response.extend_from_slice(&data);
                
                // Check if we have a complete response (ends with prompt)
                let response_str = String::from_utf8_lossy(&response);
                if response_str.contains("arxos@mesh:~$") || 
                   response_str.contains("\n>") {
                    break;
                }
            }
            
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
        
        if response.is_empty() {
            return Err(SshClientError::Timeout);
        }
        
        Ok(String::from_utf8_lossy(&response).to_string())
    }
    
    /// Receive data from the remote terminal
    pub async fn receive(&mut self) -> Option<Vec<u8>> {
        self.output_rx.recv().await
    }
    
    /// Check if connected
    pub fn is_connected(&self) -> bool {
        self.session.is_some() && self.channel.is_some()
    }
    
    /// Disconnect from the server
    pub async fn disconnect(&mut self) -> Result<(), SshClientError> {
        if let Some(session) = self.session.take() {
            session.disconnect(
                Disconnect::ByApplication,
                "User disconnected",
                "en-US",
            ).await?;
        }
        
        self.channel = None;
        info!("Disconnected from mesh node");
        Ok(())
    }
    
    /// Execute a query on the mesh node
    pub async fn query(&mut self, query: &str) -> Result<String, SshClientError> {
        let command = format!("arxos query \"{}\"", query);
        self.send_command(&command).await
    }
    
    /// Trigger a LiDAR scan
    pub async fn trigger_scan(&mut self, location: Option<&str>) -> Result<String, SshClientError> {
        let command = match location {
            Some(loc) => format!("arxos scan {}", loc),
            None => "arxos scan".to_string(),
        };
        self.send_command(&command).await
    }
    
    /// Get mesh status
    pub async fn get_status(&mut self) -> Result<String, SshClientError> {
        self.send_command("arxos status").await
    }
    
    /// Get BILT balance
    pub async fn get_bilt_balance(&mut self) -> Result<String, SshClientError> {
        self.send_command("arxos bilt").await
    }
}

/// SSH client handler for async operations
struct MeshClientHandler {
    output_tx: mpsc::UnboundedSender<Vec<u8>>,
    input_rx: Arc<Mutex<mpsc::UnboundedReceiver<Vec<u8>>>>,
    authenticated: bool,
}

#[async_trait]
impl client::Handler for MeshClientHandler {
    type Error = SshClientError;
    
    async fn check_server_key(
        &mut self,
        _server_public_key: &PublicKey,
    ) -> Result<bool, Self::Error> {
        // TODO: Implement proper host key verification
        // For now, accept all keys (INSECURE - fix for production)
        warn!("Accepting server key without verification - implement proper host key checking!");
        Ok(true)
    }
    
    async fn data(
        &mut self,
        _channel: ChannelId,
        data: &[u8],
        _session: &mut client::Session,
    ) -> Result<(), Self::Error> {
        // Send received data to the output channel
        let _ = self.output_tx.send(data.to_vec());
        Ok(())
    }
    
    async fn extended_data(
        &mut self,
        _channel: ChannelId,
        _ext: u32,
        data: &[u8],
        _session: &mut client::Session,
    ) -> Result<(), Self::Error> {
        // Handle stderr data
        let _ = self.output_tx.send(data.to_vec());
        Ok(())
    }
}

/// Load SSH configuration from file
pub async fn load_config(config_path: Option<&str>) -> Result<SshConfig> {
    let path = if let Some(p) = config_path {
        std::path::PathBuf::from(p)
    } else {
        // Default config location
        let dirs = directories::ProjectDirs::from("io", "arxos", "terminal")
            .ok_or_else(|| anyhow::anyhow!("Could not determine config directory"))?;
        dirs.config_dir().join("ssh_config.toml")
    };
    
    if path.exists() {
        let content = tokio::fs::read_to_string(&path).await?;
        let config: SshConfig = toml::from_str(&content)?;
        Ok(config)
    } else {
        // Create default config
        let config = SshConfig::default();
        
        // Try to save it
        if let Some(parent) = path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        
        let content = toml::to_string_pretty(&config)?;
        tokio::fs::write(&path, content).await?;
        
        info!("Created default config at {:?}", path);
        Ok(config)
    }
}

/// Interactive password prompt
pub fn prompt_password(prompt: &str) -> Result<String> {
    rpassword::prompt_password(prompt).map_err(Into::into)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_config_default() {
        let config = SshConfig::default();
        assert_eq!(config.port, 2222);
        assert_eq!(config.username, "arxos");
    }
    
    #[tokio::test]
    async fn test_client_creation() {
        let config = SshConfig::default();
        let client = MeshSshClient::new(config);
        assert!(!client.is_connected());
    }
}