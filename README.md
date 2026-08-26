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

## Run

```bash
python nexuschat.py
```

## Commands (inside chat)

| Command             | Action                                          |
|----------------------|--------------------------------------------------|
| `/new`               | Start a new conversation                        |
| `/sessions`          | List saved conversations                         |
| `/load <id>`         | Resume a saved conversation                      |
| `/rename <title>`    | Rename the current conversation                  |
| `/provider <name>`   | Switch AI provider: `groq`, `gemini`, `openrouter` |
| `/model <name>`      | Switch model within the current provider          |
| `/models`            | List suggested models for the current provider    |
| `/clear`             | Clear the terminal screen                        |
| `/exit`              | Quit                                             |

Switching provider automatically resets the model to that provider's
default — use `/model` right after if you want something specific.

### Default models

- **Groq:** `openai/gpt-oss-120b` (Groq deprecated the old Llama chat models)
- **Gemini:** `gemini-2.5-flash`
- **OpenRouter:** `meta-llama/llama-3.3-70b-instruct:free`

Provider APIs change their model lineups fairly often — if you hit a
`model_not_found` style error, run `/models` for suggestions or check the
provider's docs directly.

## Data

Chat history is stored at `~/.nexuschat/history.db` (SQLite). Nothing is sent
anywhere except to whichever provider's API you're actively using.

## Optional: run from anywhere

```bash
chmod +x nexuschat.py
mkdir -p ~/bin
ln -s "$(pwd)/nexuschat.py" ~/bin/nexuschat
# add ~/bin to PATH in ~/.bashrc if not already, then:
nexuschat
```
