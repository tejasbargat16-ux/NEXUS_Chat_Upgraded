"""
Web search for NEXUS Chat.

Uses Tavily (https://tavily.com) if TAVILY_API_KEY is set — it's built for
AI agents and returns clean, ranked results. Falls back to a keyless
DuckDuckGo HTML scrape so search works out of the box with zero signup.

Tavily free tier: sign up at https://tavily.com, no card required, generous
monthly quota for personal projects.
"""

import html
import os
import re

import requests

TAVILY_URL = "https://api.tavily.com/search"
DDG_URL = "https://html.duckduckgo.com/html/"

_RESULT_BLOCK_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
    r'class="result__snippet"[^>]*>(.*?)</a>',
    re.DOTALL,
)


def _load_tavily_key(script_dir):
    key = os.environ.get("TAVILY_API_KEY")
    if key:
        return key
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("TAVILY_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _strip_tags(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def search_tavily(query, api_key, max_results=5):
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }
    resp = requests.post(TAVILY_URL, json=payload, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"Tavily error {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    results = []
    for item in data.get("results", [])[:max_results]:
        results.append({
            "title": item.get("title", "") or "(untitled)",
            "url": item.get("url", ""),
            "snippet": (item.get("content", "") or "")[:400],
        })
    return results


def search_duckduckgo(query, max_results=5):
    resp = requests.post(
        DDG_URL,
        data={"q": query},
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (compatible; NEXUS-Chat/1.0)"},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"DuckDuckGo search error {resp.status_code}")

    results = []
    for match in _RESULT_BLOCK_RE.finditer(resp.text):
        url, title_html, snippet_html = match.groups()
        results.append({
            "title": _strip_tags(title_html) or "(untitled)",
            "url": url,
            "snippet": _strip_tags(snippet_html)[:400],
        })
        if len(results) >= max_results:
            break
    return results


def web_search(query, script_dir, max_results=5):
    """
    Search the web. Returns (source_name, results). Tries Tavily first if a
    key is configured; falls back to keyless DuckDuckGo on any failure or if
    no Tavily key is set.
    """
    tavily_key = _load_tavily_key(script_dir)
    if tavily_key:
        try:
            return "tavily", search_tavily(query, tavily_key, max_results)
        except Exception:
            pass  # fall through to the keyless option
    return "duckduckgo", search_duckduckgo(query, max_results)


def format_results(source, results):
    if not results:
        return f"No results found (source: {source})."
    lines = [f"Search results (via {source}):"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}\n   {r['url']}\n   {r['snippet']}")
    return "\n".join(lines)
