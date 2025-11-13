import { initWasm } from "../wasm";

export interface Coordinate {
  x: number;
  y: number;
  z?: number;
}

export interface BoundingBox {
  min: Coordinate;
  max: Coordinate;
}

export interface BuildingSummary {
  path: string;
  name: string;
  floor_count: number;
  last_modified: string;
}

export interface Building {
  path: string;
  name: string;
  address?: string;
  floors: Floor[];
  metadata: Record<string, unknown>;
}

export interface Floor {
  id: string;
  name: string;
  level: number;
  elevation: number;
  height: number;
  rooms: Room[];
  bounds: BoundingBox;
}

export interface Room {
  id: string;
  name: string;
  room_type: string;
  bounds: BoundingBox;
  polygon?: Coordinate[];
  equipment: Equipment[];
}

export interface Equipment {
  id: string;
  name: string;
  equipment_type: string;
  position: Coordinate;
  bounds?: BoundingBox;
  properties: Record<string, unknown>;
}

// Type guards for runtime validation

function isCoordinate(value: unknown): value is Coordinate {
  const coord = value as Coordinate;
  return (
    typeof coord?.x === "number" &&
    typeof coord?.y === "number" &&
    (coord.z === undefined || typeof coord.z === "number")
  );
}

function isBoundingBox(value: unknown): value is BoundingBox {
  const box = value as BoundingBox;
  return box?.min !== undefined && isCoordinate(box.min) && isCoordinate(box.max);
}

function isBuildingSummary(value: unknown): value is BuildingSummary {
  const summary = value as BuildingSummary;
  return (
    typeof summary?.path === "string" &&
    typeof summary?.name === "string" &&
    typeof summary?.floor_count === "number" &&
    typeof summary?.last_modified === "string"
  );
}

function isEquipment(value: unknown): value is Equipment {
  const equip = value as Equipment;
  return (
    typeof equip?.id === "string" &&
    typeof equip?.name === "string" &&
    typeof equip?.equipment_type === "string" &&
    isCoordinate(equip?.position) &&
    typeof equip?.properties === "object"
  );
}

function isRoom(value: unknown): value is Room {
  const room = value as Room;
  return (
    typeof room?.id === "string" &&
    typeof room?.name === "string" &&
    typeof room?.room_type === "string" &&
    isBoundingBox(room?.bounds) &&
    Array.isArray(room?.equipment) &&
    room.equipment.every(isEquipment)
  );
}

function isFloor(value: unknown): value is Floor {
  const floor = value as Floor;
  return (
    typeof floor?.id === "string" &&
    typeof floor?.name === "string" &&
    typeof floor?.level === "number" &&
    typeof floor?.elevation === "number" &&
    typeof floor?.height === "number" &&
    Array.isArray(floor?.rooms) &&
    floor.rooms.every(isRoom) &&
    isBoundingBox(floor?.bounds)
  );
}

function isBuilding(value: unknown): value is Building {
  const building = value as Building;
  return (
    typeof building?.path === "string" &&
    typeof building?.name === "string" &&
    Array.isArray(building?.floors) &&
    building.floors.every(isFloor) &&
    typeof building?.metadata === "object"
  );
}

// Exported adapter functions

export async function getBuildings(): Promise<BuildingSummary[]> {
  const module = await initWasm();
  const result = await module.get_buildings();

  if (!Array.isArray(result)) {
    throw new Error("WASM returned invalid buildings data: expected array");
  }

  if (!result.every(isBuildingSummary)) {
    throw new Error("WASM returned invalid building summary format");
  }

  return result;
}

export async function getBuilding(path: string): Promise<Building> {
  const module = await initWasm();
  const result = await module.get_building(path);

  if (!isBuilding(result)) {
    throw new Error("WASM returned invalid building format");
  }

  return result;
}

export async function getFloor(buildingPath: string, floorId: string): Promise<Floor> {
  const module = await initWasm();
  const result = await module.get_floor(buildingPath, floorId);

  if (!isFloor(result)) {
    throw new Error("WASM returned invalid floor format");
  }

  return result;
}

export async function getFloorBounds(buildingPath: string, floorId: string): Promise<BoundingBox> {
  const module = await initWasm();
  const result = await module.get_floor_bounds(buildingPath, floorId);

  if (!isBoundingBox(result)) {
    throw new Error("WASM returned invalid bounding box format");
  }

  return result;
}
