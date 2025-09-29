/**
 * Augmented Reality-related type definitions
 */

export interface ARState {
  isSupported: boolean;
  permissionGranted: boolean;
  sessionActive: boolean;
  trackingState: ARTrackingState;
  detectedAnchors: SpatialAnchor[];
  selectedAnchor: SpatialAnchor | null;
  cameraPosition: Vector3 | null;
  cameraRotation: Quaternion | null;
  lightingEstimate: LightingEstimate | null;
  detectedPlanes: DetectedPlane[];
}

export interface SpatialAnchor {
  id: string;
  equipmentId: string;
  position: Vector3;
  rotation: Quaternion;
  confidence: number;
  platform: ARPlatform;
  buildingId: string;
  createdAt: string;
  updatedAt: string;
}

export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface Quaternion {
  x: number;
  y: number;
  z: number;
  w: number;
}

export type ARPlatform = 'ARKit' | 'ARCore';

export type ARTrackingState = 'normal' | 'limited' | 'notAvailable';

export interface LightingEstimate {
  ambientIntensity: number;
  ambientColorTemperature: number;
}

export interface DetectedPlane {
  id: string;
  center: Vector3;
  extent: Vector3;
  classification: PlaneClassification;
  confidence: number;
}

export type PlaneClassification = 
  | 'none' 
  | 'wall' 
  | 'floor' 
  | 'ceiling' 
  | 'table' 
  | 'seat' 
  | 'window' 
  | 'door';

export interface ARConfiguration {
  planeDetection: boolean;
  lightEstimation: boolean;
  worldAlignment: 'gravity' | 'gravityAndHeading' | 'camera';
  maximumNumberOfTrackedImages?: number;
  enableAutoFocus?: boolean;
  enableDepth?: boolean;
}

export interface ARSessionConfig {
  configuration: ARConfiguration;
  resetTracking: boolean;
  removeExistingAnchors: boolean;
}

export interface ARHitTestResult {
  position: Vector3;
  distance: number;
  anchor?: SpatialAnchor;
  plane?: DetectedPlane;
}

export interface ARImageTracking {
  isSupported: boolean;
  trackedImages: TrackedImage[];
  maxTrackedImages: number;
}

export interface TrackedImage {
  id: string;
  name: string;
  physicalSize: Vector3;
  isTracked: boolean;
  anchor?: SpatialAnchor;
}
