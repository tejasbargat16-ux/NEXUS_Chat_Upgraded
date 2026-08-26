"""
Multi-provider AI backend for NEXUS Chat.
Supports Groq, Gemini, and OpenRouter behind one common interface.
All conversation history is kept internally in OpenAI-style format:
    [{"role": "system"|"user"|"assistant", "content": "..."}]
Each provider function translates that into whatever shape its API needs.
"""

import os
import requests

PROVIDERS = {
    "groq": {
        "label": "Groq",
        "env_key": "GROQ_API_KEY",
        "default_model": "openai/gpt-oss-120b",
        "suggested_models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
    },
    "gemini": {
        "label": "Gemini",
        "env_key": "GEMINI_API_KEY",
        "default_model": "gemini-2.5-flash",
        "suggested_models": ["gemini-2.5-flash", "gemini-3.6-flash"],
    },
    "openrouter": {
        "label": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "suggested_models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "openai/gpt-4o-mini",
            "google/gemini-2.5-flash",
        ],
    },
}


def load_key(provider, script_dir):
    """Look for the provider's key in the environment, then in a local .env file."""
    env_var = PROVIDERS[provider]["env_key"]
    key = os.environ.get(env_var)
    if key:
        return key
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(env_var + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def call_groq(api_key, model, messages):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "temperature": 0.7}
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=payload, timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


def call_openrouter(api_key, model, messages):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "temperature": 0.7}
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers, json=payload, timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


def call_gemini(api_key, model, messages):
    # Gemini uses "user"/"model" roles and a separate systemInstruction field,
    # so we translate from the internal OpenAI-style format here.
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    contents = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {"contents": contents}
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": system_parts[0]}]}

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"Gemini returned no usable content: {data}")


CALL_FUNCTIONS = {
    "groq": call_groq,
    "gemini": call_gemini,
    "openrouter": call_openrouter,
}


def call(provider, api_key, model, messages):
    return CALL_FUNCTIONS[provider](api_key, model, messages)
