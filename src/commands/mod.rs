// Command execution router for ArxOS
// This module routes CLI commands to their respective handlers

pub mod import;
pub mod export;
pub mod init;
pub mod git_ops;
pub mod config_mgmt;
pub mod render;
pub mod interactive;
pub mod room;
pub mod equipment;
pub mod spatial;
pub mod search;
pub mod watch;
pub mod ar;
pub mod sensors;
pub mod ifc;
pub mod validate;
pub mod health;
pub mod doc;
pub mod game;
pub mod sync;

use crate::cli::Commands;

/// Execute the specified command by routing to appropriate handler
pub fn execute_command(command: Commands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        Commands::Init { name, description, location, git_init, commit, coordinate_system, units } => {
            use init::InitConfig;
            init::handle_init(InitConfig {
                name,
                description,
                location,
                git_init,
                commit,
                coordinate_system,
                units,
            })
        },
        Commands::Import { ifc_file, repo, dry_run } => import::handle_import(ifc_file, repo, dry_run),
        Commands::Export { format, output, repo, delta } => {
            export::handle_export_with_format(format, output, repo, delta)
        },
        Commands::Sync { ifc, watch, delta } => sync::handle_sync(ifc, watch, delta),
        Commands::Status { verbose } => git_ops::handle_status(verbose),
        Commands::Stage { all, file } => git_ops::handle_stage(all, file),
        Commands::Commit { message } => git_ops::handle_commit(message),
        Commands::Unstage { all, file } => git_ops::handle_unstage(all, file),
        Commands::Diff { commit, file, stat } => git_ops::handle_diff(commit, file, stat),
        Commands::History { limit, verbose, file } => git_ops::handle_history(limit, verbose, file),
        Commands::Config { show, set, reset, edit } => config_mgmt::handle_config(show, set, reset, edit),
        Commands::Render { building, floor, three_d, show_status, show_rooms, format, projection, view_angle, scale, spatial_index } => {
            use render::RenderCommandConfig;
            render::handle_render(RenderCommandConfig {
                building,
                floor,
                three_d,
                show_status,
                show_rooms,
                format,
                projection,
                view_angle,
                scale,
                spatial_index,
            })
        },
        Commands::Interactive { building, projection, view_angle, scale, width, height, spatial_index, show_status, show_rooms, show_connections, fps, show_fps, show_help } => {
            use interactive::InteractiveCommandConfig;
            interactive::handle_interactive(InteractiveCommandConfig {
                building,
                projection,
                view_angle,
                scale,
                width,
                height,
                spatial_index,
                show_status,
                show_rooms,
                show_connections,
                fps,
                show_fps,
                show_help,
            })
        },
        Commands::Validate { path } => validate::handle_validate(path),
        Commands::Room { command } => room::handle_room_command(command),
        Commands::Equipment { command } => equipment::handle_equipment_command(command),
        Commands::Spatial { command } => spatial::handle_spatial_command(command),
        Commands::Watch { building, floor, room, refresh_interval, sensors_only, alerts_only, log_level } => {
            watch::handle_watch_command(building, floor, room, refresh_interval, sensors_only, alerts_only, log_level)
        },
        Commands::Search { query, equipment, rooms, buildings, case_sensitive, regex, limit, verbose } => {
            use crate::search::SearchConfig;
            let config = SearchConfig {
                query,
                search_equipment: equipment || (!equipment && !rooms && !buildings),
                search_rooms: rooms,
                search_buildings: buildings,
                case_sensitive,
                use_regex: regex,
                limit,
                verbose,
            };
            search::handle_search_command(config)
        },
        Commands::Filter { equipment_type, status, floor, room, building, critical_only, healthy_only, alerts_only, format, limit, verbose } => {
            use crate::search::{FilterConfig, OutputFormat};
            let config = FilterConfig {
                equipment_type,
                status,
                floor,
                room,
                building,
                critical_only,
                healthy_only,
                alerts_only,
                format: OutputFormat::from(format),
                limit,
            };
            search::handle_filter_command(config, verbose)
        },
        Commands::ArIntegrate { scan_file, room, floor, building, commit, message } => {
            ar::handle_ar_integrate_command(scan_file, room, floor, building, commit, message)
        },
        Commands::Ar { subcommand } => ar::handle_ar_command(subcommand),
        Commands::ProcessSensors { sensor_dir, building, commit, watch } => {
            sensors::handle_process_sensors_command(&sensor_dir, &building, commit, watch)
        },
        Commands::SensorsHttp { building, host, port } => {
            sensors::handle_sensors_http_command(&building, &host, port)
        },
        Commands::SensorsMqtt { building, broker, port, username, password, topics } => {
            sensors::handle_sensors_mqtt_command(&building, &broker, port, username.as_deref(), password.as_deref(), &topics)
        },
        Commands::IFC { subcommand } => ifc::handle_ifc_command(subcommand),
        Commands::Health { component, verbose } => health::handle_health(component, verbose),
        Commands::Doc { building, output } => doc::handle_doc(building, output),
        Commands::Game { subcommand } => {
            use crate::cli::GameCommands;
            match subcommand {
                GameCommands::Review { pr_id, pr_dir, building, interactive, export_ifc } => {
                    game::handle_game_review(pr_id, pr_dir, building, interactive, export_ifc)
                },
                GameCommands::Plan { building, interactive, export_pr, export_ifc } => {
                    game::handle_game_plan(building, interactive, export_pr, export_ifc)
                },
                GameCommands::Learn { pr_id, pr_dir, building } => {
                    game::handle_game_learn(pr_id, pr_dir, building)
                },
            }
        },
    }
}

