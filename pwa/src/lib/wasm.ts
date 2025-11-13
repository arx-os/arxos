import type {
  WasmArScanData,
  WasmBuilding,
  WasmBuildingSummary,
  WasmBoundingBox,
  WasmCommandCategory,
  WasmCommandEntry as WasmModuleCommandEntry,
  WasmCommandAvailability,
  WasmCoordinate,
  WasmEquipment,
  WasmEquipmentInfo,
  WasmFloor,
  WasmMeshBuffers,
  WasmOpening,
  WasmRoom,
  WasmRoomBoundaries,
  WasmWall
} from "@arxos-wasm";

export type {
  WasmArScanData,
  WasmBuilding,
  WasmBuildingSummary,
  WasmBoundingBox,
  WasmCommandAvailability,
  WasmCoordinate,
  WasmEquipment,
  WasmEquipmentInfo,
  WasmFloor,
  WasmMeshBuffers,
  WasmOpening,
  WasmRoom,
  WasmWall
};

export type WasmCommandEntry = WasmModuleCommandEntry;

export type ArxosWasmModule = {
  arxos_version(): string;
  parse_ar_scan(json: string): WasmArScanData;
  extract_equipment(json: string): WasmEquipmentInfo[];
  generate_scan_mesh(json: string): WasmMeshBuffers;
  validate_ar_scan(json: string): boolean;
  command_palette(): Promise<WasmModuleCommandEntry[]>;
  command_categories(): Promise<WasmCommandCategory[]>;
  command_details(name: string): Promise<WasmModuleCommandEntry>;
  get_buildings(): Promise<WasmBuildingSummary[]>;
  get_building(path: string): Promise<WasmBuilding>;
  get_floor(buildingPath: string, floorId: string): Promise<WasmFloor>;
  get_floor_bounds(buildingPath: string, floorId: string): Promise<WasmBoundingBox>;
};

let wasmModule: ArxosWasmModule | null = null;

function isCommandCategory(value: unknown): value is WasmCommandCategory {
  const record = value as Record<string, unknown>;
  return typeof record?.slug === "string" && typeof record?.label === "string";
}

function isAvailability(value: unknown): value is WasmCommandAvailability {
  const record = value as Record<string, unknown>;
  return (
    typeof record?.cli === "boolean" &&
    typeof record?.pwa === "boolean" &&
    typeof record?.agent === "boolean"
  );
}

function isCommandEntry(value: unknown): value is WasmModuleCommandEntry {
  const record = value as Record<string, unknown>;
  return (
    typeof record?.name === "string" &&
    typeof record?.command === "string" &&
    typeof record?.description === "string" &&
    isCommandCategory(record?.category) &&
    Array.isArray(record?.tags) &&
    record.tags.every((entry: unknown) => typeof entry === "string") &&
    isAvailability(record?.availability)
  );
}

function isPosition(value: unknown): value is { x: number; y: number; z: number } {
  const record = value as Record<string, unknown>;
  return ["x", "y", "z"].every((key) => typeof record?.[key] === "number");
}

function isOpening(value: unknown): value is WasmOpening {
  const record = value as Record<string, unknown>;
  return (
    typeof record?.width === "number" &&
    typeof record?.height === "number" &&
    typeof record?.type === "string" &&
    isPosition(record?.position)
  );
}

function isWall(value: unknown): value is WasmWall {
  const record = value as Record<string, unknown>;
  return (
    typeof record?.height === "number" &&
    typeof record?.thickness === "number" &&
    isPosition(record?.startPoint) &&
    isPosition(record?.endPoint)
  );
}

function isRoomBoundaries(value: unknown): value is WasmRoomBoundaries {
  const record = value as Record<string, unknown>;
  const walls = record?.walls;
  const openings = record?.openings;
  return (
    Array.isArray(walls) && walls.every(isWall) &&
    Array.isArray(openings) && openings.every(isOpening)
  );
}

function isEquipment(value: unknown): value is WasmEquipmentInfo {
  const record = value as Record<string, unknown>;
  return (
    typeof record?.id === "string" &&
    typeof record?.name === "string" &&
    typeof record?.equipmentType === "string" &&
    typeof record?.status === "string" &&
    isPosition(record?.position) &&
    typeof record?.properties === "object" &&
    record?.properties !== null &&
    typeof record?.addressPath === "string"
  );
}

function isScanData(value: unknown): value is WasmArScanData {
  const record = value as Record<string, unknown>;
  const equipment = record?.detectedEquipment;
  return (
    Array.isArray(equipment) && equipment.every((entry) => {
      const item = entry as Record<string, unknown>;
      return (
        typeof item?.name === "string" &&
        typeof item?.type === "string" &&
        typeof item?.confidence === "number" &&
        isPosition(item?.position)
      );
    }) &&
    isRoomBoundaries(record?.roomBoundaries)
  );
}

function isMeshBuffers(value: unknown): value is WasmMeshBuffers {
  const record = value as Record<string, unknown>;
  const isNumberArray = (candidate: unknown) =>
    Array.isArray(candidate) && candidate.every((entry) => typeof entry === "number");
  const boundsMin = record?.boundsMin;
  const boundsMax = record?.boundsMax;

  return (
    isNumberArray(record?.wallPositions) &&
    isNumberArray(record?.equipmentPositions) &&
    isNumberArray(record?.pointCloudPositions) &&
    Array.isArray(boundsMin) &&
      boundsMin.length === 3 &&
      boundsMin.every((entry) => typeof entry === "number") &&
    Array.isArray(boundsMax) &&
      boundsMax.length === 3 &&
      boundsMax.every((entry) => typeof entry === "number")
  );
}

export async function initWasm(): Promise<ArxosWasmModule> {
  if (wasmModule) {
    return wasmModule;
  }

  try {
    const module = (await import(
      /* @vite-ignore */
      "@arxos-wasm"
    )) as unknown as { default?: () => Promise<unknown> } & ArxosWasmModule;

    if (typeof module.default === "function") {
      await module.default();
    }

    wasmModule = module;
    return module;
  } catch (error) {
    console.error("Failed to load ArxOS WASM bindings:", error);
    throw new Error(
      "ArxOS WASM package missing. Run `wasm-pack build crates/arxos-wasm --target web --out-dir pkg` before starting the PWA."
    );
  }
}

export function requireWasm(): ArxosWasmModule {
  if (!wasmModule) {
    throw new Error("WASM module not initialized. Call initWasm() first.");
  }
  return wasmModule;
}

export async function fetchCommandPalette(): Promise<WasmCommandEntry[]> {
  const module = await initWasm();
  const payload = await module.command_palette();
  if (!Array.isArray(payload) || !payload.every(isCommandEntry)) {
    throw new Error("WASM returned invalid command palette payload");
  }
  return payload;
}

export async function fetchCommandCategories(): Promise<WasmCommandCategory[]> {
  const module = await initWasm();
  const payload = await module.command_categories();
  if (!Array.isArray(payload) || !payload.every(isCommandCategory)) {
    throw new Error("WASM returned invalid command category payload");
  }
  return payload;
}

export async function fetchCommandDetails(name: string): Promise<WasmCommandEntry | null> {
  try {
    const module = await initWasm();
    const payload = await module.command_details(name);
    if (!isCommandEntry(payload)) {
      throw new Error("Invalid command detail payload");
    }
    return payload;
  } catch (error) {
    console.warn("Command details unavailable:", error);
    return null;
  }
}

export async function parseArScan(json: string): Promise<WasmArScanData> {
  const module = await initWasm();
  const payload = module.parse_ar_scan(json);
  if (!isScanData(payload)) {
    throw new Error("WASM returned invalid AR scan payload");
  }
  return payload;
}

export async function extractEquipmentFromScan(json: string): Promise<WasmEquipmentInfo[]> {
  const module = await initWasm();
  const payload = module.extract_equipment(json);
  if (!Array.isArray(payload) || !payload.every(isEquipment)) {
    throw new Error("WASM returned invalid equipment payload");
  }
  return payload;
}

export async function generateScanMesh(json: string): Promise<WasmMeshBuffers> {
  const module = await initWasm();
  const payload = module.generate_scan_mesh(json);
  if (!isMeshBuffers(payload)) {
    throw new Error("WASM returned invalid mesh buffers");
  }
  return payload;
}

export async function validateArScan(json: string): Promise<boolean> {
  const module = await initWasm();
  return module.validate_ar_scan(json);
}

