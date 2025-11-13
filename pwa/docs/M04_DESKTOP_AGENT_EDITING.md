# M04: Desktop Agent & Editing

## Overview

M04 implements the desktop agent integration and floor plan editing capabilities for ArxOS. This milestone enables users to connect to the desktop agent, perform Git operations, import/export IFC files, and edit floor plans with full undo/redo support and validation.

## Architecture

### Agent Module (`src/modules/agent/`)

#### Client Layer (`client/`)
- **AgentClient.ts**: Singleton WebSocket client with persistent connection
  - Auto-reconnect with exponential backoff
  - Ping/pong heartbeat (30s interval)
  - Request/response pattern with timeout support
  - Streaming support for long operations
  - Connection state notifications

- **types.ts**: Complete protocol type definitions
  - WebSocket message formats
  - Agent actions and capabilities
  - Git, IFC, validation types
  - Edit operation types

- **reconnect.ts**: Reconnection logic
  - Exponential backoff with jitter
  - Max retry limit
  - Configurable delays

#### State Management (`state/`)
- **agentStore.ts**: Zustand store for agent connection state
  - Connection status tracking
  - Connection quality metrics
  - Initialize/connect/disconnect actions
  - Send method for commands

- **authStore.ts**: Authentication state with sessionStorage
  - DID:key token validation
  - Ephemeral token storage (clears on browser close)
  - Token expiration checking

#### Components (`components/`)
- **AuthModal.tsx**: DID:key authentication dialog
  - Token input with validation
  - Connection testing
  - Success/error feedback

- **ConnectionIndicator.tsx**: Real-time connection status
  - Color-coded status badge
  - Connection quality indicator
  - Detailed dropdown with metrics
  - One-click reconnect

#### Commands (`commands/`)
- **git.ts**: Git command handlers
  - `gitStatus()`: Get repository status
  - `gitDiff()`: Get diff output
  - `gitCommit()`: Commit changes
  - `gitLog()`: Get commit history

- **ifc.ts**: IFC import/export handlers
  - `ifcImport()`: Import IFC with progress streaming
  - `ifcExport()`: Export to IFC with progress streaming
  - `listIfcFiles()`: List available IFC files

- **validation.ts**: Validation command handlers
  - `validateRoom()`: Validate room data
  - `validateEquipment()`: Validate equipment data
  - `validateBatch()`: Validate multiple operations
  - `applyEdits()`: Apply edit operations with validation

### Floor Editing Module (`src/modules/floor/`)

#### Edit Operations (`edit/`)
- **operations.ts**: Edit operation types and factories
  - Room operations: add, delete, move, resize
  - Equipment operations: add, delete, move
  - Wall operations: add, delete, move (stub)
  - Factory functions for creating operations

- **history.ts**: Undo/redo with command pattern
  - Edit history stack (max 100 operations)
  - Undo/redo pointer management
  - Inverse operation generator
  - History summary statistics

- **validation.ts**: Client-side validation
  - Room dimension/position validation
  - Equipment position validation
  - Batch validation support
  - Warnings for unusual values

#### State Management (`state/`)
- **editStore.ts**: Zustand store for edit state
  - Edit mode (select, draw-room, add-equipment)
  - Selection tracking (room/equipment)
  - History management (undo/redo)
  - Operation application via agent
  - Adapter to convert operations to agent format

- **saveStore.ts**: Save/commit flow management
  - Validation pipeline
  - Client-side + agent validation
  - Git commit integration
  - Error handling

#### Components (`components/`)
- **EditToolbar.tsx**: Edit mode and action toolbar
  - Mode selector (Select, Draw Room, Add Equipment)
  - Undo/Redo buttons
  - Delete selected button
  - Keyboard shortcuts support

- **ValidationPanel.tsx**: Validation results display
  - Error/warning categorization
  - Auto-fix suggestions
  - Proceed/cancel actions
  - Color-coded severity

- **SaveDialog.tsx**: Save changes dialog
  - Commit message input
  - Changes summary
  - Validation integration
  - Git commit execution

### Updated Stores

#### Git Store (`src/state/git.ts`)
- Migrated to new agent commands
- Added diff parser for structured output
- Updated connection checking

#### IFC Store (`src/state/ifc.ts`)
- Migrated to new agent commands
- Added progress tracking with streaming
- Updated connection checking

### Updated Components

#### IFC Panel (`src/components/IfcPanel.tsx`)
- Added progress bars for import/export
- Real-time progress messages
- Uses new agent connection state

## Features

### 1. Agent Connection
- WebSocket connection to desktop agent
- DID:key authentication
- Auto-reconnect on disconnect
- Connection quality monitoring
- Real-time status indicator

### 2. Git Integration
- View repository status
- View diffs (staged/unstaged)
- Commit changes with message
- View commit history

### 3. IFC Import/Export
- Import IFC files with progress tracking
- Export to IFC format
- Delta export support
- File statistics display

### 4. Floor Plan Editing
- Edit modes: Select, Draw Room, Add Equipment
- Operations: Add, Delete, Move, Resize
- Real-time validation
- Undo/redo support (100 operation history)
- Client-side + server-side validation

### 5. Save/Commit Flow
1. Make edits to floor plan
2. Open save dialog
3. Enter commit message
4. Validate changes (client + agent)
5. Review validation results
6. Save changes (apply edits + Git commit)

## Usage

### Connecting to Agent

1. Start the desktop agent on your local machine
2. Copy your DID:key token
3. Click the connection indicator in the app header
4. Paste your token and click "Connect"
5. Wait for connection confirmation

### Editing Floor Plans

1. Ensure agent is connected
2. Load a floor plan
3. Select edit mode from toolbar:
   - **Select**: Click to select rooms/equipment
   - **Draw Room**: Click and drag to draw new room
   - **Add Equipment**: Click to place equipment
4. Make your edits
5. Use Undo/Redo buttons as needed
6. Click "Save" when ready

### Saving Changes

1. Click "Save" button in edit toolbar
2. Review changes summary
3. Enter a descriptive commit message
4. Click "Validate & Save"
5. Review validation results
6. If valid, click "Save Changes"
7. Changes are applied and committed to Git

## Technical Details

### WebSocket Protocol

**Message Format:**
```typescript
{
  id: string;              // Unique message ID
  type: MessageType;       // request | response | error | stream | ping | pong
  action?: AgentAction;    // git.status | ifc.import | etc.
  payload?: unknown;       // Command-specific data
  timestamp: number;       // Unix timestamp
}
```

**Connection Flow:**
1. Client opens WebSocket connection
2. Client sends auth message with DID:key token
3. Agent validates token and responds
4. Client starts ping interval (30s)
5. Client sends requests, agent sends responses
6. On disconnect, client auto-reconnects with backoff

### Edit Operation Flow

1. **User Action**: User performs edit in UI
2. **Create Operation**: Factory function creates operation object
3. **Client Validation**: Validate dimensions, positions, required fields
4. **Add to History**: Operation added to undo/redo stack
5. **Convert to Agent Format**: Adapter converts detailed operation to simple format
6. **Send to Agent**: Agent validates and applies operation
7. **Update UI**: UI reflects the change

### Save Flow

1. **Open Dialog**: User clicks save button
2. **Collect Operations**: Get all operations from history (up to current index)
3. **Client Validation**: Validate all operations client-side
4. **Agent Validation**: Send to agent for server-side validation
5. **Show Results**: Display validation panel with errors/warnings
6. **User Decision**: User can cancel or proceed (if valid or warnings only)
7. **Apply Edits**: Send operations to agent for application
8. **Git Commit**: Commit changed files with user's message
9. **Clear History**: Reset edit history and selection

## Configuration

### Agent Client

```typescript
{
  url: "ws://localhost:8080",  // WebSocket URL
  token: "did:key:...",         // DID:key token
  reconnect: true,              // Enable auto-reconnect
  pingInterval: 30000,          // Ping interval (ms)
  timeout: 60000,               // Request timeout (ms)
}
```

### Edit History

```typescript
{
  maxHistorySize: 100,  // Maximum operations in history
}
```

## Error Handling

### Connection Errors
- Auto-reconnect with exponential backoff
- User notification via connection indicator
- Graceful degradation (WASM commands still work)

### Validation Errors
- Client-side: Shown immediately in validation panel
- Agent-side: Shown after validation request
- Prevents invalid operations from being saved

### Save Errors
- Shown in save dialog
- User can retry or cancel
- History preserved on error

## Testing

### Manual Testing Checklist

#### Connection
- [ ] Connect with valid DID:key token
- [ ] Connect with invalid token (should fail)
- [ ] Disconnect and reconnect
- [ ] Agent offline (should auto-reconnect when back online)
- [ ] Connection quality indicator updates

#### Git Operations
- [ ] View status with changes
- [ ] View status without changes
- [ ] View diff (staged and unstaged)
- [ ] Commit changes
- [ ] View commit history

#### IFC Import/Export
- [ ] Import IFC file with progress
- [ ] Export to IFC with progress
- [ ] View import statistics
- [ ] Download exported file

#### Floor Editing
- [ ] Select mode works
- [ ] Draw room mode works
- [ ] Add equipment mode works
- [ ] Delete selected object
- [ ] Undo operation
- [ ] Redo operation
- [ ] Undo/Redo buttons enable/disable correctly

#### Save Flow
- [ ] Open save dialog
- [ ] Validate with no changes (should fail)
- [ ] Validate with valid changes
- [ ] Validate with invalid changes (should show errors)
- [ ] Save valid changes
- [ ] Cancel save dialog

## Exit Criteria

M04 is considered complete when:

- [x] Agent WebSocket client implemented with auto-reconnect
- [x] DID:key authentication working
- [x] Connection indicator showing real-time status
- [x] Git commands (status, diff, commit, log) working
- [x] IFC import/export with progress tracking
- [x] Edit operations defined and implemented
- [x] Undo/redo history working
- [x] Client-side validation implemented
- [x] EditToolbar component functional
- [x] ValidationPanel showing results
- [x] SaveDialog integrating validation and commit
- [x] All TypeScript type checks passing
- [ ] Integration testing complete
- [ ] Documentation complete

## Future Enhancements

### Short-term
- Add keyboard shortcuts (V for select, R for room, E for equipment)
- Add snap-to-grid for drawing
- Add room/equipment property editor
- Enhance Git UI with branch selection

### Medium-term
- Add wall editing tools
- Add collaborative editing (real-time sync)
- Add 3D preview integration
- Add AR preview integration

### Long-term
- Add conflict resolution UI
- Add offline editing with sync
- Add change review/approval workflow
- Add AI-assisted floor plan generation

## Dependencies

### Runtime
- `zustand`: State management
- `lucide-react`: Icons
- WebSocket API (browser native)
- sessionStorage API (browser native)

### Development
- TypeScript 5.x
- React 18.x
- Vite 5.x

## Related Documents

- [M01: WASM Integration](./M01_WASM_INTEGRATION.md)
- [M02: State Management](./M02_STATE_MANAGEMENT.md)
- [M03: Floor Viewer](./M03_FLOOR_VIEWER.md)
- [Agent Protocol Specification](./AGENT_PROTOCOL.md)
- [Git Workflow](./GIT_WORKFLOW.md)
