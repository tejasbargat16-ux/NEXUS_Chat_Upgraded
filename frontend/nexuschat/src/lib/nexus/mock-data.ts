import type { CommandSpec, ProviderId } from "./types";

/**
 * Static presentation metadata + the command catalogue.
 *
 * All conversation, provider and model DATA now comes from the live Flask
 * backend (see `api.ts` / `store.tsx`). The former MOCK_SESSIONS, MOCK_REPLIES,
 * PROVIDERS and MODELS fixtures have been removed — nothing in the app renders
 * fabricated data any more.
 *
 * What remains here is purely cosmetic: `GET /providers` returns ids, labels,
 * default models and key status, but no accent colour / blurb / key env name,
 * so those are mapped locally by provider id.
 */

export const PROVIDER_PRESENTATION: Record<
  ProviderId,
  { accent: "cyan" | "violet" | "signal"; keyEnv: string; baseUrl: string; description: string }
> = {
  groq: {
    accent: "cyan",
    keyEnv: "GROQ_API_KEY",
    baseUrl: "https://api.groq.com/openai/v1",
    description: "Lowest-latency hosted inference. Default provider for interactive turns.",
  },
  gemini: {
    accent: "violet",
    keyEnv: "GEMINI_API_KEY",
    baseUrl: "https://generativelanguage.googleapis.com/v1beta",
    description: "Long-context reasoning and multimodal prompts via Google AI Studio.",
  },
  openrouter: {
    accent: "signal",
    keyEnv: "OPENROUTER_API_KEY",
    baseUrl: "https://openrouter.ai/api/v1",
    description: "Broad model catalogue with automatic upstream failover routing.",
  },
};

export const COMMANDS: CommandSpec[] = [
  { name: "/provider", args: "<groq|gemini|openrouter>", summary: "Switch the active provider", group: "model" },
  { name: "/model", args: "<model-id>", summary: "Switch the active model", group: "model" },
  { name: "/models", summary: "List models available for the active provider", group: "model" },
  { name: "/new", args: "[title]", summary: "Start a new persisted session", group: "session" },
  { name: "/sessions", summary: "List stored SQLite sessions", group: "session" },
  { name: "/load", args: "<session-id>", summary: "Load a stored session into the workspace", group: "session" },
  { name: "/rename", args: "<title>", summary: "Rename the current session", group: "session" },
  { name: "/delete", args: "<session-id>", summary: "Delete a stored session", group: "session" },
  { name: "/clear", summary: "Clear the transcript of the current session", group: "session" },
  { name: "/architecture", summary: "Render the runtime architecture map", group: "system" },
  { name: "/exit", summary: "Detach the client and end the session", group: "system" },
];
