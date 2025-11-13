/**
 * Message Queue for Offline Support
 *
 * Queues collaboration messages when offline and replays them when reconnected.
 * Integrates with M05 offline sync infrastructure.
 */

import { get as idbGet, set as idbSet } from "idb-keyval";
import type { MessageEnvelope, CollaborationMessage, MessageStatus } from "../types";

const STORAGE_KEY = "arxos:collaboration:message-queue";

interface QueuedMessage {
  id: string;
  message: CollaborationMessage;
  retryCount: number;
  lastAttempt: number | null;
  error: string | null;
}

/**
 * Get queued messages from IndexedDB
 */
export async function getQueuedMessages(): Promise<QueuedMessage[]> {
  try {
    const queue = await idbGet<QueuedMessage[]>(STORAGE_KEY);
    return queue || [];
  } catch (error) {
    console.error("Failed to get queued messages:", error);
    return [];
  }
}

/**
 * Add message to queue
 */
export async function enqueueMessage(
  message: CollaborationMessage
): Promise<void> {
  try {
    const queue = await getQueuedMessages();

    // Check if already queued
    const exists = queue.some((q) => q.message.envelope.id === message.envelope.id);
    if (exists) {
      return;
    }

    const queuedMessage: QueuedMessage = {
      id: message.envelope.id,
      message: {
        ...message,
        status: "pending" as MessageStatus,
      },
      retryCount: 0,
      lastAttempt: null,
      error: null,
    };

    await idbSet(STORAGE_KEY, [...queue, queuedMessage]);
  } catch (error) {
    console.error("Failed to enqueue message:", error);
    throw error;
  }
}

/**
 * Remove message from queue
 */
export async function dequeueMessage(messageId: string): Promise<void> {
  try {
    const queue = await getQueuedMessages();
    const filtered = queue.filter((q) => q.id !== messageId);
    await idbSet(STORAGE_KEY, filtered);
  } catch (error) {
    console.error("Failed to dequeue message:", error);
    throw error;
  }
}

/**
 * Update queued message
 */
export async function updateQueuedMessage(
  messageId: string,
  updates: Partial<QueuedMessage>
): Promise<void> {
  try {
    const queue = await getQueuedMessages();
    const updated = queue.map((q) =>
      q.id === messageId ? { ...q, ...updates } : q
    );
    await idbSet(STORAGE_KEY, updated);
  } catch (error) {
    console.error("Failed to update queued message:", error);
    throw error;
  }
}

/**
 * Get pending message count
 */
export async function getPendingMessageCount(): Promise<number> {
  try {
    const queue = await getQueuedMessages();
    return queue.length;
  } catch (error) {
    console.error("Failed to get pending message count:", error);
    return 0;
  }
}

/**
 * Clear all queued messages
 */
export async function clearMessageQueue(): Promise<void> {
  try {
    await idbSet(STORAGE_KEY, []);
  } catch (error) {
    console.error("Failed to clear message queue:", error);
    throw error;
  }
}

/**
 * Process message queue (replay messages)
 */
export async function processMessageQueue(
  sendFn: (envelope: MessageEnvelope) => Promise<void>
): Promise<{ success: number; failed: number }> {
  const queue = await getQueuedMessages();
  let success = 0;
  let failed = 0;

  for (const queuedMessage of queue) {
    try {
      await sendFn(queuedMessage.message.envelope);
      await dequeueMessage(queuedMessage.id);
      success++;
    } catch (error) {
      failed++;

      // Update retry count
      const newRetryCount = queuedMessage.retryCount + 1;

      if (newRetryCount >= 3) {
        // Max retries reached, mark as failed
        await updateQueuedMessage(queuedMessage.id, {
          retryCount: newRetryCount,
          lastAttempt: Date.now(),
          error: (error as Error).message,
          message: {
            ...queuedMessage.message,
            status: "failed" as MessageStatus,
            error: (error as Error).message,
          },
        });
      } else {
        // Retry later
        await updateQueuedMessage(queuedMessage.id, {
          retryCount: newRetryCount,
          lastAttempt: Date.now(),
          error: (error as Error).message,
        });
      }
    }
  }

  return { success, failed };
}

/**
 * Get failed messages
 */
export async function getFailedMessages(): Promise<QueuedMessage[]> {
  try {
    const queue = await getQueuedMessages();
    return queue.filter((q) => q.retryCount >= 3);
  } catch (error) {
    console.error("Failed to get failed messages:", error);
    return [];
  }
}

/**
 * Retry failed message
 */
export async function retryFailedMessage(messageId: string): Promise<void> {
  try {
    await updateQueuedMessage(messageId, {
      retryCount: 0,
      error: null,
      lastAttempt: null,
    });
  } catch (error) {
    console.error("Failed to retry message:", error);
    throw error;
  }
}
