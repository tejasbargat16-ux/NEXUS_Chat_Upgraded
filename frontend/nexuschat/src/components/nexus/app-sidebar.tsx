import { Link, useRouterState } from "@tanstack/react-router";
import {
  Boxes,
  ChevronLeft,
  Cpu,
  Database,
  MessagesSquare,
  Network,
  Plus,
  Settings2,
  Terminal,
} from "lucide-react";

import { NexusCore } from "@/components/nexus/nexus-core";
import { useNexus } from "@/lib/nexus/store";
import { formatRelative } from "@/lib/nexus/format";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Chats", icon: MessagesSquare, exact: true },
  { to: "/sessions", label: "Sessions", icon: Database },
  { to: "/models", label: "Models", icon: Boxes },
  { to: "/providers", label: "Providers", icon: Cpu },
  { to: "/architecture", label: "Architecture", icon: Network },
  { to: "/settings", label: "Settings", icon: Settings2 },
] as const;

export function AppSidebar() {
  const {
    sidebarOpen,
    setSidebarOpen,
    toggleSidebar,
    sessions,
    activeSessionId,
    selectSession,
    newSession,
    coreState,
  } = useNexus();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <>
      {/* mobile scrim */}
      <div
        onClick={() => setSidebarOpen(false)}
        className={cn(
          "fixed inset-0 z-30 bg-background/80 backdrop-blur-sm transition-opacity lg:hidden",
          sidebarOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
      />

      <aside
        className={cn(
          "fixed z-40 flex h-full flex-col border-r border-border bg-sidebar transition-[width,transform] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] lg:static",
          sidebarOpen ? "w-[276px] translate-x-0" : "w-[276px] -translate-x-full lg:w-[68px] lg:translate-x-0",
        )}
      >
        {/* brand */}
        <div className="flex h-16 items-center gap-3 border-b border-border px-4">
          <NexusCore state={coreState} size={30} />
          <div
            className={cn(
              "min-w-0 flex-1 overflow-hidden transition-opacity duration-200",
              sidebarOpen ? "opacity-100" : "lg:opacity-0",
            )}
          >
            <div className="truncate font-mono text-[13px] font-semibold tracking-[0.2em] text-foreground">
              NEXUSCHAT
            </div>
            <div className="truncate text-[10.5px] text-muted-foreground">
              Your AI. Your models. Your command center.
            </div>
          </div>
          <button
            type="button"
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
            className={cn(
              "nx-focus grid size-7 shrink-0 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground",
              !sidebarOpen && "lg:hidden",
            )}
          >
            <ChevronLeft className="size-4" />
          </button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-2.5 py-3">
          <button
            type="button"
            onClick={() => newSession()}
            className={cn(
              "nx-focus group flex h-10 items-center gap-3 rounded-lg border border-cyan/25 bg-cyan/10 px-2.5 text-sm font-medium text-cyan transition-all hover:border-cyan/50 hover:bg-cyan/15 hover:shadow-glow-cyan",
              !sidebarOpen && "lg:justify-center lg:px-0",
            )}
          >
            <Plus className="size-4 shrink-0" />
            <span className={cn("truncate", !sidebarOpen && "lg:hidden")}>New Chat</span>
          </button>

          <nav className="mt-3 flex flex-col gap-0.5">
            <p className={cn("nx-label px-2.5 pb-1.5", !sidebarOpen && "lg:hidden")}>Workspace</p>
            {NAV.map((item) => {
              const { to, label, icon: Icon } = item;
              const exact = "exact" in item && item.exact;
              const active = exact ? pathname === to : pathname.startsWith(to);
              return (
                <Link
                  key={to}
                  to={to}
                  onClick={() => {
                    if (window.innerWidth < 1024) setSidebarOpen(false);
                  }}
                  className={cn(
                    "nx-focus group relative flex h-9 items-center gap-3 rounded-lg px-2.5 text-sm transition-colors",
                    active
                      ? "bg-surface-2 text-foreground"
                      : "text-muted-foreground hover:bg-surface/70 hover:text-foreground",
                    !sidebarOpen && "lg:justify-center lg:px-0",
                  )}
                >
                  {active && (
                    <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-cyan" />
                  )}
                  <Icon className={cn("size-4 shrink-0", active && "text-cyan")} />
                  <span className={cn("truncate", !sidebarOpen && "lg:hidden")}>{label}</span>
                </Link>
              );
            })}
          </nav>

          <div className={cn("mt-4 flex min-h-0 flex-1 flex-col", !sidebarOpen && "lg:hidden")}>
            <p className="nx-label flex items-center justify-between px-2.5 pb-1.5">
              <span>Recent</span>
              <span className="text-cyan/70">{sessions.length}</span>
            </p>
            <div className="flex flex-col gap-0.5 overflow-y-auto">
              {sessions.map((s) => {
                const active = s.id === activeSessionId;
                return (
                  <Link
                    key={s.id}
                    to="/"
                    onClick={() => {
                      selectSession(s.id);
                      if (window.innerWidth < 1024) setSidebarOpen(false);
                    }}
                    className={cn(
                      "nx-focus flex flex-col gap-0.5 rounded-lg px-2.5 py-2 text-left transition-colors",
                      active ? "bg-surface-2" : "hover:bg-surface/70",
                    )}
                  >
                    <span
                      className={cn(
                        "truncate text-[13px] leading-tight",
                        active ? "text-foreground" : "text-foreground/70",
                      )}
                    >
                      {s.title}
                    </span>
                    <span className="truncate font-mono text-[10px] text-muted-foreground">
                      {s.id} · {formatRelative(s.updatedAt)}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>

        <div
          className={cn(
            "flex items-center gap-2 border-t border-border px-4 py-3",
            !sidebarOpen && "lg:justify-center lg:px-0",
          )}
        >
          <Terminal className="size-3.5 shrink-0 text-signal" />
          <span className={cn("font-mono text-[10px] text-muted-foreground", !sidebarOpen && "lg:hidden")}>
            termux · nexus.db · v1.4.2
          </span>
        </div>
      </aside>
    </>
  );
}
