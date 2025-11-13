/**
 * AgentClient basic tests
 *
 * Note: Full WebSocket testing would require complex mocking.
 * These tests verify the basic structure and singleton pattern.
 */

import { describe, it, expect, afterEach } from "vitest";
import { AgentClient } from "../client/AgentClient";

afterEach(() => {
  // Reset singleton
  (AgentClient as any).instance = null;
});

describe("AgentClient", () => {
  describe("singleton pattern", () => {
    it("should throw if not initialized", () => {
      expect(() => AgentClient.getInstance()).toThrow(
        "AgentClient not initialized"
      );
    });

    it("should not throw when config is provided", () => {
      expect(() => {
        AgentClient.getInstance({
          endpoint: "ws://localhost:8080",
          token: "did:key:test",
        });
      }).not.toThrow();
    });

    it("should return same instance on subsequent calls", () => {
      const client1 = AgentClient.getInstance({
        endpoint: "ws://localhost:8080",
        token: "did:key:test",
      });

      const client2 = AgentClient.getInstance();

      expect(client1).toBe(client2);
    });
  });
});
