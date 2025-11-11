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

  export function arxos_version(): string;
  export function parse_ar_scan(json: string): WasmArScanData;
  export function extract_equipment(json: string): WasmEquipmentInfo[];
  export function generate_scan_mesh(json: string): WasmMeshBuffers;
  export function validate_ar_scan(json: string): boolean;
  export function command_palette(): Promise<WasmCommandEntry[]>;
  export function command_categories(): Promise<WasmCommandCategory[]>;
  export function command_details(name: string): Promise<WasmCommandEntry>;
}

