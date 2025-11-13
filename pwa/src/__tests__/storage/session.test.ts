/**
 * Session storage tests
 */

import { describe, it, expect, beforeEach } from "vitest";
import {
  createSession,
  getActiveSession,
  updateSession,
  clearSession,
} from "../../lib/storage/session";
import { enqueueCommand, clearSessionCommands } from "../../lib/storage/commandQueue";
import { clearStorage } from "../../lib/storage/db";

describe("Session storage", () => {
  beforeEach(async () => {
    await clearStorage();
  });

  it("should create a new session", async () => {
    const session = await createSession();

    expect(session).toBeDefined();
    expect(session.id).toBeDefined();
    expect(session.branchName).toContain("arxos/session-");
    expect(session.status).toBe("active");
    expect(session.commandCount).toBe(0);
    expect(session.lastSyncAt).toBeNull();
  });

  it("should retrieve active session", async () => {
    const created = await createSession();
    const retrieved = await getActiveSession();

    expect(retrieved).toBeDefined();
    expect(retrieved?.id).toBe(created.id);
  });

  it("should return null when no active session", async () => {
    const session = await getActiveSession();
    expect(session).toBeNull();
  });

  it("should update session status", async () => {
    const session = await createSession();

    await updateSession({
      status: "syncing",
      lastSyncAt: Date.now(),
    });

    const updated = await getActiveSession();
    expect(updated?.status).toBe("syncing");
    expect(updated?.lastSyncAt).toBeDefined();
  });

  it("should update command count", async () => {
    const session = await createSession();

    await updateSession({
      commandCount: 5,
    });

    const updated = await getActiveSession();
    expect(updated?.commandCount).toBe(5);
  });

  it("should delete session", async () => {
    const session = await createSession();

    await clearSession();

    const retrieved = await getActiveSession();
    expect(retrieved).toBeNull();
  });

  it("should clear session commands from queue", async () => {
    const session = await createSession();

    // Add commands to queue
    await enqueueCommand("git.commit", { message: "1" }, session.id);
    await enqueueCommand("git.commit", { message: "2" }, session.id);
    await enqueueCommand("git.commit", { message: "3" }, "other-session");

    await clearSessionCommands(session.id);

    const { getQueuedCommands } = await import("../../lib/storage/commandQueue");
    const commands = await getQueuedCommands();

    // Should only have the command from other session
    expect(commands).toHaveLength(1);
    expect(commands[0].sessionId).toBe("other-session");
  });

  it("should generate unique session IDs", async () => {
    const session1 = await createSession();
    await clearSession();

    const session2 = await createSession();

    expect(session1.id).not.toBe(session2.id);
    expect(session1.branchName).not.toBe(session2.branchName);
  });

  it("should preserve session across updates", async () => {
    const session = await createSession();
    const originalId = session.id;
    const originalBranch = session.branchName;
    const originalCreatedAt = session.createdAt;

    await updateSession({
      status: "syncing",
      commandCount: 10,
    });

    const updated = await getActiveSession();
    expect(updated?.id).toBe(originalId);
    expect(updated?.branchName).toBe(originalBranch);
    expect(updated?.createdAt).toBe(originalCreatedAt);
  });

  it("should handle status transitions", async () => {
    const session = await createSession();

    // active -> syncing
    await updateSession({ status: "syncing" });
    let updated = await getActiveSession();
    expect(updated?.status).toBe("syncing");

    // syncing -> merged
    await updateSession({ status: "merged" });
    updated = await getActiveSession();
    expect(updated?.status).toBe("merged");

    // Test conflicted state
    await updateSession({ status: "conflicted" });
    updated = await getActiveSession();
    expect(updated?.status).toBe("conflicted");
  });
});
