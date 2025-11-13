declare module "@arxos-wasm" {
  export type WasmPosition = { x: number; y: number; z: number };

  export type WasmOpening = {
    position: WasmPosition;
    width: number;
    height: number;
    type: string;
  };

  export type WasmWall = {
    startPoint: WasmPosition;
    endPoint: WasmPosition;
    height: number;
    thickness: number;
  };

  export type WasmRoomBoundaries = {
    walls: WasmWall[];
    openings: WasmOpening[];
  };

  export type WasmDetectedEquipment = {
    name: string;
    type: string;
    position: WasmPosition;
    confidence: number;
    detectionMethod?: string;
  };

  export type WasmArScanData = {
    detectedEquipment: WasmDetectedEquipment[];
    roomBoundaries: WasmRoomBoundaries;
    deviceType?: string;
    appVersion?: string;
    scanDurationMs?: number;
    pointCount?: number;
    accuracyEstimate?: number;
    lightingConditions?: string;
    roomName?: string;
    floorLevel?: number;
  };

  export type WasmCommandCategory = {
    slug: string;
    label: string;
  };

  export type WasmCommandAvailability = {
    cli: boolean;
    pwa: boolean;
    agent: boolean;
  };

  export type WasmCommandEntry = {
    name: string;
    command: string;
    description: string;
    category: WasmCommandCategory;
    shortcut?: string;
    tags: string[];
    availability: WasmCommandAvailability;
  };

  export type WasmEquipmentInfo = {
    id: string;
    name: string;
    equipmentType: string;
    status: string;
    position: WasmPosition;
    properties: Record<string, string>;
    addressPath: string;
  };

  export type WasmMeshBuffers = {
    wallPositions: number[];
    equipmentPositions: number[];
    pointCloudPositions: number[];
    boundsMin: [number, number, number];
    boundsMax: [number, number, number];
  };

  // Geometry types (M03)
  export type WasmCoordinate = {
    x: number;
    y: number;
    z?: number;
  };

  export type WasmBoundingBox = {
    min: WasmCoordinate;
    max: WasmCoordinate;
  };

  export type WasmBuildingSummary = {
    path: string;
    name: string;
    floor_count: number;
    last_modified: string;
  };

  export type WasmEquipment = {
    id: string;
    name: string;
    equipment_type: string;
    position: WasmCoordinate;
    bounds?: WasmBoundingBox;
    properties: Record<string, unknown>;
  };

  export type WasmRoom = {
    id: string;
    name: string;
    room_type: string;
    bounds: WasmBoundingBox;
    polygon?: WasmCoordinate[];
    equipment: WasmEquipment[];
  };

  export type WasmFloor = {
    id: string;
    name: string;
    level: number;
    elevation: number;
    height: number;
    rooms: WasmRoom[];
    bounds: WasmBoundingBox;
  };

  export type WasmBuilding = {
    path: string;
    name: string;
    address?: string;
    floors: WasmFloor[];
    metadata: Record<string, unknown>;
  };

  // Command & AR functions
  export function arxos_version(): string;
  export function parse_ar_scan(json: string): WasmArScanData;
  export function extract_equipment(json: string): WasmEquipmentInfo[];
  export function generate_scan_mesh(json: string): WasmMeshBuffers;
  export function validate_ar_scan(json: string): boolean;
  export function command_palette(): Promise<WasmCommandEntry[]>;
  export function command_categories(): Promise<WasmCommandCategory[]>;
  export function command_details(name: string): Promise<WasmCommandEntry>;

  // Geometry functions (M03)
  export function get_buildings(): Promise<WasmBuildingSummary[]>;
  export function get_building(path: string): Promise<WasmBuilding>;
  export function get_floor(buildingPath: string, floorId: string): Promise<WasmFloor>;
  export function get_floor_bounds(buildingPath: string, floorId: string): Promise<WasmBoundingBox>;
}

