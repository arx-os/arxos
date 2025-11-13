/**
 * Git command handlers
 */

import { AgentClient } from "../client/AgentClient";
import type { GitStatus, GitCommitOptions, GitCommitResult } from "../client/types";

/**
 * Get current Git status
 */
export async function gitStatus(): Promise<GitStatus> {
  const client = AgentClient.getInstance();
  return client.send<GitStatus>("git.status");
}

/**
 * Get Git diff
 */
export async function gitDiff(options?: {
  staged?: boolean;
  file?: string;
}): Promise<string> {
  const client = AgentClient.getInstance();
  return client.send<string>("git.diff", options);
}

/**
 * Commit changes to Git
 */
export async function gitCommit(options: GitCommitOptions): Promise<GitCommitResult> {
  const client = AgentClient.getInstance();
  return client.send<GitCommitResult>("git.commit", options);
}

/**
 * Get Git log
 */
export async function gitLog(options?: {
  limit?: number;
  offset?: number;
}): Promise<Array<{
  hash: string;
  message: string;
  author: string;
  timestamp: string;
}>> {
  const client = AgentClient.getInstance();
  return client.send("git.log", options);
}
