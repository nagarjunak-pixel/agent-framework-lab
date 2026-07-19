"""
Microsoft Agent Framework 1.0 — COMPLEX END-TO-END scenario (100% local, no API keys).

A 4-agent autonomous analyst pipeline, orchestrated with SequentialBuilder:
  1) Collector  -> load_dataset()      reads a local CSV
  2) Analyst    -> compute_stats()     parses + computes real statistics
  3) Critic     -> check_quality()     agentic self-evaluation of the analysis
  4) Reporter   -> save_report()       WRITES a markdown report to disk (real artifact)

The tools do the heavy lifting (parsing/math/file I/O) so the local 14B model
only has to orchestrate + format -- this is the right pattern for on-device LLMs.
The end-to-end proof is a real file: report.md on your disk.

Run:  source .venv/bin/activate
      export OLLAMA_MODEL_ID=qwen2.5:14b
      python e2e_pipeline.py
"""
import asyncio
import csv
import os
import statistics

from agent_framework import tool
from agent_framework.ollama import OllamaChatClient
from agent_framework.orchestrations import SequentialBuilder

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(LAB_DIR, "data", "sample_metrics.csv")
REPORT_FILE = os.path.join(LAB_DIR, "report.md")


# ---------- TOOLS (deterministic; the model only has to pass data through) ----------

@tool
def load_dataset() -> str:
    """Load the local sample_metrics.csv and return its raw contents as text."""
    with open(DATA_FILE, encoding="utf-8") as f:
        return f.read()


@tool
def compute_stats(csv_text: str) -> str:
    """Compute count/mean/min/max/sum for every numeric column in the CSV text.
    csv_text: the raw CSV text returned by load_dataset."""
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
def check_quality(text: str) -> str:
    """Score the quality of an analysis text from 0-100 and list issues.
    text: the analysis to evaluate."""
    score, issues = 50, []
    if len(text) >= 200:
        score += 20
    else:
        issues.append("too short")
    if any(c.isdigit() for c in text):
        score += 15
    else:
        issues.append("no numbers")
    if "because" in text.lower() or "therefore" in text.lower() or "trend" in text.lower():
        score += 15
    else:
        issues.append("no reasoning")
    score = min(100, score)
    verdict = "ACCEPTABLE" if score >= 70 else "NEEDS WORK"
    return f"SCORE={score} VERDICT={verdict} ISSUES={issues if issues else 'none'}"


@tool
def save_report(content: str) -> str:
    """Write the final markdown report to disk. content: full markdown text."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WRITTEN {REPORT_FILE} ({len(content)} chars)"


# ---------- AGENTS ----------

def make_agent(name: str, instructions: str, tools):
    return OllamaChatClient(
        model=os.environ.get("OLLAMA_MODEL_ID", "qwen2.5:14b"),
        host="http://localhost:11434",
    ).as_agent(name=name, instructions=instructions, tools=tools)


def extract_text(run_result) -> str:
    outputs = run_result.get_outputs()
    if not outputs:
        return "(no output)"
    return getattr(outputs[-1], "text", str(outputs[-1]))


async def main() -> None:
    collector = make_agent(
        "Collector",
        "Use the load_dataset tool to read the data, then output the raw data "
        "verbatim so the next agent can analyze it. Do not summarize.",
        tools=[load_dataset],
    )
    analyst = make_agent(
        "Analyst",
        "Use the compute_stats tool on the dataset text you received. Then write "
        "3-4 bullet-point insights that cite the actual numbers. Output the bullets.",
        tools=[compute_stats],
    )
    critic = make_agent(
        "Critic",
        "Use the check_quality tool on the analysis text. Then output: the score, "
        "whether it is ACCEPTABLE, and any notes. Keep it short.",
        tools=[check_quality],
    )
    reporter = make_agent(
        "Reporter",
        "Using the analysis and the critic's evaluation, write a final markdown "
        "report with these sections: '# Dataset Analysis Report', "
        "'## Summary Statistics', '## Insights', '## Quality Assessment'. "
        "Then use the save_report tool to write it to disk. Output a short confirmation.",
        tools=[save_report],
    )

    workflow = SequentialBuilder(
        participants=[collector, analyst, critic, reporter]
    ).build()

    print("=== Running end-to-end analyst pipeline (local Ollama) ===\n")
    result = await workflow.run("Analyze the sample dataset.")
    print("\n=== FINAL WORKFLOW OUTPUT ===\n")
    print(extract_text(result))


if __name__ == "__main__":
    asyncio.run(main())
