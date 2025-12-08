// CLI module for ArxOS
use clap::{Parser, Subcommand};

pub mod args;
pub mod commands;

use commands::{
    Command, ImportCommand, ExportCommand, InitCommand,
    git::{StatusCommand, CommitCommand, StageCommand, DiffCommand},
};
#[cfg(feature = "agent")]
use commands::RemoteCommand;

#[derive(Parser)]
#[command(name = "arx")]
#[command(about = "ArxOS - Git for Buildings")]
#[command(version = env!("CARGO_PKG_VERSION"))]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

impl Cli {
    pub fn execute(self) -> Result<(), Box<dyn std::error::Error>> {
        match self.command {
            Commands::Init { .. } => {
                let cmd = InitCommand {
                    directory: std::path::PathBuf::from("."),
                    name: None,
                    install_hooks: true,
                    init_git: true,
                };
                Ok(cmd.execute()?)
            },
            Commands::Import { ifc_file, repo, dry_run } => {
                let cmd = ImportCommand { ifc_file, repo, dry_run };
                Ok(cmd.execute()?)
            },
            Commands::Export { format, output, repo, delta } => {
                let cmd = ExportCommand { format, output, repo, delta };
                Ok(cmd.execute()?)
            },
            Commands::Render { building, interactive, brightness_style, .. } => {
                #[allow(unused_variables)]
                let brightness_style = brightness_style; // Used only when render3d feature is enabled
                if interactive {
                    #[cfg(feature = "render3d")]
                    {
                        // Validate and convert brightness style
                        let brightness_ramp = match brightness_style.as_str() {
                            "acerola" => crate::render3d::point_cloud::brightness_ramps::ACEROLA_16,
                            "classic" => crate::render3d::point_cloud::brightness_ramps::CLASSIC,
                            "extended" => crate::render3d::point_cloud::brightness_ramps::EXTENDED_16,
                            "unicode" => crate::render3d::point_cloud::brightness_ramps::UNICODE_16,
                            _ => {
                                eprintln!("❌ Invalid brightness style: '{}'", brightness_style);
                                eprintln!("   Valid options: acerola, classic, extended, unicode");
                                return Err(format!("Invalid brightness style: {}", brightness_style).into());
                            }
                        };
                        
                        crate::render3d::start_interactive_renderer(&building, brightness_ramp)?;
                    }
                    #[cfg(not(feature = "render3d"))]
                    {
                        println!("❌ Interactive 3D rendering requires --features render3d");
                        return Err("Render3D feature not enabled".into());
                    }
                } else {
                    #[cfg(feature = "tui")]
                    {
                        crate::tui::render_building(&building)?;
                    }
                    #[cfg(not(feature = "tui"))]
                    {
                        println!("📐 TUI rendering requires --features tui");
                    }
                }
                Ok(())
            },
            Commands::Merge(cmd) => {
                #[cfg(feature = "tui")]
                {
                    Ok(cmd.execute()?)
                }
                #[cfg(not(feature = "tui"))]
                {
                    println!("❌ Merge tool requires --features tui");
                    Err("TUI feature not enabled".into())
                }
            },
            Commands::Status { verbose, interactive } => {
                let cmd = StatusCommand { verbose, interactive };
                cmd.execute()
            },
            Commands::Stage { all, file } => {
                let cmd = StageCommand { all, file };
                cmd.execute()
            },
            Commands::Unstage { all, file } => {
                // Reusing StageCommand logic for unstage is not ideal but keeping it simple for now
                // Ideally UnstageCommand should be separate
                Self::handle_unstage(all, file)
            },
            Commands::Commit { message } => {
                let cmd = CommitCommand { message };
                cmd.execute()
            },
            Commands::Diff { commit, file, stat, interactive } => {
                let cmd = DiffCommand { commit, file, stat, interactive };
                cmd.execute()
            },
            Commands::History { limit, verbose, file } => {
                Self::handle_history(limit, verbose, file)
            },
            Commands::Search { query, equipment, rooms, buildings, case_sensitive, regex, limit, verbose, interactive } => {
                Self::handle_search(query, equipment, rooms, buildings, case_sensitive, regex, limit, verbose, interactive)
            },
            Commands::Query { pattern, format, verbose } => {
                Self::handle_query(pattern, format, verbose)
            },
            #[cfg(feature = "agent")]
            Commands::Remote(cmd) => {
                Ok(cmd.execute()?)
            },
            Commands::Dashboard => {
                #[cfg(all(feature = "tui", feature = "agent"))]
                {
                    use crate::agent::auth::TokenState;
                    
                    let rt = tokio::runtime::Runtime::new()?;
                    rt.block_on(async {
                        // Import trait for connect()
                        use crate::hardware::HardwareInterface;

                        // Create and connect simulated interface
                        let mut sim = crate::hardware::simulated::SimulatedInterface::new();
                        // Connect explicitly (safe because we own it here)
                        sim.connect().await.ok(); 
                         
                        let mut hardware = crate::hardware::HardwareManager::new();
                        hardware.add_interface("sim".to_string(), crate::hardware::HardwareProtocol::Simulated(sim));
                         
                        let state = std::sync::Arc::new(crate::agent::dispatcher::AgentState {
                            repo_root: std::path::PathBuf::from("."),
                            token: std::sync::Arc::new(std::sync::Mutex::new(TokenState::new("dummy".to_string(), vec![]))),
                            hardware: std::sync::Arc::new(hardware),
                        });
                        
                        crate::tui::dashboard::run_dashboard(state).await
                    })?;
                    Ok(())
                }
                #[cfg(all(feature = "tui", not(feature = "agent")))]
                {
                    println!("⚠️  Dashboard requires both --features tui and --features agent");
                    Err("Agent feature not enabled".into())
                }
                #[cfg(not(feature = "tui"))]
                {
                    println!("❌ TUI feature is required for dashboard");
                    Err("TUI feature not enabled".into())
                }
            },
            _ => {
                println!("⚠️  Command not yet implemented in restructured CLI");
                Ok(())
            },
        }
    }

    fn handle_unstage(all: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
        use crate::git::manager::{BuildingGitManager, GitConfigManager};

        let config = GitConfigManager::load_from_arx_config_or_env();
        let mut manager = BuildingGitManager::new(".", "current", config)?;

        if all || file.is_none() {
            let count = manager.unstage_all()?;
            println!("✅ Unstaged {} file(s)", count);
        } else if let Some(path) = file {
            manager.unstage_file(&path)?;
            println!("✅ Unstaged: {}", path);
        }

        Ok(())
    }

    fn handle_history(
        limit: usize,
        verbose: bool,
        file: Option<String>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        use crate::git::manager::{BuildingGitManager, GitConfigManager};

        let config = GitConfigManager::load_from_arx_config_or_env();
        let manager = BuildingGitManager::new(".", "current", config)?;

        let mut commits = if let Some(file_path) = file {
            // Get history for specific file (no limit parameter)
            manager.get_file_history(&file_path)?
        } else {
            // Get general commit history with limit
            manager.list_commits(limit)?
        };

        // Apply limit to file history results if needed
        if commits.len() > limit {
            commits.truncate(limit);
        }

        if commits.is_empty() {
            println!("📋 No commits found");
            return Ok(());
        }

        println!("📋 Commit History ({} commits)", commits.len());
        println!();

        for commit in commits {
            let short_id = if commit.id.len() >= 8 {
                &commit.id[..8]
            } else {
                &commit.id
            };

            if verbose {
                println!("Commit: {}", short_id);
                println!("Author: {}", commit.author);
                println!("Date:   {}", commit.time);
                println!();
                println!("    {}", commit.message);
                println!();
            } else {
                println!("{} - {} ({})", short_id, commit.message, commit.author);
            }
        }

        Ok(())
    }

    fn handle_search(
        query: String,
        equipment: bool,
        rooms: bool,
        buildings: bool,
        case_sensitive: bool,
        regex: bool,
        limit: usize,
        verbose: bool,
        interactive: bool,
    ) -> Result<(), Box<dyn std::error::Error>> {
        use crate::core::operations::{equipment as eq_ops, room as room_ops};
        use crate::persistence::load_building_data_from_dir;

        if interactive {
            println!("⚠️  Interactive search browser not yet implemented");
            println!("💡 Use without --interactive for text-based search");
            return Ok(());
        }

        // If no specific search type specified, search everything
        let search_all = !equipment && !rooms && !buildings;
        let search_equipment = equipment || search_all;
        let search_rooms = rooms || search_all;
        let search_buildings = buildings || search_all;

        println!("🔍 Searching for: \"{}\"", query);
        if regex {
            println!("   Mode: Regex pattern");
        } else if case_sensitive {
            println!("   Mode: Case-sensitive");
        } else {
            println!("   Mode: Case-insensitive");
        }
        println!();

        let mut total_results = 0;

        // Search equipment
        if search_equipment {
            let equipment_list = eq_ops::list_equipment(None)?;
            let mut matches = Vec::new();

            for item in equipment_list {
                let matches_name = if regex {
                    let re = regex::Regex::new(&query)?;
                    re.is_match(&item.name)
                } else if case_sensitive {
                    item.name.contains(&query)
                } else {
                    item.name.to_lowercase().contains(&query.to_lowercase())
                };

                if matches_name {
                    matches.push(item);
                }
            }

            if !matches.is_empty() {
                println!("📦 Equipment ({} found):", matches.len());
                for (i, item) in matches.iter().take(limit).enumerate() {
                    if verbose {
                        println!("  {}. {} (ID: {})", i + 1, item.name, item.id);
                        println!("     Type: {:?}", item.equipment_type);
                        if !item.properties.is_empty() {
                            println!("     Properties: {} entries", item.properties.len());
                        }
                        println!();
                    } else {
                        println!("  - {}", item.name);
                    }
                }
                if matches.len() > limit {
                    println!("  ... and {} more (use --limit to see more)", matches.len() - limit);
                }
                println!();
                total_results += matches.len();
            }
        }

        // Search rooms
        if search_rooms {
            let room_list = room_ops::list_rooms(None)?;
            let mut matches = Vec::new();

            for room in room_list {
                let matches_name = if regex {
                    let re = regex::Regex::new(&query)?;
                    re.is_match(&room.name)
                } else if case_sensitive {
                    room.name.contains(&query)
                } else {
                    room.name.to_lowercase().contains(&query.to_lowercase())
                };

                if matches_name {
                    matches.push(room);
                }
            }

            if !matches.is_empty() {
                println!("🚪 Rooms ({} found):", matches.len());
                for (i, room) in matches.iter().take(limit).enumerate() {
                    if verbose {
                        println!("  {}. {} (ID: {})", i + 1, room.name, room.id);
                        println!("     Type: {}", room.room_type);
                        println!("     Equipment: {} items", room.equipment.len());
                        println!();
                    } else {
                        println!("  - {}", room.name);
                    }
                }
                if matches.len() > limit {
                    println!("  ... and {} more (use --limit to see more)", matches.len() - limit);
                }
                println!();
                total_results += matches.len();
            }
        }

        // Search buildings
        if search_buildings {
            let building_data = load_building_data_from_dir()?;
            let building_name = &building_data.building.name;

            let matches_name = if regex {
                let re = regex::Regex::new(&query)?;
                re.is_match(building_name)
            } else if case_sensitive {
                building_name.contains(&query)
            } else {
                building_name.to_lowercase().contains(&query.to_lowercase())
            };

            if matches_name {
                println!("🏢 Building:");
                if verbose {
                    println!("  Name: {}", building_name);
                    println!("  Floors: {}", building_data.building.floors.len());
                    let total_rooms: usize = building_data.building.floors.iter()
                        .flat_map(|f| f.wings.iter())
                        .map(|w| w.rooms.len())
                        .sum();
                    println!("  Rooms: {}", total_rooms);
                    println!();
                } else {
                    println!("  - {}", building_name);
                    println!();
                }
                total_results += 1;
            }
        }

        if total_results == 0 {
            println!("❌ No results found");
        } else {
            println!("✅ Total: {} result(s)", total_results);
        }

        Ok(())
    }

    fn handle_query(
        pattern: String,
        format: String,
        verbose: bool,
    ) -> Result<(), Box<dyn std::error::Error>> {
        use crate::core::operations::equipment as eq_ops;

        println!("🔍 Query pattern: {}", pattern);
        println!();

        // Parse pattern into glob-compatible format
        // ArxAddress format: /country/state/city/building/floor/room/fixture
        let pattern_parts: Vec<&str> = pattern.trim_start_matches('/').split('/').collect();

        if pattern_parts.len() != 7 {
            return Err(format!(
                "Invalid ArxAddress pattern. Expected 7 parts, got {}.\nFormat: /country/state/city/building/floor/room/fixture",
                pattern_parts.len()
            ).into());
        }

        // Load equipment and filter by pattern
        let equipment_list = eq_ops::list_equipment(None)?;
        let mut matches = Vec::new();

        for item in equipment_list {
            // Try to construct ArxAddress for this equipment
            // For now, we'll do simple pattern matching on the ArxAddress path field if it exists
            // Note: Equipment might not have ArxAddress yet, so we'll need to construct it or skip

            // Simple glob-style matching on equipment name
            let matches_pattern = if pattern_parts[6] == "*" {
                true // Match all fixtures
            } else if pattern_parts[6].contains('*') {
                // Simple wildcard matching
                let pattern_prefix = pattern_parts[6].trim_end_matches('*');
                item.name.starts_with(pattern_prefix)
            } else {
                item.name == pattern_parts[6]
            };

            if matches_pattern {
                matches.push(item);
            }
        }

        if matches.is_empty() {
            println!("❌ No equipment found matching pattern");
            return Ok(());
        }

        // Format output
        match format.as_str() {
            "json" => {
                let json = serde_json::to_string_pretty(&matches)?;
                println!("{}", json);
            }
            "yaml" => {
                let yaml = serde_yaml::to_string(&matches)?;
                println!("{}", yaml);
            }
            "table" | _ => {
                println!("📦 Equipment ({} found):", matches.len());
                println!();
                println!("  {:<30} {:<15} {:<20}", "Name", "Type", "ID");
                println!("  {}", "-".repeat(70));

                for item in &matches {
                    let eq_type = format!("{:?}", item.equipment_type);
                    let name = if item.name.len() > 28 {
                        format!("{}...", &item.name[..28])
                    } else {
                        item.name.clone()
                    };
                    let id = if item.id.len() > 18 {
                        format!("{}...", &item.id[..18])
                    } else {
                        item.id.clone()
                    };
                    println!("  {:<30} {:<15} {:<20}", name, eq_type, id);

                    if verbose {
                        if !item.properties.is_empty() {
                            println!("     Properties:");
                            for (key, value) in item.properties.iter().take(3) {
                                println!("       {}: {}", key, value);
                            }
                            if item.properties.len() > 3 {
                                println!("       ... and {} more", item.properties.len() - 3);
                            }
                        }
                        println!();
                    }
                }

                println!();
                println!("✅ Total: {} result(s)", matches.len());
            }
        }

        Ok(())
    }
}

#[derive(Subcommand)]
pub enum Commands {
    /// Initialize a new building from scratch
    Init {
        /// Building name (required)
        #[arg(long)]
        name: String,
        /// Building description
        #[arg(long)]
        description: Option<String>,
        /// Location/address
        #[arg(long)]
        location: Option<String>,
        /// Initialize Git repository
        #[arg(long = "git-init")]
        git_init: bool,
        /// Commit initial building.yaml
        #[arg(long)]
        commit: bool,
        /// Coordinate system (default: World)
        #[arg(long, default_value = "World")]
        coordinate_system: String,
        /// Units (default: meters)
        #[arg(long, default_value = "meters")]
        units: String,
    },
    /// Import IFC file to Git repository
    Import {
        /// Path to IFC file
        ifc_file: String,
        /// Git repository URL
        #[arg(long)]
        repo: Option<String>,
        /// Dry run - show what would be done without making changes
        #[arg(long)]
        dry_run: bool,
    },
    /// Export building data to Git repository or other formats
    Export {
        /// Export format (git, ifc, gltf, usdz)
        #[arg(long, default_value = "git")]
        format: String,
        /// Output file path (required for non-git formats)
        #[arg(long)]
        output: Option<String>,
        /// Git repository URL (required for git format)
        #[arg(long)]
        repo: Option<String>,
        /// Export only changes (delta mode)
        #[arg(long)]
        delta: bool,
    },
    /// Sync building data to IFC file (continuous or one-time)
    Sync {
        /// Path to IFC file
        #[arg(long)]
        ifc: Option<String>,
        /// Enable watch mode (daemon) for continuous sync
        #[arg(long)]
        watch: bool,
        /// Export only changes (delta mode)
        #[arg(long)]
        delta: bool,
    },
    /// Render building visualization
    Render {
        /// Building identifier
        #[arg(long)]
        building: String,
        /// Floor number
        #[arg(long)]
        floor: Option<i32>,
        /// Enable 3D multi-floor visualization
        #[arg(long)]
        three_d: bool,
        /// Show equipment status indicators
        #[arg(long)]
        show_status: bool,
        /// Show room boundaries
        #[arg(long)]
        show_rooms: bool,
        /// Output format (ascii, advanced, json, yaml)
        #[arg(long, default_value = "ascii")]
        format: String,
        /// Projection type for 3D rendering (isometric, orthographic, perspective)
        #[arg(long, default_value = "isometric")]
        projection: String,
        /// View angle for 3D rendering (topdown, front, side, isometric)
        #[arg(long, default_value = "isometric")]
        view_angle: String,
        /// Scale factor for 3D rendering
        #[arg(long, default_value = "1.0")]
        scale: f64,
        /// Enable spatial index integration for enhanced queries
        #[arg(long)]
        spatial_index: bool,
        /// Enable interactive WebGL-style point cloud renderer with WASD+mouse controls
        #[arg(long)]
        interactive: bool,
        /// ASCII brightness style for point cloud rendering (acerola, classic, extended, unicode)
        ///
        /// Controls the character set used for depth visualization:
        /// - acerola: 16-level Acerola-style ramp (default, best for LiDAR scans)
        /// - classic: 9-level original ramp (legacy compatibility)
        /// - extended: 16-level extended ASCII characters
        /// - unicode: 16-level Unicode block characters
        #[arg(long, default_value = "acerola")]
        brightness_style: String,
    },
    /// Interactive 3D building visualization with real-time controls
    Interactive {
        /// Building identifier
        #[arg(long)]
        building: String,
        /// Projection type (isometric, orthographic, perspective)
        #[arg(long, default_value = "isometric")]
        projection: String,
        /// View angle (topdown, front, side, isometric)
        #[arg(long, default_value = "isometric")]
        view_angle: String,
        /// Scale factor for rendering
        #[arg(long, default_value = "1.0")]
        scale: f64,
        /// Canvas width in characters
        #[arg(long, default_value = "120")]
        width: usize,
        /// Canvas height in characters
        #[arg(long, default_value = "40")]
        height: usize,
        /// Enable spatial index integration
        #[arg(long)]
        spatial_index: bool,
        /// Show equipment status indicators
        #[arg(long)]
        show_status: bool,
        /// Show room boundaries
        #[arg(long)]
        show_rooms: bool,
        /// Show equipment connections
        #[arg(long)]
        show_connections: bool,
        /// Target FPS for rendering (1-240)
        #[arg(long, default_value = "30", value_parser = |s: &str| -> Result<u32, String> {
            let val: u32 = s.parse().map_err(|_| format!("must be a number between 1 and 240"))?;
            if val < 1 || val > 240 {
                Err(format!("FPS must be between 1 and 240, got {}", val))
            } else {
                Ok(val)
            }
        })]
        fps: u32,
        /// Show FPS counter
        #[arg(long)]
        show_fps: bool,
        /// Show help overlay by default
        #[arg(long)]
        show_help: bool,
        /// ASCII brightness style for point cloud rendering (acerola, classic, extended, unicode)
        ///
        /// Controls the character set used for depth visualization:
        /// - acerola: 16-level Acerola-style ramp (default, best for LiDAR scans)
        /// - classic: 9-level original ramp (legacy compatibility)
        /// - extended: 16-level extended ASCII characters
        /// - unicode: 16-level Unicode block characters
        #[arg(long, default_value = "acerola")]
        brightness_style: String,
    },
    /// Validate building data
    Validate {
        /// Path to building data
        #[arg(long)]
        path: Option<String>,
    },
    /// Show repository status and changes
    Status {
        /// Show detailed status information
        #[arg(long)]
        verbose: bool,
        /// Open interactive dashboard
        #[arg(long)]
        interactive: bool,
    },
    /// Stage changes in the working directory
    Stage {
        /// Stage all modified files (default behavior)
        #[arg(long)]
        all: bool,
        /// Specific file to stage
        file: Option<String>,
    },
    /// Commit staged changes
    Commit {
        /// Commit message
        message: String,
    },
    /// Unstage changes
    Unstage {
        /// Unstage all files
        #[arg(long)]
        all: bool,
        /// Specific file to unstage
        file: Option<String>,
    },
    /// Show differences between commits
    Diff {
        /// Compare with specific commit hash
        #[arg(long)]
        commit: Option<String>,
        /// Show diff for specific file
        #[arg(long)]
        file: Option<String>,
        /// Show file statistics only
        #[arg(long)]
        stat: bool,
        /// Open interactive viewer
        #[arg(long)]
        interactive: bool,
    },
    /// Show commit history
    History {
        /// Number of commits to show (1-1000)
        #[arg(long, default_value = "10", value_parser = |s: &str| -> Result<usize, String> {
            let val: usize = s.parse().map_err(|_| format!("must be a number between 1 and 1000"))?;
            if val < 1 || val > 1000 {
                Err(format!("Limit must be between 1 and 1000, got {}", val))
            } else {
                Ok(val)
            }
        })]
        limit: usize,
        /// Show detailed commit information
        #[arg(long)]
        verbose: bool,
        /// Show history for specific file
        #[arg(long)]
        file: Option<String>,
    },
    /// Manage configuration
    Config {
        /// Show current configuration
        #[arg(long)]
        show: bool,
        /// Set configuration value (format: section.key=value)
        #[arg(long)]
        set: Option<String>,
        /// Reset to defaults
        #[arg(long)]
        reset: bool,
        /// Edit configuration file
        #[arg(long)]
        edit: bool,
        /// Open interactive wizard
        #[arg(long)]
        interactive: bool,
    },
    /// Room management commands
    Room {
        #[command(subcommand)]
        command: RoomCommands,
    },
    /// Equipment management commands
    Equipment {
        #[command(subcommand)]
        command: EquipmentCommands,
    },
    /// Spatial operations and queries
    Spatial {
        #[command(subcommand)]
        command: SpatialCommands,
    },
    /// Live monitoring dashboard
    Watch {
        #[arg(long)]
        building: Option<String>,
        #[arg(long)]
        floor: Option<i32>,
        #[arg(long)]
        room: Option<String>,
        /// Refresh interval in seconds (1-3600)
        #[arg(long, default_value = "5", value_parser = |s: &str| -> Result<u64, String> {
            let val: u64 = s.parse().map_err(|_| format!("must be a number between 1 and 3600"))?;
            if val < 1 || val > 3600 {
                Err(format!("Refresh interval must be between 1 and 3600 seconds, got {}", val))
            } else {
                Ok(val)
            }
        })]
        refresh_interval: u64,
        #[arg(long)]
        sensors_only: bool,
        #[arg(long)]
        alerts_only: bool,
        #[arg(long)]
        log_level: Option<String>,
    },
    /// Search building data
    Search {
        /// Search query
        query: String,
        /// Search in equipment names
        #[arg(long)]
        equipment: bool,
        /// Search in room names
        #[arg(long)]
        rooms: bool,
        /// Search in building names
        #[arg(long)]
        buildings: bool,
        /// Case-sensitive search
        #[arg(long)]
        case_sensitive: bool,
        /// Use regex pattern matching
        #[arg(long)]
        regex: bool,
        /// Maximum number of results (1-10000)
        #[arg(long, default_value = "50", value_parser = |s: &str| -> Result<usize, String> {
            let val: usize = s.parse().map_err(|_| format!("must be a number between 1 and 10000"))?;
            if val < 1 || val > 10000 {
                Err(format!("Limit must be between 1 and 10000, got {}", val))
            } else {
                Ok(val)
            }
        })]
        limit: usize,
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
        /// Open interactive browser
        #[arg(long)]
        interactive: bool,

    },
    /// Manage remote building connections via SSH
    #[cfg(feature = "agent")]
    Remote(RemoteCommand),
    /// Query equipment by ArxAddress glob pattern
    ///
    /// Query equipment matching an ArxAddress path pattern using glob wildcards (*).
    /// Supports hierarchical path queries: /country/state/city/building/floor/room/fixture
    ///
    /// # Examples
    ///
    /// ```bash
    /// # Find all boilers in mech rooms on any floor
    /// arx query "/usa/ny/*/floor-*/mech/boiler-*"
    ///
    /// # Find all equipment in kitchen on floor 02
    /// arx query "/usa/ny/brooklyn/ps-118/floor-02/kitchen/*"
    ///
    /// # Find all HVAC equipment in any city
    /// arx query "/usa/ny/*/ps-118/floor-*/hvac/*"
    /// ```
    Query {
        /// ArxAddress glob pattern with wildcards (e.g., "/usa/ny/*/floor-*/mech/boiler-*")
        pattern: String,
        /// Output format (table, json, yaml)
        #[arg(long, default_value = "table")]
        format: String,
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
    },
    /// Integrate AR scan data
    ///
    /// **Note:** This command directly integrates AR scans without user review.
    /// For mobile apps, consider using `ar pending` workflow instead.
    ArIntegrate {
        /// AR scan data file (JSON)
        #[arg(long)]
        scan_file: String,
        /// Room name for the scan
        #[arg(long)]
        room: String,
        /// Floor level
        #[arg(long)]
        floor: i32,
        /// Building identifier
        #[arg(long)]
        building: String,
        /// Commit changes to Git
        #[arg(long)]
        commit: bool,
        /// Commit message
        #[arg(long)]
        message: Option<String>,
    },
    /// AR integration commands
    Ar {
        #[command(subcommand)]
        subcommand: ArCommands,
    },
    /// Process sensor data and update equipment status
    ProcessSensors {
        /// Directory containing sensor data files
        #[arg(long, default_value = "./sensor-data")]
        sensor_dir: String,

        /// Building name to update
        #[arg(long)]
        building: String,

        /// Commit changes to Git
        #[arg(long)]
        commit: bool,

        /// Watch mode: continuously monitor for new sensor data
        #[arg(long)]
        watch: bool,
    },
    /// Start HTTP server for real-time sensor data ingestion
    SensorsHttp {
        /// Building name to update
        #[arg(long)]
        building: String,

        /// Host address to bind to
        #[arg(long, default_value = "127.0.0.1")]
        host: String,

        /// Port to listen on (1-65535)
        #[arg(long, default_value = "3000", value_parser = |s: &str| -> Result<u16, String> {
            let val: u16 = s.parse().map_err(|_| format!("must be a number between 1 and 65535"))?;
            if val == 0 {
                Err(format!("Port must be between 1 and 65535, got 0"))
            } else {
                Ok(val)
            }
        })]
        port: u16,
    },
    /// Start MQTT subscriber for real-time sensor data ingestion
    SensorsMqtt {
        /// Building name to update
        #[arg(long)]
        building: String,

        /// MQTT broker URL
        #[arg(long, default_value = "localhost")]
        broker: String,

        /// MQTT broker port
        #[arg(long, default_value = "1883")]
        port: u16,

        /// MQTT username (optional)
        #[arg(long)]
        username: Option<String>,

        /// MQTT password (optional)
        #[arg(long)]
        password: Option<String>,

        /// MQTT topics to subscribe to (comma-separated)
        #[arg(long, default_value = "arxos/sensors/#")]
        topics: String,
    },
    /// IFC file processing commands
    #[command(name = "ifc")]
    Ifc {
        #[command(subcommand)]
        subcommand: IfcCommands,
    },
    /// Run system health diagnostics
    Health {
        /// Check specific component (all, git, config, persistence, yaml)
        #[arg(long)]
        component: Option<String>,
        /// Show detailed diagnostics
        #[arg(long)]
        verbose: bool,
        /// Open interactive dashboard
        #[arg(long)]
        interactive: bool,
        /// Generate comprehensive diagnostic report
        #[arg(long)]
        diagnostic: bool,
    },
    /// Generate HTML documentation for a building
    Doc {
        /// Building name to document
        #[arg(long)]
        building: String,
        /// Output file path (default: ./docs/{building}.html)
        #[arg(long)]
        output: Option<String>,
    },
    /// Gamified PR review and planning commands
    Game {
        #[command(subcommand)]
        subcommand: GameCommands,
    },
    /// Filter building data
    Filter {
        /// Equipment type filter
        #[arg(long)]
        equipment_type: Option<String>,
        /// Equipment status filter
        #[arg(long)]
        status: Option<String>,
        /// Floor filter
        #[arg(long)]
        floor: Option<i32>,
        /// Room filter
        #[arg(long)]
        room: Option<String>,
        /// Building filter
        #[arg(long)]
        building: Option<String>,
        /// Show only critical equipment
        #[arg(long)]
        critical_only: bool,
        /// Show only healthy equipment
        #[arg(long)]
        healthy_only: bool,
        /// Show only equipment with alerts
        #[arg(long)]
        alerts_only: bool,
        /// Output format (table, json, yaml)
        #[arg(long, default_value = "table")]
        format: String,
        /// Maximum number of results
        #[arg(long, default_value = "100")]
        limit: usize,
        /// Show detailed results
        #[arg(long)]
        verbose: bool,
    },
    /// Spreadsheet interface for editing building data
    Spreadsheet {
        #[command(subcommand)]
        subcommand: SpreadsheetCommands,
    },
    /// User management commands (admin permissions required for verify/revoke)
    ///
    /// The first user added to the registry automatically becomes an admin with
    /// 'verify_users' and 'revoke_users' permissions. Only admins can verify or
    /// revoke other users.
    Users {
        #[command(subcommand)]
        subcommand: UsersCommands,
    },
    /// Verify GPG signatures on Git commits
    ///
    /// Checks commit signatures and displays verification status.
    /// Requires GPG to be configured and public keys to be available.
    Verify {
        /// Commit hash to verify (default: HEAD)
        #[arg(long)]
        commit: Option<String>,
        /// Verify all commits in current branch
        #[arg(long)]
        all: bool,
        /// Show detailed verification information
        #[arg(long)]
        verbose: bool,
    },
    /// Migrate existing fixtures to ArxAddress format
    ///
    /// One-shot migration that fills address: for every existing fixture
    /// in building YAML files by inferring from grid/floor/room data.
    /// Old data becomes instantly searchable with the new address system.
    Migrate {
        /// Show what would be migrated without making changes
        #[arg(long)]
        dry_run: bool,
    },
    /// Economy and token operations
    Economy {
        #[command(subcommand)]
        command: EconomyCommands,
    },
    /// Resolve merge conflicts interactively
    Merge(commands::MergeCommand),
    /// Launch TUI Dashboard
    Dashboard,
}


// Sub-command definitions
pub mod subcommands;
pub use subcommands::*;
