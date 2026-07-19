"""
Microsoft Agent Framework 1.0 — MULTI-AGENT WORKFLOW demo (100% local, no API keys).

Shows orchestration: a SequentialBuilder chains two agents that BOTH run on your
local Ollama:
  1) Researcher -> drafts 3 bullet points on a topic
  2) Writer     -> turns those bullets into ONE short summary paragraph

The output of agent 1 becomes the input of agent 2 AUTOMATICALLY. This is the
opposite of a single chatbot turn.

Run:  source .venv/bin/activate
       export OLLAMA_MODEL_ID=qwen2.5:14b
       python workflow_demo.py

Swap the builder for other patterns (same API shape):
  from agent_framework.orchestrations import ConcurrentBuilder, HandoffBuilder, GroupChatBuilder, MagenticBuilder
"""
import asyncio
import os

from agent_framework.ollama import OllamaChatClient
from agent_framework.orchestrations import SequentialBuilder


def make_agent(name: str, instructions: str):
    """Wrap a local Ollama chat client as a runnable Agent."""
    return OllamaChatClient(
        model=os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:14b"),
        host="http://localhost:11434",
    ).as_agent(name=name, instructions=instructions)


def extract_text(run_result) -> str:
    """Pull the final workflow output text out of a WorkflowRunResult."""
    outputs = run_result.get_outputs()
    if not outputs:
        return "(no output)"
    # get_outputs() returns the output data objects (AgentResponse) directly
    last = outputs[-1]
    return getattr(last, "text", str(last))


async def main() -> None:
    researcher = make_agent(
        "Researcher",
        "You are a terse researcher. Given a topic, return exactly 3 short bullet "
        "points of key facts. No preamble, no numbering beyond '- '.",
    )
    writer = make_agent(
        "Writer",
        "You are a concise writer. Given bullet points, write ONE short paragraph "
        "that summarizes them. No preamble.",
    )

    workflow = SequentialBuilder(participants=[researcher, writer]).build()

    topic = "Microsoft Agent Framework 1.0"
    print(f"\n=== Topic: {topic} ===\n")
    result = await workflow.run(topic)
    print("FINAL OUTPUT (from Writer):\n")
    print(extract_text(result))


if __name__ == "__main__":
    asyncio.run(main())
