//! Spreadsheet command handler
//!
//! Handles spreadsheet TUI commands for editing building data

use crate::cli::SpreadsheetCommands;
use crate::persistence::PersistenceManager;
use crate::tui::spreadsheet::clipboard::Clipboard;
use crate::tui::spreadsheet::data_source::{
    EquipmentDataSource, RoomDataSource, SensorDataSource, SpreadsheetDataSource,
};
use crate::tui::spreadsheet::editor::{CellEditor, EditorAction};
use crate::tui::spreadsheet::export;
use crate::tui::spreadsheet::filter_sort;
use crate::tui::spreadsheet::import;
use crate::tui::spreadsheet::navigation;
use crate::tui::spreadsheet::render;
use crate::tui::spreadsheet::save_state::AutoSaveManager;
use crate::tui::spreadsheet::search::SearchState;
use crate::tui::spreadsheet::types::{CellValue, Grid};
use crate::tui::spreadsheet::undo_redo::UndoRedoManager;
use crate::tui::spreadsheet::validation::validate_cell;
use crate::tui::spreadsheet::workflow::ConflictDetector;
use crate::tui::spreadsheet::workflow::{ArScanWatcher, FileLock, WorkflowStatus};
use crate::tui::{TerminalManager, Theme};
use crossterm::event::{Event, KeyCode};
use log::{info, warn};
use std::time::{Duration, Instant};

/// Handle spreadsheet command
pub fn handle_spreadsheet_command(
    subcommand: SpreadsheetCommands,
) -> Result<(), Box<dyn std::error::Error>> {
    match subcommand {
        SpreadsheetCommands::Equipment {
            building,
            filter,
            commit,
            no_git,
        } => handle_spreadsheet_equipment(building, filter, commit, no_git),
        SpreadsheetCommands::Rooms {
            building,
            filter,
            commit,
            no_git,
        } => handle_spreadsheet_rooms(building, filter, commit, no_git),
        SpreadsheetCommands::Sensors {
            building,
            filter,
            commit,
            no_git,
        } => handle_spreadsheet_sensors(building, filter, commit, no_git),
        SpreadsheetCommands::Import {
            file,
            building,
            commit,
        } => handle_spreadsheet_import(file, building, commit),
    }
}

/// Handle equipment spreadsheet
fn handle_spreadsheet_equipment(
    building: Option<String>,
    filter: Option<String>,
    _commit: bool,
    _no_git: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    // Determine building name
    let building_name = building.unwrap_or_else(|| {
        // Default to current directory name or first building found
        "Building".to_string()
    });

    info!(
        "Opening equipment spreadsheet for building: {}",
        building_name
    );

    // Load building data
    let persistence = PersistenceManager::new(&building_name)?;
    let building_data = persistence.load_building_data()?;

    // Acquire file lock
    let building_file = persistence.working_file();
    let file_lock = FileLock::acquire(building_file)?;

    // Initialize conflict detector
    let mut conflict_detector = ConflictDetector::new(building_file)?;

    // Check for active workflows
    let workflow_status = WorkflowStatus::detect();
    if workflow_status.has_active_workflows() {
        for warning in workflow_status.warnings() {
            warn!("{}", warning);
        }
    }

    // Initialize data source
    let mut data_source = EquipmentDataSource::new(building_data, building_name.clone());
    let columns = SpreadsheetDataSource::columns(&data_source);
    let row_count = SpreadsheetDataSource::row_count(&data_source);

    // Create grid
    let mut grid = Grid::new(columns, row_count);

    // Populate grid with data
    for row in 0..row_count {
        for col in 0..grid.column_count() {
            if let Ok(cell_value) = data_source.get_cell(row, col) {
                if let Some(cell) = grid.get_cell_mut(row, col) {
                    cell.value = cell_value;
                }
            }
        }
    }

    // Apply CLI filter if provided
    if let Some(filter_str) = filter {
        // Find address column (first column should be address)
        if let Some(addr_col_idx) = grid.columns.iter().position(|c| c.id.contains("address")) {
            // Check if filter contains glob patterns
            let condition = if filter_str.contains('*') || filter_str.contains('?') {
                // Glob pattern
                crate::tui::spreadsheet::types::FilterCondition::Glob(filter_str.clone())
            } else {
                // Simple contains match
                crate::tui::spreadsheet::types::FilterCondition::Contains(filter_str.clone())
            };

            filter_sort::apply_filter(&mut grid, addr_col_idx, condition)?;
            info!(
                "Applied filter: {} ({} rows visible)",
                filter_str,
                grid.row_count()
            );
        } else {
            warn!("Address column not found, filter not applied");
        }
    }

    // Initialize AR scan watcher
    let mut ar_watcher = ArScanWatcher::new(&building_name)?;

    // Initialize TUI
    let mut terminal_manager = TerminalManager::new()?;
    let theme = Theme::from_config();

    // Main event loop
    let mut should_quit = false;
    let mut editor: Option<CellEditor> = None;
    let mut ar_scan_count = 0;
    let mut undo_redo = UndoRedoManager::new(50); // Last 50 operations
                                                  // Use longer debounce if watch mode is active to prevent excessive sync cycles
    let debounce_ms = if workflow_status.watch_mode_active || workflow_status.sync_active {
        2000 // 2 seconds for watch mode
    } else {
        500 // 500ms normal
    };
    let mut auto_save = AutoSaveManager::new(debounce_ms);
    let mut last_auto_save_check = Instant::now();
    let mut clipboard = Clipboard::new();
    let mut search_state: Option<SearchState> = None;

    while !should_quit {
        // Ensure selection is visible before rendering
        let terminal_size = terminal_manager.terminal().size()?;
        let visible_rows = (terminal_size.height.saturating_sub(5)) as usize;
        let visible_cols = (terminal_size.width.saturating_sub(2)) as usize;
        grid.ensure_selection_visible(visible_rows, visible_cols);

        // Render
        terminal_manager.terminal().draw(|frame| {
            let size = frame.size();
            let mut context =
                render::SpreadsheetRenderContext::new(size, &grid, &theme, &workflow_status);
            context.editor = editor.as_ref();
            context.save_state = Some(auto_save.state());
            context.search_state = search_state.as_ref();
            context.ar_scan_count = (ar_scan_count > 0).then_some(ar_scan_count);

            render::render_spreadsheet_with_editor_save_search_ar(frame, context);
        })?;

        // Handle events
        if let Some(Event::Key(key)) = terminal_manager.poll_event(Duration::from_millis(100))? {
            // If editing, handle editor events
            if let Some(ref mut ed) = editor {
                match ed.handle_key(key) {
                    EditorAction::Continue => {
                        // Continue editing
                    }
                    EditorAction::ValidateAndApply => {
                        // Validate and apply
                        let column = &grid.columns[grid.selected_col];
                        match validate_cell(ed.get_current_value(), column) {
                            Ok(cell_value) => {
                                // Get old value for undo
                                let old_value = grid
                                    .get_cell(grid.selected_row, grid.selected_col)
                                    .map(|c| c.value.clone())
                                    .unwrap_or(crate::tui::spreadsheet::types::CellValue::Empty);

                                // Record operation for undo
                                undo_redo.record_operation(
                                    grid.selected_row,
                                    grid.selected_col,
                                    old_value.clone(),
                                    cell_value.clone(),
                                );

                                // Apply change
                                if let Some(cell) =
                                    grid.get_cell_mut(grid.selected_row, grid.selected_col)
                                {
                                    cell.value = cell_value.clone();
                                    cell.modified = true;
                                    cell.error = None;
                                }

                                // Update data source
                                if let Err(e) = data_source.set_cell(
                                    grid.selected_row,
                                    grid.selected_col,
                                    cell_value,
                                ) {
                                    warn!("Failed to set cell: {}", e);
                                    if let Some(cell) =
                                        grid.get_cell_mut(grid.selected_row, grid.selected_col)
                                    {
                                        cell.error = Some(e.to_string());
                                    }
                                } else {
                                    // Trigger auto-save on successful edit
                                    auto_save.trigger_save();
                                }

                                // Exit edit mode
                                grid.editing_cell = None;
                                editor = None;

                                // Move to next cell
                                grid.move_down();
                            }
                            Err(e) => {
                                // Show validation error
                                if let Some(cell) =
                                    grid.get_cell_mut(grid.selected_row, grid.selected_col)
                                {
                                    cell.error = Some(e.message.clone());
                                }
                                ed.state =
                                    crate::tui::spreadsheet::editor::EditState::Error(e.message);
                            }
                        }
                    }
                    EditorAction::Cancel => {
                        // Cancel edit
                        grid.editing_cell = None;
                        editor = None;
                    }
                }
            } else {
                // Not editing - handle navigation and commands
                match key.code {
                    KeyCode::Char('q') | KeyCode::Char('Q') => {
                        should_quit = true;
                    }
                    KeyCode::Esc => {
                        // Esc: Close address modal first, then cancel search, then quit
                        if grid.address_modal.is_some() {
                            grid.address_modal = None;
                        } else if search_state.as_ref().map(|s| s.is_active).unwrap_or(false) {
                            if let Some(ref mut search) = search_state {
                                search.deactivate();
                                info!("Search cancelled");
                            }
                        } else {
                            should_quit = true;
                        }
                    }
                    KeyCode::Char('?') | KeyCode::F(1) => {
                        // Help is shown in status bar
                    }
                    KeyCode::Enter
                        if search_state.as_ref().map(|s| s.is_active).unwrap_or(false) =>
                    {
                        // Enter: Apply search and exit search mode (check this BEFORE general Enter handler)
                        if let Some(ref mut search) = search_state {
                            search.find_matches(&grid, &data_source as &dyn SpreadsheetDataSource);
                            if let Some((row, col)) = search.current_match {
                                grid.selected_row = row;
                                grid.selected_col = col;
                                grid.ensure_selection_visible(visible_rows, visible_cols);
                            }
                            search.deactivate();
                        }
                    }
                    KeyCode::Enter | KeyCode::F(2) => {
                        // Enter: Show address modal if on address column, otherwise enter edit mode
                        let column = &grid.columns[grid.selected_col];

                        // Check if this is the address column (read-only)
                        if column.id.contains("address") && !column.editable {
                            // Show address modal
                            if let Some(cell) = grid.get_cell(grid.selected_row, grid.selected_col)
                            {
                                let full_path = cell.value.to_string();
                                if !full_path.is_empty() && full_path != "No address" {
                                    grid.address_modal = Some(full_path);
                                }
                            }
                        } else if column.editable {
                            // Enter edit mode
                            let cell = grid
                                .get_cell(grid.selected_row, grid.selected_col)
                                .cloned()
                                .unwrap_or_else(|| {
                                    crate::tui::spreadsheet::types::Cell::new(
                                        crate::tui::spreadsheet::types::CellValue::Empty,
                                    )
                                });

                            // Note: Sensor locking is handled by the workflow integration system
                            // Status field editing is allowed here; sensor integration will enforce locking at the workflow layer
                            if column.id == "equipment.status" {
                                // Status field editing - sensor locking enforced by workflow system
                            }

                            let mut new_editor = CellEditor::new(column.clone(), cell.value);
                            new_editor.reset_cursor();
                            editor = Some(new_editor);
                            grid.editing_cell = Some((grid.selected_row, grid.selected_col));
                        }
                    }
                    KeyCode::Char('z')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+Z: Undo
                        undo_redo.undo(&mut grid);
                        auto_save.trigger_save();
                    }
                    KeyCode::Char('y')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+Y: Redo
                        undo_redo.redo(&mut grid);
                        auto_save.trigger_save();
                    }
                    KeyCode::Char('s')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL)
                            && !key
                                .modifiers
                                .contains(crossterm::event::KeyModifiers::SHIFT) =>
                    {
                        // Ctrl+S: Save (stage to Git)
                        if let Err(e) = perform_save(
                            &mut data_source,
                            &mut conflict_detector,
                            &mut auto_save,
                            false,
                        ) {
                            warn!("Save failed: {}", e);
                        }
                    }
                    KeyCode::Char('s')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL)
                            && key
                                .modifiers
                                .contains(crossterm::event::KeyModifiers::SHIFT) =>
                    {
                        // Ctrl+Shift+S: Save and commit
                        if let Err(e) = perform_save(
                            &mut data_source,
                            &mut conflict_detector,
                            &mut auto_save,
                            true,
                        ) {
                            warn!("Save and commit failed: {}", e);
                        }
                    }
                    KeyCode::Char('r')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+R: Reload
                        if auto_save.has_unsaved_changes() {
                            warn!("Unsaved changes will be lost. Reloading...");
                        }
                        if let Err(e) = perform_reload(
                            &mut data_source,
                            &mut conflict_detector,
                            &mut grid,
                            &mut auto_save,
                            row_count,
                        ) {
                            warn!("Reload failed: {}", e);
                        }
                    }
                    KeyCode::Char('e')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+E: Export to CSV
                        if let Err(e) = perform_export(&grid, &data_source) {
                            warn!("Export failed: {}", e);
                        }
                    }
                    KeyCode::Char('o')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+O: Import CSV
                        warn!("CSV import requires file path. Use: arx spreadsheet import --file <path>");
                    }
                    KeyCode::Char('f')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+F: Activate search
                        if search_state.is_none() {
                            search_state = Some(SearchState::new(String::new(), false));
                        }
                        if let Some(ref mut search) = search_state {
                            search.activate();
                            info!(
                                "Search activated - Type to search, Esc to cancel, n/p to navigate"
                            );
                        }
                    }
                    KeyCode::Char('n')
                        if search_state.as_ref().map(|s| s.is_active).unwrap_or(false) =>
                    {
                        // n: Next match (when in search mode)
                        if let Some(ref mut search) = search_state {
                            if let Some((row, col)) = search.next_match() {
                                grid.selected_row = row;
                                grid.selected_col = col;
                                grid.ensure_selection_visible(visible_rows, visible_cols);
                            }
                        }
                    }
                    KeyCode::Char('p')
                        if search_state.as_ref().map(|s| s.is_active).unwrap_or(false) =>
                    {
                        // p: Previous match (when in search mode)
                        if let Some(ref mut search) = search_state {
                            if let Some((row, col)) = search.previous_match() {
                                grid.selected_row = row;
                                grid.selected_col = col;
                                grid.ensure_selection_visible(visible_rows, visible_cols);
                            }
                        }
                    }
                    KeyCode::Char(c)
                        if search_state.as_ref().map(|s| s.is_active).unwrap_or(false)
                            && !key
                                .modifiers
                                .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Typing in search mode (but not Ctrl+key combinations)
                        if let Some(ref mut search) = search_state {
                            search.update_query(format!("{}{}", search.query, c));
                            search.find_matches(&grid, &data_source as &dyn SpreadsheetDataSource);
                            if let Some((row, col)) = search.current_match {
                                grid.selected_row = row;
                                grid.selected_col = col;
                                grid.ensure_selection_visible(visible_rows, visible_cols);
                            }
                        }
                    }
                    KeyCode::Backspace
                        if search_state.as_ref().map(|s| s.is_active).unwrap_or(false) =>
                    {
                        // Backspace in search mode
                        if let Some(ref mut search) = search_state {
                            let mut query = search.query.clone();
                            query.pop();
                            search.update_query(query);
                            search.find_matches(&grid, &data_source as &dyn SpreadsheetDataSource);
                            if let Some((row, col)) = search.current_match {
                                grid.selected_row = row;
                                grid.selected_col = col;
                                grid.ensure_selection_visible(visible_rows, visible_cols);
                            }
                        }
                    }
                    KeyCode::Char('c')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+C: Copy selected cell
                        if let Some(cell) = grid.get_cell(grid.selected_row, grid.selected_col) {
                            clipboard.copy_cell(cell.value.clone());
                            info!("Cell copied");
                        }
                    }
                    KeyCode::Char('v')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+V: Paste into selected cell
                        if let Some(cell_value) = clipboard.get_cell(0, 0) {
                            let column = &grid.columns[grid.selected_col];
                            if column.editable {
                                match validate_cell(&cell_value.to_string(), column) {
                                    Ok(valid_value) => {
                                        let old_value = grid
                                            .get_cell(grid.selected_row, grid.selected_col)
                                            .map(|c| c.value.clone())
                                            .unwrap_or(CellValue::Empty);

                                        undo_redo.record_operation(
                                            grid.selected_row,
                                            grid.selected_col,
                                            old_value.clone(),
                                            valid_value.clone(),
                                        );

                                        if let Some(cell) =
                                            grid.get_cell_mut(grid.selected_row, grid.selected_col)
                                        {
                                            cell.value = valid_value.clone();
                                            cell.modified = true;
                                            cell.error = None;
                                        }

                                        if let Err(e) = data_source.set_cell(
                                            grid.selected_row,
                                            grid.selected_col,
                                            valid_value,
                                        ) {
                                            warn!("Failed to set cell: {}", e);
                                        } else {
                                            auto_save.trigger_save();
                                        }
                                    }
                                    Err(e) => {
                                        if let Some(cell) =
                                            grid.get_cell_mut(grid.selected_row, grid.selected_col)
                                        {
                                            cell.error = Some(e.message.clone());
                                        }
                                    }
                                }
                            }
                        }
                    }
                    KeyCode::Char('u')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+U: Clear filters
                        filter_sort::clear_filters(&mut grid);
                        info!("Filters cleared");
                    }
                    KeyCode::Char('a')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        // Ctrl+A: Toggle address column visibility
                        // Find address column (should be first column)
                        if let Some(addr_col_idx) =
                            grid.columns.iter().position(|c| c.id.contains("address"))
                        {
                            grid.toggle_column_visibility(addr_col_idx);
                            let is_visible = grid.is_column_visible(addr_col_idx);
                            info!(
                                "Address column {}",
                                if is_visible { "shown" } else { "hidden" }
                            );
                        }
                    }
                    _ => {
                        // Handle navigation (only if not in search mode)
                        if !search_state.as_ref().map(|s| s.is_active).unwrap_or(false) {
                            navigation::handle_navigation(key, &mut grid);
                        }
                    }
                }
            }
        }

        // Check for new AR scans
        if let Ok(new_scans) = ar_watcher.check_new_scans() {
            if new_scans > 0 {
                ar_scan_count += new_scans;
                info!("AR: {} new scan(s) detected, reload to refresh", new_scans);
                // Optionally auto-reload
                if let Err(e) = perform_reload(
                    &mut data_source,
                    &mut conflict_detector,
                    &mut grid,
                    &mut auto_save,
                    row_count,
                ) {
                    warn!("Auto-reload after AR scan failed: {}", e);
                } else {
                    // Re-populate grid after reload
                    let new_row_count = SpreadsheetDataSource::row_count(&data_source);
                    for row in 0..new_row_count.min(grid.row_count()) {
                        for col in 0..grid.column_count() {
                            if let Ok(cell_value) = data_source.get_cell(row, col) {
                                if let Some(cell) = grid.get_cell_mut(row, col) {
                                    cell.value = cell_value;
                                }
                            }
                        }
                    }
                }
            }
        }

        // Check for auto-save
        if auto_save.should_save()
            && auto_save.has_unsaved_changes()
            && last_auto_save_check.elapsed() >= Duration::from_millis(100)
        {
            // Check for conflicts before auto-saving
            match conflict_detector.check_conflict() {
                Ok(true) => {
                    // Conflict detected - don't auto-save, show warning
                    warn!("External changes detected. Auto-save skipped. Press Ctrl+R to reload or Ctrl+S to save.");
                    auto_save.set_error("External changes detected".to_string());
                }
                Ok(false) => {
                    // No conflict - proceed with auto-save
                    if let Err(e) = perform_save(
                        &mut data_source,
                        &mut conflict_detector,
                        &mut auto_save,
                        false,
                    ) {
                        warn!("Auto-save failed: {}", e);
                    }
                }
                Err(e) => {
                    warn!("Conflict check failed: {}", e);
                    auto_save.set_error("Conflict check failed".to_string());
                }
            }
            last_auto_save_check = Instant::now();
        }
    }

    // Check for unsaved changes before quitting
    if auto_save.has_unsaved_changes() {
        info!("Exiting with unsaved changes");
    }

    // Release file lock
    file_lock.release()?;

    info!("Spreadsheet closed");
    Ok(())
}

/// Perform save operation (generic for any data source)
fn perform_save(
    data_source: &mut dyn SpreadsheetDataSource,
    conflict_detector: &mut ConflictDetector,
    auto_save: &mut AutoSaveManager,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    // Check for conflicts before saving
    if conflict_detector.check_conflict()? {
        return Err("External changes detected. Please reload before saving.".into());
    }

    auto_save.set_saving();

    // Perform save
    match data_source.save(commit) {
        Ok(()) => {
            auto_save.set_saved();
            conflict_detector.update()?; // Update modification time after save
            info!("Save successful (commit: {})", commit);
            Ok(())
        }
        Err(e) => {
            auto_save.set_error(e.to_string());
            Err(e)
        }
    }
}

/// Perform reload operation (generic for any data source)
fn perform_reload(
    data_source: &mut dyn SpreadsheetDataSource,
    conflict_detector: &mut ConflictDetector,
    grid: &mut Grid,
    auto_save: &mut AutoSaveManager,
    row_count: usize,
) -> Result<(), Box<dyn std::error::Error>> {
    // Reload from data source
    data_source.reload()?;

    // Reload grid data
    for row in 0..row_count.min(grid.row_count()) {
        for col in 0..grid.column_count() {
            if let Ok(cell_value) = data_source.get_cell(row, col) {
                if let Some(cell) = grid.get_cell_mut(row, col) {
                    cell.value = cell_value;
                    cell.modified = false;
                    cell.error = None;
                }
            }
        }
    }

    // Update conflict detector
    conflict_detector.update()?;

    // Mark as clean
    auto_save.set_clean();

    info!("Reload successful");
    Ok(())
}

/// Perform CSV export (generic for any data source)
fn perform_export(
    grid: &Grid,
    _data_source: &dyn SpreadsheetDataSource,
) -> Result<(), Box<dyn std::error::Error>> {
    use std::path::PathBuf;
    use std::time::SystemTime;

    // Generate default filename with timestamp
    let timestamp = SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .expect("System time should be after UNIX epoch")
        .as_secs();
    let filename = format!("equipment_export_{}.csv", timestamp);
    let file_path = PathBuf::from(&filename);

    // Collect all rows from grid
    let mut rows = Vec::new();
    for row_idx in 0..grid.row_count() {
        let mut row = Vec::new();
        for col_idx in 0..grid.column_count() {
            let cell_value = grid
                .get_cell(row_idx, col_idx)
                .map(|c| c.value.clone())
                .unwrap_or(CellValue::Empty);
            row.push(cell_value);
        }
        rows.push(row);
    }

    // Export to CSV
    export::export_to_csv(&file_path, &grid.columns, &rows)?;

    info!("Exported {} rows to {}", rows.len(), file_path.display());
    Ok(())
}

/// Handle room spreadsheet
fn handle_spreadsheet_rooms(
    building: Option<String>,
    _filter: Option<String>,
    _commit: bool,
    _no_git: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let building_name = building.unwrap_or_else(|| "Building".to_string());

    info!("Opening room spreadsheet for building: {}", building_name);

    // Load building data
    let persistence = PersistenceManager::new(&building_name)?;
    let building_data = persistence.load_building_data()?;

    // Acquire file lock
    let building_file = persistence.working_file();
    let file_lock = FileLock::acquire(building_file)?;

    // Initialize conflict detector
    let mut conflict_detector = ConflictDetector::new(building_file)?;

    // Check for active workflows
    let workflow_status = WorkflowStatus::detect();
    if workflow_status.has_active_workflows() {
        for warning in workflow_status.warnings() {
            warn!("{}", warning);
        }
    }

    // Initialize data source
    let mut data_source = RoomDataSource::new(building_data, building_name.clone());
    let columns = SpreadsheetDataSource::columns(&data_source);
    let row_count = SpreadsheetDataSource::row_count(&data_source);

    // Create grid
    let mut grid = Grid::new(columns, row_count);

    // Populate grid with data
    for row in 0..row_count {
        for col in 0..grid.column_count() {
            if let Ok(cell_value) = data_source.get_cell(row, col) {
                if let Some(cell) = grid.get_cell_mut(row, col) {
                    cell.value = cell_value;
                }
            }
        }
    }

    // Initialize TUI
    let mut terminal_manager = TerminalManager::new()?;
    let theme = Theme::from_config();

    // Main event loop (same as equipment, but with RoomDataSource)
    let mut should_quit = false;
    let mut editor: Option<CellEditor> = None;
    let mut undo_redo = UndoRedoManager::new(50);
    let debounce_ms = if workflow_status.watch_mode_active || workflow_status.sync_active {
        2000
    } else {
        500
    };
    let mut auto_save = AutoSaveManager::new(debounce_ms);
    let mut last_auto_save_check = Instant::now();
    let _clipboard = Clipboard::new();

    while !should_quit {
        let terminal_size = terminal_manager.terminal().size()?;
        let visible_rows = (terminal_size.height.saturating_sub(5)) as usize;
        let visible_cols = (terminal_size.width.saturating_sub(2)) as usize;
        grid.ensure_selection_visible(visible_rows, visible_cols);

        terminal_manager.terminal().draw(|frame| {
            let size = frame.size();
            render::render_spreadsheet_with_editor_and_save(
                frame,
                size,
                &grid,
                &theme,
                &workflow_status,
                editor.as_ref(),
                Some(auto_save.state()),
            );
        })?;

        if let Some(Event::Key(key)) = terminal_manager.poll_event(Duration::from_millis(100))? {
            if let Some(ref mut ed) = editor {
                match ed.handle_key(key) {
                    EditorAction::Continue => {}
                    EditorAction::ValidateAndApply => {
                        let column = &grid.columns[grid.selected_col];
                        match validate_cell(ed.get_current_value(), column) {
                            Ok(cell_value) => {
                                let old_value = grid
                                    .get_cell(grid.selected_row, grid.selected_col)
                                    .map(|c| c.value.clone())
                                    .unwrap_or(CellValue::Empty);

                                undo_redo.record_operation(
                                    grid.selected_row,
                                    grid.selected_col,
                                    old_value.clone(),
                                    cell_value.clone(),
                                );

                                if let Some(cell) =
                                    grid.get_cell_mut(grid.selected_row, grid.selected_col)
                                {
                                    cell.value = cell_value.clone();
                                    cell.modified = true;
                                    cell.error = None;
                                }

                                if let Err(e) = data_source.set_cell(
                                    grid.selected_row,
                                    grid.selected_col,
                                    cell_value,
                                ) {
                                    warn!("Failed to set cell: {}", e);
                                } else {
                                    auto_save.trigger_save();
                                }

                                grid.editing_cell = None;
                                editor = None;
                                grid.move_down();
                            }
                            Err(e) => {
                                if let Some(cell) =
                                    grid.get_cell_mut(grid.selected_row, grid.selected_col)
                                {
                                    cell.error = Some(e.message.clone());
                                }
                                ed.state =
                                    crate::tui::spreadsheet::editor::EditState::Error(e.message);
                            }
                        }
                    }
                    EditorAction::Cancel => {
                        grid.editing_cell = None;
                        editor = None;
                    }
                }
            } else {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Char('Q') | KeyCode::Esc => {
                        should_quit = true;
                    }
                    KeyCode::Enter | KeyCode::F(2) => {
                        let column = &grid.columns[grid.selected_col];
                        if column.editable {
                            let cell = grid
                                .get_cell(grid.selected_row, grid.selected_col)
                                .cloned()
                                .unwrap_or_else(|| {
                                    crate::tui::spreadsheet::types::Cell::new(
                                        crate::tui::spreadsheet::types::CellValue::Empty,
                                    )
                                });
                            let mut new_editor = CellEditor::new(column.clone(), cell.value);
                            new_editor.reset_cursor();
                            editor = Some(new_editor);
                            grid.editing_cell = Some((grid.selected_row, grid.selected_col));
                        }
                    }
                    KeyCode::Char('z')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        undo_redo.undo(&mut grid);
                        auto_save.trigger_save();
                    }
                    KeyCode::Char('y')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        undo_redo.redo(&mut grid);
                        auto_save.trigger_save();
                    }
                    KeyCode::Char('s')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL)
                            && !key
                                .modifiers
                                .contains(crossterm::event::KeyModifiers::SHIFT) =>
                    {
                        if let Err(e) = perform_save(
                            &mut data_source,
                            &mut conflict_detector,
                            &mut auto_save,
                            false,
                        ) {
                            warn!("Save failed: {}", e);
                        }
                    }
                    KeyCode::Char('s')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL)
                            && key
                                .modifiers
                                .contains(crossterm::event::KeyModifiers::SHIFT) =>
                    {
                        if let Err(e) = perform_save(
                            &mut data_source,
                            &mut conflict_detector,
                            &mut auto_save,
                            true,
                        ) {
                            warn!("Save and commit failed: {}", e);
                        }
                    }
                    KeyCode::Char('r')
                        if key
                            .modifiers
                            .contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        if auto_save.has_unsaved_changes() {
                            warn!("Unsaved changes will be lost. Reloading...");
                        }
                        if let Err(e) = perform_reload(
                            &mut data_source,
                            &mut conflict_detector,
                            &mut grid,
                            &mut auto_save,
                            row_count,
                        ) {
                            warn!("Reload failed: {}", e);
                        }
                    }
                    _ => {
                        navigation::handle_navigation(key, &mut grid);
                    }
                }
            }
        }

        if auto_save.should_save()
            && auto_save.has_unsaved_changes()
            && last_auto_save_check.elapsed() >= Duration::from_millis(100)
        {
            match conflict_detector.check_conflict() {
                Ok(true) => {
                    warn!("External changes detected. Auto-save skipped.");
                    auto_save.set_error("External changes detected".to_string());
                }
                Ok(false) => {
                    if let Err(e) = perform_save(
                        &mut data_source,
                        &mut conflict_detector,
                        &mut auto_save,
                        false,
                    ) {
                        warn!("Auto-save failed: {}", e);
                    }
                }
                Err(e) => {
                    warn!("Conflict check failed: {}", e);
                    auto_save.set_error("Conflict check failed".to_string());
                }
            }
            last_auto_save_check = Instant::now();
        }
    }

    if auto_save.has_unsaved_changes() {
        info!("Exiting with unsaved changes");
    }

    file_lock.release()?;
    info!("Room spreadsheet closed");
    Ok(())
}

/// Handle sensor spreadsheet
fn handle_spreadsheet_sensors(
    building: Option<String>,
    _filter: Option<String>,
    _commit: bool,
    _no_git: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let building_name = building.unwrap_or_else(|| "Building".to_string());

    info!("Opening sensor spreadsheet for building: {}", building_name);

    // Acquire file lock (read-only for sensors)
    let persistence = PersistenceManager::new(&building_name)?;
    let building_file = persistence.working_file();
    let file_lock = FileLock::acquire(building_file)?;

    // Initialize conflict detector
    let _conflict_detector = ConflictDetector::new(building_file)?;

    // Check for active workflows
    let workflow_status = WorkflowStatus::detect();

    // Initialize data source
    let mut data_source = SensorDataSource::new(building_name.clone());
    data_source.load_sensor_data()?;
    let columns = SpreadsheetDataSource::columns(&data_source);
    let row_count = SpreadsheetDataSource::row_count(&data_source);

    // Create grid
    let mut grid = Grid::new(columns, row_count);

    // Populate grid with data
    for row in 0..row_count {
        for col in 0..grid.column_count() {
            if let Ok(cell_value) = data_source.get_cell(row, col) {
                if let Some(cell) = grid.get_cell_mut(row, col) {
                    cell.value = cell_value;
                }
            }
        }
    }

    // Initialize TUI
    let mut terminal_manager = TerminalManager::new()?;
    let theme = Theme::from_config();

    // Main event loop (read-only for sensors)
    let mut should_quit = false;

    while !should_quit {
        let terminal_size = terminal_manager.terminal().size()?;
        let visible_rows = (terminal_size.height.saturating_sub(5)) as usize;
        let visible_cols = (terminal_size.width.saturating_sub(2)) as usize;
        grid.ensure_selection_visible(visible_rows, visible_cols);

        terminal_manager.terminal().draw(|frame| {
            let size = frame.size();
            render::render_spreadsheet_with_editor_and_save(
                frame,
                size,
                &grid,
                &theme,
                &workflow_status,
                None,
                None,
            );
        })?;

        if let Some(Event::Key(key)) = terminal_manager.poll_event(Duration::from_millis(100))? {
            match key.code {
                KeyCode::Char('q') | KeyCode::Char('Q') | KeyCode::Esc => {
                    should_quit = true;
                }
                KeyCode::Char('r')
                    if key
                        .modifiers
                        .contains(crossterm::event::KeyModifiers::CONTROL) =>
                {
                    // Reload sensor data
                    if let Err(e) = data_source.reload() {
                        warn!("Reload failed: {}", e);
                    } else {
                        // Rebuild grid
                        let row_count = SpreadsheetDataSource::row_count(&data_source);
                        let columns = SpreadsheetDataSource::columns(&data_source);
                        grid = Grid::new(columns, row_count);
                        for row in 0..row_count {
                            for col in 0..grid.column_count() {
                                if let Ok(cell_value) = data_source.get_cell(row, col) {
                                    if let Some(cell) = grid.get_cell_mut(row, col) {
                                        cell.value = cell_value;
                                    }
                                }
                            }
                        }
                    }
                }
                _ => {
                    navigation::handle_navigation(key, &mut grid);
                }
            }
        }
    }

    file_lock.release()?;
    info!("Sensor spreadsheet closed");
    Ok(())
}

/// Handle CSV import
fn handle_spreadsheet_import(
    file: String,
    building: Option<String>,
    commit: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use std::path::PathBuf;

    let building_name = building.unwrap_or_else(|| "Building".to_string());
    let file_path = PathBuf::from(&file);

    if !file_path.exists() {
        return Err(format!("CSV file not found: {}", file).into());
    }

    info!("Importing CSV from: {}", file_path.display());

    // Load building data
    let persistence = PersistenceManager::new(&building_name)?;
    let building_data = persistence.load_building_data()?;

    // Acquire file lock
    let building_file = persistence.working_file();
    let file_lock = FileLock::acquire(building_file)?;

    // Initialize data source
    let mut data_source = EquipmentDataSource::new(building_data, building_name.clone());
    let columns = SpreadsheetDataSource::columns(&data_source);

    // Preview CSV first
    info!("Previewing CSV file...");
    let preview = import::preview_csv_file(&file_path, 5)?;
    info!(
        "CSV preview (first {} rows):",
        preview.len().saturating_sub(1)
    );
    for (idx, row) in preview.iter().enumerate() {
        if idx == 0 {
            info!("  Headers: {:?}", row);
        } else {
            info!("  Row {}: {:?}", idx, row);
        }
    }

    // Import CSV
    let import_result = import::import_csv_file(&file_path, &columns)?;

    if !import_result.errors.is_empty() {
        warn!(
            "Import completed with {} errors:",
            import_result.errors.len()
        );
        for error in &import_result.errors {
            warn!(
                "  Row {}, Column {}: {}",
                error.row, error.column, error.message
            );
        }
    }

    // Apply imported data to data source
    info!("Applying {} imported rows...", import_result.rows.len());
    for (row_idx, row) in import_result.rows.iter().enumerate() {
        for (col_idx, cell_value) in row.iter().enumerate() {
            if let Err(e) = data_source.set_cell(row_idx, col_idx, cell_value.clone()) {
                warn!(
                    "Failed to set cell at row {}, col {}: {}",
                    row_idx, col_idx, e
                );
            }
        }
    }

    // Save imported data
    info!("Saving imported data...");
    data_source.save(commit)?;

    // Release file lock
    file_lock.release()?;

    info!(
        "CSV import completed successfully. {} rows imported.",
        import_result.row_count
    );
    Ok(())
}
