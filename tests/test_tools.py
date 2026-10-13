"""
Tests for core/tools.py (tool decorator, registry, schema generation, execution).
"""

from core.tools import (
    tool,
    generate_tool_schema,
    execute_tool,
    get_tool,
    get_all_tools,
    clear_registry,
    tool_web_search,
    tool_generate_image,
    tool_remember_fact,
    tool_recall_memory,
)


def test_tool_decorator_schema_generation():
    @tool(name="calc_add", description="Add two integers together")
    def calc_add(a: int, b: int, note: str = "sum") -> str:
        """Add two numbers."""
        return str(a + b)

    registered = get_tool("calc_add")
    assert registered is not None
    schema = registered["schema"]

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "calc_add"
    assert "Add two integers together" in schema["function"]["description"]

    params = schema["function"]["parameters"]
    assert params["type"] == "object"
    assert params["properties"]["a"]["type"] == "integer"
    assert params["properties"]["b"]["type"] == "integer"
    assert params["properties"]["note"]["type"] == "string"
    assert "a" in params["required"]
    assert "b" in params["required"]
    assert "note" not in params["required"]  # note has default


def test_tool_execution_success():
    @tool(name="multiply_numbers")
    def multiply_numbers(x: int, y: int) -> int:
        return x * y

    # Dict arguments
    result = execute_tool("multiply_numbers", {"x": 6, "y": 7})
    assert result == "42"

    # JSON string arguments
    result_json = execute_tool("multiply_numbers", '{"x": 3, "y": 5}')
    assert result_json == "15"


def test_tool_execution_error_handling():
    @tool(name="fail_tool")
    def fail_tool(msg: str) -> str:
        raise ValueError("Simulated tool crash")

    # Exception should be caught and returned as clean error string
    result = execute_tool("fail_tool", {"msg": "test"})
    assert "Error executing tool 'fail_tool': Simulated tool crash" in result

    # Invalid JSON string
    result_bad_json = execute_tool("fail_tool", "{invalid json")
    assert "Error: Invalid JSON arguments" in result_bad_json

    # Unregistered tool
    result_missing = execute_tool("nonexistent_tool_123", {})
    assert "is not registered" in result_missing


def test_tool_output_truncation():
    @tool(name="long_output_tool")
    def long_output_tool() -> str:
        return "A" * 5000

    result = execute_tool("long_output_tool", {}, max_length=100)
    assert len(result) < 200
    assert "Output truncated" in result


def test_builtin_core_tools():
    all_tools = get_all_tools()
    tool_names = [t["function"]["name"] for t in all_tools]

    assert "web_search" in tool_names
    assert "generate_image" in tool_names
    assert "remember_fact" in tool_names
    assert "recall_memory" in tool_names
