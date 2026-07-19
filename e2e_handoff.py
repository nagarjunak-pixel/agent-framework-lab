"""
Microsoft Agent Framework 1.0 — AGENT-DRIVEN BRANCHING scenario (B).

Uses FunctionalWorkflow: a Python orchestrator function that RUNS the Router agent
to get a real decision, then conditionally branches:
   - Router decides "worth analyzing"  -> Analyst -> Reporter (writes report.md)
   - Router decides "insufficient"     -> Skipper (writes a note)

This is genuine agent-driven control flow: an LLM agent makes the routing
decision, but the orchestration is deterministic Python -- the robust pattern for
local 14B models (GroupChatBuilder's message-protocol is too fragile on-device).

Run:  source .venv/bin/activate
      export OLLAMA_MODEL_ID=qwen2.5:14b
      python e2e_handoff.py
"""
import asyncio
import csv
import os
import statistics

from agent_framework import tool, FunctionalWorkflow, FunctionalWorkflowAgent
from agent_framework.ollama import OllamaChatClient

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(LAB_DIR, "data", "sample_metrics.csv")
REPORT_FILE = os.path.join(LAB_DIR, "report.md")


@tool
def load_dataset() -> str:
    """Load the local sample_metrics.csv and return its raw contents as text."""
    with open(DATA_FILE, encoding="utf-8") as f:
        return f.read()


@tool
def compute_stats(csv_text: str) -> str:
    """Compute count/mean/min/max/sum for every numeric column in the CSV text."""
    rows = list(csv.reader(csv_text.strip().splitlines()))
    if not rows:
        return "empty dataset"
    header, data = rows[0], rows[1:]
    out = []
    for i, col in enumerate(header):
        values = []
        for r in data:
            try:
                values.append(float(r[i]))
            except (ValueError, IndexError):
                pass
        if values:
            out.append(
                f"{col}: count={len(values)} mean={statistics.mean(values):.2f} "
                f"min={min(values)} max={max(values)} sum={sum(values):.2f}"
            )
    return "\n".join(out)


@tool
def save_report(content: str) -> str:
    """Write the markdown report to disk. content: full markdown text."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WRITTEN {REPORT_FILE} ({len(content)} chars)"


@tool
def write_note(content: str) -> str:
    """Write a short 'insufficient data' note to disk. content: text."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Insufficient Data\n\n{content}\n")
    return f"WRITTEN {REPORT_FILE}"


def make_agent(name: str, instructions: str, tools):
    return OllamaChatClient(
        model=os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:14b"),
        host="http://localhost:11434",
    ).as_agent(name=name, instructions=instructions, tools=tools)


def extract_text(resp) -> str:
    return getattr(resp, "text", str(resp))


async def run_agent(agent, message: str) -> str:
    result = await agent.run(message)
    # Agent.run returns an AgentResponse (or similar) with .text
    if hasattr(result, "text"):
        return result.text
    # fallback: it may be a streamed object; grab final
    return str(result)


async def orchestrator(message: str) -> str:
    router = make_agent(
        "Router",
        "Use load_dataset to read the data. DECIDE: does it have >=3 rows with "
        "numeric columns? Reply with EXACTLY one of: 'ANALYZE' or 'SKIP'.",
        tools=[load_dataset],
    )
    verdict = await run_agent(router, message)
    print(f"[Router decision] {verdict.strip()[:60]!r}")

    if "SKIP" in verdict.upper():
        skipper = make_agent(
            "Skipper",
            "The data was insufficient. Use write_note to record a short note. "
            "Then reply 'DONE'.",
            tools=[write_note],
        )
        return await run_agent(skipper, "Write the insufficient-data note.")

    analyst = make_agent(
        "Analyst",
        "Use compute_stats on the dataset, then write 3 bullet insights citing "
        "numbers. Then reply 'ANALYST DONE'.",
        tools=[compute_stats],
    )
    analysis = await run_agent(analyst, message)
    print(f"[Analyst] produced {len(analysis)} chars")

    reporter = make_agent(
        "Reporter",
        "Write a markdown report ('# Dataset Analysis Report', "
        "'## Summary Statistics', '## Insights', '## Quality Assessment') and use "
        "save_report to write it to disk. Then reply 'DONE'.",
        tools=[save_report],
    )
    return await run_agent(reporter, f"Dataset analysis:\n{analysis}")


async def main() -> None:
    wf = FunctionalWorkflow(orchestrator, name="BranchingPipeline")
    agent = FunctionalWorkflowAgent(wf, name="PipelineAgent")

    print("=== Running agent-driven BRANCHING pipeline (local Ollama) ===\n")
    out = await agent.run("Process the dataset with conditional routing.")
    print("\n=== FINAL OUTPUT ===\n")
    print(extract_text(out))


if __name__ == "__main__":
    asyncio.run(main())
