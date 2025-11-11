declare module "@arxos-wasm" {
  export function arxos_version(): string;
  export function parse_ar_scan(json: string): unknown;
  export function extract_equipment(json: string): unknown;
  export function validate_ar_scan(json: string): boolean;
  export function command_palette(): Promise<unknown>;
  export function command_categories(): Promise<unknown>;
  export function command_details(name: string): Promise<unknown>;
}

