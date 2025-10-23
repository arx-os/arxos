// Shared types between Rust backend and React Native mobile app

export interface Equipment {
  id: string;
  name: string;
  path: string;
  equipmentType: EquipmentType;
  status: EquipmentStatus;
  position: Position;
  boundingBox: BoundingBox;
  properties: Record<string, any>;
  roomId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Position {
  x: number;
  y: number;
  z: number;
  coordinateSystem: CoordinateSystem;
}

export interface BoundingBox {
  min: Position;
  max: Position;
}

export interface Room {
  id: string;
  name: string;
  path: string;
  roomType: RoomType;
  floorId: string;
  wingId?: string;
  spatialProperties: SpatialProperties;
  equipment: Equipment[];
  createdAt: string;
  updatedAt: string;
}

export interface Floor {
  id: string;
  name: string;
  level: number;
  buildingId: string;
  wings: Wing[];
  rooms: Room[];
  spatialProperties: SpatialProperties;
  createdAt: string;
  updatedAt: string;
}

export interface Wing {
  id: string;
  name: string;
  floorId: string;
  rooms: Room[];
  spatialProperties: SpatialProperties;
  createdAt: string;
  updatedAt: string;
}

export interface Building {
  id: string;
  name: string;
  path: string;
  floors: Floor[];
  equipment: Equipment[];
  spatialProperties: SpatialProperties;
  createdAt: string;
  updatedAt: string;
}

export interface SpatialProperties {
  dimensions: Dimensions;
  boundingBox: BoundingBox;
  coordinateSystem: CoordinateSystem;
  transform?: Transform;
}

export interface Dimensions {
  width: number;
  height: number;
  depth: number;
  units: string;
}

export interface Transform {
  translation: Position;
  rotation: Rotation;
  scale: Position;
}

export interface Rotation {
  x: number;
  y: number;
  z: number;
  w: number;
}

export interface ARAnchor {
  id: string;
  position: Position;
  confidence: number;
  source: ARSource;
  timestamp: string;
  equipmentId?: string;
}

export interface GitData {
  commitHash: string;
  branch: string;
  lastSync: string;
  status: GitStatus;
  changes: GitChange[];
}

export interface GitChange {
  path: string;
  status: GitChangeStatus;
  additions: number;
  deletions: number;
}

export enum EquipmentType {
  HVAC = 'HVAC',
  ELECTRICAL = 'ELECTRICAL',
  PLUMBING = 'PLUMBING',
  LIGHTS = 'LIGHTS',
  SAFETY = 'SAFETY',
  DOORS = 'DOORS',
  WINDOWS = 'WINDOWS',
  ELEVATOR = 'ELEVATOR',
  STAIRS = 'STAIRS',
  GENERATOR = 'GENERATOR',
  PUMP = 'PUMP',
  VALVE = 'VALVE',
  UNKNOWN = 'UNKNOWN'
}

export enum EquipmentStatus {
  HEALTHY = 'healthy',
  WARNING = 'warning',
  CRITICAL = 'critical',
  OFFLINE = 'offline',
  MAINTENANCE = 'maintenance',
  UNKNOWN = 'unknown'
}

export enum RoomType {
  CLASSROOM = 'classroom',
  OFFICE = 'office',
  LABORATORY = 'laboratory',
  CONFERENCE = 'conference',
  LIBRARY = 'library',
  CAFETERIA = 'cafeteria',
  GYM = 'gym',
  AUDITORIUM = 'auditorium',
  STORAGE = 'storage',
  MECHANICAL = 'mechanical',
  ELECTRICAL = 'electrical',
  RESTROOM = 'restroom',
  CORRIDOR = 'corridor',
  STAIRWELL = 'stairwell',
  ELEVATOR_SHAFT = 'elevator_shaft',
  UNKNOWN = 'unknown'
}

export enum CoordinateSystem {
  WGS84 = 'WGS84',
  UTM = 'UTM',
  BUILDING_LOCAL = 'building_local',
  CUSTOM = 'custom'
}

export enum ARSource {
  LIDAR = 'lidar',
  CAMERA = 'camera',
  MANUAL = 'manual',
  AI_DETECTION = 'ai_detection'
}

export enum GitStatus {
  CLEAN = 'clean',
  MODIFIED = 'modified',
  STAGED = 'staged',
  COMMITTED = 'committed',
  PUSHED = 'pushed',
  CONFLICT = 'conflict',
  ERROR = 'error'
}

export enum GitChangeStatus {
  ADDED = 'added',
  MODIFIED = 'modified',
  DELETED = 'deleted',
  RENAMED = 'renamed',
  COPIED = 'copied',
  UNMERGED = 'unmerged'
}

// Terminal command types
export interface TerminalCommand {
  command: string;
  args: string[];
  options: Record<string, any>;
  timestamp: string;
}

export interface TerminalOutput {
  type: 'stdout' | 'stderr' | 'info' | 'warning' | 'error';
  content: string;
  timestamp: string;
}

export interface TerminalSession {
  id: string;
  commands: TerminalCommand[];
  outputs: TerminalOutput[];
  currentDirectory: string;
  environment: Record<string, string>;
  startTime: string;
  endTime?: string;
}

// AR scanning types
export interface ARScanSession {
  id: string;
  roomId: string;
  startTime: string;
  endTime?: string;
  anchors: ARAnchor[];
  equipmentDetected: Equipment[];
  status: ARScanStatus;
  confidence: number;
}

export enum ARScanStatus {
  STARTING = 'starting',
  SCANNING = 'scanning',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// Camera types
export interface CameraSettings {
  resolution: CameraResolution;
  frameRate: number;
  focusMode: FocusMode;
  exposureMode: ExposureMode;
  whiteBalanceMode: WhiteBalanceMode;
  flashMode: FlashMode;
  zoom: number;
}

export enum CameraResolution {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  ULTRA_HIGH = 'ultra_high'
}

export enum FocusMode {
  AUTO = 'auto',
  CONTINUOUS = 'continuous',
  MANUAL = 'manual',
  LOCKED = 'locked'
}

export enum ExposureMode {
  AUTO = 'auto',
  CONTINUOUS = 'continuous',
  MANUAL = 'manual',
  LOCKED = 'locked'
}

export enum WhiteBalanceMode {
  AUTO = 'auto',
  CONTINUOUS = 'continuous',
  MANUAL = 'manual',
  LOCKED = 'locked'
}

export enum FlashMode {
  OFF = 'off',
  AUTO = 'auto',
  ON = 'on',
  TORCH = 'torch'
}

// Error types
export interface ArxError {
  code: string;
  message: string;
  details?: string;
  suggestions?: string[];
  recoverySteps?: string[];
  debugInfo?: Record<string, any>;
  helpUrl?: string;
  timestamp: string;
}

export interface ErrorContext {
  operation: string;
  component: string;
  userId?: string;
  sessionId?: string;
  deviceInfo?: DeviceInfo;
  networkInfo?: NetworkInfo;
}

export interface DeviceInfo {
  platform: 'ios' | 'android';
  version: string;
  model: string;
  manufacturer?: string;
  screenSize: { width: number; height: number };
  orientation: 'portrait' | 'landscape';
}

export interface NetworkInfo {
  type: 'wifi' | 'cellular' | 'ethernet' | 'unknown';
  isConnected: boolean;
  isInternetReachable: boolean;
  strength?: number;
}

// Configuration types
export interface MobileConfig {
  user: UserConfig;
  camera: CameraConfig;
  ar: ARConfig;
  git: GitConfig;
  sync: SyncConfig;
  ui: UIConfig;
}

export interface UserConfig {
  name: string;
  email: string;
  organization?: string;
  role?: string;
}

export interface CameraConfig {
  defaultResolution: CameraResolution;
  defaultFrameRate: number;
  enableLiDAR: boolean;
  enableAR: boolean;
  autoFocus: boolean;
  autoExposure: boolean;
}

export interface ARConfig {
  enableLiDAR: boolean;
  enableAR: boolean;
  confidenceThreshold: number;
  maxAnchors: number;
  anchorPersistence: boolean;
  equipmentDetection: boolean;
}

export interface GitConfig {
  repositoryUrl: string;
  branch: string;
  username?: string;
  email?: string;
  token?: string;
  autoSync: boolean;
  syncInterval: number;
}

export interface SyncConfig {
  enabled: boolean;
  interval: number;
  onWiFiOnly: boolean;
  backgroundSync: boolean;
  conflictResolution: ConflictResolution;
}

export enum ConflictResolution {
  MANUAL = 'manual',
  AUTOMATIC = 'automatic',
  SERVER_WINS = 'server_wins',
  CLIENT_WINS = 'client_wins'
}

export interface UIConfig {
  theme: 'light' | 'dark' | 'auto';
  fontSize: 'small' | 'medium' | 'large';
  showCoordinates: boolean;
  showConfidence: boolean;
  showDebugInfo: boolean;
  enableHapticFeedback: boolean;
  enableSoundEffects: boolean;
}

// API types
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: ArxError;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface SyncResponse {
  success: boolean;
  changes: GitChange[];
  conflicts: GitChange[];
  timestamp: string;
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type NonNullable<T> = T extends null | undefined ? never : T;

export type StringKeys<T> = {
  [K in keyof T]: T[K] extends string ? K : never;
}[keyof T];

export type NumberKeys<T> = {
  [K in keyof T]: T[K] extends number ? K : never;
}[keyof T];

export type BooleanKeys<T> = {
  [K in keyof T]: T[K] extends boolean ? K : never;
}[keyof T];
