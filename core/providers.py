"""
Multi-provider AI backend for NEXUS Chat.
Supports Groq, Gemini, OpenRouter, and OpenAI (ChatGPT API) behind one
common interface. All conversation history is kept internally in
OpenAI-style format:
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
        "suggested_models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
    },
    "gemini": {
        "label": "Gemini",
        "env_key": "GEMINI_API_KEY",
        "default_model": "gemini-3.6-flash",
        "suggested_models": ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"],
    },
    "openrouter": {
        "label": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
        "suggested_models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
            "deepseek/deepseek-r1:free",
            "qwen/qwen-2.5-72b-instruct",
        ],
    },
    "openai": {
        "label": "OpenAI (ChatGPT)",
        "env_key": "OPENAI_API_KEY",
        "default_model": "gpt-4o",
        "suggested_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
    },
    "mistral": {
        "label": "Mistral",
        "env_key": "MISTRAL_API_KEY",
        "default_model": "mistral-small-latest",
        "suggested_models": ["mistral-small-latest", "mistral-large-latest", "open-mistral-nemo"],
    },
    "cohere": {
        "label": "Cohere",
        "env_key": "COHERE_API_KEY",
        "default_model": "command-r-08-2024",
        "suggested_models": ["command-r-08-2024", "command-r-plus-08-2024"],
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


def call_openai(api_key, model, messages):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "temperature": 0.7}
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers, json=payload, timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


def call_mistral(api_key, model, messages):
    # Mistral's La Plateforme API is OpenAI-compatible, same shape as Groq/OpenRouter.
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "temperature": 0.7}
    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers, json=payload, timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Mistral API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"]


def call_cohere(api_key, model, messages):
    # Cohere's v2 chat endpoint accepts an OpenAI-style messages array but
    # returns its own response shape: message.content is a list of typed
    # blocks (usually one {"type": "text", "text": "..."} block), not the
    # OpenAI choices[0].message.content string shape.
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}
    resp = requests.post(
        "https://api.cohere.com/v2/chat",
        headers=headers, json=payload, timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Cohere API error {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    try:
        blocks = data["message"]["content"]
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    except (KeyError, IndexError):
        raise RuntimeError(f"Cohere returned no usable content: {data}")


CALL_FUNCTIONS = {
    "groq": call_groq,
    "gemini": call_gemini,
    "openrouter": call_openrouter,
    "openai": call_openai,
    "mistral": call_mistral,
    "cohere": call_cohere,
}


def call(provider, api_key, model, messages):
    return CALL_FUNCTIONS[provider](api_key, model, messages)
