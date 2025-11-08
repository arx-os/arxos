// Live monitoring dashboard command handler

use crate::commands::watch_dashboard;

/// Handle the watch command
pub fn handle_watch_command(
    building: Option<String>,
    floor: Option<i32>,
    room: Option<String>,
    refresh_interval: u64,
    sensors_only: bool,
    alerts_only: bool,
    _log_level: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    // Use enhanced dashboard
    watch_dashboard::handle_watch_dashboard(
        building,
        floor,
        room,
        refresh_interval,
        sensors_only,
        alerts_only,
    )
}
