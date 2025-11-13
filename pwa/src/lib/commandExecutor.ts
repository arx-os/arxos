import { initWasm } from "./wasm";
import { AgentClient } from "../modules/agent/client/AgentClient";
import { useAgentStore } from "../modules/agent/state/agentStore";

export type CommandResult = {
  success: boolean;
  output: string;
  error?: string;
  duration: number;
};

// Commands that require the desktop agent
const AGENT_COMMANDS = [
  "git.status",
  "git.diff",
  "git.commit",
  "git.log",
  "ifc.import",
  "ifc.export",
  "files.read",
  "validate",
  "edit",
];

export async function executeCommand(commandString: string): Promise<CommandResult> {
  const startTime = Date.now();

  try {
    const trimmed = commandString.trim();
    if (!trimmed) {
      throw new Error("Empty command");
    }

    const [command, ...args] = trimmed.split(/\s+/);

    // Check if this is an agent command
    const isAgentCommand = AGENT_COMMANDS.some((cmd) => command.startsWith(cmd));

    let output: string;

    if (isAgentCommand) {
      output = await executeAgentCommand(command, args);
    } else {
      output = await executeWasmCommand(command, args);
    }

    return {
      success: true,
      output,
      duration: Date.now() - startTime,
    };
  } catch (error) {
    return {
      success: false,
      output: "",
      error: error instanceof Error ? error.message : String(error),
      duration: Date.now() - startTime,
    };
  }
}

async function executeAgentCommand(command: string, args: string[]): Promise<string> {
  // Check if agent is connected
  const agentStore = useAgentStore.getState();

  if (!agentStore.isInitialized || agentStore.connectionState.status !== "connected") {
    return `⚠️  Agent Required

The command "${command}" requires a connection to the ArxOS desktop agent.

Please ensure:
1. The desktop agent is running
2. You have authenticated with a valid DID:key token

Current status: ${agentStore.connectionState.status}`;
  }

  try {
    const client = AgentClient.getInstance();

    // Parse command and build payload
    const payload = buildAgentPayload(command, args);

    // Send to agent
    const response = await client.send(command as any, payload);

    // Format response for display
    return formatAgentResponse(command, response);
  } catch (error) {
    throw new Error(
      `Agent command failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

function buildAgentPayload(command: string, args: string[]): Record<string, unknown> {
  // Parse command-specific arguments
  switch (command) {
    case "git.status":
      return {};

    case "git.diff":
      return {
        staged: args.includes("--staged"),
        file: args.find((arg) => !arg.startsWith("--")),
      };

    case "git.commit":
      // Extract -m flag for message
      const messageIndex = args.indexOf("-m");
      const message = messageIndex >= 0 ? args[messageIndex + 1] : "";
      return {
        message,
        files: args.filter((arg) => !arg.startsWith("-") && arg !== message),
      };

    case "git.log":
      return {
        limit: args.includes("--limit") ? parseInt(args[args.indexOf("--limit") + 1]) : 10,
      };

    default:
      // Generic payload from args
      return args.reduce((acc, arg, i) => {
        if (arg.startsWith("--")) {
          const key = arg.slice(2);
          const value = args[i + 1];
          acc[key] = value;
        }
        return acc;
      }, {} as Record<string, unknown>);
  }
}

function formatAgentResponse(command: string, response: unknown): string {
  if (typeof response === "string") {
    return response;
  }

  if (typeof response === "object" && response !== null) {
    // Pretty-print JSON response
    return JSON.stringify(response, null, 2);
  }

  return String(response);
}

async function executeWasmCommand(command: string, args: string[]): Promise<string> {
  const wasm = await initWasm();
  const version = wasm.arxos_version();

  switch (command) {
    case "version":
      return `ArxOS version ${version}`;

    case "help":
      return generateHelpText();

    case "clear":
      return "";

    default:
      return `Mock output for command: ${command} ${args.join(" ")}\n\nThis is a stub response. Full command execution will be available when the desktop agent is connected (M04).`;
  }
}

function generateHelpText(): string {
  return `ArxOS Command Shell - Available Commands:

  version              Show ArxOS version
  help                 Show this help message
  clear                Clear console output

Additional commands will be available when connected to the desktop agent (M04).
Use Cmd/Ctrl+K to open the command palette for a full list of available commands.`;
}
