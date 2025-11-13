# ArxOS PWA Development Roadmap

**Version:** 2.0
**Last Updated:** 2025-11-12
**Status:** Planning → Implementation

---

## Executive Summary

This roadmap outlines the development plan for the ArxOS Progressive Web Application, a browser-based interface for Git-native building management. The PWA shares core logic with the CLI via WebAssembly while providing an accessible, offline-first user experience.

**MVP Scope:** Milestones 01-05 (estimated 9-10 weeks solo development)
**Post-Launch Features:** Milestones 06-08 (iterative releases)

---

## Table of Contents

1. [MVP Definition](#mvp-definition)
2. [Architecture Overview](#architecture-overview)
3. [Development Timeline](#development-timeline)
4. [Milestones](#milestones)
   - [M01: Foundation](#milestone-01--foundational-pwa-setup)
   - [M02: Command Shell](#milestone-02--command-centric-shell)
   - [M03: Floor Viewer](#milestone-03--floor-plan-viewer)
   - [M04: Agent & Editing](#milestone-04--desktop-agent--editing)
   - [M05: Offline Sync](#milestone-05--offline-first-sync)
   - [M06: Collaboration](#milestone-06--collaboration--messaging)
   - [M07: 3D Visualization](#milestone-07--3d-visualization--optional-ar)
   - [M08: Quality Release](#milestone-08--quality-testing--release-readiness)
5. [Critical Path Dependencies](#critical-path-dependencies)
6. [Risk Mitigation](#risk-mitigation)

---

## MVP Definition

**What ships with M01-M05:**

✅ **Core Functionality**
- Import IFC files via desktop agent
- View floor plans in browser (pan, zoom, selection)
- Edit rooms and equipment with constraint validation
- Commit changes to Git repository
- Work offline with automatic sync when connected
- All operations run locally (zero infrastructure cost)

✅ **User Experience**
- Keyboard-first command palette
- Console output for all operations
- Responsive layout (desktop + tablet)
- Offline indicator and sync status

✅ **Technical Foundation**
- React + Vite + TypeScript
- WASM integration with Rust core
- Zustand state management
- IndexedDB persistence
- Desktop agent bridge (WebSocket)

❌ **Not in MVP** (Post-Launch)
- Real-time collaboration (M06)
- 3D visualization / WebXR AR (M07)
- Comprehensive E2E test coverage (M08)
- Mobile-optimized UI

**Value Proposition for MVP Users:**
"Manage building as-built data using Git version control. Import IFC files, edit equipment and rooms, track changes over time—all running locally with no subscription required."

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (PWA)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   React UI   │  │ Zustand Store│  │  IndexedDB   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────┬───┴──────────────────┘              │
│                        │                                     │
│              ┌─────────▼─────────┐                          │
│              │   WASM Bridge     │ (arxos-wasm)             │
│              └─────────┬─────────┘                          │
└────────────────────────┼──────────────────────────────────────┘
                         │ WebSocket (localhost:8765)
                         │
┌────────────────────────▼──────────────────────────────────────┐
│                  Desktop Agent                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Git Manager  │  │ IFC Parser   │  │ File System  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                               │
│  ┌───────────────────────────────────────────────────┐       │
│  │        Local Git Repository (.arxos/)             │       │
│  └───────────────────────────────────────────────────┘       │
└───────────────────────────────────────────────────────────────┘
```

### Module Structure

```
pwa/
├── src/
│   ├── app/              # Application shell, routing, providers
│   ├── modules/          # Feature modules (organized by milestone)
│   │   ├── command/      # M02: Command palette & console
│   │   ├── floor/        # M03-M04: Floor viewer & editor
│   │   ├── agent/        # M04: Desktop agent client
│   │   ├── offline/      # M05: Offline sync coordinator
│   │   ├── collaboration/# M06: Real-time messaging (post-MVP)
│   │   └── ar/           # M07: 3D viz & WebXR (post-MVP)
│   └── lib/              # Shared utilities
│       ├── store/        # Zustand store slices
│       ├── wasm/         # WASM loading & TypeScript bindings
│       └── storage/      # IndexedDB wrappers
├── tests/                # E2E tests (Playwright)
└── public/               # Static assets, WASM bundle
```

### Data Flow Patterns

**Read-only operations** (M03):
```
User → UI → WASM → Display
```

**Write operations** (M04+):
```
User → UI → Agent (WebSocket) → Rust Core → Git Commit → Response
```

**Offline operations** (M05):
```
User → UI → IndexedDB Queue → (reconnect) → Agent → Git Commit
```

---

## Development Timeline

### Solo Developer Estimates

| Milestone | Duration | Cumulative | Deliverable |
|-----------|----------|------------|-------------|
| **M01** Foundation | 1 week | 1 week | PWA scaffold + WASM loader |
| **M02** Command Shell | 2 weeks | 3 weeks | Command palette working |
| **M03** Floor Viewer | 1 week | 4 weeks | Read-only floor plans |
| **M04** Agent & Editing | 3 weeks | 7 weeks | Full edit + Git commit |
| **M05** Offline Sync | 2 weeks | **9 weeks** | **MVP LAUNCH** |
| **M06** Collaboration | 3 weeks | 12 weeks | v1.1 release |
| **M07** 3D Visualization | 2 weeks | 14 weeks | v1.2 release |
| **M08** Quality Polish | Ongoing | - | Continuous improvement |

**MVP Launch Target:** ~2.5 months from kickoff
**Full Feature Set:** ~3.5 months

### Assumptions
- 25-30 hours/week development time
- No major architectural rewrites
- WASM API design completed upfront
- Existing Rust core stable

---

## Milestones

---

## Milestone 01 – Foundational PWA Setup

**Duration:** 1 week
**Status:** Not Started
**Dependencies:** None

### Overview
Establish the baseline React/Vite/Zustand shell, WASM integration hooks, and developer workflow so subsequent milestones can iterate safely.

### Scope
- Scaffold web app in `pwa/` with routing, layout, and global state provider
- Integrate existing WASM bundle loading from `crates/arxos-wasm`
- Configure testing infrastructure (Jest + React Testing Library)
- Document developer workflow and tooling requirements
- Baseline CI/script updates for building the web bundle
- **NEW:** Create WASM API design document

### Architecture Notes
- Use Vite with TypeScript + React; directory structure `pwa/src/app`, `pwa/src/modules`, `pwa/src/lib`
- Zustand store initialized as composable slices; no persistence yet
- WASM bundle served from `/pkg` output; add dynamic loader utility
- Base layout should support keyboard-first navigation (matching CLI feel)
- Jest configured for unit testing from the start

### Implementation Tasks

#### 1. PWA Scaffold
- Initialize Vite React TS project inside `pwa/`
- Configure ESLint/Prettier consistent with repo style
- Set up `src/app/App.tsx`, `src/app/routes.tsx`, and shell components
- Create base layout with header, main content area, and footer placeholders

#### 2. Zustand Global Store
- Create `src/lib/store/index.ts` with root store + typed hooks
- Set up composable slice pattern (prepare for command, floor, agent slices)
- Provide store via context wrapper in `src/app/AppProviders.tsx`
- Add basic devtools integration

#### 3. WASM Bootstrap
- Add utility `src/lib/wasm/loadWasm.ts` to load `pkg/arxos_wasm_bg.wasm`
- Implement loading state management (loading, ready, error)
- Verify existing WASM exports (command catalog, AR helpers) can be called
- Create TypeScript type definitions for WASM exports

#### 4. WASM API Design Document
- **NEW:** Create `docs/web/WASM_API.md` documenting all planned Rust↔WASM↔TypeScript interfaces
- Map exports needed for each milestone
- Define TypeScript types matching Rust structs
- Document serialization patterns (serde → JSON → TS)
- Mark implemented vs. planned exports

#### 5. Testing Infrastructure (Baseline)
- Configure Jest with TypeScript support
- Set up React Testing Library
- Add baseline test: `App.test.tsx` renders without crashing
- Configure coverage reporting
- Add npm scripts: `test`, `test:watch`, `test:coverage`

#### 6. Tooling + Scripts
- Add npm scripts: `dev`, `build`, `lint`, `format`, `type-check`
- Update `package.json` with workspace-level dependency versions
- Document in `docs/web/DEVELOPMENT.md` (install steps, npm commands, architecture)
- Add `.nvmrc` or document Node version requirement

#### 7. CI Integration (Baseline)
- Extend `scripts/build-workspace.sh` to build PWA bundle
- Add CI job: install deps, lint, test, build
- Ensure build fails-fast when npm deps missing
- Cache `node_modules` for faster builds

### Testing Strategy
- **Unit Tests:** App renders, store initializes, WASM loader handles states
- **Smoke Test:** `npm run build` succeeds locally and in CI
- **Manual Verification:** Run `npm run dev`, confirm WASM loader resolves and logs "ready"

### Exit Criteria
- ✅ `npm run dev` launches development server
- ✅ `npm run build` succeeds; WASM loader verified
- ✅ `npm run test` passes with baseline test
- ✅ `npm run lint` passes with zero errors
- ✅ Developer docs updated with setup instructions
- ✅ CI/build script invokes PWA build without errors
- ✅ `docs/web/WASM_API.md` created and reviewed

### Deliverables
- Working Vite + React + Zustand scaffold
- WASM loader utility functional
- Testing infrastructure configured
- `docs/web/DEVELOPMENT.md` and `docs/web/WASM_API.md`
- CI pipeline building PWA

---

## Milestone 02 – Command-Centric Shell

**Duration:** 2 weeks
**Status:** Not Started
**Dependencies:** M01 complete

### Overview
Deliver the browser-based command palette and console driven by WASM command metadata, mirroring the terminal-first experience.

### Scope
- Load command catalog via WASM bindings
- Implement keyboard-driven command palette with fuzzy search
- Render command output in a console panel
- Provide local execution shim (agent integration arrives in M04)
- Add Playwright E2E testing baseline

### Architecture Notes
- Organize command UI under `pwa/src/modules/command`
- State slices: `commandCatalog`, `commandHistory`, `paletteState`
- Use `fuse.js` for fuzzy search
- Console component should support streaming updates (prepare for future agent)
- Command execution initially runs WASM stubs (returns mock output)

### Implementation Tasks

#### 1. WASM Command Client
- Create `src/lib/wasm/commands.ts` wrapping WASM command exports
- Fetch command metadata on app load, hydrate store
- Handle WASM errors gracefully (fallback to empty catalog with warning)
- Type definitions for `Command`, `CommandMetadata`, `CommandResult`

#### 2. Command Palette UI
- Implement `CommandPalette` component (modal with list + keyboard navigation)
- Support shortcut (`Ctrl/Cmd+K`) and focus trapping
- Fuzzy search integration with highlighting
- Keyboard navigation: ↑/↓ to select, Enter to execute, Esc to close
- Recent commands shown at top (from history slice)

#### 3. Command Console
- Create `CommandConsole` component displaying command execution output
- Support for log levels (info, warn, error, success)
- Syntax highlighting for code output (optional, using `prism-react-renderer`)
- Clear console action
- Auto-scroll to latest output

#### 4. Command Execution Pipeline
- Create executor service: `src/lib/command/executor.ts`
- Local executor runs WASM command stubs (returns mock output for now)
- Capture logs in store; dispatch to console component
- Error handling with user-friendly messages

#### 5. History & Bookmarks
- Persist recent commands in memory slice (no IndexedDB yet)
- Show recent commands in palette
- Provide quick re-run shortcuts (Ctrl/Cmd+Shift+R for last command)
- Limit history to 50 most recent

#### 6. Testing
- **Unit Tests:** Store reducers/selectors, fuzzy search logic, executor
- **Component Tests:** React Testing Library for palette open/close, keyboard nav, command selection
- **WASM Tests:** `wasm-pack test` verifying command metadata shape
- **E2E (Playwright):** Open palette, search command, execute, verify output in console

#### 7. Playwright Setup (NEW)
- Install Playwright and configure baseline project
- Create first E2E test: open palette → select command → verify console output
- Add npm script: `test:e2e`
- Document Playwright setup in `docs/web/DEVELOPMENT.md`

### Testing Strategy
- Unit tests: command execution, store state updates, search filtering
- Component tests: palette interactions, console rendering
- E2E: full command workflow (palette → execute → console)
- WASM-pack: command catalog exports

### Exit Criteria
- ✅ Palette loads commands from WASM
- ✅ Keyboard shortcut (Cmd/Ctrl+K) opens palette
- ✅ Fuzzy search filters commands correctly
- ✅ Executing a command displays output in console
- ✅ Keyboard shortcuts documented in UI (help panel or tooltip)
- ✅ Unit/integration tests pass
- ✅ First Playwright E2E test passes

### Deliverables
- Functional command palette with fuzzy search
- Console panel displaying command output
- Command history tracking
- Playwright E2E test suite baseline
- Updated WASM_API.md with command module

---

## Milestone 03 – Floor Plan Viewer

**Duration:** 1 week
**Status:** Not Started
**Dependencies:** M02 complete
**⚠️ UPDATED:** Viewer only, no editing (editing moved to M04)

### Overview
Implement a read-only interactive 2D floor plan viewer that consumes building geometry from the Rust core via WASM. This milestone focuses on visualization without modification capabilities.

### Scope
- Expose geometry DTOs via WASM (buildings, floors, rooms, equipment)
- Render floor plans with Canvas 2D (pan, zoom, layers)
- Display selection and properties sidebar
- **NO EDITING** in this milestone (deferred to M04)

### Architecture Notes
- Module location: `pwa/src/modules/floor`
- Rendering engine: Canvas2D initially (interface allows future WebGL upgrade)
- Leverage existing spatial data (`SpatialEntity`, bounding boxes) from `crates/arx`
- Read-only operations only; all data flows from WASM → UI

### Implementation Tasks

#### 1. Geometry Exposure (WASM)
- Extend `crates/arxos-wasm` to expose building/floor/room DTOs
- Export functions: `get_building()`, `get_floor(id)`, `get_rooms(floor_id)`, `get_equipment(room_id)`
- Serialize spatial data (bounding boxes, coordinates) to JSON
- Update `docs/web/WASM_API.md` with geometry module

#### 2. TypeScript Geometry Adapters
- Create `src/lib/wasm/geometry.ts` converting WASM DTOs to frontend models
- Type definitions: `Building`, `Floor`, `Room`, `Equipment`, `BoundingBox`, `Coordinate`
- Adapter functions handling coordinate transformations if needed

#### 3. Renderer Core (Canvas2D)
- Implement scene graph: `src/modules/floor/renderer/SceneGraph.ts`
- Layers: background, grid, rooms, equipment, overlays
- Pan/zoom with mouse/trackpad (using canvas transforms)
- Selection rendering (highlight on click)
- Hover effects with cursor change

#### 4. Floor Viewer Component
- Create `FloorViewer` component wrapping canvas
- Controls: zoom in/out buttons, fit-to-view, reset view
- Layer toggles (show/hide rooms, equipment, grid)
- Loading state while fetching geometry from WASM

#### 5. Properties Sidebar
- Display selected element properties (room name, dimensions, equipment details)
- Read-only text display (no inputs yet)
- "Copy to clipboard" for addresses/IDs
- Clear selection action

#### 6. Store Integration
- Add `floorSlice` to Zustand store
- State: current floor, selected element, viewport transform, layer visibility
- Actions: `selectElement`, `setFloor`, `updateViewport`, `toggleLayer`

#### 7. Testing
- **Unit Tests:** Geometry adapters, coordinate transformations, scene graph logic
- **Component Tests:** Canvas rendering (jest-canvas-mock), selection, pan/zoom interactions
- **WASM Tests:** `wasm-pack test` validating geometry export format
- **E2E:** Load building → select floor → view plan → select room → verify properties

### Testing Strategy
- Unit: geometry adapters, renderer utilities
- Integration: Canvas interactions with mocked geometry data
- E2E: Full viewer workflow with fixture IFC (`tests/fixtures/ifc/simple.ifc`)

### Exit Criteria
- ✅ Floor plan renders from WASM geometry data
- ✅ Pan and zoom work smoothly
- ✅ Clicking an element selects it and shows properties
- ✅ Layer toggles control visibility
- ✅ Works with test fixture IFC file
- ✅ Tests pass (unit + E2E)
- ✅ No editing capabilities (intentionally deferred to M04)

### Deliverables
- Read-only floor plan viewer
- Properties sidebar
- Canvas renderer with pan/zoom
- WASM geometry exports functional
- E2E test coverage for viewer

---

## Milestone 04 – Desktop Agent & Editing

**Duration:** 3 weeks
**Status:** Not Started
**Dependencies:** M03 complete
**⚠️ UPDATED:** Combines agent connectivity + editing features

### Overview
Connect the PWA to the Rust desktop agent, enabling real Git/IFC operations. Add editing capabilities to the floor viewer with full round-trip validation and Git commits.

### Scope
- Implement agent WebSocket client with DID:key authentication
- Route command executions through the agent
- Stream command output/logs to console UI
- Add editing tools to floor viewer (create/modify/delete rooms and equipment)
- Implement validation pipeline through agent → Rust → Git
- Support IFC import/export and Git status flows

### Architecture Notes
- Module location: `pwa/src/modules/agent`
- Use native `WebSocket` API with reconnect/backoff logic
- Token workflow: obtain DID:key token from user, persist in sessionStorage (memory only)
- Command execution pipeline: palette → executor → agent RPC → stream results
- Editing operations queue updates and send to agent for validation + commit

### Implementation Tasks

#### 1. Agent Client Library
- Define TypeScript client mirroring `crates/arxos-agent` protocol
- Protocol: handshake, auth, RPC request/response, streaming
- Implement reconnect with exponential backoff
- Online/offline indicators in UI
- WebSocket message types: `Command`, `Stream`, `Response`, `Error`

#### 2. Authentication Flow
- DID:key token input UI (modal on first launch)
- Validate connection with agent handshake
- Store token in sessionStorage (ephemeral)
- Visual indicator when connected/disconnected
- Graceful fallback messaging if agent unavailable

#### 3. Command Routing
- Extend executor from M02 to route commands through agent
- Handle streaming responses (console updates in real-time)
- Error channel handling with user-friendly messages
- Command execution states: queued, running, completed, failed

#### 4. Git/IFC Command UI
- Dedicated panels in command console for:
  - `import` (IFC file selection via agent filesystem access)
  - `export` (download YAML/glTF/USDZ)
  - `status` (Git status display)
  - `diff` (visual diff viewer)
- Progress indicators for long-running operations
- Final summaries with action buttons (commit, discard, etc.)

#### 5. Floor Editing Tools
- Tool palette: Select, Move, Resize Room, Add Room, Add Equipment, Delete
- Click/drag interactions for each tool
- Visual feedback during editing (preview, ghost outline)
- Constraint feedback in real-time (e.g., "Room overlaps with Room-101")

#### 6. Validation Pipeline
- Send edit operations to agent: `validate_room_edit(room_data)`
- Display validation results (errors, warnings) before commit
- Batch operations: allow multiple edits, validate all together
- Undo/redo stack within floor editor store slice

#### 7. Save/Apply Flow
- "Save" button collects all pending edits
- Send to agent for YAML diff preview
- Display diff summary in console
- User confirms → agent commits to Git
- Refresh floor viewer with committed data

#### 8. Testing
- **Unit Tests:** WebSocket client (mocked server using Node `ws`), auth flow, reconnect logic
- **Integration Tests:** Command execution through agent (mock responses)
- **Component Tests:** Editing tools, validation feedback rendering
- **E2E Tests:**
  - Connect to agent → import IFC → view floor
  - Edit room → validate → commit → verify Git change
- **Manual Checklist:** Test real agent on macOS/Linux/Windows

### Testing Strategy
- Unit: WebSocket client, auth, message parsing
- Integration: Agent RPC calls with mocked responses
- E2E: Full editing workflow (requires running agent process)
- Manual: Cross-platform agent compatibility

### Exit Criteria
- ✅ PWA connects to desktop agent via WebSocket
- ✅ DID:key authentication works
- ✅ Commands execute through agent with streamed output
- ✅ IFC import workflow functional (agent → WASM → UI)
- ✅ Floor editing tools working (add/modify/delete rooms and equipment)
- ✅ Validation errors displayed before commit
- ✅ Git commit from UI creates actual Git commit via agent
- ✅ Automated tests (mock server) pass
- ✅ Manual test checklist completed

### Deliverables
- Agent WebSocket client library
- Auth flow UI
- Git/IFC command workflows
- Full editing capabilities in floor viewer
- Validation pipeline functional
- E2E tests with agent integration

---

## Milestone 05 – Offline-First Sync

**Duration:** 2 weeks
**Status:** Not Started
**Dependencies:** M04 complete
**⚠️ UPDATED:** Adds Git branch-per-session conflict resolution

### Overview
Enable the PWA to function offline, queue edits, and synchronize with the desktop agent once connectivity returns. Includes conflict resolution strategy using Git branches.

### Scope
- Introduce service worker for asset caching and background sync
- Persist critical state (edits, command queue, session info) to IndexedDB
- Implement sync coordinator to replay queued actions through the agent
- **NEW:** Git branch-per-session for conflict handling
- Conflict detection and resolution UI

### Architecture Notes
- Modules: `pwa/src/modules/offline`, `pwa/src/lib/storage`
- Service worker built with Workbox (Vite integration via `vite-plugin-pwa`)
- IndexedDB utility using `idb-keyval` with typed wrappers
- Sync coordinator listens to store changes and schedules background sync tasks
- **NEW:** Each offline session creates ephemeral Git branch (`arxos/session-{uuid}`)

### Implementation Tasks

#### 1. Service Worker Setup
- Install `vite-plugin-pwa` and configure Workbox
- Cache strategy: NetworkFirst for HTML, CacheFirst for assets
- Cache WASM bundle and critical JSON data
- Implement background sync event to trigger command replay
- Register service worker in `src/app/main.tsx`

#### 2. Storage Layer
- Create typed IndexedDB wrappers:
  - `CommandQueueStore` (queued commands with args)
  - `FloorEditStore` (pending edits with timestamps)
  - `SessionStore` (session ID, branch name, sync status)
- Persist relevant Zustand slices on state changes
- Migration strategy for storage schema changes

#### 3. Session Branch Management (NEW)
- On PWA load in offline mode: create session ID (`uuid`)
- Agent API call: `create_session_branch(session_id)` → creates `arxos/session-{uuid}`
- All offline commits go to session branch
- On reconnect: agent attempts `git merge session-{uuid} → main`
- If merge succeeds: delete session branch, clear queue
- If conflicts: trigger conflict resolution UI

#### 4. Conflict Resolution UI (NEW)
- Detect merge conflicts from agent response
- Display conflict modal with three options:
  - **Accept Mine:** Keep session branch changes (agent: `git merge -X ours`)
  - **Accept Theirs:** Discard session changes (agent: delete session branch)
  - **Manual Merge:** Show three-way diff viewer (theirs / mine / merged)
- For manual merge: visual diff with line-by-line choose (similar to GitHub conflict editor)
- After resolution: agent completes merge and cleans up

#### 5. Sync Coordinator
- Detect online/offline transitions (`navigator.onLine` + WebSocket status)
- On reconnect: retrieve queued commands from IndexedDB
- Replay commands via agent in original order
- Handle partial failures (some commands succeed, others fail)
- Update UI with sync progress (X of Y commands replayed)

#### 6. UI Feedback
- Offline indicator in app header (yellow badge)
- Queued actions count ("3 changes pending sync")
- Sync status toast/notification (success, failure, conflicts)
- Manual sync trigger button (force sync now)

#### 7. Testing
- **Unit Tests:** Storage wrappers, sync coordinator logic, conflict detection
- **Integration Tests:** Stub `navigator.onLine`, simulate offline→online transition
- **E2E Tests:** Playwright with offline mode (browser context API)
  - Go offline → edit floor → go online → verify sync
  - Simulate conflict → verify resolution UI
- **Manual QA:** Airplane mode, reconnect scenarios, actual Git conflicts

### Testing Strategy
- Unit: storage operations, queue management, branch creation logic
- Integration: offline/online state changes, command replay
- E2E: full offline workflow with conflict simulation
- Manual: real-world network disruption scenarios

### Exit Criteria
- ✅ PWA works offline for viewing and editing
- ✅ Edits queue in IndexedDB when offline
- ✅ Upon reconnection, queued actions replay automatically
- ✅ Session branches created and merged correctly
- ✅ Conflict resolution UI functional
- ✅ Manual conflict resolution works (three-way diff)
- ✅ Service worker caching works (verified with DevTools)
- ✅ IndexedDB persistence tested across page reloads
- ✅ Tests pass (unit + integration + E2E)

### Deliverables
- Service worker with offline caching
- IndexedDB persistence layer
- Sync coordinator with queue replay
- Session branch management
- Conflict resolution UI
- Comprehensive offline tests

---

## Milestone 06 – Collaboration & Messaging

**Duration:** 3 weeks (Post-MVP)
**Status:** Not Started
**Dependencies:** M05 complete
**⚠️ UPDATED:** Agent-relay MVP only (no hosted service yet)

### Overview
Provide real-time collaboration inside the PWA, allowing users to share context, leave comments tied to building elements, and work offline with queued updates. Initial implementation uses desktop agent as relay (local network only).

### Scope
- Define collaboration messaging protocol (agent relay transport)
- Build collaboration UI components (rooms, threads, mention linking)
- Integrate with offline queue from M05
- **Deferred:** Hosted relay service (future v2.0 feature)

### Architecture Notes
- Module: `pwa/src/modules/collaboration`
- **Transport:** Route via desktop agent (WebSocket) for intranet/VPN use
- Message schema includes references (`building_path`, `room_id`, `equipment_id`)
- Offline compatibility: messages queue in IndexedDB until connection restored
- Agent discovers peers via:
  - Manual connection (user enters host:port)
  - OR mDNS/Bonjour for same-network discovery (optional enhancement)

### Implementation Tasks

#### 1. Protocol Definition
- Define message envelope schema:
  - `type` (chat, comment, ping, ack)
  - `from` (user DID)
  - `to` (room_id or direct user)
  - `payload` (message content, attachments, references)
  - `timestamp`, `message_id`
- Ack semantics (delivery confirmation)
- Versioning for protocol evolution

#### 2. Agent Relay Module
- Extend desktop agent with relay capability (`crates/arxos-agent/src/relay.rs`)
- WebSocket server accepts connections from multiple PWA clients
- Broadcast messages to subscribers (room-based pub/sub)
- Authentication reuses DID:key tokens from M04
- Store message history (SQLite or YAML files)

#### 3. Connection Discovery
- **Option A:** Manual connection UI (user inputs agent host:port)
- **Option B:** mDNS/Bonjour for automatic local network discovery
- Connection status indicator (connected peers count)
- Fallback: if agent unavailable, collaboration disabled with explanation

#### 4. Collaboration Client
- Create `src/modules/collaboration/CollaborationClient.ts`
- Connect to agent relay, subscribe to rooms
- Send/receive messages with offline queue integration
- Handle reconnect and message replay (deduplication by `message_id`)

#### 5. UI Components
- **Collaboration Sidebar:**
  - Room list (filter by building/floor)
  - Unread message indicators
  - Active users list
- **Thread View:**
  - Message list with timestamps and authors
  - Markdown rendering for message content
  - Attachment links (GitHub issues, external docs)
  - Context highlighting: click message → highlight referenced equipment on floor plan
- **Composer:**
  - Input field with markdown support
  - @mentions autocomplete
  - Attach building element reference (current selection)

#### 6. Context Linking
- When comment references room/equipment, store `room_id` or `equipment_id`
- Clicking comment highlights element on floor plan viewer
- Bi-directional: selecting element shows related comments in sidebar

#### 7. Notifications
- Toast for new messages (collapsible)
- Browser notifications via service worker (optional, requires permission)
- Unread count badge on collaboration tab

#### 8. Offline Integration
- Queue outgoing messages in IndexedDB if offline
- On reconnect, send queued messages through agent
- Sync message history from agent on connection

#### 9. Testing
- **Unit Tests:** Protocol message parsing, client state management
- **Integration Tests:** Mock WebSocket relay, message send/receive flow
- **E2E Tests:** Playwright with two browser contexts (simulate two users)
  - User A sends message → User B receives
  - User A references room → User B sees highlight
- **Manual Tests:** Two devices on same network with agent-relay

### Testing Strategy
- Unit: message serialization, client logic
- Integration: mocked relay server, offline queue
- E2E: multi-user scenarios with Playwright
- Manual: real network with multiple devices

### Exit Criteria
- ✅ Users can connect to agent-relay
- ✅ Send and receive messages in collaboration rooms
- ✅ Context highlighting works (message → floor plan element)
- ✅ Offline messages queue and replay on reconnect
- ✅ Protocol documented for agent-relay deployment
- ✅ Tests pass (unit + integration + E2E)
- ✅ Manual multi-user test successful

### Deliverables
- Agent-relay module in desktop agent
- Collaboration client library
- Collaboration UI (sidebar, threads, composer)
- Context linking between messages and floor plan
- E2E tests with multi-user scenarios
- Documentation: `docs/collaboration/AGENT_RELAY.md`

### Future Work (Post-Launch)
- **Hosted Relay Service:** Optional cloud relay for cross-site collaboration
- **End-to-End Encryption:** Encrypt messages between clients
- **Rich Attachments:** Image uploads, file sharing
- **Presence Indicators:** Show who's viewing which floor in real-time

---

## Milestone 07 – 3D Visualization & Optional AR

**Duration:** 2 weeks (Post-MVP)
**Status:** Not Started
**Dependencies:** M04 complete (can run in parallel with M06)
**⚠️ UPDATED:** Reframed as 3D viewer with WebXR as secondary feature

### Overview
Implement a Three.js-based 3D visualization of floor plans with optional WebXR overlays where supported. Primary deliverable is desktop-friendly 3D viewer; AR is experimental enhancement.

### Scope
- 3D floor plan viewer using Three.js
- Equipment overlay visualization (simulated anchors)
- Desktop-friendly controls (mouse/keyboard)
- WebXR support where available (Android Chrome, newer iOS Safari)
- Graceful fallback for unsupported devices

### Architecture Notes
- Module: `pwa/src/modules/ar`
- Abstraction layer separating WebXR-specific code from rendering
- Use feature detection (`navigator.xr`) and permission requests
- Primary renderer: Three.js with OrbitControls (desktop)
- Secondary renderer: Three.js with WebXR session (mobile AR)

### Implementation Tasks

#### 1. Capability Detection
- Implement detection utility: `src/modules/ar/capabilities.ts`
- Check `navigator.xr` availability
- Test for WebXR session support (`immersive-ar`)
- Display detailed messaging (supported browsers/devices)
- Provide "simulation mode" toggle for testing on desktop

#### 2. 3D Floor Viewer (Primary Deliverable)
- Set up Three.js scene with lighting, camera, renderer
- Load floor geometry from WASM (convert to Three.js meshes)
- Render rooms as extruded polygons (height from floor-to-floor)
- Render equipment as colored boxes or simple 3D models
- OrbitControls for desktop (mouse pan/zoom/rotate)
- Layer toggles (show/hide floors, equipment types)

#### 3. Equipment Overlays
- Visualize equipment positions from spatial data
- Color-coding by equipment type (HVAC, plumbing, electrical)
- Info tooltips on hover (equipment name, status)
- Click to select → show properties panel

#### 4. WebXR AR Mode (Secondary)
- Detect AR session capability on launch
- AR mode toggle button (only visible if supported)
- Start WebXR session with `immersive-ar` mode
- Render floor plan overlays anchored to detected planes
- Hit-test API for placing equipment in real space
- Exit AR button

#### 5. Fallback & Simulation
- For unsupported devices: display 3D viewer in regular mode
- Simulation mode: fake camera feed with overlaid 3D scene
- Clear messaging: "AR requires Android Chrome or iOS Safari 17+"
- Link to compatibility documentation

#### 6. UI/UX
- AR/3D mode toggle within floor viewer
- Onboarding tooltip: "Move device to calibrate" (AR mode)
- Status indicators: AR session active, plane detected
- Logging panel for debugging WebXR (integrated with console)

#### 7. Testing
- **Unit Tests:** Capability detection, Three.js scene setup, geometry conversion
- **Integration Tests:** Rendering with mocked geometry data
- **E2E Tests:** Playwright with WebXR polyfill (basic flows only)
- **Manual Device Matrix:**
  - Desktop: Chrome, Firefox, Safari (3D viewer)
  - Android: Chrome (WebXR AR)
  - iOS: Safari 17+ (WebXR AR)
  - Fallback: Older browsers (graceful degradation)

### Testing Strategy
- Unit: capability detection, 3D scene logic
- Integration: rendering with fixture data
- E2E: basic 3D viewer interaction (WebXR polyfill for CI)
- Manual: real device testing for AR mode

### Exit Criteria
- ✅ 3D floor viewer works on desktop with mouse controls
- ✅ Equipment overlays render correctly in 3D
- ✅ AR mode works on supported devices (Android Chrome tested)
- ✅ Fallback path works on unsupported devices (shows 3D viewer)
- ✅ Capability detection accurate
- ✅ Device support matrix documented
- ✅ Tests pass (unit + E2E)
- ✅ Manual device testing completed

### Deliverables
- Three.js 3D floor viewer
- Equipment overlay visualization
- WebXR AR mode (where supported)
- Fallback mode for unsupported devices
- Device compatibility matrix
- Documentation: `docs/features/3D_VISUALIZATION.md`

### Future Enhancements
- glTF model loading for equipment (instead of boxes)
- Real-time sensor data overlays (temperature heatmaps)
- VR mode for desktop headsets
- Advanced WebXR features (plane detection, image tracking)

---

## Milestone 08 – Quality, Testing & Release Readiness

**Duration:** Ongoing (Post-MVP)
**Status:** Not Started
**Dependencies:** M05 complete for MVP release; M07 complete for full release
**⚠️ UPDATED:** Focuses on comprehensive scenarios and release process (baseline testing moved to earlier milestones)

### Overview
Ensure production-ready quality with comprehensive automated testing, finalized documentation, and repeatable release process. This milestone is ongoing and iterative.

### Scope
- Expand E2E test coverage to comprehensive scenarios
- Performance benchmarking and optimization
- Accessibility audit and improvements
- Cross-browser/device compatibility validation
- Release checklist and artifact validation
- Documentation finalization

### Architecture Notes
- Testing configuration under `pwa/` (Jest, Playwright configs already in place from earlier milestones)
- GitHub Actions workflows in `.github/workflows/`
- Documentation updates across `docs/web/`, `docs/core/`, and README
- Release checklist: `docs/release/CHECKLIST.md`

### Implementation Tasks

#### 1. Comprehensive E2E Scenarios
- **Multi-User Workflows:**
  - User A edits floor, User B edits same floor → conflict resolution
  - Collaboration: multiple users exchanging messages
- **Complex Workflows:**
  - Import large IFC → edit 50+ rooms → commit → export
  - Offline for extended period → accumulate 20+ edits → sync
- **Error Recovery:**
  - Network failure mid-commit → verify rollback
  - Agent crash during command → verify graceful error
- **Cross-Feature Integration:**
  - AR scan → import → edit in 2D → visualize in 3D → commit

#### 2. Performance Optimization
- **Benchmarking:**
  - Measure FPS for 3D viewer with 100+ equipment
  - Measure floor render time for buildings with 10+ floors
  - Measure WASM load time and initialization
- **Optimizations:**
  - Code splitting (lazy load modules)
  - WASM bundle size reduction (feature flags)
  - Canvas rendering optimizations (off-screen canvas, web workers)
  - IndexedDB query performance (indexing strategy)
- **Performance Budget:**
  - First Contentful Paint < 1.5s
  - Time to Interactive < 3s
  - 3D render 60fps on mid-range hardware

#### 3. Accessibility Audit
- **WCAG 2.1 AA Compliance:**
  - Keyboard navigation for all features (no mouse-only actions)
  - Screen reader support (ARIA labels, roles, live regions)
  - Color contrast ratios (4.5:1 minimum)
  - Focus indicators visible
- **Tools:**
  - Lighthouse accessibility score (target: 100)
  - axe DevTools for automated checks
  - Manual screen reader testing (NVDA, VoiceOver)
- **Fixes:**
  - Add aria-labels to icon buttons
  - Ensure canvas renderer announces selection changes
  - Keyboard shortcuts documented and discoverable

#### 4. Cross-Browser/Device Testing
- **Browser Matrix:**
  - Desktop: Chrome, Firefox, Safari, Edge (latest 2 versions)
  - Mobile: iOS Safari (16+, 17+), Android Chrome (latest)
- **Device Matrix:**
  - Desktop: macOS, Windows, Linux
  - Tablet: iPad, Android tablet
  - Phone: iPhone, Android phone
- **Automated:** BrowserStack or Playwright browser contexts
- **Manual:** Critical path workflows on real devices

#### 5. Release Checklist
- Create `docs/release/CHECKLIST.md` covering:
  - **Pre-Release:**
    - All tests pass (unit, integration, E2E)
    - No console errors/warnings
    - Lighthouse scores (Performance, Accessibility, Best Practices, SEO)
    - Security audit (npm audit, Dependabot)
    - Version bump and changelog update
  - **Build:**
    - `npm run build` succeeds
    - WASM bundle included in dist
    - Service worker registered correctly
    - Source maps generated (for debugging)
  - **Deployment:**
    - Artifact uploaded (GitHub Releases)
    - Documentation site updated
    - Agent compatibility verified (version check)
  - **Post-Release:**
    - Smoke test on production URL
    - Monitor error tracking (Sentry or similar)
    - User communication (release notes, migration guide if needed)

#### 6. Documentation Finalization
- **Developer Docs:**
  - `docs/web/DEVELOPMENT.md` (setup, scripts, architecture)
  - `docs/web/WASM_API.md` (complete API reference)
  - `docs/web/TESTING.md` (testing strategy, running tests)
- **User Docs:**
  - `docs/core/USER_GUIDE.md` (updated with PWA workflows)
  - `docs/features/` (offline, collaboration, AR, etc.)
- **Architecture:**
  - Cross-link Rust core and PWA architecture docs
  - Data flow diagrams
  - Decision records (ADRs) for key choices
- **README Updates:**
  - Add PWA quick start
  - Link to live demo (if hosted)
  - Update screenshots

#### 7. CI/CD Pipeline Hardening
- **Linting & Type Checking:**
  - ESLint, Prettier (already in M01)
  - TypeScript strict mode enforced
- **Security:**
  - npm audit in CI (fail on high/critical)
  - Dependabot auto-updates
  - WASM security audit (check for unsafe code)
- **Test Coverage:**
  - Coverage threshold enforcement (80% target)
  - Upload coverage to Codecov or Coveralls
- **Build Artifacts:**
  - Generate reproducible builds (lock versions)
  - Artifact checksums (SHA-256)
  - Automated GitHub Release creation

#### 8. User Acceptance Testing (UAT)
- Recruit beta testers (facility managers, building consultants)
- Provide UAT checklist (critical workflows to verify)
- Collect feedback via survey or GitHub Discussions
- Prioritize bugs/features for post-release iterations

### Testing Strategy
- E2E: comprehensive multi-feature scenarios
- Performance: automated benchmarks in CI
- Accessibility: automated + manual audits
- Cross-browser: automated matrix testing
- UAT: real users with feedback collection

### Exit Criteria
- ✅ All automated tests pass (100% pass rate)
- ✅ E2E scenarios cover critical paths (import → edit → commit → export)
- ✅ Lighthouse scores: Performance 90+, Accessibility 100, Best Practices 100
- ✅ Cross-browser testing matrix complete (no critical bugs)
- ✅ Release checklist validated with dry-run
- ✅ Documentation complete and reviewed
- ✅ UAT feedback collected and triaged
- ✅ PWA bundle + WASM artifacts reproducible

### Deliverables
- Comprehensive E2E test suite
- Performance benchmarks and optimization report
- Accessibility compliance report (WCAG 2.1 AA)
- Cross-browser compatibility matrix
- Release checklist and automation
- Finalized documentation
- Beta testing feedback report

### Ongoing Activities
- Monitor error tracking (Sentry)
- Performance regression monitoring (CI benchmarks)
- Dependency updates (Dependabot)
- User feedback triage (GitHub Issues/Discussions)
- Incremental accessibility improvements

---

## Critical Path Dependencies

### Sequential Dependencies (Cannot Parallelize)

```
M01 → M02 → M03 → M04 → M05
(Foundation → Commands → Viewer → Agent/Editing → Offline)
```

**Rationale:**
- M02 requires M01 (needs WASM loader)
- M03 requires M02 (uses command system to load data)
- M04 requires M03 (extends viewer with editing)
- M05 requires M04 (needs agent connectivity to sync)

### Parallel Opportunities (Post-M05)

```
        ┌─→ M06 (Collaboration) ─┐
M05 ────┤                         ├─→ M08 (Quality)
        └─→ M07 (3D/AR) ─────────┘
```

**Rationale:**
- M06 and M07 are independent features
- Both depend on M04 (agent) but not on each other
- Can develop in parallel if resources allow

### MVP Critical Path

```
M01 → M02 → M03 → M04 → M05 = MVP LAUNCH
```

**Timeline:** 9 weeks (solo) or 6-7 weeks (with parallelization)

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| WASM bundle size too large (>5MB) | Medium | Medium | Feature flags, lazy loading, compression |
| Desktop agent not installed by users | High | High | Clear onboarding, fallback to view-only mode |
| WebSocket connection unstable (M04) | Medium | High | Reconnect logic, offline queue (M05) |
| Git conflicts overwhelming users (M05) | Medium | High | Session branches, guided resolution UI |
| WebXR limited device support (M07) | High | Low | 3D viewer as primary, AR as enhancement |
| Performance issues with large IFCs | Medium | Medium | Pagination, LOD, virtualization |

### Process Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep delaying MVP | High | High | Strict milestone exit criteria, defer features |
| Solo developer burnout | Medium | High | Time-box milestones, celebrate small wins |
| User adoption low | Medium | High | Beta testing, user feedback loops, demos |
| Documentation falls behind | Medium | Medium | Document as you build, include in exit criteria |

### Mitigation Strategies

1. **WASM Size:** Enable feature flags in Rust (`cargo features`), strip debug symbols, use wasm-opt
2. **Agent Adoption:** Create 1-click installers (macOS .pkg, Windows .msi), video tutorials
3. **Connection Stability:** Implement heartbeat ping/pong, auto-reconnect, connection quality indicator
4. **Conflict Resolution:** Provide conflict avoidance tips (sync often), clear visual diff
5. **Performance:** Profile early (M03), set performance budgets, optimize hot paths
6. **Scope Creep:** Weekly milestone review, defer non-critical tasks to backlog
7. **Burnout:** 4-day work weeks, rotate between front-end/back-end tasks for variety

---

## Success Metrics

### MVP Launch (M01-M05)

- **Technical:**
  - All tests passing (unit, integration, E2E)
  - Lighthouse Performance score >85
  - Zero critical bugs

- **User:**
  - 5+ beta users successfully import IFC and commit edits
  - Average workflow completion time <5 minutes (import → edit → commit)
  - User satisfaction >4/5 in UAT survey

### Post-Launch (M06-M08)

- **Adoption:**
  - 50+ active users within 3 months
  - 10+ GitHub stars
  - 3+ community contributions (issues, PRs, discussions)

- **Quality:**
  - Lighthouse Accessibility score 100
  - <5% error rate in production (error tracking)
  - 80%+ test coverage

- **Engagement:**
  - Average session duration >10 minutes
  - 50%+ weekly active user retention
  - Positive feedback on collaboration/3D features

---

## Notes for Implementation

### Development Environment Setup

```bash
# Prerequisites
- Node.js 18+ (recommend using nvm)
- Rust 1.70+ with wasm32-unknown-unknown target
- Git 2.30+

# Initial Setup
cd pwa/
npm install
npm run dev      # Start dev server on http://localhost:5173

# Build WASM
cd ../crates/arxos-wasm
wasm-pack build --target web

# Run Tests
cd ../../pwa
npm run test           # Jest unit tests
npm run test:e2e       # Playwright E2E tests
npm run test:coverage  # Coverage report
```

### Recommended Tools

- **Editor:** VS Code with extensions (ESLint, Prettier, Rust Analyzer)
- **Browser DevTools:** React DevTools, Redux DevTools (for Zustand)
- **Git GUI:** GitKraken or Sublime Merge (for visualizing branches in M05)
- **API Testing:** Postman or Insomnia (for agent WebSocket testing)
- **Performance:** Chrome DevTools Performance tab, Lighthouse CI

### Code Style Guidelines

- **TypeScript:** Strict mode, explicit return types for public functions
- **React:** Functional components with hooks, avoid class components
- **State:** Zustand slices organized by feature module
- **WASM:** Keep wasm-bindgen exports minimal, use JSON for complex types
- **Testing:** Arrange-Act-Assert pattern, descriptive test names

---

## Changelog

### Version 2.0 (2025-11-12)
- Restructured M03/M04: Split viewer and editing
- Added Git branch-per-session conflict resolution to M05
- Updated M06 to agent-relay MVP only (deferred hosted relay)
- Distributed testing infrastructure across milestones (removed from M08 batch)
- Reframed M07 as 3D visualization with optional AR
- Added MVP definition (M01-M05)
- Added timeline estimates and dependency graph
- Created unified roadmap document

### Version 1.0 (Initial)
- Created individual milestone documents (01-08)

---

## Next Steps

1. **Review & Approve:** Review this roadmap, adjust timeline/scope if needed
2. **Create WASM API Doc:** Start `docs/web/WASM_API.md` before M01 implementation
3. **Set Up Project Board:** GitHub Projects with columns for each milestone
4. **Kickoff M01:** Initialize Vite project, configure tooling
5. **Weekly Check-ins:** Review progress against timeline, adjust as needed

---

**Questions? Feedback?**
Create an issue in GitHub or update this document with notes/decisions.
