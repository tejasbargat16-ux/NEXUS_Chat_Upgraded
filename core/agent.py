"""
Tool-calling agent loop for NEXUS v2.
Replaces brittle text-pattern parsing (RUN:/SEARCH:/IMAGE:) with native OpenAI
function/tool calling. Executes tools iteratively until final answer or max_steps.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, NamedTuple

from core.config import get_agent_settings, get_default_chain
from core.llm import chat, chat_with_fallback
from core.memory import recall
from core.tools import execute_tool, get_all_tools

logger = logging.getLogger("nexus.agent")


class AgentResult(NamedTuple):
    """Result of an agent loop execution."""
    reply: str
    tool_log: list[dict[str, Any]]


def run_agent(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    max_steps: int | None = None,
    system_prompt: str | None = None,
    provider_id: str | None = None,
    fallback_chain: list[str] | None = None,
    temperature: float = 0.7,
) -> AgentResult:
    """Run the tool-calling agent loop.
    
    Args:
        messages: Conversation history in OpenAI format.
        tools: List of tool schemas (defaults to all registered tools if None).
        max_steps: Maximum iterations of tool execution (defaults to config agent.max_steps).
        system_prompt: Optional system prompt to prepend.
        provider_id: Specific provider to use (optional).
        fallback_chain: Provider chain for fallback (defaults to default_chain).
        temperature: Sampling temperature.
        
    Returns:
        AgentResult with (reply, tool_log).
    """
    agent_cfg = get_agent_settings()
    steps_limit = max_steps if max_steps is not None else agent_cfg.get("max_steps", 6)
    tool_schemas = tools if tools is not None else get_all_tools()
    chain = fallback_chain or get_default_chain()

    # Work on a copy of messages to avoid mutating caller's list
    convo = [copy.deepcopy(m) for m in messages]

    # Find last user query to inject relevant memories
    last_user_query = ""
    for m in reversed(convo):
        if m.get("role") == "user":
            last_user_query = m.get("content", "")
            break

    # Gather memory context if available
    memories_text = ""
    if last_user_query:
        try:
            matched_facts = recall(last_user_query, limit=4)
            if matched_facts:
                memories_text = "\n\nRelevant memories about user:\n" + "\n".join(f"- {f}" for f in matched_facts)
        except Exception as e:
            logger.debug("Memory recall skipped: %s", e)

    # Prepend or update system prompt
    if system_prompt or memories_text:
        combined_sys = (system_prompt or "") + memories_text
        if convo and convo[0].get("role") == "system":
            convo[0]["content"] = convo[0]["content"] + memories_text
        elif combined_sys:
            convo.insert(0, {"role": "system", "content": combined_sys.strip()})

    tool_log: list[dict[str, Any]] = []
    final_reply = ""

    for step in range(steps_limit):
        logger.debug("Agent loop step %d/%d", step + 1, steps_limit)

        # Send request to LLM
        if provider_id:
            response_msg = chat(
                provider_id=provider_id,
                messages=convo,
                tools=tool_schemas if tool_schemas else None,
                temperature=temperature,
            )
        else:
            response_msg = chat_with_fallback(
                chain=chain,
                messages=convo,
                tools=tool_schemas if tool_schemas else None,
                temperature=temperature,
            )

        tool_calls = response_msg.get("tool_calls")
        content = response_msg.get("content") or ""

        # If model did not request any tool calls, we have the final reply
        if not tool_calls:
            final_reply = content
            break

        # Append assistant message with its tool_calls
        convo.append({
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls,
        })

        # Execute each requested tool call
        for tc in tool_calls:
            call_id = tc.get("id", f"call_{step}")
            func_data = tc.get("function", {})
            func_name = func_data.get("name", "")
            func_args = func_data.get("arguments", {})

            logger.info("Agent executing tool: %s with args: %s", func_name, func_args)
            output = execute_tool(func_name, func_args)

            tool_entry = {
                "step": step + 1,
                "tool_call_id": call_id,
                "name": func_name,
                "arguments": func_args,
                "output": output,
            }
            tool_log.append(tool_entry)

            # Append tool result message
            convo.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": func_name,
                "content": output,
            })
    else:
        # Reached max_steps without a clean return
        logger.warning("Agent reached max_steps (%d)", steps_limit)
        final_reply = content or "Task completed with maximum tool steps reached."

    return AgentResult(reply=final_reply, tool_log=tool_log)
