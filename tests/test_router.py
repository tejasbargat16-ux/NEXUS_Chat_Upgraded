"""
Tests for core/router.py (task classification and provider routing).
"""

from core.router import classify, get_chain, route


def test_classify_code():
    assert classify("How do I debug a NullPointerException in Java?") == "code"
    assert classify("Write a Python function to sort a list of dicts") == "code"
    assert classify("```python\nprint('hello')\n```") == "code"
    assert classify("Fix this syntax error in my docker compose file") == "code"


def test_classify_study():
    assert classify("Explain the formula for Nyquist sampling rate") == "study"
    assert classify("Can you give me GATE syllabus for Computer Networks?") == "study"
    assert classify("What is the theorem behind Dijkstra algorithm?") == "study"


def test_classify_vision():
    assert classify("Please inspect this image and describe the diagram") == "vision"
    assert classify("Here is a screenshot of the error") == "vision"
    assert classify("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA") == "vision"


def test_classify_chat():
    assert classify("Hello, how are you doing today?") == "chat"
    assert classify("Tell me a funny joke about robots") == "chat"
    assert classify("What is the capital of France?") == "chat"


def test_route_and_chain():
    task, chain = route("Write a python script")
    assert task == "code"
    assert isinstance(chain, list)
    assert len(chain) > 0

    task, chain = route("Explain the GATE calculus syllabus")
    assert task == "study"
    assert isinstance(chain, list)
    assert len(chain) > 0
