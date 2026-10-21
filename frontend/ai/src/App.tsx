import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Terminal,
  Cpu,
  Radio,
  Shield,
  Send,
  Mic,
  Play,
  Layers,
  Code2,
  Sparkles,
  Sun,
  CheckCircle2,
  ChevronRight,
  Plus,
  Trash2,
  Copy,
  Check,
  Volume2,
  Database,
  AlertTriangle,
  RotateCcw,
  Sliders,
  MessageSquare,
  ExternalLink,
  HardDrive,
  Cpu as Microchip,
  Activity,
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./components/ui/tabs";
import { ScrollArea } from "./components/ui/scroll-area";

interface Message {
  id?: string | number;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
}

interface Provider {
  id: string;
  label: string;
  default_model: string;
  suggested_models: string[];
  has_key: boolean;
  key_configured?: boolean;
}

interface Conversation {
  id: number;
  title: string;
  created_at?: string;
  updated_at?: string;
}

interface PendingConfirmation {
  id: string;
  tool_name: string;
  command?: string;
  arguments?: Record<string, any>;
  risk_level?: string;
  timestamp?: number;
}

interface MemoryFact {
  id: number;
  fact: string;
  category: string;
  created_at: string;
}

let cachedApiKey = localStorage.getItem("nexus_api_key") || "";

async function getApiKey(): Promise<string> {
  if (cachedApiKey) return cachedApiKey;
  try {
    const res = await fetch("/config");
    if (res.ok) {
      const data = await res.json();
      if (data.api_key) {
        cachedApiKey = data.api_key;
        localStorage.setItem("nexus_api_key", data.api_key);
        return cachedApiKey;
      }
    }
  } catch (e) {
    // ignore
  }
  return "";
}

async function apiFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const key = await getApiKey();
  const headers = new Headers(options.headers || {});
  if (key) {
    headers.set("X-API-Key", key);
  }
  return fetch(url, { ...options, headers });
}

export default function App() {
  // State
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "### NEXUS Command Center Initialized\nOperational neural systems standing by for Lead Systems Architect **Tejas Bargat**.\n\nConnected to unified multi-provider routing engine with active desktop safety enforcement, real-time memory persistence, and virtual firmware sandbox.\n\nSelect a preset directive below or transmit your engineering command.",
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    },
  ]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<
    "ENGINEERING" | "ARCHITECTURE" | "ROBOTICS" | "SIMULATION"
  >("ENGINEERING");
  const [loading, setLoading] = useState(false);

  // Providers & Models
  const [providers, setProviders] = useState<Provider[]>([]);
  const [currentProvider, setCurrentProvider] = useState<string>("gemini");
  const [currentModel, setCurrentModel] = useState<string>("");
  const [latency, setLatency] = useState<number | null>(null);

  // Conversations
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConvId, setCurrentConvId] = useState<number | null>(null);

  // Safety Confirmation
  const [pendingConfirm, setPendingConfirm] =
    useState<PendingConfirmation | null>(null);

  // Memory
  const [memories, setMemories] = useState<MemoryFact[]>([]);
  const [showMemoryDialog, setShowMemoryDialog] = useState(false);
  const [newFact, setNewFact] = useState("");
  const [newFactCategory, setNewFactCategory] = useState("engineering");

  // Sandbox
  const [sandboxCode, setSandboxCode] = useState(
    `// 8051 Dual-Axis Solar Tracker: Quadrant ADC & Servo Routine
#include <reg51.h>
sbit ADC_CS = P2^0;
sbit ADC_RD = P2^1;
sbit ADC_WR = P2^2;
sbit SERVO_AZIMUTH = P1^0;

void sample_quadrant_sensors(unsigned char *az, unsigned char *el) {
    ADC_CS = 0;
    ADC_WR = 0;
    ADC_WR = 1;
    while(P3^2 == 1); // Wait for INTR
    ADC_RD = 0;
    *az = P0; // Read Azimuth differential
    ADC_RD = 1;
    ADC_CS = 1;
}`,
  );
  const [sandboxLang, setSandboxLang] = useState<"c" | "python" | "asm">("c");
  const [sandboxOutput, setSandboxOutput] = useState<string | null>(null);
  const [runningSandbox, setRunningSandbox] = useState(false);

  // Voice & UI
  const [isListening, setIsListening] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Initial Load: Fetch Providers, Conversations, and Memory
  useEffect(() => {
    fetchProviders();
    fetchConversations();
    checkPendingConfirmations();
    fetchMemories();

    const interval = setInterval(() => {
      checkPendingConfirmations();
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const fetchProviders = async () => {
    const t0 = performance.now();
    try {
      const res = await apiFetch("/providers");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: Provider[] = await res.json();
      setProviders(data);
      setLatency(Math.round(performance.now() - t0));

      if (data.length > 0) {
        // Preferred order: Groq -> Gemini -> OpenRouter -> First available
        const preferred =
          data.find((p) => p.id === "groq" && p.has_key) ||
          data.find((p) => p.id === "gemini" && p.has_key) ||
          data.find((p) => p.id === "openrouter" && p.has_key) ||
          data.find((p) => p.has_key) ||
          data[0];

        setCurrentProvider(preferred.id);
        setCurrentModel(preferred.default_model);
      }
    } catch (err: any) {
      console.warn("Providers fetch fallback:", err);
    }
  };

  const fetchConversations = async () => {
    try {
      const res = await apiFetch("/conversations");
      if (!res.ok) return;
      const data = await res.json();
      setConversations(data);
    } catch (err) {
      console.warn("Conversations fetch error:", err);
    }
  };

  const handleSelectConversation = async (cid: number) => {
    setCurrentConvId(cid);
    try {
      const res = await apiFetch(`/conversations/${cid}/messages`);
      if (!res.ok) return;
      const msgs = await res.json();
      if (msgs && msgs.length > 0) {
        setMessages(
          msgs.map((m: any) => ({
            role: m.role,
            content: m.content,
            timestamp: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          })),
        );
      }
    } catch (err) {
      console.warn("Load conversation messages error:", err);
    }
  };

  const handleCreateNewConversation = async () => {
    try {
      const res = await apiFetch("/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: `Session ${conversations.length + 1}` }),
      });
      if (res.ok) {
        const conv = await res.json();
        setCurrentConvId(conv.id);
        await fetchConversations();
        setMessages([
          {
            role: "assistant",
            content: `### New Session Initialized (#${conv.id})\nNeural context cleared. Ready for new engineering directives.`,
            timestamp: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
      }
    } catch (err) {
      console.warn("New conversation error:", err);
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, cid: number) => {
    e.stopPropagation();
    try {
      await apiFetch(`/conversations/${cid}`, { method: "DELETE" });
      await fetchConversations();
      if (currentConvId === cid) {
        setCurrentConvId(null);
        setMessages([
          {
            role: "assistant",
            content: "Conversation deleted. Ready for new input.",
            timestamp: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
      }
    } catch (err) {
      console.warn("Delete conversation error:", err);
    }
  };

  const checkPendingConfirmations = async () => {
    try {
      const res = await apiFetch("/confirm/pending");
      if (!res.ok) return;
      const items = await res.json();
      if (items && items.length > 0) {
        setPendingConfirm(items[0]);
      } else {
        setPendingConfirm(null);
      }
    } catch (err) {
      // Ignore poll error
    }
  };

  const handleConfirmationAction = async (action: "approve" | "deny") => {
    if (!pendingConfirm) return;
    try {
      await apiFetch("/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirmation_id: pendingConfirm.id,
          action,
        }),
      });
      setPendingConfirm(null);
      checkPendingConfirmations();
    } catch (err: any) {
      alert(`Safety confirmation failed: ${err.message}`);
    }
  };

  const fetchMemories = async () => {
    try {
      const res = await apiFetch("/memory");
      if (res.ok) {
        const facts = await res.json();
        setMemories(facts);
      }
    } catch (err) {
      console.warn("Memory fetch error:", err);
    }
  };

  const handleAddMemory = async () => {
    if (!newFact.trim()) return;
    try {
      await apiFetch("/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fact: newFact, category: newFactCategory }),
      });
      setNewFact("");
      fetchMemories();
    } catch (err: any) {
      alert(`Could not save memory: ${err.message}`);
    }
  };

  const handleDeleteMemory = async (fid: number) => {
    try {
      await apiFetch(`/memory/${fid}`, { method: "DELETE" });
      fetchMemories();
    } catch (err: any) {
      console.warn("Delete memory error:", err);
    }
  };

  const handleProviderChange = (pid: string) => {
    setCurrentProvider(pid);
    const prov = providers.find((p) => p.id === pid);
    if (prov) {
      setCurrentModel(prov.default_model);
    }
  };

  // Streaming Message Handler
  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || input;
    if (!textToSend.trim() || loading) return;

    const time = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    const userMsg: Message = {
      role: "user",
      content: textToSend,
      timestamp: time,
    };
    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setInput("");
    setLoading(true);

    // Context-enriched instruction
    const systemPrefix = `[Mode: ${mode}]`;
    const fullQuery = `${systemPrefix} ${textToSend}`;

    try {
      const res = await apiFetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: fullQuery,
          provider: currentProvider,
          model: currentModel,
          conversation_id: currentConvId,
        }),
      });

      if (!res.ok) {
        // Fallback to /chat non-streaming if stream returns status != 200
        const fallbackRes = await apiFetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: fullQuery,
            provider: currentProvider,
            conversation_id: currentConvId,
          }),
        });
        const fallbackData = await fallbackRes.json();
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              fallbackData.reply || fallbackData.error || "Execution complete.",
            timestamp: new Date().toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
        return;
      }

      // Stream reader
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No readable stream");
      const decoder = new TextDecoder("utf-8");
      let accumulated = "";
      let buffer = "";

      // Create initial placeholder assistant bubble
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "",
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            try {
              const payload = JSON.parse(trimmed.slice(6));
              if (payload.content || payload.delta) {
                accumulated += payload.content || payload.delta;
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === "assistant") {
                    last.content = accumulated;
                  }
                  return updated;
                });
              }
            } catch (e) {
              // Ignore incomplete chunks
            }
          }
        }
      }

      if (!accumulated) {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last && last.role === "assistant") {
            last.content = "Task routine completed nominal.";
          }
          return updated;
        });
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ Communication Error: ${err.message}`,
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } finally {
      setLoading(false);
      checkPendingConfirmations();
    }
  };

  // Run Virtual Sandbox Code
  const handleRunSandbox = async () => {
    setRunningSandbox(true);
    setSandboxOutput("Transmitting payload to execution sandbox...");
    try {
      const res = await apiFetch("/code/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: sandboxCode, language: sandboxLang }),
      });
      const data = await res.json();
      setSandboxOutput(
        `${data.output}\n\nExecution Time: ${data.executionTimeMs}ms | Exit Code: ${data.exitCode}`,
      );
    } catch (e: any) {
      setSandboxOutput(`Sandbox Execution Error: ${e.message}`);
    } finally {
      setRunningSandbox(false);
    }
  };

  // Web Speech STT
  const toggleListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition is not supported in this browser environment.");
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
      setIsListening(false);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
  };

  const copyToClipboard = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const speakText = (text: string) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/[*_#`]/g, "");
    const utter = new SpeechSynthesisUtterance(clean);
    utter.rate = 1.05;
    window.speechSynthesis.speak(utter);
  };

  return (
    <div className="flex h-screen w-screen bg-[#07090e] text-slate-100 overflow-hidden font-sans">
      {/* Safety Confirmation Dialog */}
      {pendingConfirm && (
        <Dialog open={true} onOpenChange={() => {}}>
          <DialogContent className="border-amber-500/50 bg-[#0d111c] text-white">
            <DialogHeader>
              <div className="flex items-center gap-2 text-amber-400 mb-2">
                <AlertTriangle className="w-5 h-5 animate-pulse" />
                <span className="font-mono text-xs font-bold tracking-widest uppercase">
                  Desktop Security Gate
                </span>
              </div>
              <DialogTitle className="text-lg">
                Authorize Tool Execution?
              </DialogTitle>
              <DialogDescription className="text-slate-300">
                The agent requested execution of command:
              </DialogDescription>
            </DialogHeader>

            <div className="bg-[#05070c] border border-slate-800 rounded-xl p-3 font-mono text-xs text-amber-300 overflow-x-auto my-2">
              <code>
                {pendingConfirm.command ||
                  JSON.stringify(pendingConfirm.arguments || {}, null, 2)}
              </code>
            </div>

            <DialogFooter className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => handleConfirmationAction("deny")}
              >
                Reject Directive
              </Button>
              <Button
                variant="destructive"
                onClick={() => handleConfirmationAction("approve")}
              >
                Authorize & Execute
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Memory Inspector Dialog */}
      <Dialog open={showMemoryDialog} onOpenChange={setShowMemoryDialog}>
        <DialogContent className="max-w-xl bg-[#0b0e17] border-slate-700">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-cyan-400" />
              <span>NEXUS Long-Term Memory Hub</span>
            </DialogTitle>
            <DialogDescription>
              Stored facts, project preferences, and persistent hardware
              configurations.
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-2 my-2">
            <input
              value={newFact}
              onChange={(e) => setNewFact(e.target.value)}
              placeholder="Remember fact (e.g. 8051 crystal is 11.0592 MHz)..."
              className="flex-1 bg-[#05070c] border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500"
            />
            <Button size="sm" onClick={handleAddMemory}>
              Store
            </Button>
          </div>

          <ScrollArea className="h-60 border border-slate-800 rounded-xl p-2 bg-[#05070c]/50">
            {memories.length === 0 ? (
              <div className="text-center text-xs text-slate-500 p-6">
                No facts registered in memory store.
              </div>
            ) : (
              memories.map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between p-2 hover:bg-slate-800/40 rounded-lg text-xs border-b border-slate-800/40"
                >
                  <div>
                    <div className="text-slate-200">{m.fact}</div>
                    <div className="text-[10px] text-cyan-400 font-mono">
                      {m.category} · {m.created_at}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteMemory(m.id)}
                    className="text-slate-500 hover:text-red-400 p-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Left Sidebar: Command Rail & Conversations */}
      <aside className="w-80 border-r border-slate-800/80 bg-[#0b0e17]/90 flex flex-col justify-between p-4 backdrop-blur-xl">
        <div className="flex flex-col gap-5 overflow-hidden">
          {/* Logo & Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-cyan-200 to-cyan-400 bg-clip-text text-transparent">
                  NEXUS AI
                </div>
                <div className="text-[10px] font-mono tracking-widest text-cyan-400 flex items-center gap-1.5 uppercase">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Active HUD
                </div>
              </div>
            </div>

            <Button
              size="icon"
              variant="outline"
              className="h-8 w-8 rounded-lg border-slate-800 bg-slate-900/60"
              onClick={handleCreateNewConversation}
              title="New Session"
            >
              <Plus className="w-4 h-4 text-cyan-400" />
            </Button>
          </div>

          {/* Operator Badge */}
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-3 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs">
              TB
            </div>
            <div className="overflow-hidden flex-1">
              <div className="text-xs font-semibold text-slate-200 truncate">
                Tejas Bargat
              </div>
              <div className="text-[10px] text-cyan-400 font-mono truncate">
                Lead Systems Architect
              </div>
            </div>
            <button
              onClick={() => setShowMemoryDialog(true)}
              className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-cyan-300 transition"
              title="Memory Hub"
            >
              <Database className="w-4 h-4" />
            </button>
          </div>

          {/* Provider & Model Selectors */}
          <div className="flex flex-col gap-2 bg-slate-900/40 border border-slate-800/60 p-3 rounded-xl">
            <div className="flex justify-between items-center text-[10px] font-mono uppercase tracking-wider text-slate-400">
              <span>Cognitive Engine</span>
              {latency && <span className="text-emerald-400">{latency}ms</span>}
            </div>
            <select
              value={currentProvider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full bg-[#05070c] border border-slate-800 rounded-lg py-1.5 px-2 text-xs font-mono text-cyan-300 outline-none cursor-pointer focus:border-cyan-500"
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label} {p.has_key ? "✓" : "(No Key)"}
                </option>
              ))}
            </select>

            {/* Model Subselect */}
            {providers.find((p) => p.id === currentProvider)?.suggested_models
              ?.length ? (
              <select
                value={currentModel}
                onChange={(e) => setCurrentModel(e.target.value)}
                className="w-full bg-[#05070c] border border-slate-800 rounded-lg py-1.5 px-2 text-[11px] font-mono text-slate-300 outline-none cursor-pointer"
              >
                {providers
                  .find((p) => p.id === currentProvider)
                  ?.suggested_models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
              </select>
            ) : null}
          </div>

          {/* Operating Mode Selector */}
          <div className="flex flex-col gap-1.5">
            <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase">
              Operational Mode
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {(
                [
                  "ENGINEERING",
                  "ARCHITECTURE",
                  "ROBOTICS",
                  "SIMULATION",
                ] as const
              ).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`text-[10px] font-mono py-1.5 px-2 rounded-lg border transition-all text-left flex items-center justify-between ${
                    mode === m
                      ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300 shadow-sm shadow-cyan-500/20"
                      : "bg-slate-900/40 border-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <span>{m}</span>
                  {mode === m && (
                    <span className="w-1 h-1 rounded-full bg-cyan-400"></span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Sessions List */}
          <div className="flex flex-col gap-1 flex-1 overflow-hidden">
            <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase flex justify-between items-center px-1">
              <span>Saved Sessions</span>
              <span className="text-slate-500">{conversations.length}</span>
            </div>
            <ScrollArea className="h-36 pr-2">
              <div className="flex flex-col gap-1">
                {conversations.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => handleSelectConversation(c.id)}
                    className={`group flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs cursor-pointer border transition-all ${
                      currentConvId === c.id
                        ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-200"
                        : "bg-slate-900/30 border-transparent hover:bg-slate-800/60 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <MessageSquare className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span className="truncate">
                        {c.title || `Session ${c.id}`}
                      </span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(e, c.id)}
                      className="opacity-0 group-hover:opacity-100 hover:text-red-400 p-0.5"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* System Diagnostics Footer */}
        <div className="border-t border-slate-800/80 pt-3 flex flex-col gap-1 text-[10px] font-mono text-slate-400">
          <div className="flex justify-between items-center">
            <span>Neural Core:</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Live
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Active Router:</span>
            <span className="text-cyan-400 truncate max-w-[130px]">
              {currentProvider}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Command & Chat Canvas */}
      <main className="flex-1 flex flex-col h-full bg-gradient-to-b from-[#07090e] via-[#090d16] to-[#07090e] relative overflow-hidden">
        {/* Header Bar */}
        <header className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-[#0b0e17]/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
            <span className="font-mono text-xs font-semibold tracking-wide text-slate-200 uppercase">
              Operational Stream // [{mode}]
            </span>
            <Badge variant="default" className="text-[10px]">
              {currentModel || currentProvider}
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleSendMessage(
                  "Analyze 8051 dual-axis solar tracker quadrant sensors and servo debounce routine",
                )
              }
              className="text-xs h-7 gap-1.5 border-slate-700 bg-slate-900/60"
            >
              <Sun className="w-3.5 h-3.5 text-amber-400" />
              <span>Solar Tracker</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleSendMessage(
                  "Evaluate ADC0804 sampling matrix and power rail brownout filter",
                )
              }
              className="text-xs h-7 gap-1.5 border-slate-700 bg-slate-900/60"
            >
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>ADC0804 Filter</span>
            </Button>
          </div>
        </header>

        {/* Message Log & Workspace */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col max-w-3xl ${m.role === "user" ? "ml-auto items-end" : "mr-auto items-start"}`}
            >
              <div className="flex items-center gap-2 mb-1 px-1">
                <span className="text-[10px] font-mono text-slate-500">
                  {m.timestamp}
                </span>
                <span
                  className={`text-[11px] font-mono uppercase font-semibold ${m.role === "user" ? "text-indigo-400" : "text-cyan-400"}`}
                >
                  {m.role === "user" ? "Operator Tejas" : "NEXUS Core"}
                </span>
              </div>
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap relative group ${
                  m.role === "user"
                    ? "bg-gradient-to-r from-indigo-600/90 to-indigo-700/90 text-white rounded-tr-none shadow-md shadow-indigo-500/10 border border-indigo-500/30"
                    : "bg-[#101524]/90 border border-slate-800 text-slate-200 rounded-tl-none shadow-xl shadow-black/40"
                }`}
              >
                {m.content}

                {/* Assistant Message Actions Toolbar */}
                {m.role === "assistant" && (
                  <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center gap-2">
                    <button
                      onClick={() => copyToClipboard(m.content, idx)}
                      className="text-slate-400 hover:text-cyan-300 text-[11px] font-mono flex items-center gap-1 transition"
                    >
                      {copiedIdx === idx ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                      <span>{copiedIdx === idx ? "Copied" : "Copy"}</span>
                    </button>
                    <button
                      onClick={() => speakText(m.content)}
                      className="text-slate-400 hover:text-cyan-300 text-[11px] font-mono flex items-center gap-1 transition"
                    >
                      <Volume2 className="w-3 h-3" />
                      <span>Read</span>
                    </button>
                    {m.content.includes("#include") ||
                    m.content.includes("def ") ||
                    m.content.includes("void ") ? (
                      <button
                        onClick={() => {
                          const match = m.content.match(
                            /```(?:c|cpp|python|asm)?([\s\S]*?)```/,
                          );
                          if (match) {
                            setSandboxCode(match[1].trim());
                          }
                        }}
                        className="text-cyan-400 hover:text-cyan-300 text-[11px] font-mono flex items-center gap-1 transition ml-auto"
                      >
                        <Code2 className="w-3 h-3" />
                        <span>Send to Sandbox</span>
                      </button>
                    ) : null}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 p-3 text-xs font-mono text-cyan-400 bg-cyan-950/20 border border-cyan-800/30 rounded-xl w-fit">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              Executing neural stream...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800/80 bg-[#090d16]/80 backdrop-blur-lg">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2 bg-[#0d121f] border border-slate-700/80 rounded-2xl p-2 shadow-2xl focus-within:border-cyan-500/60 focus-within:shadow-cyan-500/10 transition-all"
          >
            <button
              type="button"
              onClick={toggleListening}
              className={`p-2 rounded-xl transition ${
                isListening
                  ? "bg-red-500 text-white animate-pulse"
                  : "text-slate-400 hover:text-cyan-300 hover:bg-slate-800"
              }`}
              title={isListening ? "Stop listening" : "Voice dictation"}
            >
              <Mic className="w-4 h-4" />
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Transmit directive, firmware routine, or architecture query..."
              className="flex-1 bg-transparent px-2 text-sm text-slate-100 placeholder-slate-500 outline-none"
            />
            <Button
              type="submit"
              disabled={loading || !input.trim()}
              variant="gradient"
              className="h-9 w-9 p-0 rounded-xl"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </main>

      {/* Right Drawer: Virtual Code & Simulation Sandbox */}
      <aside className="w-96 border-l border-slate-800/80 bg-[#0b0e17]/95 flex flex-col p-4 backdrop-blur-xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
              Virtual Sandbox
            </span>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={sandboxLang}
              onChange={(e) => setSandboxLang(e.target.value as any)}
              className="bg-[#05070c] border border-slate-800 rounded px-1.5 py-0.5 text-[10px] font-mono text-slate-300 outline-none"
            >
              <option value="c">C (8051)</option>
              <option value="python">Python</option>
              <option value="asm">ASM</option>
            </select>
            <Button
              size="sm"
              onClick={handleRunSandbox}
              disabled={runningSandbox}
              className="h-7 text-xs bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/40"
            >
              <Play className="w-3 h-3 fill-current mr-1" />
              {runningSandbox ? "Running" : "Run"}
            </Button>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-2 py-3 overflow-hidden">
          <div className="text-[10px] font-mono text-slate-400 uppercase">
            Logic / Firmware Simulation
          </div>
          <textarea
            value={sandboxCode}
            onChange={(e) => setSandboxCode(e.target.value)}
            className="flex-1 w-full bg-[#05070c] border border-slate-800/90 rounded-xl p-3 font-mono text-xs text-cyan-300 outline-none resize-none focus:border-cyan-500/40"
            spellCheck={false}
          />

          {sandboxOutput && (
            <div className="h-44 bg-[#05070c] border border-slate-800 rounded-xl p-3 font-mono text-[11px] text-slate-300 overflow-y-auto whitespace-pre-wrap">
              {sandboxOutput}
            </div>
          )}
        </div>

        <div className="pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-500 flex justify-between">
          <span>Target: 8051 / ARM Core</span>
          <span>Simulation: Active</span>
        </div>
      </aside>
    </div>
  );
}
