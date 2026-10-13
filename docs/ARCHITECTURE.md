# NEXUS v2 — System Architecture & Design Specification

NEXUS v2 is a cross-platform (Windows primary, macOS/Linux supported) desktop AI assistant with native tool/function calling, long-term FTS5 memory, multi-provider LLM fallback, a 3-tier safety layer, and a native window interface.

```
+-------------------------------------------------------------------------+
|                        NEXUS Studio UI (pywebview)                      |
|                 Glassmorphic HUD Frontend (Vanilla HTML/CSS/JS)         |
+------------------------------------+------------------------------------+
                                     | REST / SSE / Events
+------------------------------------v------------------------------------+
|                         desktop/api.py (Flask Gateway)                  |
|          Binds to 127.0.0.1:5000 | Strict Localhost CORS | Secrets Auth |
+------------------------------------+------------------------------------+
                                     |
+------------------------------------v------------------------------------+
|                         core/agent.py (Agent Loop)                      |
|                  Iterative Tool Execution (max_steps: 6)                |
+-------------------+-----------------+-------------------+---------------+
                    |                 |                   |
                    v                 v                   v
            +---------------+ +---------------+   +---------------+
            | core/router.py| | core/tools.py |   |core/memory.py |
            | Task Classifier| | @tool Registry|   | SQLite FTS5   |
            | Code/Study/...| | JSON Schemas  |   | Dedup/Recall  |
            +-------+-------+ +-------+-------+   +---------------+
                    |                 |
                    v                 v
            +---------------+ +---------------+
            |  core/llm.py  | |desktop/safety |
            | Unified Client| | 3-Tier Guard  |
            | Fallback Chain| | Safe/Confirm/ |
            | Groq/Gemini/..| | Refused       |
            +---------------+ +-------+-------+
                                      |
                                      v
                              +---------------+
                              |desktop/os_layr|
                              | Cross-Platform|
                              | No shell=True |
                              +---------------+
```

---

## Directory Layout

```
NEXUS_Chat_Upgraded/
├── main.py                    # Unified application runner
├── config.yaml                # Model, route, provider, and fallback configuration
├── requirements.txt           # Core Python dependencies
├── requirements-desktop.txt   # Native desktop dependencies (pywebview, pystray, etc.)
├── .env.example               # Environment variables template
├── README.md                  # Quickstart, setup, and usage documentation
│
├── core/                      # Foundation Layer
│   ├── config.py              # Configuration loader & validator
│   ├── llm.py                 # Unified OpenAI-compatible multi-provider client
│   ├── agent.py               # Tool-calling agent loop
│   ├── tools.py               # @tool decorator & function schema generator
│   ├── memory.py              # SQLite FTS5 long-term memory store
│   ├── router.py              # Smart task classifier & route selector
│   ├── db.py                  # Conversation persistence
│   ├── identity.py            # System prompts & core persona
│   ├── search.py              # Tavily & DuckDuckGo web search
│   ├── imagegen.py            # Pollinations & Gemini image generation
│   ├── voice.py               # Audio recording & text-to-speech
│   └── local_llm.py           # Offline local GGUF/llama.cpp bridge
│
├── desktop/                   # Desktop Automation & Safety
│   ├── os_layer.py            # Cross-platform OS abstraction (Windows/macOS/Linux)
│   ├── safety.py              # 3-tier safety execution system
│   ├── tools.py               # Desktop tools registered via @tool
│   ├── voice.py               # Push-to-talk voice coordinator
│   ├── ui.py                  # Native window (pywebview) + system tray (pystray)
│   └── api.py                 # Local Flask gateway (port 5000)
│
├── frontend/                  # Web HUD
│   └── static/                # Cybernetic glassmorphic interface
│       └── index.html         # Single-page interface
│
├── launchers/                 # Mode Launchers
│   ├── launch_cli.py          # Interactive terminal chat
│   ├── launch_desktop.py      # Desktop launcher helper
│   └── launch_task.py         # Hands-free voice assistant
│
├── tests/                     # Automated Test Suites (38+ tests)
│   ├── test_security.py       # Security fix verifications
│   ├── test_llm.py            # Multi-provider client & fallback tests
│   ├── test_tools.py          # @tool decorator & execution tests
│   ├── test_agent.py          # Tool-calling agent loop tests
│   ├── test_memory.py         # SQLite FTS5 memory tests
│   ├── test_router.py         # Task classifier tests
│   └── test_desktop.py        # Safety tiers, OS layer & API tests
│
└── evals/                     # Quality Benchmarks
    ├── questions.json         # 20 standardized domain evaluation questions
    └── run_evals.py           # Evaluation runner script (100% pass rate)
```

---

## 3-Tier Safety System

Desktop operations are protected by `desktop/safety.py`:

| Tier | Policy | Operations |
|------|--------|------------|
| **SAFE** | Auto-executed | `open_application`, `take_screenshot`, `set_volume`, `web_search`, `read_clipboard`, `open_folder`, `open_website`, `list_windows`, `recall_memory` |
| **CONFIRM** | Requires user approval | `close_application`, `shell_command`, `lock_screen`, `write_clipboard`, `write_file`, `delete_file` |
| **REFUSED** | Blocked permanently | Irreversibly destructive commands (`rm -rf /`, `format`, `del /s C:\`, fork bombs, unknown actions) |

---

## Unified Multi-Provider LLM Client

All models and fallback routes are declared in `config.yaml`:
- **OpenAI-Compatible**: Groq, OpenRouter, Mistral, OpenAI, and Gemini (via Google's OpenAI-compatible endpoint).
- **Cohere**: Response normalization to standard OpenAI message structure.
- **Backoff & Retries**: Exponential backoff with automatic fallback across providers.
- **Native Tool Calling**: Returns tool call requests with argument JSON and passes outputs back to the model.
