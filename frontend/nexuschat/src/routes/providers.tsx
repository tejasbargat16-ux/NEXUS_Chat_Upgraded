import { createFileRoute } from "@tanstack/react-router";
import { Cpu, KeyRound } from "lucide-react";

import { PageShell } from "@/components/nexus/page-shell";
import { useNexus } from "@/lib/nexus/store";

export const Route = createFileRoute("/providers")({
  head: () => ({
    meta: [
      { title: "Providers — NexusChat" },
      {
        name: "description",
        content: "View provider availability and configured API keys reported by your NexusChat backend.",
      },
      { property: "og:title", content: "Providers — NexusChat" },
      {
        property: "og:description",
        content: "Live provider availability from the connected NexusChat backend.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ProvidersPage,
});

function ProvidersPage() {
  const { providers, provider } = useNexus();

  return (
    <PageShell
      eyebrow="Runtime · provider layer"
      title="Providers"
      description="Provider names, key readiness, and default models are read from your backend. API credentials remain on the machine hosting the assistant."
    >
      {providers.length === 0 ? (
        <div className="nx-glass rounded-xl p-5">
          <p className="nx-label">No providers reported</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Connect your backend in Settings to inspect provider availability.
          </p>
        </div>
      ) : (
        <div className="divide-y divide-border border-y border-border">
          {providers.map((item) => (
            <article key={item.id} className="flex flex-wrap items-center gap-3 py-4">
              <Cpu className="size-4 shrink-0 text-cyan" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="font-medium text-foreground">{item.name}</h2>
                  {item.id === provider && (
                    <span className="rounded-full border border-cyan/30 bg-cyan/10 px-2 py-0.5 font-mono text-[9px] uppercase text-cyan">
                      selected
                    </span>
                  )}
                </div>
                <p className="mt-1 text-[12.5px] text-muted-foreground">{item.description}</p>
              </div>
              <div className="flex items-center gap-1.5 font-mono text-[10.5px] text-muted-foreground">
                <KeyRound className="size-3" />
                <span>{item.keyConfigured ? "key configured" : "key not configured"}</span>
              </div>
              <div className="w-full pl-7 font-mono text-[10.5px] text-muted-foreground sm:w-auto sm:pl-0">
                default · {item.defaultModel || "not reported"}
              </div>
            </article>
          ))}
        </div>
      )}
    </PageShell>
  );
}