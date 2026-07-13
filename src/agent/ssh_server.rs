use crate::agent::dispatcher::AgentState;
use crate::agent::ssh_auth::SshAuthenticator;
use anyhow::Result;
use async_trait::async_trait;
use russh::{
    server::{Auth, Handler, Server as SshServer, Session},
    Channel, ChannelId, Pty,
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
            input_buffer: String::new(),
        }
    }
}

/// Agent SSH Server Handler - Per session
#[derive(Clone)]
struct AgentServerHandler {
    _state: Arc<AgentState>,
    authenticator: Arc<SshAuthenticator>,
    input_buffer: String,
}

#[async_trait]
impl Handler for AgentServerHandler {
    type Error = anyhow::Error;

    async fn auth_publickey(
        self,
        user: &str,
        public_key: &PublicKey,
    ) -> Result<(Self, Auth), Self::Error> {
        let key_fingerprint = public_key.fingerprint();
        log::info!(
            "SSH authentication attempt: user={}, key_fingerprint={}",
            user,
            key_fingerprint
        );

        if let Some(resolved_user) = self.authenticator.verify_key(public_key) {
            if resolved_user == user {
                if self
                    .authenticator
                    .check_permission(&resolved_user, "connect")
                {
                    log::info!("SSH authentication accepted for user={}", user);
                    return Ok((self, Auth::Accept));
                } else {
                    log::warn!(
                        "SSH authentication rejected: user={} lacks 'connect' permission",
                        user
                    );
                }
            } else {
                log::warn!(
                    "SSH authentication rejected: key belongs to user '{}', but connection requested as '{}'",
                    resolved_user,
                    user
                );
            }
        } else {
            log::warn!("SSH authentication rejected: public key not authorized");
        }

        Ok((
            self,
            Auth::Reject {
                proceed_with_methods: None,
            },
        ))
    }

    async fn channel_open_session(
        self,
        _channel: Channel<russh::server::Msg>,
        session: Session,
    ) -> Result<(Self, bool, Session), Self::Error> {
        Ok((self, true, session))
    }

    async fn pty_request(
        self,
        _channel: ChannelId,
        _term: &str,
        _col_width: u32,
        _row_height: u32,
        _pix_width: u32,
        _pix_height: u32,
        _modes: &[(Pty, u32)],
        session: Session,
    ) -> Result<(Self, Session), Self::Error> {
        Ok((self, session))
    }

    async fn shell_request(
        self,
        channel: ChannelId,
        mut session: Session,
    ) -> Result<(Self, Session), Self::Error> {
        let welcome = format!(
            "\r\nWelcome to ArxOS Agent Shell\r\nHost: {}\r\nType 'help' for commands, 'exit' to quit.\r\n\r\n> ", 
            self._state.repo_root.display()
        );
        session.data(channel, russh::CryptoVec::from(welcome.into_bytes()));
        Ok((self, session))
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
            let _ = self._state.repo_root.clone();

            match cmd {
                "get" | "set" => {
                    "Hardware/sensor SSH commands removed (revisit later). Use git/IFC agent RPC."
                        .to_string()
                }
                "help" => {
                    "Available: help. Sensor get/set deferred with hardware stack.".to_string()
                }
                _ => format!("Unknown command: {}", cmd),
            }
        };

        session.data(
            channel,
            russh::CryptoVec::from(format!("{}\n", response).into_bytes()),
        );
        session.close(channel);

        Ok((self, session))
    }

    async fn data(
        mut self,
        channel: ChannelId,
        data: &[u8],
        mut session: Session,
    ) -> Result<(Self, Session), Self::Error> {
        let input = String::from_utf8_lossy(data);

        for c in input.chars() {
            match c {
                '\r' | '\n' => {
                    session.data(channel, russh::CryptoVec::from("\r\n".as_bytes().to_vec()));

                    let cmd_line = std::mem::take(&mut self.input_buffer);
                    if !cmd_line.trim().is_empty() {
                        let parts: Vec<&str> = cmd_line.split_whitespace().collect();
                        let cmd = parts[0];

                        match cmd {
                            "exit" | "quit" => {
                                session.close(channel);
                                return Ok((self, session));
                            }
                            "help" => {
                                session.data(
                                    channel,
                                    russh::CryptoVec::from(
                                        "Commands: help, clear, exit (sensors deferred)\r\n"
                                            .as_bytes()
                                            .to_vec(),
                                    ),
                                );
                            }
                            "clear" => {
                                session.data(
                                    channel,
                                    russh::CryptoVec::from("\x1b[2J\x1b[H".as_bytes().to_vec()),
                                );
                            }
                            "get" | "set" => {
                                session.data(
                                    channel,
                                    russh::CryptoVec::from(
                                        "Hardware/sensor commands removed; use agent git/IFC RPC.\r\n"
                                            .as_bytes()
                                            .to_vec(),
                                    ),
                                );
                            }
                            _ => {
                                session.data(
                                    channel,
                                    russh::CryptoVec::from(
                                        format!("Unrecognized command: {}\r\n", cmd)
                                            .into_bytes(),
                                    ),
                                );
                            }
                        }
                    }

                    session.data(channel, russh::CryptoVec::from("> ".as_bytes().to_vec()));
                }
                '\x08' | '\x7f' => {
                    // Backspace
                    if !self.input_buffer.is_empty() {
                        self.input_buffer.pop();
                        session.data(
                            channel,
                            russh::CryptoVec::from("\x08 \x08".as_bytes().to_vec()),
                        );
                    }
                }
                '\x03' => {
                    // Ctrl-C
                    session.data(
                        channel,
                        russh::CryptoVec::from("^C\r\n".as_bytes().to_vec()),
                    );
                    self.input_buffer.clear();
                    session.data(channel, russh::CryptoVec::from("> ".as_bytes().to_vec()));
                }
                _ => {
                    self.input_buffer.push(c);
                    let mut buf = [0; 4];
                    session.data(
                        channel,
                        russh::CryptoVec::from(c.encode_utf8(&mut buf).as_bytes().to_vec()),
                    );
                }
            }
        }

        Ok((self, session))
    }
}

/// Start the SSH server
pub async fn start_ssh_server(config: SshServerConfig, state: Arc<AgentState>) -> Result<()> {
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
