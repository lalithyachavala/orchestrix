# Orchestrix — AI Agent & Workflow Orchestration

> **Independent illustrative engineering demonstration.** Orchestrix is an
> original portfolio artifact built to demonstrate engineering capability.
> It is not affiliated with, and does not represent, any real company,
> product, or customer. All business data is synthetic.

Orchestrix is a platform for building, running, and monitoring AI agents that
use **tools** to execute business tasks across connected (simulated) systems.
The tool-calling architecture is genuine: a real reason → act → observe loop
with typed tool schemas, dynamic tool selection, approval gates, retries, and
live execution streaming. Agent reasoning is pluggable behind an `AgentAdapter`
interface — the default planner is deterministic and keyless so the whole
platform runs with **zero API keys**; a real LLM can be dropped in later.

## What's inside

| Path            | What |
|-----------------|------|
| `apps/api`      | FastAPI engine: agent runtime, 6 tools over seeded SQLite, approval/retry, SSE, supervisor multi-agent. |
| `apps/web`      | Next.js 14 UI: agents, React Flow workflow builder, live execution monitor, multi-agent demo. |
| `docs`          | Case study + architecture & tool-call sequence diagrams (Mermaid). |
| `infra`         | docker-compose (api + web). |
| `scripts`       | One-command local run. |
| `demo` / `screenshots` | Walkthrough script, GIF, and captures. |

## Quick start (zero keys)

```bash
# 1. API  (http://localhost:8000)
cd apps/api
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Web  (http://localhost:3000)
cd apps/web
npm install
npm run dev
```

Or: `scripts/run.ps1` (Windows) / `scripts/run.sh` (POSIX) boots both.

The API seeds synthetic customers, orders, tickets, and CRM records on
startup (SQLite, in `apps/api/orchestrix.db`). No external services required.

## Genuine tool-calling

The engine is **not** a script that prints canned agent text. Each run:

1. The adapter is handed the task, the agent's instructions, the **JSON
   schemas** of its available tools, and the running step history.
2. It returns a decision: call a specific tool with arguments **it chose**, or
   finish. The default `MockPlanner` makes this decision from task intent +
   tool schemas + what's already been observed — real state-driven routing,
   not hardcoded output.
3. The runtime dispatches the tool against live (seeded) data, feeds the real
   result back as an observation, and loops.
4. Sensitive tools (CRM writes, notifications) halt the run at
   `pending_approval` until a human approves.

Swap `ADAPTER=claude` (and add an adapter impl + key) to route the same loop
through a real LLM — the runtime, tools, and UI don't change.

## Optional real LLM

Off by default. See `apps/api/.env.example`. No account or key is bundled or
required.
