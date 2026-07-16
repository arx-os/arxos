// CLI module for ArxOS — dispatch + re-exports.
// Clap schema lives in `spec` (help order = compiler-first).

use clap::Parser;

pub mod args;
pub mod commands;
pub mod spec;

pub use spec::{AccessSubcommand, Commands, ImportSubcommand};

// Sub-command definitions (room / equipment / spatial clap trees)
pub mod subcommands;
pub use subcommands::*;

use commands::{
    access::AccessAction,
    data::{EquipmentCommand, RoomCommand, SpatialCommand},
    git::{CommitCommand, DiffCommand, StageCommand, StatusCommand, UnstageCommand},
    AccessCommand, Command, ContributeCommand, ExportCommand, ImportCommand, InitCommand,
    MigrateCommand,
};

#[derive(Parser)]
#[command(name = "arx")]
#[command(about = "ArxOS building compiler — Git for Buildings")]
#[command(
    long_about = "Local-first building compiler: IFC / LiDAR / text → building.yaml → Git → IFC export.\n\nDefault features: compiler spine + TUI (primary UI). Optional: --features agent | web | blockchain | full.\n\nL1 pilot loop: init → import → edit/review → validate → git → export --format ifc\n(see docs/l1-supported-workflow.md). Lab contribute/access are optional."
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
                path,
                repo,
                approved_only,
                commercial,
                access_receipt,
            } => {
                let cmd = ExportCommand {
                    format,
                    output,
                    path,
                    repo,
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
            #[cfg(feature = "agent")]
            Commands::Claim {
                building_id,
                approve,
                pending_index,
                live,
            } => {
                use crate::agent::claim::GraceWindowManager;

                let grace_manager = GraceWindowManager::new();
                let repo_path = ".";

                if let Some(appr) = approve {
                    let idx = pending_index.ok_or_else(|| "Error: --pending-index <INDEX> is required when reviewing a contribution".to_string())?;
                    let owner_addr = "0x1234567890abcdef";
                    
                    let mut gm = grace_manager;
                    gm.register_active_claim(building_id.clone(), 14);

                    let (state, receipt) = gm.review_pending_contribution(
                        repo_path,
                        &building_id,
                        idx,
                        appr,
                        owner_addr,
                        live,
                    )?;
                    println!("Status: {:?}", state);
                    println!("{}", receipt);
                } else {
                    let pending = grace_manager.list_pending_contributions(repo_path)?;
                    if pending.is_empty() {
                        println!("No pending contributions for building: {}", building_id);
                    } else {
                        println!("Pending Contributions:");
                        for (idx, _content) in pending {
                            println!("[{}] Pending Contribution", idx);
                        }
                    }
                }
                Ok(())
            }
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
                        metrics: std::sync::Arc::new(crate::agent::observability::AgentMetrics::new()),
                        reload_handle: None,
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
