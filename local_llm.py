"""
Local (offline) LLM fallback for NEXUS Chat.

Every cloud provider (Groq/Gemini/OpenRouter/OpenAI/Mistral/Cohere) needs
internet. When there's none, NEXUS checks first and falls back to a small
quantized model running entirely on-device via llama.cpp, instead of just
failing. This is a real trade-off, not a free upgrade: an on-device 1-3B
model is much weaker than any of the cloud models — it's there so NEXUS can
still respond with something when there's genuinely no signal, not to
replace the cloud models day-to-day.

This only applies to the terminal app (nexuschat.py). It does NOT apply to
api.py: if the device has no internet, the cloudflared/ngrok tunnel that
lets the Lovable frontend reach the device is also down, so the frontend
can't send a request to the API at all in that situation — there's no
"offline API" case to fall back inside of.

--------------------------------------------------------------------------
ONE-TIME SETUP (real disk space + compile time — do this on Wi-Fi, once):

    pkg install clang cmake git -y
    git clone https://github.com/ggml-org/llama.cpp ~/nexuschat/llama.cpp
    cd ~/nexuschat/llama.cpp
    cmake -B build && cmake --build build --config Release -j4
    # produces: ~/nexuschat/llama.cpp/build/bin/llama-cli

Then download ONE small GGUF model (pick based on your phone's RAM):
    mkdir -p ~/nexuschat/models
    cd ~/nexuschat/models
    # e.g. Qwen2.5-1.5B-Instruct (~1GB at Q4_K_M) is a reasonable phone-sized
    # default — search "Qwen2.5-1.5B-Instruct-GGUF" on Hugging Face and
    # download the Q4_K_M .gguf file into this folder.

NEXUS auto-detects the first .gguf file in ~/nexuschat/models/. To pin a
specific one (or a custom llama.cpp build location), set in .env:
    LLAMA_CLI_PATH=/absolute/path/to/llama-cli
    LOCAL_MODEL_PATH=/absolute/path/to/your-model.gguf
--------------------------------------------------------------------------
"""

import os
import socket
import subprocess

DEFAULT_LLAMA_CLI = os.path.expanduser("~/nexuschat/llama.cpp/build/bin/llama-cli")
DEFAULT_MODEL_DIR = os.path.expanduser("~/nexuschat/models")


def is_online(timeout=2.5):
    """
    Quick, cheap connectivity check: tries a raw TCP connection to a couple
    of fast, reliable hosts. This confirms the device has a working network
    path — not that any specific provider's API is currently reachable
    (that's still handled by the normal try/except around the API call).
    """
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 443)):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def _resolve_paths():
    llama_cli = os.environ.get("LLAMA_CLI_PATH", DEFAULT_LLAMA_CLI)
    model_path = os.environ.get("LOCAL_MODEL_PATH")
    if not model_path and os.path.isdir(DEFAULT_MODEL_DIR):
        for filename in sorted(os.listdir(DEFAULT_MODEL_DIR)):
            if filename.endswith(".gguf"):
                model_path = os.path.join(DEFAULT_MODEL_DIR, filename)
                break
    return llama_cli, model_path


def is_configured():
    """True only if both the compiled binary and a model file actually exist."""
    llama_cli, model_path = _resolve_paths()
    return bool(llama_cli and os.path.exists(llama_cli) and model_path and os.path.exists(model_path))


def _flatten_messages(messages):
    """llama-cli takes a plain-text prompt, not a chat-message list — flatten it."""
    lines = []
    for m in messages:
        role, content = m["role"], m["content"]
        if role == "system":
            lines.append(f"[Instructions]\n{content}\n")
        elif role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")
    lines.append("Assistant:")
    return "\n".join(lines)


def generate_local(messages, max_tokens=512, timeout=180):
    """Run inference entirely offline. Raises RuntimeError with a clear message if not set up."""
    llama_cli, model_path = _resolve_paths()
    if not llama_cli or not os.path.exists(llama_cli):
        raise RuntimeError(
            "No local model set up (llama.cpp binary not found). See the setup "
            "instructions at the top of local_llm.py — this needs a one-time compile."
        )
    if not model_path or not os.path.exists(model_path):
        raise RuntimeError(
            "No local model set up (no .gguf file found in ~/nexuschat/models/)."
        )

    prompt = _flatten_messages(messages)
    result = subprocess.run(
        [llama_cli, "-m", model_path, "-p", prompt, "-n", str(max_tokens),
         "--temp", "0.7", "-no-cnv"],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Local model failed: {result.stderr[-300:]}")

    output = result.stdout
    if prompt in output:
        output = output.split(prompt, 1)[1]
    return output.strip()
