/**
 * AR Domain Entities - Core domain models for AR functionality
 * Implements Clean Architecture with domain-driven design
 */

import { Vector3, Quaternion } from '../types/SpatialTypes';

export interface ARContext {
  sessionId: string;
  buildingId: string;
  floorId: string;
  currentPosition: Vector3;
  activeAnchor?: SpatialAnchor;
  arPlatform: 'ARKit' | 'ARCore';
  timestamp: Date;
  sessionState: ARSessionState;
}

export interface ARSessionState {
  isActive: boolean;
  isTracking: boolean;
  lightingEstimate: number;
  planeDetectionEnabled: boolean;
  errorCount: number;
  lastError?: ARError;
}

export interface SpatialAnchor {
  id: string;
  position: Vector3;
  rotation: Quaternion;
  confidence: number;
  timestamp: Date;
  equipmentId?: string;
  buildingId: string;
  floorId: string;
  platformData?: any;
  validationStatus: 'pending' | 'validated' | 'rejected';
  lastUpdated: Date;
}

export interface EquipmentAROverlay {
  equipmentId: string;
  position: Vector3;
  rotation: Quaternion;
  scale: Vector3;
  status: EquipmentStatus;
  lastUpdated: Date;
  arVisibility: ARVisibility;
  modelType: '3D' | '2D' | 'icon';
  metadata: EquipmentARMetadata;
}

export interface EquipmentARMetadata {
  name: string;
  type: string;
  model: string;
  manufacturer?: string;
  installationDate?: Date;
  lastMaintenance?: Date;
  nextMaintenance?: Date;
  criticality: 'low' | 'medium' | 'high' | 'critical';
  maintenanceNotes?: string;
}

export interface ARVisibility {
  isVisible: boolean;
  distance: number;
  occlusionLevel: number;
  lightingCondition: 'good' | 'poor' | 'dark';
  contrast: number;
  lastVisibilityCheck: Date;
}

export interface ARNavigationPath {
  id: string;
  waypoints: Vector3[];
  distance: number;
  estimatedTime: number;
  obstacles: Vector3[];
  arInstructions: ARInstruction[];
  difficulty: 'easy' | 'medium' | 'hard';
  accessibility: boolean;
  createdAt: Date;
}

export interface ARInstruction {
  id: string;
  type: 'move' | 'turn' | 'stop' | 'equipment' | 'warning';
  position: Vector3;
  description: string;
  arVisualization: ARVisualization;
  estimatedDuration: number;
  priority: 'low' | 'medium' | 'high';
}

export interface ARVisualization {
  type: 'arrow' | 'highlight' | 'path' | 'overlay' | 'warning';
  color: string;
  size: number;
  animation?: 'pulse' | 'rotate' | 'fade' | 'none';
  opacity: number;
  duration?: number;
}

export interface ARError {
  id: string;
  code: string;
  message: string;
  platform: 'ARKit' | 'ARCore';
  timestamp: Date;
  recoverable: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
  context?: Record<string, any>;
}

export interface SpatialDataUpdate {
  id: string;
  equipmentId: string;
  spatialAnchor: SpatialAnchor;
  arPlatform: 'ARKit' | 'ARCore';
  timestamp: Date;
  technicianId: string;
  buildingId: string;
  confidence: number;
  validationStatus: 'pending' | 'validated' | 'rejected';
  syncStatus: 'pending' | 'synced' | 'failed';
  lastSyncAttempt?: Date;
  syncError?: string;
}

export interface SpatialConflict {
  id: string;
  equipmentId: string;
  conflictingAnchors: SpatialAnchor[];
  conflictType: 'position' | 'orientation' | 'scale' | 'duplicate';
  severity: 'low' | 'medium' | 'high';
  resolution: SpatialResolution;
  timestamp: Date;
  resolvedAt?: Date;
  resolutionMethod?: string;
}

export interface SpatialResolution {
  id: string;
  type: 'position' | 'orientation' | 'scale' | 'merge' | 'reject';
  resolvedAnchor: SpatialAnchor;
  resolutionMethod: 'confidence_based' | 'timestamp_based' | 'manual' | 'algorithm';
  confidence: number;
  timestamp: Date;
  appliedBy: string;
  notes?: string;
}

export interface ARSessionMetrics {
  sessionId: string;
  startTime: Date;
  endTime?: Date;
  duration?: number;
  anchorsDetected: number;
  anchorsCreated: number;
  anchorsUpdated: number;
  anchorsRemoved: number;
  equipmentOverlaysRendered: number;
  navigationPathsCalculated: number;
  errorsEncountered: number;
  averageFrameRate: number;
  averageTrackingQuality: number;
  batteryUsage: number;
  memoryUsage: number;
}

export interface ARConfiguration {
  platform: 'ARKit' | 'ARCore';
  planeDetection: boolean;
  lightEstimation: boolean;
  worldAlignment: 'gravity' | 'camera' | 'gravityAndHeading';
  maximumNumberOfTrackedImages?: number;
  maximumNumberOfTrackedObjects?: number;
  enableAutoFocus?: boolean;
  enableDepthOcclusion?: boolean;
  enableMotionBlur?: boolean;
  enableHDR?: boolean;
}

export interface ARCalibrationData {
  deviceId: string;
  platform: 'ARKit' | 'ARCore';
  calibrationDate: Date;
  cameraIntrinsics: CameraIntrinsics;
  accelerometerBias: Vector3;
  gyroscopeBias: Vector3;
  magnetometerBias: Vector3;
  validationResults: CalibrationValidation;
}

export interface CameraIntrinsics {
  focalLength: Vector3;
  principalPoint: Vector3;
  distortionCoefficients: number[];
  imageSize: Vector3;
}

export interface CalibrationValidation {
  isValid: boolean;
  accuracy: number;
  confidence: number;
  errors: string[];
  warnings: string[];
}

export enum EquipmentStatus {
  OPERATIONAL = 'operational',
  MAINTENANCE = 'maintenance',
  OFFLINE = 'offline',
  NEEDS_REPAIR = 'needs_repair',
  FAILED = 'failed',
  TESTING = 'testing',
  STANDBY = 'standby'
}

export enum ARSessionStateType {
  INITIALIZING = 'initializing',
  RUNNING = 'running',
  PAUSED = 'paused',
  STOPPED = 'stopped',
  ERROR = 'error'
}

export enum ARTrackingState {
  NOT_AVAILABLE = 'not_available',
  LIMITED = 'limited',
  NORMAL = 'normal',
  RELOCALIZING = 'relocalizing'
}

export enum ARPlaneDetection {
  NONE = 'none',
  HORIZONTAL = 'horizontal',
  VERTICAL = 'vertical',
  BOTH = 'both'
}

// Domain Services Interfaces
export interface IARContextService {
  createContext(buildingId: string, floorId: string): Promise<ARContext>;
  updateContext(context: ARContext): Promise<void>;
  getCurrentContext(): ARContext | null;
  clearContext(): void;
}

export interface ISpatialDataService {
  createSpatialAnchor(anchor: Omit<SpatialAnchor, 'id' | 'timestamp' | 'validationStatus' | 'lastUpdated'>): Promise<SpatialAnchor>;
  updateSpatialAnchor(anchor: SpatialAnchor): Promise<void>;
  deleteSpatialAnchor(anchorId: string): Promise<void>;
  getSpatialAnchorsByEquipment(equipmentId: string): Promise<SpatialAnchor[]>;
  getSpatialAnchorsByBuilding(buildingId: string): Promise<SpatialAnchor[]>;
  validateSpatialAnchor(anchor: SpatialAnchor): Promise<boolean>;
}

export interface IARErrorService {
  logError(error: ARError): Promise<void>;
  getErrorsBySession(sessionId: string): Promise<ARError[]>;
  getErrorsBySeverity(severity: ARError['severity']): Promise<ARError[]>;
  clearOldErrors(olderThan: Date): Promise<void>;
}

export interface IARMetricsService {
  startSession(sessionId: string): Promise<void>;
  endSession(sessionId: string): Promise<ARSessionMetrics>;
  recordAnchorDetected(sessionId: string): Promise<void>;
  recordAnchorCreated(sessionId: string): Promise<void>;
  recordAnchorUpdated(sessionId: string): Promise<void>;
  recordAnchorRemoved(sessionId: string): Promise<void>;
  recordEquipmentOverlayRendered(sessionId: string): Promise<void>;
  recordNavigationPathCalculated(sessionId: string): Promise<void>;
  recordError(sessionId: string, error: ARError): Promise<void>;
  updateFrameRate(sessionId: string, frameRate: number): Promise<void>;
  updateTrackingQuality(sessionId: string, quality: number): Promise<void>;
  updateResourceUsage(sessionId: string, batteryUsage: number, memoryUsage: number): Promise<void>;
}
