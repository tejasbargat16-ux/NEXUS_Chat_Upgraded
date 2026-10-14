import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { Composer } from "@/components/nexus/composer";
import { MessageList } from "@/components/nexus/message-list";
import { SessionPanel } from "@/components/nexus/session-panel";
import { WorkspaceHeader } from "@/components/nexus/workspace-header";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "NexusChat — AI Command Center" },
      {
        name: "description",
        content:
          "Chat workspace for NexusChat: switch between Groq, Gemini and OpenRouter models, run slash commands, and resume persistent sessions.",
      },
      { property: "og:title", content: "NexusChat — AI Command Center" },
      {
        property: "og:description",
        content:
          "Multi-provider AI chat workspace with command-based interaction and persistent SQLite sessions.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ChatWorkspace,
});

function ChatWorkspace() {
  const [panelOpen, setPanelOpen] = useState(false);

  return (
    <div className="flex min-h-0 flex-1">
      <div className="flex min-w-0 flex-1 flex-col">
        <WorkspaceHeader panelOpen={panelOpen} onTogglePanel={() => setPanelOpen((o) => !o)} />
        <MessageList />
        <Composer />
      </div>
      {panelOpen && (
        <div className="absolute inset-y-0 right-0 z-30 w-[300px] max-w-[85vw] shadow-panel lg:static lg:z-auto lg:shadow-none">
          <SessionPanel onClose={() => setPanelOpen(false)} />
        </div>
      )}
    </div>
  );
}
