# TUI Technical Debt Analysis

**Date:** January 2025  
**Scope:** All TUI modules created today  
**Status:** Analysis Complete

---

## 📊 File Size Analysis

| File | Lines | Status | Recommendation |
|------|-------|--------|---------------|
| `command_palette.rs` | 572 | ⚠️ Large | Refactor into 3-4 modules |
| `workspace_manager.rs` | 488 | ⚠️ Large | Refactor into 2-3 modules |
| `help.rs` | 471 | ⚠️ Large | Refactor into 2-3 modules |
| `export.rs` | 427 | ⚠️ Large | Refactor into submodules |
| `theme_manager.rs` | 395 | ⚠️ Medium-Large | Consider splitting |
| `mouse.rs` | 343 | ✅ Acceptable | No action needed |
| `error_modal.rs` | 334 | ✅ Acceptable | No action needed |

**Total Lines:** 3,607 across 13 UI files  
**Average:** ~277 lines per file

---

## 🔍 Detailed Refactoring Recommendations

### 1. **command_palette.rs (572 lines)** ⚠️ HIGH PRIORITY

**Current Structure:**
- CommandEntry/CommandCategory definitions (~50 lines)
- CommandPalette struct and impl (~200 lines)
- `load_commands()` - Large static data (~250 lines)
- `handle_command_palette()` - Event loop (~50 lines)
- `render_command_palette()` - Rendering (~80 lines)

**Recommended Refactoring:**
```
src/ui/command_palette/
├── mod.rs              # Public API
├── types.rs            # CommandEntry, CommandCategory
├── commands.rs         # load_commands() - static command definitions
├── palette.rs          # CommandPalette struct and logic
├── render.rs           # render_command_palette()
└── handler.rs          # handle_command_palette()
```

**Benefits:**
- Separates data (commands) from logic
- Easier to extend with new commands
- Better testability
- Cleaner module boundaries

---

### 2. **help.rs (471 lines)** ⚠️ HIGH PRIORITY

**Current Structure:**
- HelpContext enum, Shortcut struct (~50 lines)
- HelpSystem struct (~50 lines)
- `get_context_help()` - Huge match statement (~250 lines)
- `get_all_shortcuts()` - Shortcut definitions (~100 lines)
- Rendering functions (~50 lines)

**Recommended Refactoring:**
```
src/ui/help/
├── mod.rs              # Public API
├── types.rs            # HelpContext, Shortcut, ShortcutCategory
├── content.rs          # get_context_help() - all help text
├── shortcuts.rs        # get_all_shortcuts() - shortcut definitions
├── system.rs           # HelpSystem struct and logic
├── render.rs           # render_help_overlay(), render_shortcut_cheat_sheet()
└── events.rs           # handle_help_event()
```

**Benefits:**
- Separates help content from logic
- Easier to maintain help text
- Can generate help content from external sources
- Better organization

---

### 3. **workspace_manager.rs (488 lines)** ⚠️ MEDIUM PRIORITY

**Current Structure:**
- Workspace struct (~30 lines)
- WorkspaceManager struct (~200 lines)
- `discover_workspaces()` - File system operations (~100 lines)
- `load_building_description()` - YAML parsing (~50 lines)
- `handle_workspace_manager()` - Event loop (~50 lines)
- `render_workspace_manager()` - Rendering (~80 lines)

**Recommended Refactoring:**
```
src/ui/workspace_manager/
├── mod.rs              # Public API
├── types.rs            # Workspace struct
├── discovery.rs        # discover_workspaces(), load_building_description()
├── manager.rs          # WorkspaceManager struct and logic
├── render.rs           # render_workspace_manager()
└── handler.rs          # handle_workspace_manager()
```

**Benefits:**
- Separates file I/O from UI logic
- Better testability (can mock file system)
- Clearer separation of concerns

---

### 4. **export.rs (427 lines)** ⚠️ MEDIUM PRIORITY

**Current Structure:**
- ExportFormat enum (~50 lines)
- `export_buffer()` - Main export function (~20 lines)
- `export_as_text()` - Text export (~20 lines)
- `export_as_ansi()` - ANSI export (~60 lines)
- `export_as_html()` - HTML export (~80 lines)
- `export_as_markdown()` - Markdown export (~10 lines)
- Color conversion utilities (~100 lines)
  - `color_to_ansi()` (~40 lines)
  - `modifiers_to_ansi()` (~20 lines)
  - `color_to_css()` (~40 lines)
- `export_current_view()` - Helper (~30 lines)

**Recommended Refactoring:**
```
src/ui/export/
├── mod.rs              # Public API
├── format.rs           # ExportFormat enum
├── text.rs             # export_as_text()
├── ansi.rs             # export_as_ansi()
├── html.rs             # export_as_html()
├── markdown.rs         # export_as_markdown()
├── colors.rs           # Color conversion utilities
└── buffer.rs           # export_buffer(), export_current_view()
```

**Benefits:**
- Each format is isolated
- Easier to add new export formats
- Color utilities reusable
- Better organization

---

### 5. **theme_manager.rs (395 lines)** ⚠️ LOW PRIORITY

**Current Structure:**
- ThemeConfig struct (~30 lines)
- ThemePreset enum (~100 lines)
- ThemeManager struct (~200 lines)
- Color parsing utilities (~70 lines)

**Recommendation:** 
- **Optional** - Current size is acceptable
- Could split into `presets.rs` and `manager.rs` if it grows
- Color parsing could move to a shared `colors.rs` module

---

## 🔄 Code Duplication Analysis

### Common Patterns Found:

1. **Event Loop Pattern** - Repeated in:
   - `command_palette.rs`
   - `workspace_manager.rs`
   - Similar pattern in other TUI components

   **Recommendation:** Create a generic `TuiApp` trait or base struct

2. **Search/Filter Pattern** - Repeated in:
   - `command_palette.rs` (command filtering)
   - `workspace_manager.rs` (workspace filtering)
   - Similar in other components

   **Recommendation:** Extract to `src/ui/filter.rs` utility

3. **List Rendering Pattern** - Repeated in:
   - `command_palette.rs`
   - `workspace_manager.rs`
   - Equipment browser, etc.

   **Recommendation:** Create reusable `ListWidget` component

---

## 📋 Technical Debt Summary

### High Priority Refactoring:
1. ✅ **command_palette.rs** → Split into 5-6 modules
2. ✅ **help.rs** → Split into 6-7 modules

### Medium Priority Refactoring:
3. ✅ **workspace_manager.rs** → Split into 5-6 modules
4. ✅ **export.rs** → Split into 7-8 modules

### Low Priority / Future:
5. ⚪ **theme_manager.rs** → Monitor, split if it grows
6. ⚪ **Extract common patterns** → Create reusable components

---

## ✅ What's Good

- **No code duplication** - Logic is well-contained
- **Clear module boundaries** - Each file has a single responsibility
- **Good documentation** - All modules have doc comments
- **Consistent patterns** - Similar code structure across modules
- **No circular dependencies** - Clean module hierarchy

---

## 🎯 Refactoring Priority

**Immediate (Before Testing):**
- None - Code is functional and testable as-is

**Before Production:**
1. Refactor `help.rs` (largest content-heavy file)
2. Refactor `command_palette.rs` (large static data)
3. Refactor `workspace_manager.rs` (mixed concerns)
4. Refactor `export.rs` (multiple formats)

**Future Enhancements:**
- Extract common patterns into reusable components
- Create shared utilities for filtering/searching
- Consider a generic TUI app framework

---

## 📝 Notes

- **Current state is functional** - All code works correctly
- **Refactoring is optional** - Not blocking testing or production
- **File sizes are manageable** - Even large files are readable
- **No architectural issues** - Structure is sound
- **Easy to refactor later** - Clean boundaries make splitting straightforward

**Recommendation:** Proceed with testing as-is. Refactor during maintenance cycles or when adding new features.

