# NEXUS System Architecture & Project Organization

The codebase is organized into clean, dedicated sections separating core AI services, autonomous agents, user interfaces, standalone launchers, and documentation.

## Project Structure Overview

```
NEXUS_Chat_Upgraded/
│
├── 📁 core/                   # AI Backends, Storage & System Services
│   ├── __init__.py           # Package init & auto-path setup
│   ├── api.py                # Flask REST API backend server (port 8000)
│   ├── db.py                 # SQLite conversation & history persistence
│   ├── providers.py          # Multi-provider routing (Groq, Gemini, OpenRouter, OpenAI)
│   ├── identity.py           # System prompts, persona & instruction guidelines
│   ├── profile.py            # Long-term user profile & memory facts
│   ├── search.py             # Tavily & DuckDuckGo web search engine
│   ├── imagegen.py           # Pollinations & Gemini image synthesis
│   ├── voice.py              # Cross-platform TTS & microphone audio engine
│   └── local_llm.py          # Offline local llama.cpp / GGUF model bridge
│
├── 📁 agents/                 # Autonomous Intelligence & Automation
│   ├── __init__.py           # Package init & auto-path setup
│   ├── agent.py              # Safe system command execution engine & guardrails
│   ├── desktop_assistant.py  # Voice desktop automation (apps, files, tabs, indexing)
│   └── Nexus_task.py         # Autonomous hands-free voice task assistant
│
├── 📁 launchers/              # Dedicated Launchers & Entrypoints
│   ├── __init__.py
│   ├── launch_desktop.py     # Desktop Studio (starts API + frameless app window)
│   ├── launch_cli.py         # Terminal interactive chat REPL
│   └── launch_task.py        # Dedicated hands-free voice task launcher
│
├── 📁 frontend/               # User Interfaces & Web Dashboards
│   ├── static/               # NEXUS Studio Desktop HTML5/CSS/JS frontend
│   │   └── index.html        # Glassmorphic cybernetic desktop HUD interface
│   └── ai/                   # NEXUS Command Center React Web App
│       ├── package.json      # React 19 + TypeScript + Vite + TailwindCSS 4
│       ├── server.ts         # Express proxy server (port 3000)
│       └── src/              # React components & UI state
│
├── 📁 docs/                   # Documentation & References
│   ├── ARCHITECTURE.md       # This file: codebase layout & module specifications
│   ├── API_README.md         # Full REST API endpoints specification
│   └── MASTER_PROMPT_REFERENCE.md # System prompt engineering & context rules
│
├── 📄 Root Entrypoints (Backward-compatible runners):
│   ├── main.py               # Unified application runner (`python main.py`)
│   ├── nexus_desktop.py      # Desktop Studio launcher (`python nexus_desktop.py`)
│   ├── nexuschat.py          # Terminal CLI launcher (`python nexuschat.py`)
│   ├── api.py                # REST API server launcher (`python api.py`)
│   ├── desktop_assistant.py  # Voice Assistant launcher
│   └── Nexus_task.py         # Voice Task launcher
│
└── 📄 Configuration & Environment:
    ├── .env                  # API keys (Groq, Gemini, OpenRouter, etc.)
    ├── .env.example          # Sample environment configuration template
    ├── .gitignore            # Git ignore rules
    └── requirements.txt      # Python dependencies list
```

---

## Section Details

### 1. `core/` — Core AI & Services
- **`providers.py`**: Dispatches requests across Groq, Gemini, OpenRouter, OpenAI, Mistral, and Cohere using lightweight `requests`.
- **`db.py`**: SQLite database manager stored at `~/.nexuschat/history.db` for conversations and message logs.
- **`identity.py`**: High-performance system prompt enforcing prompt context and execution instructions.
- **`profile.py`**: Manages personal profile facts stored persistently across chat sessions.
- **`search.py`**: Live web searches using Tavily API with DuckDuckGo scrape fallback.
- **`imagegen.py`**: Image generation via Pollinations.ai or Gemini image models.
- **`voice.py`**: Text-to-Speech (pyttsx3 / Termux) and Speech-to-Text audio capture.
- **`local_llm.py`**: Offline fallback using `llama-cli` and local GGUF models.
- **`api.py`**: Flask REST API serving endpoints for chats, providers, images, and static frontend.

### 2. `agents/` — Agents & Desktop Automation
- **`desktop_assistant.py`**: Deep file and folder indexing, smart app opening, web browsing, tab closure, and NLP intent classification.
- **`Nexus_task.py`**: Continuous voice listening loop with intelligent routing between system actions and AI reasoning.
- **`agent.py`**: Tool and command execution with safety regex filters and human-in-the-loop approval.

### 3. `frontend/` — Client Interfaces
- **`frontend/static/`**: Desktop Studio interface served directly by Flask at `http://127.0.0.1:8000`. Features real-time Markdown rendering, session history, voice controls, and inspector pane.
- **`frontend/ai/`**: Advanced React 19 + TypeScript + Vite + TailwindCSS 4 digital command center with simulation sandbox and telemetry.

### 4. `launchers/` — Entrypoint Scripts
- **`launchers/launch_desktop.py`**: Native-like app mode window launcher using MS Edge / Chrome.
- **`launchers/launch_cli.py`**: Interactive terminal REPL with Rich terminal formatting.
- **`launchers/launch_task.py`**: Voice task assistant launcher.

### 5. `docs/` — Specifications & Guides
- Documentation, API references, and master prompts are isolated from executable code.
