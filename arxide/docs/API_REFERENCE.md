# ArxIDE API Reference

## 🏗️ Overview

This document provides a comprehensive reference for all APIs used in ArxIDE, including the desktop application, backend services, and AI/CAD services.

## 📋 Table of Contents

1. [Desktop Application APIs](#desktop-application-apis)
2. [Backend Services APIs](#backend-services-apis)
3. [AI/CAD Services APIs](#ai-cad-services-apis)
4. [Shared Types](#shared-types)
5. [Error Handling](#error-handling)

## 🖥️ Desktop Application APIs

### IPC Communication

#### Main Process → Renderer Process

```typescript
// File Operations
interface FileOperations {
  openFile: (filePath: string) => Promise<FileData>
  saveFile: (filePath: string, data: FileData) => Promise<void>
  exportFile: (filePath: string, format: string) => Promise<void>
  importFile: (filePath: string, format: string) => Promise<FileData>
}

// Window Management
interface WindowOperations {
  minimize: () => void
  maximize: () => void
  close: () => void
  setSize: (width: number, height: number) => void
  setPosition: (x: number, y: number) => void
}

// Extension Management
interface ExtensionOperations {
  loadExtension: (extensionPath: string) => Promise<ExtensionInfo>
  unloadExtension: (extensionId: string) => Promise<void>
  getExtensions: () => Promise<ExtensionInfo[]>
  executeExtension: (extensionId: string, command: string, params: any) => Promise<any>
}
```

#### Renderer Process → Main Process

```typescript
// File System Access
interface FileSystemAccess {
  readFile: (filePath: string) => Promise<Buffer>
  writeFile: (filePath: string, data: Buffer) => Promise<void>
  exists: (filePath: string) => Promise<boolean>
  mkdir: (dirPath: string) => Promise<void>
  readdir: (dirPath: string) => Promise<string[]>
}

// System Information
interface SystemInfo {
  getPlatform: () => Promise<string>
  getVersion: () => Promise<string>
  getAppPath: () => Promise<string>
  getUserDataPath: () => Promise<string>
}
```

### Monaco Editor Integration

```typescript
// SVGX Language Support
interface SVGXLanguage {
  id: string
  extensions: string[]
  aliases: string[]
  configuration: LanguageConfiguration
  monarchTokens: IMonarchLanguage
}

// Editor Operations
interface EditorOperations {
  setValue: (value: string) => void
  getValue: () => string
  setLanguage: (language: string) => void
  addCommand: (id: string, handler: () => void) => void
  addAction: (action: IActionDescriptor) => void
  setModel: (model: ITextModel) => void
  getModel: () => ITextModel
  focus: () => void
  layout: (dimension?: IDimension) => void
}
```

### Three.js Canvas Integration

```typescript
// Scene Management
interface SceneOperations {
  createScene: () => THREE.Scene
  addObject: (object: THREE.Object3D) => void
  removeObject: (object: THREE.Object3D) => void
  clearScene: () => void
  render: () => void
}

// Camera Controls
interface CameraOperations {
  setCamera: (camera: THREE.Camera) => void
  setControls: (controls: OrbitControls) => void
  focusOnObject: (object: THREE.Object3D) => void
  setViewport: (width: number, height: number) => void
}

// Object Selection
interface SelectionOperations {
  selectObject: (object: THREE.Object3D) => void
  deselectObject: (object: THREE.Object3D) => void
  getSelectedObjects: () => THREE.Object3D[]
  highlightObject: (object: THREE.Object3D, color: THREE.Color) => void
}
```

## 🔧 Backend Services APIs

### REST API Endpoints

#### Authentication

```go
// POST /api/auth/login
type LoginRequest struct {
    Username string `json:"username"`
    Password string `json:"password"`
}

type LoginResponse struct {
    Token     string `json:"token"`
    UserID    string `json:"user_id"`
    ExpiresAt string `json:"expires_at"`
}

// POST /api/auth/logout
type LogoutRequest struct {
    Token string `json:"token"`
}

// POST /api/auth/refresh
type RefreshRequest struct {
    RefreshToken string `json:"refresh_token"`
}
```

#### File Management

```go
// GET /api/files
type FileListRequest struct {
    Path     string `query:"path"`
    Filter   string `query:"filter"`
    Page     int    `query:"page"`
    PageSize int    `query:"page_size"`
}

type FileListResponse struct {
    Files []FileInfo `json:"files"`
    Total int        `json:"total"`
}

// POST /api/files/upload
type UploadRequest struct {
    File     multipart.File `form:"file"`
    Path     string         `form:"path"`
    Overwrite bool          `form:"overwrite"`
}

// GET /api/files/{fileID}/download
type DownloadResponse struct {
    File     []byte `json:"file"`
    Filename string `json:"filename"`
    MimeType string `json:"mime_type"`
}

// PUT /api/files/{fileID}
type UpdateFileRequest struct {
    Content string `json:"content"`
    Version int    `json:"version"`
}
```

#### Collaboration

```go
// GET /api/collaboration/sessions
type SessionListResponse struct {
    Sessions []CollaborationSession `json:"sessions"`
}

// POST /api/collaboration/sessions
type CreateSessionRequest struct {
    FileID   string `json:"file_id"`
    ReadOnly bool   `json:"read_only"`
}

// GET /api/collaboration/sessions/{sessionID}/users
type SessionUsersResponse struct {
    Users []SessionUser `json:"users"`
}

// POST /api/collaboration/sessions/{sessionID}/join
type JoinSessionRequest struct {
    UserID string `json:"user_id"`
    Token  string `json:"token"`
}
```

#### Extensions

```go
// GET /api/extensions
type ExtensionListResponse struct {
    Extensions []ExtensionInfo `json:"extensions"`
}

// POST /api/extensions/install
type InstallExtensionRequest struct {
    ExtensionID string `json:"extension_id"`
    Version     string `json:"version"`
}

// DELETE /api/extensions/{extensionID}
type UninstallExtensionRequest struct {
    ExtensionID string `json:"extension_id"`
}

// POST /api/extensions/{extensionID}/execute
type ExecuteExtensionRequest struct {
    Command string                 `json:"command"`
    Params  map[string]interface{} `json:"params"`
}
```

### GraphQL Schema

```graphql
type Query {
  files(path: String, filter: String): FileList!
  file(id: ID!): File
  collaborationSessions: [CollaborationSession!]!
  extensions: [Extension!]!
  users: [User!]!
}

type Mutation {
  createFile(input: CreateFileInput!): File!
  updateFile(id: ID!, input: UpdateFileInput!): File!
  deleteFile(id: ID!): Boolean!

  createCollaborationSession(input: CreateSessionInput!): CollaborationSession!
  joinSession(sessionId: ID!, userId: ID!): SessionUser!
  leaveSession(sessionId: ID!, userId: ID!): Boolean!

  installExtension(extensionId: ID!, version: String): Extension!
  uninstallExtension(extensionId: ID!): Boolean!
  executeExtension(extensionId: ID!, command: String!, params: JSON): JSON!
}

type Subscription {
  fileChanged(fileId: ID!): FileChange!
  sessionUserJoined(sessionId: ID!): SessionUser!
  sessionUserLeft(sessionId: ID!): SessionUser!
}
```

## 🤖 AI/CAD Services APIs

### Natural Language Processing

```python
# POST /api/agent/command
class NaturalLanguageCommand(BaseModel):
    command: str
    building_id: str
    context: Dict[str, Any] = {}
    user_id: str
    session_id: Optional[str] = None

class CommandResponse(BaseModel):
    success: bool
    svgx_code: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
    error: Optional[str] = None
    confidence: float = 0.0

# POST /api/agent/validate
class ValidationRequest(BaseModel):
    svgx_code: str
    building_id: str
    context: Dict[str, Any] = {}

class ValidationResponse(BaseModel):
    valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []
    suggestions: List[str] = []
```

### SVGX Engine Integration

```python
# POST /api/svgx/process
class SVGXProcessRequest(BaseModel):
    svgx_code: str
    building_id: str
    operation: str  # "validate", "simulate", "optimize"
    parameters: Dict[str, Any] = {}

class SVGXProcessResponse(BaseModel):
    success: bool
    result: Dict[str, Any] = {}
    errors: List[str] = []
    warnings: List[str] = []
    performance_metrics: Dict[str, float] = {}

# POST /api/svgx/simulate
class SimulationRequest(BaseModel):
    building_id: str
    simulation_type: str  # "electrical", "hvac", "plumbing", "structural"
    parameters: Dict[str, Any] = {}
    duration: Optional[float] = None

class SimulationResponse(BaseModel):
    success: bool
    results: Dict[str, Any] = {}
    timeline: List[Dict[str, Any]] = []
    alerts: List[Dict[str, Any]] = []
```

### CAD Processing

```python
# POST /api/cad/analyze
class CADAnalysisRequest(BaseModel):
    building_id: str
    analysis_type: str  # "structural", "electrical", "hvac", "plumbing"
    parameters: Dict[str, Any] = {}

class CADAnalysisResponse(BaseModel):
    success: bool
    analysis_results: Dict[str, Any] = {}
    recommendations: List[str] = []
    compliance_status: Dict[str, bool] = {}
    performance_metrics: Dict[str, float] = {}

# POST /api/cad/optimize
class OptimizationRequest(BaseModel):
    building_id: str
    optimization_target: str  # "energy", "cost", "performance", "safety"
    constraints: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}

class OptimizationResponse(BaseModel):
    success: bool
    optimized_svgx: str
    improvements: Dict[str, float] = {}
    cost_analysis: Dict[str, float] = {}
    implementation_steps: List[str] = []
```

## 📊 Shared Types

### Core Data Structures

```typescript
// File Management
interface FileInfo {
  id: string
  name: string
  path: string
  size: number
  type: string
  created_at: string
  updated_at: string
  version: number
  checksum: string
}

interface FileData {
  content: string
  metadata: FileMetadata
  version: number
  last_modified: string
}

// Building Models
interface BuildingModel {
  id: string
  name: string
  description: string
  systems: BuildingSystem[]
  metadata: BuildingMetadata
  created_at: string
  updated_at: string
}

interface BuildingSystem {
  id: string
  type: SystemType
  components: SystemComponent[]
  connections: SystemConnection[]
  properties: SystemProperties
}

// Extensions
interface ExtensionInfo {
  id: string
  name: string
  version: string
  description: string
  author: string
  permissions: string[]
  commands: ExtensionCommand[]
  status: ExtensionStatus
}

interface ExtensionCommand {
  id: string
  name: string
  description: string
  parameters: CommandParameter[]
  return_type: string
}

// Collaboration
interface CollaborationSession {
  id: string
  file_id: string
  users: SessionUser[]
  permissions: SessionPermissions
  created_at: string
  expires_at: string
}

interface SessionUser {
  id: string
  name: string
  email: string
  role: UserRole
  cursor_position?: CursorPosition
  last_active: string
}
```

### Error Handling

```typescript
// Error Types
interface APIError {
  code: string
  message: string
  details?: any
  timestamp: string
  request_id: string
}

interface ValidationError {
  field: string
  message: string
  code: string
  severity: 'error' | 'warning' | 'info'
}

// Error Codes
enum ErrorCodes {
  // Authentication
  AUTH_INVALID_CREDENTIALS = 'AUTH_001',
  AUTH_TOKEN_EXPIRED = 'AUTH_002',
  AUTH_INSUFFICIENT_PERMISSIONS = 'AUTH_003',

  // File Operations
  FILE_NOT_FOUND = 'FILE_001',
  FILE_ACCESS_DENIED = 'FILE_002',
  FILE_CORRUPTED = 'FILE_003',
  FILE_VERSION_CONFLICT = 'FILE_004',

  // Extension System
  EXTENSION_NOT_FOUND = 'EXT_001',
  EXTENSION_LOAD_FAILED = 'EXT_002',
  EXTENSION_EXECUTION_ERROR = 'EXT_003',
  EXTENSION_PERMISSION_DENIED = 'EXT_004',

  // AI/CAD Services
  AI_SERVICE_UNAVAILABLE = 'AI_001',
  AI_COMMAND_INVALID = 'AI_002',
  AI_PROCESSING_ERROR = 'AI_003',

  // SVGX Engine
  SVGX_PARSE_ERROR = 'SVGX_001',
  SVGX_VALIDATION_ERROR = 'SVGX_002',
  SVGX_SIMULATION_ERROR = 'SVGX_003',

  // Collaboration
  SESSION_NOT_FOUND = 'COLLAB_001',
  SESSION_ACCESS_DENIED = 'COLLAB_002',
  SESSION_CONFLICT = 'COLLAB_003'
}
```

## 🔐 Security

### Authentication

```typescript
// JWT Token Structure
interface JWTPayload {
  user_id: string
  username: string
  email: string
  roles: string[]
  permissions: string[]
  exp: number
  iat: number
}

// Permission System
interface Permission {
  resource: string
  action: string
  conditions?: PermissionCondition[]
}

interface PermissionCondition {
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'in' | 'not_in'
  value: any
}
```

### Rate Limiting

```typescript
// Rate Limit Configuration
interface RateLimitConfig {
  window_ms: number
  max_requests: number
  skip_successful_requests: boolean
  skip_failed_requests: boolean
}

// Rate Limit Headers
interface RateLimitHeaders {
  'X-RateLimit-Limit': string
  'X-RateLimit-Remaining': string
  'X-RateLimit-Reset': string
  'Retry-After': string
}
```

## 📈 Monitoring & Logging

### Metrics

```typescript
// Performance Metrics
interface PerformanceMetrics {
  response_time: number
  memory_usage: number
  cpu_usage: number
  error_rate: number
  throughput: number
}

// Business Metrics
interface BusinessMetrics {
  active_users: number
  files_created: number
  commands_executed: number
  extensions_installed: number
  collaboration_sessions: number
}
```

### Logging

```typescript
// Log Levels
enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4
}

// Log Entry
interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  context: LogContext
  user_id?: string
  session_id?: string
  request_id?: string
}

interface LogContext {
  component: string
  operation: string
  parameters?: any
  stack_trace?: string
}
```

This API reference provides a comprehensive guide to all the interfaces, endpoints, and data structures used in ArxIDE. It serves as the definitive reference for developers working on the project.
