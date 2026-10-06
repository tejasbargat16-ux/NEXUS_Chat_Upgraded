#!/usr/bin/env python3
"""
NEXUS AI Voice Desktop Assistant Module (desktop_assistant.py)
------------------------------------------------------------
Implements intelligent voice-controlled desktop automation:
  - Deep File & Folder Indexing with fast lookups
  - Deep File Search with antonym penalty matrix & fuzzy word-scoring
  - Smart App Opener (System Apps + Web Apps)
  - Bulletproof Website Opener & Web Search (Google / DuckDuckGo / LLM URL resolution)
  - Cross-platform Open & Close support for Apps, Files, Folders, and Browser Tabs (Windows/macOS/Linux)
  - Intent Classification (Local Regex + LLM intent extraction fallback & tie-breaking)

Inspired by & upgraded from AI-Voice-Desktop-Assistant by Yuvakunaal.
"""

import os
import re
import sys
import json
import time
import platform
import subprocess
import webbrowser
import requests
from difflib import get_close_matches

import providers

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_env():
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env()

# ------------------------------------------------------------------ Maps & Dictionaries
HARDCODED_FOLDERS = {
    'applications': '/Applications' if platform.system() == 'Darwin' else os.path.expandvars(r'%ProgramData%\Microsoft\Windows\Start Menu\Programs'),
    'downloads': os.path.expanduser('~/Downloads'),
    'desktop': os.path.expanduser('~/Desktop'),
    'documents': os.path.expanduser('~/Documents'),
    'pictures': os.path.expanduser('~/Pictures'),
    'music': os.path.expanduser('~/Music'),
    'movies': os.path.expanduser('~/Movies'),
    'videos': os.path.expanduser('~/Movies') if platform.system() == 'Darwin' else os.path.expanduser('~/Videos'),
    'public': os.path.expanduser('~/Public'),
    'library': os.path.expanduser('~/Library'),
    'appdata': os.path.expanduser('~/AppData'),
    'home': os.path.expanduser('~'),
}

SYSTEM_APP_MAP = {
    'terminal': 'Terminal' if platform.system() == 'Darwin' else 'cmd.exe',
    'cmd': 'cmd.exe',
    'command prompt': 'cmd.exe',
    'powershell': 'powershell.exe',
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'calc': 'calc.exe',
    'explorer': 'explorer.exe',
    'file explorer': 'explorer.exe',
    'task manager': 'taskmgr.exe',
    'settings': 'System Settings' if platform.system() == 'Darwin' else 'ms-settings:',
    'system settings': 'System Settings' if platform.system() == 'Darwin' else 'ms-settings:',
    'system preferences': 'System Settings' if platform.system() == 'Darwin' else 'ms-settings:',
    'finder': 'Finder',
    'activity monitor': 'Activity Monitor',
    'console': 'Console',
    'disk utility': 'Disk Utility',
    'safari': 'Safari',
    'chrome': 'Google Chrome' if platform.system() == 'Darwin' else 'chrome',
    'edge': 'Microsoft Edge' if platform.system() == 'Darwin' else 'msedge',
    'app store': 'App Store',
    'preview': 'Preview',
    'notes': 'Notes',
    'calendar': 'Calendar',
    'reminders': 'Reminders',
    'music': 'Music',
    'photos': 'Photos',
    'mail': 'Mail',
    'messages': 'Messages',
    'contacts': 'Contacts',
}

WEB_APP_MAP = {
    'gemini': 'https://gemini.google.com',
    'chatgpt': 'https://chat.openai.com',
    'bard': 'https://bard.google.com',
    'notion': 'https://notion.so',
    'figma': 'https://figma.com',
    'github': 'https://github.com',
    'gmail': 'https://mail.google.com',
    'youtube': 'https://youtube.com',
    'linkedin': 'https://linkedin.com',
    'facebook': 'https://facebook.com',
    'twitter': 'https://x.com',
    'x': 'https://x.com',
    'slack': 'https://slack.com',
    'zoom': 'https://zoom.us',
    'drive': 'https://drive.google.com',
    'google drive': 'https://drive.google.com',
    'meet': 'https://meet.google.com',
    'google meet': 'https://meet.google.com',
    'calendar': 'https://calendar.google.com',
    'spotify': 'https://open.spotify.com',
    'whatsapp': 'https://web.whatsapp.com',
    'codechef': 'https://www.codechef.com',
    'leetcode': 'https://leetcode.com',
    'hackerrank': 'https://www.hackerrank.com',
}

ANTONYM_PAIRS = [
    ('internal', 'external'),
    ('external', 'internal'),
    ('old', 'new'),
    ('new', 'old'),
    ('draft', 'final'),
    ('final', 'draft'),
    ('temp', 'permanent'),
    ('backup', 'original'),
]

USER_FOLDERS = [
    os.path.expanduser('~/Downloads'),
    os.path.expanduser('~/Desktop'),
    os.path.expanduser('~/Documents'),
    os.path.expanduser('~/Pictures'),
    os.path.expanduser('~/Music'),
    os.path.expanduser('~/Movies'),
    os.path.expanduser('~/Videos'),
]

# Cache index globally
_INDEX_CACHE = None
_INDEX_TIMESTAMP = 0

# ------------------------------------------------------------------ Indexer
def build_index(force_refresh=False):
    """Build or retrieve indexed cache of user-facing files, folders, and apps."""
    global _INDEX_CACHE, _INDEX_TIMESTAMP
    now = time.time()
    # Cache index for 10 minutes unless forced
    if _INDEX_CACHE and not force_refresh and (now - _INDEX_TIMESTAMP < 600):
        return _INDEX_CACHE

    home = os.path.expanduser('~')
    system = platform.system()
    
    search_dirs = [f for f in USER_FOLDERS if os.path.exists(f)]
    if system == 'Darwin':
        search_dirs.extend(['/Applications', os.path.join(home, 'Applications')])
    elif system == 'Windows':
        search_dirs.extend([
            os.path.expandvars(r'%ProgramData%\Microsoft\Windows\Start Menu\Programs'),
            os.path.expandvars(r'%AppData%\Microsoft\Windows\Start Menu\Programs')
        ])

    files = []
    folders = []
    apps = []

    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        try:
            for root, dirs, filelist in os.walk(search_dir):
                # Skip hidden directories
                if any(part.startswith('.') for part in root.split(os.sep)):
                    continue
                # Cap walk depth to avoid long hangs
                depth = root.count(os.sep) - search_dir.count(os.sep)
                if depth > 4:
                    continue

                for d in dirs:
                    if not d.startswith('.'):
                        folders.append((d, os.path.join(root, d)))
                for f in filelist:
                    if not f.startswith('.'):
                        files.append((f, os.path.join(root, f)))
                        if system == 'Windows' and f.lower().endswith(('.exe', '.lnk')):
                            apps.append((os.path.splitext(f)[0], os.path.join(root, f)))
                
                if system == 'Darwin' and root in ['/Applications', os.path.join(home, 'Applications')]:
                    for app in [a for a in dirs if a.endswith('.app')]:
                        apps.append((app.replace('.app', ''), os.path.join(root, app)))
        except Exception as e:
            print(f"[Index Warning] Error indexing {search_dir}: {e}")

    _INDEX_CACHE = {'files': files, 'folders': folders, 'apps': apps}
    _INDEX_TIMESTAMP = now
    return _INDEX_CACHE


def normalize_name(name):
    return re.sub(r'[-_\s\.]+', '', name.lower())


def split_words(text):
    return [w for w in re.split(r'[-_\s\.]+', text.lower()) if w]


def find_best_match(name, index, kind='files'):
    name_norm = normalize_name(name)
    items = index.get(kind, [])
    names = [normalize_name(n[0]) for n in items]
    
    # Exact or substring match
    for i, n in enumerate(names):
        if name_norm == n or name_norm in n:
            return items[i][1]
            
    # Fuzzy match
    matches = get_close_matches(name_norm, names, n=1, cutoff=0.6)
    if matches:
        idx = names.index(matches[0])
        return items[idx][1]
    return None

# ------------------------------------------------------------------ Deep Search
def file_match_score(query_words, file_words, ext=None):
    score = 0
    for qw in query_words:
        if qw in file_words:
            score += 2
        elif any(get_close_matches(qw, file_words, n=1, cutoff=0.7)):
            score += 1
            
    # Penalize antonym / conflicting word matches
    for q in query_words:
        for f in file_words:
            for a, b in ANTONYM_PAIRS:
                if q == a and b in file_words:
                    score -= 2

    if ext and ext in file_words:
        score += 2
    return score


def deep_file_search(query, file_type=None):
    query_words = split_words(query)
    ext = None
    known_exts = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'py', 'js', 'html', 'zip', 'csv', 'mp3', 'mp4']
    for w in query_words:
        if w in known_exts:
            ext = w

    matches = []
    for folder in USER_FOLDERS:
        if not os.path.exists(folder):
            continue
        try:
            for root, dirs, files in os.walk(folder):
                if any(part.startswith('.') for part in root.split(os.sep)):
                    continue
                depth = root.count(os.sep) - folder.count(os.sep)
                if depth > 4:
                    continue

                for f in files:
                    if file_type and not f.lower().endswith(file_type):
                        continue
                    file_words = split_words(f)
                    score = file_match_score(query_words, file_words, ext)
                    if score > 0:
                        matches.append({
                            'name': f,
                            'path': os.path.join(root, f),
                            'type': 'file',
                            'score': score,
                            'ext': os.path.splitext(f)[1].lower()
                        })
        except Exception:
            pass

    matches = sorted(matches, key=lambda m: (-m['score'], ext and m['ext'] == f'.{ext}', m['name']))
    return matches

# ------------------------------------------------------------------ LLM Helpers
def get_configured_ai_provider():
    for p in ["groq", "gemini", "openrouter", "openai", "mistral", "cohere"]:
        key = providers.load_key(p, SCRIPT_DIR)
        if key:
            model = providers.PROVIDERS[p]["default_model"]
            return p, model, key
    return None, None, None


def llm_parse_command(command):
    provider, model, key = get_configured_ai_provider()
    if not provider:
        return None, None

    prompt = (
        "You are a desktop voice assistant intent parser. Given the user's spoken command, extract the intent as one of:\n"
        "'open_folder', 'open_website', 'search', 'open_file', 'open_app', 'close_app', 'close_folder', 'close_file', 'close_website'.\n"
        "Rules:\n"
        "- If user says 'folder' at the end, use 'open_folder' or 'close_folder'.\n"
        "- If user says 'file' or document/pdf/txt, use 'open_file' or 'close_file'.\n"
        "- If user says 'app' or executable name, use 'open_app' or 'close_app'.\n"
        "- If user says website or web service (e.g., youtube, gmail, codechef, chatgpt), use 'open_website' or 'close_website'.\n"
        "- If user says search/google for something, use 'search'.\n"
        "Respond ONLY in valid lowercase JSON: {\"intent\": \"...\", \"target\": \"...\"}.\n"
        f"User command: '{command}'"
    )
    
    try:
        reply = providers.call(provider, key, model, [{"role": "user", "content": prompt}])
        match = re.search(r'\{\s*"intent"\s*:\s*"([a-z_]+)"\s*,\s*"target"\s*:\s*"([^"]+)"\s*\}', reply, re.IGNORECASE)
        if match:
            return match.group(1).lower(), match.group(2).lower()
        parsed = json.loads(reply)
        return parsed.get("intent"), parsed.get("target")
    except Exception as e:
        print(f"[Desktop Assistant LLM Parse Error] {e}")
        return None, None


def llm_choose_best_match(command, candidates):
    provider, model, key = get_configured_ai_provider()
    if not provider or not candidates:
        return None

    options = '\n'.join([f"{i+1}. {c['name']} ({c['type']}) in {c['path']}" for i, c in enumerate(candidates)])
    prompt = (
        f"User command: '{command}'. Possible matching candidates on computer:\n{options}\n"
        "Which candidate is the best match? Respond ONLY with the single number of the best match (e.g. '1')."
    )
    try:
        reply = providers.call(provider, key, model, [{"role": "user", "content": prompt}])
        match = re.search(r'(\d+)', reply)
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]['path']
    except Exception as e:
        print(f"[Desktop Assistant LLM Tie-Break Error] {e}")
    return None

# ------------------------------------------------------------------ Local Regex Parser
def local_parse_command(command):
    cmd = command.lower().strip()

    # Web & Chrome
    if re.search(r'open (.+?) (in chrome|website|in browser|on web)', cmd):
        match = re.search(r'open (.+?) (in chrome|website|in browser|on web)', cmd)
        if match:
            site = match.group(1).replace(' ', '').replace('dot', '.').replace('www.', '')
            return 'open_website', site

    if re.search(r'close (.+?) (in chrome|website|in browser|on web)', cmd):
        match = re.search(r'close (.+?) (in chrome|website|in browser|on web)', cmd)
        if match:
            site = match.group(1).replace(' ', '').replace('dot', '.').replace('www.', '')
            return 'close_website', site

    # Close commands
    match = re.match(r'(?:close|stop|quit|exit) (.+) app$', cmd)
    if match:
        return 'close_app', match.group(1).strip()
    match = re.match(r'(?:close|stop|quit|exit) (.+) folder$', cmd)
    if match:
        return 'close_folder', match.group(1).strip()
    match = re.match(r'(?:close|stop|quit|exit) (.+) file$', cmd)
    if match:
        return 'close_file', match.group(1).strip()
    match = re.match(r'(?:close|stop|quit|exit) (.+)$', cmd)
    if match:
        return 'close_any', match.group(1).strip()

    # Open commands
    match = re.match(r'(?:open|launch|start|run) (.+) app$', cmd)
    if match:
        return 'open_app', match.group(1).strip()
    match = re.match(r'(?:open|launch|start|show) (.+) folder$', cmd)
    if match:
        return 'open_folder', match.group(1).strip()
    match = re.match(r'(?:open|launch|start|show) (.+) file$', cmd)
    if match:
        return 'open_file', match.group(1).strip()
    match = re.match(r'(?:search for|google for|search) (.+)', cmd)
    if match:
        return 'search', match.group(1).strip()
    match = re.match(r'(?:open|launch|start|show) (.+)$', cmd)
    if match:
        return 'open_any', match.group(1).strip()

    return None, None


def parse_command(command):
    intent, target = local_parse_command(command)
    if intent is not None:
        return intent, target
    return llm_parse_command(command)

# ------------------------------------------------------------------ Actions Implementation
def system_open_path(path):
    system = platform.system()
    if system == 'Windows':
        os.startfile(path)
    elif system == 'Darwin':
        subprocess.run(['open', path])
    elif system == 'Linux':
        subprocess.run(['xdg-open', path])


def open_app_action(app_name, index=None, original_command=None):
    index = index or build_index()
    app_norm = normalize_name(app_name)
    system = platform.system()

    # 1. System app map
    for key, sys_app in SYSTEM_APP_MAP.items():
        if app_norm == normalize_name(key) or app_norm in normalize_name(key):
            if system == 'Darwin':
                subprocess.run(['open', '-a', sys_app])
                return True, f"Opened system app: {sys_app}"
            elif system == 'Windows':
                if sys_app.startswith('ms-settings'):
                    webbrowser.open(sys_app)
                else:
                    subprocess.Popen(sys_app, shell=True)
                return True, f"Opened system app: {sys_app}"
            elif system == 'Linux':
                subprocess.Popen([sys_app])
                return True, f"Opened system app: {sys_app}"

    # 2. Web app map
    for key, url in WEB_APP_MAP.items():
        if app_norm == normalize_name(key) or normalize_name(key) in app_norm:
            webbrowser.open(url)
            return True, f"Opened web app: {key.title()} ({url})"

    # 3. Local indexed apps
    candidates = []
    for name, path in index.get('apps', []):
        if app_norm in normalize_name(name):
            candidates.append({'name': name, 'path': path, 'type': 'local_app'})

    if candidates:
        if len(candidates) > 1 and original_command:
            best_path = llm_choose_best_match(original_command, candidates[:5])
            chosen_path = best_path if best_path else candidates[0]['path']
        else:
            chosen_path = candidates[0]['path']
        
        system_open_path(chosen_path)
        return True, f"Opened application: {os.path.basename(chosen_path)}"

    # 4. Fallback AppOpener
    try:
        from AppOpener import open as app_open
        app_open(app_name, match_closest=True, output=False)
        return True, f"Opened application: {app_name.title()}"
    except Exception:
        pass

    return False, f"Could not find or open application: '{app_name}'."


def open_folder_action(folder_name, index=None):
    index = index or build_index()
    key = folder_name.lower().replace(' folder', '').replace('the ', '').strip()

    # 1. Hardcoded standard user folder check
    if key in HARDCODED_FOLDERS:
        path = HARDCODED_FOLDERS[key]
        if os.path.exists(path):
            system_open_path(path)
            return True, f"Opened folder: {path}"

    # 2. Indexed folder search
    query_norm = normalize_name(folder_name)
    candidates = []
    for name, path in index.get('folders', []):
        if query_norm in normalize_name(name):
            candidates.append({'name': name, 'path': path})

    if candidates:
        chosen_path = candidates[0]['path']
        system_open_path(chosen_path)
        return True, f"Opened folder: {chosen_path}"

    return False, f"Could not locate folder: '{folder_name}'."


def open_file_action(file_name, index=None, original_command=None):
    candidates = deep_file_search(file_name)
    if not candidates:
        return False, f"Could not find file matching: '{file_name}'."

    top_score = candidates[0]['score']
    top_candidates = [c for c in candidates if c['score'] == top_score]
    if len(top_candidates) > 1 and original_command:
        best_path = llm_choose_best_match(original_command, top_candidates[:5])
        chosen_path = best_path if best_path else top_candidates[0]['path']
    else:
        chosen_path = candidates[0]['path']

    if os.path.exists(chosen_path):
        system_open_path(chosen_path)
        return True, f"Opened file: {chosen_path}"
    return False, f"Path found but does not exist: {chosen_path}"


def open_website_action(site, original_command=None):
    site_clean = site.lower().strip().replace(' ', '')
    url = None

    # Presets
    for k, v in WEB_APP_MAP.items():
        if site_clean in normalize_name(k) or normalize_name(k) in site_clean:
            url = v
            break

    if not url:
        if site_clean.startswith('http'):
            url = site_clean
        elif '.' in site_clean:
            url = f"https://{site_clean}"
        else:
            url = f"https://www.{site_clean}.com"

    webbrowser.open(url)
    return True, f"Opened website: {url}"


def open_search_action(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return True, f"Searching Google for: '{query}'"


def close_app_action(app_name):
    system = platform.system()
    if system == 'Darwin':
        script = f'tell application "{app_name}" to quit'
        subprocess.run(['osascript', '-e', script])
        return True, f"Closed application: {app_name}"
    elif system == 'Windows':
        try:
            # Try taskkill
            subprocess.run(f"taskkill /f /im {app_name}.exe", shell=True, capture_output=True)
            # Try AppOpener close fallback
            try:
                from AppOpener import close as app_close
                app_close(app_name, match_closest=True, output=False)
            except Exception:
                pass
            return True, f"Closed application: {app_name}"
        except Exception as e:
            return False, f"Error closing app {app_name}: {e}"
    else:
        subprocess.run(['killall', app_name])
        return True, f"Closed application: {app_name}"


def close_folder_action(folder_name):
    system = platform.system()
    if system == 'Darwin':
        script = f'''
tell application "Finder"
    set folderName to "{folder_name.lower()}"
    repeat with aWin in (every window)
        try
            set tPath to (POSIX path of (target of aWin as alias)) as text
            if (lowercase tPath) contains folderName then close aWin
        end try
    end repeat
end tell'''
        subprocess.run(['osascript', '-e', script])
        return True, f"Closed Finder folder window matching: {folder_name}"
    elif system == 'Windows':
        # Close explorer windows with folder name in title
        cmd = f'powershell "(New-Object -ComObject Shell.Application).Windows() | Where-Object {{ $_.LocationName -like \'*{folder_name}*\' }} | ForEach-Object {{ $_.Quit() }}"'
        subprocess.run(cmd, shell=True)
        return True, f"Closed Explorer folder window matching: {folder_name}"
    return True, f"Close folder request processed for {folder_name}"


def close_file_action(file_name):
    system = platform.system()
    if system == 'Darwin':
        script = f'tell application "System Events" to set the visible of every process whose name contains "{file_name}" to false'
        subprocess.run(['osascript', '-e', script])
        return True, f"Hidden/closed file window matching: {file_name}"
    elif system == 'Windows':
        close_app_action(file_name)
        return True, f"Attempted closing file window matching: {file_name}"
    return True, f"Closed file matching {file_name}"


def close_chrome_tab_action(site):
    system = platform.system()
    if system == 'Darwin':
        script = f'''
tell application "Google Chrome"
    set siteText to "{site.lower()}"
    repeat with aWindow in (every window)
        repeat with atab in (every tab of aWindow)
            if (URL of atab as text) contains siteText or (title of atab as text) contains siteText then close atab
        end repeat
    end repeat
end tell'''
        subprocess.run(['osascript', '-e', script])
        return True, f"Closed browser tab matching: {site}"
    return True, f"Closed browser tab matching: {site}"

# ------------------------------------------------------------------ Master Handler
def handle_desktop_command(command, index=None):
    """
    Main entry point for processing voice desktop commands.
    Returns (handled: bool, response_message: str).
    """
    if not command or not command.strip():
        return False, ""

    cmd = command.strip()
    index = index or build_index()

    intent, target = parse_command(cmd)
    if not intent or not target:
        return False, ""

    print(f"[Desktop Assistant] Intent: '{intent}' | Target: '{target}'")

    if intent == 'open_folder':
        return open_folder_action(target, index)
    elif intent == 'open_website':
        return open_website_action(target, cmd)
    elif intent == 'search':
        return open_search_action(target)
    elif intent == 'open_file':
        return open_file_action(target, index, cmd)
    elif intent == 'open_app':
        return open_app_action(target, index, cmd)
    elif intent == 'open_any':
        # Check if local app match exists first
        if find_best_match(target, index, kind='apps') or target.lower() in SYSTEM_APP_MAP or target.lower() in WEB_APP_MAP:
            return open_app_action(target, index, cmd)
        else:
            return open_website_action(target, cmd)
    elif intent == 'close_app':
        return close_app_action(target)
    elif intent == 'close_folder':
        return close_folder_action(target)
    elif intent == 'close_file':
        return close_file_action(target)
    elif intent == 'close_website':
        return close_chrome_tab_action(target)
    elif intent == 'close_any':
        close_app_action(target)
        close_folder_action(target)
        close_file_action(target)
        close_chrome_tab_action(target)
        return True, f"Closed all instances and windows matching: '{target}'"

    return False, ""
