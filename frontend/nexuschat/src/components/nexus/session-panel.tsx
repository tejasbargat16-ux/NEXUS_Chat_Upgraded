import { Database, Pencil, Plus, Trash2, X } from "lucide-react";

import { formatRelative } from "@/lib/nexus/format";
import { useNexus } from "@/lib/nexus/store";
import { cn } from "@/lib/utils";

export function SessionPanel({ onClose }: { onClose: () => void }) {
  const { sessions, activeSessionId, selectSession, newSession, deleteSession, renameSession } =
    useNexus();

  return (
    <aside className="flex h-full w-full flex-col border-l border-border bg-sidebar lg:w-[300px]">
      <div className="flex h-[54px] items-center gap-2 border-b border-border px-4">
        <Database className="size-3.5 text-signal" />
        <span className="nx-label">Sessions</span>
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">nexus.db</span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close session panel"
          className="nx-focus grid size-6 place-items-center rounded-md text-muted-foreground hover:bg-surface-2 hover:text-foreground"
        >
          <X className="size-3.5" />
        </button>
      </div>

      <div className="border-b border-border p-3">
        <button
          type="button"
          onClick={() => newSession()}
          className="nx-focus flex h-9 w-full items-center justify-center gap-2 rounded-lg border border-border bg-surface/70 text-[13px] text-foreground transition-colors hover:border-cyan/40 hover:text-cyan"
        >
          <Plus className="size-3.5" /> New session
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sessions.map((s) => {
          const active = s.id === activeSessionId;
          return (
            <div
              key={s.id}
              className={cn(
                "group mb-1 rounded-xl border px-3 py-2.5 transition-colors",
                active
                  ? "border-cyan/25 bg-cyan/[0.07]"
                  : "border-transparent hover:border-border hover:bg-surface/70",
              )}
            >
              <button
                type="button"
                onClick={() => selectSession(s.id)}
                className="nx-focus block w-full text-left"
              >
                <span
                  className={cn(
                    "block truncate text-[13px] leading-tight",
                    active ? "text-foreground" : "text-foreground/75",
                  )}
                >
                  {s.title}
                </span>
                <span className="mt-1 block truncate font-mono text-[10px] text-muted-foreground">
                  {s.id} · row {s.rowId} · {s.messages.length} turns
                </span>
                <span className="mt-0.5 block font-mono text-[10px] text-muted-foreground/60">
                  {s.provider} · {formatRelative(s.updatedAt)}
                </span>
              </button>
              <div className="mt-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
                <button
                  type="button"
                  aria-label={`Rename ${s.title}`}
                  onClick={() => {
                    const next = window.prompt("Rename session", s.title);
                    if (next?.trim()) renameSession(s.id, next.trim());
                  }}
                  className="nx-focus flex items-center gap-1 rounded-md border border-border px-1.5 py-1 font-mono text-[10px] text-muted-foreground hover:text-foreground"
                >
                  <Pencil className="size-2.5" /> rename
                </button>
                <button
                  type="button"
                  aria-label={`Delete ${s.title}`}
                  onClick={() => deleteSession(s.id)}
                  className="nx-focus flex items-center gap-1 rounded-md border border-border px-1.5 py-1 font-mono text-[10px] text-muted-foreground hover:border-destructive/40 hover:text-destructive"
                >
                  <Trash2 className="size-2.5" /> delete
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
