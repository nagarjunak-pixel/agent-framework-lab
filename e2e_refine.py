"""
Microsoft Agent Framework 1.0 — EXTENDED END-TO-END scenario (A): self-refinement loop.

Builds on e2e_pipeline.py by adding a 5th agent:
  1) Collector -> load_dataset()
  2) Analyst   -> compute_stats()
  3) Critic    -> check_quality()
  4) Reporter  -> save_report()        (writes report.md)
  5) Refiner   -> read_report()        READS report.md BACK from disk
                  -> improve_report()  rewrites it with deeper reasoning

This closes the loop: the system observes its own artifact (the file on disk)
and improves it. Proves the framework can do iterative self-improvement ON DISK.

Run:  source .venv/bin/activate
      export OLLAMA_MODEL_ID=qwen2.5:14b
      python e2e_refine.py
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
    if any(w in text.lower() for w in ("because", "therefore", "trend", "growth", "decline")):
        score += 15
    else:
        issues.append("no reasoning")
    score = min(100, score)
    verdict = "ACCEPTABLE" if score >= 70 else "NEEDS WORK"
    return f"SCORE={score} VERDICT={verdict} ISSUES={issues if issues else 'none'}"


@tool
def save_report(content: str) -> str:
    """Write the initial markdown report to disk. content: full markdown text."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WRITTEN {REPORT_FILE} ({len(content)} chars)"


@tool
def read_report() -> str:
    """Read the current report.md from disk and return its contents for refinement."""
    with open(REPORT_FILE, encoding="utf-8") as f:
        return f.read()


@tool
def improve_report(improved: str) -> str:
    """Overwrite report.md with an improved version (deeper insights). improved: full markdown."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(improved)
    return f"REFINED {REPORT_FILE} ({len(improved)} chars)"


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
        "Use the load_dataset tool to read the data, then output the raw data verbatim.",
        tools=[load_dataset],
    )
    analyst = make_agent(
        "Analyst",
        "Use the compute_stats tool on the dataset text. Then write 3-4 bullet "
        "insights that cite actual numbers. Output the bullets.",
        tools=[compute_stats],
    )
    critic = make_agent(
        "Critic",
        "Use the check_quality tool on the analysis text. Then output the score, "
        "verdict, and any notes. Keep it short.",
        tools=[check_quality],
    )
    reporter = make_agent(
        "Reporter",
        "Write a markdown report with sections: '# Dataset Analysis Report', "
        "'## Summary Statistics', '## Insights', '## Quality Assessment'. Then use "
        "save_report to write it to disk. Output a short confirmation.",
        tools=[save_report],
    )
    refiner = make_agent(
        "Refiner",
        "Use read_report to read the existing report.md from disk. Then make it "
        "STRICTLY BETTER: add a '## Trends' section with 2-3 sentences of real "
        "reasoning about growth/decline using the numbers. Use improve_report to "
        "overwrite the file. Output a short confirmation.",
        tools=[read_report, improve_report],
    )

    workflow = SequentialBuilder(
        participants=[collector, analyst, critic, reporter, refiner]
    ).build()

    print("=== Running 5-agent self-refinement pipeline (local Ollama) ===\n")
    result = await workflow.run("Analyze the sample dataset and refine the report.")
    print("\n=== FINAL WORKFLOW OUTPUT ===\n")
    print(extract_text(result))


if __name__ == "__main__":
    asyncio.run(main())
