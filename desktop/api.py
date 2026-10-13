"""
REST API Gateway for NEXUS v2 Desktop Assistant.
Serves the HUD frontend, manages streaming and non-streaming chat requests
routed through the tool-calling agent loop, handles safety confirmations,
and provides memory endpoints.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import sys
from typing import Any, Generator

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

from core.agent import run_agent
from core.config import get_available_providers, get_config, get_default_chain, load_config
from core.db import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    get_messages,
    init_db,
    list_conversations,
    rename_conversation,
)
from core.identity import CORE_SYSTEM_PROMPT
from core.imagegen import IMAGES_DIR
from core.llm import chat_stream, load_key
from core.memory import clear_memory, delete_fact, list_facts, remember
from core.router import route
from core.tools import get_all_tools
from desktop.safety import (
    approve_confirmation,
    deny_confirmation,
    get_confirmation,
    get_pending_confirmations,
)

logger = logging.getLogger("nexus.desktop.api")

PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(PROJ_ROOT, "frontend", "static")
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = os.path.join(PROJ_ROOT, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")

# Strict localhost CORS
CORS(app, resources={r"/*": {"origins": [r"http://127\.0\.0\.1:.*", r"http://localhost:.*"]}})


# ---------------------------------------------------------------------------
# Auth Helper
# ---------------------------------------------------------------------------

def _ensure_api_key() -> str:
    key = os.environ.get("NEXUS_API_KEY")
    if not key:
        env_path = os.path.join(PROJ_ROOT, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("NEXUS_API_KEY="):
                        key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not key:
            key = secrets.token_urlsafe(32)
            try:
                with open(env_path, "a", encoding="utf-8") as f:
                    f.write(f"\nNEXUS_API_KEY={key}\n")
            except Exception:
                pass
        os.environ["NEXUS_API_KEY"] = key
    return key


@app.before_request
def check_auth():
    if request.method == "OPTIONS":
        return
    # Public endpoints
    if request.path in ("/", "/health", "/favicon.ico") or request.path.startswith("/static"):
        return

    expected = _ensure_api_key()
    provided = request.headers.get("X-API-Key") or request.args.get("key", "")
    if provided != expected:
        return jsonify({"error": "Invalid or missing API key."}), 401


# ---------------------------------------------------------------------------
# Frontend Static & Images
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "environment": "desktop",
    })


@app.route("/images/<path:filename>", methods=["GET"])
def serve_image(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        return jsonify({"error": "Invalid filename"}), 400
    return send_from_directory(IMAGES_DIR, filename)


# ---------------------------------------------------------------------------
# Providers & Tools
# ---------------------------------------------------------------------------

@app.route("/providers", methods=["GET"])
def list_providers_endpoint():
    providers_cfg = get_available_providers()
    out = []
    for pid, meta in providers_cfg.items():
        has_key = bool(load_key(pid))
        out.append({
            "id": pid,
            "label": pid.title(),
            "default_model": meta.get("default_model", ""),
            "suggested_models": meta.get("suggested_models", []),
            "has_key": has_key,
        })
    return jsonify(out)


@app.route("/tools", methods=["GET"])
def list_tools_endpoint():
    return jsonify(get_all_tools())


# ---------------------------------------------------------------------------
# Chat & Agent Endpoints
# ---------------------------------------------------------------------------

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    conv_id = data.get("conversation_id")
    provider_id = data.get("provider")

    if not messages:
        return jsonify({"error": "messages array is required"}), 400

    # Extract user text to route and log
    user_query = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_query = m.get("content", "")
            break

    # Smart routing
    task_type, chain = route(user_query)

    try:
        agent_result = run_agent(
            messages=messages,
            provider_id=provider_id,
            fallback_chain=chain,
            system_prompt=CORE_SYSTEM_PROMPT,
        )

        # Persist to database if conversation_id provided
        if conv_id:
            try:
                add_message(conv_id, "user", user_query)
                add_message(conv_id, "assistant", agent_result.reply)
            except Exception as e:
                logger.debug("Failed saving messages to DB: %s", e)

        return jsonify({
            "reply": agent_result.reply,
            "task_type": task_type,
            "chain_used": chain,
            "tool_log": agent_result.tool_log,
        })
    except Exception as exc:
        logger.error("Chat execution failed: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@app.route("/chat/stream", methods=["POST"])
def chat_stream_endpoint():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    provider_id = data.get("provider") or get_default_chain()[0]

    def generate_events() -> Generator[str, None, None]:
        try:
            for chunk in chat_stream(provider_id=provider_id, messages=messages):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return Response(generate_events(), mimetype="text/event-stream")


# ---------------------------------------------------------------------------
# Safety Confirmations Endpoints
# ---------------------------------------------------------------------------

@app.route("/confirm/pending", methods=["GET"])
def get_pending_confirm_endpoint():
    return jsonify(get_pending_confirmations())


@app.route("/confirm", methods=["POST"])
def process_confirm_endpoint():
    data = request.get_json(silent=True) or {}
    conf_id = data.get("confirmation_id")
    action = data.get("action", "approve")

    if not conf_id:
        return jsonify({"error": "confirmation_id is required"}), 400

    try:
        if action == "approve":
            res = approve_confirmation(conf_id)
        else:
            res = deny_confirmation(conf_id)
        return jsonify(res)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


# ---------------------------------------------------------------------------
# Conversations CRUD
# ---------------------------------------------------------------------------

@app.route("/conversations", methods=["GET"])
def list_convs():
    init_db()
    return jsonify(list_conversations())


@app.route("/conversations", methods=["POST"])
def create_conv():
    init_db()
    data = request.get_json(silent=True) or {}
    cid = create_conversation(data.get("title", "New Chat"))
    return jsonify({"id": cid})


@app.route("/conversations/<int:cid>/messages", methods=["GET"])
def get_conv_messages(cid: int):
    init_db()
    return jsonify(get_messages(cid))


@app.route("/conversations/<int:cid>", methods=["DELETE"])
def remove_conv(cid: int):
    init_db()
    delete_conversation(cid)
    return jsonify({"status": "deleted"})


# ---------------------------------------------------------------------------
# Long-Term Memory Endpoints
# ---------------------------------------------------------------------------

@app.route("/memory", methods=["GET"])
def get_memories():
    return jsonify(list_facts(limit=100))


@app.route("/memory", methods=["POST"])
def add_memory_fact():
    data = request.get_json(silent=True) or {}
    fact = data.get("fact", "").strip()
    category = data.get("category", "general")
    if not fact:
        return jsonify({"error": "fact is required"}), 400
    stored = remember(fact, category)
    return jsonify({"stored": stored})


@app.route("/memory/<int:fid>", methods=["DELETE"])
def remove_memory_fact(fid: int):
    success = delete_fact(fid)
    return jsonify({"deleted": success})


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Run Flask development server bound securely to localhost."""
    if host not in ("127.0.0.1", "localhost"):
        logger.warning("WARNING: Binding to %s is insecure. Defaulting to 127.0.0.1.", host)
        host = "127.0.0.1"

    init_db()
    _ensure_api_key()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
