"""
Microsoft Agent Framework 1.0 — MCP TOOL INTEGRATION scenario (C).

Proves the framework can call an external MCP (Model Context Protocol) server
over stdio via MCPStdioTool. We spin up our own tiny mcp_server.py as the MCP
server and let a local agent invoke its `data_quality_flag` tool.

This is the SAME protocol Claude Code / Cursor / every MCP client uses -- so
the pattern extends to thousands of real MCP servers (filesystem, github, etc.).

Run:  source .venv/bin/activate
      export OLLAMA_MODEL_ID=qwen2.5:14b
      python e2e_mcp.py
"""
import asyncio
import json
import os

from agent_framework import MCPStdioTool
from agent_framework.ollama import OllamaChatClient

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(LAB_DIR, "mcp_server.py")


async def main() -> None:
    # Connect to our local MCP server over stdio (no external service, no keys)
    mcp_tool = MCPStdioTool(
        name="tiny-mcp",
        command="python3",
        args=[SERVER],
        env=dict(os.environ),
    )

    agent = OllamaChatClient(
        model=os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:14b"),
        host="http://localhost:11434",
    ).as_agent(
        name="MCPAgent",
        instructions=(
            "You have an MCP tool called 'tiny-mcp.data_quality_flag'. Use it to "
            "check data quality of a numeric series. Given a series, call the tool "
            "and report its verdict in one sentence."
        ),
        tools=[mcp_tool],
    )

    series = [12000, 13500, 11800, 15200, 16100, 17500]
    prompt = f"Check data quality for this revenue series: {json.dumps(series)}"

    print("=== Running MCP-tool agent (local Ollama + local MCP server) ===\n")
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run(prompt, stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
