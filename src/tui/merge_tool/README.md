# ArxOS Merge Tool

Interactive three-way merge conflict resolution tool for YAML building data and other text files.

## Features

- **Two-column diff viewer**: Side-by-side comparison of "ours" vs "theirs"
- **Base version toggle**: View the common ancestor on demand (press `b`)
- **Keyboard navigation**: Vim-style navigation (j/k, n/p) and conflict jumping (g/G)
- **Multiple resolution strategies**:
  - Choose "ours" (left side)
  - Choose "theirs" (right side)
  - Choose both (ours + theirs)
  - Choose both reversed (theirs + ours)
  - Skip (leave conflict markers)
- **Preview before save**: Review merged result before writing to disk
- **Git integration**: Auto-detect conflicted files from `git diff`
- **Context awareness**: Shows lines before/after each conflict for clarity

## Usage

### List conflicted files

```bash
arx merge --list
```

### Resolve specific file

```bash
arx merge path/to/building.yaml
```

### Resolve all conflicted files

```bash
arx merge
```

This will iterate through all files with Git conflict markers and launch the interactive viewer for each one.

## Keyboard Shortcuts

### Navigation
- `n` / `j` - Next conflict
- `p` / `k` - Previous conflict
- `↓` / `↑` - Scroll within conflict
- `g` - Go to first conflict
- `G` - Go to last conflict

### Resolution
- `o` - Choose OURS (left side)
- `t` - Choose THEIRS (right side)
- `B` - Choose BOTH (ours + theirs)
- `R` - Choose BOTH REVERSED (theirs + ours)
- `s` - Skip this conflict (leave markers)

### View
- `b` - Toggle BASE version popup (shows common ancestor)
- `P` - Preview merged result
- `?` - Toggle help screen

### Actions
- `w` - Write (save and exit)
- `q` / `Esc` - Quit (cancel and exit)

## Workflow

1. **Auto-detect conflicts**: Tool finds all files with Git conflict markers
2. **Navigate conflicts**: Use `n`/`p` to jump between conflicts
3. **Review context**: See surrounding code and base version (`b`)
4. **Choose resolution**: Press `o`, `t`, `B`, or `R` for each conflict
5. **Preview**: Press `P` to see the final merged result
6. **Save**: Press `w` to write changes
7. **Git add & commit**: After resolving, commit your changes

## Architecture

### Components

- **`conflict.rs`**: Parser for Git conflict markers (`<<<<<<< ======= >>>>>>>`)
- **`resolver.rs`**: Resolution engine that builds merged content from user choices
- **`diff_viewer.rs`**: Interactive TUI with Ratatui
- **`mod.rs`**: Main entry point and Git integration

### Data Flow

```
Git File with Conflicts
        ↓
ConflictParser::parse_file()
        ↓
Vec<Conflict> (base/ours/theirs)
        ↓
MergeViewer::run()
        ↓
User makes choices
        ↓
ResolutionEngine::build_merged_content()
        ↓
Preview & Save
```

## Design Decisions

### Why two-column instead of three-column?

For YAML building data, most conflicts are between two branches. The base version is available on demand (`b` key) to save screen space and reduce cognitive load.

### Why manual save with preview?

Building data is critical infrastructure. Showing a preview before writing gives users confidence and allows final review before committing changes.

### Why support both Git markers and merge-tree?

- **Git markers**: Universal format, works everywhere
- **merge-tree**: Cleaner three-way diff when base is needed

Both are supported for maximum flexibility.

## Example

Given a conflict in `building.yaml`:

```yaml
name: "Office Building"
<<<<<<< HEAD
floors: 5
||||||| base
floors: 3
=======
floors: 4
>>>>>>> feature-branch
address: "123 Main St"
```

The merge tool will:
1. Parse the conflict into ours (5), base (3), theirs (4)
2. Display side-by-side comparison
3. Allow you to choose or combine values
4. Build the final YAML with your choice

## Testing

Run the unit tests:

```bash
cargo test -p arxos-core --lib merge_tool
```

## Future Enhancements

- [ ] Custom edit mode for manual resolution
- [ ] Syntax highlighting for YAML
- [ ] Diff highlighting (line-by-line changes)
- [ ] Undo/redo for resolution choices
- [ ] Save session and resume later
- [ ] Integration with `git mergetool`
- [ ] Support for binary conflicts (images, etc.)
