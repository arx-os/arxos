/**
 * Validation tests
 */

import { describe, it, expect } from "vitest";
import { validateOperation, validateBatch } from "../edit/validation";
import {
  createAddRoomOperation,
  createDeleteRoomOperation,
  createMoveRoomOperation,
  createResizeRoomOperation,
  createAddEquipmentOperation,
  createDeleteEquipmentOperation,
  createMoveEquipmentOperation,
} from "../edit/operations";

describe("Validation", () => {
  describe("validateOperation", () => {
    describe("add-room", () => {
      it("should validate valid room", () => {
        const op = createAddRoomOperation("floor-1", {
          name: "Conference Room",
          bounds: {
            min: { x: 0, y: 0 },
            max: { x: 10, y: 8 },
          },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it("should reject room without name", () => {
        const op = createAddRoomOperation("floor-1", {});

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
        expect(result.errors).toContain("Room name is required");
      });

      it("should reject room with invalid dimensions", () => {
        const op = createAddRoomOperation("floor-1", {
          name: "Tiny Room",
          bounds: {
            min: { x: 0, y: 0 },
            max: { x: 0.2, y: 0.3 },  // Too small
          },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      });

      it("should reject room with huge dimensions", () => {
        const op = createAddRoomOperation("floor-1", {
          name: "Huge Room",
          bounds: {
            min: { x: 0, y: 0 },
            max: { x: 200, y: 200 },  // Too large
          },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      });

      it("should accept large but valid dimensions", () => {
        const op = createAddRoomOperation("floor-1", {
          name: "Large Room",
          bounds: {
            min: { x: 0, y: 0 },
            max: { x: 60, y: 60 },
          },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
      });

      it("should reject room out of bounds", () => {
        const op = createAddRoomOperation("floor-1", {
          name: "Far Room",
          bounds: {
            min: { x: 2000, y: 2000 },  // Way out of bounds
            max: { x: 2010, y: 2010 },
          },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      });
    });

    describe("delete-room", () => {
      it("should validate valid delete", () => {
        const op = createDeleteRoomOperation("floor-1", "room-1");

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it("should reject delete without roomId", () => {
        const op = createDeleteRoomOperation("floor-1", "");

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
        expect(result.errors).toContain("Room ID is required");
      });
    });

    describe("move-room", () => {
      it("should validate valid move", () => {
        const op = createMoveRoomOperation("floor-1", "room-1", 0, 0, 10, 10);

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it("should reject move without roomId", () => {
        const op = createMoveRoomOperation("floor-1", "", 0, 0, 10, 10);

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });

      it("should reject move out of bounds", () => {
        const op = createMoveRoomOperation("floor-1", "room-1", 0, 0, 5000, 5000);

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });

      it("should reject move with NaN coordinates", () => {
        const op = createMoveRoomOperation("floor-1", "room-1", 0, 0, NaN, 10);

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });
    });

    describe("resize-room", () => {
      it("should validate valid resize", () => {
        const op = createResizeRoomOperation("floor-1", "room-1", 5, 5, 10, 8);

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it("should reject resize without roomId", () => {
        const op = createResizeRoomOperation("floor-1", "", 5, 5, 10, 8);

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });

      it("should reject resize to invalid dimensions", () => {
        const op = createResizeRoomOperation("floor-1", "room-1", 5, 5, 0.1, 0.2);

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });
    });

    describe("add-equipment", () => {
      it("should validate valid equipment", () => {
        const op = createAddEquipmentOperation("floor-1", {
          name: "Desk",
          position: { x: 5, y: 5, z: 0 },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it("should reject equipment without name", () => {
        const op = createAddEquipmentOperation("floor-1", {
          position: { x: 5, y: 5, z: 0 },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
        expect(result.errors).toContain("Equipment name is required");
      });

      it("should reject equipment out of bounds", () => {
        const op = createAddEquipmentOperation("floor-1", {
          name: "Desk",
          position: { x: 5000, y: 5000, z: 0 },
        });

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });
    });

    describe("delete-equipment", () => {
      it("should validate valid delete", () => {
        const op = createDeleteEquipmentOperation("floor-1", "equipment-1");

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it("should reject delete without equipmentId", () => {
        const op = createDeleteEquipmentOperation("floor-1", "");

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });
    });

    describe("move-equipment", () => {
      it("should validate valid move", () => {
        const op = createMoveEquipmentOperation("floor-1", "equipment-1", 0, 0, 0, 10, 10, 0);

        const result = validateOperation(op);

        expect(result.valid).toBe(true);
        expect(result.errors).toHaveLength(0);
      });

      it("should reject move without equipmentId", () => {
        const op = createMoveEquipmentOperation("floor-1", "", 0, 0, 0, 10, 10, 0);

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });

      it("should reject move out of bounds", () => {
        const op = createMoveEquipmentOperation("floor-1", "equipment-1", 0, 0, 0, 5000, 5000, 0);

        const result = validateOperation(op);

        expect(result.valid).toBe(false);
      });
    });
  });

  describe("validateBatch", () => {
    it("should validate empty batch", () => {
      const result = validateBatch([]);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("should validate all valid operations", () => {
      const ops = [
        createAddRoomOperation("floor-1", {
          name: "Room 1",
          bounds: { min: { x: 0, y: 0 }, max: { x: 10, y: 8 } },
        }),
        createAddRoomOperation("floor-1", {
          name: "Room 2",
          bounds: { min: { x: 15, y: 0 }, max: { x: 25, y: 8 } },
        }),
      ];

      const result = validateBatch(ops);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("should collect all errors from batch", () => {
      const ops = [
        createAddRoomOperation("floor-1", {}),  // Missing name
        createDeleteRoomOperation("floor-1", ""),  // Missing roomId
        createAddEquipmentOperation("floor-1", {}),  // Missing name
      ];

      const result = validateBatch(ops);

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThanOrEqual(3);
    });

    it("should validate valid batch", () => {
      const ops = [
        createAddRoomOperation("floor-1", {
          name: "Large Room",
          bounds: { min: { x: 0, y: 0 }, max: { x: 60, y: 60 } },
        }),
      ];

      const result = validateBatch(ops);

      expect(result.valid).toBe(true);
    });
  });
});
