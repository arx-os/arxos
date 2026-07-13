// CLI module for ArxOS
use clap::{Parser, Subcommand};

pub mod args;
pub mod commands;

#[cfg(feature = "agent")]
use commands::RemoteCommand;
use commands::{
    access::AccessAction,
    data::{EquipmentCommand, RoomCommand, SpatialCommand},
    git::{CommitCommand, DiffCommand, StageCommand, StatusCommand, UnstageCommand},
    AccessCommand, Command, ContributeCommand, ExportCommand, ImportCommand, InitCommand,
    MigrateCommand,
};

#[derive(Parser)]
#[command(name = "arx")]
#[command(about = "ArxOS building compiler — Git for Buildings (compiler-core by default)")]
#[command(
    long_about = "Local-first building compiler: IFC/LiDAR/text → building.yaml → Git → IFC export.\n\n\
Default features include TUI (primary UI). Optional: --features agent | web | blockchain | full.\n\n\
L1 pilot path: init → import → edit/review → validate → git → export --format ifc"
)]
#[command(version = env!("CARGO_PKG_VERSION"))]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

impl Cli {
    pub fn execute(self) -> Result<(), Box<dyn std::error::Error>> {
        match self.command {
            Commands::Init {
                name,
                no_git,
                ..
            } => {
                // Git is on by default (L1 / product path). Opt out with --no-git.
                let cmd = InitCommand {
                    directory: std::path::PathBuf::from("."),
                    name: Some(name),
                    install_hooks: !no_git,
                    init_git: !no_git,
                };
                Ok(cmd.execute()?)
            }
            Commands::Import { subcommand } => match subcommand {
                ImportSubcommand::Ifc {
                    ifc_file,
                    repo,
                    dry_run,
                    strict,
                } => {
                    let cmd = ImportCommand {
                        ifc_file,
                        repo,
                        dry_run,
                        strict,
                    };
                    Ok(cmd.execute()?)
                }
                ImportSubcommand::Lidar {
                    file_path,
                    voxel_size,
                    light,
                    dry_run,
                    merge,
                    building,
                } => {
                    let cmd = commands::import_lidar::ImportLidarCommand {
                        file_path,
                        voxel_size,
                        light,
                        dry_run,
                        merge,
                        building,
                    };
                    Ok(cmd.execute()?)
                }
                ImportSubcommand::Text {
                    script,
                    building,
                    dry_run,
                } => {
                    let cmd = commands::edit::EditCommand {
                        script,
                        building,
                        dry_run,
                    };
                    Ok(cmd.execute()?)
                }
            },
            Commands::Edit {
                script,
                building,
                dry_run,
            } => {
                let cmd = commands::edit::EditCommand {
                    script,
                    building,
                    dry_run,
                };
                Ok(cmd.execute()?)
            }
            Commands::Export {
                format,
                output,
                repo,
                delta,
                approved_only,
                commercial,
                access_receipt,
            } => {
                let cmd = ExportCommand {
                    format,
                    output,
                    repo,
                    delta,
                    approved_only,
                    commercial,
                    access_receipt,
                };
                Ok(cmd.execute()?)
            }
            Commands::Contribute {
                output,
                latitude,
                longitude,
                git_commit,
                allow_invalid,
                dry_run,
                sign,
                private_key,
                oracle,
                chain_id,
                submit,
                worker,
                amount,
                rpc_url,
            } => {
                let cmd = ContributeCommand {
                    output: std::path::PathBuf::from(output),
                    latitude,
                    longitude,
                    git_commit,
                    allow_invalid,
                    dry_run,
                    sign,
                    private_key,
                    oracle,
                    chain_id,
                    submit,
                    worker,
                    amount,
                    rpc_url,
                };
                Ok(cmd.execute()?)
            }
            Commands::Access { subcommand } => {
                let action = match subcommand {
                    AccessSubcommand::Quote {
                        building_id,
                        amount,
                        output,
                    } => AccessAction::Quote {
                        building_id,
                        amount_axd: amount,
                        output: std::path::PathBuf::from(output),
                    },
                    AccessSubcommand::Grant {
                        building_id,
                        tx_hash,
                        output,
                    } => AccessAction::Grant {
                        building_id,
                        tx_hash,
                        output: std::path::PathBuf::from(output),
                    },
                    AccessSubcommand::Pay {
                        building_id,
                        amount,
                        nonce,
                        private_key,
                        router,
                        token,
                        rpc_url,
                        chain_id,
                        request,
                    } => AccessAction::Pay {
                        building_id,
                        amount_axd: amount,
                        nonce_hex: nonce,
                        private_key,
                        router,
                        token,
                        rpc_url,
                        chain_id,
                        request_file: request.map(std::path::PathBuf::from),
                    },
                };
                Ok(AccessCommand { action }.execute()?)
            }
            #[cfg(feature = "tui")]
            Commands::Render { building, .. } => {
                // Hierarchy tree only — LiDAR point-cloud / Bevy viz deferred.
                crate::tui::render_building(&building)?;
                Ok(())
            }
            #[cfg(feature = "tui")]
            Commands::Merge(cmd) => Ok(cmd.execute()?),
            Commands::Status {
                verbose,
                interactive,
            } => {
                let cmd = StatusCommand {
                    verbose,
                    interactive,
                };
                cmd.execute()
            }
            Commands::Stage { all, file } => {
                let cmd = StageCommand { all, file };
                cmd.execute()
            }
            Commands::Unstage { all, file } => {
                let cmd = UnstageCommand { all, file };
                cmd.execute()
            }
            Commands::Commit {
                message,
                message_flag,
            } => {
                let message = message_flag.or(message).ok_or_else(|| {
                    Box::<dyn std::error::Error>::from(
                        "commit message required: arx commit \"msg\" or arx commit -m \"msg\"",
                    )
                })?;
                let cmd = CommitCommand { message };
                cmd.execute()
            }
            Commands::Diff {
                commit,
                file,
                stat,
                interactive,
            } => {
                let cmd = DiffCommand {
                    commit,
                    file,
                    stat,
                    interactive,
                };
                cmd.execute()
            }
            Commands::History {
                limit,
                verbose,
                file,
            } => Self::handle_history(limit, verbose, file),
            Commands::Search {
                query,
                equipment,
                rooms,
                buildings,
                case_sensitive,
                regex,
                limit,
                verbose,
                interactive,
            } => Self::handle_search(
                query,
                equipment,
                rooms,
                buildings,
                case_sensitive,
                regex,
                limit,
                verbose,
                interactive,
            ),
            Commands::Query {
                pattern,
                format,
                verbose,
            } => commands::query::run_address_query(&pattern, &format, verbose),
            Commands::Migrate { dry_run } => {
                let cmd = MigrateCommand {
                    dry_run,
                    path: None,
                };
                Ok(cmd.execute()?)
            }
            Commands::Room { command } => {
                let cmd = RoomCommand {
                    subcommand: command,
                };
                cmd.execute()
            }
            Commands::Equipment { command } => {
                let cmd = EquipmentCommand {
                    subcommand: command,
                };
                cmd.execute()
            }
            Commands::Spatial { command } => {
                let cmd = SpatialCommand {
                    subcommand: command,
                };
                cmd.execute()
            }
            #[cfg(feature = "agent")]
            Commands::Remote(cmd) => Ok(cmd.execute()?),
            #[cfg(all(feature = "tui", feature = "agent"))]
            Commands::Dashboard => {
                use crate::agent::auth::TokenState;

                let rt = tokio::runtime::Runtime::new()?;
                rt.block_on(async {
                    let state = std::sync::Arc::new(crate::agent::dispatcher::AgentState {
                        repo_root: std::path::PathBuf::from("."),
                        token: std::sync::Arc::new(std::sync::Mutex::new(TokenState::new(
                            "dummy".to_string(),
                            vec![],
                        ))),
                    });

                    crate::tui::dashboard::run_dashboard(state).await
                })?;
                Ok(())
            }
            Commands::Validate { path } => {
                use crate::persistence::{load_building_at, BUILDING_YAML};
                use crate::validation::validate_building;

                let base = path
                    .as_deref()
                    .map(std::path::PathBuf::from)
                    .unwrap_or_else(|| std::path::PathBuf::from("."));
                let building = load_building_at(&base).map_err(|e| {
                    format!(
                        "Failed to load {} under {}: {}",
                        BUILDING_YAML,
                        base.display(),
                        e
                    )
                })?;
                let report = validate_building(&building);
                for line in report.summary_lines() {
                    println!("{}", line);
                }
                if report.has_errors() {
                    Err("Building validation failed".into())
                } else {
                    println!("✅ Validation completed successfully");
                    Ok(())
                }
            }
        }
    }

    pub(crate) fn handle_history(
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

    #[allow(clippy::too_many_arguments)]
    pub(crate) fn handle_search(
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
            #[cfg(feature = "tui")]
            {
                use crate::persistence::load_building_data_from_dir;
                use crate::tui::search::{SearchAction, SearchBrowser};
                use crate::tui::TerminalManager;
                use crossterm::event::{self, Event};
                use std::time::Duration;

                // Load building data
                let building_data = load_building_data_from_dir()?;

                // Initialize terminal (automatically enters alternate screen)
                let mut terminal_manager = TerminalManager::new()?;

                // Create search browser with initial query
                let mut browser = SearchBrowser::new(building_data);
                for c in query.chars() {
                    browser.handle_key(event::KeyEvent::from(crossterm::event::KeyCode::Char(c)));
                }

                // Main event loop
                let result = loop {
                    terminal_manager.terminal().draw(|frame| {
                        browser.render(frame, frame.size());
                    })?;

                    if event::poll(Duration::from_millis(100))? {
                        if let Event::Key(key) = event::read()? {
                            match browser.handle_key(key) {
                                SearchAction::Continue => {}
                                SearchAction::Select(result) => {
                                    break Ok(result);
                                }
                                SearchAction::Exit => {
                                    // TerminalManager cleanup handled by Drop
                                    return Ok(());
                                }
                            }
                        }
                    }
                };

                // TerminalManager cleanup handled by Drop trait

                // Display selected result
                match result {
                    Ok(result) => {
                        println!(
                            "Selected: {} {} - {}",
                            result.icon(),
                            result.title,
                            result.subtitle
                        );
                        println!("ID: {}", result.id);
                        return Ok(());
                    }
                    Err(e) => return Err(e),
                }
            }
            #[cfg(not(feature = "tui"))]
            {
                println!("⚠️  Interactive search browser requires --features tui");
                println!("💡 Use without --interactive for text-based search");
                return Ok(());
            }
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
                    println!(
                        "  ... and {} more (use --limit to see more)",
                        matches.len() - limit
                    );
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
                    println!(
                        "  ... and {} more (use --limit to see more)",
                        matches.len() - limit
                    );
                }
                println!();
                total_results += matches.len();
            }
        }

        // Search buildings
        if search_buildings {
            let building = load_building_data_from_dir()?;
            let building_name = &building.name;

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
                    println!("  Floors: {}", building.floors.len());
                    let total_rooms: usize = building
                        .floors
                        .iter()
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
        /// Legacy flag (Git init is now the default). Kept so old scripts do not fail.
        #[arg(long = "git-init", hide = true)]
        git_init: bool,
        /// Skip Git repository initialization
        #[arg(long = "no-git")]
        no_git: bool,
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
    /// Import data into building model
    Import {
        #[command(subcommand)]
        subcommand: ImportSubcommand,
    },
    /// Apply text / AR command script to a building YAML
    Edit {
        /// Script file path, or "-" for stdin
        script: String,
        /// Building YAML path or name
        #[arg(long)]
        building: Option<String>,
        /// Show result without writing
        #[arg(long)]
        dry_run: bool,
    },
    /// Export building SSOT (IFC is the compiler interchange spine).
    ///
    /// IFC export uses `export::ifc` only — review-gated, deterministic GlobalIds.
    /// Vendor BIM: export clean IFC from the CAD tool, then `arx import ifc`.
    /// No CAD plugins. Agent/daemon is not the L1 export authority.
    #[command(long_about = "\
Export the durable Building model (building.yaml).

IFC (`--format ifc`) is the only official industry interchange path. It runs
through export::ifc with review warnings and optional --approved-only.

BIM policy: ArxOS is IFC-only — no Revit/ArchiCAD plugins. Vendor tools must
export clean IFC for import.

Official pilot handoffs: `arx export --format ifc` (not agent auto-export).
--delta is not implemented and hard-errors if passed.")]
    Export {
        /// Export format: ifc (recommended), yaml, json
        #[arg(long, default_value = "ifc")]
        format: String,
        /// Output file path
        #[arg(long)]
        output: Option<String>,
        /// Git repository URL (legacy; prefer arx commit for SSOT)
        #[arg(long)]
        repo: Option<String>,
        /// Not implemented — hard-errors if set (hidden; no silent ignore)
        #[arg(long, hide = true)]
        delta: bool,
        /// Exclude proposed/rejected LiDAR auto entities from IFC export
        #[arg(long)]
        approved_only: bool,
        /// Commercial export: require access-receipt.json proving $AXD payment (N7 host gate)
        #[arg(long)]
        commercial: bool,
        /// Path to access receipt JSON (default: access-receipt.json)
        #[arg(long)]
        access_receipt: Option<String>,
    },
    /// Buyer market: quote / grant receipt / pay $AXD (lab path; not required for L1 success)
    Access {
        #[command(subcommand)]
        subcommand: AccessSubcommand,
    },
    /// Package verified building data as a contribution claim (lab reward path; not L1-required)
    Contribute {
        /// Output JSON path
        #[arg(long, default_value = "contribution.json")]
        output: String,
        /// Optional site latitude for location hash
        #[arg(long)]
        latitude: Option<f64>,
        /// Optional site longitude for location hash
        #[arg(long)]
        longitude: Option<f64>,
        /// Bind package to an explicit Git commit oid (default: HEAD if repo)
        #[arg(long)]
        git_commit: Option<String>,
        /// Allow packaging even if validation has errors (not for mint path)
        #[arg(long)]
        allow_invalid: bool,
        /// Print package summary without writing a file
        #[arg(long)]
        dry_run: bool,
        /// EIP-712 sign package (requires --features blockchain)
        #[arg(long)]
        sign: bool,
        /// Private key hex or env var name (default: ARX_PRIVATE_KEY or Anvil #0)
        #[arg(long)]
        private_key: Option<String>,
        /// Oracle contract address for EIP-712 domain / submit
        #[arg(long)]
        oracle: Option<String>,
        /// Chain id (31337 = Anvil local)
        #[arg(long, default_value = "31337")]
        chain_id: u64,
        /// Submit proposeContribution via RPC (oracle role + stake required)
        #[arg(long)]
        submit: bool,
        /// Worker wallet that performed the field labor
        #[arg(long)]
        worker: Option<String>,
        /// Whole $AXD amount to propose for mint
        #[arg(long, default_value = "100")]
        amount: u64,
        /// RPC URL for --submit
        #[arg(long)]
        rpc_url: Option<String>,
    },
    /// Print building hierarchy as text (default TUI helper — not LiDAR point-cloud viz)
    #[cfg(feature = "tui")]
    Render {
        /// Building name or id (loaded from cwd building.yaml)
        #[arg(long)]
        building: String,
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
        /// Commit message (positional)
        #[arg(value_name = "MESSAGE")]
        message: Option<String>,
        /// Commit message (git-style; preferred for field techs)
        #[arg(short = 'm', long = "message", value_name = "MESSAGE")]
        message_flag: Option<String>,
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
    /// Backfill missing durable ArxAddress fields on equipment in building.yaml
    Migrate {
        /// Preview changes without writing
        #[arg(long)]
        dry_run: bool,
    },
    /// Resolve merge conflicts interactively (requires `--features tui`)
    #[cfg(feature = "tui")]
    Merge(commands::MergeCommand),
    /// Launch TUI dashboard (requires `--features tui,agent`)
    #[cfg(all(feature = "tui", feature = "agent"))]
    Dashboard,
}

// Sub-command definitions
pub mod subcommands;
pub use subcommands::*;

#[derive(Subcommand)]
pub enum AccessSubcommand {
    /// Create an access request JSON (building id + nonce) for the data market
    Quote {
        /// Building UUID (default: load from building.yaml)
        #[arg(long)]
        building_id: Option<String>,
        /// Whole $AXD to offer
        #[arg(long, default_value = "1")]
        amount: u64,
        /// Output path
        #[arg(long, default_value = "access-request.json")]
        output: String,
    },
    /// Record access-receipt.json from a known payment tx (N7 host gate)
    Grant {
        /// Building UUID (default: from building.yaml)
        #[arg(long)]
        building_id: Option<String>,
        /// Payment transaction hash
        #[arg(long)]
        tx_hash: String,
        /// Output path
        #[arg(long, default_value = "access-receipt.json")]
        output: String,
    },
    /// Pay $AXD on-chain via ArxPaymentRouter (requires --features blockchain)
    Pay {
        /// Building UUID (or use --request)
        #[arg(long)]
        building_id: Option<String>,
        /// Whole $AXD amount
        #[arg(long, default_value = "1")]
        amount: u64,
        /// Hex nonce (or from --request)
        #[arg(long)]
        nonce: Option<String>,
        /// Path to access-request.json from `arx access quote`
        #[arg(long)]
        request: Option<String>,
        /// Buyer private key or env name
        #[arg(long)]
        private_key: Option<String>,
        /// Payment router address
        #[arg(long)]
        router: Option<String>,
        /// $AXD token address
        #[arg(long)]
        token: Option<String>,
        /// RPC URL
        #[arg(long)]
        rpc_url: Option<String>,
        /// Chain id
        #[arg(long, default_value = "31337")]
        chain_id: u64,
    },
}

#[derive(Subcommand)]
pub enum ImportSubcommand {
    /// Import IFC file
    Ifc {
        /// Path to IFC file
        ifc_file: String,
        /// Git repository URL
        #[arg(long)]
        repo: Option<String>,
        /// Dry run - show what would be done without making changes
        #[arg(long)]
        dry_run: bool,
        /// Enable strict validation (fail on missing spatial entities)
        #[arg(long)]
        strict: bool,
    },
    /// Import LiDAR point cloud
    Lidar {
        /// Path to PLY, LAS, or CSV/XYZ file
        file_path: String,
        /// Voxel size in meters for downsampling
        #[arg(long, default_value = "0.05")]
        voxel_size: f64,
        /// Enable light mode (aggresive downsampling & lower memory limits)
        #[arg(long)]
        light: bool,
        /// Dry run - parse and downsample without writing to disk
        #[arg(long)]
        dry_run: bool,
        /// Merge into an existing building instead of creating new
        #[arg(long)]
        merge: bool,
        /// Name of the existing building to merge into
        #[arg(long)]
        building: Option<String>,
    },
    /// Apply a text / AR command script (same as `arx edit`)
    Text {
        /// Script file path, or "-" for stdin
        script: String,
        /// Building YAML path or name
        #[arg(long)]
        building: Option<String>,
        /// Show result without writing
        #[arg(long)]
        dry_run: bool,
    },
}
