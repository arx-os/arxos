import { nanoid } from "nanoid";
import { create } from "zustand";

export type LogLevel = "info" | "warn" | "error" | "success";

export type LogEntry = {
  id: string;
  timestamp: number;
  level: LogLevel;
  message: string;
  command?: string;
};

export type ExecutionState = "idle" | "running" | "complete" | "error";

type CommandExecutionStore = {
  logs: LogEntry[];
  executionState: ExecutionState;
  currentCommand: string | null;
  addLog: (level: LogLevel, message: string, command?: string) => void;
  clearLogs: () => void;
  setExecutionState: (state: ExecutionState) => void;
  setCurrentCommand: (command: string | null) => void;
};

export const useCommandExecutionStore = create<CommandExecutionStore>((set) => ({
  logs: [],
  executionState: "idle",
  currentCommand: null,

  addLog: (level, message, command) => {
    set((state) => ({
      logs: [
        ...state.logs,
        {
          id: nanoid(),
          timestamp: Date.now(),
          level,
          message,
          command
        }
      ]
    }));
  },

  clearLogs: () => {
    set({ logs: [] });
  },

  setExecutionState: (executionState) => {
    set({ executionState });
  },

  setCurrentCommand: (currentCommand) => {
    set({ currentCommand });
  }
}));
