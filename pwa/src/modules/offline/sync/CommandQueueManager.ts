/**
 * Command Queue Manager
 *
 * Manages queuing and processing of commands when offline/online.
 */

import { AgentClient } from "../../agent/client/AgentClient";
import type { AgentAction } from "../../agent/client/types";
import {
  getQueuedCommands,
  enqueueCommand,
  dequeueCommand,
  updateQueuedCommand,
  getPendingCount,
} from "../../../lib/storage/commandQueue";
import { incrementCommandCount } from "../../../lib/storage/session";
import type { QueuedCommand } from "../../../lib/storage/types";

export interface QueueProcessResult {
  processed: number;
  successful: number;
  failed: number;
  errors: Array<{ commandId: string; error: string }>;
}

const MAX_RETRIES = 3;

export class CommandQueueManager {
  private isProcessing = false;
  private processingListeners: Set<(progress: QueueProcessResult) => void> = new Set();

  /**
   * Queue a command for later execution
   */
  async queue(
    command: AgentAction,
    payload: unknown,
    sessionId: string
  ): Promise<QueuedCommand> {

    const queuedCommand = await enqueueCommand(command, payload, sessionId);
    await incrementCommandCount();

    return queuedCommand;
  }

  /**
   * Process all queued commands
   */
  async processQueue(): Promise<QueueProcessResult> {
    if (this.isProcessing) {
      return {
        processed: 0,
        successful: 0,
        failed: 0,
        errors: [],
      };
    }

    this.isProcessing = true;

    const result: QueueProcessResult = {
      processed: 0,
      successful: 0,
      failed: 0,
      errors: [],
    };

    try {
      const queue = await getQueuedCommands();
      const pendingCommands = queue.filter(
        (cmd) => cmd.status === "pending" || cmd.status === "retrying"
      );


      for (const cmd of pendingCommands) {
        result.processed++;
        this.notifyProgress(result);

        try {
          await this.executeCommand(cmd);
          await dequeueCommand(cmd.id);
          result.successful++;
        } catch (error) {
          const errorMessage = (error as Error).message;
          console.error(`Command failed: ${cmd.command}`, error);

          // Increment retry count
          const newRetryCount = cmd.retryCount + 1;

          if (newRetryCount >= MAX_RETRIES) {
            // Max retries reached, mark as failed
            await updateQueuedCommand(cmd.id, {
              status: "failed",
              retryCount: newRetryCount,
            });
            result.failed++;
            result.errors.push({ commandId: cmd.id, error: errorMessage });
          } else {
            // Retry later
            await updateQueuedCommand(cmd.id, {
              status: "retrying",
              retryCount: newRetryCount,
            });
          }
        }
      }

      this.notifyProgress(result);
    } catch (error) {
      console.error("Queue processing error:", error);
    } finally {
      this.isProcessing = false;
    }

    return result;
  }

  /**
   * Execute a single queued command
   */
  private async executeCommand(cmd: QueuedCommand): Promise<void> {
    const client = AgentClient.getInstance();
    await client.send(cmd.command, cmd.payload, { timeout: 30000 });
  }

  /**
   * Get current queue status
   */
  async getStatus(): Promise<{
    pending: number;
    isProcessing: boolean;
  }> {
    const pending = await getPendingCount();
    return {
      pending,
      isProcessing: this.isProcessing,
    };
  }

  /**
   * Subscribe to processing progress
   */
  onProgress(listener: (progress: QueueProcessResult) => void): () => void {
    this.processingListeners.add(listener);
    return () => {
      this.processingListeners.delete(listener);
    };
  }

  /**
   * Notify all listeners of progress
   */
  private notifyProgress(progress: QueueProcessResult): void {
    this.processingListeners.forEach((listener) => listener(progress));
  }

  /**
   * Check if queue is empty
   */
  async isEmpty(): Promise<boolean> {
    const pending = await getPendingCount();
    return pending === 0;
  }
}

// Singleton instance
let queueManager: CommandQueueManager | null = null;

export function getQueueManager(): CommandQueueManager {
  if (!queueManager) {
    queueManager = new CommandQueueManager();
  }
  return queueManager;
}
