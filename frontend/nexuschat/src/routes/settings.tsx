import { createFileRoute } from "@tanstack/react-router";
import { KeyRound, Link2, Loader2, PlugZap, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { PageShell } from "@/components/nexus/page-shell";
import { api, clearConfig, describeError, readConfig, writeConfig } from "@/lib/nexus/api";
import { useNexus } from "@/lib/nexus/store";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — NexusChat Connection" },
      {
        name: "description",
        content:
          "Connect NexusChat to your own Flask backend: paste the current cloudflared or ngrok tunnel URL and your API key.",
      },
      { property: "og:title", content: "Settings — NexusChat Connection" },
      {
        property: "og:description",
        content: "Runtime connection settings for the NexusChat backend tunnel URL and API key.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { systemOnline, connectionError, providers, reconnect } = useNexus();
  const [url, setUrl] = useState("");
  const [key, setKey] = useState("");
  const [status, setStatus] = useState<"idle" | "testing" | "ok" | "error">("idle");
  const [detail, setDetail] = useState<string>("");

  useEffect(() => {
    const cfg = readConfig();
    setUrl(cfg.url);
    setKey(cfg.key);
  }, []);

  const save = async () => {
    setStatus("testing");
    setDetail("");
    writeConfig({ url, key });
    try {
      const list = await api.providers();
      setStatus("ok");
      setDetail(`Connected. ${list.length} provider(s) reported by the backend.`);
      reconnect();
    } catch (e) {
      setStatus("error");
      setDetail(describeError(e));
    }
  };

  const disconnect = () => {
    clearConfig();
    setUrl("");
    setKey("");
    setStatus("idle");
    setDetail("");
  };

  return (
    <PageShell
      eyebrow="Runtime · connection"
      title="Settings"
      description="NexusChat talks to your own Flask backend over a tunnel whose URL changes every time cloudflared or ngrok restarts. Paste the current URL and API key here — they are stored locally in this browser and sent as an X-API-Key header, never bundled into the app."
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section className="nx-glass rounded-2xl p-5">
          <label className="nx-label flex items-center gap-2" htmlFor="nexus-url">
            <Link2 className="size-3" /> Backend URL
          </label>
          <input
            id="nexus-url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://your-tunnel.trycloudflare.com"
            spellCheck={false}
            className="nx-focus mt-2 w-full rounded-lg border border-border bg-surface/70 px-3 py-2.5 font-mono text-[12.5px] text-foreground outline-none placeholder:text-muted-foreground/60"
          />

          <label className="nx-label mt-5 flex items-center gap-2" htmlFor="nexus-key">
            <KeyRound className="size-3" /> API key
          </label>
          <input
            id="nexus-key"
            value={key}
            type="password"
            onChange={(e) => setKey(e.target.value)}
            placeholder="X-API-Key value"
            spellCheck={false}
            className="nx-focus mt-2 w-full rounded-lg border border-border bg-surface/70 px-3 py-2.5 font-mono text-[12.5px] text-foreground outline-none placeholder:text-muted-foreground/60"
          />

          <div className="mt-6 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => void save()}
              disabled={!url.trim() || !key.trim() || status === "testing"}
              className="nx-focus flex h-9 items-center gap-2 rounded-lg border border-cyan/30 bg-cyan/10 px-3 text-[13px] text-cyan transition-colors hover:bg-cyan/20 disabled:border-border disabled:bg-surface-2 disabled:text-muted-foreground/50"
            >
              {status === "testing" ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <PlugZap className="size-3.5" />
              )}
              Test &amp; Save
            </button>
            <button
              type="button"
              onClick={disconnect}
              className="nx-focus flex h-9 items-center gap-2 rounded-lg border border-border bg-surface/70 px-3 text-[13px] text-muted-foreground transition-colors hover:border-destructive/40 hover:text-destructive"
            >
              <Trash2 className="size-3.5" /> Clear
            </button>
          </div>

          {detail && (
            <p
              className={`mt-4 font-mono text-[11.5px] leading-relaxed ${
                status === "error" ? "text-destructive" : "text-signal"
              }`}
            >
              {detail}
            </p>
          )}
        </section>

        <section className="nx-glass rounded-2xl p-5">
          <p className="nx-label">Connection</p>
          <p className="mt-3 font-mono text-[11.5px] text-muted-foreground">
            status ·{" "}
            <span className={systemOnline ? "text-signal" : "text-destructive"}>
              {systemOnline ? "online" : "offline"}
            </span>
          </p>
          {connectionError && (
            <p className="mt-2 font-mono text-[11px] leading-relaxed text-muted-foreground/70">
              {connectionError}
            </p>
          )}
          <div className="mt-4 border-t border-border pt-3">
            <p className="nx-label">Providers</p>
            {providers.length === 0 ? (
              <p className="mt-2 text-[12.5px] text-muted-foreground">None reported yet.</p>
            ) : (
              <ul className="mt-2 space-y-1.5">
                {providers.map((p) => (
                  <li key={p.id} className="flex items-center gap-2 font-mono text-[11.5px]">
                    <span
                      className={`size-1.5 rounded-full ${
                        p.keyConfigured ? "bg-signal" : "bg-muted-foreground/50"
                      }`}
                    />
                    <span className="text-foreground">{p.id}</span>
                    <span className="ml-auto truncate text-muted-foreground/70">
                      {p.defaultModel}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </PageShell>
  );
}
