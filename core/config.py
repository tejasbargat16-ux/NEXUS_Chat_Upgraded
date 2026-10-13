"""
Configuration loader and validator for NEXUS v2.
Loads config.yaml and applies environment variable overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

_CONFIG: dict[str, Any] | None = None
_CONFIG_PATH: str | None = None


def find_config() -> str:
    """Locate config.yaml relative to this file or the project root."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(here), "config.yaml"),  # project root
        os.path.join(here, "config.yaml"),
        os.path.join(os.getcwd(), "config.yaml"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("config.yaml not found in project root or core/")


def load_config(path: str | None = None, reload: bool = False) -> dict[str, Any]:
    """Load, cache, and return the YAML configuration."""
    global _CONFIG, _CONFIG_PATH
    if _CONFIG is not None and path is None and not reload:
        return _CONFIG

    cfg_path = path or find_config()
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    _CONFIG = data
    _CONFIG_PATH = cfg_path
    return _CONFIG


def get_config() -> dict[str, Any]:
    """Return the loaded configuration, loading if necessary."""
    return load_config()


def get_providers() -> dict[str, dict[str, Any]]:
    """Return dictionary of all configured providers."""
    return get_config().get("providers", {})


get_available_providers = get_providers


def get_provider_config(provider_id: str) -> dict[str, Any]:
    """Return configuration block for a specific provider."""
    providers = get_providers()
    if provider_id not in providers:
        raise ValueError(f"Unknown provider '{provider_id}'. Available: {list(providers)}")
    return providers[provider_id]


def get_routes() -> dict[str, list[str]]:
    """Return task routing definitions."""
    return get_config().get("routes", {})


def get_route_chain(route_name: str) -> list[str]:
    """Return the provider chain for a given route name, or default_chain."""
    cfg = get_config()
    routes = cfg.get("routes", {})
    if route_name in routes:
        return list(routes[route_name])
    return get_default_chain()


def get_default_chain() -> list[str]:
    """Return the default fallback chain."""
    cfg = get_config()
    return list(cfg.get("default_chain", ["groq", "gemini", "openrouter", "openai"]))


def get_agent_settings() -> dict[str, Any]:
    """Return agent configuration settings."""
    cfg = get_config()
    return cfg.get("agent", {
        "max_steps": 6,
        "result_truncation": 4000,
    })


def get_voice_settings() -> dict[str, Any]:
    """Return voice configuration settings."""
    cfg = get_config()
    return cfg.get("voice", {
        "wake_word_enabled": False,
        "tts_engine": "pyttsx3",
        "stt_engine": "groq-whisper",
    })
