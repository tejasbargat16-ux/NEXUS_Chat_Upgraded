import { PanelLeft } from "lucide-react";
import type { ReactNode } from "react";

import { StatusPill } from "@/components/nexus/workspace-header";
import { useNexus } from "@/lib/nexus/store";

export function PageShell({
  eyebrow,
  title,
  description,
  children,
  aside,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  aside?: ReactNode;
}) {
  const { toggleSidebar } = useNexus();

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="z-20 flex items-center gap-2 border-b border-border bg-background/70 px-4 py-2.5 backdrop-blur-xl sm:px-6">
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
          className="nx-focus grid size-9 shrink-0 place-items-center rounded-lg border border-border bg-surface/70 text-muted-foreground transition-colors hover:text-foreground"
        >
          <PanelLeft className="size-4" />
        </button>
        <span className="nx-label truncate">{eyebrow}</span>
        <div className="ml-auto flex items-center gap-2">
          {aside}
          <StatusPill />
        </div>
      </header>

      <div className="nx-grid-bg flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-8">
          <h1 className="text-[26px] font-semibold tracking-tight text-foreground sm:text-3xl">{title}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">{description}</p>
          <div className="mt-9">{children}</div>
        </div>
      </div>
    </div>
  );
}
