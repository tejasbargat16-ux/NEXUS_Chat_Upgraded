import { Check, Copy } from "lucide-react";
import { useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * Small dependency-free markdown renderer tuned for AI transcripts:
 * fenced code blocks, tables, headings, lists, blockquotes, bold/italic,
 * inline code and links. Anything unrecognised renders as a paragraph.
 */

function inline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern =
    /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let i = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    const token = match[0];
    const key = `${keyPrefix}-${i++}`;

    if (token.startsWith("`")) {
      nodes.push(
        <code
          key={key}
          className="rounded-[5px] border border-border bg-surface-2 px-1.5 py-0.5 font-mono text-[0.85em] text-cyan"
        >
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("**")) {
      nodes.push(
        <strong key={key} className="font-semibold text-foreground">
          {token.slice(2, -2)}
        </strong>,
      );
    } else if (token.startsWith("[")) {
      const parsed = token.match(/\[([^\]]+)\]\(([^)]+)\)/);
      const label = parsed?.[1] ?? token;
      const href = parsed?.[2] ?? "#";
      nodes.push(
        <a
          key={key}
          href={href}
          target="_blank"
          rel="noreferrer"
          className="text-cyan underline decoration-cyan/30 underline-offset-4 hover:decoration-cyan"
        >
          {label}
        </a>,
      );
    } else {
      nodes.push(
        <em key={key} className="italic text-foreground/90">
          {token.slice(1, -1)}
        </em>,
      );
    }
    last = match.index + token.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function CodeBlock({ code, lang }: { code: string; lang: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    void navigator.clipboard?.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="group my-4 overflow-hidden rounded-xl border border-border bg-[oklch(0.125_0.008_265)]">
      <div className="flex items-center justify-between border-b border-border bg-surface/60 px-3 py-1.5">
        <span className="nx-label">{lang || "text"}</span>
        <button
          type="button"
          onClick={copy}
          aria-label="Copy code"
          className="nx-focus flex items-center gap-1.5 rounded-md px-2 py-1 font-mono text-[11px] text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground"
        >
          {copied ? <Check className="size-3 text-signal" /> : <Copy className="size-3" />}
          {copied ? "copied" : "copy"}
        </button>
      </div>
      <pre className="overflow-x-auto px-4 py-3.5">
        <code className="font-mono text-[12.5px] leading-relaxed text-foreground/90">{code}</code>
      </pre>
    </div>
  );
}

export function Markdown({ content, className }: { content: string; className?: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i]!;

    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i]!.trim().startsWith("```")) {
        buf.push(lines[i]!);
        i++;
      }
      i++;
      blocks.push(<CodeBlock key={key++} code={buf.join("\n")} lang={lang} />);
      continue;
    }

    if (line.trim().startsWith("|") && lines[i + 1]?.trim().match(/^\|[\s\-:|]+\|$/)) {
      const cells = (row: string) =>
        row
          .trim()
          .replace(/^\||\|$/g, "")
          .split("|")
          .map((c) => c.trim());
      const head = cells(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i]!.trim().startsWith("|")) {
        rows.push(cells(lines[i]!));
        i++;
      }

      blocks.push(
        <div key={key++} className="my-4 overflow-x-auto rounded-xl border border-border">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="bg-surface/70">
                {head.map((h, hi) => (
                  <th key={hi} className="nx-label border-b border-border px-3 py-2">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, ri) => (
                <tr key={ri} className="border-b border-border/60 last:border-0">
                  {r.map((c, ci) => (
                    <td key={ci} className="px-3 py-2 align-top text-foreground/85">
                      {inline(c, `t${ri}${ci}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      const level = heading[1]?.length ?? 1;
      blocks.push(
        <p
          key={key++}
          className={cn(
            "mt-5 mb-2 font-semibold tracking-tight text-foreground first:mt-0",
            level <= 2 ? "text-base" : "text-sm",
          )}
        >
          {inline(heading[2] ?? line, `h${key}`)}
        </p>,
      );
      i++;
      continue;
    }

    if (/^\s*>\s+/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^\s*>\s?/.test(lines[i]!)) {
        buf.push(lines[i]!.replace(/^\s*>\s?/, ""));
        i++;
      }
      blocks.push(
        <blockquote
          key={key++}
          className="my-4 border-l-2 border-violet/60 bg-violet/5 py-2 pl-4 pr-3 text-sm text-foreground/85"
        >
          {inline(buf.join(" "), `q${key}`)}
        </blockquote>,
      );
      continue;
    }

    if (/^\s*(?:[-*]|\d+\.)\s+/.test(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const items: string[] = [];
      while (i < lines.length && /^\s*(?:[-*]|\d+\.)\s+/.test(lines[i]!)) {
        items.push(lines[i]!.replace(/^\s*(?:[-*]|\d+\.)\s+/, ""));
        i++;
      }
      blocks.push(
        <ul key={key++} className="my-3 space-y-1.5 pl-1">
          {items.map((item, ii) => (
            <li key={ii} className="flex gap-2.5 text-sm leading-relaxed text-foreground/85">
              <span
                className={cn(
                  "mt-0.5 shrink-0 font-mono text-[11px] tabular-nums",
                  ordered ? "text-cyan" : "text-cyan/70",
                )}
              >
                {ordered ? `${ii + 1}.` : "—"}
              </span>
              <span>{inline(item, `l${key}${ii}`)}</span>
            </li>
          ))}
        </ul>,
      );
      continue;
    }

    if (!line.trim()) {
      i++;
      continue;
    }

    const buf: string[] = [];
    while (
      i < lines.length &&
      lines[i]!.trim() &&
      !lines[i]!.trim().startsWith("```") &&
      !lines[i]!.trim().startsWith("|") &&
      !/^\s*(?:[-*]|\d+\.)\s+/.test(lines[i]!) &&
      !/^#{1,4}\s/.test(lines[i]!) &&
      !/^\s*>\s/.test(lines[i]!)
    ) {
      buf.push(lines[i]!);
      i++;
    }
    if (buf.length) {
      blocks.push(
        <p key={key++} className="my-2.5 text-[14.5px] leading-[1.75] text-foreground/85 first:mt-0">
          {inline(buf.join(" "), `p${key}`)}
        </p>,
      );
    }
  }

  return <div className={cn("min-w-0", className)}>{blocks}</div>;
}
