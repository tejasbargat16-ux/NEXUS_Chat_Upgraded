"""
Tool registry and @tool decorator for NEXUS v2.
Generates OpenAI-compatible function calling schemas from Python functions,
manages tool execution, error handling, and truncation.
"""

from __future__ import annotations

import functools
import inspect
import json
import logging
import os
from typing import Any, Callable, get_type_hints

logger = logging.getLogger("nexus.tools")

# Global registry of registered tools
_REGISTRY: dict[str, dict[str, Any]] = {}


def _python_type_to_json_type(py_type: Any) -> str:
    """Map Python type to JSON Schema type."""
    if py_type in (str, type(None)):
        return "string"
    if py_type is int:
        return "integer"
    if py_type is float:
        return "number"
    if py_type is bool:
        return "boolean"
    if py_type in (list, tuple) or (hasattr(py_type, "__origin__") and py_type.__origin__ in (list, tuple)):
        return "array"
    if py_type is dict or (hasattr(py_type, "__origin__") and py_type.__origin__ is dict):
        return "object"
    return "string"


def generate_tool_schema(func: Callable, name: str | None = None, description: str | None = None) -> dict[str, Any]:
    """Generate an OpenAI-compatible function schema from a callable."""
    func_name = name or func.__name__
    func_doc = (description or func.__doc__ or f"Execute {func_name}").strip()

    sig = inspect.signature(func)
    try:
        type_hints = get_type_hints(func)
    except Exception:
        type_hints = {}

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        param_type = type_hints.get(param_name, str)
        json_type = _python_type_to_json_type(param_type)

        param_spec: dict[str, Any] = {
            "type": json_type,
            "description": f"Parameter '{param_name}'",
        }
        properties[param_name] = param_spec

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": func_name,
            "description": func_doc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def tool(name: str | None = None, description: str | None = None) -> Callable:
    """Decorator to register a function as an LLM tool.
    
    Can be used as @tool or @tool(name="...", description="...").
    """
    def decorator(fn: Callable) -> Callable:
        tool_name = name or fn.__name__
        tool_desc = description or fn.__doc__ or f"Tool {tool_name}"
        schema = generate_tool_schema(fn, name=tool_name, description=tool_desc)

        _REGISTRY[tool_name] = {
            "name": tool_name,
            "func": fn,
            "schema": schema,
            "description": tool_desc,
        }

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper.tool_name = tool_name
        wrapper.schema = schema
        return wrapper

    if callable(name):
        actual_func = name
        name = None
        return decorator(actual_func)
    return decorator


def register_tool(func: Callable, name: str | None = None, description: str | None = None) -> Callable:
    """Explicitly register a tool callable."""
    return tool(name=name, description=description)(func)


def get_tool(name: str) -> dict[str, Any] | None:
    """Return tool registration entry by name."""
    return _REGISTRY.get(name)


def get_all_tools() -> list[dict[str, Any]]:
    """Return list of all tool schemas for OpenAI function calling."""
    return [entry["schema"] for entry in _REGISTRY.values()]


def get_registered_tool_names() -> list[str]:
    """Return list of all registered tool names."""
    return list(_REGISTRY.keys())


def clear_registry() -> None:
    """Clear all registered tools (useful for isolated testing)."""
    _REGISTRY.clear()


def execute_tool(
    name: str,
    arguments: dict[str, Any] | str,
    max_length: int = 4000,
) -> str:
    """Execute a registered tool and return the string result.
    
    Tool errors are caught and returned as clean error strings so the LLM
    can inspect the failure and self-correct. Long outputs are truncated.
    """
    if name not in _REGISTRY:
        return f"Error: Tool '{name}' is not registered. Available tools: {list(_REGISTRY.keys())}"

    # Parse JSON string arguments if necessary
    args_dict: dict[str, Any] = {}
    if isinstance(arguments, str):
        if not arguments.strip():
            args_dict = {}
        else:
            try:
                args_dict = json.loads(arguments)
            except Exception as exc:
                return f"Error: Invalid JSON arguments for tool '{name}': {exc}"
    elif isinstance(arguments, dict):
        args_dict = arguments
    else:
        return f"Error: Expected dict or JSON string arguments, got {type(arguments)}"

    func = _REGISTRY[name]["func"]
    try:
        output = func(**args_dict)
        result_str = str(output) if output is not None else "Success (no output)"
    except Exception as exc:
        logger.warning("Tool '%s' execution failed: %s", name, exc)
        return f"Error executing tool '{name}': {exc}"

    if len(result_str) > max_length:
        result_str = result_str[:max_length] + f"\n... [Output truncated at {max_length} characters]"

    return result_str


# ---------------------------------------------------------------------------
# Built-in Core Tools
# ---------------------------------------------------------------------------

@tool(name="web_search", description="Search the web for current, up-to-date information, news, or facts.")
def tool_web_search(query: str) -> str:
    """Search the web for queries."""
    from core.search import web_search, format_results
    source, results = web_search(query, os.getcwd())
    return format_results(source, results)


@tool(name="generate_image", description="Generate an image from a text description using Pollinations AI or Gemini.")
def tool_generate_image(prompt: str) -> str:
    """Generate an image from a prompt."""
    from core.imagegen import generate_image_pollinations
    path = generate_image_pollinations(prompt)
    return f"Image successfully generated and saved to: {path}"


@tool(name="remember_fact", description="Save an important durable fact or preference about the user into long-term memory.")
def tool_remember_fact(fact: str, category: str = "general") -> str:
    """Save a fact to long-term memory."""
    from core.memory import remember
    stored = remember(fact=fact, category=category)
    if stored:
        return f"Fact remembered: '{fact}' (category: {category})"
    return f"Fact already known: '{fact}'"


@tool(name="recall_memory", description="Search long-term memory for saved facts about the user, preferences, or past details.")
def tool_recall_memory(query: str) -> str:
    """Search long-term memory."""
    from core.memory import recall
    facts = recall(query=query)
    if not facts:
        return f"No memories found matching '{query}'."
    return "Relevant memories:\n" + "\n".join(f"- {f}" for f in facts)
