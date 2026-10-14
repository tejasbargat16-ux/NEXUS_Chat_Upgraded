import { Activity, PanelLeft, PanelRight, Settings2 } from "lucide-react";
import { Link } from "@tanstack/react-router";

import { CoreStateLabel } from "@/components/nexus/nexus-core";
import { ModelSelector, ProviderSelector } from "@/components/nexus/selectors";
import { formatUptime } from "@/lib/nexus/format";
import { useNexus } from "@/lib/nexus/store";
import { cn } from "@/lib/utils";

export function StatusPill() {
  const { systemOnline, uptimeSeconds } = useNexus();
  return (
    <div className="flex h-9 items-center gap-2 rounded-lg border border-signal/25 bg-signal/10 px-2.5">
      <span className="relative flex size-1.5">
        <span className="absolute inline-flex size-full animate-ping rounded-full bg-signal opacity-70" />
        <span className="relative inline-flex size-1.5 rounded-full bg-signal" />
      </span>
      <span className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-signal">
        {systemOnline ? "online" : "offline"}
      </span>
      <span className="hidden font-mono text-[10.5px] text-signal/60 sm:inline">
        {formatUptime(uptimeSeconds)}
      </span>
    </div>
  );
}

export function WorkspaceHeader({
  panelOpen,
  onTogglePanel,
}: {
  panelOpen?: boolean;
  onTogglePanel?: () => void;
}) {
  const { toggleSidebar, activeSession, coreState } = useNexus();

  return (
    <header className="z-20 flex flex-col gap-2 border-b border-border bg-background/70 px-4 py-2.5 backdrop-blur-xl sm:px-6">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
          className="nx-focus grid size-9 shrink-0 place-items-center rounded-lg border border-border bg-surface/70 text-muted-foreground transition-colors hover:text-foreground"
        >
          <PanelLeft className="size-4" />
        </button>

        <Link
          to="/settings"
          aria-label="Settings"
          className="nx-focus grid size-9 shrink-0 place-items-center rounded-lg border border-border bg-surface/70 text-muted-foreground transition-colors hover:text-foreground"
        >
          <Settings2 className="size-4" />
        </Link>

        <div className="mr-1 hidden min-w-0 flex-col md:flex">
          <span className="truncate text-[13.5px] font-medium leading-tight text-foreground">
            {activeSession?.title ?? "No session"}
          </span>
          <span className="truncate font-mono text-[10px] text-muted-foreground">
            {activeSession?.id} · sqlite row {activeSession?.rowId}
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <div className="hidden sm:block">
            <ProviderSelector />
          </div>
          <ModelSelector />
          <StatusPill />
          {onTogglePanel && (
            <button
              type="button"
              onClick={onTogglePanel}
              aria-label="Toggle session panel"
              className={cn(
                "nx-focus grid size-9 shrink-0 place-items-center rounded-lg border transition-colors",
                panelOpen
                  ? "border-cyan/30 bg-cyan/10 text-cyan"
                  : "border-border bg-surface/70 text-muted-foreground hover:text-foreground",
              )}
            >
              <PanelRight className="size-4" />
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Activity className="size-3 shrink-0 text-muted-foreground" />
        <CoreStateLabel state={coreState} />
        <span className="hidden font-mono text-[10.5px] text-muted-foreground/60 sm:inline">
          {activeSession?.messages.length ?? 0} turns persisted
        </span>
      </div>
    </header>
  );
}
