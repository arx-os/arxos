/**
 * Floor plan edit operations
 *
 * Defines operations for adding, deleting, moving, and resizing
 * rooms, walls, and equipment in the floor viewer.
 */

import type { Room, Equipment } from "../../../lib/wasm/geometry";

/**
 * Edit operation types
 */
export type EditOperationType =
  | "add-room"
  | "delete-room"
  | "move-room"
  | "resize-room"
  | "add-wall"
  | "delete-wall"
  | "move-wall"
  | "add-equipment"
  | "delete-equipment"
  | "move-equipment";

/**
 * Base edit operation interface
 */
export interface EditOperation {
  id: string;
  type: EditOperationType;
  timestamp: number;
  floorId: string;
}

/**
 * Add room operation
 */
export interface AddRoomOperation extends EditOperation {
  type: "add-room";
  room: Partial<Room>;
}

/**
 * Delete room operation
 */
export interface DeleteRoomOperation extends EditOperation {
  type: "delete-room";
  roomId: string;
  deletedRoom?: Room; // For undo
}

/**
 * Move room operation
 */
export interface MoveRoomOperation extends EditOperation {
  type: "move-room";
  roomId: string;
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
}

/**
 * Resize room operation
 */
export interface ResizeRoomOperation extends EditOperation {
  type: "resize-room";
  roomId: string;
  fromWidth: number;
  fromHeight: number;
  toWidth: number;
  toHeight: number;
}

/**
 * Add equipment operation
 */
export interface AddEquipmentOperation extends EditOperation {
  type: "add-equipment";
  equipment: Partial<Equipment>;
}

/**
 * Delete equipment operation
 */
export interface DeleteEquipmentOperation extends EditOperation {
  type: "delete-equipment";
  equipmentId: string;
  deletedEquipment?: Equipment; // For undo
}

/**
 * Move equipment operation
 */
export interface MoveEquipmentOperation extends EditOperation {
  type: "move-equipment";
  equipmentId: string;
  fromX: number;
  fromY: number;
  fromZ: number;
  toX: number;
  toY: number;
  toZ: number;
}

/**
 * Wall operations (stub for future implementation)
 */
export interface AddWallOperation extends EditOperation {
  type: "add-wall";
  wall: {
    startX: number;
    startY: number;
    endX: number;
    endY: number;
    thickness: number;
  };
}

export interface DeleteWallOperation extends EditOperation {
  type: "delete-wall";
  wallId: string;
}

export interface MoveWallOperation extends EditOperation {
  type: "move-wall";
  wallId: string;
  deltaX: number;
  deltaY: number;
}

/**
 * Union type of all edit operations
 */
export type AnyEditOperation =
  | AddRoomOperation
  | DeleteRoomOperation
  | MoveRoomOperation
  | ResizeRoomOperation
  | AddEquipmentOperation
  | DeleteEquipmentOperation
  | MoveEquipmentOperation
  | AddWallOperation
  | DeleteWallOperation
  | MoveWallOperation;

/**
 * Generate a unique operation ID
 */
export function generateOperationId(): string {
  return `op-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Create an add room operation
 */
export function createAddRoomOperation(
  floorId: string,
  room: Partial<Room>
): AddRoomOperation {
  return {
    id: generateOperationId(),
    type: "add-room",
    timestamp: Date.now(),
    floorId,
    room,
  };
}

/**
 * Create a delete room operation
 */
export function createDeleteRoomOperation(
  floorId: string,
  roomId: string,
  deletedRoom?: Room
): DeleteRoomOperation {
  return {
    id: generateOperationId(),
    type: "delete-room",
    timestamp: Date.now(),
    floorId,
    roomId,
    deletedRoom,
  };
}

/**
 * Create a move room operation
 */
export function createMoveRoomOperation(
  floorId: string,
  roomId: string,
  fromX: number,
  fromY: number,
  toX: number,
  toY: number
): MoveRoomOperation {
  return {
    id: generateOperationId(),
    type: "move-room",
    timestamp: Date.now(),
    floorId,
    roomId,
    fromX,
    fromY,
    toX,
    toY,
  };
}

/**
 * Create a resize room operation
 */
export function createResizeRoomOperation(
  floorId: string,
  roomId: string,
  fromWidth: number,
  fromHeight: number,
  toWidth: number,
  toHeight: number
): ResizeRoomOperation {
  return {
    id: generateOperationId(),
    type: "resize-room",
    timestamp: Date.now(),
    floorId,
    roomId,
    fromWidth,
    fromHeight,
    toWidth,
    toHeight,
  };
}

/**
 * Create an add equipment operation
 */
export function createAddEquipmentOperation(
  floorId: string,
  equipment: Partial<Equipment>
): AddEquipmentOperation {
  return {
    id: generateOperationId(),
    type: "add-equipment",
    timestamp: Date.now(),
    floorId,
    equipment,
  };
}

/**
 * Create a delete equipment operation
 */
export function createDeleteEquipmentOperation(
  floorId: string,
  equipmentId: string,
  deletedEquipment?: Equipment
): DeleteEquipmentOperation {
  return {
    id: generateOperationId(),
    type: "delete-equipment",
    timestamp: Date.now(),
    floorId,
    equipmentId,
    deletedEquipment,
  };
}

/**
 * Create a move equipment operation
 */
export function createMoveEquipmentOperation(
  floorId: string,
  equipmentId: string,
  fromX: number,
  fromY: number,
  fromZ: number,
  toX: number,
  toY: number,
  toZ: number
): MoveEquipmentOperation {
  return {
    id: generateOperationId(),
    type: "move-equipment",
    timestamp: Date.now(),
    floorId,
    equipmentId,
    fromX,
    fromY,
    fromZ,
    toX,
    toY,
    toZ,
  };
}
