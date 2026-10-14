import { Check, ChevronDown, Cpu, Layers } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { accentClasses, formatContext } from "@/lib/nexus/format";
import { useNexus } from "@/lib/nexus/store";
import { cn } from "@/lib/utils";

export function ProviderSelector({ compact = false }: { compact?: boolean }) {
  const { provider, setProvider, providers } = useNexus();
  const active = providers.find((p) => p.id === provider);
  const accent = active ? accentClasses[active.accent] : accentClasses.cyan;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={cn(
          "nx-focus group flex h-9 items-center gap-2 rounded-lg border border-border bg-surface/70 px-2.5 text-[13px] transition-colors hover:border-border hover:bg-surface-2",
        )}
      >
        <span className={cn("size-1.5 rounded-full", accent.dot)} />
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          {compact ? "" : "provider"}
        </span>
        <span className="font-medium text-foreground">{active?.name ?? provider}</span>
        <ChevronDown className="size-3.5 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-72 border-border bg-popover/95 backdrop-blur-xl">
        <DropdownMenuLabel className="nx-label">Provider layer</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {providers.map((p) => {
          const a = accentClasses[p.accent];
          return (
            <DropdownMenuItem
              key={p.id}
              onClick={() => setProvider(p.id)}
              className="flex-col items-start gap-1 py-2"
            >
              <div className="flex w-full items-center gap-2">
                <Cpu className={cn("size-3.5", a.text)} />
                <span className="font-medium">{p.name}</span>
                <span className="ml-auto font-mono text-[10px] text-muted-foreground">
                  {p.status}
                </span>
                {p.id === provider && <Check className="size-3.5 text-cyan" />}
              </div>
              <p className="pl-5 text-[11.5px] leading-snug text-muted-foreground">{p.description}</p>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ModelSelector() {
  const { provider, model, setModel, models } = useNexus();
  const active = models.find((m) => m.id === model);
  const forProvider = models.filter((m) => m.provider === provider);
  const others = models.filter((m) => m.provider !== provider);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="nx-focus group flex h-9 max-w-[240px] items-center gap-2 rounded-lg border border-border bg-surface/70 px-2.5 text-[13px] transition-colors hover:bg-surface-2">
        <Layers className="size-3.5 shrink-0 text-violet" />
        <span className="truncate font-mono text-[11.5px] text-foreground">{active?.id ?? model}</span>
        <ChevronDown className="size-3.5 shrink-0 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-80 border-border bg-popover/95 backdrop-blur-xl">
        <DropdownMenuLabel className="nx-label">Active provider · {provider}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {forProvider.map((m) => (
          <DropdownMenuItem key={m.id} onClick={() => setModel(m.id)} className="flex-col items-start gap-1">
            <div className="flex w-full items-center gap-2">
              <span className="truncate font-mono text-[11.5px] text-foreground">{m.id}</span>
              {m.id === model && <Check className="ml-auto size-3.5 shrink-0 text-cyan" />}
            </div>
            <span className="font-mono text-[10px] text-muted-foreground">
              {m.contextWindow ? `${formatContext(m.contextWindow)} ctx · ` : ""}
              {m.throughput ?? "suggested"}
            </span>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="nx-label">Other providers</DropdownMenuLabel>
        {others.map((m) => (
          <DropdownMenuItem key={m.id} onClick={() => setModel(m.id)} className="gap-2">
            <span className="truncate font-mono text-[11.5px] text-muted-foreground">{m.id}</span>
            <span className="ml-auto font-mono text-[10px] text-muted-foreground/70">{m.provider}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
