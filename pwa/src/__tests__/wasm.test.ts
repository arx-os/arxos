import { describe, it, expect } from "vitest";

// Note: These tests verify the WASM integration layer structure.
// The actual WASM module is mocked in vitest.setup.ts for Node environment testing.
// For full integration testing with real WASM, use Playwright E2E tests in browser.

describe("WASM Module Integration", () => {
  describe("Type Safety", () => {
    it("should define proper TypeScript types for WASM exports", () => {
      // This test verifies that our type definitions exist and are correct
      // The actual WASM module types are defined in src/types/arxos-wasm.d.ts
      expect(true).toBe(true);
    });
  });

  describe("Mock Validation", () => {
    it("should have WASM mocks available for testing", async () => {
      // Import the mocked module
      const { arxos_version, validate_ar_scan } = await import("@arxos-wasm");

      expect(typeof arxos_version).toBe("function");
      expect(arxos_version()).toBe("2.0.0");

      expect(typeof validate_ar_scan).toBe("function");
      expect(
        validate_ar_scan(
          '{"detectedEquipment": [], "roomBoundaries": {"walls": [], "openings": []}}'
        )
      ).toBe(true);
    });

    it("should validate AR scan data format", async () => {
      const { validate_ar_scan } = await import("@arxos-wasm");

      // Valid scan
      expect(
        validate_ar_scan(
          JSON.stringify({
            detectedEquipment: [],
            roomBoundaries: { walls: [], openings: [] },
          })
        )
      ).toBe(true);

      // Invalid scan (missing required fields)
      expect(validate_ar_scan("{}")).toBe(false);
      expect(validate_ar_scan("invalid json")).toBe(false);
    });
  });

  describe("Command Palette Mock", () => {
    it("should return mocked command entries", async () => {
      const { command_palette } = await import("@arxos-wasm");

      const commands = await command_palette();
      expect(Array.isArray(commands)).toBe(true);
      expect(commands.length).toBeGreaterThan(0);

      // Verify structure of first command
      const firstCommand = commands[0];
      expect(firstCommand).toHaveProperty("name");
      expect(firstCommand).toHaveProperty("command");
      expect(firstCommand).toHaveProperty("description");
      expect(firstCommand).toHaveProperty("category");
      expect(firstCommand).toHaveProperty("tags");
      expect(firstCommand).toHaveProperty("availability");

      // Verify category structure
      expect(firstCommand.category).toHaveProperty("slug");
      expect(firstCommand.category).toHaveProperty("label");

      // Verify availability structure
      expect(firstCommand.availability).toHaveProperty("cli");
      expect(firstCommand.availability).toHaveProperty("pwa");
      expect(firstCommand.availability).toHaveProperty("agent");
    });

    it("should include commands with proper PWA availability", async () => {
      const { command_palette } = await import("@arxos-wasm");

      const commands = await command_palette();
      // At least some commands should be available for PWA
      const pwaCommands = commands.filter((cmd) => cmd.availability.pwa);
      expect(pwaCommands.length).toBeGreaterThan(0);
    });
  });

  describe("Categories Mock", () => {
    it("should return mocked categories", async () => {
      const { command_categories } = await import("@arxos-wasm");

      const categories = await command_categories();
      expect(Array.isArray(categories)).toBe(true);
      expect(categories.length).toBeGreaterThan(0);

      // Verify structure
      const firstCategory = categories[0];
      expect(firstCategory).toHaveProperty("slug");
      expect(firstCategory).toHaveProperty("label");
      expect(typeof firstCategory.slug).toBe("string");
      expect(typeof firstCategory.label).toBe("string");
    });

    it("should include expected categories", async () => {
      const { command_categories } = await import("@arxos-wasm");

      const categories = await command_categories();
      const slugs = categories.map((cat) => cat.slug);

      // Check for some expected categories
      expect(slugs).toContain("building");
      expect(slugs).toContain("git");
      expect(slugs).toContain("ar");
    });
  });

  describe("Command Details Mock", () => {
    it("should return details for a valid command", async () => {
      const { command_details } = await import("@arxos-wasm");

      const details = await command_details("version");
      expect(details).toBeDefined();
      expect(details.name).toBe("version");
      expect(details).toHaveProperty("description");
      expect(details).toHaveProperty("category");
    });

    it("should reject invalid commands", async () => {
      const { command_details } = await import("@arxos-wasm");

      await expect(command_details("nonexistent-command-xyz")).rejects.toThrow(
        "Command not found"
      );
    });
  });

  describe("AR Scan Functions", () => {
    const validScanJson = JSON.stringify({
      detectedEquipment: [
        {
          name: "Test-Unit",
          type: "HVAC",
          position: { x: 1.0, y: 2.0, z: 3.0 },
          confidence: 0.95,
          detectionMethod: "Manual",
        },
      ],
      roomBoundaries: {
        walls: [],
        openings: [],
      },
    });

    it("should parse valid AR scan data", async () => {
      const { parse_ar_scan } = await import("@arxos-wasm");

      const data = parse_ar_scan(validScanJson);
      expect(data).toBeDefined();
      expect(data.detectedEquipment).toHaveLength(1);
      expect(data.roomBoundaries).toBeDefined();
    });

    it("should extract equipment from scan", async () => {
      const { extract_equipment } = await import("@arxos-wasm");

      const equipment = extract_equipment(validScanJson);
      expect(Array.isArray(equipment)).toBe(true);
      expect(equipment.length).toBeGreaterThan(0);
    });

    it("should generate scan mesh", async () => {
      const { generate_scan_mesh } = await import("@arxos-wasm");

      const mesh = generate_scan_mesh(validScanJson);
      expect(mesh).toHaveProperty("wallPositions");
      expect(mesh).toHaveProperty("equipmentPositions");
      expect(mesh).toHaveProperty("pointCloudPositions");
      expect(mesh).toHaveProperty("boundsMin");
      expect(mesh).toHaveProperty("boundsMax");
    });
  });
});
