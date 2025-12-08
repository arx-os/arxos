//! Remote building management commands - requires agent feature
#![cfg(feature = "agent")]

use clap::{Args, Subcommand};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::fs;
use anyhow::{Context, Result};
use std::sync::Arc;
use russh::client;
use russh_keys::key;
use async_trait::async_trait;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct BuildingHost {
    pub host: String,
    pub port: u16,
    pub user: String,
    pub identity_file: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize, Default)]
pub struct BuildingsConfig {
    pub buildings: HashMap<String, BuildingHost>,
}

#[derive(Args)]
pub struct RemoteCommand {
    #[command(subcommand)]
    pub action: RemoteAction,
}

#[derive(Subcommand)]
pub enum RemoteAction {
    /// Add a new building host configuration
    Add {
        /// Name of the building (alias)
        name: String,
        /// Hostname or IP address
        host: String,
        /// SSH port
        #[arg(long, default_value = "2222")]
        port: u16,
        /// Username
        #[arg(long, default_value = "admin")]
        user: String,
        /// Path to identity file (private key)
        #[arg(long)]
        identity: Option<String>,
    },
    /// List configured buildings
    List,
    /// Execute a command on a remote building
    Exec {
        /// Building name
        building: String,
        /// Command to execute
        #[arg(trailing_var_arg = true)]
        command: Vec<String>,
    },
    /// Connect to a remote building (interactive shell)
    Connect {
        /// Building name
        building: String,
    },
}

impl RemoteCommand {
    pub fn execute(self) -> Result<()> {
        match self.action {
            RemoteAction::Add { name, host, port, user, identity } => {
                Self::add_building(name, host, port, user, identity)
            }
            RemoteAction::List => Self::list_buildings(),
            RemoteAction::Exec { building, command } => {
                let cmd_str = command.join(" ");
                Self::run_client(building, Some(cmd_str))
            }
            RemoteAction::Connect { building } => {
                Self::run_client(building, None)
            }
        }
    }

    fn load_config() -> Result<BuildingsConfig> {
        let home = dirs::home_dir().context("Could not find home directory")?;
        let config_path = home.join(".arxos").join("buildings.yaml");
        
        if config_path.exists() {
            let content = fs::read_to_string(&config_path)?;
            let config: BuildingsConfig = serde_yaml::from_str(&content)?;
            Ok(config)
        } else {
            Ok(BuildingsConfig::default())
        }
    }

    fn save_config(config: &BuildingsConfig) -> Result<()> {
        let home = dirs::home_dir().context("Could not find home directory")?;
        let arx_dir = home.join(".arxos");
        if !arx_dir.exists() {
            fs::create_dir_all(&arx_dir)?;
        }
        let config_path = arx_dir.join("buildings.yaml");
        let content = serde_yaml::to_string(config)?;
        fs::write(config_path, content)?;
        Ok(())
    }

    fn add_building(name: String, host: String, port: u16, user: String, identity: Option<String>) -> Result<()> {
        let mut config = Self::load_config()?;
        config.buildings.insert(name.clone(), BuildingHost {
            host,
            port,
            user,
            identity_file: identity,
        });
        Self::save_config(&config)?;
        println!("✅ Added building '{}'", name);
        Ok(())
    }

    fn list_buildings() -> Result<()> {
        let config = Self::load_config()?;
        if config.buildings.is_empty() {
            println!("No buildings configured.");
            return Ok(());
        }
        println!("Configured Buildings:");
        println!("{:<20} {:<30} {:<10} {:<15}", "Name", "Host", "Port", "User");
        println!("{}", "-".repeat(75));
        for (name, host) in config.buildings {
            println!("{:<20} {:<30} {:<10} {:<15}", name, host.host, host.port, host.user);
        }
        Ok(())
    }

    fn run_client(building_name: String, command: Option<String>) -> Result<()> {
        let config = Self::load_config()?;
        let building = config.buildings.get(&building_name)
            .context(format!("Building '{}' not found in config", building_name))?;

        let host_addr = format!("{}:{}", building.host, building.port);
        let user = building.user.clone();
        
        // Find identity key
        let key_path = if let Some(path) = &building.identity_file {
            PathBuf::from(path)
        } else {
            let home = dirs::home_dir().unwrap();
            home.join(".ssh").join("id_ed25519")
        };

        if !key_path.exists() {
             return Err(anyhow::anyhow!("SSH key not found at {:?}", key_path));
        }

        println!("Connecting to {} ({}) as {}...", building_name, host_addr, user);

        // Run async client in blocking runtime
        let runtime = tokio::runtime::Runtime::new()?;
        runtime.block_on(async {
           connect_and_run(host_addr, user, key_path, command).await
        })
    }
}

struct ClientHandler;

#[async_trait]
impl client::Handler for ClientHandler {
    type Error = russh::Error;
    // We don't check server keys in this simple client yet
    async fn check_server_key(
        self,
        _server_public_key: &key::PublicKey,
    ) -> Result<(Self, bool), Self::Error> {
        Ok((self, true))
    }
}

async fn connect_and_run(addr: String, user: String, key_path: PathBuf, command: Option<String>) -> Result<()> {
    let config = Arc::new(russh::client::Config::default());
    let sh = ClientHandler;
    let mut session = russh::client::connect(config, addr, sh).await?;
    
    // Load key
    let key_pair = russh_keys::load_secret_key(key_path, None)?;
    let auth_res = session.authenticate_publickey(user, Arc::new(key_pair)).await?;
    
    if !auth_res {
        return Err(anyhow::anyhow!("Authentication failed"));
    }

    if let Some(cmd) = command {
        let mut channel = session.channel_open_session().await?;
        channel.exec(true, cmd).await?;
        
        // Stream output
        while let Some(msg) = channel.wait().await {
            match msg {
                russh::ChannelMsg::Data { ref data } => {
                    tokio::io::stdout().write_all(data).await?;
                }
                russh::ChannelMsg::ExitStatus { exit_status } => {
                    if exit_status != 0 {
                        // eprintln!("Exited with status {}", exit_status);
                    }
                    break;
                }
                _ => {}
            }
        }
    } else {
        // Interactive shell
        println!("Interactive shell session started (type 'exit' to quit)");
        let mut channel = session.channel_open_session().await?;
        
        // Request PTY
        // term, col_width, row_height, pix_width, pix_height, modes
        channel.request_pty(true, "xterm", 80, 24, 0, 0, &[]).await?;
        
        // Request Shell
        channel.request_shell(true).await?;
        
        // Enter raw mode if possible logic
        #[cfg(feature = "tui")]
        {
            use crossterm::terminal::{enable_raw_mode, disable_raw_mode};
            enable_raw_mode()?;
            
            // We need to restore raw mode on any exit.
            // For this simple implementation, we'll try to ensure we call disable at end.
            // Using a scope guard or similar would be better in production.
        }

        let mut stdin = tokio::io::stdin();
        let mut stdout = tokio::io::stdout();
        let mut buf = [0u8; 1024];

        // Loop until channel closes or user quits
        loop {
             tokio::select! {
                 // Read from remote
                 msg = channel.wait() => {
                     match msg {
                         Some(russh::ChannelMsg::Data { data }) => {
                             stdout.write_all(&data).await?;
                             stdout.flush().await?;
                         }
                         Some(russh::ChannelMsg::ExitStatus { .. }) => {
                             break;
                         }
                         Some(russh::ChannelMsg::Close) => {
                             break;
                         }
                         None => break,
                         _ => {}
                     }
                 }
                 // Read from stdin
                 n = stdin.read(&mut buf) => {
                     match n {
                         Ok(0) => break, // EOF
                         Ok(n) => {
                             // Send to remote
                             channel.data(&buf[0..n]).await?;
                         }
                         Err(_) => break,
                     }
                 }
             }
        }
        
        #[cfg(feature = "tui")]
        {
            use crossterm::terminal::disable_raw_mode;
            let _ = disable_raw_mode();
        }
    }
    
    session.disconnect(russh::Disconnect::ByApplication, "Bye", "English").await?;
    Ok(())
}
