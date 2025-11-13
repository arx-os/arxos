import { describe, expect, it } from "vitest";
import { executeCommand } from "../lib/commandExecutor";

describe("commandExecutor", () => {
  describe("executeCommand", () => {
    it("should execute version command and return success", async () => {
      const result = await executeCommand("version");

      expect(result.success).toBe(true);
      expect(result.output).toContain("ArxOS version");
      expect(result.output).toContain("2.0.0");
      expect(result.duration).toBeGreaterThanOrEqual(0);
      expect(result.error).toBeUndefined();
    });

    it("should execute help command and return success", async () => {
      const result = await executeCommand("help");

      expect(result.success).toBe(true);
      expect(result.output).toContain("ArxOS Command Shell");
      expect(result.output).toContain("version");
      expect(result.output).toContain("help");
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it("should execute clear command and return empty output", async () => {
      const result = await executeCommand("clear");

      expect(result.success).toBe(true);
      expect(result.output).toBe("");
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it("should execute unknown command and return mock output", async () => {
      const result = await executeCommand("unknown-command arg1 arg2");

      expect(result.success).toBe(true);
      expect(result.output).toContain("Mock output for command");
      expect(result.output).toContain("unknown-command arg1 arg2");
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it("should handle empty command and return error", async () => {
      const result = await executeCommand("");

      expect(result.success).toBe(false);
      expect(result.output).toBe("");
      expect(result.error).toBe("Empty command");
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it("should handle whitespace-only command and return error", async () => {
      const result = await executeCommand("   ");

      expect(result.success).toBe(false);
      expect(result.output).toBe("");
      expect(result.error).toBe("Empty command");
      expect(result.duration).toBeGreaterThanOrEqual(0);
    });

    it("should measure execution duration", async () => {
      const result = await executeCommand("version");

      expect(result.duration).toBeGreaterThanOrEqual(0);
      expect(typeof result.duration).toBe("number");
    });

    it("should parse command with multiple arguments", async () => {
      const result = await executeCommand("test-cmd arg1 arg2 arg3");

      expect(result.success).toBe(true);
      expect(result.output).toContain("test-cmd arg1 arg2 arg3");
    });
  });
});
