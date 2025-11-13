/**
 * Message Queue Tests
 */

import { describe, it, expect, beforeEach } from "vitest";
import {
  enqueueMessage,
  dequeueMessage,
  getQueuedMessages,
  getPendingMessageCount,
  clearMessageQueue,
  processMessageQueue,
  getFailedMessages,
  retryFailedMessage,
} from "../../modules/collaboration/offline/messageQueue";
import type { CollaborationMessage } from "../../modules/collaboration/types";

// Mock IndexedDB is automatically available via fake-indexeddb in vitest.setup.ts

describe("Message Queue", () => {
  beforeEach(async () => {
    await clearMessageQueue();
  });

  const createTestMessage = (id: string): CollaborationMessage => ({
    envelope: {
      version: "1.0.0",
      id,
      type: "chat",
      timestamp: Date.now(),
      from: "user-1",
      to: "room-1",
      payload: {
        content: "Test message",
      },
    },
    status: "pending",
    localTimestamp: Date.now(),
  });

  describe("enqueueMessage", () => {
    it("should add message to queue", async () => {
      const message = createTestMessage("msg-1");

      await enqueueMessage(message);

      const queue = await getQueuedMessages();
      expect(queue).toHaveLength(1);
      expect(queue[0].message.envelope.id).toBe("msg-1");
    });

    it("should not duplicate messages", async () => {
      const message = createTestMessage("msg-1");

      await enqueueMessage(message);
      await enqueueMessage(message);

      const queue = await getQueuedMessages();
      expect(queue).toHaveLength(1);
    });

    it("should set initial status to pending", async () => {
      const message = createTestMessage("msg-1");

      await enqueueMessage(message);

      const queue = await getQueuedMessages();
      expect(queue[0].message.status).toBe("pending");
    });
  });

  describe("dequeueMessage", () => {
    it("should remove message from queue", async () => {
      const message1 = createTestMessage("msg-1");
      const message2 = createTestMessage("msg-2");

      await enqueueMessage(message1);
      await enqueueMessage(message2);

      await dequeueMessage("msg-1");

      const queue = await getQueuedMessages();
      expect(queue).toHaveLength(1);
      expect(queue[0].message.envelope.id).toBe("msg-2");
    });
  });

  describe("getPendingMessageCount", () => {
    it("should return correct count", async () => {
      await enqueueMessage(createTestMessage("msg-1"));
      await enqueueMessage(createTestMessage("msg-2"));
      await enqueueMessage(createTestMessage("msg-3"));

      const count = await getPendingMessageCount();
      expect(count).toBe(3);
    });

    it("should return 0 for empty queue", async () => {
      const count = await getPendingMessageCount();
      expect(count).toBe(0);
    });
  });

  describe("processMessageQueue", () => {
    it("should process all messages successfully", async () => {
      await enqueueMessage(createTestMessage("msg-1"));
      await enqueueMessage(createTestMessage("msg-2"));

      const sendFn = vi.fn().mockResolvedValue(undefined);

      const result = await processMessageQueue(sendFn);

      expect(result.success).toBe(2);
      expect(result.failed).toBe(0);
      expect(sendFn).toHaveBeenCalledTimes(2);

      const queue = await getQueuedMessages();
      expect(queue).toHaveLength(0);
    });

    it("should handle failures and retry", async () => {
      await enqueueMessage(createTestMessage("msg-1"));

      const sendFn = vi.fn().mockRejectedValue(new Error("Network error"));

      const result = await processMessageQueue(sendFn);

      expect(result.success).toBe(0);
      expect(result.failed).toBe(1);

      const queue = await getQueuedMessages();
      expect(queue).toHaveLength(1);
      expect(queue[0].retryCount).toBe(1);
      expect(queue[0].error).toBe("Network error");
    });

    it("should mark as failed after max retries", async () => {
      await enqueueMessage(createTestMessage("msg-1"));

      const sendFn = vi.fn().mockRejectedValue(new Error("Network error"));

      // Process 3 times (max retries)
      await processMessageQueue(sendFn);
      await processMessageQueue(sendFn);
      await processMessageQueue(sendFn);

      const queue = await getQueuedMessages();
      expect(queue[0].retryCount).toBe(3);
      expect(queue[0].message.status).toBe("failed");

      const failed = await getFailedMessages();
      expect(failed).toHaveLength(1);
    });
  });

  describe("retryFailedMessage", () => {
    it("should reset retry count", async () => {
      await enqueueMessage(createTestMessage("msg-1"));

      const sendFn = vi.fn().mockRejectedValue(new Error("Network error"));

      // Fail it 3 times
      await processMessageQueue(sendFn);
      await processMessageQueue(sendFn);
      await processMessageQueue(sendFn);

      const queue = await getQueuedMessages();
      expect(queue[0].retryCount).toBe(3);

      // Retry
      await retryFailedMessage("msg-1");

      const updatedQueue = await getQueuedMessages();
      expect(updatedQueue[0].retryCount).toBe(0);
      expect(updatedQueue[0].error).toBeNull();
    });
  });
});
