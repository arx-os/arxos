import { describe, expect, it, beforeEach } from "vitest";
import { useCommandExecutionStore } from "../state/commandExecution";

describe("commandExecution", () => {
  beforeEach(() => {
    const { clearLogs, setExecutionState, setCurrentCommand } =
      useCommandExecutionStore.getState();
    clearLogs();
    setExecutionState("idle");
    setCurrentCommand(null);
  });

  describe("addLog", () => {
    it("should add a log entry with correct properties", () => {
      const { addLog } = useCommandExecutionStore.getState();

      addLog("info", "Test message", "test command");

      const { logs } = useCommandExecutionStore.getState();
      expect(logs).toHaveLength(1);
      expect(logs[0]).toMatchObject({
        level: "info",
        message: "Test message",
        command: "test command"
      });
      expect(logs[0].id).toBeDefined();
      expect(logs[0].timestamp).toBeGreaterThan(0);
    });

    it("should add multiple log entries in order", () => {
      const { addLog } = useCommandExecutionStore.getState();

      addLog("info", "First message");
      addLog("success", "Second message");
      addLog("error", "Third message");

      const { logs } = useCommandExecutionStore.getState();
      expect(logs).toHaveLength(3);
      expect(logs[0].message).toBe("First message");
      expect(logs[1].message).toBe("Second message");
      expect(logs[2].message).toBe("Third message");
    });

    it("should handle different log levels", () => {
      const { addLog } = useCommandExecutionStore.getState();

      addLog("info", "Info message");
      addLog("warn", "Warning message");
      addLog("error", "Error message");
      addLog("success", "Success message");

      const { logs } = useCommandExecutionStore.getState();
      expect(logs).toHaveLength(4);
      expect(logs[0].level).toBe("info");
      expect(logs[1].level).toBe("warn");
      expect(logs[2].level).toBe("error");
      expect(logs[3].level).toBe("success");
    });
  });

  describe("clearLogs", () => {
    it("should remove all log entries", () => {
      const { addLog, clearLogs } = useCommandExecutionStore.getState();

      addLog("info", "Test 1");
      addLog("info", "Test 2");
      addLog("info", "Test 3");

      const { logs: logsAfterAdding } = useCommandExecutionStore.getState();
      expect(logsAfterAdding).toHaveLength(3);

      clearLogs();

      const { logs: logsAfterClearing } = useCommandExecutionStore.getState();
      expect(logsAfterClearing).toHaveLength(0);
    });
  });

  describe("setExecutionState", () => {
    it("should update execution state", () => {
      const { setExecutionState, executionState: initial } = useCommandExecutionStore.getState();

      expect(initial).toBe("idle");

      setExecutionState("running");
      expect(useCommandExecutionStore.getState().executionState).toBe("running");

      setExecutionState("complete");
      expect(useCommandExecutionStore.getState().executionState).toBe("complete");

      setExecutionState("error");
      expect(useCommandExecutionStore.getState().executionState).toBe("error");
    });
  });

  describe("setCurrentCommand", () => {
    it("should update current command", () => {
      const { setCurrentCommand, currentCommand: initial } = useCommandExecutionStore.getState();

      expect(initial).toBeNull();

      setCurrentCommand("version");
      expect(useCommandExecutionStore.getState().currentCommand).toBe("version");

      setCurrentCommand("help");
      expect(useCommandExecutionStore.getState().currentCommand).toBe("help");

      setCurrentCommand(null);
      expect(useCommandExecutionStore.getState().currentCommand).toBeNull();
    });
  });
});
