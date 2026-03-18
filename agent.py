
# agent without streamlit dependencies, for using html
from __future__ import annotations

import asyncio
import json
import os
import sys

from llm_client import get_client, MODEL

MCP_SERVER_PATH = os.path.join(os.path.dirname(__file__), "mcp_server.py")

SYSTEM_PROMPT = (
    "You are an AI rescue model that aids in drone mission choices, resource management, and information retrieval of the environment for a detecting survivors in the designated disaster region. "
    "You have tools available to scan the area with drones, check drone locations and status"
    "Always use the appropriate tool. For drone scans, collect all information you can from the scan results"
    "You will be asked to make decisions about the ideal route of the drone when scanning, and how to best utilize the drone's battery life. You can also be asked to retrieve information about the environment or the drones themselves. Always use the tools at your disposal to make informed decisions and provide accurate information." 
    "You will confirm with the user before making any decisions or taking any actions with the drones. Always provide reasoning for your decisions and actions, and ask for user confirmation before proceeding."
    "Always give a step by step reasoning for your decisions and actions"
)

MAX_ITERATIONS = 10

# ---------------------------------------------------------------------------
# MCP helpers
# ---------------------------------------------------------------------------

async def _list_mcp_tools() -> list[dict]:
    from mcp import StdioServerParameters, stdio_client
    from mcp.client.session import ClientSession

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_PATH],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return _mcp_tools_to_openai(tools_result.tools)


async def _call_mcp_tool(tool_name: str, tool_args: dict) -> str:
    from mcp import StdioServerParameters, stdio_client
    from mcp.client.session import ClientSession

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_PATH],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    parts.append(content.text)
                else:
                    parts.append(str(content))
            return "\n".join(parts) if parts else "(no output)"


def _mcp_tools_to_openai(mcp_tools) -> list[dict]:
    openai_tools = []
    for tool in mcp_tools:
        parameters = tool.inputSchema if tool.inputSchema else {"type": "object", "properties": {}}
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": parameters,
            },
        })
    return openai_tools


# ---------------------------------------------------------------------------
# Agent loop — no Streamlit, works anywhere
# ---------------------------------------------------------------------------

def run_agent(user_input: str, tools: list[dict], message_history: list[dict] = []) -> tuple[str, list[dict]]:
    api_messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *message_history,
        {"role": "user", "content": user_input},
    ]

    tool_events: list[dict] = []

    for _ in range(MAX_ITERATIONS):
        response = get_client().chat.completions.create(
            model=MODEL,
            messages=api_messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or "", tool_events

        api_messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(_call_mcp_tool(tc.function.name, args))
            loop.close()
            tool_events.append({"id": tc.id, "name": tc.function.name, "args": args, "result": result})
            api_messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "I wasn't able to complete the request within the allowed steps.", tool_events