"""Phase 0 security tests for NEXUS v2."""
import os
import sys
import re

# Ensure project modules are importable
PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _sub in ("core", "agents", "launchers"):
    _p = os.path.join(PROJ_ROOT, _sub)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)


def test_no_hardcoded_api_key():
    """DEFAULT_NEXUS_KEY must not exist anywhere in the codebase."""
    api_path = os.path.join(PROJ_ROOT, "core", "api.py")
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "DEFAULT_NEXUS_KEY" not in content, "Hardcoded DEFAULT_NEXUS_KEY still present in core/api.py"
    assert "XDy3lmPYUWvUGZtORMfKdDwCVBcqpgua0MtQEtOEOso" not in content, "Hardcoded key value still present"


def test_generated_key_uses_secrets():
    """The _generate_and_persist_api_key function must use secrets module."""
    api_path = os.path.join(PROJ_ROOT, "core", "api.py")
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "import secrets" in content, "secrets module not imported"
    assert "secrets.token_urlsafe" in content, "Not using secrets.token_urlsafe for key generation"


def test_cors_not_wildcard():
    """CORS must NOT use origins='*'."""
    api_path = os.path.join(PROJ_ROOT, "core", "api.py")
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Check that the wildcard CORS is not present
    assert '"origins": "*"' not in content, "CORS wildcard '*' still present"
    assert "'origins': '*'" not in content, "CORS wildcard '*' still present (single quotes)"
    # Check that localhost origins are configured
    assert "127.0.0.1" in content or "127\\.0\\.0\\.1" in content, "CORS should allow 127.0.0.1"
    assert "localhost" in content, "CORS should allow localhost"


def test_gemini_key_not_in_url():
    """Gemini API key must be sent in header, never in URL query parameter."""
    for filename in ("providers.py", "imagegen.py"):
        filepath = os.path.join(PROJ_ROOT, "core", filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Find all generateContent URLs — none should have ?key=
        urls = re.findall(r'generateContent\S*', content)
        for url_fragment in urls:
            assert "key=" not in url_fragment, (
                f"Gemini key in URL found in {filename}: ...generateContent{url_fragment}"
            )
        # Verify x-goog-api-key header is used
        assert "x-goog-api-key" in content, f"x-goog-api-key header not found in {filename}"


def test_flask_binds_to_localhost():
    """Default Flask bind address must be 127.0.0.1, not 0.0.0.0."""
    api_path = os.path.join(PROJ_ROOT, "core", "api.py")
    with open(api_path, "r", encoding="utf-8") as f:
        content = f.read()
    # The default should be 127.0.0.1
    assert '"HOST", "127.0.0.1"' in content, "Default HOST should be 127.0.0.1"
    # Should warn when 0.0.0.0 is used
    assert '0.0.0.0' in content and 'WARNING' in content, "Should warn when binding to 0.0.0.0"


def test_no_shell_true_in_desktop_assistant():
    """desktop_assistant.py should not use shell=True."""
    da_path = os.path.join(PROJ_ROOT, "agents", "desktop_assistant.py")
    with open(da_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "shell=True" not in content, "shell=True still present in agents/desktop_assistant.py"


def test_agent_run_command_uses_shlex():
    """agents/agent.py run_command should use shlex on non-Windows."""
    agent_path = os.path.join(PROJ_ROOT, "agents", "agent.py")
    with open(agent_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "import shlex" in content, "shlex not imported in agents/agent.py"
    assert "shlex.split" in content, "shlex.split not used in agents/agent.py"


def test_duplicate_root_launchers_removed():
    """Duplicate root launcher files should be removed."""
    removed_files = [
        "api.py", "agent.py", "desktop_assistant.py",
        "nexuschat.py", "nexus_desktop.py", "Nexus_task.py", "Identity .py"
    ]
    for filename in removed_files:
        filepath = os.path.join(PROJ_ROOT, filename)
        assert not os.path.exists(filepath), f"Duplicate launcher still exists: {filename}"


def test_main_py_still_exists():
    """main.py should still be the single entry point."""
    main_path = os.path.join(PROJ_ROOT, "main.py")
    assert os.path.exists(main_path), "main.py is missing"
