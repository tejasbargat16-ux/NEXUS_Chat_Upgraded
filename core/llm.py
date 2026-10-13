"""
Unified multi-provider LLM client for NEXUS v2.

ONE OpenAI-compatible client for Groq, OpenRouter, Mistral, OpenAI, and
Gemini (via its OpenAI-compatible endpoint). Cohere handled as a special
case (accepts OpenAI messages, returns a different response shape).

Supports: non-streaming, SSE streaming, and native tool/function calling.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Generator

import requests
import yaml

logger = logging.getLogger("nexus.llm")

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

_CONFIG: dict | None = None
_CONFIG_PATH: str | None = None


def _find_config() -> str:
    """Locate config.yaml relative to this file or the project root."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(here), "config.yaml"),  # project root
        os.path.join(here, "config.yaml"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("config.yaml not found in project root or core/")


def load_config(path: str | None = None) -> dict:
    """Load and cache the YAML configuration."""
    global _CONFIG, _CONFIG_PATH
    if _CONFIG is not None and path is None:
        return _CONFIG
    cfg_path = path or _find_config()
    with open(cfg_path, "r", encoding="utf-8") as f:
        _CONFIG = yaml.safe_load(f)
    _CONFIG_PATH = cfg_path
    return _CONFIG


def get_provider_config(provider_id: str) -> dict:
    """Return the provider block from config.yaml."""
    cfg = load_config()
    providers = cfg.get("providers", {})
    if provider_id not in providers:
        raise ValueError(f"Unknown provider '{provider_id}'. Available: {list(providers)}")
    return providers[provider_id]


def get_available_providers() -> dict[str, dict]:
    """Return all provider configs."""
    return load_config().get("providers", {})


# ---------------------------------------------------------------------------
# Key loading
# ---------------------------------------------------------------------------

def _load_dotenv_key(env_var: str) -> str | None:
    """Try loading a key from .env if not in os.environ."""
    key = os.environ.get(env_var)
    if key:
        return key
    # Search for .env in project root
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    for env_dir in (root, here):
        env_path = os.path.join(env_dir, ".env")
        if os.path.isfile(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(env_var + "="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def load_key(provider_id: str) -> str | None:
    """Load the API key for a provider from env or .env file."""
    pcfg = get_provider_config(provider_id)
    return _load_dotenv_key(pcfg["env_key"])


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _build_headers(provider_id: str, api_key: str) -> dict[str, str]:
    """Build auth headers based on the provider's auth_style."""
    pcfg = get_provider_config(provider_id)
    auth_style = pcfg.get("auth_style", "bearer")
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_style == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    elif auth_style == "x-goog-api-key":
        headers["x-goog-api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _chat_url(provider_id: str) -> str:
    """Build the chat completions endpoint URL."""
    pcfg = get_provider_config(provider_id)
    base = pcfg["base_url"].rstrip("/")
    response_style = pcfg.get("response_style", "")
    if response_style == "cohere":
        return f"{base}/chat"
    return f"{base}/chat/completions"


def _is_cohere(provider_id: str) -> bool:
    """Check if the provider uses Cohere's response format."""
    pcfg = get_provider_config(provider_id)
    return pcfg.get("response_style") == "cohere"


# ---------------------------------------------------------------------------
# Non-streaming chat
# ---------------------------------------------------------------------------

def chat(
    provider_id: str,
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    api_key: str | None = None,
    timeout: int = 60,
) -> dict:
    """Send a chat completion request. Returns the full response message dict.

    Returns:
        dict with keys: 'role', 'content', and optionally 'tool_calls'.
    """
    key = api_key or load_key(provider_id)
    if not key:
        raise RuntimeError(f"No API key configured for provider '{provider_id}'")

    pcfg = get_provider_config(provider_id)
    mdl = model or pcfg["default_model"]
    url = _chat_url(provider_id)
    headers = _build_headers(provider_id, key)

    payload: dict[str, Any] = {
        "model": mdl,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        payload["tools"] = tools

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(
            f"{provider_id} API error {resp.status_code}: {resp.text[:300]}"
        )

    data = resp.json()

    # Parse response based on provider
    if _is_cohere(provider_id):
        return _parse_cohere_response(data)
    return _parse_openai_response(data)


def _parse_openai_response(data: dict) -> dict:
    """Parse standard OpenAI-format response into a message dict."""
    try:
        msg = data["choices"][0]["message"]
        result: dict[str, Any] = {
            "role": msg.get("role", "assistant"),
            "content": msg.get("content") or "",
        }
        if msg.get("tool_calls"):
            result["tool_calls"] = msg["tool_calls"]
        return result
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected response format: {data}") from exc


def _parse_cohere_response(data: dict) -> dict:
    """Parse Cohere v2/chat response into a message dict."""
    try:
        blocks = data["message"]["content"]
        content = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        result: dict[str, Any] = {"role": "assistant", "content": content}
        if data["message"].get("tool_calls"):
            result["tool_calls"] = data["message"]["tool_calls"]
        return result
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Cohere response format: {data}") from exc


# ---------------------------------------------------------------------------
# Streaming chat (SSE)
# ---------------------------------------------------------------------------

def chat_stream(
    provider_id: str,
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    api_key: str | None = None,
    timeout: int = 120,
) -> Generator[dict, None, None]:
    """Stream a chat completion via SSE. Yields delta dicts.

    Each yielded dict has: 'content' (text delta) and/or 'tool_calls' (list).
    Final yield has 'done': True.
    """
    if _is_cohere(provider_id):
        # Cohere doesn't support standard SSE streaming the same way;
        # fall back to non-streaming and yield the full result.
        result = chat(provider_id, messages, model, tools, temperature, api_key, timeout)
        yield {"content": result.get("content", ""), "done": True}
        return

    key = api_key or load_key(provider_id)
    if not key:
        raise RuntimeError(f"No API key configured for provider '{provider_id}'")

    pcfg = get_provider_config(provider_id)
    mdl = model or pcfg["default_model"]
    url = _chat_url(provider_id)
    headers = _build_headers(provider_id, key)

    payload: dict[str, Any] = {
        "model": mdl,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    if tools:
        payload["tools"] = tools

    resp = requests.post(
        url, headers=headers, json=payload, timeout=timeout, stream=True
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"{provider_id} streaming error {resp.status_code}: {resp.text[:300]}"
        )

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data: "):
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                yield {"done": True}
                return
            try:
                chunk = json.loads(data_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                result: dict[str, Any] = {}
                if delta.get("content"):
                    result["content"] = delta["content"]
                if delta.get("tool_calls"):
                    result["tool_calls"] = delta["tool_calls"]
                if result:
                    yield result
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

    yield {"done": True}


# ---------------------------------------------------------------------------
# Fallback chain
# ---------------------------------------------------------------------------

def chat_with_fallback(
    chain: list[str],
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_retries: int = 2,
    backoff_factor: float = 1.0,
) -> dict:
    """Try each provider in the chain with exponential backoff.

    Returns the first successful response message dict.
    Raises RuntimeError if all providers fail.
    """
    errors: list[str] = []
    for provider_id in chain:
        key = load_key(provider_id)
        if not key:
            logger.debug("Skipping %s: no API key", provider_id)
            continue

        for attempt in range(max_retries + 1):
            try:
                return chat(
                    provider_id, messages, tools=tools,
                    temperature=temperature, api_key=key,
                )
            except Exception as exc:
                wait = (2 ** attempt) * backoff_factor
                errors.append(f"{provider_id} (attempt {attempt+1}): {exc}")
                logger.warning(
                    "%s attempt %d failed: %s (retry in %0.1fs)",
                    provider_id, attempt + 1, exc, wait,
                )
                if attempt < max_retries and wait > 0:
                    time.sleep(wait)

    raise RuntimeError(
        f"All providers in chain {chain} failed:\n" + "\n".join(errors)
    )


# ---------------------------------------------------------------------------
# Model validation (optional startup check)
# ---------------------------------------------------------------------------

def validate_models() -> list[str]:
    """Check configured models against provider /models endpoints.

    Returns a list of warning messages for models that weren't found.
    Non-fatal: some providers don't expose a /models endpoint.
    """
    warnings: list[str] = []
    cfg = load_config()
    for pid, pcfg in cfg.get("providers", {}).items():
        key = load_key(pid)
        if not key:
            continue
        base = pcfg["base_url"].rstrip("/")
        headers = _build_headers(pid, key)
        try:
            resp = requests.get(f"{base}/models", headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            model_ids = set()
            for m in data.get("data", []):
                model_ids.add(m.get("id", ""))
            if not model_ids:
                continue
            for model_name in pcfg.get("suggested_models", []):
                if model_name not in model_ids:
                    msg = f"[{pid}] Model '{model_name}' not found in /models list"
                    warnings.append(msg)
                    logger.warning(msg)
        except Exception:
            continue  # /models endpoint not available, skip
    return warnings


# ---------------------------------------------------------------------------
# Legacy compatibility shim (used by code that still imports providers.py)
# ---------------------------------------------------------------------------

# Maps old provider IDs to the new unified client
PROVIDERS = {}


def _init_compat():
    """Populate PROVIDERS dict for backward compatibility."""
    global PROVIDERS
    try:
        cfg = load_config()
    except FileNotFoundError:
        return
    for pid, pcfg in cfg.get("providers", {}).items():
        PROVIDERS[pid] = {
            "label": pid.title(),
            "env_key": pcfg["env_key"],
            "default_model": pcfg["default_model"],
            "suggested_models": pcfg.get("suggested_models", []),
        }


_init_compat()
