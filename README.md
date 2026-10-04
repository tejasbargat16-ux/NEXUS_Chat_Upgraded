# NEXUS Chat

Terminal-based AI chatbot for Termux with **multi-provider routing** (Groq,
Gemini, OpenRouter) and persistent SQLite chat history so conversations
survive across sessions.

Uses plain `requests` (no provider SDKs) to avoid Rust/`jiter`-style compile
failures that are common in Termux's Python environment.

## Setup (Termux)

```bash
pkg install python -y
cd nexuschat
pip install -r requirements.txt
```

Set the API key(s) for whichever provider(s) you have. You don't need all
three — NEXUS Chat auto-picks the first one it finds a key for (priority:
Groq → Gemini → OpenRouter).

```bash
export GROQ_API_KEY="your_key_here"
export GEMINI_API_KEY="your_key_here"
export OPENROUTER_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
export MISTRAL_API_KEY="your_key_here"
export COHERE_API_KEY="your_key_here"
```

Or copy `.env.example` to `.env` and fill in whichever keys you have:

```bash
cp .env.example .env
nano .env
```

Where to get keys:
- Groq: https://console.groq.com/keys
- Gemini: https://aistudio.google.com/apikey
- OpenRouter: https://openrouter.ai/keys
- OpenAI (ChatGPT): https://platform.openai.com/api-keys (needs billing set up — unlike the others, OpenAI's API has no free tier)
- Mistral: https://console.mistral.ai/api-keys (free "Experiment" tier, rate-limited, requires phone verification)
- Cohere: https://dashboard.cohere.com/api-keys (free trial key auto-generated on signup — 1,000 calls/month cap, prototyping only)

## Run

```bash
python nexuschat.py
```

## Commands (inside chat)

| Command             | Action                                          |
|----------------------|--------------------------------------------------|
| `/voice on\|off`      | Toggle voice mode — spoken replies, mic input via `v` |
| `/new`               | Start a new conversation                        |
| `/sessions`          | List saved conversations                         |
| `/load <id>`         | Resume a saved conversation                      |
| `/rename <title>`    | Rename the current conversation                  |
| `/provider <name>`   | Switch AI provider: `groq`, `gemini`, `openrouter` |
| `/model <name>`      | Switch model within the current provider          |
| `/models`            | List suggested models for the current provider    |
| `/remember <fact>`   | Save a fact about you so NEXUS remembers it always |
| `/profile`           | Show everything NEXUS remembers about you          |
| `/forget all`        | Erase everything NEXUS remembers about you         |
| `/agent on\|off`      | Toggle agent mode — NEXUS can propose shell commands |
| `/search <query>`    | Search the web right now and show results          |
| `/image <description>` | Generate an image right now (saved + opened)     |
| `/clear`             | Clear the terminal screen                        |
| `/exit`              | Quit                                             |

## Voice mode (Jarvis-style speech in/out)

`/voice on` turns on two things:

- **Speech input** — type `v` + Enter at any prompt to record a short
  message via the mic. It is transcribed with Groq's Whisper API (when `GROQ_API_KEY` is set) or seamlessly falls back to free Google Web Speech recognition via `SpeechRecognition`!
- **Speech output** — every reply is read aloud (`pyttsx3` on Windows/Mac/Linux; `termux-tts-speak` on Android). Press Enter anytime to interrupt mid-sentence, like talking over Jarvis.

While voice mode is on, replies are automatically kept short and
conversational — no markdown, bullet lists, or code blocks, since those
sound awful read aloud. Turn it off anytime with `/voice off` to go back to
normal detailed text replies.

- **On Windows / Mac / Linux**: all required libraries are installed via `pip install -r requirements.txt` (`pyttsx3`, `sounddevice`, `numpy`, `speechrecognition`).
- **On Android / Termux**: requires `pkg install termux-api` plus the **Termux:API** companion app (F-Droid/Play Store). `/voice on` will notify you if it is missing.

## Web search

NEXUS can search the internet on its own — every chat turn (agent mode or
not) includes search capability. If the model decides it needs current
information (news, prices, versions, anything time-sensitive), it searches
automatically and you'll see a "Search results" panel before the final
answer.

By default this uses a **free, keyless DuckDuckGo lookup** — no signup
needed. For better-quality, AI-tuned results, set `TAVILY_API_KEY` (free
tier at https://tavily.com, no card required) in `.env` — NEXUS will
prefer Tavily automatically when that key is present, falling back to
DuckDuckGo if Tavily fails for any reason.

You can also search manually anytime with `/search <query>`, without going
through the AI at all.

## Image generation

NEXUS can generate images too — ask for a picture, illustration, thumbnail,
poster concept, or logo idea, and it'll create one automatically (no
approval needed, since generating an image is non-destructive).

Two backends:

- **Pollinations.ai** (default) — completely free, no signup, no API key.
  Good for quick illustrations and concept art.
- **Gemini "Nano Banana"** (optional, higher quality) — uses your existing
  `GEMINI_API_KEY`. May consume paid Gemini quota depending on your tier —
  check https://ai.google.dev/pricing.

Images save to `~/.nexuschat/images/` and open automatically in your default
viewer (via `termux-open`, if Termux:API is installed). You can also
generate one manually anytime with `/image <description>`.

**No video generation.** There's currently no good free video-generation API
suitable for a personal project — real video models (Sora, Veo, Kling,
Runway) are paid, often expensive, and use async job-queue APIs rather than
a simple request/response. NEXUS will say so honestly if you ask for video
rather than pretending an image is a substitute.

## Agent mode

`/agent on` lets NEXUS propose shell commands to actually get things done —
checking files, running scripts, installing packages, etc. — instead of just
talking about them.

**Nothing ever runs automatically.** Every proposed command is shown to you
first, and you must approve it (y/n) before it executes. NEXUS sees the real
output afterward and can react to it, so it can do multi-step tasks like
"check my disk space and clean up the largest folder" — one confirmed step
at a time.

A small built-in blocklist also refuses obviously destructive commands
(`rm -rf /`, fork bombs, `mkfs`, `curl | sh`, etc.) even if you accidentally
approve them — but treat that as a last-resort safety net, not a reason to
stop reading commands before approving them.

Turn it off any time with `/agent off`.

### Phone control (via Termux:API)

With agent mode on and Termux:API installed, NEXUS can control real phone
functions — always as a `RUN:` command you approve first, exactly like any
other command:

- **Open apps** — "open WhatsApp" / "khol camera" (uses `am start` with the
  app's package name)
- **Flashlight** — on/off via `termux-torch`
- **Volume / brightness** — set specific levels or auto-brightness
- **Send a notification** — post a custom notification to yourself
- **Send an SMS / make a call** — NEXUS will describe exactly what it's
  about to send/dial before asking for approval, since these have real
  consequences (cost, someone receiving it) unlike read-only commands

Requires `pkg install termux-api` + the **Termux:API** app (F-Droid/Play
Store), same as voice mode. SMS and calls need their Android runtime
permissions granted to Termux:API the first time you use them.

Switching provider automatically resets the model to that provider's
default — use `/model` right after if you want something specific.

### Default models

- **Groq:** `openai/gpt-oss-120b` (Groq deprecated the old Llama chat models)
- **Gemini:** `gemini-3.6-flash`
- **OpenRouter:** `meta-llama/llama-3.3-70b-instruct:free`
- **OpenAI (ChatGPT):** `gpt-5.4`
- **Mistral:** `mistral-small-latest`
- **Cohere:** `command-r-08-2024`

Provider APIs change their model lineups fairly often — if you hit a
`model_not_found` style error, run `/models` for suggestions or check the
provider's docs directly.

## Offline fallback (local model)

Every cloud provider needs internet. When there's none, NEXUS checks first
(a quick connectivity test, not a guess) and — if you've set one up — falls
back to a small model running entirely on-device via
[llama.cpp](https://github.com/ggml-org/llama.cpp), instead of just failing.

**Be realistic about this**: an on-device 1-3B model is much weaker than any
of the cloud models. It's there so NEXUS can still say *something* useful
when there's genuinely no signal — not a free upgrade, and not meant to
replace the cloud models day-to-day.

This only applies to `nexuschat.py` (the terminal app). It does **not**
apply to `api.py`: if the device has no internet, the tunnel that lets the
Lovable frontend reach it is also down, so there's no request to even
answer offline in that case.

**One-time setup** (do this on Wi-Fi — it's a real compile + a model
download, a few hundred MB to a few GB):

```bash
pkg install clang cmake git -y
git clone https://github.com/ggml-org/llama.cpp ~/nexuschat/llama.cpp
cd ~/nexuschat/llama.cpp
cmake -B build && cmake --build build --config Release -j4
```

Then download **one** small GGUF model sized for your phone's RAM — e.g.
Qwen2.5-1.5B-Instruct (~1GB at Q4_K_M) is a reasonable default. Search
"Qwen2.5-1.5B-Instruct-GGUF" on Hugging Face and save the `.gguf` file into:

```bash
mkdir -p ~/nexuschat/models
# save the downloaded .gguf file into ~/nexuschat/models/
```

NEXUS auto-detects the first `.gguf` file it finds there. To pin a specific
model or a custom llama.cpp build location, set in `.env`:

```
LLAMA_CLI_PATH=/absolute/path/to/llama-cli
LOCAL_MODEL_PATH=/absolute/path/to/your-model.gguf
```

No setup done yet? NEXUS just tells you plainly that there's no internet
and no local model configured, rather than pretending to answer.

## Data

Chat history is stored at `~/.nexuschat/history.db` (SQLite). Nothing is sent
anywhere except to whichever provider's API you're actively using.

Facts you save with `/remember` are stored as plain text at
`~/.nexuschat/profile.txt` and are automatically included in every new
conversation's system prompt, so you don't have to reintroduce yourself
every session. Edit or delete that file directly any time, or use
`/forget all` to wipe it.

## Identity / operating principles

`identity.py` holds NEXUS's core system prompt — a condensed, token-efficient
version of the user's full "Master AI Context & Quality Prompt" (the complete
32-section version is kept for reference at `MASTER_PROMPT_REFERENCE.md`,
but isn't sent on every API call since that would burn tokens/latency for
no benefit). It covers: understand-before-answering, execute rather than
just describe, verify time-sensitive claims via search, separate fact from
inference, admit uncertainty honestly, and match communication style
(Hinglish/English/Marathi) to the user.

Edit `identity.py` directly to adjust NEXUS's behavior — both `nexuschat.py`
(terminal) and `api.py` (REST API for the Lovable frontend) import from it,
so a change there applies everywhere.

## Optional: run from anywhere

```bash
chmod +x nexuschat.py
mkdir -p ~/bin
ln -s "$(pwd)/nexuschat.py" ~/bin/nexuschat
# add ~/bin to PATH in ~/.bashrc if not already, then:
nexuschat
```
