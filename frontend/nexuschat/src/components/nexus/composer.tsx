import { CornerDownLeft, Slash, Square } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { COMMANDS } from "@/lib/nexus/mock-data";
import { useNexus } from "@/lib/nexus/store";
import { cn } from "@/lib/utils";

const GROUP_ACCENT = {
  session: "text-signal",
  model: "text-cyan",
  system: "text-violet",
} as const;

export function Composer() {
  const { submit, streaming, stop, provider, model } = useNexus();
  const [value, setValue] = useState("");
  const [highlight, setHighlight] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const suggestions = useMemo(() => {
    const trimmed = value.trimStart();
    if (!trimmed.startsWith("/") || trimmed.includes(" ")) return [];
    const q = trimmed.toLowerCase();
    return COMMANDS.filter((c) => c.name.startsWith(q));
  }, [value]);

  useEffect(() => setHighlight(0), [suggestions.length]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 220)}px`;
  }, [value]);

  const accept = (name: string) => {
    setValue(`${name} `);
    textareaRef.current?.focus();
  };

  const send = () => {
    if (!value.trim() || streaming) return;
    submit(value);
    setValue("");
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (suggestions.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setHighlight((h) => (h + 1) % suggestions.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setHighlight((h) => (h - 1 + suggestions.length) % suggestions.length);
        return;
      }
      const selected = suggestions[highlight];
      if (e.key === "Tab" || (e.key === "Enter" && !e.shiftKey && selected && value.trim() !== selected.name)) {
        e.preventDefault();
        if (selected) accept(selected.name);
        return;
      }
      if (e.key === "Escape") {
        setValue("");
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="relative border-t border-border bg-background/80 px-4 pb-4 pt-3 backdrop-blur-xl sm:px-8">
      <div className="mx-auto w-full max-w-3xl">
        {suggestions.length > 0 && (
          <div className="animate-nx-rise absolute bottom-full left-4 right-4 mb-2 sm:left-8 sm:right-8">
            <div className="mx-auto max-w-3xl overflow-hidden rounded-xl border border-border bg-popover/95 shadow-panel backdrop-blur-xl">
              <div className="nx-label flex items-center gap-2 border-b border-border px-3 py-2">
                <Slash className="size-3" />
                command palette
                <span className="ml-auto normal-case tracking-normal">
                  ↑↓ navigate · tab complete · esc dismiss
                </span>
              </div>
              <ul className="max-h-64 overflow-y-auto py-1">
                {suggestions.map((c, i) => (
                  <li key={c.name}>
                    <button
                      type="button"
                      onMouseEnter={() => setHighlight(i)}
                      onClick={() => accept(c.name)}
                      className={cn(
                        "flex w-full items-baseline gap-2.5 px-3 py-2 text-left transition-colors",
                        i === highlight ? "bg-surface-2" : "hover:bg-surface/70",
                      )}
                    >
                      <span className={cn("font-mono text-[12.5px]", GROUP_ACCENT[c.group])}>
                        {c.name}
                      </span>
                      {c.args && (
                        <span className="font-mono text-[11px] text-muted-foreground/70">{c.args}</span>
                      )}
                      <span className="ml-auto truncate pl-3 text-[11.5px] text-muted-foreground">
                        {c.summary}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div
          className={cn(
            "group relative rounded-2xl border bg-surface/60 transition-all duration-300",
            streaming ? "border-cyan/40 shadow-glow-cyan" : "border-border focus-within:border-cyan/40",
          )}
        >
          <textarea
            ref={textareaRef}
            value={value}
            rows={1}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Message Nexus, or type / for commands…"
            aria-label="Message composer"
            className="block w-full resize-none bg-transparent px-4 pb-11 pt-3.5 text-[14.5px] leading-relaxed text-foreground outline-none placeholder:text-muted-foreground/70"
          />

          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center gap-2 px-3 pb-2.5">
            <span className="font-mono text-[10px] text-muted-foreground">
              {provider}
              <span className="text-muted-foreground/40"> / </span>
              <span className="text-muted-foreground/80">{model}</span>
            </span>
            <span className="ml-auto" />
            {streaming ? (
              <button
                type="button"
                onClick={stop}
                aria-label="Stop generating"
                className="nx-focus pointer-events-auto grid size-8 place-items-center rounded-lg border border-border bg-surface-2 text-foreground transition-colors hover:border-destructive/50 hover:text-destructive"
              >
                <Square className="size-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={send}
                disabled={!value.trim()}
                aria-label="Send message"
                className="nx-focus pointer-events-auto grid size-8 place-items-center rounded-lg border border-cyan/30 bg-cyan/15 text-cyan transition-all hover:bg-cyan/25 hover:shadow-glow-cyan disabled:border-border disabled:bg-surface-2 disabled:text-muted-foreground/50 disabled:shadow-none"
              >
                <CornerDownLeft className="size-3.5" />
              </button>
            )}
          </div>
        </div>

        <p className="mt-2 text-center font-mono text-[10px] text-muted-foreground/60">
          Responses are generated by the selected external provider. Sessions persist to SQLite.
        </p>
      </div>
    </div>
  );
}
