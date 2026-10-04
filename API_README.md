# NEXUS Chat API

Flask REST API that exposes `nexuschat`'s backend (multi-provider chat,
SQLite history, profile memory, agent mode) to the Lovable frontend at
https://nexus-futuristic-chat.lovable.app — or any other HTTP client.

Pure Python + Flask, no Rust-extension dependencies (deliberately avoids
FastAPI/pydantic-core, which fail to build on Termux's `aarch64-linux-android`
Python).

## Setup (Termux)

```bash
cd ~/nexuschat
pip install -r requirements.txt
```

Set your keys:

```bash
export NEXUS_API_KEY="pick-a-long-random-string"   # protects every endpoint
export GROQ_API_KEY="..."
export GEMINI_API_KEY="..."
export OPENROUTER_API_KEY="..."
```

(or put them in `.env` next to the script — same loading logic as `nexuschat.py`)

## Run

```bash
python api.py
```

Starts a Flask dev server on `0.0.0.0:8000`. It's a dev server (fine for
personal/prototype use on your own device) — don't expose it to the public
internet without the tunnel + API key protection described below.

## Expose it to the internet (for the Lovable frontend)

The frontend is hosted online and can't reach `localhost`, so tunnel it:

```bash
pkg install cloudflared -y
cloudflared tunnel --url http://localhost:8000
```

Copy the `https://xxxx.trycloudflare.com` URL it prints. Paste that URL and
your `NEXUS_API_KEY` into the frontend's **Settings** page, click
**Test & Save**. The tunnel URL changes every time cloudflared restarts —
update Settings again when that happens.

## Endpoints

All routes except `/health` require an `X-API-Key` header matching
`NEXUS_API_KEY`.

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | `{status: "ok"}` (no auth) |
| GET | `/images/:filename` | — | The raw image file. Accepts either `X-API-Key` header or `?key=` query param (needed so `<img>` tags can load it directly). |
| GET | `/voice/status` | — | `{voice_available: bool, mic_available: bool, is_termux: bool}` |
| POST | `/voice/transcribe` | Multipart `file` or JSON `{audio_base64}` | `{text: "transcribed speech"}` |
| GET | `/providers` | — | `[{id, label, default_model, suggested_models, key_configured}]` |
| GET | `/conversations` | — | `[{id, title, created_at}]` |
| POST | `/conversations` | `{title?}` | `{id, title, created_at}` |
| GET | `/conversations/:id/messages` | — | `[{role, content}]` |
| PATCH | `/conversations/:id` | `{title}` | `{ok: true}` |
| DELETE | `/conversations/:id` | — | `{ok: true}` |
| POST | `/chat` | `{conversation_id, provider, model, message}` | `{type:"message", content}` or `{type:"agent_command", command, conversation_id}` |
| POST | `/agent/run` | `{conversation_id, command}` | `{stdout, stderr, exit_code, follow_up}` |
| POST | `/agent/decline` | `{conversation_id}` | `{follow_up}` |
| GET | `/profile` | — | `{text}` |
| POST | `/profile` | `{fact}` | `{ok: true}` |
| DELETE | `/profile` | — | `{ok: true}` |

## How agent mode works over the API

Every `/chat` call has agent capability enabled — if the model decides a
shell command would help, the reply comes back as `agent_command` instead of
plain `message`. The frontend shows the proposed command and only calls
`/agent/run` if the user clicks approve; `/agent/decline` is called instead
if they decline. Nothing runs on the server without that explicit round-trip.

A hardcoded blocklist (`agent.py`) also rejects obviously destructive
commands (`rm -rf /`, fork bombs, `mkfs`, `curl | sh`, etc.) with a 403, even
if a client tries to call `/agent/run` with one directly.

## Search and image generation over the API

Unlike shell commands, web search and image generation are non-destructive,
so they're auto-resolved server-side with no approval round-trip — the
`/chat` caller just gets the final answer, with any intermediate search/
image steps already baked in and saved to the conversation's DB history.
Image URLs embedded in a reply include `?key=...` so an `<img>` tag can load
them directly without needing to attach a custom header.

## Security notes

- `/agent/run` executes real shell commands on whatever machine runs `api.py`.
  Keep `NEXUS_API_KEY` secret and only expose this through a private tunnel —
  never make it a permanent public unauthenticated endpoint.
- CORS is currently wide open (`origins: "*"`) for ease of prototyping from
  the Lovable preview domain. Tighten this to your frontend's exact origin
  before treating this as anything beyond a personal project.
- The Flask dev server (`app.run`) is not meant for production traffic — fine
  for single-user personal use over a tunnel, not for a public multi-user app.
