import { Check, Terminal, User, X } from "lucide-react";
import { useEffect, useRef } from "react";

import { Markdown } from "@/components/nexus/markdown";
import { NexusCore } from "@/components/nexus/nexus-core";
import { formatClock } from "@/lib/nexus/format";
import { useNexus } from "@/lib/nexus/store";
import type { ChatMessage } from "@/lib/nexus/types";
import { cn } from "@/lib/utils";

function MessageRow({ message }: { message: ChatMessage }) {
  const { approveCommand, declineCommand } = useNexus();

  if (message.role === "system") {
    return (
      <div className="animate-nx-rise mx-auto w-full max-w-3xl">
        <div className="rounded-xl border border-border border-dashed bg-surface/40 px-4 py-3">
          <div className="nx-label mb-1.5 flex items-center gap-2 text-signal">
            <Terminal className="size-3" />
            system
            <span className="ml-auto text-muted-foreground">{formatClock(message.createdAt)}</span>
          </div>
          <Markdown content={message.content} className="text-[13px]" />
        </div>
      </div>
    );
  }

  if (message.role === "user") {
    return (
      <div className="animate-nx-rise mx-auto flex w-full max-w-3xl justify-end">
        <div className="flex max-w-[85%] items-start gap-3">
          <div className="min-w-0 rounded-2xl rounded-tr-md border border-cyan/25 bg-cyan/10 px-4 py-3">
            <p className="whitespace-pre-wrap text-[14.5px] leading-relaxed text-foreground">
              {message.content}
            </p>
            <p className="mt-1.5 text-right font-mono text-[10px] text-cyan/70">
              {formatClock(message.createdAt)}
            </p>
          </div>
          <div className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-lg border border-border bg-surface-2">
            <User className="size-3.5 text-muted-foreground" />
          </div>
        </div>
      </div>
    );
  }

  const pending = message.pendingCommand;
  const unresolved = pending && !pending.resolved;

  return (
    <div className="animate-nx-rise mx-auto w-full max-w-3xl">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">
          <NexusCore state={message.streaming ? "responding" : "idle"} size={28} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="nx-label text-foreground/80">Nexus</span>
            <span className="font-mono text-[10px] text-muted-foreground">
              {message.provider} · {message.model}
            </span>
            {message.meta && (
              <span className="font-mono text-[10px] text-muted-foreground/70">
                {message.meta.latencyMs}ms · {message.meta.tokensIn}↓ {message.meta.tokensOut}↑
              </span>
            )}
          </div>

          {unresolved ? (
            <div className="my-2 rounded-xl border border-violet/25 bg-violet/10 p-4">
              <p className="mb-3 text-[13px] leading-relaxed text-foreground/90">
                Proposed terminal command:
              </p>
              <div className="mb-4 rounded-lg border border-border bg-[oklch(0.125_0.008_265)] px-3 py-2 font-mono text-[12.5px] text-foreground/90">
                {pending.command}
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => approveCommand(message.id)}
                  className="nx-focus flex h-8 items-center gap-1.5 rounded-lg border border-signal/30 bg-signal/10 px-3 text-[12.5px] text-signal transition-colors hover:bg-signal/20"
                >
                  <Check className="size-3.5" /> Approve
                </button>
                <button
                  type="button"
                  onClick={() => declineCommand(message.id)}
                  className="nx-focus flex h-8 items-center gap-1.5 rounded-lg border border-destructive/30 bg-destructive/10 px-3 text-[12.5px] text-destructive transition-colors hover:bg-destructive/20"
                >
                  <X className="size-3.5" /> Decline
                </button>
              </div>
            </div>
          ) : (
            <>
              <Markdown content={message.content} />
              {pending?.resolved && (
                <span
                  className={cn(
                    "mt-1 inline-flex items-center gap-1 font-mono text-[10px]",
                    pending.resolved === "approved" ? "text-signal" : "text-destructive",
                  )}
                >
                  {pending.resolved === "approved" ? <Check className="size-3" /> : <X className="size-3" />}
                  {pending.resolved}
                </span>
              )}
            </>
          )}

          {message.streaming && (
            <span className="animate-nx-caret ml-0.5 inline-block h-4 w-[7px] translate-y-0.5 bg-cyan" />
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  const { coreState } = useNexus();
  const prompts = [
    "Explain the provider failover chain",
    "/models",
    "Write a Termux service wrapper",
    "/architecture",
  ];
  const { submit } = useNexus();

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <NexusCore state={coreState} size={112} />
      <h1 className="mt-8 font-mono text-2xl font-semibold tracking-[0.22em] text-foreground">
        NEXUSCHAT
      </h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        Your AI. Your models. Your command center.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        {prompts.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => submit(p)}
            className={cn(
              "nx-focus rounded-full border border-border bg-surface/60 px-3.5 py-1.5 text-[12.5px] text-muted-foreground transition-all hover:border-cyan/40 hover:text-foreground",
              p.startsWith("/") && "font-mono text-cyan/80",
            )}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

export function MessageList() {
  const { activeSession, coreState } = useNexus();
  const endRef = useRef<HTMLDivElement>(null);
  const count = activeSession?.messages.length ?? 0;
  const lastLength = activeSession?.messages.at(-1)?.content.length ?? 0;

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [count, lastLength]);

  if (!activeSession || activeSession.messages.length === 0) return <EmptyState />;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="flex flex-col gap-7 px-4 py-8 sm:px-8">
        {activeSession.messages.map((m) => (
          <MessageRow key={m.id} message={m} />
        ))}
        {coreState === "thinking" && (
          <div className="mx-auto flex w-full max-w-3xl items-center gap-3">
            <NexusCore state="thinking" size={28} />
            <span className="nx-label animate-pulse text-violet">Routing through provider layer…</span>
          </div>
        )}
        <div ref={endRef} className="h-1" />
      </div>
    </div>
  );
}
