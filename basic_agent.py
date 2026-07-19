"""
Microsoft Agent Framework 1.0 — LOCAL demo (no API keys, runs on your Ollama).
Model: pulled from OLLAMA_MODEL_ID env, defaults to qwen2.5-coder:7b.
Teaches: Agent Framework's Agent abstraction + OllamaChatClient (local model runtime).
"""
import asyncio
import os

from agent_framework.ollama import OllamaChatClient


async def main() -> None:
    model = os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:14b")
    agent = OllamaChatClient(
        model=model,               # any model you pulled in Ollama
        host="http://localhost:11434",
    ).as_agent(
        name="LocalTutor",
        instructions="You are a concise, friendly tutor. Answer in plain language.",
    )

    result = await agent.run("In one sentence, what is Microsoft Agent Framework 1.0?")
    print("Agent:", result)


if __name__ == "__main__":
    asyncio.run(main())
