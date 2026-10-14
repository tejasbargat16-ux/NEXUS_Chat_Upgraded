/**
 * NexusChat domain types.
 *
 * This is the single contract between the UI and the data layer. The current
 * implementation is backed by `mock-data.ts` + in-memory reducer state, but every
 * shape here mirrors what the Python backend already exposes (providers, models,
 * SQLite sessions, command handler results), so swapping `NexusProvider`'s
 * mock calls for real fetch/websocket calls requires no component changes.
 */

export type ProviderId = "groq" | "gemini" | "openrouter";

export type ProviderStatus = "online" | "degraded" | "offline";

export interface ModelInfo {
  id: string;
  label: string;
  provider: ProviderId;
  /** Unknown for live backend models; hidden in the UI when absent. */
  contextWindow?: number;
  /** Relative speed hint shown in the model selector. */
  throughput?: string;
  tags: string[];
  description: string;
}

export interface ProviderInfo {
  id: ProviderId;
  name: string;
  status: ProviderStatus;
  /** Where the API key comes from on the backend. */
  keyEnv: string;
  keyConfigured: boolean;
  baseUrl: string;
  /** Not reported by the Flask backend; hidden in the UI when absent. */
  latencyMs?: number;
  /** Default model reported by GET /providers. */
  defaultModel?: string;
  accent: "cyan" | "violet" | "signal";
  description: string;
}

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: number;
  provider?: ProviderId;
  model?: string;
  /** Present once a response has completed. */
  meta?: {
    latencyMs: number;
    tokensIn: number;
    tokensOut: number;
  };
  /** True while the assistant text is being revealed token-by-token. */
  streaming?: boolean;
  /**
   * Set when agent mode proposed a shell command that needs explicit approval
   * (POST /chat -> { type: "agent_command" }). Rendered as an approve/decline
   * bubble; resolved through POST /agent/run or POST /agent/decline.
   */
  pendingCommand?: { command: string; resolved?: "approved" | "declined" };
}

export interface Session {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  provider: ProviderId;
  model: string;
  messages: ChatMessage[];
  /** Mirrors the SQLite row id on the Python side. */
  rowId: number;
  /** Raw backend conversation id, used for every /conversations call. */
  remoteId: string | number;
  /** False until GET /conversations/:id/messages has been fetched. */
  loaded?: boolean;
}

/** Runtime state of the Nexus Core visual. */
export type CoreState = "idle" | "thinking" | "responding";

export interface CommandSpec {
  name: string;
  args?: string;
  summary: string;
  group: "session" | "model" | "system";
}
