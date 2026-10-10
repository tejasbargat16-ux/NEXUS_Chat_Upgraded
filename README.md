# NEXUS Studio — J.A.R.V.I.S. AI Desktop Operating System

> **Autonomous AI Command Center & Desktop Operating Partner**  
> Powered by Multi-Provider AI (Groq, Gemini, OpenRouter), Real-time Hardware Telemetry, Hands-Free Ambient Wake-Word Voice, Windows OS Automation, and an Iron Man Arc Reactor HUD.

---

## ⚡ Overview

**NEXUS Studio** is a desktop AI system designed for hands-free automation, hardware telemetry, deep file searching, and natural language command execution. With the **J.A.R.V.I.S. Core Engine**, NEXUS bridges conversational AI with native Windows OS control.

---

## 🚀 Key J.A.R.V.I.S. Capabilities

### 1. 🎙️ Hands-Free Ambient Wake-Word Mode
- Continuous ambient listening in browser and terminal.
- Activates on `"Jarvis"`, `"Hey Jarvis"`, or `"Nexus"`.
- Web Audio tactical sound synthesizer (rising pulse activation, chord completion, alert beep).

### 2. ⚡ Real-Time Hardware Telemetry & Diagnostics
- Live CPU % load and RAM usage with GB free/total breakdown.
- Power and battery status (percentage, AC connected vs discharging).
- System uptime and diagnostics speech report.
- Natural voice command: *"Jarvis, report system status"*.

### 3. 🖥️ Native Windows OS & Desktop Hardware Controls
- **Volume & Audio**: Volume up/down, mute/unmute toggle.
- **Media Playback**: Play/pause, next track, previous track.
- **Workstation Security**: Instant lock screen (`LockWorkStation`).
- **Window Management**: Minimize all windows / Show Desktop.
- **Tools**: Screen capture / screenshot saved locally, Recycle Bin purge, clipboard read/write.
- **Application Opener**: Launch & close system apps, web apps, folders, and files.

### 4. 🌅 Executive Morning Protocol & Briefing Routine
- Time-calibrated greetings (Morning, Afternoon, Evening, Late night).
- Spoken date, time, system health status, and active task overview.
- Natural voice command: *"Jarvis, good morning"* or *"Jarvis, run morning briefing"*.

### 5. ⏱️ Background Countdown Timers & Reminders
- Schedule background countdown timers with custom labels.
- Audible voice notification via speech synthesis upon completion: *"Sir, your {label} timer has concluded."*

### 6. ⚛️ Iron Man Arc Reactor HUD Interface
- Rotating cybernetic Arc Reactor visualizer with dynamic pulse.
- Real-time hardware telemetry gauges (CPU bar, RAM bar, Power chip, Uptime).
- 12-button Tactical Command Deck for instant 1-click desktop control.

---

## 🛠️ Quick Start

### 1. Setup Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
```ini
GROQ_API_KEY="your_groq_api_key"
GEMINI_API_KEY="your_gemini_api_key"
OPENROUTER_API_KEY="your_openrouter_api_key"
NEXUS_API_KEY="your_secret_nexus_api_key"
```

### 3. Run NEXUS Studio
```bash
# Launch Desktop Studio (Flask REST API + Frameless Desktop Window)
python main.py

# Launch Headless REST API
python main.py --server-only

# Launch Terminal Voice Assistant
python main.py --task

# Launch Interactive Terminal Chat CLI
python main.py --cli
```

---

## 🌐 REST API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/system/telemetry` | `GET` | Real-time CPU, RAM, Battery, Disk, and Uptime |
| `/system/action` | `POST` | Execute OS action (`lock_workstation`, `minimize_all`, `volume_up`, `volume_down`, `volume_mute`, `media_play_pause`, `take_screenshot`, `empty_recycle_bin`) |
| `/jarvis/briefing` | `GET` | Executive morning / daily status report |
| `/jarvis/timers` | `GET` | List active timers and pop fired alerts |
| `/jarvis/timer` | `POST` | Schedule a background timer (`{ "seconds": 300, "label": "Break" }`) |
| `/chat` | `POST` | Conversation & zero-latency J.A.R.V.I.S. natural language dispatch |
| `/providers` | `GET` | Available LLM providers and key status |
| `/health` | `GET` | Service health status |

---

## 🗣️ Common J.A.R.V.I.S. Voice Commands

- *"Jarvis, report system telemetry and hardware status"*
- *"Jarvis, good morning"* (or *"morning protocol"*)
- *"Jarvis, lock the workstation"*
- *"Jarvis, volume up"* / *"Jarvis, mute audio"*
- *"Jarvis, pause music"* / *"Jarvis, next track"*
- *"Jarvis, set a timer for 10 minutes for build"*
- *"Jarvis, take a screenshot"*
- *"Jarvis, open Visual Studio Code"*
- *"Jarvis, open YouTube"*
