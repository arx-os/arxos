//! Interactive two-column diff viewer for merge conflicts
//!
//! Displays "ours" vs "theirs" side-by-side with keyboard navigation
//! and conflict resolution actions.

use super::conflict::{Conflict, ConflictSection};
use super::resolver::{Resolution, ResolutionChoice};
use crossterm::event::{self, Event, KeyCode, KeyEvent};
use crossterm::terminal::{disable_raw_mode, enable_raw_mode};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::Line,
    widgets::{Block, Borders, List, ListItem, Paragraph, Wrap},
    Frame, Terminal,
};
use std::io;
use std::path::{Path, PathBuf};

/// Main merge viewer state
pub struct MergeViewer {
    conflicts: Vec<Conflict>,
    file_path: PathBuf,
    current_conflict: usize,
    scroll_offset: usize,
    resolutions: Vec<Resolution>,
    show_base: bool,
    show_help: bool,
    preview_mode: bool,
}

impl MergeViewer {
    /// Create a new merge viewer
    pub fn new(conflicts: &[Conflict], file_path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        Ok(Self {
            conflicts: conflicts.to_vec(),
            file_path: file_path.to_path_buf(),
            current_conflict: 0,
            scroll_offset: 0,
            resolutions: Vec::new(),
            show_base: false,
            show_help: false,
            preview_mode: false,
        })
    }

    /// Run the interactive viewer
    pub fn run(&mut self) -> Result<Vec<Resolution>, Box<dyn std::error::Error>> {
        enable_raw_mode()?;
        let stdout = io::stdout();
        let backend = CrosstermBackend::new(stdout);
        let mut terminal = Terminal::new(backend)?;

        terminal.clear()?;

        let result = self.run_loop(&mut terminal);

        disable_raw_mode()?;
        terminal.show_cursor()?;

        result
    }

    /// Main event loop
    fn run_loop(
        &mut self,
        terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    ) -> Result<Vec<Resolution>, Box<dyn std::error::Error>> {
        loop {
            terminal.draw(|f| self.render(f))?;

            if let Event::Key(key) = event::read()? {
                match self.handle_key(key) {
                    KeyAction::Continue => {}
                    KeyAction::SaveAndExit => break,
                    KeyAction::CancelAndExit => {
                        self.resolutions.clear();
                        break;
                    }
                }
            }
        }

        Ok(self.resolutions.clone())
    }

    /// Render the UI
    fn render(&self, f: &mut Frame) {
        let size = f.size();

        // Main layout: header, diff area, footer
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(3),  // Header
                Constraint::Min(0),     // Diff area
                Constraint::Length(3),  // Footer with help
            ])
            .split(size);

        // Render header
        self.render_header(f, chunks[0]);

        // Render diff area based on mode
        if self.preview_mode {
            self.render_preview(f, chunks[1]);
        } else if self.show_help {
            self.render_help(f, chunks[1]);
        } else {
            self.render_diff(f, chunks[1]);
        }

        // Render footer
        self.render_footer(f, chunks[2]);
    }

    /// Render header with file info and progress
    fn render_header(&self, f: &mut Frame, area: Rect) {
        let file_name = self
            .file_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");

        let resolved_count = self.resolutions.len();
        let total_count = self.conflicts.len();

        let header_text = format!(
            "{} | Conflict {}/{} | Resolved: {}/{}",
            file_name,
            self.current_conflict + 1,
            total_count,
            resolved_count,
            total_count
        );

        let header = Paragraph::new(header_text)
            .block(Block::default().borders(Borders::ALL).title("Merge Tool"))
            .alignment(Alignment::Left)
            .style(Style::default().fg(Color::Cyan));

        f.render_widget(header, area);
    }

    /// Render two-column diff view
    fn render_diff(&self, f: &mut Frame, area: Rect) {
        if self.conflicts.is_empty() {
            let msg = Paragraph::new("No conflicts to resolve")
                .style(Style::default().fg(Color::Green))
                .alignment(Alignment::Center);
            f.render_widget(msg, area);
            return;
        }

        let conflict = &self.conflicts[self.current_conflict];

        // Split into two columns
        let columns = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Percentage(50), Constraint::Percentage(50)])
            .split(area);

        // Render "ours" column
        self.render_section(
            f,
            columns[0],
            &conflict.sections.ours,
            "OURS",
            Color::Green,
        );

        // Render "theirs" column
        self.render_section(
            f,
            columns[1],
            &conflict.sections.theirs,
            "THEIRS",
            Color::Blue,
        );

        // If showing base, render it as overlay/popup
        if self.show_base {
            if let Some(ref base) = conflict.sections.base {
                self.render_base_popup(f, area, base);
            }
        }
    }

    /// Render a conflict section (ours or theirs)
    fn render_section(
        &self,
        f: &mut Frame,
        area: Rect,
        section: &ConflictSection,
        title: &str,
        color: Color,
    ) {
        // Check if this section is part of the resolution
        let is_selected = self.is_section_selected(title);

        let mut style = Style::default().fg(color);
        if is_selected {
            style = style.add_modifier(Modifier::BOLD);
        }

        // Create list items with line numbers
        let items: Vec<ListItem> = section
            .lines
            .iter()
            .enumerate()
            .skip(self.scroll_offset)
            .map(|(i, line)| {
                let line_num = format!("{:4} ", i + 1);
                let content = format!("{}{}", line_num, line);
                ListItem::new(content).style(style)
            })
            .collect();

        let block_title = if is_selected {
            format!("{} ({})", title, section.label)
        } else {
            format!("{} ({})", title, section.label)
        };

        let list = List::new(items).block(
            Block::default()
                .borders(Borders::ALL)
                .title(block_title)
                .border_style(style),
        );

        f.render_widget(list, area);
    }

    /// Check if a section is currently selected in the resolution
    fn is_section_selected(&self, section_name: &str) -> bool {
        if let Some(resolution) = self.resolutions.iter().find(|r| r.conflict_index == self.current_conflict) {
            match (section_name, resolution.choice) {
                ("OURS", ResolutionChoice::Ours) => true,
                ("THEIRS", ResolutionChoice::Theirs) => true,
                ("OURS" | "THEIRS", ResolutionChoice::Both | ResolutionChoice::BothReversed) => true,
                _ => false,
            }
        } else {
            false
        }
    }

    /// Render base version as popup overlay
    fn render_base_popup(&self, f: &mut Frame, area: Rect, base: &ConflictSection) {
        // Center popup
        let popup_width = (area.width * 80) / 100;
        let popup_height = (area.height * 80) / 100;
        let popup_x = (area.width - popup_width) / 2;
        let popup_y = (area.height - popup_height) / 2;

        let popup_area = Rect::new(popup_x, popup_y, popup_width, popup_height);

        // Render base section
        let items: Vec<ListItem> = base
            .lines
            .iter()
            .enumerate()
            .map(|(i, line)| {
                let content = format!("{:4} {}", i + 1, line);
                ListItem::new(content)
            })
            .collect();

        let list = List::new(items).block(
            Block::default()
                .borders(Borders::ALL)
                .title(format!("BASE ({}) - Press 'b' to close", base.label))
                .style(Style::default().fg(Color::Yellow)),
        );

        // Clear background
        f.render_widget(Block::default().style(Style::default().bg(Color::Black)), popup_area);
        f.render_widget(list, popup_area);
    }

    /// Render help overlay
    fn render_help(&self, f: &mut Frame, area: Rect) {
        let help_text = vec![
            "=== MERGE TOOL KEYBOARD SHORTCUTS ===",
            "",
            "Navigation:",
            "  n / j       - Next conflict",
            "  p / k       - Previous conflict",
            "  ↓ / ↑       - Scroll within conflict",
            "  g           - Go to first conflict",
            "  G           - Go to last conflict",
            "",
            "Resolution:",
            "  o           - Choose OURS (left)",
            "  t           - Choose THEIRS (right)",
            "  B           - Choose BOTH (ours + theirs)",
            "  R           - Choose BOTH REVERSED (theirs + ours)",
            "  s           - Skip this conflict",
            "",
            "View:",
            "  b           - Toggle BASE version popup",
            "  P           - Preview merged result",
            "",
            "Actions:",
            "  w           - Save and exit",
            "  q / Esc     - Cancel and exit",
            "  ?           - Toggle this help",
            "",
            "Press any key to close help...",
        ];

        let items: Vec<ListItem> = help_text
            .iter()
            .map(|line| ListItem::new(*line))
            .collect();

        let help = List::new(items).block(
            Block::default()
                .borders(Borders::ALL)
                .title("Help")
                .style(Style::default().fg(Color::Yellow)),
        );

        f.render_widget(help, area);
    }

    /// Render preview of merged content
    fn render_preview(&self, f: &mut Frame, area: Rect) {
        use super::resolver::ResolutionEngine;

        let engine = ResolutionEngine::new(self.conflicts.clone());
        // Note: In real implementation, we'd pass resolutions here
        let merged = engine.build_merged_content();

        let lines: Vec<Line> = merged.lines().map(|l| Line::from(l)).collect();

        let preview = Paragraph::new(lines)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Preview (Press 'P' to exit preview)"),
            )
            .wrap(Wrap { trim: false })
            .scroll((self.scroll_offset as u16, 0));

        f.render_widget(preview, area);
    }

    /// Render footer with action hints
    fn render_footer(&self, f: &mut Frame, area: Rect) {
        let footer_text = if self.preview_mode {
            "Preview Mode | P: Exit Preview | w: Save | q: Cancel"
        } else {
            "o: Ours | t: Theirs | B: Both | b: Base | ?: Help | w: Save | q: Cancel"
        };

        let footer = Paragraph::new(footer_text)
            .block(Block::default().borders(Borders::ALL))
            .style(Style::default().fg(Color::DarkGray))
            .alignment(Alignment::Center);

        f.render_widget(footer, area);
    }

    /// Handle keyboard input
    fn handle_key(&mut self, key: KeyEvent) -> KeyAction {
        if self.show_help {
            // Any key closes help
            self.show_help = false;
            return KeyAction::Continue;
        }

        if self.preview_mode {
            match key.code {
                KeyCode::Char('P') => self.preview_mode = false,
                KeyCode::Char('w') => return KeyAction::SaveAndExit,
                KeyCode::Char('q') | KeyCode::Esc => return KeyAction::CancelAndExit,
                KeyCode::Down => self.scroll_offset += 1,
                KeyCode::Up => self.scroll_offset = self.scroll_offset.saturating_sub(1),
                _ => {}
            }
            return KeyAction::Continue;
        }

        match key.code {
            // Navigation
            KeyCode::Char('n') | KeyCode::Char('j') => self.next_conflict(),
            KeyCode::Char('p') | KeyCode::Char('k') => self.prev_conflict(),
            KeyCode::Down => self.scroll_offset += 1,
            KeyCode::Up => self.scroll_offset = self.scroll_offset.saturating_sub(1),
            KeyCode::Char('g') => self.current_conflict = 0,
            KeyCode::Char('G') => self.current_conflict = self.conflicts.len().saturating_sub(1),

            // Resolution choices
            KeyCode::Char('o') => self.choose_ours(),
            KeyCode::Char('t') => self.choose_theirs(),
            KeyCode::Char('B') => self.choose_both(),
            KeyCode::Char('R') => self.choose_both_reversed(),
            KeyCode::Char('s') => self.skip_conflict(),

            // View controls
            KeyCode::Char('b') => self.show_base = !self.show_base,
            KeyCode::Char('P') => self.preview_mode = !self.preview_mode,
            KeyCode::Char('?') => self.show_help = !self.show_help,

            // Actions
            KeyCode::Char('w') => return KeyAction::SaveAndExit,
            KeyCode::Char('q') | KeyCode::Esc => return KeyAction::CancelAndExit,

            _ => {}
        }

        KeyAction::Continue
    }

    // Navigation methods
    fn next_conflict(&mut self) {
        if self.current_conflict < self.conflicts.len() - 1 {
            self.current_conflict += 1;
            self.scroll_offset = 0;
        }
    }

    fn prev_conflict(&mut self) {
        if self.current_conflict > 0 {
            self.current_conflict -= 1;
            self.scroll_offset = 0;
        }
    }

    // Resolution methods
    fn choose_ours(&mut self) {
        self.add_resolution(ResolutionChoice::Ours);
    }

    fn choose_theirs(&mut self) {
        self.add_resolution(ResolutionChoice::Theirs);
    }

    fn choose_both(&mut self) {
        self.add_resolution(ResolutionChoice::Both);
    }

    fn choose_both_reversed(&mut self) {
        self.add_resolution(ResolutionChoice::BothReversed);
    }

    fn skip_conflict(&mut self) {
        self.add_resolution(ResolutionChoice::Skip);
    }

    fn add_resolution(&mut self, choice: ResolutionChoice) {
        let resolution = Resolution {
            conflict_index: self.current_conflict,
            choice,
            custom_content: None,
        };

        // Remove existing resolution for this conflict if any
        self.resolutions
            .retain(|r| r.conflict_index != self.current_conflict);

        // Add new resolution
        self.resolutions.push(resolution);

        // Auto-advance to next conflict
        self.next_conflict();
    }
}

/// Action to take based on key press
enum KeyAction {
    Continue,
    SaveAndExit,
    CancelAndExit,
}
