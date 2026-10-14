import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Database, Pencil, Plus, Trash2 } from "lucide-react";

import { PageShell } from "@/components/nexus/page-shell";
import { formatRelative } from "@/lib/nexus/format";
import { useNexus } from "@/lib/nexus/store";

export const Route = createFileRoute("/sessions")({
  head: () => ({
    meta: [
      { title: "Sessions — NexusChat" },
      {
        name: "description",
        content:
          "Browse, load, rename and delete persistent NexusChat sessions stored in SQLite, each with its own provider and model.",
      },
      { property: "og:title", content: "Sessions — NexusChat" },
      {
        property: "og:description",
        content: "Persistent SQLite conversation sessions with per-session provider and model state.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SessionsPage,
});

function SessionsPage() {
  const { sessions, activeSessionId, selectSession, deleteSession, renameSession, newSession } =
    useNexus();
  const navigate = useNavigate();

  const open = (id: string) => {
    selectSession(id);
    void navigate({ to: "/" });
  };

  return (
    <PageShell
      eyebrow="Persistence · nexus.db"
      title="Sessions"
      description="Every turn is written to SQLite before it is rendered. Sessions store their own provider and model, so loading one restores the exact runtime it was created with."
      aside={
        <button
          type="button"
          onClick={() => {
            newSession();
            void navigate({ to: "/" });
          }}
          className="nx-focus flex h-9 items-center gap-2 rounded-lg border border-cyan/25 bg-cyan/10 px-3 text-[13px] text-cyan transition-colors hover:bg-cyan/20"
        >
          <Plus className="size-3.5" /> New
        </button>
      }
    >
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {sessions.map((s) => (
          <article
            key={s.id}
            className="nx-glass group flex flex-col rounded-2xl p-4 transition-all hover:border-cyan/25"
          >
            <div className="flex items-center gap-2">
              <Database className="size-3.5 text-signal" />
              <span className="font-mono text-[10.5px] text-muted-foreground">row {s.rowId}</span>
              {s.id === activeSessionId && (
                <span className="ml-auto rounded-full border border-cyan/30 bg-cyan/10 px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-widest text-cyan">
                  active
                </span>
              )}
            </div>
            <h2 className="mt-3 text-[15px] font-medium leading-snug text-foreground">{s.title}</h2>
            <p className="mt-1 font-mono text-[10.5px] text-muted-foreground">
              {s.id} · {s.messages.length} turns · {formatRelative(s.updatedAt)}
            </p>
            <p className="mt-3 line-clamp-2 text-[12.5px] leading-relaxed text-muted-foreground/80">
              {s.messages.find((m) => m.role === "user")?.content ?? "No prompts yet."}
            </p>
            <div className="mt-4 flex items-center gap-2 border-t border-border pt-3">
              <span className="font-mono text-[10px] text-violet">{s.provider}</span>
              <span className="truncate font-mono text-[10px] text-muted-foreground/70">{s.model}</span>
              <div className="ml-auto flex gap-1">
                <button
                  type="button"
                  aria-label={`Rename ${s.title}`}
                  onClick={() => {
                    const next = window.prompt("Rename session", s.title);
                    if (next?.trim()) renameSession(s.id, next.trim());
                  }}
                  className="nx-focus grid size-7 place-items-center rounded-md border border-border text-muted-foreground hover:text-foreground"
                >
                  <Pencil className="size-3" />
                </button>
                <button
                  type="button"
                  aria-label={`Delete ${s.title}`}
                  onClick={() => deleteSession(s.id)}
                  className="nx-focus grid size-7 place-items-center rounded-md border border-border text-muted-foreground hover:border-destructive/40 hover:text-destructive"
                >
                  <Trash2 className="size-3" />
                </button>
              </div>
            </div>
            <button
              type="button"
              onClick={() => open(s.id)}
              className="nx-focus mt-3 h-9 rounded-lg border border-border bg-surface/60 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-cyan/40 hover:text-cyan"
            >
              /load {s.id}
            </button>
          </article>
        ))}
      </div>
    </PageShell>
  );
}
