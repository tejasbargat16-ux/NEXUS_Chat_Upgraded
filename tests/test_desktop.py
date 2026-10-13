"""
Tests for Phase 2: Desktop automation, OS layer, 3-tier safety system, and desktop API.
"""

from unittest.mock import patch, MagicMock
import pytest

from desktop.safety import (
    check_safety,
    create_confirmation,
    get_confirmation,
    get_pending_confirmations,
    approve_confirmation,
    deny_confirmation,
    clear_confirmations,
    SAFE_TOOLS,
    CONFIRM_TOOLS,
)
from desktop.os_layer import (
    HARDCODED_FOLDERS,
    SYSTEM_APP_MAP,
    WEB_APP_MAP,
    open_app,
    close_app,
    open_folder,
    open_url,
)
from core.tools import get_all_tools, get_tool
import desktop.tools  # Registers desktop tools into registry


def test_safety_tier_classification():
    # SAFE tier
    assert check_safety("web_search") == "safe"
    assert check_safety("take_screenshot") == "safe"
    assert check_safety("open_application") == "safe"
    assert check_safety("open_folder") == "safe"
    assert check_safety("read_clipboard") == "safe"

    # CONFIRM tier
    assert check_safety("close_application") == "confirm"
    assert check_safety("lock_screen") == "confirm"
    assert check_safety("write_clipboard") == "confirm"
    assert check_safety("shell_command", {"command": "echo test"}) == "confirm"

    # REFUSED tier (unknown tools)
    assert check_safety("format_drive") == "refused"
    assert check_safety("random_unregistered_hack") == "refused"


def test_safety_blocked_patterns():
    # Destructive shell commands MUST be refused immediately
    assert check_safety("shell_command", {"command": "rm -rf /"}) == "refused"
    assert check_safety("shell_command", {"command": "del /s /q c:\\windows"}) == "refused"
    assert check_safety("shell_command", {"command": "format C:"}) == "refused"
    assert check_safety("shell_command", {"command": ":(){ :|:& };:"}) == "refused"
    assert check_safety("shell_command", {"command": "drop database users"}) == "refused"


def test_confirmations_workflow():
    clear_confirmations()

    # Create pending confirmation
    rec = create_confirmation("close_application", {"name": "notepad"})
    conf_id = rec["id"]
    assert rec["status"] == "pending"

    pending = get_pending_confirmations()
    assert len(pending) == 1
    assert pending[0]["id"] == conf_id

    # Deny confirmation
    denied = deny_confirmation(conf_id)
    assert denied["status"] == "denied"
    assert len(get_pending_confirmations()) == 0

    # Create another and approve
    rec2 = create_confirmation("write_clipboard", {"text": "hello test"})
    conf_id2 = rec2["id"]

    with patch("desktop.os_layer.clipboard_write", return_value="Text copied to clipboard."):
        approved = approve_confirmation(conf_id2)
        assert approved["status"] == "approved"
        assert approved["result"] == "Text copied to clipboard."


def test_desktop_tools_registered():
    tool_names = [t["function"]["name"] for t in get_all_tools()]
    expected_tools = [
        "open_application",
        "close_application",
        "open_website",
        "open_folder",
        "take_screenshot",
        "set_volume",
        "lock_screen",
        "read_clipboard",
        "write_clipboard",
        "shell_command",
        "list_windows",
    ]
    for tool_name in expected_tools:
        assert tool_name in tool_names, f"Tool '{tool_name}' missing from registered tools"


def test_os_layer_app_maps():
    assert "downloads" in HARDCODED_FOLDERS
    assert "desktop" in HARDCODED_FOLDERS
    assert "chatgpt" in WEB_APP_MAP
    assert "github" in WEB_APP_MAP
    assert "notepad" in SYSTEM_APP_MAP


@patch("webbrowser.open")
def test_open_web_app(mock_web_open):
    res = open_app("chatgpt")
    assert "https://chat.openai.com" in res
    mock_web_open.assert_called_once()


def test_desktop_api_endpoints():
    from desktop.api import app

    client = app.test_client()

    # Health check (public)
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"

    # API key validation
    res_unauth = client.get("/tools")
    assert res_unauth.status_code == 401

    api_key = app.view_functions["health"].__globals__["_ensure_api_key"]()
    headers = {"X-API-Key": api_key}

    # Tools endpoint
    res_tools = client.get("/tools", headers=headers)
    assert res_tools.status_code == 200
    tools_list = res_tools.get_json()
    assert len(tools_list) >= 10

    # Pending confirmations endpoint
    res_conf = client.get("/confirm/pending", headers=headers)
    assert res_conf.status_code == 200
