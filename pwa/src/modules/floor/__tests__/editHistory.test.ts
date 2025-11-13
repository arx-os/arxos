/**
 * Edit history tests
 */

import { describe, it, expect } from "vitest";
import {
  createEditHistory,
  addOperation,
  canUndo,
  canRedo,
  getUndoOperation,
  getRedoOperation,
  undo,
  redo,
  getInverseOperation,
  getHistorySummary,
} from "../edit/history";
import {
  createAddRoomOperation,
  createDeleteRoomOperation,
  createMoveRoomOperation,
  createAddEquipmentOperation,
} from "../edit/operations";

describe("Edit History", () => {
  describe("createEditHistory", () => {
    it("should create empty history", () => {
      const history = createEditHistory();

      expect(history.operations).toEqual([]);
      expect(history.currentIndex).toBe(-1);
    });
  });

  describe("addOperation", () => {
    it("should add operation to empty history", () => {
      const history = createEditHistory();
      const operation = createAddRoomOperation("floor-1", { name: "Room 1" });

      const newHistory = addOperation(history, operation);

      expect(newHistory.operations).toHaveLength(1);
      expect(newHistory.operations[0]).toBe(operation);
      expect(newHistory.currentIndex).toBe(0);
    });

    it("should add multiple operations", () => {
      let history = createEditHistory();

      const op1 = createAddRoomOperation("floor-1", { name: "Room 1" });
      const op2 = createAddRoomOperation("floor-1", { name: "Room 2" });
      const op3 = createAddRoomOperation("floor-1", { name: "Room 3" });

      history = addOperation(history, op1);
      history = addOperation(history, op2);
      history = addOperation(history, op3);

      expect(history.operations).toHaveLength(3);
      expect(history.currentIndex).toBe(2);
    });

    it("should clear redo history when adding new operation", () => {
      let history = createEditHistory();

      const op1 = createAddRoomOperation("floor-1", { name: "Room 1" });
      const op2 = createAddRoomOperation("floor-1", { name: "Room 2" });
      const op3 = createAddRoomOperation("floor-1", { name: "Room 3" });

      history = addOperation(history, op1);
      history = addOperation(history, op2);

      // Undo once
      history = undo(history);
      expect(history.currentIndex).toBe(0);

      // Add new operation - should clear op2
      history = addOperation(history, op3);

      expect(history.operations).toHaveLength(2);
      expect(history.operations[1]).toBe(op3);
      expect(history.currentIndex).toBe(1);
    });

    it("should limit history size", () => {
      let history = createEditHistory();

      // Add 150 operations (max is 100)
      for (let i = 0; i < 150; i++) {
        const op = createAddRoomOperation("floor-1", { name: `Room ${i}` });
        history = addOperation(history, op);
      }

      expect(history.operations).toHaveLength(100);
      expect(history.currentIndex).toBe(99);
    });
  });

  describe("canUndo", () => {
    it("should return false for empty history", () => {
      const history = createEditHistory();
      expect(canUndo(history)).toBe(false);
    });

    it("should return true when operations exist", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });
      history = addOperation(history, op);

      expect(canUndo(history)).toBe(true);
    });

    it("should return false after undo to beginning", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });
      history = addOperation(history, op);
      history = undo(history);

      expect(canUndo(history)).toBe(false);
    });
  });

  describe("canRedo", () => {
    it("should return false for empty history", () => {
      const history = createEditHistory();
      expect(canRedo(history)).toBe(false);
    });

    it("should return false when at latest operation", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });
      history = addOperation(history, op);

      expect(canRedo(history)).toBe(false);
    });

    it("should return true after undo", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });
      history = addOperation(history, op);
      history = undo(history);

      expect(canRedo(history)).toBe(true);
    });
  });

  describe("getUndoOperation", () => {
    it("should return null for empty history", () => {
      const history = createEditHistory();
      expect(getUndoOperation(history)).toBeNull();
    });

    it("should return current operation", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });
      history = addOperation(history, op);

      expect(getUndoOperation(history)).toBe(op);
    });
  });

  describe("getRedoOperation", () => {
    it("should return null when at latest", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });
      history = addOperation(history, op);

      expect(getRedoOperation(history)).toBeNull();
    });

    it("should return next operation after undo", () => {
      let history = createEditHistory();
      const op1 = createAddRoomOperation("floor-1", { name: "Room 1" });
      const op2 = createAddRoomOperation("floor-1", { name: "Room 2" });

      history = addOperation(history, op1);
      history = addOperation(history, op2);
      history = undo(history);

      expect(getRedoOperation(history)).toBe(op2);
    });
  });

  describe("undo", () => {
    it("should move pointer backward", () => {
      let history = createEditHistory();
      const op1 = createAddRoomOperation("floor-1", { name: "Room 1" });
      const op2 = createAddRoomOperation("floor-1", { name: "Room 2" });

      history = addOperation(history, op1);
      history = addOperation(history, op2);

      expect(history.currentIndex).toBe(1);

      history = undo(history);
      expect(history.currentIndex).toBe(0);
    });

    it("should not go below -1", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });

      history = addOperation(history, op);
      history = undo(history);
      history = undo(history);

      expect(history.currentIndex).toBe(-1);
    });
  });

  describe("redo", () => {
    it("should move pointer forward", () => {
      let history = createEditHistory();
      const op1 = createAddRoomOperation("floor-1", { name: "Room 1" });
      const op2 = createAddRoomOperation("floor-1", { name: "Room 2" });

      history = addOperation(history, op1);
      history = addOperation(history, op2);
      history = undo(history);

      expect(history.currentIndex).toBe(0);

      history = redo(history);
      expect(history.currentIndex).toBe(1);
    });

    it("should not go beyond operations length", () => {
      let history = createEditHistory();
      const op = createAddRoomOperation("floor-1", { name: "Room 1" });

      history = addOperation(history, op);
      history = undo(history);
      history = redo(history);
      history = redo(history);

      expect(history.currentIndex).toBe(0);
    });
  });

  describe("getInverseOperation", () => {
    it("should create inverse for add-room", () => {
      const op = createAddRoomOperation("floor-1", {
        id: "room-1",
        name: "Room 1",
      });

      const inverse = getInverseOperation(op);

      expect(inverse).toBeDefined();
      expect(inverse?.type).toBe("delete-room");
      expect((inverse as any).roomId).toBe("room-1");
    });

    it("should create inverse for delete-room", () => {
      const deletedRoom: any = {
        id: "room-1",
        name: "Room 1",
        room_type: "office",
        bounds: { min: { x: 0, y: 0 }, max: { x: 10, y: 10 } },
        equipment: [],
      };

      const op = createDeleteRoomOperation("floor-1", "room-1", deletedRoom);

      const inverse = getInverseOperation(op);

      expect(inverse).toBeDefined();
      expect(inverse?.type).toBe("add-room");
      expect((inverse as any).room).toBe(deletedRoom);
    });

    it("should create inverse for move-room", () => {
      const op = createMoveRoomOperation("floor-1", "room-1", 0, 0, 10, 10);

      const inverse = getInverseOperation(op);

      expect(inverse).toBeDefined();
      expect(inverse?.type).toBe("move-room");
      expect((inverse as any).fromX).toBe(10);
      expect((inverse as any).toX).toBe(0);
    });

    it("should return null for delete without deleted data", () => {
      const op = createDeleteRoomOperation("floor-1", "room-1");

      const inverse = getInverseOperation(op);

      expect(inverse).toBeNull();
    });
  });

  describe("getHistorySummary", () => {
    it("should return correct summary", () => {
      let history = createEditHistory();

      const op1 = createAddRoomOperation("floor-1", { name: "Room 1" });
      const op2 = createAddRoomOperation("floor-1", { name: "Room 2" });
      const op3 = createAddRoomOperation("floor-1", { name: "Room 3" });

      history = addOperation(history, op1);
      history = addOperation(history, op2);
      history = addOperation(history, op3);
      history = undo(history);

      const summary = getHistorySummary(history);

      expect(summary.totalOperations).toBe(3);
      expect(summary.undoCount).toBe(2);
      expect(summary.redoCount).toBe(1);
    });
  });
});
