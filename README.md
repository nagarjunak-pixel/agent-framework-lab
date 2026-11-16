# Microsoft Agent Framework 1.0 — Local Lab

**Purpose:** hands-on intro to Microsoft Agent Framework 1.0, running 100% locally
on your own Ollama — no API keys, no cost, no cloud.

## Why this matters
- Agent Framework 1.0 (GA, both Python + .NET) is the **production successor** to
  **AutoGen** AND **Semantic Kernel** (same Microsoft teams). It merges AutoGen's
  agent abstractions with Semantic Kernel's enterprise features (session state,
  middleware, telemetry) and adds graph-based **Workflows** for explicit
  multi-agent orchestration.
- First-party connectors: Microsoft Foundry, Azure OpenAI, OpenAI, Anthropic,
  Amazon Bedrock, Google Gemini, **and Ollama** (local). The Ollama connector is
  what lets us run everything on-machine.
- This is the *opposite* of Manus: Manus is a hosted autonomous cloud agent (now
  owned by Meta) that spins up its own VM and executes tasks end-to-end. Agent
  Framework is a *builder SDK* you run and own.

## What's in this lab
- `basic_agent.py` — minimal Agent that answers a question via your local Ollama model.
- `tool_agent.py` — an Agent that calls a local Python **function tool** (`get_time`)
  and streams its answer. Proves tool-use works against a local model.
- `workflow_demo.py` — **multi-agent orchestration**: a `SequentialBuilder` chains a
  Researcher agent → Writer agent (both local Ollama). Output of agent 1 auto-feeds
  agent 2. Swap the builder for `ConcurrentBuilder` / `HandoffBuilder` /
  `GroupChatBuilder` / `MagenticBuilder` for other patterns (same API shape).
- `e2e_pipeline.py` — **COMPLEX END-TO-END**: 4-agent sequential pipeline
  (Collector → Analyst → Critic → Reporter). Tools do real work: `load_dataset()`
  reads a CSV, `compute_stats()` does actual math, `check_quality()` scores the
  analysis, `save_report()` **writes report.md to disk**. Proof = a real file.
- `e2e_refine.py` — **(A) self-refinement loop**: adds a 5th `Refiner` agent that
  `read_report()`s the file back from disk and `improve_report()`s it. The system
  observes its own artifact and iterates.
- `e2e_handoff.py` — **(B) agent-driven control flow**: `HandoffBuilder` where a
  `Router` agent DECIDES which branch runs (`HANDOFF_ANALYST` vs `HANDOFF_SKIP`),
  then `Analyst` → `Reporter` or `Skipper` → `DONE`. Control flow driven by agent
  decisions, not a fixed order.
- `e2e_mcp.py` + `mcp_server.py` — **(C) MCP integration**: a tiny stdio MCP server
  exposing `data_quality_flag`, called by the agent via `MCPStdioTool`. Same protocol
  Claude Code / Cursor use — extends to thousands of real MCP servers.
- `openrouter_demo.py` — **OpenRouter-backed agent** (your API key, gitignored in `.env`).
  Uses the Chat Completions API with real tool-calling (e.g. `get_revenue_growth`).
  NOTE: MS Agent Framework's `OpenAIChatClient` is Responses-API-only and OpenRouter
  does NOT support the Responses API, so this demo uses the `openai` SDK transport
  directly — the correct working path for OpenRouter. Set `OPENROUTER_MODEL` to override
  (default `deepseek/deepseek-v4-flash`).
- `.env` — your OpenRouter API key. **GITIGNORED — never committed.**
- `data/sample_metrics.csv` — sample dataset the pipelines analyze.
- `report.md` — artifact written by the pipelines (overwritten each run).

## Run
    cd ~/agent-framework-lab
    source .venv/bin/activate
    export OLLAMA_MODEL_ID=qwen2.5:14b   # or any model you pulled
    python basic_agent.py
    python tool_agent.py
    python workflow_demo.py
    python e2e_pipeline.py          # writes report.md
    python e2e_refine.py            # reads + improves report.md
    python e2e_handoff.py           # conditional routing
    python e2e_mcp.py               # agent calls local MCP server

## Teaching notes
1. `OllamaChatClient(model="qwen2.5:14b", host="http://localhost:11434")` is the ONLY
   thing pointing at a model — swap `model=` to any local model with no code change.
   NOTE: the Ollama connector (beta, `--pre`) uses `model=`, NOT `model_id=`.
2. `.as_agent(name=, instructions=)` wraps a chat client into a runnable Agent.
3. `@tool` decorates a plain Python function so the agent can invoke it. Local
   models vary in tool-calling reliability — qwen2.5:14b worked here; qwen2.5-coder:7b
   is a solid local choice.
4. Multi-agent orchestration: `from agent_framework.orchestrations import
   SequentialBuilder` (sequential / concurrent / handoff / group-chat / Magentic-One).
   `SequentialBuilder(participants=[a, b]).build()` -> `Workflow`; call `await workflow.run(topic)`
   and read `result.get_outputs()[-1].text` for the final output. Participants MUST be
   distinct agent instances (no duplicates).

---

## Author & Enterprise AI Architecture Hub
Built by **[Nagarjuna Reddy Kamireddy](https://nagarjunak-pixel.github.io/)** (*Nagarjuna Kamireddy / Nagarjuna K*) — Lead AI Architect, GenAI & Agentic AI Lead, and Corporate AI Trainer (20+ years across Enterprise Data, SAP HANA & Production AI; AWS Certified Solutions Architect – Professional & NVIDIA-Certified Professional: Agentic AI).

- **Official Portfolio & Architecture Hub:** [https://nagarjunak-pixel.github.io/](https://nagarjunak-pixel.github.io/)
- **Enterprise Case Studies & Technical Articles:** [Case Studies](https://nagarjunak-pixel.github.io/case-studies.html) · [Architecture Articles](https://nagarjunak-pixel.github.io/articles.html) · [10-Mandate Role Fit](https://nagarjunak-pixel.github.io/roles.html)
- **Master CV & AI Search Index:** [Master CV](https://nagarjunak-pixel.github.io/resume.html) · [`llms-full.txt`](https://nagarjunak-pixel.github.io/llms-full.txt) · [LinkedIn](https://www.linkedin.com/in/nagarjuna-kamireddy)
