/**
 * Spatial and AR-related type definitions
 */

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

export interface SpatialDataUpdate {
  equipmentId: string;
  spatialAnchor: {
    position: Vector3;
    rotation: Quaternion;
    confidence: number;
  };
  arPlatform: ARPlatform;
  timestamp: string;
}

export interface ARSessionState {
  isSupported: boolean;
  permissionGranted: boolean;
  sessionActive: boolean;
  trackingState: ARTrackingState;
  detectedAnchors: SpatialAnchor[];
  selectedAnchor: SpatialAnchor | null;
  cameraPosition: Vector3 | null;
  cameraRotation: Quaternion | null;
}

export type ARTrackingState = 'normal' | 'limited' | 'notAvailable';

export interface ARConfiguration {
  planeDetection: boolean;
  lightEstimation: boolean;
  worldAlignment: 'gravity' | 'gravityAndHeading' | 'camera';
  maximumNumberOfTrackedImages?: number;
}
