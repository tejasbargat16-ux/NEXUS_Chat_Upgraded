#!/usr/bin/env python3
"""
J.A.R.V.I.S. Core Engine for NEXUS
==================================
Autonomous System Diagnostics, Hardware Controls, Timer/Reminder Scheduling,
Morning Briefing Protocols, and Natural Language Desktop Automation.
"""

import os
import sys
import time
import math
import uuid
import ctypes
import platform
import datetime
import threading
import subprocess
from typing import Dict, Any, List, Optional, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "core" else SCRIPT_DIR
for _p in (ROOT_DIR, os.path.join(ROOT_DIR, "core"), os.path.join(ROOT_DIR, "agents")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# ----------------------------------------------------------------------
# 1. Hardware & System Telemetry
# ----------------------------------------------------------------------

def get_system_telemetry() -> Dict[str, Any]:
    """Collect real-time system metrics: CPU, RAM, Disk, Battery, Uptime."""
    telemetry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "processor": platform.processor(),
        "cpu_percent": 0.0,
        "cpu_count": os.cpu_count() or 1,
        "ram_total_gb": 0.0,
        "ram_used_gb": 0.0,
        "ram_free_gb": 0.0,
        "ram_percent": 0.0,
        "disk_total_gb": 0.0,
        "disk_free_gb": 0.0,
        "disk_percent": 0.0,
        "battery_percent": None,
        "battery_power_plugged": None,
        "battery_time_left_min": None,
        "uptime_seconds": 0,
        "uptime_formatted": "0m",
    }

    if HAS_PSUTIL:
        try:
            # CPU
            telemetry["cpu_percent"] = round(psutil.cpu_percent(interval=0.1), 1)
            
            # RAM
            mem = psutil.virtual_memory()
            telemetry["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
            telemetry["ram_used_gb"] = round((mem.total - mem.available) / (1024 ** 3), 2)
            telemetry["ram_free_gb"] = round(mem.available / (1024 ** 3), 2)
            telemetry["ram_percent"] = round(mem.percent, 1)

            # Disk
            root_path = "C:\\" if platform.system() == "Windows" else "/"
            disk = psutil.disk_usage(root_path)
            telemetry["disk_total_gb"] = round(disk.total / (1024 ** 3), 1)
            telemetry["disk_free_gb"] = round(disk.free / (1024 ** 3), 1)
            telemetry["disk_percent"] = round(disk.percent, 1)

            # Battery
            battery = psutil.sensors_battery()
            if battery:
                telemetry["battery_percent"] = round(battery.percent)
                telemetry["battery_power_plugged"] = bool(battery.power_plugged)
                if battery.secsleft > 0 and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                    telemetry["battery_time_left_min"] = round(battery.secsleft / 60)

            # Uptime
            boot_time = psutil.boot_time()
            uptime_s = int(time.time() - boot_time)
            telemetry["uptime_seconds"] = uptime_s
            hours, rem = divmod(uptime_s, 3600)
            minutes, _ = divmod(rem, 60)
            telemetry["uptime_formatted"] = f"{hours}h {minutes}m" if hours else f"{minutes}m"
        except Exception as exc:
            telemetry["error"] = str(exc)
    else:
        telemetry["note"] = "psutil not installed; fallback metrics used"

    return telemetry


def get_telemetry_speech_summary() -> str:
    """Generate a crisp, Jarvis-style spoken diagnostic report."""
    t = get_system_telemetry()
    cpu = t.get("cpu_percent", 0)
    ram_pct = t.get("ram_percent", 0)
    ram_free = t.get("ram_free_gb", 0)
    battery = t.get("battery_percent")
    plugged = t.get("battery_power_plugged")
    uptime = t.get("uptime_formatted", "unknown")

    parts = ["All core systems operational, sir."]
    parts.append(f"CPU load is at {cpu} percent, and memory utilization is at {ram_pct} percent with {ram_free} gigabytes available.")
    
    if battery is not None:
        p_state = "connected to AC power" if plugged else "discharging on battery"
        parts.append(f"Power reserve is at {battery} percent, {p_state}.")
    
    parts.append(f"System uptime is {uptime}.")
    return " ".join(parts)


# ----------------------------------------------------------------------
# 2. Windows OS & Desktop Hardware Controls
# ----------------------------------------------------------------------

# Virtual-Key codes for Windows
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_LWIN = 0x5B
KEYEVENTF_KEYUP = 0x0002

def _send_vk(vk_code: int):
    """Simulate a key tap on Windows."""
    if platform.system() == "Windows":
        try:
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False
    return False


def volume_up(steps: int = 5) -> Tuple[bool, str]:
    """Increase system volume by sending volume up keypresses."""
    if platform.system() != "Windows":
        return False, "Volume control is currently configured for Windows."
    for _ in range(steps):
        _send_vk(VK_VOLUME_UP)
        time.sleep(0.02)
    return True, f"Volume increased by {steps * 2}%."


def volume_down(steps: int = 5) -> Tuple[bool, str]:
    """Decrease system volume by sending volume down keypresses."""
    if platform.system() != "Windows":
        return False, "Volume control is currently configured for Windows."
    for _ in range(steps):
        _send_vk(VK_VOLUME_DOWN)
        time.sleep(0.02)
    return True, f"Volume decreased by {steps * 2}%."


def volume_mute() -> Tuple[bool, str]:
    """Toggle mute on/off."""
    if platform.system() != "Windows":
        return False, "Mute toggle is currently configured for Windows."
    _send_vk(VK_VOLUME_MUTE)
    return True, "Audio mute toggled, sir."


def media_play_pause() -> Tuple[bool, str]:
    """Toggle media play/pause."""
    if platform.system() != "Windows":
        return False, "Media control is currently configured for Windows."
    _send_vk(VK_MEDIA_PLAY_PAUSE)
    return True, "Media playback toggled, sir."


def media_next() -> Tuple[bool, str]:
    """Skip to next media track."""
    if platform.system() != "Windows":
        return False, "Media control is currently configured for Windows."
    _send_vk(VK_MEDIA_NEXT_TRACK)
    return True, "Skipped to next track, sir."


def media_prev() -> Tuple[bool, str]:
    """Return to previous media track."""
    if platform.system() != "Windows":
        return False, "Media control is currently configured for Windows."
    _send_vk(VK_MEDIA_PREV_TRACK)
    return True, "Reverted to previous track, sir."


def lock_workstation() -> Tuple[bool, str]:
    """Lock the Windows workstation immediately."""
    if platform.system() != "Windows":
        return False, "Workstation lock is only supported on Windows."
    try:
        ctypes.windll.user32.LockWorkStation()
        return True, "Workstation locked securely, sir."
    except Exception as exc:
        return False, f"Could not lock workstation: {exc}"


def minimize_all_windows() -> Tuple[bool, str]:
    """Toggle Minimize All / Show Desktop using Windows Shell."""
    if platform.system() != "Windows":
        return False, "Desktop toggle is currently configured for Windows."
    try:
        # PowerShell COM Shell.Application MinimizeAll
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "(New-Object -ComObject Shell.Application).MinimizeAll()"],
            capture_output=True,
            timeout=5
        )
        return True, "Minimizing all active windows, sir."
    except Exception as exc:
        # Fallback to Win+D simulation
        _send_vk(VK_LWIN)
        return False, f"Could not minimize windows: {exc}"


def empty_recycle_bin() -> Tuple[bool, str]:
    """Silently empty Windows Recycle Bin."""
    if platform.system() != "Windows":
        return False, "Recycle Bin empty is only supported on Windows."
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            timeout=8
        )
        return True, "Recycle Bin purged successfully, sir."
    except Exception as exc:
        return False, f"Could not purge Recycle Bin: {exc}"


def take_screenshot(custom_name: Optional[str] = None) -> Tuple[bool, str]:
    """Capture screen and save into ~/.nexuschat/screenshots/."""
    save_dir = os.path.expanduser("~/.nexuschat/screenshots")
    os.makedirs(save_dir, exist_ok=True)
    filename = custom_name or f"screenshot_{int(time.time())}.png"
    filepath = os.path.join(save_dir, filename)

    if platform.system() == "Windows":
        ps_cmd = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphic = [System.Drawing.Graphics]::FromImage($bitmap)
$graphic.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{filepath}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphic.Dispose()
$bitmap.Dispose()
"""
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=10)
            if os.path.exists(filepath):
                return True, f"Screenshot captured and stored at: {filepath}"
        except Exception as exc:
            return False, f"Screenshot capture error: {exc}"

    return False, "Screenshot capture failed."


def get_clipboard_text() -> Tuple[bool, str]:
    """Fetch current plain text from clipboard."""
    if platform.system() == "Windows":
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                text=True,
                timeout=5
            ).strip()
            return True, out if out else "(Clipboard is empty)"
        except Exception as exc:
            return False, f"Could not read clipboard: {exc}"
    return False, "Clipboard lookup is currently configured for Windows."


# ----------------------------------------------------------------------
# 3. Jarvis Morning Protocol & Executive Briefings
# ----------------------------------------------------------------------

def get_morning_briefing(operator_name: str = "Sir") -> Dict[str, Any]:
    """Generate comprehensive executive morning / daily status report."""
    now = datetime.datetime.now()
    hour = now.hour
    
    if 5 <= hour < 12:
        greeting = f"Good morning, {operator_name}."
    elif 12 <= hour < 17:
        greeting = f"Good afternoon, {operator_name}."
    elif 17 <= hour < 22:
        greeting = f"Good evening, {operator_name}."
    else:
        greeting = f"Standing by through the late hours, {operator_name}."

    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    telemetry = get_system_telemetry()
    cpu = telemetry.get("cpu_percent", 0)
    ram = telemetry.get("ram_percent", 0)
    free_ram = telemetry.get("ram_free_gb", 0)
    battery = telemetry.get("battery_percent")
    plugged = telemetry.get("battery_power_plugged")

    active_timers = get_active_timers()

    speech_lines = [
        f"{greeting} The time is {time_str} on {date_str}.",
        f"Diagnostic sweep indicates system telemetry is optimal with CPU at {cpu} percent and {free_ram} gigabytes of RAM available.",
    ]
    if battery is not None:
        p_desc = "plugged into AC power" if plugged else "running on battery"
        speech_lines.append(f"Battery is currently at {battery} percent, {p_desc}.")
    
    if active_timers:
        speech_lines.append(f"You have {len(active_timers)} active reminder timers running.")
    else:
        speech_lines.append("No pending timers scheduled.")
        
    speech_lines.append("Command protocols are active and ready for your instruction.")

    full_speech = " ".join(speech_lines)
    
    return {
        "greeting": greeting,
        "date": date_str,
        "time": time_str,
        "telemetry": telemetry,
        "active_timers_count": len(active_timers),
        "speech": full_speech,
        "markdown": f"""### 🌅 J.A.R.V.I.S. Daily Protocol Briefing
**Status:** Nominal  
**Date & Time:** {date_str} — {time_str}  
**System Load:** CPU `{cpu}%` | RAM `{ram}%` ({free_ram} GB free)  
**Power:** {f'{battery}%' if battery is not None else 'Desktop AC'} ({'Plugged In' if plugged else 'Battery'})  
**Active Timers:** `{len(active_timers)}`  

*{full_speech}*
"""
    }


# ----------------------------------------------------------------------
# 4. Background Timer & Reminder System
# ----------------------------------------------------------------------

_TIMERS: Dict[str, Dict[str, Any]] = {}
_TIMER_LOCK = threading.Lock()
_FIRED_ALERTS: List[Dict[str, Any]] = []

def _timer_worker(timer_id: str, duration_sec: int, label: str):
    time.sleep(duration_sec)
    with _TIMER_LOCK:
        if timer_id in _TIMERS and _TIMERS[timer_id]["status"] == "active":
            _TIMERS[timer_id]["status"] = "finished"
            alert = {
                "id": timer_id,
                "label": label,
                "finished_at": datetime.datetime.now().isoformat(),
                "message": f"Alert, sir: Your {label} timer has concluded."
            }
            _FIRED_ALERTS.append(alert)
            # Audible voice notification
            try:
                import pyttsx3
                eng = pyttsx3.init()
                eng.setProperty("rate", 175)
                eng.say(f"Sir, your timer for {label} has finished.")
                eng.runAndWait()
            except Exception:
                pass


def set_timer(duration_sec: int, label: str = "Task") -> Dict[str, Any]:
    """Schedule a background countdown timer that alerts upon completion."""
    timer_id = str(uuid.uuid4())[:8]
    now = datetime.datetime.now()
    ends_at = now + datetime.timedelta(seconds=duration_sec)

    record = {
        "id": timer_id,
        "label": label,
        "duration_sec": duration_sec,
        "created_at": now.isoformat(),
        "ends_at": ends_at.isoformat(),
        "status": "active"
    }
    with _TIMER_LOCK:
        _TIMERS[timer_id] = record

    t = threading.Thread(target=_timer_worker, args=(timer_id, duration_sec, label), daemon=True)
    t.start()
    return record


def get_active_timers() -> List[Dict[str, Any]]:
    """List all currently active countdown timers."""
    with _TIMER_LOCK:
        return [t for t in _TIMERS.values() if t["status"] == "active"]


def cancel_timer(timer_id: str) -> bool:
    """Cancel an active timer."""
    with _TIMER_LOCK:
        if timer_id in _TIMERS:
            _TIMERS[timer_id]["status"] = "cancelled"
            return True
    return False


def pop_fired_alerts() -> List[Dict[str, Any]]:
    """Retrieve and clear any newly fired alerts."""
    global _FIRED_ALERTS
    with _TIMER_LOCK:
        alerts = list(_FIRED_ALERTS)
        _FIRED_ALERTS = []
        return alerts


# ----------------------------------------------------------------------
# 5. Natural Language Jarvis Intent Dispatcher
# ----------------------------------------------------------------------

def handle_jarvis_command(text: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if the input text corresponds to a direct Jarvis desktop action.
    Returns (handled, response_text, metadata).
    """
    cmd = text.strip().lower()

    # 1. System status / Telemetry / Battery / CPU
    if any(k in cmd for k in ["system status", "telemetry", "hardware status", "system diagnostics", "jarvis status", "pc status", "battery status", "battery", "cpu status", "cpu load", "ram status", "memory status", "power status"]):
        speech = get_telemetry_speech_summary()
        t = get_system_telemetry()
        return True, speech, {"action": "telemetry", "data": t}

    # 2. Workstation Lock
    if any(k in cmd for k in ["lock pc", "lock screen", "lock workstation", "lock computer", "lock the pc"]):
        ok, msg = lock_workstation()
        return True, msg, {"action": "lock_workstation", "success": ok}

    # 3. Minimize / Show Desktop
    if any(k in cmd for k in ["minimize all", "show desktop", "minimize windows", "hide all windows"]):
        ok, msg = minimize_all_windows()
        return True, msg, {"action": "minimize_all", "success": ok}

    # 4. Volume controls
    if any(k in cmd for k in ["volume up", "increase volume", "louder", "turn volume up"]):
        ok, msg = volume_up(5)
        return True, msg, {"action": "volume_up", "success": ok}
    if any(k in cmd for k in ["volume down", "decrease volume", "lower volume", "quieter"]):
        ok, msg = volume_down(5)
        return True, msg, {"action": "volume_down", "success": ok}
    if any(k in cmd for k in ["mute audio", "mute sound", "mute volume", "unmute", "toggle mute"]):
        ok, msg = volume_mute()
        return True, msg, {"action": "volume_mute", "success": ok}

    # 5. Media Controls
    if any(k in cmd for k in ["pause music", "resume music", "play music", "toggle media", "play pause"]):
        ok, msg = media_play_pause()
        return True, msg, {"action": "media_play_pause", "success": ok}
    if any(k in cmd for k in ["next song", "next track", "skip track", "skip song"]):
        ok, msg = media_next()
        return True, msg, {"action": "media_next", "success": ok}
    if any(k in cmd for k in ["previous song", "previous track", "last song"]):
        ok, msg = media_prev()
        return True, msg, {"action": "media_prev", "success": ok}

    # 6. Screenshot
    if any(k in cmd for k in ["take a screenshot", "take screenshot", "capture screen", "screenshot"]):
        ok, msg = take_screenshot()
        return True, msg, {"action": "take_screenshot", "success": ok}

    # 7. Recycle Bin
    if any(k in cmd for k in ["empty recycle bin", "clean recycle bin", "purge trash", "empty trash"]):
        ok, msg = empty_recycle_bin()
        return True, msg, {"action": "empty_recycle_bin", "success": ok}

    # 8. Clipboard
    if any(k in cmd for k in ["read clipboard", "get clipboard", "what's in my clipboard", "clipboard content"]):
        ok, content = get_clipboard_text()
        return True, f"Clipboard content: {content}", {"action": "clipboard", "content": content}

    # 9. Morning Protocol / Daily Briefing
    if any(k in cmd for k in ["good morning", "morning protocol", "daily briefing", "morning report", "executive briefing"]):
        briefing = get_morning_briefing()
        return True, briefing["speech"], {"action": "briefing", "data": briefing}

    # 10. Timers (e.g. "set timer for 10 minutes", "set a timer for 30 seconds")
    import re
    timer_match = re.search(r'(?:set|start)(?:\s+a)?\s+timer\s+for\s+(\d+)\s*(minute|second|min|sec|hour|hr)s?(?:\s+(?:for|labeled|called)\s+(.+))?', cmd)
    if timer_match:
        val = int(timer_match.group(1))
        unit = timer_match.group(2)
        label = (timer_match.group(3) or "Reminder").strip()
        
        multiplier = 1
        if "min" in unit:
            multiplier = 60
        elif "hour" in unit or "hr" in unit:
            multiplier = 3600
        
        duration = val * multiplier
        rec = set_timer(duration, label)
        return True, f"Timer scheduled for {val} {unit}s labeled '{label}', sir. I will alert you once elapsed.", {"action": "set_timer", "data": rec}

    return False, "", {}
