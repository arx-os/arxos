//! Information Panel for Interactive 3D Renderer
//!
//! Provides a Ratatui-based info panel showing:
//! - Selected equipment details
//! - Camera position and settings
//! - View mode and rendering stats
//! - Quick actions and controls

use crate::render3d::state::{CameraState, InteractiveState, ViewMode};
use crate::tui::{StatusColor, Theme};
use crate::core::{EquipmentHealthStatus, EquipmentStatus};
use crate::yaml::BuildingData;
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
};

/// Information panel state
pub struct InfoPanelState {
    pub show_panel: bool,
    pub panel_width: u16,
    pub theme: Theme,
}

impl InfoPanelState {
    pub fn new() -> Self {
        Self {
            show_panel: true,
            panel_width: 40,
            theme: Theme::default(),
        }
    }

    pub fn toggle(&mut self) {
        self.show_panel = !self.show_panel;
    }
}

impl Default for InfoPanelState {
    fn default() -> Self {
        Self::new()
    }
}

/// Render equipment info panel
pub fn render_equipment_info<'a>(
    state: &'a InteractiveState,
    building_data: &'a BuildingData,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let mut lines = vec![
        Line::from(vec![Span::styled(
            "Equipment Information",
            Style::default()
                .fg(theme.primary)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(Span::raw("")),
    ];

    if state.selected_equipment.is_empty() {
        lines.push(Line::from(vec![Span::styled(
            "No equipment selected",
            Style::default().fg(theme.muted),
        )]));
        lines.push(Line::from(Span::raw("")));
        lines.push(Line::from(vec![Span::styled(
            "Press 's' to select equipment",
            Style::default().fg(theme.muted),
        )]));
    } else {
        for equipment_id in &state.selected_equipment {
            // Find equipment in building data
            for floor in &building_data.building.floors {
                if let Some(equipment) = floor.equipment.iter().find(|e| e.id == *equipment_id) {
                    lines.push(Line::from(vec![
                        Span::styled("ID: ", Style::default().fg(theme.muted)),
                        Span::styled(equipment.id.as_str(), Style::default().fg(theme.text)),
                    ]));
                    lines.push(Line::from(vec![
                        Span::styled("Name: ", Style::default().fg(theme.muted)),
                        Span::styled(equipment.name.as_str(), Style::default().fg(theme.text)),
                    ]));
                    lines.push(Line::from(vec![
                        Span::styled("Type: ", Style::default().fg(theme.muted)),
                        Span::styled(
                            format!("{:?}", equipment.equipment_type),
                            Style::default().fg(theme.text),
                        ),
                    ]));
                    // Use health_status if available, otherwise map from operational status
                    let status_color = if let Some(ref health) = equipment.health_status {
                        match health {
                            EquipmentHealthStatus::Healthy => StatusColor::Healthy,
                            EquipmentHealthStatus::Warning => StatusColor::Warning,
                            EquipmentHealthStatus::Critical => StatusColor::Critical,
                            EquipmentHealthStatus::Unknown => StatusColor::Unknown,
                        }
                    } else {
                        // Map operational status to health status color
                        match equipment.status {
                            EquipmentStatus::Active => StatusColor::Healthy,
                            EquipmentStatus::Maintenance => StatusColor::Warning,
                            EquipmentStatus::OutOfOrder => StatusColor::Critical,
                            EquipmentStatus::Inactive | EquipmentStatus::Unknown => {
                                StatusColor::Unknown
                            }
                        }
                    };
                    let status_text = if let Some(ref health) = equipment.health_status {
                        format!("{:?}", health)
                    } else {
                        format!("{:?}", equipment.status)
                    };
                    lines.push(Line::from(vec![
                        Span::styled("Status: ", Style::default().fg(theme.muted)),
                        Span::styled(status_text, Style::default().fg(status_color.color())),
                    ]));
                    // Room information is stored separately in floor data
                    // Find room name by searching through floors and wings
                    for floor in building_data.building.floors.iter() {
                        let mut found_room = None;
                        for wing in &floor.wings {
                            if let Some(room) = wing
                                .rooms
                                .iter()
                                .find(|r| r.equipment.iter().any(|e| e.id == equipment.id.as_str()))
                            {
                                found_room = Some(room);
                                break;
                            }
                        }
                        if let Some(room) = found_room {
                            lines.push(Line::from(vec![
                                Span::styled("Room: ", Style::default().fg(theme.muted)),
                                Span::styled(room.name.clone(), Style::default().fg(theme.text)),
                            ]));
                            break;
                        }
                    }
                    lines.push(Line::from(Span::raw("")));
                    break;
                }
            }
        }
    }

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Equipment"))
        .alignment(Alignment::Left)
}

/// Render camera info panel
pub fn render_camera_info<'a>(
    camera_state: &'a CameraState,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let lines = vec![
        Line::from(vec![Span::styled(
            "Camera Information",
            Style::default()
                .fg(theme.primary)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled("Position: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!(
                    "({:.1}, {:.1}, {:.1})",
                    camera_state.position.x, camera_state.position.y, camera_state.position.z
                ),
                Style::default().fg(theme.text),
            ),
        ]),
        Line::from(vec![
            Span::styled("Target: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!(
                    "({:.1}, {:.1}, {:.1})",
                    camera_state.target.x, camera_state.target.y, camera_state.target.z
                ),
                Style::default().fg(theme.text),
            ),
        ]),
        Line::from(vec![
            Span::styled("Zoom: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!("{:.2}x", camera_state.zoom),
                Style::default().fg(theme.text),
            ),
        ]),
        Line::from(vec![
            Span::styled("FOV: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!("{:.1}°", camera_state.fov),
                Style::default().fg(theme.text),
            ),
        ]),
        Line::from(vec![
            Span::styled("Rotation: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!(
                    "P:{:.1}° Y:{:.1}° R:{:.1}°",
                    camera_state.rotation.pitch,
                    camera_state.rotation.yaw,
                    camera_state.rotation.roll
                ),
                Style::default().fg(theme.text),
            ),
        ]),
    ];

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Camera"))
        .alignment(Alignment::Left)
}

/// Render view mode info
pub fn render_view_mode_info<'a>(
    view_mode: &'a ViewMode,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let mode_text = match view_mode {
        ViewMode::Standard => "Standard 3D View",
        ViewMode::CrossSection => "Cross-Section View",
        ViewMode::Connections => "Connections View",
        ViewMode::Maintenance => "Maintenance Overlay",
    };

    let lines = vec![
        Line::from(vec![Span::styled(
            "View Mode",
            Style::default()
                .fg(theme.primary)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled(
            mode_text,
            Style::default().fg(theme.text),
        )]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled(
            "Press 'v' to cycle modes",
            Style::default().fg(theme.muted),
        )]),
    ];

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("View"))
        .alignment(Alignment::Left)
}

/// Render rendering statistics
pub fn render_stats<'a>(
    fps: f64,
    frame_count: u32,
    render_time: std::time::Duration,
    _area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let lines = vec![
        Line::from(vec![Span::styled(
            "Statistics",
            Style::default()
                .fg(theme.primary)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled("FPS: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!("{:.1}", fps),
                Style::default().fg(if fps > 20.0 {
                    Color::Green
                } else if fps > 10.0 {
                    Color::Yellow
                } else {
                    Color::Red
                }),
            ),
        ]),
        Line::from(vec![
            Span::styled("Frames: ", Style::default().fg(theme.muted)),
            Span::styled(format!("{}", frame_count), Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("Render Time: ", Style::default().fg(theme.muted)),
            Span::styled(
                format!("{:.2}ms", render_time.as_secs_f64() * 1000.0),
                Style::default().fg(theme.text),
            ),
        ]),
    ];

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Stats"))
        .alignment(Alignment::Left)
}

/// Render quick actions/controls
pub fn render_controls<'a>(_area: Rect, theme: &'a Theme) -> Paragraph<'a> {
    let lines = vec![
        Line::from(vec![Span::styled(
            "Controls",
            Style::default()
                .fg(theme.primary)
                .add_modifier(Modifier::BOLD),
        )]),
        Line::from(Span::raw("")),
        Line::from(vec![Span::styled(
            "WASD/Arrows: Move camera",
            Style::default().fg(theme.muted),
        )]),
        Line::from(vec![Span::styled(
            "Q/E: Zoom in/out",
            Style::default().fg(theme.muted),
        )]),
        Line::from(vec![Span::styled(
            "V: Cycle view modes",
            Style::default().fg(theme.muted),
        )]),
        Line::from(vec![Span::styled(
            "S: Select equipment",
            Style::default().fg(theme.muted),
        )]),
        Line::from(vec![Span::styled(
            "I: Toggle info panel",
            Style::default().fg(theme.muted),
        )]),
        Line::from(vec![Span::styled(
            "H: Toggle help",
            Style::default().fg(theme.muted),
        )]),
        Line::from(vec![Span::styled(
            "ESC/Q: Quit",
            Style::default().fg(theme.muted),
        )]),
    ];

    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Left)
}

/// Render the complete info panel layout
pub fn render_info_panel<'a>(
    state: &'a InteractiveState,
    building_data: &'a BuildingData,
    fps: f64,
    frame_count: u32,
    render_time: std::time::Duration,
    area: Rect,
    theme: &'a Theme,
) -> Vec<(Rect, Paragraph<'a>)> {
    let chunks = Layout::default()
        .direction(ratatui::layout::Direction::Vertical)
        .constraints([
            Constraint::Min(8), // Equipment info
            Constraint::Min(6), // Camera info
            Constraint::Min(4), // View mode
            Constraint::Min(4), // Stats
            Constraint::Min(8), // Controls
        ])
        .split(area)
        .to_vec();

    vec![
        (
            chunks[0],
            render_equipment_info(state, building_data, chunks[0], theme),
        ),
        (
            chunks[1],
            render_camera_info(&state.camera_state, chunks[1], theme),
        ),
        (
            chunks[2],
            render_view_mode_info(&state.view_mode, chunks[2], theme),
        ),
        (
            chunks[3],
            render_stats(fps, frame_count, render_time, chunks[3], theme),
        ),
        (chunks[4], render_controls(chunks[4], theme)),
    ]
}
