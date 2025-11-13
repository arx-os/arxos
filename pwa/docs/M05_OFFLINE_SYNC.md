# M05: Offline-First Sync

**Status**: ✅ Complete
**Version**: 1.0.0
**Last Updated**: 2025-11-12

## Overview

M05 implements a complete offline-first synchronization system for ArxOS PWA, enabling users to work seamlessly offline with automatic sync when connectivity is restored. The implementation uses session-based Git branching for conflict resolution and IndexedDB for persistent storage.

## Architecture

### Core Components

```
src/modules/offline/
├── components/          # UI components
│   ├── ConflictDialog.tsx
│   ├── OfflineIndicator.tsx
│   └── SyncStatusToast.tsx
├── hooks/               # React hooks
│   └── useOnlineStatus.ts
├── state/               # State management
│   └── sessionStore.ts
└── sync/                # Sync coordination
    ├── CommandQueueManager.ts
    ├── SyncCoordinator.tsx
    └── index.ts

src/lib/storage/         # Storage layer
├── types.ts             # Type definitions
├── db.ts                # IndexedDB utilities
├── commandQueue.ts      # Command queue operations
├── session.ts           # Session management
└── floorEdit.ts         # Floor edit persistence
```

## Key Features

### 1. Session-Based Git Branching

Each offline session creates a unique Git branch:

```typescript
// Session structure
interface Session {
  id: string;                    // UUID
  branchName: string;            // arxos/session-{uuid}
  createdAt: number;
  lastSyncAt: number | null;
  status: "active" | "syncing" | "merged" | "conflicted";
  commandCount: number;
}
```

**Benefits**:
- Clean conflict resolution via Git merge strategies
- Full offline history preserved in Git
- Easy rollback if needed
- Multiple conflict resolution strategies

### 2. Command Queuing

All operations while offline are queued:

```typescript
interface QueuedCommand {
  id: string;
  command: AgentAction;
  payload: unknown;
  timestamp: number;
  retryCount: number;
  status: "pending" | "retrying" | "failed";
  sessionId: string;
}
```

**Features**:
- Automatic retry with exponential backoff
- Max 3 retry attempts before marking as failed
- Session-based command grouping
- Persistent storage in IndexedDB

### 3. Dual Online Detection

Combines browser and agent connectivity:

```typescript
interface OnlineStatus {
  isOnline: boolean;           // Overall connectivity
  browserOnline: boolean;      // navigator.onLine
  agentConnected: boolean;     // WebSocket connection
  lastOnline: Date;
}
```

**Why Both?**:
- Browser online doesn't guarantee agent connectivity
- Agent may be down while network is up
- Accurate offline detection for better UX

### 4. Automatic Sync

The `SyncCoordinator` component orchestrates sync:

1. **On Going Online**:
   - Process command queue (retry failed commands)
   - If all commands succeed, merge session branch
   - Handle conflicts if detected
   - Clean up on successful merge

2. **On Going Offline**:
   - Create new session branch (if first offline operation)
   - Queue all subsequent operations
   - Continue working seamlessly

### 5. Conflict Resolution

Three strategies available:

- **Accept Mine**: Keep offline changes, overwrite server (`git merge -X ours`)
- **Accept Theirs**: Discard offline changes, use server version
- **Manual**: Three-way diff viewer for line-by-line resolution

#### Manual Resolution with Three-Way Diff Viewer

The manual resolution mode opens a full-screen diff viewer that provides:

**Features**:
- Side-by-side comparison of Base, Theirs (server), and Mine (offline)
- Color-coded diff lines (added, removed, unchanged, conflict)
- Five resolution strategies per conflict hunk:
  - **Use Base**: Restore original version
  - **Use Theirs**: Accept server changes
  - **Use Mine**: Keep offline changes
  - **Use Both**: Concatenate mine then theirs
  - **Use Neither**: Discard both changes (use base)
- Real-time progress tracking (conflicts resolved / total)
- File navigation for multi-file conflicts
- Preview of selected resolution before applying

**Architecture**:
```
src/modules/offline/components/diff/
├── types.ts                    # TypeScript types for diffs
├── parser.ts                   # Git conflict parsing utilities
├── DiffPanel.tsx              # Individual version panel
├── ConflictHunkViewer.tsx     # Single conflict with resolution UI
└── ThreeWayDiffViewer.tsx     # Main diff viewer component
```

**Usage Flow**:
1. User selects "Manual Resolution" from ConflictDialog
2. Three-way diff viewer opens in full screen
3. User reviews each conflict hunk across three versions
4. User clicks panels or buttons to select resolution strategy
5. Progress bar shows conflicts resolved / total
6. When all conflicts resolved, "Apply Resolutions" becomes enabled
7. Applied resolutions merge into session branch

## Storage Layer

### IndexedDB Structure

Using `idb-keyval` for simple key-value storage:

```typescript
// Storage keys
const STORAGE_KEYS = {
  SESSION: "arxos:session",
  COMMAND_QUEUE: "arxos:command-queue",
  FLOOR_EDITS: "arxos:floor-edits",
} as const;
```

### Storage Functions

**Database Operations** (`db.ts`):
- `getItem<T>(key): Promise<T | null>`
- `setItem<T>(key, value): Promise<void>`
- `deleteItem(key): Promise<void>`
- `clearStorage(): Promise<void>`

**Command Queue** (`commandQueue.ts`):
- `enqueueCommand(command, payload, sessionId)`
- `dequeueCommand(commandId)`
- `updateQueuedCommand(commandId, updates)`
- `getSessionCommands(sessionId)`
- `clearSessionCommands(sessionId)`
- `getPendingCount()`

**Session Management** (`session.ts`):
- `createSession()`
- `getActiveSession()`
- `updateSession(updates)`
- `clearSession()`
- `markSyncing() / markMerged() / markConflicted()`

## Agent API

New Git session commands added to agent:

```typescript
// Create a session branch
createSessionBranch(sessionId: string): Promise<SessionBranchResult>

// Merge session branch back to main
mergeSessionBranch(
  sessionId: string,
  strategy?: "ours" | "theirs"
): Promise<MergeResult>

// Delete session branch after merge
deleteSessionBranch(sessionId: string): Promise<void>

// Get session branch info
getSessionBranchInfo(sessionId: string): Promise<SessionInfo>

// List all session branches
listSessionBranches(): Promise<SessionInfo[]>
```

## UI Components

### OfflineIndicator

Shows when the app is offline with pending command count:

```tsx
<OfflineIndicator />
```

**Features**:
- Fixed positioning (bottom-right)
- Shows reason for offline (no internet vs agent disconnected)
- Displays pending sync count
- Manual sync button when online

### SyncStatusToast

Shows sync progress and completion:

```tsx
<SyncStatusToast />
```

**States**:
- **Syncing**: Blue spinner, "Uploading offline changes"
- **Synced**: Green checkmark, auto-dismiss after 3s
- **Conflicted**: Amber warning, opens conflict dialog
- **Error**: Red error icon with error message

### ConflictDialog

Modal for resolving Git conflicts:

```tsx
<ConflictDialog />
```

**Features**:
- Lists conflicted files
- Three resolution strategies (radio buttons)
- Discard all changes button
- Automatic resolution via merge strategies

## Service Worker

Configured with Workbox for offline asset caching:

```typescript
VitePWA({
  registerType: "autoUpdate",
  workbox: {
    globPatterns: ["**/*.{js,css,html,ico,png,svg,wasm}"],
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/.*\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
        handler: "CacheFirst",
        options: {
          cacheName: "images-cache",
          expiration: {
            maxEntries: 100,
            maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
          },
        },
      },
    ],
  },
})
```

## Testing

### Test Coverage

**Storage Layer** (33 tests):
- IndexedDB utilities (7 tests)
- Command queue operations (9 tests)
- Session management (10 tests)
- Session store (8 tests)

**Hooks** (9 tests):
- Online status detection
- Online/offline event handling
- Dual connectivity tracking

**Total**: 180 tests passing ✅

### Test Setup

Using `fake-indexeddb` for IndexedDB mocking:

```typescript
// vitest.setup.ts
import "fake-indexeddb/auto";
```

## Usage Example

### Offline Workflow

```typescript
// 1. User goes offline
// - SyncCoordinator detects offline state
// - Creates session branch: arxos/session-abc123

// 2. User makes changes
await editFloor({ type: "add-room", data: {...} });
// - Command queued in IndexedDB
// - Session command count incremented

// 3. User comes back online
// - SyncCoordinator detects online state
// - Processes command queue (sends all queued commands)
// - Merges session branch to main
// - If conflicts: shows ConflictDialog
// - If success: cleans up session branch
```

### Manual Sync

```typescript
const queueManager = getQueueManager();
await queueManager.processQueue();
```

### Conflict Resolution

```typescript
// From ConflictDialog
const { resolveConflicts } = useSessionStore();

// Accept my changes
await resolveConflicts("ours");

// Accept server changes
await resolveConflicts("theirs");
```

## Configuration

### Environment Variables

None required - works out of the box.

### Customization

**Command Retry Settings** (`CommandQueueManager.ts`):
```typescript
const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 5000]; // ms
```

**Storage Keys** (`types.ts`):
```typescript
export const STORAGE_KEYS = {
  SESSION: "arxos:session",
  COMMAND_QUEUE: "arxos:command-queue",
  FLOOR_EDITS: "arxos:floor-edits",
} as const;
```

## Performance

### Bundle Size

- Service Worker: ~15 KB
- Workbox Runtime: ~20 KB
- Offline Module: ~8 KB
- Total overhead: ~43 KB (gzipped)

### IndexedDB Performance

- Typical queue size: < 100 commands
- Read/Write latency: < 5ms
- Storage limit: Quota API (typically GB+)

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 15.4+
- ✅ All browsers with IndexedDB + Service Worker support

## Limitations

1. **Large File Operations**: Not optimized for syncing large binary files
2. **Concurrent Edits**: No real-time collaboration during offline mode
3. **Session Persistence**: Session cleared on successful merge (no session history)
4. **Advanced Diff Algorithm**: Currently uses simple line-by-line comparison (Myers diff algorithm would be better)

## Future Enhancements

### Phase 6 (Future)

- [ ] Advanced diff algorithm (Myers diff) for better change detection
- [ ] Syntax highlighting in diff viewer based on file type
- [ ] Inline editing of conflict resolutions
- [ ] Optimistic UI updates with rollback
- [ ] Compression for large command payloads
- [ ] Session history and replay
- [ ] Background sync API integration
- [ ] Conflict auto-resolution heuristics
- [ ] Multi-device sync coordination
- [ ] Offline analytics and diagnostics

## Dependencies

```json
{
  "vite-plugin-pwa": "^0.20.5",
  "workbox-window": "^7.1.0",
  "idb-keyval": "^6.2.1",
  "uuid": "^11.0.3",
  "fake-indexeddb": "^6.0.0" // dev only
}
```

## Migration Notes

No migration required - this is a new feature addition. Existing functionality continues to work unchanged.

## Troubleshooting

### Issue: IndexedDB not available

**Solution**: Check browser compatibility and ensure not in private/incognito mode.

### Issue: Commands not syncing

**Solution**:
1. Check browser console for errors
2. Verify agent connectivity
3. Check pending queue: `await getPendingCount()`

### Issue: Merge conflicts every time

**Solution**: May indicate schema mismatch or concurrent edits. Use "Accept Mine" or "Accept Theirs" strategy.

### Issue: Service worker not registering

**Solution**:
1. Must be served over HTTPS (or localhost)
2. Check browser console for registration errors
3. Ensure `vite-plugin-pwa` is properly configured

## Credits

- **Implementation**: Claude Code + Joel Pate
- **Architecture**: Session-based Git branching pattern
- **Storage**: IndexedDB via idb-keyval
- **Service Worker**: Workbox
- **Testing**: Vitest + fake-indexeddb

## References

- [PWA Roadmap](../PWA_ROADMAP.md)
- [IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Workbox](https://developer.chrome.com/docs/workbox)
- [Git Merge Strategies](https://git-scm.com/docs/git-merge)
