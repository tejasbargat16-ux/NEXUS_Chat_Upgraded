import { createFileRoute } from "@tanstack/react-router";
import { ArrowDown, Database, Terminal } from "lucide-react";

import { PageShell } from "@/components/nexus/page-shell";

export const Route = createFileRoute("/architecture")({
  head: () => ({
    meta: [
      { title: "Architecture — NexusChat" },
      {
        name: "description",
        content: "Explore how the NexusChat interface connects your assistant, provider layer, and persistent sessions.",
      },
      { property: "og:title", content: "Architecture — NexusChat" },
      {
        property: "og:description",
        content: "The request and response path between the NexusChat interface and your assistant backend.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ArchitecturePage,
});

const FLOW = [
  { name: "User", detail: "Message or slash command" },
  { name: "NexusChat frontend", detail: "Workspace, provider and model selection" },
  { name: "Command / input handler", detail: "Routes chat and session actions" },
  { name: "Provider layer", detail: "Groq · Gemini · OpenRouter" },
  { name: "AI response", detail: "Returned to the workspace" },
] as const;

function ArchitecturePage() {
  return (
    <PageShell
      eyebrow="System · request path"
      title="Architecture"
      description="The interface sends requests to your Flask assistant, which selects the configured provider and returns responses to the workspace."
    >
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_280px]">
        <section aria-label="Request path">
          {FLOW.map((step, index) => (
            <div key={step.name} className="flex flex-col items-center">
              <article className="nx-glass w-full max-w-xl rounded-xl px-4 py-3.5">
                <div className="flex items-center gap-3">
                  <span className="grid size-7 shrink-0 place-items-center rounded-lg border border-border font-mono text-[10px] text-cyan">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div className="min-w-0">
                    <h2 className="text-sm font-medium text-foreground">{step.name}</h2>
                    <p className="mt-0.5 text-[12px] text-muted-foreground">{step.detail}</p>
                  </div>
                </div>
              </article>
              {index < FLOW.length - 1 && <ArrowDown className="my-2 size-4 text-cyan/60" />}
            </div>
          ))}
        </section>

        <aside className="flex flex-col justify-center gap-3">
          <div className="nx-glass rounded-xl p-4">
            <div className="flex items-center gap-2">
              <Terminal className="size-4 text-violet" />
              <h2 className="text-sm font-medium text-foreground">Agent commands</h2>
            </div>
            <p className="mt-2 text-[12.5px] leading-relaxed text-muted-foreground">
              Proposed terminal actions wait for approval in the chat before the backend runs them.
            </p>
          </div>
          <div className="nx-glass rounded-xl p-4">
            <div className="flex items-center gap-2">
              <Database className="size-4 text-signal" />
              <h2 className="text-sm font-medium text-foreground">Persistent sessions</h2>
            </div>
            <p className="mt-2 text-[12.5px] leading-relaxed text-muted-foreground">
              Conversations are managed by the assistant backend and stored in its SQLite database.
            </p>
          </div>
        </aside>
      </div>
    </PageShell>
  );
}