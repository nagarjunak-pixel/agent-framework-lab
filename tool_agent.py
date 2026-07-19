"""
Microsoft Agent Framework 1.0 — LOCAL tool-using agent (no API keys).
Shows function-tool calling against your local Ollama model + streaming output.
Tool: get_time — proves the agent can invoke a local Python function.
"""
import asyncio
import os
from datetime import datetime

from agent_framework import tool
from agent_framework.ollama import OllamaChatClient


@tool
def get_time() -> str:
    """Return the current local date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def main() -> None:
    model = os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:14b")
    agent = OllamaChatClient(
        model=model,
        host="http://localhost:11434",
    ).as_agent(
        name="TimeAgent",
        instructions="You are a helpful assistant. Use the get_time tool when asked about time.",
        tools=[get_time],
    )

    # streaming run — prints tokens as they arrive
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run("What time is it right now? Tell me.", stream=True):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
