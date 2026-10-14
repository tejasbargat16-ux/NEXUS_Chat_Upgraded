import { cn } from "@/lib/utils";
import type { CoreState } from "@/lib/nexus/types";

/**
 * The Nexus Core: an always-present system heartbeat.
 * idle = slow breathing, thinking = tighter pulse + counter-rotating rings,
 * responding = bright core with a fast scan ring.
 */
export function NexusCore({
  state,
  size = 72,
  className,
}: {
  state: CoreState;
  size?: number;
  className?: string;
}) {
  const thinking = state === "thinking";
  const responding = state === "responding";

  return (
    <div
      className={cn("relative shrink-0", className)}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      {/* outer ring */}
      <div
        className={cn(
          "absolute inset-0 rounded-full border transition-colors duration-500",
          responding ? "border-cyan/40" : thinking ? "border-violet/35" : "border-border",
          (thinking || responding) && "animate-nx-spin-slow",
        )}
        style={{ borderStyle: "dashed" }}
      />
      {/* mid ring */}
      <div
        className={cn(
          "absolute rounded-full border transition-colors duration-500",
          responding ? "border-cyan/30" : thinking ? "border-violet/40" : "border-border/70",
          (thinking || responding) && "animate-nx-spin-rev",
        )}
        style={{ inset: size * 0.14 }}
      />
      {/* halo */}
      <div
        className={cn(
          "absolute rounded-full blur-md transition-all duration-700",
          responding ? "bg-cyan/30" : thinking ? "bg-violet/25" : "bg-cyan/10",
        )}
        style={{ inset: size * 0.26 }}
      />
      {/* core */}
      <div
        className={cn(
          "absolute rounded-full transition-colors duration-500 animate-nx-pulse",
          responding ? "bg-cyan" : thinking ? "bg-violet" : "bg-cyan/70",
        )}
        style={{
          inset: size * 0.34,
          animationDuration: responding ? "0.9s" : thinking ? "1.4s" : "3.6s",
        }}
      />
      {/* orbiting node */}
      <div
        className={cn(
          "absolute inset-0",
          responding ? "animate-nx-spin-slow" : thinking ? "animate-nx-spin-rev" : "animate-nx-spin-slow",
        )}
        style={{ animationDuration: responding ? "2.2s" : thinking ? "4s" : "14s" }}
      >
        <span
          className={cn(
            "absolute left-1/2 top-0 -translate-x-1/2 rounded-full",
            responding ? "bg-cyan" : thinking ? "bg-violet" : "bg-signal/80",
          )}
          style={{ width: size * 0.07, height: size * 0.07 }}
        />
      </div>
    </div>
  );
}

export function CoreStateLabel({ state }: { state: CoreState }) {
  const copy: Record<CoreState, string> = {
    idle: "Core idle · awaiting input",
    thinking: "Core engaged · routing prompt",
    responding: "Core streaming · decoding tokens",
  };
  return (
    <span
      className={cn(
        "nx-label",
        state === "responding" && "text-cyan",
        state === "thinking" && "text-violet",
      )}
    >
      {copy[state]}
    </span>
  );
}
