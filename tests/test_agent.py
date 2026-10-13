"""
Tests for core/agent.py (tool-calling agent loop).
"""

from unittest.mock import patch
import pytest

from core.agent import run_agent, AgentResult
from core.tools import tool, clear_registry


def test_agent_direct_response():
    # LLM returns content with no tool calls
    mock_response = {
        "role": "assistant",
        "content": "Paris is the capital of France.",
        "tool_calls": None,
    }

    with patch("core.agent.chat_with_fallback", return_value=mock_response):
        res = run_agent([{"role": "user", "content": "What is the capital of France?"}])

    assert isinstance(res, AgentResult)
    assert res.reply == "Paris is the capital of France."
    assert len(res.tool_log) == 0


def test_agent_tool_calling_loop():
    # Step 1: Model requests a tool call to 'get_weather'
    # Step 2: Model receives tool result and returns final answer
    step1_response = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call_abc",
                "type": "function",
                "function": {
                    "name": "mock_weather",
                    "arguments": '{"city": "Tokyo"}',
                },
            }
        ],
    }
    step2_response = {
        "role": "assistant",
        "content": "The weather in Tokyo is sunny and 22C.",
        "tool_calls": None,
    }

    @tool(name="mock_weather")
    def mock_weather(city: str) -> str:
        return f"{city}: Sunny, 22C"

    with patch("core.agent.chat_with_fallback", side_effect=[step1_response, step2_response]):
        res = run_agent(
            messages=[{"role": "user", "content": "How is the weather in Tokyo?"}],
            max_steps=5,
        )

    assert res.reply == "The weather in Tokyo is sunny and 22C."
    assert len(res.tool_log) == 1
    assert res.tool_log[0]["name"] == "mock_weather"
    assert "Tokyo: Sunny, 22C" in res.tool_log[0]["output"]


def test_agent_max_steps_guard():
    # Infinite tool calling loop simulation
    loop_response = {
        "role": "assistant",
        "content": "Calling tool again...",
        "tool_calls": [
            {
                "id": "call_loop",
                "type": "function",
                "function": {"name": "mock_loop_tool", "arguments": "{}"},
            }
        ],
    }

    @tool(name="mock_loop_tool")
    def mock_loop_tool() -> str:
        return "looping"

    with patch("core.agent.chat_with_fallback", return_value=loop_response):
        res = run_agent(
            messages=[{"role": "user", "content": "Loop forever"}],
            max_steps=3,
        )

    assert len(res.tool_log) == 3
    assert "Calling tool again..." in res.reply or "maximum tool steps reached" in res.reply
