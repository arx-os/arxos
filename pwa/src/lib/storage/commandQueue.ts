/**
 * Command queue storage operations
 */

import { v4 as uuidv4 } from "uuid";
import { getItem, setItem } from "./db";
import type { QueuedCommand, STORAGE_KEYS } from "./types";
import type { AgentAction } from "../../modules/agent/client/types";

const QUEUE_KEY: (typeof STORAGE_KEYS)["COMMAND_QUEUE"] = "arxos:command-queue";

/**
 * Get all queued commands
 */
export async function getQueuedCommands(): Promise<QueuedCommand[]> {
  const queue = await getItem<QueuedCommand[]>(QUEUE_KEY);
  return queue || [];
}

/**
 * Add a command to the queue
 */
export async function enqueueCommand(
  command: AgentAction,
  payload: unknown,
  sessionId: string
): Promise<QueuedCommand> {
  const queue = await getQueuedCommands();

  const queuedCommand: QueuedCommand = {
    id: uuidv4(),
    command,
    payload,
    timestamp: Date.now(),
    retryCount: 0,
    status: "pending",
    sessionId,
  };

  queue.push(queuedCommand);
  await setItem(QUEUE_KEY, queue);

  return queuedCommand;
}

/**
 * Remove a command from the queue
 */
export async function dequeueCommand(commandId: string): Promise<void> {
  const queue = await getQueuedCommands();
  const filteredQueue = queue.filter((cmd) => cmd.id !== commandId);
  await setItem(QUEUE_KEY, filteredQueue);
}

/**
 * Update a command in the queue
 */
export async function updateQueuedCommand(
  commandId: string,
  updates: Partial<QueuedCommand>
): Promise<void> {
  const queue = await getQueuedCommands();
  const index = queue.findIndex((cmd) => cmd.id === commandId);

  if (index !== -1) {
    queue[index] = { ...queue[index], ...updates };
    await setItem(QUEUE_KEY, queue);
  }
}

/**
 * Get commands for a specific session
 */
export async function getSessionCommands(
  sessionId: string
): Promise<QueuedCommand[]> {
  const queue = await getQueuedCommands();
  return queue.filter((cmd) => cmd.sessionId === sessionId);
}

/**
 * Clear all commands for a session
 */
export async function clearSessionCommands(sessionId: string): Promise<void> {
  const queue = await getQueuedCommands();
  const filteredQueue = queue.filter((cmd) => cmd.sessionId !== sessionId);
  await setItem(QUEUE_KEY, filteredQueue);
}

/**
 * Clear all queued commands
 */
export async function clearAllCommands(): Promise<void> {
  await setItem(QUEUE_KEY, []);
}

/**
 * Get pending commands count
 */
export async function getPendingCount(): Promise<number> {
  const queue = await getQueuedCommands();
  return queue.filter((cmd) => cmd.status === "pending").length;
}

/**
 * Get failed commands
 */
export async function getFailedCommands(): Promise<QueuedCommand[]> {
  const queue = await getQueuedCommands();
  return queue.filter((cmd) => cmd.status === "failed");
}
