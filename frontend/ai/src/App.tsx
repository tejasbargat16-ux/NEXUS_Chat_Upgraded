import React, { useState, useRef, useEffect } from 'react';
import { 
  Terminal, Cpu, Radio, Shield, Send, Mic, Play, 
  Layers, Code2, Sparkles, Sun, CheckCircle2, ChevronRight 
} from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'NEXUS Digital Command Center initialized. Neural systems operational for Lead Systems Architect Tejas Bargat. How may I assist your engineering directive today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<'ENGINEERING' | 'ARCHITECTURE' | 'ROBOTICS' | 'SIMULATION'>('ENGINEERING');
  const [loading, setLoading] = useState(false);
  const [sandboxCode, setSandboxCode] = useState('// 8051 Servo ADC Sampling Routine\nvoid sample_quadrant() {\n    ADC0804_CS = 0;\n    ADC0804_RD = 0;\n    val = P1;\n}');
  const [sandboxOutput, setSandboxOutput] = useState<string | null>(null);
  const [runningSandbox, setRunningSandbox] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || input;
    if (!textToSend.trim() || loading) return;

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg: Message = { role: 'user', content: textToSend, timestamp: time };
    setMessages(prev => [...prev, userMsg]);
    if (!customText) setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: textToSend, mode }),
      });
      const data = await res.json();
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: data.reply || 'Routine execution complete.', 
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
        }
      ]);
    } catch (err: any) {
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: `⚠️ Neural connection error: ${err.message}`, 
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSandbox = async () => {
    setRunningSandbox(true);
    try {
      const res = await fetch('/api/code/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: sandboxCode, language: 'c' }),
      });
      const data = await res.json();
      setSandboxOutput(data.output);
    } catch (e: any) {
      setSandboxOutput(`Execution Error: ${e.message}`);
    } finally {
      setRunningSandbox(false);
    }
  };

  const handleVoiceTest = async () => {
    const query = 'Run system diagnostics on 8051 solar tracker';
    try {
      const res = await fetch('/api/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: query }),
      });
      const data = await res.json();
      handleSendMessage(data.transcript);
    } catch (e) {
      handleSendMessage(query);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#07090e] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Command Rail */}
      <aside className="w-80 border-r border-slate-800/80 bg-[#0b0e17]/90 flex flex-col justify-between p-5 backdrop-blur-xl">
        <div className="flex flex-col gap-6">
          {/* Logo & Status */}
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
                Command Center
              </div>
            </div>
          </div>

          {/* Operator Badge */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-sm">
              TB
            </div>
            <div className="overflow-hidden">
              <div className="text-xs font-semibold text-slate-200 truncate">Tejas Bargat</div>
              <div className="text-[10px] text-slate-400 font-mono truncate">Lead Systems Architect</div>
            </div>
          </div>

          {/* Operating Mode Selector */}
          <div className="flex flex-col gap-2">
            <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase">Operational Mode</div>
            <div className="grid grid-cols-2 gap-1.5">
              {(['ENGINEERING', 'ARCHITECTURE', 'ROBOTICS', 'SIMULATION'] as const).map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`text-[11px] font-mono py-2 px-2.5 rounded-lg border transition-all text-left flex items-center justify-between ${
                    mode === m 
                      ? 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300 shadow-sm shadow-cyan-500/20' 
                      : 'bg-slate-900/50 border-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <span>{m}</span>
                  {mode === m && <span className="w-1 h-1 rounded-full bg-cyan-400"></span>}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Hardware Presets */}
          <div className="flex flex-col gap-2">
            <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase">Hardware Directives</div>
            <button 
              onClick={() => handleSendMessage('Analyze 8051 solar tracker dual-axis sensor differential and servo hysteresis')}
              className="text-xs p-2.5 rounded-lg border border-slate-800 bg-slate-900/40 hover:bg-slate-800/60 hover:border-slate-700 transition flex items-center gap-2 text-slate-300 text-left"
            >
              <Sun className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="truncate">8051 Dual-Axis Solar Tracker</span>
            </button>
            <button 
              onClick={() => handleSendMessage('Design ADC0804 LDR sampling matrix with 5V power brownout decoupling')}
              className="text-xs p-2.5 rounded-lg border border-slate-800 bg-slate-900/40 hover:bg-slate-800/60 hover:border-slate-700 transition flex items-center gap-2 text-slate-300 text-left"
            >
              <Layers className="w-4 h-4 text-cyan-400 shrink-0" />
              <span className="truncate">ADC0804 Sampling Decoupling</span>
            </button>
          </div>
        </div>

        {/* System Diagnostics Footer */}
        <div className="border-t border-slate-800/80 pt-4 flex flex-col gap-2 text-[11px] font-mono text-slate-400">
          <div className="flex justify-between items-center">
            <span>Neural Engine:</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Online
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span>Core Model:</span>
            <span className="text-cyan-400">gemini-2.5-flash</span>
          </div>
          <div className="flex justify-between items-center">
            <span>Port:</span>
            <span className="text-slate-300">3000</span>
          </div>
        </div>
      </aside>

      {/* Main Command & Chat Canvas */}
      <main className="flex-1 flex flex-col h-full bg-gradient-to-b from-[#07090e] via-[#090d16] to-[#07090e] relative">
        {/* Header Bar */}
        <header className="h-16 border-b border-slate-800/80 px-6 flex items-center justify-between bg-[#0b0e17]/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
            <span className="font-mono text-sm font-semibold tracking-wide text-slate-200 uppercase">
              Operational Stream // [{mode}]
            </span>
          </div>

          <div className="flex items-center gap-3">
            <a 
              href="https://ai.studio/apps/2f448cd5-0e62-4173-bb8f-d0da48de10cf"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 text-xs font-mono hover:bg-cyan-500/20 transition shadow-sm shadow-cyan-500/10"
              title="Open in Google AI Studio"
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>AI Studio</span>
            </a>
            <button 
              onClick={handleVoiceTest}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-mono hover:bg-indigo-500/20 transition"
              title="Trigger simulated voice telemetry directive"
            >
              <Mic className="w-3.5 h-3.5 text-indigo-400" />
              <span>Voice Directive</span>
            </button>
            <div className="h-4 w-[1px] bg-slate-800"></div>
            <div className="text-xs font-mono text-slate-400 flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-cyan-400" /> 42ms
            </div>
          </div>
        </header>

        {/* Message Log & Workspace */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5">
          {messages.map((m, idx) => (
            <div 
              key={idx} 
              className={`flex flex-col max-w-3xl ${m.role === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1.5 px-1">
                <span className="text-[10px] font-mono text-slate-400">{m.timestamp}</span>
                <span className={`text-[11px] font-mono uppercase font-semibold ${m.role === 'user' ? 'text-indigo-400' : 'text-cyan-400'}`}>
                  {m.role === 'user' ? 'Operator Tejas' : 'NEXUS Neural Core'}
                </span>
              </div>
              <div 
                className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === 'user' 
                    ? 'bg-gradient-to-r from-indigo-600/80 to-indigo-700/80 text-white rounded-tr-none shadow-md shadow-indigo-500/10 border border-indigo-500/30' 
                    : 'bg-[#101524]/90 border border-slate-800 text-slate-200 rounded-tl-none shadow-xl shadow-black/40'
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 p-3 text-xs font-mono text-cyan-400 bg-cyan-950/20 border border-cyan-800/30 rounded-xl w-fit">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              Synthesizing engineering neural routine...
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-5 border-t border-slate-800/80 bg-[#090d16]/80 backdrop-blur-lg">
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
            className="flex items-center gap-3 bg-[#0d121f] border border-slate-700/80 rounded-2xl p-2.5 shadow-2xl focus-within:border-cyan-500/60 focus-within:shadow-cyan-500/10 transition-all"
          >
            <input 
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter technical query, schematic request, or firmware directive..."
              className="flex-1 bg-transparent px-3 text-sm text-slate-100 placeholder-slate-500 outline-none"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-10 h-10 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 flex items-center justify-center text-white disabled:opacity-30 disabled:cursor-not-allowed transition shadow-md shadow-cyan-500/20"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </main>

      {/* Right Drawer: Virtual Code & Simulation Sandbox */}
      <aside className="w-96 border-l border-slate-800/80 bg-[#0b0e17]/95 flex flex-col p-5 backdrop-blur-xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">Virtual Sandbox</span>
          </div>
          <button 
            onClick={handleRunSandbox}
            disabled={runningSandbox}
            className="px-3 py-1 bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 rounded-lg text-xs font-mono flex items-center gap-1.5 hover:bg-emerald-500/25 transition disabled:opacity-50"
          >
            <Play className="w-3 h-3 fill-current" />
            {runningSandbox ? 'Executing...' : 'Run'}
          </button>
        </div>

        <div className="flex-1 flex flex-col gap-3 py-4 overflow-hidden">
          <div className="text-[11px] font-mono text-slate-400">Firmware Logic (C / ASM / TypeScript)</div>
          <textarea 
            value={sandboxCode}
            onChange={(e) => setSandboxCode(e.target.value)}
            className="flex-1 w-full bg-[#05070c] border border-slate-800/90 rounded-xl p-3 font-mono text-xs text-cyan-300 outline-none resize-none focus:border-cyan-500/40"
          />

          {sandboxOutput && (
            <div className="h-40 bg-[#05070c] border border-slate-800 rounded-xl p-3 font-mono text-[11px] text-slate-300 overflow-y-auto whitespace-pre-wrap">
              {sandboxOutput}
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-800 text-[10px] font-mono text-slate-500 flex justify-between">
          <span>Target Architecture: 8051 / ARM</span>
          <span>Simulation Engine: Active</span>
        </div>
      </aside>
    </div>
  );
}
