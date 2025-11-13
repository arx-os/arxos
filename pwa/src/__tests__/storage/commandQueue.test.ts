/**
 * Command Queue storage tests
 */

import { describe, it, expect, beforeEach } from "vitest";
import {
  enqueueCommand,
  dequeueCommand,
  getQueuedCommands,
  updateQueuedCommand,
  clearAllCommands,
  getPendingCount,
} from "../../lib/storage/commandQueue";
import { clearStorage } from "../../lib/storage/db";

describe("Command Queue storage", () => {
  const mockSessionId = "test-session-123";

  beforeEach(async () => {
    await clearStorage();
  });

  it("should enqueue a command", async () => {
    const command = await enqueueCommand(
      "git.commit",
      { message: "Test commit" },
      mockSessionId
    );

    expect(command).toBeDefined();
    expect(command.command).toBe("git.commit");
    expect(command.sessionId).toBe(mockSessionId);
    expect(command.status).toBe("pending");
    expect(command.retryCount).toBe(0);
  });

  it("should retrieve queued commands", async () => {
    await enqueueCommand("git.commit", { message: "Commit 1" }, mockSessionId);
    await enqueueCommand("git.status", {}, mockSessionId);

    const commands = await getQueuedCommands();
    expect(commands).toHaveLength(2);
    expect(commands[0].command).toBe("git.commit");
    expect(commands[1].command).toBe("git.status");
  });

  it("should dequeue a command", async () => {
    const command = await enqueueCommand(
      "git.commit",
      { message: "Test" },
      mockSessionId
    );

    await dequeueCommand(command.id);

    const commands = await getQueuedCommands();
    expect(commands).toHaveLength(0);
  });

  it("should update command status", async () => {
    const command = await enqueueCommand(
      "git.commit",
      { message: "Test" },
      mockSessionId
    );

    await updateQueuedCommand(command.id, {
      status: "retrying",
      retryCount: 1,
    });

    const commands = await getQueuedCommands();
    expect(commands[0].status).toBe("retrying");
    expect(commands[0].retryCount).toBe(1);
  });

  it("should get pending count", async () => {
    await enqueueCommand("git.commit", { message: "1" }, mockSessionId);
    await enqueueCommand("git.commit", { message: "2" }, mockSessionId);
    await enqueueCommand("git.commit", { message: "3" }, mockSessionId);

    const count = await getPendingCount();
    expect(count).toBe(3);
  });

  it("should filter pending commands correctly", async () => {
    const cmd1 = await enqueueCommand("git.commit", { message: "1" }, mockSessionId);
    await enqueueCommand("git.commit", { message: "2" }, mockSessionId);
    const cmd3 = await enqueueCommand("git.commit", { message: "3" }, mockSessionId);

    // Mark one as failed
    await updateQueuedCommand(cmd1.id, { status: "failed" });

    const count = await getPendingCount();
    expect(count).toBe(2); // Should only count pending/retrying
  });

  it("should clear all commands", async () => {
    await enqueueCommand("git.commit", { message: "1" }, mockSessionId);
    await enqueueCommand("git.commit", { message: "2" }, mockSessionId);

    await clearAllCommands();

    const commands = await getQueuedCommands();
    expect(commands).toHaveLength(0);
  });

  it("should preserve command payload", async () => {
    const payload = {
      message: "Test commit",
      files: ["file1.txt", "file2.txt"],
      author: { name: "Test", email: "test@example.com" },
    };

    const command = await enqueueCommand("git.commit", payload, mockSessionId);

    const commands = await getQueuedCommands();
    expect(commands[0].payload).toEqual(payload);
  });

  it("should handle multiple sessions", async () => {
    const session1 = "session-1";
    const session2 = "session-2";

    await enqueueCommand("git.commit", { msg: "S1C1" }, session1);
    await enqueueCommand("git.commit", { msg: "S1C2" }, session1);
    await enqueueCommand("git.commit", { msg: "S2C1" }, session2);

    const commands = await getQueuedCommands();
    expect(commands).toHaveLength(3);

    const s1Commands = commands.filter((c) => c.sessionId === session1);
    const s2Commands = commands.filter((c) => c.sessionId === session2);

    expect(s1Commands).toHaveLength(2);
    expect(s2Commands).toHaveLength(1);
  });
});
