//! Interactive Diff Viewer for ArxOS TUI
//!
//! Provides an intuitive interface for viewing building data changes:
//! - Side-by-side comparison (old vs new)
//! - Syntax highlighting for YAML structure
//! - Collapsible sections (collapse unchanged parts)
//! - Navigate hunks (jump to next/previous change)
//! - File tree for multi-file diffs
//! - Summary panel showing overall changes

use crate::ui::{TerminalManager, Theme};
use crate::git::manager::{BuildingGitManager, GitConfigManager};
use crate::git::{DiffResult, DiffLineType};
use crate::commands::git_ops::find_git_repository;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
};
use std::time::Duration;
use std::collections::{HashMap, HashSet};

/// Diff hunk (group of related changes)
#[derive(Debug, Clone)]
struct DiffHunk {
    start_line: usize,
    end_line: usize,
    old_lines: Vec<String>,
    new_lines: Vec<String>,
    context_lines: usize,
}

/// Diff viewer state
struct DiffViewerState {
    diff_result: DiffResult,
    file_diffs: HashMap<String, Vec<DiffHunk>>,
    selected_file: Option<String>,
    selected_hunk: usize,
    hunks: Vec<DiffHunk>,
    scroll_offset: usize,
    show_file_tree: bool,
    collapsed_hunks: HashSet<usize>,
    view_mode: ViewMode,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ViewMode {
    SideBySide,
    Unified,
}

impl DiffViewerState {
    fn new(diff_result: DiffResult) -> Self {
        // Group file diffs by file and create hunks
        let mut file_diffs: HashMap<String, Vec<DiffHunk>> = HashMap::new();
        let mut current_file = String::new();
        let mut current_hunk: Vec<(usize, String, DiffLineType)> = Vec::new();
        
        for diff in &diff_result.file_diffs {
            if diff.file_path != current_file {
                // Save previous hunk
                if !current_hunk.is_empty() && !current_file.is_empty() {
                    Self::add_hunk_to_file(&mut file_diffs, &current_file, &current_hunk);
                }
                current_file = diff.file_path.clone();
                current_hunk.clear();
            }
            
            // Clone the line type (it's Copy-able)
            let line_type = diff.line_type;
            current_hunk.push((diff.line_number, diff.content.clone(), line_type));
        }
        
        // Save last hunk
        if !current_hunk.is_empty() && !current_file.is_empty() {
            Self::add_hunk_to_file(&mut file_diffs, &current_file, &current_hunk);
        }
        
        // Get first file's hunks for initial display
        let first_file = file_diffs.keys().next().cloned();
        let hunks = first_file.as_ref()
            .and_then(|f| file_diffs.get(f))
            .cloned()
            .unwrap_or_default();
        
        Self {
            diff_result,
            file_diffs,
            selected_file: first_file,
            selected_hunk: 0,
            hunks,
            scroll_offset: 0,
            show_file_tree: true,
            collapsed_hunks: HashSet::new(),
            view_mode: ViewMode::SideBySide,
        }
    }
    
    fn add_hunk_to_file(
        file_diffs: &mut HashMap<String, Vec<DiffHunk>>,
        file_path: &str,
        lines: &[(usize, String, crate::git::DiffLineType)],
    ) {
        if lines.is_empty() {
            return;
        }
        
        let mut old_lines = Vec::new();
        let mut new_lines = Vec::new();
        let mut old_line_num = lines[0].0;
        let mut new_line_num = lines[0].0;
        let mut context_lines = 0;
        
        for (line_num, content, line_type) in lines {
            match line_type {
                DiffLineType::Addition => {
                    new_lines.push(format!("{:4} {}", *line_num, content));
                    new_line_num += 1;
                }
                DiffLineType::Deletion => {
                    old_lines.push(format!("{:4} {}", *line_num, content));
                    old_line_num += 1;
                }
                DiffLineType::Context => {
                    old_lines.push(format!("{:4} {}", old_line_num, content));
                    new_lines.push(format!("{:4} {}", new_line_num, content));
                    old_line_num += 1;
                    new_line_num += 1;
                    context_lines += 1;
                }
            }
        }
        
        let hunk = DiffHunk {
            start_line: lines[0].0,
            end_line: lines.last().map(|l| l.0).unwrap_or(lines[0].0),
            old_lines,
            new_lines,
            context_lines,
        };
        
        file_diffs.entry(file_path.to_string()).or_insert_with(Vec::new).push(hunk);
    }
    
    fn select_file(&mut self, file_path: &str) {
        self.selected_file = Some(file_path.to_string());
        self.hunks = self.file_diffs.get(file_path)
            .cloned()
            .unwrap_or_default();
        self.selected_hunk = 0;
        self.scroll_offset = 0;
    }
    
    fn next_hunk(&mut self) {
        if !self.hunks.is_empty() {
            self.selected_hunk = (self.selected_hunk + 1) % self.hunks.len();
            self.scroll_offset = 0;
        }
    }
    
    fn previous_hunk(&mut self) {
        if !self.hunks.is_empty() {
            self.selected_hunk = if self.selected_hunk == 0 {
                self.hunks.len() - 1
            } else {
                self.selected_hunk - 1
            };
            self.scroll_offset = 0;
        }
    }
    
    fn toggle_hunk_collapse(&mut self, hunk_idx: usize) {
        if self.collapsed_hunks.contains(&hunk_idx) {
            self.collapsed_hunks.remove(&hunk_idx);
        } else {
            self.collapsed_hunks.insert(hunk_idx);
        }
    }
    
    fn toggle_view_mode(&mut self) {
        self.view_mode = match self.view_mode {
            ViewMode::SideBySide => ViewMode::Unified,
            ViewMode::Unified => ViewMode::SideBySide,
        };
    }
    
    fn get_file_list(&self) -> Vec<String> {
        self.file_diffs.keys().cloned().collect()
    }
}

/// Render header
fn render_header<'a>(
    state: &'a DiffViewerState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let title = format!(
        "Diff Viewer - {} files changed | +{} / -{}",
        state.diff_result.files_changed,
        state.diff_result.insertions,
        state.diff_result.deletions
    );
    
    let commit_info = format!(
        "{} → {}",
        &state.diff_result.compare_hash[..8],
        &state.diff_result.commit_hash[..8]
    );
    
    Paragraph::new(vec![
        Line::from(vec![
            Span::styled(title, Style::default().fg(theme.text).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(vec![
            Span::styled("Commits: ", Style::default().fg(theme.muted)),
            Span::styled(commit_info, Style::default().fg(theme.primary)),
        ]),
    ])
    .block(Block::default().borders(Borders::ALL).title("Diff Viewer"))
    .alignment(Alignment::Left)
}

/// Render file tree
fn render_file_tree<'a>(
    state: &'a DiffViewerState,
    area: Rect,
    theme: &'a Theme,
) -> List<'a> {
    let files = state.get_file_list();
    
    let items: Vec<ListItem> = files.iter()
        .enumerate()
        .map(|(idx, file)| {
            let is_selected = state.selected_file.as_ref().map_or(false, |f| f == file);
            let prefix = if is_selected { ">" } else { " " };
            
            // Count changes in file
            let hunk_count = state.file_diffs.get(file).map(|h| h.len()).unwrap_or(0);
            
            ListItem::new(Line::from(vec![
                Span::styled(prefix, Style::default().fg(theme.accent)),
                Span::styled(" ", Style::default()),
                Span::styled(
                    file.clone(),
                    Style::default()
                        .fg(theme.text)
                        .add_modifier(if is_selected { Modifier::BOLD | Modifier::REVERSED } else { Modifier::empty() }),
                ),
                Span::styled(format!(" ({})", hunk_count), Style::default().fg(theme.muted)),
            ]))
        })
        .collect();
    
    List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Files"))
        .highlight_style(Style::default().add_modifier(Modifier::BOLD))
}

/// Render side-by-side diff
fn render_side_by_side_diff<'a>(
    state: &'a DiffViewerState,
    area: Rect,
    theme: &'a Theme,
) -> Vec<Paragraph<'a>> {
    if state.hunks.is_empty() || state.selected_hunk >= state.hunks.len() {
        return vec![
            Paragraph::new("No changes to display")
                .block(Block::default().borders(Borders::ALL).title("Diff"))
                .alignment(Alignment::Center)
        ];
    }
    
    let hunk = &state.hunks[state.selected_hunk];
    let is_collapsed = state.collapsed_hunks.contains(&state.selected_hunk);
    
    if is_collapsed {
        return vec![
            Paragraph::new(vec![
                Line::from(vec![
                    Span::styled("▶ ", Style::default().fg(theme.accent)),
                    Span::styled(format!("Hunk {} ({} lines)", state.selected_hunk + 1, hunk.old_lines.len() + hunk.new_lines.len()), Style::default().fg(theme.text)),
                ]),
            ])
            .block(Block::default().borders(Borders::ALL).title("Diff (Collapsed)"))
            .alignment(Alignment::Left)
        ];
    }
    
    // Split area for old and new
    let chunks = Layout::default()
        .direction(ratatui::layout::Direction::Horizontal)
        .constraints([
            Constraint::Percentage(50),
            Constraint::Percentage(50),
        ])
        .split(area)
        .to_vec();
    
    // Build old lines
    let old_lines: Vec<Line> = hunk.old_lines.iter()
        .map(|line| {
            Line::from(vec![
                Span::styled("- ", Style::default().fg(Color::Red)),
                Span::styled(line.clone(), Style::default().fg(Color::Red)),
            ])
        })
        .collect();
    
    // Build new lines
    let new_lines: Vec<Line> = hunk.new_lines.iter()
        .map(|line| {
            Line::from(vec![
                Span::styled("+ ", Style::default().fg(Color::Green)),
                Span::styled(line.clone(), Style::default().fg(Color::Green)),
            ])
        })
        .collect();
    
    vec![
        Paragraph::new(old_lines)
            .block(Block::default().borders(Borders::ALL).title("Old Version"))
            .alignment(Alignment::Left),
        Paragraph::new(new_lines)
            .block(Block::default().borders(Borders::ALL).title("New Version"))
            .alignment(Alignment::Left),
    ]
}

/// Render unified diff
fn render_unified_diff<'a>(
    state: &'a DiffViewerState,
    area: Rect,
    theme: &'a Theme,
) -> Paragraph<'a> {
    if state.hunks.is_empty() || state.selected_hunk >= state.hunks.len() {
        return Paragraph::new("No changes to display")
            .block(Block::default().borders(Borders::ALL).title("Diff"))
            .alignment(Alignment::Center);
    }
    
    let hunk = &state.hunks[state.selected_hunk];
    let is_collapsed = state.collapsed_hunks.contains(&state.selected_hunk);
    
    if is_collapsed {
        return Paragraph::new(vec![
            Line::from(vec![
                Span::styled("▶ ", Style::default().fg(theme.accent)),
                Span::styled(format!("Hunk {} ({} lines)", state.selected_hunk + 1, hunk.old_lines.len() + hunk.new_lines.len()), Style::default().fg(theme.text)),
            ]),
        ])
        .block(Block::default().borders(Borders::ALL).title("Diff (Collapsed)"))
        .alignment(Alignment::Left);
    }
    
    // Combine old and new lines with context
    let mut unified_lines = Vec::new();
    
    // Add old lines (deletions)
    for line in &hunk.old_lines {
        unified_lines.push(Line::from(vec![
            Span::styled("- ", Style::default().fg(Color::Red)),
            Span::styled(line.clone(), Style::default().fg(Color::Red)),
        ]));
    }
    
    // Add new lines (additions)
    for line in &hunk.new_lines {
        unified_lines.push(Line::from(vec![
            Span::styled("+ ", Style::default().fg(Color::Green)),
            Span::styled(line.clone(), Style::default().fg(Color::Green)),
        ]));
    }
    
    Paragraph::new(unified_lines)
        .block(Block::default().borders(Borders::ALL).title("Unified Diff"))
        .alignment(Alignment::Left)
}

/// Render summary panel
fn render_summary<'a>(
    state: &'a DiffViewerState,
    theme: &'a Theme,
) -> Paragraph<'a> {
    let lines = vec![
        Line::from(vec![
            Span::styled("Summary", Style::default().fg(theme.primary).add_modifier(Modifier::BOLD)),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled("Files changed: ", Style::default().fg(theme.muted)),
            Span::styled(state.diff_result.files_changed.to_string(), Style::default().fg(theme.text)),
        ]),
        Line::from(vec![
            Span::styled("Insertions: ", Style::default().fg(theme.muted)),
            Span::styled(format!("+{}", state.diff_result.insertions), Style::default().fg(Color::Green)),
        ]),
        Line::from(vec![
            Span::styled("Deletions: ", Style::default().fg(theme.muted)),
            Span::styled(format!("-{}", state.diff_result.deletions), Style::default().fg(Color::Red)),
        ]),
        Line::from(Span::raw("")),
        Line::from(vec![
            Span::styled("Hunks: ", Style::default().fg(theme.muted)),
            Span::styled(format!("{}/{}", state.selected_hunk + 1, state.hunks.len()), Style::default().fg(theme.text)),
        ]),
        if let Some(ref file) = state.selected_file {
            Line::from(vec![
                Span::styled("File: ", Style::default().fg(theme.muted)),
                Span::styled(file.clone(), Style::default().fg(theme.text)),
            ])
        } else {
            Line::from(vec![
                Span::styled("File: ", Style::default().fg(theme.muted)),
                Span::styled("None", Style::default().fg(theme.muted)),
            ])
        },
    ];
    
    Paragraph::new(lines)
        .block(Block::default().borders(Borders::ALL).title("Summary"))
        .alignment(Alignment::Left)
}

/// Render footer
fn render_footer<'a>(
    theme: &'a Theme,
    view_mode: ViewMode,
) -> Paragraph<'a> {
    let help_text = match view_mode {
        ViewMode::SideBySide => "←/→: Navigate hunks | t: Toggle mode | c: Collapse | f: Files | q: Quit",
        ViewMode::Unified => "←/→: Navigate hunks | t: Toggle mode | c: Collapse | f: Files | q: Quit",
    };
    
    Paragraph::new(help_text)
        .style(Style::default().fg(theme.muted))
        .block(Block::default().borders(Borders::ALL).title("Controls"))
        .alignment(Alignment::Center)
}

/// Handle interactive diff viewer
pub fn handle_diff_viewer(
    commit: Option<String>,
    file: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut terminal = TerminalManager::new()?;
    let theme = Theme::default();
    
    // Get diff result
    let repo_path = find_git_repository()?
        .ok_or("Not in a Git repository")?;
    
    let config = GitConfigManager::default_config();
    let manager = BuildingGitManager::new(&repo_path, "Building", config)?;
    let diff_result = manager.get_diff(commit.as_deref(), file.as_deref())?;
    
    if diff_result.file_diffs.is_empty() {
        println!("✅ No changes found");
        return Ok(());
    }
    
    let mut state = DiffViewerState::new(diff_result);
    let mut file_list_state = ListState::default();
    let mut file_tree_index = 0;
    
    loop {
        terminal.terminal().draw(|frame| {
            let chunks = Layout::default()
                .direction(ratatui::layout::Direction::Vertical)
                .constraints([
                    Constraint::Length(4),
                    Constraint::Min(0),
                    Constraint::Length(3),
                ])
                .split(frame.size())
                .to_vec();
            
            // Header
            let header = render_header(&state, &theme);
            frame.render_widget(header, chunks[0]);
            
            // Content
            if state.show_file_tree {
                let content_chunks = Layout::default()
                    .direction(ratatui::layout::Direction::Horizontal)
                    .constraints([
                        Constraint::Percentage(30),
                        Constraint::Percentage(70),
                    ])
                    .split(chunks[1])
                    .to_vec();
                
                // File tree
                let file_tree = render_file_tree(&state, content_chunks[0], &theme);
                file_list_state.select(Some(file_tree_index));
                frame.render_stateful_widget(file_tree, content_chunks[0], &mut file_list_state);
                
                // Diff view
                let diff_area = Layout::default()
                    .direction(ratatui::layout::Direction::Vertical)
                    .constraints([
                        Constraint::Min(0),
                        Constraint::Length(8),
                    ])
                    .split(content_chunks[1])
                    .to_vec();
                
                match state.view_mode {
                    ViewMode::SideBySide => {
                        let diff_widgets = render_side_by_side_diff(&state, diff_area[0], &theme);
                        let diff_chunks = Layout::default()
                            .direction(ratatui::layout::Direction::Horizontal)
                            .constraints([
                                Constraint::Percentage(50),
                                Constraint::Percentage(50),
                            ])
                            .split(diff_area[0])
                            .to_vec();
                        
                        if diff_widgets.len() >= 2 {
                            frame.render_widget(diff_widgets[0].clone(), diff_chunks[0]);
                            frame.render_widget(diff_widgets[1].clone(), diff_chunks[1]);
                        }
                    }
                    ViewMode::Unified => {
                        let diff_widget = render_unified_diff(&state, diff_area[0], &theme);
                        frame.render_widget(diff_widget, diff_area[0]);
                    }
                }
                
                // Summary
                let summary = render_summary(&state, &theme);
                frame.render_widget(summary, diff_area[1]);
            } else {
                // Full diff view without file tree
                let diff_area = Layout::default()
                    .direction(ratatui::layout::Direction::Vertical)
                    .constraints([
                        Constraint::Min(0),
                        Constraint::Length(8),
                    ])
                    .split(chunks[1])
                    .to_vec();
                
                match state.view_mode {
                    ViewMode::SideBySide => {
                        let diff_widgets = render_side_by_side_diff(&state, diff_area[0], &theme);
                        let diff_chunks = Layout::default()
                            .direction(ratatui::layout::Direction::Horizontal)
                            .constraints([
                                Constraint::Percentage(50),
                                Constraint::Percentage(50),
                            ])
                            .split(diff_area[0])
                            .to_vec();
                        
                        if diff_widgets.len() >= 2 {
                            frame.render_widget(diff_widgets[0].clone(), diff_chunks[0]);
                            frame.render_widget(diff_widgets[1].clone(), diff_chunks[1]);
                        }
                    }
                    ViewMode::Unified => {
                        let diff_widget = render_unified_diff(&state, diff_area[0], &theme);
                        frame.render_widget(diff_widget, diff_area[0]);
                    }
                }
                
                // Summary
                let summary = render_summary(&state, &theme);
                frame.render_widget(summary, diff_area[1]);
            }
            
            // Footer
            let footer = render_footer(&theme, state.view_mode);
            frame.render_widget(footer, chunks[2]);
        })?;
        
        // Handle events
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            match event {
                Event::Key(key_event) => {
                    if key_event.code == KeyCode::Char('q') || key_event.code == KeyCode::Esc {
                        break;
                    } else if key_event.code == KeyCode::Right || key_event.code == KeyCode::Char('n') {
                        state.next_hunk();
                    } else if key_event.code == KeyCode::Left || key_event.code == KeyCode::Char('p') {
                        state.previous_hunk();
                    } else if key_event.code == KeyCode::Char('t') || key_event.code == KeyCode::Char('T') {
                        state.toggle_view_mode();
                    } else if key_event.code == KeyCode::Char('c') || key_event.code == KeyCode::Char('C') {
                        state.toggle_hunk_collapse(state.selected_hunk);
                    } else if key_event.code == KeyCode::Char('f') || key_event.code == KeyCode::Char('F') {
                        state.show_file_tree = !state.show_file_tree;
                    } else if state.show_file_tree {
                        // File tree navigation
                        let files = state.get_file_list();
                        if key_event.code == KeyCode::Down || key_event.code == KeyCode::Char('j') {
                            file_tree_index = (file_tree_index + 1) % files.len().max(1);
                            if file_tree_index < files.len() {
                                state.select_file(&files[file_tree_index]);
                            }
                        } else if key_event.code == KeyCode::Up || key_event.code == KeyCode::Char('k') {
                            file_tree_index = if file_tree_index == 0 {
                                files.len().saturating_sub(1)
                            } else {
                                file_tree_index - 1
                            };
                            if file_tree_index < files.len() {
                                state.select_file(&files[file_tree_index]);
                            }
                        } else if key_event.code == KeyCode::Enter {
                            if file_tree_index < files.len() {
                                state.select_file(&files[file_tree_index]);
                            }
                        }
                    }
                }
                _ => {}
            }
        }
    }
    
    Ok(())
}

