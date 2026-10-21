<p align="center">
  <img src="assets/banner.png" alt="NEXUS Chat: One Interface, Multiple Intelligences" width="100%">
</p>

# ⚡ NEXUS Chat [Upgraded]

**Your All-in-One AI Assistant on Android & Cross-Platform Desktop**

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/API-Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/DB-SQLite%20FTS5-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"></a>
  <a href="https://termux.dev/"><img src="https://img.shields.io/badge/Platform-Termux%20%7C%20Android-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Platform"></a>
  <a href="https://github.com/tejasbargat16-ux/NEXUS_Chat_Upgraded"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License"></a>
</p>

> **"One App. Multiple Minds. Infinite Possibilities."**  
> *Built for Android & Cross-Platform Desktop — Fast • Smart • Powerful.*

<p align="center">
  <img src="assets/overview.png" alt="NEXUS Chat Upgraded: System Overview and Architecture" width="100%">
</p>

---

## ✨ Key Pillars & Features

| Feature | Details |
|---|---|
| 🔀 **Multi-LLM Routing** | Unified provider routing across **Groq**, **Gemini**, **OpenRouter**, **OpenAI (ChatGPT)**, **Claude**, **Llama**, **Perplexity**, **Mistral**, and **Cohere** with automatic exponential fallback |
| 🌐 **Real Web Search** | Real-time fresh context retrieval using DuckDuckGo and Tavily API |
| 🎙️ **Voice Mode (I/O)** | Push-to-talk natural speech input with Whisper STT and offline/online TTS (`pyttsx3` / `termux-tts-speak`) |
| 🧩 **Plugin & Tool Calling System** | Autonomous `@tool` decorated functions auto-generating JSON Schemas for file operations, app control, system actions, and web browsing |
| 🧠 **Persistent SQLite FTS5 Memory** | Long-term memory store for user facts, preferences, and goals with contextual recall (`/remember`, `/profile`, `/forget`) |
| 🛡️ **Three-Tier Safety Layer** | Built-in security governor categorizing commands into `SAFE` (auto-run), `CONFIRM` (user prompt), and `REFUSED` (destructive command blocklist) |
| 🖥️ **Universal Deployment** | Runs natively in **Android Termux** terminal CLI, desktop native Arc Reactor HUD (`pywebview` + system tray), browser UI, or headless REST API |
| 📊 **Real-Time Telemetry & J.A.R.V.I.S. Engine** | Live CPU, RAM, Battery, Disk metrics, executive morning briefings, and background timers |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph UI ["User Interfaces"]
        CLI["Terminal CLI (Termux / Desktop)"]
        Voice["Hands-Free Voice Task Assistant"]
        HUD["Arc Reactor HUD (pywebview / Web UI)"]
        API["REST API (Flask / 127.0.0.1)"]
    end

    subgraph Core ["NEXUS Core Engine"]
        Main["main.py Launcher"]
        Router["Smart Router (core/router.py)"]
        Agent["Agent Loop (core/agent.py)"]
        Tools["Tool Registry (core/tools.py)"]
        Memory[("SQLite FTS5 Memory (core/memory.py)")]
        LLM["Unified Multi-Provider Client (core/llm.py)"]
    end

    subgraph Safety ["Security & OS Layer"]
        Gov{"Three-Tier Safety Governor"}
        Safe["SAFE: Read-only, Search, Screenshots"]
        Confirm["CONFIRM: File edits, App close, Shell"]
        Refuse["REFUSED: Block destructive commands"]
        OS["Cross-Platform OS Layer (desktop/os_layer.py)"]
    end

    subgraph Providers ["Supported LLM Backends"]
        Groq["Groq (Llama / Mixtral)"]
        Gemini["Google Gemini"]
        OpenRouter["OpenRouter (Free / Pro models)"]
        OpenAI["OpenAI (GPT-4o / o3-mini)"]
        Claude["Anthropic Claude"]
        Llama["Meta Llama"]
        Perplexity["Perplexity Web Reasoning"]
        Mistral["Mistral AI"]
        Cohere["Cohere Command-R"]
    end

    CLI --> Main
    Voice --> Main
    HUD --> Main
    API --> Main

    Main --> Agent
    Agent --> Router
    Router --> LLM
    LLM --> Providers

    Agent --> Tools
    Tools --> Gov
    Gov -->|Auto| Safe --> OS
    Gov -->|Prompt User| Confirm --> OS
    Gov -->|Deny| Refuse

    Agent --> Memory
```

---

## 🚀 Quickstart Guide

### 📱 Android / Termux Setup

```bash
# 1. Update and install base packages
pkg update && pkg install python git termux-api -y

# 2. Clone the repository
git clone https://github.com/tejasbargat16-ux/NEXUS_Chat_Upgraded.git
cd NEXUS_Chat_Upgraded

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env

# 5. Launch terminal CLI
python main.py --cli
```

### 💻 Desktop Setup (Windows / macOS / Linux)

```bash
# 1. Clone repository
git clone https://github.com/tejasbargat16-ux/NEXUS_Chat_Upgraded.git
cd NEXUS_Chat_Upgraded

# 2. Install core and desktop GUI / audio extensions
pip install -r requirements.txt
pip install -r requirements-desktop.txt

# 3. Setup environment variables
cp .env.example .env
```

Edit `.env` with your API keys (you only need one provider to start; NEXUS auto-selects available providers):

```env
GROQ_API_KEY="your_groq_key"
GEMINI_API_KEY="your_gemini_key"
OPENROUTER_API_KEY="your_openrouter_key"
OPENAI_API_KEY="your_openai_key"
TAVILY_API_KEY="your_tavily_key"      # Optional: for web search
NEXUS_API_KEY="auto-generated-if-empty"
```

---

## ▶️ Running Modes

`main.py` provides a single unified entry point for all operating modes:

```bash
# 1. Launch Native Desktop Window (pywebview) + System Tray (Default)
python main.py

# 2. Launch in Browser (Localhost Web HUD)
python main.py --browser

# 3. Run Interactive Terminal CLI (Optimized for Termux)
python main.py --cli

# 4. Run Dedicated Hands-Free Voice Assistant
python main.py --task

# 5. Run Headless REST API Server
python main.py --server-only

# 6. Verify System & Dependency Integrity
python main.py --check
```

---

## ⌨️ Interactive CLI Commands

| Command | Action |
|---|---|
| `/new` | Start a fresh chat conversation |
| `/sessions` | List saved conversation history |
| `/load <id>` | Resume a previous conversation |
| `/remember <fact>` | Store a fact or preference in persistent SQLite memory |
| `/profile` | Display all saved user profile facts |
| `/forget all` | Wipe stored user profile facts |
| `/provider <name>` | Switch active LLM provider (`groq`, `gemini`, `openrouter`, `openai`, `mistral`, `cohere`) |
| `/model <name>` | Change model under current provider |
| `/models` | View suggested models for active provider |
| `/voice on` / `/voice off` | Toggle spoken output and push-to-talk mic input |
| `/task` | Launch hands-free voice task assistant |
| `/search <query>` | Trigger instant web search |
| `/image <prompt>` | Generate images via Pollinations.ai or Gemini |
| `/clear` | Clear terminal screen |
| `/exit` | Exit application |

---

## 🌐 REST API Endpoints

The built-in Flask API server (`desktop/api.py`) runs at `http://127.0.0.1:5000`:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Service status, uptime, and active version |
| `/chat` | `POST` | Agent chat with tool calling, smart routing & memory |
| `/chat/stream` | `POST` | Server-Sent Events (SSE) streaming chat |
| `/confirm/pending` | `GET` | Retrieve pending CONFIRM-tier action requests |
| `/confirm` | `POST` | Approve or deny a pending action |
| `/tools` | `GET` | List all registered tool JSON Schemas |
| `/memory` | `GET` / `POST` | Query or save long-term SQLite facts |
| `/system/telemetry` | `GET` | Real-time CPU, RAM, Battery, and Disk diagnostics |
| `/system/action` | `POST` | Perform OS actions (lock workstation, volume, screenshot) |
| `/jarvis/briefing` | `GET` | Daily executive morning brief |
| `/jarvis/timers` | `GET` / `POST` | Inspect and schedule background timers |

---

## 🧪 Testing & Evaluation

### Automated Unit & Security Tests (38 tests)
```bash
python -m pytest -v
```

### 20-Question Evaluation Benchmark
Standardized evaluation assessing code synthesis, ECE theory, safety blocklists, and memory recall:
```bash
python evals/run_evals.py
```

---

## 📁 Repository Structure

```
NEXUS_Chat_Upgraded/
├── assets/                     # Visual banners & architecture overviews
│   ├── banner.png              # Header visual poster
│   └── overview.png            # Android & system architecture graphic
├── config.yaml                 # Providers, models, routes & fallback chains
├── main.py                     # Unified entry point for all modes
├── requirements.txt            # Core dependencies
├── requirements-desktop.txt    # Desktop GUI, tray, and audio extensions
├── .env.example                # Environment configuration template
├── core/                       # Core engine: LLM client, agent loop, tools, memory, router
├── desktop/                    # OS layer, safety governor, voice, native UI, Flask API
├── frontend/                   # Web HUD and React frontend
├── launchers/                  # Mode launchers (CLI, voice task, desktop)
├── tests/                      # Automated test suite (38 unit & security tests)
├── evals/                      # Standardized evaluation benchmark
└── docs/                       # Architecture and API documentation
```

---

## 🛡️ Security Guarantees

- **No Hardcoded Keys**: API keys are isolated in `.env` and environment variables. If `NEXUS_API_KEY` is omitted, a 32-byte secure token is generated automatically.
- **Localhost Bound**: The API server strictly binds to `127.0.0.1` with restricted CORS.
- **No Unsanitized Shell Calls**: `shell=True` has been completely eliminated in favor of explicit argument arrays.
- **Three-Tier Safety Filter**: Dangerous commands (`rm -rf`, format disks, fork bombs) are refused unconditionally.

---

## 👤 Author

**Tejas Bargat**  
*2nd-year B.Tech ECE (Minor in CSE), TGPCET Nagpur*  
*“Built by Tejas 👑 — For a Smarter Tomorrow”*  

[![GitHub](https://img.shields.io/badge/GitHub-Profile-181717?style=flat-square&logo=github)](https://github.com/tejasbargat16-ux)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/tejas-bargat-9ab8523b0)
[![Repository](https://img.shields.io/badge/Repository-NEXUS__Chat__Upgraded-blue?style=flat-square&logo=git)](https://github.com/tejasbargat16-ux/NEXUS_Chat_Upgraded)

---

⭐ If this project helped or inspired you, consider starring the repo!
