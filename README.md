# NEXUS v2 — Desktop AI Assistant

A cross-platform (Windows primary, macOS/Linux supported) desktop AI assistant featuring a unified multi-provider LLM client with fallback, native function/tool calling agent loop, long-term memory (SQLite FTS5), smart task routing, desktop control tools with a 3-tier safety layer, push-to-talk voice, and a native glassmorphic HUD window.

---

## ⚡ Features

- **Unified Multi-Provider LLM Client (`core/llm.py`)**: One OpenAI-compatible client supporting Groq, Gemini, OpenRouter, OpenAI, Mistral, and Cohere with exponential backoff and automatic provider fallback.
- **Native Tool Calling Agent Loop (`core/agent.py`)**: Multi-step agent loop using OpenAI tool/function schemas rather than fragile text parsing.
- **`@tool` Decorator & Registry (`core/tools.py`)**: Auto-generates JSON Schema parameters directly from Python type annotations and docstrings.
- **Long-Term Memory (`core/memory.py`)**: Persistent SQLite FTS5 store for user facts, goals, and preferences with deduplication and relevant memory recall.
- **Smart Model & Task Router (`core/router.py`)**: Classifies queries into `code`, `study`, `vision`, or `chat` and selects the optimal provider chain from `config.yaml`.
- **Cross-Platform OS Layer (`desktop/os_layer.py`)**: Safely controls apps, folders, URLs, screen capture, volume, and clipboard across Windows, macOS, and Linux without `shell=True`.
- **Three-Tier Safety System (`desktop/safety.py`)**:
  - `SAFE`: Read-only, search, screenshots, apps (auto-executed).
  - `CONFIRM`: File modifications, closing apps, shell execution (requires explicit user approval).
  - `REFUSED`: Destructive commands (`rm -rf`, `format`, `del /s C:\`, fork bombs) blocked unconditionally.
- **Push-to-Talk Voice (`desktop/voice.py`)**: Hotkey-triggered recording with STT (Whisper) and offline TTS (pyttsx3).
- **Native Window & System Tray (`desktop/ui.py`)**: Embedded glassmorphic HUD in a native window (`pywebview`) with persistent system tray controls (`pystray`).
- **Single Entry Point (`main.py`)**: Everything runs from one clean CLI.

---

## 🚀 Quickstart

### 1. Installation

Python 3.11+ is supported. Install dependencies:

```bash
# Core dependencies
pip install -r requirements.txt

# Native desktop window, tray, and audio extensions
pip install -r requirements-desktop.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and insert your API keys:

```bash
cp .env.example .env
```

```env
GROQ_API_KEY="your_groq_key_here"
GEMINI_API_KEY="your_gemini_key_here"
OPENROUTER_API_KEY="your_openrouter_key_here"
OPENAI_API_KEY="your_openai_key_here"
NEXUS_API_KEY="auto-generated-on-first-run-if-empty"
```

### 3. Run NEXUS v2

```bash
# Launch Native Desktop Window (pywebview) + Tray
python main.py

# Launch in default browser instead of native window
python main.py --browser

# Run terminal interactive chat
python main.py --cli

# Run hands-free voice task assistant
python main.py --task

# Run API backend only (headless)
python main.py --server-only

# Verify module integrity
python main.py --check
```

---

## 🧪 Testing & Evaluation

### Unit Test Suite

Run all 38 automated test suites covering security, LLM clients, fallback, tools, memory, router, and desktop safety:

```bash
python -m pytest tests/ -v
```

### 20-Question Evaluation Benchmark

Run the standardized 20-question evaluation suite covering coding, ECE/GATE theory, safety tiers, and memory recall:

```bash
python evals/run_evals.py
```

---

## 📁 Repository Structure

```
NEXUS_Chat_Upgraded/
├── main.py                    # Single entrypoint for all modes
├── config.yaml                # Providers, models, routes & fallback chains
├── requirements.txt           # Core dependencies
├── requirements-desktop.txt   # Native desktop UI & voice dependencies
├── .env.example               # Environment variables template
├── core/                      # Unified client, agent loop, tools, memory, router
├── desktop/                   # Cross-platform OS layer, safety, voice, pywebview UI
├── frontend/static/           # Glassmorphic HUD interface (HTML5/CSS3/JS)
├── launchers/                 # Mode runners (CLI, voice task)
├── tests/                     # 38 pytest unit & security tests
├── evals/                     # 20-question evaluation benchmark
└── docs/                      # Architecture & API documentation
```

---

## 🔒 Security Guarantees

- **No Hardcoded Keys**: API keys are loaded solely from environment variables or `.env`. If `NEXUS_API_KEY` is not found, a cryptographically secure token is generated via `secrets.token_urlsafe(32)`.
- **Localhost Binding**: API strictly binds to `127.0.0.1` and CORS is restricted to localhost origins only.
- **Header Authentication**: Gemini API keys are sent via `x-goog-api-key` header rather than exposed in query strings.
- **No Unsanitized Shell Calls**: `shell=True` has been completely eliminated in favor of explicit argument lists.
