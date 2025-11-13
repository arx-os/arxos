# Three-Way Diff Viewer

**Feature**: Manual Conflict Resolution
**Version**: 1.0.0
**Status**: ✅ Complete
**Last Updated**: 2025-11-12

## Overview

The Three-Way Diff Viewer provides a professional, full-screen interface for manually resolving Git conflicts that occur when syncing offline changes. It displays three versions side-by-side (Base, Theirs, Mine) and allows users to choose resolution strategies per conflict hunk.

## Features

### Visual Comparison

- **Side-by-Side Layout**: Three panels showing Base (original), Theirs (server), and Mine (offline)
- **Color-Coded Diffs**:
  - 🟢 Green: Added lines
  - 🔴 Red: Removed lines
  - 🟡 Amber: Conflict lines
  - ⚪ Gray: Unchanged lines
- **Line Numbers**: Each line prefixed with its number for easy reference
- **Syntax Agnostic**: Works with any text-based file format

### Resolution Strategies

Each conflict hunk can be resolved using five strategies:

1. **Use Base** - Restore the original version (common ancestor)
2. **Use Theirs** - Accept the server's changes
3. **Use Mine** - Keep offline changes
4. **Use Both** - Concatenate mine then theirs (useful for non-conflicting additions)
5. **Use Neither** - Discard both changes, use base (fallback)

### User Experience

- **Interactive Selection**: Click panels or buttons to select strategy
- **Real-Time Progress**: Shows "X/Y conflicts resolved" with percentage
- **Multi-File Support**: Navigate between files with conflicted content
- **Visual Feedback**: Selected panels highlighted with blue border
- **File Navigation**: Tabs with status indicators (resolved vs pending)
- **Statistics Dashboard**: Files, conflicts, resolved count, progress %

## Architecture

### Component Structure

```
src/modules/offline/components/diff/
├── types.ts                    # TypeScript interfaces
├── parser.ts                   # Parsing and resolution utilities
├── DiffPanel.tsx              # Single version panel (Base/Theirs/Mine)
├── ConflictHunkViewer.tsx     # Individual conflict with 5 resolution buttons
├── ThreeWayDiffViewer.tsx     # Main orchestrator component
└── index.ts                    # Public exports
```

### Type Definitions

```typescript
// A single line in the diff
interface DiffLine {
  lineNumber: number;
  content: string;
  type: "added" | "removed" | "unchanged" | "conflict";
}

// A section with conflicts
interface ConflictHunk {
  id: string;
  startLine: number;
  endLine: number;
  base: DiffLine[];      // Original version
  theirs: DiffLine[];    // Server version
  mine: DiffLine[];      // Offline version
  resolution: HunkResolution | null;
}

// Resolution choice
type HunkResolution = "base" | "theirs" | "mine" | "both" | "neither";

// Complete file conflict
interface ConflictFile {
  filePath: string;
  hunks: ConflictHunk[];
  base: string;
  theirs: string;
  mine: string;
}
```

## Usage

### From ConflictDialog

1. User encounters conflicts during sync
2. ConflictDialog shows with three options:
   - Accept My Changes (automatic)
   - Accept Server Changes (automatic)
   - **Manual Resolution** ← Opens diff viewer
3. User selects "Manual Resolution" and clicks "Open Diff Viewer"

### In Diff Viewer

1. **Review**: User sees three-column comparison
2. **Select**: Click panels or buttons to choose resolution
3. **Navigate**: Use file tabs to move between conflicted files
4. **Progress**: Watch progress bar update as conflicts resolved
5. **Apply**: When all resolved, click "Apply Resolutions"
6. **Return**: Viewer closes, conflicts merged into session branch

### Programmatic Usage

```typescript
import { ThreeWayDiffViewer } from "./modules/offline/components/diff";

function MyComponent() {
  const [conflicts, setConflicts] = useState<GitConflict[]>([]);

  const handleResolve = async (resolutions: Map<string, string>) => {
    // resolutions: filePath -> resolved content
    for (const [path, content] of resolutions) {
      await applyResolution(path, content);
    }
  };

  return (
    <ThreeWayDiffViewer
      conflicts={conflicts}
      onResolve={handleResolve}
      onCancel={() => setConflicts([])}
    />
  );
}
```

## Parser Utilities

### parseGitConflict

Converts Git conflict data into structured format:

```typescript
const conflict = parseGitConflict(
  "file.txt",
  "base content\nline 2",
  "theirs content\nline 2",
  "mine content\nline 2"
);
// Returns ConflictFile with hunks
```

### detectChanges

Compares two sets of lines to identify changes:

```typescript
const changes = detectChanges(baseLines, changedLines);
// Returns DiffLine[] with types: added, removed, unchanged
```

### resolveHunk

Applies resolution strategy to a hunk:

```typescript
const resolved = resolveHunk(hunk, "mine");
// Returns resolved content as string
```

### calculateDiffStats

Computes statistics across all files:

```typescript
const stats = calculateDiffStats(files);
// Returns: { totalConflicts, resolvedConflicts, filesWithConflicts, ... }
```

## Components

### ThreeWayDiffViewer

**Props**:
- `conflicts: GitConflict[]` - Array of conflicts to resolve
- `onResolve: (resolutions: Map<string, string>) => void` - Callback with resolutions
- `onCancel: () => void` - Cancel callback

**Features**:
- Full-screen layout
- Header with stats dashboard
- File navigation tabs
- Conflict hunk list
- Footer with actions

### ConflictHunkViewer

**Props**:
- `hunk: ConflictHunk` - The conflict to display
- `fileNumber: number` - File index (for labeling)
- `hunkNumber: number` - Hunk index (for labeling)
- `onResolve: (hunkId, resolution) => void` - Resolution callback

**Features**:
- Three-column diff display
- Five resolution buttons
- Status indicator (resolved/pending)
- Help text for guidance

### DiffPanel

**Props**:
- `title: string` - Panel title ("Base", "Theirs", "Mine")
- `side: DiffSide` - Which version this represents
- `lines: DiffLine[]` - Lines to display
- `isSelected: boolean` - Selection state
- `onSelect: () => void` - Selection callback

**Features**:
- Color-coded title
- Line-by-line display
- Line numbers
- "Selected" badge
- Line count footer

## Testing

### Test Coverage

**Parser Tests** (15 tests):
```bash
✓ parseGitConflict
  ✓ should parse a simple conflict
  ✓ should handle empty content
  ✓ should create hunks with proper line numbers

✓ detectChanges
  ✓ should detect added lines
  ✓ should detect removed lines
  ✓ should detect modified lines
  ✓ should handle unchanged lines

✓ resolveHunk
  ✓ should resolve with "base" strategy
  ✓ should resolve with "theirs" strategy
  ✓ should resolve with "mine" strategy
  ✓ should resolve with "both" strategy
  ✓ should resolve with "neither" strategy

✓ calculateDiffStats
  ✓ should calculate stats correctly
  ✓ should count resolved conflicts
  ✓ should handle empty files array
```

**Component Tests** (9 tests):
```bash
✓ DiffPanel
  ✓ should render panel with title
  ✓ should display line count
  ✓ should show 'Selected' badge when selected
  ✓ should call onSelect when clicked
  ✓ should display all lines with line numbers
  ✓ should show 'Empty' message when no lines
  ✓ should use correct color for base side
  ✓ should use correct color for theirs side
  ✓ should use correct color for mine side
```

### Running Tests

```bash
# All diff tests
npm run test:unit -- diff

# Specific test file
npm run test:unit -- parser.test.ts

# Watch mode
npm run test:unit -- --watch diff
```

## Styling

### Color Palette

```css
/* Panel Titles */
Base:   text-slate-400
Theirs: text-purple-400
Mine:   text-emerald-400

/* Line Types */
Added:      bg-emerald-500/10 text-emerald-300
Removed:    bg-red-500/10 text-red-300
Conflict:   bg-amber-500/10 text-amber-200
Unchanged:  text-slate-300

/* Selection State */
Selected:   border-blue-500 bg-blue-500/5
Unselected: border-slate-700 hover:border-slate-600

/* Resolution Buttons */
Base:    border-blue-500 bg-blue-500/20 text-blue-300
Theirs:  border-purple-500 bg-purple-500/20 text-purple-300
Mine:    border-emerald-500 bg-emerald-500/20 text-emerald-300
Both:    border-cyan-500 bg-cyan-500/20 text-cyan-300
Neither: border-slate-500 bg-slate-500/20 text-slate-300
```

### Layout

```
┌─────────────────────────────────────────────────┐
│ Header: Manual Conflict Resolution              │
│ Stats: [Files: 2] [Conflicts: 5] [Resolved: 3]  │
├─────────────────────────────────────────────────┤
│ [File1.txt ✓] [File2.txt ⚠]                     │
├─────────────────────────────────────────────────┤
│                                                  │
│ ┌─────────┬─────────┬─────────┐                │
│ │  Base   │ Theirs  │  Mine   │  ← Diff Panels │
│ │ line 1  │ line 1  │ line 1  │                │
│ │ line 2  │ changed │ changed │                │
│ └─────────┴─────────┴─────────┘                │
│                                                  │
│ [Use Base] [Use Theirs] [Use Mine] ...          │
│                                                  │
├─────────────────────────────────────────────────┤
│ [Cancel] [Apply Resolutions →]                  │
└─────────────────────────────────────────────────┘
```

## Performance

### Bundle Size

- **Parser Utilities**: ~2 KB (gzipped)
- **Components**: ~6 KB (gzipped)
- **Total Impact**: ~8 KB (gzipped)

### Rendering

- **Large Files**: Handles up to 1000 lines per version efficiently
- **Virtual Scrolling**: Could be added for files > 1000 lines
- **Re-renders**: Optimized with proper key props

## Browser Compatibility

Works in all modern browsers that support:
- ✅ ES6+ JavaScript
- ✅ CSS Grid & Flexbox
- ✅ React 18+

## Accessibility

- ✅ Keyboard navigation between panels
- ✅ ARIA labels on all interactive elements
- ✅ Screen reader friendly structure
- ✅ High contrast color scheme
- ⚠️ Full keyboard-only workflow (could be improved)

## Limitations

1. **Diff Algorithm**: Simple line-by-line comparison (not Myers diff)
2. **Syntax Highlighting**: Not implemented (shows plain text)
3. **Inline Editing**: Cannot manually edit conflict text
4. **Large Files**: May slow down with files > 1000 lines
5. **Binary Files**: Not supported

## Future Enhancements

### Phase 1 (Short Term)

- [ ] Keyboard shortcuts (j/k for navigation, 1-5 for resolution selection)
- [ ] Undo/redo for resolution choices
- [ ] Search within diffs
- [ ] Copy lines to clipboard

### Phase 2 (Medium Term)

- [ ] Myers diff algorithm for better change detection
- [ ] Syntax highlighting based on file extension
- [ ] Inline editing of selected resolution
- [ ] Virtual scrolling for large files
- [ ] Diff statistics per file (lines added/removed)

### Phase 3 (Long Term)

- [ ] Binary file diff (hex viewer)
- [ ] Image diff (pixel-by-pixel comparison)
- [ ] Collaborative conflict resolution (real-time)
- [ ] AI-assisted conflict resolution suggestions
- [ ] Export diff as patch file

## Examples

### Simple Text Conflict

```
Base:           Theirs:         Mine:
line 1          line 1          line 1
old line        server change   my change
line 3          line 3          line 3
```

**Resolution Options**:
- Use Base → "old line"
- Use Theirs → "server change"
- Use Mine → "my change"
- Use Both → "my change\nserver change"
- Use Neither → "old line" (base)

### Multi-Line Conflict

```
Base:           Theirs:         Mine:
function foo()  function foo()  function bar()
  return 1        return 2        return 3
}               }               }
```

**Use Case**: Different function signatures and implementations

### Empty Line Conflicts

```
Base:           Theirs:         Mine:
line 1          line 1          line 1
                line 2
line 3          line 3          line 3
```

**Use Case**: Whitespace differences

## Best Practices

### For Users

1. **Review All Panels**: Don't just pick "Mine" automatically
2. **Understand Context**: Read surrounding lines
3. **Test After Resolving**: Verify merged result works
4. **Save Frequently**: Apply resolutions often (don't accumulate)

### For Developers

1. **Parse Early**: Convert Git conflicts to structured format immediately
2. **Immutable Updates**: Use spread operators for state updates
3. **Key Props**: Always provide unique keys for list rendering
4. **Error Boundaries**: Wrap viewer in error boundary
5. **Loading States**: Show skeleton while parsing large conflicts

## Troubleshooting

### Issue: Lines Don't Match

**Cause**: Conflict data may be corrupted or incomplete
**Solution**: Re-fetch conflict data from agent

### Issue: Slow Rendering

**Cause**: Too many lines being rendered
**Solution**: Implement virtual scrolling or pagination

### Issue: Resolution Not Applied

**Cause**: Strategy may not match expected format
**Solution**: Check `resolveHunk` implementation and Map format

### Issue: Colors Not Showing

**Cause**: Tailwind classes may not be compiled
**Solution**: Ensure Tailwind processes all diff component files

## Credits

- **Architecture**: Three-column diff pattern inspired by GitKraken
- **Parser**: Custom implementation for ArxOS session branching
- **UI/UX**: Professional Git tooling standards
- **Testing**: Comprehensive coverage with Vitest + React Testing Library

## References

- [Git Merge Strategies](https://git-scm.com/docs/merge-strategies)
- [Myers Diff Algorithm](https://blog.jcoglan.com/2017/02/12/the-myers-diff-algorithm-part-1/)
- [Three-Way Merge](https://en.wikipedia.org/wiki/Merge_(version_control)#Three-way_merge)
- [M05 Offline Sync](./M05_OFFLINE_SYNC.md)
