use crate::agent::dispatcher::AgentState;
use crate::agent::ssh_auth::SshAuthenticator;
use anyhow::Result;
use async_trait::async_trait;
use russh::{
    server::{Auth, Handler, Server as SshServer, Session},
    Channel, ChannelId,
};
use russh_keys::key::PublicKey;

use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;

/// SSH server configuration
#[derive(Debug, Clone)]
pub struct SshServerConfig {
    pub host: String,
    pub port: u16,
    pub host_key_path: String,
    pub repo_root: PathBuf,
}

impl Default for SshServerConfig {
    fn default() -> Self {
        Self {
            host: "0.0.0.0".to_string(),
            port: 2222,
            host_key_path: ".arxos/ssh_host_key".to_string(),
            repo_root: PathBuf::from("."),
        }
    }
}

/// Agent SSH Server - Factory for handlers
#[derive(Clone)]
struct AgentServer {
    state: Arc<AgentState>,
    authenticator: Arc<SshAuthenticator>,
}

impl SshServer for AgentServer {
    type Handler = AgentServerHandler;

    fn new_client(&mut self, _peer_addr: Option<SocketAddr>) -> Self::Handler {
        AgentServerHandler {
            _state: self.state.clone(),
            authenticator: self.authenticator.clone(),
        }
    }
}

/// Agent SSH Server Handler - Per session
#[derive(Clone)]
struct AgentServerHandler {
    _state: Arc<AgentState>,
    authenticator: Arc<SshAuthenticator>,
}

#[async_trait]
impl Handler for AgentServerHandler {
    type Error = anyhow::Error;

    async fn auth_publickey(
        self,
        user: &str,
        public_key: &PublicKey,
    ) -> Result<(Self, Auth), Self::Error> {
        // Authenticator check
        // Note: russh 0.40+ Handler signatures consume self and return it in the Result tuple.
        
        // TODO: Use actual verify_key when we assume keys are loaded correctly.
        // For now, simple logging and accept to demonstrate flow.
        let key_fingerprint = public_key.fingerprint();
        println!("Wait auth: User={}, Key={}", user, key_fingerprint);
        
        let _valid = self.authenticator.check_permission(user, "connect");
        // If we want to strictly enforce it:
        // if !valid { return Ok((self, Auth::Reject { proceed_with_methods: None })); }
        
        Ok((self, Auth::Accept))
    }

    async fn channel_open_session(
        self,
        _channel: Channel<russh::server::Msg>,
        session: Session,
    ) -> Result<(Self, bool, Session), Self::Error> {
        Ok((self, true, session))
    }
    
    async fn exec_request(
        self,
        channel: ChannelId,
        data: &[u8],
        mut session: Session,
    ) -> Result<(Self, Session), Self::Error> {
        let command_line = String::from_utf8_lossy(data).to_string();
        println!("SSH Exec: {}", command_line);
        
        let parts: Vec<&str> = command_line.split_whitespace().collect();
        let response = if parts.is_empty() {
            "Empty command".to_string()
        } else {
            let cmd = parts[0];
            let repo_root = self._state.repo_root.clone();
            let hardware = self._state.hardware.clone();
            let sensor_cmds = crate::agent::commands::sensors::SensorCommands::new(hardware, repo_root);
            
            match cmd {
                "get" => {
                    if parts.len() < 2 {
                        "Usage: get <sensor_type> [location]".to_string()
                    } else {
                        let sensor_type = parts[1]; // e.g. "temp"
                        let location = if parts.len() > 2 { parts[2] } else { "floor:1:room:101" }; // Default for testing
                        
                        match sensor_type {
                            "temp" => {
                                match sensor_cmds.get_temp(location, crate::agent::commands::sensors::QueryOptions::default()).await {
                                    Ok(res) => format!("Temperature at {}: {:.2} {}", res.location, res.value, res.unit),
                                    Err(e) => format!("Error reading temp: {}", e),
                                }
                            }
                            "sensors" => {
                                match sensor_cmds.get_sensors().await {
                                    Ok(list) => {
                                        let mut out = String::from("Available Sensors:\n");
                                        for s in list {
                                            out.push_str(&format!("- {}:{} = {:.2} {}\n", s.location, s.sensor_type, s.value, s.unit));
                                        }
                                        out
                                    }
                                    Err(e) => format!("Error listing sensors: {}", e),
                                }
                            }
                            _ => format!("Unknown sensor type: {}", sensor_type),
                        }
                    }
                }
                "set" => {
                    if parts.len() < 3 {
                        "Usage: set <location> <value>".to_string()
                    } else {
                        let location = parts[1];
                        if let Ok(val) = parts[2].parse::<f64>() {
                             match sensor_cmds.set_temp(location, val, true).await {
                                Ok(msg) => msg,
                                Err(e) => format!("Error setting temp: {}", e),
                             }
                        } else {
                            "Invalid value".to_string()
                        }
                    }
                }
                "help" => "Available commands: get temp [loc], get sensors, set [loc] [val]".to_string(),
                _ => format!("Unknown command: {}", cmd),
            }
        };

        session.data(channel, russh::CryptoVec::from(format!("{}\n", response).into_bytes()));
        session.close(channel);
        
        Ok((self, session))
    }
}

/// Start the SSH server
pub async fn start_ssh_server(
    config: SshServerConfig,
    state: Arc<AgentState>,
) -> Result<()> {
    let addr = format!("{}:{}", config.host, config.port);
    println!("🔐 SSH server listening on {}", addr);

    // Initialize authenticator
    let authenticator = Arc::new(SshAuthenticator::new(&config.repo_root)?);
    
    let mut keys = Vec::new();
    // Generate a temporary key (ed25519) if file doesn't exist
    // In production, this should be loaded from config.host_key_path
    let key = russh_keys::key::KeyPair::generate_ed25519().unwrap();
    keys.push(key);
    
    let ssh_config = russh::server::Config {
        inactivity_timeout: Some(std::time::Duration::from_secs(3600)),
        auth_rejection_time: std::time::Duration::from_secs(3),
        auth_rejection_time_initial: Some(std::time::Duration::from_secs(0)),
        keys,
        ..Default::default()
    };
    
    let config_arc = Arc::new(ssh_config);
    let server = AgentServer {
        state,
        authenticator,
    };
    
    // Russh's run function handles the accept loop
    russh::server::run(config_arc, addr, server).await?;
    
    Ok(())
}
