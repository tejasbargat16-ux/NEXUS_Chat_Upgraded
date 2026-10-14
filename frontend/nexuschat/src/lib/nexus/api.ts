/**
 * Typed fetch client for the NexusChat Flask backend (`api.py`).
 *
 * The backend runs on the user's own machine / Termux device and is exposed
 * through a tunnel (cloudflared / ngrok) whose URL changes over time, so the
 * base URL and API key are NOT baked in at build time — they are read from
 * localStorage at call time and edited from the Settings page.
 *
 *   localStorage["nexus_api_url"]  e.g. https://abc-123.trycloudflare.com
 *   localStorage["nexus_api_key"]  sent as the `X-API-Key` header
 *
 * Endpoint contract (adjust here if the Flask side differs):
 *
 *   GET    /providers                  -> ApiProvider[]
 *   GET    /conversations              -> ApiConversation[]
 *   POST   /conversations {title?}     -> ApiConversation
 *   GET    /conversations/:id/messages -> ApiMessage[]
 *   PATCH  /conversations/:id {title}  -> { ok: true }
 *   DELETE /conversations/:id          -> { ok: true }
 *   POST   /chat {conversation_id, provider, model, message}
 *            -> { type: "message", content }
 *            |  { type: "agent_command", command, conversation_id }
 *   POST   /agent/run {conversation_id, command}
 *            -> { stdout, stderr, exit_code, follow_up }
 *   POST   /agent/decline {conversation_id} -> { follow_up }
 *   GET    /profile                    -> { text }
 *   POST   /profile {fact}             -> { ok: true }
 *   DELETE /profile                    -> { ok: true }
 */

export const API_URL_KEY = "nexus_api_url";
export const API_KEY_KEY = "nexus_api_key";

export interface ApiConfig {
  url: string;
  key: string;
}

/** Thrown when the tunnel URL / API key have not been configured yet. */
export class NotConfiguredError extends Error {
  constructor() {
    super("Not connected — add your API URL and key in Settings.");
    this.name = "NotConfiguredError";
  }
}

/** Thrown for transport / HTTP failures against a configured backend. */
export class ApiError extends Error {
  status?: number | undefined;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    if (status !== undefined) this.status = status;
  }
}

export const DEFAULT_API_URL =
  (import.meta.env.VITE_NEXUS_API_URL as string | undefined) || "http://127.0.0.1:8000";
export const DEFAULT_API_KEY =
  (import.meta.env.VITE_NEXUS_API_KEY as string | undefined) ||
  "XDy3lmPYUWvUGZtORMfKdDwCVBcqpgua0MtQEtOEOso";

export function readConfig(): ApiConfig {
  if (typeof window === "undefined") return { url: DEFAULT_API_URL, key: DEFAULT_API_KEY };
  const storedUrl = window.localStorage.getItem(API_URL_KEY);
  const storedKey = window.localStorage.getItem(API_KEY_KEY);
  return {
    url: (storedUrl !== null && storedUrl !== "" ? storedUrl : DEFAULT_API_URL).trim().replace(/\/+$/, ""),
    key: (storedKey !== null && storedKey !== "" ? storedKey : DEFAULT_API_KEY).trim(),
  };
}

export function writeConfig({ url, key }: ApiConfig) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(API_URL_KEY, url.trim().replace(/\/+$/, ""));
  window.localStorage.setItem(API_KEY_KEY, key.trim());
  window.dispatchEvent(new Event("nexus:config"));
}

export function clearConfig() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(API_URL_KEY);
  window.localStorage.removeItem(API_KEY_KEY);
  window.dispatchEvent(new Event("nexus:config"));
}

export function isConfigured() {
  const { url, key } = readConfig();
  return Boolean(url && key);
}

async function request<T>(
  path: string,
  init: { method?: string; body?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  const { url, key } = readConfig();
  if (!url || !key) throw new NotConfiguredError();

  const method = init.method ?? "GET";
  const headers: Record<string, string> = { "X-API-Key": key };
  const fetchInit: RequestInit = {
    method,
    headers,
    signal: init.signal ?? null,
  };
  if (init.body !== undefined) {
    headers["Content-Type"] = "application/json";
    fetchInit.body = JSON.stringify(init.body);
  }

  let res: Response;
  try {
    res = await fetch(`${url}${path}`, fetchInit);
  } catch (e) {
    throw new ApiError(
      `Could not reach ${url}${path}. The tunnel may have changed or the backend is offline. (${
        e instanceof Error ? e.message : "network error"
      })`,
    );
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(
      res.status === 401 || res.status === 403
        ? `Rejected by the backend (${res.status}). Check the API key in Settings.`
        : `${method} ${path} failed with ${res.status}. ${text.slice(0, 200)}`,
      res.status,
    );
  }

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(`${path} returned a non-JSON response.`);
  }
}

/* ------------------------------------------------------------------ shapes */

export type ApiProviderId = "groq" | "gemini" | "openrouter";

export interface ApiProvider {
  id: ApiProviderId;
  label: string;
  default_model: string;
  suggested_models: string[];
  key_configured: boolean;
}

export interface ApiConversation {
  id: string | number;
  title: string;
  created_at: string | number;
}

export interface ApiMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export type ApiChatResponse =
  | { type: "message"; content: string }
  | { type: "agent_command"; command: string; conversation_id: string | number };

export interface ApiAgentRunResponse {
  stdout: string;
  stderr: string;
  exit_code: number;
  follow_up: string;
}

/* --------------------------------------------------------------- endpoints */

export const api = {
  providers: () => request<ApiProvider[]>("/providers"),

  listConversations: () => request<ApiConversation[]>("/conversations"),

  createConversation: (title?: string) =>
    request<ApiConversation>("/conversations", { method: "POST", body: { title } }),

  messages: (id: string | number) =>
    request<ApiMessage[]>(`/conversations/${encodeURIComponent(String(id))}/messages`),

  renameConversation: (id: string | number, title: string) =>
    request<{ ok: true }>(`/conversations/${encodeURIComponent(String(id))}`, {
      method: "PATCH",
      body: { title },
    }),

  deleteConversation: (id: string | number) =>
    request<{ ok: true }>(`/conversations/${encodeURIComponent(String(id))}`, { method: "DELETE" }),

  chat: (input: {
    conversation_id: string | number;
    provider: string;
    model: string;
    message: string;
  }) => request<ApiChatResponse>("/chat", { method: "POST", body: input }),

  agentRun: (conversation_id: string | number, command: string) =>
    request<ApiAgentRunResponse>("/agent/run", {
      method: "POST",
      body: { conversation_id, command },
    }),

  agentDecline: (conversation_id: string | number) =>
    request<{ follow_up: string }>("/agent/decline", {
      method: "POST",
      body: { conversation_id },
    }),

  getProfile: () => request<{ text: string }>("/profile"),

  addProfileFact: (fact: string) =>
    request<{ ok: true }>("/profile", { method: "POST", body: { fact } }),

  clearProfile: () => request<{ ok: true }>("/profile", { method: "DELETE" }),
};

/** Human-readable message for any thrown error from this module. */
export function describeError(e: unknown): string {
  if (e instanceof NotConfiguredError) return e.message;
  if (e instanceof ApiError) return e.message;
  return e instanceof Error ? e.message : String(e);
}
