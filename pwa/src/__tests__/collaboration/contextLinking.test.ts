/**
 * Context Linking Utilities Tests
 */

import { describe, it, expect } from "vitest";
import {
  createElementReference,
  hasElementReference,
  getElementReference,
  filterMessagesByElement,
  extractElementReferences,
  countMessagesByElement,
  formatElementReference,
  matchesElementReference,
  parseElementId,
} from "../../modules/collaboration/utils/contextLinking";
import type {
  CollaborationMessage,
  ElementReference,
  MessageEnvelope,
} from "../../modules/collaboration/types";

describe("Context Linking Utilities", () => {
  describe("createElementReference", () => {
    it("should create element reference with minimal data", () => {
      const ref = createElementReference("room", "room-123");

      expect(ref).toEqual({
        type: "room",
        id: "room-123",
        name: undefined,
        buildingPath: undefined,
        floorId: undefined,
      });
    });

    it("should create element reference with full data", () => {
      const ref = createElementReference("equipment", "eq-456", {
        name: "HVAC Unit",
        buildingPath: "/building1",
        floorId: "floor-2",
      });

      expect(ref).toEqual({
        type: "equipment",
        id: "eq-456",
        name: "HVAC Unit",
        buildingPath: "/building1",
        floorId: "floor-2",
      });
    });
  });

  describe("hasElementReference", () => {
    it("should return true for comment messages", () => {
      const message: CollaborationMessage = {
        envelope: {
          version: "1.0.0",
          id: "msg-1",
          type: "comment",
          timestamp: Date.now(),
          from: "user-1",
          to: "room-1",
          payload: {
            content: "Test comment",
            elementRef: createElementReference("room", "room-1"),
          },
        },
        status: "delivered",
        localTimestamp: Date.now(),
      };

      expect(hasElementReference(message)).toBe(true);
    });

    it("should return false for chat messages", () => {
      const message: CollaborationMessage = {
        envelope: {
          version: "1.0.0",
          id: "msg-1",
          type: "chat",
          timestamp: Date.now(),
          from: "user-1",
          to: "room-1",
          payload: {
            content: "Test chat",
          },
        },
        status: "delivered",
        localTimestamp: Date.now(),
      };

      expect(hasElementReference(message)).toBe(false);
    });
  });

  describe("getElementReference", () => {
    it("should extract element reference from comment", () => {
      const elementRef = createElementReference("room", "room-1", {
        name: "Conference Room",
      });

      const message: CollaborationMessage = {
        envelope: {
          version: "1.0.0",
          id: "msg-1",
          type: "comment",
          timestamp: Date.now(),
          from: "user-1",
          to: "room-1",
          payload: {
            content: "Test comment",
            elementRef,
          },
        },
        status: "delivered",
        localTimestamp: Date.now(),
      };

      const result = getElementReference(message);
      expect(result).toEqual(elementRef);
    });

    it("should return null for non-comment messages", () => {
      const message: CollaborationMessage = {
        envelope: {
          version: "1.0.0",
          id: "msg-1",
          type: "chat",
          timestamp: Date.now(),
          from: "user-1",
          to: "room-1",
          payload: {
            content: "Test chat",
          },
        },
        status: "delivered",
        localTimestamp: Date.now(),
      };

      const result = getElementReference(message);
      expect(result).toBeNull();
    });
  });

  describe("filterMessagesByElement", () => {
    const createMessage = (
      elementRef: ElementReference | null
    ): CollaborationMessage => ({
      envelope: {
        version: "1.0.0",
        id: `msg-${Math.random()}`,
        type: elementRef ? "comment" : "chat",
        timestamp: Date.now(),
        from: "user-1",
        to: "room-1",
        payload: elementRef
          ? { content: "Comment", elementRef }
          : { content: "Chat" },
      },
      status: "delivered",
      localTimestamp: Date.now(),
    });

    it("should filter messages by element reference", () => {
      const ref1 = createElementReference("room", "room-1");
      const ref2 = createElementReference("room", "room-2");

      const messages = [
        createMessage(ref1),
        createMessage(ref2),
        createMessage(ref1),
        createMessage(null),
      ];

      const filtered = filterMessagesByElement(messages, ref1);

      expect(filtered).toHaveLength(2);
      expect(filtered[0].envelope.type).toBe("comment");
    });
  });

  describe("extractElementReferences", () => {
    it("should extract unique element references", () => {
      const ref1 = createElementReference("room", "room-1");
      const ref2 = createElementReference("equipment", "eq-1");

      const messages: CollaborationMessage[] = [
        {
          envelope: {
            version: "1.0.0",
            id: "msg-1",
            type: "comment",
            timestamp: Date.now(),
            from: "user-1",
            to: "room-1",
            payload: { content: "Comment 1", elementRef: ref1 },
          },
          status: "delivered",
          localTimestamp: Date.now(),
        },
        {
          envelope: {
            version: "1.0.0",
            id: "msg-2",
            type: "comment",
            timestamp: Date.now(),
            from: "user-1",
            to: "room-1",
            payload: { content: "Comment 2", elementRef: ref2 },
          },
          status: "delivered",
          localTimestamp: Date.now(),
        },
        {
          envelope: {
            version: "1.0.0",
            id: "msg-3",
            type: "comment",
            timestamp: Date.now(),
            from: "user-1",
            to: "room-1",
            payload: { content: "Comment 3", elementRef: ref1 },
          },
          status: "delivered",
          localTimestamp: Date.now(),
        },
      ];

      const refs = extractElementReferences(messages);

      expect(refs).toHaveLength(2);
      expect(refs).toContainEqual(ref1);
      expect(refs).toContainEqual(ref2);
    });
  });

  describe("countMessagesByElement", () => {
    it("should count messages per element", () => {
      const ref1 = createElementReference("room", "room-1");
      const ref2 = createElementReference("equipment", "eq-1");

      const messages: CollaborationMessage[] = [
        {
          envelope: {
            version: "1.0.0",
            id: "msg-1",
            type: "comment",
            timestamp: Date.now(),
            from: "user-1",
            to: "room-1",
            payload: { content: "Comment 1", elementRef: ref1 },
          },
          status: "delivered",
          localTimestamp: Date.now(),
        },
        {
          envelope: {
            version: "1.0.0",
            id: "msg-2",
            type: "comment",
            timestamp: Date.now(),
            from: "user-1",
            to: "room-1",
            payload: { content: "Comment 2", elementRef: ref2 },
          },
          status: "delivered",
          localTimestamp: Date.now(),
        },
        {
          envelope: {
            version: "1.0.0",
            id: "msg-3",
            type: "comment",
            timestamp: Date.now(),
            from: "user-1",
            to: "room-1",
            payload: { content: "Comment 3", elementRef: ref1 },
          },
          status: "delivered",
          localTimestamp: Date.now(),
        },
      ];

      const counts = countMessagesByElement(messages);

      expect(counts.get("room:room-1")).toBe(2);
      expect(counts.get("equipment:eq-1")).toBe(1);
    });
  });

  describe("formatElementReference", () => {
    it("should format reference with all fields", () => {
      const ref = createElementReference("room", "room-1", {
        name: "Conference Room",
        buildingPath: "/building1",
        floorId: "floor-2",
      });

      const formatted = formatElementReference(ref);

      expect(formatted).toBe(
        "/building1 → Floor floor-2 → room: Conference Room"
      );
    });

    it("should format reference with minimal fields", () => {
      const ref = createElementReference("equipment", "eq-1");

      const formatted = formatElementReference(ref);

      expect(formatted).toBe("equipment: eq-1");
    });
  });

  describe("matchesElementReference", () => {
    it("should match identical references", () => {
      const ref1 = createElementReference("room", "room-1", {
        buildingPath: "/building1",
        floorId: "floor-1",
      });

      const ref2 = createElementReference("room", "room-1", {
        buildingPath: "/building1",
        floorId: "floor-1",
      });

      expect(matchesElementReference(ref1, ref2)).toBe(true);
    });

    it("should not match different references", () => {
      const ref1 = createElementReference("room", "room-1");
      const ref2 = createElementReference("room", "room-2");

      expect(matchesElementReference(ref1, ref2)).toBe(false);
    });
  });

  describe("parseElementId", () => {
    it("should parse room ID", () => {
      expect(parseElementId("room:123")).toEqual({
        type: "room",
        id: "123",
      });

      expect(parseElementId("room-456")).toEqual({
        type: "room",
        id: "456",
      });
    });

    it("should parse equipment ID", () => {
      expect(parseElementId("equipment:abc")).toEqual({
        type: "equipment",
        id: "abc",
      });
    });

    it("should return null type for unparseable ID", () => {
      expect(parseElementId("unknown-123")).toEqual({
        type: null,
        id: "unknown-123",
      });
    });
  });
});
