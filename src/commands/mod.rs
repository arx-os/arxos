// Command execution router for ArxOS
// This module routes CLI commands to their respective handlers

pub mod import;
pub mod export;
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

use crate::cli::Commands;

/// Execute the specified command by routing to appropriate handler
pub fn execute_command(command: Commands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        Commands::Import { ifc_file, repo } => import::handle_import(ifc_file, repo),
        Commands::Export { repo } => export::handle_export(repo),
        Commands::Status { verbose } => git_ops::handle_status(verbose),
        Commands::Diff { commit, file, stat } => git_ops::handle_diff(commit, file, stat),
        Commands::History { limit, verbose, file } => git_ops::handle_history(limit, verbose, file),
        Commands::Config { show, set, reset, edit } => config_mgmt::handle_config(show, set, reset, edit),
        Commands::Render { building, floor, three_d, show_status, show_rooms, format, projection, view_angle, scale, spatial_index } => {
            render::handle_render(building, floor, three_d, show_status, show_rooms, format, projection, view_angle, scale, spatial_index)
        },
        Commands::Interactive { building, projection, view_angle, scale, width, height, spatial_index, show_status, show_rooms, show_connections, fps, show_fps, show_help } => {
            interactive::handle_interactive(building, projection, view_angle, scale, width, height, spatial_index, show_status, show_rooms, show_connections, fps, show_fps, show_help)
        },
        Commands::Validate { path } => validate::handle_validate(path),
        Commands::Room { command } => room::handle_room_command(command),
        Commands::Equipment { command } => equipment::handle_equipment_command(command),
        Commands::Spatial { command } => spatial::handle_spatial_command(command),
        Commands::Watch { building, floor, room, refresh_interval, sensors_only, alerts_only, log_level } => {
            watch::handle_watch_command(building, floor, room, refresh_interval, sensors_only, alerts_only, log_level)
        },
        Commands::Search { query, equipment, rooms, buildings, case_sensitive, regex, limit, verbose } => {
            search::handle_search_command(query, equipment, rooms, buildings, case_sensitive, regex, limit, verbose)
        },
        Commands::Filter { equipment_type, status, floor, room, building, critical_only, healthy_only, alerts_only, format, limit, verbose } => {
            search::handle_filter_command(equipment_type, status, floor, room, building, critical_only, healthy_only, alerts_only, format, limit, verbose)
        },
        Commands::ArIntegrate { scan_file, room, floor, building, commit, message } => {
            ar::handle_ar_integrate_command(scan_file, room, floor, building, commit, message)
        },
        Commands::Ar { subcommand } => ar::handle_ar_command(subcommand),
        Commands::ProcessSensors { sensor_dir, building, commit, watch } => {
            sensors::handle_process_sensors_command(&sensor_dir, &building, commit, watch)
        },
        Commands::IFC { subcommand } => ifc::handle_ifc_command(subcommand),
    }
}

