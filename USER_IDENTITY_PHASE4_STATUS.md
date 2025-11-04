# User Identity Phase 4 - Development Status

## Current Phase: Phase 4 - Enhanced TUI Display

**Date:** Current session  
**Status:** In Progress - 2 compilation errors remaining

---

## What We've Been Doing

### Phase 4 Implementation: Enhanced TUI Display with User Attribution

Phase 4 focuses on creating interactive TUI interfaces for browsing users, viewing their activity, and displaying user attribution throughout the system.

### Completed Work

1. **Watch Dashboard Enhancement** (`src/commands/watch_dashboard.rs`)
   - ✅ Added user attribution to recent changes display
   - ✅ Integrated `UserRegistry` loading into dashboard state
   - ✅ Created `UserActivityItem` and `UserInfo` structs for display
   - ✅ Added `load_recent_changes()` method to fetch Git commits and resolve user info
   - ✅ Added "Activity" tab to watch dashboard
   - ✅ Modified Overview tab to display "Recent Changes" alongside "Recent Alerts"
   - ✅ Fixed `BuildingGitManager::new()` calls to use `&str` instead of `&Path`

2. **User Browser TUI** (`src/ui/users.rs`)
   - ✅ Created interactive user browser with list/detail view
   - ✅ Implemented `UserBrowserState` with filtering and organization grouping
   - ✅ Added `load_user_activity()` to fetch user-specific Git commits
   - ✅ Created render functions for:
     - User list with verification badges
     - User details panel (name, email, org, role, permissions, activity timestamps)
     - User activity timeline (recent commits)
     - Organization grouping view
   - ✅ Added CLI command integration (`arx users browse`)
   - ✅ Fixed `BuildingGitManager::new()` calls to use `&str` instead of `&Path`
   - ✅ Fixed `users` field to use `Vec<User>` instead of `&[User]`
   - ✅ Added lifetime annotations to render functions
   - ✅ Removed unused imports

---

## Remaining Issues

### Compilation Errors (2 remaining)

**File:** `src/ui/users.rs`

**Error 1 - Line 506:**
```
error[E0502]: cannot borrow `state.list_state` as mutable because it is also borrowed as immutable
```

**Location:** Inside the `frame.draw()` closure when calling `render_stateful_widget()`

**Error 2 - Line 483:**
```
error[E0502]: cannot borrow `state` as mutable because it is also borrowed as immutable
```

**Location:** Same area - borrow conflict in the render loop

### Root Cause

The issue is in `handle_user_browser()` function around line 486-506. The problem is:
1. `render_user_list(&state, ...)` borrows `state` immutably
2. Then `frame.render_stateful_widget(..., &mut state.list_state)` tries to borrow `state.list_state` mutably
3. Rust prevents this because `state` is already borrowed immutably

### Solution Pattern

Looking at similar code in the codebase (`src/commands/search_browser.rs`, `src/commands/ar_pending_manager.rs`), the pattern is:

1. **Extract data before the closure:** Get all needed data from `state` before entering the `draw()` closure
2. **Use separate variables:** Clone or extract values that don't need to be mutable
3. **Update state after rendering:** Make state mutations outside the render closure

**Example from `search_browser.rs` (lines 337-344):**
```rust
terminal.terminal().draw(|frame| {
    let chunks = list_detail_layout(frame.size(), 50);
    
    let selected_item = state.selected_item().cloned();  // Extract before using state
    
    // Left: Results list
    let results_list = render_results_list(&state, chunks[0], &theme);
    list_state.select(Some(state.selected));  // Use state immutably
    frame.render_stateful_widget(results_list, chunks[0], &mut list_state);  // list_state is separate
    
    // ... rest uses selected_item instead of state.selected_item()
});
```

**Example from `ar_pending_manager.rs` (lines 464-507):**
```rust
let mut state = PendingManagerState::new(building_name)?;
let mut list_state = ListState::default();  // Separate list_state

loop {
    terminal.terminal().draw(|frame| {
        // ... render using &state and &mut list_state separately
        list_state.select(Some(state.selected_index));
        frame.render_stateful_widget(pending_list, content_chunks[0], &mut list_state);
    })?;
    // ... event handling that mutates state
}
```

---

## How to Fix

### Fix for `src/ui/users.rs`

The issue is that `UserBrowserState` has `list_state` as a field, but we need it separately for `render_stateful_widget`.

**Option 1 (Recommended - Match existing pattern):**
Extract `list_state` from `UserBrowserState` and manage it separately, similar to how `search_browser.rs` and `ar_pending_manager.rs` do it.

1. Remove `list_state` field from `UserBrowserState`
2. Create `let mut list_state = ListState::default();` in `handle_user_browser()`
3. Update `list_state.select(Some(state.selected_index))` before render
4. Pass `&mut list_state` to `render_stateful_widget`
5. After render, sync `state.selected_index` from `list_state.selected()` if needed

**Option 2 (Alternative):**
Extract all needed data from `state` before the closure:
1. Clone `selected_user()` result before entering closure
2. Clone `selected_user_activity` before entering closure
3. Store `selected_index` in a local variable

**Recommended Fix (Option 1):**

```rust
// In handle_user_browser(), around line 468:
let mut state = UserBrowserState::new(registry);
let mut list_state = ListState::default();  // Separate from state
if !state.filtered_users.is_empty() {
    list_state.select(Some(0));
}

// In the render loop (around line 486):
terminal.terminal().draw(|frame| {
    // ... existing code ...
    
    match state.view_mode {
        ViewMode::List => {
            let content_chunks = list_detail_layout(chunks[1], 40);
            
            // Extract data before rendering
            let selected_user = state.selected_user().map(|u| (u.email.clone(), u.id.clone()));
            let selected_activity = state.selected_user_activity.clone();
            
            // User list
            let user_list = render_user_list(&state, &theme, content_chunks[0]);
            list_state.select(Some(state.selected_index));  // Sync before render
            frame.render_stateful_widget(user_list, content_chunks[0], &mut list_state);
            
            // Details panel
            if state.show_details {
                // ... use selected_user and selected_activity instead of state.selected_user()
            }
        }
        // ... rest of match
    }
})?;

// After render, sync selected_index back from list_state if needed
if let Some(selected) = list_state.selected() {
    state.selected_index = selected.min(state.filtered_users.len().saturating_sub(1));
}
```

Also need to update `move_up()` and `move_down()` to update `list_state` separately.

---

## Next Steps to Resume

1. **Fix the 2 compilation errors** in `src/ui/users.rs` using Option 1 above
2. **Run `cargo check`** to verify no remaining errors
3. **Test the user browser** with `arx users browse`
4. **Test watch dashboard** with `arx watch` to see user attribution
5. **Document any remaining Phase 4 items** from `USER_IDENTITY_AND_ATTRIBUTION.md`

---

## Files Modified in This Session

- `src/commands/watch_dashboard.rs` - Added user attribution
- `src/ui/users.rs` - Created user browser TUI (needs final fix)
- `src/commands/users.rs` - Added `Browse` command handler
- `src/cli/mod.rs` - Added `Browse` subcommand

---

## Related Documentation

- `USER_IDENTITY_AND_ATTRIBUTION.md` - Main design document
- `USER_IDENTITY_IMPLEMENTATION_MAP.md` - Implementation roadmap
- Phase 4 section describes: Enhanced TUI Display, Interactive User Browser, User Activity Timeline, Organization Grouping, Contact Information with Clipboard Support

---

## Quick Resume Checklist

- [ ] Fix borrow checker errors in `src/ui/users.rs` (Option 1 recommended)
- [ ] Run `cargo check --lib` to verify compilation
- [ ] Test `arx users browse` command
- [ ] Test `arx watch` to see user attribution in dashboard
- [ ] Verify all Phase 4 features from design doc are complete
- [ ] Move to next phase or address any remaining Phase 4 items
