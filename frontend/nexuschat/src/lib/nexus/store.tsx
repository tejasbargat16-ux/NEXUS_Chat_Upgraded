import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  api,
  describeError,
  isConfigured,
  type ApiConversation,
  type ApiProvider,
} from "./api";
import { COMMANDS, PROVIDER_PRESENTATION } from "./mock-data";
import type {
  ChatMessage,
  CoreState,
  ModelInfo,
  ProviderId,
  ProviderInfo,
  Session,
} from "./types";

/**
 * Single source of truth for the NexusChat frontend — now backed by the real
 * Flask backend (`api.ts`) instead of fixtures.
 *
 *   - providers/models  <- GET /providers
 *   - sessions          <- GET /conversations (messages lazy-loaded per session)
 *   - chat turns        -> POST /chat (+ /agent/run, /agent/decline)
 *   - session CRUD      -> POST/PATCH/DELETE /conversations
 *
 * Flask does not stream, so the returned text is revealed with the same
 * chunk-reveal animation the prototype used, purely for visual continuity.
 *
 * Every backend call funnels through `fail()` on error, which appends a system
 * note pointing the user at Settings rather than crashing the UI.
 */

const uid = () => Math.random().toString(36).slice(2, 10);

/** Local-only session used to surface connection problems in the transcript. */
const OFFLINE_ID = "local_offline";

const NOT_CONNECTED_NOTE =
  "**Not connected.** Open **Settings** and paste your current tunnel URL and API key, then press *Test & Save*. The tunnel URL changes each time cloudflared/ngrok restarts.";

function toTimestamp(value: string | number | undefined): number {
  if (typeof value === "number") return value < 1e12 ? value * 1000 : value;
  if (typeof value === "string") {
    const parsed = Date.parse(value.includes("Z") || value.includes("+") ? value : `${value}Z`);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return Date.now();
}

function toSession(conv: ApiConversation, provider: ProviderId, model: string): Session {
  const id = String(conv.id);
  const created = toTimestamp(conv.created_at);
  const numeric = Number(conv.id);
  return {
    id,
    remoteId: conv.id,
    rowId: Number.isFinite(numeric) ? numeric : 0,
    title: conv.title?.trim() || "Untitled session",
    createdAt: created,
    updatedAt: created,
    provider,
    model,
    messages: [],
    loaded: false,
  };
}

function toProviderInfo(p: ApiProvider): ProviderInfo {
  const meta = PROVIDER_PRESENTATION[p.id] ?? PROVIDER_PRESENTATION.groq;
  return {
    id: p.id,
    name: p.label || p.id,
    status: p.key_configured ? "online" : "offline",
    keyEnv: meta.keyEnv,
    keyConfigured: p.key_configured,
    baseUrl: meta.baseUrl,
    accent: meta.accent,
    description: meta.description,
    defaultModel: p.default_model,
  };
}

function toModels(list: ApiProvider[]): ModelInfo[] {
  const out: ModelInfo[] = [];
  for (const p of list) {
    const ids = Array.from(new Set([p.default_model, ...(p.suggested_models ?? [])].filter(Boolean)));
    for (const id of ids) {
      out.push({
        id,
        label: id,
        provider: p.id,
        tags: id === p.default_model ? ["default"] : [],
        ...(id === p.default_model ? { throughput: "default" } : {}),
        description: `${p.label || p.id} model reported by the backend.`,
      });
    }
  }
  return out;
}

interface NexusContextValue {
  sessions: Session[];
  activeSession: Session | undefined;
  activeSessionId: string;
  providers: ProviderInfo[];
  models: ModelInfo[];
  provider: ProviderId;
  model: string;
  coreState: CoreState;
  streaming: boolean;
  sidebarOpen: boolean;
  systemOnline: boolean;
  connectionError: string | null;
  uptimeSeconds: number;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setProvider: (id: ProviderId) => void;
  setModel: (id: string) => void;
  selectSession: (id: string) => void;
  newSession: (title?: string) => void;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => void;
  clearSession: (id: string) => void;
  submit: (input: string) => void;
  stop: () => void;
  reconnect: () => void;
  approveCommand: (messageId: string) => void;
  declineCommand: (messageId: string) => void;
}

const NexusContext = createContext<NexusContextValue | null>(null);

export function NexusProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [provider, setProviderState] = useState<ProviderId>("groq");
  const [model, setModelState] = useState<string>("");
  const [coreState, setCoreState] = useState<CoreState>("idle");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [systemOnline, setSystemOnline] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [uptimeSeconds, setUptimeSeconds] = useState(0);
  const [pendingApproval, setPendingApproval] = useState(false);

  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  useEffect(() => {
    const t = setInterval(() => setUptimeSeconds((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => clearTimers, [clearTimers]);

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  const patchSession = useCallback((id: string, patch: (s: Session) => Session) => {
    setSessions((prev) => prev.map((s) => (s.id === id ? patch(s) : s)));
  }, []);

  const appendMessage = useCallback(
    (id: string, message: ChatMessage) => {
      patchSession(id, (s) => ({
        ...s,
        updatedAt: Date.now(),
        messages: [...s.messages, message],
      }));
    },
    [patchSession],
  );

  /** Appends a system note, creating the local offline session if needed. */
  const systemNote = useCallback(
    (content: string) => {
      const message: ChatMessage = {
        id: uid(),
        role: "system",
        content,
        createdAt: Date.now(),
      };
      setSessions((prev) => {
        const targetId = prev.some((s) => s.id === activeSessionId) ? activeSessionId : OFFLINE_ID;
        if (prev.some((s) => s.id === targetId)) {
          return prev.map((s) =>
            s.id === targetId
              ? { ...s, updatedAt: Date.now(), messages: [...s.messages, message] }
              : s,
          );
        }
        setActiveSessionId(OFFLINE_ID);
        const offline: Session = {
          id: OFFLINE_ID,
          remoteId: "",
          rowId: 0,
          title: "Not connected",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          provider: "groq",
          model: "",
          messages: [message],
          loaded: true,
        };
        return [offline, ...prev];
      });
    },
    [activeSessionId],
  );

  const fail = useCallback(
    (e: unknown) => {
      const detail = describeError(e);
      setCoreState("idle");
      systemNote(
        `${detail}\n\nCheck the API URL and key in **Settings** — the tunnel URL changes whenever cloudflared/ngrok restarts.`,
      );
    },
    [systemNote],
  );

  /* ------------------------------------------------------------- bootstrap */

  const bootstrap = useCallback(async () => {
    if (!isConfigured()) {
      setSystemOnline(false);
      setConnectionError("Not configured");
      systemNote(NOT_CONNECTED_NOTE);
      return;
    }
    try {
      const [providerList, conversations] = await Promise.all([
        api.providers(),
        api.listConversations(),
      ]);

      const infos = providerList.map(toProviderInfo);
      setProviders(infos);
      setModels(toModels(providerList));

      const preferred = providerList.find((p) => p.key_configured) ?? providerList[0];
      const nextProvider = (preferred?.id ?? "groq") as ProviderId;
      const nextModel = preferred?.default_model ?? "";
      setProviderState(nextProvider);
      setModelState(nextModel);

      const mapped = conversations.map((c) => toSession(c, nextProvider, nextModel));
      setSessions(mapped);
      setActiveSessionId(mapped[0]?.id ?? "");
      setSystemOnline(true);
      setConnectionError(null);
    } catch (e) {
      setSystemOnline(false);
      setConnectionError(describeError(e));
      setSessions([]);
      setActiveSessionId("");
      systemNote(`${describeError(e)}\n\n${NOT_CONNECTED_NOTE}`);
    }
  }, [systemNote]);

  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    void bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const reconnect = useCallback(() => {
    setSessions((prev) => prev.filter((s) => s.id !== OFFLINE_ID));
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const onConfig = () => reconnect();
    window.addEventListener("nexus:config", onConfig);
    return () => window.removeEventListener("nexus:config", onConfig);
  }, [reconnect]);

  /* ------------------------------------------------------- message loading */

  const loadMessages = useCallback(
    async (session: Session) => {
      if (session.loaded || session.id === OFFLINE_ID || !session.remoteId) return;
      try {
        const rows = await api.messages(session.remoteId);
        patchSession(session.id, (s) => ({
          ...s,
          loaded: true,
          messages: rows.map((r, i) => ({
            id: `${s.id}_${i}`,
            role: r.role,
            content: r.content,
            createdAt: s.createdAt + i,
            ...(r.role === "assistant" ? { provider: s.provider, model: s.model } : {}),
          })),
        }));
      } catch (e) {
        patchSession(session.id, (s) => ({ ...s, loaded: true }));
        fail(e);
      }
    },
    [patchSession, fail],
  );

  useEffect(() => {
    if (activeSession && !activeSession.loaded) void loadMessages(activeSession);
  }, [activeSession, loadMessages]);

  /* ---------------------------------------------------------- session CRUD */

  const newSession = useCallback(
    (title?: string) => {
      void (async () => {
        try {
          const conv = await api.createConversation(title?.trim() || undefined);
          const session = { ...toSession(conv, provider, model), loaded: true };
          setSessions((prev) => [session, ...prev.filter((s) => s.id !== OFFLINE_ID)]);
          setActiveSessionId(session.id);
          setSystemOnline(true);
        } catch (e) {
          fail(e);
        }
      })();
    },
    [provider, model, fail],
  );

  const selectSession = useCallback(
    (id: string) => {
      const target = sessions.find((s) => s.id === id);
      if (!target) return;
      clearTimers();
      setCoreState("idle");
      setPendingApproval(false);
      setActiveSessionId(id);
      if (target.provider) setProviderState(target.provider);
      if (target.model) setModelState(target.model);
      void loadMessages(target);
    },
    [sessions, clearTimers, loadMessages],
  );

  const renameSession = useCallback(
    (id: string, title: string) => {
      const target = sessions.find((s) => s.id === id);
      if (!target) return;
      patchSession(id, (s) => ({ ...s, title }));
      if (!target.remoteId) return;
      void api.renameConversation(target.remoteId, title).catch(fail);
    },
    [sessions, patchSession, fail],
  );

  const deleteSession = useCallback(
    (id: string) => {
      const target = sessions.find((s) => s.id === id);
      if (!target) return;
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== id);
        if (id === activeSessionId) setActiveSessionId(next[0]?.id ?? "");
        return next;
      });
      if (!target.remoteId) return;
      void api.deleteConversation(target.remoteId).catch(fail);
    },
    [sessions, activeSessionId, fail],
  );

  /** Local transcript clear — the backend has no matching endpoint. */
  const clearSession = useCallback(
    (id: string) => patchSession(id, (s) => ({ ...s, messages: [] })),
    [patchSession],
  );

  /* -------------------------------------------------- provider / model state */

  const setProvider = useCallback(
    (id: ProviderId) => {
      setProviderState(id);
      const fallback =
        providers.find((p) => p.id === id)?.defaultModel ??
        models.find((m) => m.provider === id)?.id;
      if (fallback) setModelState(fallback);
      patchSession(activeSessionId, (s) => ({
        ...s,
        provider: id,
        model: fallback ?? s.model,
      }));
    },
    [activeSessionId, patchSession, providers, models],
  );

  const setModel = useCallback(
    (id: string) => {
      const found = models.find((m) => m.id === id);
      setModelState(id);
      if (found) setProviderState(found.provider);
      patchSession(activeSessionId, (s) => ({
        ...s,
        model: id,
        provider: found?.provider ?? s.provider,
      }));
    },
    [activeSessionId, patchSession, models],
  );

  /* ------------------------------------------------------------- streaming */

  /**
   * Reveals already-received text in frame-batched chunks so the UI keeps its
   * streaming feel even though Flask returns the full response at once.
   */
  const revealAssistant = useCallback(
    (sessionId: string, full: string, startedAt: number, promptLength: number) => {
      const messageId = uid();
      setCoreState("responding");
      appendMessage(sessionId, {
        id: messageId,
        role: "assistant",
        content: "",
        createdAt: Date.now(),
        provider,
        model,
        streaming: true,
      });

      const chunks = full.match(/\s*\S+/g) ?? [full];
      chunks.forEach((chunk, i) => {
        timers.current.push(
          setTimeout(() => {
            patchSession(sessionId, (s) => ({
              ...s,
              messages: s.messages.map((m) =>
                m.id === messageId ? { ...m, content: m.content + chunk } : m,
              ),
            }));
          }, 18 * (i + 1)),
        );
      });

      timers.current.push(
        setTimeout(
          () => {
            patchSession(sessionId, (s) => ({
              ...s,
              messages: s.messages.map((m) =>
                m.id === messageId
                  ? {
                      ...m,
                      content: full,
                      streaming: false,
                      meta: {
                        latencyMs: Date.now() - startedAt,
                        tokensIn: Math.round(promptLength / 3.6),
                        tokensOut: Math.round(full.length / 3.9),
                      },
                    }
                  : m,
              ),
            }));
            setCoreState("idle");
          },
          18 * (chunks.length + 2),
        ),
      );
    },
    [appendMessage, patchSession, provider, model],
  );

  /* --------------------------------------------------------- agent commands */

  const resolveCommand = useCallback(
    (messageId: string, decision: "approved" | "declined") => {
      const session = sessions.find((s) => s.messages.some((m) => m.id === messageId));
      const message = session?.messages.find((m) => m.id === messageId);
      if (!session || !message?.pendingCommand || message.pendingCommand.resolved) return;

      const command = message.pendingCommand.command;
      patchSession(session.id, (s) => ({
        ...s,
        messages: s.messages.map((m) =>
          m.id === messageId ? { ...m, pendingCommand: { command, resolved: decision } } : m,
        ),
      }));
      setPendingApproval(false);
      setCoreState("thinking");
      const startedAt = Date.now();

      void (async () => {
        try {
          if (decision === "approved") {
            const res = await api.agentRun(session.remoteId, command);
            const output = [
              `\`\`\`console\n$ ${command}\n${(res.stdout || "").trim()}${
                res.stderr?.trim() ? `\n${res.stderr.trim()}` : ""
              }\n\`\`\``,
              `exit code \`${res.exit_code}\``,
            ].join("\n\n");
            appendMessage(session.id, {
              id: uid(),
              role: "system",
              content: output,
              createdAt: Date.now(),
            });
            revealAssistant(session.id, res.follow_up ?? "", startedAt, command.length);
          } else {
            const res = await api.agentDecline(session.remoteId);
            revealAssistant(session.id, res.follow_up ?? "", startedAt, command.length);
          }
        } catch (e) {
          fail(e);
        }
      })();
    },
    [sessions, patchSession, appendMessage, revealAssistant, fail],
  );

  const approveCommand = useCallback(
    (messageId: string) => resolveCommand(messageId, "approved"),
    [resolveCommand],
  );
  const declineCommand = useCallback(
    (messageId: string) => resolveCommand(messageId, "declined"),
    [resolveCommand],
  );

  /* -------------------------------------------------------------- commands */

  const runCommand = useCallback(
    (raw: string): void => {
      const [name, ...rest] = raw.trim().split(/\s+/);
      const arg = rest.join(" ").trim();
      const known = COMMANDS.some((c) => c.name === name);

      if (!known) {
        systemNote(
          `Unknown command \`${name}\`. Type \`/\` in the composer to see the full command list.`,
        );
        return;
      }

      switch (name) {
        case "/provider": {
          const target = providers.find((p) => p.id === arg.toLowerCase());
          if (!target) {
            systemNote("Usage: `/provider <groq|gemini|openrouter>`");
            break;
          }
          setProvider(target.id);
          systemNote(
            `Provider switched to \`${target.id}\`${
              target.keyConfigured ? "" : " — the backend reports no API key configured for it"
            }.`,
          );
          break;
        }
        case "/model": {
          const target = models.find((m) => m.id === arg);
          if (!arg) {
            systemNote("Usage: `/model <model-id>` — run `/models` for the catalogue.");
            break;
          }
          setModel(arg);
          systemNote(
            target
              ? `Model switched to \`${target.id}\` on \`${target.provider}\`.`
              : `Model set to \`${arg}\` (not in the backend's suggested list for \`${provider}\`).`,
          );
          break;
        }
        case "/models": {
          const list = models
            .filter((m) => m.provider === provider)
            .map((m) => `- \`${m.id}\`${m.tags.includes("default") ? " — default" : ""}`)
            .join("\n");
          systemNote(
            list
              ? `Models reported by the backend for \`${provider}\`:\n\n${list}`
              : "No models reported yet. Check your connection in **Settings**.",
          );
          break;
        }
        case "/new":
          newSession(arg);
          break;
        case "/sessions": {
          const list = sessions
            .filter((s) => s.id !== OFFLINE_ID)
            .map((s) => `- \`${s.id}\` — ${s.title}`)
            .join("\n");
          systemNote(
            list ? `Conversations stored by the backend:\n\n${list}` : "No conversations yet.",
          );
          break;
        }
        case "/load": {
          const target = sessions.find((s) => s.id === arg);
          if (!target) {
            systemNote(`No session \`${arg || "—"}\`. Run \`/sessions\` to list ids.`);
            break;
          }
          selectSession(target.id);
          break;
        }
        case "/rename": {
          if (!arg) {
            systemNote("Usage: `/rename <new title>`");
            break;
          }
          renameSession(activeSessionId, arg);
          systemNote(`Session renamed to **${arg}**.`);
          break;
        }
        case "/delete": {
          const target = sessions.find((s) => s.id === arg);
          if (!target) {
            systemNote(`No session \`${arg || "—"}\` to delete.`);
            break;
          }
          deleteSession(target.id);
          break;
        }
        case "/clear":
          clearSession(activeSessionId);
          break;
        case "/architecture":
          systemNote(
            "Runtime map rendered on the **Architecture** page: User → NexusChat Frontend → Command/Input Handler → Provider Layer → Groq · Gemini · OpenRouter → AI Response → UI, with SQLite persisting every session.",
          );
          break;
        case "/exit":
          systemNote("Client detached. Session state remains persisted in `nexus.db`.");
          break;
      }
    },
    [
      activeSessionId,
      clearSession,
      deleteSession,
      models,
      newSession,
      provider,
      providers,
      renameSession,
      selectSession,
      sessions,
      setModel,
      setProvider,
      systemNote,
    ],
  );

  /* ---------------------------------------------------------------- submit */

  const sendChat = useCallback(
    async (sessionId: string, remoteId: string | number, text: string) => {
      const startedAt = Date.now();
      setCoreState("thinking");
      try {
        const res = await api.chat({
          conversation_id: remoteId,
          provider,
          model,
          message: text,
        });

        if (res.type === "agent_command") {
          setCoreState("idle");
          setPendingApproval(true);
          appendMessage(sessionId, {
            id: uid(),
            role: "assistant",
            content: "",
            createdAt: Date.now(),
            provider,
            model,
            pendingCommand: { command: res.command },
          });
          return;
        }

        revealAssistant(sessionId, res.content ?? "", startedAt, text.length);
      } catch (e) {
        fail(e);
      }
    },
    [appendMessage, revealAssistant, provider, model, fail],
  );

  const submit = useCallback(
    (input: string) => {
      const text = input.trim();
      if (!text || coreState !== "idle" || pendingApproval) return;

      if (text.startsWith("/")) {
        if (activeSession) {
          appendMessage(activeSessionId, {
            id: uid(),
            role: "user",
            content: text,
            createdAt: Date.now(),
          });
        }
        runCommand(text);
        return;
      }

      void (async () => {
        let sessionId = activeSessionId;
        let remoteId = activeSession?.remoteId;

        // No usable conversation yet (fresh install, or the offline placeholder)
        // -> create one on the backend first.
        if (!activeSession || !remoteId) {
          try {
            const conv = await api.createConversation(text.slice(0, 48));
            const session = { ...toSession(conv, provider, model), loaded: true };
            setSessions((prev) => [session, ...prev.filter((s) => s.id !== OFFLINE_ID)]);
            setActiveSessionId(session.id);
            setSystemOnline(true);
            sessionId = session.id;
            remoteId = session.remoteId;
          } catch (e) {
            fail(e);
            return;
          }
        }

        appendMessage(sessionId, {
          id: uid(),
          role: "user",
          content: text,
          createdAt: Date.now(),
        });
        await sendChat(sessionId, remoteId!, text);
      })();
    },
    [
      activeSession,
      activeSessionId,
      appendMessage,
      coreState,
      fail,
      model,
      pendingApproval,
      provider,
      runCommand,
      sendChat,
    ],
  );

  const stop = useCallback(() => {
    clearTimers();
    setCoreState("idle");
    patchSession(activeSessionId, (s) => ({
      ...s,
      messages: s.messages.map((m) => (m.streaming ? { ...m, streaming: false } : m)),
    }));
  }, [activeSessionId, clearTimers, patchSession]);

  const value = useMemo<NexusContextValue>(
    () => ({
      sessions,
      activeSession,
      activeSessionId,
      providers,
      models,
      provider,
      model,
      coreState,
      streaming: coreState !== "idle" || pendingApproval,
      sidebarOpen,
      systemOnline,
      connectionError,
      uptimeSeconds,
      setSidebarOpen,
      toggleSidebar: () => setSidebarOpen((o) => !o),
      setProvider,
      setModel,
      selectSession,
      newSession,
      renameSession,
      deleteSession,
      clearSession,
      submit,
      stop,
      reconnect,
      approveCommand,
      declineCommand,
    }),
    [
      sessions,
      activeSession,
      activeSessionId,
      providers,
      models,
      provider,
      model,
      coreState,
      pendingApproval,
      sidebarOpen,
      systemOnline,
      connectionError,
      uptimeSeconds,
      setProvider,
      setModel,
      selectSession,
      newSession,
      renameSession,
      deleteSession,
      clearSession,
      submit,
      stop,
      reconnect,
      approveCommand,
      declineCommand,
    ],
  );

  return <NexusContext.Provider value={value}>{children}</NexusContext.Provider>;
}

export function useNexus() {
  const ctx = useContext(NexusContext);
  if (!ctx) throw new Error("useNexus must be used inside <NexusProvider>");
  return ctx;
}
