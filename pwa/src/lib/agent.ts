import { nanoid } from "nanoid";

const AGENT_ENDPOINT = "ws://127.0.0.1:8787/ws";

export type AgentAction =
  | "git.status"
  | "git.diff"
  | "git.commit"
  | "files.read"
  | "ifc.import"
  | "ifc.export"
  | "collab.sync"
  | "collab.config.get"
  | "collab.config.set"
  | "ping"
  | "version"
  | "capabilities";

export type CollabTarget = { type: "issue" | "pull_request"; number: number };
export type CollabConfig = { owner: string; repo: string; target: CollabTarget };

export type CollabSyncSuccess = {
  id: string;
  remoteId: number;
  remoteUrl?: string;
  syncedAt: string;
};

export type CollabSyncError = { id: string; error: string };

export type CollabSyncResponse = {
  successes: CollabSyncSuccess[];
  errors: CollabSyncError[];
};

export type AgentRequestPayload = Record<string, unknown> | undefined;

export interface AgentResponse<T = unknown> {
  status: "ok" | "error";
  payload: T;
}

export async function invokeAgent<T = unknown>(
  token: string,
  action: AgentAction,
  payload?: AgentRequestPayload
): Promise<AgentResponse<T>> {
  if (!token.startsWith("did:key:")) {
    throw new Error("Agent token must be a DID:key");
  }

  return new Promise((resolve, reject) => {
    const requestId = nanoid(12);
    let resolved = false;

    const socket = new WebSocket(`${AGENT_ENDPOINT}?token=${encodeURIComponent(token)}`);

    socket.addEventListener("open", () => {
      socket.send(
        JSON.stringify({
          id: requestId,
          action,
          payload: payload ?? {}
        })
      );
    });

    socket.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data?.payload?.message === "connected") {
          return;
        }

        if (data?.id && data.id !== requestId) {
          return;
        }

        resolved = true;
        resolve({ status: data.status, payload: data.payload });
        socket.close();
      } catch (error) {
        reject(error instanceof Error ? error : new Error(String(error)));
        socket.close();
      }
    });

    socket.addEventListener("error", () => {
      if (!resolved) {
        reject(new Error("Unable to reach ArxOS agent"));
      }
    });

    socket.addEventListener("close", () => {
      if (!resolved) {
        reject(new Error("Agent connection closed"));
      }
    });
  });
}
