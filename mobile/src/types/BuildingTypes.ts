/**
 * Building Types - Core building data structures
 */

import { Vector3, BoundingBox } from './SpatialTypes';

export interface BuildingLayout {
  id: string;
  floors: FloorLayout[];
  accessibilityFeatures: AccessibilityFeature[];
}

export interface FloorLayout {
  id: string;
  rooms: RoomLayout[];
  corridors: CorridorLayout[];
  obstacles: ObstacleLayout[];
}

export interface RoomLayout {
  id: string;
  bounds: BoundingBox;
  doors: DoorLayout[];
}

export interface CorridorLayout {
  id: string;
  path: Vector3[];
  width: number;
}

export interface DoorLayout {
  id: string;
  position: Vector3;
  width: number;
  height: number;
  accessible: boolean;
}

export interface ObstacleLayout {
  id: string;
  position: Vector3;
  bounds: BoundingBox;
  type: 'furniture' | 'equipment' | 'construction' | 'temporary';
}

export interface AccessibilityFeature {
  type: 'elevator' | 'ramp' | 'accessible_door' | 'handrail';
  position: Vector3;
  description: string;
}
