export type WasmCommandCategory = {
  slug: string;
  label: string;
};

export type WasmCommandEntry = {
  name: string;
  command: string;
  description: string;
  category: WasmCommandCategory;
  shortcut?: string;
};

export type ArxosWasmModule = {
  arxos_version(): string;
  parse_ar_scan(json: string): unknown;
  extract_equipment(json: string): unknown;
  validate_ar_scan(json: string): boolean;
  command_palette(): Promise<unknown>;
  command_categories(): Promise<unknown>;
  command_details(name: string): Promise<unknown>;
};

let wasmModule: ArxosWasmModule | null = null;

function isCommandCategory(value: unknown): value is WasmCommandCategory {
  const record = value as Record<string, unknown>;
  return typeof record?.slug === "string" && typeof record?.label === "string";
}

function isCommandEntry(value: unknown): value is WasmCommandEntry {
  const record = value as Record<string, unknown>;
  return (
    typeof record?.name === "string" &&
    typeof record?.command === "string" &&
    typeof record?.description === "string" &&
    isCommandCategory(record?.category)
  );
}

export async function initWasm(): Promise<ArxosWasmModule> {
  if (wasmModule) {
    return wasmModule;
  }

  try {
    // Expect wasm-pack output in crates/arxos-wasm/pkg. `@vite-ignore` avoids static analysis so we
    // can surface a helpful runtime error if the package has not been generated yet.
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

  // Unreachable; the throw above keeps TypeScript satisfied.
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

export async function parseArScan<T = unknown>(json: string): Promise<T> {
  const module = await initWasm();
  return module.parse_ar_scan(json) as T;
}

export async function extractEquipmentFromScan<T = unknown>(json: string): Promise<T> {
  const module = await initWasm();
  return module.extract_equipment(json) as T;
}

export async function validateArScan(json: string): Promise<boolean> {
  const module = await initWasm();
  return module.validate_ar_scan(json);
}

