"""
Tests for core/llm.py (unified client, parsing, streaming, and fallback).
"""

from unittest.mock import MagicMock, patch
import pytest

from core.llm import (
    _parse_openai_response,
    _parse_cohere_response,
    chat,
    chat_stream,
    chat_with_fallback,
)


def test_parse_openai_response():
    data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello there!",
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {"name": "web_search", "arguments": '{"query": "NEXUS"}'},
                        }
                    ],
                }
            }
        ]
    }
    parsed = _parse_openai_response(data)
    assert parsed["role"] == "assistant"
    assert parsed["content"] == "Hello there!"
    assert len(parsed["tool_calls"]) == 1
    assert parsed["tool_calls"][0]["function"]["name"] == "web_search"


def test_parse_cohere_response():
    data = {
        "message": {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "This is Cohere output."}
            ],
            "tool_calls": [],
        }
    }
    parsed = _parse_cohere_response(data)
    assert parsed["role"] == "assistant"
    assert parsed["content"] == "This is Cohere output."


@patch("core.llm.requests.post")
@patch("core.llm.load_key", return_value="fake_key")
def test_chat_success(mock_load_key, mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {"message": {"role": "assistant", "content": "Success response"}}
        ]
    }
    mock_post.return_value = mock_resp

    res = chat("groq", [{"role": "user", "content": "Hi"}])
    assert res["content"] == "Success response"


@patch("core.llm.requests.post")
@patch("core.llm.load_key", return_value="fake_key")
def test_chat_stream(mock_load_key, mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        'data: {"choices": [{"delta": {"content": "Hello"}}]}',
        'data: {"choices": [{"delta": {"content": " World"}}]}',
        'data: [DONE]',
    ]
    mock_post.return_value = mock_resp

    chunks = list(chat_stream("groq", [{"role": "user", "content": "Hi"}]))
    assert len(chunks) == 3
    assert chunks[0].get("content") == "Hello"
    assert chunks[1].get("content") == " World"
    assert chunks[2].get("done") is True


@patch("core.llm.chat")
@patch("core.llm.load_key", return_value="fake_key")
def test_chat_with_fallback(mock_load_key, mock_chat):
    # Provider 1 (groq) fails twice, Provider 2 (gemini) succeeds
    mock_chat.side_effect = [
        RuntimeError("Groq 500 server error"),
        RuntimeError("Groq 500 server error"),
        {"role": "assistant", "content": "Gemini fallback succeeded!"},
    ]

    res = chat_with_fallback(
        chain=["groq", "gemini"],
        messages=[{"role": "user", "content": "Hi"}],
        max_retries=1,
        backoff_factor=0.0,  # Fast testing without sleep
    )

    assert res["content"] == "Gemini fallback succeeded!"
    assert mock_chat.call_count == 3
