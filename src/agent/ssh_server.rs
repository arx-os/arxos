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
        _channel: ChannelId,
        data: &[u8],
        session: Session,
    ) -> Result<(Self, Session), Self::Error> {
        let command = String::from_utf8_lossy(data).to_string();
        println!("SSH Exec: {}", command);
        
        // FUTURE: Dispatch 'command' to self.state
        // For now, we just acknowledge receipt.
        
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
