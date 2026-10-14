import { createFileRoute } from "@tanstack/react-router";
import { Boxes, Cpu } from "lucide-react";

import { PageShell } from "@/components/nexus/page-shell";
import { formatContext } from "@/lib/nexus/format";
import { useNexus } from "@/lib/nexus/store";

export const Route = createFileRoute("/models")({
  head: () => ({
    meta: [
      { title: "Models — NexusChat" },
      {
        name: "description",
        content: "Inspect the language models currently reported by your NexusChat backend.",
      },
      { property: "og:title", content: "Models — NexusChat" },
      {
        property: "og:description",
        content: "Backend-reported models available to the NexusChat workspace.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ModelsPage,
});

function ModelsPage() {
  const { models, provider } = useNexus();

  return (
    <PageShell
      eyebrow="Runtime · model catalog"
      title="Models"
      description="Models shown here come from the providers your backend reports. Select one in the workspace header to use it for your next message."
    >
      {models.length === 0 ? (
        <div className="nx-glass rounded-xl p-5">
          <p className="nx-label">No models reported</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Connect your backend in Settings to load its available models.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {models.map((model) => (
            <article key={`${model.provider}:${model.id}`} className="nx-glass rounded-xl p-4">
              <div className="flex items-center gap-2">
                <Boxes className="size-4 text-violet" />
                <span className="min-w-0 truncate font-mono text-[12px] text-foreground">
                  {model.id}
                </span>
                {model.provider === provider && (
                  <span className="ml-auto shrink-0 rounded-full border border-cyan/30 bg-cyan/10 px-2 py-0.5 font-mono text-[9px] uppercase text-cyan">
                    active provider
                  </span>
                )}
              </div>
              <div className="mt-3 flex items-center gap-1.5 font-mono text-[10.5px] text-muted-foreground">
                <Cpu className="size-3" />
                <span>{model.provider}</span>
                {model.tags.includes("default") && <span>· default</span>}
                {model.contextWindow ? (
                  <span>· {formatContext(model.contextWindow)} context</span>
                ) : null}
              </div>
              <p className="mt-3 text-[12.5px] leading-relaxed text-muted-foreground">
                {model.description}
              </p>
            </article>
          ))}
        </div>
      )}
    </PageShell>
  );
}