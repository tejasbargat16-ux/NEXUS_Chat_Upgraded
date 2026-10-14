export function formatClock(ts: number) {
  return new Date(ts).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatRelative(ts: number) {
  const diff = Date.now() - ts;
  const min = Math.round(diff / 60_000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hours = Math.round(min / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

export function formatUptime(seconds: number) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function formatContext(tokens: number) {
  if (tokens >= 1_000_000) return `${tokens / 1_000_000}M`;
  return `${Math.round(tokens / 1000)}K`;
}

export const accentClasses = {
  cyan: {
    text: "text-cyan",
    bg: "bg-cyan/10",
    border: "border-cyan/30",
    dot: "bg-cyan",
    glow: "shadow-glow-cyan",
  },
  violet: {
    text: "text-violet",
    bg: "bg-violet/10",
    border: "border-violet/30",
    dot: "bg-violet",
    glow: "shadow-glow-violet",
  },
  signal: {
    text: "text-signal",
    bg: "bg-signal/10",
    border: "border-signal/30",
    dot: "bg-signal",
    glow: "shadow-glow-cyan",
  },
} as const;
